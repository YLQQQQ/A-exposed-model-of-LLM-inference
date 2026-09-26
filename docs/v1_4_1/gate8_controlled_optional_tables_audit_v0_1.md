# Controlled SQLite adapter audit 0.1

2026-09-26；Engineering；旧后处理 BLOCKED 原样保留。依据已批准RouteA范围规则作窄adapter对齐，不授科学资格。

## 实物核验

执行07625b7的0.2后处理目录有29文件；清单覆盖28项，size/hash全部一致。
清单SHA256 `c97830531d81b2246a8062b3a4458969bc17e03b525a43260fbb13a2a8ebf54f`。
第一次export PASS、exit0、0.125秒，SQLite323584 bytes/hash
`34f614db50ad659a6c553160ead4830d64094e933c911c407a8a01b333ac7587`，
REP仍为`edf4c429969f9315b988cf3fb6cee84fa51810ea282ca6165768308c883967d9`。
audit exit1停在MEMSET缺表；本地只读诊断前后SQLite hash不变。

## 已确定的adapter缺陷与最小修复

META_DATA_EXPORT肯定记录product2026.2.1.210、schema3.25.0、lazy=true。
已复制目标安装UserGuide的export --lazy说明（1696–1700行）明确：lazy只创建有数据表；
--tables（1719–1729行）是选择性导出，实际export argv没有此选项。
既有Canonical/observation已有受支持lazy schema规则；新controlled checker却无条件读取
本构造从不调用的MEMSET表。不是需更换collector或重采的科学语义问题。

最小修复只适用于上述**唯一版本组合、唯一元数据值、lazy=true、Cuda capture存在**；
缺MEMSET显式标`ABSENT_SUPPORTED_LAZY_EXPORT`，不是零丢失声明。
未知/重复元数据、非lazy、未启用Cuda均拒绝；可见memset API与额外memset activity
仍拒绝；没有广义缺表→空列表fallback。Raw-check报告0.1.1，construction保持0.2。
producer/native/S/A/B/Q0/registry/profile均不变。

同类表一次盘点：本构造必需NVTX/StringIds/enums/Runtime/kernel/copy/sync均存在，
即使lazy也不能缺。DRIVER缺失沿用既有适配；存在非空则拒绝。
CUDA_EVENT缺失不为stream-sync构造增添依赖；event API不能越过精确API集合检查。
DIAGNOSTIC_EVENT存在，不归一为空，不放宽其当前门。

红测1 failed/21 passed精确复现MEMSET错误；修复后Raw/chain/Canonical定向65通过，
扩展producer/CLI/stream回归85通过；追加diagnostics保留回归后Raw23通过。
compileall、contract37/37、Canonical7模块、oracle independence、diff-check通过。
最终CPU全量1189 passed / 5 skipped（201.51s，显式隔离nvcc）；随后补充两个
实文件/外PID可见CUDA负例，由最终98项定向覆盖（38.52s）。不把新增两项冒称已在
先前全量收集中运行；五skip均为CUDA source编译项。静态检查全部通过。
协调窗口只读review通过；本地检查不声称服务器再分析通过。

## 前瞻发现：diagnostics仍阻塞，不逐错部署

只读实际SQLite经过新MEMSET适配后，独立checker的活动、顺序、sync/W(s)预期检查
均完成，停于`UNBOUNDED_DIAGNOSTIC_REQUIRES_REVIEW`。没有绕门生成合格A/B/D。
ENUM明确Info/Warning、Injection/Daemon/Analysis及TargetTimestamp/HostTimestamp。
19条记录分类如下（全部原记录保留）：

- 全局2条Info：profiling started/stopped；负globalPid是全局标识，不能当目标PID。
- 目标PID61832的11条Info：NVTX/CUDA计数、注入成功、flush政策、CUPTI路径/计数、
  device graph tracing启用、hardware trace不支持而采software trace。它们不是零丢失计数。
- PID53572的2条Info：profiler启动该进程、common injection成功。
- PID53572的4条Analysis/Warning：NVTX可能不全/无NVTX、CUDA可能未正确启动/无CUDA。
  这些是HostTimestamp，不能以24ms直接和目标request的trace钟比较后排除。

Runtime32条均属61832；kernel为device0/context1、warmup stream13、request stream14/15。
source构造仅自身分配、无IPC/event共享，target独立stream依赖集合匹配。
这比“PID不同”更强，但本包未给出父子进程关系表；53572是venv launcher仅为推断。
不能从无可见外部API单独证明外部行为不存在。

范围审查后实现`controlled-diagnostic-assessment/0.1.0`：仅明确product/schema、
enum、精确模板组合；Info保留为状态诊断，未知模板拒绝。计数正则仅识别消息形状，
**未用24/42等计数验证完整性**；不把计数或成功初始化当成零丢失。
四种精确的per-process Warning仅在非目标且非全局PID、没有该PID可见CUDA记录，
并且独立operation/W(s)匹配已通过时标`OUTSIDE_DECLARED_DEPENDENCY_SCOPE`。
核心依据不是PID不同，而是固定源码下的私有allocation、无IPC/event共享、独立stream
依赖闭合。native/producer/CLI明确钉住07625b7的LF/CRLF两组字节hash；
源码变动（包括IPC/event扩展）不能继承此规则。没有父子关系假设。
19条原文、时间类型、来源、severity、PID、SQLite hash/rowid均进入报告；
UNKNOWN、measurement NOT_ASSESSED及资格边界不变。目标/缺PID/global风险、未知文本、
enum/clock冲突、源码不匹配或未闭合依赖仍拒绝。原07625b7失败报告不重写。

## 本地实文件前瞻（不是服务器复验）

本地读取服务器回传source_bytes，逐文件验证等于07625b7 Git blob的CRLF表示；
仅在诊断进程内让SOURCE/NATIVE文件引用指向这些实际字节，以满足既有hash门，
不改hash、不改源码、不运行这些源文件。原29文件前后hash一致。新派生目录位于
忽略的本地diagnostics，分析使用当时未提交adapter，故不是版本化服务器验收。
私有复核脚本与具体路径记录在本地handoff，不上传原trace或机器路径。

结果：`CONTROLLED_CALCULATION_ONLY`、`measurement_validity=NOT_ASSESSED`；
独立W(s)预期2/4/2/4，terminal与目标4个B timing匹配。以下均为纳秒：

| request/phase | window | Host | submit API | non-submit API | device wait | sync residual | unattributed |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0/full | 1766747 | 898490 | 228622 | 0 | 45152 | 594483 | 0 |
| 0/prefill | 725393 | 452145 | 47261 | 0 | 33312 | 192675 | 0 |
| 0/decode | 1041354 | 446345 | 181361 | 0 | 11840 | 401808 | 0 |
| 1/full | 1442473 | 762487 | 254832 | 0 | 87807 | 337347 | 0 |
| 1/prefill | 561438 | 404624 | 26440 | 0 | 2112 | 128262 | 0 |
| 1/decode | 881035 | 357863 | 228392 | 0 | 85695 | 209085 | 0 |

六窗top-level守恒差均0。依据Measurement Contract §10，sync residual是valid sync
内未被W(s) activity区间并集覆盖的片段，包含执行前/执行间隙及return tail，
**不等于B的sync_return_tail**，不能解释为已识别的runtime overhead。
不是把缺失证据挪入residual；unknown0不代表开销为0、也不独立证明归属正确。
共9条B：4目标B_VALID；5条窗口外warmup/prepare/cleanup保持B_INVALID/
INVOCATION_BOUNDARY_INVALID，不能总括“B全部通过”。现有Derived门检查全部B，
故`DERIVED_BLOCKED_UPSTREAM_NOT_QUALIFIED`，没有Signature。未过滤这5条、未修订D门。
publication中的记账margin仍禁止mechanism claim。若需要per-request Derived选择域，
必须另行明确输入集合，不混入本次adapter修复。

## 2026-09-26 目标服务器离线复验实物审计

已直接读取用户传回的完整新目录，不再仅依据聊天回执。本轮本地只读审计，
未运行Nsight/export/native/模型，也没有重跑服务器测试。

- capture commit：`07625b72e90d5fbb5bcb581d03a6f7582b2e0dc6`；
  analysis commit：`c827b61ebe3ec08eae26fe9ab0d063892914a22e`。
- 清单SHA256：`d96fec461a0c55f2c1c265ae7f3f6bc73ead5699aea6644797ecc06304ccbddf`；
  72项大小/hash逐项通过，恰覆盖其余全部文件，总73文件。38个派生链引用通过；
  prior_inputs内29文件与此前直接取得的原件逐字节hash一致，旧BLOCKED报告未变。
- 主分析报告SHA256：`b6294b66936efe99f700be1327057a56aeb2708c819c040ab6c3350cf42c28ab`。
  receipt为`REANALYZED_CONTROLLED_CALCULATION_ONLY_NOT_ACCEPTED`，static/audit exit0，
  error=null；不是科学验收或Gate PASS。路径只记录于忽略的本地handoff。
- 原始transcript：Python3.11.16，98 passed/91.36s；contract37/37、Canonical7、
  oracle independence PASS。脚本含compileall/diff检查，static_exit=0，未重跑全量。
- SQLite以`mode=ro&immutable=1`读取，integrity_check=ok；只证明数据库完整，
  不证明采集零丢失。19条diagnostic逐字段与原表匹配：15状态、4窄范围外Warning。
  dropped_count=null、collector UNKNOWN、measurement NOT_ASSESSED全部保留。

### 独立数值核验与不能扩大之处

本地审计脚本不导入A/B/S实现：按固定构造的两request、各kernel→D2H两次顺序，
直接从原SQLite核对sync rows 3/4/6/7的活动集合2/4/2/4及D2H terminal。
Host阻塞区间使用correlation唯一联结的Runtime API，不误用内部CUPTI synchronization
activity较窄的端点。活动顺序不重叠已核验，独立区间算术得到上表全部六行A。
request=prefill∪decode，分界相等、无重叠；unattributed、守恒差均0。

四个目标B的五个时长字段全部匹配独立预期（ns）：

| sync row | hidden union | exposed union | terminal pre | terminal overlap | return tail |
|---|---:|---:|---:|---:|---:|
| 3 | 0 | 33312 | 0 | 1088 | 8695 |
| 4 | 33312 | 11840 | 0 | 1184 | 7776 |
| 6 | 0 | 2112 | 0 | 1024 | 7504 |
| 7 | 2112 | 85695 | 0 | 14080 | 29533 |

这些是逐sync值，不构成可相加B指标。其余rows 1/2/5/8/9确在六窗外，
保持B_INVALID/INVOCATION_BOUNDARY_INVALID、request=null与null timing。
现有gate8_analysis.py全B资格门仍阻断Derived；目录无Derived/Signature产物。
publication只保留CONTROLLED_ACCOUNTING_ONLY差值，mechanism_claim_allowed=false。

### 新发现：B phase provenance字段未贯通

**不能把上述数值匹配称为B全部字段通过。** S的activity_origin_phases是
activity ID→phase映射；b_provenance.py `_project_b_record`使用`list(mapping)`，
输出映射的键。四个真实B的同名字段因此装入activity IDs，而非phase名称。
S本身保留正确映射：prefill同步仅prefill；decode同步含prefill/decode，
terminal_origin_phase和cross_phase_dependency与构造一致。
现有B单测却手工提供phase列表，没覆盖实际S producer的mapping形状；
schema只验证唯一string/null数组，未揭示语义错位。

此为可定位的S→B字段投影缺陷，不证明W(s)/A/timing公式错误，也不授权改写
历史B产物或撤销/重跑Gate6。当前B phase摘要不应用于机制解释。
修复应先用真实S形状写失败回归，显式核对旧A/B读取与新输出兼容，
补actual-file-chain断言；不得借机改变B可加性、Derived范围或冻结公式。

### 本地最小修复及兼容边界

已依持续授权完成tests-first局部修复；不是新的测量语义amendment。
依据Measurement Contract §10–11保留origin要求、S实际producer映射及A/B 0.2/0.3
既有unique string/null数组合同，B取映射**值**而非键、去重并按字符串排序，null末尾。
排序仅稳定序列化，不代表执行顺序；不归一phase大小写。显式null保留unknown，
缺字段/非mapping/漏成员/额外成员/空或非字符串phase均报错，不填补或猜测。
S映射键必须恰为W(s)活动；原S、W(s)、terminal、validity与五timing逻辑不改。

修复前13 failed/31 passed，包含实际文件链的四行phase断言；首次GREEN扩大检查
发现共享旧S夹具仍伪造list，15 failed/29 passed。已将两处夹具对齐真实mapping，
未添加生产fallback；提前启动的CPU全量因此中止，不作为验证成绩。
修复后B/AB输入/AB bundle/Derived/controlled文件链定向129 passed（33.50s）。
最终CPU全量1204 passed/5 skipped（226.39s，Python3.12.7，子进程mask=-1、
PATH排除nvcc且断言不可解析；五skip均为Q0 CUDA source编译项）。compileall、
contract37/37、Canonical7、oracle independence及diff-check通过；协调只读审查无阻塞。
未改生产skip，没有本轮CUDA编译/服务器测试。冻结合同、S、Q0、Derived门、runner、
原始evidence均zero diff；生产改动只在B字段投影，不改变公式。
旧A/B 0.2及0.3读取器不变：回归证明旧错误phase字节仍原样读取、不偷偷修复；
历史产物仍按原commit解释，不因新实现追认phase provenance资格。

对既有真实Raw在全新本地诊断目录重分析：S全部记录完全相同，A仅新Canonical
lineage带来的window_id改变，所有边界/身份/数值相同；B仅四目标origin数组修正，
其他字段与五范围外INVALID逐字段不变。旧29输入hash前后一致。沿用明确记录的
本地source-byte诊断适配，不把本次未提交源码的本地计算称服务器版本复验。
Derived仍阻断、UNKNOWN/NOT_ASSESSED不变。测试及私有复核脚本路径见本地handoff。

## 下一动作（取代此前待部署状态）

本次adapter已在服务器c827b61完成离线复验；无需重复部署/导出/采集。
phase修复完成本地审查后，只需新分析commit的窄静态检查及一次已有SQLite离线复验，
不需重复DLL/采集/export或服务器全量测试；部署及执行须先协调审查交付包，不自动执行。
Derived范围问题与此分开：如拟从整bundle资格变更为逐窗口依赖闭合集合资格，
必须明确可排除的范围外记录及跨窗依赖/未知影响的阻断规则，不能直接过滤INVALID。
本轮未作该选择；shared-stream epoch也未被本独立stream构造验证。
未知完整性不改零，不重新要求全capture厂商认证；模型/new-Q0资格仍需后续证据。

历史下一动作（已执行，保留来源）：

完成回归和审查后，只一次部署必要分析adapter。复用现REP/SQLite及sealed输入，
在新版本/新诊断目录重分析；执行commit07625b7与分析commit分开记录。
没有改变producer/native字节，不需重新编译DLL、采集或export；不可覆写原BLOCKED report。
Gate7 PASS，Gate8及新版Q0 NOT_RUN。
