# DeepSeek NVTX / Nsight Systems 使用说明

本文档整理当前项目中 `nsys` 的常用用法，重点说明如何利用 NVTX 标签避免“每次采集整个程序导致报告过大”的问题。

当前项目里推荐使用的 Nsight Systems CLI 是：

```text
tools\nsight_systems\nsight_systems-windows-x86_64-2025.6.3.541-archive\nsight-systems\2025.6.3\target-windows-x64\nsys.exe
```

注意：`tools\nsight_compute\...` 目录下也带有一个旧版 `nsys.exe`。本文命令默认使用 Nsight Systems 2025.6.3，不使用 Nsight Compute 目录下的旧版 `nsys.exe`。

## 1. 一次性初始化 PowerShell 环境

在项目根目录执行：

```powershell
$env:TEMP = (Resolve-Path .\nsys_tmp).Path
$env:TMP = $env:TEMP
$env:TMPDIR = $env:TEMP

$nsysDir = (Resolve-Path ".\tools\nsight_systems\nsight_systems-windows-x86_64-2025.6.3.541-archive\nsight-systems\2025.6.3\target-windows-x64").Path
$env:Path = "$nsysDir;$env:Path"
$nsys = Join-Path $nsysDir "nsys.exe"
```

验证版本：

```powershell
& $nsys --version
```

应看到类似：

```text
NVIDIA Nsight Systems version 2025.6.3.541
```

## 2. 当前项目已有的 NVTX 开关

`chat_deepseek.py` 支持：

| 参数 | 作用 | 建议 |
| --- | --- | --- |
| `--nvtx` | 开启外层和粗粒度 NVTX range | 日常 profiling 首选 |
| `--nvtx-detail` | 开启模型内部细粒度 NVTX range，同时自动开启普通 NVTX | 定位 Attention / MLP / MoE / KV cache 时使用 |
| `--nvtx-sync` | 在 NVTX range 边界执行 `torch.cuda.synchronize()` | 只用于对齐边界，不用于真实性能数据 |
| `--torch-nvtx` | 用 PyTorch 自带 `emit_nvtx(record_shapes=True)` 包住 `model.generate()`，自动标记 ATen op | 想看 PyTorch 内部 op 和当前模型级 range 的嵌套关系时使用 |

也可以用环境变量开启：

```powershell
$env:ENABLE_NVTX="1"
$env:ENABLE_NVTX_DETAIL="1"
$env:ENABLE_NVTX_SYNC="1"
```

等价别名：

```text
DEEPSEEK_NVTX=1
DEEPSEEK_NVTX_DETAIL=1
DEEPSEEK_NVTX_SYNC=1
```

NVTX 封装代码位于：

```text
Deepseek_v2_litter\nvtx_utils.py
```

`--torch-nvtx` 使用的是 PyTorch 自带 profiler/NVTX 入口，不走上面的环境变量开关。默认不开启 NVTX，不影响普通推理。

最小验证命令：

```powershell
.\deepseek_py310\python.exe .\chat_deepseek.py `
  --prompt "HALLO" `
  --max-new-tokens 8 `
  --temperature 0 `
  --device cuda `
  --nvtx-detail `
  --torch-nvtx
```

用 Nsight Systems 采集时，至少保留 `cuda,nvtx` trace：

```powershell
& $nsys profile `
  --force-overwrite=true `
  --trace=cuda,nvtx,python-gil `
  -o nsys_tmp\deepseek_torch_nvtx `
  .\deepseek_py310\python.exe .\chat_deepseek.py `
  --prompt "HALLO" `
  --max-new-tokens 8 `
  --temperature 0 `
  --device cuda `
  --nvtx-detail `
  --torch-nvtx
```

这样可以在 `Generation.*`、`DeepseekV2Attention.*`、`DeepseekV2MoE.*` 等项目自定义 range 里看到 PyTorch 自动标出的 ATen op。它会增加 profiling 开销，正式测端到端性能时建议再跑一版不带 `--torch-nvtx` 的对照。

## 3. 最推荐：只采集一个 NVTX range

这是解决报告过大的核心方法。

`nsys profile` 关键参数：

| 参数 | 含义 |
| --- | --- |
| `--capture-range=nvtx` | 不从程序启动就采集，而是等指定 NVTX range 出现才开始 |
| `--nvtx-capture=<range>` | 指定哪个 NVTX range 触发采集 |
| `--capture-range-end=stop` | 指定 range 结束后停止采集，但程序继续运行 |
| `--capture-range-end=stop-shutdown` | 指定 range 结束后停止采集并关闭 profiling session |
| `--capture-range-end=repeat:N` | 多次捕获同名 range，最多捕获 N 次 |

### 3.1 只抓 `generate`

适合先排除模型加载、tokenizer、初始化等无关阶段：

```powershell
& $nsys profile `
  --force-overwrite=true `
  --trace=cuda,nvtx `
  --capture-range=nvtx `
  --nvtx-capture=generate `
  --capture-range-end=stop `
  -o nsys_tmp\deepseek_generate_only `
  deepseek_py310\python.exe chat_deepseek.py `
  --nvtx `
  --prompt "HALLO" `
  --max-new-tokens 32
```

输出：

```text
nsys_tmp\deepseek_generate_only.nsys-rep
```

### 3.2 只抓 prefill 阶段的模型主体

`Generation.prefill.model` 是当前代码中真实存在的静态 NVTX range，适合只抓首轮 prefill 的模型主体：

```powershell
& $nsys profile `
  --force-overwrite=true `
  --trace=cuda,nvtx `
  --capture-range=nvtx `
  --nvtx-capture=Generation.prefill.model `
  --capture-range-end=repeat:1 `
  -o nsys_tmp\deepseek_prefill_model `
  deepseek_py310\python.exe chat_deepseek.py `
  --nvtx `
  --prompt "HALLO" `
  --max-new-tokens 32
```

### 3.3 只抓某一层 Decoder Layer

需要模型内部细粒度标签时，加 `--nvtx-detail`：

```powershell
& $nsys profile `
  --force-overwrite=true `
  --trace=cuda,nvtx `
  --capture-range=nvtx `
  --nvtx-capture=DeepseekV2DecoderLayer.forward.layer_0 `
  --capture-range-end=repeat:1 `
  -o nsys_tmp\deepseek_layer0_once `
  deepseek_py310\python.exe chat_deepseek.py `
  --nvtx-detail `
  --prompt "HALLO" `
  --max-new-tokens 32
```

### 3.4 只抓 Attention 的 QK matmul

```powershell
& $nsys profile `
  --force-overwrite=true `
  --trace=cuda,nvtx `
  --capture-range=nvtx `
  --nvtx-capture=DeepseekV2Attention.qk_matmul `
  --capture-range-end=repeat:1 `
  -o nsys_tmp\deepseek_qk_once `
  deepseek_py310\python.exe chat_deepseek.py `
  --nvtx-detail `
  --prompt "HALLO" `
  --max-new-tokens 32
```

### 3.5 多次抓同一个 range

例如抓前 5 次 decode 阶段的模型主体：

```powershell
& $nsys profile `
  --force-overwrite=true `
  --trace=cuda,nvtx `
  --capture-range=nvtx `
  --nvtx-capture=Generation.decode.model `
  --capture-range-end=repeat:5 `
  -o nsys_tmp\deepseek_decode_model_first5 `
  deepseek_py310\python.exe chat_deepseek.py `
  --nvtx `
  --prompt "HALLO" `
  --max-new-tokens 32
```

如果希望每个 range 结束后立即生成结果，可用：

```powershell
--capture-range-end=repeat:5:async
```

通常不建议用 `sync`，因为它会阻塞程序线程。

## 4. 如果仍想采集完整程序

完整采集适合第一次了解整体结构，但报告会更大。

### 4.1 最小 CUDA + NVTX

```powershell
& $nsys profile `
  --force-overwrite=true `
  --trace=cuda,nvtx `
  -o nsys_tmp\deepseek_full_cuda_nvtx `
  deepseek_py310\python.exe chat_deepseek.py `
  --nvtx `
  --prompt "HALLO" `
  --max-new-tokens 32
```

### 4.2 细粒度完整采集

```powershell
& $nsys profile `
  --force-overwrite=true `
  --trace=cuda,nvtx `
  -o nsys_tmp\deepseek_full_detail `
  deepseek_py310\python.exe chat_deepseek.py `
  --nvtx-detail `
  --prompt "HALLO" `
  --max-new-tokens 32
```

### 4.3 带 cuBLAS / cuDNN 调用

```powershell
& $nsys profile `
  --force-overwrite=true `
  --trace=cuda,nvtx,cublas,cuDNN `
  -o nsys_tmp\deepseek_full_libs `
  deepseek_py310\python.exe chat_deepseek.py `
  --nvtx-detail `
  --prompt "HALLO" `
  --max-new-tokens 32
```

### 4.4 带 Windows WDDM

```powershell
& $nsys profile `
  --force-overwrite=true `
  --trace=cuda,nvtx,wddm `
  -o nsys_tmp\deepseek_full_wddm `
  deepseek_py310\python.exe chat_deepseek.py `
  --nvtx-detail `
  --prompt "HALLO" `
  --max-new-tokens 32
```

`wddm` 和部分 ETW 事件可能需要管理员权限，并会增加报告体积。

### 4.5 带 GPU metrics

先查看可用设备：

```powershell
& $nsys profile --gpu-metrics-devices=help
```

采集当前 CUDA 可见 GPU：

```powershell
& $nsys profile `
  --force-overwrite=true `
  --trace=cuda,nvtx `
  --gpu-metrics-devices=cuda-visible `
  --gpu-metrics-frequency=10000 `
  -o nsys_tmp\deepseek_gpu_metrics `
  deepseek_py310\python.exe chat_deepseek.py `
  --nvtx `
  --prompt "HALLO" `
  --max-new-tokens 32
```

GPU metrics 可用于看 SM 利用率、显存带宽等系统级指标，但会增加开销和文件体积。

## 5. `nsys profile` 常用参数速查

### 5.1 Trace 类型

Windows 版 2025.6.3 常用 `--trace` 值：

| 值 | 用途 |
| --- | --- |
| `cuda` | CUDA API、CUDA kernel、memcpy 等，深度学习必选 |
| `nvtx` | 采集 NVTX range，配合本项目标签必选 |
| `cublas` | cuBLAS 调用 |
| `cublas-verbose` | 更详细的 cuBLAS 信息，开销更高 |
| `cuDNN` | cuDNN 调用 |
| `cuDNN-verbose` | 更详细的 cuDNN 信息，开销更高 |
| `cusolver` | cuSOLVER 调用 |
| `cusparse` | cuSPARSE 调用 |
| `wddm` | Windows GPU 调度/队列信息 |
| `python-gil` | Python GIL 信息 |
| `none` | 不采 API trace，通常只用于特殊场景 |

推荐从小到大：

```powershell
--trace=cuda,nvtx
--trace=cuda,nvtx,cublas,cuDNN
--trace=cuda,nvtx,wddm
```

不要在当前 Windows 版里使用：

```powershell
--trace=cuda,nvtx,osrt
```

否则可能报：

```text
Illegal --trace argument 'osrt'
```

### 5.2 输出控制

| 参数 | 作用 |
| --- | --- |
| `-o <path>` / `--output=<path>` | 输出报告名，不写扩展名 |
| `--force-overwrite=true` | 覆盖同名报告 |
| `--export=sqlite` | 采集后额外导出 SQLite |
| `--export=json` | 采集后额外导出 JSON，通常较大 |
| `--stats=true` | 采集结束后生成统计，需额外 SQLite |
| `--show-output=true` | 显示被测程序 stdout/stderr，默认 true |

示例：

```powershell
& $nsys profile `
  --force-overwrite=true `
  --trace=cuda,nvtx `
  --export=sqlite `
  --stats=true `
  -o nsys_tmp\deepseek_with_stats `
  deepseek_py310\python.exe chat_deepseek.py `
  --nvtx `
  --prompt "HALLO" `
  --max-new-tokens 16
```

### 5.3 降低 CPU 采样开销

如果只关心 CUDA timeline 和 NVTX，可关闭 CPU 采样和 CPU 调度：

```powershell
--sample=none --cpuctxsw=none --backtrace=none
```

完整示例：

```powershell
& $nsys profile `
  --force-overwrite=true `
  --trace=cuda,nvtx `
  --sample=none `
  --cpuctxsw=none `
  --backtrace=none `
  --capture-range=nvtx `
  --nvtx-capture=generate `
  --capture-range-end=stop `
  -o nsys_tmp\deepseek_generate_low_overhead `
  deepseek_py310\python.exe chat_deepseek.py `
  --nvtx `
  --prompt "HALLO" `
  --max-new-tokens 32
```

### 5.4 限制采集时长

如果程序可能长时间运行，可加 `--duration`：

```powershell
--duration=10
```

表示最多采集 10 秒。注意：`--duration` 是时间上限，不是 NVTX 过滤；真正减少无关阶段仍优先用 `--capture-range=nvtx`。

### 5.5 设置被测进程环境变量

可以用 `--env-var` 给被测 Python 进程注入环境变量：

```powershell
& $nsys profile `
  --force-overwrite=true `
  --trace=cuda,nvtx `
  --env-var=ENABLE_NVTX=1,ENABLE_NVTX_DETAIL=1 `
  -o nsys_tmp\deepseek_env_nvtx `
  deepseek_py310\python.exe chat_deepseek.py `
  --prompt "HALLO" `
  --max-new-tokens 32
```

实际使用中更推荐直接传 `chat_deepseek.py --nvtx` 或 `--nvtx-detail`，可读性更好。

## 6. NVTX 标签速查

### 6.1 外层对话流程

这些标签由 `chat_deepseek.py` 提供：

| NVTX range | 含义 |
| --- | --- |
| `setup.load_tokenizer` | 加载 tokenizer |
| `setup.load_model` | 加载模型 |
| `setup.load_generation_config` | 加载生成配置 |
| `tokenize.apply_chat_template` | 构造输入 prompt |
| `tokenize.to_model_device` | 输入搬到模型设备 |
| `chat_once` | 一次完整对话 |
| `generate` | HuggingFace generate 主体 |
| `generate.start_thread` | 启动生成线程 |
| `decode.stream_collect` | streamer 收集输出 |
| `decode.stream_chunk` | 单个输出 chunk mark |
| `generate.join_thread` | 等待生成线程结束 |
| `decode.join_chunks` | 拼接输出文本 |

先抓 `generate`，通常就能排除模型加载和 tokenizer。

### 6.2 模型粗粒度结构

常用范围：

```text
Generation.call_000001
Generation.prefill.model
Generation.decode.model
DeepseekV2Model.embed_tokens
DeepseekV2Model.prepare_attention_mask
DeepseekV2Model.final_norm
DeepseekV2DecoderLayer.forward.layer_0
DeepseekV2DecoderLayer.self_attn.layer_0
DeepseekV2DecoderLayer.mlp.layer_0
Generation.prefill.lm_head
Generation.decode.lm_head
```

如果不同层耗时差异大，先抓慢的 `DeepseekV2DecoderLayer.forward.layer_x`；如果所有层都均匀慢，通常是整体计算、显存带宽或 kernel 效率问题。

### 6.3 Attention 细粒度结构

普通 Attention：

```text
DeepseekV2Attention.forward.layer_x
DeepseekV2Attention.q_proj
DeepseekV2Attention.kv_proj
DeepseekV2Attention.rope
DeepseekV2Attention.qk_matmul
DeepseekV2Attention.softmax_dropout
DeepseekV2Attention.av_matmul
DeepseekV2Attention.o_proj
```

FlashAttention2：

```text
DeepseekV2FlashAttention2.forward.layer_x
DeepseekV2FlashAttention2.q_proj
DeepseekV2FlashAttention2.kv_proj
DeepseekV2FlashAttention2.rope
DeepseekV2FlashAttention2.flash_attention
DeepseekV2FlashAttention2.o_proj
DeepseekV2FlashAttention2.unpad_input
DeepseekV2FlashAttention2.flash_attn_varlen_func
DeepseekV2FlashAttention2.flash_attn_func
DeepseekV2FlashAttention2.pad_output
```

### 6.4 MLP / MoE

```text
DeepseekV2MLP.forward
DeepseekV2MLP.gate_proj
DeepseekV2MLP.up_proj
DeepseekV2MLP.act_mul
DeepseekV2MLP.down_proj
DeepseekV2MoE.forward
DeepseekV2MoE.gate
DeepseekV2MoE.infer_experts
DeepseekV2MoE.shared_experts
DeepseekV2MoE.moe_infer.count_sort_tokens
DeepseekV2MoE.moe_infer.expert_0
DeepseekV2MoE.moe_infer.concat_experts
DeepseekV2MoE.moe_infer.restore_and_weight
```

### 6.5 KV cache / Decode 阶段

代码里会生成带阶段信息的标签，例如：

```text
Generation.call_000001
Generation.prefill.step_000001
Generation.decode.step_000002
Generation.prefill.model
Generation.decode.model
kv_cache_read.usable_length.layer_x
kv_cache_write.update.layer_x
kv_cache_read.key_for_attention.layer_x
kv_cache_read.value_for_attention.layer_x
DeepseekV2ForCausalLM.prepare.slice_input_ids
DeepseekV2ForCausalLM.prepare.crop_attention_mask
DeepseekV2ForCausalLM.prepare.position_ids
```

如果 decode 越跑越慢，重点看 KV cache read/write、attention matmul 和 `lm_head`。

## 7. NVTX 相关 `nsys stats` 用法

`nsys stats` 可以不打开 GUI，直接从 `.nsys-rep` 或 `.sqlite` 生成汇总。

### 7.1 查看 NVTX 汇总

```powershell
& $nsys stats `
  --report nvtx_sum `
  nsys_tmp\deepseek_full_detail.nsys-rep
```

更适合 push/pop range 的报告：

```powershell
& $nsys stats `
  --report nvtx_pushpop_sum `
  nsys_tmp\deepseek_full_detail.nsys-rep
```

查看 NVTX 与 GPU kernel 的投影关系：

```powershell
& $nsys stats `
  --report nvtx_gpu_proj_sum `
  nsys_tmp\deepseek_full_detail.nsys-rep
```

查看每个 NVTX range 里包含的 kernel：

```powershell
& $nsys stats `
  --report nvtx_kern_sum `
  nsys_tmp\deepseek_full_detail.nsys-rep
```

### 7.2 只统计某个 NVTX range

例如只统计 `generate` 范围内的 CUDA kernel：

```powershell
& $nsys stats `
  --filter-nvtx generate `
  --report cuda_gpu_kern_sum `
  nsys_tmp\deepseek_full_detail.nsys-rep
```

只看第一次 `Generation.decode.model`：

```powershell
& $nsys stats `
  --filter-nvtx Generation.decode.model/0 `
  --report cuda_gpu_kern_sum `
  nsys_tmp\deepseek_full_detail.nsys-rep
```

只看第二次：

```powershell
& $nsys stats `
  --filter-nvtx Generation.decode.model/1 `
  --report cuda_gpu_kern_sum `
  nsys_tmp\deepseek_full_detail.nsys-rep
```

`/0`、`/1` 是同名 NVTX range 的实例索引，从 0 开始。

### 7.3 常用 CUDA 统计报告

```powershell
& $nsys stats --report cuda_api_sum nsys_tmp\deepseek_full_detail.nsys-rep
& $nsys stats --report cuda_gpu_kern_sum nsys_tmp\deepseek_full_detail.nsys-rep
& $nsys stats --report cuda_gpu_trace nsys_tmp\deepseek_full_detail.nsys-rep
& $nsys stats --report cuda_kern_exec_sum nsys_tmp\deepseek_full_detail.nsys-rep
& $nsys stats --report cuda_gpu_mem_time_sum nsys_tmp\deepseek_full_detail.nsys-rep
& $nsys stats --report cuda_gpu_mem_size_sum nsys_tmp\deepseek_full_detail.nsys-rep
```

常用报告含义：

| report | 含义 |
| --- | --- |
| `nvtx_sum` | NVTX range 总览 |
| `nvtx_pushpop_sum` | push/pop 类型 NVTX range 汇总，本项目主要使用这种 |
| `nvtx_pushpop_trace` | push/pop 类型 NVTX range 时间线 |
| `nvtx_gpu_proj_sum` | NVTX range 投影到 GPU 活动后的汇总 |
| `nvtx_kern_sum` | 按 NVTX range 聚合 kernel |
| `cuda_api_sum` | CUDA API 耗时汇总 |
| `cuda_gpu_kern_sum` | GPU kernel 耗时汇总 |
| `cuda_gpu_trace` | GPU kernel 时间线明细 |
| `cuda_kern_exec_sum` | kernel launch 与执行时间汇总 |
| `cuda_gpu_mem_time_sum` | GPU memcpy/memset 按时间汇总 |
| `cuda_gpu_mem_size_sum` | GPU memcpy/memset 按大小汇总 |
| `wddm_queue_sum` | Windows WDDM 队列利用率 |

### 7.4 输出为 CSV / JSON

输出 CSV 到文件：

```powershell
& $nsys stats `
  --report nvtx_pushpop_sum,cuda_gpu_kern_sum `
  --format csv `
  --output nsys_tmp\deepseek_stats `
  nsys_tmp\deepseek_full_detail.nsys-rep
```

输出 JSON：

```powershell
& $nsys stats `
  --report nvtx_pushpop_sum `
  --format json `
  --output nsys_tmp\deepseek_nvtx_stats `
  nsys_tmp\deepseek_full_detail.nsys-rep
```

## 8. `nsys export` 用法

导出 SQLite，适合后续 SQL 查询或脚本分析：

```powershell
& $nsys export `
  --force-overwrite=true `
  --type=sqlite `
  --output=nsys_tmp\deepseek_full_detail.sqlite `
  nsys_tmp\deepseek_full_detail.nsys-rep
```

只导出部分表：

```powershell
& $nsys export `
  --force-overwrite=true `
  --type=sqlite `
  --tables=NVTX.*,CUPTI_ACTIVITY_KIND_KERNEL `
  --output=nsys_tmp\deepseek_nvtx_kernel.sqlite `
  nsys_tmp\deepseek_full_detail.nsys-rep
```

按时间范围导出：

```powershell
& $nsys export `
  --force-overwrite=true `
  --type=sqlite `
  --times=1s/3s `
  --output=nsys_tmp\deepseek_1s_3s.sqlite `
  nsys_tmp\deepseek_full_detail.nsys-rep
```

常用导出格式：

| 格式 | 适用场景 |
| --- | --- |
| `sqlite` | 最常用，便于 SQL 和 `nsys stats` |
| `json` | 与外部工具交换，但文件可能很大 |
| `text` | 查看原始事件文本 |
| `hdf` | HDF5 分析流程 |
| `arrow` / `arrowdir` / `parquetdir` | 大规模数据分析 |

## 9. 按时间节点采集或导出信息

本节按当前项目里的 Nsight Systems 2025.6.3 的 `nsys profile --help` 整理。先确认一件事：

```text
nsys profile 没有 --times=<start>/<end> 这种采集参数。
```

采集时按时间控制主要用：

| 参数 | `nsys profile --help` 中的含义 | 用法 |
| --- | --- | --- |
| `-y, --delay=` | Collection start delay in seconds | 从被测程序启动后延迟多少秒才开始采集 |
| `-d, --duration=` | Collection duration in seconds | 开始采集后最多采集多少秒 |
| `-c, --capture-range=` | 可选 `none`、`cudaProfilerApi`、`nvtx`、`hotkey` | 不从程序启动就采集，等触发条件出现再开始 |
| `-p, --nvtx-capture=` | 只在 `--capture-range=nvtx` 时生效 | 指定哪个 NVTX range 触发采集 |
| `--capture-range-end=` | 只在 `--capture-range` 时生效 | 指定触发 range 结束时如何停止或重复采集 |

如果你是在已有 `.nsys-rep` 上事后切出 `2.30s/2.80s`，那是 `nsys export --times=2.30s/2.80s`，不是 `nsys profile` 的采集参数。

### 9.1 用 `--delay` 和 `--duration` 采集固定时间段

如果你已经知道目标大概出现在程序启动后的第几秒，用：

```text
--delay=<开始秒数>
--duration=<采集秒数>
```

例如只采集程序启动后 `45s` 到 `50s` 这一段：

```powershell
& $nsys profile `
  --force-overwrite=true `
  --trace=cuda,nvtx `
  --sample=none `
  --cpuctxsw=none `
  --backtrace=none `
  --delay=45 `
  --duration=5 `
  -o nsys_tmp\deepseek_time_45s_50s `
  deepseek_py310\python.exe chat_deepseek.py `
  --nvtx-detail `
  --prompt "HALLO" `
  --max-new-tokens 128
```

输出：

```text
nsys_tmp\deepseek_time_45s_50s.nsys-rep
```

注意：`--delay=45` 是从被测 Python 进程启动开始算，不是从 `generate`、`prefill` 或第一条 CUDA kernel 开始算。这个方法适合模型加载时间比较稳定的情况。

### 9.2 用 NVTX 触发后再采集一段时间

如果模型加载时间波动比较大，更推荐让 Nsight Systems 等到某个 NVTX range 出现后再开始采集。

例如等 `generate` 出现后采集 3 秒：

```powershell
& $nsys profile `
  --force-overwrite=true `
  --trace=cuda,nvtx `
  --sample=none `
  --cpuctxsw=none `
  --backtrace=none `
  --capture-range=nvtx `
  --nvtx-capture=generate `
  --duration=3 `
  -o nsys_tmp\deepseek_generate_first3s `
  deepseek_py310\python.exe chat_deepseek.py `
  --nvtx-detail `
  --prompt "HALLO" `
  --max-new-tokens 128
```

这个命令的含义是：程序先正常启动和加载模型，`generate` 这个 NVTX range 开始时才开始采集，采集最多持续 3 秒。

例如等 `Generation.prefill.model` 出现后采集 10 秒：

```powershell
& $nsys profile `
  --force-overwrite=true `
  --trace=cuda,nvtx `
  --sample=none `
  --cpuctxsw=none `
  --backtrace=none `
  --capture-range=nvtx `
  --nvtx-capture=Generation.prefill.model `
  --duration=10 `
  -o nsys_tmp\deepseek_prefill_model_first10s `
  deepseek_py310\python.exe chat_deepseek.py `
  --nvtx-detail `
  --prompt "HALLO" `
  --max-new-tokens 128
```

如果目标 range 本身短于 `--duration`，报告里只会有实际发生过的 CUDA/NVTX 活动；`--duration` 是上限，不会制造额外活动。

### 9.3 完整采集某个 NVTX range

如果目标不是“前几秒”，而是“完整抓住某个 range”，通常用 `--capture-range-end=stop` 或 `repeat:N`，不需要 `--duration`。

只抓完整 `generate`：

```powershell
& $nsys profile `
  --force-overwrite=true `
  --trace=cuda,nvtx `
  --sample=none `
  --cpuctxsw=none `
  --backtrace=none `
  --capture-range=nvtx `
  --nvtx-capture=generate `
  --capture-range-end=stop `
  -o nsys_tmp\deepseek_generate_range `
  deepseek_py310\python.exe chat_deepseek.py `
  --nvtx-detail `
  --prompt "HALLO" `
  --max-new-tokens 128
```

只抓第一次 `Generation.prefill.model`：

```powershell
& $nsys profile `
  --force-overwrite=true `
  --trace=cuda,nvtx `
  --sample=none `
  --cpuctxsw=none `
  --backtrace=none `
  --capture-range=nvtx `
  --nvtx-capture=Generation.prefill.model `
  --capture-range-end=repeat:1 `
  -o nsys_tmp\deepseek_prefill_model_once `
  deepseek_py310\python.exe chat_deepseek.py `
  --nvtx-detail `
  --prompt "HALLO" `
  --max-new-tokens 128
```

`nsys profile --help` 里 `--capture-range-end` 的常用值：

| 值 | 含义 |
| --- | --- |
| `none` | range 结束时不停止采集 |
| `stop` | range 结束时停止采集，被测程序继续运行 |
| `stop-shutdown` | range 结束时停止采集并关闭 profiling session |
| `repeat:N` | 捕获同名 range N 次 |
| `repeat-shutdown:N` | 捕获同名 range N 次后关闭 session |

### 9.4 先短采集，再确定时间点

如果还不知道目标出现在第几秒，先做一次完整但短的探测采集：

```powershell
& $nsys profile `
  --force-overwrite=true `
  --trace=cuda,nvtx `
  --sample=none `
  --cpuctxsw=none `
  --backtrace=none `
  -o nsys_tmp\deepseek_timeline_probe `
  deepseek_py310\python.exe chat_deepseek.py `
  --nvtx-detail `
  --prompt "HALLO" `
  --max-new-tokens 16
```

打开 GUI：

```powershell
nsys-ui nsys_tmp\deepseek_timeline_probe.nsys-rep
```

在 Timeline 里看 NVTX、CUDA API、CUDA GPU Kernel 三类轨道，确认目标大概在第几秒。然后再回到：

```text
--delay=<start> --duration=<len>
```

或：

```text
--capture-range=nvtx --nvtx-capture=<range> --duration=<len>
```

做第二次更小的采集。

### 9.5 事后按时间窗口导出 SQLite

如果已经有一份完整 `.nsys-rep`，可以事后按时间范围导出 SQLite：

```powershell
& $nsys export `
  --force-overwrite=true `
  --type=sqlite `
  --times=2.30s/2.80s `
  --output=nsys_tmp\deepseek_timeline_2p30s_2p80s.sqlite `
  nsys_tmp\deepseek_timeline_probe.nsys-rep
```

只导出 NVTX 和 CUDA 活动相关表：

```powershell
& $nsys export `
  --force-overwrite=true `
  --type=sqlite `
  --tables=NVTX.*,CUPTI_ACTIVITY_KIND_KERNEL,CUPTI_ACTIVITY_KIND_MEMCPY,CUPTI_ACTIVITY_KIND_MEMSET `
  --times=2.30s/2.80s `
  --output=nsys_tmp\deepseek_timeline_2p30s_2p80s_cuda.sqlite `
  nsys_tmp\deepseek_timeline_probe.nsys-rep
```

注意：`nsys export --times` 只是事后切片，不会让原始 `.nsys-rep` 变小。想在采集阶段就控制体积，要用 `nsys profile --delay`、`--duration`、`--capture-range=nvtx`、`--capture-range-end`。

### 9.6 对时间窗口生成统计

先切出 SQLite，再对这段窗口运行 `stats`：

```powershell
& $nsys stats `
  --report nvtx_pushpop_sum,cuda_gpu_kern_sum,cuda_gpu_mem_time_sum `
  nsys_tmp\deepseek_timeline_2p30s_2p80s.sqlite
```

这样统计结果只对应 `2.30s` 到 `2.80s` 这一段。

### 9.7 选择建议

| 目标 | 推荐方式 |
| --- | --- |
| 已知程序启动后第几秒出问题 | `--delay=<start> --duration=<len>` |
| 模型加载时间不稳定，但知道目标 NVTX range | `--capture-range=nvtx --nvtx-capture=<range>` |
| 只想采某个 NVTX range 的前几秒 | `--capture-range=nvtx --nvtx-capture=<range> --duration=<len>` |
| 想完整采某个 NVTX range | `--capture-range=nvtx --nvtx-capture=<range> --capture-range-end=stop` |
| 同名 range 很多，只采前 N 次 | `--capture-range-end=repeat:N` |
| 已经有完整报告，想事后切时间段 | `nsys export --times=<start>/<end>` |

## 10. `nsys analyze` 用法

`nsys analyze` 会根据内置规则尝试指出优化机会。

```powershell
& $nsys analyze nsys_tmp\deepseek_full_detail.nsys-rep
```

只分析某个 NVTX range：

```powershell
& $nsys analyze `
  --filter-nvtx generate `
  nsys_tmp\deepseek_full_detail.nsys-rep
```

输出 JSON：

```powershell
& $nsys analyze `
  --format json `
  --output nsys_tmp\deepseek_analyze `
  nsys_tmp\deepseek_full_detail.nsys-rep
```

`analyze` 的结论只能作为提示，最终仍需要结合 Timeline、NVTX range 和 CUDA kernel 明细判断。

## 11. GUI 打开报告

如果 `nsys-ui` 在 PATH 里：

```powershell
nsys-ui nsys_tmp\deepseek_generate_only.nsys-rep
```

如果不在 PATH，直接打开 Nsight Systems GUI，再选择：

```text
nsys_tmp\deepseek_generate_only.nsys-rep
```

Timeline 中建议先看：

| 轨道 / 区域 | 重点 |
| --- | --- |
| NVTX | range 嵌套关系，确认采集范围是否正确 |
| CUDA API | kernel launch、memcpy、同步 API |
| CUDA GPU Kernel | 实际 GPU 执行时间 |
| CUDA Memory | H2D / D2H / D2D 拷贝 |
| GPU Metrics | SM、显存带宽、Tensor Core 等利用率 |
| WDDM | Windows GPU 队列和调度 |

## 12. 推荐分析流程

1. 先用完整但短的采集确认标签结构：

```powershell
& $nsys profile `
  --force-overwrite=true `
  --trace=cuda,nvtx `
  -o nsys_tmp\deepseek_probe `
  deepseek_py310\python.exe chat_deepseek.py `
  --nvtx `
  --prompt "HALLO" `
  --max-new-tokens 8
```

2. 在 GUI 或 `nsys stats --report nvtx_pushpop_sum` 里找最慢 range。

3. 用 `--capture-range=nvtx --nvtx-capture=<range>` 只抓目标 range。

4. 如果目标在模型内部，再切换到 `--nvtx-detail`。

5. 如果需要 kernel 级指标，再用 Nsight Compute 对同一个 NVTX range 做深挖。

## 13. 常见问题

### 13.1 报告太大

优先使用：

```powershell
--capture-range=nvtx --nvtx-capture=generate --capture-range-end=stop
```

其次减少 trace：

```powershell
--trace=cuda,nvtx
```

再关闭不需要的 CPU 采样：

```powershell
--sample=none --cpuctxsw=none --backtrace=none
```

### 13.2 没看到 NVTX

检查三件事：

```powershell
--trace=cuda,nvtx
```

并且被测脚本要加：

```powershell
--nvtx
```

或者：

```powershell
--nvtx-detail
```

如果用环境变量，确认是在被测 Python 进程中生效。

### 13.3 `--capture-range=nvtx` 没触发

常见原因：

| 原因 | 处理 |
| --- | --- |
| `--nvtx-capture` 名字写错 | 先完整短采集一次，用 GUI 或 `nvtx_pushpop_sum` 确认名字 |
| 忘记给脚本加 `--nvtx` | 加 `--nvtx` 或 `--nvtx-detail` |
| 目标是细粒度标签但只开了 `--nvtx` | 改用 `--nvtx-detail` |
| range 在默认 domain，但写了错误 domain | 本项目通常直接写 range 名，不加 `@domain` |

### 13.4 同名 range 太多

生成阶段会多次 forward，同名 range 很常见。处理方式：

```powershell
--capture-range-end=repeat:1
```

或在统计时指定实例：

```powershell
--filter-nvtx Generation.decode.model/0
```

### 13.5 开了 `--nvtx-sync` 后变慢

这是预期行为。`--nvtx-sync` 会在 range 边界强制 CUDA 同步，边界更清楚，但会改变真实性能。

正式性能数据：

```text
不要开 --nvtx-sync
```

只用于边界对齐：

```text
可以临时开 --nvtx-sync
```

### 13.6 `osrt` 报错

当前 Windows 版 `nsys profile --trace` 可选项里没有 `osrt`。不要使用：

```powershell
--trace=cuda,nvtx,osrt
```

改用：

```powershell
--trace=cuda,nvtx
```

### 13.7 想看 PyTorch 自动 NVTX

Nsight Systems 还支持 PyTorch 插件：

```powershell
--pytorch=autograd-nvtx
--pytorch=autograd-shapes-nvtx
--pytorch=functions-trace
```

例如：

```powershell
& $nsys profile `
  --force-overwrite=true `
  --trace=cuda,nvtx `
  --pytorch=functions-trace `
  -o nsys_tmp\deepseek_pytorch_functions `
  deepseek_py310\python.exe chat_deepseek.py `
  --nvtx `
  --prompt "HALLO" `
  --max-new-tokens 16
```

注意：`functions-trace` 会给很多 `torch.Module.forward()` 生成 NVTX range，报告可能明显变大。已有手写 NVTX 标签时，通常先不用它。

## 14. 最常用命令集合

只抓生成阶段：

```powershell
& $nsys profile --force-overwrite=true --trace=cuda,nvtx --capture-range=nvtx --nvtx-capture=generate --capture-range-end=stop -o nsys_tmp\deepseek_generate_only deepseek_py310\python.exe chat_deepseek.py --nvtx --prompt "HALLO" --max-new-tokens 32
```

只抓 prefill 模型主体：

```powershell
& $nsys profile --force-overwrite=true --trace=cuda,nvtx --capture-range=nvtx --nvtx-capture=Generation.prefill.model --capture-range-end=repeat:1 -o nsys_tmp\deepseek_prefill_model deepseek_py310\python.exe chat_deepseek.py --nvtx --prompt "HALLO" --max-new-tokens 32
```

只抓一次 QK matmul：

```powershell
& $nsys profile --force-overwrite=true --trace=cuda,nvtx --capture-range=nvtx --nvtx-capture=DeepseekV2Attention.qk_matmul --capture-range-end=repeat:1 -o nsys_tmp\deepseek_qk_once deepseek_py310\python.exe chat_deepseek.py --nvtx-detail --prompt "HALLO" --max-new-tokens 32
```

查看 NVTX 汇总：

```powershell
& $nsys stats --report nvtx_pushpop_sum nsys_tmp\deepseek_qk_once.nsys-rep
```

查看某个 NVTX 内的 kernel 汇总：

```powershell
& $nsys stats --filter-nvtx generate --report cuda_gpu_kern_sum nsys_tmp\deepseek_generate_only.nsys-rep
```

导出 SQLite：

```powershell
& $nsys export --force-overwrite=true --type=sqlite --output=nsys_tmp\deepseek_generate_only.sqlite nsys_tmp\deepseek_generate_only.nsys-rep
```
