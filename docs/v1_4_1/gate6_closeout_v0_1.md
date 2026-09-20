# Gate 6 Closeout：Q0 资格验证落账与技术总结

状态：**Gate 6 = `PASS`；Q0 = `PASS`**（`Engineering` / `Q0_QUALIFICATION_ONLY`）。本文件是 Gate 6 的唯一 closeout 记录，用于收口当前状态、证据身份、根因映射与实现成熟度；`docs/v1_4_1/research_progress.md` 仍是科研进度事实源。

## 1. 最终状态与证据身份

| 项 | 值 |
|---|---|
| final run | `q0-win-4090-20260920-gate6-final-04` |
| canonical frozen HEAD | `4720881f400762d98f4d0759b1ffb55708968970` |
| implementation commit | `ec945a67f048ff624e3701229d287894b9701ea3` |
| package / analyzer | `0.2.2` |
| formal binary SHA256 | `4DFF82028F4FCFB57D42ABF061AE8962C1867DCE19DF23808D223B425868FC80` |
| binary size | `588800` bytes |
| CUDA source SHA256 | `7D0260CA3D4F62E6A2D1AFFE4943A32E84063B19DE3DCBD823205BAD5160E32D` |
| build receipt schema | `exposedpath-q0-build-receipt/0.1.0`（nvcc CUDA 12.4.131、`-arch=sm_89`） |
| run manifest | schema `exposedpath-q0-run/0.2.1`，SHA256 `4DE8A4A47C01A7318A48EE30BA0B17C8B79776D7AEF3F751098056230657B067` |
| real evidence | 21/21 `REAL_CASE_PASS` |
| synthetic-only cases | `Q0-TERMINAL-TIE-001`、`Q0-SUBMISSION-RACE-001`，均 `PASS` |
| full synthetic regression | 23/23 `SYNTHETIC_PASS`，报告 SHA256 `80A46C4F5B87F584EE2A635A72DB31E919934426ABB418A6E22A3BB78345A2C8` |
| 唯一 gate report | schema `exposedpath-q0-gate/0.2.0`，`23/23`、`verdict=PASS`、`q0_status=PASS`、report count `1`，SHA256 `3A94F8B9B65294D82929EF183C59C4C84177D489F5AE9E8AF56FDDD676178967` |
| 传输归档 | tar.gz SHA256 `CBE51B057D41FB823AE483F5899ADED4D1FF294D4A3F01A740B2AD4586CAE701` |
| handoff manifest | SHA256 `6304061BD68115FEF83F8088BC6E318139AA8E5D04E924C96796221A9806B3EF` |
| 本地解包复核 | 524/524 文件、`28169328` bytes，与 handoff manifest 一致 |

证据位置（2026-09-20 收件时记录的本地位置；若该目录在本机被移动或清理，Gate 6 的证据身份仍以本表中 build receipt／binary SHA／CUDA source SHA／run manifest／唯一 gate report 的 SHA256 为准——本地副本的存续不是 Gate 6 判据）：

- 服务器原始输出：`YLQ_test_q0_v141\engineering_evidence\q0_real\q0-win-4090-20260920-gate6-final-04\`（服务器工作目录见 runbook §1）
- 本地不可变传输件：仓库外 `ExposedPath_Server_Evidence_20260920\gate6-final04\`（tar.gz + handoff manifest）
- 本地解包副本：仓库外 `ExposedPath_Server_Evidence_20260920\gate6-final04-extracted\`

**行尾 provenance 说明（2026-09-20 复核发现，必须保留）：** 上表中的 CUDA source SHA256 `7D0260CA3D4F62E6A2D1AFFE4943A32E84063B19DE3DCBD823205BAD5160E32D` 是**服务器 checkout 字节**的哈希（Windows 行尾：`q0/cuda/exposedpath_q0.cu` 为 `34278` bytes，含 808 个 CRLF）。仓库内同一 blob 的本地字节不同（LF：`33470` bytes，SHA256 `CE8562A120C670D99366F7F0EB1C9C7C1FB2E4280C4130C0F03CED31F159C6B7`）。二者是同一内容的不同行尾表示；在本地以 `core.autocrlf=false` 复核 build receipt 时会得到 LF 哈希，这**不是** source 与 receipt 不一致。复核 source 身份时以 runbook §3 冻结的服务器字节身份与 exact compile argv 为准，不得据此修改 build contract 或重编 binary。

### 1.1 Provenance caveat（必须保留的边界）

final-04 在 prepare 阶段**没有生成** `code_commit.txt`、`frozen_implementation_commit.txt`、`git_status.txt` 三个 sidecar。`post_gate_handoff_provenance.json`（SHA256 `C97678BF0749E7A9C384DBA8694C55AB981E4F11263DE830FC7CDAC0A8AB05B5`，`record_scope=POST_GATE_HANDOFF_ONLY`）明确声明：

- 它不是 pre-run provenance，`substitutes_for_missing_pre_run_sidecars=false`；
- 它没有修改 gate 输入、没有重跑 Q0、没有重跑 gate aggregation。

因此这三个 sidecar 视为**缺失**，任何人不得回填、伪造或把它们当作 run 前产物。final-04 的 identity 由 build receipt、CUDA source SHA、binary SHA、run manifest、collection receipt 与唯一 gate report 共同证明。

## 2. 目标 observation stack、建立了什么 / 没有建立什么

### 2.1 目标 observation stack（本 PASS 的适用范围）

| 项 | 值 |
|---|---|
| OS / 机器 | Windows（实验室服务器） |
| GPU | RTX 4090，UUID `GPU-0d8fafe6-a1e9-33cc-25fb-632316736455` |
| CUDA / Toolchain | CUDA 12.4.131（`nvcc -arch=sm_89`，VC14.39 / v143） |
| Profiler | Nsight 2026.2.1（导出器 3.25.0，`--lazy=false`） |
| Analyzer | package `0.2.2` |
| 数据角色 | `Engineering` / `Q0_QUALIFICATION_ONLY`（`formal_evidence=false`） |

Q0 资格只在这个栈上成立。第二平台（含 Linux）的等价性未被建立，其 launcher、smoke、平台资格检查与 Q0 属 Gate 9。

### 2.2 建立了什么 / 没有建立什么

**建立了：** 在单一目标 observation stack（Windows + RTX 4090 UUID `GPU-0d8fafe6-a1e9-33cc-25fb-632316736455` + CUDA 12.4.131 + Nsight 2026.2.1 + package 0.2.2）上，analyzer 对 23 个必需 Q0 case 的 `W(s)`、terminal、validity、A/B、守恒与 fail-closed 行为与**独立 oracle** 一致，并产出唯一一份 `23/23 + verdict=PASS + q0_status=PASS` 的 gate report。这是**正确性资格**证据。

**没有建立：**

- 不代表 Engineering Pilot、Pilot 或 Formal 数据成立；
- 不代表 Protocol Freeze 通过；
- 不构成 N1/G1/G2 的信息增益或决策增益证据；
- 不建立 Linux 或任何第二平台的等价性；
- 不解释 `EP-ISSUE-16` 的底层机制（WDDM/driver/Runtime/调度层仍不作根因归因）；
- 不把 final-01/02/03 的任何结果追溯升级。

## 3. 根因 → amendment → implementation → verification 映射

Gate 6 的失败簇收敛为四类。为避免把不同性质的问题混在一起，类别定义如下：

- **测量/构造问题**：被测构造本身没有产生 oracle 所需的可观察形态（改微程序或 manifest policy）。
- **观测适配问题**：真实 trace 的 Nsight/schema/scope 与已冻结合同不一致（条件化 adapter，不放宽语义）。
- **语义/analyzer 问题**：S 层对 ownership、phase、sync role 的投影规则错误（需 amendment 修正投影语义）。
- **evaluator/证据聚合问题**：判定或聚合规则错，而非被测语义错（修正比较与窗口规则）。

历史诊断细节保留在 runbook 与 `research_progress.md` 的压缩记录中，不在此复述。

| 类别 | 失败表现（case） | 根因 | 冻结 amendment | implementation | 验证 | 剩余限制 |
|---|---|---|---|---|---|---|
| 测量/构造 | `Q0-KERNEL-MEMOP-001` | 无 warm-up 时 512 MiB H2D 与 10 ms kernel 在真实 device timeline 上串行（overlap=`0`）；证据只支持与 pre-capture same-kernel 条件化强相关，不支持“平台 incapable” | `gate6_construction_amendment_v0_1.md` | manifest policy：仅该 case 使用 `PRE_CAPTURE_SAME_KERNEL_WARMUP`，其余 20 real 为 `NONE`，runtime 完全由 policy 驱动 | final-04 `REAL_CASE_PASS`，A/B `VALID` | 底层机制仍未归因（`EP-ISSUE-16`）；禁止在该平台继续参数搜索或诊断 |
| 观测适配 | r2～r8 系列（Nsight 版本与可选表、`lazy` 零行 KERNEL 表、request scope、target identity 唯一性、graph node tracing） | 真实 SQLite 的 schema/scope 与已冻结 observation contract 不一致 | 无（adapter 修复，随 `EP-G6-02C`～`EP-G6-02I`） | 条件化 adapter + fail closed；不删除 Raw、不放宽语义、不伪造 runtime 映射 | final-04 21/21 real PASS；r2～r8 现场永久 frozen incomplete | 只覆盖已审查的 Nsight 2026.2.1 / 3.25.0 schema；未知 schema 继续 fail closed |
| 语义/analyzer（marker authority 过强） | `Q0-EXTERNAL-001` | request 外的 activity marker 携带当前 request identity，把外部活动错误恢复成当前 invocation | `gate6_marker_ownership_amendment_v0_1.md` | trusted marker authority + External real reason producer | final-04 real PASS | 外部 ownership 只能由满足 trusted marker 条件的证据表达 |
| 语义/analyzer（worker ownership 过弱） | `Q0-MULTITHREAD-ORDERED-001`、`Q0-OVERLAPPING-HOST-SYNC-001` | worker sync/event marker 无法跨线程传播 request/repeat/phase ownership | 同上 | worker sync/event 跨线程 ownership；Multithread 增加纯 host-side `EVENT_RECORD_THREAD_A` marker；External/Multithread/Overlapping 的 synthetic 改走真实 semantics 推导链 | final-04 real 均 PASS | ownership 证据仍必须同线程且完整覆盖 enqueue API |
| 语义/analyzer（registry role 投影） | `Q0-QUERY-001`、`Q0-SYNC-D2H-UNSUPPORTED-001`、`Q0-MULTITHREAD-ORDERED-001`（投影侧） | `NON_SYNC`/`DEPENDENCY_EDGE` 被投影成 semantic sync；无 mapped `cuda_sync` 的 `UNSUPPORTED` API 没有 candidate | `gate6_sync_projection_amendment_v0_1.md` | registry-role-preserving projection（`sync_semantics.py` 与 `ab_inputs.py` 复用同一 helper）＋ UNSUPPORTED API-backed semantic sync（唯一权威 `kind=sync` marker；缺失/重复/冲突 fail closed） | final-04 real 三者均 PASS | 无 case-id / API-name 特判；sync registry 与 oracle expected 均未改动 |
| evaluator/证据聚合 | `Q0-PHASE-SPILL-001`、`Q0-DEVICE-001`（r9 wait-set 顺序） | 窗口发现规则过严（exact boundary equality）；wait-set 成员比较误用 list 顺序 | `gate6_phase_spill_amendment_v0_1.md` ＋ evaluator 集合比较修正 | Q0 controlled 三窗口改用 containment/order/non-overlap rule；仅 `wait_set_activity_labels` 改用无序、无重复的精确成员比较 | final-04 无 `WINDOW_DISCOVERY_INVALID`；21/21 real PASS | 三窗口规则只适用于 Q0 controlled 形态；普通 workload 仍要求 full_request/prefill/decode 三段 |
| evaluator/oracle（Missing-Corr） | `Q0-MISSING-CORR-001` | 删除 correlation 后 submission proof 只剩 GPU-start-before-sync，在目标栈上无法确定性成立 | `gate6_missing_corr_amendment_v0_2.md`（v0.1 superseded） | 回退为 `launch K_UNMAPPED → S_STREAM → cudaStreamSynchronize`；oracle 期望 `primary = MISSING_ACTIVITY_CORRELATION` + `secondary = [SUBMISSION_ORDER_AMBIGUOUS]`；删除 sentinel/watchdog/system-scope atomic 路径 | final-04 real PASS | 新 run 若出现 `submission_evidence = PROVEN`（secondary 不再是 ambiguous）必须 STOP 并重新评审；`can_map_host_memory` 继续必填但值为 `0` 不再拒绝 collection |
| build/provenance 合同 | 全部 case | build contract 缺少 arch 与 provenance；CUDA 12.4 的 system-scope `atomic_ref` 需要显式 `sm_70+` arch | `gate6_q0_build_contract_amendment_v0_1.md` | 固定 `-arch=sm_89`；生成 `<binary>.build_receipt.json`；记录 `can_map_host_memory` | final-04 build receipt PASS；compile argv 恰一次 `-arch=sm_89` | 服务器字节（CRLF）与仓库 blob（LF）是同一内容的不同行尾表示，见 §1 行尾说明 |

Missing-Corr 的修复路径单独说明：`gate6_missing_corr_amendment_v0_1.md` 的 mapped-sentinel deterministic handshake 被诊断证据否决（pure host poll queue ≈30 s；单次 `cudaStreamQuery` 可推进 submission 但污染 synchronization activity；pre-capture same-kernel warm-up 与 `cudaStreamGetFlags` 均无效），由 v0.2 supersede 为上述普通 construction。final-04 的 `Q0-MISSING-CORR-001 = REAL_CASE_PASS` 即该 v0.2 语义的验证。

## 4. 实现成熟度

**已实现并已在真实 RTX 4090 / Nsight 数据上验证：** Canonical Raw → S → A/B → 独立 evaluator 的 Q0 全链路；registry-role-preserving sync 投影；trusted marker authority 与跨线程 worker ownership；Phase-Spill 三窗口规则；`-arch=sm_89` 固定 build contract 与 build receipt；Missing-Corr 的真实 fault → 真实 semantics 推导（含 oracle 的 ambiguous secondary）。

**已实现但仅为离线/合成验证：** v141 计算模块的全部非 GPU 回归路径；`--list-cases` / `--environment-json` 等非 case 入口。合成结果只具 `SYNTHETIC_ONLY` 资格。

**仍在 Gate 6 范围之外（转后续 Gate）：** runner/launcher 的 token 就绪边界与 Pass0/Pass1 parity（Gate 7）；跨平台执行与平台资格（Gate 7/9）；workload、Pilot、Protocol Freeze（Gate 8～12）；N1/G1/G2（Gate 13/14）。

**已关闭、不再需要用于正常前进执行的诊断分支：**

- Missing-Corr submission-progress 系列（host poll / stream query / pre-capture warm-up / `cudaStreamGetFlags`）——全部由 amendment v0.2 收口，禁止重跑；
- KERNEL-MEMOP construction 调参系列（512 MiB/64 MiB、H2D/D2H、memcpy-first、concurrent-host、WDDM deep dive）——construction 已通过 pre-capture same-kernel warm-up policy 恢复，停止继续参数搜索；
- D2D、64 MiB/1 ms、`r11` 及更早的 `rN` 失败现场——保持 frozen incomplete，不 retry/resume；
- Candidate Platform admission 路线（`EP-G6-07`）——Windows/RTX 4090 已在自身 Q0 上通过，该路线不再阻塞前进；仅在需要第二平台（含 Linux Formal 平台）时按 Gate 9 重新启用。

**遗留未决（不影响 Gate 6 verdict）：** `EP-ISSUE-16` 的底层机制未归因；`tests/test_server_smoke_script.py::test_dry_run` 与 `::test_spaces` 两项既有的本地 PowerShell smoke 失败（并入 Gate 7 平台适配步骤处理）；final-01/02/03 永久保持 frozen incomplete。

### 4.1 剩余限制与未来平台资格

| 限制 | 当前边界 | 下一步归属 |
|---|---|---|
| `EP-ISSUE-16` 的底层机制未归因 | 只声明 pre-capture same-kernel warm-up 与该构造恢复强相关；不作 WDDM/driver/Runtime/调度层归因 | 保留为科学记录，不产生新任务 |
| 第二平台（含 Linux）等价性 | 未建立，不声明支持 | Gate 9（平台资格检查：launcher、真实 smoke、Q0） |
| 观测版本敏感性 | adapter 只覆盖已审查的 Nsight `2026.2.1 / 3.25.0` schema；未知 schema 继续 fail closed | Nsight/Toolkit 升级时重新审查 |
| runner/launcher 语义与 parity | token 就绪边界、Pass0/Pass1 parity、平台适配隔离均未完成 | Gate 7（`EP-G7-08`～`EP-G7-11`） |
| 数据资格 | final-04 的 `Engineering` / `Q0_QUALIFICATION_ONLY` 只用于 Q0 正确性资格 | 不得升级为 Pilot/Formal；Pilot 属 Gate 11，Formal 需 Protocol Freeze |
| provenance caveat | 缺失的 prepare-time sidecar 不得回填（见 §1.1） | 永久边界 |
