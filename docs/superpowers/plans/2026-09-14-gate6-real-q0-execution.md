# Gate 6 真实 Q0 执行 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 补齐可在服务器逐 case 执行、派生、独立比较并生成唯一 Gate 报告的真实 Q0 工具链。

**Architecture:** 采集层使用 CUDA Profiler API 控制范围并为每个 case 写不可覆盖 receipt；派生层只修改 Canonical 副本；真实 observed 通过稳定 NVTX label 连接真实区间和 S/A/B，独立 evaluator 与 gate 聚合器不调用被测语义恢复逻辑。

**Tech Stack:** Python 3.12、JSON/JSON Schema、pytest、CUDA C++、NVTX、Nsight Systems CLI。

**Spec:** `docs/superpowers/specs/2026-09-14-gate6-real-q0-execution-design.md`

## Global Constraints

- 不修改 Gate 2 oracle expected、Measurement Contract v0.2、旧 analyzer/runner 或 Raw trace。
- 真实采集前后均保持 `data_role=Engineering`、`formal_evidence=false`。
- 外部命令使用参数数组；每个输出拒绝覆盖；失败不得留下成功 receipt。
- 多 GPU 必须显式选择，记录物理 UUID 与逻辑设备 0 的映射。
- 只有 23 个必需 case 完整且正确时，唯一 Gate 报告才可写 `q0_status=PASS`。

---

### Task 1: 修复 capture 与 GPU 身份合同

**Files:** Modify `q0/cuda/exposedpath_q0.cu`, `exposedpath_v141/q0_execution.py`, `exposedpath_v141/cli.py`, `tests/test_v141_q0_cuda_source.py`, `tests/test_v141_q0_execution.py`.

**Interfaces:** `prepare_q0_run(..., cuda_visible_device: str) -> Path`；命令使用 `--capture-range=cudaProfilerApi`。

- [x] 先写失败测试，要求 CUDA source 调用 Profiler Start/Stop、argv 禁止 NVTX capture、source manifest 记录显式 GPU 选择。
- [x] 运行定向测试确认因当前行为失败。
- [x] 最小实现 CUDA capture 和 manifest/CLI 参数。
- [x] 编译微程序并运行定向测试。
- [x] 提交 `fix: make q0 capture deterministic`。

### Task 2: 单 case 真实采集与 receipt

**Files:** Create `exposedpath_v141/q0_collection.py`, `tests/test_v141_q0_collection.py`; modify CLI.

**Interfaces:** `execute_q0_case(run_manifest: Path, case_id: str) -> Path`；CLI `execute-q0-case`。

- [x] 先写假 nsys/binary 的失败测试，覆盖成功 receipt、工具哈希变化、已有 Raw/receipt、非 native case 和非零退出码。
- [x] 运行测试确认缺接口失败。
- [x] 实现严格 manifest 重载、GPU 环境、结构化 subprocess、日志、Raw 发现/哈希与原子 receipt。
- [x] 运行测试和 CLI smoke。
- [x] 提交 `feat: execute q0 cases with immutable receipts`。

### Task 3: Canonical 故障副本

**Files:** Create `exposedpath_v141/q0_faults.py`, `tests/test_v141_q0_faults.py`; modify CLI.

**Interfaces:** `apply_q0_fault(canonical_manifest: Path, case_id: str, output_dir: Path) -> Path`。

- [x] 先写三个 mutation 和源 bundle 不变的失败测试。
- [x] 运行测试确认缺接口失败。
- [x] 实现确定性 bundle 重写、schema 校验、lineage/hash 与不可覆盖。
- [x] 运行 fault、Canonical loader 和 S 传播测试。
- [x] 提交 `feat: add controlled q0 canonical faults`。

### Task 4: 真实 observed 与独立 evaluator

**Files:** Create `exposedpath_v141/q0_real.py`, `tests/test_v141_q0_real.py`; modify observed schema/evaluator/independence checker/CLI.

**Interfaces:** `build_real_q0_observed(...) -> dict`、`evaluate_q0_observed(...) -> dict`。

- [ ] 先写 fixture 测试，证明 marker->API->activity label 唯一映射、真实区间 B 算术、A 关系和冲突 fail closed。
- [ ] 运行测试确认真实 source kind 被拒绝。
- [ ] 扩展严格 schema 和 adapter；evaluator 只做独立比较与区间算术。
- [ ] 运行 real/synthetic evaluator 与静态独立性测试。
- [ ] 提交 `feat: evaluate real q0 observations`。

### Task 5: 唯一 Q0 Gate 聚合与服务器说明

**Files:** Create `exposedpath_v141/q0_gate.py`, `tests/test_v141_q0_gate.py`, `docs/v1_4_1/q0_server_runbook_windows.md`; modify CLI/progress.

**Interfaces:** `build_q0_gate_report(case_reports: Sequence[Mapping], environment: Mapping) -> dict`；CLI `finalize-q0-gate`。

- [ ] 先写 23-case PASS 和缺失/重复/失败/错误来源/环境缺失的失败测试。
- [ ] 运行测试确认缺接口失败。
- [ ] 实现唯一聚合器和中文 Windows 单 case→批量 runbook。
- [ ] 运行 Q0 定向、compileall、边界和全仓测试；生成 GPU 前就绪证据，Gate6 保持 BLOCKED。
- [ ] 提交 `test: complete real q0 execution readiness`。
