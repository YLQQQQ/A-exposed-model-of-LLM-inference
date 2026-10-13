# 自然完成路径支持范围与首引擎适用性收敛 0.1

2026-10-13；**只读语义审查与待裁决方案，不是合同amendment、引擎资格或采集授权。**
本页为当前入口。四对C0/Cpre追加Pilot暂停；Cpre保留为受控机制对照，不替代自然baseline。
Gate13限定PASS、Gate14 NOT_RUN及原Engineering/BLOCKED/UNKNOWN/NOT_ASSESSED不变。

## 1. 自然token复制的裁决：C，有明确的合同解释缺口

**现有观测不能可靠拆分自然复制API内部等待；保留已批准的API预算，不制造同步/W/B。**
这不是“Device wait修好了”，也不是证明复制非阻塞。应分别理解：

- 已有独立正反例、Raw联结和区间复核支持限定S/A预算实现；守恒或零unattributed不能证明全部阻塞已恢复。
- 自然`.cpu()`路径的Host调用预算可含未分离阻塞；能恢复的后续流同步，不等于该wrapper内全部等待。
- Cpre增加真实同步后，必要活动交集进入该同步预算；这是执行政策干预，不是对C0内部等待的精确分解。

| 权威来源／实际实现 | 已确定规则 | 本次一致性判断 |
|---|---|---|
| [研究设计v7.1](../current/ExposedPath_研究设计.docx)§2.3.3/§2.4、[Pre-Pilot协议v2.1](../current/ExposedPath_实验协议.docx)§3.2.3/§3.3 | physical blocking sync按完成语义识别；unsupported不能假装非阻塞API | broad目标包含依参数阻塞的复制，不能只按名称或时长判断实例 |
| [Measurement Contract 0.2](measurement_contract_v0_2.md)§6/§10、[sync registry 0.2](contracts/sync_semantics_registry_v0_2.json) | 同步copy/依参数阻塞调用入universe；未恢复scope则fail closed；sync优先 | 有同步copy规则，但未提供`cudaMemcpyAsync`参数条件到completion scope的恢复规则 |
| [A registry 0.1](contracts/a_api_registry_v0_1.json) `A-SUBMIT-MEMORY`、[批准的类别审查](gate8_non_submit_api_review_v0_1.md) | 明确将异步复制识别为submit，实际同步证据优先；不保证Host非阻塞 | 本实例按已批准有限规则记API；submit映射成功不能代替参数依赖阻塞的支持证明 |
| [签署G12-ROUTEA/0.1.1](gate12_protocol_signed_v0_1_1.json) | 精确锁定上述registry、分域/质量门；P0性能与P1机制分开 | 签署锁定不能消除正文与registry之间的覆盖/措辞缺口，不授全部GPU相关Host阻塞解释 |

**缺口是“完整blocking覆盖”的证据/解释能力，不是已证实某个同步记录漏算。** 当前成功D2H
实例有返回码、唯一设备效果和后续成功流同步，但Host内存类别/该复制调用的完成保证未确定。
依据[CUDA 12.4.1同步行为](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/api-sync-behavior.html)，
异步复制的Host同步行为依参数而变，资源原因也可阻塞；不能从长包络、重叠或返回前活动结束
推出其等待scope，更不能从`Async`推出非阻塞。`.cpu()`整体保证Host值可读，不等于其中每个API都承担这个保证。

复用已保存的block1/G512实物（ns，统一trace clock），不重跑分析：

| 记录／关系 | 区间或值 | 能证明／不能证明 |
|---|---|---|
| runtime37815，`cudaMemcpyAsync_v3020`，corr197682 | [26747027542,26748902040)，1.874498ms；return=0 | API包络及成功，不能分离内部等待；callchain缺失 |
| MEMCPY347，同corr/context1/stream7 | [26748819715,26748820259)，8 bytes，D2H；dstKind=0，Host类型未确认 | 唯一设备效果；不能补成pageable/pinned参数证据 |
| runtime37816，`cudaStreamSynchronize_v3020`，corr197683；physical354 | [26748902941,26748938494)，35.553µs | 已恢复成功流完成语义；D2H结束早于入口82.682µs，不能由此推断`.cpu()`早已返回 |

源为现有[Formal完成/API审查](gate13_cuda_api_storage_review_v0_1.md)与本地已保存的
`G13-COPY-API-EXPLANATION/0.1`引用；当前[producer](../../exposedpath/runner.py)依次执行复制、Host值读取、completion记录。
目标PyTorch 2.6头文件的`memcpy_and_sync`是复制后流同步，不能把wrapper等同单个复制API。

**影响与边界：** 原Formal按签署registry的有限预算及已有显式同步结果保留，不改Raw/结果或
Gate13限定判定；不能据此声称完整枚举了参数依赖blocking、全部GPU等待或纯CPU/API分解。
本次没有足够事实判定某个已知unsupported copy被违规放行，亦不作“所有潜在问题已排除”的承诺。
未来如实例证据确定其属于unsupported completion，应按合同拒绝/保留unattributed，不能用本页豁免。
若要恢复复制内部等待或新增opaque-copy准入，那是**B类新语义裁决**，至少需实例参数、成功返回完成保证、
实际scope/依赖桥接及独立反例；cudaMalloc窄域amendment不自动适用。本轮不实施，也不为旧实例补造参数。

## 2. 首引擎：推荐vLLM v0.20.0；仅比较两个候选

| 固定候选与官方依据 | 最小路径与代价 | 推荐判断 |
|---|---|---|
| vLLM v0.20.0：[GPU平台](https://docs.vllm.ai/en/v0.20.0/getting_started/installation/gpu/)、[模型架构](https://docs.vllm.ai/en/v0.20.0/models/supported_models/) | 官方GPU路线要求Linux；支持Qwen2ForCausalLM，可沿用HF权重内容。默认wheel CUDA12.9；不能假定旧Windows/torch2.6/cu124/driver555.99兼容 | 首选：自然完成调用有明确event锚点，不需要为增大wait插入Cpre；须用户决定Linux环境并另锁软件栈 |
| llama.cpp v0.6.0：[Windows/CUDA构建](https://github.com/ggml-org/llama.cpp/blob/v0.6.0/docs/build.md)、[Qwen2转换](https://github.com/ggml-org/llama.cpp/blob/v0.6.0/conversion/qwen.py)、[自然入口](https://github.com/ggml-org/llama.cpp/blob/v0.6.0/examples/simple/simple.cpp) | Windows可构建；须HF→GGUF、模型内容/数值及native后端资格；自然处理/采样/Host token路径需新的native桥接 | OS变化较少，但不是沿用旧模型/资格的捷径；暂不并行推进，Linux不获准时停止并另裁决 |

vLLM候选配置：单GPU、TP/PP/DP=1、UniProc、隔离单请求，FP16/Qwen2.5-1.5B-Instruct，
固定旧32-token输入及digest、greedy/实际输出2、warmup3/repeat1。明确关闭prefix cache、
chunked prefill、speculative decode、offload及async scheduling；不运行HTTP/网络输出，
`detokenize=False`。`enforce_eager=True`在该版关闭torch.compile与CUDA Graph
（[配置实现](https://github.com/vllm-project/vllm/blob/v0.20.0/vllm/config/vllm.py#L839-L845)）。
`max_num_seqs=1`，`max_model_len=max_num_batched_tokens=64`为首例资源限界，不是容量结论。
attention backend、wheel/torch/CUDA/driver/Nsight与实际源码hash须在新环境审查后固定，未锁定不采集，
不自动fallback。仅授这个配置子域，不代表默认异步、多进程、graph或并发serving资格。

## 3. 自然完成锚点与必须新增的桥接

固定源[GPUModelRunner](https://github.com/vllm-project/vllm/blob/v0.20.0/vllm/v1/worker/gpu_model_runner.py)：
非async、无spec分支`_bookkeeping_sync`调用`_to_list`；后者把token复制到pinned Host，记录event，
等待该event，再转为Host列表。**使用它原有的完成操作，不增同步、不切流。**

- 首/末ready：在该Host列表真实取得并确认request-index/token值之后、后续bookkeeping之前记录。
  不用`LLM.generate`最终返回、`LLMEngine.step`外层、NVTX本身或网络TTFT代替GPU/Host完成。
  ledger保留真实读取事实与token序号；NVTX只提供trace-clock投影，保留marker延迟/开销诊断，不宣称零误差。
  [sampling参数](https://github.com/vllm-project/vllm/blob/v0.20.0/vllm/sampling_params.py#L240-L244)允许不做detokenize；
  网络发送/用户接收不在本研究窗口，也不假定必由另一进程执行。
- 建议新起点为已选中隔离request的首次`execute_model`入口，含其自然input preparation/H2D。
  request=[start,last ready)，prefill=[start,first ready)，decode=[first,last ready)，保持半开及共同clock。
  **这不同于MC0.2 §4的“输入已驻留GPU、drain后紧邻首次forward”条件，需单独版本化边界批准。**
  不加额外drain把引擎改成旧HF，不把`add_request`的排队/分词混进起点；窗内后续调度/准备照实保留。
  加载、初始化、暖机及成功drain仍在窗外。不能将新窗口与旧Formal的数值直接视为同口径引擎排名。
- [LLMEngine](https://github.com/vllm-project/vllm/blob/v0.20.0/vllm/v1/engine/llm_engine.py#L139-L161)的
  multiprocessing环境变量可覆盖构造参数；必须明确设为关闭并核验实际UniProc、PID实例及相关TID，
  不能只凭配置认为单进程/单线程。多worker、远端或未绑定ownership即停，不扩展并发模型。
- adapter保留request/repeat/pass、Host token值与event **每次record的生命周期**、record/sync对应，
  以correlation/context/实际trace stream和device UUID桥接，不能native handle/编号相等推映射。
  S用该次event捕获的传递闭包，包含已完成前缀，不纳入record后的提交；A投影依边界与drain准入。
  未知模式相关性、跨流边或target诊断影响无法界定即拒绝；没有graph事件才限定eager，不补造graph依赖。

**能继续检验的主线：** 自然执行中的有限、可证伪依赖归属，与同窗API/kernel/MemOp/sync的
count/sum/union及合法mapping/timeline公平比较。CUDA API内部不可分部分明确保留；该范围不是
“整个自然request的所有GPU阻塞已精确解释”。自然event锚点只是可行性依据，不是已取得trace资格。

## 4. 最小下一步、预算与硬停止

1. **当前集中决定**：是否允许Linux新栈的vLLM限定子域，以及上述包含自然input preparation的引擎窗口。
   尚无Linux目标/固定栈，Windows资料已足够排除原生直接部署；无需再查询Windows、安装或制作包。
   不默认WSL/社区Windows分支，不自动换服务器GPU；不同硬件只作适用性、不作引擎因果对比。
2. 批准后先做本地最小boundary/event/identity adapter及CPU文件链。独立手算正例：同流先行活动
   [0,4)、[6,10)，Host event-record提交=7、sync=[8,12)且两活动均在record前提交，W保留两者，wait=2、
   residual=2；record后提交不进入W。反例：latest-record错配、缺关联、错request/device/流、
   Host token未实际取得、额外同步、input/start冲突及未知相关依赖必须拒绝，不能只验守恒。
3. 新平台仅做一次同完成调用的受控event桥接（独立预期，非完整Q0），再一对32/2引擎P0/P1。
   **提议上限：1个受控CUDA进程/1profile＋2个模型进程/1profile**，同配置及逐值token配对；
   不要求等于旧HF数值token，不隐藏EOS、不强制生成凑2。首批结束即审查，不扩大负载或重复组。
   估计验证/采集30～60分钟、临时数据预留12GiB；新Linux环境/安装耗时和包体积尚未知，不作既批准预算。
   新环境存储须计入长期50GB目标，实际现存清理量未获回执确认；不复制模型/整仓库来筹备。
4. 身份/参数/record映射/依赖/clock/边界失败、OOM、超时、新诊断冲突或early EOS即停止，无自动重试。
   引擎已运行但无法形成合格W/A也是有效的适用性失败，不用低unknown或wait占比筛选。
   回传只需单ZIP：版本/输入/配置、真实producer/ledger/receipt、Raw/SQLite及最小派生与同窗baseline，
   归档核验后才清理可重建展开文件。此处不是可运行入口，执行仍须独立审查授权。

后续负载按token/工作量或资源问题预定，接受零wait、API主导、无额外信息和不确定结果；不以
“出现大Device wait”为选点或成功门。第二引擎、追加C0/Cpre Pilot、Gate14、Formal均不自动启动。
