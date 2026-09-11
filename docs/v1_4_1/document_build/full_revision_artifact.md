# ExposedPath 完整文档修订版式与谱系规范

## 修订目标

以两份既有 Word 母版为结构与版式基础，逐章吸收 v1.4.1 的研究语义、证据链和阶段路线，生成两份可直接阅读与交付的完整文档。输出不是摘要，也不另造第三份解释性正文。

## 输入谱系

| 角色 | 文件 | SHA256 |
| --- | --- | --- |
| 研究设计母版 | `ExposedPath_研究设计与论文证据框架_v6.0_语义冻结增补_蓝色标注版.docx` | `0EE058EE1DD2D1FB69EC59D230DBD6B6F03BAEDC319D9C246AEE3ED229B530F1` |
| 实验协议母版 | `ExposedPath_实验与分析协议冻结版_v2.0_语义冻结增补_蓝色标注版.docx` | `1AD97E338F03C951E46BD81B15A5633D46A3B6E6490FEC4B2DFA8840028C0685` |
| 语义修订依据 | `ExposedPath_CCF-A顶刊研究定位与机制归因补充说明_v1.4.1_执行路线与当前阶段补充_黄色标注版.docx` | `2C61AC496CEDBC0BA4D146F795EE0FC99D4CFEEEBA915A533396DBF7553855AF` |

## 母版结构基线

### 研究设计母版

- 296 个正文段落、36 张表、6 个内嵌图片、1 个 A4 纵向节。
- 保留原有章节、参考文献、附录、图片、页眉页脚、编号与主题。
- 允许在相关章节标题后插入少量 v1.4.1 归并说明；不删除原有章节。

### 实验协议母版

- 142 个正文段落、39 张表、3 个节，依次为纵向、横向、纵向。
- 保留原有实验组、统计、停止规则、附录、页眉页脚和横向大表布局。
- 只把尚未通过 Pilot 的正式口吻改为“候选/Pre-Pilot”，不伪造已冻结状态。

## 版式规则

- 直接复制母版后做定点修改，最大限度保留原主题、样式、图片、节设置和关系文件。
- 标题层级沿用母版；新增解释正文使用 `Normal`，关键决定和风险分别使用母版 `Decision`、`Warning` 样式。
- 修订完成后清除用于旧版增补辨识的蓝色/黄色字符标记；正式标题与正文使用黑色。
- Word 打开时更新目录和域；不手工伪造目录页码。

## 内容规则

- 研究设计输出为当前完整主体 v7.1，第一章完整归并 v1.4.1 的背景、立意和研究价值论证，可取代“主体 + 补充说明”的日常阅读组合。
- 实验协议输出为 v2.1 Pre-Pilot 执行依据，不重复研究背景；只有 Pilot 与全部冻结门通过后才能另行形成 Protocol Freeze 版本。
- 固定 `Raw -> S -> {A, B} -> D / Exposure Signature`，并明确 Activity Cost 与 Request-Visible Exposure 不同。
- S 必须依据 completion semantics、提交关系与 ownership 恢复完整 `W(s)`；已在同步前完成的语义前驱仍属于 `W(s)`，时间重叠不能生成依赖。
- terminal 必须有唯一 completion evidence；证据不足进入 ambiguous/invalid，并 fail closed。
- A 是 request/phase 互斥墙钟 accounting；B 是 per-sync provenance，不跨同步求和；D 只导航；Exposure Signature 只汇总冻结后的 A/B。
- 证据链固定为 `Correctness -> Information Gain -> Decision Gain`，对应 Q0、N1/G1、G2。
- 核心边界为单 GPU、请求内部、纯模型推理的 Host-device exposure；自然逐 Token 的模型侧 Token-ready 同步在范围内，后续文本处理、网络和前端不在范围内。
- 历史 trace 和旧结果只能作为 Prototype/Engineering 回归资料。

## 输出与验收

- `docs/current/ExposedPath_研究设计.docx`
- `docs/current/ExposedPath_实验协议.docx`
- 自动检查：输入哈希未变、DOCX ZIP 完整、表/节/图片数量与图片哈希保持、关键语义齐全、过时硬承诺不存在、无 TODO/TBD、无修订批注残留。
- 视觉检查：渲染全部页面，逐页检查溢出、截断、表格错位、横竖节异常和不可读字符。
