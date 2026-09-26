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

六窗top-level守恒差均0。sync residual是既有有证据的同步return-tail分类，
不是把缺失证据挪入residual；unknown0不代表开销为0、也不独立证明归属正确。
共9条B：4目标B_VALID；5条窗口外warmup/prepare/cleanup保持B_INVALID/
INVOCATION_BOUNDARY_INVALID，不能总括“B全部通过”。现有Derived门检查全部B，
故`DERIVED_BLOCKED_UPSTREAM_NOT_QUALIFIED`，没有Signature。未过滤这5条、未修订D门。
publication中的记账margin仍禁止mechanism claim。若需要per-request Derived选择域，
必须另行明确输入集合，不混入本次adapter修复。

## 下一动作

完成回归和审查后，只一次部署必要分析adapter。复用现REP/SQLite及sealed输入，
在新版本/新诊断目录重分析；执行commit07625b7与分析commit分开记录。
没有改变producer/native字节，不需重新编译DLL、采集或export；不可覆写原BLOCKED report。
Gate7 PASS，Gate8及新版Q0 NOT_RUN。
