# Gate 6 Phase-Spill Amendment v0.1：Q0 受控三窗口 observational boundary

状态：**批准（2026-09-19）**
适用范围：Gate 6 / Q0 Qualification，仅涉及 `Q0-PHASE-SPILL-001` 的 A 窗口发现规则
canonical baseline 分支：`codex/gate6-canonical-baseline`
canonical implementation commit：`2e81f6f9a9ec590d37fb01be9e31f2251645c5d1`

本文件冻结 Phase-Spill amendment 的 evidence basis、normative boundary、
observational-boundary rule、implementation scope、A accounting 语义、不变量、
`final-01` 文档处置、迁移与 STOP 条件。它不改变 Measurement Contract、Q0 oracle、
Canonical、S、B、native measured construction、23-case composition 或 Gate 6 PASS
判据，也不重写 Gate5 accounting design 的历史原文。

## 1. Evidence basis

Primary evidence：frozen Engineering run

```text
q0-win-4090-20260919-gate6-final-01
```

其中 `Q0-PHASE-SPILL-001` 的三条结构化 `kind=request/phase` NVTX range，直接由该 run
的 Canonical 读出：

```text
full_request = 31,043,268 .. 71,956,668
prefill      = 31,047,054 .. 31,767,312
decode       = 31,769,816 .. 71,956,427

leading gap  = 3,786 ns   (prefill.start - full.start)
phase gap    = 2,504 ns   (decode.start - prefill.end)
trailing gap = 241 ns     (full.end - decode.end)
```

因此实际满足

```text
full.start < prefill.start < prefill.end < decode.start < decode.end < full.end
```

而当前 A 窗口发现要求

```text
full.start == prefill.start
prefill.end == decode.start
decode.end == full.end
```

三条 equality 在冻结 evidence 中全部失败。

同一 case 的冻结 S/B 事实：

- request / prefill / decode 三条 structured NVTX range 全部存在；
- `S_DECODE_OWNER`：`VALID_NONEMPTY`，wait set = 该 prefill kernel，
  terminal = 同一 prefill kernel，`terminal_origin_phase=prefill`、
  `sync_owner_phase=decode`、`cross_phase_dependency=true`；
- B = `B_VALID`，phase 归属与 S 一致；
- A windows = `0`，A/B quality = `FAIL_CLOSED` / `WINDOW_DISCOVERY_INVALID`；
- 该 case 的 real evaluator 因 A 窗口 blocker 未完成。

解释边界（冻结）：本证据只用于说明“Q0 受控构造的两段 phase 边界由三次独立记录的
NVTX push/pop 给出”，不支持任何关于底层平台、driver、Runtime 或硬件的因果结论。

## 2. Normative boundary

判断（冻结）：三条 equality **不是 Measurement Contract 的规范要求，而是 analyzer
对“合成式精确切分”的过强实现假设**。

依据：

- `docs/v1_4_1/contracts/measurement_contract_v0_2.json` 的 `phase_boundaries`
  以**可观察条件**定义 phase（`request.start`、`token[0].host_readable`、
  `token[N-1].host_readable`），对应规则为 `MC-PH-001` … `MC-PH-007`（含
  `MC-PH-003 prefill_ends_at_first_token_host_readable`、
  `MC-PH-006 decode_is_valid_empty_when_fixed_output_tokens_equals_one`）以及
  `MC-A-005 cross_phase_activity_is_clipped_to_each_phase_window`；
  `semantic_ordering_tolerance_ns = 0`。
- 该 contract 全文**没有**要求 phase 窗口的 NVTX 时间戳相等，也没有要求三段窗口
  并集恰好等于 full_request。三条 equality 的 normative 前提是“相邻窗口的共享边界
  由同一个可观察事件佐证”（同一个 `token[0].host_readable` 同时是 prefill.end 与
  decode.start）。
- 三条 equality 只出现于 Gate5 accounting design
  （`docs/superpowers/specs/2026-09-12-gate5-accounting-design.md` §4）与实现
  （`exposedpath_v141/ab_inputs.py::_discovery_result` 的边界判定）。该前提在 Q0
  受控微程序中不成立：Q0 没有 token，三段边界是三次独立记录的时间戳。
- 同源先例：`q0_one_phase` 放宽规则由 `f788ea7f46148b94bdb919ebac0191680710fda9`
  引入，已为 Q0 的两窗口形式（full_request + decode）显式放宽同一 equality，说明该
  assumption 与真实 NVTX 可观测边界不兼容已被确认过一次。

因此本 amendment 的规范结论为：

| 项目 | 处置 |
|---|---|
| Measurement Contract `0.2.0` | **不修改**（改它等于削弱 `MC-PH-003/004`，方向错误） |
| Q0 oracle | **不修改** |
| Canonical / S / B | **不修改** |
| native measured construction | **不修改** |
| 23-case composition / Gate 6 PASS criterion | **不修改** |
| `q0_gate.py` | **不修改** |
| Gate5 accounting design 历史原文 | **不重写**；amendment 仅声明其 exact-equality 表述对 Q0 controlled three-window observation 不适用 |

## 3. Amendment rationale

缺陷类别是**构造 ↔ 规则不兼容**，不是“缺 metadata”：

1. 三条 range 均已存在，S 的 ownership 正是靠它们恢复的（`_phase_ownership` 取最内层
   包含区间，故 `sync_owner_phase=decode`）；因此不是“marker-only / 无窗口身份”分支。
2. 该构造只能以三次独立 `nvtxRangePushA/PopA` 表达三段，边界时间戳必然互不相等
   （identity 构串与 push 自身都带开销），frozen evidence 的 3,786 / 2,504 / 241 ns
   偏移即为实测结果；因此 equality 在此构造下**不可满足**，而非偶发失败。
3. 影响面可精确界定：21 个 real case 中只有 `Q0-PHASE-SPILL-001` 发出三段 phase range
   （`run_phase_spill` 是 `q0/cuda/exposedpath_q0.cu` 中唯一的 `prefill` phase 发出点），
   其余 case 的 `prefill` 计数为 0、先命中既有 `q0_one_phase` 分支。
4. 该 equality 对任何真实 instrumented trace 同样不可满足。本 amendment **只**覆盖
   Q0 受控观测类；自然 trace（N1/G1）继续适用原严格规则，留待独立决定。

## 4. Proposed observational-boundary rule（冻结）

对 `experiment_id == "exposedpath-q0"` 的 controlled observational class，三窗口
（full_request + prefill + decode）形状必须满足：

```text
full.start    <= prefill.start
prefill.start <= prefill.end
prefill.end   <= decode.start
decode.start  <= decode.end
decode.end    <= full.end
```

同时要求：

- 恰好 1 × `full_request`、恰好 1 × `prefill`、恰好 1 × `decode`；
- 三者落在**完全相同**的 7-field identity key（`experiment_id`、`wmpc_id`、
  `run_id`、`run_role`、`pass_id`、`request_id`、`repeat_id`）内；
- 不允许 phase overlap（由 `prefill.end <= decode.start` 给出）；
- 上述不等式已经隐含 full_request 包含两个 phase；这一条给出包含与非重叠，不得再
  引入其它时序约束；
- **不允许**任何 tolerance / epsilon / 结果驱动阈值；
- **不允许**按 `case_id`、`run_id`、oracle 或运行结果分支；
- 仅适用于既有 `experiment_id == "exposedpath-q0"` controlled observational class；
- non-Q0 trace 保持原 strict rule；
- 允许退化相等（即 `==`），因此该规则**是严格放宽**：ideal carve 与既有 synthetic
  fixture 行为不变，旧接受集是新接受集的子集；
- 不新增 thread / process 约束（identity key 已保证 request 唯一）。

## 5. Implementation scope（冻结）

本 amendment 正式 production scope **只批准**：

1. `exposedpath_v141/ab_inputs.py`（`_discovery_result` 的 Q0 三窗口分支）

对应测试：

2. `tests/test_v141_ab_inputs.py`

外加本文件：

3. `docs/v1_4_1/gate6_phase_spill_amendment_v0_1.md`

测试至少覆盖：Q0 三窗口 slack 被接受；反序 / 重叠 / 缺一 / 重复 → fail closed；
ideal carve（边界相等）继续通过；非 Q0 trace 的同一 slack 仍 fail closed；既有
`q0_one_phase` 与 synthetic fixture 回归不变；改动不影响三窗口以外的 case。

**明确排除在本 amendment implementation 之外（optional / future item）：**

- `exposedpath_v141/ab_bundle.py` 的 observability 改进（把 `window_discovery_issues`
  的真实 reason 与 `source_nvtx_record_ids` 落盘，替代当前对任何窗口发现问题都写入
  字面量 `WINDOW_DISCOVERY_INVALID` 的行为）；
- `docs/v1_4_1/contracts/ab_schema_v0_2.json` 及任何 schema 改动；
- `exposedpath_v141/q0_real.py` / evaluator 增强（例如把
  `accounting_owner_phase=DECODE` 改为 decode A window 与 S ownership 的联合校验）。

上述三项都不得随本 amendment 一起进入同一个 implementation commit。

## 6. A accounting 语义

amendment 通过后，`Q0-PHASE-SPILL-001` 的 A 层应生成三条 A 记录：

- `full_request`
- `prefill`
- `decode`

并保持：

- `MC-A-005` phase clipping 不变：跨 phase 活动只取与当前窗口的交集；
- 守恒仍是**逐窗口**的（每个窗口内部顶层类别互斥且
  `T_window_ns = Σ top-level A categories`），不得跨窗口求和；
- 三窗口**不再被要求无缝拼成** full_request：真实 instrumentation gap
  （frozen 的 3,786 / 2,504 / 241 ns）只在 full_request 窗口内按
  `host_path / cuda_api / unattributed` 正常记账，**不丢失、不人为吸附到 phase 边界、
  不跨 phase 重复计数**；
- `MC-S-014`（activity origin 与 wall-clock exposure owner 分离）不变：该 case 的
  prefill 窗口在 sync 入口之前结束，故其 device-wait 裁剪为空，绝大部分 device wait
  落在 decode 窗口。

## 7. Invariants

amendment 通过后以下全部保持不变：

- Q0 oracle（`exposedpath-q0-oracle-0.2.0`）；
- Measurement Contract（`exposedpath-measurement-contract-0.2.0`）；
- Canonical Raw（schema 与 extractor）与既有 canonical 产物；
- S semantics（含 `_phase_ownership` 的最内层包含选择）与既有 S 产物；
- B semantics 与既有 B 产物；
- native measured construction 与 21 native seed 集合；
- 21 real + 2 synthetic 的 23-case composition；
- Gate 6 PASS 判据与 `q0_gate.py`；
- 既有 `q0_one_phase` 规则，以及三窗口形式以外所有 case 的 A/B 输出。

## 8. final-01 disposition（文档叙述，不新增 machine-schema enum）

```text
q0-win-4090-20260919-gate6-final-01
```

是 frozen incomplete Engineering run：

- 已生成 real evidence = 16；其中 PASS = 12、FAIL = 4；
- frozen FAIL：`Q0-MISSING-CORR-001`、`Q0-EXTERNAL-001`、
  `Q0-MULTITHREAD-ORDERED-001`、`Q0-OVERLAPPING-HOST-SYNC-001`；
- `Q0-PHASE-SPILL-001` 的 real evaluator 未完成（A-window discovery blocker）；
- 未完成全部 real evaluator，**无 gate report**。

处置：

- 不重跑已执行 case；
- 不继续剩余 evaluator；
- 不做跨 run / 跨平台 / 跨 binary 拼接；
- 不通过重派生升级为 Gate PASS；amendment 后对该 run 的只读重派生仅可用于诊断，
  不构成任何证据；
- Raw / SQLite / Canonical / S / A-B / 已有 real evidence 只读保留，不得改写；
- 不使用新的 machine-schema enum 值，本处置只以文档叙述记录。

Gate 6 保持 `FAIL`、Q0 保持 `NOT_RUN`。

## 9. Migration / acceptance

下一正式 run 的前置条件（按序，缺一不可）：

1. 本 Phase-Spill amendment approved；
2. 按 §5 完成 implementation；
3. offline validation（targeted tests + Q0 offline regression + compileall +
   `git diff --check`）；
4. 另外 4 个 semantic FAIL 全部完成 root triage，并给出各自结论；
5. 所有必要修复统一冻结在**同一个** implementation commit 内；
6. server rebuild + identity（HEAD 等于冻结 commit、binary SHA256、工具链与 Nsight
   版本、`--list-cases` 与冻结 21 native seed 集合一致）；
7. 然后才允许新的唯一一次完整 21 real + 2 synthetic run（新 run-id、同一 run 与
   环境与 binary），产出唯一 `q0_gate_report.json`。

Gate 6 只有在唯一 `q0_gate_report.json` 同时满足 `23/23`、`verdict=PASS`、
`q0_status=PASS`、21 real 全部来自真实 evidence、2 synthetic 只承担冻结 boundary
role、同一 run / 环境 / binary 时才判 PASS。部分通过、warning、跳过、mock 或无法
运行的 GPU 测试一律不得转为 PASS。

## 10. Hard STOP

出现以下任一情况立即 STOP，且不得通过新增 attempt“补跑到成功”：

- 修改 Measurement Contract、Q0 oracle、Canonical、S、B 或 native measured
  construction；
- 引入任何 tolerance / epsilon / 结果驱动阈值；
- 以 `case_id`、`run_id`、oracle 或运行结果分支替代静态形状判定；
- 把放宽应用到 `experiment_id != "exposedpath-q0"` 的 trace；
- 改动使三窗口形式以外的任何 case A/B 输出发生变化，或使 ideal carve fixture 由
  通过变为失败；
- 顺带引入 observability / schema / evaluator / construction 变更；
- 任一 evidence invalid / ambiguous / schema unsupported / hash failure；
- 任何 retry、参数 tuning 或跨 run 拼接。

Gate 6 保持 `FAIL`、Q0 保持 `NOT_RUN`，直至 §9 条件在同一 run 中全部满足。

## 11. Implementation file list

本 amendment implementation 的完整范围：

1. `exposedpath_v141/ab_inputs.py` — 在既有 Q0 controlled 分支内把三窗口边界判定改为
   §4 冻结的五条不等式；不引入 tolerance、不按 case_id 分支、不触碰 `q0_one_phase`
   语义；
2. `tests/test_v141_ab_inputs.py` — §5 列出的形状接受 / fail-closed / 回归测试；
3. `docs/v1_4_1/gate6_phase_spill_amendment_v0_1.md` — 本文件。

明确不涉及：`q0/oracle_cases_v0_2.json`、`canonical_raw.py`、`sync_semantics.py`、
`b_provenance.py`、`a_accounting.py`、`ab_bundle.py`、`q0_real.py`、
`q0_evaluator.py`、`q0_gate.py`、`q0/cuda/exposedpath_q0.cu`、
`docs/v1_4_1/contracts/` 下任何 schema 或 contract 文件、任何 evidence 文件。
