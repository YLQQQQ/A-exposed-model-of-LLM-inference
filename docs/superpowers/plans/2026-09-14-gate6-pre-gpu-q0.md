# Gate 6 GPU 前 Q0 执行包 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在没有真实 GPU 执行证据的条件下，完成可编译、可 dry-run、可机器核验的 Q0 执行包，并保持 Gate 6 为 `BLOCKED`。

**Architecture:** 以 Gate 2 的 23 个独立 oracle case 为唯一标准答案来源；新增执行 manifest 将每个 case 映射到原生 CUDA、真实 trace 后受控故障注入或纯合成 Canonical 三种执行策略。CUDA 程序只制造已冻结的同步/completion 情形；Python 执行层负责严格校验合同、生成不可覆盖的 Engineering run manifest/结构化命令和比较标准化 observed 结果，不从 construction 推导 expected。

**Tech Stack:** Python 3.12、JSON/JSON Schema、pytest、CUDA C++/NVTX、Nsight Systems 命令数组。

**Spec:** `docs/v1_4_1/q0_oracle_design_v0_2.md`、`docs/v1_4_1/pre_gpu_readiness_design_v0_1.md`

## Global Constraints

- 当前数据角色只能是 `Engineering`，所有产物必须写明 `q0_status=NOT_RUN`、`formal_evidence=false`。
- 不修改 Measurement Contract v0.2、Gate 2 oracle expected、旧 analyzer 或 runner。
- 23 个 `required_for_q0` case 必须在执行 manifest 中恰好出现一次；未知、缺失、重复或策略不一致一律 fail closed。
- 原生 CUDA case 使用稳定的 `case_id`、`activity_label`、`sync_label`；不得以 Nsight 行号或时间顺序作为身份。
- 无法稳定由真实硬件制造的 terminal tie、submission race、dropped record、缺失 correlation 和 graph mapping 缺失必须显式声明故障注入策略。
- dry-run 只生成命令与 manifest，不执行 GPU、Nsight 或 analyzer，不得输出 Q0 PASS。
- Q0 evaluator 只比较已给定 observed 与人工 expected，不允许恢复 `W(s)`、选择 terminal 或调用 S/A/B 计算逻辑。
- 输出目录拒绝覆盖；路径使用 `pathlib`，外部命令使用结构化参数数组。

---

### Task 1: 冻结 Q0 执行合同与 23-case 映射

**Files:**
- Create: `docs/v1_4_1/contracts/q0_execution_schema_v0_2.json`
- Create: `q0/execution_manifest_v0_2.json`
- Create: `exposedpath_v141/q0_execution.py`
- Create: `tests/test_v141_q0_execution.py`
- Modify: `docs/v1_4_1/research_progress.md`

**Interfaces:**
- Consumes: `load_oracle_bundle(root: Path | None) -> dict[str, Any]`
- Produces: `load_q0_execution_manifest(root: Path | None) -> dict[str, Any]`、`validate_q0_execution_manifest(manifest, oracle) -> None`

- [ ] **Step 1: Write the failing tests** — 使用最小 literal manifest 验证合法输入；验证缺 case、额外 case、重复 case、非 Engineering 资格、策略缺少 seed/mutation、标签集合与 oracle 不一致均被拒绝。
- [ ] **Step 2: Run tests to verify RED** — `python -m pytest -q -p no:cacheprovider tests/test_v141_q0_execution.py -k manifest`，预期因模块不存在失败。
- [ ] **Step 3: Write minimal implementation** — 定义版本、资格、三种策略、每个 case 的 `synthetic_profile`、stable label selector 与严格集合等价检查；提交 23-case 执行 manifest。核心接口固定为：

```python
def validate_q0_execution_manifest(
    manifest: Mapping[str, Any], oracle: Mapping[str, Any]
) -> None: ...

def load_q0_execution_manifest(root: Path | None = None) -> dict[str, Any]: ...
```
- [ ] **Step 4: Run tests to verify GREEN** — 同一命令全部通过，并运行 `python -m exposedpath_v141 validate-q0-oracle` 确认未改 oracle。
- [ ] **Step 5: Commit** — `git commit -m "feat: freeze q0 execution contract"`。

### Task 2: 实现无 GPU 可编译的 CUDA/NVTX 微程序

**Files:**
- Create: `q0/cuda/exposedpath_q0.cu`
- Create: `tests/test_v141_q0_cuda_source.py`
- Modify: `exposedpath_v141/q0_execution.py`
- Modify: `exposedpath_v141/cli.py`
- Modify: `docs/v1_4_1/research_progress.md`

**Interfaces:**
- Consumes: 执行 manifest 的 `native_seed_case_id`、activity/sync labels
- Produces: executable CLI `--list-cases` 与 `--case <id> --run-id <id>`；Python `build_q0_compile_command(...) -> tuple[str, ...]`

- [ ] **Step 1: Write the failing tests** — 命令构造必须为参数数组且不依赖 shell；编译后 `--list-cases` 的集合必须与 manifest 中所有 native seed case 完全相等；未知 case 返回非零且不初始化 GPU。
- [ ] **Step 2: Run tests to verify RED** — 定向测试预期因源文件/接口不存在失败。
- [ ] **Step 3: Write minimal implementation** — 使用唯一 kernel tag、NVTX request/phase/sync/marker 身份、stream/device/context/event/query/sync-copy/graph 等最小 case；list/参数错误路径位于任何 CUDA 初始化之前。命令构造接口固定为：

```python
def build_q0_compile_command(
    nvcc: Path, source: Path, output: Path, *, platform: str
) -> tuple[str, ...]: ...
```
- [ ] **Step 4: Run tests to verify GREEN** — 用本机 `nvcc` 编译到临时目录并运行 `--list-cases`；不得运行 case；无 nvcc 环境只允许明确 skip 编译测试，manifest/命令测试仍须通过。
- [ ] **Step 5: Commit** — `git commit -m "feat: add controlled q0 cuda microbench"`。

### Task 3: 实现跨平台 dry-run 与不可覆盖 run manifest

**Files:**
- Modify: `exposedpath_v141/q0_execution.py`
- Modify: `exposedpath_v141/cli.py`
- Modify: `tests/test_v141_q0_execution.py`
- Create: `docs/v1_4_1/q0_execution_package_v0_2.md`
- Modify: `docs/v1_4_1/research_progress.md`

**Interfaces:**
- Produces: `prepare_q0_run(...) -> Path`；CLI `prepare-q0-run --output-dir ... --binary ... --nsys ... --platform windows|linux`
- Output: `q0_run_manifest.json`，内含输入哈希、23-case 计划、逐 case argv、环境待采字段、`PREPARED_NOT_EXECUTED/NOT_RUN` 资格。

- [ ] **Step 1: Write the failing tests** — Windows/Linux 路径含空格时 argv 保持独立；缺 binary/nsys、重复输出目录、非法平台、非 23-case 计划 fail closed；dry-run 不创建 `.nsys-rep` 或执行外部程序。
- [ ] **Step 2: Run tests to verify RED** — 预期缺接口失败。
- [ ] **Step 3: Write minimal implementation** — 为每个 case 生成单独 trace 前缀与 `nsys profile` argv；记录 executable/oracle/execution manifest/source SHA-256 及空缺的 GPU/driver 字段。接口固定为：

```python
def prepare_q0_run(
    output_dir: Path, binary: Path, nsys: Path, platform: str, run_id: str
) -> Path: ...
```
- [ ] **Step 4: Run tests to verify GREEN** — 定向 pytest 与 CLI dry-run 均通过；检查输出 JSON 可重载、不能覆盖、无 Q0 PASS 字样。
- [ ] **Step 5: Commit** — `git commit -m "feat: prepare q0 runs without gpu"`。

### Task 4: 实现合成 Canonical 执行器与独立 observed 对照器

**Files:**
- Create: `docs/v1_4_1/contracts/q0_observed_schema_v0_2.json`
- Create: `exposedpath_v141/q0_synthetic.py`
- Create: `exposedpath_v141/q0_evaluator.py`
- Create: `tests/test_v141_q0_synthetic.py`
- Create: `tests/test_v141_q0_evaluator.py`
- Modify: `scripts/verify_q0_oracle_independence.py`
- Modify: `exposedpath_v141/cli.py`
- Modify: `docs/v1_4_1/research_progress.md`

**Interfaces:**
- Synthetic executor consumes: 执行 manifest 中逐 case 的显式 `synthetic_profile`，构造 Canonical 事实并调用正式 S/A/B；不得读取 oracle expected 来构造输入。
- Evaluator consumes: 人工 oracle 与标准化 observed JSON；不消费 dependency edges，不导入 S/A/B 计算模块。
- Produces: `run_synthetic_q0(...) -> Path`、`evaluate_q0_observed(...) -> dict[str, Any]`；CLI `run-q0-synthetic`。GPU 前只能输出 `SYNTHETIC_PASS` 或 `FAIL`，永不输出 Q0 PASS。

- [ ] **Step 1: Write the failing tests** — 23 个显式 synthetic profile 必须通过正式 S/A/B 生成 observed，再与 oracle 的集合/terminal/validity/B/status 逐项对照；删除 case、未知 label、错误 wait-set、错误 primary reason、错误 terminal、错误 B 状态必须产生 mismatch 和非零 CLI。测试同时证明 synthetic builder 不读取 `case["expected"]`。
- [ ] **Step 2: Run tests to verify RED** — 预期缺 synthetic executor/evaluator 失败。
- [ ] **Step 3: Write minimal implementation** — synthetic 模块只负责构造输入和调用被测实现；evaluator 严格校验 schema/哈希/覆盖，独立比较 stable labels 与 frozen expected。接口固定为：

```python
def run_synthetic_q0(output_dir: Path) -> Path: ...

def evaluate_q0_observed(
    oracle: Mapping[str, Any], observed: Mapping[str, Any]
) -> dict[str, Any]: ...
```

报告必须写明 `evidence_scope=SYNTHETIC_ONLY`、`q0_status=NOT_RUN`。
- [ ] **Step 4: Run tests to verify GREEN** — evaluator、oracle independence、合同和 Gate 5 定向测试通过。
- [ ] **Step 5: Commit** — `git commit -m "feat: add independent q0 result evaluator"`。

### Task 5: GPU 前集成验收与进度事实源更新

**Files:**
- Create: `engineering_evidence/q0_pre_gpu_v0_2/readiness_report.json`
- Modify: `docs/v1_4_1/research_progress.md`

**Interfaces:**
- Consumes: Tasks 1–4 的合同、程序、dry-run manifest 与测试输出
- Produces: 唯一 GPU 前 Engineering 就绪报告；Gate 6 仍为 `BLOCKED`

- [ ] **Step 1: Run focused verification** — 执行 manifest/schema、CUDA compile/list、dry-run、evaluator、oracle independence、Canonical boundary、Gate 5 定向测试。
- [ ] **Step 2: Run full non-GPU suite** — `python -m pytest -q -p no:cacheprovider`，分开记录新增失败与两项既有 PowerShell smoke 失败。
- [ ] **Step 3: Write evidence and progress** — `EP-G6-01/02` 仅在实际完成条件满足后勾选；`EP-G6-03/04/05` 保持受阻；记录 compiler 版本、命令、哈希、跳过项和数据角色。
- [ ] **Step 4: Verify artifacts** — JSON 重载、`python -m compileall exposedpath_v141`、`git diff --check`、工作树无临时 binary/trace。
- [ ] **Step 5: Commit** — `git commit -m "test: complete gate 6 pre-gpu readiness"`。
