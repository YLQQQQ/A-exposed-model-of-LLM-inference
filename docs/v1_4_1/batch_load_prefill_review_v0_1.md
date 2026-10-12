# Batch-load Prefill局部证据审查 0.1

2026-10-12；前两节7.139/7.140为历史只读审查/设计，后附7.141为用户已批准的本地实现及待审交付。历史执行身份仍为`2af14b11dd990d159ff0b3204d26a1527244079c`；历史局部计算代码为`dc78fc881157a4078c4a6c9f8f34c724140f4660`，当时runner/S/A/Engineering scope/G9 domain相对执行版本零diff。7.141不修改这些旧Raw/报告，不将新实现追认到旧attempt。

## 裁决：前缀闭合与局部准入分开判断

**B4 Prefill在预声明支持域下证据闭合，可依据现行合同单独作局部Engineering投影A审查；B4 Request/Decode及原attempt继续BLOCKED。** 本结论不是将旧request报告改为通过，也不授batch4科学资格、自然默认流物理B、Formal、D或Signature。

[G9分域资格合同0.1 §2](gate9_domain_qualification_contract_v0_1.md)规定逐窗口核对身份、前缀、必要成员/依赖与质量；失败传播条款明确“拒绝受影响窗口；不能证明局限到phase则拒绝整个request三窗”。[本批合同](batch_load_engineering_plan_v0_1.md)复用该自然G1投影A规则。本次不要求把缺映射调用当零提交，也不把其区间改为局部unattributed：它们的效果仍未知，整个Decode及包含它的Request被拒绝；只保留此前已完成的Prefill。

当前`process_domain`/`_request`实现仍按full_request统一判定三窗，没有新增partial-phase发布/读取接口。本次独立审查只选择原投影中已有的prefill窗口，使用原`calculate_a_windows`计算；保留完整Canonical记录，不将Prefill伪装为缩短的request，不制作可被旧domain reader当作成功run的产物。该实现限制不反推合同要求所有phase无条件联坐。本报告和局部小汇总不是新准入schema/资格证书，不得拼接成B4完整三窗。

## 来源及前缀核对

复用[7.136完整归档/身份审查](batch_load_failure_review_v0_1.md)及[7.137 Raw→Canonical核对](batch_load_memset_effect_review_v0_1.md)，不重复全包扫描或旧参数追索。原ZIP SHA256 `b290a96f85d68c54adf8f9be0705fce2f188d4dffc8e98b44f7b6d5a909b8494`；清单SHA256 `157ff32769bb569ef1982ba3daa2846dbe06979a10e8330a9720a648f2ea4998`。

B4 SQLite SHA256 `569b690715495748f1af6706d2ea93a5b0a5a94a0fc29f104e1c9cd542b2a7be`，Canonical manifest `a1770cf5e4e1747c701d1280b2d0e8a5ad81fffed472045b820c0258b18cdaac`，scope `2c001f29ad171177c54f88466b05e2907730f1350b257bd6120320b0616ba358`，input receipt `81ce764bf7776a09d63983957eec8906b97c1edc338fa39692b24faab523b06b`。本次实际重读source-bound execution、Canonical/sidecars与projection，按原host ledger重新推导锚点并比较；所消费input-receipt文件集合在计算前后哈希不变。模型本体未本地复算。

- 目标PID65008/TID59500，global PID `282565629968384`、global TID `282565630027884`；context1、trace device0、NULL FIFO stream7。physical GPU3→logical0→trace device0沿用已核验UUID/PCI adapter，不按编号相等推断。clock保持`NSYS_TRACE_RELATIVE_NS`；三点仍为原NVTX row1/2/3，原完整request和其身份未改。
- 窗前drain唯一映射：runtime36760/correlation172084成功`cudaDeviceSynchronize_v3020`，API `23540916025..23540928074 ns`；physical sync352结束`23540927573 ns`。10,491条已观察前缀活动最晚完成`23535741783 ns`，均在drain前完成；无观测到的迟发/跨边界提交。
- 原Prefill窗口`[23541802679,23694390270)`，152,587,591ns。1,821条后缀活动为1,790 kernel、2 memcpy、29 memset，均有唯一实际提交映射、成功API、同进程实例/主线程/context/clock及VALID ownership；无相关其他stream、event、graph或跨边界API。此阶段4,810条API全部核对：1,790 launch、2 copy、29 memset、2 stream sync、2,986 function查询、1 capture查询，没有未支持/缺映射提交。
- 原stage范围包含drain至首token完成，setup在drain前；实际before/after native观察与声明一致。`observe_token_ready_boundary`先执行`.cpu().reshape(-1).tolist()`，取得四个Host token值，再记录completion point；不是NVTX本身证明GPU完成，也不是网络发送。B4首token向量为四个29184，P0/P1逐值一致。
- 原84条缺效果调用均同主线程/同trace clock；最早runtime38606/correlation201238始于`23699269762 ns`，比首ready晚4,879,492ns；末条runtime39985/correlation226267始于`23783505645 ns`。这是实际时间/身份比较，不是依赖Decode标签作排除。此前必要集合中没有这些调用或后续活动，未发现可见incoming/event/跨流依赖穿越已完成边界。未记录incoming依赖不存在仍是原预声明支持假设，非新证明；UNKNOWN不改为零。
- Prefill实际semantic-sync universe恰为physical353/354。分别按LEGACY/PER_THREAD重建原后缀：必要成员数8/1,821，closure COMPLETE、无reason，frontier唯一为MEMCPY346/347；成员及依赖边完全相同、均在同步返回前完成。旧whole-request诊断图含后续Decode边，不能直接说它与局部图全等；取其Prefill诱导子图后1,820条FIFO边与本次完全一致。未裁改完整物理S/W/B。
- 原同类官方warning按已有规则处置，本次未新增豁免。全局clock/identity质量检查通过，`dropped_records_status=UNKNOWN`、`measurement_validity=NOT_ASSESSED`保持，不称绝对完整。

## 既有窗口上的局部A结果

仅P1观测执行；单位ms，括号为各自原trace窗口百分比。不是P0时延组成，也不是统计结论。两模式的A逐字段一致；顶层/API子类守恒、overlap/uncovered/out-of-window均0。B1本次局部计算与已接受observation Prefill记录逐字段完全一致。

|条件|Prefill T|Host|CUDA API|Device wait|sync residual|unattributed|GPU activity union（非A）|
|---|---:|---:|---:|---:|---:|---:|---:|
|B1|100.116413|45.683467（45.630347%）|53.771358（53.708834%）|0.525502（0.524891%）|0.136086（0.135928%）|0|52.541659|
|B4，仅局部审查|152.587591|69.544101（45.576512%）|82.895299（54.326370%）|0.025024（0.016400%）|0.123167（0.080719%）|0|104.121389|

CUDA API submit/non-submit：B1为52.179575/1.591783ms，B4为79.467389/3.427910ms；本Prefill无已观察cudaMalloc，不补造allocation预算。CUDA API成本不等于纯CPU计算，submit/non-submit不等于阻塞/非阻塞。Device wait保持必要活动与受支持同步区间的union交集，不以terminal减同步入口代替，不拆复制API内部等待。

## 同步与完成时序

以下绝对值均为原trace ns；必要成员是A后缀投影，**不是自然默认流完整物理W/B**。

|条件/同步|API入口→返回|必要后缀数 / 最后完成|Device wait union|准确解释|
|---|---|---|---:|---|
|B1内部sync353|22320718013→22321351749|8 / 22321317943|525502ns|无源码callsite观测，保留Raw内部身份，不冒称token-ready|
|B1首token sync354|22419022372→22419050224|1905 / 22419004550|0|最后D2H在入口前17822ns完成；首ready为22419841194|
|B4内部sync353|23543125794→23543233414|8 / 23543219708|25024ns|唯一API36770/correlation172191，非结构化token-ready；不能把107620ns全算wait|
|B4首token sync354|23693187174→23693227745|1821 / 23693055451|0|API38584/correlation200923，natural_token_ready/prefill.token_ready/token0；首ready为23694390270|

B4首token copy为API38583/correlation200922：`23649330213..23693185121 ns`（43.854908ms）；唯一32-byte D2H activity347为`23693055035..23693055451 ns`（416ns）。其后stream sync是当前`.cpu()`完成helper的实际路径；D2H早于sync入口131723ns，不意味着`.cpu()`已经返回。API内部等待不能从这些区间分离，整体保留CUDA API预算。sync返回到原completion point间隔1.162525ms不是GPU Device wait，也不移动边界。

## 能回答什么，停在哪里

局部路径已经能回答**当前完成路径下，512输入batch1→4的一次Prefill负载个案**：GPU活动union增加约一倍、Prefill墙钟及CUDA API预算增加，但受支持同步暴露反而减少。负载增加不强制Device wait占比增加；不能从单次观测证明稳定趋势，不能把API预算变化归因成某种已识别内部等待。unattributed=0也不等于所有内部机制可解释。

因此暂停独立CUPTI native实现及旧84参数追索；为这个Prefill问题没有必要的新服务器操作。若另要回答B4 Decode/完整Request，需要其未解决的提交效果证据，不能借本报告补齐。原ZIP/REP/SQLite/Canonical、BLOCKED machine report、Formal结果及Gate13限定PASS保持，Gate14不启动。新小汇总与准确本地位置仅存忽略的诊断目录和handoff；未重跑整批S/B、Q0、pytest或采集，不清理文件。

## 7.140补充：复制区间实物与完成路径对照待审方案

2026-10-12；方案身份`COMPLETION-PATH-ENGINEERING-DRAFT/0.1`，**仅供审查，未实现、未批准部署或采集**。下述新干预用于检验完成路径是否改变显式同步中的可观察暴露位置，不是为了使Device wait变大，也不延续7.138的CUPTI方案。研究/冻结定义及已有结果不改；不新增单独流程文档。

### 原SQLite独立复核

使用上文同一B4 SQLite的read-only/immutable连接，读取前后SHA256仍为`569b690715495748f1af6706d2ea93a5b0a5a94a0fc29f104e1c9cd542b2a7be`。只复核指定API及其区间内原活动，不重算A、整批S/B或完整analyzer。

| 原记录（同trace clock、PID65008/TID59500、context1/device0/stream7） | 起止，ns | 已核验值 |
|---|---|---|
| runtime38583，correlation200922，成功`cudaMemcpyAsync_v3020` | 23649330213→23693185121 | Host API包络43.854908ms，维持CUDA submit API预算 |
| 与该包络相交的516个kernel，逐个唯一成功launch映射 | 按各kernel实际区间裁剪并集 | 30.867774ms；launch均在复制入口前返回，无其他进程/context/stream的kernel混入 |
| 最后kernel11846，correlation200916，ArgMax；launch runtime38582成功 | kernel23692936604→23693053659；launch23648418051→23648426694 | 完成在复制入口后43.723446ms；依据真实correlation，不按时间邻近配对 |
| D2H347，correlation200922，32 bytes | 23693055035→23693055451 | 416ns；比最后kernel完成晚1376ns开始 |
| runtime38584，correlation200923，成功`cudaStreamSynchronize_v3020`；physical354 | API23693187174→23693227745 | 同步包络40.571µs；D2H早于入口131.723µs；已核验必要后缀与同步交集0 |
| 原首Host-readable completion投影point | 23694390270 | 位于复制/同步返回及Host token提取后；不是网络发送或独立GPU完成证据 |

同主线程在复制包络内只观察到这一个runtime API，没有记录可据以分离其内部等待的嵌套runtime/driver调用。最后ArgMax、D2H、物理sync分别通过原correlation/context/stream连接；516个kernel的区间并集仅是activity量，不能单凭重叠成为等待/依赖证据。

**已证明的是设备工作在复制API期间继续推进，到后续sync入口前已完成，不是GPU负载很小。** 尚未证明43.854908ms中的Host何时因何等待，也不能将30.867774ms或入口至最后kernel的43.723446ms改记Device wait；区间余量同样不能被反推为纯CPU成本。复制API全预算不变，当前首token sync wait=0、Prefill总wait=0.025024ms仍来自上文已支持的内部sync。`unattributed=0`不等于内部机制全部已分离。

### 唯一最小待审对照

固定为**512输入、batch4、每样本2输出**的一次整体batched request；同一4090、Qwen2.5-1.5B-Instruct内容快照/输入digest、torch2.6+cu124、FP16/eager/SDPA/greedy/cache、主线程、自然实际流、collector和全部质量门。warmup3、repeat1、加载/暖机/成功drain均在窗外，不新建N1专用流，不增加负载或改变Decode。首token完成后仍按原路径生成第二token；本方案只检验Prefill，**不解决或放行Request/Decode的原缺效果问题**。

建议将来批准后最多两个P1模型进程/两条profile，固定`C0→Cpre`，每路径一次，不另采P0/marker组、不重试或按结果续批。C0保留自然执行路径；Cpre仅在**测量Prefill的token0、argmax已提交后、`.cpu()`Host复制之前**增加一次实际流同步。两个路径使用同一新增诊断包装/身份准备位置，C0该位置不调用CUDA同步；记录公共包装的原始范围/开销，不假定其扰动为零。暖机继续两路径共同的原暖机合同，不把配置值冒充实际次数。

| 路径 | 固定执行顺序与唯一变化 |
|---|---|
| C0 | forward→argmax提交→原cache/共同Host准备→原token-ready helper：`.cpu()`（复制API→helper内stream sync）→Host整数token→原completion记录 |
| Cpre | 同前缀→在同一helper入口、Host复制前对持有的实际current-stream对象`synchronize()`一次→完全相同的`.cpu()`/helper同步/Host值/completion；新增同步有独立干预身份，不能标为natural_token_ready |

两个路径的request/phase公式和Host-readable completion规则相同，但实测时间点/时长当然可以不同；不把新同步返回当first-ready，不移窗口、不增加Host读取/D2H，不把NVTX本身当完成。每次测量输出仍须两个、每个四个实际Host token，C0/Cpre逐值核对，EOS/缺值照既有规则拒绝；不复制旧token作为新实测。

**实际流与必要集合的可审查要求：**

- 已有B4实物的actual FIFO为context1/stream7（NULL）。framework current stream、native handle0和trace stream7是三种身份；不按编号/handle=0推断LEGACY/PTDS。新run不能硬编码stream7或假定仍相同。
- 将来producer在两路径同一位置记录/持有实际framework stream及native handle/device/主线程身份；Cpre调用该对象，而不是device-wide synchronize或另造显式流。Raw必须将实际argmax submit→kernel、Cpre API→physical sync，以及后续copy→D2H通过唯一correlation和进程/context/lifetime相连，并核验它们位于同一实际FIFO。只凭Python stream对象/上下文不足；发现相关其他流/event/未知incoming依赖即拒绝，不能为了匹配结果关闭框架行为。
- Cpre的必要集合按成功drain、原物理前缀、所有实际先行提交、stream/context/event依赖恢复；不能只取pending或与sync重叠的kernel。**尚未提交的后续D2H不在这次新增同步的必要集合内**，但必须进入之后helper同步的相关集合。保留早已完成的前缀及原来源，不裁物理W。
- 默认模式仍允许UNKNOWN；沿用G9投影证明义务：LEGACY/PTDS的相关后缀成员、依赖边、完整闭包和唯一frontier必须相同，再作目标Prefill交集。无证据或两模式不同即停止局部A，不借N1非默认非阻塞流资格来发布自然流完整物理B。依赖尚未记录但不存在仍是显式支持假设，不变成新证明。
- 新干预必须预声明为独立Engineering完成路径变体。当前[自然域消费者](../../exposedpath_v141/gate9_domain.py)明确拒绝`G1_INTERVENTION_CONFLICT`，不能直接走旧自然G1入口或伪造自然身份。未来仅在此方案获准后增加窄域封套/分派及对应反例，复用原S/投影A；本次不改消费者、schema或冻结合同，也不发布新A结果。

### 预定判别、拒绝与解释边界

| 将来观测 | 可作的个案判断，不能预设其出现 |
|---|---|
| Cpre新增同步内仍有必要GPU活动，交集非零；后续copy包络变短或完成位置变化 | 支持“显式completion位置能改变预算落点”的Engineering解释；不能将差值等同原复制API内部等待、稳定收益或纯同步因果贡献 |
| Cpre新增同步交集为零，活动已在入口前完成 | 合法零结果：本次预同步入口前工作已完成，不能据此否定所有路径效应或强制改负载/标记来获得wait |
| 新增sync很长但必要活动交集很小；或copy仍长 | 分别保留wait、residual、copy API包络和activity原值，现有证据不支持把全部Host阻塞解释成GPU暴露 |
| token/身份/clock/drain、提交映射、实际流、依赖、frontier或新诊断冲突 | 硬停止，保留失败/UNKNOWN，不输出可信局部A、不自动重试；只有独立证明影响在首ready之后的缺口才可沿现合同保留Prefill审查 |

未来实现的最小独立预期：同FIFO先行K1=[10,30)、K2=[30,40)，均在20前已提交，Cpre同步=[20,42)的必要集合含K1/K2，wait union=20、residual=2；之后才提交的D2H=[43,44)不属于Cpre的集合。C0复制API=[20,45)、之后helper同步=[46,48)则该helper的wait=0，复制仍全部记API。此手算仅用于接线回归，不预测GPU实测时长；错stream但相同时段、缺correlation/失败同步、把后提交D2H加入Cpre、两模式集合不同却A同值、错variant/干预次数必须拒绝。两路径均只增加最小版本化身份，不能把旧数据改role升级。

旧封存自然B4用于定位/说明，不能当新干预的同期配对重复。将来新结果即使局部闭合也只是受干预的Engineering个案，不授Formal、统计趋势、P0精确组成迁移、完整request/default-stream B或Gate14；不修改原B4 BLOCKED/UNKNOWN/NOT_ASSESSED或Gate13限定PASS。**当前下一步只有审查本方案，不需要服务器操作、部署包或新采集入口。**

## 7.141 用户批准后的最小实现与新执行合同

本节取代7.140末尾的“尚未实现”现行指令，历史审查/数字不改。用户批准本地实现、验证及待审交付，不授权本窗口服务器或GPU/Nsight执行。方案具有个案判别价值：同负载只改变Prefill复制前completion位置，比较已观测预算落点；无法识别自然复制API内部等待，也不保证Device wait增加/复制缩短或E2E改善。共同包装/标记本身有扰动，不能宣称零开销。

| 产物/入口 | 新版本及约束 |
|---|---|
| manifest `completion_path` | `COMPLETION-PATH-ENGINEERING/0.1`闭集C0/Cpre，独立run/WMPC，pass1、512/b4/o2/w3/r1、token0/prefill；study_mode=`COMPLETION_PATH_ENGINEERING`，domain_qualification=null，不伪装G1/N1 |
| pass ledger | `exposedpath-pass-identity/0.6.0`，保留所有真实暖机/measured request、manifest/prompt/source hash及新增binding；旧0.5路径不变 |
| execution | `exposedpath-completion-path-execution/0.1.0`，共同hook的实际PID/TID/device/native handle/identity、variant、成功状态、实测0/1 sync次数；token仍为原batch逐值文件，不新增D2H |
| 新局部结果 | `exposedpath-completion-path-prefill/0.1.0`，独立`prefill.json`及完整hash文件链；旧domain reader明确拒绝。Request/Decode=`NOT_ACCEPTED_LOCAL_REVIEW_ONLY`，physical_b_qualified=false，Formal/D/Signature不授予 |
| driver / 交付 | `completion-path-delivery/0.1`，固定C0→Cpre两模型进程/两profile；单次profile300s、export180s、外层driver900s，无重试/替补，固定两槽完成即STOP_FOR_REVIEW |

producer调用持有的actual current stream对象，前后native/device一致，测量第一token仅一次；两组同hook，C0无sync。Raw再核验公共range、独立`engineering_precopy_completion`结构化sync、唯一成功API→physical mapping、target thread/context/trace FIFO以及argmax/copy→activity correlation，不能以Python对象/native0或编号相等代替trace映射。首版沿当前观测到的默认native流支持域，出现其他实际流、相关event/graph或默认模式歧义拒绝，不借N1资格。

新消费者复用Canonical、原projection/S/A及官方同类warning处置。完整drain前缀保留Raw引用，成功drain及返回前完成事实逐条核对；其setup/warmup没有request ownership时仍未知，**不伪造来源，不称其为合格物理S/B**。新增同步的当前request集合经原S在LEGACY/PTDS分别恢复，全部先行成员（含已完成）/依赖边/唯一terminal一致；drained Raw FIFO前缀另列、核验同线程/流/顺序。后提交D2H不得混入新增sync，必须有其后copy唯一效果映射。报告`all_observed_preceding_activity_ids`与`request_wait_set_activity_ids`明确分离，不用“pending集合”代替完整先行工作，不裁Raw。

局部准入按真实首Host-ready边界，不按“Decode”标签：未知提交效果只有同进程实例/主线程/clock、API实际起于完成点之后、无相关incoming/event/cross-stream/全局诊断冲突，才能在保留Decode拒绝的同时继续Prefill。跨界/缺时间或影响不明阻塞整个局部结果和后续组。完整性仍UNKNOWN、measurement validity仍NOT_ASSESSED，未记录依赖不存在沿原显式支持假设，不新增零丢失证明。旧batch消费者/自然domain的整request严格拒绝路径保留。

CPU独立预期：已完成前缀[1,5)、K1[10,30)、K2[30,40)，均在预同步20前已提交；Cpre sync[20,42)的S集合三项全保留，wait=20、residual=2；43后提交的D2H[43,44)排除于预同步，纳入后sync[46,48)。同窗[0,60)手算顶层C0为Host31/API27/wait0/residual2/unknown0，Cpre为Host32/API4/wait20/residual4/unknown0；这只是确定性预期，非目标模型时长预测。真实producer暖机3×2token×2kernel的12条窗前前缀也保留，不把它们赋成当前request ownership。

负例覆盖错variant/次数/role/input/request、失败同步/错物理流/缺或重复mapping、边界/drain/graph/event与影响不明warning、两模式成员不同但wait都0、前缀其他流、缺效果位于Prefill与Decode的区别、旧domain拒绝新role；真实seal→profile argv边界用CPU替身，不启动任何collector。最初红例及中间7失败保留，最终11个相关测试文件**241 passed/0 failed/0 skipped，124.35s**；相关compileall、PS5.1语法解析及diff通过。共用报告函数从launcher下沉到core以避免测试替身在模块导入时捕获，旧batch委托同函数，未改变预算公式或拒绝门。完整命令见唯一[科研进度7.141](research_progress.md)。

交付自审再加device/token布尔值不得冒充整数：先2 failed再最小强化新execution类型门。最终与部署相同的三个相关文件83 passed/0 failed/0 skipped，53.12s，和241项覆盖重叠不相加；修改文件compileall/diff再次通过。

交付源码/配置/输入/hash及prerequisite由实际实现commit锁定，机器路径/包SHA仅在忽略的本地交接索引维护，不制造自引用hash。阶段A默认部署及相关83项CPU，完成回执须协调审查；B另行显式启用，预计15～25分钟、至少12GiB临时空闲（估计），最多两个P1、不含P0，不自动retry/续采。单ZIP保留静态副本、真实入口/异常/退出、完整Raw/REP/SQLite与局部派生/diagnostics/comparison/清单，不含模型权重；UNKNOWN writer时沿原门拒绝强封包。当前仅待协调审查交付，不默认执行、不清理数据、Gate14不启动。
