# 受控资格 warning 有界审计 v0.1

2026-09-27；Engineering，只读审计d4865d0实际失败attempt，不改合同/代码/旧报告。

## 原件与已核验事实

输入ZIP：243486 bytes，SHA256
`39667bee6d8576ea1bab3875e52a67c1af1720cd084152f9c9160a006d98234d`；
清单SHA256 `8ac8edf066525c5029ab5d06ad8ea3476fe2704719129c76078e9fa773fddaa3`。
本地直接核验CRC、路径/重复、52文件（51清单项加清单自身）、全部bytes/hash及精确集合。
SQLite从ZIP反序列化到内存检查，未解压或改写原件；integrity=ok。
REP SHA256 `c6b2630b3db4ae53a1e145d6032aa7ef8f55fda73325b0b04b1833cc0146fbc8`；
SQLite SHA256 `f6024c80358857476bb18940fbea9310b3970474237ca5780bce73e7d8887dea`。

server_receipt绑定d4865d04340ddaa597d38064714d8f8259616e2f、git_status空。
服务器定向51 passed/33.97s（不是本地重跑）；新DLL已构建。执行COMPLETE，token11/12/21/22、
6 boundary、2 drain；Nsight launcher PID56476、exit0、无timeout；单次export PASS。
collection仍BLOCKED：QUALIFICATION_ORACLE_WARNING_IMPACT_UNKNOWN，无qualification.json。
上述执行完成不证明后续全部Raw/oracle/A检查通过；不能称warning是唯一潜在缺口。

## 四条警告与进程角色

DIAGNOSTIC_EVENT共19行；以下四条均severity2、source3=Analysis、timestampType2=HostTimestamp，
globalPid282492145762304（PID60628）。不得直接用该时间裁NSYS trace request窗口。

| rowid | 原文 | 能证明的内容与限制 |
|---|---|---|
| 3 | Not all NVTX events might have been collected. | 完整性风险提示，不是肯定丢失计数 |
| 4 | No NVTX events collected. Does the process use NVTX? | 该关联进程未收集到NVTX；不证明它本来应有或确实没有NVTX调用 |
| 6 | CUDA profiling might have not been started correctly. | CUDA采集启动风险，不是目标kernel失败证据 |
| 7 | No CUDA events collected. Does the process use CUDA? | 该关联进程无CUDA采集事件；不证明其不使用CUDA |

row8明确60628由profiler启动；ProcessStreams/ANALYSIS_FILE绑定该进程stdout/stderr，
嵌入内容为空。META_DATA_CAPTURE记录唯一启动命令为仓库venv Python及本次资格入口，
INCLUDE_CHILDREN=true；PROCESS_0:PID和APPLICATION_PID均为0，不能当作实际PID映射。
结合argv与启动通知，可定位其为本次直接启动端；“只是venv转发launcher”仍是推断。

producer目标PID55192/globalPid282400944816128；该进程有独立Common/CUDA/NVTX注入通知。
已观察Runtime28、Kernel5、Memcpy5、physical sync11、NVTX29；Runtime/Kernel/NVTX目标身份一致。
计数不是零丢失证明，更不能由60628无activity推断它没有依赖。表集合没有进程parent/image/lifetime
的完整映射；ThreadNames只给profiler线程名。REP非ZIP；有限字符串检查不是受支持的进程树解析，
不能据此宣称REP本身没有更多信息。未调用Nsight/UI/export。

## 与批准质量门的一致性

[engineering-sufficiency/0.1](gate8_engineering_sufficiency_amendment_v0_1.md)“诊断与unknown”要求
逐条绑定处置与依据，目标相关或影响范围不明则拒绝，OTHER_PROCESS不是豁免。
其“0.1实现合同”明确当前没有warning局部化证书入口，任何warning仍IMPACT_UNBOUNDED。
oracle第63行及Engineering scope的_diagnostics/_request与此实现一致。

因此**当前attempt保持拒绝是正确的**。一律severity!=1拒绝是当前未实现范围解析器的保守实现，
不是研究层“任何warning永久否决”的新要求。只有具备可复核的局部/无关范围证据，才能按用户
本轮授权新增版本化处置及独立正反例；当前未达到该条件，不能只删oracle检查，scope也会拒绝。
本次不修改实现、不生成绕过warning的A结果、不把UNKNOWN改零，也不追认旧Qwen。

有界外部核查：[NVIDIA同类Windows讨论](https://forums.developer.nvidia.com/t/no-cuda-events-collected/288543)
涉及2024.2.1、不同程序和权限推测，不能证明本build的四条消息无害或权限就是本次根因。
不以该讨论建立消息白名单，不开展新一轮泛化搜索或厂商询证。

另记录未执行到的确定性适配风险：实际ENUM_CUPTI_SYNC_TYPE使用完整
`CUPTI_ACTIVITY_SYNCHRONIZATION_TYPE_*`名称，而新oracle目前比较短名
CONTEXT_SYNCHRONIZE/STREAM_SYNCHRONIZE；当前warning检查更早终止，因此未实际触发该比较。
这不是豁免warning的依据，本轮按只读范围记录、不顺带改代码。未来获准适配时应先以实际枚举
最小fixture复现，有限精确映射，不静默宽泛fallback。

## 历史补证要求（已结束，不再执行）

只针对**这一份原REP**，请协调窗口用已安装Nsight GUI只读打开，保存一份带REP hash的
进程/诊断详情回执：60628和55192的image、父子关系/生命周期，以及四条诊断详细信息能否
明确界定为60628进程局部采集状态而非共享collector故障。截图/可用属性原文即可；
不是新profile、export、Python/CUDA探针或模型重采，不要求全capture零丢失认证。

若现有REP/UI不提供所需属性或仍不能界定影响，明确记录“不可得/未证明”并停止本attempt的
范围处置；不自动重采、不自动改collector或恢复厂商询证。仅证实launcher身份仍不足以保证
诊断无跨进程影响。可继续的证据标准是角色关系与诊断影响边界同时有依据，不是PID不同。

Gate7历史PASS；本次attempt BLOCKED，新Q0/Gate8 NOT_RUN，D/Signature关闭。

## GUI补证收口与原件身份（2026-09-27追加）

以下为用户回传的截图内容与服务器文件回执，本窗口未直接读取截图或变化后的REP：
55192显示GPU/NVTX活动，60628显示Profiler overhead；四警告列在60628下，消息注明
其由profiler启动。两进程均显示information not available，未提供程序名、父子关系、
生命周期或警告仅影响60628的说明。补证没有闭合影响范围，停止该attempt资格判定，
维持BLOCKED。前节补证任务已结束，不再要求打开REP、服务器操作、重采或询证。

| 身份 | bytes | SHA256 |
|---|---:|---|
| GUI打开前REP，封存ZIP内原件 | 90424 | C6B2630B3DB4AE53A1E145D6032AA7EF8F55FDA73325B0B04B1833CC0146FBC8 |
| GUI关闭后服务器REP | 90405 | B39FA8EDF6E459FA79CC5F6136697C1B75F76B977D222D51675BEFA83A8854E3 |
| 封存ZIP，身份不变 | 243486 | 39667BEE6D8576EA1BAB3875E52A67C1AF1720CD084152F9C9160A006D98234D |

变化后REP的LastWriteTimeUtc=2026-09-27T13:39:16.2560288Z；用户确认无残留nsys/nsys-ui。
只确认两次文件身份不同，不推断具体写入者、内部变化内容或数据损坏。此前“只读GUI”是
操作意图，不能据此保证文件不变。变化后的服务器REP不是原件，也不再与原SQLite/export
receipt构成相同hash链；不能替换原ZIP或重新包装冒充原采集。若以后确有差异分析必要，
只能用分别标识的新本地副本；本轮不请求传回变化后文件、不做差异分析。

## 唯一下一方案：本地显式目标解释器启动合同

仅提出供审查，不实施、不采集：为未来受控资格设计直接启动实际解释器的身份合同，
避免将未识别的venv转发端与执行端混为一体。科学必要性是把“谁提交必要工作、谁承载
completion、诊断关联谁”变成可核验输入，不是让warning消失。venv转发假设仍未证明，
本方案不是对此次warning根因的结论，也不保证直接启动后无警告。

先在本地用CPU替身验证：固定解释器/环境与源码身份；启动端PID与producer实际PID须
匹配（若不能匹配则拒绝并保留关系未知）；运行前绑定预期操作与独立oracle；必要的
进程身份观察位于request外，不新增GPU同步或修改窗口。直接解释器是否能保留原环境
必须显式核对，不通过PATH、PYTHONHOME猜测或静默切换环境。
产物为一份小型启动合同及确定性正反例方案；未知/跨进程影响warning仍拒绝，不能用
PID相同替代诊断范围证据。若本地无法建立这条身份链，方案停在设计阶段，不要求服务器
补搜或重采。任何未来真实执行须另行审查授权，本次BLOCKED结果不会因此追认。

sync短名适配是独立的确定性缺陷，可另行tests-first有限修复；不作为第二条实验路线，
不称其解决warning。本轮未修改生产代码或运行测试；Gate7 PASS，新Q0/Gate8 NOT_RUN。

### 后续本地实现（7.69，非旧attempt重判）

用户随后批准[显式目标解释器合同0.1](gate8_target_python_v0_1.md)：新qualification0.2封套
连接CPU probe、实际producer及Nsight启动通知的身份；独立oracle0.1.1有限适配全/短sync名称。
仅新attempt可使用，不在这份旧Raw上绕过warning或重新验收。本地确定性检查不是目标平台
资格，也不能证明原警告根因或影响已解决。旧GUI补证已经结束，旧ZIP继续封存。
