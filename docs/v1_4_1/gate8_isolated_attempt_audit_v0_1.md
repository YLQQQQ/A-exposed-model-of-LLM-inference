# 隔离预检 attempt 有界审计 0.1

2026-09-28；Engineering只读审计。执行commit `db9f028b1a7ceac40b9a110bfaacf6d613319638`。
**结论：原attempt保持BLOCKED；停止同配置重采、重复来源记录及本包PID追索路线。**
Gate7历史PASS、限定受控资格保持；Gate8 NOT_RUN，D/Signature关闭，UNKNOWN不改零。

## 1. 原件与可核验对照

新ZIP 26487072 bytes，SHA256 `660B531F45BD768441C13757ADDDC57EE249911E0DB24A7C80F62E69B70BF360`；
清单SHA256 `B6186F0CC8671FCDA96FC441F1E5CE99D12EB83DC8C6A3D8B1EF5735D3E6B4ED`。
本窗口独立验证CRC、路径安全、无重复、70项size/hash和完整覆盖；71个解压文件分析后仍与ZIP逐字节一致。
SQLite只读immutable打开，integrity=ok，SHA256 `2d52d6dbb1253880e0c0a6776b7e65480128c97962bcd7f537182a5612913321`。
REP SHA256 `98eca3d360959b24e48cc764f50e7cdcad172c6c99ad4b45aec7b85d2e0ce675`；未打开REP或运行export。
本地定位及派生脚本在忽略的交接索引；不提交Raw/用户路径。

| 项目 | 旧097f68a attempt | 本次db9f028原件事实 |
|---|---|---|
| target/采集/导出 | target65784 exit0、采集成功、export PASS | target53792 EXITED/0、producer COMPLETE；profile COMPLETE/0/无timeout；一次export PASS/0、0.203s |
| warning | 8条，10988/54228，影响不明 | 4条，52740，影响仍不明；不能用数量变化证明旧根因 |
| target辅助预检 | 原模型入口有Git/nvidia-smi调用路径 | subprocess_origin仅OPEN/CLOSED，scope=ACTIVE_PLATFORM_ADAPTER_CALLS_ONLY；不覆盖第三方/native |
| 新身份链 | 无isolated0.1链 | 新manifest声明0.1；preflight/claim/target/final的run、nonce、hash匹配；final PASS |
| 实际GPU | 已有目标设备观察 | cuda_probe PID53792、logical0、mask3、实际UUID/PCI与preflight physical3归一化一致 |
| 正式A | BLOCKED，空a_records | 同样BLOCKED，ENGINEERING_SCOPE_DIAGNOSTIC_IMPACT_UNBOUNDED，空a_records |

新run=`run-20260928T063642Z-c87ea81e`，wmpc=`wmpc-8a2d01d603f252a5`。
manifest commit/dirty为db9f028/false；runner_source实际hash与manifest均为
`7ed08a068915b8bf765d3ce8a674b470be011b200dc2cfef8cb88eedd90bf94a`。
四个prepared输入hash与preflight匹配。新链证明对应检查路径已执行，不证明恶意TOCTOU不可发生，
也不证明所有预检无缺陷：第4节发现tracked清单解码的独立fail-open问题。
模型本体未在本地重新哈希；不把服务器模型检查与本地文件审计混称。

## 2. PID52740与四类warning：证据路线停止

`DIAGNOSTIC_EVENT` row2/3/5/6均severity2/source3/timestampType2(HostTimestamp)，
globalPid=282359807082496；分别为潜在NVTX不完整、无NVTX、CUDA profiling可能未正确启动、无CUDA。
row10仅说明该对象的common injection初始化成功。`ThreadNames`为NSys通讯/redirect/服务线程，
`PROFILER_OVERHEAD`八行是TLS/Chunk allocation、线程名服务及plugin加载；**都不是宿主程序名**。
`ProcessStreams`只有目标53792和配置对象；无52740的exe、parent、birth/exit实例或用途。
target claim所报parent_pid=14120也不能据此认领52740。
警告时间属于HostTimestamp，不能直接与request的TargetTimestamp比较后称“窗外无影响”。
目标row4/7报告13 NVTX和28805 CUDA事件，只证明收到活动，不证明警告隔离或完整性。

重新对照已封存安装资料的UserGuide（process-tree及flush）、ReleaseNotes（条件性teardown）、
AnalysisGuide（CPU lost events）、export schema notes，以及实际SQLite全部表名/相关字段。
来源hash及定位沿用[7.79有界审查第3节](gate8_process_origin_feasibility_v0_1.md)。
没有affected-process集合、受影响区间或共享collector故障传播说明，不能建立排他影响范围。
UserGuide的`--process-scope=main`仅Embedded Edition；不能据此给当前Windows Workstation安排“只采主进程”。
`--cuda-trace-scope=process-tree`也不等于single-process。没有发现被adapter漏读的可用范围字段。
因此停止本包同类SQL/GUI/来源记录调查；不声称工具绝不支持，只说当前证据不能决定。

## 3. 同包反事实检查（不是可信A，不是验收）

在独立v0.1派生目录复用封存Canonical/projection及物理S容器；仅诊断调用不应用warning门，
原engineering_a/Raw/报告不改。默认流后缀恢复仍实际计算，未用历史结果替代。
沿用已验证的窗外API区间排除及纯函数缓存加速本地候选计算；不是生产代码变更或独立Q0 oracle。

- 三锚点：NVTX row1/2/3；同一NSYS_TRACE_RELATIVE_NS。
  full_request `[30163654309,30360741452)`；prefill到`30270700124`，decode从此到末点。
- 窗外drain：runtime row17431 `cudaDeviceSynchronize_v3020`，returnValue0，correlation61548；
  sync row346 CONTEXT_SYNC，API end30162803099早于request start；3838个观察到的前缀activity。
- 窗内三个stream sync：runtime17441/19143/20737、sync347/348/349，均return0，
  correlations61655/90867/116232，context1/stream7。包含内部同步，不仅两token边界同步。
- LEGACY/PER_THREAD两模式必要集合分别8/1906/3498项，逐ID一致；三窗口A候选也逐字段一致。
  此为批准支持域下的条件等价，不是已实证真实默认流模式或warning无影响。

以下全部为反事实ns值，禁止作为可信模型归属或性能结论：

| 窗口 | duration | Host | CUDA API | device wait | sync residual | unattributed |
|---|---:|---:|---:|---:|---:|---:|
| request | 197087143 | 112375976 | 79836669 | 11520 | 132445 | 4730533 |
| prefill | 107045815 | 59051351 | 45496161 | 11520 | 103732 | 2383051 |
| decode | 90041328 | 53324625 | 34340508 | 0 | 28713 | 2347482 |

互斥/守恒检查0误差。6171条局部gap为`cuKernelGetFunction`与`cudaStreamIsCapturing_v10000`，
union unattributed=4730533ns，约4.731ms/2.40%；不转Host/residual，不为降比例改分类。
旧包相应为约4.988ms/2.78%，这不是受控性能比较或warning安全证据。
本次未发现warning之外新的request边界/drain/后缀计算阻塞；预检解码缺陷另列。

## 4. GBK错误不是A拒绝；最小修复设计与7.83本地实施

`14_collect.log`/transcript的栈是Python `subprocess._readerthread -> fh.read()`，
不是对已存Nsight日志调用read_text；profile stdout/stderr直接写文件，export也不经此text管道。
可定位的缺陷路径为`gate8_isolated_preflight.seal`的`git ls-files --cached -z`
→ `platform_adapter.git/query_tool/run_tool(text=True)` → 默认GBK reader。
从固定db9f028 Git tree重建的同序NUL文件名串，精确复现位置4195的0xae，
对应中文协议文件名。真实CPU子进程强制GBK重现reader异常，同时returncode=0、stdout=None；
`query_tool`的`(stdout or '').strip()`把它变空串，使`tracked <= inventory.keys()`可空集通过。
服务器未保存该命令原始字节，不能声称直接恢复了丢失stdout；但位置/字节/内容与代码链完整复现。

独立核对本次封存`tree_hashes`确实有固定commit全部486个tracked路径，无缺项。
这补证的是路径集合覆盖，不替代运行时检查、不冒称本地复算服务器486份内容，不追认attempt。

后续确有执行必要时的最小修复：只为这类Git NUL清单提供二进制查询；原样落盘stdout/stderr、
argv用途/exit/byte数/hash后，再由主线程严格UTF-8解码和NUL结构校验。
非零退出、stdout非bytes/缺失、非法编码、非终止NUL、重复/越界路径、意外空tracked清单均拒绝；
真正允许为空的ignored清单与必须非空的tracked清单分开。展示可另做escaped view，不用errors=ignore/replace改变身份输入。
不全局改变所有工具编码或把UTF-8假设强加给本地化stderr。
CPU字节设计探针已验证中文NUL stdout、非法UTF-8 stderr `ffae`及exit7均原样保留；
后续生产回归须覆盖上述每个负例及“缺一个tracked文件必须拒绝”的真实seal接线。
7.82审计时只形成设计；7.83经用户批准完成上述本地修复，并与本审计同一提交。
只改`gate8_isolated_preflight`的两条NUL清单查询，沿用adapter的`text=False`，
原始stdout/stderr `.bin`及查询exit/hash/错误记录留在新执行输出目录，缺失仍保持null而非空字节。
生产receipt/schema与测量语义不变；修复不赋予旧receipt新资格。
26项新增回归先在旧实现上失败；修复后直接相关5文件100 passed（本地Windows/Python3.12.7），
改动Python compileall及diff-check通过。真实临时Git仓库覆盖中文路径，独立CPU子进程覆盖二进制管道；
外部GPU身份是明确替身，没有真实CUDA/Nsight。无部署包或服务器执行；不解决warning。

## 5. 协调裁决与Gate8停点（7.83）

**厂商询证继续暂停，不发送；不重采，不再追索本次未知PID。**
7.82曾提出窄询证建议，协调窗口未采用；本节记录裁决，不把旧建议留作当前下一指令。
本地Git读取修复关闭后停止追加工程。没有新的trace范围、质量判据或研究范围amendment。

现有证据仍能支持Engineering执行/产物可读性、已观察身份与completion标记一致性、
导出及schema接线检查；可以复用限定受控资格和独立反例做本地回归，并保留明确隔离的候选计算。
不能据此授予真实Qwen窗口可信A、模型资格、完整Gate8通过，或相对常规指标的信息增益claim。
“拿到trace/算出数值”与“支持归属结论”分开；不能靠重复同配置让后者自然成立。

资格链确有过度工程化部分：反复来源记录、包装/交接层和不能关闭警告的采集迭代，
其边际研究价值已不足。简化的是工作组织与扩展投入，不是删除独立oracle、身份/边界或拒绝反例。
当前收敛为一个预检入口、一个准入结论、按改动影响复用既有测试/资格；不全重验、不再加监控，
不以多做Gate/receipt替代研究进展。在现有约束不变且无新证据时，应明确暂停真实模型资格链，
而非继续承诺下一轮工程能解除阻塞。历史代码/数据不删、不重标记。
