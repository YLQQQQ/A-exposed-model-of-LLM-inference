# Gate8 接口差距审计 v0.1

2026-09-25；Engineering / 规划；Gate8 `NOT_RUN`。本文件不授权实现、GPU、真实 Nsight（含 export）或实验。Gate7 PASS 及其 legacy-only 限制不变。

## 1. 权威与审计身份

- 研究目标：`docs/current/ExposedPath_研究设计.docx` v7.1；执行依据：`docs/current/ExposedPath_实验协议.docx` v2.1、Pre-Pilot。后者 §3.7 的 Q0/Pre-Pilot Go–NoGo 及 trace 质量要求不能由 Gate7 legacy 验收替代；DOCX 的早期进度描述不覆盖当前科研进度。
- 冻结规则：[Measurement Contract v0.2](measurement_contract_v0_2.md) §4–5、§7、§9–12；[S 合同](s_layer_v0_2.md) §2–6；`contracts/canonical_raw_schema_v0_2.json`、`ab_schema_v0_2.json`、`derived_schema_v0_2.json` 及 Gate6 amendments。
- [Gate6 closeout](gate6_closeout_v0_1.md) 证明目标栈的受控 Q0/oracle 正确性，不证明真实模型全链；[Gate7 closeout](gate7_closeout_v0_1.md) 证明 runner/instrumentation/legacy 后处理集成，不证明 v1.4.1 科学链。
- 本地审计代码：main `f8c6b050476cf91b53bf158645bb09c36a1b960f`。历史输入执行 commit：`8d64f7580d43d7c8e1cb7a416b459cec8f60b011`，唯一 Gate7 PASS attempt `smoke_20260924T084657Z`。本轮未重跑测试/采集，不修改历史 report。
- 用户回传服务器固定 checkout 仍为 clean 8d64f75，YLQ 下 evidence/diagnostics/logs/transfer 容器已建。layout receipt 尚未直接取得；机器路径和回执位置仅在本机 handoff。

## 2. 实际历史输入诊断（不是 Gate8 evidence）

只读原 SQLite，调用当前 `inspect_sqlite`、`convert_sqlite_to_canonical`、`analyze-s`、`analyze-ab`；所有新产物写入忽略目录 `.local/diagnostics/gate8-gap-v0_1-20260925-r3/`。角色为 `HISTORICAL_INPUT_COMPATIBILITY_DIAGNOSTIC_NOT_GATE8_ACCEPTANCE`，没有改写/填充原 manifest。初次本地辅助脚本两次因 Windows 相对路径分隔符比较错误退出，保留旧诊断目录；r3 修正仅限本地辅助脚本，不是 analyzer 修复。

| 输入 | SHA256 |
|---|---|
| REP | `7d47d8f38a2069c816a8573b78d52c4932fbdd022013d532b5c1c23e78b6fa19` |
| SQLite | `005cf068bff99c36585a91343d8841d12bb2cad41a94bdc9bc1478045691877c` |
| 原 manifest | `36dac76945475615396892d6db37a21a264904d9bad8f81333719d7e2664fe07` |

原 REP、SQLite、manifest、machine report 四文件 SHA256 在诊断前后相同。私有数据不进入 Git。

- Observation 返回 `valid`，仅 `LAZY_EXPORT` warning；这**不证明 dropped records=0**。
- Canonical 成功生成，但 identity=`AMBIGUOUS`，缺 `pass_id/repeat_id`；execution_context.default_stream_mode=null，selected_device_id=3。
- S CLI exit=1：354 条 physical sync 全部 `INVALID`；输入原因 `INVOCATION_OWNERSHIP_AMBIGUOUS`，记录可见 `INVOCATION_BOUNDARY_INVALID`。这是全进程数量，包含模型初始化/warmup等，不能作请求覆盖率分母。仅作定位时按旧 full_request 范围完整包含筛查，两个 repeat 各 3 条；这不是已验收的窗口分母。
- A/B CLI exit=1：window_count=0，quality=`FAIL_CLOSED`，原因 `INVOCATION_OWNERSHIP_AMBIGUOUS`、`WINDOW_DISCOVERY_INVALID`。未继续执行 D/Signature，未补造窗口。派生 manifest 的 `q0_status=NOT_RUN` 是该产物资格，不撤销项目 Gate6 PASS。

## 3. Producer → consumer 差距矩阵

“有代码/测试”不等于“本模型真实输入已验证”。以下测试仅审阅其覆盖，本轮未重跑。

| 接口 | 已实现 / 已有验证 | 实物与差距 | 后续最小工作 |
|---|---|---|---|
| benchmark → runner 输入/Pass parity | 冻结 token IDs、host-readable helper、EOS/attempt、pre-model身份门；`test_runner_token_ready.py` / `test_runner_pass_parity.py`；Gate7实证通过 | 数值完成边界已验证，但不能直接与 Nsight 相对 ns 比较 | 保留控制流与身份；增加从真实 producer 输出进入新版 consumer 的集成回归 |
| runner → request/phase NVTX | `nvtx.py:make_invocation_label/make_phase_label` 仍输出 legacy；structured sync 已存在 | 12 range = 8 legacy + 4 structured sync，无 structured request/phase。`ab_inputs.py:_discovery_result` 只认后者 | 设计共同 completion 锚点及结构化窗口，而非给旧字符串改名 |
| completion → Canonical 窗口 | runner 的 perf_counter_ns 以最后 token-ready 结束；cleanup 不进入其数值窗口 | 独立 NVTX push/pop 与 helper timestamp 不同。两 repeat 的 prefill-start/full-start、decode-start/prefill-end、full-end/decode-end 差值分别为 (1291,2774,962)、(1602,2123,1062) ns；consumer 非Q0要求严格相等 | 共用边界及明确时钟映射/可观察锚点；不得套用仅Q0的 phase-spill exception、加容差或让 cleanup 进入窗口 |
| WMPC → Canonical identity | `canonical_raw.py:convert_sqlite_to_canonical` 要求 source manifest 的单值 pass/repeat；校验所有 structured rows | WMPC跨两repeat且缺pass/repeat，marker含0/1；给共享manifest填一个repeat将与另一repeat冲突 | 先决定版本化 per-pass/request identity 表或有明确lineage的分析单元；不按文件名/顺序猜，不丢弃未选中的原记录 |
| GPU identity → trace namespace | Gate7 physical/logical/UUID/PCI均通过 | converter fallback将 gpu_index=3 当 selected_device_id；实物 context/device activity 使用 device_id=0 | 显式通过target device/context事实和UUID映射关联，禁止把physical/logical/Nsight命名空间互换或只写死0 |
| 数据角色 | data_role=Engineering；旧 run_role=PILOT，marker一致 | 两字段用途不同，不得据PILOT字符串升级资格 | 新合同明确两字段及允许组合；保留旧原值，不静默重新命名历史数据 |
| Raw → S completion证据 | Gate6受控stream/device/event/context、default stream、ownership、correlation等已有Q0；`s_layer_v0_2.md` | 当前default mode未知，context null_stream_id=7；event行0；初始化/框架内部同步和callsite未由token marker完整覆盖 | 必需的scope/mode/event映射逐项查证；确实无event依赖才不要求其record；内部同步身份缺失保留invalid，不伪造natural_token_ready |
| Observation / diagnostics | CUDA+NVTX与context/stream等表可转换；69诊断行 | 11条“Not all NVTX events might have been collected.”，另有非目标进程警告；当前regex未匹配此句，未提供明确零丢失证明 | 明确dropped evidence来源及目标scope；不得把未匹配warning视作0，也不得直接套Q0专用scope豁免。不能仅以警告文本反推目标进程已丢记录 |
| S → A/B | 窗口发现、原子互斥、invalid优先、B逐sync均已实现；`test_v141_ab_inputs.py` 使用手写完整identity fixture；Gate6有受控真实证明 | 本真实模型0窗口，尚无request A科学验收 | producer-shaped deterministic trace回归，验证身份/窗口/关联缺失与重复；不能只测手工完备consumer输入 |
| Coverage | 冻结合同要求supported count/duration及失败分布；B-valid与supported不同 | 当前A/B bundle没有完整版本化request/phase coverage输出；既有legacy coverage=unknown不是替代品 | 先解决§4口径，coverage只揭示证据缺口，不是新贡献、暴露时长或完整request解释比例 |
| A/B → D/Signature → report | `derived.py`/schema已实现纯派生、零分母null | 本模型没有合格A/B输入；Gate7 launcher仍调用legacy analyzer | 新Gate8编排/报告显式调用Canonical/S/A-B/Derived，保留Gate7原验收合同；不能仅改最终PASS字符串 |

当前最小 profile 的 cuda,nvtx 是必要基础，但“可转换”不足以证明 completion/event/dropped 证据充分。CPU sampling、context-switch、memory-usage、GPU metrics、WDDM等不因进入Gate8自动变为必需；CUDA memcpy/memset activity 与 allocation/usage tracking 不同。只有定位到缺失的必需事实后，才提出限定采集变更和平台影响审查。

## 4. 集中待决项（实现前 review，不猜测）

2026-09-25后续收敛见[合同决策稿](gate8_contract_decisions_v0_1.md)：以下为首次审计问题清单，不再表示四项都需用户选择。协议§3.6已确定B-valid分母=支持sync；设备映射/多repeat承载已有工程推荐，仅D1边界表达与D2 coverage统计细则待批准，零丢失来源属于技术核验。

1. **边界表达与时钟**：批准前需给出 request-start/token-ready 共用可观察锚点怎样精确投影为三个窗口，以及 host clock 与 trace clock 的证据。现有独立range不满足非Q0相等约束；仅改标签不是可行方案。若需 schema扩展须显式版本化审查；若需改变 frozen completion 定义则停止请求新授权。
2. **多repeat身份与trace范围**：选择每pass带request/repeat集合的来源合同，或有可验证范围/外部依赖保留规则的分析单元。禁止修改旧WMPC、全trace硬填repeat0或为消除错误静默裁切Raw。初始化/尾部如何与请求区分，要保留作用域内的外部dependency。
3. **Coverage补充输出规则**：分母必须按稳定physical sync ID在目标窗口定义，不用全进程354条、marker数或B明细数。supported由S支持性/证据完整性判定（`VALID_EMPTY`不是B-valid），B-valid仅`VALID_NONEMPTY`且B条件满足；仍须明确跨phase sync计数归属、clipping、重叠duration用何种union/失败优先规则、零分母null及缺失/ambiguous状态。当前独立coverage schema不足以唯一确定这些工程统计；不能用duration求和充当request exposure，不能把B-valid率替代A守恒/validity。
4. **质量证据**：为非Q0真实workload制定有来源的dropped状态和进程范围；unknown必须保留且不能通过要求零丢失的科学trace质量门。如何取得可信零丢失依据尚未解决，不靠改正则或缺表=0放行。default-stream模式也必须有观测/配置依据，不能因缺少event表或flag猜定。

以上先审查技术设计；未确认前不开始新采集，不扩展N1/G1正式实验、参数扫描或性能排名。下一步见[最小计划](../superpowers/plans/2026-09-25-gate8-minimal-execution-plan.md)。
