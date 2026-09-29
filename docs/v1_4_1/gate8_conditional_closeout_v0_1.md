# Gate8 条件性集中收尾 0.1

> 最新证据裁决：[7.89 warning审查](gate8_warning_evidence_review_v0_1.md)；原BLOCKED和本报告历史条件状态不回写。

> 历史证据审计，正文按原版本保留。当前工程退出以[G8-ENGINEERING-EXIT/0.1](gate8_engineering_exit_amendment_v0_1.md)为准；当前进度只见[research_progress](research_progress.md)。本版NOT_RUN/BLOCKED与旧数值不回写，non-submit修正见[7.87报告](gate8_non_submit_api_review_v0_1.md)。

2026-09-28，Engineering，research_progress 7.86。执行/分析代码均固定为
`36ed952b57f20651dd290fc484d7b21fc7dbbfc4`；本报告的提交是文档收尾身份，不是执行身份。
依据[条件配对合同0.1](gate8_conditional_pair_v0_1.md)及[路线A退出范围0.2](gate8_route_a_execution_v0_2.md)。
用户明确批准的假设仅为四条指定外进程warning不影响目标request；不是作用域证明。
正式报告仍BLOCKED，Gate7历史PASS、限定受控资格保持，标准Gate8仍NOT_RUN。

## 封存与本地审计

原件逻辑名`pair_36ed952b57f2_pair.zip`，26583909 bytes，SHA256
`3c90764357547cfb28de3c16bc624664e36d58565dfa4dcb02f1063e0294940f`。
顶层清单SHA256 `b1d30c1ab77304fe885680b4b4c813bdb2616c58bd88e164657420e28a7bd12b`。
本地独立核验CRC、146文件、安全路径/无重复、顶层145项精确覆盖及嵌套清单
19/124/18项大小/hash；原static ZIP内容逐字节一致。未操作服务器或运行Nsight。
派生根为忽略的`.local/diagnostics/gate8_pair_closeout_v0_1/`；`sealed_copy`保持原字节，
审计脚本/JSON、`conditional`新目录均与原件分离。原collection/formal报告不改。

复现入口为下列固定代码CLI（`$Pass1`指封存副本的`pair/pass1`，`$Derived`必须尚不存在）：

```powershell
python -m exposedpath_v141.gate8_warning_assumption --formal-result "$Pass1/analyzed/engineering_a.json" --input-receipt "$Pass1/input_receipt.json" --execution-receipt "$Pass1/diagnostic/engineering_execution.json" --output-dir "$Derived" --assumption FOUR_OTHER_PROCESS_WARNINGS_NO_TARGET_IMPACT/0.1
```

没有猴补丁、快速替代分析器或关闭其他检查；正式来源先按原逻辑重算并精确比对，再生成独立派生。
本地审计脚本仅检查归档/绑定、直接SQLite行及区间union；不写封存输入。

生产条件入口exit0，结果`CONDITIONAL_A_ONLY_NOT_ACCEPTED`，新`conditional_a.json`
926646005 bytes，SHA256 `bf17787e6647d36b0fc15ccb87deb9519b384ebab0c4fd2dfa691f793a6f2e4a`。
原formal SHA256 `83e24fe704b68db7a3b352b827c15413c52dda47a02fe52c591129b1a0de9eb4`保持。
最终`final_audit.json`确认三窗逐分量匹配独立区间核算、两模式必要成员逐项相等，
顶层/子类守恒误差、overlap、uncovered、越窗均0；146份封存副本仍与原ZIP逐字节一致。
审计脚本首次误用守恒字段名产生KeyError，改为实际schema的`top_level_conservation_error_ns`等字段后通过；
这不是analyzer失败，未改源证据或生产代码。局部原因`CUDA_API_SEMANTICS_UNRESOLVED`保留。
完整派生JSON较大（含物理S/B保留记录），只存本地；该存储成本已记录，不上传Git、不临时新增压缩开发或验收阈值。

REP 728304 bytes，SHA256 `ab08d6a757f1c077d06de5964eb7965f45de55e82c98d567f2e22782609ba1a4`；
SQLite 1880064 bytes，SHA256 `3cd28252abe8be5b84f00a0b43aa299a777fd362d28dae36007beba3a7125e49`。
一次export exit0、0.204s、无timeout；attempt/canonical哈希一致。本地immutable只读integrity=ok，
不等于零丢失。服务器定向日志94 passed/42.51s，CPU静态回执通过；本轮没有重跑测试。

## 实际身份与输入链

两pass Git查询exit0，stdout各23833 bytes、strict UTF-8、终止NUL、496个唯一路径；
与本地固定执行commit的`git ls-tree -r -z`集合完全一致，且tree_hashes恰好覆盖496项。
中文路径未丢失，stderr为真实空bytes而非读取失败。ignored清单与excluded一致。
seal/target claim/final均绑定本次输入hash、run、独立nonce；目标回执等于claim，final hash复核通过。
这是实际运行产物覆盖，不仅是CPU测试。服务器完整源码未全部传回，不能称本地重hash了服务器496文件；
内容一致性依据执行前/目标/执行后实际快照检查及clean Git身份；传回runner字节单独与seal核对。

pass0 run=`run-20260928T112530Z-d7a4f74b`、PID65180；
pass1 run=`run-20260928T112619Z-3ba9c226`、PID60060，两入口exit0、producer COMPLETE、preflight final PASS。
模型Qwen2.5-1.5B-Instruct，32/2 tokens、batch1、fp16、greedy、eager、SDPA/use_cache，warmup1/repeat1。
模型清单SHA256 `72465c906baeb0cfa4fd94d21ef6c69c1cd8046bb68c61a94c02a1580d2541f9`；
prompt文件SHA256 `4dffd0ddcbd3185c656ae4a27efaf5aab302febba6ead5df4d37d903a2091920`。
本地未复算模型本体；revision未知保留。输出数量/EOS通过，不声称输出token值序列逐字节一致。
设备physical3/logical0/trace0/inventory2，经UUID/PCI与source记录关联而不是编号相等推断。
配置实际值、显式解释器snapshot、输入/代码和设备两pass一致；无排除、early EOS或重试。

## 窗口、同步与条件结果

Raw NVTX row1/2/3的共同trace点为24082591723、24172229069、24246851635 ns。
成功窗外drain Runtime17431、corr61548、return0，结束24081963566 < request开始。
窗内Runtime17441/19143/20737分别关联sync347/348/349，corr61655/90867/116232，均return0、context1/stream7/device0。
独立原记录检查与提交关联得到3838项已完成前缀、3498项后缀，必要集合大小8/1906/3498。
模型加载、warmup和drain在窗口外；内部同步及token同步均保留，不将窗外physical S/B invalid当作request失败。

下列是**依赖warning假设的条件性记账**，单位ns；不是可信模型资格或正式研究结果：

| 窗口 | T | Host path | CUDA API | Device wait | Sync residual | Unattributed |
|---|---:|---:|---:|---:|---:|---:|
| request | 164259912 | 100941487 | 58847854 | 11552 | 618868 | 3840151 |
| prefill | 89637346 | 52515342 | 34407151 | 11552 | 590496 | 2112805 |
| decode | 74622566 | 48426145 | 24440703 | 0 | 28372 | 1727346 |

6171条局部API分类gap为`cuKernelGetFunction`、`cudaStreamIsCapturing_v10000`；
request占2.33785%，未转Host/residual，未为降低unknown改分类。低unknown不证明warning无影响。
独立区间union核算与必要成员列表用作本包核查，不替代已获限定受控资格的独立oracle。
默认流LEGACY/PTDS等价仍是受支持后缀的条件等价，不声称实测全进程默认流模式。
无用户并发/显式IPC-event依赖/未记录incoming依赖为预声明支持域假设，不冒称Raw已证明一切不存在。

## 配对观察与限制

host-readable边界计时（不是上述trace-marker A时钟）经本地重算，与服务器pair_observation完全一致：

| 窗口 | pass0 ns | pass1 ns | 差值 ns | 相对差 |
|---|---:|---:|---:|---:|
| request | 117197100 | 164476100 | 47279000 | 40.3414% |
| prefill | 60721200 | 89486800 | 28765600 | 47.3732% |
| decode | 56475900 | 74989300 | 18513400 | 32.7811% |

三次host-observed到before-marker延迟528700/610300/320000 ns，明确非零；
trace request与host request相差-216188 ns，不混用两种窗口或时钟。
一次顺序配对包含profile/插桩与运行波动，不能识别纯profiler因果开销、稳定性或冻结Pilot阈值。
存储、失败历史、一次成功执行及排除已记录；不据此给出可靠性概率。

## 逐项退出与下一步

1. EP-G8-01/02身份、输入驻留、warmup/drain与D1三窗：本次实际证据覆盖；支持域假设显式保留。
2. 必要blocking API/correlation/后缀与默认流条件等价：仅在四warning无影响假设下成立；正式准入仍拒绝。
3. 受影响资格：复用[限定资格覆盖](gate8_bounded_qualification_review_v0_1.md)真实正例/独立负例与历史稳定Q0；
   后续Git/入口/配对/假设隔离改动由定向CPU与本次真实接线覆盖，不授完整新版Q0或模型资格。
4. EP-G8-03三窗口A、局部unknown、单次开销/存储/排除：条件性完成，不新增阈值或重复要求。
5. EP-G8-04封存、lineage和限制报告：本报告及本地审计索引完成；不是标准Gate8 PASS closeout。

四条指定warning为DIAGNOSTIC_EVENT row3/4/6/7、OTHER_PROCESS PID64488。
仅按`FOUR_OTHER_PROCESS_WARNINGS_NO_TARGET_IMPACT/0.1`隔离；PID角色/共享故障传播未证明。
保留dropped_records_status=UNKNOWN、measurement_validity=NOT_ASSESSED、trusted_a=false、
scope_proven=false；D/Signature关闭。厂商答复不是本轮工作的前置，也不是自动验收。
**已批准的限定条件性范围内，其余退出条件已完成，仅warning作用域假设待决；未发现另一个必要阻塞。**
这不消除既有支持域假设、局部unknown和单次配对限制，也不等于完整新版Q0、信息增益或Formal证据。
在批准的限定范围内，不增加服务器批次或同配置重采；下一步仅协调审阅条件性报告与该未证假设，
标准Gate8是否具备升级依据另行裁决，不能用本报告追认旧BLOCKED。
