# LLM 推理 nsys Profiling 项目

> PyTorch eager + NVTX + nsys → A/B 层暴露时延归因

## 项目结构

```
project/
  bench_eager.py                          # 核心 benchmark（NVTX + streaming + real/synthetic prompt）
  run_one.py                              # 单组运行
  run_matrix.py                           # 矩阵批量运行
  configs/
    workloads_16group.yaml                # 16 组矩阵 — RTX 6000 Ada (prompt 128~1024)
    workloads_16group_4090.yaml           # 16 组矩阵 — RTX 4090 (prompt 64~512)
  scripts/
    run_nsys_single.ps1                   # 单组 nsys profile
    run_nsys_matrix.ps1                   # 批量 nsys profile → .nsys-rep + .sqlite
    batch_accounting.ps1                  # 一键 A/B 归因 + 矩阵汇总
    export_nsys_sqlite.ps1                # 手动导出 sqlite（备用）
  analysis/
    exposed_accounting.py                 # A/B 层暴露时延归因
    summarize_matrix.py                   # 矩阵结果汇总 JSON
    parse_nsys_sqlite.py                  # sqlite → CSV/JSON（诊断用）
  requirements.txt
  README.md
```

---

## 1. 环境准备

### 1.1 前置要求

- Windows Server / 10 / 11 + PowerShell
- Python 3.10+，CUDA Toolkit，NVIDIA Nsight Systems 2025.6+
- GPU：RTX 6000 Ada (48GB) 或 RTX 4090 (24GB)

### 1.2 nsys 路径

```powershell
$nsysDir = "你的Nsight Systems路径\target-windows-x64"
$env:Path = "$nsysDir;$env:Path"
nsys --version
```

### 1.3 虚拟环境

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
python -c "import torch; print(torch.cuda.is_available())"
```

### 1.4 模型下载

```powershell
$env:HF_ENDPOINT = "https://hf-mirror.com"
pip install huggingface_hub
hf download Qwen/Qwen2.5-1.5B-Instruct `
    --local-dir "C:\Users\Wsn1\YLQ_test\models\Qwen2.5-1.5B-Instruct"
```

---

## 2. 单组测试

```powershell
# 普通测试
python bench_eager.py `
    --model-path "C:\Users\Wsn1\YLQ_test\models\Qwen2.5-1.5B-Instruct" `
    --prompt "What is the capital of France?" `
    --output-len 16 --streaming `
    --warmup-iters 5 --repeat-iters 10 --gpu 0 `
    --output-dir ".\results\test"

# nsys 采集
.\scripts\run_nsys_single.ps1 `
    -ModelPath "C:\Users\Wsn1\YLQ_test\models\Qwen2.5-1.5B-Instruct" `
    -Prompt "What is the capital of France?" `
    -BatchSize 1 -OutputLen 16 -Streaming `
    -OutDir ".\nsys_results\test" -RunName "test" `
    -WarmupIters 5 -RepeatIters 10 -Gpu 0
```

---

## 3. 矩阵实验

### 3.1 6000 Ada（48GB）

```powershell
# 正向 (w01 → w16)
.\scripts\run_nsys_matrix.ps1 `
    -ModelPath "C:\Users\Wsn1\YLQ_test\models\Qwen2.5-1.5B-Instruct" `
    -WorkloadYaml "configs\workloads_16group.yaml" `
    -OutputRoot ".\nsys_matrix_6000ada" `
    -WarmupIters 5 -RepeatIters 10 -Gpu 0 -Streaming

# 逆向 (w16 → w01)
.\scripts\run_nsys_matrix.ps1 `
    -ModelPath "C:\Users\Wsn1\YLQ_test\models\Qwen2.5-1.5B-Instruct" `
    -WorkloadYaml "configs\workloads_16group.yaml" `
    -OutputRoot ".\nsys_matrix_6000ada" `
    -WarmupIters 5 -RepeatIters 10 -Gpu 0 -Streaming -Reverse

# 一键正向+逆向 (run_all_nsys_matrix.ps1)
.\scripts\run_all_nsys_matrix.ps1 `
    -ModelPath "C:\Users\Wsn1\YLQ_test\models\Qwen2.5-1.5B-Instruct" `
    -WorkloadYaml "configs\workloads_16group.yaml" `
    -OutputRoot ".\nsys_matrix_6000ada" `
    -WarmupIters 5 -RepeatIters 10 -Gpu 0 -Streaming

.\scripts\batch_accounting.ps1 -ResultsDir ".\nsys_matrix_6000ada"
```

### 3.2 RTX 4090（24GB）

```powershell
# 正向 (w01 → w16)
.\scripts\run_nsys_matrix.ps1 `
    -ModelPath "C:\Users\Wsn1\YLQ_test\models\Qwen2.5-1.5B-Instruct" `
    -WorkloadYaml "configs\workloads_16group_4090.yaml" `
    -OutputRoot ".\nsys_matrix_4090" `
    -WarmupIters 5 -RepeatIters 10 -Gpu 1 -Streaming

# 逆向 (w16 → w01)
.\scripts\run_nsys_matrix.ps1 `
    -ModelPath "C:\Users\Wsn1\YLQ_test\models\Qwen2.5-1.5B-Instruct" `
    -WorkloadYaml "configs\workloads_16group_4090.yaml" `
    -OutputRoot ".\nsys_matrix_4090" `
    -WarmupIters 5 -RepeatIters 10 -Gpu 1 -Streaming -Reverse

# 一键正向+逆向
.\scripts\run_all_nsys_matrix.ps1 `
    -ModelPath "C:\Users\Wsn1\YLQ_test\models\Qwen2.5-1.5B-Instruct" `
    -WorkloadYaml "configs\workloads_16group_4090.yaml" `
    -OutputRoot ".\nsys_matrix_4090" `
    -WarmupIters 5 -RepeatIters 10 -Gpu 1 -Streaming

.\scripts\batch_accounting.ps1 -ResultsDir ".\nsys_matrix_4090"
```

### 3.3 矩阵参数

| | 6000 Ada | RTX 4090 |
|------|------|------|
| prompt_len | 128, 256, 512, 1024 | 128, 256, 512, 1024 |
| batch_size | 1, 2, 4, 8 | 1, 2, 4, 8 |
| output_len | 16 | 16 |
| warmup | 5 | 5 |
| repeat | 10 | 10 |
| 总计 | 16 组 | 16 组 |

所有组共用同一段约 1000 词英文文本，tokenize 后按 `prompt_len` 截断。同 `prompt_len` 的输入完全一致。

---

## 4. 输出文件

### 单组输出

```
nsys_matrix/<timestamp>/<workload_id>/
  ├── *.nsys-rep          nsys profile
  ├── *.sqlite             nsys export
  ├── results.jsonl        benchmark 结果
  ├── summary.json
  ├── results.csv
  ├── command.txt
  └── accounting/
      ├── accounting_result.json   A/B 层完整结果
      ├── a_metrics_summary.csv    A 层 CSV
      ├── b_provenance_prefill.csv B 层 prefill 明细
      └── b_provenance_decode.csv  B 层 decode 明细
```

### 矩阵汇总

```
matrix_summary.json
  每条记录：hardware + workload + benchmark_sanity + A 层 (mean±std) + B 层
```

---

## 5. A/B 层指标

### A 层 — "谁暴露了端到端时延"

遍历 CPU 时间线上 CUDA API，5 项互斥不重叠：

| 指标 | 含义 |
|------|------|
| **A_submit** | CPU 向 GPU 提交任务（所有非 sync API） |
| **A_device_compute** | GPU kernel 在关键路径上的时间 |
| **A_memory_transfer** | memcpy 在关键路径上的时间 |
| **A_host_runtime** | CPU + GPU 同时空闲的间隙 |
| **A_sync_residual** | sync API 中 GPU 已空闲后的残余等待 |

```
T_phase = A_device + A_memory + A_submit + A_host + A_sync
每指标输出 mean ± std + pct + CV
```

### B 层 — "暴露的 GPU 计算被什么阻塞了"

对每个 `A_device_compute` 段，追溯 `[submit → exposed_start]`：

| 指标 | 含义 |
|------|------|
| **self_block** | kernel 自己跑在 sync 前面的部分 |
| **kernel_block** | 同 stream 其他 kernel 排队 |
| **memory_block** | memcpy 排队 |
| **device_gap** | stream 空闲间隙 |

---

## 6. NVTX 标签结构

```
prepare_input   ← tokenizer（真实 prompt 模式，不在 core inference）
full_request    ← 推理边界
  prefill       ← 1× model() + TTFT sync
  decode        ← N× model() + per-step sync (streaming)
    decode_step_i  ← 单个 token
```

warmup 无 NVTX，不参与归因。`prompt_len` 相同 → 输入 token 完全一致。

---

## 7. 设计决策

- **真实 prompt**：16 组矩阵用同一个约 1000 词英文文本，tokenize 后截断；同 `prompt_len` 的组输入一致
- **streaming**：每 decode step 有 sync（模拟真实逐 token 返回）
- **memory_transfer ≈ 0**：纯 GPU resident benchmark，无 H2D/D2H
- **偏差校验**：每指标输出 mean ± std + CV，max_dev > 10% 标记 UNSTABLE
- **GPU 选择**：`-Gpu 0` = 6000 Ada，`-Gpu 1` = 4090
- **不要 `--capture-range`**：会导致第一轮异常
- **不要 `--gpu-metrics-device`**：Windows 需管理员权限
