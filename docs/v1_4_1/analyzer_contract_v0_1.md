# ExposedPath v1.4.1 Analyzer 输入输出合同（草案 0.1）

> **历史状态说明（2026-09-11）：** 本文件只保留 Gate 1 之前的 observation 草案与追溯价值，其中“尚未冻结”的描述不再代表当前状态。现行 Measurement Contract 见 `measurement_contract_v0_2.md`，现行 Raw 边界见 `canonical_raw_v0_2.md` 及 `contracts/canonical_raw_schema_v0_2.json`，最新完成状态只看 `research_progress.md`。

## 当前用途与边界

本合同服务于 Prototype/Engineering 阶段的离线 analyzer 重建。它只冻结第一段边界：`Nsight SQLite -> observation report`。当前版本不实现 S、A、B、D 或 Exposure Signature，也不能作为 Q0、Pilot、Protocol Freeze 或 Formal 实验已经就绪的证据。

## 输入合同

新版入口为：

```text
python -m exposedpath_v141 inspect-sqlite \
  --sqlite <只读 SQLite> \
  --output-dir <独立派生目录> \
  --data-role <Prototype|Engineering|Pilot|Formal> \
  --raw-sha256 <对应 Raw 报告哈希> \
  --collector-version <采集器版本> \
  [--source-manifest <运行 manifest>]
```

约束如下：

1. SQLite 必须以只读、immutable 模式打开；入口不得修改或覆盖 SQLite、`.nsys-rep` 或已有输出。
2. `raw_sha256` 表示对应 `.nsys-rep` 的身份，SQLite 自身另行计算 SHA-256。两者不能互相替代。
3. `collector_version` 与 SQLite 中的 `EXPORT_PRODUCT_VERSION` 分开记录。
4. 文件名不能替代 request、repeat、workload 或运行身份。缺少 source manifest 时，Prototype/Engineering 可生成报告，但 validity 至少为 `ambiguous`；Pilot/Formal 为 `invalid`。
5. 新采集使用 `--lazy=false` 获得稳定表结构；对受支持 schema 的历史 lazy 导出，零行 activity 表可能不创建。缺表只能按下述条件化或可选表规则解释，不能普遍降级。
6. 当前 adapter 精确支持两组已审查组合：`2026.1.1.204 / 3.24.14` 与 `2026.2.1.210 / 3.25.0`。其他组合即使列名相似也必须判为 `invalid`，经独立 schema 审查后才能扩展允许列表。

## 必需的 observation evidence

当前 SQLite adapter 要求以下表及关键字段存在：

- `META_DATA_CAPTURE`、`META_DATA_EXPORT`：采集与导出元数据；
- `NVTX_EVENTS`、`StringIds`：request/phase 可观察标签；
- `CUPTI_ACTIVITY_KIND_RUNTIME`：CUDA API、correlation 与 Host 线程事实；
- `CUPTI_ACTIVITY_KIND_SYNCHRONIZATION`、`ENUM_CUPTI_SYNC_TYPE`：同步 activity 事实；
- `TARGET_INFO_CUDA_CONTEXT_INFO`、`TARGET_INFO_CUDA_STREAM`、`TARGET_INFO_GPU`：context/stream/process/device 映射；
- `DIAGNOSTIC_EVENT`：dropped/missing record 与采集诊断证据。

`CUPTI_ACTIVITY_KIND_KERNEL` 是条件化 activity 表。表存在时字段必须完整；表不存在时，只有白名单 schema、`lazy=true`、明确采集 CUDA 且不存在任何可观察 kernel/graph launch API 证据，才能以 `ZERO_ROWS_LAZY_EXPORT` 规范化为 0 条。`EXPORT_PRODUCT_VERSION`、`EXPORT_SCHEMA_VERSION` 与 `EXPORT_PARAM_LAZY` 还必须各自恰有一个值，且 lazy 值必须精确为小写 `true` 或 `false`；缺失、重复、冲突或非法取值均 fail closed。存在 `cudaLaunchKernel`/`cuLaunchKernel`、`cudaGraphLaunch`/`cuGraphLaunch` 等潜在启动证据（含版本和 `_ptsz`/`_ptds` 变体）、非 lazy、未知 schema 或未采集 CUDA 时同样不能采用零行规范化。通用 `kind=marker` 不携带 activity 类型，不能仅凭标签前缀推断 kernel 存在。

`CUPTI_ACTIVITY_KIND_MEMCPY`、`CUPTI_ACTIVITY_KIND_MEMSET` 与 `CUPTI_ACTIVITY_KIND_CUDA_EVENT` 是按活动出现的可选表：表不存在表示该类源记录为 0；表一旦存在，缺少 Canonical 提取所需任一字段仍必须 fail closed。核心表缺失、目标受控 observation 内 sync 到 CUDA API 的 correlation 缺失或不唯一、明确的 dropped/missing record 诊断，同样必须 fail closed。唯一例外只适用于 Q0：当 source manifest 与唯一结构化 `kind=request, phase=full_request` 范围完整匹配时，起点不早于该 request 结束的 synchronization 被显式标记为 `HARNESS_OUTSIDE_REQUEST`。这类记录仍原样保留并产生 warning，但不影响目标 request 的 observation validity。目标范围无法唯一恢复、request 内同步证据缺失，以及非 Q0 trace 均继续全局 fail closed。

## 输出合同

唯一输出文件为 `observation_report.json`，schema 为 `exposedpath.observation-report/0.4.0`。内容分层保存：

- `observed_facts`：输入哈希、导出元数据、表/字段、行数、GPU、sync/phase 计数；
- `derived_checks`：核心/条件化/可选表合同检查、关键导出元数据唯一性、KERNEL 缺表规范化及 presence evidence、Q0 目标 request 范围、带 `TARGET_REQUEST` / `HARNESS_OUTSIDE_REQUEST` / `GLOBAL_TRACE` 分类的 sync correlation 检查、dropped-record 扫描；
- `validity`：`valid`、`ambiguous` 或 `invalid`，以及机器可读原因；
- `research_eligibility`：当前产物是否可用于 Formal 证据。

入口退出码：`0=valid`、`2=ambiguous`、`3=invalid`、`1=执行错误`。报告已经生成不等于 observation gate 已通过。

## 尚未冻结、因此暂不实现的语义

1. Request、Prefill、Decode、TTFT 的可观察 completion boundary。
2. 各 CUDA synchronization 类型的完整 scope，尤其 event record/event wait 映射。
3. `W(s)` 的 submission-order、context、stream、event 与 ownership 规则。
4. terminal 唯一性及并列候选的时间容差。
5. A 的互斥类别、residual 策略与守恒容差。
6. B 的 hidden/exposed/return-tail 字段和 invalid 传播规则。

这些项目必须在合成 fixture 与 Q0 oracle 预期之前明确，不能从旧 analyzer 行为反推为新合同。
