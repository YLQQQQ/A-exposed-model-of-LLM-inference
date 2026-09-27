# Route A 最小执行与退出范围 v0.2

2026-09-27。依据用户已批准的A优先、单平台单模型范围修订**未来执行计划**；不是
Protocol Freeze，不重写MC/S/W/B，不追认旧数据。当前Gate8仍NOT_RUN。

## 1. Gate8验收范围的显式收缩

原EP-G8-02的真实Raw→S→A/B→D/Signature全链目标保留历史编号及记录，但B历史完整性
与D/Signature发布后移为独立能力资格，不再当作当前**A主线Engineering**的统一前置。
未来按本版形成的Gate8 PASS必须标注`A_SCOPE_ENGINEERING_ONLY / route-a-execution/0.2`，
不能写成原全链通过。以下五项全部有实际证据后才可判定，不因本地实现或一次快照完成改判：

1. 模型及输入驻留、warmup和原有成功drain在T外；同次身份与D1三窗可复核。此前工作
   不计入A，不重建完整load trace；证书仍须排除影响请求的迟发工作，drain不覆盖未来。
2. 请求内所有blocking CUDA API及必要依赖可恢复，包括第三个内部sync和1-byte D2H；
   correlation、实际scope、clock、completion有证据。边界或污染影响不明拒绝该窗；
   可证明局部缺口保留unattributed和原因，不转Host/residual。
3. 仅受改变影响的新Q0资格获得独立正/反例支持：D1/身份联结、drain前缀上界、后缀
   实际同步集合、A逐类及scope拒绝。复用旧公式/稳定Q0证据，不全重采，不自动继承新资格。
4. request/prefill/decode A互斥守恒且受控正例有正确具体归属；记录unknown、开销、
   可靠性和排除。不给真实模型预设零unknown或百分比阈值；Pilot固定可解释程度政策。
5. Engineering原件封存、版本/身份/lineage一致、形成EP-G8-04报告并明确限制。

B有充分证据时仍按旧规则独立有效；历史不足保留invalid/null。D/Signature未合格不发布。
当前A-only结果的`measurement_validity=NOT_ASSESSED`不能满足上面实际资格要求；
`dropped_records_status=UNKNOWN`必须附目标范围影响依据，不默认放行或改零。

`gate8_request_scope.py`首版的全inventory同域、无event、历史段禁重建、单TID、零unknown
是**合成实现支持域**，不是本版要求整个进程/历史满足的科学条件。当前先保留这些限制，
真实adapter只能按已批准target-scope规则有证据地收窄检查范围，不能直接删检查放行。

## 2. 当前真实Qwen路径与一次补证的目的

本地runner不传`attn_implementation`；已回传Transformers5.17.0 `modeling_utils.py:1845`
默认尝试SDPA，再按支持情况回退。**eager执行不等于eager attention**；本轮不擅自强制
backend以改变被测行为。旧首request内部Runtime23806之前，Memcpy344为1-byte D2H，
correlation61632→Runtime23805；另两copy是8-byte token D2H。该内部同步属于T，
具体Python调用点仍未知，不能仅凭字节数推定mask/item来源。

一次`qwen-request/0.1.0`静态快照限定七文件，不扫描整个包，不读DLL/模型权重，不导入
torch/transformers或实例化模型，不调用CUDA/Nsight。复用已有快照工具的新显式profile：

| 文件（包内相对路径） | 只回答的具体问题 |
|---|---|
| torch/version.py | 将本次包来源与既有2.6.0+cu124/commit身份对照，不重hash大DLL |
| transformers/modeling_utils.py | 绑定当前backend selector字节，避免沿用已改变安装的旧片段 |
| transformers/models/qwen2/modeling_qwen2.py | 实际Qwen forward的候选算子、attention dispatch和Host控制流 |
| transformers/models/qwen2/configuration_qwen2.py | Qwen支持域与配置默认值，不能替代实际实例值 |
| transformers/masking_utils.py | 定位可能产生1-byte Host判定及内部同步的mask路径 |
| transformers/cache_utils.py | use_cache更新是否有可识别的额外提交/异步来源 |
| transformers/integrations/sdpa_attention.py | 默认候选SDPA接口及其分支，不等于该次实际选中backend |

七文件各≤2MiB、metadata/RECORD有界；源副本最多14MiB，通常远小于此。读取版本、wheel
RECORD hash；缺文件、版本/RECORD冲突即INCOMPLETE并停止，不安装、不搜索替代文件。
回执`actual_attention_backend=UNKNOWN_NOT_EXECUTED`；这是候选来源材料，不是mode/
无迟发/完整性证明。成本是一次小文件读取与传回，无GPU扰动。

**收口停点：**回传后只检查表中命题是否能给出限定实际路径的来源证明，并匹配既有Raw。
若仍缺必要native stream/依赖或无迟发依据，报告具体未证边并停止；不再索取全包/PDB、
开CPU sampling、换collector、换stream或盲重采。该快照不设为所有A分析的通用必要条件，
也不承诺七文件足以解除真实资格门。当前不交付模型采集命令。

## 3. Gate8–14最短组织方式（保留编号）

| 稳定项 | 本路线的最小组织与证据边界 |
|---|---|
| EP-G8-01/02 | 一个最小真实request workload共享同次身份/三窗/Raw/S/A；先受影响Q0，再新Engineering，B/Derived后移 |
| EP-G8-03/04 | 同次记录存储、overhead、成功/失败及unknown原因，写A范围Engineering报告；小repeat不声称统计稳定 |
| EP-G9-01/02/04 | 复用当前单平台身份与已有资格，仅补新adapter/Q0增量；Formal资格另作结论，不重复采整套身份 |
| EP-G9-03 | eager必要检查共享；第二平台和compile/graph后移 |
| EP-G10-01～03、EP-G11-01～04 | 合并一次小Pilot组织，限信息增益对照所需点；共同记录OOM/EOS/retry、repeat/overhead/质量政策。Engineering与Pilot角色分开，不把前者偷偷改名为后者 |
| EP-G12-01～05 | Freeze固定A范围claim、支持执行/观测合同、版本、受影响Q0、输入点、排除/unknown政策、重复/overhead、比较统计；此后改动新版本使受影响Formal失效 |
| EP-G13-01～04 | 最小N1同步干预与G1自然对照分别标身份，以常规latency/activity/utilization为基线检验有限信息增益；不以A闭合代替信息增益。不使用未合格B/D支持claim |
| EP-G14-01～03 | G2可选、当前后移；仅增量价值和资源允许时另决定，不是路线A先决条件 |

可共享环境事实/代码校验与操作批次，不能共享或升级数据用途；Formal必须新采。
历史Gate6/7 PASS不动。本版计划调整只用于后续证据，暂无Pilot/Formal合格结果。

## 4. 服务器动作边界

只准备一次来源补证：传输固定版本的`scripts/gate8_install_source_snapshot.py`副本，
放`$ServerRoot/transfer`；用固定checkout的`.venv/Scripts/python.exe -I -S`执行
`--profile qwen-request --repo $CodeRoot --output <全新diagnostics子目录>`。
不更新checkout，不需要部署最新研究代码；核对副本hash和工具commit与服务器HEAD分别记录。
机器路径、固定SHA及完整单段PowerShell草案放忽略的`.local/`交付索引。
回传source_snapshot.json、artifact_manifest.json、七源副本和transcript即可；无Raw或权重。
当前仅本地准备，须用户/协调窗口另行确认执行；不发送GPU/Nsight命令。
