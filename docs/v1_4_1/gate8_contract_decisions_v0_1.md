# Gate8 实施前合同收敛 v0.1（待裁决，不是新冻结合同）

**后续状态（2026-09-25）：用户已接受D1/D2，并仅授权amendment/schema设计与独立测试预期。下文保留当时裁决依据；“待批准”不再是当前阻塞。正式设计见[boundary amendment](gate8_observation_boundary_amendment_v0_1.md)和[coverage amendment](gate8_coverage_reporting_amendment_v0_1.md)。尚未实现/部署/采集，零丢失证据仍UNKNOWN。**

2026-09-25；Engineering。只读核对当前研究设计v7.1、实验协议v2.1、Measurement Contract v0.2（下称MC）、当前源码及历史Gate7 SQLite。无业务代码修改、无GPU/Nsight执行。Gate7 PASS及限制不变，Gate8 NOT_RUN。

**结论：设备映射、多repeat身份承载、缺失/冲突处理可以直接确定工程设计；不再让用户选择文件组织细节。需批准的只有两项新增约定：D1共同completion锚点的观测表达，D2 coverage窗口/重叠统计细则。dropped=0的肯定证据目前未落实，是技术阻塞，不是可投票豁免的规则。** 下文新字段均为建议schema，不声称已经实现。

## 1. Completion / 时钟：规则确定，观测表达需D1批准

**已冻结：** MC §3–5：整数ns、半开窗口、同一completion语义；request.start在输入驻留和predrain之后、首次forward之前；token-ready在Host可读后；prefill=[r,t0)，decode=[t0,tLast)，full=[r,tLast)。N=1 decode为空；EOS明确排除；cleanup不入窗；Pass0/1输入/控制流/同步一致。Canonical schema.clock_model要求`NSYS_TRACE_RELATIVE_NS`、单source trace、`timestamp_normalization=DISABLED`。不允许直接把perf_counter_ns写进NVTX时间字段，也不能平移/拟合后声称0ns精确。

**推荐工程路径（D1）：同源离散锚点 + 独立可追溯scope projection。**

1. runner共同boundary helper在固定程序点记录：predrain后紧邻forward的`request_start`，以及首次/后续同一Host读取操作完成后、EOS/cleanup前的`token_ready(i)`。不添加CUDA synchronize/event来制造边界。Pass0记录host-clock性能时间，Pass1另发结构化非同步NVTX点；它们是相同语义程序点的两种观测，不承诺数值相同、不互相换算。
2. marker携带完整request键、`boundary_id`、`boundary_kind`、`token_index`（token点）、完成机制；开始点不能借用`kind=sync`。实际kind/附加字段由版本化boundary schema登记，不猜解析旧字符串。Host sidecar存`boundary_id/host_observed_ns/host_clock_id`供parity审计。
3. Canonical保留原NVTX point的`record_id/source_table/source_rowid/start_ns`和trace clock，不伪造“原始NVTX range”。新增有版本的scope projection产物：`request_key/phase/start_boundary_ref/end_boundary_ref/start_ns/end_ns/clock_domain_id/source_sqlite_sha256/projection_version`。r、t0、tLast各只取一次原始point时间，再按MC公式生成三个窗口；相等边界来自同一ref，而不是独立push/pop恰巧相等。
4. S ownership与A窗口发现共同消费此经验证scope；已有Q0 structured range路径仍保留。不得覆盖旧Raw、不修改依赖图/terminal/A分类公式；window projection不是S依赖证据。缺点、重号、乱序、跨pid/request/clock、越界或不闭合均拒绝窗口，不以legacy范围fallback。

**D1真正需批准之处：** 以“Host读取完成后立即发出的trace原生观测点”作为该completion的可观察时间戳，并允许从点派生scope替代只接受原始request/phase range的输入接口。NVTX采样有观测开销，不是Host可读的不可观测物理瞬间，也不等于旧perf_counter采样瞬间；须记录程序次序、marker bracket/overhead诊断，不能声称误差为0。若要求严格复原旧perf_counter的同一物理采样瞬间，现有单trace合同与材料不能证明可行，必须停下研究时钟映射，而不是填一个offset。

备选：经可证明的共同clock/映射承载原Host时间；当前未有依据，且会改变Canonical禁止时间归一化的合同，需要clock amendment及新的观测资格验证。独立NVTX range改标签/加容差不是备选。

推荐贡献：使A的完整request分区真正绑定completion证据，而非漂亮的数值闭合。实现代价主要是boundary schema、Canonical派生scope、S/A共同ownership入口和runner instrumentation；D1须出**observation/boundary amendment及adapter/schema版本**，保持MC §4公式。变更触及ownership输入，须重验受影响Q0（phase-spill/外部ownership/multithread/clock负例），不能自动继承新版本资格；历史Gate6 PASS不撤销，也不能本轮擅自重跑。

**确定性测试：** 用runner helper真实生成payload（假token/假clock/记录marker的sink），再用独立写定的trace时间装入SQLite fixture；经实际converter/projection/S/A消费。验证N=1/N=2、共同ref相等、first/later相同路径、predrain/cleanup在外、host与trace数值完全不同也不混算；缺点/重复/错线程/错request/逆序fail closed。合成测试不证明真实Nsight时间行为，未来新Engineering run仍须实证。

## 2. 多repeat与设备身份：工程方案直接确定，不需研究裁决

**已冻结：** MC §3、Canonical.record_identity和structured_nvtx.common_identity_fields：不得由文件名/时间序重建身份；物理记录键包含source SQLite hash/table/rowid；Pass/Request/Repeat必须贯穿；S/B一行对应一个physical sync。

### 身份承载与字段映射

| Producer产物 | 建议承载字段 | Canonical → S/A/B |
|---|---|---|
| 不变的WMPC manifest | experiment/wmpc/run、data_role、model/input/执行模式、commit/源码hash；不填单个repeat/pass | `source.wmpc_manifest_sha256` + run-level identity |
| 每pass执行manifest/receipt | pass_id、attempt_id、pid、WMPC hash、prompt hash、代码/环境身份、计划request集合、raw hash（采集后receipt） | `source.pass_manifest_sha256`、显式pass与进程；禁止循环hash，可由末端receipt绑定Raw |
| runner request/attempt ledger | 稳定request_id、repeat_id、pass_id、attempt_id、warmup/measured、expected/actual tokens、EOS/exclusion及boundary refs | `identity.requests[]`索引；每条NVTX/API ownership按完整键联结，不用数组位置 |
| structured NVTX point/sync/activity marker | 现有七字段identity；sync的origin/callsite/ordinal；必要的新增attempt/boundary引用 | 保留原marker payload；S保留request/repeat/phase；A按request/phase出窗，B按physical sync出行，manifest保留pass/attempt来源 |

推荐一份per-pass多request Canonical bundle：升级来源identity schema，run/pass为共有字段，repeat/request为集合；校验每条marker在ledger中唯一存在、计划与完成集合一致。**不选“一repeat一次采集”或把共享manifest硬填repeat0**：前者改动实验结构，后者制造冲突。保留全trace，初始化/尾部不成为A窗口；依赖closure中的外部activity不能裁掉以免掩盖bleed。过滤报表与删除Raw是两回事。

`data_role=Engineering`唯一决定数据资格；旧`run_role=PILOT`不是Pilot证据。新run明确登记run_role允许值并在全部载体一致，不能为美化历史而改旧字段。跨pass配对用相同workload/repeat计划键，trace物理记录ID仍隔离；retry用不同attempt，不能合并到同一次完成记录。

### 三种设备身份（另保留Nsight inventory ID）

1. preflight/telemetry：`gpu_index = gpu_index_physical`为nvidia-smi physical ordinal；UUID/PCI是核验对象。mask/order与同进程CUDA probe给出`gpu_index_logical`及其实际UUID/PCI；不能仅从mask字符串假定同卡。
2. adapter读取`TARGET_INFO_CUDA_DEVICE`的`pid/cudaId/uuid/gpuId`：目标PID与pass receipt/structured marker PID一致，`cudaId`与本进程logical设备一致、UUID一致；再用gpuId联结`TARGET_INFO_GPU.id`，核对UUID和busLocation。UUID只做严格格式规范化，PCI按数值domain/bus/device/function规范化；不截断、模糊匹配或按型号认卡。
3. context的`processId/deviceId/contextId`及activity/sync的`deviceId/contextId`须与该CUDA设备映射相符。Canonical `execution_context.selected_device_id`必须来自经证实的**trace activity deviceId**，不是physical ordinal，也不是Nsight inventory gpuId；保留`device_mapping[]`及各源记录ref/hash。S仍使用Canonical device/context scope，不自己查询SQLite。

历史实物验证得到 physical=3、logical/cudaId=0、Nsight inventory gpuId=2、目标context/activity deviceId=0；gpuId=2对应UUID与PCI匹配。这证明数字不可混用，不是新Gate8验收。Nsight官方schema确实区分这些字段，见[Analysis Guide](https://docs.nvidia.com/nsight-systems/AnalysisGuide/index.html#sqlite-schema-reference)。在线文档可能领先本地3.25.0，adapter必须锁定实际schema并验证字段，不据在线新字段假定目标版本支持。

**测试：** 生成两repeat producer记录再进converter，测试乱序不改身份、缺repeat/重复request/错误pass/串attempt阻塞；设备fixture专门设physical/logical/inventory三值不同，覆盖同型号多卡、UUID/PCI冲突、target PID不符、缺表、多映射；不得device_count反推physical、不得缺字段fallback到0。属于identity/provenance schema版本与adapter修复，不改S数学语义；需受影响Canonical/S ownership回归和新版本资格影响审查，不要求用户选字段文件名。

## 3. Coverage：协议已经决定分母；窗口统计细则需D2

**已冻结，修正上一轮过宽的“全部未决”：**

- 研究设计v7.1 §2.3.1及协议v2.1 §3.6：supported count分母是阶段内**全部physical blocking sync**；duration是支持sync duration/全部blocking sync duration。
- **协议§3.6明确 B_valid_coverage = B_valid sync / 支持sync**，不是全部sync；不能擅自统一分母。valid-empty、invalid/ambiguous须分列。
- MC §6、§9–11：由registry判universe；依赖edge/query不算blocking；一个physical sync一条B，重复映射不能重复计数；A用半开窗口交集/区间并集，B不跨sync相加；局部失败保留unattributed和原因。Coverage不是request解释比例或A守恒替代品。

**可直接确定的工程映射：**

- 复用`build_semantic_sync_candidates()`及API-backed/mapped去重规则；全局UID=`source_sqlite_sha256 + sync_id`，不是NVTX数量/函数名/ordinal。UID只在同source内去重；冲突副本报错。
- 当前S的`wait_set_status`最终等于validity，terminal tie也会变AMBIGUOUS；不得从“API类型支持”或原因字符串反推证据充分。推荐保守映射supported=`VALID_NONEMPTY or VALID_EMPTY`，B-valid读取匹配B行`B_VALID`并要求属于supported集合。有效空集合计supported但不计B-valid；invalid/ambiguous不计supported，均留分母和原因。该映射贯彻MC§9的强归属边界；若要把terminal ambiguous但自称W可恢复也算supported，则需新增独立wait-set资格定义及Q0，不在本方案偷加。
- 缺时间/ownership/unclassified导致无法证明分母完整时，`denominator_status=UNKNOWN/INCOMPLETE`、比例null；可列已观察数量但不能冠名完整total。全局drop unknown同样不产生“完整覆盖率”。完整空分母为`NOT_APPLICABLE`且比例null，真实已知计数0允许输出，**未知不是0**。完整分母>0且已证明无supported时，0%才是合法观测值。

**D2推荐细则（需coverage reporting amendment，不改A/B公式）：**

令W为一个合法request/phase，U(W)为与W有正时长交集的去重blocking sync；零时长sync仅在其timestamp属于W的半开区间时计count，duration贡献0。`d(s,W)=max(0,min(s.end,W.end)-max(s.start,W.start))`。

- count=`|supported∩U|/|U|`；B-valid count=`|B_VALID∩U|/|supported∩U|`。
- duration=`sum(d(s,W), supported)/sum(d(s,W), U)`；B-valid duration同样以supported duration为分母，并显式字段命名。
- **这里按不同physical call的裁剪时长加权**，只去掉同一调用的重复记录，不对不同调用union；重叠call仍各计其duration。这是“sync-call duration coverage”，可能total duration>T_window，绝不是request-visible exposure。A依然按union及invalid优先，不受此报告算法影响。
- 跨phase sync在相交phase各有一次membership，但B原行不复制；full_request单独从UID集合重算，不把phase count相加。sync_owner_phase保持S原值，与窗口membership分开。

**真正未定的是duration的聚合运算和跨phase计数口径**，不是universe或B-valid分母。推荐上述调用加权最贴近协议§3.6表述，便于审计“哪些调用/同步时长证据不充分”。备选为window内blocking区间union coverage，并规定重叠有效/无效时的保守优先级；它回答另一个墙钟覆盖问题，不能悄悄复用原字段，需更大报告语义修订。另一备选按owner phase只计一次call会改变“阶段内全部blocking sync”的解释，不推荐。

贡献是可证伪的支持边界/解释限制，不新增科学指标。支持性阈值、A_unattributed阈值仍由后续Pilot决定，不先编造99%或100%阈值。D2只新增report schema/统计规则并补独立oracle fixture；不改变现有W(s)/terminal/A/B，故不撤销旧Q0；若实现扩张supported定义或改S状态，则必须另审查并重验相关Q0。

**测试：** 两条重叠调用、同ID重复、跨phase调用、边界相切/零时长、valid-empty、terminal tie、unknown时间/ownership、未知API及drop unknown。独立手算分母/裁剪/加权比例；验证A五类数值不受coverage计算改变，B不生成additive total。

## 4. Dropped-record：规则不待裁决，证据可得性仍阻塞

**已确定：** 协议§3.6/3.7要求无dropped/NVTX缺失/bleed；MC§9/15要求完整性证据，global损失污染整个受影响窗口。无警告、进程exit0、SQLite integrity、表非空、collected event数量、缓冲已flush均不单独证明zero drops。现有observation regex未命中不等于0；旧Gate7 dropped unknown不继承为Gate8豁免。

**直接确定工程合同：** producer收集器完成回执 → Canonical `observation_evidence`保留每个channel的`status=ZERO_CONFIRMED/NONZERO/UNKNOWN/CONFLICT`、count（未知null）、scope（process/context/channel、完整采集区间）、provider/tool版本、原始artifact hash/record ref、finalized标志 → 全局quality verdict → S/A fail closed。不得把UNKNOWN统一伪装成“已确认丢失”，也不得给UNKNOWN提供science acceptance。

ZERO_CONFIRMED必须有**该实际收集器/该次会话的肯定完成与丢失计数或等价明确完整性声明**，覆盖所有必需CUDA activity及NVTX通道、全部目标scope/缓冲周期，且无相反证据；只证CUDA不能替代NVTX。NVTX另以预期boundary/identity ledger与trace逐项双向匹配验证应用标记完整。非目标进程diagnostic只在进程身份与影响scope可证明不相交时可局部化；不得仅因PID不同就排除collector-wide损失。

本轮官方资料能确认[CUPTI GetNumDroppedRecords](https://docs.nvidia.com/cupti/api/group__CUPTI__ACTIVITY__API.html)有丢失计数且读取会重置；这**不证明Nsight 2026.2.1把完整计数导出到当前SQLite，也不覆盖NVTX**。不建议向Nsight进程额外注入一个CUPTI计数reader：读数可能不属于其收集生命周期，最后一次0也不能证明此前无丢失。当前未定位到可用的Nsight全会话肯定零证据来源。

推荐下一步仅做工具版本文档/已有完整collector原始日志与schema核验，给出具体source+scope证明；找不到就继续UNKNOWN并阻塞科学验收。**这是技术调查，不需要用户选择“相信没有警告”。** 备选若必须换收集方式、增加并行collector或把unknown降级放行，属于observation stack/acceptance范围扩张，必须另授权和相关Q0资格重验；不列为本次默认路径。

**测试：** 显式0/正数/缺失/截断/未finalize/错pass或hash/只覆盖部分context/读数重置周期缺口/相反diagnostic/仅NVTX ledger匹配；只接受完整肯定证据，unknown保留null，受影响窗口正确阻塞。

## 裁决与下一动作

只请求批准 **D1：trace原生共同completion锚点与可追溯scope projection**、**D2：逐窗口physical-call裁剪加权coverage及跨phasemembership**。均先写amendment/schema与独立测试预期，不直接改冻结合同正文。设备映射与多repeat承载按§2实施设计，无需另选方案；零丢失来源继续由主窗口技术核验，不让用户代替证据作决定。

批准方案不等于授权服务器实验；实现、资格验证及新采集仍按分阶段授权推进。本轮旧evidence不修改、旧诊断不升级、无Formal数据资格。
