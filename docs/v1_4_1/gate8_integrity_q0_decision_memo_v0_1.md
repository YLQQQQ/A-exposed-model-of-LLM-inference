# Gate8 完整性可行性与新版 Q0 决策备忘录 v0.1

> **历史调查与资格矩阵。** 本文统一全capture肯定证明、厂商询证和默认全部real-case
> 重采顺序已由用户批准的[RouteA amendment](gate8_route_a_quality_amendment_v0_1.md)
> 替代，不再作为当前执行指令。UNKNOWN保留；按具体接口影响复用历史证据。
> 当前受控原件及最小剩余工作见[执行计划7.37](../superpowers/plans/2026-09-25-gate8-minimal-execution-plan.md)。

## 决策与下一项最小动作

**7.26当前覆盖：** B安装资料已回传并审查；本轮调查收口仍无充分来源，不等于工具绝不支持。下一项仅用户审阅[厂商询证草稿](gate8_nsys_vendor_inquiry_v0_1.md)，未发送，不重复执行下方安装指令。Q0矩阵及资格前置保持有效；UNKNOWN继续阻塞。下方B是7.25历史决策。

**结论 B：需要一次目标安装内容的只读取证；现有材料不足以形成 A（充分证明），尚不能断言工具绝不支持。** 由用户服务器协调窗口执行附录命令，仅读取安装文件并回传输出；主窗口核对版本、字段说明及生命周期。不要部署160ad1be，不运行任何Nsight命令、模型或CUDA微程序。

继续条件：得到可绑定 **2026.2.1实际build、collector组件、CUDA/NVTX各通道、目标PID、完整capture interval、最终flush及所有counter读取/重置区间** 的肯定证明来源。只有字段名或零值不够。若安装材料仍没有该说明，只进行一次聚焦厂商询证；答复否定或仍无法确认则停在“当前支持方式无法证明”，保持UNKNOWN，提交§4替代路线裁决。不再重复搜索同一SQLite/网页，也不以再跑模型碰运气。

## Material Passport

- Origin：ExposedPath research protocol + ARS experiment-agent，plan模式；2026-09-25。
- 实现基线：`160ad1be95cb49384e92f81e5ce9c6c4eab13ebe`；package 0.3.1、adapter 0.2.0、A/B与Derived 0.3。本文仅计划与只读审计，资格 `UNVERIFIED/NOT_RUN`。
- 权威：研究设计v7.1（A闭合不是正确性证明、执行顺序与Q0硬门）；实验协议v2.1 Pre-Pilot §3.3；Measurement Contract0.2；D1/D2及时间表示amendment。不是Protocol Freeze，不改变冻结公式。
- Gate6/7历史PASS保持；Gate8 NOT_RUN。历史输入不改写、不追认。无本轮测试/采集成绩；160ad1be的80定向、1116/5 CPU回归仅为此前本地实现证据。

## 1. 本轮直接核验的证据与范围

历史唯一Gate7 PASS `smoke_20260924T084657Z`，来源/定位见[closeout](gate7_closeout_v0_1.md)及私有本地索引。读取完整SQLite（immutable/read-only），复核REP文件身份，不调用REP解码器、GUI或export；不声称已检查REP全部内部未导出字段。

- REP：948603 bytes，SHA256 `7d47d8f38a2069c816a8573b78d52c4932fbdd022013d532b5c1c23e78b6fa19`。
- SQLite：2568192 bytes，SHA256 `005cf068bff99c36585a91343d8841d12bb2cad41a94bdc9bc1478045691877c`；本轮查询前后相同。46张表，69条DIAGNOSTIC_EVENT；所有列名未见drop/lost/loss计数。**列名检索无命中不是不存在其他接口的证明。**
- collector版本日志：2026.2.1.210-262137639646v0；profile stdout为收集/生成REP进度，stderr空；export stderr为进度。postprocess receipt只证明导出执行及REP→SQLite lineage。

| 记录/字段、定位 | 生命周期及可证明范围 | 不能证明什么 |
|---|---|---|
| DIAGNOSTIC_EVENT：timestamp、timestampType、source、severity、text、globalPid；rowid 1/69 | 会话start/stop观察；TargetTimestamp与HostTimestamp、Injection/Daemon/Analysis枚举分别保留 | 不可将两类timestamp直接排序相减或把stopped视为全部buffer已交付 |
| rowid 10/33：NVTX collected 12、CUDA collected 41975；globalPid=282326252650496，对应PID50740，与CUDA device表PID一致 | Analysis阶段报告目标进程的已收集计数 | 分母/过滤/事件类别口径未知，不是loss counter |
| rowid 66/68：CUPTI produced 42863/42868、buffers20 | Injection阶段两次快照；必须保留两条及其时间 | 不可相减、不可与41975作差推断丢失；不知重置、去重/过滤与统计时点 |
| rowid 52、55、60：flush配置文字、CUDA/NVTX injection initialized | 初始化/策略观察 | 不等于已执行最终flush，更不是零丢失声明 |
| rowid 53：实际加载`target-windows-x64/cupti64_129.dll`；67：实际software-instrumented trace | collector实际组件及路径线索、trace方法 | 模型torch CUDA12.4 ≠ collector CUPTI12.4；DLL精确版本/hash仍需安装取证，不能仅凭129判定patch |
| rowid 2–47中其他PID的NVTX/CUDA warnings | process-tree里多进程诊断；目标PID之外仍需保留 | 不能因PID不同普遍豁免会话级错误；也不据此宣布目标PID已丢失 |
| META_DATA_CAPTURE：PROFILING_SESSION_UUID、CUDA_TRACE_SCOPE=ProcessTree、CUDA_SKIP_SOME_API_CALLS=true | 会话身份、配置与API universe限制 | 全会话是声明scope内的完整时间生命周期，不是system-wide所有进程；已选择API的零丢失也不证明必需API全部启用 |
| META_DATA_CAPTURE flush-on-stop=false，而row52文本表达会在stop时flush | 两种来源有待解释的配置/诊断差异 | 不选有利字段消除差异；不能据此认定执行过stop，也不能直接认定丢失。当前完整性UNKNOWN，局部配置歧义保留 |
| ANALYSIS_DETAILS startTime/stopTime/duration；TARGET_INFO_SESSION_START_TIME | 捕获时段、原时钟资料 | 不能单独建立host perf-counter到trace的映射；不改变D1 trace-native规则 |
| NVTX_EVENTS + 新版host ledger（新版尚无真实产物） | 双向ID/序列匹配可证明**声明的应用marker集合**被观察 | 不证明其他NVTX、不证明CUDA、不覆盖进程/collector早退后的未知记录 |

`ANALYSIS_FILE`/`ProcessStreams`各3项也核对：应用stdout/stderr及空流，不是额外collector完整性证明。stderr内有非UTF-8字节，初次严格文本查询失败；随后只按BLOB检查长度/hash与有限ASCII关键词，未忽略错误并宣称全文解码成功。META_DATA_EXPORT含导出版本、schema、过滤/时间转换配置等字段，未出现通道完整性认证；有非UTF-8本地时间字段，不猜编码。

**证据隐私警示：** 既有SQLite会携带进程环境及认证信息，不能上传GitHub或原样发给厂商。本轮原证据不改写；后续对外只提交审查过的字段名/脱敏问题，来源hash单独保留。令牌处置属于用户账号操作，不属于本轮代码改动。

## 2. 对应版本官方资料与尚缺的肯定合同

本轮最初直接URL访问失败，经[官方Archives](https://docs.nvidia.com/nsight-systems/Archives/)→2026.2目录链接后，已成功读取以下相关章节，不再沿用“正文始终无法访问”的旧状态：

- [2026.2 Analysis Guide](https://archive.docs.nvidia.com/nsight-systems/2026.2/AnalysisGuide/index.html)：DIAGNOSTIC_EVENT schema及ProcessStreams/PID查询；正文检索dropped/loss无命中。不提供本次所需的全会话认证合同。
- [2026.2 User Guide](https://archive.docs.nvidia.com/nsight-systems/2026.2/UserGuide/index.html)：Diagnostics Summary混合采集与后处理消息；CUDA Trace/flush说明收集结束flush的行为及未交付device-buffer风险。flush行为保证不等于涵盖过滤、溢出、未完成记录和NVTX链路的零损失证明。CLI列有cuda-trace-all-apis；不能据API表非空确认universe完备。
- [2026.2 Release Notes](https://archive.docs.nvidia.com/nsight-systems/2026.2/ReleaseNotes/index.html)：记录容量上限、CUPTI buffer分配与异常退出风险；另有CLI API subset不可更改的文字，与User Guide的选项说明不完全一致。必须核对具体2026.2.1安装说明/厂商解释，不能自行打开新选项或断言当前profile充分。
- [CUPTI 12.9.1 Activity API](https://docs.nvidia.com/cupti/12.9.1/api/group__CUPTI__ACTIVITY__API.html)：`cuptiActivityGetNumDroppedRecords`报告buffer不足导致的activity丢失，按context/stream或global queue读取，读取会清零；FlushAll不隐式同步，forced flush可以交付未完整记录。这是与已观察DLL系列相关的API语义参考，**不是精确DLL版本证明，也不代表Nsight向用户暴露该counter**，不覆盖NVTX或全部故障原因。禁止旁注reader与Nsight争用/重置计数。

未来A路线的提取合同只有取得厂商/版本依据后才可落地：原始证据hash+selector、exact build/component、session UUID、scope PID集合/完整时段/clock、通道及包含的API/activity类型、初始状态、每次读取/重置的累计区间、最终flush与未完成记录处置、传输/后处理损失及与反证的优先关系。counter=0仅在其证明范围闭合时可用；非计数等价声明count保持null。NVTX应用ledger匹配仍是附加条件，不替代该合同。现有`assess_integrity`仅验证shape，`provider_authenticated=False`；不可把手填receipt接入真实放行路径。

## 3. 新版本Q0资格计划（未执行）

目标是验证正确性而非性能；固定目标Windows/RTX4090栈及实际collector组件，保持单GPU/请求内范围。独立oracle继续来自受控构造的人工W(s)/terminal/状态与区间算术，禁止从被测S输出生成expected。既有23案例清单及execution strategy保留，不修改旧oracle/evaluator或历史qualification报告。

| 影响项 | 可复用 / 已有本地证据 | 新资格必需验证及停止规则 |
|---|---|---|
| D1共同completion | 原host-readable定义、三个窗口公式；本地fake token/marker序列测试 | 真实受控完成后marker、host ledger与trace一一匹配；首/后token同helper，不加隐藏sync。缺点/重号/倒序/clock冲突阻塞，不把marker调用包络说成零误差 |
| 身份/device adapter | UUID/PCI联结规则；非同号namespace及错PID回归 | actual process PID、physical/logical/inventory/activity映射、context/stream/event/correlation闭环；跨request/repeat/pass/attempt混用必须拒绝。旧Raw无新ledger，不能回填伪造资格 |
| projection→S/A | 既有W(s)/ownership语义，手算投影与文件hash负例 | STREAM/DEVICE/CONTEXT/EVENT/EVENT-XSTREAM、DEFAULT-LEGACY/PTDS；PHASE-SPILL、EXTERNAL、INVOCATION-BLEED、MULTITHREAD-ORDERED、OVERLAPPING-HOST-SYNC。原point引用必须可解引用，projection不作dependency；旧Q0 containment例外不搬到D1窗口 |
| A/B0.3 signed表示 | 旧0.2默认路径回归；[-60,140)手算A=165/5/20/10/0，B=10/20/10/20/10；int64极值及uint64差值往返 | COMPLETED、EMPTY、KERNEL-MEMOP及上行所有case重验证；负时间/跨零/等边界/越界/缺失的独立合成扩展。真实trace不强求出现负数，不移动时间制造“真实负时间证据” |
| Derived0.3 / D2 | D=-150、score=-150/190手算；独立裁剪/去重/membership、unknown与空分母测试 | 来自合格新版A/B的文件派生/版本与hash匹配；A unattributed/invalid、B ambiguous/invalid、完整性UNKNOWN不产生有效D；不新增CUDA实验专门“证明D公式” |
| 完整性及支持边界 | 旧DROPPED、MISSING-CORR、MISSING-EVENT、GRAPH-UNSUPPORTED、SYNC-D2H-UNSUPPORTED、QUERY expected；新shape负例 | 每通道finalized/范围/重置/证据真实性；未知/非零/冲突/局部计数必须拒绝。缺映射/unsupported保留原因及null，不填0；无需故意压垮collector验证丢失 |
| 含糊case | TERMINAL-TIE、SUBMISSION-RACE既有synthetic-only资格策略 | 保持synthetic-only，但在新adapter/表示入口重新核对明确ambiguous，不能让其充当真实Q0 |

矩阵覆盖全部23既有case；不是新增一轮参数扫描。**重用边界：** 历史Gate6 PASS只证明0.2.2旧栈；不可变旧Raw重放最多证明旧输入兼容，不能证明D1 marker/new profile。共享identity/observation/projection入口影响全部case，因此新profile完整资格的默认计划为21个原有REAL_CONTROLLED_TRACE策略（包括原seed+fault策略）+2个synthetic-only，并非21种额外实验；保留23项本地回归。除非采集前的逐case影响审查证明某项完全未受影响且有符合新要求的原始证据，否则不得删减真实资格项。当前旧输入缺新锚点/完整性证明，不满足该豁免。

新增独立正负预期：已完成活动仍在W(s)、无关重叠不入W(s)、空集合合法；负时间hidden progress不丢；三窗共享端点且半开；同一sync跨phase只裁剪membership，B不求跨sync总和；计数器早读清零/缺最终区间、NVTX缺点、scope外warning可能影响共享collector、跨run有效hash混用均拒绝。精确离散身份/集合/状态与整数fixture必须完全匹配；真实时长按既有oracle的实际已知标签区间关系核算，不拿合成ns当真实时延、不发明容差。

资格产物应单独绑定code/source/binary/oracle/evaluator/schema/profile/collector组件hash、环境、每case construction admission、原始REP/SQLite、producer/identity/integrity receipt及逐case差异报告。现有`q0_gate.py`仍是0.2 Gate6聚合器，不能将其旧PASS作为新版资格报告；新版profile资格封套/汇总适配须后续最小实现并审查，旧路径保留。Q0微程序新marker载体也尚未实现/验收，不把模型fixture当微程序。

顺序：**肯定证据方案定案 → provider/必要编排与新版资格封套本地验证 → 经授权固定部署/静态检查 → 新profile受控Q0（完整性先于数值）→ 独立审计qualification → 另行授权Gate8最小真实workload → EP-G8-01～04报告。** 本轮没有任何采集授权；即使Q0通过，也不自动授权workload。失败case或身份/完整性不明立即停止对应资格汇总，保留新目录失败记录，禁止自动重试/拼接；修复后按受影响范围完整重验，不用workload结果弥补Q0。

## 4. B取证仍不足时的有界替代路线（仅供裁决）

1. **优先厂商支持的同collector可审计证明/配置。** 如只是提取已有且充分的字段，属于版本化provider工程适配；若增加新capture选项/范围/flush政策，需observation profile版本及成本/Q0审查，不假定开关能证明完整性。
2. **collector-side专门完整性记录或替换collector。** 需拥有buffer生命周期、损失累计、最终交付与NVTX证据；不能只外接CUPTI dropped reader。会改变collector/Canonical来源和observation contract，必须明确授权amendment、新Q0、时钟/相关性/观测开销验证。收益是可审核证据，不是新的研究贡献指标。
3. **保留现栈仅作UNKNOWN工程诊断。** 可停止无效采集投入，但不能获得本科学验收资格；若要以有限检测能力代替肯定证明，必须显式修改验收amendment并限制研究claim，不能默认执行。不存在“将UNKNOWN改0”的方案。

## 5. 真实采集编排的必要剩余差距

- `run_gate8_requests_to_files`运行实际runner代码，但测试使用CPU model/token doubles与mock NVTX；接收已加载model/resident输入，不负责模型加载前admission。当前legacy CLI/`run_server_smoke_test.ps1`没有调用此新API，不能用旧launcher宣布新profile已采集。
- file-chain测试REP为显式synthetic字节、SQLite为fixture，WMPC/producer/export receipt部分由测试构造；它证明文件联结与拒绝规则，不证明真实collector→receipt生成。旧Gate7真实export成功只可复用工具可用性线索。
- 当前历史SQLite的46表中没有`CUPTI_ACTIVITY_KIND_DRIVER`或`CUPTI_ACTIVITY_KIND_CUDA_EVENT`；不得据其缺失推断目标工具永远不支持，也不得由fixture填齐这些映射。后续真实Q0必须逐同步类型证明Runtime/Driver/context/event事实满足registry，缺事实按原unsupported/invalid规则处理。官方API过滤说明不一致必须先解决必需API universe，零丢失也不能补足主动未采集的字段。
- 必须最小打通：固定WMPC/model内容与prompt→模型加载前commit/dirty/GPU/mask门→同进程probe/PID→共享计划的双pass producer→不可变Raw/export receipt→Canonical finalized sidecars→肯定integrity provider→科学链与机器报告。计划/receipt hash须单向，不补写旧文件。
- 双pass实际输入/模式/warmup/repeat/EOS/exclusion/attempt与telemetry配对、新marker观测延迟、collector完整生命周期、输出中断和限定重试仍需目标栈验收；32/2、batch1、warmup1/repeat2仅候选Engineering最小workload，不作统计结论。不增加N1/G1、性能排名或新指标。
- 未来执行入口需显式去除无关敏感环境变量并保留白名单身份，避免Raw自动捕获凭证；变更启动环境需登记provenance并核对所需运行环境不变。现在只记录要求，不改现有Raw/代码。

## 附录：协调窗口的一次最小安装只读取证

由协调窗口从已有安装回执设置`$NsysInstallRoot`为**目标2026.2.1安装根**。下段不调用任何exe/dll/脚本；只枚举安装树、读取文件版本/hash与有限文本命中，输出到现有协调窗口回执。不要枚举全盘，不打印环境变量，不上传安装二进制。若权限失败则报告失败，不提权/换路径猜测。文档缺失也是可回传结果。

```powershell
$ErrorActionPreference = 'Stop'
if (-not (Get-Variable NsysInstallRoot -ErrorAction SilentlyContinue)) {
    throw 'Set NsysInstallRoot from the existing installation receipt first'
}
$auditInstall = (Resolve-Path -LiteralPath $NsysInstallRoot).Path.TrimEnd('\')
if ((Split-Path -Leaf $auditInstall) -ne 'Nsight Systems 2026.2.1') {
    throw 'Unexpected installation root; STOP and reconcile receipt'
}
$auditAll = @(Get-ChildItem -LiteralPath $auditInstall -Recurse -File -ErrorAction Stop)
$auditBins = @($auditAll | Where-Object {
    $_.Name -eq 'nsys.exe' -or $_.Name -eq 'cupti64_129.dll'
})
if ($auditBins.Count -eq 0) { throw 'Recorded components not found' }
$auditBins | ForEach-Object {
    [pscustomobject]@{ RelativePath=$_.FullName.Substring($auditInstall.Length+1)
        Length=$_.Length; FileVersion=$_.VersionInfo.FileVersion
        ProductVersion=$_.VersionInfo.ProductVersion
        SHA256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash }
} | ConvertTo-Json -Depth 4
$auditDocs = @($auditAll | Where-Object {
    $_.Extension -in '.html','.htm','.md','.txt','.json','.sql','.py','.pdf','.chm' -and
    $_.FullName -match '(?i)doc|help|report|recipe|schema|readme|release|diagnostic'
})
"DOCUMENT_CANDIDATES=$($auditDocs.Count)"
$auditDocs | ForEach-Object { $_.FullName.Substring($auditInstall.Length+1) }
$auditText = @($auditDocs | Where-Object {
    $_.Extension -notin '.pdf','.chm' -and $_.Length -le 4MB
})
$auditHits = @($auditText | ForEach-Object {
    Select-String -LiteralPath $_.FullName -Pattern `
      'GetNumDroppedRecords|dropped.records|records.dropped|data.loss|lost.events|final.flush|CUDA_SKIP_SOME_API_CALLS|cuda-trace-all-apis|DIAGNOSTIC_EVENT' `
      -AllMatches -ErrorAction Stop
})
"TEXT_FILES_SCANNED=$($auditText.Count); MATCH_LINES=$($auditHits.Count)"
$auditHits | Select-Object -First 120 | ForEach-Object {
    [pscustomobject]@{ RelativePath=$_.Path.Substring($auditInstall.Length+1)
        LineNumber=$_.LineNumber; Text=$_.Line }
} | ConvertTo-Json -Depth 4
"TRUNCATED=$($auditHits.Count -gt 120)"
```

回传组件身份、文档候选列表、命中及是否截断；如命中有意义，再由主窗口指定**少量原说明文件**供完整上下文核验，PDF/CHM当前只列名不执行。不因无命中重复扩大到整台机器。

一次厂商询证问题（无私有数据）：该build的software CUDA及NVTX分别有无可导出的完整session丢失counter/等价声明？它覆盖哪些过滤前后API/activity、PID/context/queue、buffer/transport/analysis阶段？所有读取重置和最终flush如何累计？初始化/退出时未交付或未完成记录如何报告？明确0时是否必有记录？相关字段及build文档在哪里？不要原样发送REP、环境或凭证。
