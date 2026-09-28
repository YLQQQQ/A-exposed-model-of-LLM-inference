# Qwen model-run失败审计与持久化诊断 0.1

2026-09-28。Engineering；原attempt BLOCKED；限定受控资格不变，Gate8 NOT_RUN。

## 不变输入与已证明事实

ZIP `qwen_a_only_20260928T024935Z_66b253da03b1494e974bc444b95520bb.zip`：32187 bytes，
SHA256 `603d650baa40f3afc7b80aa069072cecdd125194c6322ac0c911dc9c0e4683d7`。
本轮直接只读核验CRC、唯一安全路径及27项清单hash/size；未解压/打开REP至Nsight，未export。
原报告：0ed0454 clean；profile launcher PID61632、16.75秒、exit1、无timeout。
REP存在（102635 bytes），外层stderr为空，stdout仅Nsight生成报告信息，没有diagnostic目录。
此前CPU isolated import日志显示torch2.6.0+cu124/CUDA12.4/transformers5.17.0；prepare完成。
这些不证明目标模型启动成功，Nsight exit1不能单独解释为模型exit1或PATH故障。

## 启动链及检查顺序

记录argv是明确base Python `-I -S -c` bootstrap→target_python.main→model-run→
gate8_diagnostic.main→run_diagnostic。目录创建前依次可能失败于：
runner import；project_root/output检查；manifest读取/profile声明；target snapshot比较；
模型内容清单重hash；pre-model Git/GPU身份；固定workload/prompt/runner源码hash。
之后才创建diagnostic目录，进行目标CUDA probe和model setup。没有目录只说明未留下此阶段产物，
不能仅据耗时推断模型已执行。

对REP原字节的有界搜索找到`RUNTIME_ENVIRONMENT`（零基字节偏移57998），邻近压缩片段含
`runtime=current(manifest[...])`、snapshot比较和`return model()`，还含Nsight session内部
`streams/stdout_...log`路径片段。这支持“目标输出可能被REP内部保存而未转发”的解释；
不是已完整解析的ProcessStreams/目标stderr记录，不冒称恢复了完整traceback或PID关联。
不从部分压缩字符串推断精确PATH/sys.path等差异；没有官方解码输出或目标snapshot差异记录。
**最深可定位线索是runtime snapshot guard，底层差异字段仍未证明。**

## 最小修复（不改变验收）

target_python在model-run派发前，使用已传入output位置创建独立兄弟目录
`diagnostic-entry`（禁止覆盖），先保存started.json，再导入模型入口。版本
`exposedpath-target-entry/0.1.0`记录实际PID/parent/executable/argv及环境摘要。
Python stdout/stderr独立文件不依赖Nsight转发；退出时保存exit.json和原异常类型、消息、
完整traceback，原异常仍抛出。runtime snapshot不相等仍原样拒绝，只附加具体差异字段。
不记录原始PATH值，只使用既有PATH hash；私有路径/traceback仅在本地证据中，不入Git。

STARTED但无exit只代表未闭合；无法保证native crash/强杀/磁盘损坏可写出最终记录。
直接OS fd写入不受Python redirect完全覆盖。解释器启动前或bootstrap导入本模块之前的失败、
没有合法output参数、入口目录创建失败也不能由该记录器捕获；不能把无记录当通过。
写退出记录失败时：原异常优先保留，原本成功则必须非零退出，不静默成功。

定向验证：四文件50 passed/21.57s；新增3项先失败、IO失败补充反例再经历red/green。
真实隔离CPU子进程因缺必需参数exit2，exit.json保留SystemExit/traceback且runner_imported=false；
独立sentinel异常验证stdout/原始异常/PID，snapshot差异与写盘失败验证不放宽门、不假成功。
compileall、diff-check通过。本轮不跑全量、不加载模型、不调用GPU或真实Nsight。

## 最小下一步与停止点

### 7.74 CPU复现补充（优先于下方7.73建议）

本地Python3.12.7真实base解释器 -I/-S：snapshot→模型入口→runner逐阶段比较。
入口导入scripts.gate7_smoke_validation时重复插入仓库路径，是唯一变化字段sys_path；
runner导入无额外变化，PATH摘要及所有其余既有字段相同。修复后各阶段差异为空，
torch.cuda._initialized=false。未调用模型构造、CUDA API、Nsight。
该结果确定本地可复现缺陷，不证明旧服务器失败的唯一字段；服务器3.11与包版本差异仍需
后续目标平台CPU回归验证，但无需为此安排重采或新增补证入口。

回归先失败于同一runtime guard；最小修复只让直接脚本执行初始化repo路径。
保持expected probe不变，current全字段精确比较、executable/hash/site/environment/PID等门不变。
独立重复路径反例仍拒绝；外部cwd直接CLI --help通过。六文件83 passed，compileall和diff-check通过。
本地前后逐字段记录位于忽略的诊断目录；不上传机器路径。单一bundle包含7.73与7.74，
仅供协调窗口审查，不再建议单独部署日志补丁。无新的服务器操作要求，无Gate判定变化。

先审查此补丁、CPU失败验证及已有REP线索；不重新运行旧REP、不export、不重采来拿错误。
必要部署仅该入口诊断增量和定向CPU测试，不需修改runner/manifest验收或warning门。
部署静态复验可运行target_entry/target_python测试，CUDA_VISIBLE_DEVICES=-1；本轮不执行服务器。
本补丁不修复未知环境差异；不允许恢复旧Qwen采集命令直到协调窗口审查并另行决定诊断执行范围。
若后续确需重现，应先限定在模型前身份检查并保证入口持久化；不得直接跑完整模型/profile。
任何新执行需另行授权。既有Raw/报告和旧attempt不改，不发新模型成功claim。
