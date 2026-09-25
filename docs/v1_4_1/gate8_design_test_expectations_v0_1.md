# Gate8 独立测试预期 v0.1

版本`G8-DESIGN-EXPECTED/0.1.0`，2026-09-25。以下期望人工先写定，不调用生产projection、S或coverage算法生成。它们是**待实现测试规格**，不是已运行的新功能测试，更不是GPU/Q0验收。配套JSON只含schema形状样例与变异预期；真实语义测试须通过producer生成payload后进入adapter，不能只手工填完consumer。

## 1. D1手算与producer链

输入：request `r0`，pass1/attempt-a，原point rowids=10/11/12，source hash=64个a（合成占位identity，不是真实数据）；trace锚点r=100、t0=180、t1=300 ns；各自boundary_id=r/t0/t1，pid=42/tid=7。host时间为900000/900080/900200，明确不同clock。独立预期：full=[100,300)、prefill=[100,180)、decode=[180,300)，durations=200/80/120；共享端点ref完全相同，scope依赖证据=false。任何以host值作trace offset的结果都错误。

| case | 输入变更 | 独立预期（shape或semantic阶段） |
|---|---|---|
| D1-01 | 上述N=2，producer产出两个token完成点 | 三窗口与原record精确绑定；Host值读取先于marker；同一helper用于first/later |
| D1-02 | N=1，仅r/t0 | full=prefill=[100,180)，decode=[180,180)，start_ref=end_ref=row11 |
| D1-03 | 缺t1或trace未采到ledger要求的点 | BOUNDARY_MISSING，零个r0可接受scope；不得用旧decode pop补齐 |
| D1-04 | boundary_id=t0出现两原row，即便时间相同 | BOUNDARY_DUPLICATE，拒绝窗口 |
| D1-05 | t1=170或r=180=t0 | BOUNDARY_ORDER_INVALID |
| D1-06 | row11改request/attempt/pid/tid/clock，或另一source hash | BOUNDARY_IDENTITY_CONFLICT / CLOCK_DOMAIN_UNRESOLVED / SOURCE_HASH_MISMATCH，拒绝 |
| D1-07 | projection.end_ns=301但ref仍row12@300 | PROJECTION_REF_MISMATCH，shape可合法但语义必须拒绝 |
| D1-08 | predrain[50,90]、cleanup[310,330] | 皆不入[100,300)；projection不得取它们延长窗口 |
| D1-09 | helper在tolist前发点，或EOS重新读GPU | producer顺序回归失败；即便JSON形状合法也不允许生成科学scope |
| D1-10 | after_marker<before_marker；host与trace故意不成同offset | 前者拒绝；后者不据此拒绝合法trace，而是禁止跨clock相减 |
| D1-11 | COMPLETE却实际token=1、计划2，或earlyEOS | ledger一致性拒绝COMPLETE；EXCLUDED记录保留，不生成完整N=2验收 |

producer测试使用记录事件顺序的fake host-readable token与NVTX sink，再把该**真实producer payload**和以上固定trace时间装入独立SQLite fixture。fixture的时间由上述常量给出，不从实现输出反算expected。

## 2. D2手算主例（所有调用已证明属于同一request）

沿用full[100,300)、prefill[100,180)、decode[180,300)。完整性预设为合成ZERO_CONFIRMED，仅用于数值测试，不伪称真实collector已满足。输入四个唯一physical ID：

| ID | Host区间 | S/B状态 | 独立设备事实（仅验证A不被coverage污染） |
|---|---|---|---|
| a | [120,200) | VALID_NONEMPTY/B_VALID | W中唯一activity=[150,190) |
| b | [160,220) | INVALID/B_INVALID | 缺completion证据，不填activity |
| c | [250,250) | VALID_EMPTY/B_NOT_APPLICABLE | 真正已证明空集合 |
| d | [240,290) | VALID_NONEMPTY/B_VALID | W中唯一activity=[260,280) |

逐窗人工预期（均为精确分数，不靠百分比舍入比对）：

| W | members | 总/支持/B-valid count | 总/支持/B-valid调用ns | supported count/duration | B-valid count/duration |
|---|---|---|---|---|---|
| full | a,b,c,d | 4/3/2 | 190/130/130 | 3/4，130/190 | 2/3，130/130 |
| prefill | a,b | 2/1/1 | 80/60/60 | 1/2，60/80 | 1/1，60/60 |
| decode | a,b,c,d | 4/3/2 | 110/70/70 | 3/4，70/110 | 2/3，70/70 |

手算说明：a跨边界，prefill60ns、decode20ns；b分别20/40ns；c仅decode count、时长0；d只decode50ns。phase count之和6≠full count4，不得相加；同ID只一条B。B-valid分母是支持数量/时长，而非全部。

在只给出以上CUDA同步API且其余窗口为已证明Host推进的独立A例中，invalid b优先：full A_host=50、A_cuda_api=0、A_device_wait=30、A_sync_residual=60、A_unattributed=60，总200ns。prefill分别20/0/10/30/20，总80；decode分别30/0/20/30/40，总120。具体原子划分：Host[100,120)、[220,240)、[290,300)；unattributed[160,220)；device wait[150,160)、[260,280)；其余有效sync为residual。**coverage的190ns不能替代A的200ns预算，启停coverage不改变这些A预期。** 本例是独立合成事实，不声称从缺失b恢复W。

## 3. Coverage边界/负例

| case | 输入 | 预期 |
|---|---|---|
| C-OVERLAP | W[100,300)，两不同调用均[100,300)，一valid一invalid | 总调用400ns、支持200ns，duration=1/2；A invalid优先覆盖200ns而非取此50%作可解释墙钟 |
| C-DUP | 主例a重复完全相同引用 | 与主例相同；若同UID时间/状态不同则COVERAGE_INPUT_INVALID |
| C-ENDPOINT | 额外zero call@180 | prefill不计、decode/full计；zero@300三个窗都不计 |
| C-ZERO | W[100,180)，只有valid-empty零时长@120 | count supported=1/1，B-valid count=0/1；两duration均NOT_APPLICABLE(0/0)，显示null |
| C-EMPTY | 完整W没有blocking sync，或合法空decode | members=[]、观察数0；四比例NOT_APPLICABLE(0/0)，显示null |
| C-ALLINVALID | 一个时间/ownership已知的invalid [120,140) | supported count=0/1、duration=0/20；B-valid两项0/0 NOT_APPLICABLE；分母仍COMPLETE |
| C-TIE | a改为TERMINAL_TIE/AMBIGUOUS | a留总分母，不计P/V；不能依据registry支持类型把它放回supported |
| C-MISSING | b缺时间/ownership，可能在W；未知API可能阻塞 | denominator INCOMPLETE，四比例UNKNOWN(null/null)；保留观察数，不输出完整total |
| C-DROP | 只有collector exit0或无warning，无肯定证明 | integrity UNKNOWN；coverage四比例UNKNOWN，不是COMPLETE |
| C-BJOIN | a对应两冲突B行、缺B行或B_VALID但S INVALID | COVERAGE_INPUT_INVALID；不选其中有利记录 |
| C-OUTSIDE | 全部已证明其他request/完全在W外且无作用域内dependency | 不计U；若外部activity影响本request closure，则按冻结外部ownership失效，不得仅裁掉 |

## 4. 身份与完整性独立预期

- ID-01：两个request r0/r1、repeat0/1，打乱ledger/NVTX行顺序 → 完整键联结不变；不给bundle顶层硬写repeat0。
- ID-02：planned r1没有对应完成记录、r0跨attempt串联或NVTX出现未知request → IDENTITY_CONFLICT；warmup不得补作repeat。
- GPU-01：physical=3、logical=0、inventory=2、trace=0，合成UUID与PCI四元组均相同 → 映射有效、selected_device_id=0；UUID/PID不符或多候选/缺表 → DEVICE_MAPPING_UNPROVEN。不调用device_count。
- LOSS-01：同session完整CUDA通道collector计数0、finalized且范围覆盖、无反证 → 该通道ZERO_CONFIRMED；仍不能据此声称NVTX也为零。
- LOSS-02：counter>0 → NONZERO；仅末次0而中间计数重置记录缺失 → UNKNOWN；证据互相矛盾 → CONFLICT。
- LOSS-03：肯定声明有记录来源而无数值count → count=null；不捏造0。来源不属于当前Raw/pass/session → 拒绝联结。
- LOSS-04：预期NVTX ledger匹配，但无collector CUDA完整性证据 → 全局science acceptance仍阻塞；SQLite integrity及export exit0不改变此结论。

## 5. 验证分层

本轮可执行JSON解析、Draft2020-12 schema自身检查、`gate8_design_schema_examples_v0_1.json`的正例及变异负例验证；这只验证设计形状约束。上列语义例必须由未来实现产生actual并与固定expected比较，不能以本轮shape检查勾选它们完成。现有冻结contract内部一致性可读校验，不重新采集/聚合Q0。受影响Q0范围见boundary amendment §6。
