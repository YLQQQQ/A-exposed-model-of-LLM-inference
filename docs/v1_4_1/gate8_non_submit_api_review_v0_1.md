# Gate8 non-submit CUDA API 分类修正与条件性复算 0.1

> 本文保留1733ff3时的审计与证据等级。后续工程退出政策见[G8-ENGINEERING-EXIT/0.1](gate8_engineering_exit_amendment_v0_1.md)；Gate9已可开展评估。下文原Gate8 NOT_RUN/Gate9不启动是历史状态，原条件性数据及其限制不改变。

状态：本地 Engineering 分类修正；不是新采集、Q0 资格或可信模型 A 验收。标准 Gate8 `NOT_RUN`，Gate7 历史 PASS 保持。四条 warning 无目标影响仍只是用户批准的假设；正式门、原 BLOCKED 报告、Raw、UNKNOWN/NOT_ASSESSED 均不改。Gate9/Pilot、D/Signature 不启用。

## 1. 语义依据与实现缺陷

- 当前研究设计 v7.1 §2.4：A_cuda_api 是请求路径 Runtime/Driver 的独占 wall-clock API 段，包含提交、查询和资源管理；不是整段 blocking sync，也不是设备等待或反事实可消除时间。A_unattributed 保留边界、ownership、correlation、wait-set 等不足或冲突。Host 是扣除这些部分之后的请求路径补集，不是 CPU 忙碌率。
- 实验协议 v2.1（仍是 Pre-Pilot）§3.3 与 Measurement Contract 0.2 §10：按同步语义和互斥区间并集记账；无效同步优先保留 unknown，有效同步拆分 device-wait/residual，然后是剩余可归属 API，最后 Host。二级分类位于父类内部，`A_cuda_api = submit + non_submit`，不能重复计时。
- “non-submit”只表示不提交设备工作且不属于需要恢复 completion/wait 的调用，不保证 Host 调用不阻塞。CUDA 官方明确任一 API 可能因内部资源争用等阻塞；这种可能性不能凭名称推导 W(s)，也不能把整个查询时间说成已恢复设备等待。[CUDA 12.4.1 synchronization behavior](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/api-sync-behavior.html)
- 实现遗漏：parser 已保留 API 名称、返回值、区间与 correlation；信息未在解析阶段丢失。A 原来复用物理同步注册表决定 API 子类，未注册的 handle/capture 查询进入顶层 unknown。另有“唯一 correlation + activity 即 submit”的兜底，可能把未知调用或尚未恢复的同步误归 submit。本次都修正；不根据实现现状重定义研究语义。

## 2. 版本化机制与适用边界

新增 `contracts/a_api_registry_v0_1.json`（`exposedpath-a-api-registry/0.1.0`）及唯一 A 分类 adapter。先查冻结同步规则：物理/unsupported sync 不成为普通 API；已有 dependency-edge/query 规则保留。其余仅精确规则及合法末尾 `_v[1-9][0-9]*` 版本后缀可进入 submit/non-submit；每条新规则记录依据及官方来源。未知前缀、畸形后缀、无 activity 均不能推导 non-submit。新规则已记录的非零/null 返回值不默认为成功；真实 Engineering 入口另外强制存在且为零。旧合成 A 输入未带 return_value 的兼容路径以及旧 query 的 NotReady 行为保持，不把这种兼容当真实输入缺字段的许可。

submit 仍需要唯一 API correlation 和实际 activity；non-submit 若有矛盾的 activity 或同步映射，不能借类别规则放行。Engineering 文件入口复用同一分类器，删除旧两名称“永久局部分类缺口”分支。正式 warning 拒绝保持；条件输出记录注册表版本与 SHA256。ABI 后缀规范化不是未知 CUDA 版本的语义资格授予；MC §15 要求的受影响资格验证仍按范围复用/补充，不能自动继承历史 PASS。

同步/ownership 优先级和 atomic union 不改：重叠 non-submit 只算并集；覆盖有效同步部分先归 wait/residual，无效同步保持 unknown；已知 submit/non-submit 的冲突重叠仍保守 unknown，不任意选择一个子类。真实窗内是否存在这种重叠另由 Raw 检查，不以合成测试替代。

**父类已知、子类仍未知的边界**：当前 schema 没有“API 父类已知但子类未定”字段；不能只增 A_cuda_api 而破坏 `submit + non_submit`。若未来出现无法解决的这种调用，最小 amendment 候选是版本化增加父类内 unknown-subtype 及相应二级守恒，顶层仍五类；本轮不实施也不预先批准。当前 request 七种 API 已有足够类别依据，不依赖该裁决。真正语义不明或冲突仍 unknown/拒绝，绝不填 Host。

### 两个实物回归样例

- `cuKernelGetFunction`：CUDA 12.4.1 Driver Library API 定义为根据 kernel 和当前 context 返回 CUfunction handle，不是 launch 接口；实际设备 launch 另由 cuLaunchKernel 表达。本次按成功的 handle 查询归 non-submit，而非按“无 kernel”猜测；未宣称无内部锁、资源处理或绝不阻塞。若出现相关 activity/sync 冲突，不适用此规则。[Library Management](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-driver-api/group__CUDA__LIBRARY.html)、[Execution Control](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-driver-api/group__CUDA__EXEC.html)
- `cudaStreamIsCapturing`：读取 None/Active/Invalidated capture 状态，不启动/结束 capture，也不等待 stream completion。legacy stream 在其他 blocking stream capture 时可能返回 capture 错误，还可能报告先前异步错误；失败不按成功查询放行。现有纯 eager 支持域不因该查询而扩展到 graph/capture。[Stream Management](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/group__CUDART__STREAM.html)

## 3. 现有 trace 的覆盖边界

封存配对执行 commit：`36ed952b57f20651dd290fc484d7b21fc7dbbfc4`。原 ZIP SHA256：`3c90764357547cfb28de3c16bc624664e36d58565dfa4dcb02f1063e0294940f`。本地修改不冒充服务器执行版本。

目标 request 实际七种 API，一次性覆盖如下；API 名保留 Raw 形式：

| API | 调用数 | 类别及证据用途 |
|---|---:|---|
| cuKernelGetFunction | 6169 | 成功 handle 查询，non-submit；无矛盾关联是校验，不是分类依据 |
| cudaStreamIsCapturing_v10000 | 2 | 成功 capture-state 查询，non-submit |
| cuLaunchKernel | 197 | submit + 唯一 activity correlation |
| cudaLaunchKernel_v7000 | 3295 | submit + 唯一 activity correlation |
| cudaMemcpyAsync_v3020 | 3 | submit + 实际 memop；若有同步证据仍同步优先 |
| cudaMemsetAsync_v3020 | 3 | submit + 实际 memop；不把 Async 当绝不阻塞 |
| cudaStreamSynchronize_v3020 | 3 | 物理同步及必要集合，按既有 wait/residual 拆分，不吞入 non-submit |

全 trace 共 22 种，其余 15 种仅在窗口外出现，不将加载/暖机注册表扩展当作 request 修复前置：

| 窗口外 API（完整名称/全 trace 数量） | 本轮处置 |
|---|---|
| cuCtxSynchronize (1), cudaDeviceSynchronize_v3020 (3) | 既有同步规则；drain 沿用原证据及资格检查，不归普通 non-submit |
| cuDeviceGetLuid (4), cuGetProcAddress_v2 (1300), cuLibraryGetKernel (22), cuModuleGetLoadingMode (4), cudaGetDeviceProperties_v2_v12000 (2), cudaGetDriverEntryPoint_v11030 (2), cudaMemGetInfo_v3020 (1) | 名称指向信息/handle 接口，但本轮未逐一资格审查，**未新增普通 A 支持规则**；不靠名字猜测，进入未来 request 必须另作有界审查 |
| cuInit (5), cuLibraryLoadData (18), cudaEventCreateWithFlags_v3020 (18), cudaFree_v3020 (1), cudaHostAlloc_v3020 (1), cudaMalloc_v3020 (33) | 初始化/资源/可能隐式同步等不在本轮已证明类别；不按无 activity 推为 non-submit，不扩大支持域 |

同名窗外调用不继承 request 的 ownership/准入；注册类别不能替代窗口证据。物理 S/B 和旧合成输入路径保留，未改冻结 sync registry。

## 4. 定向验证与离线结果

先新增独立字面预期，红测 15 failed，复现遗漏和 activity 兜底误归；再最小实现。相关 A/AB schema、signed-time、Engineering 文件链、条件 warning 入口七文件回归 143 passed。另补真实 SQLite 文件入口的 non-submit activity/sync/error 三种冲突反例，验证类别规则不绕过准入。compileall（修改模块）、validate-contract 37/37（仅内部一致性）、diff-check 通过；不运行全量、Q0、模型或 Nsight。

追加三项文件入口反例全部通过（3 passed）。本地 Python 3.12.7；七文件命令是
`python -m pytest -q -p no:cacheprovider tests/test_v141_api_classification.py tests/test_v141_a_accounting.py tests/test_v141_ab_bundle.py tests/test_v141_ab_schemas.py tests/test_gate8_signed_time.py tests/test_gate8_engineering_scope.py tests/test_gate8_conditional_a.py`；
追加检查使用同一 pytest 参数及 `tests/test_gate8_engineering_scope.py -k non_submit_rule_cannot`。
均为 CPU/合成或文件入口回归，不称目标机或新 Q0 验证。

实际离线入口 `exposedpath_v141.gate8_warning_assumption` 正常 exit0；同一四消息假设版本
`FOUR_OTHER_PROCESS_WARNINGS_NO_TARGET_IMPACT/0.1`，输出仍 `CONDITIONAL_A_ONLY_NOT_ACCEPTED`。
复算写新版本目录，原 ZIP/146 个解压文件、原正式报告及旧条件输出全部重新核对不变。
新条件 JSON：924663324 bytes，SHA256
`f0e81b5e3f1dba30f0e2c8b6a6d3f9542a361d4005b338b6905ae54696ec4928`。
注册表 SHA256 `e3b9b87b71e02101690012fc322bb7f78e4e902c08ac10bd7130cd8ea0fbbe7b`；
本机索引记录实际源码字节 hash、精简审计及完整派生位置，不提交原始产物。

三窗五类 A（单位 ms，`旧 → 新`；相同项只列一次）：

| 窗口 / T（不变） | Host | CUDA API | Device wait | Sync residual | Unattributed |
|---|---:|---:|---:|---:|---:|
| Request / 164.259912 | 100.941487 | 58.847854 → 62.688005 | 0.011552 | 0.618868 | 3.840151 → 0 |
| Prefill / 89.637346 | 52.515342 | 34.407151 → 36.519956 | 0.011552 | 0.590496 | 2.112805 → 0 |
| Decode / 74.622566 | 48.426145 | 24.440703 → 26.168049 | 0 | 0.028372 | 1.727346 → 0 |

增量全部进入 **non-submit 子类**；submit/Host/wait/residual 未变。Raw 查询两类均 returnValue=0，
无关联 activity；请求内 API 相互重叠数为0。独立 Raw 裁窗复算 6171 调用得到
3840151/2112805/1727346 ns，与转移量逐一相符，不调用被测分类器生成标准答案。
其中 cuKernelGetFunction 6169 次共3835475ns、cudaStreamIsCapturing 2次共4676ns；
没有剩余局部分类原因，三窗 primary_reason=null、secondary_reasons=[]。
这不是把全会话证据 unknown 改零：warning 假设、`dropped_records_status=UNKNOWN`、
`measurement_validity=NOT_ASSESSED`、`trusted_a=false` 全部保持。

两个默认流模式的必要集合与此前独立证据逐成员一致，prefix/suffix 不变；整数 ns 域顶层及
二级守恒、重叠、未覆盖、越窗误差均为0，五类及二级 API 均满足 Request=Prefill+Decode。
无额外资格或采集步骤；原正式 A 仍为空/BLOCKED，未用事后注册表修正追认旧 attempt。

## 5. 结论边界

本次修复分类机制遗漏，不以 unattributed=0 为验收条件，也不把 A 守恒等同归属正确或科学资格。保留独立反例证明未知 API、缺同步依赖、ownership 与子类冲突仍未知/拒绝。四 warning 影响范围是独立真实证据限制，未被类别覆盖解决；即使当前条件性 unattributed 清零，也只能声称本支持域和声明假设下的分类缺口消除。不准备新部署包或服务器采集，不追认任何旧 attempt。
