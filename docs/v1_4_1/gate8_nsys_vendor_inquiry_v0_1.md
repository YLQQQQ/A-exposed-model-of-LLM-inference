# Gate8 完整性调查收口与厂商询证 v0.1

**7.27：用户已暂停询证，不发送。** 新执行采用
[Route A目标scope质量门](gate8_route_a_quality_amendment_v0_1.md)，不以统一全capture认证
为前置。以下保留为未发送的历史调查草稿，不再是下一步指令。

2026-09-25；状态 `DRAFT_NOT_SENT`。仅 Engineering 文档，不是 observation amendment、采集指令或厂商能力认证。Gate7 PASS；Gate8 NOT_RUN；完整性 UNKNOWN 继续阻塞科学验收。

## 1. 有界调查结论

目标安装资料已回传并直接读取：components/summary、585项候选清单、15条文本命中、transcript，以及四份完整说明文件。安装盘点回执声明未调用可执行程序。本地复核下列四文件大小和SHA256全部一致；组件二进制没有传回，其大小/hash来自服务器回执，不声称本地复算过二进制。机器定位仅在不提交的根handoff。

| 本地说明 | bytes | SHA256 |
|---|---:|---|
| AnalysisGuide.html | 906597 | BDCF574189E7EB687D4DC7C52BCEBACAE9C700C5A93A9E3AED8FF674960CBB11 |
| ReleaseNotes.html | 43032 | 9D007C391B840BD5CCCC5EC7D5C54673E9CCF573DC5047A57E6F7AB5ED1B71FE |
| UserGuide.html | 899707 | 5B100930126F3A3A819F13DD8335EFC0BC2CD7F8BF0207A7063D57ACB4C33E7C |
| export_schema_version_notes.txt | 15782 | F396286BDB91EF40BC40741CAB81876BA731FEC2ED8D07B53D4E9E6D52B536A1 |

- AnalysisGuide L5871起的 Thread Summary 将 lost events 讨论限定于 CPU sampling/thread utilization；不是 CUDA activity 或 NVTX 应用标记的完整性证明。
- ReleaseNotes L591起 teardown loss 对应 CC-DevTools 与使用 libcrypto 应用的特定条件。所述退出/flush缓解不能推广为每次会话零丢失声明，也不据此给本项目添加同步。
- UserGuide L772/L1946 描述 `--cuda-trace-all-apis`；ReleaseNotes L488起仍称 CLI API subset 不可改变。保留目标 Windows build 适用性疑问，不擅自选择其中一条或修改 profile。
- schema version notes 提到 DIAGNOSTIC_EVENT、eventSyncId 等演进，但未提供覆盖 CUDA/NVTX 各通道、所有目标进程及完整时间区间的肯定零丢失合同。日志中的消息、SQLite结构完整、应用ledger匹配、exit0均不能代替该合同。
- 回执：`cupti64_129.dll`，4579976 bytes，FileVersion `2025.2.1.0`，SHA256 `47B244AAFD892C52BC9F6E954B49C8F94E01186A73152E6D9AAF1FBC5D2AA8D8`；`nsys.exe`，65294976 bytes，版本字段空，SHA256 `B26707E479540314EBE4931B687B149C6A2D8A86EB6075A0C98169BEFC6E7417`。CLI身份沿用既有实际回执 `2026.2.1.210-262137639646v0`，不是本轮重新执行所得；CUPTI文件版本不等于应用 CUDA 12.4。

**安装只读取证 B 已完成。当前仍未找到充分来源，不等于工具绝不支持。** 关闭本轮重复搜索，进入一次聚焦询证的用户审阅点。历史REP/SQLite调查及新版Q0影响矩阵保留在[决策备忘录](gate8_integrity_q0_decision_memo_v0_1.md)；不重开旧证据或追认资格。

## 2. 英文询证草稿（仅本节供用户审阅后发送，无附件）

**Subject: Nsight Systems 2026.2.1 Windows — explicit CUDA/NVTX capture completeness evidence and API coverage**

Hello Nsight Systems team,

We need to distinguish a complete trace from an unverified trace for reproducible analysis. Our target is Windows x64, RTX 4090, Nsight Systems CLI `2026.2.1.210-262137639646v0`, with installed `cupti64_129.dll` FileVersion `2025.2.1.0` (application CUDA runtime: 12.4).

The observation profile uses `--trace=cuda,nvtx --sample=none --cpuctxsw=none --cuda-memory-usage=false --cuda-trace-scope=process-tree --isr=false`. Collection and SQLite export are separate. We have not enabled `--cuda-trace-all-apis`.

Could you clarify for this exact Windows build:

1. Is there an explicit dropped/lost-record count, including an explicit zero, or equivalent completeness statement for CUDA activity/API records and NVTX application marks/ranges? Where is it available (REP view, SQLite table/columns, collector log or supported interface)? Please distinguish each channel, target process/child process/context, and the entire capture interval from system-wide tracing or CPU sampling.
2. What are the counter scope, initialization/reset/read semantics and final-flush guarantees? Does the evidence cover buffered records at shutdown and losses during collection, transport and export? How are missing or incomplete finalization and unsupported channels reported? We cannot treat absence of warnings or a successful export as proof of zero loss.
3. The installed User Guide documents `--cuda-trace-all-apis`, while the Release Notes state that the CLI API subset cannot be changed. Which applies to this build? Please identify supported default/optional coverage of Runtime/Driver stream, device/context and event synchronization, event record/stream-wait-event, launches and memory operations, and associated correlation/context/stream/event identifiers. Are NVTX point marks/ranges covered independently of that CUDA filter?
4. If no supported interface establishes completeness for these scopes, please state the boundary explicitly, including any documented prerequisites or alternative supported mechanism. We are asking about supported evidence, not a guarantee inferred from quiet logs.

Version-specific documentation or a schema/example without application data would be very helpful. No trace, database or environment dump is attached.

Thank you.

## 3. 中文说明与官方渠道

问题分开询问“通道是否收全”“计数的生命周期”“必需API是否被过滤”，防止把CUDA局部计数套到NVTX或全会话。厂商说支持某开关仍不等于获得每次run的完整性证据。只发送上节的必要版本、profile和问题，不发送本说明的私有回执、REP/SQLite、环境快照、令牌、模型或用户数据。

首选 [NVIDIA Nsight Systems / Profiling x86 Windows Targets 官方论坛](https://forums.developer.nvidia.com/c/developer-tools/nsight-systems/profiling-x86-windows-targets/122)。本轮只读确认该分类存在；未登录、发帖或上传。备选 [NVIDIA Bug Tracking System](https://developer.nvidia.com/nvidia_bug/add)，账户与权限由用户自行确认；不同时重复提交。

渠道依据：目标安装 UserGuide.html L10705–10709 的 For More Support 明确链接官方论坛和 Bug Tracking，并说明提问/报bug需 NVIDIA Developer Program 注册；对应[2026.2 User Guide](https://archive.docs.nvidia.com/nsight-systems/2026.2/UserGuide/index.html#for-more-support)。本轮在线归档直链读取失败，不冒称网页本轮已读；渠道说明已由哈希固定的完整安装文档直接确认。若厂商要求原始产物，必须先单独审查脱敏及用户授权，本草稿不授权外传。

## 4. 答复后的有限决策路线

| 情形 | 下一项动作与停止条件 |
|---|---|
| 支持且给出充分合同 | 主窗口核对精确build、通道/PID/区间、重置及final flush、导出谱系；设计版本化provider提取/拒绝合同与独立负例。只有局部计数、泛化flush建议或营销式保证仍不充分。完成审查后另行申请最小平台/Q0验证；不因邮件直接生成 ZERO_CONFIRMED 或授权采集。 |
| 明确不支持所需范围 | 固定不支持的版本及scope，保持UNKNOWN。向用户提出保留当前collector但暂停科学验收，或评估有肯定完整性接口的collector/sidecar；后者需observation amendment、开销/干扰审查及受影响新版Q0。任何缩小完整性判据/研究claim的方案也必须显式裁决，不能工程上降门槛。 |
| 无答复或仍含糊 | 建议从用户实际发送日起10个工作日设置一次决策检查点（项目建议，不是厂商SLA；未发送不开始等待）。到点关闭等待，记录“支持能力未确认”，向用户提交同上替代路线，不反复搜索或默认换collector。若只有一个具体歧义，可由用户选择在同一询证中集中澄清，不能自动续期无限等待。 |

当前没有发送、自动提醒或监控任务。下一项最小动作是用户审阅草稿并决定是否/通过哪个渠道发送；服务器无需操作。新版Q0资格不继承Gate6；Gate7历史PASS不撤销，Gate8 NOT_RUN。没有改生产代码、冻结合同、collector或旧证据，没有运行GPU/Nsight/Q0。
