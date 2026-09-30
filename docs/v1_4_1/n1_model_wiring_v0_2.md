# N1 verified模型接线与最小可行性 0.2

当前状态（7.110）：[N1模型三组限定Engineering可行性PASS](n1_model_feasibility_closeout_v0_1.md)。V0复用c21封存数据的新合同分析；d25 Vmarker/V16实际回传已审查。现行consumer为adapter0.3/A-B0.6，增加规则见[opaque amendment](n1_opaque_allocation_v0_1.md)；下文保留本版接线设计及历史0.2说明，不是当前待采集批次。无新服务器任务，Pilot尚未启动。
7.107历史：[Raw来源amendment与allocation裁决稿0.1](n1_raw_provenance_allocation_v0_1.md)曾记录V0因allocation政策未授而拒绝。其原报告和[7.106实物审查](n1_v0_review_v0_1.md)保持；后来批准的0.3分析不覆盖旧判定。
7.105补正：首次c6cdb36服务器尝试在profile前被共享G1-only validator拒绝，未执行模型。该分派遗漏已用真实prepared及prepare→seal/collector边界CPU回归修复；旧attempt仍BLOCKED，详见[进度7.105](research_progress.md)。
依据：Pre-Pilot协议v2.1 §4.2 V16及[Gate9分域合同0.1](gate9_domain_qualification_contract_v0_1.md)。
本版接替[0.1的部分实现状态](n1_model_wiring_v0_1.md)，不是新测量语义、完整N1矩阵或新Q0资格。

## 执行合同与真实接线

- 继续使用`gate8_target_python model-run → gate8_diagnostic → run_gate8_requests_to_files`。显式解释器/PID、isolated preflight的Git二进制清单、源树/模型内容/输入digest、实际CUDA UUID/PCI和logical映射均沿用原检查；没有复制模型入口或跳过门槛。
- 执行前manifest同时声明既有`n1_model`与`N1-VERIFIED-MODEL/0.1`。V0/Vmarker/V16共用32/2、batch1、fp16/eager/SDPA/cache/greedy、warmup1/repeat1；V16内部兼容名仍为Vsync。只在decode第16层（index15）forward返回后干预一次；Vmarker同包装/范围不同步；V0无干预包装。实际计数及输出token进入sidecar，不能用声明值代替执行。
- 按Gate9优先的fresh measured-stream路线，warmup在单独held非默认非阻塞流上完成并成功drain；随后创建不同measured流，保留两对象至执行结束，拒绝handle复用。此策略三组一致。原0.1 resident子helper仍保留为本地回归，不用于部署，也不冒充新入口。
- 三组共同在最终device drain之前、request之外执行一次current-stream同步锚点，保存native handle/generation。其Raw API→physical sync→context/trace stream连接证明实际映射，不能把handle数字等同trace stream ID。随后原成功drain和三个host-readable completion点不变；锚点/模型加载/warmup/cleanup均不加入request窗口。
- sidecar `n1_model_calls.json`由execution SHA256绑定，包含warmup/测量调用、held lifetime、前后实际handle、层位/次数、host token和实际input shape。producer receipt/边界/drain/stage仍使用原schema，不给共享manifest塞单个request身份。

## 多API消费及拒绝

`exposedpath-n1-model-ownership/0.2.0`只由明确N1模型manifest分派；旧0.1.1分析文件按其显式版本复读，0.1.0执行产物仍原样保留。适配仅在实际Raw证明nondefault NON_BLOCKING且没有已观察或顺序不明incoming依赖时限定S建图范围，不填全局default模式、不截完整物理前缀；旧Gate9单操作桥接及G1默认路径不opt-in。

1. 复用不可变input receipt、Canonical、D1 projection、stage/drain与已接受官方诊断处置。保留原warning、UNKNOWN/NOT_ASSESSED；不豁免新诊断。
2. 将锚点与相同process/thread/clock/device/context的drain核对，查CUPTI stream type=NON_BLOCKING及非null流，不能拿runtime flags替代CUPTI编码。前缀活动须在drain完成；measured trace流已有历史工作则拒绝，**不裁掉物理W前缀**。
3. 对全部窗内API按唯一correlation/原record验证实际活动/同步；逐条输出request、phase、native generation、context/trace stream、API/physical/forward refs。一个forward允许多个API及多个活动，不要求一标记一API。
4. 所有已观察提交/同步都要被消费；其他线程/流、graph、未支持event依赖、悬空/歧义correlation、冲突或未知API拒绝。锚点/干预范围可含已注册且无冲突的non-submit查询，但必须恰有预定数量的真实同步；未知伴随API仍拒绝，不按“没有activity”猜类别。
5. 原物理S负责完整W/terminal及validity，原A负责互斥union，原B逐sync发布。P1显式S0.4/A-B0.5允许可复核Raw来源的内部同步，源码origin/callsite/ordinal仍null，不能从forward伪造。成功状态、唯一映射、进程/时钟/scope/owner、完整W/terminal仍必需；token-ready和预定干预缺结构身份或来源冲突仍拒绝。旧版本仍执行原来源要求，不是G1投影A的规则变更。
6. 所有measured physical B必须合格，A不能带证据/归属拒绝原因；不以效果或低unattributed筛选点。API分类注册表没有扩张。Raw、旧报告与历史资格不改。

## 本地独立验证与边界

tests-first曾复现verified入口拒绝N1、旧单API消费者拒绝模型sidecar、collector未分派及缺三组编排；随后最小接通。
实际verified producer写manifest/pass/boundary/drain/stage/calls，经CPU记录器生成synthetic SQLite，再走真实Canonical→projection→S/A/B及复读；并非仅填满consumer字段。

独立构造：每token两个顺序kernel提交及一次D2H，token-ready同步；V16另在decode第二kernel后同步。W活动数量V0/Vmarker=`[3,6]`、V16=`[3,5,6]`。
每API区间10ns、活动在同步入口前完成：每phase API=30ns、wait=0、residual=10ns；V16 decode residual=20ns；Host由预设窗口减去这些确定区间，unknown=0。此预期未调用analyzer生成。
负例涵盖缺边界/drain/correlation、重复映射、线程/流/graph/依赖冲突、未知诊断/伴随API、错sidecar身份/次数、Vmarker实际多同步，以及原异常/forward恢复、错误入口身份。原版本未标记内部同步拒绝行为保留；新版本仅在完整Raw来源证据下允许，缺结构token/干预及冲突仍拒绝。已注册查询伴随项不被误作第二个同步。

相关14文件CPU回归192 passed；收口后三文件定向36 passed（与192有重叠，不累加）。Python语法、PowerShell解析、diff检查；无全量/Q0重跑，无模型/GPU/Nsight或服务器操作。CPU成功只证明接线、编排与确定性判断，不能替代目标机。

## 历史最小目标机批次：已执行V0并停止，当前不再交付或执行

固定提交、单一增量包，当前修复前置为服务器c6cdb36（原700f671包为历史）；只运行相关CPU回归。mask=3、显式目标解释器/site、已有模型及32token内容清单保持。经审查授权后才运行V0→Vmarker→V16各一个warmup/一个measured request，每组独立新目录与manifest。

- V0：验证真实模型在统一专用流政策下的完成、实际提交/同步/ownership和A/单sync B支持域；不是自然G1。
- Vmarker：验证已批准layer16包装/标记位置次数、没有新增实际同步、与V0 token及公共执行身份相同。
- V16：验证一次真实干预同步的correlation/实际流/W/terminal/B，其他合同及token不变。首批不比较干预收益、稳定性或Pilot阈值。

复用Gate9显式流调用和S/B资格、三窗A及正反例、现有环境/模型快照；新证据仅验证模型行为是否满足这些条件，不重跑完整Q0/G1。
成功只产生`BATCH_COMPLETE_PENDING_REVIEW`及各组`FEASIBLE_ONCE_PENDING_REVIEW`，N1可行性待回传审查，不能自动授Pilot/科学结论。
身份/配置/内容或token冲突、错误位置/实际次数、OOM、early EOS、超时、缺边界/映射/S身份、其他流/依赖、未知诊断、分析失败均立即停止后续组，不重试/恢复/改参。证据不足属于不可判别，机器保持BLOCKED而非“未观察到干预效果”。外层900秒及已有profile120秒界限保持；若后代退出未知，停止打包并交协调窗口，禁止杀无关进程。
整段入口为`scripts/run_n1_model_once.ps1`；机器路径和固定commit/hash只放忽略的本地交付包。单ZIP含执行脚本/身份、CPU回执、prepared、入口异常/退出、preflight、producer、原REP/SQLite/export、Canonical/projection/domain与批次报告及覆盖全部文件的清单。
本轮仅交付审查，不代表服务器获准自动执行。
