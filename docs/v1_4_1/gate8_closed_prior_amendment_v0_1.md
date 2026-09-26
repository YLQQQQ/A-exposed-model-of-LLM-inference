# G8-CLOSED-PRIOR/0.1.0

2026-09-27；用户批准共享stream裁决稿0.2后的Engineering合同。旧MC/S0.2/A-B0.2、0.3
与历史产物不改；新增显式profile，不能自动继承Q0。Gate7 PASS，Gate8/新Q0 NOT_RUN。

## 语义

保留物理W的完整可观察前缀及所有历史owner，同request已完成前驱不删除。新增
closed-prior只改变有证据的ownership准入，不改变submission、terminal、A union或B公式。
A只裁剪当前窗口；B保留物理历史进度，不成为当前request进度比例或跨sync加总指标。
`cross_request_dependency`独立；`cross_phase_dependency`只比较同invocation成员。
原phase标签保留，新逐activity来源绑定完整identity、role、generation及原始drain引用。

## 最小实现与版本

Producer receipt0.2新增drain ledger0.1（旧receipt0.1仍读取）：仅包裹现有同步，
逐request operation ID、identity、logical device、host诊断时间、COMPLETE/FAILED；
Pass1加非同步NVTX range，Pass0无marker，两者同步次数和位置不变。
Canonical原样保留Raw；单独closed-prior证据文件绑定Canonical/scope/drain ledger hash。
证据校验后才传给S；新S0.3及A/B0.4显式记录profile与证据hash，旧loader不得猜测。
新A/B采用已批准signed-int64时间/uint64 duration。Derived尚不支持新identity版本，
保持拒绝；不通过删掉五INVALID或零unknown门放行。

Drains必须同时匹配producer回执、同PID/TID的唯一NVTX范围、唯一真实
cudaDeviceSynchronize API及其correlation唯一映射的physical cuda_sync行；后者的
PID/device/context/trace clock须与lifetime绑定scope一致，区间在API内。`drain_ref`
指physical行，原行的runtime_record_id再解引用API；缺physical scope也拒绝，
不以设备声明或API名代替scope证明。producer在warmup前及原无参同步前核对
current logical device，冲突拒绝而非改变device或增加同步。API成功、logical→trace映射明确，
必须在目标request起点之前且在旧owner窗口之后。Host clock须为既定perf-counter域，
仅与同域request-start anchor检查顺序，不作trace/host时钟拟合。
缺hash、重复、跨run/pass、缺API/clock、失败返回或时间冲突均拒绝。

Lifetime证据不由drain提供。连续存活stream可用**producer持有同一资源生命周期**的
非同步范围声明，结合范围内binding activity的correlation和Raw stream/context inventory
确定trace namespace；声明绑定producer源码hash并须在目标资格时验证其持有/释放行为。
它不是CUDA依赖边、丢失计数或仅靠marker就能证明的硬件事实。未取得该producer
资格时输出始终NOT_ASSESSED。新本地实现先限定连续、非default、无跨owner event的
单stream支持域；不是把未支持路径当无依赖。
Raw若出现与该范围冲突的stream/context销毁、重建或reset，不能让声明覆盖事实；
Runtime缺handle映射时在当前窄域保守拒绝。没有相反记录也不独立证明持续持有。

Default stream需独立核对LEGACY/PER_THREAD与context/thread生命周期，不能无故要求
cudaStreamCreate；destroy/recreate需generation及真实生命周期映射，不能凭编号接边。
上述两种路径本版不准入closed-prior，保留旧S路径/拒绝行为，不自动声称已支持。
无初始化/warmup owner、capture前历史、相关pending/event/external证据缺口，不生成
历史成员或hidden。可界定局部失败按Route A保留unattributed；影响不明拒绝窗口claim。
collector UNKNOWN不改零，无全capture认证前置。

**实现限制不是新增研究门槛。** 本版要求选中进程的inventory activities全部具有
完整measured request projection并绑定连续lifetime；这是窄确定性fixture的闭合支持域，
不是Route A要求capture所有活动有owner。setup/warmup无projection以及可证明无关的
其它活动目前也可能被拒绝；不得声称一般eager模型已接通，更不能换stream躲过default。
低层S_VALID/B_VALID表示在该输入声明/版本内算术与语义检查通过，不代表真实声明已资格验证。
高层真实入口保持BLOCKED/NOT_ASSESSED，明确`CLOSED_PRIOR_TARGET_SOURCE_NOT_QUALIFIED`；
合成完整性计数仅SYNTHETIC_REGRESSION_ONLY，新profile不消费既有controlled source proof。

## 来源、版本及失败边界

| 入口→产物 | 版本 / 必需关系 |
|---|---|
| 原runner调用→drain ledger→producer receipt | drain0.1 / receipt0.2；与每次完整identity绑定，失败drain保留FAILED并停止后续request；旧receipt0.1不带此文件 |
| 已有Raw/SQLite→Canonical/projection | 原版本不改；包含Raw原始NVTX/drain事实、三namespace映射和D1 point；host clock不替代trace clock |
| input receipt→lifetime bindings→closed-prior | input0.2 / bindings0.1 / evidence0.1；bindings钉住SQLite字节hash、Raw lifetime marker ID及binding activity ID；drain ledger、Canonical、scope分别hash引用 |
| S→A/B→coverage | S0.3 / A-B0.4；source含closed-prior hash；每activity完整原identity/role/phase/generation/lifetime_ref/activity_ref/relation/drain_ref；cross-request独立于cross-phase；coverage沿用D2不新增指标 |
| analysis→file-chain→Derived | analysis0.5 / file-chain0.4；保存原drain/bindings/provenance，重新核对hash；Derived明确拒绝A-B0.4，不映射成旧0.3 |

hash有向且无循环；Raw/输入不变，已有输出拒绝覆盖。坏版本/identity/hash、未闭合scope、
部分写入不发布成功索引；保留诊断staging，不resume拼接。时间戳/时长边界仍精确为
signed-int64/uint64；两合法时间戳之差仍按duration范围验证，不经浮点转换。

## 独立预期与执行计划

依据bridge0.2纸面例：同ownerhidden8；两ownerhidden25；三ownerhidden35；exposed均5、
tail10、sync内A_wait5/residual10。文件回归允许另一组显式时间，预期仍须独立手算。
负例：缺/失败drain、错误clock/run/pass、未标记历史、event/external、lifetime缺失/重用、
hash变动和未知schema。原件不改，新派生使用独立目录并拒绝覆盖；部分写入不发布成功。

- [x] Producer RED→GREEN：新增`tests/test_gate8_drain_producer.py`；真实runner输出receipt，
  CPU device/model doubles仅隔离GPU；验证调用次数、成功/失败、Pass0/1与实际文件hash。
- [x] S/AB RED→GREEN：`tests/test_gate8_closed_prior.py`经合成SQLite真实Canonical入口，
  两/三owner与旧路径隔离；匹配drain/lifetime后保留全部W、原owner、正确B和A窗口。
  函数入口`build_projected_ab_inputs(..., closed_prior_manifest=...)`，证据重新解引用。
- [x] 文件链：S/AB版本化写读、producer/input receipt衔接、哈希拒绝、Derived版本拒绝；
  本地UNKNOWN质量门仍阻止不合格科学发布，不将合成结果称为真实验证。
- [x] 目标支持域review、定向/CPU全量/compileall/contract/Canonical/oracle/diff检查；
  进度与handoff同提交，正常推送；只有真实证据源与接口均可行后才准备服务器包。

旧Q0的未变公式与单owner闭包结论保留，只新增共享stream/drain/来源与失败传播的
受影响验证；合成通过不等于资格。真实模型当前缺lifetime/初始化owner来源及新入口
目标栈验证；本版不自动包装为部署就绪，也不要求重跑旧smoke。

本地验证：最终CPU全量1240 passed/5 skipped（nvcc隔离）；定向迭代73 passed，
独立review复核11 passed；compileall、contract37/37、Canonical7模块、oracle静态独立性、
diff检查通过。原始RED及执行限制详见research_progress7.39；合成完整性计数不代表Nsight。

## 下一项最小接口工作（本地，无采集授权）

1. 现Raw能证明：API成功/物理sync的scope、相关activity/correlation、D1点、inventory编号。
   它单独不能证明未标记setup/warmup owner或某一编号从未重用；hash只证明来源字节。
   实际源码入口：`load_model`的初始化在Gate8 producer API外；`run_warmup`仍是无NVTX
   且仅记录pass outcome；`run_gate8_requests_to_files`只接受已resident输入，不是模型
   launcher。当前runner没有显式stream创建/持有声明，不能从device字符串推断default模式。
2. producer可在不加同步条件下补：已实际执行的setup/warmup scope/role、持有资源对象的
   generation及开始/释放声明。须检查真实torch资源所有权是否能给出这些事实，不造假API。
   连续nondefault可复用本接口；default需context/thread及LEGACY/PER_THREAD语义映射，
   不要求不存在的create/destroy；确有destroy/recreate才需generation切换，不能按编号接边。
3. consumer下一步只应选取目标request的必要前驱及可证明无关scope，保留完整W；
   再用未标记前驱与无关stream成对反例验证，不把当前全inventory限制扩大为研究验收要求。
4. 完成上述本地来源可行性/接口审查后，才提出一次目标栈两request共享stream/drain
   受控验证：固定新执行源码/版本/原oracle，回传原REP/SQLite、producer/drain/lifetime
   及Raw scope引用；仅补新增ownership路径，历史未变公式/同owner结论复用而非全矩阵重采。
   任何scope/来源不匹配停止；不自动运行、换流或将独立stream旧capture升级。
