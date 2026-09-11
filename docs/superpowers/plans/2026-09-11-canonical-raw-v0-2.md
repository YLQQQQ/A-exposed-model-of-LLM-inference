# Canonical Raw v0.2 实施计划

> **执行要求：** 按任务顺序执行；每项测试先红后绿；每个任务结束都审查研究语义、运行测试并提交检查点。

**目标：** 完成 Gate 3，冻结唯一、版本化、可追溯的 Canonical Raw schema，并实现 Nsight SQLite 到该 schema 的确定性只读转换，使未来 S/A/B 不再直接查询 Nsight 私有表。

**架构：** Nsight SQLite adapter 只负责提取可观察事实与稳定来源引用，输出一个不可覆盖的目录 bundle。bundle 由 manifest 和分类型 JSONL 构成；所有记录保留 source table/rowid、原始 ID、统一 trace-relative ns 时钟域和输入哈希。Request/phase 只接受带版本的结构化 NVTX identity；旧 `full_request/prefill/decode` 标签保留为事实但不猜 request/repeat 身份。

**技术栈：** Python 3 标准库、SQLite、JSON/JSONL、pytest、Nsight Systems 2026.1.1 本地只读导出、Markdown、Git。

**规范依据：** Measurement Contract v0.2、Q0 oracle v0.2、NVIDIA Nsight Systems SQLite Schema Reference。官方 schema 明确说明 SQLite schema 会变化，且 `globalTid` 为序列化硬件/虚机/进程/线程身份，因此 adapter 必须版本锁定并保留原值。

## 全局约束

- 输入 `.nsys-rep` 与 SQLite 不得修改；输出目录已存在时拒绝覆盖。
- Canonical Raw 只保存事实、来源与观察有效性，不恢复 `W(s)`、terminal 或 A/B。
- SQLite schema adapter 仍只支持已审查的 `2026.1.1.204 / 3.24.14`。
- 记录身份是 `(source_sqlite_sha256, source_table, source_rowid)`；不能用时间排序或文件名重建实验身份。
- 时钟统一声明为单 trace 的 `NSYS_TRACE_RELATIVE_NS`；不得跨 trace 直接比较时间戳。
- `globalTid/globalPid` 原值必须保留；拆出的 pid/tid 只是确定性派生字段。
- event record 与 Host blocking sync 分开存储；CUPTI syncType 不替代 runtime API 名称分类。
- 缺 manifest 的历史 trace 可用于 Engineering 回归，但 identity validity 保持 ambiguous；不得升级为 Q0/Pilot/Formal 证据。

---

### 任务 1：冻结机器可检验的 Canonical Raw schema

**文件：**

- 新建：`docs/v1_4_1/contracts/canonical_raw_schema_v0_2.json`
- 新建：`exposedpath_v141/canonical_raw.py`
- 新建：`tests/test_v141_canonical_raw.py`

- [x] 先写 schema 缺字段、重复字段、未知 record kind、S/A/B 字段混入等失败测试。
- [x] 实现 schema bundle 加载与校验器。
- [x] 冻结 bundle manifest、NVTX、CUDA API、physical sync、device activity、CUDA event、context、stream、diagnostic 的必需/可空字段。
- [x] 冻结版本、时钟、lineage、记录身份、数据角色和 fail-closed 状态字段。
- [x] 定向测试通过并提交。

### 任务 2：实现确定性 SQLite 转换核心

**文件：**

- 修改：`exposedpath_v141/canonical_raw.py`
- 修改：`tests/test_v141_canonical_raw.py`

- [ ] 先用合成 SQLite 写失败测试：记录数、名称解析、排序、source identity、globalTid 拆分和输入不变。
- [ ] 实现只读、流式、确定性转换；每种记录写独立 JSONL，manifest 最后生成。
- [ ] 输出采用临时同级目录后原子改名，已存在目标拒绝覆盖。
- [ ] 验证重复运行内容稳定；仅 `generated_at_utc` 不进入记录文件内容哈希。
- [ ] 定向测试通过并提交。

### 任务 3：补齐 identity、event 与 fail-closed 边界

**文件：**

- 修改：`exposedpath_v141/canonical_raw.py`
- 修改：`tests/test_v141_canonical_raw.py`

- [ ] 先写结构化 NVTX marker、旧标签不猜身份、eventSyncId 保留、runtime mapping 不唯一、dropped records、未知 schema 和无效时间区间测试。
- [ ] 解析 `EXPOSEDPATH_JSON_V1:` 结构化标记；缺必需 identity 字段时标记问题，不补造值。
- [ ] physical sync 同时保存 CUPTI sync 枚举与唯一 runtime API 映射；event record 独立保存。
- [ ] observation invalid 时拒绝转换；Engineering ambiguous 可转换但完整传播问题和研究资格。
- [ ] 定向测试通过并提交。

### 任务 4：CLI、历史 trace 回归与 Gate 3 审查

**文件：**

- 修改：`exposedpath_v141/cli.py`
- 新建：`docs/v1_4_1/canonical_raw_v0_2.md`
- 新建：`engineering_evidence/canonical_raw_v0_2/historical_regression.json`
- 修改：`docs/v1_4_1/research_progress.md`
- 修改：`tests/test_v141_canonical_raw.py`

- [ ] 先写 `convert-sqlite` CLI 失败测试，再实现命令。
- [ ] 使用本机 Nsight 2026.1.1 将三份封存 `.nsys-rep` 只读导出到临时目录，再转换 Canonical Raw；比较 Raw 前后 SHA-256。
- [ ] 记录三份历史输入的行数、输出文件哈希、validity 和限制；不提交大型临时 SQLite/JSONL。
- [ ] 增加下游边界测试/检查，禁止未来 `sync/accounting` 模块直接出现 Nsight 表名或 sqlite 查询。
- [ ] 写中文 schema 说明并将 Gate 3 更新为 PASS；明确历史回归不是 Q0。
- [ ] 运行定向、CLI、三份历史回归、全量测试和 `git diff --check`；只允许两项既有 PowerShell smoke 失败。
- [ ] 提交 Gate 3。

## 完成后的下一 Gate

Gate 3 通过后进入 Gate 4：S 层只能读取 Canonical Raw，依据同步 completion semantics、提交证据、依赖边和 ownership 恢复 `W(s)`、terminal 与 validity。任何 Raw 缺失不得在 S 层被静默填零。
