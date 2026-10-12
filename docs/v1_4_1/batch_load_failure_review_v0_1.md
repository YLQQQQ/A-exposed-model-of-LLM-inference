# Batch-load Engineering 失败审查 0.1

2026-10-11；[执行合同0.1](batch_load_engineering_plan_v0_1.md)。本次仅本地CPU核验与离线续算，无服务器、模型、CUDA、Nsight或新样本。Gate13限定PASS、Gate14 NOT_RUN保持。

2026-10-12后续有界审查已收口：[memset提交效果审查0.1](batch_load_memset_effect_review_v0_1.md)。Raw/Canonical及全部已采关联表未发现实现遗漏，旧84次调用缺参数/效果证明，停止旧实例追索；本文末尾“先查现存REP/调用资料”的下一步现为历史。只提出窄域参数取证待审设计，不安排同配置重采，不改本文原始失败结论。

## 结论及封存身份

**四个模型进程均完成；B1自然投影A通过；B4的A仍BLOCKED。** 最早具体失败是 `ENGINEERING_SCOPE_SUBMIT_MAPPING`，不是外层 `08_batch failed`、模型崩溃、采集超时或export失败。原批次/Raw/报告不改判。

输入 `batch_load_2af14b11dd99_engineering.zip`：103907198 bytes，SHA256 `b290a96f85d68c54adf8f9be0705fce2f188d4dffc8e98b44f7b6d5a909b8494`；清单SHA256 `157ff32769bb569ef1982ba3daa2846dbe06979a10e8330a9720a648f2ea4998`。本地核验安全路径、重复项、CRC、258项大小/内容哈希和全覆盖：259文件恰为258项＋清单，无遗漏。静态原件副本也在覆盖内。

四份manifest的执行commit `2af14b11dd990d159ff0b3204d26a1527244079c`/clean、264源码文件的Git内容和显式LF/CRLF表示、直接解释器/PID/producer、模型/输入引用、设备/隔离预检seal→claim→final、实际三次暖机/shape/逐样本token均核验。模型本体未回传，不声称本地重算权重哈希。两份原domain共约3.38GiB，已从ZIP流式核验但未另外展开；没有删除文件。

|槽|实际执行及采集|结果|
|---|---|---|
|B1P0|目标PID59100，exit0，producer COMPLETE；512×1/每样本2，baseline完成|性能/身份可复用，原BASELINE_COMPLETE_NOT_ACCEPTANCE保持|
|B1P1|目标PID52532，exit0；profile exit0/无超时/export PASS|原三窗口A、pair、observation均已生成，本轮复核一致|
|B4P0|目标PID62736，exit0，producer COMPLETE；512×4/每样本2|输入/token/性能可复用，不授batch4 A资格|
|B4P1|目标PID65008，exit0；profile exit0/无超时/export PASS|Canonical/projection/S/A准入/物理B计算已完成；A拒绝，原pair/observation/comparison未生成|

`DIAGNOSTIC_COLLECTED_NOT_QUALIFIED`及collector exit0不等于A通过；批次严格拒绝是正确行为。4模型进程/2profile全部已执行，**没有未运行组可续跑**。

## 最早具体记录及证据缺口

B4的七种API均已有分类覆盖：cudaLaunchKernel、cuLaunchKernel、cudaMemcpyAsync、cudaMemsetAsync、cudaStreamSynchronize、cuKernelGetFunction、cudaStreamIsCapturing。不是名称注册遗漏：cudaMemsetAsync本来就是submit。

114条成功cudaMemsetAsync_v3020中，84条无同进程/correlation可关联的device activity，全部位于Decode，API墙钟累计50717ns。首条runtime row38606/Canonical `cuda_api:CUPTI_ACTIVITY_KIND_RUNTIME:38606`，corr201238，目标PID65008/TID59500，trace23699269762～23699271214ns，returnValue=0。

随后driver cuLaunchKernel row23455/corr201239，在23699271675～23699280228ns；其kernel11867有自身corr201239唯一映射。两API不嵌套，时间相邻/correlation加一/相同线程不能证明该kernel属于前一memset。

[CUDA12.4.1内存API定义](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/group__CUDART__MEMORY.html)中count表示设置的字节数；Async名称不是Host非阻塞保证。现SQLite runtime字段只有start/end/eventClass/globalTid/correlationId/nameId/returnValue/callchainId，没有这些调用的count、地址、native stream实参或runtime→driver桥接。不能证明零字节/no-op、替代kernel路径或设备记录丢失中的任何一种。**没有activity、成功返回，均不证明没有提交。**

[G9分域合同0.1](gate9_domain_qualification_contract_v0_1.md)的提交映射/必要成员/依赖义务保持。未知提交效果尚未独立局限，不能按API墙钟小就只放局部unattributed，也不能改为non-submit、Host或opaque allocation、借近邻成员、填零。此处未证明全局丢失，dropped仍UNKNOWN。没有需要现在批准的A/B语义放宽。

## 后续链及可复用结果

新 `reanalysis_v0_1` 目录复用封存Canonical/投影，用原未修改的分域消费者每run一次复核S/A/B，然后释放大型W对象，不重新convert/export或写巨型domain。B1物理S输入41.857s、request/A10.185s、物理B0.008s；B4为41.004s/2.447s/0.007s。配对/附加检查合计约58s/49s，是本地CPU时间。

两组的边界/时钟/身份、窗外成功drain、setup与实际流、所有已观察活动的ownership/提交顺序/流/context、同步映射及既有官方warning处置均复核；B1接受同类warning row3/4/6/7，B4 row2/3/5/6，原warning/UNKNOWN保持。首次拒绝之后的全部API逐行检查，除84条缺映射之外，无新的scope、失败返回、同步/non-submit冲突或未知类别。

B4**已观察子集**的LEGACY/PTDS投影成员/边相同、各sync有唯一terminal，三个成员数8/1821/3385；这不能证明缺关联调用无额外成员，不发布B4 A/W/B。自然默认流完整物理B本不在该合同claim内，原物理B INVALID没有被当作独立request失败。

严格配对消费者的Host时长，单位ms：

|槽|Request|Prefill|Decode|
|---|---:|---:|---:|
|B1P0|141.544300|72.305100|69.239200|
|B1P1|179.584700|100.965000|78.619700|
|B4P0|231.408800|167.782100|63.626700|
|B4P1|248.322400|152.443000|95.879400|

P1−P0 signed差：B1为38.040400/28.659900/9.380500ms；B4为16.913600/−15.339100/32.252700ms。B4新派生pair只是PAIR_OBSERVED_NOT_ACCEPTANCE，不补写旧pair或使A通过，不拆为纯Nsight开销，不支持稳定收益。

B1原生trace锚点A与原observation逐记录一致；**不用上表Host时长作分母**。单位ms：

|窗口|trace窗口|Host|CUDA API|Device wait|sync residual|unattributed|
|---|---:|---:|---:|---:|---:|---:|
|Request|178.790817|87.402909|90.700161|0.525502|0.162245|0|
|Prefill|100.116413|45.683467|53.771358|0.525502|0.136086|0|
|Decode|78.674404|41.719442|36.928803|0|0.026159|0|

顶层及submit/non-submit子类守恒、Request=Prefill+Decode通过。已观察GPU activity并集为B1 Request71.678087ms、B4 Request138.484709ms。后者只说明已有记录的activity cost增加，不能替代84条缺证据或转换为Device wait，**本包尚无合法B4 A占比对照**。

## 最小修复与验证

本轮只修两个控制层的原因丢失：collector保留MODEL_A_SCOPE_BLOCKED并附加 `model-scope-rejection/0.1.0`，绑定结果文件名/SHA、状态及request原身份/reasons；实际main写入报告，batch透传拒绝上下文。附带拒绝诊断却声称成功也不能通过。不改collector退出含义、准入、parser、registry、runner、completion、流、S/A/B、baseline或冻结统计。**修复可定位性，不解决84条缺证据。**

tests-first：新增5项先失败，最小实现后5 passed；扩大文件链时1 failed/81 passed为CPU替身漏diagnostic目录，只修替身，不修改拒绝预期。最终：

`python -X utf8 -m pytest -q -p no:cacheprovider --basetemp=.local/batch_failure_release tests/test_batch_load_scope_failure.py tests/test_batch_load_driver.py tests/test_batch_load_diagnostic.py tests/test_gate8_diagnostic_collect.py tests/test_gate9_domain.py`

**83 passed/0 failed/0 skipped，50.93s。** 独立正例5ns submit→显式35ns MEMSET及字面A预期；缺activity、近邻driver/连续corr仍拒绝；实际collection报告→batch拒绝接线、错request数/缺reasons及既有身份/token/边界/drain/流/依赖/warning反例。CPU替身不是目标平台batch4资格。修改文件compileall/diff通过。

## 唯一停点

输入/token/性能、B1结果、两组Raw/REP/SQLite及来源链可复用。B4全request三窗口保持拒绝；没有第二个已观察独立冲突，但完整必要集合不能据已观察子集宣布成立。

**不重跑四槽，不交付再次撞同一拒绝的部署/重采包。** 下一项仅是取得84次memset的实际提交效果依据：可关联的设备/driver成员，或可核验的零提交实参及来源。现SQLite不足；先判断现存REP/调用资料能否补齐，而非预设无害。若必须新观测，先提出确实能得到该特定证据的窄域方案。本轮没有服务器补执行，不扩大负载、不提高wait目标、不改变定义。

私有定位只在忽略的handoff及本地审计JSON；不提交Raw、ZIP、模型、机器路径或原token文件。原BLOCKED及UNKNOWN/NOT_ASSESSED保留。
