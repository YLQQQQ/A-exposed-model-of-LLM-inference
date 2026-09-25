# Gate8 本地实现状态 v0.1

历史第一批记录；当前状态已由[v0.2](gate8_local_implementation_v0_2.md)取代，以下“未完成”是当次状态。

2026-09-25；基线 `8ea177e15fa09f28f1d1603f88c412d8fb3f416c`。用户已授权 D1/D2 本地 tests-first 实现、文档及正常提交推送；未授权服务器部署、GPU/Nsight 或旧证据重新验收。

**这是第一批本地实现，不是完整 Gate8 就绪声明。** Gate7 历史 PASS 保留；Gate8 / 新版本 Q0 均 NOT_RUN。package/analyzer 升为 `0.3.0`；新 adapter `exposedpath-gate8-adapter/0.1.0`，不继承历史 `0.2.2` 的 Q0 资格。旧默认 Q0 路径、冻结 schema、oracle、evaluator、Gate6/7 closeout 不改。

## 已实现的本地 API 与验证路径

| 层 | 入口与显式版本 | 范围 |
|---|---|---|
| Producer | `runner.run_gate8_requests`、`Gate8BoundaryRecorder` | 对已 resident 的输入调用原 `run_one_invocation`；记录实际 COMPLETE/EXCLUDED/FAILED、warmup/measured 与全部计划项。Pass0 不发 NVTX；Pass1 以原 helper 的 Host 可读结果后发非同步 point。无新增 GPU sync/event；原 CLI/launcher 不自动切换到新 API。 |
| Identity / device | `make_gate8_pass_identity`；`convert_sqlite_to_canonical(..., gate8_sources=...)` | 独立 per-pass 多请求 ledger；physical/logical/inventory/activity namespace 通过 UUID/PCI、PID/context 验证，不按编号相等猜测。缺字段、多候选、冲突或坏结构化 marker 拒绝。 |
| Scope | `project_completion_scopes`、`load_projected_ownership` | `G8-OBS-BOUNDARY/0.1.0`；保留原 point/clock/Raw refs、Host ledger 字节、anchor artifact；解引用后按 r/t0/tLast 重算三个窗口。新 scope bundle `exposedpath-gate8-scope-bundle/0.1.0`。 |
| S/A/B 接口 | `build_projected_ab_inputs` | S 与 A 共用已核验的内存 `ProjectedScope` ownership view；不将其写成 Raw NVTX range，不提供 dependency/terminal 证据。复用现有 S/A/B 算法；跨期/外部活动仍保留。低层函数只供计算与确定性测试，不是验收入口。 |
| Coverage | `coverage_from_inputs`、`calculate_window_coverage` | `exposedpath-sync-call-coverage/0.1.0`；复用 semantic sync universe，按 physical UID 去重、逐窗裁剪，B-valid 分母为 supported；零分母 NOT_APPLICABLE，缺证据 UNKNOWN/null。无法分类的可能阻塞 API 不被悄悄排除。 |
| Integrity / 入口 | `nsys_unknown_receipts`、`assess_integrity`、`analyze_gate8_local` | `exposedpath-observation-integrity/0.1.0`；检查双通道、范围、Raw/pass/session 与状态一致性。结构一致只叫 EVIDENCE_SHAPE_CONFIRMED，不叫 PASS。实际 Nsight provider 未实现，默认 UNKNOWN/BLOCKED，不产生科学 A/B 数值。 |

`analyze_gate8_local` 的输出版本为 `exposedpath-gate8-local-analysis/0.1.0`。仅显式 synthetic fixture + 双通道肯定 receipt 形状一致时，写独立 S/A/B/coverage 派生产物与哈希；必须标 `SYNTHETIC_REGRESSION_ONLY` / `SYNTHETIC_CALCULATION_ONLY`、measurement validity NOT_ASSESSED、Q0/Gate8 NOT_RUN。这条测试通路不是可供真实 collector 使用的 fallback。

`gate8_sources` 必须显式包含 `pass_identity`、`preflight`、`cuda_probe` 三个文件。preflight 提供 `gpu_index_physical,gpu_uuid,pci_bus_id,cuda_device_order,cuda_visible_devices`；同进程 probe 提供 `pid,gpu_index_logical,gpu_uuid,pci_bus_id,cuda_device_order,cuda_visible_devices`。这是本地 adapter 的已知字段接口，不会猜测任意旧 telemetry 字段。上线前仍需接入并核验目标平台同进程 probe 的实际生产路径。

## 测试证据与评审

四阶段均先运行新增失败测试，再实现并运行绿测：初始身份 14 fail → 14 pass；共同锚点 6 fail → 6 pass；D2 10 fail → 10 pass；完整性入口 11 fail → 11 pass。后续补充真实 runner→SQLite fixture→Canonical→projection→S/A/B→coverage 联结、EOS/Pass0 parity、单 token 空 decode、坏 marker、乱序 ledger、sidecar 篡改、未知 API 和缺 PID 等回归。测试使用 fake token/model 与人工固定 trace 时间，不调用 GPU 或真实 Nsight。

手算主例固定为 full/prefill/decode 的 supported count `3/4,1/2,3/4`，supported duration `130/190,60/80,70/110`；B-valid 分母分别 `3,1,3`。另一个完整接口 fixture：full=200ns，A Host/API/wait/residual/unattributed=`165/5/10/20/0`，其中 W activity `[150,160)`，不能把整个 sync-prefix 当成 wait。coverage 开关不改变 A。其余旧 Q0/语义回归由仓库 CPU suite 覆盖。

本轮自审按来源→producer→adapter→scope→S/A/B→report 逐层检查；遵循研究 skill 不启用未经用户明确请求的子 agent，**不是独立第二位审查者签字**。发现并修复：真实 sync producer 丢弃 attempt 字段、Pass0 空 NVTX range、ledger 按数组顺序匹配、坏 marker 被忽略、device sidecar 未复核、未知 API 被排出分母。最终命令结果以 research_progress 当次记录为准。

## 未完成事项与停止边界

1. **带符号时间兼容缺口**：D1/Canonical 允许 signed-int64，冻结 `ab_schema_v0_2.json` 的窗口/同步时间及 `intervals.py`、A/B 部分校验仍要求非负。新 Raw/anchor/projection 保留负数；送入 A/B 前明确报 `GATE8_SIGNED_AB_ADAPTER_NOT_IMPLEMENTED`。没有平移时钟、截掉负时间活动或改旧 schema。不能称 D1 所有时间域已经贯通。下一批应先核对并版本化新 profile 的 A/B 时间字段适配（保持旧路径），补负时间下 hidden/exposed union 的独立预期；若需要改变冻结公式而非表示约束，先报告，不自行实施。
2. **真实完整性 provider 仍 UNKNOWN**：官方资料尚未建立目标 Nsight 全会话肯定零丢失来源；receipt shape、exit0、无警告、SQLite integrity 均不能替代它。未更换 collector、未注入 CUPTI reader。
3. **服务器编排未启用**：本轮提供本地显式 API，不修改 Gate7 launcher，不启用新服务器 CLI。还需固定实际 preflight/probe/WMPC/模型内容及 pass plan 的文件生产、不可覆盖生命周期、Gate8 S/A/B→既有 D/Signature 的发布包装和相应接口回归；未完成之前不提交采集命令。
4. **资格未继承**：boundary amendment §6 的 scope/ownership、设备/event/correlation、完整性/default-stream、empty/tie/race/D2H/query 及全部 23 case 静态差异审查仍须维持。现有 CPU 回归不等于新 profile 的真实 Q0。后续哪些 case 重采/重放，按实现最终 diff 决定并另行授权；历史 Gate6 PASS 不撤销。

本批不修改冻结数学合同，不追认 Gate7、失败 attempt 或历史诊断。上述技术缺口尚在，**不能将四类本地 API 的存在写成 Gate8 实现全部完成或部署就绪**。
