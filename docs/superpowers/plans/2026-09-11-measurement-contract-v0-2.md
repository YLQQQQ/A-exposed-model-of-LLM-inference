# Measurement Contract v0.2 实施计划

> **供执行代理使用：** 必须按 `executing-plans` 逐任务执行；每个任务均遵循测试先行，步骤使用复选框记录。

**目标：** 完成并审查 ExposedPath Gate 1，形成可供 Q0 oracle、Canonical Raw、S 和 A/B 实现共同消费的 Measurement Contract v0.2。

**架构：** 合同采用“一份中文规范正文 + 三份机器可读清单 + 一个只读校验器”的结构。正文解释研究语义，机器清单分别固定核心规则、同步 API registry 和规则到验证案例的映射；`exposedpath_v141.contract` 只校验合同内部一致性，不实现 analyzer，也不读取旧 accounting 的结论。

**技术栈：** Python 3 标准库、JSON、pytest、Markdown、Git。

**规范依据：** `CONTEXT.md`、`docs/current/ExposedPath_研究设计.docx`、`docs/current/ExposedPath_实验协议.docx`、`docs/v1_4_1/analyzer_contract_v0_1.md`、`docs/v1_4_1/pre_gpu_readiness_design_v0_1.md`。

## 全局约束

- 当前阶段始终为 `Engineering/Pre-Pilot`；完成 Gate 1 不等于 Q0、Pilot 或 Protocol Freeze 通过。
- 研究边界保持为单 GPU、单次 batched invocation 内、纯模型推理的 Host-device exposure。
- 固定方法链 `Raw -> S -> {A, B} -> D / Exposure Signature`；Activity Cost 不得替代 Request-Visible Exposure。
- 时间重叠不得生成 dependency；`W(s)` 必须来自 completion scope、提交证据、依赖闭包和 ownership。
- 自然逐 Token 同步属于 G1 自然推理行为；N1 人为同步必须有独立的 variant/callsite 身份。
- A 是互斥守恒墙钟分区；B 保持 per-sync provenance；D 与 Exposure Signature 只能从 A/B 派生。
- 旧 `analysis/` 与 `exposedpath/` 仅作 prototype 对照，本计划不修改它们。
- 合同和清单不得包含 `TODO`、`TBD`、“待定”或静默 fallback；尚由 Pilot 决定的数值只能作为明确的后续协议参数，不能参与 Gate 1 的语义判定。

---

### 任务 1：建立合同包校验器

**文件：**

- 新建：`tests/test_v141_contract.py`
- 新建：`exposedpath_v141/contract.py`

**接口：**

- 输入：三个已经解析为 `Mapping[str, Any]` 的 JSON 对象，或包含默认合同文件的仓库根目录。
- 输出：`validate_contract_bundle(contract, registry, test_map) -> None`；不满足不变量时抛出 `ContractValidationError`。
- 输出：`load_contract_bundle(root: Path | None = None) -> dict[str, Any]`；返回键 `contract`、`registry`、`test_map`。

- [ ] **步骤 1：写入失败测试，覆盖可观察的合同破坏**

```python
def test_duplicate_rule_id_is_rejected():
    contract, registry, test_map = valid_literal_bundle()
    contract["rules"].append(dict(contract["rules"][0]))
    with pytest.raises(ContractValidationError, match="重复规则"):
        validate_contract_bundle(contract, registry, test_map)


def test_unmapped_rule_is_rejected():
    contract, registry, test_map = valid_literal_bundle()
    test_map["cases"][0]["rule_ids"] = []
    with pytest.raises(ContractValidationError, match="没有验证案例"):
        validate_contract_bundle(contract, registry, test_map)


def test_derived_metric_cannot_read_raw_fields():
    contract, registry, test_map = valid_literal_bundle()
    contract["derived"]["D_score"]["inputs"].append("raw.kernel_duration_ns")
    with pytest.raises(ContractValidationError, match="只能读取 A/B"):
        validate_contract_bundle(contract, registry, test_map)
```

- [ ] **步骤 2：运行定向测试并确认红灯来自接口尚不存在**

```powershell
python -m pytest tests/test_v141_contract.py -q -p no:cacheprovider
```

预期：collection 阶段因 `exposedpath_v141.contract` 不存在而失败。

- [ ] **步骤 3：实现最小只读校验器**

```python
class ContractValidationError(ValueError):
    """Measurement Contract 包内部不一致。"""


def validate_contract_bundle(contract, registry, test_map) -> None:
    """验证版本绑定、规则唯一性、registry 完整性、A 分区和测试覆盖。"""


def load_contract_bundle(root: Path | None = None) -> dict[str, Any]:
    """从 docs/v1_4_1/contracts 读取并验证三份只读 JSON。"""
```

校验器必须检查：三份版本互相绑定；规则 ID、registry rule ID、API alias 和案例 ID 唯一；每条合同规则至少映射一个案例；每个案例只能引用存在的规则；supported sync 必须声明 completion scope 和 required evidence；A 优先级恰好覆盖五个顶层类别；D/Signature 输入只允许引用 A/B；占位文本被拒绝。

- [ ] **步骤 4：运行定向测试并确认绿灯**

```powershell
python -m pytest tests/test_v141_contract.py -q -p no:cacheprovider
```

预期：任务 1 的测试全部通过。

- [ ] **步骤 5：提交任务 1**

```powershell
git add exposedpath_v141/contract.py tests/test_v141_contract.py
git commit -m "test: validate measurement contract bundle"
```

---

### 任务 2：冻结 phase、Token 与同步身份

**文件：**

- 新建：`docs/v1_4_1/contracts/measurement_contract_v0_2.json`
- 新建：`docs/v1_4_1/contracts/sync_semantics_registry_v0_2.json`
- 新建：`docs/v1_4_1/contracts/measurement_contract_test_map_v0_2.json`
- 修改：`tests/test_v141_contract.py`

**接口：**

- `phase_boundaries` 提供 Request、Prefill、Decode、首 Token、后续 Token 的半开区间和完成证据。
- `sync_identity` 区分 `natural_token_ready`、`n1_intervention` 与 `non_sync_marker`。
- registry 为每个 physical blocking sync 提供 `registry_rule_id`、API alias、支持状态、completion scope 和必需证据。

- [ ] **步骤 1：先写默认合同加载和边界行为测试**

```python
def test_default_bundle_freezes_observable_token_boundaries():
    bundle = load_contract_bundle()
    phases = bundle["contract"]["phase_boundaries"]
    assert phases["prefill"]["end"] == "token[0].host_readable"
    assert phases["decode"]["empty_when_fixed_output_tokens"] == 1
    assert phases["full_request"]["end"] == "token[N-1].host_readable"


def test_natural_and_intervention_sync_have_disjoint_origins():
    bundle = load_contract_bundle()
    identities = bundle["contract"]["sync_identity"]["origins"]
    assert identities["natural_token_ready"]["study_role"] == "G1_NATURAL"
    assert identities["n1_intervention"]["study_role"] == "N1_INTERVENTION"
```

- [ ] **步骤 2：运行测试并确认因合同文件缺失而失败**

```powershell
python -m pytest tests/test_v141_contract.py -q -p no:cacheprovider
```

预期：默认合同文件不存在，测试失败。

- [ ] **步骤 3：写入三份机器清单的第一部分**

冻结以下事实：输入张量已在目标设备上且 request 前 drain 完成后，紧邻首次模型调用前为 `request.start`；`token[i].host_readable` 是整批 Token ID 已经可被 Host 读取且对应阻塞操作已经返回；Prefill 结束于 `token[0].host_readable`；Decode 从该点开始，结束于 `token[N-1].host_readable`；`N=1` 时 Decode 是合法空区间；反分词、文本拼接、网络和前端均不进入窗口。

自然同步必须携带 request/repeat/phase/token/callsite 身份。N1 同步必须另带 intervention variant、callsite 和 ordinal；Pass0 与 Pass1 执行相同同步和 Token-ready 路径，Pass1 只增加标记和 profiler。

- [ ] **步骤 4：写入 physical blocking sync registry**

核心支持项：Runtime/Driver stream synchronize、Runtime device synchronize、Driver context synchronize、Runtime/Driver event synchronize。依赖图节点包括 event record 与 stream wait event，但二者本身不被当作 Host blocking sync。同步 copy/隐式阻塞 API 进入 universe 但在 v0.2 标记 unsupported；query 和纯异步 enqueue 标记 non-sync。

- [ ] **步骤 5：运行定向测试并确认绿灯**

```powershell
python -m pytest tests/test_v141_contract.py -q -p no:cacheprovider
```

- [ ] **步骤 6：提交任务 2**

```powershell
git add docs/v1_4_1/contracts tests/test_v141_contract.py
git commit -m "docs: freeze phase and sync identity contract"
```

---

### 任务 3：冻结 W(s)、terminal、validity 与 A/B/D

**文件：**

- 修改：`docs/v1_4_1/contracts/measurement_contract_v0_2.json`
- 修改：`docs/v1_4_1/contracts/sync_semantics_registry_v0_2.json`
- 修改：`docs/v1_4_1/contracts/measurement_contract_test_map_v0_2.json`
- 修改：`tests/test_v141_contract.py`

**接口：**

- S 输出：每个 physical sync 的 scope、submission evidence、dependency closure、`W(s)`、terminal、ownership、validity 和 reason。
- A 输出：每个 request/phase 的五类互斥整数纳秒区间及二级分类。
- B 输出：每个 physical sync 独立保存 wait-set 与 terminal 生命周期，不提供跨同步总和。
- D/Signature 输出：只读取 A/B 字段的确定性派生视图。

- [ ] **步骤 1：先写 S/A/B 关键不变量测试**

```python
def test_default_bundle_keeps_completed_predecessors_and_rejects_overlap_dependency():
    rules = {r["rule_id"]: r for r in load_contract_bundle()["contract"]["rules"]}
    assert rules["MC-S-008"]["decision"] == "completed_before_sync_remains_in_W"
    assert rules["MC-S-009"]["decision"] == "temporal_overlap_never_creates_dependency"


def test_a_priority_is_conservative_and_complete():
    a = load_contract_bundle()["contract"]["a_layer"]
    assert a["priority"] == [
        "A_unattributed", "A_device_wait", "A_sync_residual",
        "A_cuda_api", "A_host_path",
    ]
    assert set(a["priority"]) == set(a["top_level_categories"])


def test_b_is_per_sync_and_excluded_from_a_budget():
    b = load_contract_bundle()["contract"]["b_layer"]
    assert b["aggregation_policy"] == "NO_CROSS_SYNC_SUM"
    assert b["enters_a_wall_clock_budget"] is False
```

- [ ] **步骤 2：运行测试并确认红灯对应缺少冻结内容**

```powershell
python -m pytest tests/test_v141_contract.py -q -p no:cacheprovider
```

- [ ] **步骤 3：完成 S 规则**

写入 `submission_proven(e,s) := e.gpu_start < s.host_start OR enqueue(e).host_end <= s.host_start`；无法证明顺序时为 `SUBMISSION_ORDER_AMBIGUOUS`。Stream 使用目标 stream 的可观察传递前驱闭包；device/context 使用目标 context 的全部可观察 frontier；event 使用同步调用时最近一次 event record 捕获的前缀且不含 record 后活动；default-stream mode 未记录时 fail closed。

terminal 先由依赖图 frontier 产生候选：唯一 frontier 直接形成 completion evidence；多个 frontier 仅在同一时钟域且存在唯一最大完成时刻时选择；完成时间完全相同即 `TERMINAL_TIE`。语义选择使用整数纳秒和 `0 ns` tie tolerance；Pilot 以后确定的统计比较容差不得反向改变成员或 terminal identity。

- [ ] **步骤 4：完成 validity 与 reason 优先级**

固定 `VALID_NONEMPTY`、`VALID_EMPTY`、`AMBIGUOUS`、`INVALID`；`VALID_EMPTY` 只能由可观察闭包确认为空。按 trace 完整性、边界/ownership、universe 支持性、mapping、submission、dependency closure、terminal、timestamp ordering 的优先级确定 primary reason，其他原因保留为 secondary reasons。

- [ ] **步骤 5：完成 A/B/D/Signature**

A 使用半开区间和整数纳秒，按 `unattributed -> device_wait -> sync_residual -> cuda_api -> host_path` 优先级覆盖原子片段。合法空等待的整个同步窗口进入 residual；ambiguous/invalid/unsupported 同步窗口进入 unattributed。A_cuda_api 在父类内分 submit/non-submit；A_device_wait 在父类内分 kernel-only、memop-only、mixed。

B 固定 wait-set pre-sync union、wait-set sync-overlap union、terminal pre-sync、terminal overlap-sync 和 sync 内 return tail；返回尾部只计算 `[max(sync.start, terminal.end), sync.end)`，不得把 terminal 在 sync 前完成到 sync.start 的间隔算入尾部。D 固定为研究设计中的 `D_margin` 与 `D_score`；Exposure Signature 固定为 A 一级/二级字段和 B 的 per-sync 分布/coverage/provenance，禁止读取 Raw 时间重新建立第二套 accounting。

- [ ] **步骤 6：运行定向测试并确认绿灯**

```powershell
python -m pytest tests/test_v141_contract.py -q -p no:cacheprovider
```

- [ ] **步骤 7：提交任务 3**

```powershell
git add docs/v1_4_1/contracts tests/test_v141_contract.py
git commit -m "docs: freeze synchronization and accounting semantics"
```

---

### 任务 4：形成中文合同正文并完成 Gate 1 审查

**文件：**

- 新建：`docs/v1_4_1/measurement_contract_v0_2.md`
- 修改：`docs/v1_4_1/research_progress.md`
- 修改：`docs/superpowers/plans/2026-09-11-measurement-contract-v0-2.md`

**接口：**

- 中文正文按机器规则 ID 逐段解释输入、处理、输出、拒答条件和研究解释边界。
- 进度清单记录 EP-G1-02 至 EP-G1-09 的证据和 Gate verdict。

- [ ] **步骤 1：撰写规范正文**

正文必须包含：适用范围与非主张；时间/身份基本规则；phase/Token 边界；自然与人为同步；physical sync universe；submission 与依赖闭包；三类 completion scope；`W(s)`；terminal；validity/reason；A/B；D/Signature；输出最小字段；规则到测试映射；当前 prototype 差距；版本兼容与变更规则；NVIDIA 官方语义来源。

- [ ] **步骤 2：运行合同校验和禁止占位扫描**

```powershell
python -m pytest tests/test_v141_contract.py -q -p no:cacheprovider
rg -n "TODO|TBD|待定|时间重叠.*依赖|B.*跨同步.*求和" docs/v1_4_1/measurement_contract_v0_2.md docs/v1_4_1/contracts
```

预期：测试通过；扫描只允许出现明确的禁止性表述，不允许出现未解决占位。

- [ ] **步骤 3：逐条审查 EP-G1-02 至 EP-G1-09**

```powershell
python -m exposedpath_v141 validate-contract
```

预期：输出合同版本、registry 版本、规则数、案例数、覆盖率 `100%` 和 `PASS`。该命令仅表示合同内部审查通过，不表示 analyzer 或 Q0 通过。

- [ ] **步骤 4：更新科研进度唯一事实源**

将清单版本递增；只有在默认合同加载、规则映射覆盖和全文审查均通过后，才勾选 `EP-G1-02` 至 `EP-G1-09` 并把 Gate 1 改为 `PASS`。最高优先级随后改为 Gate 2 的 Q0 独立标准答案设计；Gate 3 至 Gate 14 的 verdict 保持原状态。

- [ ] **步骤 5：运行最小检查与全量回归**

```powershell
python -m compileall exposedpath_v141
python -m pytest tests/test_v141_contract.py tests/test_v141_observation.py -q -p no:cacheprovider
python -m pytest -q -p no:cacheprovider
git diff --check
```

预期：新增定向测试全部通过；全量测试仅允许复现已经记录的两项 PowerShell smoke 基线失败，不得出现新失败。

- [ ] **步骤 6：提交任务 4**

```powershell
git add docs/v1_4_1/measurement_contract_v0_2.md docs/v1_4_1/research_progress.md docs/superpowers/plans/2026-09-11-measurement-contract-v0-2.md exposedpath_v141/cli.py
git commit -m "docs: pass measurement contract gate"
```

---

## 完成后的下一 Gate

Gate 1 通过后，只进入 Gate 2：为每个 Q0 case 写独立 expected/oracle。不得直接实现 S，也不得把合同校验器、合成 fixture 或历史 trace 回归描述为 Q0 通过。
