# Gate8 controlled bridge 0.1.0

> 历史 construction 说明。当前新执行候选为 [0.2.0](gate8_controlled_launch_v0_2.md)：
> 直接检查 launch 返回值。旧 0.1 trace 缺 GetLastError 仍 BLOCKED，不适用新 API 集合。
> 7.38当前动作仅为下方共享stream裁决稿0.2；0.2受控采集及f5edc64离线修复已审计。
> 本文旧“部署/采集下一步”保留为历史，不是当前服务器执行指令。

2026-09-26；Engineering，实现说明与待授权服务器草案，不是新Q0资格。
承接 Route A quality amendment 0.1.0；Gate7历史PASS，Gate8 NOT_RUN。

7.29兼容修复：服务器24f58f8的native构建在cudaDeviceGetUuid未定义处失败。
改用已有`q0/cuda/exposedpath_q0.cu`的Runtime方式：
`cudaGetDeviceProperties(&properties, 0)`取得`properties.uuid.bytes`，仍复制16字节；
失败返回、logical device0、PCI查询及Python UUID比对不变。这不是改为physical index。
依据[CUDA12.4.1 Device API](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/group__CUDART__DEVICE.html)
和[cudaDeviceProp.uuid](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/structcudaDeviceProp.html)。
源合同回归不替代目标nvcc编译；服务器恢复只构建，不运行GPU。

## 支持域与文件合同

仅 `CONTROLLED-D2H-REQUEST/0.1.0`：单进程单线程，两个request，各两个int token
（11/12、21/22）；一个独立stream warmup。三个nonblocking stream同时创建，
两个request各用一个、全部保留至cleanup，防止stream ID复用；同request两token
的已完成前驱保留。不是模型、G1/N1或Pass0/Pass1性能对照，不作开销claim。

原生源 `scripts/gate8_controlled_token.cu`：kernel写int → async D2H到pinned host
→ stream completion → CPU读值 → D1 token-ready point。读取后验token；错误停止。
request start前有device drain，cleanup不进入request。NVTX point的观测延迟仍按
D1诊断处理，不能宣称零误差。Python host clock只是诊断，窗口来自trace原生clock。

`gate8_controlled_cli prepare`静态固定clean commit、producer/native/library hash、
目标physical/mask/UUID/PCI、输入和manifest；`run --execute-controlled`才加载CUDA。
启动前复核hash/commit/mask；初始化后用CUDA实际UUID/PCI与preflight比对。
producer生成逐pass/request ledger、host boundary、operation ledger及receipt。
execution receipt记录warmup/cleanup及其**自报**return value；外层collection receipt
另记真实Nsight argv/exit、REP与execution hash。原始server路径仅是产物内容，
拷贝后按hash联结，不能把本地路径与原server argv字符串直接比较。

无循环hash：plan引用静态输入；execution引用plan和producer；collection引用
execution/REP；input receipt引用Raw/SQLite/export和producer；派生索引引用这些来源。
所有输出必须是新目录；失败保留partial但不promotion为成功。禁止改输入。

新增版本：package0.3.3；controlled plan/execution/collection/operations/raw-check
均0.1.0；带controlled proof的文件链0.3.0、分析报告0.4.0。旧0.1/0.2文件链读取
与旧A/B/Derived路径保留；S/A/B/Derived公式及schema未改变。

## 独立Raw检查，而非手填完整性旗标

`gate8_controlled_raw.py`不导入Canonical/S/A/B；按明确construction验证每个API、
kernel、D2H、physical sync与原始NVTX引用，调用既有独立q0_oracle计算B timing。
wait set预期依次2/4/2/4，terminal均为对应D2H；与实际S集合、terminal及B逐项对照。
检查前窗同流活动、目标窗口全部API/physical sync、memset与未知Driver调用；
重复/额外/缺失或未知变体均停止，不按时间重叠推断依赖。

当前适配已观察的Nsight混合Runtime表，用ENUM_NSYS_EVENT_CLASS区分Runtime/Driver，
不把表名当API层。另有非空Driver表时显式要求新adapter，不能静默漏读。
DtoH由ENUM_CUDA_MEMCPY_OPER名称确定，非假设固定数字。
DIAGNOSTIC_EVENT存在记录则本窄构造保守停止待定位；不是断言每条warning都影响窗口。
没有该表、无记录、exit0和SQLite integrity均不证明零丢失；始终UNKNOWN/null。

file-backed proof每次计算重查hash和来源；拒绝任意flag代替证据。输出
`CONTROLLED_CALCULATION_ONLY`/`CONTROLLED_ENGINEERING_DIAGNOSTIC_ONLY`，
measurement validity NOT_ASSESSED、Q0/Gate8 NOT_RUN；合成测试明确synthetic。

## 已证实的限制，不扩大冻结语义

1. `cudaGetLastError`是native安全检查，但不在冻结A分类registry。合成实文件链
   每request两个10ns调用形成20ns unattributed、每phase10ns；全部4个B有效。
   这是可定位的API支持缺口，不因名字断言“不影响研究”，不删除检查或改成Host。
   若目标CLI API subset未采到它，Raw checker停止；不自行改变profile。
   该构造不是完全受支持的低unknown正例资格；第一批独立正例仍检查具体A五类和0unknown。
2. 真实模型复用同stream的多request：两个request均有GPU记录时，第二个触发
   INVOCATION_BLEED；各用独立stream才通过。`test_gate8_request_stream_scope.py`
   保留两种实文件负/正例。不能把模型改用新stream只为绕过该问题。

### 共享stream裁决稿 0.2：保留物理前缀，只审查closed-prior ownership准入

2026-09-26 / 进度7.38；**PROPOSED_NOT_APPROVED，不是生效amendment或实现**。
本节修正7.28/7.37提案中的“旧request从W(s)排除”方向；历史提案保存在Git，
不能再把其中`W={新活动}`作为独立oracle。当前代码与冻结合同均未修改。

**冲突与推荐层次。** MC §4.1规定窗前drain，§7.2/7.3规定完整语义前缀且
已完成成员不删除；现`sync_semantics.ownership_supported`只接受同invocation，
共享stream第二request的旧前驱因此产生`INVOCATION_BLEED`。
drain完成不意味着原stream的物理顺序消失。推荐只在新版S的ownership准入层
识别“来源明确、已被有证据drain关闭的前一request”，**保留它的原owner和物理
W(s)成员身份**；不在Canonical/projection删记录或造边，也不将旧工作改标为当前request。
这是显式validity/ownership例外，不能由已有drain条款自动推出，须独立批准。
“前一request”指W内**所有已闭合历史owner**，不只紧邻request。capture开始之前或
未标记的setup/warmup不能凭drain补造owner、活动或hidden；保留为证据范围缺口，
不足以恢复物理前缀时不发布合格S/B。是否可保留有证据的局部A仍按Route A判断，
不能因为历史不在窗口内就自动认定其影响已界定。

A仍按目标request/phase窗口裁剪同一W(s)，保留互斥union规则；窗前完成的旧成员
对当前A_wait贡献为0。B仍为physical-sync provenance，hidden可含旧request进度，
不得把整个B隐藏量解释为当前request的隐藏工作。新版输出须逐activity保留
原invocation/role、closed-prior关系及证据引用，而非只写phase数组；旧schema/读取
行为不变。没有显式消费此新身份的Derived/Signature不得据此放行，现全B门保留。

新版本字段设计需明确：`cross_request_dependency`单独表示W含不同request owner；
既有`cross_phase_dependency`仍用于**同invocation**的origin/owner phase比较，不能把
旧request的decode当成当前request的decode。`activity_origin_phases`继续是W真实
origin phase标签的去重列表（保留null），`terminal_origin_phase`仍取真实terminal标签；
这些标签不携带request身份，须同时读取新逐activity来源，不靠prefill/decode同名合并owner。
序列化提案例如：`{"activity_id":"X","origin_request_id":"r0","origin_repeat_id":0,"origin_role":"measured","origin_phase":"decode","relation_to_sync":"closed_prior_request","drain_ref":"raw:drain-0"}`。
若sync属r1/prefill且其同request成员全属prefill，则新cross-request=true、cross-phase=false，
phase摘要仍可为[decode,prefill]；terminal若属r1/prefill则terminal_origin_phase=prefill。
以上须由显式新schema定义并测试，不向旧版本字段静默塞入新解释；完整run/pass/source
身份由来源引用校验，示例不是完整schema。

**最小证据合同（设计，非现有字段已齐备）。**

1. Producer逐pass ledger/receipt记录现有drain的operation ID、前/后request身份、
   成功/异常、process/thread、logical device及稳定GPU映射；共享manifest不放单repeat。
   非同步NVTX范围仅用于将该operation匹配到真实Runtime/Driver completion调用。
2. Canonical绑定输入hash、Raw table/record引用、API family/调用区间和同一trace clock、
   device/context及stream lifetime。device drain不得冒充仅同编号stream的完成证明。
   raw调用返回与producer成功回执相互核验；缺失、冲突、多候选或只有marker均拒绝。
3. 必须证明旧成员已提交且在drain completion前完成，drain return不晚于新request起点；
   仅时间早于窗口不足以证明关闭。前一request及相关warmup/setup必须有可追溯owner/role，
   未归属历史不能批量改为closed-prior。目标scope内晚到的旧owner提交仍为冲突。
4. 检查相关event/default-stream传递边、pending工作和外部ownership；未决跨边界依赖、
   外部/并发提交或无法界定的缺证据使对应窗口不具可信归属资格。已解析的跨边界边
   不删除，保留原依赖和owner；不能只凭“没有warning”断言没有边。
   handle重用须证明lifetime generation，或持续存活且未重用；数字相同不等于同一stream。
5. 证据范围是目标request及必要依赖，不恢复全capture认证要求；collector UNKNOWN保留。
   可界定局部失败按Route A保留unattributed，影响范围不明则拒绝对应窗口claim。

CUDA12.4.1将`cudaDeviceSynchronize`描述为等待此前请求的任务完成，并可能返回先前
异步任务的错误；它不是后续无提交或无记录丢失的认证。
依据：[NVIDIA Device API](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/group__CUDART__DEVICE.html)。
这里对ownership准入的建议是本项目提案，不是NVIDIA提供的分析规则。

**独立手算及负例（ns；尚未实施/执行新测试）。** 以下数值只针对指定sync区间，
不填造完整request的Host/API分类；假定该例其余身份、submission与terminal证据明确。

| 例 | 构造与独立预期 |
|---|---|
| 同request已完成前驱 | X[32,35)、Y[40,50)，sync[45,60)，无其他前驱；W={X,Y}，terminal Y；hidden8/exposed5/tail10；该sync内A_wait5/residual10 |
| 已关闭旧request | X属旧request[0,20)，drain于25完成，新request始于30，Y[40,50)，sync[45,60)；当前实现拒绝；提案证据齐全才准入W={X,Y}，terminal Y；hidden25/exposed5/tail10，原owner不同；当前sync内A_wait5/residual10，旧X对当前A为0 |
| 三request共享stream | r0的X[0,20)、r1的Y[40,50)，分别有25/55完成的drain；r2始于60，Z[70,80)，sync[75,90)；前两owner均可核验时W={X,Y,Z}，terminal Z，hidden35/exposed5/tail10，当前sync内A_wait5/residual10；不可只保留紧邻r1 |
| 跨边界event未解析/外部提交 | 即使有drain也不通过准入；保留候选和原因。仅局部sync受影响则该[45,60)为15ns unattributed、B无有效数值；无法界定传播则整受影响窗口拒绝可信claim |
| 缺drain/仅marker/错误clock或scope | 不建立closed-prior，不能按旧活动end较小放行；保持invalid/ambiguous及相应unattributed，不输出机制结论 |
| stream handle复用 | 无lifetime证据不连同流边、不建立准入；已证明销毁/新建不同generation则不得仅按相同数字把旧X并入新stream W |

同request正例检验hidden不被pending过滤删除；跨request正例检验**物理集合不截断**、
A局部化且B来源不混淆。独立预期不由S算法生成；真正资格仍需受影响目标栈证据。
B hidden可随可观察历史增加；不同capture起点/初始化/warmup历史的跨run数值不能
直接作为“当前request隐藏能力”对照。本提案不增加裁剪版B指标；必要比较须固定并
披露历史范围，否则只解释单次physical sync，不能据此作信息增益结论。

**实际runner可行性。** `exposedpath/runner.py::run_one_invocation`在计时和request
marker之前已有`torch.cuda.synchronize()`，Pass0/1均经过它；本提案首先绑定既有调用，
不新增drain或换stream。现`run_gate8_requests_to_files`的pass/host边界receipt尚未
承载该drain的上述闭合证据，warmup也没有测量request边界集合；受控native的固定
source proof不能自动移植到torch。还需核对目标模型的实际API/线程/context范围。
如果只能通过新增同步取得证据，那将改变执行行为与开销，须另行决定，不能隐含实施。
新增非同步标记也有观测延迟/开销，需保持Pass0/1操作一致并诊断，而非宣称零扰动。

**Q0最小影响。** 历史Gate6的submission、同request已完成进度、stream/event/default
闭包、terminal和A/B公式结论保留；仅适用原版本/栈，不直接授新profile资格。
新版本需要上述五类（含三request扩展）独立预期的文件链回归，覆盖身份/clock/hash/失败传播；复用现有
oracle的集合、terminal与B算术，不调用S生成答案。真实补证首先只针对新增的共享流
两request和可匹配drain路径；可复用历史用例的部分必须列接口映射，不默认全矩阵重采。
事件/external/handle未验证的路径不纳入新支持声明，不能用窄正例覆盖它们。

**唯一当前裁决：是否批准上述“保留W(s)完整物理前缀的closed-prior ownership例外”
及其显式版本/来源字段设计，再tests-first实现？** 推荐批准；收益是让连续复用stream
的request可验证记账，而不牺牲hidden progress定义。风险是闭合证据不足或误承认旧owner；
以上负例和拒绝条件是必要约束。备选是维持现规则，仅声明独立stream受控支持域，
暂不称一般eager模型受支持。当前无代码/资格/采集授权扩展，Derived发布另行收口。

## 验证范围与下一步

tests-first：producer真实落盘→合成SQLite→独立Raw checker→Canonical/projection→
S/A/B/coverage/publication文件链。包括坏token、wait/cleanup失败、before-CUDA
身份拒绝、重复/额外sync、前窗memset、Driver表、冲突profile/plan、实文件hash。
合成REP不是合法Nsight REP，测试不会调用export或native DLL。
不把S/B吻合当独立A全资格，也不把记账差值当机制或根因。

历史7.28下一步曾为部署/静态复验/编译native及另授权受控采集；这条路径已执行并有
后续7.37原件审计，不再是待办，旧[服务器草案](gate8_controlled_server_runbook_v0_1.md)
仅供追溯。当前下一步是本节一次语义裁决后本地tests-first，不操作服务器。
不得自动接模型、Q0或Gate8 PASS。
