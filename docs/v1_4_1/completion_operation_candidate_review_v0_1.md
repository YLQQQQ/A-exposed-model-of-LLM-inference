# 复制—同步完成操作候选：事后探索性审查 0.1

标识：`COMPLETION-OPERATION-CANDIDATE/0.1`；2026-10-15。
角色：事后探索性派生，不是新Formal A、S/B资格或冻结合同修订。
生产S/A/B、registry、原始数据与报告、Gate13限定PASS和历史停止结论保持。
本轮是用户单独批准的新完成操作假设检查，不自动恢复此前路线B或采集任务。

## 1. 演算前锁定的对象与选择规则

本节先于本轮候选数值演算写定；已知道block1/G512的旧API时序，**不声称盲选或预注册**。
固定消费已有六block的G32/G512 P1，共12run、24次token完成，不按交集大小筛选。
复用原输入receipt、实际token、执行源码及限定G1投影资格，只读SQLite，不读取巨型domain，
不调用生产S/A/B作为答案。任何新冲突拒绝对应链，保留原因，不选择替代样本。

- A候选：单个复制API自身的返回完成scope；须有实例适用的规范保证，不能仅凭活动已结束。
- B候选：同一结构化natural_token_ready范围、同线程内唯一成功复制与随后成功stream sync；
  correlation唯一映射D2H与physical sync，进程/device/context/stream一致，原token身份一致。
  固定子包络 **I=[复制runtime.start, 配对sync runtime.end)**，不以kernel起点或等待大小调整。
  I不是整个`.cpu()`、NVTX范围或Host token读取区间；成功sync保证先行同流工作及D2H完成，
  随后的实际Host token值证明该次读取成功。没有native栈，不称已实测完整C++调用栈。
- 必要后缀：成功窗前drain后、同步提交前，由原correlation和主要线程提交边界确定的同一FIFO
  全体先行活动，**包括早已完成的成员**；不是仅取copy correlation，也不只是pending成员。
  不把全部FIFO前驱说成token数学数据依赖；它们因该stream同步语义必须完成。
- 已完成历史前缀单列原始来源与闭合证据。G1仍不授完整物理W/B资格；只允许其对I的投影为零。
  必要后缀/依赖边须满足原LEGACY/PTDS投影条件。可见其他流、event、线程、未闭合前缀、
  未来/歧义提交或缺映射拒绝，不借时间重叠纳入活动，不回填全局默认流模式。
- 同时算μ(I∩union必要活动)、原sync交集、I总长和I中未覆盖区间；kernel/MemOp按原record
  去重、union，不把空隙称return开销。额外报告复制API内、API间隙和sync内交集，避免遮蔽Host间隙。
- 所有新结果标`EXPLORATORY_POSTHOC_NOT_FORMAL_ACCOUNTING`；UNKNOWN/NOT_ASSESSED保留。

Cpre固定源码中`before_copy`在natural_token_ready NVTX **之前**；不能借该range覆盖新增同步，
也不能将C0/Cpre起点事后移到最早GPU活动。本轮不以其做共同包络的受控效应比较。

## 2. 先验独立手算反例（单位ns；区间半开）

以下是CPU模型关系检查，不是CUDA资格；预期不由A/B或候选实现生成。

| 情形 | 固定事实/集合 | 独立预期与禁止解释 |
|---|---|---|
| 复制返回后Host做有用工作 | copy[0,2)，Host工作[2,8)，sync[8,10)，必要K[1,9) | I交集8；原sync交集1；其中Host工作重叠6，**8不能称纯Host等待** |
| 无关流长kernel | copy[0,2)，sync[2,5)，必要K[1,3)，D[3,4)，无关U[0,20) | I交集3、原sync交集2；U必须排除 |
| D2H很短但先行kernel长 | copy[4,10)，sync[10,12)，必要K[2,9)，D[9,10) | I交集6、原sync交集0；仅copy correlation得1，漏掉必要前驱 |
| 必要工作早已完成 | copy[10,12)，sync[12,14)，K[0,4)，D[4,5) | 成员仍保留，I交集0、未覆盖4；不能删成员伪造完整W |
| 操作内GPU空隙 | copy[0,8)，sync[8,10)，K[1,3)，D[7,8) | I交集3、未覆盖7；不能用入口至terminal的8替代交集 |
| 已完成前缀/未来工作 | drain于-2成功，前缀K0[-5,-3)，后缀K[1,3)，未来F在sync后提交 | 前缀单列且投影0，F排除；前缀pending、错流、错身份、缺映射则拒绝 |

这些反例现已落实为[独立CPU检查](../../tests/test_completion_operation_candidate.py)，不是GPU资格。
另有合法signed时间、重叠union、提交/完成次序、pending前缀、错流/线程、缺/重复correlation、
失败提交及错run/role/request/协议引用拒绝。改变起点会改变测量对象（同例可由6变8），
不是发现更多真实阻塞；本轮实际选择没有据此调整。

## 3. 语义裁决：单API不充分，组合完成操作成立于限定范围

[CUDA12.4.1同步行为§Memcpy](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/api-sync-behavior.html)
区分synchronous和asynchronous两类函数：前者Device→Host返回保证不能直接套给Async。
Async Device↔Pageable **可能**对Host同步；这不是每个实例的强返回保证，更不是内部等待计时。
其他内部资源原因也可能阻塞，不能从长API或重叠归因。
[同版stream sync规范](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/group__CUDART__STREAM.html)
则提供stream工作完成后才能返回的明确保证。

目标PyTorch **2.6.0+cu124**已保存`CUDAFunctions.h`：4027 bytes，SHA256
`343d0cd132554849db0825f03834912bb2d82ebd6785908662838452ad0dd84a`，本轮重新读取/核验。
`memcpy_and_sync`的CUDA分支依次检查`cudaMemcpyAsync`、`cudaStreamSynchronize`成功。
[官方v2.6.0头文件L70–90](https://github.com/pytorch/pytorch/blob/v2.6.0/c10/cuda/CUDAFunctions.h#L70-L90)
与[Copy.cu L341–377](https://github.com/pytorch/pytorch/blob/v2.6.0/aten/src/ATen/native/cuda/Copy.cu#L341-L377)
说明blocking复制分支的同流调用；non_blocking分支只有提交，不应被选择成B。

固定producer为[99f3bae runner L82–118](https://github.com/YLQQQQ/A-exposed-model-of-LLM-inference/blob/99f3bae966f2fb794073ff4d7468233b6b8dd2ac/exposedpath/runner.py#L82-L118)：
`detach().cpu().reshape(-1).tolist()`→实际整数token→Host完成记录。
本轮复用原输入receipt的runner字节hash及旧执行/身份审查，不用当前HEAD代替该源码。

**A裁决：未证明单个Async复制具有本研究所需的独立返回completion scope。**
24个实物中D2H都先于复制返回完成，可报告此先后事实；但不能把这种结果/参数条件改写成规范
必然性，也不能据此定位内部等待。Raw没有buffer指针、native stream handle实参、driver
调用栈或Host内部就绪状态；已有的bytes/内存类型/方向/stream映射不应因此被说成全都缺失。

**B裁决：可以定义并计算“复制—成功同步子包络内的必要活动暴露”。**
它不依赖单复制API独立完成保证，因为随后成功stream sync给出整体的完成保证；其必要集合
由该sync的语义确定，I仅选择观测区间。不能把这个结论说成复制API已经被证明是独立sync。
它回答的是“该有完成保证的操作子包络期间，哪些语义必要工作仍在执行、执行了多少”，
不是“Host因GPU阻塞了多少”“终点前整段都在等”或“优化可节省多少”。

## 4. 指定原件、来源与必要集合

指定成员为封存Formal包的
`source/batch/formal-99f3bae966f2-20261010-sixblock-b1-G512-pass1/collection/capture.sqlite`，
SHA256 `84d3a0cfc8afab129f3c07b893d5155c1ee7101017b376359303f0cfec70d87e`，本轮一致。
原包身份和完整性复用[Gate13审查](gate13_local_review_v0_1.md)，未再扫描1.38GB封包。

- runtime37815：`cudaMemcpyAsync_v3020`，corr197682，returnValue0。
  MEMCPY347：同corr，bytes8、copyCount1；本SQLite的枚举解为Device→Pageable、Device-to-Host。
  `srcDeviceId/srcContextId/dstDeviceId/dstContextId/virtualAddress`为空，不能补造地址或内存依赖。
- runtime37816：`cudaStreamSynchronize_v3020`，corr197683，returnValue0；physical sync354唯一映射。
  同目标进程PID66320/线程50484、activity device0/context1/trace stream7；inventory cuda0→gpu2、
  UUID `0d8fafe6-a1e9-33cc-25fb-632316736455`，编号不同，复用原UUID/物理身份桥接而非按编号相等。
  本轮还按原receipt绑定的cuda_probe/preflight、context表和inventory UUID/PCI逐项核对：
  physical选择3、logical0、activity device0、inventory gpu2各自保存，不用数值相等建立映射。
- 原NVTX13明确run/request/repeat/pass、prefill/token0、natural_token_ready；point2在真实token
  取得之后。原Host ledger/actual token `[29184]`和输入receipt/source hash绑定保持。
- drain NVTX9含唯一成功runtime35936/corr169012→context sync352，结束26657276198ns；
  request point为26660130438ns，不能跨Host/trace钟直接相减。
- 目标进程10827个已观测历史活动全部于成功drain前完成，保存全体Raw ID，不给它们伪造
  request归属；后缀1905成员全部由主线程、同一FIFO在request开始后/sync提交前提交。
  其中1899在copy入口前已完成，仍保留为成员，而非删掉“pending以外”的记录。
  后缀其余成员由明确correlation关联submit，未使用时间邻近配对。
- 未观测到post-drain incoming event/wait/graph或其他流/线程提交冲突；LEGACY/PTDS下
  本地后缀与依赖边一致。沿用[Gate9合同§2](gate9_domain_qualification_contract_v0_1.md#2-g1投影a充分条件是联合条件不是单一数值检查)
  的**无未记录incoming依赖支持假设**，不是“无记录证明无依赖”。完整物理W/B仍不授资格；
  历史物理清单、闭合证明与本地必要后缀分开保存。10827不是完整物理W的声明。

所有先行同FIFO成员因stream sync顺序语义必须完成，但不声称每个成员都在token数学数据
依赖图中不可或缺；该数据图/地址没有被Raw全部恢复。D2H确与该次8字节Host token路径
和唯一调用相符，buffer地址和native调用栈仍未实测。无关流上仅时间重叠的活动不能加入。

## 5. 真实候选演算（全部为新事后探索性结果）

### 5.1 block1/G512首token时间线

下表为同一trace时钟，相对request point，单位ms；没有移动原点以改变区间关系。
半开区间交集在原整数ns上计算，下表只作相对展示。

| Raw来源 | 起点～终点 | 解释 |
|---|---:|---|
| copy runtime37815 | 86.897104～88.771602 | I的固定起点，API总长1.874498 |
| kernel12039 / runtime37810 | 87.084265～87.090953 | 同FIFO必要前驱 |
| kernel12040 / runtime37811 | 87.091689～87.095977 | 同FIFO必要前驱 |
| kernel12041 / runtime37812 | 87.097353～88.531454 | GEMM，同FIFO必要前驱 |
| memset343 / runtime37813 | 88.533182～88.533502 | 同FIFO必要MemOp，非“无关重叠” |
| kernel12042 / runtime37814 | 88.608445～88.687869 | argmax/reduce先行工作，非copy correlation |
| D2H347 / runtime37815 | 88.689277～88.689821 | terminal；8字节Device→Pageable |
| paired sync runtime37816 | 88.772503～88.808056 | I固定终点；物理记录354包络为88.776850～88.807796 |
| Host-readable后point2 | 91.390771 | 不属于I，也不把point延迟加成等待 |

I长**1.910952ms**；候选必要活动交集**1.525365ms**：kernel **1.524501ms**，
MemOp **0.000864ms**（memset0.000320+D2H0.000544），未覆盖**0.385587ms**。
原token-ready sync交集**0**；原sync墙钟0.035553ms，不能用它替代交集。
只用copy correlation只能取得**0.000544ms**，会漏掉其必须等待的流序前驱；
把copy API总长1.874498ms当GPU等待又会吞掉未分离的间隙/Host/驱动/观测成本。
0.385587不是纯return tail：包含首个相关活动前、活动之间、terminal后的所有补集。

### 5.2 固定12run/24token结果，无删样本

原token-ready物理sync交集在24链上均为0（**不是整Prefill A均为0**）。
新候选交集全部位于copy API区间内，API间隙和配对sync内的必要活动交集均为0。
API间的墙钟间隙为772～25838ns，不能从短间隙推出纯阻塞。

| 条件/完成链 | 候选交集中位数 [六block范围] ms | I总长范围 ms | 未覆盖范围 ms |
|---|---:|---:|---:|
| G32 / 首token | 0.6721385 [0.643322,0.819610] | 0.842096～1.756081 | 0.198774～1.100246 |
| G512 / 首token | 1.6422750 [1.525365,1.733586] | 1.910952～2.681682 | 0.379839～0.991840 |
| G32 / 第2token | 0.6182995 [0.575036,0.856602] | 0.848556～1.893807 | 0.273520～1.288915 |
| G512 / 第2token | 0.0004480 [0.000416,0.826105] | 0.103995～1.198929 | 0.103547～0.372824 |

全部24行整数ns、kernel/MemOp、原sync、I、补集、成员数及SQLite来源在
[候选演算CSV](completion_operation_candidates_v0_1.csv)。G512第2token中五个block仅剩D2H，
block4还有kernel；保留这个方向/量级差异，不据此改包络、删样本或扩负载。
新Prefill值六block均高于相应G32只是**事后描述**，不是普遍单调负载规律或新的验证性结果。
两个token链也不能当成独立重复；没有把子包络数值伪装为整个phase的新A比例。

独立脚本[analyze_completion_operation_candidate.py](../../scripts/analyze_completion_operation_candidate.py)
不导入生产S/A/B、torch或domain reader。复用旧资格/身份，不把旧analyzer数值当交集oracle。
输入receipt/12个SQLite/runner/token/ledger绑定，查询后SQLite hash不变。
完整本地结果及成员索引在忽略的`.local/diagnostics/completion_operation_candidate_v0_1/final_bound_v0_1/`；
该目录约7.44MB，不复制大domain。结果JSON SHA256
`f9a21f8fe526925e19f29ed0537a7a32078c8fd8946e086ac3c693b8ccc7c16e`；
公共CSV SHA256 `41d85e557d6db07c22bc68accc071ac039e400b31c5f779d52aa6acb304db4e0`，
每行明确分析角色/版本及原输入角色，不通过CSV改role升级数据。
原首次身份比较发现receipt是run级、token是request级，
已改为**固定字段集合+共同字段逐项+原签署引用/request/repeat精确检查**；未忽略身份差异。
保留最初探索脚本的拒绝现场，未改原资料或旧正式门。

## 6. 信息增量与禁止重复记账

| 比较口径 | 实际可回答 | 仍不可回答 |
|---|---|---|
| 复制API count/sum/union | 该调用花了多久、预算在哪个API | 哪些GPU活动是完成必需，内部耗时由谁造成 |
| 原physical sync及既有S/A | 同步区间内必要活动暴露；本token为0 | 不能覆盖此前copy API期间的必要执行 |
| B候选完成操作依赖视角 | 同一有完成保证的子包络内，何种/多少必要活动在执行；区分FIFO前驱、复制与补集 | 不是纯Host等待、关键路径、可优化时延或全部`.cpu()`成本 |
| 完整同窗correlation/stream/依赖timeline | 也可恢复本候选的同样结果 | 本轮没有证明ExposedPath独占信息、优于该强baseline或新的论文贡献 |

因此新对象对“为什么原sync为0而必要kernel在copy期间完成”有具体解释能力；这是**观察对象
补充**，不是旧算法算错/Device wait已修好，也不是单靠数值变大就解决科研增量。
异步提交后Host工作反例明确否定普遍纯阻塞解释；首尾间GPU空隙反例否定terminal距离真值。
这些反例不否定限定的完成操作交集本身。

本轮**不进入A**。若将来批准改A，应以每个原子墙钟片段从原API/Host/residual预算中重分配，
不是在原A上另加候选数。操作重复/嵌套须union；原sync交集、kernel/MemOp相互重叠必须去重。
不可把同时保留的原A与新候选相加，也不改变现有单sync B或跨sync求和政策。

## 7. 唯一建议：审阅窄域候选合同，不新增采集

**证据足够支持B这一有限测量对象及上述探索演算，不够支持A单API或纯GPU阻塞。**
建议仅提交以下同页草案供裁决，不以旧路线B停止直接否决新假设，也不据此恢复8-profile。

候选：`COMPLETION-OPERATION-EXPOSURE/0.1-draft`，**未批准、未实现于生产、未签署**。

1. 仅涵盖已核对helper中的同线程、唯一连续Device→Pageable复制和成功同流同步，实际token
   完成/身份可追溯；非阻塞复制、异步任务期间可做有用Host工作的通用包络不授“等待”解释。
2. `operation_id`由输入SQLite hash、范围身份、copy/sync原record构成；保留clock、source hash、
   `start_rule=COPY_RUNTIME_ENTRY`、`end_rule=PAIRED_SYNC_RUNTIME_RETURN`，不得任意伸缩。
3. `completion_guarantee_source=SUCCESSFUL_STREAM_SYNC`，另存copy实例参数、实际token和边界。
   缺配对/返回失败/错身份/多副本/依赖闭包冲突拒绝，不以“已结束”补造返回保证。
4. 必要成员沿用已获资格的S依赖；完整物理W与局部投影分开。完成前缀保留，后提交工作排除；
   无关流不得靠重叠纳入，未知incoming/模式歧义不得被更大包络掩盖。
5. 输出仅`operation_wall`、`necessary_activity_overlap`及补集/来源，保留kernel/MemOp union；
   不称纯阻塞、可消除时延、完整Host等待或新的Formal A，不自动改五类预算。

**真正缺的增量资格很窄**：上述“操作配对/包络与原始完成保证”的独立检查，及其与既有必要
集合的连接；不是重新证明CUDA/PyTorch全栈，也不是重跑完整Q0。可优先复用
[NULL-FIFO-D2H受控原件](gate8_controlled_qualification_v0_1.md)的四token独立操作计划：
其已知后缀分别含K1/C1与K1/C1/K2/C2，terminal为相应D2H；核对实际copy/sync范围后，
按这些**预先给定成员**独立算候选交集，而不调用新脚本的集合恢复作oracle。
历史数据仍是Engineering，只能做兼容性/增量资格检查，不能升级Formal。
当前未做此项新资格、未授权新目标机执行；先审阅此草案即可，无服务器操作需求。

此步骤能决定是否采用一个诚实、边界固定的自然完成操作指标；**不能单独决定论文增量或
普遍负载假设成立**。原A/B、Formal与技术报告/旧停止判断均保留。Cpre干预不在自然NVTX
范围内，没有共同起点资格，因此本轮不作“新指标消除了C0/Cpre差异”的比较。

## 附：本轮验证与保全

`python -m pytest -q -p no:cacheprovider tests/test_completion_operation_candidate.py
--junitxml=.local/diagnostics/completion_operation_candidate_v0_1/cpu_final.xml`：
**31 passed、0 failed、0 skipped**；独立手算包含指定原件六段的
6688+4288+1434101+320+79424+544=1525365ns，不调用候选实现生成标准答案。
`python -m py_compile scripts/analyze_completion_operation_candidate.py
tests/test_completion_operation_candidate.py`通过。先红测再实现，未修改旧测试或生产门。
独立演算命令为`python -X utf8 -u scripts/analyze_completion_operation_candidate.py --output
.local/diagnostics/completion_operation_candidate_v0_1/final_bound_v0_1`；新目录拒绝覆盖，
不是可采集入口。31项CPU检查只说明此探索脚本的逻辑，不授CUDA/正式方法资格。

12个SQLite在查询后均与各自输入receipt的SHA256一致；公共CSV与24条JSON逐项核对。
用户研究设计DOCX SHA256仍为
`7e630e4afc19fc9253acf2f327918ed291fdbeaf0c8487afb4bded7ac7140e87`，
保留其修改、不纳入提交。旧封包、Raw、报告、全Formal汇总和生产schema/registry无改动。
本轮使用研究协议技能限制语义、ARS有界验证组织证据、TDD验证独立脚本，不调用外部模型、
子agent或新采集，不把这些流程本身当作科研成果。
