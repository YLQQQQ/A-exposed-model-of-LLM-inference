# 限定 Engineering：247f4fd 静态回执与下一项资格工作 v0.1

2026-09-27。仅审计和执行规划；不是新amendment，不改准入规则，不授权采集。
执行代码固定 `247f4fd211007b7dfc2ef011043d7ecebdbf6f88`；本文后续文档提交不是服务器执行版本。
依据：engineering-sufficiency/0.1、route-a-execution/0.2，以及研究设计v7.1/协议v2.1 Pre-Pilot。

## 1. 直接核验的服务器静态证据

单一ZIP 4680 bytes，SHA256 `fc129db5a104ce8e052f56512a6bab292bddbd12c670a260f57d98fa2c0b41d3`。
CRC、8个唯一且安全的文件路径、精确文件集合通过。清单SHA256
`fa10caa43c662893f08e3d3af7d43db8f58246fce0e748bb562c483f90bf4ce0`，7项bytes/hash全部匹配。
未解压或改写原件，按BOM读取PowerShell UTF-16日志；本地首次误用UTF-8显示失败不是服务器失败。

原transcript与targeted.log：Python3.11.16，95 passed/42.63s；contract37/37仅内部一致性、
Canonical7模块、oracle静态独立性通过。receipt六步exit0、STATIC_PASS、error=null、
collection_run=false，expected_commit为247f4fd，previous_commit为35b5bff；bundle hash与本地交付一致。
compileall无单独日志文件（静默成功），成功依据是receipt中的exit0，不补造空日志。
transcript含`247f4fd (HEAD)`及show-check输出；完整部署前bundle verify/fetch/checkout控制台
回执属于用户提供，发生于transcript开始之前，不冒称本包包含。最终clean依赖已核对执行段的
终态检查与STATIC_PASS，不冒称包内有独立的完整git状态快照。

这证明目标Python上的确定性接口及静态检查通过，不是新增服务器全量、native编译、
CUDA/Nsight可观测性、新Q0或模型A验收。Gate7 PASS；新Q0/Gate8 NOT_RUN。

## 2. 外PID警告：事实、推断边界与停止点

只读复核已有Qwen canonical SQLite（SHA256
`25e7bd0e79597744f3485c1eb155621e0d93491b034ccb7756dc9f312d5e0145`），不改旧report、不接入新准入：

- producer目标PID50660对应完整globalPid282324910473216。Runtime21468条、Kernel6984条
  均在该globalPid；这只是已观察记录的分布，不证明其它进程没有CUDA工作。
- DIAGNOSTIC_EVENT row3–6、8–11为8条warning，分别关联globalPid282567307689984与
  282570059153408（PID65108/65272）：NVTX可能不完整/无事件、CUDA profiling可能未正确启动/无事件。
- row12说PID65108由profiler启动；其它注入通知不能识别两个进程的可执行文件和完整角色。
  ProcessStreams仅globalPid/filenameId/contentId，不提供可证明的父子关系或依赖排除证书。
- warning的timestampType=2（HostTimestamp）；目标trace时间不能与其原数值直接比较。
  不用“83ms较早”裁掉影响，也不因目标计数非零或PID不同判定局部无害。

处置保持IMPACT_UNBOUNDED。既不能据此宣布目标已丢记录，也不能标OUT_OF_SCOPE。
以后若要限定范围，至少需同次记录绑定进程角色/生命周期，以及该具体诊断是进程局部还是
共享collector故障的可复核依据；“没有其它activity”不是缺采情况下的否定证明。当前材料
不足，不要求重查安装包、PDB、厂商全capture认证，也不为消除warning重复模型采集。
旧Qwen未预声明profile，本来就不能补写后重新验收；即使未来补足解释也不追认。

## 3. 最小受影响资格矩阵

| 必要命题 | 已有证据能证明什么 | 仍需补什么 |
|---|---|---|
| 物理S/B与A公式 | Gate6历史资格、0.2受控trace及f5edc64审计六A/四B；本轮未改算法 | 保留回归，不全重采，不把历史资格授予新profile |
| D1/设备/时钟/多request链 | 旧受控真实链证明其旧构造；247f4fd目标机95项验证新文件接口 | 同次新profile的真实producer/drain/stage/点→Canonical绑定；不能填旧receipt |
| 成功drain前缀与默认流后缀 | 独立手算正反例、两个mode交集测试；旧显式流trace不证明NULL流准入 | 最小受控NULL FIFO的实际trace，逐sync完成、内部sync集合与独立oracle |
| 局部缺口/全局未知拒绝 | 本地与目标机确定性测试已覆盖API有界缺口、缺点/映射/外PID警告拒绝 | 对新受控输入做独立派生故障注入；不必为制造丢失再跑GPU |
| 真实Qwen解释 | 旧trace只诊断：边界/内部sync事实、警告和支持域缺口 | 受影响资格通过后另行授权新attempt；当前不重跑、不发布机制claim |

## 4. 下一项最小动作：主窗口本地准备，不是服务器命令

247f4fd的模型入口已接通，但**没有可直接执行的新profile受控资格入口**：
`gate8_controlled.py`仍为CONTROLLED-D2H-REQUEST/0.2；`gate8_source_probe.py`仍为
SOURCE_DIAGNOSTIC_ONLY，且带旧来源诊断profile。不能把它们改名、补假backend或复用
曾暂停的采样/backtrace profile来冒充本次资格。

下一项仅准备一个明确标为受控构造的资格封套/最小连接器及独立oracle预期，再审查：

1. 复用现有小型kernel→D2H→host-readable构造、真实runner边界/drain/stage观察和新A核验；
   不加载Qwen，不新增指标。受控construction身份与实际模型backend字段分开，不伪造模型配置。
2. 目标为一次最小受控执行：驻留/暖机在窗外，两个顺序request、各两个token，覆盖前缀drain、
   request/prefill/decode及一个已知内部sync。运行前固定操作/顺序/独立期望token和必要活动集合。
   实际时长取新Raw原区间，独立oracle不调用S/A计算函数、不要求GPU实测等于合成ns。
3. 正例验证具体分类而非仅总和：预先命名的活动与sync集合、host-readable结果、互斥窗和
   未知原因逐项吻合；不以任意百分比阈值放行。默认两种mode的条件等价由独立正反例支持，
   不宣称实测识别了进程默认流mode。
4. 缺boundary/correlation、跨身份、未界定warning等反例优先在新独立派生副本注入；保留
   原件hash和fault说明，验证拒绝、不填Host/residual。其它流不等价保留现有独立反例，
   不为未改变的全部Q0类别另起采集。
5. 本地连接器若发现须扩大支持域或修改合同，先明确具体差异；不能伪造execution receipt。
   完成前不生成一个当前版本无法执行的服务器“资格命令”。

**当前无需服务器操作，也无需新部署包。** 本轮不实现连接器、不重复静态测试。
真正执行前再固定实现commit、oracle与最小argv，提供一段命令和单ZIP回传；停止条件为
身份/构造/边界冲突、非预期stream/API/诊断影响不明、采集/导出失败或oracle不符，不自动重试。
回传必须同包包含原REP/SQLite、producer与身份/构造/执行receipt、诊断、派生结果、独立oracle
对照、操作日志和排除自身的hash清单。受控PASS只授予明示影响范围，不自动等于模型/Gate8 PASS。
