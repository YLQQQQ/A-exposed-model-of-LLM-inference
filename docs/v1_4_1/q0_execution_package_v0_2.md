# ExposedPath Q0 执行包 v0.2

## 当前用途

本执行包把 Gate 2 已冻结的 23 个标准答案转换为可执行计划。当前阶段为 Engineering；编译成功、dry-run 或合成对照均不能判定 Q0 通过。只有获得 GPU 后，在目标 CUDA/Nsight observation stack 上完成全部必需 case 的真实采集、故障注入审计和 oracle 对照，Gate 6 才可能由 `BLOCKED` 改为 `PASS`。

## 文件职责

- `q0/oracle_cases_v0_2.json`：人工标准答案，禁止由 analyzer 重算。
- `q0/execution_manifest_v0_2.json`：23 个 case 的执行策略、稳定 label 和故障注入身份。
- `q0/cuda/exposedpath_q0.cu`：21 个 native seed 的最小 CUDA/NVTX 程序。
- `exposedpath_v141/q0_execution.py`：执行合同校验、编译命令（固定 `-arch=sm_89`）和 dry-run manifest。
- `docs/v1_4_1/contracts/q0_observed_schema_v0_2.json`：合成 observed 的严格输入合同。
- `exposedpath_v141/q0_synthetic.py`：从显式 case profile 构造 Canonical 事实，并调用正式 S/A/B。
- `exposedpath_v141/q0_evaluator.py`：不调用 S/A/B 的独立逐 case 对照器。
- `q0_run_manifest.json`：一次 GPU 执行计划，状态固定为 `PREPARED_NOT_EXECUTED`。

## 三类执行策略

1. `NATIVE_CUDA`：直接由受控 CUDA 程序制造同步行为。
2. `NATIVE_WITH_CANONICAL_FAULT`：先采集真实 seed，再对版本化派生副本执行预定义故障注入。原始 `.nsys-rep` 不可修改；变换前后必须分别记录哈希和操作类型。
3. `SYNTHETIC_CANONICAL`：仅用于硬件上无法稳定制造的 terminal tie 和 submission race。它验证 analyzer 的 fail-closed 语义，但不替代真实 observation stack 的正例覆盖。

这三类结果必须在最终报告中分开，不得把合成 case 描述为真实 GPU 观测。

## 无 GPU 操作

编译微程序：

```powershell
python -m exposedpath_v141 build-q0-microbench --nvcc "<nvcc路径>" --output "<输出binary>" --platform windows
```

Linux 将 `--platform` 改为 `linux`。该命令只编译，不运行 CUDA case；输出明确保持 `q0_execution_status: NOT_RUN`。

Gate 6 Q0 build contract amendment 之后，编译 argv 由 `build_q0_compile_command()` 统一固定加入一次 `-arch=sm_89`（不新增可变 arch 参数、不读取默认 arch、不接受环境变量注入），并在编译成功后自动写出 `<二进制>.build_receipt.json`（`receipt_version=exposedpath-q0-build-receipt/0.1.0`、完整 compile argv、nvcc `--version`、`gpu_arch=sm_89`、CUDA source/binary 的 path 与 SHA256）。receipt 已存在时拒绝覆盖，避免 stale receipt 与新 binary 错配。该 receipt 只承载构建 provenance，不进入 run/execution manifest。

设备能力探针同样已扩展：

```powershell
& "<Q0 binary>" --environment-json
```

输出新增 `can_map_host_memory`（来自 `cudaDevAttrCanMapHostMemory`）。它是 mapped-host capability 的唯一 gate；任何 Q0 正式 case 之前该值必须为 `1`，`unifiedAddressing` 不作为 gate。采集 receipt 的 `selected_gpu` 保存该字段，字段缺失或不为 1 一律 fail closed。

生成 dry-run：

```powershell
python -m exposedpath_v141 prepare-q0-run --output-dir "<新目录>" --binary "<Q0 binary>" --nsys "<nsys路径>" --platform windows --run-id q0-engineering-001 --cuda-visible-device "<GPU序号或UUID>"
```

dry-run 为每个 case 生成独立的 source manifest 和结构化 `argv`。每次必须显式选择一个物理 GPU，程序通过 `CUDA_VISIBLE_DEVICES` 将其映射为逻辑设备 0。采集范围由微程序中的 `cudaProfilerStart/cudaProfilerStop` 控制，Nsight 使用 `--capture-range=cudaProfilerApi`，不依赖动态 NVTX 字符串触发。dry-run 不执行 binary、Nsight 或 analyzer，不创建 `.nsys-rep`，并拒绝覆盖已有目录。

运行合成语义回归：

```powershell
python -m exposedpath_v141 run-q0-synthetic --output-dir "<新目录>"
```

该命令覆盖 23 个 case，经正式 `S -> A/B` 后交给独立 evaluator；输出只能是 `SYNTHETIC_ONLY`，Q0 状态固定为 `NOT_RUN`。它可提前发现语义实现错误，但不能验证真实 CUDA/Nsight 的可观察性、关联字段或时钟行为。

## 获得 GPU 后的固定顺序

1. 记录 GPU、driver、CUDA runtime、Nsight、OS、编译器和 git commit；先执行 observation preflight。
2. 按 `q0_run_manifest.json` 的参数数组逐 case 采集，每个 case 单独生成 Raw trace。
3. 核对 Raw SHA-256 后再生成 SQLite/Canonical；原始 trace 保持只读。
4. 对三项预定义 fault case 只变换派生副本并记录前后哈希；两个 synthetic-only case 单独运行。
5. 执行 `Canonical -> S -> A/B`，将稳定 label 标准化后交给独立 evaluator。
6. 任一必需 case 缺失、含糊处理错误、映射冲突或质量 gate 失败，Q0 均不得判为 `PASS`。

## 已知环境边界

Windows 的 `CL` 和 `_CL_` 是 MSVC 保留的隐式参数变量。本机 `CL` 当前被外部环境误设为编译器目录，因此编译入口只在 nvcc 子进程中移除这两个变量，不修改系统配置。正式平台资格检查必须重新记录该环境。
