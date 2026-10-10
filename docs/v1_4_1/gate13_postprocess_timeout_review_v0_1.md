# Gate13 后处理超时审查 0.1

2026-10-10；`G13-POSTPROCESS-REVIEW/0.1`。**Gate13 BLOCKED，执行完成不等于 Formal 合格。**
本页是当前后处理入口；不恢复原批次、不新增样本，不覆盖 Raw 或原报告。

## 已核验事实

用户回传的小诊断 ZIP：86330 bytes，SHA256
`ae8c6deb277a61cb1dbd77ced06d9926df684f04221ba86f42e645625e803fea`。
11 文件（10 项索引加索引自身），CRC、唯一路径、完整覆盖、大小与 hash 全通过；
索引 SHA256 `cf27ee85231bb2e3f1f55bd5f66dc53b8fa090f3359142e61aec1737cd29796f`，missing_files=[]。
索引、batch_report 和 formal_index 的 60 槽位一一对应。
执行/原分析均为 `99f3bae966f2fb794073ff4d7468233b6b8dd2ac`，
签署发布 hash `1378c89db04336102a9dc0ce53ef7b1ef17dd9c518320c060e74d39abaa5b669`。
60 条 `RUN_COMPLETE_PENDING_REVIEW`、30 pair；最终 `BLOCKED_POSTPROCESSING`。
finish 超时 7200.016 秒；历史 `UNKNOWN_STOP_AND_INSPECT_NO_RETRY` 不修改。

**小包没有 60 run 的实际输入/manifest、Raw、SQLite、Canonical、domain、baseline 或 token 文件。**
它证明控制层和日志状态，不足以核验这 60 次的实际测量资格，也没有当前 Formal 全链性能样本。

## 重复路径与实际成本

每条 P1 的采集阶段调用链为 `process_domain` → `result_reload_validation/load_domain`
→ `write_baseline/_file_value/load_domain`：3 次完整恢复。
收尾为 `read_formal_batch/load_domain` → `load_baseline/_file_value/load_domain`：再 2 次。
完整日志包含 30 次 canonical、30 次 reload，采集部分的 S 恢复为 G1 36 次、N1 54 次，
与 12 条 G1、18 条 N1 的每条三次相符。

finish 独立日志：G1 S/A/B 均完成 22 次；N1 S 开始 32 次、完成 31 次，A/B 完成 31 次。
即完成 53 次恢复，另 1 次 S 中断。S 完成累计 4729.759 秒，A/G1准入与 N1 A/B 合计
647.184 秒，G1 B 0.281 秒；未记录阶段、未完成 S、baseline、读取等不能凭差额精确归因。
root 日志包含 finish 的转发，不能把两份日志相加；reload 计时还包住 S/A/B，亦不能双计。

旧日志无 run 标签。依据固定串行源码和签署顺序推定：前 26 条 profile 各复核两次，
第 27 条（block6/Nm）第二次 S 中断，最后三条未开始最终复核。
这是日志定位推断，不用来重建测量身份。完整逐 profile 索引保存在本地审计汇总。

历史封存代表数据的 CPU profile 确认还有逐 sync 依赖图恢复和大量 registry 文件读取：
N1 的两次恢复约 702 次 `analyze_sync_semantics`、40494 次 registry load；
G1 约 700 次同步分析、20776 次 registry load。profile 本身增加运行成本，不能直接作为加速比例。
代表性 domain JSON 实际约 558MB/930MB；完整结果的深拷贝/重复解析也是必须控制的成本。
因此重复恢复是已证实因素，但不是声称唯一瓶颈，更不是本轮改写 S 算法的依据。

## 最小修复与拒绝条件

只改最终复核接线：每条 P1 一个 `DomainReview`，先完成原有完整验证，
随后 baseline 复用绑定文件的**小准入凭据**，不复制或缓存完整 S/W 对象。
baseline 的同窗 count/sum/union/mapping/ownership 仍独立重算，结果仍逐值对比。
source/derived 完整文件集合、大小/hash、合同/registry/schema/source、SQLite 非空 WAL/journal
及 Formal 的实际 checkout/artifact 门保持；baseline 重算后再检查不变性。
不同路径/run/receipt/bridge、变化/缺失/新增文件、合同变化、未封存 SQLite 均拒绝。
完整 domain 由当前调用方持有，用完释放；会话在异常时也清空，不做全批大对象缓存。
新增逐 run 和 domain/baseline 阶段进度。原 `load_domain`、旧读取路径和 schema 不变。

S 的 W/terminal、A 互斥/类别、B per-sync、baseline 口径、signed 差、完整 block、bootstrap
及停止/排除规则没有改动；未增加超时、未删任何质量检查。

## 验证和冻结兼容边界

最终相关 CPU 回归 **36 passed / 0 failed / 0 skipped，244.25s**；测试包含实际 producer 文件链、
60 CPU 替身的完整批次、每条 P1 仅一次完整 domain 验证、错误复用、registry 变化、
WAL/journal、baseline 篡改及重算期间源变化、子目录 schema 变化。替身不是 Formal/目标机资格。
历史 G1/N1 实物只用于同输入的结果等值和性能诊断；不升级旧数据角色。

同机、同封存输入的最终无 profiler 比较：G1 106.945s → 66.377s，N1 103.601s →
66.466s；完整 domain 与 baseline 逐值相等，输入 hash 未变，恢复次数均为 2 → 1。
这是各一组本地 CPU 耗时观察，不是目标机加速保证或本批 Formal 的全批时间预测。
早期保留完整结果的原型曾因大对象拷贝抵消收益，未采用；最终实现仅保留小准入凭据。
代码审查发现并补齐合同源码/registry 绑定和 SQLite sidecar 拒绝，没有用跳过检查提速。

判断为**纯性能/对象生命周期补丁**，不改变签署研究或统计规则；原采集身份保持 99f3bae。
但签署 0.1.1 精确钉住 analysis commit 和源码 hash，不能直接以新 HEAD 通过原门：
新分析 commit 及三实现文件差异须作为独立兼容绑定接受后才用于 Formal 新派生复核。
相对 99f3bae 的冻结 artifact 集还继承两份此前提交的 Gate12 签署状态说明变化；
已核对只新增历史/重签状态提示，不改变研究条款，仍须显式列出字节差异，不能声称全部其余源码零差异。
当前 `validate_analysis` 未放宽，原 seal/manifest/domain 的来源字段不回写。
兼容记录不是自动重新签署、Formal 合格或原批次 PASS；不因性能修复作废或重采原样本。

## 唯一待审恢复方案

1. 原现场冻结。先一次只读检查当前相关进程可见性、active/WAL/journal 状态及文件元数据稳定性；
   外部新回执只证明本次观测，不能把历史 descendant UNKNOWN 改成已退出。
   有活跃/无法检查对象或变化则 STOP，不能删除 marker、杀无关进程或调用旧封包入口。
2. 协调审查静止证据后，做单个**取证复制 ZIP**，保留完整原树和历史 UNKNOWN/BLOCKED，
   清单在原树外生成，流式核验源/ZIP大小、hash、CRC、安全路径和完整覆盖。
   它不是接受原批次的 retention receipt。保存当前静止回执和版本索引；不清理现场。
3. 完整档回传并核验后，复制到新版本派生诊断目录；先完成分析补丁的精确兼容绑定，
   再仅 CPU 离线复核全部 60 run/30 pair、baseline 和完整 block 统计。
   不调用原 `--finish-only`、模型、profile 或 export；原 report/UNKNOWN 不改。
   缺文件、hash/身份/依赖/质量/统计冲突即拒绝，partial 不拼接。
4. 独立报告分别列采集 commit、新分析 commit、输入/输出 hash、阶段时间与资格判断；
   全部必需审查通过后才另作 Gate13 裁决。本轮仍 BLOCKED，不作信息增益结论。

私有绝对路径、一次只读命令及本地审计结果见忽略的本地恢复索引；服务器当前不部署新代码。
