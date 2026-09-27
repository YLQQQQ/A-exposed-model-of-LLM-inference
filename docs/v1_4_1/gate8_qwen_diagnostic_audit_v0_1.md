# Qwen 单次诊断只读审计 v0.1

2026-09-27；Engineering / NOT_QUALIFIED。执行commit为
`35b5bffe4f771f9783d10fdcdb8260d056902bdd`。本地仅读取回传ZIP及其内存SQLite，
不运行profile/export/模型，不修改原件，不授予Q0或Gate8资格。

## 身份与文件链

ZIP 1,434,073 bytes，SHA256
`adb6a88d9b14170cf40353b317ffba18998b3c28ac2d2c50160bc2649893bd5a`。
27源文件加清单共28项，逐项大小/SHA、CRC通过；输入三副本字节一致，producer
receipt四文件hash一致。REP SHA256为
`981537c3db8799dbfe5ffa88c7e113fd6df716d60533e0523d59ae2ea6406ed1`；
canonical与attempt1 SQLite同hash
`25e7bd0e79597744f3485c1eb155621e0d93491b034ccb7756dc9f312d5e0145`，
1,863,680 bytes，只读integrity检查ok。一次collection exit0、28.516s；一次export
exit0、0.234s，无timeout/retry。报告仍明确NOT_QUALIFIED/NOT_ASSESSED。

run=`run-20260927T094130Z-cc460baf`，wmpc=`wmpc-9f1e23faccf92c93`，pass1，
diagnostic-1；PID50660，measured request-0/repeat0，warmup另列。两者COMPLETE，
measured 2/2 tokens、无early EOS。不是Pass0/Pass1配对实验或可靠性统计。
runner报告hash `7ed08a068915b8bf765d3ce8a674b470be011b200dc2cfef8cb88eedd90bf94a`
等于该commit源码CRLF表示；本地LF字节不同，不冒称收到服务器源码原件。
模型沿用历史内容清单并核当前大小/集合，10输入文件与13缓存辅助文件分开；
revision UNKNOWN，未复算权重。loaded config为sdpa/use_cache=true，native backend UNKNOWN。

## 三窗与同步的直接观察

`NVTX_EVENTS` rowid1/2/3为同身份、同globalTid的三个point，trace ns依次为
20995361790、21085953944、21160901865。按D1公式，marker窗口为：
request 165540075 ns；prefill 90592154 ns；decode 74947921 ns。
这些是共同trace clock的窗口，不是已合格A归属或无扰动延迟。
Host observed→before marker间隔分别459900/414200/419800 ns，marker调用
18500/33700/59000 ns；不将host与trace原点直接相减，不宣称观测误差为零。

drain NVTX row7包含Runtime row17430的cudaDeviceSynchronize，correlation61540、
return0，结束20994877037，早于request point。setup/warmup/measured三段range及ledger
齐全；drain只证明先行完成，不能单独证明无未来迟发工作。

| 阶段 | Runtime row / correlation | API区间(ns) | 对应D2H |
|---|---|---|---|
| prefill内部 | 17440 / 61647 | 20996393139–20996484466 | correlation61646，1 byte |
| token0 | 19142 / 90859 | 21085435931–21085463331 | correlation90858，8 bytes |
| token1 | 20736 / 116224 | 21160422320–21160447157 | correlation116223，8 bytes |

三条cudaStreamSynchronize均return0，分别关联CUPTI sync row347/348/349，
context1/stream7/activity device0；不能仅凭字节数断定内部Python调用点。
目标窗口观察到3492 kernel、3 copy、3 memset，均此PID/context/stream/device；
9672 Runtime行均来自同globalTid，返回码无非零。每项GPU活动存在同进程Runtime
correlation，未观察到活动跨request首尾或prefill/decode界。以上不等于完整W(s)、
唯一terminal或零丢失证明，也未把API/activity时长当exposure。

## 设备、诊断与尚未取得的资格

manifest/preflight目标physical3/logical0；SQLite CUDA_DEVICE的PID50660/cudaId0
指向gpuId2，GPU inventory id2的UUID和PCI匹配目标；activity device0沿进程CUDA
映射联结，不以0=physical/inventory推断。CONTEXT_INFO明确PID50660/context1的
nullStreamId=7；stream7确为默认/null stream，但这不确定每次调用的legacy/PTDS
语义或完整依赖闭包。当前synthetic-only入口的DEFAULT_STREAM_NOT_SUPPORTED仍有效，
不能删除检查或把模型换stream以掩盖此真实准入缺口。

24条DIAGNOSTIC_EVENT中，目标PID报告13 NVTX、28804 CUDA events；另有CUPTI
produced计数29682/29687，计数层级/时点不同，不能相减解释为丢失数量。
“Not all NVTX events might have been collected”及CUDA未正常启动警告关联
PID65108/65272而非目标50660；保留其范围，不能删除，也不能仅因不同PID便证明
其对目标必要依赖无影响。目标注入成功/计数非零/SQLite完整均不使dropped UNKNOWN变零。

当前能确认的是三个已观察sync及活动关联。不能发布supported/B-valid覆盖比例：
API识别不等于依赖scope受支持，分母完整性和B资格未通过。缺少独立真实device/source
准入与目标依赖影响证明；pass identity的raw/device mapping hash为采集前null，后续
须在独立派生receipt中绑定，不回写producer。当前没有合格A、B或D/Signature产物。

## 下一项最小工作

本地对本包三个sync形成逐项target-scope准入/拒绝清单：成功drain前缀上界、
request后缀提交与必要依赖、默认流条件等价所需条件、跨进程警告影响范围；
只能按已批准合同给出受证结论。不能闭合的边必须具体保留UNKNOWN，不再要求统一
全capture认证、不继续无界索源、不盲重采。新Q0增量仍须独立oracle验证，不能以
此真实诊断替代。服务器暂不操作；Gate7 PASS，新Q0/Gate8 NOT_RUN。
后续回传统一一个包含prepared/collection/logs及完整清单的ZIP，不重复三份副本。

## 7.62 三sync准入清单与本地独立预期

继续检查已批准的request-drain amendment §2–3：它明确限定合成来源、非默认流，
且不新增UNKNOWN mode等价规则。因此当前不能仅更换basis或删除DEFAULT_STREAM门
来实现真实准入；阻塞不是“尚未写adapter”这一工程问题。

| 条件 | 本包可直接证明的部分 | 尚不能证明的部分 |
|---|---|---|
| T与drain | 三point身份/同钟/顺序、原drain成功与物理scope | drain不保证其它来源今后不提交 |
| 三sync | 各自Runtime/physical sync唯一关联、成功、同TID/context/null stream | 每次默认handle/mode，以及未记录incoming依赖不存在 |
| 后缀提交 | 已记录3498项GPU活动都能关联Runtime；内部sync没有漏出审计 | 记录集合之外没有改变W的其它blocking stream/event/迟发活动 |
| 资源与来源 | 已记录目标窗口无Create/Destroy/Reset/Event API，配置sdpa | native路径及缺失记录范围不能由配置或API缺席肯定证明 |
| 其它进程警告 | PID与目标不同；不应一律算目标丢失 | 是否存在目标必要依赖关联，现材料没有肯定排除依据 |

`tests/test_gate8_default_scope_obligations.py`使用既有S→A实现及独立手算，
不是新增准入算法，也不从真实trace制造synthetic完整性证书：

- 正例以完整单FIFO为**显式fixture前提**，三sync=[30,50)/[90,110)/[160,180)，
  三K=[20,40)/[80,100)/[150,170)，三个submit各2ns；全窗[0,200)，phase界120。
  LEGACY、PER_THREAD各自得到full A=(134,6,30,30,0)，prefill=(76,4,20,20,0)，
  decode=(58,2,10,10,0)。这验证条件性算术，不是给实际调用指定mode。
- 反例另一blocking stream E=[0,60)，默认K=[60,70)，sync=[30,75)：
  terminal同为K，但LEGACY wait=40、PTDS wait=10；terminal相同不足以保证A相同。
- 从反例隐藏E后，分析器在被错误声明完整的输入上仍可守恒且unknown=0；
  这直接说明“活动一一关联/单stream/守恒”不能自证归属正确。
- mode UNKNOWN保留三sync共60ns unattributed；不可界定全窗风险则200ns全部
  unattributed。两者是不同证据条件，不能用局部unknown覆盖未知影响范围。

这些新增的是既有行为的独立回归预期，非生产修复，不声称经历不存在的RED→GREEN；
实际文件入口的默认流/真实source拒绝及旧Q0 S/A回归一同验证。没有新增Q0采集或资格。

**准确停止点：**未证命题是“drain后至最后completion，所有可能改变三次sync A交集的
提交/依赖均在可解释范围内”。当前包及既有七文件不能唯一推出它。仅新增fixture或
用相同profile重采都不能补足。最小后续动作是对这一命题选择可实证的窄支持域证明，
或显式审议条件性claim/可定位unknown的合同变化；不能在本次授权内擅自把条件当事实。
不再申请服务器快照、换collector或换stream；本地可完成的独立反例与现门回归已先推进。

### 一个集中待决项：目标scope观测充分性，而非绝对不存在证明

以上反例是对过强推断的否证，不要求证明所有不可见世界均不存在，更不恢复全capture
厂商认证前置。研究可采用明确的受支持执行方式与观测充分性假设，但当前0.1证书没有
定义真实栈如何承载该假设，不能让实现者悄悄用四个true补上。

**推荐待审候选 `TARGET_SCOPE_ENGINEERING_SUFFICIENCY/0.1`，尚未生效：**
将单模型、单request、eager、固定backend配置、无用户并发/显式IPC/event、已驻留输入
及原drain限定为支持执行方式；以本次target PID的注入、三point、成功物理sync、设备/
时钟/submit关联和完整产物链作正证；所有可见冲突必须拒绝，缺失影响有证据局部化才
进入unattributed；未知影响范围仍拒绝。目标外警告单列scope审查，不一律转目标失败，
也不删除。默认流A条件性等价只在支持执行方式与后缀依赖范围证据共同成立时使用，
不能由单stream计数单独触发。物理S/B不改，D/Signature继续禁用。

该候选明确承认常规观测的残余不可检测风险；测试能证明已定义故障的拒绝，不能证明
任意隐身缺失都可发现。因此需用户确认是否接受这种**限定支持域的Engineering
观测充分性依据**，而非把它描述为全依赖的绝对证明。若接受，还须具体化真实source
receipt的可验证来源与反例触发条件；不是立即接受本包或开放当前门。
若不接受，当前包只能保持条件性诊断，不能靠再写测试或再采一次消除认识上的缺口。
这是一项真实证据准入amendment决定，不是底层文件组织选择；旧Q0/Gate7历史不受影响。

候选的最小可执行化不是再要求“完整native来源证明”：①固定上述执行配置与版本、
producer/输入/loaded-config字节身份；②逐窗口核锚点、drain、PID/device/context/clock；
③枚举全部已观察blocking API并核scope/return/correlation/资源冲突，不能漏内部sync；
④对每条diagnostic明确关联scope与处置，目标相关或影响不可界定错误拒绝；⑤以本节
正反例及受影响Q0检验已声明可检测故障。**另外明确声明观测无法排除的未记录incoming
依赖为残余风险/支持域假设，而非已证事实。**若用户不接受这一假设，不能称前五项
足以完成真实准入；若接受，先版本化其claim与质量门，再实现，不能直接将本包改判。

### 有界条件性A分量原型（不是合格A文件链）

对原ZIP的内存SQLite构造明确假设的ABInputs，调用现有A计算器；不伪造或保存
Canonical/S证书，不把结果送B/Derived。假设“已观察同FIFO提交前缀就是所需后缀”，
并以三point投影的同TID窗口作为条件性ownership，得到full_request以下ns：

| Host | CUDA API | device wait | sync residual | unattributed | 总窗口 |
|---:|---:|---:|---:|---:|---:|
| 81223925 | 81122141 | 21184 | 122380 | 3050445 | 165540075 |

这不是实际S恢复通过，只是条件性算术原型。三sync合计143564ns；若另外**假设**
缺口仅在三sync，把wait+residual全部保守转unknown后为3194009ns，其余不变。
若影响范围无法界定，整窗165540075ns保持unknown。143564不是任意漏活动风险的
上界；更不能用“小比例”放行。不将Host称CPU忙，不把这些条件性数值写入实际结果。

另发现可独立处理的工程缺口：6169个cuKernelGetFunction共3045778ns、2个
cudaStreamIsCapturing共4667ns没有活动correlation，当前A registry不能分类，
恰组成3050445ns的unknown，不能直接填成Host或non-submit。
[CUDA12.4.1 Library Management](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-driver-api/group__CUDA__LIBRARY.html)
将前者定义为取得function handle；[同版本Runtime API](https://docs.nvidia.com/cuda/archive/12.4.1/pdf/CUDA_Runtime_API.pdf)
定义后者为查询capture状态。这足以限定下一项API合同核对，但不从函数名宣称绝无
隐式等待或自动修改冻结registry。下一本地工程动作仅核对这两类是否可按既有A定义
版本化纳入non-submit及其失败/嵌套规则，先回归再最小实现；不需要服务器或新采集。
它与真实default/source准入决定独立，解决它也不会使本包取得资格。
