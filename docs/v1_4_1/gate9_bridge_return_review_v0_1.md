# Gate9 桥接回传及离线续算审查 0.1

2026-09-29；`G9-BRIDGE-RETURN-REVIEW/0.1`；Engineering 增量审查，不是 Formal 数据。
执行版本 `15b24ec744616754f6fdd437bd333aa8a2059bf1`；修复/离线审查版本为包含本文件的提交。

## 原件与拒绝原因

原 ZIP `gate9_bridge_15b24ec_once.zip`，276954 bytes，SHA256
`4bf17fb1ded2fa6f6d54e041c196d0817703d94132afe375fc114a9ca6c2b5ea`。
本地独立验证 CRC、无重复/越界路径、71项大小/hash、清单恰覆盖其余文件，72个解压文件均与ZIP字节一致。
清单SHA256 `7bd539195a91d462df1bcab46e33b0fb37000fcc24c6f5134fb839d3d84bec93`。
REP SHA256 `6fdf03f6f3d08ba4c329ac28c6a72f21942ae36b0f977e3a627b9b55ad904146`；
SQLite SHA256 `d96a15abe1133a4cf8c12b6a3c3080291f9fb80947504104594eac880428789f`，只读integrity=ok。
本机位置只在忽略的handoff记录，不上传原件。

`DIAGNOSTIC_EVENT` rowid 3/4/6/7，severity=2、source=3、timestampType=2，均关联OTHER_PROCESS PID60888，依次为：

- `Not all NVTX events might have been collected.`
- `No NVTX events collected. Does the process use NVTX?`
- `CUDA profiling might have not been started correctly.`
- `No CUDA events collected. Does the process use CUDA?`

目标PID27224由producer、pass ledger及profiler launch row8共同绑定；完整global PID命名空间一致。
目标实际31条NVTX、595条runtime API、4条kernel、4条memcpy、10条synchronization；诊断自身报告31 NVTX/603 CUDA（计数口径不是全部表相加）。
19条诊断除上述4条外均匹配既有information规则，没有新类型或目标零事件冲突。PID60888无CUDA API/activity或NVTX记录，不据此推断其程序用途。
profile COMPLETE/exit0/无timeout，producer COMPLETE/error=null，tokens=[[0,1],[11,12]]；export仅一次PASS。
服务器CPU原始日志为102 passed。这不是本地执行的目标平台测试。

## 两项实现遗漏与严格边界

1. N1原门只接受INFORMATION_ONLY，未接入[已接受官方解释](gate8_warning_evidence_review_v0_1.md)。
   新`exposedpath-gate9-diagnostic-review/0.1.0`只在受支持Windows/Nsight版本、同namespace非目标进程、完整四消息组合及目标原始NVTX/activity证据匹配时记录独立处置。
   新消息、目标/未知PID、不同namespace、缺实际目标活动、版本/来源hash冲突或与no-events相矛盾的活动继续拒绝。
   原diagnostics和旧classifier的IMPACT_UNBOUNDED记录原样保存；新review注明原始row引用、依据`G8-WARNING-EVIDENCE/0.1`及USER_RELAYED_OFFICIAL_RESPONSE。
   不是重新询证、身份豁免或零丢失认证；旧Gate8入口不改。
2. 越过诊断门后，原桥接将CUPTI stream type与runtime创建flags混用。
   同一SQLite的`ENUM_CUPTI_STREAM_TYPE`明确1=DEFAULT、2=NON_BLOCKING、3=NULL；stream13为2，context1的null stream为7。
   producer实际runtime native_flags=1与此一致而非冲突。仅N1桥接比较改为CUPTI值2；Raw/Canonical数值不改，不改S/A/B公式。
   两个Gate9合成fixture此前也写错编码，随独立反例修正；1/0/3/99均不能作为nonblocking通过。
   本包8个活动全部在stream13，没有默认流活动；不据此授予跨默认流完整B资格，也不改历史S/default-stream分支。

## 新派生结果与独立核验

封存副本独立目录`derived_v0_2`，旧失败报告、原partial、Raw保持不变。
`domain.json` SHA256 `8332c978d68b15805e93c96a1fc0f9bd20de9b0adbe6d29aaa89a6e7db6eb938`；
含独立oracle的`reanalysis_v0_2.json` SHA256 `7c8377f2ad64f4b60785f4c613adf1b52b40aafbb9a176a0ae3ef85fd0149d0c`。
文件链重读验证通过；domain=QUALITY_CHECK_PASSED_NOT_QUALIFICATION，oracle=MATCH_REVIEW_REQUIRED。

14个实际调用唯一绑定同context1/stream13及持有的native handle；两次成功窗前drain、6个共同completion点、内部同步和必要提交均被检查。
独立Raw oracle未改，也不调用被测S/A/B：六个W成员数1/2/4/5/6/8、terminal、hidden/exposed/tail和六窗A全部匹配；第二request保留已完成物理前缀。

| request / phase | T(ns) | Host | CUDA API | device wait | residual | unattributed |
|---|---:|---:|---:|---:|---:|---:|
| 0 / request | 44113254 | 2236008 | 40884574 | 4640 | 988032 | 0 |
| 0 / prefill | 42780596 | 1733740 | 40849812 | 2592 | 194452 | 0 |
| 0 / decode | 1332658 | 502268 | 34762 | 2048 | 793580 | 0 |
| 1 / request | 2265581 | 1073581 | 145718 | 23616 | 1022666 | 0 |
| 1 / prefill | 1329935 | 631453 | 33179 | 13280 | 652023 | 0 |
| 1 / decode | 935646 | 442128 | 112539 | 10336 | 370643 | 0 |

各窗互斥守恒，request每一分量=prefill+decode。微程序warmup=0，这些时长不是模型/稳定性能结果。
显式解释器runtime绑定、trace launch、DLL hash和关键源码身份复核通过；3份关键源码与Git blob字节相同，
复用的`gate8_qualification_token.cu`服务器hash精确匹配该commit LF blob的CRLF checkout，单独记录而非谎称blob字节相同。

## 验证与结论

tests-first：诊断接线正例先复现原DIAGNOSTIC_IMPACT_UNBOUNDED；stream反例先证明旧实现拒绝2却接受1。
本地CPU相关36 passed；G1/旧diagnostic回归24 passed；修改文件compileall、diff-check通过。
没有全量、CUDA、Nsight、模型或服务器操作；未改独立oracle或冻结测量语义。

**本包warning接线阻塞及stream编码遗漏已消除，N1目标桥接离线增量与独立oracle匹配，未发现本包其他实际阻塞。**
仍保留dropped_records_status=UNKNOWN、measurement_validity=NOT_ASSESSED、非Formal，D/Signature不启用。
Gate8 PASS不变；原attempt/receipt/report仍BLOCKED。Gate9总体判定本轮不自动升级：下一项仅将本N1增量与7.97的G1投影资格/既有实物复用完成最终分域退出汇总，不要求重采或新平台资料。
这不是新模型验收、完整新版Q0或信息增益结果；不需服务器部署、export、GUI或采集。
