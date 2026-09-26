# Gate8 eager 来源对齐 / G8-STAGE-OBS/0.1.0

2026-09-27；基线 f022520。已批准 closed-prior 方向内的工程接线，不改 W(s)、A/B、
completion 或研究质量门。Gate7 PASS；Gate8/新 Q0 NOT_RUN。无服务器部署/采集授权。

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
