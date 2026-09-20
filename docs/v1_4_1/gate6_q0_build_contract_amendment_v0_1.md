# Gate 6 Q0 Build Contract Amendment v0.1：显式 codegen architecture 与 build provenance

> **后记（2026-09-20）：** 本文档为冻结的 amendment 记录，其 `-arch=sm_89` 与 build receipt 要求不变；正文中“Gate 6 = `FAIL` / Q0 = `NOT_RUN` / Gate 7 `BLOCKED/暂停`”等描述均为批准时刻的历史状态，已由 Gate 6/Q0 `PASS`（`q0-win-4090-20260920-gate6-final-04`，package `0.2.2`）取代。注意 `can_map_host_memory` 的 hard-gate 语义已由 `gate6_missing_corr_amendment_v0_2.md` 收窄为“继续记录且必填、值为 0 不拒绝 collection”。当前状态见 `docs/v1_4_1/research_progress.md` 与 `docs/v1_4_1/gate6_closeout_v0_1.md`。

状态：**批准（2026-09-19）**
适用范围：Gate 6 / Q0 Qualification 的正式 Q0 binary 构建合同与构建 provenance
canonical baseline 分支：`codex/gate6-canonical-baseline`
canonical implementation commit：`2e81f6f9a9ec590d37fb01be9e31f2251645c5d1`
frozen run：`q0-win-4090-20260919-gate6-final-01`（frozen incomplete Engineering run，不得重跑/续跑/重派生/升级）

本文件冻结正式 Q0 binary 的 codegen architecture 规则、build receipt 内容、
`canMapHostMemory` 能力前置检查、provenance 链、scope、zero-diff 清单与 STOP 条件。

本 amendment **不**处理：

- `Q0-MISSING-CORR-001` 的 handshake / sentinel 语义（其 handshake 设计另行定稿，本轮只承接其中
  与本文件直接相关的 `sm_89` codegen 需求与 `canMapHostMemory` 前置检查）；
- Phase-Spill 与 Unified Marker Ownership 的语义规则（分别由
  `gate6_phase_spill_amendment_v0_1.md`、`gate6_marker_ownership_amendment_v0_1.md` 批准）。

本 amendment 不修改 Measurement Contract、Q0 oracle、Canonical、S/A/B 实现与 schema、
evaluator、`q0_gate.py`、execution manifest / run manifest schema、23-case composition
与 Gate 6 PASS 判据。

## 1. Evidence basis

### 1.1 冻结 build 现状（源码事实）

正式 Q0 binary 目前由唯一一处 argv 生成：

```text
build_q0_compile_command(nvcc, source, output, platform)
  -> (nvcc, -std=c++17, -O2, -lineinfo, <source>,
      -Xcompiler=/EHsc | -Xcompiler=-pthread, -lcuda, -o, <output>)
```

该 argv **不含** `-arch` / `-gencode` / `-ccbin`；仓库中不存在环境变量注入 codegen 的路径。
因此当前 target architecture 由 nvcc 的隐式/默认选择决定，属于不可审计、不可复现的构建属性。

### 1.2 服务器记录（用户回传，本轮未复验）

CUDA 12.4.131 / Windows、冻结 flags、**不带** `-arch` 时：

```text
cuda::atomic_ref<..., cuda::thread_scope_system>
  compile_exit_code = 2
  CUDA atomics are only supported for sm_60+ on *nix
  and sm_70+ on Windows.
```

同一服务器显式指定：

```text
nvcc = CUDA 12.4.131
-arch=sm_89
compile/link = PASS
executable created = True
no GPU workload executed
```

因此当前 implicit/default target **不可接受**：正式 Q0 build 必须显式冻结 codegen
architecture。本机 CUDA 13.0 的 compile-only 证据只作支持性材料，不构成 12.4 compatibility proof。

## 2. Architecture contract（冻结）

正式 Q0 binary 统一使用：

```text
-arch=sm_89
```

由 `build_q0_compile_command()` 固定加入，**不新增可变 CLI 参数**（不引入 `--gpu-arch`）。

要求：

- argv 中 `-arch=sm_89` 恰好出现一次；
- 不依赖 build host 当前可见 GPU；
- 不依赖 nvcc default architecture；
- 不允许通过环境变量追加或覆盖 arch；
- 对整份 Q0 binary 统一生效，**不按 case-id 特判**；
- 换 compute capability 必须重新走 build-contract review，不得就地改值。

`exposedpath_v141/cli.py` 保持 **zero-diff**：`build-q0-microbench` 的 `--nvcc` / `--output` /
`--platform` 参数集合与输出文本不变。

SASS-only（不额外生成 PTX forward-compat）是接受的行为：换平台必须重新冻结 build contract，
而不是静默 JIT 重定向到未冻结的 target。

## 3. Build receipt（冻结）

`compile_q0_microbench()` 成功后**自动生成**：

```text
<binary>.build_receipt.json
```

receipt 至少包含：

- `receipt_version`：冻结为 `exposedpath-q0-build-receipt/0.1.0`（仅 build provenance，
  自身不属于 formal Q0 schema，不进入 run/execution manifest）；
- `generated_at_utc`；
- `platform`；
- CUDA source 的 path 与 SHA256；
- nvcc path；
- nvcc `--version` 的完整输出；
- `gpu_arch = "sm_89"`；
- 完整 compile argv；
- binary path、binary size、binary SHA256。

规则：

- receipt 已存在时**拒绝覆盖**（与拒绝覆盖已有 binary 同等处理，防止 stale receipt 与
  新 binary 错配）；
- builder **禁止**自行读取或推断 Git commit；
- nvcc 版本信息取不到时 fail closed（receipt 为必产物，不得静默跳过）。

Git provenance 继续由 server runbook 独立冻结：

```text
HEAD == frozen implementation commit
tracked tree clean
```

由此形成完整 provenance 链：

```text
frozen Git tree
    -> CUDA source SHA256
    -> build receipt / exact argv / nvcc version / sm_89
    -> binary SHA256
    -> q0_run_manifest binary SHA256
```

## 4. `canMapHostMemory` preflight（冻结）

本 amendment 显式批准此前标记的 scope expansion。

> **Supersede 注记（2026-09-20）**：本节中 `can_map_host_memory == 1` 的 formal hard gate、以及
> Missing-Corr case 内的 `properties.canMapHostMemory != 0` native fail-closed guard，已由
> `docs/v1_4_1/gate6_missing_corr_amendment_v0_2.md` **supersede**：sentinel handshake 被 diagnostic
> evidence 否决后，该 capability 不再是正式 Q0 的硬性准入条件。字段本身仍由 `--environment-json` /
> collection 记录并要求存在（缺失仍 fail closed），但 `can_map_host_memory == 0` 不再自动拒绝正式
> collection。§2 的 `-arch=sm_89` 与 §3 的 build receipt 规则保持不变；§1 中
> 「不带 `-arch` 时 system-scope atomic 编译失败」降级为历史依据。

`--environment-json` 新增字段：

```text
can_map_host_memory
```

取值来自 `cudaDevAttrCanMapHostMemory`。`unifiedAddressing` **不是** capability gate。

正式 target preflight 必须在任何 Q0 case 之前证明：

```text
can_map_host_memory == 1
```

`exposedpath_v141/q0_collection.py`：

- selected GPU environment 保存该字段；
- 新采集时该字段必填；
- 缺失即 fail closed。

同时 Missing-Corr case 内仍保留 `properties.canMapHostMemory != 0`，作为最终 native
fail-closed guard。两层都不得用 `unifiedAddressing` 代替。

该字段扩展不升版 collection receipt 的 `schema_version`（保持
`exposedpath-q0-collection/0.2.0`），也不修改 run/execution schema。

## 5. Scope（冻结）

REQUIRED production：

- `exposedpath_v141/q0_execution.py`
  - `build_q0_compile_command()` 固定加入 `-arch=sm_89`；
  - `compile_q0_microbench()` 写 build receipt 并拒绝覆盖已有 receipt。
- `q0/cuda/exposedpath_q0.cu`
  - `print_environment_json()` 输出 `can_map_host_memory`。
- `exposedpath_v141/q0_collection.py`
  - environment probe 映射该字段；`_validate_environment` 将其列为必填。

REQUIRED tests：

- `tests/test_v141_q0_execution.py`
  - compile argv 精确包含 `-arch=sm_89`；
  - build receipt 生成与内容；
  - receipt 覆盖拒绝；
  - source / binary 哈希 provenance。
- `tests/test_v141_q0_cuda_source.py`
  - environment JSON 包含 `can_map_host_memory`。
- `tests/test_v141_q0_collection.py`
  - probe / fixture 新字段；
  - missing field rejection；
  - target environment 保存该字段。

REQUIRED docs：

- 本 amendment；
- implementation 阶段：`docs/v1_4_1/gate6_windows_server_runbook.md`；
- implementation 阶段：`docs/v1_4_1/q0_execution_package_v0_2.md`。

## 6. Zero-diff 清单

- `exposedpath_v141/cli.py`；
- execution manifest 与 `q0_execution_schema_v0_2.json`；
- run manifest schema（`exposedpath-q0-run/0.2.1` 不变）；
- Q0 oracle（`q0/oracle_cases_v0_2.json`）；
- Measurement Contract（`measurement_contract_v0_2.json` / `.md`）；
- Canonical；
- S / A / B 实现与 schema；
- evaluator（`q0_evaluator.py`）；
- `q0_gate.py`；
- 23-case composition；
- Gate 6 PASS criterion。

## 7. Versioning 与 provenance 策略（冻结）

- package `__version__` **不在本 amendment 内修改**；`0.2.0 -> 0.2.1`
  由 Unified Marker Ownership amendment 独立负责；
- execution schema 保持 `exposedpath-q0-execution/0.2.1`；
- run schema 保持 `exposedpath-q0-run/0.2.1`；
- collection receipt schema 保持 `exposedpath-q0-collection/0.2.0`；
- Measurement Contract 与 oracle 版本不变；
- build receipt 使用独立 `receipt_version`，与上述任何 schema 版本解耦。

## 8. Server gate（正式 run 前置，冻结）

在任何新的正式 Q0 run 之前必须逐项成立：

- HEAD == frozen implementation commit；
- tracked tree clean；
- nvcc == CUDA 12.4.131；
- build receipt 存在；
- receipt `gpu_arch == "sm_89"`；
- compile argv 精确包含 `-arch=sm_89`；
- source SHA 与 checkout 一致；
- binary SHA 与 receipt 一致；
- `--list-cases` = 21/21；
- target `can_map_host_memory == 1`；
- 无 ambient build / CUDA 覆盖（含 `NVCC_APPEND_FLAGS`、`CL`、`_CL_` 之外的任何注入）。

任一失败即 STOP；不得通过补加 `-arch`、更换 arch、修改 flags 或环境变量覆盖后重试。

## 9. Invariants

- 构建 argv 唯一、可审计、可复现；同一冻结源码只对应一个冻结 codegen target；
- receipt 与 binary/source 必须互相匹配，任一不匹配即视为构建无效；
- 能力位只用于 fail-closed 前置判定，不参与任何语义结论；
- build contract 变化不改变 Q0 case composition、Gate 6 PASS 判据或任何 accounting 语义；
- `can_map_host_memory` 只回答"该设备能否映射 host memory"，不得被解释为 overlap 或
  任何 exposure 证据。

## 10. Hard STOP

以下任一情形必须立即停止并回报，不得自行扩大 scope：

- arch 可由调用方任意改变；
- 使用 nvcc implicit / default arch；
- 通过 environment variable 注入 codegen；
- receipt 与实际 binary 或 source 不匹配；
- `can_map_host_memory != 1`；
- 为解决 Missing-Corr 顺带修改 schema / oracle / contract / evaluator；
- 新增第四个 production 文件或修改第 5 节之外的测试文件；
- 静默更换 arch 或 fallback 到未冻结的 codegen 形式。

## 11. Migration / acceptance

1. amendment 批准（本文件）；
2. unified implementation（production / tests / docs，同一 implementation commit）；
3. offline validation：
   - targeted tests（`tests/test_v141_q0_execution.py`、`tests/test_v141_q0_cuda_source.py`、
     `tests/test_v141_q0_collection.py`）；
   - `tests/test_v141_q0_*.py` offline regression；
   - `python -m compileall -q exposedpath_v141 tests`；
   - `git diff --check`；
4. server rebuild + identity verification（compile-only，不运行任何 Q0 case）；
5. 所有已批准 amendment 在同一 implementation commit 冻结后，才允许新 run-id 下**唯一一次**
   完整 21 real + 2 synthetic Q0；
6. 唯一 gate report 达 23/23 才可能使 Gate 6 PASS。

当前正式状态保持：Gate 6 = `FAIL`、Q0 = `NOT_RUN`、Gate 7 = `BLOCKED/暂停`、Gate 8 未启动。
