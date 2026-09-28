# Profile前辅助预检隔离 0.1

2026-09-28；Engineering；用户批准的本地最小实现。schema `exposedpath-isolated-preflight/0.1.0`。
**工程可行，本地接线已实现；目标平台原生设备查询和新采集尚未执行。**
不改变request/drain/token语义、S/A/B、warning门或旧attempt；不是旧外PID无关的证明。
取代7.79的“停止追加实现”作为下一项工作授权，但其旧证据结论保持。

## 执行合同及变化风险

新prepare在有显式target interpreter的Engineering manifest内预声明本版本，旧读取/旧路径保留，
不追认旧manifest。collector在profile前重新执行原`validate_pre_model_identity`：Git commit/clean、
GPU physical/logical别名、mask、UUID/PCI、Engineering/G1等检查不删。另直接nvidia-smi实查目标
physical index/UUID/PCI；两次Git观察包围快照，状态变化拒绝。没有从预期字段生成“实测值”。

新run必须新prepare、新output。collector用`prepared/collection_intent.json`排他预约本run，
即使失败也不删预约、不换输出重试；只在新授权的新run继续。`auxiliary_preflight.json`以x模式写入：
run、输出根、随机nonce、四个输入文件hash、当前worktree文件集合/hash、Git HEAD/index/refs/config
元数据、实际预检Git/GPU身份、环境mask/PATH摘要、collector PID与wall/monotonic时刻。
Git ignored路径由当次Git枚举；tracked必须全部纳入快照。仅额外排除Python字节缓存与pytest缓存；
若tracked文件落入排除范围则拒绝。新增/消失的非忽略文件、内容变化、symlink/junction跳转均拒绝。
仅支持普通固定checkout，`.git`为worktree指针文件时拒绝，不临时复制仓库。

profile argv携带receipt路径、hash、nonce，不通过继承PATH选择Python。目标在模型前：

1. 检查manifest版本、receipt hash/run/输出目录/nonce、输入固定路径；缺一项拒绝。
2. 双时钟age须处于0–120秒（快照核验前后均检查）；这是启动新鲜度上限，不是实验时钟或性能指标。
3. 不调用Git，重新读所有封存文件、文件集合、Git元数据及mask/PATH摘要；与预检不一致拒绝。
   原Git检查外移而非跳过，`git_observation_role=PREFLIGHT_NOT_TARGET_GIT_QUERY`明确来源。
4. 原`current()`解释器/exe hash/site/jsonschema/sys.path/环境严格比较、model inventory内容重哈希、
   prompt/runner源码、32/2/batch1/warmup1/repeat1/eager/fp16/采样配置检查仍执行。
5. 排他创建claim绑定实际`os.getpid()/getppid()`；同receipt再次消费失败，不借用prepare PID。
6. 目标Torch可见数=1/current=0；Torch实际UUID与CUDA Driver查询UUID相等后，读取实际PCI。
   UUID/PCI再与已封存preflight比较，不把physical=3直接当logical/driver ordinal，不复制预期PCI。
7. 模型setup原observer仍核验实际sdpa、qwen2、use_cache；不改变加载、warmup、成功窗外drain或三点。

模型执行后目标复核快照；profile退出后collector复核快照与真实Git commit/clean，成功才写
`auxiliary_preflight.final.json`，再export/analyzer。新analyzer编排绑定receipt、claim、final与
producer实际PID；warning规则未变。来源记录仍随diagnostic-entry保存，预期这条显式路径没有
adapter子命令，但空记录不能排除第三方/native子进程。

边界：快照不是对抗恶意并发写者的锁/签名，不能证明“改后再恢复”从未发生。使用原先单用户、
无并发代码/输入修改的执行条件；前/目标/后核验发现变化即拒绝，不以时间短代替内容检查。
不宣称site-packages全部字节已封存：依赖版本和既有解释器snapshot保持原覆盖范围。
ignored数据不作代码身份依据，模型另用原完整内容清单核验。文件I/O位于request窗外，开销不称零。

## 原生查询及覆盖边界

`platform_adapter.cuda_identity_native`在目标进程调用已加载栈的CUDA Driver：cuInit、cuDeviceGet、
cuDeviceGetUuid_v2、cuDeviceGetPCIBusId；Windows仅System32 nvcuda.dll，找不到symbol/错误码立即拒绝，
无nvidia-smi fallback、无同步/采样/监控。所有查询在模型/drain/request之前。
依据：[CUDA12.4.1 Driver API](https://docs.nvidia.com/cuda/archive/12.4.1/pdf/CUDA_Driver_API.pdf)
Device Management和Memory Management的上述函数定义。新增只读初始化不是zero GPU interaction；
本轮只用CPU ABI替身，不加载驱动、不授予Windows实际ABI或Linux平台验证。

已知外部命令：prepare的Git/GPU/解释器probe，以及collector的Git/nvidia-smi/nsys version均在profile前；
postflight Git与export在profile后。model-run的原两Git+一nvidia-smi由上述目标本地检查替代。
runner此入口不走legacy parity/telemetry命令路径；第三方/native行为不禁用也未假定不存在。
没有为了消除warning关闭模型功能、NVTX、CUDA trace或process-tree范围。

## 本地验证与资格边界

先看到缺模块/缺原生身份16个失败，再实现；实际run_diagnostic新参数接线先2个失败；
profile缺receipt先失败；快照期间过期、同prepared换目录重试均先失败后修复。
测试覆盖真实临时Git仓库→seal→独立`-I -S` CPU子进程consume、实际producer文件入口和collector顺序；
过期/未来时间、错run/nonce/output、丢输入、改内容/新增文件、Git变化、mask/UUID/PCI冲突、
未知版本、重复消费、postflight变化均拒绝。GPU/模型/Nsight端使用明确CPU替身。
不把已有受控资格自动扩大到本新设备adapter；新attempt必须完成目标身份与原质量门。

最终相关9文件128 passed/48.40s，新增文件25项；改动代码compileall、git diff --check通过。
命令为`python -m pytest -q -p no:cacheprovider`加以下文件：
test_gate8_isolated_preflight、test_gate8_diagnostic_entry、test_gate8_diagnostic_collect、
test_gate8_engineering_producer、test_gate8_target_entry、test_process_origin、test_platform_adapter、
test_gate8_import_identity、test_gate8_target_python（均为tests目录的.py）。未跑全量。
本地自审检查版本分支、保留旧路径、前后身份链、真实观察来源和失败中断；未发现需改研究语义的事项。

## 一次最小新执行方案（仅供审查，未授权执行）

固定本次交付的完整实现commit，不追随main或只凭短SHA；服务器当前097f68a不自动更新。
部署后只运行本次相关CPU回归，不重新跑全量、旧Q0或旧模型。沿用已批准Qwen内容清单/输入hash、
physical3及既定UUID/PCI、显式目标Python/既定site、sdpa/eager/fp16、32/2、batch1、warmup1/repeat1。
外层prepare可以用仓库venv，target仍使用已验证直接base interpreter，禁止用PATH python。
新根为`$ServerRoot/evidence/gate8/<new-run>`，代码仍固定checkout；历史证据不迁移。

经协调审查并另获单次执行授权后，以已核验机器配置变量运行以下两步（各exit非零立即停止）：

```powershell
# $ExpectedCommit 必须填交付回执的完整SHA；所有其他变量来自核验过的本机配置。
$ErrorActionPreference = 'Stop'
if ((git -C $CodeRoot rev-parse HEAD).Trim() -ne $ExpectedCommit) { throw 'commit mismatch' }
if (git -C $CodeRoot status --porcelain) { throw 'dirty tree' }
if (Test-Path -LiteralPath $RunRoot) { throw 'new run directory required' }
$env:CUDA_DEVICE_ORDER = 'PCI_BUS_ID'
$env:CUDA_VISIBLE_DEVICES = '3'
New-Item -ItemType Directory -Path $RunRoot -ErrorAction Stop | Out-Null
Push-Location -LiteralPath $CodeRoot
try {
  & $RepoPython -m exposedpath.gate8_diagnostic prepare `
    --output-dir "$RunRoot/prepared" --model-path $ModelPath `
    --inventory-path $ModelInventory --inventory-sha256 $ModelInventorySha256 `
    --prompt-path $PromptPath --prompt-sha256 $PromptSha256 `
    --expected-commit $ExpectedCommit --physical-gpu 3 `
    --engineering-attention-backend sdpa --target-python $TargetPython --site-root $SiteRoot
  if ($LASTEXITCODE -ne 0) { throw 'prepare failed; no profile' }
  & $RepoPython scripts/gate8_diagnostic_collect.py --nsys $NsysExe --python $TargetPython `
    --prepared "$RunRoot/prepared" --output "$RunRoot/collection" `
    --execute-engineering-diagnostic --engineering-a-only
  if ($LASTEXITCODE -ne 0) { throw 'blocked; preserve all files; no retry' }
} finally { Pop-Location }
```

单次执行可回答：已知辅助工具外移后，实际身份/新鲜度是否仍一致，以及该新attempt在不改warning门下
能否得到限定A准入。不能回答旧PID角色或追认旧attempt，也不保证第三方warning消失。
原生查询失败就在模型前停止；身份/receipt/配置失败不继续；任何warning影响不明保持BLOCKED。
不因再失败增加监控或自动重采，先读单包判断唯一实际失败点。

单ZIP回传整个新run：prepared/collection_intent、manifest/prompt/模型清单、预检/claim/final、
diagnostic-entry起始/退出/异常/stdout/stderr/来源记录、target_runtime/实际probe/config、producer、
REP/SQLite/export/diagnostic-scope/A/report及操作transcript。失败时同样回传已生成的全部文件，
不调用GUI、不补改报告。先固定文件列表、排除hash清单自身，再写相对路径/size/SHA256清单并复核；
压缩到`$ServerRoot/transfer`中的单ZIP，记录ZIP大小/hash，传回本地`.local/transfer`。
代码包如后续获部署授权只交一个固定增量bundle，本轮不要求部署。

Gate7 PASS、限定受控资格及旧BLOCKED保持；UNKNOWN不改零，完整新Q0/Gate8 NOT_RUN；D/Signature关闭。
