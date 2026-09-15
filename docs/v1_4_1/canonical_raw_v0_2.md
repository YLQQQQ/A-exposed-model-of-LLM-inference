# ExposedPath Canonical Raw v0.2

## 1. 作用与边界

Canonical Raw 是 Nsight SQLite 与研究语义层之间唯一的数据边界。它把版本易变的 Nsight 表转换为 ExposedPath 自己控制的稳定事实记录；S 层以后只能读取此 bundle，不能直接写 SQL 或引用 `CUPTI_ACTIVITY_KIND_*` 等私有表名。

Canonical Raw 不判断某个活动是否属于 `W(s)`，不选 terminal，也不计算 A/B/D/Exposure Signature。它保存的是“观察到了什么”，不是“这些事实应如何解释”。

## 2. 输入、输出与不可变性

输入为 Nsight SQLite、对应 `.nsys-rep` 的 SHA-256、采集器版本、数据角色和可选 source manifest。adapter 仅接受已经审查的两组版本：`2026.1.1.204 / 3.24.14` 与 `2026.2.1.210 / 3.25.0`；不接受版本范围或未知 schema。

输出是一个新目录，包含 `canonical_manifest.json` 和八类确定性 gzip JSONL：NVTX、CUDA API、CUDA synchronization activity、device activity、CUDA event、context、stream、diagnostic。若源 SQLite 因没有相应活动而缺少 Memcpy、Memset 或 CUDA event 表，仍生成记录数为 0 的规范化文件；这不等于伪造源表。已有输出目录一律拒绝覆盖；转换通过同级临时目录完成，全部成功后才原子改名。输入 SQLite 以 read-only/immutable 方式打开，Raw 报告只读取哈希。

## 3. 记录身份与时钟

每条记录的全局身份是 `(source_sqlite_sha256, source_table, source_rowid)`。`record_id` 只是在 bundle 内的可读缩写，不能脱离 manifest 的 SQLite 哈希单独使用。时间排序和文件名均不得作为实验身份。

bundle manifest 还保留 S 层必需但不属于事件行的执行上下文：`default_stream_mode` 与 `selected_device_id`。它们只能来自 source manifest；缺失时保持空值，不能从文件名或活动形状猜测。

所有时间字段原样保留 Nsight 导出的单 trace 有符号相对纳秒，时钟域固定为 `NSYS_TRACE_RELATIVE_NS`。采集控制 API 或 profiler 初始化诊断可能跨越时钟原点而出现负值；这不是请求时长为负，也不得通过平移时间轴掩盖。区间采用半开语义且必须满足 `end >= start`；时间只能在同一 source trace 内比较，不允许把两份 trace 的相对时间直接相减。A/B 的请求窗口与时长仍执行各自的非负和守恒约束。`globalTid/globalPid` 原值保留，拆出的 pid/tid 是依据 NVIDIA 序列化 GlobalId 位布局得到的派生便利字段。

## 4. 事实映射

| Canonical 文件 | Nsight 来源 | 保存内容 |
|---|---|---|
| `nvtx.jsonl.gz` | `NVTX_EVENTS` + `StringIds` | 原始范围/标记、文本、线程和可选结构化身份 |
| `cuda_api.jsonl.gz` | `CUPTI_ACTIVITY_KIND_RUNTIME` + `StringIds` | Host API 区间、名称、线程、correlation、返回值 |
| `cuda_sync.jsonl.gz` | `...SYNCHRONIZATION` + runtime + sync enum | 中性的 CUPTI synchronization activity 及 runtime API 映射计数；唯一映射时保存 runtime 行，Q0 request 外的 harness 尾部记录允许保留空映射；两套名称均保留，尚未判定是否为 Host blocking sync |
| `device_activity.jsonl.gz` | kernel/memcpy/memset | 活动区间、device/context/stream、correlation、名称与类型属性 |
| `cuda_event.jsonl.gz` | `...CUDA_EVENT` | event record 的时间、eventId/eventSyncId、context/stream |
| `context/stream.jsonl.gz` | `TARGET_INFO_CUDA_*` | context、null stream 与 stream 元数据 |
| `diagnostic.jsonl.gz` | `DIAGNOSTIC_EVENT` | dropped/missing 等原始诊断文本与代码 |

Raw 中的 CUDA synchronization activity 既可能对应 Host blocking sync，也可能表示依赖边；其 `syncType` 枚举标签不能代替 runtime API 名称。event record 也不能伪装成 Host 阻塞同步。S 层以后必须同时使用这些事实和同步 registry 才能分类。

## 5. 结构化 NVTX identity

新版标记前缀为 `EXPOSEDPATH_JSON_V1:`，后接紧凑 JSON。公共字段为 experiment、WMPC、run、run role、pass、request 和 repeat；phase、token-ready、sync 等 kind 再按合同要求携带 phase、token index、callsite、sync origin 与 ordinal。

旧 `full_request/prefill/decode` 标签会原样保存，但绝不按出现顺序补造 request/repeat。前缀 JSON 无法解析、字段不全或与 source manifest 冲突时，identity 为 `AMBIGUOUS` 并给出机器原因；不会保留“半套可用身份”。

## 6. fail-closed

核心表/字段缺失、可选活动表存在但字段不完整、未知导出 schema、目标受控 observation 内 sync correlation 缺失或不唯一、dropped records 证据、必需非空字段为空、逆序时间区间都会拒绝转换。可选活动表不存在只表示该类记录为 0。

Q0 有一条范围严格受限的保留规则：只有 source manifest 与唯一、可解析的结构化 request identity 完整匹配后，起点不早于 request 结束的同步才能标记为 harness 尾部证据。此类记录不能被删除或伪造 runtime 映射，Canonical 中保留 `runtime_mapping_count`，缺 correlation 时 `correlation_id` 为 `null`，无唯一候选时 `runtime_api_name` 等 runtime 字段为 `null`。目标 request 内、目标范围无法唯一确定、存在无法解析的结构化 NVTX，或非 Q0 trace 的 correlation 问题仍 fail closed。缺 source manifest 的 Prototype/Engineering trace 可以生成派生 bundle，但 observation/identity 问题必须传播，研究资格仍为 false；Pilot/Formal 缺 manifest 时直接 invalid。

## 7. 历史 trace 工程回归

三份封存报告均由 Nsight 2026.1.1 以 `lazy=false` 导出到临时 SQLite，再转换为 v0.2。Raw 前后哈希完全一致。三份 SQLite 分别约 28.8、29.2、28.3 MB；gzip Canonical 记录分别约 11.9、12.2、11.4 MB。初版未压缩 JSONL 曾使首份输出膨胀至约 248 MB，因此在 Gate 3 冻结前改为确定性 gzip。

三份 trace 均有 95 条 NVTX、446 条 CUDA synchronization activity、约 20.6～21.5 万条 CUDA API 和约 20.6～21.3 万条 device activity；CUDA event 均为 0 条。它们都缺 source manifest 且只含旧式 phase 标签，所以 observation/identity 均保持 ambiguous。这证明转换链可运行并能 fail closed，不证明 event 语义正确，也不构成 Q0、Pilot 或 Formal 证据。完整计数与哈希见 `engineering_evidence/canonical_raw_v0_2/historical_regression.json`。

## 8. 验证入口

```powershell
python -m exposedpath_v141 convert-sqlite --sqlite <trace.sqlite> --output-dir <new-dir> --data-role Engineering --raw-sha256 <hash> --collector-version <version>
python scripts/verify_canonical_raw_boundary.py
python -m pytest tests/test_v141_canonical_raw.py tests/test_v141_observation.py -q -p no:cacheprovider
```

Gate 3 通过后，下一步只能在 Canonical Raw 之上实现 S 层。三份历史 trace 没有 event 案例和稳定请求身份，不能代替 Q0 oracle 对照。
