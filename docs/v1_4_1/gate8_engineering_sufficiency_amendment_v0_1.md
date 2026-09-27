# Target-scope Engineering sufficiency amendment 0.1

2026-09-27。用户已明确接受限定依据；profile
`TARGET_SCOPE_ENGINEERING_SUFFICIENCY/0.1`。本版只定义Engineering质量门，
不是Protocol Freeze、Q0资格或Gate8 PASS，不追认已有诊断包。

## 依据与限制

支持域：已驻留模型/输入、单请求执行、固定eager及实际backend配置、无用户并发、
无显式IPC/event跨源依赖；实际drain及D1三点定义窗口。固定版本/身份/输入是可验证事实，
未记录incoming依赖的残余不可检测风险是支持域假设，分字段记录，不称零丢失证明。
仅新manifest在执行前显式选择本profile并记录假设的attempt可进入新入口。
旧证据只供诊断；不得事后补manifest、将真实trace标synthetic或默认选择本profile。

逐窗口核对producer、Raw、projection的hash/identity/clock；成功drain只约束前缀，
不作为未来无提交的证明。枚举全部已观察blocking API、submit/correlation及物理scope，
包含内部sync。单实际FIFO与限定后缀的默认流条件等价仅为A交集证明，不重写物理W/B。
有其它相关stream、event、资源/身份/时钟冲突或未知影响范围即拒绝；不泛化到混合
默认handle、并发执行或通用默认流解释器。

## 诊断与unknown

新sidecar `exposedpath-diagnostic-scope/0.1.0`保留源SQLite hash、DIAGNOSTIC_EVENT
rowid、原timestamp/timestampType/source/severity/text/globalPid、可解出的PID及目标
关联（TARGET_PROCESS/OTHER_PROCESS/UNKNOWN）。旧Canonical diagnostic不改。
`timestamp_raw`仅保留原值；未解释timestampType时不命名为ns，也不据此裁剪request。
源必须为封存SQLite主文件：非空WAL/journal拒绝，不checkpoint；immutable只读、前后
hash核对。reader重新派生并逐项比对，不能手填处置冒充原始事实。
globalPid缺失、负系统sentinel或不是明确的进程粒度编码时PID=null/UNKNOWN，不能
用消息文字或其它行猜测。外部PID仅是来源关系，不自动等于OUT_OF_SCOPE或可豁免。
新门必须逐条绑定处置与依据；目标相关或影响范围不明错误拒绝，局部缺口须有原记录
边界和可复核原因。absence/exit0/integrity-ok不令dropped_records_status从UNKNOWN变零。

旧严格合成request_scope路径及其零unknown条件不改。新真实路径不要求零unknown或
任意百分比：局部有界缺口进unattributed，绝不转Host/residual；全窗影响不明拒绝
可信归属。保守记账输出不等于机制解释，B/D/Signature不自动启用。

## 实现与验证分段

1. 带原始引用的diagnostic范围adapter；确定性SQLite/producer夹具验证缺字段、
   PID冲突、系统scope、未知PID、source hash与不覆盖；不将OTHER_PROCESS当豁免。
2. 新profile显式声明、receipt及目标scope质量门；绑定实际producer文件链，不接受
   四个bool替代证据；旧profile/旧包拒绝。逐sync/局部unknown/错误诊断负例。
3. 新A-only编排在两种受限默认流假设下核相同交集；保留物理S/B，拒绝不等价情况，
   复用既有互斥union算法；D/Signature关闭。目标scope声明不授予新Q0。
4. 两API只做有官方依据的有限对齐；无法确定的部分保留unknown，不扩全API工程。

每段先失败测试、最小实现、定向回归及进度记录；实际目标机资格与新采集仍未授权。

## 0.1实现合同（限定Engineering，不是新Q0资格）

`exposedpath.gate8_engineering_contract`定义预执行声明；新prepare显式传
`--engineering-attention-backend sdpa`或`eager`才加入manifest。旧默认不变。
声明包含profile、配置backend、PRE_EXECUTION及三项支持域假设：无用户并发、
无显式IPC/event依赖、无未记录incoming依赖。最后一项明确不是可观测事实。
runner现有模型setup observer在warmup/request之前核对实际配置backend/use_cache/model_type，
不强制改模型backend，不匹配则保留INCOMPLETE并停止。固定eager/batch1及原诊断32/2、
warmup1/repeat1不变；不修改runner及其加载/同步策略。

`exposedpath-engineering-execution/0.1.0`携带原manifest和producer receipt hash、
run/pass/attempt/PID、原声明、实际配置观察与完成状态。目标进程另存CUDA probe、
Canonical用preflight和runner源码字节；这些不能用prepare进程PID代替。
输入仍经input-receipt/0.3.0逐文件hash/size、producer、export、设备adapter校验。
旧manifest无声明时不得补写后接入；旧Qwen包不追认。

新`exposedpath-engineering-a-scope/0.1.0`入口为
`python -m exposedpath_v141.gate8_engineering_scope --input-receipt <receipt>
--execution-receipt <execution> --output-dir <new-directory>`。
只读原文件、派生至新目录；中断仅保留partial staging，不发布结果。reader核对全部
派生文件集合/hash，再由源receipt、projection和诊断重算，不能仅改结果摘要。

每个request分别核对三边界、成功drain、setup先于drain、stage及native handle观察、
完整global PID（不能只比较数字PID）、设备/context/clock、全部可见API/physical sync、
submission correlation及逐活动归属。缺sync物理映射、失败API、跨线程、其它相关流、
event/graph路径、资源变化、未知API作用或无法界定的诊断影响拒绝对应request的三窗口。
另一独立request的已核结果可保留，run状态仍BLOCKED。身份/边界文件损坏或Canonical拒绝
则不发布完成目录。所有已恢复成员必须在相应sync返回前完成，不以request内结束代替。

在明确支持域下，仅将成功drain之前已完成前缀从条件性A交集移除；不删除Raw或物理S/B。
后缀只允许同request/TID/context的单实际NULL FIFO，分别按LEGACY与PER_THREAD调用既有
`recover_wait_set`，closure必须COMPLETE、无reason、非空frontier唯一。复用既有A互斥
union记账，三窗口结果逐项相同才可发布。未标记的内部sync以原API/physical记录和已
验证projection参与交集，不伪造sync_origin/callsite/ordinal；条件性输入不作为物理S输出。
原S及B继续按旧函数生成并保留无效状态；新结果不能送旧AB/Derived reader冒充资格。

诊断规则当前仅绑定Nsight `2026.2.1.210[-262137639646v0]`，每条保留原rowid及处置。
已知启动/停止、注入、软件trace模式及正计数等明确通知只标INFORMATION_ONLY，
绝不等于零丢失。目标0事件计数与实际边界冲突时拒绝；未知通知、任何warning（含
其它PID）仍为IMPACT_UNBOUNDED，无按消息模糊匹配的warning豁免。
本实现**没有**任意缺记录/任意warning的局部化证书入口；没有证据界定影响时宁可拒绝。

## 两API的有限处理与边界

[CUDA12.4.1 cuKernelGetFunction](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-driver-api/group__CUDA__LIBRARY.html)
定义返回function handle；[cudaStreamIsCapturing](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/group__CUDART__STREAM.html)
定义查询capture状态。只在成功返回、原API区间/身份完整、无相联activity或physical sync
的条件下，将这两项的**分类缺口**界定在原调用区间；不声称调用永不阻塞，也不把它们
新分类为CUDA non-submit。旧registry不改，A原样给出unattributed，原引用及区间单列
BOUNDED_API_CLASSIFICATION_GAP。其它未知API可能影响后续依赖，拒绝而非照搬此规则。
这不是将缺失activity界定到一个API区间，不支持一般丢记录修复或百分比放行。

`A_SCOPE_ENGINEERING_ONLY`仅代表限定依据下的条件性记账；整体measurement_validity仍
NOT_ASSESSED、dropped UNKNOWN、新Q0/Gate8 NOT_RUN、D/Signature禁用。本地合成trace与
CPU模型替身的实际producer文件链测试不等于Nsight目标平台验证。现存Qwen包的外PID
warning影响范围仍未证明；新门会拒绝，不能通过重跑同一配置来假设问题消失。
