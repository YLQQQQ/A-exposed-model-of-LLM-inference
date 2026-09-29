# Gate9 最终分域资格裁决 0.1

2026-09-29；`G9-DOMAIN-CLOSEOUT/0.1`；**Gate9 = PASS**。
裁决依据为用户批准的[G9-DOMAIN-QUALIFICATION/0.1.0](gate9_domain_qualification_contract_v0_1.md) §2–5，
不是新amendment，不更改冻结测量语义。适用分析实现固定为`fe25d5ba9fca27a3055d7ad00bb1d0f8982a653b`。
本提交只签发限定平台/分域资格；它不是服务器执行commit。

## 退出条件与证据对应

| 合同必需项 | 已有可复查证据及类型 | 裁决 |
|---|---|---|
| 平台/设备/代码/输入身份及eager能力（§1/3/5，EP-G9-01/03） | [Gate8配对实物](gate8_conditional_closeout_v0_1.md)的runtime、seal、模型/config、UUID/PCI映射；[7.98桥接实物](gate9_bridge_return_review_v0_1.md)复核producer/ledger/trace launch、源码/DLL与解释器 | 满足当前固定栈，不推断服务器此刻未变化 |
| N1实际current-stream调用与ownership（§3/5） | 执行15b24ec的两request目标实物：14调用由NVTX/API/correlation连接native handle、持有lifetime、context1/stream13；成功窗前drain、实际非默认非阻塞流；不是仅凭with-stream | 满足限定专用流桥接 |
| N1完整W、terminal、单sync B与三窗A（§4/5） | 7.98在不变Raw上用fe25d5b离线；未改独立Raw oracle，六W成员数1/2/4/5/6/8、terminal、hidden/exposed/tail及六窗A匹配；第二request保留已完成物理前缀 | 满足；不跨sync加总B，不扩大request窗口 |
| G1身份、completion、drain及自然执行（§2.1–3） | [限定受控资格](gate8_bounded_qualification_review_v0_1.md)及Gate8真实Qwen配对的三窗口、主线程、成功drain、全部blocking API/必要后缀；[1733ff3分类审查](gate8_non_submit_api_review_v0_1.md)独立裁窗和分类依据 | 复用事实作为适用性证据；旧Qwen输出仍条件性Engineering，不追认新科学数据 |
| G1必要集合/依赖边及投影证明（§2.4–5） | 7.97/fe25d5b的`tests/test_gate9_domain.py`实际文件入口：必要成员/依赖边两模式检查；独立手算三窗45/15/15/25/0、长度变体及同A数值却错成员反例；既有Qwen实物逐成员后缀一致 | 满足“本地增量验证＋既有实物复用”的合同路径；不只靠守恒/数值等价，不授默认流物理B |
| 缺证据、冲突和局部缺口（§2.6/4） | 同文件缺correlation/drain/boundary/worker/stream/未知warning/版本/N1 marker拒绝；独立5ns局部分类证据故障保留unattributed；N1文件链含身份/lifetime/映射反例 | CPU确定性拒绝行为已验证；不冒称真实GPU故障注入或用unknown填Host |
| 诊断与版本封套（§2/3） | 7.89已接受官方解释＋7.98目标采集实物；版本化review正反例，原diagnostics及UNKNOWN保留；文件链重读与hash来源已核 | 满足本组消息适用条件；新消息/冲突仍按质量门拒绝 |

N1目标机CPU原日志102 passed是服务器静态证据；7.97本地核心101 passed及追加17 passed有重叠，不相加。
fe25d5b本地相关36 passed、G1/旧diagnostic24 passed及静态检查见7.98。本轮仅引用，不重跑测试/离线计算。
7.97曾记录的旧测试把已支持non-submit当unknown的失败保留；它已在旧基线复现，不能删除记录或称全量全绿，也不否定本合同独立字面预期。

## fe25d5b修复的资格影响与历史边界

- warning：原N1入口未接入已接受的`G8-WARNING-EVIDENCE/0.1`，现按精确消息/版本/namespace/目标实物条件处置，未降低边界、identity、dependency门。
- stream：区分runtime创建flags=1与CUPTI type=2（NON_BLOCKING），拒绝DEFAULT/NULL/UNKNOWN。Raw/Canonical编码和S/A/B公式均未改；真实bridge本包无默认流活动，不把此证明推广为跨默认流资格。
- 执行commit仍为`15b24ec744616754f6fdd437bd333aa8a2059bf1`，分析修复为fe25d5b。
  原ZIP SHA256 `4bf17fb1ded2fa6f6d54e041c196d0817703d94132afe375fc114a9ca6c2b5ea`；
  独立续算domain SHA256 `8332c978d68b15805e93c96a1fc0f9bd20de9b0adbe6d29aaa89a6e7db6eb938`；
  oracle续算报告SHA256 `7c8377f2ad64f4b60785f4c613adf1b52b40aafbb9a176a0ae3ef85fd0149d0c`。
  完整清单/REP/SQLite身份沿用7.98，不重新包装证据。
- 原attempt、receipt、collection_report继续BLOCKED；原probe继续INCONCLUSIVE；旧Qwen条件标签及UNKNOWN/NOT_ASSESSED不变。
  本文件是独立资格裁决，不回写机器报告。分析侧修复无需重新采集；未来实际执行仍须钉住经核对的执行/分析版本，不能默认服务器已部署fe25d5b。

## PASS的确切支持范围

当前Windows/RTX4090单GPU、CUDA12.4（nvcc12.4.131）、PyTorch2.6.0+cu124、Nsight2026.2.1.210-262137639646v0及已封存关联环境；模型路线为Qwen2.5-1.5B-Instruct/eager。
N1仅获同显式非默认非阻塞专用流合同下A与**合格单sync B**的适用资格；完整V0/Vmarker/Vsync模型runner与矩阵未被宣称已执行。
G1获自然request/phase**投影A**资格，不改变自然执行，不授自然默认流完整物理B/hidden，也不将N1机制直接套用到G1。

仍以单request主要线程、可恢复的实际FIFO/ownership和**无未记录incoming依赖**为支持域条件；后者是声明的假设，不是工具证明。
逐request必须核验身份/边界/drain/同步与必要集合/诊断；可见冲突或影响无法界定即拒绝，可定位局部缺口才进入unattributed。
输入长度改变本身不重Q0，但新语义/新依赖或平台栈变化按影响增量评估。当前不批准warmup历史无法映射的流复用。

不授全部新版Q0、Pilot、Protocol Freeze、Formal、信息/决策增益、第二平台或compile/graph资格。
不证明零丢失、无共享采集故障或不存在未记录依赖；D/Signature不启用。没有剩余Gate9必需证据缺口。

## Gate10唯一最小下一步

Gate10为NOT_RUN。先在本地按已选单模型/eager路线，固定有限信息增益对照所需的最小workload候选表（输入/token内容、长度/output/batch、N1/G1域及比较目的）。
复用自然G1 32/2、batch1已完成的可行性记录，但不把该点外推成其他长度或显式流N1模型可行性。
只对最终选定且无既有证据的点拟定有界可执行性检查与OOM/early-EOS/身份/质量失败停止规则，再交协调窗口审查。
本轮不采集，不广域OOM扫描，不选Pilot重复数、统计阈值或开销政策；目前无需用户服务器操作。
