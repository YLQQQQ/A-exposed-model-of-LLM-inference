# Windows llama.cpp候选窗口与最小接线 0.1

2026-10-13；依据用户本轮本地实现授权。`LLAMA-NATIVE-WINDOW/0.1.0`只用于未来新
Engineering；不是签署Formal协议、平台资格或采集授权。Gate13限定PASS保持、Gate14
NOT_RUN；PyTorch自然baseline和原冻结结果不变，四对C0/Cpre追加Pilot仍暂停。

## 1. 窗口与实际完成链

固定引擎commit `d81235049384534c167caea52b85a694f6103d14`，只支持单GPU、隔离request、
32输入/2输出、batch1、warmup3/repeat1，CPU greedy、backend sampler count=0、无graph。
不把这一子域授予其他采样方式、所有输入长度、并发请求或完整llama.cpp。

- Request开始：成功窗前drain后、首次处理固定token输入之前。包含该次调用内的自然
  Host batch准备/H2D，不预执行模型，不额外把输入搬到GPU来套旧起点。
- 首/末完成：`llama_sampler_sample`实际返回Host token后观察；文本化、发送和持久化
  在窗外。CPU采样路径取得Host logits再选择token，不与PyTorch GPU argmax/小token
  D2H视为同一数值/执行路径。
- Prefill=`[start,ready0)`；Decode=`[ready0,ready1)`；Request=`[start,ready1)`。
  三个区间共用trace原生point引用；Host steady clock只用于诊断，不平移或拟合trace时钟。
  NVTX是非同步标记，不能单独证明GPU完成，也不表示实际网络流式发送。

**与MC0.2的差异明确保留**：旧PyTorch从GPU-resident输入之后开始；此候选包含自然输入
准备。用户授权候选设计与本地接线，不自动签署新Formal起点，也不授跨引擎同口径排名。
后续若作Formal或横向比较，须单独批准native支持声明/协议，不更改旧窗口。

固定源码原件核对纠正了上一页的接口简写：实际头文件`llama_process`接收
`llama_batch_ext*`，不是普通`llama_batch`；本入口使用同版本已有的`llama_decode(ctx,batch)`。
模型调用后仍走自然sampler/getter→context/scheduler→CUDA backend同步，不新增Cpre。
实际头文件SHA256 `c9a5f025ad7dbf07eda6660c8ff2c32cd80c07ba440d80728707a9c9d13c1bc3`；
网页抽取行号不作接口/字节身份依据。[官方接口](https://github.com/ggml-org/llama.cpp/blob/d81235049384534c167caea52b85a694f6103d14/include/llama.h)。

## 2. 已实现的最小文件与版本合同

| 入口 | 职责与严格边界 |
|---|---|
| `exposedpath/native_llama.py` | prepare、来源字节核验、角色/配置/模型/输入约束、实际producer和P0/P1逐值消费 |
| `native/llama_cpp/{main.cpp,producer_core.hpp,observer.*}` | 真实native入口与共享编排；实际暖机、窗外context drain、token返回后point；CPU替身只替换Engine依赖 |
| `native/llama_cpp/CMakeLists.txt` | 固定源码/工具链、静态observer单实例、关闭graph；新patched编译输入不修改vendor原件 |
| `exposedpath_v141/native_llama_scope.py` | 新point投影/真实调用桥接，复用Canonical、设备映射、官方诊断规则和S/A，不重写算法 |
| `scripts/native_llama_local.py` | CPU文件CLI：patch-backend/prepare/inspect-producer/review；没有build、模型启动、profile/export或默认采集子命令 |

spec/build/conversion/producer/scope分别为`exposedpath-native-llama-<kind>/0.1.0`；
boundary=`exposedpath-native-boundary/0.1.0`、sync=`exposedpath-native-sync/0.1.0`。
角色只能ENGINEERING/Engineering；公共旧schema、registry、A/B公式及旧读取路径零改动。
未知版本、错role、错hash或错误配置拒绝，不把旧Engineering/Pilot/失败结果改名升级。

spec绑定：稳定experiment/WMPC/run/pass/attempt/request/repeat；实际binary/model及
输入i32文件的长度/SHA256；build与conversion回执；执行commit/clean；候选声明和GPU
mask/UUID/PCI。输入是32个非负little-endian int32 ID（128 bytes），不再tokenize、插入
BOS或chat template；native加载后校验实际词表范围。文件SHA与spec SHA、模型SHA分开。
producer记录PID/TID、spec原字节hash、实际暖机和drain、逐token值/EOS、point延迟及实际
sync调用。失败/partial不能COMPLETE；每个pass/run用新路径，不覆盖/resume/retry。
P0/P1必须逐值一致，不要求生成token与旧HF一致。

### 必要标记，不是通用监控

固定CUDA backend原件SHA256
`1315f06baff63da74e085b7ec01974474dac1f8ec1074af13eb70faba4751961`。
只包装五个已有调用点：backend synchronize，buffer set/get tensor及set/get tensor 2d
中的原`cudaStreamSynchronize`。函数名是真实源码callsite，实际执行序号独立记录；
流参数只求值一次，调用总数/顺序不变，没有插入、删去或移动CUDA同步。
特别保留自然H2D helper的`cudaStreamPerThread`同步，不只标记输出getter。

标记包含backend device index、实际CUDA ordinal、native handle、phase/token及返回值；
native handle从原调用参数取得，不因它等于0或2推断trace stream/mode。
marker→同线程唯一runtime API→唯一CUPTI sync correlation→context/trace stream，
再以UUID/PCI关联physical mask、CUDA logical、Nsight inventory与activity设备。
一个handle发生冲突/复用歧义就拒绝，不把编号相等当证据。

只记录**真实调用线程的active native frame**。其他线程不会自动继承request身份；
`n_threads=1`不证明没有第三方线程。未标记blocking API、外线程提交的未知ownership、
未支持completion或影响不明诊断仍拒绝；没有记录不等于没有依赖。
P0也保留共同诊断包装，仅P1启用NVTX，故P0不是未经包装的SDK精确性能基准。
标记/序列化会带来Host开销和观测延迟，不宣称零误差或所有内部阻塞已拆解。

### S/A消费与尚未授予的资格

投影保留point原Raw引用、clock、spec/producer/SQLite hash；它不提供dependency。
同步身份来自精确调用点，不从宽泛forward范围伪造callsite，也不泛用N1 RAW_PHYSICAL
或opaque allocation特例。已知submit必须有设备效果，缺映射/失败/错流/未知依赖拒绝。
`cudaMalloc`的旧窄域许可没有推广到native；若实物出现，只能停在具体适用性问题。

默认模式保持UNKNOWN；计算两种条件下**完整W、边、ownership、terminal、validity及
原因**，不能仅以A数值相等放行。当前实现保守地要求整个计算输入的S等价；若实际证据
只能证明更窄的目标scope，不通过猜模式来解决，需先给出对应的局部适用性依据。
复用既有四消息官方处置规则，不改warning/UNKNOWN，不豁免新类型/目标冲突。
输出只能`ADAPTER_CALCULATION_ONLY_NOT_QUALIFICATION`，物理B未资格、D/Signature关闭。

**窗前drain的真实差额**：native使用引擎`llama_synchronize`的scheduler/backend scope，
不是CUDA device-wide drain。不能复制旧device-wide的已闭合前缀声明。本地S保留完整
前驱并拒绝未知ownership；真实暖机历史可能因此阻塞，需要同backend桥接证明实际
drain/stream/event闭包与必要前缀。若需native局部closed-prior适配，先提交窄域条款和
独立预期，不删除历史成员、伪造其request ownership或授完整物理B。

## 3. 构建与模型身份锁定（未在目标机执行）

固定VS2022 x64、MSVC14.38.33130、CUDA12.4、sm89、Release、静态库、GGML_NATIVE=OFF、
GGML_CUDA=ON、GGML_CUDA_GRAPHS=OFF。不取较新预编译包、升级driver/Toolkit或转Linux。
构建必须提供干净固定vendor根、另存的patched backend及NVTX include根；LF原件字节pin
不接受静默CRLF归一化。CMake会拒绝错误commit/字节/工具链或不唯一source替换。
最小构建参数（待审，不是本轮执行）：

```powershell
cmake -S $CodeRoot/native/llama_cpp -B $BuildRoot -G 'Visual Studio 17 2022' -A x64 -T 'version=14.38.33130' -DLLAMA_SOURCE_ROOT=$EngineSource -DNATIVE_PATCHED_BACKEND=$PatchedBackend -DNVTX_INCLUDE_ROOT=$NvtxInclude
cmake --build $BuildRoot --config Release --target native-llama --parallel 2
```

build回执须从实际Git、源码/patch、CMake cache、工具链与binary生成；不能手填一份通过
的CPU fixture回执部署。实际编译/链接仍未验证，源码可行性或CPU语法检查不代替它。

HF→GGUF使用同commit转换器`--outtype f16`。conversion回执固定原HF快照清单hash、
converter源码hash/commit/参数、实际GGUF hash和`GGUFReader`实际tensor类型/数量。
允许混合F16及非量化F32，不能填“全部FP16”；其他/未知类型拒绝。revision缺失保持null。
原HF/模型/历史路径不迁移，转换输出另存；转换后数值/时延不直接与旧HF等价比较。
[固定reader字段](https://github.com/ggml-org/llama.cpp/blob/d81235049384534c167caea52b85a694f6103d14/gguf-py/gguf/gguf_reader.py)。

## 4. 独立预期与实际验证边界

CPU实际文件链使用编译的共享producer core，替身Engine，不调用CUDA/Nsight/模型。
合成Raw：Request `[100,300)`，Prefill `[100,180)`，Decode `[180,300)`；先行活动
`[110,120)`已完成但仍属于首sync W；`[130,160)`在sync `[140,170)`暴露20ns；后提交
Decode活动`[210,260)`不得进入首W，在第二sync `[240,270)`暴露20ns。
launch API为2+5+5=12ns；Request五预算为Host128/API12/wait40/residual20/unattributed0。
这是独立手算，不以analyzer自产预期；明确不证明全部内部等待或真实平台资格。

反例：角色升级、错commit/graph/量化/输入、重封后违规、错GPU、错token/EOS/warmup/drain、
缺边界、错request/stream、缺correlation或设备效果、新型诊断、两模式W不同及结果篡改。
仅有守恒、零unknown或大wait不算成功。编译失败/部分调用和已观察EOS保留原异常/实际token。
host语法检查使用固定真实llama.h及声明-only CUDA/NVTX替身，不链接/运行CUDA；CUDA backend
和目标VS14.38的编译仍未执行。少量官方头/源码只读下载在忽略的本地诊断目录，不是安装。

## 5. 最小目标机方案与停点

1. **先仅构建/转换及身份回执**：固定源码、实际cache/工具链/binary/GGUF/tensor表、既有
   HF清单来源和32-token输入。不要运行native模型或collector。预计45–120分钟CPU构建/
   转换，临时15GiB（估计；以实际磁盘预检为准），长期YLQ仍<50GB。失败立即停止，不升级。
2. **回执审查后必要同backend桥接**：公开GGML CUDA接口上的小型确定性加法→自然async
   D2H→原backend synchronize→Host标量；预期值事先固定，含已完成先行成员和后提交排除。
   比较源码hook、实际stream/context/correlation、drain/event闭包与terminal，不借旧Q0
   自动授native。该native受控GPU微程序尚未实现/运行，不交付可采集入口冒充准备完成。
   预算最多1个受控进程/1profile、10分钟/1GiB估计；缺映射、未知依赖或不可判别即停。
3. **桥接和必要closed-prior适用性已闭合后**，才审查一对自然32/2 P0→P1，warmup3/repeat1，
   最多2模型进程/1profile，15–25分钟/3GiB估计。不得明知历史前缀仍被拒绝就启动。
   全新身份/目录；输出逐值相等、完整point/实际调用、所有必要效果/依赖和质量检查。
   非零exit、EOS、OOM、timeout、身份冲突、未支持同步、不可界定缺口均停止，不重试/替补。

每个阶段只回传**一个ZIP**：操作transcript/exit，实际build/conversion/config/source索引，
manifest/spec及producer/entry；若采集获批，再含REP/SQLite/export、Canonical、projection/
调用桥接/诊断/S/A及全部失败记录，文件大小/SHA256清单完整覆盖。不得把P0/P1差当纯Nsight
成本，不要求wait增大，不授Formal或引擎排名。原件不变；审查与完整归档核验后才另列可恢复
副本的精确清理清单，本轮不清理。

实际target构建、GGUF事实、native drain/ownership/依赖资格仍未取得。下面的阶段1交付
替代此前“未制包”状态；当前唯一可进入的目标步骤仍是阶段1，须协调审查/用户执行。

## 6. 阶段1固定离线交付（7.148；仅本地准备）

> 7.149：首次cc9b595阶段1已在源码Git身份检查处BLOCKED，尚未建立CPU转换环境、编译或
> 转换。文件专用ZIP遗漏空`.git/refs`导致Git exit128；下述目录保全修复仅供全新attempt，
> 不恢复原入口或更改旧失败状态。固定源码/依赖/构建参数、GPU预算0及资格边界保持。

`scripts/run_native_llama_stage1.ps1`与`exposedpath/native_stage1.py`是唯一阶段1入口：
固定增量bundle、固定llama浅Git源码快照、NVTX 3.1.1头文件（commit
`6230bdf710bc94f44d433acceba735aaa9090ba5`）、Windows/Python3.11完整wheel清单及SHA256
锁文件均放在同一个忽略的部署ZIP中。目标机不下载源码/依赖、不升级CUDA/driver、不运行
native-llama、CUDA身份查询、模型forward或collector。原HF位置保持，只读核验原23项清单。
GGUF转换写新目录；读取实际GGUFReader tensor表与F16/F32计数，不能用`--outtype f16`
冒充实际全部tensor为F16。缓存辅助文件仍按原清单保留身份，不宣称它们都是模型输入。
依赖现有VS2022 BuildTools/x64 MSVC14.38.33130及Windows SDK、nvcc12.4.131和CUDA12.4
runtime DLL、Git及Python3.11/已有pytest。包内不再分发MSVC/Toolkit/driver；缺件即停，
不自动安装。cl/nvcc实际版本、路径/hash及三项CUDA runtime DLL文件身份纳入回执。
控制入口固定使用已验证的仓库venv（jsonschema/pytest），不假设Conda base拥有这些包；
base仅做stdlib bootstrap/部署和创建私有CPU转换venv。旧推理venv不安装或改包。

转换用新私有CPU环境：torch 2.11.0+cpu（固定引擎转换requirements要求）、transformers
4.57.6、numpy2.2.6等；不修改原torch2.6+cu124推理venv。它只读取/变换权重，不运行
模型；转换后的表示/数值仍不授HF推理等价。revision继续未知。build/conversion回执记录
原HF清单hash、原始converter/source hash、实际编译参数/cache/toolchain/binary/GGUF
身份；不能把期望值复制成“实测GPU”字段。

**配置的CUDA副作用已显式处理**：固定CMake3.31.10的`CMakeTestCUDACompiler`在ABI
编译成功后调用`cmake_cuda_architectures_native`运行CUDA ABI程序，单设sm89仍不足以
满足本轮禁止初始化CUDA。交付只在新私有CMake环境中、核对原模块SHA256
`f0958609e1886fd10deb71ba2554d77dde7289608dcd3c54d5b0cd0a19d88145`后，将该函数替换为
记录“设备探测禁用、native架构未知”的CPU-only函数。原模块另存回执；不修改系统CMake，
不设`COMPILER_FORCED`/伪造编译成功，正常编译/链接检查仍保留。固定sm89、GGML_NATIVE=OFF、
禁用FetchContent联网；固定源码中Windows/x64/MSVC所选分支没有另一CUDA程序运行路径。
[官方检测调用](https://github.com/Kitware/CMake/blob/v3.31.10/Modules/CMakeTestCUDACompiler.cmake)
与[设备探测模块](https://github.com/Kitware/CMake/blob/v3.31.10/Modules/Internal/CMakeCUDAArchitecturesNative.cmake)。

编译允许调用现有cl/nvcc CPU编译工具；版本检查不是GPU初始化。CPU回归只覆盖交付文件链、
safe ZIP、来源/内容绑定、工具调用顺序、故障保留和私有CMake函数行为，不授MSVC/CUDA实编译
通过。目标构建失败即停、不安装替代工具链。构建上限90分钟、转换30分钟；超时只终止该
直接工具PID，不杀同名进程，后代仍未知则保留状态。回传仅完成的日志和metadata；不证明
所有后代不存在，也不自动运行下一阶段。

预留20GiB临时磁盘、45–120分钟估计；暂存可以超过长期50GB目标。长期新增应只保留
必要binary/runtime依赖、GGUF约3.1GB、回执/来源与封存交付，约4–5GiB估计。构建中间件、
独立CPU转换环境、vendor展开副本可重建，但只能在批次审查/完整归档核验后另列准确清单
清理；本脚本不清理。若现有长期量加必要保留量超过50GB，应先裁定可恢复副本，不能删除
HF/Raw/旧证据腾空间。

回传一个metadata ZIP，含完整大小/hash清单、日志、Git/toolchain/CPU原始回执、CMake cache
与probe原件/patch、GGUF tensor表、build/conversion receipt、失败/退出状态。GGUF和build
tree不再复制进回传ZIP；实际内容hash钉在回执中，服务器原新目录保留。阶段1成功仅
`STAGE1_COMPLETE_NOT_QUALIFICATION`；GPU/native资格NOT_RUN，旧Gate13限定PASS不变。

### 阶段2独立预期与停点（仅设计，不附执行入口）

同SDK scheduler/backend调用的受控图：已标注暖机H2D→确定性加法→自然D2H；调用实际
`ggml_backend_sched_synchronize`（对应`llama_synchronize`下游），返回后才开始测量。
输入向量`[1,2]+[3,4]`，Host输出必须`[4,6]`，预先固定，不调用S/A自产oracle。首个
measured图同样加法，随后自然Host读取；第二图只能在首Host token返回后提交。记录实际
warmup/measured/后提交身份，不假设`n_threads=1`能覆盖native worker。

1. **drain命题**：实际scheduler使用的所有backend/stream/events必须由原API、correlation
   和调用顺序恢复；drain物理W包含所有语义前驱（已完成成员也保留），必要terminal不晚于
   成功drain返回。只看到活动end早于返回，或只看到调用名成功，不足以证明闭包。CPU
   backend无CUDA事件时需其实际完成scope，不把未记录backend推断不存在。
2. **同步命题**：首sync W必须包含同scope已完成暖机前缀及本轮先行H2D/kernel/D2H；按
   实际自然调用顺序分别确定，不能把后提交D2H塞入前sync，也不能只选pending活动。用
   映射实际设备/context/stream和event边验证；native handle不是trace ID、特殊handle不
   决定LEGACY/PTDS。两模式若依赖集合/terminal不同则INCONCLUSIVE，不用A相等替代。
3. **局部A命题**：成功drain之后没有未关闭必要前驱/未知跨流边，request/phase与Host
   token锚点同trace时钟。warmup身份属真实窗外角色，完整物理W仍保留；只有现有合同可
   支持的局部投影才能不给其预算。若模型实物缺少该ownership、需要native closed-prior
   增量条款，单独裁决，不凭受控例自动推及模型所有线程/allocator。
4. **判别/停止**：实际数值错、sync失败、缺mapping/event边、错线程/stream、闭包或
   ownership无法确定即拒绝；活动交集为零可合法成立，不以较大wait为成功。正例只证明
   该同调用子域，不能证明全部native模型或B资格。最多1受控进程/1profile待另审，
   drain/ownership未闭合时不得启动自然P0/P1；本阶段1包没有该程序或自动续采路径。

### 7.149 目录保全修复与依赖复用

新源码归档显式写入目录成员，含空Git refs/objects/info；对于已封存旧文件专用ZIP，
只按`exposedpath-native-source-layout/0.1.0`的哈希绑定目录清单恢复到新目录。清单来自
原producer快照，其3712个文件与旧归档文件清单逐字节一致；不是在失败现场猜测补目录。
源码ZIP仍保持原字节，新增目录不改变任何文件，恢复后再次核验文件/目录集合。

Git查询与CMake都显式指定源码自己的`--git-dir`/`--work-tree`；核对绝对Git目录、顶层、
固定HEAD及clean，结构缺失/父仓库/错误HEAD不能通过。身份查询禁用可选锁刷新，防止
只读`git status`改变封存index字节；原source/hash/commit要求不放宽。

修复交付以前置cc9b595为基线，只含增量bundle、控制脚本、目录清单与新配置。已传完整
离线包作为只读资产根，原manifest SHA256与全部40项当前文件/覆盖严格核验；缺失、
变化、reparse或错来源即停。旧package/失败树不写入，不复用旧展开engine或转换环境；
在全新root重新完成阶段1，没有模型/GPU探测/Nsight入口。回传仍一个metadata ZIP。
