# Gate12 限定路线A签署与收尾 0.1

> 2026-10-10：本页保留旧0.1签署历史。prepare修复已按用户授权重签[0.1.1发布](gate12_protocol_signed_v0_1_1.json)，当前以[0.1.1收尾](gate12_closeout_v0_1_1.md)为准。旧seal/失败现场不改，Gate13仍BLOCKED，不能执行原e38阶段B。

2026-10-09；`G12-CLOSEOUT/0.1`。**Gate12 PASS，限于本页签署范围；Gate13 NOT_RUN。** 用户本轮明确接受有限P0性能/P1机制、限定Formal适用及六block预算，并授权记录签署。服务器执行仍须协调窗口审查交付和静态回执后，由用户显式启动。

## 唯一生效身份

- [签署发布记录](gate12_protocol_signed_v0_1.json)：`exposedpath-signed-protocol-release/0.1.0`，批准ID `USER-20261009-G12-ROUTEA-01`，生效 `2026-10-09T13:21:15Z`（北京时间21:21:15）。人类授权由助手记录，不冒称密码学签名或第三方认证。
- 协议 `G12-ROUTEA/0.1` / 封套 `G12-FORMAL-ENVELOPE/0.1`；规范化协议SHA256 `389a28a17bec830e4f32bea72c259dce15ba279ce69fc20caebfdca88a1326e2`。执行和分析均固定 **e38fa91850b8f31e17cc0ee264987ef3c1313d7d**；文档/外部批次控制器提交不冒充执行身份。
- [未签署候选](gate12_freeze_candidate_v0_1.json)保留原件，文件SHA256 `78cff3228d00b8410a42d51930df4556121eaf879eb95b430c9365ac8788e761`，其approval=null/预算未批是历史状态。签署发布另列实际批准，不重写候选。
- 闭合协议payload内的 `status=FREEZE_CANDIDATE` 是既有封套0.1要求的固定内容字段，**不再承担发布生效状态**；真实状态由外层SIGNED发布和hash匹配的人类approval决定。不得改payload以绕过兼容性或改变已批准内容hash。
- 125个Git内容锁和11项schema/registry、限定资格引用保持；运行时实字节另seal，显式LF/CRLF表示证明不替代实际执行字节身份。模型revision UNKNOWN，固定内容清单；用户修改DOCX仅为审阅来源，不覆盖或纳入提交。

## 退出条件与依据

| 必需项 | 结论及依据 |
|---|---|
| 问题、有限claim、统计单位与固定预算 | 用户当前明确接受；[冻结草案0.1](gate12_protocol_freeze_draft_v0_1.md)§1–6和[科学审查0.1](gate12_scientific_readiness_review_v0_1.md)，公平baseline允许不支持/不确定 |
| 执行/分析与schema/registry/source绑定 | 本轮复核候选125个Git blob、11版本、限定资格引用、协议hash及无自引用；固定e38fa91，不追随main |
| 前瞻角色、拒绝与真实文件链 | 复用进度7.120最终九文件 **224 passed/0 failed/0 skipped**、语法/审查记录；本轮不重跑。未签署、旧角色升级、错身份/hash/输入、partial block均拒绝 |
| 平台与正确性资格的限定Formal适用 | 用户接受候选中的分域资格复用；Gate9桥接/G1投影A、RAW_PHYSICAL与窄域opaque、Gate10选定点和N1、Gate11政策实物。**不是完整新版Q0或全局模型科学有效性** |
| 签署、生效与失效规则 | 版本化人类批准回执已落地；只接受签署后新声明/新采数据。实质变化须新协议并标明受影响Formal失效，不能事后调规则或追认旧BLOCKED |

## 固定研究边界

五条件G32/G512/N0/Nm/N16、输入32或512/输出2、batch1/eager/configured SDPA、warmup3/repeat1、六完整block，60新模型进程/30profile。固定pass与组序；硬失败或预算完成即停，无补采、替补、retry/resume或显著性停止。独立重复是完整block，不是kernel/token/sync。六block不保证10/5ms精度、平稳性、独立性或稳定收益。

P0报告未profile同合同性能，P1报告观测执行的投影A/合格N1单sync B及同窗公平count/sum/union/mapping/timeline。保留signed配对差和全部有效样本；不从A扣差，不迁移P1为P0精确组成、不跨sync求和。自然G1无完整物理B；opaque allocation内部等待不拆，A_device_wait只覆盖支持的同步恢复。D/Signature、G2、多平台/模型、OOM边界、compile/graph不启用。

UNKNOWN/NOT_ASSESSED、native backend未知、有限支持假设和官方同类warning处置的边界保持，不改成零丢失或全capture证明。旧Engineering/Pilot、Raw/ZIP和BLOCKED报告不升级、不覆盖。Protocol Freeze对未来限定数据有效，不把原Pre-Pilot v2.1 DOCX改称已冻结协议。

下一项仅为[Gate13待审交付](gate13_delivery_v0_1.md)。准备交付不是采集、信息增益或Gate13 PASS；本轮未操作服务器、模型、CUDA/Nsight。
