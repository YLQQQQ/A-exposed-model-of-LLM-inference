# Gate8 controlled bridge 0.1.0

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

### 一项必须单独裁决的研究语义

是否引入**有证据的request dependency epoch**：只有完整drain完成、相关设备/context/
stream身份一致、无未决跨epoch event/外部工作时，后续request的W(s)能否排除
已被前一epoch独立完成的旧request成员？当前MC §7.2/7.3保留已完成语义前驱，
D1 projection明确不是dependency证据，不能从§3/4的drain直接推出这一例外。

推荐先审批窄epoch amendment后实现：Raw原样保留、epoch切点引用真实completion，
同request前驱及hidden progress不删；缺证据/冲突拒绝，跨epoch edge反例必须拒绝。
备选为保持现规则并显式限制可验证支持域为独立stream受控构造；不能据此宣称
一般eager模型已受支持。此处仅提案，**本提交不实现epoch、不修改W(s)**。
相应新Q0须补epoch隔离、同request已完成前驱保留、跨epoch event/外部ownership负例；
历史Gate6 PASS不撤销，新资格不自动继承。GetLastError分类需另行明确API支持规则，
本轮保持unknown，不绑入epoch的批准。

## 验证范围与下一步

tests-first：producer真实落盘→合成SQLite→独立Raw checker→Canonical/projection→
S/A/B/coverage/publication文件链。包括坏token、wait/cleanup失败、before-CUDA
身份拒绝、重复/额外sync、前窗memset、Driver表、冲突profile/plan、实文件hash。
合成REP不是合法Nsight REP，测试不会调用export或native DLL。
不把S/B吻合当独立A全资格，也不把记账差值当机制或根因。

服务器最小下一步是**另授权后部署、静态复验并编译native DLL**；本机未编译它。
随后可另授权窄受控采集核验工具接口；这仍不解除模型的epoch/API支持限制。
见[受控服务器草案](gate8_controlled_server_runbook_v0_1.md)。不得自动接模型、Q0或Gate8 PASS。
