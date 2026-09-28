# 路线A限定新版资格覆盖审查 0.1

日期：2026-09-28。判定：**限定 Engineering A-only 资格 PASS**。
资格名：`NULL-FIFO-D2H / target-scope A-only / bounded-qualification-0.1`。
不是完整新版Q0总Gate PASS，不是Gate8模型验收，不改变原collection BLOCKED。

## 判据、版本与来源

依据[qualification-next §3–4](gate8_engineering_qualification_next_v0_1.md)、
[受控构造/独立oracle](gate8_controlled_qualification_v0_1.md)、
[限定Engineering amendment](gate8_engineering_sufficiency_amendment_v0_1.md)。
本审查授予的是这些材料预先声明的受影响子集，不新增准入条件或更改测量语义。

执行commit `8ef1385604c7d35d8ac15efbe76aa9d3a26ba9a2`；离线修复commit
`cb4b3b3b2bfcd393413b9df5968f5e9e1d58bdfb`，oracle 0.1.2，qualification封套0.2。
目标Windows/RTX4090/CUDA12.4/Nsight 2026.2.1.210-262137639646v0，单NULL FIFO、
两个顺序request、每request两个token，预声明无并发/IPC/event跨源及未记录incoming依赖。
构造为NULL-FIFO-D2H/0.1.0；只允许该支持域的条件性A，不推广到通用默认流或其它平台。

真实输入身份、六窗口分量与原始引用见[drain离线审计](gate8_drain_api_reanalysis_v0_1.md)。
ZIP SHA256 `42c40987ae982e9887a5fb2dde0785759d6421ba52efcdae476ee9cb4c3703a5`；
离线qualification文件SHA256 `cb161b74f348221cba67604e447ccc3ca33fa714bf7d557d54705aea6a9999c5`。
本轮重核53文件与ZIP逐字节一致、派生文件hash与既有reanalysis索引一致；没有重分析或改Raw。

## 逐项覆盖

| 必要命题 | 本次真实受控证据 | 独立反例/复用范围 | 结论 |
|---|---|---|---|
| 共同边界、时钟与身份 | 六个trace原生点、host-readable token 11/12/21/22；producer→ledger→projection；PID61132与profiler启动row4完整global PID绑定，manifest/device/source/hash链通过 | qualification的boundary/identity/token_identity负例；target_python的nonce/exe/environment/PID/namespace负例；不把CPUprobe PID等同后续采集PID | PASS |
| 成功drain界定前缀 | Runtime row10/18 return0，corr130/140→context sync row2/6；drain结束先于request点，先行活动完成。row26 cleanup不作为drain | versioned_drain的失败返回、重复、错线程、错correlation/type，以及缺drain反例；不从drain推断未来无提交 | PASS |
| 默认流后缀必要集合 | 每request 2kernel+2D2H；三次同步独立期望成员为K1、K1/C1、K1/C1/K2/C2。LEGACY/PTDS条件集合逐项相同，内部sync未遗漏 | default_scope_obligations独立手算；另一个相关blocking stream使mode不等价；membership_mismatch即使A相同仍拒绝 | PASS（条件等价，不是实测mode认证） |
| 六窗口A具体归属 | 两request各full/prefill/decode，五分量逐项与不调用S/A的oracle相符；非仅求和。各窗unattributed=0，原始区间/分类保留 | 手算错分类但总和闭合负例；有界2ns/5ns分类缺口进入unattributed而非Host/residual | PASS（构造内） |
| 缺边界/映射/身份拒绝 | 正例只证明完整路径可通过，不声称实际发生了这些故障 | qualification_faults、unproved_drain、engineering_scope的boundary/correlation/missing_sync/worker/namespace及producer身份负例；损坏时不发布或对应窗拒绝 | PASS（确定性故障证据） |
| 影响不明诊断拒绝 | 14条已识别info，未出现warning；没有零丢失推论 | qualification的warning及engineering_scope的warning/foreign_warning/未知API/0事件冲突负例；未知范围拒绝，其他PID不豁免 | PASS（确定性拒绝证据） |

以上负例为独立预期的合成文件/CPU测试，不伪称目标平台真实丢失注入。
本轮本地Python重新运行qualification、target_python、engineering_scope、
default_scope_obligations四文件：79 passed/97.14s；未运行GPU/native/Nsight或全量测试。
git diff --check通过。首次本地ZIP逐字节查询有路径分隔符及命令语法错误，修正查询后
53项逐字节通过；该查询错误未修改证据，也不是服务器失败。
qualification-next写“优先”在真实输入派生副本注入，而非强制重新制造GPU故障；用户本轮
明确允许复用既有独立负例。已复用实际文件入口的相同拒绝分支，无需为重复负例重采。

## 历史稳定Q0如何复用

[Gate6 closeout](gate6_closeout_v0_1.md) final-04记录21真实+2合成必需case及23/23总PASS，
gate report SHA256 `3A94F8B9B65294D82929EF183C59C4C84177D489F5AE9E8AF56FDDD676178967`。
它支持原版本物理S的completion-set/terminal/validity、A互斥守恒和B provenance；其中
Missing-Corr等历史反例仍是原版本结论。本轮复用其已封存结论，不声称重新读取全部Gate6 Raw。
它不证明新D1、启动adapter、drain裁前缀、默认流条件A或新版schema；这些由上述新增证据补齐。
物理S/B保留原输出及invalid状态，不能用本次条件A的PASS把物理B改成valid。

## 残余风险与不授予事项

- 无未记录incoming依赖是显式支持域假设，不是“只看到一条流”推出的事实。
  受控源码/操作/token/Raw集合相符约束该假设；对隐藏缺失仍有不可检测风险。
- marker在host-readable之后有观测延迟；使用共同trace时钟不证明零开销或绝对无偏。
- `dropped_records_status=UNKNOWN`、`measurement_validity=NOT_ASSESSED`保持；
  此PASS不认证全capture无损，不用于Formal机制claim。
- 本次实测不能证明任意局部缺记录都可界定。只有合同允许的有界分类缺口可以进入unattributed；
  可见冲突或影响不明仍拒绝。正例unattributed=0不是一般模型质量阈值。
- 不授予通用物理S/B新版资格、D/Signature、模型workload、第二平台、并发/event/graph资格。
  模型的backend/setup、真实内部提交及可解释程度尚未由本构造验证。

**结论：该限定资格无剩余必要补证，停止本轮覆盖审查。** 原attempt和旧Qwen仍不追认；
新建本审查结论而非改写旧report。Gate7历史PASS；完整新版Q0总状态和Gate8仍NOT_RUN。
下一项可进入单模型最小Engineering方案的授权前审查，而不是默认重采受控程序；本轮不授权执行。
