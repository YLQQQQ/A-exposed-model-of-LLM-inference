# N1 模型最小接线 0.1（本地调用层）

历史部分实现记录：当前接线与交付状态以[0.2](n1_model_wiring_v0_2.md)及research_progress 7.104为准；下文“剩余/尚未交付”是31cd84e时点，不是当前待办。

状态：部分实现，**不是可部署采集入口**；N1模型可行性仍NOT_RUN。Gate10限定G1 PASS不变。
依据：当前研究设计v7.1、Pre-Pilot实验协议v2.1 §4.2、[Gate9分域合同0.1](gate9_domain_qualification_contract_v0_1.md)。不修改冻结S/A/B、历史资格或G1自然执行，不是Pilot/Freeze。

## 已有决定，无需重新选点

协议§4.2的首选V16明确为“每个Decode iteration第16层后current-stream sync”；V8/V24是后续可选点，本轮不启用。
此处`Vsync`明确对应V16：Qwen2第16层（零基index15）forward返回后、下一层之前，一次/decode forward；不在prefill插入。
首批拟复用32输入/2输出、batch1、fp16、eager/SDPA/use_cache/greedy、warmup1/repeat1。
2输出只有一次measured decode，因此Vsync恰有一次测量窗内干预。Vmarker同callsite/分支/范围标记但不调用同步；V0不安装layer干预包装。
三组具有相同的公共调用观察、输入和专用流策略。不是根据既有A比例或“明显效果”选位置。

## 本次已实现及验证

- `exposedpath/n1_model.py`：`exposedpath-n1-model-calls/0.1.0`，独立opt-in adapter，复用未修改的`run_one_invocation`及其host-readable completion/EOS/drain。G1、旧CLI和Gate9受控入口不变。
- 使用仅在decode期间安装的instance forward wrapper，不复制Transformers forward、不注册持久forward hook。原args/kwargs/cache/返回对象不变，异常后恢复原descriptor或已有instance override。V0不包装层；Vmarker/Vsync的范围数量和嵌套相同，只有实际sync调用不同。NVTX sync-callsite标签不是已执行sync的证明，`synchronize_called`和Raw API才是执行事实。
- 复用Gate9 `StreamBridge`的实际current handle/device/native-thread检查及current-stream synchronize调用记录；逐call保存request/pass/repeat/attempt、层位/token序号、held generation、前后handle、成功/异常。**这些不提供trace context/stream/correlation，也不证明框架内部没有其他流。**
- resident文件入口只接收调用方已验证并加载的模型，不自行加载模型或启动采集。执行前封存plan/prompt字节及hash；实际tensor来自该prompt；闭合字段、EOS声明/实际tokenizer值、mode/backend/计数冲突拒绝。记录实际模型class/config、源码字节hash，不把预期平台或权重内容复制成实际证明。
- 三组均在同一held专用流上完成variant对应warmup，再复用原成功device drain及三个completion边界。warmup在测量窗外，物理前缀必须保留；held marker不是native fresh-create/destroy证明，不截断物理W/B。完成cleanup/文件写入在测量窗外。
- 新目录独占写入，无覆盖/恢复；失败回执保留原异常。输出明确为`COMPLETE_PENDING_TRACE_OWNERSHIP`、`physical_ownership=NOT_ASSESSED`、`n1_model_feasibility=NOT_RUN`，不能被当成domain/资格报告。

tests-first：先见缺入口的11项红例；另见marker结构差异、缺resident入口、超出两token范围及输入封存缺失的红例，再做最小实现。
相关CPU五文件 **62 passed**；修改Python compileall、diff-check通过。真实runner函数＋CPU模型/设备替身，实际文件/hash/失败链；不是Qwen或CUDA执行。
独立预期：所有组token相同；prefill无干预；一次decode的V0/Vmarker/Vsync实际sync数0/0/1；第16层后且第17层前；共同completion不变。
覆盖错variant/backend/identity/stream、重复/缺层调用、原异常/恢复、EOS、错prompt/EOS/mode/device/声明、目录覆盖及失败回执。
复用相关Gate9 N1回归中correlation、identity、flags、generation/drain等拒绝行为；没有宣称新增模型consumer已经获得这些资格。

## 明确剩余工程接线，不向用户转交普通实现选择

当前Gate9 `bridge_bindings`要求每个submit/copy/wait标记恰对应一个API，且窗口内所有提交/同步均被绑定。
一个模型forward含大量kernel/API及内部同步，**不能把它伪装成Gate9单操作，也不能删除unbound检查**。
本轮新sidecar尚未进入该consumer；因此本地模型端到端接线未完成，不发采集包。

下一段最小本地工作（沿用本授权，不需重选层位）：

1. 将resident子入口接到已有显式解释器/isolated preflight/model-content验证路径；生成真正的执行前WMPC manifest和pass ledger，固定三组公共配置/输入/源文件身份及输出token parity。当前resident plan仅是子合同，不能代替该验证。
2. 为实际模型多API记录接上Canonical文件消费者：将实际native调用绑定到trace context/stream/correlation，再检查所有已观察提交、内部blocking调用和必要依赖。V0/Vmarker也必须有独立实际stream桥接证据，不能从Vsync或`with stream`复制资格。保留Gate9物理S/B、完整warmup前缀/closed-prior及全部未知/冲突拒绝；补实际文件链反例。
3. 上述完成后才固定单包/整段命令交协调窗口。不是缺少新研究语义授权，也不是要求重跑完整Q0。当前不需要用户服务器操作。

## 首批目标机验证的问题与停止条件（尚未交付/授权执行）

仅32/2三组各warmup1/request1：验证实际层位/次数、token一致、三窗口、成功窗前drain、专用流实际归属及内部同步是否落在已获资格域。不能用一次差值评价干预效果、选Pilot阈值或授Formal。
直接复用Gate9显式流S/单sync B和已获资格A语义、目标栈身份/模型内容快照；新证据只补真实模型调用/依赖与支持域，不重采旧Q0/G1。
任何身份/输入/实际backend冲突、early EOS、OOM/超时、缺correlation/边界、未支持其他流/依赖或新型影响不明诊断均停止，不自动重试或改位置。旧官方诊断处置只按已获准适用条件复用。
完整原始日志、plan/manifest/实际调用与退出、Raw/export/Canonical/域报告及hash清单将统一单ZIP；此处不是可执行服务器指令。
