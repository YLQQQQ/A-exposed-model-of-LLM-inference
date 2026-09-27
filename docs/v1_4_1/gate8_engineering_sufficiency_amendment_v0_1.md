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

当前仅第1段实现。第2～4段尚未完成，不存在真实profile准入成功入口；本文件批准
质量门方向，不把sidecar生成成功等同质量门通过。原物理S/B与旧Q0读取路径不变。
