# Gate 5 A/B 与派生层实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: 使用 `subagent-driven-development` 按任务逐项实施；每项任务必须先写失败测试，再写最小实现，再独立复审。

**目标：** 实现符合 Measurement Contract v0.2 的 A/B 分析器与只读 A/B 的 D/Exposure Signature 派生层，并用确定性合成数据和历史 Engineering trace 验证 fail-closed 行为。

**架构：** Canonical Raw 与 S 通过严格双输入适配层联结；共享区间模块只处理整数半开区间；A 与 B 分别投影；A/B bundle 通过 schema 校验后不可覆盖写出；派生层只能读取 A/B bundle。旧 `analysis/exposed_accounting.py`、SQLite 和 Nsight 私有表不进入新版依赖链。

**技术栈：** Python 3、标准库、JSON Schema、gzip JSONL、pytest、AST 静态边界检查、现有 `exposedpath_v141` CLI。

**规范：** `docs/superpowers/specs/2026-09-12-gate5-accounting-design.md`

## 全局约束

- 当前属于 Engineering/Pre-Pilot；任何离线通过均不得写成 Q0、Pilot 或 Formal 已通过。
- 不修改 benchmark、runner、旧 analyzer 或 Raw trace。
- 每个业务代码提交必须同步更新 `docs/v1_4_1/research_progress.md`，只记录当时实际完成的证据。
- 新模块不得导入 `sqlite3`、引用 Nsight 私有表名或调用 `analysis/exposed_accounting.py`。
- 必需事实缺失、schema/哈希/lineage 不一致时 fail closed；不得静默 fallback 或用 0 代替未知。
- 所有时长使用整数纳秒和半开区间 `[start_ns, end_ns)`。
- 每项任务的实施者不得自审；独立复审发现 Critical/Important 后必须返修并重新复审。

---

## Task 1：冻结 A/B 与派生层机器 schema

**文件：**

- 新建：`docs/v1_4_1/contracts/ab_schema_v0_2.json`
- 新建：`docs/v1_4_1/contracts/derived_schema_v0_2.json`
- 新建：`tests/test_v141_ab_schemas.py`
- 修改：`docs/v1_4_1/research_progress.md`

### 步骤

- [ ] 写失败测试：加载两个 schema，验证 `$id`、`schema_version`、必需字段与 `additionalProperties: false`；测试非法 A 守恒字段、B 时长错误填零、B 聚合总量字段、派生输入 lineage 缺失均被拒绝。
- [ ] 运行 `python -m pytest -q -p no:cacheprovider tests/test_v141_ab_schemas.py`，确认因 schema 文件不存在而失败。
- [ ] 实现 `exposedpath-ab/0.2.0`：manifest、A window record、B sync record 三个 `$defs`；B 只允许冻结字段，不允许跨同步 total。
- [ ] 实现 `exposedpath-derived/0.2.0`：manifest、D window、Exposure Signature；signature 只保存 A 向量/比例、B 状态 count、有效 B 的 median/p90 和分布。
- [ ] 使用 Measurement Contract 的字段名；B 状态固定为 `B_VALID/B_NOT_APPLICABLE/B_AMBIGUOUS/B_INVALID`，非 `B_VALID` 的时长必须为 `null`。
- [ ] 更新进度清单为 Gate 5 schema 已冻结、代码尚未完成，Gate verdict 保持 `NOT_RUN`。
- [ ] 运行定向测试并提交：`feat: freeze gate 5 schemas`。

### 完成条件

- 两份 schema 自身可被 JSON Schema 校验器加载；正例通过、所有反例失败；未引入未冻结指标或研究解释字段。

---

## Task 2：实现严格双输入、联结与窗口发现

**文件：**

- 新建：`exposedpath_v141/ab_inputs.py`
- 新建：`tests/test_v141_ab_inputs.py`
- 修改：`docs/v1_4_1/research_progress.md`

### 接口

```python
@dataclass(frozen=True)
class ABInputs:
    canonical: CanonicalBundle
    s_manifest: dict[str, object]
    s_records: tuple[dict[str, object], ...]
    windows: tuple[RequestPhaseWindow, ...]
    global_quality_reasons: tuple[str, ...]

def load_ab_inputs(canonical_manifest: Path, s_manifest: Path) -> ABInputs: ...
def discover_request_phase_windows(canonical: CanonicalBundle) -> tuple[RequestPhaseWindow, ...]: ...
```

### 步骤

- [ ] 写失败 fixture：最小 Canonical bundle、S bundle 和结构化 `EXPOSEDPATH_JSON_V1` request/prefill/decode NVTX。
- [ ] 写失败测试：schema/hash/contract 版本、source SQLite hash、Canonical manifest hash、sync identity、wait-set activity、terminal activity 任一不一致均抛出明确异常且不生成输出。
- [ ] 写失败测试：每个 S `sync_id` 与 Canonical physical sync 必须一一对应；S 中重复、缺失或多余 sync 均拒绝。
- [ ] 写失败测试：有效 full_request/prefill/decode 产生三个唯一窗口；缺失、重复、相交、边界不连续时只记录可机器读取的窗口发现失败，不猜测窗口。
- [ ] 运行定向测试，确认缺实现而失败。
- [ ] 实现 S manifest、gzip JSONL 和哈希校验；严格核对 S 声明的 contract、registry 与 Canonical lineage。
- [ ] 仅用 Canonical 事实建立 API/activity/ownership 索引；不得重算 S 的 `W(s)`、terminal 或 validity。
- [ ] 实现结构化窗口发现，接受 `full_request/prefill/decode`；固定输出数为 1 时允许空 decode，其余窗口使用半开区间。
- [ ] dropped records、clock 或 invocation identity 全局失败写入 `global_quality_reasons`；证据结构损坏与研究证据 invalid 必须区分。
- [ ] 更新进度清单，运行 `python -m pytest -q -p no:cacheprovider tests/test_v141_ab_inputs.py tests/test_v141_s_bundle.py`，提交：`feat: add strict ab input adapter`。

### 完成条件

- 正确 bundle 可稳定加载；所有结构/lineage 冲突 fail closed；窗口只来自结构化身份；旧 trace 不会因时间顺序被猜出 request。

---

## Task 3：实现共享半开区间工具

**文件：**

- 新建：`exposedpath_v141/intervals.py`
- 新建：`tests/test_v141_intervals.py`
- 修改：`docs/v1_4_1/research_progress.md`

### 接口

```python
Interval = tuple[int, int]

def intersect_interval(left: Interval, right: Interval) -> Interval | None: ...
def clip_intervals(intervals: Iterable[Interval], window: Interval) -> tuple[Interval, ...]: ...
def union_intervals(intervals: Iterable[Interval]) -> tuple[Interval, ...]: ...
def interval_length(intervals: Iterable[Interval]) -> int: ...
def atomic_segments(window: Interval, boundaries: Iterable[int]) -> tuple[Interval, ...]: ...
```

### 步骤

- [ ] 写失败测试覆盖：相交、相邻合并、嵌套、重复、多线程重叠 union、窗口裁剪、空区间、逆序/负时间拒绝、原子切分无重复无缺口。
- [ ] 运行定向测试，确认缺实现而失败。
- [ ] 实现无研究语义、纯整数、确定性排序的最小区间函数。
- [ ] 对所有公开接口校验 `start <= end`；空区间不产生正长度片段；长度不得由逐纳秒枚举计算。
- [ ] 更新进度清单，运行 `python -m pytest -q -p no:cacheprovider tests/test_v141_intervals.py`，提交：`feat: add half-open interval primitives`。

### 完成条件

- 所有边界测试通过；模块不知道 sync、A、B、CUDA 或 phase 的含义。

---

## Task 4：实现 A 的互斥墙钟记账

**文件：**

- 新建：`exposedpath_v141/a_accounting.py`
- 新建：`tests/test_v141_a_accounting.py`
- 修改：`docs/v1_4_1/research_progress.md`

### 接口

```python
def calculate_a_windows(inputs: ABInputs) -> tuple[dict[str, object], ...]: ...
def validate_a_record(record: Mapping[str, object]) -> None: ...
```

### 步骤

- [ ] 写可手算失败 fixture：一个 100 ns window，同时含 Host 空隙、submit/non-submit API、valid sync、`W(s)` kernel/memop、invalid sync 和跨 phase activity。
- [ ] 写失败测试验证固定优先级：全局/无效 sync→unattributed；valid sync 中活动执行→device_wait；valid sync 空档→sync_residual；明确 API→cuda_api；其余→host_path。
- [ ] 写失败测试验证 API 二级分类：唯一 enqueue/event-record/stream-wait 为 submit；registry 非阻塞 query 为 non-submit；未知或并发冲突为 unattributed。
- [ ] 写失败测试验证 device-wait 二级分类：kernel-only、memop-only、mixed；未知类型进入 unattributed。
- [ ] 写失败测试验证多线程 API interval union、同步重叠、phase clipping、0 ns decode，以及每个窗口整数守恒。
- [ ] 运行定向测试，确认缺实现而失败。
- [ ] 用 Task 3 原子区间切分实现唯一分类，不按线程时长直接累加。
- [ ] 输出五项顶层 A、五项二级 A、窗口长度、重复/未覆盖/越界检查和 reason codes；`A_host_path` 不命名为 CPU busy。
- [ ] 全局质量失败时，有效已知窗口全部进入 `A_unattributed`；窗口不可唯一恢复时不生成 A 记录。
- [ ] 更新进度清单，运行 `python -m pytest -q -p no:cacheprovider tests/test_v141_a_accounting.py tests/test_v141_intervals.py`，提交：`feat: implement conservative a accounting`。

### 完成条件

- 每个 A 记录满足顶层和二级精确守恒；所有含糊情况保守归入 unattributed；无时间重叠推导 dependency。

---

## Task 5：实现 B 的单同步 provenance

**文件：**

- 新建：`exposedpath_v141/b_provenance.py`
- 新建：`tests/test_v141_b_provenance.py`
- 修改：`docs/v1_4_1/research_progress.md`

### 接口

```python
def calculate_b_syncs(inputs: ABInputs) -> tuple[dict[str, object], ...]: ...
def validate_b_record(record: Mapping[str, object]) -> None: ...
```

### 步骤

- [ ] 从 `q0/oracle_cases_v0_2.json` 选取提前完成、同步期间完成、跨流无依赖、terminal 唯一/并列、valid-empty、ambiguous、invalid 案例，先写失败测试。
- [ ] expected timing 必须调用独立 `q0_oracle.calculate_expected_timing` 或使用预写常量；测试不得调用 B 实现生成 expected。
- [ ] 写失败测试验证一条 S physical sync 恰有一条 B、`sync_id` 集合完全一致、输出顺序确定。
- [ ] 写失败测试验证状态投影：`VALID_NONEMPTY→B_VALID`；`VALID_EMPTY→B_NOT_APPLICABLE`；ambiguous/invalid 对应 B 状态且全部时长为 `null`。
- [ ] 写失败测试验证 `W(s)` union 的 pre-sync hidden、sync 内 exposed、terminal pre/overlap 和 return-tail；跨 phase 标记保留但不裁剪 B 生命周期。
- [ ] 写失败测试拒绝任何 `b_total`、跨 sync sum 或把未知填 0 的接口/字段。
- [ ] 运行定向测试，确认缺实现而失败。
- [ ] 实现 per-sync B；直接信任并投影 S 的 wait-set/terminal/validity，不重算依赖。
- [ ] 更新进度清单，运行 `python -m pytest -q -p no:cacheprovider tests/test_v141_b_provenance.py tests/test_v141_q0_oracle.py`，提交：`feat: implement per-sync b provenance`。

### 完成条件

- B 与 S 一一对应；所有状态和时长符合冻结合同；公开输出不提供可误用的跨同步总量。

---

## Task 6：实现 A/B bundle、CLI 与边界检查

**文件：**

- 新建：`exposedpath_v141/ab_bundle.py`
- 新建：`tests/test_v141_ab_bundle.py`
- 修改：`exposedpath_v141/cli.py`
- 修改：`scripts/verify_canonical_raw_boundary.py`
- 修改：`tests/test_v141_canonical_raw.py`
- 修改：`docs/v1_4_1/research_progress.md`

### CLI

```text
python -m exposedpath_v141 analyze-ab \
  --canonical-manifest PATH \
  --s-manifest PATH \
  --output-dir PATH
```

### 步骤

- [ ] 写失败测试：CLI 正例生成 `ab_manifest.json`、`a_window_records.jsonl.gz`、`b_sync_records.jsonl.gz`；再次写同目录拒绝覆盖。
- [ ] 写失败测试：记录逐条 schema 校验；manifest 保存输入文件 SHA-256、contract/schema/analyzer 版本、data role、质量状态、counts、validity 分布和资格限制。
- [ ] 写失败测试：相同输入在不同目录运行，两个 JSONL gzip 的 SHA-256 完全相同；gzip `mtime=0`。
- [ ] 扩展静态边界测试，覆盖 `ab_inputs.py`、`a_accounting.py`、`b_provenance.py`、`ab_bundle.py`，拒绝 sqlite3、Nsight 私有表名和旧 accounting 导入。
- [ ] 运行定向测试，确认缺实现而失败。
- [ ] 实现 schema 校验、确定性 JSONL、临时目录成功后原子改名、不可覆盖写出与严格 bundle loader。
- [ ] 在 CLI 中注册 `analyze-ab`，失败时不得残留看似完整的输出目录。
- [ ] 更新进度清单，运行 `python -m pytest -q -p no:cacheprovider tests/test_v141_ab_bundle.py tests/test_v141_canonical_raw.py`，提交：`feat: add versioned ab bundle and cli`。

### 完成条件

- CLI 可从合成 Canonical+S 生成可重载、可校验、确定性的 A/B bundle；错误路径无部分产物；架构边界检查通过。

---

## Task 7：实现只读 A/B 的 D 与 Exposure Signature

**文件：**

- 新建：`exposedpath_v141/derived.py`
- 新建：`tests/test_v141_derived.py`
- 修改：`exposedpath_v141/cli.py`
- 修改：`scripts/verify_canonical_raw_boundary.py`
- 修改：`docs/v1_4_1/research_progress.md`

### CLI

```text
python -m exposedpath_v141 derive-exposure \
  --ab-manifest PATH \
  --output-dir PATH
```

### 步骤

- [ ] 写失败测试：每个 A window 的 `D_margin`、`D_score` 正确，分母 0 时 score 为 `null`。
- [ ] 写失败测试：signature 按 `(phase, sync_kind, sync_origin, callsite_id)` 汇总 B 状态 count、仅 B_VALID 的 median/nearest-rank p90、terminal/provenance 分布；不得产生 B total。
- [ ] 写失败测试：派生层只接收 A/B manifest；schema/hash/lineage 错误拒绝；相同输入的 JSONL gzip 哈希稳定；已有目录拒绝覆盖。
- [ ] 写 AST 失败测试：`derived.py` 不得导入 Canonical/S 模块，不得出现 Raw/S 时间字段或 SQLite/Nsight 私有表名。
- [ ] 运行定向测试，确认缺实现而失败。
- [ ] 实现严格 A/B bundle loader、D、median、nearest-rank p90、signature 和不可覆盖派生 bundle。
- [ ] 输出只保留导航与机制摘要，不生成“瓶颈、根因、优化上界”等标签。
- [ ] 更新进度清单，运行 `python -m pytest -q -p no:cacheprovider tests/test_v141_derived.py tests/test_v141_ab_bundle.py`，提交：`feat: derive exposure summaries from ab only`。

### 完成条件

- 派生结果可完全由 A/B 重建；静态边界证明它未回读 Raw/S；统计规则和空集合行为确定。

---

## Task 8：历史 Engineering 回归、全量验证与 Gate 复审

**文件：**

- 新建：`engineering_evidence/ab_v0_2/historical_regression.json`
- 修改：`docs/v1_4_1/research_progress.md`
- 按审查需要修改：Gate 5 新增模块与测试

### 步骤

- [ ] 对历史 `w01_p128_b1_o16.nsys-rep` 只读导出到工作树内临时目录，固定使用 `nsys export --lazy=false`；不得覆盖原始 trace。
- [ ] 运行 `SQLite -> Canonical Raw -> S -> A/B`；验证旧 trace 因缺结构化 request identity 不产生合格 A window，446 条 S invalid 投影为 446 条 `B_INVALID`，Q0 仍为 `NOT_RUN`。
- [ ] 把命令、工具版本、输入 SHA-256、输出 counts/hash、资格结论和限制写入 Engineering evidence；清理前先核对临时目录绝对路径位于当前 worktree。
- [ ] 运行 Gate 5 全部定向测试、边界脚本、合同校验和 `python -m compileall exposedpath_v141`。
- [ ] 运行全量 `python -m pytest -q -p no:cacheprovider`，只允许基线已有的两项 PowerShell smoke 失败；任何新增失败必须修复。
- [ ] 由独立 reviewer 审查完整 Gate 5 diff；Critical/Important 必须修复并重审。
- [ ] 仅当 schema/CLI、严格联结、A 守恒、B 一一对应、Q0 合成对照、AB-only 派生、历史 fail-closed 和独立复审全部满足时，将 Gate 5 verdict 更新为 `PASS`。
- [ ] 明确 Gate 6 仍为 `BLOCKED`：GPU 前只可继续实现 CUDA 微程序、manifest、合成 trace 自动对照与 dry-run；真实 Q0 trace 和最终 verdict 需要 GPU。
- [ ] 提交：`test: complete gate 5 engineering validation`。

### 完成条件

- Gate 5 全部离线验收项有可复查证据；历史数据资格未升级；全量测试无新增失败；独立复审无 Critical/Important。

---

## 最终验收命令

```powershell
python -m compileall exposedpath_v141
python -m exposedpath_v141 validate-contract
python scripts/verify_q0_oracle_independence.py
python scripts/verify_canonical_raw_boundary.py
python -m pytest -q -p no:cacheprovider tests/test_v141_ab_schemas.py tests/test_v141_ab_inputs.py tests/test_v141_intervals.py tests/test_v141_a_accounting.py tests/test_v141_b_provenance.py tests/test_v141_ab_bundle.py tests/test_v141_derived.py
python -m pytest -q -p no:cacheprovider
```

验收报告必须分别写明：已验证事实、仍属推断的内容、环境限制、跳过项、既有失败、Gate 5 verdict，以及 Gate 6/Q0 的阻塞状态。
