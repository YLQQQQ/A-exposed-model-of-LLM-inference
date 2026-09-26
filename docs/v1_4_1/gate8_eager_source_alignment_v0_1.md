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

## 4. 剩余最小动作 / 停止点

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
