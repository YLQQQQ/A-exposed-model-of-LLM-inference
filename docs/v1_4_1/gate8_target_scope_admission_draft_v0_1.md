# Target-scope admission 0.1 — 未生效草案

状态：`DRAFT_NOT_APPROVED`。本文件不注册生产 schema，不赋予新 Q0 资格，不授权采集。
提议 ID：`exposedpath-target-scope-admission/0.1.0`；审计基线 `3296123`。
仅限 Route A 单 GPU、eager、串行 request；不改变 W、A/B、D 公式及旧 reader。
本草案细化[支持域方案](gate8_model_scope_design_v0_1.md)，取代其抽象方向作为待审对象。

## 1. 来源核验与技术停止点

CUDA 12.4.1 明确默认流行为可按编译单元选择，并可传入显式 legacy/per-thread handle。
PTDS 关联 thread/context，且与 legacy 共存时可能发生同步，不能将一个进程简化成一个 mode。
依据：[目标版本 Stream synchronization behavior](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/stream-sync-behavior.html)。
动态入口还可按解析 flags 选择版本；这只是候选证据机制，不证明目标 wheel 的实际调用。
依据：[NVIDIA Driver Entry Point Access](https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/driver-entry-point-access.html)。

已固定的目标 header、PE imports/exports 及历史 SQLite 结论见
[来源对齐§10](gate8_eager_source_alignment_v0_1.md)：源码/导入表没有实际调用绑定，
nullStreamId、统一 API 名和空 callchain 也没有记录有效 mode 或完整 context/thread 寿命。
Nsight [User Guide](https://docs.nvidia.com/nsight-systems/UserGuide/index.html)描述 trace/NVTX/backtrace，
不构成本机 build 的逐调用 mode 证明；版本化在线页面本轮访问失败，不能用滚动文档冒充
2026.2 安装能力认证。已回传安装版UserGuide L5153起列有`cudaEventRecord_ptsz`、
`cudaLaunchKernel_ptsz`等API名；API列表不是该次执行入口、参数或寿命的证明。
安装文档和原件的既有审计仍有效，当前**未找到已验证的可执行
mode/连续性 adapter**，不是断言工具绝不支持。停止扩展安装/PDB搜索，不默认采样取栈。

## 2. 提议字段与最小准入规则

下表带 `新增` 的字段是待批准接口，现 producer 不应声称已输出。所有证据引用使用
`artifact_sha256 + record_namespace + record_id`；JSON 文件用版本和 JSON pointer，禁止裸行号跨文件拼接。

| 项 | producer／原始来源 | 新准入的检查与范围 |
|---|---|---|
| 身份/输入 | producer0.4五文件、manifest、Raw digest、source descriptor | 完整 hash DAG、run/pass/request/repeat/attempt；物理 UUID/PCI→logical→trace inventory/context 唯一绑定，不按数字等同 |
| completion | boundary marker 原 point、token序号、clock；host-readable结果已有 ledger | 既有D1唯一同clock三窗；缺失/倒序/重复冲突拒绝，不把 host timestamp 当 trace timestamp |
| 调用语义 `call_semantics[]`（新增） | 每条相关 Runtime/Driver API reference、correlation、PID/thread-instance/context、实际 stream 参数证据 | `effective_stream_kind=EXPLICIT/LEGACY/PER_THREAD/UNKNOWN`，必须有证据；API名称、stream_id=7或0均不单独定 mode |
| mode依据（新增） | `evidence_kind`、`evidence_refs`、`covered_call_refs`、适用 thread/context；若走编译来源则 exact binary/build/TU/callsite；若走动态入口则解析 flags→实际指针使用绑定 | 编译单元证明不可推广至整DLL/进程；显式特殊handle须证明实际参数；候选来源尚无可执行adapter。未覆盖相关调用保留UNKNOWN |
| 寿命 `resource_epochs[]`（新增） | context/stream/thread-instance创建/销毁或覆盖所需区间的明确生命周期来源；原始引用、clock、起止与覆盖理由 | 不以无destroy行证明连续；context/TID/stream编号复用必须拆epoch；PTDS同时依赖thread与context，legacy依赖context；对必要历史跨度逐项覆盖 |
| 原owner `origin_bindings[]`（新增） | stage/task原marker→同线程被包围API→correlation activity；绑定source hash | `SETUP`引用stage且request=null；`WARMUP/MEASURED`引用各自request；worker须task/thread-instance证据，不借主线程range归属 |
| 历史scope `dependency_scope`（新增） | 目标sync、先行提交、stream flags、event record/wait及上述epoch/mode | 列出必要历史起点及理由、原owner、缺口/反证；不截drain之前W，不要求已证明无关的全inventory有request projection |
| drain | drain ledger和同PID/TID唯一成功device/context sync记录 | 仅作相应completion证据，不代替模式/寿命，不重置物理W；窗口外不计本窗A |

**窄域策略：** 每个待分析闭包内，相关默认调用须证明属于同一已知语义族，且PTDS逐线程
保留身份；不得从一个调用外推。发现legacy/PTDS混合路径，本版拒绝为域外，不能把它
映射成单一全局字段。多语义混合不是CUDA非法，而是本版尚无资格支持。
旧 S 的 `execution_context.default_stream_mode` 只可在逐调用证明齐全且一致时派生供兼容；
不得作为输入自我证明。新 adapter/合成验证/受影响真实资格通过前仍保持现有拒绝门。

## 3. 拒绝与发布矩阵

| 证据情况 | 提议行为 |
|---|---|
| identity/clock/completion冲突、mode未知、epoch无法覆盖且影响不可界定、混合mode | 拒绝对应窗口可信A/B及D/Signature；保留Raw、diagnostics，不填零 |
| 已独立界定影响范围的局部缺口 | 只在证明的范围记unattributed，保留原因；受影响B为invalid/null；沿用Route A保守差值发布限制，不开放D_score/Signature |
| 可证明不进入目标必要闭包的记录 | 保留原始引用和排除依据，不因其无request owner拒绝目标窗；不能仅以窗口外判无关 |
| 所有必要证据齐备且新版本资格通过 | 按原W/terminal/互斥union分析；低unattributed仍需实际验证，守恒不等于正确性 |

UNKNOWN从不改成零丢失；不要求全capture认证。gap局部性不能由sync API短区间单独推出。

## 4. 独立预期与资格增量

- 正例：同一已证LEGACY流，setup X=[0,10)、warmup Y=[12,18)、request Z=[22,30)，
  sync=[25,35)，三次提交均先于sync；无其它必要边且terminal唯一。W={X,Y,Z}，
  hidden=19、exposed=5、tail=5；sync部分A wait=5/residual=5。setup/warmup原owner不变。
  这是手算合成预期，不是整request A或真实运行结果。
- 负例：同样数值但setup worker与request线程的PTDS不同且无incoming边，不能沿用上述W；
  若Y/Z同request线程，则W={Y,Z}，hidden=9。缺少mode证据应拒绝而非任选一组答案。
- 反例：一个调用证明LEGACY、另一个证明PTDS，或TID复用却未拆epoch，拒绝本版准入；
  即使A数值恰相同也不能放行B或A-only资格。
- 文件链反例：缺task绑定、混pass/hash、丢最后token marker分别触发来源／身份／窗口拒绝；
  不能由手填完整consumer fixture替代producer0.4实际文件入口验证。

复用旧Q0的stream/device/event、completed-before、PTDS/无关流、external、phase spill、
missing-correlation等独立语义与历史结果；旧reader/公式做回归，不全重采。
必须新增资格：默认调用mode/epoch→真实Raw映射、setup/worker原owner、跨warmup历史闭包、
D1及producer0.4文件接线。先上述确定性正反例，再仅覆盖变更的受控真实验证；
新真实接口不可继承旧0.2.2资格。Gate6/Gate7历史PASS不变。

## 5. 集中裁决与下一步

待用户批准的是§2逐调用证据及同族窄域、原owner/完整历史规则和§3拒绝矩阵，
不是宣称mode来源已解决，也不是采集授权。批准后可实现确定性接口；目标mode/epoch
adapter仍是**明确技术阻塞**。须提出能提供这些字段的具体来源和失效条件再申请最小采集。
一次source profile不能单独证明参数、编译模式、连续性或无历史遗漏；本轮不默认采用它。
不需要用户选择文件组织，不增加新指标，不改研究公式。
