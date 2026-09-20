# Gate 5：A/B 与派生层设计

> **HISTORICAL / SUPERSEDED FOR CURRENT EXECUTION** — 本规格是历史设计记录，仅作追溯保留。正文中的 `Q0 = NOT_RUN` 等为当时状态，不得作为当前执行依据。当前 Gate 状态见 `docs/v1_4_1/research_progress.md`；Gate 6 结论见 `docs/v1_4_1/gate6_closeout_v0_1.md`。

## 1. 状态与目标

本设计遵循 `exposedpath-measurement-contract-0.2.0`、Canonical Raw v0.2 和 S v0.2，属于 Engineering/Pre-Pilot。它不修改 Measurement Contract，不表示 Q0 已执行，也不产生 Pilot 或 Formal 证据。

Gate 5 的目标是把已经恢复的同步语义转换为两类结果：A 回答一个 request/phase 墙钟窗口中的时间如何互斥分配；B 回答每个 physical sync 的 hidden/exposed/terminal/return-tail provenance。D 与 Exposure Signature 只能读取冻结后的 A/B 输出，不能重新读取 Raw 时间戳改变分类。

本阶段不修改 benchmark、runner、CUDA 同步行为或 Nsight 采集方式；这些属于 Gate 6/7。旧 `analysis/exposed_accounting.py` 仅作为 prototype 对照，不作为新版实现依赖。

## 2. 采用方案与边界

采用“共享原子区间工具 + 独立 A/B 投影 + 独立派生层”：

1. 输入适配层验证 Canonical Raw 与 S 的 schema、哈希、数据角色和 lineage，并建立只读索引。
2. 通用区间工具只实现半开区间交、并、裁剪和原子切分，不包含研究分类。
3. A 按冻结优先级对原子片段做唯一分类，并执行整数纳秒守恒检查。
4. B 每个 physical sync 独立计算，不进入 A 预算，也不提供跨同步总和。
5. 派生层只读取 A/B bundle，生成 D 与版本化 Exposure Signature。

不采用 A/B 各自复制区间逻辑的方案，因为容易产生边界差异；不把 A/B 塞回 S，因为会破坏 `Raw -> S -> {A,B}` 的研究分层。

## 3. 输入合同与联结

`analyze-ab` 同时接收 `canonical_manifest.json` 和 `s_manifest.json`。结构损坏、文件哈希错误、schema/Measurement Contract 版本不匹配、source SQLite 哈希不一致，或 S 所声明的 Canonical manifest 哈希不匹配时，命令拒绝执行，不生成部分结果。

结构正确但研究证据为 ambiguous/invalid 时允许生成 fail-closed Engineering 产物：

- S sync 必须按 `sync_id` 与 Canonical physical sync 一一对应，并核对 host start/end、context/stream/device/event 和 registry identity；冲突即拒绝联结。
- S 中每个 wait-set activity ID 和 terminal activity ID 必须存在于同一 Canonical bundle；缺失即拒绝联结。
- data role 原样继承，不能通过重新分析升级。
- Canonical 全局 dropped-record、clock 或 invocation identity 无效时，已知窗口全部归 `A_unattributed`；若连唯一窗口都无法恢复，则 A 输出为空，并在 manifest 中记录 `WINDOW_DISCOVERY_INVALID`，不得猜测窗口。
- B 始终按 S 记录逐行投影；S 的 ambiguous/invalid 不得填成零。

## 4. request/phase 窗口

窗口只来自带 `EXPOSEDPATH_JSON_V1` 结构化身份的 NVTX 半开区间。以 `(experiment_id, wmpc_id, run_id, run_role, pass_id, request_id, repeat_id, phase)` 为逻辑键；`phase` 只接受 `full_request/prefill/decode`。同一逻辑键必须对应唯一范围，范围缺失、重复、交叉冲突或与冻结 phase 边界不一致时，不生成可记账窗口并记录原因。

有效关系为：Prefill 与 Decode 均位于 Full Request 内，Prefill 结束等于 Decode 开始，二者的并集等于 Full Request；固定输出数为 1 时允许 Decode 为合法空区间。每个窗口分别产生 A 记录，跨 phase 活动只取与当前窗口的交集。

## 5. A：互斥墙钟记账

每个窗口以窗口边界、CUDA API 边界、physical sync 边界和 S wait-set activity 边界切分原子片段。每个片段严格按以下优先级分配一次：

1. 全局无效证据，或落在 ambiguous/invalid/unsupported sync 内：`A_unattributed`。
2. 落在 valid sync 内且至少一个属于该 sync `W(s)` 的活动正在执行：`A_device_wait`。
3. 落在 valid sync 内但没有 `W(s)` 活动正在执行：`A_sync_residual`。
4. 不在 sync 内、且被明确支持并具有合法窗口 ownership 的 CUDA API：`A_cuda_api`。
5. 其余 ownership 完整的窗口片段：`A_host_path`。
6. 仍无法唯一判断的片段：`A_unattributed`。

顶层字段严格满足：

`T_window_ns = A_host_path_ns + A_cuda_api_ns + A_device_wait_ns + A_sync_residual_ns + A_unattributed_ns`

重复覆盖、未覆盖和越界均必须为 0 ns。多个 Host 线程使用 interval union，不直接累加调用时长。`A_host_path` 只能称为请求路径剩余时间，不能称为 CPU busy。

### 5.1 CUDA API 二级分类

物理阻塞 sync 的 runtime API 已由更高优先级的同步类别处理，不再进入 `A_cuda_api`。其余 API 采用可观察、保守规则：

- `A_cuda_api_submit`：该 API 通过唯一 correlation 成为至少一个 Canonical device activity 的 enqueue，或由冻结 sync registry 明确分类为 event record/stream wait dependency edge。
- `A_cuda_api_non_submit`：冻结 registry 明确分类为非阻塞 query 的 API。
- 其余未分类 API 不猜测语义，其覆盖片段进入 `A_unattributed`。
- 多线程导致 submit 与 non-submit 同时覆盖同一原子片段时，该片段进入 `A_unattributed`，不设置任意优先级。

两项二级字段只划分 `A_cuda_api`，其和必须等于父类。

### 5.2 Device-wait 二级分类

按原子片段内正在执行的 `W(s)` 活动类型分类：仅 KERNEL 为 kernel-only；仅 MEMCPY/MEMSET 为 memop-only；二者同时存在为 kernel-memop-mixed。三项之和必须等于 `A_device_wait`。未知活动类型使该原子片段进入 `A_unattributed`。

## 6. B：单同步 provenance

B 的行数和 `sync_id` 集合必须与 S physical sync 完全一致：

- `VALID_NONEMPTY -> B_VALID`：根据 Canonical activity 区间计算 wait-set hidden union、exposed union、terminal pre-sync、terminal overlap-sync 和 return-tail。
- `VALID_EMPTY -> B_NOT_APPLICABLE`：所有 B 时长字段为 `null`，避免把“不适用”伪装成数值 0。
- `AMBIGUOUS -> B_AMBIGUOUS`、`INVALID -> B_INVALID`：时长字段为 `null`，保留 primary/secondary reasons。

只有 `B_VALID` 中真实计算得到的 0 才能输出 0。区间全部使用半开语义与 interval union。`sync_return_tail_ns` 只表示完成条件满足后仍处于同步调用内部的可观察尾部，不能解释为 runtime overhead。

B 保留 S 的 sync identity、request/phase、origin、callsite、wait-set、terminal、activity origin 和 cross-phase 标记。实现和 schema 均不提供 B 总时长、跨 sync 求和或可被误用为 A 预算的字段。

## 7. 输出与版本

A/B 输出为不可覆盖的 `exposedpath-ab/0.2.0` bundle：

- `ab_manifest.json`：输入哈希、schema/contract/analyzer 版本、data role、质量状态、窗口/sync 数量、validity 分布和研究资格。
- `a_window_records.jsonl.gz`：窗口身份、边界、五项顶层 A、五项二级 A、守恒检查和原因。
- `b_sync_records.jsonl.gz`：严格使用 Measurement Contract 冻结的 B 字段。

`derive-exposure` 只接收 A/B manifest，输出不可覆盖的 `exposedpath-derived/0.2.0` bundle：

- 每个 A 窗口的 `D_margin` 与 `D_score`；分母为 0 时 score 为 `null`。
- Exposure Signature 保存 A 一级/二级向量及其窗口内比例，并按 `(phase, sync_kind, sync_origin, callsite_id)` 汇总 B 状态 count、有效行的 median 和 p90、terminal/provenance 分布。
- median 使用通常的中位数定义；偶数样本取中间两项平均值。p90 使用 nearest-rank。两者是摘要统计，不产生可相加的 B total。
- 不输出“瓶颈”“根因”“可优化上界”等结论标签。

## 8. 实现单元

- `exposedpath_v141/ab_inputs.py`：双 manifest 加载、哈希/lineage/identity 联结和窗口发现。
- `exposedpath_v141/intervals.py`：无研究语义的整数半开区间运算。
- `exposedpath_v141/a_accounting.py`：A 原子片段分类、二级分类和守恒。
- `exposedpath_v141/b_provenance.py`：S 到单同步 B 的投影。
- `exposedpath_v141/ab_bundle.py`：A/B schema 校验、确定性压缩、不可覆盖输出和 CLI 编排。
- `exposedpath_v141/derived.py`：只读取 A/B 的 D 与 Exposure Signature。
- `docs/v1_4_1/contracts/ab_schema_v0_2.json` 与 `derived_schema_v0_2.json`：机器合同。

这些模块不得导入 `sqlite3`，不得读取 Nsight 私有表名，也不得调用旧 `analysis/exposed_accounting.py`。

## 9. 验证策略

1. 区间单元测试覆盖相交、相邻、嵌套、重复、多线程 union 和空窗口。
2. 使用人工可手算 fixture 验证 A 顶层互斥守恒、sync overlap、phase clipping、submit/non-submit 冲突和 device-wait 二级分类。
3. 用 Q0 oracle 的人工 wait-set/terminal 与 `calculate_expected_timing` 对照 B，不使用正式 A/B 实现生成 expected。
4. 覆盖 valid-empty、ambiguous、invalid、dropped records、窗口 identity 缺失、S/Raw lineage 冲突和 wait activity 缺失。
5. 静态边界检查确保 A/B/D 不直接访问 SQLite/Nsight 表，并验证 derived 模块不读取 Raw/S。
6. 历史 `.nsys-rep -> SQLite -> Canonical Raw -> S -> A/B` 仅验证执行链和 fail-closed：现有旧 trace 应保持无合格 A 窗口、B 全部 invalid、Q0 `NOT_RUN`。
7. 输出重复运行应产生相同 JSONL 哈希；manifest 中允许生成时间不同。
8. 全量仓库测试只允许已经记录的两项 PowerShell smoke 基线失败。

## 10. Gate 5 完成条件

只有以下条件全部满足才可写 `PASS`：A/B schema 和 CLI 已实现；Canonical/S 联结 fail closed；A 顶层及二级分类在整数纳秒域完全守恒；B 与 S 一一对应且无跨同步求和；Q0 合成 expected 对照通过；D/Signature 只读取 A/B；历史 Engineering 回归保持无资格升级；独立代码审查无 Critical/Important。

Gate 5 PASS 仍不表示 Q0 PASS。下一 Gate 是先实现 Gate 6 的 CUDA 微程序、manifest 和自动对照代码；其中真实 trace 采集与最终 Q0 verdict 需要 GPU。
