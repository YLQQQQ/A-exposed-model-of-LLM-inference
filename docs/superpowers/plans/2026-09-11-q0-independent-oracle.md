# Q0 独立标准答案实施计划

> **供执行代理使用：** 必须按 `executing-plans` 逐任务执行；每个任务均遵循测试先行，步骤使用复选框记录。

**目标：** 完成 ExposedPath Gate 2，为 Q0 受控案例预先写定、可机器校验且独立于正式 analyzer 的标准答案。

**架构：** 使用一份版本化 JSON 保存受控结构与手工 expected，活动通过稳定语义标签识别，不绑定 Nsight 临时行号。`q0_oracle.py` 只验证和读取标准答案，并用独立区间并集计算已给定 `W(s)` 的时间关系；它不从 trace 恢复 dependency、`W(s)` 或 terminal，也不导入未来 S/A/B 实现。

**技术栈：** Python 3 标准库、JSON、pytest、AST 静态导入检查、Markdown、Git。

**规范依据：** `docs/v1_4_1/measurement_contract_v0_2.md`、`docs/v1_4_1/contracts/measurement_contract_v0_2.json`、`docs/current/ExposedPath_实验协议.docx` 第三章。

## 全局约束

- Gate 2 只完成 oracle 设计与离线自检；不声称真实 CUDA/Nsight Q0 已运行。
- expected 的 `W(s)` 和 terminal 必须人工写定，不能由 dependency traversal 或 analyzer 分类函数生成。
- 数值时间仅用于合成案例的独立区间算术；真实 CUDA 案例比较稳定语义标签和关系，不要求预知运行时纳秒值。
- 必需覆盖 stream、device、context、event、completed-before、valid-empty、无关重叠、terminal tie、ownership、missing mapping、dropped records、submission race、default stream、phase spill 和 invocation bleed。
- Q0 文件不得导入 `analysis`、旧 `exposedpath` 或未来 `raw/sync/accounting` 实现模块。

---

### 任务 1：建立只读 oracle 校验器

**文件：**

- 新建：`tests/test_v141_q0_oracle.py`
- 新建：`exposedpath_v141/q0_oracle.py`

**接口：**

- `validate_oracle_bundle(bundle: Mapping[str, Any]) -> None`
- `load_oracle_bundle(root: Path | None = None) -> dict[str, Any]`
- `calculate_expected_timing(case: Mapping[str, Any], sync_label: str) -> dict[str, int | None]`

- [x] **步骤 1：写失败测试**

```python
def test_duplicate_case_id_is_rejected():
    bundle = literal_bundle()
    bundle["cases"].append(deepcopy(bundle["cases"][0]))
    with pytest.raises(OracleValidationError, match="重复 case_id"):
        validate_oracle_bundle(bundle)


def test_oracle_does_not_infer_wait_set():
    bundle = literal_bundle()
    del bundle["cases"][0]["expected"]["syncs"][0]["wait_set_activity_labels"]
    with pytest.raises(OracleValidationError, match="wait-set 标准答案"):
        validate_oracle_bundle(bundle)
```

- [x] **步骤 2：运行红灯**

```powershell
python -m pytest tests/test_v141_q0_oracle.py -q -p no:cacheprovider
```

- [x] **步骤 3：实现最小读取、校验和独立区间函数**

校验 case/sync/activity 标签唯一，expected 必需字段存在，`W(s)` 只引用 case 内活动，terminal 必须符合 expected validity。区间函数只接收已写定 `W(s)`，计算 wait-set hidden/exposed union、terminal pre-sync/overlap 和 sync 内 return tail；禁止遍历 dependency edges 生成答案。

- [x] **步骤 4：运行绿灯并提交**

```powershell
python -m pytest tests/test_v141_q0_oracle.py -q -p no:cacheprovider
git add exposedpath_v141/q0_oracle.py tests/test_v141_q0_oracle.py docs/superpowers/plans/2026-09-11-q0-independent-oracle.md
git commit -m "test: validate independent q0 oracle"
```

---

### 任务 2：写定核心正例

**文件：**

- 新建：`q0/oracle_cases_v0_2.json`
- 修改：`tests/test_v141_q0_oracle.py`

**接口：**

- 每个 case 包含 `construction`、`expected.syncs`、`required_contract_rules` 和 `required_for_q0`。
- 每个 activity 使用 `activity_label`；真实 trace 以后通过 Q0 marker/correlation 映射该标签。

- [x] **步骤 1：先写默认 bundle 的覆盖测试并确认因文件缺失而失败**

```python
def test_core_positive_cases_exist():
    case_ids = {case["case_id"] for case in load_oracle_bundle()["cases"]}
    assert {"Q0-STREAM-001", "Q0-DEVICE-001", "Q0-CONTEXT-001", "Q0-EVENT-001"} <= case_ids
```

- [x] **步骤 2：写入核心案例及手工 expected**

至少写定：stream 同流前缀与无关流、device 跨流、driver context 跨流、event record 前缀、cross-stream wait-event、completed-before、valid-empty、kernel/MemOp mixed。每个案例明确 expected `W(s)`、terminal、validity、A/B 关系；合成时间案例写入可手算的纳秒值。

- [x] **步骤 3：验证标准答案与独立算术**

```powershell
python -m pytest tests/test_v141_q0_oracle.py -q -p no:cacheprovider
```

- [x] **步骤 4：提交核心正例**

```powershell
git add q0/oracle_cases_v0_2.json tests/test_v141_q0_oracle.py docs/superpowers/plans/2026-09-11-q0-independent-oracle.md
git commit -m "test: define q0 positive oracle cases"
```

---

### 任务 3：补齐负例、含糊例和独立性证明

**文件：**

- 修改：`q0/oracle_cases_v0_2.json`
- 修改：`tests/test_v141_q0_oracle.py`
- 新建：`scripts/verify_q0_oracle_independence.py`

**接口：**

- 独立性脚本解析 `exposedpath_v141/q0_oracle.py` 的 AST，拒绝 `analysis`、旧 `exposedpath` 以及 `exposedpath_v141.raw/sync/accounting` 导入。
- 覆盖审查输出正例、负例、含糊例和必需特性数量。

- [x] **步骤 1：先写缺口覆盖与非法导入测试**

覆盖 terminal tie、missing event/correlation、dropped records、external ownership、submission race、legacy/PTDS、multi-thread ordered、overlapping Host sync、phase spill、invocation bleed、graph unsupported、同步 D2H unsupported 和 query/poll。

- [x] **步骤 2：运行红灯**

```powershell
python -m pytest tests/test_v141_q0_oracle.py -q -p no:cacheprovider
```

- [x] **步骤 3：写入剩余 expected 并实现 AST 独立性检查**

所有 `AMBIGUOUS/INVALID` case 必须给出 primary reason，且不得伪造 terminal；`VALID_EMPTY` 必须显式 `W=[]`、terminal N/A、B_NOT_APPLICABLE。

- [x] **步骤 4：运行绿灯和独立性检查**

```powershell
python -m pytest tests/test_v141_q0_oracle.py -q -p no:cacheprovider
python scripts/verify_q0_oracle_independence.py
```

- [x] **步骤 5：提交**

```powershell
git add q0/oracle_cases_v0_2.json tests/test_v141_q0_oracle.py scripts/verify_q0_oracle_independence.py docs/superpowers/plans/2026-09-11-q0-independent-oracle.md
git commit -m "test: complete q0 oracle edge cases"
```

---

### 任务 4：审查 Gate 2 并更新进度

**文件：**

- 新建：`docs/v1_4_1/q0_oracle_design_v0_2.md`
- 修改：`docs/v1_4_1/research_progress.md`
- 修改：`exposedpath_v141/cli.py`
- 修改：`tests/test_v141_q0_oracle.py`
- 修改：`docs/superpowers/plans/2026-09-11-q0-independent-oracle.md`

**接口：**

- `python -m exposedpath_v141 validate-q0-oracle` 输出 case 数、覆盖组、独立性状态和 `DESIGN_ONLY_PASS`。

- [x] **步骤 1：先写 CLI 失败测试，再实现验证命令**

```python
def test_validate_q0_oracle_cli_is_scope_limited(capsys):
    assert main(["validate-q0-oracle"]) == 0
    assert "verdict: DESIGN_ONLY_PASS" in capsys.readouterr().out
```

- [x] **步骤 2：写中文设计说明**

说明 case schema、符号标签映射、数值/关系两类 expected、独立性边界、覆盖矩阵、未来真实 Q0 使用方式，以及为什么 Gate 2 PASS 不等于 Gate 6 PASS。

- [x] **步骤 3：更新科研进度**

通过全部离线检查后，将 `EP-G2-01` 至 `EP-G2-05` 标记完成，Gate 2 改为 PASS；最高优先级切换到 `EP-G3-05` Canonical Raw schema。Gate 6 继续保持 BLOCKED。

- [x] **步骤 4：最终验证**

```powershell
python -m compileall -q exposedpath_v141 scripts
python -m pytest tests/test_v141_q0_oracle.py tests/test_v141_contract.py tests/test_v141_observation.py -q -p no:cacheprovider
python -m exposedpath_v141 validate-q0-oracle
python scripts/verify_q0_oracle_independence.py
python -m pytest -q -p no:cacheprovider
git diff --check
```

全量回归只允许复现已记录的两项 PowerShell smoke 基线失败，不得出现新增失败。

- [x] **步骤 5：提交 Gate 2**

```powershell
git add docs/v1_4_1/q0_oracle_design_v0_2.md docs/v1_4_1/research_progress.md exposedpath_v141/cli.py tests/test_v141_q0_oracle.py docs/superpowers/plans/2026-09-11-q0-independent-oracle.md
git commit -m "docs: pass q0 oracle design gate"
```

---

## 完成后的下一 Gate

Gate 2 通过后进入 Gate 3：冻结 Canonical Raw schema 并实现 SQLite 转换器。Oracle 的标准答案必须保持只读；未来 S/A/B 只能接受它的检验，不能回写或重生成 expected。
