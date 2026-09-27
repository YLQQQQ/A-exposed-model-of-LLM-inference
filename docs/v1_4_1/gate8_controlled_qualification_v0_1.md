# Engineering NULL FIFO 受控资格连接器 v0.1

2026-09-27；执行依据为 engineering-sufficiency/0.1 和 qualification-next/0.1。
这是已批准支持域的受控构造实现，不是新测量语义、模型资格或自动Gate判定。

## 固定构造与文件合同

新 construction `NULL-FIFO-D2H/0.1.0`；新封套
`exposedpath-controlled-qualification/0.1.0`，执行声明
`exposedpath-engineering-controlled-execution/0.1.0`，独立oracle
`exposedpath-qualification-oracle/0.1.0`。旧controlled入口、物理S/B与Q0不变。

入口 `python -m exposedpath_v141.gate8_qualification`：

- `prepare --output NEW --preflight FILE --library DLL --commit SHA --run-id ID`：
  clean commit、mask/GPU、native/source字节、固定操作/期望token写入plan；不加载DLL。
- `collect --plan PLAN --output NEW --nsys ABSOLUTE_EXE --execute-controlled`：
  精确目标build检查；一次cuda,nvtx collection→封存producer校验→一次export→Raw oracle→A对照。
  `run`仅供collector子进程，仍强制显式执行flag；不是普通测试自动入口。
- 所有目录拒绝覆盖。输入receipt保留Raw/export、manifest/prompt/source、pass/host/drain/stage
  hash链；执行receipt再绑定原plan。失败目录保留，不发布qualification成功文件。

DLL独立编译自 `scripts/gate8_qualification_token.cu`，不复用旧DLL冒充。
编译固定CUDA12.4、MSVC14.38、`--default-stream legacy`、`-arch=sm_89`；
DLL导出construction供加载前校验。CPU测试不编译或加载它。
分配、库初始化和一个同构token0暖机均在request窗外；不加载模型。

两个顺序request：controlled-0/repeat0输出11、12；controlled-1/repeat1输出21、22。
每次先真实cudaDeviceSynchronize，再request-start point；固定操作为：

1. kernel(token1) → internal stream sync → 4-byte D2H → token stream sync → host read → first-ready point。
2. kernel(token2) → 4-byte D2H → token stream sync → host read → last-ready point。

三个窗口使用同一trace时钟的start/first/last点，公式不变；cleanup在last点后。
每request必要活动为2 kernel+2 D2H，三次stream sync的后缀必要集合分别是
`{K1}`、`{K1,C1}`、`{K1,C1,K2,C2}`，绝不是按时间重叠推断依赖。
前request与暖机仍保留原始物理记录，drain只界定A后缀，不截断物理W/B。

## 独立oracle与准入

oracle只用标准库读取原SQLite/producer：逐操作NVTX→成功API→correlation→物理sync/activity，
并核验drain、NULL stream/context、GPU（共享身份adapter再次验证）、PID/thread、三个点、
host read值及request身份。syncType按导出的枚举名解释，不硬编码合成fixture编号。
Raw table/rowid是预期集合来源；与Canonical record identity逐项对应，比较LEGACY/PTDS
两份条件后缀集合和六个窗口的五类A值。oracle不调用S/A，也不复制通用analyzer算法。

该串行构造的独立算术：非重叠提交API裁窗长度为A_api；必要活动与sync API的交集长度
为A_wait；sync其余部分为A_residual；有界未分类API原区间为A_unattributed；剩余为Host。
前提是操作、依赖集合、区间不重叠和来源核对已通过；不是仅凭五类和闭合证明正确。
手算例 `[0,100)`：API `[5,10),[70,75)`，sync `[30,60)`，必要活动 `[20,45)`，
预期 `(Host,API,Wait,Residual,Unknown)=(60,10,15,15,0)`；加入5ns互斥局部缺口后
Host减5、Unknown加5。实机使用实测Raw区间，不要求等于合成时间。

可核验事实：源码/构建/操作顺序、成功返回、readback、Raw映射、drain及已观察集合。
支持域假设：无用户并发、无显式IPC/event依赖、无未记录incoming依赖，单实际NULL FIFO。
源码意图/无额外行不等于工具全量完备认证；默认流两mode条件等价也不是实测mode证书。
没有宣称零丢失，`dropped_records_status=UNKNOWN`、`measurement_validity=NOT_ASSESSED`。

缺点/correlation/drain、身份冲突、额外作用/stream、未知warning（含外PID）拒绝。
仅既有两API成功且无activity/sync冲突、可界定的分类缺口可保留unattributed；不填Host/residual。
局部正例、缺点/映射/身份/warning/物理drain反例均使用新派生合成文件，旧Qwen不重判。

## 一次目标机执行与停止

交付的本地整段脚本固定执行commit及从247f4fd的单一bundle；机器路径只在忽略的`.local/`。
不追随main；服务器固定checkout部署后做定向CPU检查、精确工具/GPU身份核验和新DLL构建。
新run位于 `$ServerRoot/evidence/gate8/<run>`；操作日志/原始/派生同包可追溯。
无模型、无第二platform、无扫描，最多一次受控collection和一次export；超时不重试。

成功仅为 `CONTROLLED_SCOPE_MATCH` 候选：须回传原REP/SQLite、plan、source/DLL/build日志、
producer全部文件、collection/export receipt与stdout/stderr、Canonical/projection/诊断、
Engineering A及oracle对照。收到完整ZIP后再审计授予的具体资格范围；不自动Gate8 PASS。
失败同样保留并回传；timeout且子进程状态UNKNOWN时先停止并人工确认写入停止，不按名称kill。
单ZIP附排除自身的精确hash清单；不重复export/覆盖旧run。D/Signature关闭。
Gate7历史PASS、新Q0/Gate8 NOT_RUN；真实模型后续必须另行授权。
