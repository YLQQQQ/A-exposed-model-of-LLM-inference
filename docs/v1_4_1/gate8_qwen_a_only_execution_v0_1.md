# 路线A：单Qwen request执行审查 0.1

2026-09-28。只交付可审查实现/草案；没有授权服务器、GPU、Nsight或模型执行。
前置限定资格见[7.71](gate8_bounded_qualification_review_v0_1.md)。

## 固定执行合同

- 模型Qwen2.5-1.5B-Instruct，FP16，qwen2，greedy、use_cache=true；不compile/graph。
- 模型清单SHA256 `72465c906baeb0cfa4fd94d21ef6c69c1cd8046bb68c61a94c02a1580d2541f9`。
  模型本体保留服务器历史位置，不搬迁；prepare和目标进程加载前重新核验全部清单hash。
  实际输入集合与.cache辅助项区分，revision仍UNKNOWN，不能以内容hash推断revision。
- 原固定prompt文件SHA256 `4dffd0ddcbd3185c656ae4a27efaf5aab302febba6ead5df4d37d903a2091920`；
  32 input/2 output、batch1、warmup1、measured repeat1；不重新分词/随机生成输入。
- 配置backend固定sdpa；声明在模型加载之前写入manifest。实际加载后核对sdpa/qwen2/use_cache，
  不匹配则在warmup/request前停止；不强制覆盖实际配置，不使用加载fallback。
  sdpa配置不等于已证明native kernel backend；后者仍UNKNOWN。
- Windows/RTX4090，physical3→logical0；CUDA_DEVICE_ORDER=PCI_BUS_ID、mask=3，
  preflight与目标CUDA probe再通过UUID/PCI映射到trace设备，不按数字相等猜测。
- Nsight 2026.2.1.210-262137639646v0、torch2.6.0+cu124、CUDA12.4、transformers5.17.0；
  固定执行commit和单bundle身份置于本机交付索引，不追随服务器main。

## 最小实现与实际入口

`exposedpath.gate8_diagnostic prepare`新增显式`--target-python/--site-root`，
仅与预声明Engineering profile同时使用。复用已验证CPU probe与隔离base解释器，
不经venv launcher生成另一个Python子进程。依赖仍取固定checkout的venv purelib。
manifest封存target_python；目标进程在模型前重验snapshot并保存target_runtime。
`model-run`复用同一bootstrap，仅派发到已有模型入口，不改变controlled路径或runner。

`scripts/gate8_diagnostic_collect.py --engineering-a-only`：
先检查显式profile、target与环境、精确Nsight版本；一次profile→一次export→目标PID与
producer/原始profiler启动行绑定→input receipt→既有Canonical/projection/Engineering A门。
新报告版本`gate8-qwen-engineering-collection/0.1.0`保存result、manifest、runtime、launch哈希。
旧非A-only诊断入口保留，不能据其DIAGNOSTIC_COMPLETE替代新准入。

本地验证：先观察4项失败（prepare仅查size、identity冲突不拒绝、旧argv未隔离），
再最小实现；六文件106 passed/97.62s。CPU替身实际producer→Canonical→A链通过，
运行时PID篡改拒绝；缺target合同在collector启动前拒绝，错误backend/model_type在请求前拒绝。
compileall/contract37/Canonical7/oracle独立性/diff-check及PS Parser通过；没有运行全量/GPU。

prepare和target进程的GPU probe均可能初始化CUDA；不是zero GPU interaction。
未来执行脚本首先在相同isolated解释器下仅import框架核验版本，失败则不profile。
该Windows动态库/依赖组合尚未执行新模型入口，本地CPU替身不证明服务器能加载模型。

## 窗口、同步及停止规则

模型加载、一次warmup在测量窗外；实测request前记录成功cudaDeviceSynchronize drain。
runner仍用既有host-readable completion生成start/first/last共同trace点，形成full/prefill/decode；
EOS/完成记录须满足两token，cleanup不进入窗口。不添加每token设备同步来改变模型行为。

所有已观察blocking API和submit/correlation均进入现有逐窗口检查，包括未单独NVTX标注的
内部sync。前缀drain不证明未来无提交；仅当实际单NULL FIFO、身份/时钟/映射无冲突，
LEGACY/PER_THREAD后缀必要集合与各A分量相同时才允许条件A。不能以终点相同或总和闭合替代。
物理S/B保留invalid，不用条件A反向提升其资格。旧S/B、Measurement Contract、Q0不改。

缺边界/映射、失败API、其它相关stream、event/graph依赖、身份冲突、未知API作用、
任何影响不明诊断（包括外PIDwarning）均BLOCKED；不因受控trace无warning而豁免旧或新Qwen。
仅已批准两类有界API分类缺口可进入unattributed；不把任意缺采局部化，不填Host/residual。
输出需检查具体分类、保留残余和unknown，不以“有结果”或任意百分比为模型成功判据。

## 一次执行及回传边界

7.76更新：目标CPU静态复验已通过，下一次执行固定
`097f68a21eb9c75dbf390b7529a19c4316dda98e`。不再执行下述旧部署/定向静态步骤；
保留commit/clean、环境、输入hash、模型清单和新manifest检查，不复用旧manifest。
本机脚本默认拒绝采集，仅显式CollectionAuthorized开关可开启；此为待审查草案，不是授权。
新collection的diagnostic-entry（started/exit/stdout/stderr）递归纳入单ZIP；失败也保留
已生成记录，缺exit不能当成功。此次仅脚本/文档更新，无需新代码bundle或服务器跟随main。

协调窗口先审查忽略的`.local/gate8_qwen_engineering_once.ps1`完整块和bundle身份。
脚本默认CollectionAuthorized=false；人工授权后才改为true。固定checkout正常detach部署，
定向静态检查和verify通过后只运行一次采集/导出；无resume、无覆盖、无自动retry。
Nsight最大120秒、collector host等待300秒；超时不是OS安全保证（历史BugCheck根因未证）。
descendant状态未知则停止打包，先确认没有写入者，不按进程名kill，不自动重跑。

新run=`$ServerRoot/evidence/gate8/qwen_a_only_<UTC>_<GUID>`；prepare、环境、操作日志、
producer/配置/运行时身份、原REP、SQLite/export、A及诊断都在同run。清单快照排除自身，
统一单ZIP至`$ServerRoot/transfer`；返回路径、bytes、ZIP和清单SHA256。失败同样保留原报告。

机器候选成功仅`A_SCOPE_ENGINEERING_ONLY_PENDING_AUDIT`；UNKNOWN/NOT_ASSESSED不改，
D/Signature关闭，Gate7历史PASS、完整新版Q0/Gate8 NOT_RUN。旧attempt保持原状态。
无需再采旧Q0；真实Qwen是否符合支持域只能由这次另行授权的新证据核对，不事先宣称通过。
