// Fixed source API. Windows-only target; no serving/text/network inside windows.
#include "producer_core.hpp"
#include "llama.h"
#include <cuda_runtime.h>
#include <nvtx3/nvToolsExt.h>
#include <windows.h>
#include <filesystem>
#include <algorithm>
#include <cctype>
#include <cstdio>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <sstream>

using namespace exposedpath_native;
static void check(bool ok,const char * message) { if (!ok) throw std::runtime_error(message); }
static void cuda_check(cudaError_t error) { check(error==cudaSuccess,cudaGetErrorString(error)); }
static void verify_ref(const json & ref) {
    const auto path=ref.at("path").get<std::string>();
    check(std::filesystem::file_size(std::filesystem::u8path(path))==ref.at("size_bytes").get<uint64_t>(),"artifact size conflict");
    check(sha_file(path)==ref.at("sha256"),"artifact SHA256 conflict");
}
static json query_device(const json & expected) {
    const char * order=std::getenv("CUDA_DEVICE_ORDER"),* mask=std::getenv("CUDA_VISIBLE_DEVICES");
    check(order && mask && expected.at("cuda_device_order")==order && expected.at("cuda_visible_devices")==mask,"mask/order conflict");
    int count,device;cuda_check(cudaGetDeviceCount(&count));cuda_check(cudaGetDevice(&device));
    check(count==1 && device==0,"actual CUDA device count/index conflict");
    cudaDeviceProp properties{};cuda_check(cudaGetDeviceProperties(&properties,device));
    const auto & uuid=properties.uuid;
    char pci[64];cuda_check(cudaDeviceGetPCIBusId(pci,sizeof(pci),device));
    std::ostringstream out;
    for (int i=0;i<16;++i) {
        if(i==4||i==6||i==8||i==10)out<<'-';
        out<<std::hex<<std::setw(2)<<std::setfill('0')<<static_cast<unsigned>(static_cast<unsigned char>(uuid.bytes[i]));
    }
    auto expected_uuid=expected.at("gpu_uuid").get<std::string>();
    if(expected_uuid.rfind("GPU-",0)==0)expected_uuid=expected_uuid.substr(4);
    std::transform(expected_uuid.begin(),expected_uuid.end(),expected_uuid.begin(),[](unsigned char c){return std::tolower(c);});
    check(out.str()==expected_uuid,"actual GPU UUID conflict");
    // Parse PCI components, do not compare formatting or ordinals.
    auto parse_pci=[](const std::string & text) {
        unsigned d,b,s,f;char extra;
        check(std::sscanf(text.c_str(),"%x:%x:%x.%x%c",&d,&b,&s,&f,&extra)==4,"PCI parse failure");
        return std::vector<unsigned>{d,b,s,f};
    };
    check(parse_pci(pci)==parse_pci(expected.at("pci_bus_id")),"actual GPU PCI conflict");
    return json{{"cuda_device_order",order},{"cuda_visible_devices",mask},
        {"gpu_index_physical",std::stoi(mask)}, // derived from actual numeric mask, not CUDA ordinal
        {"gpu_index_logical",device},{"gpu_uuid",out.str()},{"pci_bus_id",pci}};
}

class LlamaEngine : public Engine {
    llama_model * model=nullptr;
    llama_context * context=nullptr;
    llama_sampler * sampler=nullptr;
    const llama_vocab * vocab=nullptr;
public:
    json actual_arguments;
    explicit LlamaEngine(const json & spec) {
        llama_backend_init();
        auto mp=llama_model_default_params();
        mp.n_gpu_layers=-1;mp.split_mode=LLAMA_SPLIT_MODE_NONE;mp.main_gpu=0;
        mp.use_extra_bufts=false;mp.check_tensors=true;
        model=llama_model_load_from_file(spec.at("artifacts").at("model").at("path").get<std::string>().c_str(),mp);
        check(model!=nullptr,"model load failure");vocab=llama_model_get_vocab(model);
        auto cp=llama_context_default_params();
        cp.n_ctx=64;cp.n_batch=32;cp.n_ubatch=32;cp.n_seq_max=1;
        cp.n_threads=1;cp.n_threads_batch=1;cp.samplers=nullptr;cp.n_samplers=0;
        cp.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;
        cp.type_k=GGML_TYPE_F16;cp.type_v=GGML_TYPE_F16;
        context=llama_init_from_model(model,cp);check(context!=nullptr,"context init failure");
        sampler=llama_sampler_chain_init(llama_sampler_chain_default_params());
        check(sampler!=nullptr,"sampler init failure");
        llama_sampler_chain_add(sampler,llama_sampler_init_greedy());
        // These are the real constructor arguments, not a copied expectation.
        actual_arguments={{"input_tokens",32},{"output_tokens",2},{"batch_size",1},{"warmup_count",3},{"repeat_count",1},
            {"sampling","CPU_GREEDY"},{"backend_sampler_count",cp.n_samplers},{"n_ctx",cp.n_ctx},
            {"n_batch",cp.n_batch},{"n_ubatch",cp.n_ubatch},{"n_threads",cp.n_threads},
            {"n_threads_batch",cp.n_threads_batch},{"n_gpu_layers",mp.n_gpu_layers},{"split_mode","NONE"},
            {"backend","GGML_CUDA"},{"cuda_graphs",false},{"flash_attention","DISABLED"},{"kv_type","F16"}};
        check(actual_arguments==spec.at("configuration"),"actual configuration arguments conflict");
    }
    ~LlamaEngine() override {
        if(sampler)llama_sampler_free(sampler);
        if(context)llama_free(context);
        if(model)llama_model_free(model);
        llama_backend_free();
    }
    void reset() override { llama_memory_clear(llama_get_memory(context),false);llama_sampler_reset(sampler); }
    void drain() override { llama_synchronize(context); } // outside request only
    void process(const std::vector<int32_t> & tokens) override {
        for(auto t:tokens)check(t>=0 && t<llama_vocab_n_tokens(vocab),"input token outside actual vocabulary");
        auto batch=llama_batch_get_one(const_cast<llama_token *>(tokens.data()),static_cast<int32_t>(tokens.size()));
        check(llama_decode(context,batch)==0,"native process failure");
    }
    int32_t sample() override { return llama_sampler_sample(sampler,context,-1); }
    bool is_eog(int32_t token) override { return llama_vocab_is_eog(vocab,token); }
};

int main(int argc,char ** argv) {
    if(argc!=3) {std::cerr<<"usage: native-llama run_spec.json new_producer.json\n";return 2;}
    Observer * observer=nullptr;
    try {
        auto spec=read_json(argv[1]);
        observer=new Observer(spec,sha_file(argv[1]),GetCurrentProcessId(),GetCurrentThreadId());
        observer->document["execution_kind"]="NATIVE_CUDA";
        write_new_json(std::string(argv[2])+".entry.json",{{"status","ENTERED_PRE_MODEL"},
            {"pid",observer->pid},{"tid",observer->tid},{"spec_sha256",observer->spec_hash}});
        check(spec.at("schema_version")=="exposedpath-native-llama-spec/0.1.0"
            && spec.at("engine_commit")=="d81235049384534c167caea52b85a694f6103d14"
            && spec.at("identity").at("run_role")=="ENGINEERING"
            && spec.at("identity").at("data_role")=="Engineering"
            && spec.at("declaration").at("status")=="CANDIDATE_ENGINEERING_ONLY","spec version/role conflict");
        for(auto & ref:spec.at("sources"))verify_ref(ref);
        for(auto & ref:spec.at("artifacts"))verify_ref(ref);
        wchar_t self[32768];check(GetModuleFileNameW(nullptr,self,32768)>0,"executable path unavailable");
        check(std::filesystem::equivalent(std::filesystem::path(self),
            std::filesystem::u8path(spec.at("artifacts").at("binary").at("path").get<std::string>())),"actual executable path conflict");
        observer->document["actual_gpu"]=query_device(spec.at("expected_gpu"));
        int runtime_version,driver_api_version;
        cuda_check(cudaRuntimeGetVersion(&runtime_version));cuda_check(cudaDriverGetVersion(&driver_api_version));
        observer->document["runtime_identity"]={{"cuda_runtime_version",runtime_version},
            {"cuda_driver_api_version",driver_api_version}};
        check(runtime_version==12040 && driver_api_version>=12040,"actual CUDA runtime/driver capability conflict");
        auto input=read_tokens(spec.at("sources").at("token_input").at("path"));
        if(spec.at("identity").at("pass_id")=="pass1") {
            observer->mark=[](const std::string & s){nvtxMarkA(s.c_str());};
            observer->push=[](const std::string & s){nvtxRangePushA(s.c_str());};
            observer->pop=[](){nvtxRangePop();};
        } else check(spec.at("identity").at("pass_id")=="pass0","pass conflict");
        LlamaEngine engine(spec);
        observer->document["observed_configuration"]=engine.actual_arguments;
        run_request(engine,input,*observer);
        observer->persist(argv[2]);delete observer;return 0;
    } catch(const std::exception & error) {
        // Persistence failure cannot turn failure into success or hide stderr.
        if(observer) {
            observer->document["status"]="FAILED";observer->document["error"]=error.what();
            try {observer->persist(argv[2]);}catch(...){std::cerr<<"producer receipt IO failed\n";}
        }
        std::cerr<<error.what()<<'\n';delete observer;return 1;
    }
}
