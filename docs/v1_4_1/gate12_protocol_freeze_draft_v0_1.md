# Gate12 限定路线A协议冻结草案 0.1

2026-10-02；`G12-ROUTEA-FREEZE-DRAFT/0.1`；Material Passport：ExposedPath / ARS experiment-agent plan；状态 **DRAFT / NOT_FROZEN / NOT_EXECUTABLE**。科学依据与待裁决见[适用性审查0.1](gate12_scientific_readiness_review_v0_1.md)。Gate12 NOT_RUN；本页不是预算批准、采集任务或Formal资格。研究设计v7.1和Pre-Pilot v2.1原件保留，不把草案签字推定为已完成。

## 1. 拟冻结对象与允许结论

主问题只有G1两输入端点的request/phase解释信息，以及N1固定同步的局部机制信息。正确拆分、机制事实、信息增益、性能收益分开裁决；允许无增益/不支持/不确定，不以A图、零unattributed、守恒或加速必现为成功。

**P0**：未profile的同合同执行、host-readable三个completion窗口，报告性能/对照，仍有共同计时记录。**P1**：被观测执行、trace原生锚点/投影A与合格N1单sync B；host窗口仅供与P0配对。不能从A扣P1−P0，不授P1→P0精确组成迁移。配对不同进程、不是同时执行，delta含扰动和波动。

G1自然流，只获窗口投影A；N1所有variant同显式非默认NON_BLOCKING专用流及输入/执行配置，仅预定wrapper/marker/sync不同。保留无未记录incoming依赖等**支持假设**，逐request检查可见事实；不是证明所有隐藏关系不存在。D/Signature、自然默认流完整物理B、G2/Decision Gain、compile/graph、多平台、多模型、OOM边界、通用性能预测全部不启用。

## 2. 固定候选与身份锁

| 条件 | 输入/输出/batch | 模式与唯一作用 |
|---|---|---|
| G32 | 32/2/1 | 自然G1参考端点 |
| G512 | 512/2/1 | 相同生成规则的长输入端点，非输入上限 |
| N0 | 32/2/1 | N1 V0：同专用流，无marker干预包装 |
| Nm | 32/2/1 | N1 Vmarker：每decode的第16层后一次预定wrapper/marker，不同步 |
| N16 | 32/2/1 | N1 Vsync展示名V16：同位置/marker，增加一次实际current-stream sync |

Qwen2.5-1.5B-Instruct，既定模型内容、batch1/fp16/eager、configured SDPA、cache、greedy、主要请求线程；实际native attention backend UNKNOWN，不主张特定实现。32-token固定input文件SHA256 `4dffd0ddcbd3185c656ae4a27efaf5aab302febba6ead5df4d37d903a2091920`；512-token既有循环构造input文件SHA256 `36c507c56d1c851bab0238c30dfd7645a5ea7eef646310c01988ae2aaffbdd0a`。冻结使用**相同已审查input字节和顺序**，不是重新tokenize或从文本选prompt；保留input_ids内容digest，文件digest与token序列digest分栏，不互相冒充。

模型inventory SHA256 `72465c906baeb0cfa4fd94d21ef6c69c1cd8046bb68c61a94c02a1580d2541f9`，23文件分10实际模型输入与13cache辅助项；revision UNKNOWN。revision未知不填缓存名，实际内容锁与执行前验证必须成立，不换模型。输出长度实际2、非early EOS；逐值核对同pair、同输入各条件/各block（既有32输入参考[[463],[2529]]、512输入[[29184],[6556]]），不在计时内增加token读取/sync。

候选平台为已资格Windows/RTX4090固定栈：physical3/logical0、`CUDA_DEVICE_ORDER=PCI_BUS_ID`和既定mask3，UUID/PCI及trace context/stream按既有adapter证明映射，不按编号等同。driver555.99、CUDA12.4、Python3.11.16、torch2.6.0+cu124、transformers5.17.0、Nsight2026.2.1.210-262137639646v0、已有x64 MSVC/CUDA环境。共享平台、动态clock及未控制Host竞争按实记录，不伪称独占或因果隔离；不为本草案另引CPU采样/常驻监控。

采集范围沿既定cuda,nvtx/process-tree，sample=none、cpuctxsw=none、cuda-memory-usage=false、isr=false；REP验证后单独export SQLite，不改collector。工具/环境/source均须固定hash，绝对路径只在本地配置；旧证据路径不迁移。

## 3. warmup、边界、运行预算与完整顺序

每进程独立加载模型，**实际成功warmup3、measured repeat1**。模型加载、每次暖机、窗前成功drain及cleanup在request之外。N1三次held暖机流保留，measured使用fresh专用流，不能因暖机policy改变而热复用measured流；P0也实际保持variant包装/marker/sync。未观测暖机token/EOS保持未知。

request=[start,last-host-readable-ready)，prefill=[start,first-ready)，decode=[first-ready,last-ready)；P1原始marker/record/clock与scope projection可追溯，marker延迟单列不补偿；end≥start、signed-int64 timestamp及非负duration/范围检查沿原schema。输出2只有一个decode step，不能推广长decode稳定性。

**建议六完整block，共60新模型进程/30profile，全部在冻结后新采，Pilot不占Formal样本。**前三block沿Pilot顺序，后三反向对应；相邻P0/P1同pair、独立run/PID。下表只锁顺序设计，不是可运行任务。

| block | 条件顺序 | 各位置的pass先后 |
|---|---|---|
| 1 | G32,N0,Nm,N16,G512 | 01,10,01,10,01 |
| 2 | G512,Nm,N16,N0,G32 | 10,01,10,01,10 |
| 3 | G32,N16,N0,Nm,G512 | 01,10,01,10,01 |
| 4 | G512,N16,Nm,N0,G32 | 10,01,10,01,10 |
| 5 | G32,N0,N16,Nm,G512 | 01,10,01,10,01 |
| 6 | G512,Nm,N0,N16,G32 | 10,01,10,01,10 |

01=Pass0后Pass1；10相反。每条件各3次01/10；各条件位置平均为3、每对条件先后对称。**不是所有位置等频的Latin-square、不是随机化，不保证独立或无漂移。**顺序先锁，不依据正式结果改变。block是联合比较/重采样单位；每条件6个request，不是60个独立样本、token/kernel/sync数也不是n。

估算200–240min、约42.1GB原件、预留90GB含审查；基于实际共同w3 driver/存储，非保证，传输另计。这是拟议预算，需确认后另行交付；没有自动续批、替补或加采。当前不申请新Pilot来保证稳定/精度。

## 4. 主要与次要比较、baseline、统计与图表

### 主要比较（均不可因不利结果删除）

1. **G1**：同block G512−G32；P0 Request为主性能描述，Prefill/单步Decode并报；P1三窗A与同窗常规activity解释分别对照。主要信息命题按审查§1：activity成本是否足以唯一解释必要等待/互斥预算及Host补集；无额外解释即“不显示增益”，不得改成输入轴趋势成功。
2. **N1**：同block同pass的Nm−N0及N16−Nm均报告Request、Prefill、Decode；P1对照A分量及对应callsite/origin的合格单sync B。Vmarker是必要对照，不机械扣成纯marker成本。关键干预sync、两个token-ready及内部Raw来源sync分别留完整W/terminal/有效性；未对应的sync不虚构零值配对，完整W的已完成前缀不删。
3. **观测扰动**：每condition/block/phase的host P1−P0与相对差、两项N1的profile×variant差中差；保留signed/负值，与P1机制报告并列，不校正A、不称纯Nsight成本。

常规baseline固定为同一P1目标窗的API/kernel/MemOp/sync count、sum与union、GPU active ratio、launch-to-start以及mapping coverage/status，附流/context/correlation/调用序标准timeline。aggregate与timeline两层都展示；分类registry与输入范围对双方一致。launch-to-start按协议§6.1，唯一correlation/context/stream合法才报告，STARTED_BEFORE_API_RETURN不截零；未纳入/ambiguous保留原因。GPU activity跨窗口只裁其交集；不能把不必要但重叠的活动自动说成dependency。

baseline具体口径不得偷换：raw API全量包含同步，另列已识别sync与非sync的区间union；runtime/driver嵌套按原record身份分别报告count/sum，墙钟union去重，不把两层sum称互斥成本。A的CUDA API排除被优先拆分的sync，必须显示这种定义差异，不能声称较小A API是原API成本减少。GPU active ratio是目标owned activity裁剪union/T，缺ownership不能当0。launch统计的phase成员按原launch API起点落入半开phase确定，保留跨界完整配对和状态；区间成本裁剪与launch-to-start的未裁剪时差分栏，不混成一量。

次要：API submit/non-submit及opaque调用逐类成本、A占比、阶段每token视角、warmup stage原值、marker lag/各clock窗口诊断、allocation实际差异。它们用于解释限制，不升级硬件因果或新指标。Decode分母固定为实际output−1=1；Prefill输入32或512。B只按相同语义位置/origin逐sync比较，聚类保留所有sync，不跨sync相加；不存在的V0/Vmarker干预B为“不适用”，不是0。

### 统计方法（拟冻结，不承诺功效）

- 原始整数ns保留；ms只显示转换。每个预定比较先在完整block内求差，再跨block报告全部原值、算术mean、median、min/max、样本SD与95%percentile whole-block bootstrap；所有条件/pass/phase及对应B记录一同重采样，不能各自独立抽样。固定seed=20261001、10000次，线性插值分位数`i=p*(m−1)`；这是有限重复的不确定性描述，非覆盖率/平稳性保证。
- 图表/主要表展示逐block配对连线、实际执行顺序、P0性能与P1三窗A分栏、A绝对值/占比（含residual/unattributed及opaque注释）、N1对应单sync W/terminal provenance。baseline同窗并列；不把两输入点拟合为响应曲线或挑代表trace：必要Raw复核固定首尾镜像block1/4及所有被用于机制claim的record来源。
- 同时报告逐一留出block的均值变化和前/后三block原值，检查顺序/漂移敏感性；这不是删异常、替代主估计或事后选择最有利pass。若不平稳迹象明显，区间限于该运行序列，不作平台总体精度claim。无需为了形式运行小n正态检验或增加复杂混合模型。
- 不做显著性选点/可选停止；本版不以p值、CI离零或10/5ms决定信息增益。所有指定比较展示区间但不作多重检验“显著发现”名单；n6/小样本bootstrap不保证覆盖率。Request/Prefill 10ms、Decode5ms仅报告原候选是否得到支持，**未获保证、不设效应/等价带、质量门或任意放宽后的替代目标**。CI跨0不等于无效应或等价。
- 支持某方向/量级claim必须有该量自身的不确定性及留出/顺序一致性，不以P0较小SD推定A/B精度；局部证据缺口的保守区间若足以反转解释，就不给精确分量claim。单次合法W/terminal可支持观测实例机制事实，但不据小SD宣称统计规律或亚毫秒P0影响。

### 预定结论口径（不另造效应阈值）

信息判定逐问题而非给方法总分：对预定解释命题，先要求有效源记录及独立必要集合/区间核对；再展示baseline能直接给出的答案。只有后者不能唯一支持该归属而完成语义证据能解决时，标为**该观测实例的有限新增解释**；baseline已解决标为**该实例未显示增益**，两者证据均不足标为**不确定**。这不等于只凭“baseline没有名为A的列”判断不够。所有block实例的三种判断与具体依据全量报告，不能从失败或null中只挑成功例。

重复方向只使用字面判据：六个有效完整block的预定差同号、全部留一均值同号、前/后三块没有方向反转且该命题的质量/局部缺口保守范围不跨反方向时，才可称“本六块观察方向一致”；否则称混合/不确定，零值不强分方向。**即使成立也不称统计稳定、群体效应或等价**。mean与pointwise 95%描述区间仍全部展示，不按是否离零挑claim。跨block若解释命题仅在部分成立，只报告实例/条件性范围，不称在整个自然输入域或所有执行中不可替代。固定预算无论上述结果均结束，不能以不确定性代替缺失的准入证据。

## 5. 质量、排除、失败与结果判定

沿已批准目标request及必要依赖范围的质量门；不新增全capture认证。身份/代码clean/输入/配置/设备/实际token、PID实例、三个completion源/clock、成功drain、相关提交/sync映射、流生命周期/ownership/必要集合/terminal及整数互斥守恒都必需。sync优先于API、嵌套/union去重；守恒不是语义正确性的替代。

- N1 actual0/1 marker及层16/ordinal/sync必须匹配；缺失/多次/错stream、未知相关incoming依赖拒绝。预定干预与token-ready需结构身份；内部RAW_PHYSICAL必须满足其版本条件，源码callsite未知不伪造。cudaMalloc只在已批准窄条件下计opaque API成本，不拆内部等待、不构造W/B、不删除先行活动。
- G1所有blocking调用和必要后缀/边都检查；两模式**必要集合/投影来源**一致，不只A数字相同或总和闭合。物理B未获资格，不能标成空B有效或coverage100%。
- 既有官方四类消息只按`G8-WARNING-EVIDENCE/0.1`精确适用条件处置，原warning保留；新类型、目标冲突或影响范围未知拒绝。dropped=UNKNOWN、measurement_validity=NOT_ASSESSED保持，不当零丢失或全会话有效性。
- 仅可独立界定局部影响的缺口保留unattributed/原因和有证据分量，不填Host/residual；无法界定的缺口拒绝受影响窗口，不能定位phase则三窗全拒绝。required单sync B缺W/terminal/来源或invalid时禁止对应机制claim。coverage为physical-call裁剪证据诊断，不是request可解释比例；不设回溯零unknown/百分比放行门。
- 输出不符、early EOS、OOM、身份/语义硬失败、超时或磁盘不足立即停止固定批次，保留失败/partial/未执行，**不retry/resume/替补**。沿已有tool120s/collection300s/driver900s，不为噪声延长。疑似写入者未退出先停封包，不杀无关进程。
- 有效长值、负差、波动大/方向不符/CI跨0不是排除理由。若批次硬停，已完成run保留实例描述，但不拿不完整block拼成成功六block或从不同block凑对；缺完整配对不补值。完整固定预算结束即停。

结果分开存：observed事实、派生A/B与validity、范围/质量裁决、研究claim。单次归属成立但baseline无增益：报告方法适用与本设计不支持增益；合法结果但差值不精确：不确定；源冲突：拒绝，不以“可能不确定”包装无资格结果。Gate13不会因60/60执行或A守恒而通过信息增益；Formal角色也不是方法有效性的证书。

## 6. 版本、历史兼容与Freeze前的真实缺口

拟适用**未来新采**、用户确认并签字后的限定Formal；旧Engineering/Pilot及BLOCKED、UNKNOWN/NOT_ASSESSED/false资格字段不回写。旧schema读取原样保留。明确覆盖Pre-Pilot原统一5/10%开销、dropped=0/自动重跑、广域矩阵与全面新版资格要求：本版取消自然P0精确迁移，采用目标scope/有限claim/硬失败停；不是证明原标准已满足。该覆盖和原研究目标损失需集中确认，不能在Formal结果后改政策。

当前可复用候选：MC0.2、Canonical0.2、D1/scope0.1、S0.4、A/B0.6、API registry0.2、N1 adapter0.3与RAW_PHYSICAL/opaque正式引用；G1沿已验证signed投影路径（其A版本不得随N1强行混成同版本）。正式受支持profile发布/内容锁不等于所有旧v0.x功能授全面v1.0资格。既有测试/真实qualification逐变更映射即可，不机械完整Q0重跑。

新角色封套只能记录“允许进入本冻结限定分析”及逐窗证据/claim裁决；它不将源字段UNKNOWN/NOT_ASSESSED改成全局有效。旧Pilot的formal_eligible=false不改，新采Formal是否可用由新封套与已签字的有限资格/逐request硬门共同决定，不能靠把这个布尔值改成true取得资格。

**冻结必需项及历史缺口（2026-10-09：第2/3项本地实现已验证，见§7；第1/4项仍待确认/绑定签署，不能Gate12 PASS）：**

1. 用户集中确认本草案的有限claim、Formal阶段适用及六block固定预算；不承诺10/5ms或P1→P0组成迁移。
2. 新Formal封套producer→receipt/ledger/NVTX→Canonical→消费者/报告已在本地实际文件入口完成。224项相关CPU回归包含仅改role/旧数据升级、错协议/hash/run/pass、配置/token等拒绝；未签署仍不能接受Formal结果。旧Engineering/Pilot读取保留，不复制runner或改变测量同步。
3. 同窗baseline及成块配对统计/图表已完成独立预期与文件链检查，源码hash绑定如下；CPU合成事实不授目标机或全面Q0资格。signed差、错scope/mapping、union嵌套、不完整block及固定失败处理保留。
4. 执行/分析版本已绑定e38fa91850b8f31e17cc0ee264987ef3c1313d7d，schema/registry/profile及限定资格来源见候选；签署仍未完成。旧审查基线05cfc9e和Pilot执行470c5afa均不充作Formal执行commit。候选/收尾文档提交另行，不包含自身hash。

这些是本地封套/复算/确认缺口，不提出新平台实验。若只改角色/封套而边界/流/插桩/S/A/B无变化，定向CPU链+旧资格可复用；若实际改变提交/同步/依赖/clock，则仅相应资格增量需审查，不能自动继承或静默扩域。

冻结后实质修改measurement、runner/插桩/流政策、分类、分析、输入选择、排除/统计或claim判据：建立新协议版本，明确受影响Formal数据失效/分开数据集；不能看结果重选规则或只对有利trace重算。仅consumer修复也需版本化统一评估所有受影响输入，不把错误结果默认为有效。历史Raw/原报告不改。

**历史停点（2026-10-02）：**两份草案可审阅，Gate12仍NOT_RUN；当时仅有文档/本地算术。用户随后批准冻结前本地实现，当前接线与待签署边界见§7，不把该实现批准解释为协议签署或预算批准。

## 7. 冻结前实现封套与审阅入口（2026-10-09）

本节是已批准草案的工程实现说明，不变更§1～5测量与比较语义。候选协议版本`G12-ROUTEA/0.1`、封套`G12-FORMAL-ENVELOPE/0.1`；仍为**待签署、不可接受Formal数据、Gate12 NOT_RUN**。先提交实现取得实际commit，再由后续绑定记录引用该commit的Git内容hash；绑定文档commit不是执行commit，不将候选记录纳入其自身hash。

### 签署与跨文件链

`formal_protocol.py`只验证外部的人类批准回执，不签署协议，也不能证明回执的作者身份。真实签署必须另行保存用户对**完整候选内容hash、有限claim与预算**的批准；不能由脚本填写`SIGNED`代替。候选hash采用UTF-8、ASCII JSON转义、键排序、紧凑分隔符及末尾LF的规范化JSON编码；原文件SHA256独立保留，不冒充该内容hash。批准时间为UTC，run预声明必须晚于批准，不收旧Engineering/Pilot引用。

协议对象闭合绑定执行/分析commit、源码/合同hash、两份输入hash、模型inventory、设备及软件栈、五条件、六block、warmup3与支持域。manifest承载完整协议、批准及slot；producer/pass ledger承载相同binding；request身份及结构NVTX承载`protocol_version/protocol_sha256/approval_sha256`。sealed preflight与target claim贯通该引用并继续保留当前真实字节校验、输入/Git/设备/解释器门。receipt→Canonical→scope→domain→报告核对引用、Raw/hash与actual plan/token；分析器另核实际analysis commit与clean/source内容。新schema是显式元数据扩展，不修改旧Engineering/Pilot schema读取和S/A/B公式。

源码兼容证明只接受预先绑定的Git内容精确字节，或**明确记录**的LF/CRLF表示等价；保留实际运行文件SHA256/长度，不能用任意当前hash更新期望，运行时seal仍严格核实际字节。不同执行/分析commit必须分别锁定；不能用收尾文档HEAD代替执行身份。未签署、错协议/hash/role、旧role升级、配置/设备/输入/token冲突、partial或错pair均拒绝。

### 公平baseline文件入口

`exposedpath_v141.activity_baseline.write_baseline`消费已准入的domain、同一input receipt、Canonical与projection及原SQLite；新独立目录保存结果，`load_baseline`复核来源与数值。使用同一目标PID/主要TID、request/phase、trace clock、实际ownership及API registry0.2；从同一Raw只读补充可用driver层，不把它接入S/A/B推导。driver表/字段未采集时为UNKNOWN，不能与观察到空表的零值等同。

按相交的physical record计count，sum使用逐record裁剪时长，union按层去重；runtime/driver嵌套分别列sum并列联合union。同步API、已分类非同步API及未分类record分别保留；raw API包含同步，而A CUDA API排除优先拆分的同步，该差异随结果说明。GPU active ratio为已知owned activity裁剪union/窗口，不是必要等待。launch成员按原API起点落入半开phase；合法correlation/context/stream映射后报告原始未裁剪launch-to-start及signed post-return差，嵌套/歧义/missing/ownership unknown不填零。组合API统计只覆盖实际可读表，不能声称完整CUDA SDK或collector过滤之外的记录已观测。

### 配对、统计与图表文件入口

`paired_statistics.read_formal_batch`只读取完整60run文件索引及实际回执，不接受索引提供的测量数值。六block、五条件、相邻pass、唯一run/pair/slot、固定顺序、共同协议/输入/环境/loaded配置及逐值token均检查；P1另须合格domain及同窗baseline，P0无P1产物。缺失/错位/跨批/不完整block不能拼接或补值。

`write_formal_report`生成全原值CSV、P0/P1逐block配对图、独立P1三窗A图、逐sync B来源文件及机器统计。预定G1两端点、N1两必要对照、profile差及交互全部保留；signed差、whole-block联合重采样、固定seed/10000次、线性分位、留一及前后三block敏感性沿§4。B记录随整个block保留，**不跨sync求和**；具体W/terminal与同语义单sync解释由审阅者逐record核对，不因数值表生成就宣告信息增益。通用未准入原值描述入口始终标记`DESCRIPTIVE_NOT_QUALIFICATION`，不是Formal准入捷径。

这些函数没有默认采集任务或Formal批次launcher；实际采集入口须显式选择已签署协议，当前没有签署文件、部署包、执行脚本或服务器预算。所有mock批准/设备事实/完整性条件仅用于CPU接口测试，不授目标机或新版本全面Q0资格。最终集中待确认仍是：有限P0性能/P1机制与公平负结果范围、限定资格适用、六block固定预算及对应候选hash。签署和未来执行授权分开处理。

### 最终本地验证

恢复后的实际九文件命令及temp ACL初次失败记录见[进度7.120](research_progress.md)：224 passed，0 failed，0 skipped，336.25s。覆盖旧Pilot、N1及token-ready回归、未签署/旧数据升级/错身份配置、baseline同窗/嵌套/缺mapping、signed配对/完整block及60run CPU替身文件链；compileall与diff-check通过。不是60次模型、目标机CUDA、真实Nsight或正式实验。独立手算预期与文件hash复核不授全面新Q0资格。

### 未签署候选身份及集中确认

[绑定候选0.1](gate12_freeze_candidate_v0_1.json)采用`exposedpath-freeze-candidate-record/0.1.0`，执行/分析均为**e38fa91850b8f31e17cc0ee264987ef3c1313d7d**。125个Git源码/合同/资格hash取该提交，包含本草案和科学审查在实现提交中的快照；当前文档仅补充绑定说明，不以文档HEAD替换其源码或hash。候选自身不在artifact集合，实际运行字节另seal。

协议规范化内容SHA256：`389a28a17bec830e4f32bea72c259dce15ba279ce69fc20caebfdca88a1326e2`；候选文件SHA256：`cdd6764a2f37bf6089b1c916685a7040571fb221e58a95ec1ba1bb8765cd234e`。approval=null/PENDING_USER_SIGNATURE；没有签署回执、执行脚本或服务器预算授权。绑定设备/模型/input/software来自已有Pilot小manifest的复核引用，不证明服务器此刻未变、不升级Pilot结果。schema/registry版本及限定资格来源完整列于候选；hash锁不授列出源码中其他功能资格。

集中确认项：是否接受本草案限定P0性能/P1观测机制、公平baseline及负结果判据和窄资格Formal适用，并批准五条件w3/repeat1、六完整block的固定预算与上述完整候选签署？估计60进程/30profile、200～240min、42.1GB原件/90GB空间，不保证10/5ms。批准者/批准原文与完整hash须独立封存；签署和未来服务器执行授权分开，当前仍Gate12 NOT_RUN。
