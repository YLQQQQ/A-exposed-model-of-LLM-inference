# Controlled capture receipt audit 0.1 — 2026-09-26

本地直接审计17个原件；不解析REP、不执行export/GPU，不授Q0/Gate8资格。
固定执行commit `7f61102e1313d298c64da44487373675e33b8fa5`；
run `controlled_20260926T040859Z_48bf088f634b453fb2070eecda6c6c39`。

## 已核验事实

- REP：82711 bytes，SHA256 `10be1d6a92de0f223e622c7f8ad5e026de192eb34811e0ca2b31efe670571106`，匹配collection receipt。
- collection receipt SHA256 `60bfbaa53d3461956a705c361c2135043118767093bf9de72a327987fd944033`。
- plan SHA256 `18c620ce3be61af48b8aced4a744c64ba2d650d5bcdd3c7298a7924ddd786921`；execution SHA256 `c07a5a17cf86f680ddd5e66138f124cf02da35004d2bd85c4159d165bb093c8a`。
- collection外层exit0；execution自报exit0，status/init/warmup/cleanup均COMPLETE、errors空；PID61680与probe/ledger一致。两种exit证据不混称。
- producer/controlled receipts为COMPLETE；8项封存文件入口的size/hash及manifest/prompt/source/plan/execution绑定通过。
- 两request/repeat各2token，实际值11/12及21/22、无early EOS；expected/observed boundary ID一致。这是host ledger完整，不是已验证trace时钟的completion窗口。
- physical3/logical0、UUID/PCI、PCI_BUS_ID/mask3在manifest/preflight/实际probe间一致。
- collection为精确19项argv：cuda,nvtx、sample none、cpuctxsw none、memory false、process-tree、isr false，无额外profile开关；Python/plan/output与execution原始路径绑定。
- native、producer、CLI的报告源码hash分别与7f61102 Git blob的CRLF表示一致；producer源码副本有原字节。native DLL与此前直接审计build receipt哈希一致。
- 全17文件审计前后hash不变。没有把复制或重新命名升级为新数据资格。

## 结论和下一步

`CAPTURE_RECEIPTS_CHECKED_NOT_TRACE_ACCEPTANCE`：可以审查并授权该REP的有界离线后处理，
不需要重新采集。采集成功不保证必需API/physical sync/trace marker都已观测。
S/W(s)/terminal、B独立oracle、A/unattributed、trace diagnostics均待实际SQLite检查。
Gate7 PASS；Gate8/Q0仍NOT_RUN；不是模型工作负载结果。

后处理草案固定原服务器7f61102 checkout与工具绝对路径；新建唯一diagnostics目录，
逐字节保留17项输入副本与server source bytes，原采集目录只读不补写。
原因：现有input receipt要求所有artifact处在receipt根内；在新根复制小型输入，
不使用越界路径，也不在本机LF源码上绕过hash校验。副本仍是同一run/REP，不是新采集。
已有helper的readiness上限60秒、每次export180秒、最多2次，确认记录PID退出后才重试；
失败保留partial并停止，无按名kill。随后audit保持严格拒绝，未知记录/依赖不猜测修复。
audit人工300秒停止点、无自动重采/改collector/模型。产物无论成功或BLOCKED都保留。
归档清单先快照、排除自身、再写并复核；公开仓库不包含Raw或机器绝对路径。

本轮草案验证仅PowerShell Parser和针对真实17文件的只读preflight；未执行其export/audit。
