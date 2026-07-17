# LLM 推理 nsys Profiling 项目生成说明

> 目标：让 Claude Code 根据本文档生成一个完整、可运行、可在 Windows 服务器上用 `nsys` 采集 trace 的 PyTorch eager LLM 推理 profiling 项目。  
> 当前阶段重点是：**先跑通 NVTX + CUDA API + GPU kernel / memory trace**，为后续 raw / hidden / exposed latency accounting 做准备。  
> 不要求第一版就实现完整 exposed latency accounting 算法。

---

## 1. 当前阶段的实验定位

本项目服务于一个系统/体系结构方向研究：

**面向本地私有与资源受限单设备 LLM 推理的端到端暴露时延归因。**

当前阶段不是做普通 benchmark，也不是追求最快推理速度，而是要建立稳定的 trace 采集闭环：

1. 使用 PyTorch eager baseline 跑 LLM 推理。
2. 使用 NVTX 标出主要阶段。
3. 使用 `nsys` 采集：
   - NVTX ranges
   - CUDA API calls
   - GPU kernels
   - Memcpy / memory operations
   - OS runtime events，可选但建议打开
4. 导出 `.sqlite`。
5. 解析出结构化 CSV，为后续 raw / hidden / exposed 分析准备数据。

---

## 2. 硬件与软件环境

### 2.1 硬件

当前主要平台：

| GPU | 角色 |
|---|---|
| RTX 6000 Ada 48GB | 主实验平台，跑完整 workload matrix |
| RTX 4090 24GB | 对比平台，跑代表性 workload matrix |

### 2.2 系统

服务器系统：

```text
Windows
PowerShell
CUDA
PyTorch
Nsight Systems / nsys
Python 3.10+
```

### 2.3 模型

调试模型：

```text
Qwen2.5-1.5B-Instruct
FP16
```

正式主实验模型：

```text
Qwen2.5-3B-Instruct
FP16
```

推荐模型本地路径示例：(服务器下载路径)

```text
C:\Users\Wsn1\YLQ_TEST\models\Qwen2.5-3B-Instruct
```

正式实验前，模型应提前下载到服务器本地，避免把网络下载、缓存初始化等因素混入实验。

---

## 3. 实验边界说明

### 3.1 当前主窗口：core inference

当前阶段主测量窗口只关注：

```text
full_request
  prefill
  decode
    decode_step_i
```

第一版 NVTX 只需要标：

```text
full_request
prefill
decode
decode_step_i
```

这样足够支持预实验，能够先观察：

- prefill / decode 阶段划分是否正确；
- TTFT / TPOT 是否基本合理；
- nsys trace 是否能稳定采集；
- CUDA API / GPU kernel / memory operation 是否能与 NVTX 阶段对应。


## 4. 输出指标原则

第一版 benchmark 脚本不需要输出过多复杂指标。

### 4.1 benchmark 阶段只输出 sanity metrics

只需要输出这些基础指标：（需要选择指定单块gpu，如GPU0或者GPU1）

```text
run_name
prompt_len
batch_size
output_len
prefill_latency_ms
decode_latency_ms
full_latency_ms
ttft_ms
tpot_ms
gpu_name
cuda_version
torch_version
transformers_version
```

这些指标只是用于判断实验是否正常，不是论文最终归因结果。

### 4.2 不要在 benchmark 阶段计算这些指标

第一版不要在 `bench_eager.py` 中计算：

```text
A_host_runtime
A_submit
A_device_compute
A_memory_transfer
A_sync_residual
raw time
hidden time
exposed time
coverage
residual
provenance motif
```

这些应由后续 trace 解析与 accounting 脚本基于 nsys sqlite 计算。

### 4.3 nsys 解析阶段重点保留字段

从 nsys sqlite 解析出的事件至少应尽量包含：

```text
start_ns
end_ns
duration_ns
event_type
name
stream_id
correlation_id
process_id
thread_id
nvtx_range
```

---

## 5. 项目生成 Prompt 1：生成完整项目

将下面整段直接发给 Claude Code。

```text
你是一个资深系统性能实验工程师。请帮我生成一个完整可运行的 LLM 推理 nsys profiling 项目。

我的研究目标：
使用 PyTorch eager baseline 对本地单卡 LLM 推理进行端到端 trace 采集，后续用于 raw / hidden / exposed latency accounting。当前阶段只需要完成稳定采集、基础 NVTX 标注、结构化结果输出和 nsys profile，不要求实现完整 exposed accounting 算法。

当前阶段采集重点：
1. NVTX ranges
2. CUDA API calls
3. GPU kernels
4. Memcpy / memory operations
5. OS runtime events，可选但建议采集

硬件：
- RTX 6000 Ada 48GB
- RTX 4090 24GB

系统：
- Windows 服务器
- 已安装 Python、CUDA、PyTorch、Nsight Systems / nsys
- 项目应兼容 Windows PowerShell

模型：
- 调试模型：Qwen2.5-1.5B-Instruct
- 正式模型：Qwen2.5-3B-Instruct
- 精度：FP16
- 使用本地模型路径运行，例如 D:\models\Qwen2.5-3B-Instruct

强约束：
1. 使用 PyTorch eager。
2. 不使用 torch.compile。
3. 不使用 CUDA Graph。
4. 不使用 vLLM。
5. 不使用 model.generate()。
6. 不把 tokenizer 时间计入 core inference 主窗口。
7. 使用 synthetic input_ids。
8. 使用 model.eval()。
9. 使用 torch.inference_mode()。
10. 不要在每个 decode step 后 torch.cuda.synchronize()。
11. 只在 benchmark 边界同步。
12. NVTX 第一版只需要标注：
    - full_request
    - prefill
    - decode
    - decode_step_i
13. 后续可扩展 tokenization / prepare / postprocess，但当前先保持简单。
14. benchmark 脚本只输出基础 sanity metrics，不要在 benchmark 阶段计算 exposed latency、hidden latency、A_submit、A_device_compute、coverage、residual 或 provenance motif。

请生成完整项目，包含：

project/
  bench_eager.py
  run_one.py
  run_matrix.py
  configs/
    workloads_6000ada_full.yaml
    workloads_4090_representative.yaml
    workloads_test.yaml
  scripts/
    run_nsys_single.ps1
    run_nsys_matrix.ps1
    export_nsys_sqlite.ps1
  analysis/
    parse_nsys_sqlite.py
  requirements.txt
  README.md

bench_eager.py 要求：
1. 支持参数：
   --model-path
   --prompt-len
   --batch-size
   --output-len
   --warmup-iters
   --repeat-iters
   --dtype fp16
   --device cuda
   --output-dir
   --run-name

2. 加载模型：
   AutoModelForCausalLM.from_pretrained(
       model_path,
       torch_dtype=torch.float16,
       device_map="cuda",
       trust_remote_code=True
   )

3. 使用 synthetic input_ids：
   - shape = [batch_size, prompt_len]
   - seed 固定
   - token id 范围合法
   - attention_mask 全 1
   - 不把 tokenizer 放进主测量窗口

4. 手写推理：
   - prefill: model(input_ids, attention_mask, use_cache=True)
   - decode: 循环 output_len 次，每次输入上一步 token 和 past_key_values
   - greedy argmax
   - 不使用 generate()

5. NVTX 标注：
   - full_request
   - prefill
   - decode
   - decode_step_i

6. 输出基础 sanity metrics：
   - run_name
   - prompt_len
   - batch_size
   - output_len
   - prefill_latency_ms
   - decode_latency_ms
   - full_latency_ms
   - ttft_ms
   - tpot_ms
   - gpu_name
   - cuda_version
   - torch_version
   - transformers_version

7. warmup 不记录。
8. repeat 每次单独记录。
9. 每次 repeat 前 reset_peak_memory_stats。
10. 输出：
    - results.jsonl
    - summary.json
    - results.csv

11. 如果 OOM：
    - 捕获 RuntimeError
    - 输出 traceback
    - 写入 failed.json
    - 退出码非 0

workloads_test.yaml 只放一组：
- id: test_512_b1_o128
  prompt_len: 512
  batch_size: 1
  output_len: 128

6000 Ada full matrix 放 16 组：
1: prompt 128, batch 1, output 128
2: prompt 512, batch 1, output 128
3: prompt 2048, batch 1, output 128
4: prompt 4096, batch 1, output 128
5: prompt 512, batch 2, output 128
6: prompt 512, batch 4, output 128
7: prompt 512, batch 8, output 128
8: prompt 512, batch 16, output 128
9: prompt 128, batch 16, output 128
10: prompt 2048, batch 4, output 128
11: prompt 2048, batch 8, output 128
12: prompt 4096, batch 2, output 128
13: prompt 128, batch 1, output 512
14: prompt 512, batch 1, output 512
15: prompt 512, batch 4, output 512
16: prompt 2048, batch 1, output 512

4090 representative matrix 放 10 组：
1, 2, 3, 4, 5, 7, 9, 10, 13, 15

run_matrix.py 要求：
- 读取 yaml
- 逐组调用 bench_eager.py
- 每组单独 output_dir
- 某组失败不影响后续组
- 记录 failed_workloads.json
- 保存每组 command.txt

PowerShell 脚本要求：
1. run_nsys_single.ps1：
   - 输入模型路径、prompt_len、batch_size、output_len、out_dir、run_name
   - 使用 nsys profile
   - trace=cuda,nvtx,osrt
   - cuda-memory-usage=true
   - gpu-metrics-device=all
   - force-overwrite=true
   - stats=true
   - 输出 .nsys-rep

2. run_nsys_matrix.ps1：
   - 读取 workload yaml
   - 每组单独 nsys profile
   - 失败不中断
   - 每组保存 command.txt

3. export_nsys_sqlite.ps1：
   - 输入结果目录
   - 遍历所有 .nsys-rep
   - 执行 nsys export --type sqlite

analysis/parse_nsys_sqlite.py 要求：
- 输入 sqlite 文件
- 自动列出所有表
- 尽量解析：
  - NVTX ranges
  - CUDA API calls
  - GPU kernels
  - memcpy events
  - OS runtime events
- 不同 nsys 版本表名可能不同，所以要健壮
- 表不存在就 warning，不要崩溃
- 输出：
  - tables.json
  - nvtx_ranges.csv
  - cuda_api.csv
  - gpu_kernels.csv
  - memcpy.csv
  - osrt.csv，如果可用
  - timeline_summary.json

README 要写清楚：
1. 如何安装依赖
2. 如何先跑一组普通测试
3. 如何先跑一组 nsys 测试
4. 如何跑 workloads_test.yaml
5. 如何跑 6000 Ada full matrix
6. 如何跑 4090 representative matrix
7. 如何导出 sqlite
8. 如何解析 sqlite
9. 为什么 tokenizer 暂时不计入 core inference
10. 为什么第一版 NVTX 只标 prefill 和 decode
11. benchmark 输出只是 sanity metrics，正式 raw / hidden / exposed accounting 后续由 sqlite trace 解析脚本完成

请直接输出所有文件的完整内容，不要省略。
```

---

## 6. 项目生成 Prompt 2：代码审查与修复

Claude Code 生成项目后，继续发送下面这段，让它自检并修复。

```text
请你现在像代码审查员一样检查刚才生成的整个项目。

重点检查：
1. Windows PowerShell 路径是否正确。
2. nsys 命令在 Windows 下是否可运行。
3. bench_eager.py 是否真的没有使用 model.generate()。
4. decode 是否真的使用 past_key_values。
5. 是否只在 benchmark 边界 torch.cuda.synchronize()。
6. 是否没有每个 decode step 都 synchronize。
7. synthetic input_ids 是否不会超过 vocab_size。
8. Qwen2.5 模型是否能正常支持 use_cache=True。
9. FP16 加载是否正确。
10. results.jsonl、summary.json、results.csv 是否都会生成。
11. OOM 后是否会写 failed.json 并退出非 0。
12. run_matrix.py 是否能在某组失败后继续后面的 workload。
13. nsys 输出目录是否清晰。
14. sqlite export 是否不会覆盖错文件。
15. parse_nsys_sqlite.py 是否能兼容不同 nsys 版本的表名差异。
16. README 中的命令是否和真实文件名一致。
17. benchmark 阶段是否只输出基础 sanity metrics，没有提前计算 A 层归因。
18. nsys 解析阶段是否保留 NVTX、CUDA API、GPU kernel、memcpy 和 OSRT 相关数据。

如果发现问题，请直接给我修复后的完整文件内容。
不要只描述问题，必须给出可复制替换的代码。
```

---

## 7. 项目生成 Prompt 3：生成最终运行命令

最后发送下面这段，让 Claude Code 输出你服务器上实际要执行的命令。

```text
请基于最终项目，给我一份 Windows 服务器上的实际运行命令清单。

我的模型路径假设为：
D:\models\Qwen2.5-3B-Instruct

我的项目路径假设为：
D:\llm_nsys_project

要求按顺序给出：

第一步：创建环境并安装依赖。

第二步：先不使用 nsys，跑一组普通测试：
prompt_len=512
batch_size=1
output_len=128
warmup_iters=2
repeat_iters=3

第三步：确认普通测试输出哪些文件，如何判断结果正常。

第四步：使用 nsys 跑同一组测试。

第五步：导出 sqlite。

第六步：解析 sqlite。

第七步：如果单组测试正常，再跑 workloads_test.yaml。

第八步：如果 workloads_test.yaml 正常，再跑 6000 Ada full matrix。

第九步：如果换到 4090，再跑 4090 representative matrix。

要求：
1. 所有命令都用 PowerShell 格式。
2. 每一步都给出完整命令。
3. 不要使用 Linux bash 命令。
4. 不要省略路径。
5. 说明每一步成功后应该看到什么输出文件。
6. 明确说明：普通测试只用于确认 benchmark 逻辑，正式 trace 分析以 nsys sqlite 导出的 NVTX / CUDA API / GPU kernel / memcpy / OSRT 数据为准。
```

---

## 8. 推荐实际执行顺序

你本人的实际操作顺序建议如下。

### 8.1 先用小模型调通

建议先用：

```text
Qwen2.5-1.5B-Instruct
prompt_len=512
batch_size=1
output_len=128
warmup_iters=2
repeat_iters=3
```

目的：

- 检查模型能否加载；
- 检查 synthetic input_ids 是否正常；
- 检查 prefill / decode 是否能跑通；
- 检查结果文件是否生成；
- 检查 NVTX 是否能在 nsys 里看到。

### 8.2 再用正式模型单组测试

正式模型：

```text
Qwen2.5-3B-Instruct
FP16
```

先跑：

```text
prompt_len=512
batch_size=1
output_len=128
```

如果这组正常，再进入矩阵实验。

### 8.3 再跑 workloads_test.yaml

`workloads_test.yaml` 只保留一组，用于测试 `run_matrix.py` 和 `run_nsys_matrix.ps1` 是否能正常调度。

### 8.4 最后跑大矩阵

RTX 6000 Ada：

```text
workloads_6000ada_full.yaml
16 组
```

RTX 4090：

```text
workloads_4090_representative.yaml
10 组
```

---

## 9. 6000 Ada 完整 workload matrix

| 组别 | prompt_len | batch_size | output_len | 目的 |
|---:|---:|---:|---:|---|
| 1 | 128 | 1 | 128 | 短 prompt / 小 batch |
| 2 | 512 | 1 | 128 | 中等 prompt baseline |
| 3 | 2048 | 1 | 128 | 长 prompt |
| 4 | 4096 | 1 | 128 | 超长 prompt |
| 5 | 512 | 2 | 128 | batch scaling |
| 6 | 512 | 4 | 128 | batch scaling |
| 7 | 512 | 8 | 128 | batch scaling |
| 8 | 512 | 16 | 128 | 高 batch，若 OOM 则记录失败 |
| 9 | 128 | 16 | 128 | 短 prompt 高 batch |
| 10 | 2048 | 4 | 128 | 长 prompt 中 batch |
| 11 | 2048 | 8 | 128 | 长 prompt 高 batch |
| 12 | 4096 | 2 | 128 | 超长 prompt 中 batch |
| 13 | 128 | 1 | 512 | decode stress |
| 14 | 512 | 1 | 512 | decode stress |
| 15 | 512 | 4 | 512 | batch + decode |
| 16 | 2048 | 1 | 512 | prefill + decode 长链 |

---

## 10. 4090 代表性 workload matrix

| 组别 | prompt_len | batch_size | output_len | 目的 |
|---:|---:|---:|---:|---|
| 1 | 128 | 1 | 128 | 小请求 baseline |
| 2 | 512 | 1 | 128 | 标准 baseline |
| 3 | 2048 | 1 | 128 | 长 prompt |
| 4 | 4096 | 1 | 128 | 超长 prompt |
| 5 | 512 | 2 | 128 | batch 起点 |
| 7 | 512 | 8 | 128 | 高 batch |
| 9 | 128 | 16 | 128 | 短 prompt 高 batch |
| 10 | 2048 | 4 | 128 | 长 prompt + batch |
| 13 | 128 | 1 | 512 | decode stress |
| 15 | 512 | 4 | 512 | batch + decode |

---

## 11. 运行结果应该包含什么

### 11.1 普通 benchmark 输出

每组结果目录应包含：

```text
results.jsonl
summary.json
results.csv
command.txt
```

如果 OOM 或失败，应包含：

```text
failed.json
```

### 11.2 nsys 输出

每组 nsys 结果目录应包含：

```text
*.nsys-rep
```

导出后应包含：

```text
*.sqlite
```

### 11.3 sqlite 解析输出

解析后应包含：

```text
tables.json
nvtx_ranges.csv
cuda_api.csv
gpu_kernels.csv
memcpy.csv
osrt.csv
timeline_summary.json
```

其中 `osrt.csv` 可以是可选输出，如果当前 nsys 版本或 trace 配置没有对应表，不应让程序崩溃。

---

## 12. 单组测试成功的判断标准

一组普通测试成功，应满足：

1. 程序正常退出。
2. 没有 OOM。
3. `results.jsonl` 每行对应一次 repeat。
4. `summary.json` 中有 prefill、decode、full latency。
5. `prefill_latency_ms > 0`。
6. `decode_latency_ms > 0`。
7. `tpot_ms > 0`。
8. GPU 名称正确识别。

一组 nsys 测试成功，应满足：

1. 生成 `.nsys-rep`。
2. 能成功导出 `.sqlite`。
3. 解析后能看到 NVTX ranges。
4. 解析后能看到 CUDA API 或 GPU kernel 表。
5. `prefill` 和 `decode` 的 NVTX range 能对应到 GPU 活动。

---

## 13. 注意事项

### 13.1 `.venv` 不建议直接复制

即使本地和服务器都是 Windows，也不建议复制 `.venv`。

推荐做法：

```powershell
pip freeze > requirements.txt
```

到服务器后重新创建：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

项目代码可以复制，虚拟环境建议重建。

### 13.2 模型必须提前下载到服务器本地

正式实验不要边下载边运行。

推荐：

```text
D:\models\Qwen2.5-3B-Instruct
```

运行时使用：

```powershell
--model-path "D:\models\Qwen2.5-3B-Instruct"
```

### 13.3 不要让 Claude Code 顺手优化 baseline

必须保持 baseline 干净：

```text
PyTorch eager
FP16
synthetic input_ids
manual prefill/decode
no generate()
no torch.compile
no CUDA Graph
no vLLM
```

否则后面看到的指标差异可能来自代码优化，而不是硬件、模型或 trace 归因。

### 13.4 第一版 NVTX 边界可以简单

预实验阶段：

```text
full_request
prefill
decode
decode_step_i
```

已经足够。

正式论文分析前再扩展：

```text
full_request
prepare
prefill
decode
postprocess
```

如果要做用户端完整端到端，再加入：

```text
tokenization
detokenization
```

---

## 14. 后续阶段：从 trace 到 exposed accounting

当前项目只完成 trace 采集与基础解析。

后续应新增 accounting 脚本，从 sqlite 解析结果中计算：

```text
raw time
hidden time
exposed time
A_submit
A_device_compute
A_memory_transfer
A_sync_residual
coverage
residual
Top-K provenance motifs
```

建议后续文件结构可以扩展为：

```text
analysis/
  parse_nsys_sqlite.py
  build_timeline.py
  exposed_accounting.py
  provenance_motifs.py
  plot_figures.py
```

但第一阶段不要一次性做太多，先确保：

```text
能跑
能采
能导出
能解析
能看到 prefill / decode 对应的 CUDA / GPU 活动
```

---

## 15. 最终结论

当前最稳流程是：

```text
1. 让 Claude Code 生成项目
2. 让 Claude Code 自检修复
3. 让 Claude Code 给出 Windows PowerShell 运行命令
4. 本地/服务器重建 .venv
5. 提前下载模型到服务器
6. 先跑 Qwen2.5-1.5B 单组普通测试
7. 再跑 Qwen2.5-3B 单组普通测试
8. 再跑同一组 nsys 测试
9. 导出 sqlite
10. 解析 sqlite
11. 确认 NVTX / CUDA API / GPU kernel / memcpy 数据正常
12. 再跑 workloads_test.yaml
13. 最后跑 6000 Ada full matrix 和 4090 representative matrix
```

一句话原则：

**第一阶段不要追求复杂指标，先把 NVTX、CUDA API、GPU kernel、memory trace 稳定采集下来。benchmark 输出只做 sanity check，真正的 raw / hidden / exposed 归因放到后续 sqlite trace 分析阶段。**
