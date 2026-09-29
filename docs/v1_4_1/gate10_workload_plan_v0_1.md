# Gate10 最小 workload 可行性准备 0.1

版本：G10-WORKLOAD-FEASIBILITY/0.1。Engineering；[7.102退出裁决：Gate10限定G1 PASS](gate10_closeout_v0_1.md)。下述准备/待执行语句保留为计划历史，两个新点均已完成，不再执行旧交付。
依据：当前研究设计v7.1 §2.1、Pre-Pilot实验协议v2.1 §2.1候选池、用户批准的单平台路线及[Gate9分域资格](gate9_closeout_v0_1.md)。不修改冻结S/A/B公式，不是Pilot或Freeze。

## 候选与执行边界

| 点 | 处理 | 比较问题与信息用途 |
|---|---|---|
| 输入32/输出2/batch1 | 复用Gate8封存配对和1733ff3分类审查，不重跑 | 最短已有完整prefill/decode执行基线；不是当前提交的重新验证 |
| 输入128/输出2/batch1 | 首个新点，一次profile | 输入增至4倍时，同一eager/SDPA执行及G1投影支持域能否成立，为后续输入轴比较提供可行点 |
| 输入512/输出2/batch1 | 仅128成功后执行一次profile | 再增至4倍，检查中等输入的资源及必要依赖证据；不预设API/kernel工作是否按比例转为A |

128/512来自协议候选池；输出2沿用已批准Engineering基线，不冒充W01/W04的16输出token点。没有根据既有A比例选点，也不将unattributed=0或趋势符合预期作为通过条件。2048/4096、第二模型/平台、compile/graph、G2本轮不做。

固定Qwen2.5-1.5B-Instruct内容快照、batch1、fp16、greedy、eager、SDPA/use_cache、原GPU及隔离解释器；自然G1不增加人工同步。模型加载、一次同输入warmup及成功drain在request窗外，测量一次request（repeat1）。输出2覆盖prefill首token与decode一个token。
仅Pass1逐request支持域/资源可行性，不另跑Pass0、不估计新点overhead；已有32/2配对仅是单次工程观察。未来latency比较仍需同合同Pass0，不用profile时间当自然性能。

## 输入和有效性

使用已封存prompt文件（SHA256 `4dffd0ddcbd3185c656ae4a27efaf5aab302febba6ead5df4d37d903a2091920`）sample0的32个token，按原顺序循环4/16次；无tokenizer在线操作、无chat template、无截断/补齐。新文件保留tokenizer/special-token元数据，batch只取一个样本，attention_mask全1，显式记录构造及源文件hash。文件SHA256在prepare之前生成并写入候选清单与manifest。
必须逐token检查整数、vocab范围、非special token、长度/全1 mask及模型config最大位置长度；模型内容必须匹配已封存inventory，revision仍UNKNOWN/content-addressed，不冒称revision已知。
实际runner输入由经过hash校验的同一prompt构造；输出数来自producer实际读取token计数，early EOS/不足2即不可接受，不禁用EOS、不替换prompt、不自动重试。合成token只服务本批Engineering，不授予语言质量/真实语料代表性。

## 必要实现与验证计划

采用writing-plans与tests-first；在当前根目录直接执行，不新建worktree或委派。

- [x] 新增 `exposedpath/gate10_workload.py`：固定有限点/构造/声明/输入检查，拒绝未知版本、错长度、无效token；对应 `tests/test_gate10_workload.py` 先红后绿。
- [x] 最小对齐 `gate8_diagnostic.py` prepare及target入口：仅显式Gate10声明允许128/512，旧32路径原样；manifest在执行前声明G1分域，实际文件producer测试验证非32不会静默回退。runner在完成窗后回调读取既有shape/count事实，单独写 `gate10-workload-observed/0.1`，绑定manifest/producer hash与request身份；不修改封闭pass identity schema或引入同步。
- [x] 将已接受官方warning review接入G1 domain；原诊断和UNKNOWN保留，新型/目标warning拒绝。以真实fixture文件链验证正反例；collector只在显式domain声明时调用domain，不绕过任何边界/成员/依赖检查。
- [x] 新增有限batch编排/服务器脚本，逐点停止，保留失败/未执行点；打包同一ZIP。CPU测试验证清单、顺序、停止、未知分类及实际接线；仅相关回归/语法检查。

N1 V0/Vmarker/Vsync模型矩阵尚未实现，未来需相同专用显式流/输入/边界与真实ownership桥接；不阻塞本批G1，不能由G1可行性替代N1可行性。G1每request重新验证身份、三窗口、窗前drain、内部sync、必要成员/依赖边和支持域；长度变化本身不触发新Q0。

## 7.101执行调整

128/2在76ef717已采集，原driver离线分析900秒超时。经[不变Raw续算审查](gate10_timeout_review_v0_1.md)，性能修复后128/2一次可行性通过；仅512/2未运行。下一交付使用`--remaining-512-only`新目录单点，不重新调用原两点批次、不恢复旧输出；其余合同和超时上限不变。原失败及UNKNOWN后代记录不改。

## 停止与结果

顺序128→512；任何失败停止余下点并记NOT_RUN，禁止重试/恢复/覆盖/临场改参数/扩大搜索。collection沿用120秒工具上限、300秒外层上限；单次export，无自动retry。超时可能有存活后代时停止打包，先由协调窗口处置写入者，不杀进程名、不重试。

区分事实与裁决：明确CUDA OOM异常才记RESOURCE_INFEASIBLE；超时记TIMEOUT_UNRESOLVED，不推测OOM；身份/配置/输入冲突为EXECUTION_CONTRACT_FAILURE；缺表/边界/依赖/超支持域/未知诊断/分析失败为EVIDENCE_OR_ANALYSIS_FAILURE；其他异常保留UNCLASSIFIED_FAILURE及原文。低unknown不是warning安全证据，known局部unattributed按合同保留。
单点成功要求实际2token、非EOS、完整producer/entry/preflight/REP/SQLite、G1 domain逐request质量通过；仅记FEASIBLE_ONCE_NOT_STABILITY。有界失败不是方法科学否定，也不是把该点从Formal中静默删除。

回传后才审查EP-G10-02/03；不以两次单次成功确定repeat数、overhead阈值、统计显著性或“稳定范围”。Pilot/Freeze另行准备。Gate7/8/9历史限定PASS保持。

## 本地验证及交付（7.100）

先红后绿已复现候选模块缺失、非32目标文件入口、实际shape未持久化、G1同类warning未接线、collector未dispatch domain、失败未分类等问题。相关7文件CPU回归119 passed；最终新增/收口定向22 passed（与119有重叠，不相加当独立测试数）。compileall及PowerShell语法解析、diff-check通过；不是目标机或CUDA验证。既有未知warning、missing correlation/drain/ownership及模式成员不等价负例保持，新增同类warning与correlation缺口共存仍拒绝。

执行入口 `scripts/run_gate10_once.ps1`，编排 `scripts/gate10_feasibility.py`；机器本地delivery固定commit/prerequisite、源码/输入hash、模型inventory与路径，随单包交协调窗口审查。以服务器15b24ec为前置，部署后只跑相关CPU测试，再顺序两点；无需重新编译native、跑旧probe/完整Q0/全量测试。prepare会初始化CUDA做设备身份查询，不能称整段CPU-only。
单次collection仍120秒工具限制/300秒外层限制，包含analysis的point子进程900秒上限；超时不自动延长。所有原始exit/stdout/stderr、entry异常记录、输入/manifest/preflight、producer/drain/stage、REP/SQLite/export、domain/diagnostics和batch机器报告统一单ZIP。任何中断只保留已产生证据，未执行点不得补成失败或成功。
本批只能确认G1两点一次可行性；不能据此宣布N1同点模型执行或完整N1/G1共同可行域已验证。N1模型功能准备与以后Pilot仍分开。
