# Gate13 固定版本待审交付与数据保留 0.1

**2026-10-10后续状态：旧e38首槽prepare失败，Gate13 BLOCKED。** 本页为原交付历史，不能执行旧阶段B。[0.1.1重签收尾](gate12_closeout_v0_1_1.md)、[签署发布](gate12_protocol_signed_v0_1_1.json)及科研进度7.126优先；执行/分析99f3bae、前置e38，新唯一签署包先阶段A默认部署/CPU，静态单ZIP审查通过后才显式B。原包/报告/签署保持，下方原预算/测量/归档原则作为历史修订来源；实际路径与命令见忽略的本地交付索引。

2026-10-09；`G13-DELIVERY/0.1`。依据[签署记录](gate12_protocol_signed_v0_1.json)/[Gate12收尾](gate12_closeout_v0_1.md)。**Gate13 NOT_RUN；本轮只本地交付准备。** 机器路径、唯一ZIP/大小/hash和可复制命令存于忽略的本地交付索引，不提交私有配置。

## 执行边界与固定身份

执行/分析checkout **e38fa91850b8f31e17cc0ee264987ef3c1313d7d**；服务器前置为已完成共同w3 Pilot的 **470c5afa6400a77fb79692699cdd8cecc47b314d**，若实际不符立即停止，不reset/覆盖。增量bundle只部署该固定执行版本；签署JSON和有hash的外部控制脚本在checkout之外，保持工作树clean。协议125个源码锁、实际LF/CRLF字节选择和每run真实seal相互区分。交付控制器不复制runner/S/A/B，也不修改e38fa91。

默认PowerShell入口只部署、核实字节与必要Formal封套CPU检查；mask=-1，不初始化CUDA。停等协调窗口核对静态回执。`-CollectReviewedFormal`才启动唯一新批次，明确初始化CUDA/模型并执行Nsight collection/export。该开关须用户在审查后独立执行，不能自动接在部署后。

固定六block/五条件/相邻P0–P1，60模型进程、30profile、共同实际warmup3/repeat1。顺序完全取签署协议；N1两pass保留相同variant包装/marker/层16同步和fresh measured stream，逐值token比较。模型加载/暖机/成功drain/cleanup在三窗口外。输入、模型、GPU、软件、backend、实际身份和所有原有门不削弱。

预计模型/采集链 **200–240min、42.1GB原件，至少90GB空闲**，来自Pilot外推、不是保证。新增公平baseline和完整文件复核还需CPU时间，未用真实Formal实物测量；不能伪称均已计入旧估算。每run原driver上限900s、工具/profile/导出原界限保持；每个纯CPU baseline上限900s、完整批次复核/统计上限7200s，后两者是交付操作界限，**不增加模型预算或改变测量窗口**。超时只停止记录PID并保留后代UNKNOWN，禁止杀无关进程/自动重试；写入者状态不明停止封包与清理。传输/ZIP核验另计，不能以时间估算承诺完成。

OOM、空间不足、身份/协议/输入/token/配置/边界/drain/ownership/必要依赖/terminal/干预/诊断冲突、采集/export/分析/baseline失败全部立即停；保留partial及NOT_RUN槽位，不恢复旧attempt。批次完成也STOP_FOR_REVIEW，不把执行exit0认定信息增益或Gate13 PASS。partial block不拼接补齐；原始有效长值和负差不删除。

## 单ZIP与审查

每阶段只一个封存ZIP：静态回执审查后再执行新批；最终ZIP包含原静态目录逐字节副本、signed release、输入/模型清单、配置/顺序/source seal、60run及30pair、entry异常/exit、真实producer/ledger/token/stage/drain、REP/SQLite/export/诊断、Canonical/projection、A/逐sync B、同窗baseline、完整block索引与统计/图表、partial/NOT_RUN及机器报告。stream/context/correlation/PID/源hash及原值留存。不将Pilot身份引用当Formal样本。

封包前确认活动锁已释放、已记录launchers已退出且无UNKNOWN后代；清单先快照文件列表，**只排除根清单自身，保留嵌套静态清单**。流式核包大小/hash/完整覆盖与CRC，打印ZIP/清单SHA256。超时后写入者不明时不生成假完整ZIP，先交回已有日志说明。原始报告和Raw不改。

## 数据分类与清理门

1. **必须归档**：完整封存ZIP及其hash/清单、签署/源码版本/bundle/实际字节和输入模型内容引用、所有原REP/SQLite、producer/身份/边界/drain/同步/诊断、原始失败/排除/机器报告、已审查A/B/domain/baseline/统计/图表及批准/审查/清理回执。allocation、UNKNOWN/NOT_ASSESSED和限制必须保留。模型本体不打包、不复制，不进入Git。
2. **可重建/重复展开**：完整归档已含的Canonical八类压缩record文件、projection/scope及额外展开副本；可由固定SQLite/执行和分析版本恢复。恢复后需重新核hash/来源，**不能宣称新export必然产生同字节SQLite**。本版不删除REP/SQLite、最终A/B/domain、baseline或统计，优先删除已归档的大型中间record和明确重复展开；无法判断用途保留。
3. **临时**：退出后无唯一内容的pending/cache/额外传输复制，仅列入后续准确清单，不在采集期间删除，也不清全仓/旧现场。此轮不清理任何现有证据。

清理是**批次审查完成＋完整归档核验**后的独立人工动作。用户/协调窗口提供带ZIP hash和review_id的`BATCH_REVIEWED_ARCHIVE_VERIFIED`回执；`gate13_retention.py plan`逐项核档和当前字节后生成准确的path/size/SHA256/archive_member清单。默认不删；`cleanup_gate13_reviewed.ps1`先dry-run，审查后才显式`-DeleteReviewedFiles`，仅逐文件`Remove-Item -LiteralPath`，验证允许根/重解析点/实际hash，无递归目录删除。删除前后持续写不可覆盖的cleanup receipt；全部可从保留ZIP恢复。

**未来批次尚未产生，当前不能捏造准确待删文件名单。**交付已提供生成器与安全命令；回传审查后再批准实际清单。清理后展开目录是瘦副本、原清单仍描述完整归档；复算前必须从ZIP恢复已删中间文件并核验，不能直接将瘦副本交给严格loader。不改旧定位、旧清单或报告。

本地只新增外部编排/归档控制层及其定向CPU验证；旧224项和实验只复核记录。Gate12限定PASS不授新实验结论，Gate13待真实新采数据和公平信息增益审查。
