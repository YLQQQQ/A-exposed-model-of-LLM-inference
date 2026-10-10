# Gate12 prepare工程修复重签与交付收尾 0.1.1

2026-10-10；`G12-CLOSEOUT/0.1.1`。**Gate12限定PASS，Gate13仍BLOCKED；本轮没有服务器或采集。**
用户明确授权沿用已批准的研究范围与六block预算，复核后记录此次精确候选重签。
这是前瞻人类授权记录，不是密码学签名或对历史结果的追认。

## 签署与源码身份

- [新签署发布](gate12_protocol_signed_v0_1_1.json)：G12-ROUTEA/0.1.1；approval ID
  `USER-20261010-G12-ROUTEA-011`；生效 `2026-10-10T03:25:04Z`。
- 协议规范化内容SHA256 `d9204a80bf15ce810093ec53c506d4bf3eadd2f1ad71db8844cff330f0c7448b`。
  发布文件SHA256 `1378c89db04336102a9dc0ce53ef7b1ef17dd9c518320c060e74d39abaa5b669`；
  approval规范化内容SHA256 `423852a31bd858a56255ca092bc370eb2349fc293ecab182c9fae7dbc562780e`。
- 执行/分析固定 **99f3bae966f2fb794073ff4d7468233b6b8dd2ac**（parent c443c105018606b6b7a7f9992c6ad574990e3e16）。
  本签署/进度文档提交不是执行身份。外部控制器也取99f3bae；五个交付helper与旧c5fcb77逐字节相同。
- [0.1.1候选](gate12_freeze_candidate_v0_1_1.json)文件SHA256
  `22c644a5e1bad12fea62f8fcf48f50b926df1f743bbbd6156a666710b93d8566`，原approval=null状态保留。
  新签署另列，不覆盖候选或[旧0.1发布](gate12_protocol_signed_v0_1.json)。
- 126源码/合同Git blob及12项schema/registry、资格引用均核对；无候选/发布自引用。
  实际运行文件须另seal：只允许已列的Git LF与其显式CRLF表示，不任取当前hash放行。

## 接线与兼容审查

prepare先校验已签署binding/source/输入文件，再复制输入；finalize从实际副本计算文件字节SHA256/WMPC，
随后执行原严格Formal校验，全部通过才写manifest。missing、原输入或副本内容变化、hash/config/身份冲突仍拒绝。
后续verified入口重新核对prepared内容、角色、设备和实际producer；不是只在prepare检查一次。

版本闭集仅 **G12-ROUTEA/0.1 与 G12-ROUTEA/0.1.1**。封套仍G12-FORMAL-ENVELOPE/0.1；
reference字段仍只含protocol_version、protocol_sha256、approval_sha256，closed schema禁止其他字段。
0.1与0.1.1各有独立reference定义，未知版本/畸形hash拒绝；0.1.1必须锁定新schema。
ledger/NVTX reference还须与自己的已签署binding精确相同，不能跨版本混用。
未签署、旧approval用于新内容、旧角色改名、错误schema源码或角色/输入/配置冲突仍不接受。

复用7.124的最终 **150 passed / 0 failed / 0 skipped，67.07s**：五条件×双pass×新旧版本实际
prepare→verified CPU替身→producer文件链和拒绝负例，本轮不重跑。只复核回执、源码/签署hash、计划及交付；
新增签署核验调用生产validate_release和60槽位plan，没有模型、CUDA或collector操作。
设备/模型CPU替身不能授目标机或全面新Q0资格。

## 保持的研究与数据边界

输入/模型内容、batch1/eager/SDPA、G32/G512/N0/Nm/N16、32或512输入/2输出、w3/repeat1、
六平衡block/60进程/30profile及固定组序/pass序、完整block统计、signed差、质量门与原payload一致。
P0性能与P1观测A/合格单sync B分开；不从A扣配对差，不跨sync累加B，不授P1→P0精确组成迁移或10/5ms保证。
G1仅自然投影A；N1显式流及预定干预；opaque内部等待不拆，D/Signature关闭；UNKNOWN/NOT_ASSESSED保持。
没有新增语义、输入选择、资格实验或预算，无自动retry/resume/替补/续采。

旧失败ZIP/报告/旧seal/0.1签署完整保留。首槽在prepare失败：未启动模型或Nsight采集，
仅解释器及最小CUDA身份查询发生，Formal测量样本为0。旧Engineering/Pilot和BLOCKED不升级。

## 唯一新交付与停点

`gate13_99f3bae966f2_signed_delivery.zip`，**106697 bytes**；SHA256
`c223b8b09710a02727449cc3962b1b675916e73ea78440447f96daf30401f677`。
15文件/14清单、CRC/完整覆盖/大小/hash通过；清单SHA256
`ada313cfbb92a4e29718709b13af0aadeadae8ab22e6acd042e1620d17a6ae27`。
复用增量bundle63889 bytes / `a33d7393b1f50194d9343c8d10a7a69922c1aad23ed4e95bb1bdb0493dfe275e`，
服务器前置e38fa91850b8f31e17cc0ee264987ef3c1313d7d，verify通过。
launcher SHA256 `26b88cada4be7537fe6bfb4300fe29476d978fe11304be91157c9dce4c6d6472`，与旧helper相同；PS5.1只解析语法通过。

阶段A默认仅传输/固定版本部署及CPU身份/源码/签署/输入/60槽位检查，不跑已完成150项、不初始化CUDA/模型/collector。
A单ZIP回传并经协调审查后，用户才独立显式阶段B；新输出目录不复用旧首槽失败现场。
阶段B沿用200–240分钟粗估/42.1GB原件/90GB空间门，CPU后处理与封包时间另计，不保证精度。
硬失败或固定预算结束停、partial/NOT_RUN保留；完整批次仍STOP_FOR_REVIEW，不自动Gate13 PASS或信息增益成立。
清理只在批次审查及完整归档核验后生成准确文件清单/安全逐文件命令与回执；当前不清理。
机器路径、完整A/B命令和回传路径在忽略的本地交付说明，不提交私有配置。
