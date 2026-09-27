# Request-drain A范围准入 amendment 0.1

状态：用户已批准的本地实现范围；非目标栈资格、非Protocol Freeze。
适用profile `G8-REQUEST-DRAIN-SCOPE/0.1.0`；证书
`exposedpath-request-prefix-certificate/0.1.0`；独立结果
`exposedpath-request-a-scope/0.1.0`。

## 1. 改变什么，不改变什么

承接[原草案](gate8_request_drain_scope_draft_v0_1.md)与研究设计v7.1 §1.5。
模型和输入已就绪，从原有成功request-start drain后的D1点，到最后token ID
host-readable；sampling/prefill/decode包含在内，外层文本化、网络和加载不混入A。
不添加同步，不重新定义三个窗口。允许合格前缀完成证书与后缀依赖证据独立授予
`A_SCOPE_CERTIFIED`，不再要求历史B完整才能计算这个范围内的A。

这是MC0.2 §9–10的**版本化证据准入扩展**，不是旧数据改名合格。MC正文、原S/A-B
schema/reader、W定义、互斥union、B及D/Signature公式保持原样。仅显式选择新入口
的派生分析适用；旧Gate6/7结论不撤销，旧attempt不追认。

若`W_full=P∪Q`，证书证明P已提交且在drain实际completion scope内完成，
`end(P)≤end(d)≤request_start≤sync_start`，则P与本次sync相交为空。
这只证明A交集无历史贡献，不补造P时长、owner、hidden或精确terminal。
完整物理S/B按原路径原样保留；后缀计算仅为A交集证明，不输出为替代物理W。
B历史不足继续invalid/null；本profile不发布D_score或Exposure Signature。

## 2. 明确的首版实现支持域与停止点

`exposedpath_v141/gate8_request_scope.py`提供独立文件入口与重推导reader。
本版仅接受显式`synthetic_fixture=True`及`SYNTHETIC_CONTROLLED_ORACLE`证书。
真实入口无条件`SOURCE_NOT_QUALIFIED`：登记任务COMPLETE或无其它线程记录不构成
真实producer全范围封闭证明。不能将此参数用于把实际trace重标为合成而取得资格。

首版实际算法域：单目标request、单context、一个已识别的请求Host提交线程、连续
非默认stream、无event路径，所有已观察活动必须可归为已完成前缀或合格请求后缀。
其它相关线程、跨scope、资源重建、未定序提交、后续其它request活动均拒绝；这是首版
实现限制，不把它宣称为研究上的永久必要条件。第二参与线程不自动排除，需有独立证据
及显式adapter支持后再纳入，当前不预开发通用多线程。

不新增mode UNKNOWN等价规则：完整合成来源及无NULL-stream活动是本版前提；
出现NULL-stream即拒绝，不猜TU mode。旧Qwen使用NULL stream，因此**当前实现不是
自然Qwen已经可运行的证明**。真实前缀封闭与请求内mode/资源/依赖证据仍需落实，
没有因此生成服务器命令或collector方案。

## 3. 机器字段及验证顺序

证书为严格闭集对象：`schema_version`、`canonical_manifest_sha256`、`scope_sha256`、
`request_id`、`drain_ledger={filename,sha256}`、`source_proof`。
`source_proof`仅允许上述合成basis与四项严格bool true：
`prefix_producers_closed`、`no_late_relevant_submission`、
`request_dependency_records_complete`、`resource_lifetime_continuous`。
它们是受控fixture的显式前提，不是自动从trace推导的工具完整性声明。

1. Canonical和projection hash、D1重新推导、完整pass/request/repeat/attempt身份及
   设备adapter照旧校验。request_id仅作已绑定pass内选择器，不跨run寻找同名request。
2. drain ledger完整身份匹配唯一request；成功状态、host同钟顺序；唯一原NVTX范围
   对应唯一成功`cudaDeviceSynchronize` Runtime及physical sync，核对PID/TID、
   logical→trace device、context、trace clock及结束先于request_start。
3. 原活动、API/correlation和drain scope确定前缀已提交且完成；activity与请求内sync均
   核对实际PID/device/context/clock，不能借另一进程的同号correlation；未知owner可以保留，
   不以时间重叠确定W。请求内API须同主线程、同钟、成功，资源连续性反证阻塞。
4. 后缀通过既有S闭包/owner/terminal规则，再交既有A互斥计算。任何未覆盖错误不
   被忽略为Host。此严格证书入口不吞掉局部错误；已有Route A局部unattributed路径
   保持独立，本次不扩充其准入，也不修改既有局部/不可界定反例。
5. 结果单独保存`a_records`、`a_suffix_proof`（明确不是物理W）、原`physical_s_records`
   与`physical_b_records`，以及原record namespace/rowid/clock/SQLite hash的drain/
   prefix引用。`validation_role=SYNTHETIC_REGRESSION_ONLY`，
   `measurement_validity=NOT_ASSESSED`、`dropped_records_status=UNKNOWN`。
6. 输出不覆盖；缺产物、未知版本、hash/内容冲突或部分JSON拒绝。显式reader从输入
   重推导并逐字段比对，新结果不送旧AB/Derived loader，避免版本猜测和循环hash。

## 4. 独立预期与资格边界

测试经过实际DrainRecorder、runner boundary producer、合成SQLite、Canonical、D1
projection，再进入新文件入口；不使用分析器生成预期数值。
目标request=[400,600)，prefill=[400,480)，decode=[480,600)。前缀K=[130,160)，
其API=[20,25)没有request owner；drain API=[380,390)，physical=[381,389)。
后缀API=[410,415)，K=[430,460)，sync=[440,470)：A=(165,5,20,10,0)。
第二token变体再加API=[530,535)，K=[550,580)，sync=[560,590)：
prefill=(45,5,20,10,0)，decode=(85,5,20,10,0)，full=(130,10,40,20,0)。
空Q变体A=(170,0,0,30,0)，并不表示物理历史为空。B始终保留原失败/null。
包含负时间/跨零、迟发/其它线程、错误drain scope/pass/clock、资源重建、缺correlation、
terminal、版本/hash、重读篡改和不覆盖回归；复用旧Q0及Route A反例，不重采历史。

这些是本地确定性验证，不能授予新Q0/Gate8资格。未来最小真实验证仍是一个明确
producer来源、已驻留输入的单主线程受控request，含加载前缀与原有drain，两token
使prefill/decode都产生可核验归属。独立oracle比较完成关系与逐类A；错误注入优先在
独立派生副本中完成。只有来源门、本地审查和受影响资格方案具体可执行后，才申请
一次新Engineering采集，回传Raw、producer/D1/drain/source证据、身份及封存清单。
**当前无服务器操作；Gate7 PASS，新Q0/Gate8 NOT_RUN。**
