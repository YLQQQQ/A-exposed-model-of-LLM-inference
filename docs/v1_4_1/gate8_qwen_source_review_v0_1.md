# Gate8 Qwen 七文件审查 v0.1

状态：2026-09-27；来源快照已完成，非模型执行、非资格证据。Gate7 PASS；新Q0/Gate8 NOT_RUN。

## 实际来源与结论

固定工具30b14cb；目标安装torch2.6.0+cu124/transformers5.17.0；服务器checkout f5edc64前后clean。
本地直接读取source_snapshot.json、transcript与指定源码；协调窗口独立核验总10文件及内部8项bytes/hash一致。
服务器脚本exit0，隔离解释器-I/-S，7项RECORD匹配；这是服务器静态回执，不是本地执行服务器测试。
原件定位存忽略handoff；不提交原始源码快照或机器路径。

| 来源（快照内相对路径/行） | 能确定 | 不能确定 |
|---|---|---|
| transformers/models/qwen2/modeling_qwen2.py:213–231、约350–389 | attention接口按config选择；forward构造DynamicCache与causal mask，然后调用层 | 实际加载后的backend、native dispatch |
| transformers/masking_utils.py:231–275、823–861 | fast_all返回布尔tensor；非tracing的SDPA mask跳过判断需要其Python truth；2D mask转bool；packed判断仅mask与cache皆None才进入 | 旧trace具体Python调用栈 |
| transformers/cache_utils.py:129–163、1322–1325、1392–1400、1803 | DynamicLayer以cat更新、长度来自shape；offloading默认false，额外prefetch stream受offloading分支控制 | 所有native库无worker/迟发工作；实际cache未被外部改配 |
| transformers/integrations/sdpa_attention.py:79–145 | SDPA接口及条件路径；is_causal.item受jit tracing条件限制 | 具体CUDA kernel/backend选择 |
| transformers/modeling_utils.py:1845–1878 | 未显式选择attention时存在sdpa选择/回退路径 | eager运行等于eager attention（两者不等价） |

runner prefill传attention_mask，decode只传token/cache。因而**prefill非tracing SDPA的fast_all条件**是旧request内1-byte D2H及第三sync的具体候选；bool标量求值与该观测相容，但不能仅凭bytes/次数认定callsite。
packed_sequence检测要求mask=None且cache=None，不符合通常use_cache=True的此路径；jit专属item也不能直接用来解释eager运行。
实际backend、native默认流模式、无迟发工作保持UNKNOWN；没有源码证据允许把物理W/B历史缩短。静态补证已到停止点，不再索取新包或搜索全安装。

## 最短后续：一次NOT_QUALIFIED Engineering诊断

资格不足不是禁止Engineering采集的理由。允许提出一次独立新目录的最小真实Qwen诊断，目的仅为检验新版producer可观测性，不产出合格A/B/D、不改变Gate verdict，也不追认旧trace。

当前具体工程缺口：`run_gate8_requests`是显式API，其docstring明确未由legacy CLI/launcher启用。直接重跑旧launcher不能取得新版D1/ledger。下一项本地工作只应是可测试的窄诊断入口/调用封装，使用现有API及身份参数，落盘实际attention配置/cache配置与producer/stage/drain/ledger；不得以来源UNKNOWN阻断诊断，也不得伪造资格证书或启用synthetic admission。

建议固定既有模型/内容身份、单GPU、batch1、32输入/2输出、warmup1/测量request1、eager非compile；这是诊断样本，不替代后续repeat/overhead验收。不强制attention backend或另建stream；实际配置只记录。沿用已审查minimal CUDA/NVTX profile，不CPU sampling、不额外模型优化、不参数扫描、不自动重试。

先CPU fixture验证入口实物身份/锚点/失败保存与独占输出，固定commit后由用户授权部署及**一次**运行；旧服务器f5不自动升级。执行草案应含工具/模型/代码身份、单次profile、REP保留、已有有界export、完整回传，禁止覆盖旧目录。

风险与停点：曾有Nsight系统BugCheck，旧Gate7成功不能保证本次安全；不得承诺低风险等于零风险。OOM、异常、profile/export失败立即停止并保留partial，无自动重试。边界/身份/相关依赖缺失只阻止可信归属，不删除原始诊断；未解决native/丢失影响不生成有效A。回传一次后报告可观测缺口和局部/不可界定范围，不自动加新采集或扩大collector。

此稿仅方案和来源审查，没有实际GPU/Nsight或新Q0测试。无需重复服务器安装搜索，也不需先取得Formal级充分证明才能请求Engineering诊断授权。
