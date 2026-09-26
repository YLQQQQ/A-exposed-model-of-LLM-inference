# Controlled build audit 0.1 — 2026-09-26

Engineering，仅本地只读审计；未执行GPU/Nsight。执行候选固定
`7f61102e1313d298c64da44487373675e33b8fa5`，parent
`24f58f8b9864ab3ed4380986a7120506777e97e9`。后续文档commit不是执行commit。

## 直接取得的证据

传回两个原目录：`gate8_controlled_uuid_static_20260926T035323Z_ace0012083bf42418dc28cdb0cb4c210`
与`gate8_controlled_uuid_build_d78ba36f01524d2a9a8df71ba5a50877`。
五个文件为transcript、build_receipt、DLL、LIB、EXP；机器位置在本地忽略handoff。

| 原件 | 本地核验 |
|---|---|
| transcript.txt | SHA256 `9cf22e3e0eee428acb77b6abfcdafd7b598944bdb59046914e1a74504c22b321` |
| build_receipt.json | SHA256 `50df7d469c3f6869d20558da40e50bf21b9bfa7ddbfb1281ce4feb05ebfffe15` |
| gate8_controlled_token.dll | 305152 bytes；SHA256 `1f0ce44a3f1ebe95cc6c5fa7132097d4916c836368bdbf68ac54b9acc14546a6`，与receipt一致 |
| native source身份 | receipt为 `b67ea74876ab116a844f7ba1d6a2fc285b262807184158b3faf25979a1d60d4e`，恰等于7f61102中对应Git blob的CRLF表示 |

源码不是此次传回的五文件之一。独立从Git读取的LF blob与本地文件SHA256均为
`3fdb62ff9f6ec8272e879fe8412281da381cf175fc43f2a067a667bc304a9b17`。
只在内存构造CRLF字节做哈希比对，未改源码、receipt或Raw；这是已说明的checkout
换行表示差异，不声称两份源码原字节相同。后续归档应保留服务器native源码原字节。
在LF checkout重新执行file-proof会遇到严格source hash拒绝，不应改旧hash绕过；
当前后处理草案在原服务器checkout执行，再传回派生供本地只读审计。

日志确认VS2022 17.8.6、MSVC14.38.33130/cl19.38.33135.0 x64、nvcc12.4.131、
repo Python3.11.16；30 passed/54.20s、contract37/37、Canonical7、oracle PASS。
native编译产生DLL，receipt为STATIC_AND_BUILD_COMPLETE/TARGETED_30_AND_NATIVE_BUILD。
完成脚本在receipt生成前检查HEAD/parent及clean；本地复核该脚本控制流与日志中的HEAD一致，
不把这描述为本地直接执行服务器Git查询。compileall由fail-closed脚本继续到终点证明，
没有额外全量成绩；1165/1属于24f58f8的上一回执，skip原因仍未知。

日志可见两个compatibility marker长度0；格式化输出没有完整展示其hash，不能声称本地
复算过marker字节。它们未被初始化流程执行/修改；本次实际编译成功已验证工具链路径。
终点为STATIC_AND_BUILD_ONLY，mask恢复3，无DLL加载/CUDA程序运行。

## 决定与下一阶段边界

**窄受控采集静态前置已通过审查，可提交用户授权；未执行，不是新Q0或Gate8 PASS。**
现有capture草案固定7f61102；仍检查HEAD/clean、build/DLL/source identity、
Nsight2026.2.1.210、目标GPU/driver/mask/order；任一变化停止，不自动重建或改profile。
采集只限CONTROLLED-D2H-REQUEST/0.1.0两个request、独立warmup/streams，非模型，
不做性能对照；人工300秒deadline，超时Ctrl+C保全现场、无retry/自动export或按名kill。
取得完整REP、producer/execution/collection及环境记录后停止，另行审查后处理。

尚待真实验证：CUDA初始化/UUID、D1标记、必需API记录、依赖scope与独立S/B对照。
GetLastError未分类及模型跨request epoch未决限制不变；不把构建成功升级为低unknown
正例、新版Q0资格或模型就绪。Gate7历史PASS；Gate8 NOT_RUN。

后续协调窗口回传一次启动前失败：Get-Command nsys.exe未解析到工具，发生在
RunRoot创建及profile之前；不是采集attempt，不据此判方法失败或采集成功。
协调窗口将用此前已知工具绝对位置核验版本，只在当前进程临时调整PATH并在结束恢复；
不改系统PATH或正在执行的已校验脚本。本窗口没有执行该操作，后续结果待回执。
