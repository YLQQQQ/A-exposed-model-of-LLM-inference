# Batch4 memset参数取证可行性审查 0.1

## 2026-10-17增补：新B2 Prefill参数诊断实现 0.6（当前，目标机待验证）

**最小实现与本地CPU验证完成；只交付待审阶段A，不授予模型覆盖、A或COE资格。** 用户接受下文
0.5窄域方案后，本轮实现独立Engineering profile与参数消费者。0.5保留为设计时历史，旧微例
PASS、旧B2/Pilot BLOCKED、7槽NOT_RUN/0完整block及原UNKNOWN/NOT_ASSESSED均保持。

### 实际接线与版本边界

- 新声明`MEMSET-PYTORCH-PREFILL-PARAMS/0.1`、profile
  `MEMSET_PREFILL_PARAMETER_DIAGNOSTIC/0.1`、side/receipt/execution独立0.1.0；不是旧G1/Pilot
  的batch2扩容。manifest严格绑定新run/commit、完整`[2,512]`输入及mask摘要、实际两样本两token、
  三次warmup、repeat1、普通CUDART与记录器DLL实字节。旧batch版本仍不接受B2。
- [verified入口](../../exposedpath/gate8_diagnostic.py)复用原解释器、prepare→seal→model-run、
  模型inventory、设备UUID/PCI、真实软件配置及producer链。记录器**在原最终drain之前安装**，
  原成功drain后只启用预分配记录；原first Host-readable token时间戳之后关闭记录，Decode前停用。
  `.cpu()`、completion锚点、流、同步、请求边界和token-ready helper内容不改。落盘/拆除在窗外。
- [native recorder](../../scripts/native_memset_probe/prefill_recorder.cpp)仅hook已核验绝对路径的
  共享普通`cudaMemsetAsync`。一次Detours事务纳入既存同进程线程；4096预分配槽、自动call_id、
  uint64 count、指针地址别名、原value/return/LastError。命中时恰好一次原参数转发，无新CUDA
  查询/复制/同步、堆分配或磁盘I/O。别名不证明allocation生命周期；PTSZ/private不自动覆盖。
- [consumer](../../analysis/memset_prefill.py)枚举整个Prefill的目标runtime，不按旧84条或邻近时间
  配对。side↔闭合唯一NVTX domain/range↔同PID/TID/runtime严格双向唯一；实际process creation
  FILETIME另与入口started.json绑定。负返回仅复用已验`-1/-1`情况且仍要求真实完整范围。
  非零必须唯一合法MEMSET效果；零参正效果、未知效果、漏记、重入、外线程、溢出均拒绝。

### 零payload消费：独立实现，不是生产准入豁免

规则`MEMSET-ZERO-LOGICAL/0.1`仅用于这个未来新Engineering profile。保留原API墙钟/submit
类别、逻辑身份、真实提交顺序和原Canonical，不创建0ns或其他device activity。
临时验证视图仅去除已被参数证明count0的“必须有正activity”断言，再调用原局部Prefill门；
原始A输入仍含这些API预算，内部A不发布。随后必须独立满足同次drain、设备/context/native-
trace流桥、Host token、成功sync、所有真实成员/相邻FIFO边、terminal及LEGACY/PTDS必要后缀
一致。已完成历史和已完成必要成员保留；操作内D2H包含，sync提交边界之后工作不纳入。

允许的两种有限关系只是“Host零调用”或“同一隔离FIFO内空节点”；二者不得改变真实成员、
真实依赖和后续D2H terminal。零调用必须在该实际后续提交之前。pending历史、事件/graph/
跨流依赖、未知context/入口、模式相关歧义或terminal缺失仍拒绝；不声称已排除所有未记录依赖，
不授完整物理W/B。若真实B2不能证明这些条件，就停止，不扩hook或改合同追绿。

输出`parameters.json`包括原始实例参数、原API预算、效果引用、全部源hash、局部门事实及零节点
证明，成功仅称`MEMSET_PREFILL_EVIDENCE_COMPLETE_PENDING_REVIEW`。A/COE仍NOT_ASSESSED，
Request/Decode NOT_ACCEPTED。当前没有新模型trace或新可信A/COE结果。

### 本地验证与明确限制

定向新检查64项：参数/范围/覆盖反例，独立FIFO成员与terminal正反例，实际prepare→seal→profile
argv→verified producer→Canonical→参数消费文件链，阶段A/B显式分派与失败封包。运行环境
Python3.12.7；目标Python3.11.16尚待阶段A，未把本地AST或替身称为目标验证。

真实CUDA12.4头文件编译/链接与真实Detours **Host替身**转发执行已完成；本地工具链14.44/
SDK26100，目标既有14.38/SDK20348仍须实际编译验证。测试包含64位大count、原错误码/LastError、
容量溢出仍原转发、重入/外线程/错误入口、ctypes真实ABI与落盘；不运行CUDA程序。
旧路径另有14项相关检查通过（9项定向选择、5项入口检查），不是重跑全110/Q0。

整段本地演练实际运行PS5.1→控制器→头文件编译/Host Detours→64项CPU→单ZIP及CRC/hash；
Git部署/HEAD是明确替身，模型/设备/collector只在测试边界用替身。第一次深目录演练59通过/
5失败，原因为Windows路径长度，失败现场保留；改用新短路径后重跑，不修改测试期望或身份门。
最终命令、结果和回执位置见唯一科研进度7.179。未重跑旧SQLite/完整analyzer、旧54/110或Q0。

### 唯一待审交付与停止条件

增量前置以已核验微例回执的执行`002f3ae9fcc22f04356dbd22092dcddd8c63a460`绑定，
而非猜测服务器HEAD。复用固定Detours4.0.1/NVTX3.1.0/SDK12.4头文件；无安装/升级。
包索引绑定提交后实际执行/分析commit、全部新增接线实字节、输入/模型引用及历史功能token参考，
不把旧B2功能值参考解释为旧准入通过。实际包和阶段A整段命令见本地handoff交付入口。

阶段A仅部署、头文件编译链接、Host CPU检查、源码/运行库身份与新鲜空间回执；不运行模型/
CUDA程序/Nsight。阶段B必须另经真实A回执审查、绑定其精确SHA后显式启用；本轮不提供B命令。
只允许一个全新B2/512/2/warmup3/repeat1、1模型进程/1profile，无P0/Cpre/旧槽恢复。
安装/记录会扰动执行，该次只作参数/支持域诊断，不作自然性能或Pilot重复。

未来单次预算估计15分钟；profile300s、export180s（另readiness60s）、离线300s、driver900s硬
上限，无重试/替补/自动追加。启动实际输出/临时/归档卷分别检查且同卷不重复计数，2GiB预留；
历史YLQ总量null/UNKNOWN、长期50,000,000,000bytes目标未证明，不扫描ACL或自动清理。

**新B2成功**只意味着普通入口确实完整覆盖这次Prefill、参数/效果及有限局部依赖证据可审，
可以决定是否另审参数辅助COE；不自动恢复9组Pilot或发布A。**失败**则定位普通入口缺覆盖、
非零缺效果、参数/身份/范围或依赖/terminal不闭合的具体项并停止；不回填旧168次实例，
不恢复旧B2和7槽，不扩大hook/工具链。生产A/B/COE/registry、原Formal/Gate判定均未改变。

<a id="2026-10-17增补真实pytorch覆盖桥接与参数消费规则草案-05当前"></a>

## 2026-10-17增补：真实PyTorch覆盖桥接与参数消费规则草案 0.5（历史设计）

**裁决：GO，限进入一个新B2 Engineering参数诊断的最小本地实现准备；不是模型覆盖/COE准入已通过。**
参数完整后存在合法的窄域解决路径：正长度继续要求真实效果；零长度保留逻辑调用和已证依赖，
不伪造activity，并只在局部依赖闭包不受未定顺序语义影响时消除“必需正activity”这一拒绝。
若共享普通入口不能覆盖、出现非零缺效果或依赖不闭合，就在这一条路线停止，不扩hook。
本轮只审查/设计，未实现新记录器/消费者、未测试/编译、未发包或服务器命令，未运行任何GPU程序。

Material Passport：ARS experiment-agent / bounded plan；日期2026-10-17；本节DRAFT、未实施；
来源为当前源码、固定第一方接口和既有封存事实，不是新实验/新资格。当前研究设计v7.1、
实验协议v2.1与限定签署路线均不改；0.4微例PASS和旧B2/批次BLOCKED并存且含义不同。

### 0.5.1 真实调用覆盖：已有依据与尚不能证明的部分

微例已证明目标Torch目录内**共享CUDART普通导出**可被此Detours实现命中，并在一次Nsight
采集中与runtime/效果关联；目标运行库实际SHA256为
`f95273031fc5ea44cdb37e0a696a1b15b9d84a4ee977299a6f6e652ef4d790cf`，不是本地SDK归档DLL的hash。
不能由相同文件名、同版CUDA、微例成功推导PyTorch全部调用命中。

已有目标机PE原件（2026-09-27）在本轮按自身清单核对：
`torch_cuda.dll.imports.txt` SHA256 `608df902abc49982e4b3f9faa30c0c90977725324fb7fae59af86f5fd4855148`，
`c10_cuda.dll.imports.txt` SHA256 `0449388f81783840444f030227dcf11513cb129e7ff2e7867316480f9a36c51c`。
**c10_cuda导入cudart64_12.dll；两份导入表都没有cudaMemsetAsync或PTSZ直接导入；torch_cuda
另导入cuBLAS/cuBLASLt等native库。** 这既不证明缺口来自某vendor，也不证明一定是私有runtime；
动态解析、静态/私有副本及vendor内部路径尚未排除。该历史PE不冒充未来进程的实际加载事实。

固定执行链可读到：`gate8_diagnostic.model_run`核验解释器/输入/设备后，复用
[runner](../../exposedpath/runner.py)的setup→三次warmup→成功窗前drain→Prefill forward/argmax→
自然`detach().cpu().reshape(-1).tolist()`→实际Host token锚点；本轮不改该链。
保存的Transformers SDPA调用进入`torch.nn.functional.scaled_dot_product_attention`；
[PyTorch2.6 CUDABlas](https://github.com/pytorch/pytorch/blob/v2.6.0/aten/src/ATen/cuda/CUDABlas.cpp)
说明BLAS调用路径，[FillKernel](https://github.com/pytorch/pytorch/blob/v2.6.0/aten/src/ATen/native/cuda/FillKernel.cu)
使用gpu_kernel，均不能给旧168次实例指定真实callsite或count。**精确实例来源仍未知，拟用同次
动态覆盖判定，而不是继续源码猜测。** 本轮不查询旧SQLite或追索84条参数。

未来覆盖集合T预先定义为：已绑定目标进程/创建实例、原Prefill半开窗口内全部同类runtime，
包括合法数字版本后缀；另外审列PTSZ/其他入口和外线程，不能先过滤后宣布全覆盖。
T与侧记录R必须双向一一对应：run/request/phase、PID/TID、call_id、真实模块/导出、闭合唯一
NVTX domain范围、唯一完整runtime及原返回码全部一致；不是按旧rowid、次数84或最近时间配对。
PTSZ/private副本、漏记、范围跨界、重复、重入、外线程、容量溢出、未支持诊断一律BLOCKED。

### 0.5.2 从双case记录器到模型所需的最小调整（尚未实现）

1. **范围而非逐case arm。** 保留现有微例接口/角色；新增独立
   `MEMSET-PYTORCH-PREFILL-PARAMS/0.1` Engineering声明和侧记录版本，不把B2伪装旧G1/Pilot。
   复用verified模型入口与prepare/seal/输入/实际batch/token门，新源码/运行库/DLL另绑定新执行身份。
2. **窗口通知。** 在原成功drain之后、forward之前启用记录；首个Host token完成后停用，Decode
   前关闭，异常finally关闭。开始/完成仍取原锚点，不把NVTX或hook返回当completion。
   仅`before_copy`不够：它漏掉forward阶段调用。暖机/窗外调用原样转发、不误报“未arm”；
   Prefill内不允许不记录。只新增诊断Host/NVTX工作，不新增CUDA查询、同步、复制或切流。
3. **多调用但有上限。** 预分配4096记录及消息槽，自动单调uint64 call_id，不假定实例数；
   每个真实命中自动记录count/value/native stream/原return、调用线程与run内pointer别名。
   别名不能继续用“非空全部等于1”，也不记录内存内容。边界内无分配/磁盘I/O；溢出标错、
   仍恰好一次原转发，不覆写旧槽或重试。uint64 count/原LastError等复用已验ABI/转发纪律。
4. **安装与线程安全。** 仅同一绝对路径/实际模块普通导出，不改全API hook或第二subscriber。
   不能把微例的`DetourUpdateThread(current)`直接当多线程安全证明；安装/拆除在无在途调用的
   窗外，按[Detours事务接口](https://github.com/microsoft/Detours/wiki/Using-Detours)一次性纳入
   本进程可能受影响的既存线程，失败即停，不做常驻线程监控/权限升级。边界内外线程调用
   必须留故障事实并拒绝，不能静默略过；不得以只记录主线程掩盖其他线程的runtime。
5. **落盘/消费。** 原Host完成后保存完整侧记录、装载/attach/detach状态、原始NVTX返回值及
   捕获/漏记计数；真实导出范围仍是记录证明。Canonical不改写，新增参数证据sidecar引用
   原API/source hash；所有目标API统一审查。独立新profile消费后才能调用原局部投影/COE，
   不调用旧失败批次入口、不伪造`coe_pilot.process`成功。当前双caseconsumer不能直接用于模型。

### 0.5.3 参数消费草案：MEMSET-ZERO-LOGICAL/0.1-DRAFT

这是一项**仅未来新Engineering profile的准入增量草案，尚未批准生效/编码**，不是旧A/B或COE
公式改版。依据[CUDA12.4.1 memset规范](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/group__CUDART__MEMORY.html)
的count字节范围及[stream completion](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/group__CUDART__STREAM.html)，
count0只证明请求的字节写入范围为空，成功不证明工作完成/无内部命令/无顺序影响。

|实例证据|拟保留的事实与处置|不能推导|
|---|---|---|
|count=0、成功、完整实例覆盖|逻辑submit调用节点z、原API墙钟、原ordinal/native stream/context证据；没有设备记录就不创建device activity，状态ZERO_PAYLOAD_LOGICAL_ONLY；须再满足下面闭包条件|非阻塞、没有队列/顺序作用、全capture零丢失、自动COE通过|
|count>0、成功、唯一合法MEMSET效果|保留实际bytes/value/device/context/stream及correlation桥，沿原活动/依赖规则；首版只支持已验单MEMSET，value按字节语义核对，原int值不丢|最终token正确即可补关联；多效果求和/替代kernel自动获资格|
|count>0但缺效果，或count/身份/关联未知|具体NONZERO_EFFECT_MISSING或PARAMETER/PAIR/SCOPE原因，BLOCKED|填零、改non-submit/Host、借相邻活动；不能再用同配置重采追绿|

**零长度的有限可证明条件：**

- z保持API身份和真实同线程提交顺序；`host_call_order`不是GPU依赖边。已有流FIFO、event边、
  成功drain闭合的历史、已完成必要前缀以及所有后续真实成员全部保留；不删先行工作。
- native handle不直接当trace ID。必须复用同次成功drain/自然sync的物理scope、实际设备/主线程
  stream记录以及完整已支持调用序列，唯一约束z所在context/stream；仅阶段前后handle相同、
  或表里只看到一个context不足。context/device切换、未知入口或生命周期不明时继续BLOCKED。
- 首版限定已批准的**主线程、同一自然流、成功drain后的局部Prefill、无新incoming event/跨流/
  graph依赖**。所有正活动/正提交均完整映射且由实际copy/成功sync及Host token完成界定。
  完整必要成员截止于该sync捕获的提交边界，含copy内部D2H，不截在copy入口。
- 不宣称z实际入队或被跳过。分别保留“仅Host零长度调用”与“可能承担同流顺序的逻辑空操作”
  的未定关系；并沿既有LEGACY/PTDS审查。此处只比较文档流序语义和这两种零payload表示
  所构成的有限候选关系，不要求排除所有未观测内部机制。只有在**这些候选关系均不改变
  真实活动成员、真实成员间必要依赖及被观测terminal证据**时，才可消去z的几何贡献，继续局部投影。
  同一隔离FIFO内两种关系都保留相同先行活动是成立实例；不能仅比较A数值相同或守恒。
- 若z可能携入别流工作、成为无法被后续已观测必要效果界定的完成前沿，或终端/closure依赖
  未定关系，拒绝；不能以sync返回为z造GPU终止时间，不能给z造零ns activity或B barrier。
  已观测的正效果与count0矛盾也拒绝，未知效果不填零。

逻辑节点的设备区间是**不存在的观测对象**，不是“测得0ns”。A仍计原CUDA submit API墙钟；
COE只与被恢复为必要成员的真实GPU区间相交。内部未分离时间/空隙不改成纯等待，单sync B
保持原义且不因本草案获得完整物理资格。baseline也保留原API count/sum/union，将“参数证明
零payload”与“未解决缺映射”分栏，不能把两者一起改为mapped或零成本。

### 0.5.4 预先固定的独立预期/反例（设计，未运行）

|手工构造|独立预期|
|---|---|
|同S提交K，z(count0)，L，D2H，成功sync(S)；K已在sync前完成|W中的真实成员仍K/L/D2H；z保留逻辑序号，无activity；已完成K不删除，terminal为后续已证D2H；零关系投影不改真实依赖|
|别流Q工作可经legacy默认流空操作z影响后续S，缺少该关系证明|两种关系可能改变W，BLOCKED，即使count0、返回成功、最终token正确|
|z位于未映射context/stream，或只知stage前后handle0|BLOCKED，不复制相邻调用scope|
|z是末端可能完成节点，没有后续已观测效果约束|terminal未闭合，BLOCKED，不用sync.end造z终点|
|count0却关联正bytes MEMSET或未支持效果|冲突/BLOCKED；不按零参数过滤证据|
|count64→同次唯一64-byte MEMSET/正确scope，全部其他门完整|按原必要活动规则继续；不由读值代替映射|
|count64成功但无效果，或bytes/value/scope冲突|BLOCKED；这会否定“该实例仅因零payload缺activity”的解释|
|侧记录少/多一条、重复runtime、PTSZ/private未覆盖、外线程或第4097次命中|覆盖/容量明确失败，原调用仍转发；不得靠已有84条清单选择实例或扩大hook|
|零值合法但未知诊断、失败drain、pending历史或token冲突|独立质量门仍拒绝，不因为参数齐全而放行|

### 0.5.5 唯一后续建议及决策价值（待批准实现，非执行授权）

若继续，只实现上述最小调整与CPU文件链负例，再审一个**新B2 Engineering参数诊断**：现有
Windows/4090、固定1.5B/FP16/eager/SDPA、相同512输入复制两份、每样本输出2、warmup3/
repeat1、自然Host-readable路径；1新模型进程/1profile，无P0/Cpre/其他负载/旧槽续跑。
安装在窗外，记录仅主请求Prefill；模型仍按原定义完成Decode，Decode不准入也不追参数。
reuse未改的解释器/模型/输入/device检查，role与新源码精确绑定，不沿用旧seal。
这不是预先承诺旧B2的scope可复用：所需context/stream桥和有限关系不变性必须由新run事实
与已支持语义逐项建立；缺少任何一项，即使全部count为0也仍BLOCKED。

一次运行要同时回答两项有可判别后果的问题，而非为获得更多样本：
**共享入口是否完整覆盖本次Prefill？缺映射实例究竟是零payload、合法正效果，还是非零缺效果？**
双向覆盖及新草案所有前提均成立，才可另作参数辅助局部准入审查；普通入口未命中/部分命中、
非零缺效果、context/default依赖或terminal不闭合任一成立，就停止该路径，无重试、补样、
hook private/PTSZ、PyTorch重编或工具链更换。不要求新实例重现84次，不回填旧B2。

本地实现仍受原1～2工作日上限约束，先复用已验ABI/Detours/微例与既有S能力，只补模型
范围通知、多调用覆盖/容量、逻辑节点投影和实际文件链的独立CPU反例；不重跑完整Q0/110项。
未来目标预算建议：profile硬上限300s（含setup/warmup）、export180s、离线300s，整个流程
预留15分钟是估计，不是成功承诺；临时预留2GiB，预计新增保留20～100MiB（不含既有权重/
环境），不生成巨型domain。实际fresh空间待后续静态回执，长期YLQ<50,000,000,000bytes
仍未证明；本轮不盘点、清理或假定当前checkout。固定单次/硬失败即停，无自动追加。

**当前停点：覆盖审查和规则/反例草案完成，可继续这一窄域本地实现；真实PyTorch覆盖与
新规则资格未完成。** 若不接受上述窄域逻辑节点消费条件，则仅得到参数不能关闭准入，
不应为此制作采集包。旧B2/Pilot BLOCKED、7槽NOT_RUN/0完整block、旧A/B/COE、Formal/
UNKNOWN/历史Gate和全部原件均保持；0.4微例结论不升级。

<a id="2026-10-16增补nvtx返回值适配与封存微例离线裁决-04当前"></a>

## 2026-10-16增补：NVTX返回值适配与封存微例离线裁决 0.4（历史微例审查）

**限定0/64-byte同次微例Engineering复核PASS；原attempt仍BLOCKED，旧B2/批次仍BLOCKED。**
这是对已采原件的消费者0.1.1离线修复，不是新采集、模型覆盖或COE资格。下文0.3保留交付时状态。
没有服务器操作、部署、微例重采、CUDA/Nsight执行或新包。

### 根因与最小规则

原消费者把`push_level>=0 && pop_level==push_level`当作NVTX记录必要条件；两次实际返回均
`-1/-1`，却已有完整NVTX导出范围，因此在设备效果检查前误拒绝。
[NVTX接口文档](https://nvidia.github.io/NVTX/doxygen/group___m_a_r_k_e_r_s___a_n_d___r_a_n_g_e_s.html)
描述层级及负值错误约定，但[CUDA12.4.1 Profiler §5.1 Return Values](https://docs.nvidia.com/cuda/archive/12.4.1/profiler-users-guide/index.html#nvtx-api-overview)
明确提示返回值随工具实现变化，不宜用于条件判断；
[2023年官方论坛讨论](https://forums.developer.nvidia.com/t/nvtxrangepusha-and-nvtxrangepop-returns-2/255993)
也有Nsight返回-1而正确记录范围的实例。这不证明所有负值成功，不能据此忽略丢范围。

消费者/微型导出provider升级为**0.1.1**，side仍按0.1.0读取。只增加已观察的`-1/-1`
返回组合兼容，原始值写入新结果、标记`UNAVAILABLE_LEVEL_NOT_RECORDING_PROOF`，不改0或成功码；
其他未知负值/混合组合仍拒绝。无论返回正负，都必须核对：同进程唯一DomainCreate(event75)
实物及名称`EP_MEMSET_MICRO`、正确非默认domainId、闭合event59范围、run/call/PID/TID、
外层scope包含关系、固定调用/验证次序、唯一完整runtime动态范围和原返回码。
随后全部原设备/context/stream/correlation/bytes/value、功能参考及diagnostic门继续执行。
不是按NVTX消息推断domain，也不是用时间邻近配对。旧0.1.0 raw_excerpt缺少这些证明字段，
不能当新provider输入；从同一原SQLite重新提取，旧结果保留原版本，不补造字段。
native记录器、producer、launcher、采集argv及生产S/A/B/COE/registry均未改。

### 封存输入与独立复核

原ZIP `memset_micro_002f3ae9fcc2_once.zip`：68,580 bytes，SHA256
`29e4413ad7c2895d261718c54fd301266c01a94e647fe2d265475865f22ab3b8`。
CRC、27唯一安全成员/26项清单全部通过；manifest SHA256
`c177dcdd8caf4fb448074cf648c03f0e7734dd8f5c1ae48e7460a5b2be67bb32`。
原执行/原分析002f3ae9fcc22f04356dbd22092dcddd8c63a460，13源实字节↔对应Git blob、
delivery/包清单、已审A receipt/build/runtime引用全部一致，profile/export均exit0/无超时。
本次修复分析版本0.1.1及实际分析commit/源码hash另立绑定，不沿用旧分析身份。

|case / count|实际NVTX / domain|唯一runtime / corr|设备效果与验证|窄域判断|
|---|---|---|---|---|
|1 / 0|row2 / EP_MEMSET_MICRO，返回-1/-1|row8 / 126|未见关联效果；成功sync corr127 / physical row2，context1/stream7；读回64字节0x3c|零长度参数事实成立，顺序作用仍NOT_PROVEN|
|2 / 64|row3 / 同domain，返回-1/-1|row11 / 129|MEMSET row2，64bytes/value123，同context1/stream7；成功sync corr130 / physical row3；读回64字节0x7b|非零设备效果明确映射|

两次PID70312/TID73452、native stream0；不把native0等同trace7或全局默认流模式。
DomainCreate row1与外层row4均实际存在；setup成功drain为runtime row7，先于外层scope。
14条diagnostic全部severity1，既有规则无阻塞；不因此声称全会话无丢失，UNKNOWN保持。
独立Raw SQL按固定scope/call标签、同线程动态范围和文档correlation恢复以上表，不调用候选函数
生成预期成员；与完整消费者输出交叉核对。没有按最长API、相邻活动或最终读值补关联。

### 验证、产物与停止点

新增[回归](../../tests/test_memset_nvtx_recording.py)先复现14失败/2通过，原件失败原因为
`NVTX_RECORDING`；修复后实际命令：

```text
python -m pytest -q -p no:cacheprovider tests/test_memset_nvtx_recording.py tests/test_memset_same_capture.py --basetemp .local/micro_nvtx_final --junitxml .local/diagnostics/memset_micro_nvtx_reanalysis_v0_1/final.xml --tb=short -ra
```

**54 passed / 0 failed / 0 skipped，1.50s**，本地Python3.12.7；仅消费者CPU回归，不重跑native
构建、110项、完整Q0或任何实验。缺/重复范围、错domain/进程/线程/run、未闭合、API越界、
范围交叠、未知负值、效果缺失及真实SQLite错domain/endGlobalTid反例均按具体原因拒绝；
原正返回路径保留，fixture仅增加真实provider要求的domain/scope字段，不删负例。
py_compile、diff检查通过。复核新目录`memset_micro_nvtx_reanalysis_v0_1/analysis_0_1_1`包含
review/source_hashes/raw_excerpt、独立adjudication/calls及提交后analysis_binding；输入副本与原ZIP
前后逐项hash不变。原Raw/side/原derived/原BLOCKED receipt全保留，不覆盖报告。

**本次仅关闭这个微例的消费者误拒绝。** 可确认普通共享CUDART入口在这一次Nsight观测中完成
两次参数/NVTX/runtime/效果取证，但不能外推PyTorch/cuBLAS内部覆盖、零长度无顺序作用、
COE/A准入或自然性能。旧B2/批次BLOCKED、7槽NOT_RUN/0完整block、Gate13限定PASS及
UNKNOWN/NOT_ASSESSED不变。无需服务器补执行，不发新包、不恢复剩余槽；任何模型覆盖/零字节
消费政策仍未获本微例授权。本轮用户DOCX与大型原件均不纳入提交。

## 2026-10-16增补：最小同次微例实现与待审交付 0.3（历史交付状态）

**本地实现与CPU审查完成；目标机阶段A/B均NOT_RUN。** 用户已接受0.2接口级GO，
本轮只落实普通动态runtime入口的0/64-byte微例，不接模型、不恢复d6957de剩余7槽，
不改生产A/B、COE、registry、已签署协议或旧证据。下面0.2是设计来源，不再是当前实现状态；
不是因为本地通过就授予新实例/旧B2的准入。

### 0.3.1 实际接线与版本身份

- [记录器](../../scripts/native_memset_probe/recorder.cpp)、[真实SDK接口](../../scripts/native_memset_probe/recorder.h)
  固定Detours v4.0.1 / `e4bfd6b03e50de46b47abfbd1e46b384f0c5f833`，
  NVTX v3.1.0 / `bc282655dadb9288505f419c5b79d2ed3f1b4dfd`，CUDA12.4.127 runtime头与12.4.131 CRT头。
  依赖归档SHA与逐文件清单放入唯一交付，不在服务器下载浮动依赖或升级环境。
- [微例](../../scripts/native_memset_probe/micro.cpp)无CUDART/static runtime导入或链接库；
  未来B仅由绝对路径加载目标Torch所用`cudart64_12.dll`，校验实际模块路径/导出所属模块，
  查实际runtime API版本12040、单个mask3设备UUID/PCI。仅ordinary `cudaMemsetAsync`被审，
  PTSZ/static/private副本没有覆盖声明。微例通过也不能证明PyTorch内部走这个地址。
- 包装内只有一次原参数trampoline转发，保留原CUDA返回码及Win32线程LastError；
  `size_t`按uint64保存，含`2^63+7`的CPU实转发检查，无float/signed截断。
  预分配记录，无包装内磁盘I/O、CUDA查询/同步/复制。重入、未arm/溢出明确标错。
  实际PID/TID、进程创建FILETIME、run/call_id、native stream、导出地址与事务状态保留。
- 每次调用由专用domain的闭合NVTX线程范围包住；[离线消费者](../../analysis/memset_same_capture.py)
  用同PID/TID/entry的唯一完整动态包围关系双向配对，**不是最近时间**。
  侧记录、NVTX范围、runtime和效果均单独校验；readback不能代替效果映射。
  `side / exported-provider / review / delivery / receipt`均显式0.1.0版本。

本轮补齐的是**Nsight导出命名空间依据**，不改旧Native CUPTI字段解释：保存的目标2026.2
`AnalysisGuide.html`（SHA256 `bdcf574189e7eb687d4dc7c52bcebacae9c700c5a93a9e3aed8ff674960cbb11`）
明确把MEMSET.correlationId外键指向`CUPTI_ACTIVITY_KIND_RUNTIME(correlationId)`，该API表
eventClass 0/1区分runtime/driver。新微例只用该provider关系及进程内唯一correlation，
不把原生`CUpti_ActivityMemset4`的driver编号无条件当runtime编号。0.2要求的“已证明的Nsight关系”
据此落实；旧B2确无效果，仍无桥可补。目标归档网页不能直接读取，依据是已保存且复核hash的
安装文档，公开[AnalysisGuide](https://docs.nvidia.com/nsight-systems/AnalysisGuide/index.html)仅作可访问参照。

### 0.3.2 独立预期、真实验证及其界限

固定顺序不依赖实际活动长短：64-byte buffer setup为0x3c，成功device drain在测试scope外；
case1原参数count0/value0x7b，验证读回全0x3c；case2 count64/value0x7b，读回全0x7b。
两case各自既定成功stream sync与D2H是**微例功能参考**，位于被测调用范围之外，
不向模型增加同步。普通native handle0经每次独立成功stream sync的物理记录绑定trace
device/context/stream，**不证明全局LEGACY/PTDS**。正64必须唯一关联同scope的64-byte MEMSET；
非零无效果、错scope、重复/未知关联停止。count0只报告零长度实参；顺序作用NOT_PROVEN、
COE/A准入NOT_ASSESSED、dropped UNKNOWN，不实施零字节消费豁免。

独立手写fixture/SQLite文件链与实际Host DLL检查见
[配对测试](../../tests/test_memset_same_capture.py)、
[交付测试](../../tests/test_memset_micro_delivery.py)、
[native测试](../../tests/test_memset_micro_native.py)。
先验证缺失、重复、wrong entry/stream/identity、失败返回、重入、count溢出、未知诊断、
错误sync类型、缺drain和缺效果的拒绝；不能用更早的错误掩盖预期负例。
MEMSET之外的相关KERNEL/MEMCPY也读入，避免过滤后误称零效果；缺诊断表不等于空诊断。
同类官方warning沿用既有Gate9处置规则，不新建宽松规则。

本地实际命令（显式`MEMSET_MICRO_CPU_CONFIG`指向本地MSVC/SDK/固定依赖）：

```text
python -m pytest -q -p no:cacheprovider tests/test_memset_same_capture.py tests/test_memset_micro_delivery.py tests/test_memset_micro_native.py --basetemp .local/memset_micro_release --junitxml .local/diagnostics/memset_same_capture_v0_1/release.xml --tb=short -ra
```

最终 **54 passed / 0 failed / 0 skipped，10.93s**。本地Python3.12.7、MSVC19.44.35217、
SDK10.0.26100.0；目标Python3.11.16/MSVC19.38.33135/SDK10.0.20348.0仍待A。
真实编译/链接了完整微例与生产记录DLL，未执行二者；PE导入检查无CUDART/nvcuda/CUPTI。
真实运行的是Host函数替身DLL＋**真实Detours**，验证原参数恰好一次、返回码/LastError、
detach、错误入口和重入；NVTX在这组CPU测试中是明确替身，不是目标Nsight收集证据。
官方CUDART PE文件只读查询得到`6.14.11.12040`，不是虚构的toolkit semver；没有加载CUDA DLL。

另在全新本地目录完成**真实PS5.1→默认A→编译/HostCPU→回执/封包→已审A SHA→显式B失败**演练：
A exit0、内层54通过，B的采集器替身exit17后立即BLOCKED并封存原退出码，未生成side/SQLite、
未进入export或任何微例。Git部署/HEAD/clean和Nsight程序是明确CPU替身，不能冒称真实部署/共存。
证据位于忽略目录`memset_same_capture_v0_1/entry_rehearsal_release/audit.json`及原始日志/单ZIP。
本地未跑完整110项、完整Q0或旧模型分析；不新增长期监控或追索旧PID。

### 0.3.3 唯一交付及停止点

[默认PS入口](../../scripts/run_memset_micro.ps1)与[控制器](../../scripts/memset_micro.py)
仅A部署/构建/CPU检查，B必须显式开关＋真实已审A receipt SHA。新执行=分析commit在实现提交后
由[包生成器](../../scripts/package_memset_micro.py)精确绑定，避免hash自引用；服务器前置仅复用
封存d6957de真实receipt，旧失败包不解锁。交付包括bundle、固定依赖/SDK头、来源/源码/工具链
清单；不附新模型/新环境。A只编译链接与CPU替身，不运行微例、GPU查询或Nsight。
新runtime文件实际hash/PE导出/二进制hash必须先审A，再由B复核同一字节，不能由运行时hash自认证。

资源仅查询新输出、TEMP/TMP（可选TMPDIR）及归档卷的fresh空闲、同卷去重/可写；每卷预留
0.25GiB。本次无历史遍历/ACL/清理；长期目标<50,000,000,000 bytes，历史总量null/UNKNOWN。
预计A数分钟、含B/导出审查预留15分钟，仅估计；B单profile120s硬上限、export另120s，
失败/缺桥/共存/重入/诊断冲突即停，禁止重试/替补/模型；timeout后代UNKNOWN时拒绝自动封包。
所有新输出/ZIP不覆盖；旧B2、7槽NOT_RUN、0完整block及旧Gate/Raw/UNKNOWN保持。
**下一项只有协调审查这一个交付，然后由用户选择执行A；当前没有B采集授权或模型续跑授权。**

## 2026-10-16增补：同次Nsight实例取证的有界裁决 0.2

**裁决：GO，仅指有依据进入一个窄域同进程记录器的最小实现评审与受控微例设计；不是目标机验证通过，也不是模型采集或COE准入授权。** 选用下面路径b，不增加CUPTI subscriber。路径a在固定版本的已核验接口内不足。若b的唯一调用绑定或与Nsight共存不能在微例闭合，停止此路线，不扩大hook范围、换工具链或制作模型包。

本节保留0.2时点的接口裁决与设计来源，当前实现状态见0.3；下文2026-10-12的独立CUPTI方案/CPU原型保留为历史，不是本次选定路径。当前依据是[本批失败审查§13](completion_operation_batch_prefill_review_v0_1.md#13-d6957de候选pilot失败收口b2-prefill缺提交效果不续剩余槽位2026-10-16)：d6957de的B1完成、B2阻塞、7槽未运行、0完整block；B2 Prefill/Decode各84次缺效果。复用已完成Raw/Canonical和替代关联核对，本轮不重新查询SQLite。新实例不能补旧参数，旧B2/批次保持BLOCKED。

### 0.2.1 参数事实不等于资格

共同必要事实是新run/进程创建实例、PID/TID、实际被调用模块/入口、`size_t count`、native stream、原始返回码和同次Nsight API身份；还需原request/phase、设备/context/stream生命周期、drain、依赖闭包与完成证据。

|同次证据|能证明什么|仍不能自动证明什么|
|---|---|---|
|count=0且成功，实参/调用绑定完整|请求写入0字节；可以标记ZERO_LENGTH_ARGUMENT_OBSERVED|无内部设备操作、无顺序影响、全局无漏记录或A/COE合格|
|count>0且成功，有唯一合法设备效果桥，bytes/value/scope相符|该实例的非零效果可纳入既有提交/依赖恢复审查|必要前驱齐全、默认流条件、terminal与整窗质量均通过|
|count>0但效果缺失，或参数/桥接不明|具体缺口可被区分和定位|不能补零、改成non-submit/Host或借相邻kernel；仍BLOCKED|

[CUDA12.4.1 memory API](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/group__CUDART__MEMORY.html)定义count为字节数、写入前count字节；没有给出“count=0必然不建立任何顺序关系”的独立保证。因此零参数不能删除先行成员、事件边或默认流依赖，不能据此更改submit门。若未来拟允许“有实参但无activity”的零长度实例，仍须另审窄域零字节操作的消费规则及反例；本节不实施或预批准该语义。返回成功也不等于异步工作已完成；[API synchronization behavior](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/api-sync-behavior.html)不支持把调用墙钟解释为纯等待。

### 0.2.2 仅比较两条接口路径

**a．固定Nsight自有接口：本轮NO-GO。** 保存的2026.2.1安装UserGuide（SHA256 `5b100930126f3a3a819f13dd8335efc0bc2cd7f8bf0207a7063d57acb4c33e7c`）L763–779把`cuda-memory-usage`定义为内存使用观测、`cuda-trace-all-apis`定义为API覆盖；backtrace提供调用栈，不提供count。L6109起的NVTX payload能力能记录调用者显式传入的数据，并不自动取得第三方CUDA实参。现有已审schema没有这些API参数。固定[2026.2官方归档链接](https://archive.docs.nvidia.com/nsight-systems/2026.2/UserGuide/index.html)本轮不可读取，版本判断来自本地安装原件，不借滚动新版网页授予目标build能力。结论仅为“已核验接口不足”，不声称REP内部永无参数；不再搜索私有REP或增加采样。

**b．同进程native入口拦截＋专用NVTX调用范围：源码/接口级GO，目标兼容性NOT_RUN。**

- 候选插入点是实际已加载CUDA runtime模块的`cudaMemsetAsync`机器码入口，不是Python `.zero_()`包装或另一份runtime。匹配12.4.127 SDK的`cuda_runtime_api.h:7538`声明为`cudaError_t CUDARTAPI (void*, int, size_t, cudaStream_t)`；保留x64宽度/调用约定。头文件L210另有PTSZ重定向，**不得把_ptsz、私有静态runtime或其他模块默认为同一入口**；首版未绑定的入口一律未覆盖。
- 具体机制为[Microsoft Detours v4.0.1](https://github.com/microsoft/Detours/releases/tag/v4.0.1)，release绑定commit `e4bfd6b03e50de46b47abfbd1e46b384f0c5f833`。其[固定源码样例](https://github.com/microsoft/Detours/blob/e4bfd6b03e50de46b47abfbd1e46b384f0c5f833/samples/simple/simple.cpp)展示`DetourAttach`、trampoline调用原函数并原样返回结果；[使用说明](https://github.com/microsoft/Detours/wiki/Using-Detours)要求签名/调用约定一致。仅加载独立参数DLL，不调用`cuptiSubscribe`、不启用第二套activity、不借用Nsight私有CUPTI DLL。
- 在模型窗外完成库身份、地址和事务检查；包装体仅分配预留记录槽，复制count/value/stream与run内目标指针别名，push唯一调用NVTX范围，**原参数转发原trampoline恰好一次**，保存返回码并pop。不得新增CUDA查询、同步、D2H、模型行为或原request边界；不在包装内做磁盘I/O/模型日志，溢出或异常保留失败。保存原返回码/Windows线程错误状态，不清除CUDA错误或伪造成功。DLL/所指模块/导出地址身份、实际加载实例与事务结果均需留痕；加载、调用覆盖未在目标机验证。
- NVTX使用已有基础线程范围接口`nvtxDomainRangePushEx/Pop`，专用domain、带run nonce的消息及uint64 call_id；不依赖新扩展payload功能。[NVIDIA接口定义](https://nvidia.github.io/NVTX/doxygen/group___m_a_r_k_e_r_s___a_n_d___r_a_n_g_e_s.html)保证的是同线程嵌套范围，**不是CUDA correlation自动桥**。参数/返回记录在窗外落盘并绑定源码、DLL和REP/SQLite身份；不保存完整环境、调用参数全集或用户数据。

### 0.2.3 同次绑定及不能越过的边界

拟验证的证据链：`run/进程实例/TID/call_id侧记录 → 同call_id闭合NVTX线程范围 → 该动态范围内唯一原函数runtime记录 → Nsight合法correlation/driver桥 → device effect`。

这不是最近时间配对：范围由受审包装明确包住**一次原函数调用**；必须在同一Nsight时钟、PID/TID、函数/事件类别内完整包含该runtime，且一对一、无重复、无重入歧义，返回码与侧记录一致。无runtime、两个候选、范围丢失/交叉或不能证明一次原转发均拒绝，不设距离容差或回退到相邻编号。NVTX的call_id不冒充CUPTI correlation；缺少实际效果时，范围本身不能补造效果。

非零效果继续使用已验证的Nsight关联合同；匹配SDK `CUpti_ActivityMemset4`的correlation是**driver API命名空间**（`cupti_activity.h:2247–2252`），不能无条件等同runtime编号。有可见、唯一的嵌套driver桥或其他已证明的Nsight关系才使用；仅bytes、重叠或最终内存内容相同不足以补桥。native stream handle不能直接等于trace stream ID，尤其handle0不能判全局模式。零长度无activity时context/stream仍需独立现有生命周期与调用scope桥；缺失则停，不从相邻调用复制。

**覆盖/共存风险是微例的硬门，不是已消除的假设。** [Detours FAQ](https://github.com/microsoft/Detours/wiki/FAQ#why-dont-i-see-any-calls-to-my-detour-of-malloc)明确指出hook另一份函数不能覆盖目标私有实现。未来被审scope中每条目标Nsight runtime都必须唯一匹配记录器，记录器也必须反向匹配；未绑定的静态/动态副本、PTSZ变体保留未知，不升级成全API hook。安装UserGuide L1089–1092的`--injection-use-detours`仅描述Nsight进程注入，**不是自有API hook与Nsight共存保证**。不得修改Nsight的hook或以关闭Nsight绕过冲突；若记录丢失/重复或API/诊断冲突，路线停止。此附加NVTX/Host工作有时延扰动，所得运行不能当自然P0性能或无扰动基准。

### 0.2.4 唯一微例与停止预算（仅设计，未实现/未授权执行）

一个新native x64进程、一条同版本Nsight CUDA+NVTX profile；同Windows/4090/driver555.99/CUDA12.4栈，使用实际锁定runtime，不改工具链。与PyTorch同runtime文件身份必须另核；直接调用微例**不证明cuBLAS等第三方内部路径已覆盖**。只审已绑定的`cudaMemsetAsync`入口；不加载模型、不追加模型槽。

1. Setup在case窗外：选择既定GPU，单context、实际默认流入口、64-byte合法device buffer，置0x3c并成功drain；记录身份。测试计划预先给定两个不同call_id，不从analyzer生成答案。
2. case Z：原始参数`(buffer,0x7b,0,stream)`，原样转发一次；随后在**被测调用范围之外**执行既定成功sync/D2H验证，64字节须仍为0x3c。必须记录count0、实际stream与原始成功返回，并一对一找到Nsight runtime。零次/零bytes activity均按实物保留，不能预设缺activity=零顺序影响；出现正bytes矛盾或未知桥则停。
3. case N：同buffer/流调用`(buffer,0x7b,64,stream)`，随后范围外相同验证，64字节须全为0x7b。必须取得count64/成功、唯一runtime及合法64-byte设备效果桥、正确device/context/stream。最终读值是独立功能参考，不替代correlation；效果未映射即失败，即使读值正确。

这是一次微例内两个预定case，不是两个模型进程；验证用sync/读取属于微例oracle，**不复制进模型完成路径**。任何构建/加载/入口身份、NVTX/runtime覆盖、参数/return/效果或诊断冲突即停止；零值本身不是失败，必需记录缺失也不能判成功。结果只决定是否值得审查记录器的有限模型应用：通过不能认证旧B2，不能证明所有模型调用经过该地址，更不能授予COE或零字节准入。后续新模型如再出现任何未覆盖/非零缺效果，仍拒绝，不临场补hook/加采。

投入上限建议：后续若批准，最小本地原型及CPU ABI/转发/文件链审查封顶1～2工作日，**这是止损预算而非完成承诺**；目标机仅1进程/1profile、硬超时120s、含构建/审查预留15分钟/临时0.25GiB估计，未知空间拒绝，无重试/模型/额外样本。微例失败或到本地投入上限仍不能建立唯一调用桥即NO-GO，保留失败事实并结束，不滚动扩建。本轮没有代码、测试、包或服务器命令。

### 0.2.5 本轮证据与未验证项

本轮只读安装说明/匹配SDK/公开接口，未运行旧SQL、CUDA DLL、Nsight或任何实验。新核对`cuda_runtime_api.h` SHA256 `fb3c938ef38d3a9be88e111688ced12ea9b96dd62e48da8c955409e867e1db08`；UserGuide与`cupti_activity.h`的既有hash复核一致（后者`3796fb651d9983e407f2d007d8089f53a218e96b167a5452ab23908176b18b6e`）。官方Detours/NVTX/CUDA资料只证明接口存在与所述功能；目标加载、共存、命中率和效果桥均NOT_RUN。没有“取得参数即可放行”的规则改变；COE/生产A/B/registry/旧Formal、UNKNOWN/NOT_ASSESSED和Gate13限定PASS均不变。唯一建议下一步是**审查该微例的最小实现是否值得投入**，不是恢复剩余7槽或重采旧配置。

---

## 2026-10-12历史方案（以下原文保留，不作为当前执行计划）

2026-10-12；Engineering设计和CPU原型，不是collector资格、服务器交付或采集授权。[旧实例审查](batch_load_memset_effect_review_v0_1.md)已结束：原B4仍BLOCKED，旧84次调用不再追索。Gate13限定PASS、Gate14 NOT_RUN保持。

## 明确结论

**有公开SDK依据的窄域候选是独立CUPTI callback＋activity诊断，不能假设与现Nsight并行。** 匹配CUDA12.4的Windows头文件已核验，CPU原型验证了参数复制和拒绝关联歧义；目标进程的实际DLL加载、订阅及activity路径仍未验证。因此本轮不交付模型/重采入口、不修改A准入；下面的有界步骤须先审查，再实现和验证其native运行部分。若要求“原Nsight profile不变且直接增添CUPTI subscriber”，该方式停止。

新增记录用于识别**新调用实例**的count、stream、return和设备效果，不是自然性能结果；也不能补旧84次参数或恢复原B4资格。独立CUPTI数据不是现Nsight Canonical合同的自动替代品，不启动通用collector、全Q0或新A/B资格工程。

## 固定版本与第一方依据

目标平台已有回执：Windows/x64、Python3.11.16、torch2.6.0+cu124、CUDA12.4、原4090/driver555.99、Nsight2026.2.1.210-262137639646v0。模型、固定512-token输入、batch4、每样本输出2、FP16/eager/SDPA、warmup3/repeat1和Host-readable完成路径均沿用原[batch合同](batch_load_engineering_plan_v0_1.md)。不升级平台或改allocator/同步/边界。

已保存的目标安装UserGuide：SHA256 `5b100930126f3a3a819f13dd8335efc0bc2cd7f8bf0207a7063d57acb4c33e7c`。`cuda-memory-usage`是内存使用观测，`cuda-trace-all-apis`是API覆盖，backtrace是栈信息；这些说明没有给出当前build能导出每次memset count/native参数的肯定接口。已有SQLite/API schema也无此实参。**仅结论“当前已核验接口不足”，不是工具绝不支持。** 不为此开启CPU采样或重复REP搜索。

从[NVIDIA CUDA12.4.1官方组件索引](https://developer.download.nvidia.com/compute/cuda/redist/redistrib_12.4.1.json)取得并校验Windows组件，未安装、未执行其中的CUDA工具或DLL：

|组件|版本|ZIP bytes|ZIP SHA256|
|---|---|---:|---|
|cuda_cupti|12.4.127|14921079|6ad8df634d60e4bc96cf6914af71a5708f6460a25a39d0183780c6bdebfa60c7|
|cuda_cudart|12.4.127|2474721|6a1c32e68ee1a95ca17334691ff9ad1ffe7f352c24a083d55e4c96b8063b2bcb|
|cuda_nvcc（仅CRT头文件依赖）|12.4.131|63662970|3b14cf8dd9dda4a3b1a9682270d46eef775f018e17650187a8a448a06111f2b8|

此SDK的CUPTI API版本为22；`cupti64_2024.1.1.dll`为4576840 bytes、FileVersion2024.1.1.0、SHA256 `560a36596b6c6db6ecb44bbdc1b9d3bbf34965e919d13e7285f4d1c3542916ce`。这只是已下载候选，**未在目标机加载或查询版本**。目标Nsight安装自带`cupti64_129.dll`为4579976 bytes、FileVersion2025.2.1.0、SHA256 `47b244aafd892c52bc9f6e954b49c8f94e01186a73152e6d9aaf1fbc5d2aa8d8`；库存信息不证明其实际加载、公共ABI版本或可作为第三方client依赖，禁止借用/混装。

匹配SDK中的可复查定义（并非拿较新文档推断目标ABI）：

- `generated_cuda_runtime_api_meta.h:1988–1993`：`cudaMemsetAsync_v3020_params`包含devPtr、value、size_t count及cudaStream_t stream。count是字节数；x64不得经signed-int64/浮点截断。[CUDA12.4.1 API定义](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/group__CUDART__MEMORY.html)。
- `cupti_callbacks.h`的CallbackData/订阅说明：参数只在callback内有效；ENTRY复制参数，EXIT复制返回码，`correlationData`绑定同次进入/退出。runtime/driver callback各自匹配相应API activity correlation，命名空间不得混用。只允许单subscriber；Nsight启动时也可能返回`CUPTI_ERROR_MULTIPLE_SUBSCRIBERS_NOT_SUPPORTED`，必须停止，不取消他人订阅或换较新多subscriber版本。
- `cupti_activity.h:2194–2302`的Memset4：bytes、context/device/stream、时间及**driver API correlation**。没有MEMCPY结构中的runtimeCorrelationId桥接，不能把原runtime编号直接借给MEMSET。start=end=0表示时间不可得，不是零时长证明。
- `cuptiGetTimestamp`提供activity共同时间域；`cuptiGetContextId`、`cuptiGetDeviceId`、`cuptiGetStreamIdEx`提供显式映射，后者要求正确perThreadStream语义。native handle0、logical cuda:0、trace stream0不等价；若默认流映射不能证明，保留UNKNOWN/拒绝，不回填全局LEGACY/PTDS。

匹配归档内完整说明/头文件与本地审计存于忽略的诊断目录；不提交vendor文件、二进制或机器路径。

## 最小运行设计（尚无可启动入口）

**候选native client仅服务本任务；不同时运行Nsight、torch.profiler或另一CUPTI subscriber。** 在独立目标Python进程中、模型加载/首次CUDA初始化之前，显式初始化client。使用绝对路径加载锁定DLL，不搜索PATH；保存候选SHA、实际模块路径/文件身份/hash、实际`cuptiGetVersion`及每项enable/subscribe返回值。已加载不匹配CUPTI、API不为22、subscriber冲突或初始化失败立即停，不尝试另一版本/自动重试。调用SDK查询本身不是CPU-only。

只启用所需runtime/driver/resource callback和API/MEMSET/KERNEL/MEMCPY activity。全driver回调只用于同线程实际嵌套桥接，不记录用户数据/环境/无关参数。callback内禁止CUDA runtime/driver调用；仅用文档允许的CUPTI查询、复制小记录，窗外落盘；callback异常、队列溢出或flush失败保留拒绝，不让记录器改变同步语义。量化新增记录数量/时间，但不将诊断时延当自然性能。

同次记录最少包括run/进程创建实例/TID、全局序号、独立call_id、ENTRY/EXIT、domain/cbid/name、context/native stream、count/value、run内pointer别名、返回码及CUPTI clock。参数指针不能留到EXIT再读。request/phase绑定来自原producer的显式scope生命周期接口并保留原ledger引用，不能仅按相邻时间猜ownership；接线不移动原completion/NVTX或增加同步。资源映射保留查询参数、返回码、同线程/生命周期；设备必须对应既定UUID/PCI，不按编号相同推断。

runtime ENTRY → 实际嵌套driver ENTRY/EXIT → runtime EXIT → 对应API activity → driver-correlation设备activity为唯一允许的关联链。无嵌套记录、缺context/stream映射、correlation重复、跨run/进程或未能界定的诊断均拒绝；不借邻近kernel。若库内部不走可观测driver桥接，记录参数事实但设备效果保持未知。kernel替代路径仅保存明确桥接事实，不能用kernel时长或假bytes冒充MEMSET覆盖。

三种关键结果必须分开：

|证据|允许输出|不能输出|
|---|---|---|
|同次ENTRY实际count=0、EXIT成功、身份/参数完整|ZERO_LENGTH_ARGUMENT_OBSERVED|全部GPU效果为零、无顺序影响、A自动通过|
|count>0且有唯一同次显式MEMSET映射、bytes/流/设备一致|NONZERO_DEVICE_EFFECT_MAPPED|全capture无丢失或自然性能结论|
|count>0但无明确设备效果|NONZERO_EFFECT_MISSING，BLOCKED|补零、non-submit/Host归类或借成员|

参数/返回码/关联未知继续拒绝；零参数与实际正bytes效果矛盾、多MEMSET仅靠bytes相加、未支持kernel关联、时间/生命周期冲突均单独阻塞。UNKNOWN保持UNKNOWN；事实确认和测量资格分开，不以返回成功或未见warning放行。

## 一次受控验证与有界预算

后续若批准并完成native client，只允许以下**顺序门**，不是重新跑原四组：

1. 一个不加载模型的tiny CUDA进程，锁定相同DLL、身份和client。初始化与必要drain在测试scope外；固定显式nonblocking流和64-byte buffer。独立预期：先置为0x3c，调用count=0后Host读取仍为0x3c；再调用count=64/value=0x7b后64字节均为0x7b。实际参数/返回码必须分别为0/64及成功；非零须有明确driver桥接的64-byte MEMSET和正确资源映射。测试中允许其既定验证sync/D2H，绝不向模型request添加这些调用。CPU原型不能替代此目标栈验证。
2. 只有上述全部通过，才考虑**最多一个新B4模型进程**，固定512×4/每样本2输出/warmup3/repeat1，原input/model/GPU/backend及完成路径不变，无P0/B1或同批补采。在目标scope中逐call输出三类事实；本进程用独立CUPTI，不产生“同Nsight qualified A”。新实例数量可与旧84线索描述性比较，但不能认证旧实例或假定同样参数。

本轮不执行、不打包；先协调审查此证据路径是否值得。未来预算建议：tiny最多120s、模型最多300s、总15min/临时2GiB硬上限，均为待审估计；固定两进程上限、无自动重试/换provider/扩点/补采。加载/订阅/微例失败就在模型前终止；新B4参数仍未知、非零缺效果或冲突时到此结束，不追加监控或同配置采集。原长期存储<50GB政策沿用，完整归档核验后才另审可重建副本清理，不在本轮删除。

即使此参数诊断成功，若要发布新B4可信A，仍须另审其实际输入桥接与现有科学消费者适用性；本方案不承诺通过，也不把新provider自动纳入冻结协议。无需重做完整旧Q0；不启用D/Signature、Pilot或Gate14。

## 本轮CPU原型与验证边界

[纯CPU参数证据原型](../../scripts/memset_parameter_prototype.py)版本`memset-parameter-prototype/0.1.0`，显式只接受`CPU_SYNTHETIC`/`ENGINEERING_PARAMETER_FORENSICS`。它没有采集CLI、torch/CUDA/CUPTI调用或S/A入口。真实数据不能靠改role送入科学链。只实现单MEMSET的窄域关联，不用求和补齐多活动，不支持的路径拒绝。

[native结构体复制原型](../../scripts/prototypes/memset_callback_copy.cpp)使用匹配SDK真实定义，ENTRY复制count/value/native stream，EXIT复制return；CPU替身改变原参数后，副本必须保持。它是普通EXE而非注入DLL，未链接CUDA/CUPTI。实际PE导入表只有Windows/CRT，源码没有动态加载/vendor API调用；没有通过打印“0 CUDA调用”来代替检查。

[独立测试](../../tests/test_memset_parameter_prototype.py)包含零/非零/缺效果、同次ENTRY/EXIT、driver桥接、跨run/PID、correlation跨线程复用、native0错流、缺参数/return、失败/部分记录、零时间未知、多活动求和错误及实际JSON文件往返。六个native用例含x64大count `2^63+7`，不加载GPU库。未设置匹配SDK和MSVC时native测试显式skip，不能称验证完成。本次显式配置执行后的最终结果见科研进度7.138；不重复全量/Q0或旧实物分析。

本地MSVC为19.44.35217（不是目标机19.38），本地头文件编译不是服务器加载/回调资格。编译依赖/编码/无关activity头文件padding导致的初稿失败已保留，改为匹配12.4 CRT依赖、UTF-8和最小callback头文件；未改vendor定义或屏蔽生产错误。

**停止点：本地可行性/CPU接线可审查；目标加载及tiny CUDA验证未运行，新B4不获授权，旧B4保持BLOCKED。** 目前没有可安全直接部署的采集包；不把SDK存在等同真实回调成功，不制作未经验证的重采入口。
