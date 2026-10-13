#pragma once
#include "observer.hpp"
#include <stdexcept>

namespace exposedpath_native {
struct Engine {
    virtual ~Engine() = default;
    virtual void reset() = 0;
    virtual void drain() = 0;
    virtual void process(const std::vector<int32_t> &) = 0;
    virtual int32_t sample() = 0;
    virtual bool is_eog(int32_t) = 0;
};
inline std::vector<int32_t> invoke(Engine & engine,const std::vector<int32_t> & input,Observer * observer) {
    std::vector<int32_t> current=input,output;
    for (int ordinal=0;ordinal<2;++ordinal) {
        int32_t token;
        if (observer) {
            ActiveFrame frame(*observer,ordinal==0?"prefill":"decode",ordinal);
            engine.process(current); // natural batch preparation/H2D remains inside
            token=engine.sample();   // real Host token must return before boundary
            observer->boundary(ordinal+1,token);
            observer->document["tokens"].push_back(token);
        } else {
            engine.process(current);token=engine.sample();
        }
        if (engine.is_eog(token)) {
            if(observer)observer->document["early_eos"]=true;
            throw std::runtime_error("EARLY_EOS");
        }
        output.push_back(token); current={token};
    }
    return output;
}
inline void run_request(Engine & engine,const std::vector<int32_t> & input,Observer & observer) {
    observer.document["actual_input_token_ids"]=input;
    for (int i=0;i<3;++i) {
        engine.reset();
        const auto start=now_ns();auto tokens=invoke(engine,input,nullptr);const auto end=now_ns();
        observer.document["warmups"].push_back({{"ordinal",i},{"status","COMPLETE"},
            {"host_start_ns",start},{"host_end_ns",end},{"tokens",tokens}});
    }
    engine.reset();
    const auto start=now_ns();engine.drain();const auto end=now_ns();
    observer.document["drain"]={{"status","COMPLETE"},{"scope","ENGINE_CONTEXT_SCHEDULER"},
        {"host_start_ns",start},{"host_end_ns",end}};
    observer.document["actual_input_tokens"]=input.size();
    observer.boundary(0);
    invoke(engine,input,&observer);
    observer.document["early_eos"]=false;
    observer.document["status"]="COMPLETE";
    // Persistence/text output belongs to the caller after the last boundary.
}
}
