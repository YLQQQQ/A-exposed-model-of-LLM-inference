# Gate8 eager 来源对齐 / G8-STAGE-OBS/0.1.0

2026-09-27；基线 f022520。已批准 closed-prior 方向内的工程接线，不改 W(s)、A/B、
completion 或研究质量门。Gate7 PASS；Gate8/新 Q0 NOT_RUN。无服务器部署/采集授权。

**7.47当前覆盖：来源profile暂停，不再请求采样风险批准。** §12是当前下一步；
§10/11及交付包只是未授权备用，不是Gate8必经或执行指令。既有mode/lifetime未知与
科学拒绝门保持。§8本地加载观察已实现；只是Host诊断，科学接线仍缺必要mode/lifetime证明。
§5的一次安装快照已在用户服务器完成，解压原件已直接审计；
不要重跑该指令或要求重传ZIP。§7记录实际源码依据、尚不能赋值的字段及下一项
本地接口工作。7.41“目标源字节尚缺”的状态仅历史；目标运行ownership/default-mode仍未证明。

## 1. 真实输入与源码核查

历史 Gate7 唯一 PASS attempt `smoke_20260924T084657Z` 的 SQLite 以只读方式核查，
前后 hash 不变，仅作兼容性诊断，不能补写 owner 或升级为新版本验收。

- 10476 kernel / 349 memcpy / 9 memset 均落在 activity device 0/context 1/stream 7。
  context 的 nullStreamId=7；stream flag=3 对应该文件 enum 的 NULL。这里的 7 是
  trace namespace，不等于 Torch native handle，也不能代替 LEGACY/PER_THREAD 资格。
- 四个 Token-ready range 内有 8-byte DtoH 与 `cudaStreamSynchronize_v3020`；
  physical sync rowid 348/349/352/353。两个原 request 前 drain 的 Runtime
  rowid 23796/27103 对应 physical 346/350，API 是 `cudaDeviceSynchronize_v3020`。
  新匹配复用既有 registry 精确规则 `SYNC-DEVICE-RUNTIME-001` 及已有数字 ABI 尾缀规则；
  不用 startswith，不把 driver/context 或未知 API 代为匹配。
- 首 request 前有 3492 kernel / 343 memcpy / 3 memset；其中 338 memcpy 来自四个
  worker TID。原 NVTX 12 行没有 setup/warmup owner。主线程范围包含时间，不能证明
  worker 提交的 owner；所有 correlation 唯一也不能证明未捕获记录不存在。
- 有 event 创建 API，缺少足以闭合相关 event 历史的证据；没有 eventRecord/wait 行
  不是“没有依赖”的肯定证明。旧 metadata 含敏感环境信息，不复制到公共材料。

第一方源码与文档给出以下边界（是版本源码依据，不是目标 wheel 的资格证明）：

- PyTorch 2.6 把每线程 current stream 初始设为 default；default 的 native handle
  返回空句柄。stream pool 是进程共享、循环复用的；持有一个 Python Stream 包装对象
  不等于独占 stream。见 [CUDAStream.cpp](https://raw.githubusercontent.com/pytorch/pytorch/v2.6.0/c10/cuda/CUDAStream.cpp)
  与 [CUDAStream.h](https://raw.githubusercontent.com/pytorch/pytorch/v2.6.0/c10/cuda/CUDAStream.h)。
- CUDA 12.4 default stream 模式可能按编译单元选择；LEGACY 和 PER_THREAD 的
  隐式依赖不同。不能从 native handle=0、nullStreamId 或两个 handle 相等推断模式。
  见 [CUDA 12.4.1 stream synchronization behavior](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/stream-sync-behavior.html)。
- current/default stream Python API 可触发 lazy initialization；观察器在未初始化时
  不调用它们，仅记录 UNKNOWN。初始化后读取仍有观测开销，不宣称零 CUDA 交互或零延迟。
  见 [PyTorch 2.6 CUDA Python entry](https://raw.githubusercontent.com/pytorch/pytorch/v2.6.0/torch/cuda/__init__.py)。

## 2. 版本化字段与实际文件入口

`runner.run_gate8_requests_to_files(record_stages=True, record_drains=True, ...)` 为显式
opt-in；旧 CLI/launcher 不自动切换。`model_setup` 可提供 `model_path, prompt_path,
manifest_path, physical_gpu_index, batch_size`，函数实际调用原 `load_model` 和原 tensor
初始化。仍可使用原 resident 路径，后者显式 `setup_observed=false`，不得补造 setup。

模型加载前核 WMPC/prompt/实际 runner 字节 hash、run/commit/dirty 声明、eager/G1、
模型路径、输入/输出/batch、warmup/repeat 与 plan 一致、physical-index mask 和 logical
映射。它不替代 launcher 的实际 Git/UUID/PCI、模型内容快照、环境及双 pass preflight。
未知或冲突不回退；setup 失败保存 FAILED，计划 request 保留未执行原因，不继续推理。

| 产物 | 明确内容与边界 |
|---|---|
| stage ledger / marker 0.1 | PASS identity、PID、源码 hash、稳定 stage_id、role、logical device；setup 的 request_identity=null，warmup/measured 关联原 identity；scope_semantics=HOST_CALL_ONLY |
| stage 观测 | TID、perf-counter start/end、before/after probe、COMPLETE/FAILED/error；default_stream_mode 与 lifetime_status 始终 UNKNOWN。handle 是 producer native namespace，不能与 trace stream 数字直接对齐 |
| producer receipt 0.3 | pass/host/drain/stage 四文件 hash/size；所有阶段实际执行，阶段与逐 request outcome 双向核对。旧 0.1/0.2 不改 |
| input receipt 0.3 | 原输入集合 + drain/stage ledger；严格版本、hash、来源和计划校验；不忽略额外/缺失文件 |
| stage diagnostics 0.1 | 原 Canonical NVTX row 引用及 trace clock；同 PID/TID 且全范围内 API 仅标 same_thread_api_refs；其他线程/跨范围标 UNKNOWN 原因，不生成 GPU dependency 或 S owner |
| file-chain 0.5 | stage diagnostics hash 及原始 stage provenance；读取重算诊断、核原文件集合。诊断入口仅 BLOCKED/NOT_ASSESSED，不允许 quality/closed-prior override 注入后放行 A/B/D |

两种时钟不拟合：host 时间只诊断本线程执行顺序；trace 范围只由真实匹配 NVTX 提供。
stage 的 Host 返回不是 device-complete；warmup 没有新的 token-ready 窗口。原 D1
request/prefill/decode 公式不变。范围 marker、stream 读取和 Python 记录可能有开销；
Pass0/Pass1 使用同一观察逻辑，Pass0 不发 NVTX。测试确认原同步次数不增加、不选新流；
实机开销、目标工具/模型行为尚未验证。

新文件独立发布，失败只留诊断 staging、不覆盖输入、不 resume；hash 无循环。
新版本本地文件测试用合成 SQLite 和 CPU model/device doubles，非目标 Nsight/Q0。
读取必须同时绑定封存input、producer和result版本及精确文件集合：input0.1只读原
result0.1/0.2/0.3，input0.2只对应closed-prior result0.4，input0.3只对应stage result0.5。
不能仅修改result版本/删掉stage hash字段来跳过重算；刷新文件清单hash也不能解除
版本/产物冲突。stage/drain/closed-prior必需文件缺失或旧入口夹带stage均拒绝。

验证：tests-first 的producer8/文件入口4/真实ABI别名1及review负例均先RED后GREEN；
第一轮定向113 passed、CPU全量1274 passed/5 skipped；后续协调review发现版本降级，
stage五个反例与closed-prior一个反例先RED后修复；修复后三文件61 passed，最终CPU全量
1279 passed/5 skipped（251.18s）。详见research_progress7.40。
CPU全量均隔离nvcc，skip为既有CUDA编译项；
compileall、contract37/37内部一致性、Canonical7模块、oracle静态独立性、diff-check通过。
独立只读review发现的阶段截断、WMPC实际执行合同及logical mapping冲突均补回归修复。

## 3. 必要 scope 与不能忽略的反例

下面是已批准语义的工程判定规则，不是将 all-inventory 放宽成无证据过滤：

1. 必需集合包含 target sync 同 context/stream 的完整先行物理前缀；已完成 setup、
   warmup、旧 request 仍保留。相关 event/default 隐式依赖需继续闭包，不能按窗口时间删。
2. “另一个 stream”“在 request 外”“早已完成”均不足以排除。可证无关要求正确
   device/context/generation 和已验证依赖语义；同 context 其它 blocking stream 在
   LEGACY default 模式下可能相关。只有非相关 scope 的证据闭合后才允许忽略其 owner 缺失。
3. 成对反例：已知 nonblocking 独立流、无传入 event 的合格受控源码可排除；同样的
   时间轴加入指向它的 event wait 或改为 LEGACY 隐式依赖时必须纳入。不能把两例都按
   “没有重叠”删掉。历史文件缺少这套肯定来源，不能在本轮自动判为第一种情况。
4. 本轮实际成对文件测试：同线程 submission 范围关联保留原 API 引用；只改成 worker
   TID 后必须转为 OTHER_THREAD_OWNERSHIP_UNKNOWN。即使所有 hash/marker 自洽，错误
   logical device 仍拒绝。两者都不是强 ownership/依赖准入，不增加科学类别。

连续非 default 的旧窄 profile 仍保持原资格限制；default 要证明相关调用的实际模式
及 context/thread 来源；destroy/recreate 要解开 generation 与真实资源映射。三者均
不能靠新 stage marker 或 Python 对象存在替代。本轮**不删** all-inventory 保守拒绝，
因为一般模型必要依赖 closure 尚无合格 source 描述；它仍只是窄实现限制，不是全capture门。

## 4. 精确版本来源核查（7.41；非目标安装证实）

本地 `.local/server_receipts` 与历史 evidence inbox 已有环境版本、Nsight安装说明和
controlled源码，但没有下列目标Torch/Transformers安装源码字节或default-mode构建依据。
不重复安装搜索，不从敏感Raw metadata导出环境来补充它们。

| 来源 | 能支持的源码级事实 | 不能据此推出 |
|---|---|---|
| [Transformers v5.17.0 modeling_utils.py](https://raw.githubusercontent.com/huggingface/transformers/v5.17.0/src/transformers/modeling_utils.py)，`_load_pretrained_model` | Windows safetensors路径选择pread/CPU，获取slice后交给`convert_and_load_state_dict_in_model` | 目标wheel字节完全相同、所有实际输入都采用此分支 |
| [同tag integrations/accelerate.py](https://raw.githubusercontent.com/huggingface/transformers/v5.17.0/src/transformers/integrations/accelerate.py)，`check_and_set_device_map`、`get_device` | runner的`cuda:N`字符串转为整模型设备映射，再解析各参数目的设备；此字典不是自动分配 | 目标文件已经核对或实际模型没有自定义加载路径 |
| [同tag core_model_loading.py](https://raw.githubusercontent.com/huggingface/transformers/v5.17.0/src/transformers/core_model_loading.py)，`spawn_materialize`、`_materialize_copy`、`WeightTransform.materialize_tensors` | 一般异步路径用最多4个worker；job执行slice和`tensor.to(device,dtype)`，主路径读取Future结果。禁异步环境开关、disk offload、on-the-fly quantization会走另一分支 | 旧Raw的四个TID就是该pool；CPU future结束等于任意CUDA工作的完成；仅凭setup时间范围认领worker |
| [PyTorch v2.6.0 Copy.cu](https://raw.githubusercontent.com/pytorch/pytorch/v2.6.0/aten/src/ATen/native/cuda/Copy.cu)，`copy_kernel_cuda` | CPU/GPU copy使用current stream；blocking分支进入`memcpy_and_sync` | 所有模型operator都使用同一流；不存在其他依赖 |
| [同tag CUDAFunctions.h](https://raw.githubusercontent.com/pytorch/pytorch/v2.6.0/c10/cuda/CUDAFunctions.h)，`memcpy_and_sync` | CUDA分支依次调用`cudaMemcpyAsync`与`cudaStreamSynchronize` | 目标wheel每个编译单元的default-mode；历史Token-ready每个调用已经完成资格认证 |

runner已有`load_model`传FP16及单CUDA device_map、调用AutoModel与AutoTokenizer；没有
显式禁异步或指定worker归属。它的`trust_remote_code`及fallback也不能被源码tag
掩盖：将来执行描述必须绑定实际加载来源与分支，不能因model_type字符串就视为已证明。
本轮不改变加载行为、不关异步、不换stream、不增加sync来躲避问题。
特别注意：core loader最终使用`shutdown(wait=False, cancel_futures=True)`，不是全pool
join。已消费Future返回不能覆盖异常/跳过/重试下仍运行的任务；不能先把所有worker
判为setup完成。目标加载分支、实际model class及任务/TID/correlation仍须后续来源绑定。

**停止点明确：** 现证据只能给出可核对的候选来源链，不能形成可被S消费的合格
source descriptor。先取得一次目标安装字节；default-mode仍需相关编译单元/实际API
语义来源，DLL哈希只能固定二进制身份。回件不自动放行；若仍无构建依据，明确记录
该单项缺口并评估已有API/来源能否闭合必要依赖，不重复请求整包或全capture认证。

## 5. 一次只读补证工具与精确范围

`scripts/gate8_install_source_snapshot.py`，schema `gate8-install-source-snapshot/0.1.0`。
独立工具，不接入producer、Canonical、S/A/B或任何验收gate，不新增准入fallback。
使用固定checkout `.venv/Scripts/python.exe -I -S`，显式解析同venv的`Lib/site-packages`，
不用PATH Python、`sys.prefix`或site初始化；不import Torch/Transformers、不执行被读源码。
只对两个包读取Name/Version、WHEEL tag及对应RECORD条目，不输出pip配置、环境或全包清单。

| 限定文件（相对site-packages） | 取得目的 |
|---|---|
| `torch/version.py` | AST读取version/cuda/git_version字面量，绑定2.6.0+cu124/12.4；不是执行源码 |
| `torch/cuda/__init__.py`、`torch/cuda/streams.py` | 对齐Python stream/current/default入口及lazy-init来源 |
| `torch/include/c10/cuda/CUDAFunctions.h`、`CUDAStream.h` | 对齐copy/sync及stream包装声明；不假装header就是编译参数 |
| `torch/lib/c10_cuda.dll`、`torch_cuda.dll` | 仅流式读取bytes/SHA256/RECORD匹配，**不加载、不复制**二进制 |
| `transformers/modeling_utils.py`、`core_model_loading.py` | 对齐实际loader/worker/materialize/Future来源与分支 |
| `transformers/integrations/accelerate.py` | 闭合字符串device_map→参数目的设备的来源链，而非扫描另一个包 |

共10个文件，最多拷贝8份限定源码。缺失、版本冲突、RECORD不符或路径重定向等保留
issue并非零退出，不扩大搜索范围；仅完整快照才标`SNAPSHOT_COMPLETE_NOT_QUALIFICATION`。
`default_stream_mode=UNKNOWN`、`worker_trace_ownership=UNKNOWN`、`qualification=NOT_ASSESSED`
固定保留。RECORD一致性不是wheel真实性认证，也不是编译mode证明。
METADATA的Name/Version从同一已hash字节解析，各必须唯一；不重新读取后只取首值。
WHEEL tag缺失或git_version未知不补造；即使所有文件已读取，也不代表来源充分。
输出只写全新独立目录，拒绝覆盖/写入安装树；manifest显式列已完成产物，排除自身。
本工具无网络、子进程、模型、CUDA或Nsight操作；CLI只支持这次Windows目标安装取证。

### 交接操作（只准备，须用户另行执行）

不用部署新commit、不生成bundle、不重跑full/static/controlled。只将已审查的**一个工具文件**
复制至`$ServerRoot/transfer`，用交付索引SHA256核对；服务器checkout继续固定`f5edc64`。
机器路径与完整PowerShell封装在忽略的本地交付索引中，不进入Git。

核心调用（协调窗口先审查固定变量和工具hash；下列不是本轮已执行的命令）：

```powershell
$PythonExe = Join-Path $CodeRoot '.venv\Scripts\python.exe'
$RunId = 'source_snapshot_' + (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '_' + [guid]::NewGuid().ToString('N')
$RunRoot = Join-Path (Join-Path $ServerRoot 'diagnostics') $RunId
New-Item -ItemType Directory -Path $RunRoot -ErrorAction Stop | Out-Null
& $PythonExe -I -S $TransferredTool --repo $CodeRoot --output (Join-Path $RunRoot 'snapshot')
$SnapshotExit = $LASTEXITCODE
```

完整封装还核对操作前后Git HEAD/clean，保存工具hash、输出和退出码；任何冲突即停，
失败目录保留且不重试补填。只回传本次RunRoot（源码快照、身份receipt、stdout/stderr、
两个相对路径清单）及transfer ZIP的bytes/SHA256；不传DLL、Raw、模型或环境dump。
快照清单只覆盖快照，外层传输清单覆盖操作receipt/工具，均排除自身避免循环hash。
用户回传后本地主窗口比对版本源码、引用与目标字节，协调窗口复核封装/清单；只有
来源合同明确的部分才继续本地scope接口，不要求用户选择底层文件组织。

本地验证：初始10个失败测试先RED后GREEN；独立/协调review的重复metadata identity
三个负例和补全device_map源文件检查先RED后修复。最终15项通过（3.12s）；隔离子进程
用假安装文件并禁止目标包import/网络连接/子进程/动态库加载。一次测试误把标准库
间接import socket当网络操作，定位后改为事件级禁止，未改变工具边界。
这是本地Python3.12.7确定性验证，不是目标Python3.11安装回执。不为只读工具重复
上轮全量或旧controlled；运行代码、S/A/B/Derived和历史证据不变。

## 6. 后续资格边界

不再复验旧独立 stream controlled capture。主窗口下一项是把已定位的真实 eager
提交来源（含 setup worker）和 default-mode/生命周期来源做成可解引用、目标限定的
descriptor，再将必要前驱闭包与可证无关 scope 接入 S；不能先删除 UNKNOWN/全域拒绝。
本轮已实际接到 model loader/阶段文件，但一般模型科学归属入口仍未就绪。

若本地现有源码/Raw 无法确定目标二进制的来源，提交**一次最小补证方案**而非盲跑模型：
目标安装的 torch CUDA 实现/构建身份及相关调用 default-mode 依据、加载器 worker
提交/join 来源。只读取得字节/构建依据，不 profile/export、不运行微程序或重复安装搜索。
它解决指定缺口，不请求全capture认证；未取得时保留 UNKNOWN。

当 descriptor 与本地正反例均完成后，才准备新增路径受控验证：同一自然 stream、setup/
warmup 后两 request、原 drain，不新增 sync；独立 oracle 固定全部历史 W 成员、hidden/
exposed/tail 和 A 窗口。无关流/event、缺 source/错 generation 作为独立反例；只补受影响
资格，不重采旧全矩阵。回传固定源码/构建、pass/host/drain/stage/source receipts、原 REP/
SQLite、collector argv/log、Canonical 来源与派生报告。缺 scope、来源或无法界定缺口即停，
不 retry 改构造求通过。以上仅准备方向，**不是可执行服务器采集授权或部署包**。

## 7. 目标安装原件审计 / 7.42

直接读取run `source_snapshot_20260927T024740Z_fa29319e1be040deb99c2ac9402900fb`
解压目录。外清单SHA256 `870a2184abc0bdb00cdf972991015fdb47c1d7f7a644ee757426e7a7919b81c3`，
14项大小/hash/精确集合匹配，总15文件；内清单9项（8份源码与receipt）同样匹配。
内清单SHA256 `43beca90ce7cf25cf7dedfbe65abfec2c73c26797aaf7e1a7435315a5a1f7c79`；
snapshot receipt SHA256 `09a31660436544e1d369d39f861f9107f5ad4c0f364b7eb3a2b3ab89d883cb09`。
工具字节与7.41固定副本一致，原件保持不变。**未收到ZIP本体**，不能称ZIP SHA或CRC已
本地验证；既有ZIP大小/hash仅用户回执，不影响上述解压文件级审计，不要求重传。

operation原件记录server `f5edc64862a8d5fbe94a7bf19be68303a4874b7f` 前后clean、
exit0、无operation error；目标Python3.11.16/isolated/no_site。snapshot为
`SNAPSHOT_COMPLETE_NOT_QUALIFICATION`、issues为空、10项record_match=true。
Torch为2.6.0+cu124/CUDA12.4，源码git_version声明为
`2236df1770800ffea5697b11b0bb0d910b2e59e1`；Transformers5.17.0。
这些是本地读取的服务器记录，不是本窗口在服务器执行；DLL未传回，不能声称本地复算DLL。

以下行号指**收到的原文件**，不是网页抽取行号。可以据此固定来源身份，不能跳到运行事实：

| 目标文件 / SHA256 | 本地直接读到的来源事实 | descriptor中的合法边界 |
|---|---|---|
| `transformers/modeling_utils.py` / `38c2bd02ed7af229f54e2f02dae65663be7af29ed2c9498bd1c460cf60fbb62d` | L4356起loader；L4393 allocator warmup；L4439～4456按平台形成CPU slice并进入core loader | 源码引用已知；实际model class、输入分支、加载attempt和fallback仍须producer记录，不能凭model_type推定 |
| `transformers/core_model_loading.py` / `c5b6bcdb6401a3cfdf825bc979d41ac3e7e075e09459021363dce5e68c54de22` | L953～976消费Future；L1236～1274 materialize/job；L1630～1636选择pool；L1717～1738目的device/提交；L1793非等待shutdown | 可以定位观察接点；任务ID、实际native TID、异常/取消/仍在运行必须从执行取得，不是从历史时间窗推断 |
| `transformers/integrations/accelerate.py` / `4469496da61fdc632faf9cacfc128729b12030eb03c5ef4bb70a66b6012b3a82` | L96字符串device_map规范化；L338非auto字典保持；L431/450参数目的设备 | 只证明源码中的logical device选择规则；不将logical/native/trace编号相等作为映射 |
| `torch/cuda/__init__.py` / `92f2d2434ce713d81f58aece36fe1bbc8fd9942973dbda7ba12009de30ddd885`；`streams.py` / `d346ee0d52d7bee80e3e355d38ceaf2730da62d74a2ed512e7fc8b393056d1b3` | init L1001/1019的current/default会lazy-init；streams L31包装与L117 ExternalStream不拥有外部生命周期 | 现stage的未初始化UNKNOWN政策有实际安装依据；Python包装对象/handle不能证明trace generation |
| `torch/include/c10/cuda/CUDAFunctions.h` / `343d0cd132554849db0825f03834912bb2d82ebd6785908662838452ad0dd84a`；`CUDAStream.h` / `214f041517a86b29bbb564655acc589ed46c3abb5039282e9c16992755a053d0` | Functions L95～96的copy+stream sync；Stream L19～49的pool/current区别及L229起default接口 | 安装header身份已知，但预处理宏/相关编译单元实际mode、二进制调用点仍未知。注释不能替代资格 |

特别保留两个反证：

- `shutdown(wait=False, cancel_futures=True)`不保证正在运行任务退出；提交循环还在后续
  `try/finally`之前，提交中途异常也不能假设已执行shutdown。runner旧的异常fallback
  不能据此抹掉前attempt。正常加载的已消费Future结果也不自动覆盖所有失败/跳过任务。
- snapshot只含两DLL的服务器hash/RECORD一致性，没有编译命令或调用点映射。即使以后
  得到PE imports，也只能证明导入候选；混合编译单元、动态解析或无实际调用绑定时，
  不能把整个模块标成LEGACY/PER_THREAD，更不能只凭NULL trace flag补值。

### 下一项最小动作与停止条件

**服务器现在没有新增操作。** 安装资料补证完成；不再重搜安装、不重传ZIP、不部署、
不跑旧controlled或模型。主窗口可以继续本地来源观察接口，而不等待完整性厂商认证：

1. 依据上述明确函数接点，设计/实现一个显式opt-in的加载attempt/task观察适配。
   记录pass/setup identity、实际model来源/loader源码hash、attempt_id、task_id、提交与
   job线程native TID、原调用成功/失败/取消/IN_FLIGHT和原始非同步marker。setup没有
   伪request；不导出权重、参数名或私有模型路径到公共测试。不增Future等待、sync、
   event，不改pool规模、异步开关、流选择或原加载fallback。
2. 用真实Python线程池/受控假张量在本地验证提交→job→Future及失败中断的**文件链**，
   并测试遗漏任务、重用TID、跨attempt、失败后仍运行及source hash冲突。仅记录原有
   操作；observer关闭时原结果不变，未终结任务不伪填COMPLETE。不得把测试里的线程
   或合成NVTX称为目标CUDA资格。
3. Canonical仍保留原始Raw；后续task marker只能先建立同PID/TID/trace clock的Host-call
   来源关联，再借实际correlation引用GPU activity。它不证明default隐式依赖、resource
   lifetime或zero loss。source的静态身份与运行观察分字段，UNKNOWN继续阻止对应S准入。
4. 在发出任何新增采集方案前，须把目标**必要调用点**的default/lifetime证据需求列明。
   如已有源码/实际API引用足以形成不依赖未知mode的相同closure证明，应显式说明并
   测试反例；否则保留阻塞，集中提出一次只针对这些模块/调用点的静态构建或二进制
   解析方案及能力边界。不要预先扩大到整栈资料，也不承诺一份imports就能解决。

本轮收口的是安装来源与接口可行性核查，没有新增生产descriptor/准入代码或schema，
也没有改变冻结合同。上述为7.42审计时点；后续本地实现见§8，不能当作目标运行证据。

## 8. 加载任务观察0.1 / producer0.4（7.43）

显式`record_load_tasks=True`仅允许与`model_setup`、stage及drain记录共同启用。
默认legacy入口不启用；目标source resolver检查Transformers5.17.0及§7三个loader
文件的精确SHA，确认原`spawn_materialize`函数来源后，只在一个加载attempt内临时
包住该函数的pool.submit接点，finally恢复。没有site-packages文件修改或全局线程跟踪。
检测并发观察scope冲突，其他提交线程不认领并记录issue。
源码验证同时编译已验字节（不执行模块）比较函数代码对象；拿到scope锁后再核原hook
对象/代码，避免读到其他观察器wrapper后错误恢复。reader固定三文件路径与hash集合。

合同版本：`exposedpath-load-task-ledger/0.1.0`、
`exposedpath-load-task-marker/0.1.0`、`hf-load-tasks/0.1.0`、
`exposedpath-gate8-producer-receipt/0.4.0`。原receipt0.1～0.3路径不变。

| 事实 | producer字段 / 来源 | 不允许的推断 |
|---|---|---|
| scope | pass identity、PID、父setup stage_id、source_descriptor及hash | setup不属于某个伪request |
| 加载尝试 | attempt_id=pass/parent/ordinal摘要、branch、原异常类型、实际返回类名称 | 返回类名称不是该model实现的源码资格 |
| job | task_id=attempt/ordinal摘要、提交native TID、执行native TID、线程实例ID | TID数值相同不证明同一生命周期；不按时间包含认领 |
| 状态 | SUBMITTED/IN_FLIGHT/COMPLETE/FAILED/CANCELLED/SUBMIT_FAILED；没有pool时UNOBSERVED_SYNC_CALLABLE | Future已消费不等于所有worker结束，HOST_JOB不是GPU completion |
| 封存 | AT_SEAL_NO_WAIT、原host clock、sealed_host_ns、issues | host clock不是trace clock；封存后晚结束不能回写已落盘证据 |

原函数参数、提交顺序、pool大小、Future对象、调用方消费、返回值/异常均保留；
没有额外Future.result/exception、join、shutdown、CUDA调用或stream切换。
同步deferred callable原样返回，明确未观察其执行；不能为了记录而偷偷消费。
旧load_model第一分支异常仍执行原fallback，但attempt身份分离；前attempt失败或任何
任务未闭合使观察/producer标INCOMPLETE。Pass0/1均观察任务，只有Pass1发非同步NVTX；
锁、hash、Python包装及marker有非零开销，尚无目标overhead证据，不宣称零扰动。

实际文件入口写全新目录：pass_identity、host_boundaries、drain_ledger、stage_ledger、
load_tasks及最后的receipt；逐文件bytes/hash，不循环引用、不覆盖输入。读取严格检查
版本/文件集合/hash、pass-parent-attempt-task身份及host/drain跨run混用。失败部分目录
无最终receipt不能作为成功；source校验失败在模型加载前停止。
`load_producer_observations`只验证此来源诊断链，不代替boundary/drain的Canonical资格。
既有科学file-chain0.5不接受producer0.4，因此不能静默丢掉load_tasks继续分析。

### 仍未完成的科学接线及最小验证义务

任务marker未来只可在同PID/native TID、可证trace clock及原record引用下关联Host API，
再按真实correlation关联activity；仍须逐调用点mode/context/stream lifetime及必要前驱
闭包证明，才能向S提交owner证据。当前不实现此准入，也不将安装hash、marker范围或
COMPLETE观察状态当作证明。default-mode=UNKNOWN、ownership/measurement=NOT_ASSESSED。
目标loader源码调用路径验证、线程marker实际落入trace、相关调用mode/lifetime及开销
均未执行；之后只补这些受影响Q0资格，历史Gate6 PASS不自动继承或撤销。

本地测试使用真实CPU线程池与受控模型/张量/marker替身，包含同线程多任务、并发多线程、
异常/取消、失败attempt仍运行而fallback成功、冻结快照不被晚完成改写、source冲突、
实际loader→producer→文件reader和跨run/hash/版本反例。不能称目标CUDA或Nsight验证。
服务器此刻没有新增操作，不交付部署包；Gate7 PASS，新Q0/Gate8 NOT_RUN。

只读review提出并修正封存半终态、锁前读取hook、thread_pool关键字、内存/磁盘来源及
来源文件集合检查缺口；分别先新增确定性失败回归。marker收尾后原子提交终态，
封存不等待、不回写，晚到错误不把先前IN_FLIGHT快照升级成功。最终定向81 passed。
最终CPU全量1323 passed/5 skipped（246.37s，本地Python3.12.7，nvcc隔离；5项既有CUDA
编译skip）；compileall、contract37/37内部一致性、Canonical边界及oracle静态独立性通过。
两轮review修复前的全量主动中止、不算通过；冻结MC/旧schema/Q0/科学实现零修改。

## 9. 必要调用点与有限停止点（7.44；不是新准入合同）

**结论：本地可闭合的是条件性规则，尚不能闭合目标模型的事实前提。** 不再添加一套
仅诊断的中间版本，不把mode猜成LEGACY，也不重复跑旧独立stream受控程序。没有新增
业务代码或S准入；下述唯一外部候选为一次限定静态调用来源核查，仍须另行授权执行。

本轮直接以`mode=ro&immutable=1`读取Gate7合格历史SQLite的白名单表，输入SHA256前后
均为`005cf068bff99c36585a91343d8841d12bb2cad41a94bdc9bc1478045691877c`，未读敏感metadata。
四个physical token sync rowid348/349/352/353皆为context1/stream7、Runtime返回0；
两个drain346/350为device sync，其stream字段4294967295不能当真实stream。
Memcpy共349条、同trace stream7、关联5个Host TID；相关349个stream sync的callchain
均null。inventory另有6/8/9/10/11/12等stream；18条event-create记录不能证明event依赖
已完整观察，flag枚举也不能直接当CUDA native创建flag。没有新task marker或可验证的
完整生命周期来源。以上仅旧输入兼容性事实，**不升级旧attempt/Q0资格**。

### 9.1 只保留影响目标W的调用点

| 调用点 | 必需事实与现有依据 | 最小未知 / 处置 |
|---|---|---|
| setup worker的tensor.to / materialize | §7精确loader源码、§8 task/attempt→native TID；将来须经同PID/TID原NVTX行→Runtime correlation→activity | 目标新observer未采集；旧worker不能补认领。失败attempt未结束时不闭合来源；不以Future或drain删除其历史 |
| warmup / measured的model.forward、argmax | 实际stage源码与未来同线程API引用；每个launch/copy须关联实际context/stream generation | 模型/库内部提交是否全在已证明scope、是否有其它thread/event前驱尚未有肯定依据；不能凭Python当前stream推出全部库操作 |
| token.cpu / DtoH→stream sync | 安装CUDAFunctions.h的copy+sync路径，旧Raw四个physical sync及API/correlation已知 | header不是目标二进制实际调用点。需要相关copy/sync实际入口及native→trace/lifetime映射；`_v3020`不证明legacy或PTDS |
| 原request-start device drain | 原函数、回执设计、旧物理device sync与成功返回已知 | drain证明先前工作完成，不证明owner、stream generation或完整W；不可变成截断历史的重置点 |
| 可能传入目标流的event/default边 | 只对目标context必要前驱递归检查；明确nonblocking且无传入event才能排除另一流 | 库event-create而无完整record/wait来源，不能以缺行证明无边；未知影响范围拒绝对应claim |

default生命周期不要求虚构cudaStreamCreate：legacy须绑定context存活区间；PTDS另须
thread实例及实际调用入口；显式nondefault须真实资源或合格source的持有区间。重用、
context reset、mixed-module mode冲突均不得按相同编号拼接。原始activity/owner保持。

### 9.2 mode无关的正例与反例（独立纸面预期，未授目标资格）

依据[CUDA 12.4.1官方stream语义](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/stream-sync-behavior.html)：
模式可按编译单元选择；legacy有blocking-stream隐式边，PTDS与thread/context关联。
混用时不能把整个进程当单个模式。这决定以下证明义务，而非要求全capture认证。

正例P：已由合格来源证明从相关context建立到s只存在同一线程的同一连续默认流，
无其它必要流/event/外部提交或早期未知前驱。X=[0,10)、Y=[20,30)，s=[25,35)。
所有可行LEGACY/PTDS解释均有W={X,Y}、terminal=Y；B hidden=15、exposed=5、tail=5，
sync内A wait=5、return-tail/residual=5。mode字段仍UNKNOWN；相同closure是条件性结论，
不是把UNKNOWN填为零或已知mode。A窗口其它类别须另据Host/API区间归属。

反例N1：worker默认流的X=[0,10)，成功device drain=[12,15)，随后main默认流Y=[20,30)，
s=[25,35)。LEGACY下W={X,Y}、hidden=15；PTDS且无传入边时W={Y}、hidden=5；两者
exposed=5、tail=5，A可相同。X早已完成仍改变B完整历史，不能以drain或低unknown掩盖。
这两个世界的真实physical mapping也可能不同，不能强行给二者都填相同stream ID。

反例N2：另一blocking流X在目标default提交Y之前已提交。LEGACY可能要求X，PTDS无边
时不要求；即使两者时间上不重叠也不能删X。明确nonblocking且无传入event时才能排除；
加入event wait又必须纳入。未证明生命周期/任务来源或scope完整性时，P的前提不成立。

所以，只比较两次假定mode运行得到相同数值不足以准入：还须覆盖所有可行mapping、
generation、mixed-mode及依赖解释，并有目标scope证据。现有材料不足；旧S明确
`DEFAULT_STREAM_MODE_UNKNOWN`与closed-prior非default门继续保留。若以后采用此
条件性等价准入，须版本化记录source支持域/证明输入和反例，不静默改旧schema。

### 9.3 一次限定补证候选与停止规则

**谁做下一步：** 主窗口已准备限域脚本/字节hash/传输与回件说明于忽略的本地交付索引，
协调窗口审查，用户手工执行时确认具体范围；不重复泛泛请求普通只读补证授权。本轮未执行。
这是一项有决策用途的候选，不是Gate的必经条件；无符号时不投入更多静态搜集。
不复制整包/模型，不导出Raw，不profile/export，不import Torch或初始化CUDA。

输入只限§7已hash的`c10_cuda.dll`与`torch_cuda.dll`及**已存在**的匹配符号/构建记录。
使用现有MSVC二进制检查工具，固定工具路径/版本/hash、两DLL原hash：

1. 只读PE imports/exports及已有debug-directory/PDB身份；收集涉及copy/stream sync、
   stream获取、event、context reset和动态入口解析的相关条目，不扫描其它安装目录。
2. 本次脚本到`/imports /exports /headers`即止，不反汇编。预期候选为
   `c10::cuda::stream_synchronize`→stream sync、`memcpy_and_sync`→copy+sync（可能内联
   无导出）、default/current stream helper→native来源；其余launch/event/context入口
   只提示需检查的前驱。若实际存在可解析符号/RVA，回件后才评估相关局部调用绑定是否
   值得做；无可用符号就停止。不全量反汇编、不下载PDB、不把imports当已执行的调用。
3. 新诊断目录保存命令、退出、字节hash和筛选结果；缺符号或动态/混合入口无法解析也
   是最终结果，不能伪填来源。现有checkout/环境/旧证据不变，不要求部署d5ff1da。

**能证明：** 被解析的具体静态调用点使用哪个入口、是否有候选mixed/dynamic路径；
若与实际调用链可绑定，可服务该调用的source descriptor。
**不能证明：** imports存在即实际执行、整个模型只有一种模式、无未捕获event、运行
线程/资源生命周期或collector零丢失。旧Raw callchain为空，单有imports仍不能合格。

一次回件后只允许两个终点：

- 找到相关调用点的完整source依据并可与目标scope关联：主窗口补必要版本化adapter与
  成对确定性测试，然后准备一次新路径资格验证（自然流、setup/worker/warmup/两request、
  原drain；独立W/oracle；不重采旧全矩阵）。source门/marker/correlation/lifetime/必要
  event任何冲突即停，不retry换构造。新结果只是受影响资格，不自动批准真实模型claim。
- 仅得到imports/无法绑定调用点：**静态路线就此结束**，不继续索取更多环境包。
  下一可裁决方案是一次目标调用路径的Engineering来源观察，可以UNKNOWN起步并只产
  诊断；不能循环要求先知道运行绑定才能采集运行绑定。若必须额外采集callchain或修改
  observation profile，应先核对目标2026.2.1精确参数、额外开销、预定义输出和停止点，
  单项审查后再执行，不要求完备性认证。不能以普通torch微程序
  已通过代替Qwen全部内部调用已证明，也不自动改变collector或研究支持域。

本轮终点：本地已有材料不足以解除目标mode/lifetime来源阻塞；服务器静态调用点核查
是唯一准备中的外部候选；准确脚本已交协调审查，未执行。静态读取的收益只在于判断
哪些相关入口可定位、是否应直接结束静态路线，不保证解除运行绑定未知。
Gate7 PASS，新Q0/Gate8 NOT_RUN；没有扩大研究claim或修改生产代码。

## 10. PE原件收口与一次Engineering来源观察提案（7.45）

**静态路线关闭，不再索取DLL、PDB或反汇编包。** 已直接读取
`pe_source_20260927T034417Z_826108098513436c84501b34bb4a7b77`的10文件，清单9项
bytes/hash/精确集合均匹配，清单SHA256
`4a6e2c241a5d4496b2fdf2368dbac8f39fad62c01f3fc840897e162fc255e3e5`。
receipt记录六条命令exit0、error=null、server f5edc64/仓库未变、dumpbin14.38.33135.0；
本地核的是回传报告，不是亲自运行服务器，也未取得/复算DLL本体。

| 原件位置 | 已观察事实 | 不可升级的结论 |
|---|---|---|
| c10 exports L81/82/103/131 | current/default helper RVA 0x3C360/0x3C440，memcpy_and_sync 0x5530，stream_synchronize 0x7AD0 | 有导出候选，不表示旧token实际经过该RVA |
| c10 imports L81～120 | cudart64_12.dll下含cudaMemcpyAsync、cudaStreamSynchronize及event入口；此表无_ptsz/_ptds命中 | 不足以判整进程/所有模块模式，不能替代实际调用链及传入stream值 |
| torch imports L29～30/49/52 | 导入c10的current/default、stream_synchronize、memcpy_and_sync | 只建立模块候选边，不是每次运行调用边 |
| 两headers L95起 | debug-directory只显示coffgrp，报告无CodeView/RSDS/PDB identity | 不能因此宣称系统绝无PDB，但不为本任务再扩搜索 |
| 两imports的GetProcAddress | 存在通用动态查找入口 | 不证明实际动态查找CUDA，也不证明不存在其它路径 |

静态证据已完成其决策用途：选定要观察的copy/sync/helper候选；无法补回旧Raw为空的
callchain，也无法证明实际default/context/thread生命周期。保留UNKNOWN/NOT_ASSESSED。
不继续仅靠读取更多静态文件寻求模型资格，旧evidence保持原状。

### 10.1 下一项本地准备与独立预期

拟准备**一次全新Engineering来源观察**，可从UNKNOWN启动，只输出来源诊断，
不接S/A/B/D资格门、不要求先有运行绑定才允许取得运行绑定。不是重跑旧controlled：

- 使用目标已固定Torch2.6+cu124和Transformers5.17来源；小CPU张量经实际
  `spawn_materialize`/`.to(cuda)`形成两个可编号task，沿已实现task观察入口记录。
  原Future按源程序需要消费；不改变真实模型loader的线程数/异步政策来强求结果。
- 两个小request在自然默认流执行确定性张量操作并产生各两个host-readable token；
  保留原request-start drain，不加用于调时/制造依赖的同步或stream切换。
  该小程序是来源诊断fixture，不是Qwen workload，不冒充模型内部全部路径资格。
- 独立源码预期先固定：2个不同task ID、同一setup父scope、一个明确attempt，2个
  request各1 start+2 token completion点。拟用两份CPU向量x=y=[0,…,15]经各自task拷贝；
  每次step的scores=x+y+step，独立整数算术预期argmax始终15，因此四个host token
  均为15；不从GPU/analyzer反算标准答案。worker实际TID不强求
  必须不同，不把调度结果当oracle。预期callchain应回答实际copy/sync来自哪个模块/RVA，
  **不预填**它必须命中c10导出，也不预定kernel数或用analyzer产生W标准答案。
- 接口最小工作仅为绑定已有task/stage与真实Raw行、保存callchain/module原引用；
  缺失、截断、未知模块/版本、跨PID/TID/correlation冲突保留诊断，不转成S ownership。
  拿到来源后再决定受影响Q0的W/terminal数值oracle；此次本身不授新版Q0资格。

以上是准备方案，不是已经实现/执行的小程序。下一项由主窗口完成必要本地入口及
确定性正反例；下述profile单项变更先交协调审查，未获采集授权前不部署或运行。

### 10.2 必须显式审查的profile差异

已直接读目标安装UserGuide.html：L805～817及1968～1980说明cudabacktrace类别与阈值、
需要CPU sampling；L714～725说明sample非none时cpuctxsw硬设同scope；L1293～1335说明
sample与Windows sampling-frequency。不是凭经验拼命令。

候选精确增量（仅提案，不是服务器执行命令）：

```text
--cudabacktrace=memory:0,sync:0
--sample=process-tree
--cpuctxsw=process-tree
--sampling-frequency=200
```

保留现有cuda,nvtx、process-tree CUDA范围、memory-usage=false、isr=false与collection/
export分离；不增加GPU metrics、WDDM或system-wide，不同时启用all-APIs等其它变化。
阈值0用于避免默认1000ns把短copy/sync调用系统性排除，不是零开销。只观察memory/sync
调用，不承诺覆盖所有kernel调用栈；200Hz只控制CPU采样频率，不限制API backtrace成本。
CPU context-switch tracing不能在此组合中声称仍为none。当前安装文档支持这些参数
形式；目标CLI尚未实际验证，若拒绝则停止，不静默换选项。

**风险与限制：** 额外CPU采样/调度事件/调用栈可能显著扰动时序；此前有BugCheck历史，
根因未证明，不能因本地文档检查就称该组合安全。该attempt不用于Pass0/Pass1性能比较、
overhead结论、A数值研究claim或历史attempt拼接；它只检查来源可观察性。是否执行这一
限定组合须明确审查；不能以“普通工程”自动重新打开此前关闭的采集功能。

### 10.3 一次观察的成功、失败与停止点

成功只表示：固定身份/版本、计划task/request/point记录齐全，目标copy/sync Runtime
可通过callchain ID→frame→模块身份/RVA关联，或以明确理由保留无法符号化的地址。
只有足以区分候选实际入口并与task/TID/physical活动关联的项，才形成后续source依据。
模块地址/导出名相近、imports命中或无警告不算运行绑定，更不算零丢失。

若参数不支持、进程/系统异常、目标调用callchain为空/截断、模块身份无法绑定，停止
本次，不以增加采样率、扩大类别或重跑碰运气补齐。保存失败/UNKNOWN，集中报告是
工具可观察性还是所选源路径不支持；后续是否改变支持域或collector另作单项裁决。

回传新run的固定源码/环境身份、两pass用途声明（若仅诊断Pass1须明确无性能parity
claim）、producer/task/stage/drain/host receipts、collection argv/退出、完整REP、独立
SQLite及export lineage、所用module/frame/callchain原表与派生引用、排除自身hash清单。
模型本体/私有环境不进入Git；原件不可变，诊断输出新目录。所有科学validity仍可UNKNOWN。
Gate7 PASS、新Q0/Gate8 NOT_RUN；本轮只完成PE实审与方案，不执行上述采集。

## 11. 本地来源 fixture 收口候选（7.46）

`exposedpath_v141.gate8_source_probe` 已实现静态prepare、纯argv构造、显式run入口及
独立目录文件读取；仅用CPU替身验证，尚未在目标Torch/CUDA/Nsight执行。它不接入
默认launcher、不加载Qwen、不执行profiler/export、不做自动重试或科学链放行。

验证：新增22项先补反例；最终五文件定向88 passed，CPU全量1345 passed/5 skipped
（247.16s；原Q0 CUDA编译项，nvcc明确隔离），compileall/contract37/Canonical7/oracle/
diff与相对链接检查通过。独立review发现的重哈希身份、发布失败伪接受、失败边界丢失
均先复现再修复并定点关闭。以上不含目标backend运行或真实调用栈证据。

- plan/result 为 `exposedpath-source-probe-{plan,result}/0.1.0`；profile为
  `gate8-source-backtrace/0.1.0`。prepare固定commit/clean、preflight原件hash、六个
  相关源码hash、构造与独立预期；run前再次检查源码、mask与Git，再比对物理UUID/PCI
  和唯一logical CUDA设备UUID。导入此模块/prepare本身不加载Torch或CUDA。
- `hf-source-probe/0.1.0` 使用load-task ledger/marker **0.2.0**及`source_probe`分支，
  不冒充`trust_remote_code`/`fallback`模型加载。旧hf-load-tasks/0.1.0和ledger/marker
  0.1.0原路径保持；未知profile或版本/分支混用拒绝。marker前缀仍V1，payload显式分版。
- fixture启动两个CPU向量的实际spawn_materialize任务，消费原Future后执行两个request。
  这是fixture自己的消费等待，不更改真实模型loader的非等待shutdown政策，也不证明
  Qwen加载全过程。复用runner统一host-readable token、D1、stage/drain；只保留已有
  两次request-start drain，不新增CUDA同步、流切换或事件来制造依赖。
- 保存plan/preflight/manifest/prompt/实际cuda probe、producer0.4及五sidecar、逐request
  host token记录和source receipt。reader核固定构造、PASS_FIELDS、源码/输入hash、
  request/repeat/边界与token记录、task来源版本；同步重哈希仍不能掩盖跨身份冲突。
  所有来源绑定仍UNKNOWN、measurement NOT_ASSESSED、Gate8/Q0 NOT_RUN；COMPLETE只表示
  该producer诊断构造完成，不表示已经获得调用栈、W(s)或正确A/B。
- 先写独立partial再发布；错误保留已有task/stage/request边界/drain及failure，拒绝
  partial/failure回执。缺文件、变更hash、错误token、错误身份和发布失败均不授通过。
  原trace/receipt和Gate6/7不改；旧scientific file-chain继续拒绝producer0.4。

### 11.1 历史候选：有额外风险的profile（7.47暂停，非当前待裁决项）

原minimal profile加task marker可回答“哪个Host task/thread调用”，但旧Raw的callchain
为空，不能回答copy/sync实际来自哪个模块/RVA；故不能用marker时间包含冒充函数调用边。
本候选只对需要此绑定的memory/sync请求backtrace，不要求所有来源一律取得调用栈。
可接受有模块身份与RVA而未符号化的frame；不因此追加PDB/反汇编调查。

| 固定参数 | 本次拟取得的证据/代价 |
|---|---|
| trace=cuda,nvtx | Runtime/activity原记录与task/request标记；不是dependency证明 |
| cudabacktrace=memory:0,sync:0 | copy/sync调用链，0阈值避免短调用被阈值过滤；可能显著增加开销 |
| sample=process-tree、sampling-frequency=200 | 目标Guide要求的backtrace前置；200Hz只限CPU采样频率，不限制CUDA栈采集成本 |
| cpuctxsw=process-tree | Guide规定随非none sample生效；不是沿用原“关闭ctxsw”配置 |
| cuda-memory-usage=false、cuda-trace-scope=process-tree、isr=false | 保留原限定；无metrics、WDDM、system-wide、stats/overwrite增量 |

**尚未授权执行。** 既往BugCheck 0x133根因未证明；低频、短fixture、timeout或Ctrl+C
都不保证操作系统不会再次异常。固定版本包和不执行的步骤可先本地准备；只有用户明确
接受这一个组合的风险后才实施部署和单次执行，没有隐含连续重试权限。参数拒绝、空/截断栈、未知模块绑定或进程/系统
异常即结束一次尝试，不提高采样率、不扩大类别、不自动回退或换collector。

候选步骤（仅供审查，当前不执行）：

1. 固定将来批准的完整执行commit、仓库clean、目标既有环境/preflight；不能自动跟随main。
   新`diagnostics/<source-probe-run>`保存plan，新`evidence/gate8/<source-probe-run>`保存采集。
2. 使用仓库Python运行`-m exposedpath_v141.gate8_source_probe prepare --output <new-plan-dir>
   --preflight <verified-preflight.json> --expected-commit <approved-sha> --run-id <unique-run>`。
3. 在固定checkout作为cwd调用纯`profile_argv(<absolute-nsys>,<repo-python>,<plan.json>,
   <new-capture-dir>)`取得结构化argv；builder要求capture-dir尚不存在。随后以**不覆盖**
   方式创建该新父目录，保存完整argv/来源版本后，人工按授权执行一次。不要把参数列表
   拼成shell字符串；`-m`必须从批准checkout解析。profile输出capture，子进程输出producer。
4. 退出后只保存事实；由协调检查回执后安排独立SQLite export及只读来源关联，不自动连跑。producer COMPLETE
   不替代REP/SQLite/callchain审计。本轮未实现新的callchain解析器或自动科学转换。
5. 回传整个新目录、collection退出/argv、原REP、producer所有文件、环境/源版本关联，
   后续如export则加独立lineage与完整SQLite。清单先快照输入集合并排除所有输出清单，
   不修改旧attempt。任何失败保留原件，不追认、不继续第二次profile。

这一候选不要求先解除UNKNOWN才能诊断；也不承诺一次观察可以解除default-mode或
lifetime未知。若仍不足，先给具体剩余证据与研究影响，再裁决支持域，停止宽泛取证。

## 12. 必要性重审：暂停profile，回到目标推断（7.47）

**调整：不再将module/RVA来源观察作为唯一下一步或科学验收普遍前置。** 保留本地
d62c818实现/测试、固定bundle及三脚本为未授权备用；不部署、不发送A/B/C操作，不再
要求用户作采样风险决定。此为执行优先级修正，不修改冻结语义或降低既有拒绝条件。

目标安装UserGuide关于cudabacktrace的两段（L805～817、1968～1980）及
[NVIDIA官方说明](https://docs.nvidia.com/nsight-systems/UserGuide/)区分了API调用取栈与
周期CPU采样：前者仍要求启用CPU sampling，但不是用200Hz周期样本保证命中全部kernel。
候选仅memory/sync，0阈值不保证完整栈；新增开销及历史BugCheck风险不能由低频消除。
因此“所有kernel都必须有CPU调用栈”不是本研究当前必要要求。

权威门与工程候选应分开：

- [Measurement Contract](measurement_contract_v0_2.md)的completion集合与default-stream
  条款（L80～93）要求submission、ownership、stream/event/default依赖及模式证据，
  没有将module/RVA/callchain规定为每条活动必需字段。S的`_add_default_stream_edges`
  使用活动、mode、flags与提交顺序；它不使用模块RVA来直接恢复边。
- [closed-prior amendment](gate8_closed_prior_amendment_v0_1.md)本版只支持连续nondefault、
  合法原owner及限定event路径。`gate8_closed_prior.load_admissions`检查lifetime引用、
  scope/generation与反证，不消费callchain。不能因找到调用栈就把默认流纳入该窄域。
- 当前真实模型接线仍有`STAGE_SOURCE_NOT_QUALIFIED`、
  `CLOSED_PRIOR_TARGET_SOURCE_NOT_QUALIFIED`及default-mode/lifetime未知。栈可能辅助
  找到实现入口，但不能单独证明传入stream、完整历史前驱、资源连续性或owner；现未
  找到一个已被证明**只能**靠模块/RVA解除的必要门。
- 原受控native明确流构造与独立oracle证据可按实际已证明部分复用；不重采整矩阵，
  不自动授新版本资格。旧模型Raw的同stream外观、成功drain或空栈仍不足以定义已获
  资格的默认流/跨worker支持域，暂停高风险方案不等于真实模型已经就绪。

**下一项具体只读工作（主窗口）：** 固定已有Raw原件与hash，只检查四个目标Token-ready
physical sync（历史row348/349/352/353）和两个原request-start drain（346/350）及其
必要前驱。沿现有source、NVTX/task、PID/TID/correlation、context/stream/event列每个
sync的“已证明事实／唯一关键缺口／可行解释是否改变W、terminal、A、B／最小补证”。
旧Raw没有新task marker必须标缺失，不能回填；不读取全环境metadata，不更改输入。

产物限制为一张紧凑差距表与低风险路径判定：优先复用已证明受控项，区分已有字段可
工程映射、需未来最小cuda,nvtx+task观测、以及确实需语义裁决的项。不能以“没调用栈”
单独判所有活动失败，也不能把边界/mode/闭包未知放行。若A在多种解释下看似相同但B
不同，只记录这一差异；当前S/派生拒绝门不删，任何新等价准入需显式版本化裁决。
没有具体缺口证明需要栈之前，不恢复source profile、不扩大调查或增加工具。

本轮仅文档/只读核查，无新测试、实现或采集；7.46测试是历史本地验证，不是本轮结果。
冻结Measurement Contract、S/A/B/Q0及Gate6/7原件未改，Formal协议/数据不受影响。
Gate7 PASS，新Q0/Gate8 NOT_RUN；服务器仍固定原版本，无新增用户服务器操作。
