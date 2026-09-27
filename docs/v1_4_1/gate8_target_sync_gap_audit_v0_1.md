# Gate8 目标同步最小缺口审查 v0.1（7.48）

2026-09-27；仅只读历史输入兼容性诊断，不追认Gate8/Q0。执行代码及冻结语义未改。
输入为Gate7唯一PASS attempt的Pass1 SQLite，SHA256
`005cf068bff99c36585a91343d8841d12bb2cad41a94bdc9bc1478045691877c`。
以`mode=ro&immutable=1`查询白名单；前后hash相同。未读环境metadata、未调用Nsight。
精确本机位置保留在忽略handoff；下列rowid均带表命名空间，不能把sync行号当Runtime行号。

## 1. 结论及共同前提

**当前没有一项必要门已证明只能用module/RVA解除。** Runtime/correlation已足以定位
这六个调用。缺的主要是新版completion锚点、历史owner、default/context/thread连续性
及必要依赖范围；调用栈不单独证明它们。source profile继续暂停。

- 六physical行来自`CUPTI_ACTIVITY_KIND_SYNCHRONIZATION`（下称S），对应Runtime行
  来自`CUPTI_ACTIVITY_KIND_RUNTIME`（R）。六API均returnValue=0、同一Host globalTid、
  callchainId=null；device0/context1。token同步stream7，drain的4294967295是哨兵，
  不作实际流。context inventory将7标为null stream，不能由此填LEGACY或PER_THREAD。
- 四token有原structured natural_token_ready NVTX（repeat0/1，各prefill/decode），
  其前有同线程、同stream的8-byte DtoH；不是靠CPU周期采样命中才能看见这些事实。
- **整窗资格共同缺口：** D1 boundary、stage、load-task三种新marker计数均为0；旧
  request/phase是legacy范围。旧manifest为run_role=PILOT/data_role=Engineering，与
  旧标记一致，不将其视作Gate7失败，也不能自动改成新版Engineering pass身份。
  旧Host时间与trace不能静默拟合；没有D1原始点不能改写生成新版完成窗口。
- 捕获内全部目标context kernel/memcpy/memset均有唯一Runtime correlation匹配；
  对每个目标sync，按**已观测API结束不晚于sync进入**筛选的活动，全部在进入前结束，
  且没有这些活动对应的提交API横跨sync进入。该集合只是观测候选，不是已恢复W(s)。
  没有唯一匹配错误不证明没有丢失；不能据此将等待填0或把sync整体归residual。
- 只观测18次event-create，没有event record/wait API行；生命周期create/destroy/reset
  查询无命中。缺行不证明无边或连续存活。首drain前候选包含四worker的338次copy，
  旧Raw无task owner；不能用主线程范围或成功drain认领/删除历史。

## 2. 六行差距表

表内时间是**Runtime调用时长**，不是request exposure。四token最后一列的copy间隔
是sync进入减去已匹配DtoH结束，正数仅描述观察到的先后。共同D1缺口适用于全部request。

| physical→Runtime / correlation | 已证事实 | 本行关键未证部分 | 对W / terminal / A / B的影响 | 最小低风险补证方向 |
|---|---|---|---|---|
| S346→R23796 / 61526 | device sync 17,897ns；位于repeat0 legacy invocation之前；无包围NVTX；先行候选K3492/M343/S3 | 与原request-start drain的新版身份联结及setup/warmup原owner | 自身在旧范围外，不塞入request A；但不能用它截断后续W，B历史仍可能含先前任务 | 已实现drain/D1原件联结；setup/task源码及同线程API→correlation证据，非新增CUDA同步 |
| S348→R25508 / 90845 | repeat0/prefill；30,556ns；DtoH M345已结束17,227ns | 默认流与初始化/worker前缀闭包及原owner | 当前token候选可定位；完整W/terminal未资格，B hidden历史不可填；不能把这30,556ns直接写wait或residual | 同上加目标默认流context/thread支持依据；module栈不是唯一证据形式 |
| S349→R27102 / 116210 | repeat0/decode；29,063ns；DtoH M346已结束20,886ns | 同request prefill前缀和更早历史的连续scope | 已完成prefill仍可属W；删到decode起点会低报B hidden；A是否变化取决于真实terminal，当前不授数值 | 保留同request跨phase成员与原phase；不再采全部kernel栈 |
| S350→R27103 / 116215 | device sync 15,172ns；在两legacy invocation之间；无包围NVTX；先行候选K6984/M346/S6 | repeat0→repeat1的闭合历史owner及scope联结 | 原request之外，不作为request A片段；成功返回不能消除上一request在物理W中的历史成员 | 新drain标记/原始physical行+完整旧owner引用；不新增drain或清空历史 |
| S352→R28815 / 145534 | repeat1/prefill；29,084ns；DtoH M348已结束74,480ns | 上一request、warmup/setup进入当前默认流闭包的资格 | 与S348同类，另含cross-request历史；B不能当本request进度比例；当前A仍受共同边界门阻塞 | 有依据的历史owner/default-lifetime支持域；先解决版本/准入范围，不索PDB |
| S353→R30409 / 170899 | repeat1/decode；27,281ns；DtoH M349已结束5,802ns | 当前prefill+前request+setup历史的完整前缀 | 不能只保留pending/本phase活动；没有已资格terminal，不能把短sync解释成已知return-tail | 同request与closed-prior来源分开保留，按必要闭包逐项验证 |

K/M/S分别为kernel/memcpy/memset计数，不是时间贡献。四token进入前候选计数依次为
(5394,345,5)、(6984,346,6)、(8886,348,8)、(10476,349,9)；同一候选物理历史会反复出现，
不能跨sync加总为工作量或暴露。表中M345等指MEMCPY表rowid，不与S行号混用。

## 3. 整request阻塞与可保守保留的边界

依据[Route A质量门](gate8_route_a_quality_amendment_v0_1.md)：

1. **该旧输入：** 新版completion/身份联结缺失，拒绝新版整窗可信A与机制claim；保留
   原工程结果、Raw及本表诊断。不是把整个request填满unattributed后称“通过”。
2. **未来边界已合格、其余closure影响可定位时：** 某一sync解释不足可将受影响片段
   留为unattributed，相关B invalid/null，其余有证据的A可保留。还须检查相关submit
   和传递依赖；不能自动把影响裁成这一个sync的API区间。
3. **历史/默认流/未观测边的影响无法界定：** 拒绝对应窗口可信归属，不把“无事件行”
   当无依赖。当前没有足够证据将本表全部问题降为局部，因此不发布新A/B数值。
4. **条件性敏感性：** 已观察候选都早于sync进入结束，说明不同历史成员集合可能只
   改变B hidden而不改变A；但这不是完整closure证明。不得因此删S validity、授A-only
   新资格、把mode改已知，或解除Derived/Signature拒绝门。

## 4. 一项下一步：对齐真实模型支持域，而非提高采样率

主窗口下一项仅本地完成**producer0.4到目标scope的窄支持域方案**：明确setup/warmup
保留原角色、drain不是owner、默认流context/thread连续性的可接受证据及反例，逐项
对照已有独立oracle与历史Q0可复用部分。当前[closed-prior合同](gate8_closed_prior_amendment_v0_1.md)
明确承认“所有inventory均有measured projection/连续nondefault”是窄实现限制，
不是新的研究门槛；真实Qwen默认流与setup历史不在已实现准入内，调用栈不能修复接口。

方案只区分既有语义内的字段接线与必须明确批准的默认流准入扩展，不先实现、不再
泛查安装。不用换stream、禁异步或截断历史规避真实执行方式。未来如需补D1/task原件，
优先保留原cuda,nvtx最小profile，并先写清采集能解决什么、仍不能解决什么；本轮不授权。

本表为新增只读事实，不是测试/实验PASS。Gate7历史PASS；新Q0/Gate8 NOT_RUN。
