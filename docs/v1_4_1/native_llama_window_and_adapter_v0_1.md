# Windows llama.cpp候选窗口与最小接线 0.1

2026-10-13；依据用户本轮本地实现授权。`LLAMA-NATIVE-WINDOW/0.1.0`只用于未来新
Engineering；不是签署Formal协议、平台资格或采集授权。Gate13限定PASS保持、Gate14
NOT_RUN；PyTorch自然baseline和原冻结结果不变，四对C0/Cpre追加Pilot仍暂停。

**2026-10-14安全停点（7.156）：llama.cpp扩展暂停。** 已完成的§7.155最小API修复
保留在`1e1c1fd6b91ed2001ea308d9bda2b721c23c2f9b`，不撤销工作或删除原件；不再制作
部署包、不安排服务器执行或后续引擎资格。当前转回[PyTorch完成政策与负载路线](device_exposure_scope_and_windows_engine_v0_2.md#当前pytorch路线完成政策负载与可支持的解释)。
后文构建/桥接/自然配对步骤均为历史待审方案，不是现行执行指令。

**最近已完成的本地工程记录为§7.155。** 48567aa目标C/C++、CUDA真实编译链接预检及完整configure
已通过；完整build停于adapter引用不存在的CUDA Runtime API。修复与前置真实头文件
编译门仅在本地验证，尚未授构建/GPU资格。本轮无新包、命令或服务器执行安排；旧入口
及§7.148～7.154保留历史，不再恢复或重复执行。

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

spec/conversion/producer/scope为`exposedpath-native-llama-<kind>/0.1.0`；当前Ninja
build为0.2.2（仅构建回执适配），显式旧build0.1.0/0.2.0/0.2.1读取见§7.155；
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

## 3. 构建与模型身份锁定（完整目标构建尚未成功）

固定VS2022 x64、MSVC14.38.33130、CUDA12.4、sm89、Release、静态库、GGML_NATIVE=OFF、
GGML_CUDA=ON、GGML_CUDA_GRAPHS=OFF。不取较新预编译包、升级driver/Toolkit或转Linux。
构建必须提供干净固定vendor根、另存的patched backend及NVTX include根；LF原件字节pin
不接受静默CRLF归一化。CMake会拒绝错误commit/字节/工具链或不唯一source替换。
以下VS生成器参数仅保留为历史设计；当前Ninja路线使用§7.151/7.154的固定参数与
生成的交付配置，不再次执行此旧命令：

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

### 7.150 VS实例发现与真实C/C++预检

598d447目标机回传证明Git目录修复、依赖安装和32项CPU回归通过；CMake3.31.10却在
首个C/C++ project处拒绝VS实例，尚未编译或转换。cl/nvcc版本正确仅证明相应文件可执行，
不证明VS Installer实例/默认工具目录/MSBuild/SDK完整。失败argv没有显式实例；未取得
实例事实前，不据此猜测缺安装或修改选择。原cache/失败root与原ZIP保持。

依据[CMake3.31.10实例发现源码](https://github.com/Kitware/CMake/blob/v3.31.10/Source/cmVSSetupHelper.cxx)
的LoadVSInstanceVCToolsetVersion与实例选择路径，记录默认VCTools声明及实际目录存在性；
不把DevShell所选14.38覆盖写入声明。依据[VS实例选择](https://cmake.org/cmake/help/v3.31/variable/CMAKE_GENERATOR_INSTANCE.html)
与[Microsoft vswhere/MSBuild](https://github.com/microsoft/vswhere/wiki/Find-MSBuild)，定向查询
包含BuildTools的产品集合、VC和MSBuild资格谓词，保留all与qualified的区别。不能用
空结果/查询异常推断工具绝不存在；portable实例需真正的安装build version，不编造版本。

`inspect_native_vs_once.ps1`默认只读取固定checkout/原receipt、实例和指定组件文件，
将facts、原stdout/stderr/exit以及旧cache/log的只读副本放到新诊断目录；不改DevShell、
旧环境/源码/cache，不编译、不转换、不调用模型或CUDA。缺项继续unknown，只有事实
回传完成，绝不是toolchain PASS。机器路径和包身份只存本地交接/忽略配置。

新增`native/toolchain_precheck`仅LANGUAGES C CXX：使用Windows SDK、C对象和C++运行库，
真实configure/compile/link，生成exe不运行。`native_vs_precheck`按事实唯一选择已完整
注册的预定实例，并绑定原cl hash/当前MSBuild/CMake字节；同VS17/x64/-T14.38.33130，
验证实际cache、19.38.33135编译器版本和exe内容。新build目录不可resume，失败即停；
无实例/状态不完整/错版本/变化/歧义拒绝，不能借用本机其他VS版本证明目标机通过。

当前唯一下一动作是取一次事实ZIP，不重跑整套阶段1。真实C/C++预检已经本地接线，但
目标机NOT_RUN；核实实例后才能提供其独立CPU执行，不先交完整构建修复包。后续应
优先严格只读引用已通过的固定CPU工具/资产，避免每次重复pip安装；新build与新回执，
不得修改旧converter或失败cache。实际CUDA编译/转换仍须随后单独通过，CPU预检不授
GPU/native资格，不改变旧Gate13限定PASS或Gate14 NOT_RUN。

### 7.151 固定Ninja构建路线

7.150目标事实已经完整回传：VS/MSBuild存在，但VC组件谓词为空、默认VCTools声明和
VS CUDA12.4 props/targets缺失。原VS发现失败不靠指定实例位置追绿；该旧路线/失败cache
保留，不创建系统默认文件、改注册表、安装组件或升级现有栈。

用户批准stage1/build schema **0.2.0**使用[固定Ninja1.12.1官方资产](https://github.com/ninja-build/ninja/releases/tag/v1.12.1)
（单exe SHA256 `68865c3276d449d746cea5065fdec2baf755d7813e161ab04205b0907b2629b8`），
MSVC14.38.33130/cl19.38.33135、nvcc12.4.131、已观测SDK10.0.20348.0。旧0.1.0只支持
原VS声明，新版本精确匹配Ninja、Release、SDK及实际编译预检，未知版本/错路径或
重封不合格预检拒绝。producer/window/转换与S/A/B版本不变；不授native GPU资格。

`native_ninja`按绝对路径锁定cl/link/lib/nvcc/rc/mt/Ninja/CMake，设置具体SDK头/库和
编译PATH，去除继承的CUDAHOSTCXX/CUDACXX/CL/LINK等覆盖。不用VS Installer和CUDA
MSBuild扩展，不将缺注册解释为实际编译器不可用；实际文件/版本和随后真正编译才决定。
[CMake CUDA host compiler说明](https://cmake.org/cmake/help/v3.31/envvar/CUDAHOSTCXX.html)
规定其环境优先级，故新路线移除该覆盖并显式传入现有cl。所有必需缺件一次集中列出。

同一入口顺序固定：身份/现存依赖与原件绑定 → 相关CPU回归 → 新目录C/C++编译链接 →
新目录CUDA编译链接 → native构建 → GGUF转换/tensor身份。所有生成exe均不运行；
真实cache与CMake生成的编译器字段、输出字节验证成功才前进。CUDA预检含sm89 kernel
和runtime链接，只证明能编译链接，不证明GPU可用；ABI运行架构探测维持已有禁用patch，
没有COMPILER_FORCED或手填WORKS。构建检查在转换前完成，失败停止、不重试/替代。

严格只读复用598运行的CPU转换环境/CMake：原receipt/toolchain/probe patch与两份封存
输入精确hash关联，当前cl/nvcc/CMake/SDK字节核对；pip check及CPU版本核对，不再
pip install或修改旧环境。设置禁pyc和新HF/cache目录；固定源码、目录layout及NVTX
资产继续从旧manifest全覆盖核验，展开到新root；原HF/旧失败/旧cache不写。其他工具
按预定目录与实际版本/hash记录，不把任意新哈希替代已有期望。

回传新增C/C++/CUDA预检JSON、cache、compiler files及configure raw log；native实际
编译信息、build/转换/tensor身份及完整阶段退出仍在同一小metadata ZIP，不重复传GGUF、
源码树/CPU环境或大型build中间件。预留20GiB临时、45–120分钟估计；长期50GB政策
与归档后精确清理条件保持，无自动清理。目标步骤交协调审查后由用户执行；即使全部
stage1成功，仍先审查构建/模型身份，再另行审查受控桥接，不能自动跑自然P0/P1。

### 7.152 工具身份查询独立规则

7.151目标机Ninja版本/原资产核对已通过，但link /?真实退出1100；stdout包含
14.38.33135.0及帮助，stderr为空。它不是实际链接命令，通用Runner提前拒绝导致
未进入C/C++预检。旧BLOCKED回执、原始字节及真实退出码保持，不能由此判断编译能力。

本次选择Windows固定PE资源查询，而不是猜测link/lib本地化帮助的退出约定。
身份规则`exposedpath-native-tool-identity/0.1.0`读取
[GetFileVersionInfoW](https://learn.microsoft.com/en-us/windows/win32/api/winver/nf-winver-getfileversioninfow)
与[VerQueryValueW](https://learn.microsoft.com/en-us/windows/win32/api/winver/nf-winver-verqueryvaluew)
的固定部分：两个实际工具的路径/长度/SHA256先与本次封存reference一致，版本资源
保留原DWORD和实际14.38.33135.0，查询后再核对字节。缺资源、错误版本/工具/读取、
变化均拒绝；不执行link/lib，exit_code为null，不把原1100改成0，也不生成构建PASS。

其余工具保持原严格约定：Ninja/CMake版本、Git身份、Python/CPU依赖assert成功；
真实configure/compile/link/转换仍exit0且核对cache、真实编译器及输出文件。旧VS
查询规则只供原版本路径，不全局允许非零。新目录元数据保留独立link/lib身份回执、
toolchain引用及原帮助回执ZIP的SHA，完整帮助原件不转码改写。

部署前置为882425c，旧CPU环境/VS事实来源仍598d447，二者显式分开，不随新HEAD
改写历史身份。新小包带原帮助失败reference并复用原40资产及只读converter；不再
安装依赖、不修改系统文件/旧源码/cache。相关CPU回归、真正C/C++与CUDA编译链接
预检成功后才native构建/转换；生成exe不运行，设备查询/模型/collector预算均0。
目标机尚未执行本修复，不授任何GPU资格；新输出/单metadata ZIP/失败即停，不重试。

### 7.153 定向CPU测试身份与环境一致性

d77386工具身份查询已在目标通过；91 passed/6 failed/4 skipped停止于测试共享helper
导入，未进入实际编译。仓库tests是namespace目录，原`tests.test_native_*`依赖环境中
同名package选择。外部同名regular包可独立复现相同6项错误；原回执缺实际包来源，
不得把该复现当作某服务器第三方包身份已经证明。

仅该CPU入口采用既有`test_*` helper导入，包括内部反向导入，显式PYTHONPATH
本仓库tests/code优先并保留转换gguf-py路径。独立新进程记录实际解释器/base/version、
cwd、这几个环境字段及实际helper origin/hash；错来源拒绝。不得把配置值复制为实际值，
也不全仓包化tests或配置新的全局pytest行为。同名外部包干扰的独立pytest子进程通过
全部6项原反例；actual stage1→环境门→CPU回归→编译前文件链保持，不吞ImportError。

CPU回归保留`-rs`，记录可选g++和私有源码/SDK/JSON头输入存在性。原四个skip为
可选upstream字节审计、真实SDK语法审计及两个compiled CPU替身用例；原-q日志没有
细分OR条件的缺件事实。目标机必须执行的C/C++、CUDA两项真实compile/link不属于
这些skip，必须有exit0、实际cache/compiler/output；本机替身/可选审计不能代替。

native CMake的Git现在通过已验证的固定Git路径显式传入，不依赖干净编译PATH猜测。
部署前置d77386与598 CPU来源、882 query来源各自绑定，原件hash不变，不追认失败。
相关本地107项为104 passed/3既有skip；Python3.12.7的生产入口接线验证不等目标
3.11.16复验。旧0.1/0.2 build/producer/测量语义保持，仍只允许构建/转换/身份检查，
不运行生成程序、GPU探测或native模型。新root/单ZIP/失败即停，stage2不自动启动。

### 7.154 CMake路径与原始版本合同

真实失败来源是未类型化反斜杠RC路径在`CMakeRCCompiler.cmake`中形成非法转义，
不是VS缺安装。所有CMake路径参数采用正斜杠、工具FILEPATH和目录PATH，含空格/
括号仍为单独argv；`-S/-B/--build`同样处理。只变路径表示，不变目标文件、源码字节
或hash。NUL/换行/分号/插值/引号等无法安全表示的路径拒绝，不静默改名。

实际CMake3.31.10识别MSVC为19.38.33135.0，工具此前显示19.38.33135。三个实际
CMakeLists、预检读取、native构建读取及receipt消费者仅接受这两个精确形式；原值
保留，不trim、前缀匹配或补字段伪装。SDK10.0.20348.0、固定工具字节、nvcc12.4.131
不变；Toolkit只限12.4系列，不能放行新compiler build。共同规则文件
`native/cmake/NativeBuildContract.cmake`纳入native源码身份。CUDA版本仍由实际CUDA
预检/生成的compiler文件和native输出检查验证，不从vendor子目录猜测父scope变量。

新build0.2.1须配precheck0.2.0，后者保存原始版本；旧Ninja build0.2.0只配原
precheck0.1.0及三段MSVC版本，VS build0.1.0保留。错配、未知版本、错路径/hash、
缺真实链接产物仍拒绝。转换0.1.0、stage1配置0.2.0、producer/adapter及测量合同不变。

本地使用固定真实CMake模板生成→读取、三个实际CMakeLists版本门及实际stage1
文件消费链验证；143 passed/3既有可选skip。LANGUAGES NONE不执行cl/nvcc/rc/link，
外部编译结果仅CPU替身，不冒充目标机成功。本次未运行任何生成程序/模型/CUDA/Nsight。
原34fa失败、103/4及所有Raw/合同保留；后续真实预检→native→GGUF仍需新目标回执。

唯一待审小包以前置34fa866，仍复用原固定Ninja/旧资产/只读598 CPU环境和882工具
query原件；新root/单metadata ZIP，不恢复旧cache或入口。20GiB临时空间及45–120
分钟仅后续估计，长期50GB政策与归档后清理条件不变。本轮停在本地交付审查，未授权
安排目标机执行；成功也不授GPU资格，不自动阶段2或自然配对。

### 7.155 实际CUDA接口与adapter前置编译；支线收口范围

48567aa回传的C/C++、CUDA预检均为实际compile/link成功，完整configure exit0；
build在1606.078s exit1，唯一编译错误为main.cpp调用不存在的`cudaDeviceGetUuid`。
原stub自行声明该函数，旧Host语法测试因此不能证明SDK兼容。本次改用固定Runtime
的`cudaGetDeviceProperties(&properties,device)`读取实际`properties.uuid`；mask/count/
logical ordinal、16字节UUID、PCI及错误返回门不变，仍在模型加载/测量窗口之外。
[CUDA12.4.1 Device Management](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/group__CUDART__DEVICE.html)
与[DeviceProp.uuid](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/structcudaDeviceProp.html)
给出该接口/字段。错误stub删除虚构声明，仅提供显式不完整的语法子集，不作ABI证明。

本轮第一方adapter的全部Runtime调用核对如下，固定12.4真实头文件静态签名检查覆盖：

| 调用 | 用途及边界 |
|---|---|
| `cudaGetDeviceCount(int*)`、`cudaGetDevice(int*)` | 窗外实际可见设备与当前logical device，不将编号直接解释为physical身份 |
| `cudaGetDeviceProperties(cudaDeviceProp*,int)` | 窗外查询实际UUID，保留全部16字节比较，不复制期望值 |
| `cudaDeviceGetPCIBusId(char*,int,int)` | 窗外实际PCI，按component核对 |
| `cudaGetErrorString(cudaError_t)` | 保留原错误，不将失败转换为成功 |
| `cudaRuntimeGetVersion(int*)`、`cudaDriverGetVersion(int*)` | API版本/driver能力；前者不是独立的已加载DLL字节认证 |
| `cudaStreamSynchronize(cudaStream_t)` | 五个已有backend调用点，原参数/顺序/次数保留；handle/PTDS常量不直接推断trace ID或模式 |

依据[版本接口](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/group__CUDART____VERSION.html)、
[错误接口](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/group__CUDART__ERROR.html)和
[stream接口](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/group__CUDART__STREAM.html)。
未修改固定upstream后端的CUDA调用；本核对不授予vendor全部API的S/A支持或运行资格。

顺序改为：旧身份/工具门→真实C/C++、CUDA预检→完整configure→
`native-adapter-headers`→完整backend/link→GGUF转换/内容检查。新增target编译**同一份**
main对象和observer，依赖固定llama/NVTX/CUDA真实头文件，但不依赖llama/ggml后端。
后续native-llama复用该main对象及observer库，不复制入口、不手填compiler works。
前置门最多300s，失败/缺对象/头版本冲突立刻停，不能进入昂贵后端或转换；无exe执行。

新adapter-compile0.1.0保存实际cache/compiler、源码/SDK头/两个对象长度及SHA，
build0.2.2必须引用它并核对源码hash；缺字段、执行标志、错版本/hash/来源拒绝。
旧build0.1.0/0.2.0/0.2.1显式读取及其历史判定保留，不补写旧回执。测量spec、
producer、窗口、流、原同步、registry/S/A/B及旧Formal不变；本次不是协议amendment。

本地使用NVIDIA固定Windows runtime12.4.127及nvcc12.4.131发布包的真实头文件，
只解出头文件、未安装/加载DLL或执行nvcc。runtime主头hash与封存目标SDK一致；
其他头来自对应发布包，不能称已逐字节核对全部服务器SDK。本地GCC的语法检查及
真实CMake/Ninja对象编译不等于目标MSVC14.38资格；没有运行生成程序/模型/CUDA。
新13项检查全通过；实际CPU入口152 passed/7既有或可选本地编译审计skip，后续目标
adapter门是mandatory，不能用skip或本机通过替代。详细命令/原件身份见科研进度7.155。

**支线最小研究产出**：一个固定Windows/native自然执行子域，证明Host-token完成、
身份/依赖/窗口可合法恢复，并与同窗常规baseline比较能否新增解释。保留API主导、
零Device wait、无额外信息或不确定结果；不保证更大wait，不替代PyTorch核心Formal，
不做引擎排名、并发、负载扫描或新Formal。候选起点包含自然输入准备，不能直接与旧
GPU-resident PyTorch时延横向排名。

剩余必要顺序仅三项，均非本轮执行要求：先完成目标adapter/最终link及F16转换身份；
通过后仅验证新增scheduler/backend drain、线程/stream/event/correlation/ownership桥接；
桥接充分后才另审一对自然32/2 P0/P1。任一步有具体缺件/闭包不明就停止此子域，
不反复补设施或修改完成政策求大wait。当前停止在本地修复审查；不生成新部署/采集包。
