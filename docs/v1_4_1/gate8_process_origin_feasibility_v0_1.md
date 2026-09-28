# 子进程来源方案最后一轮可行性审查 0.1

2026-09-28；Engineering；审查实现 `ebdf4eb7f338a425e3eb758c878f42f009111b91`。
**结论B：记录器不能单独关闭关键缺口。停止追加实现，不部署、不重采。**
它能改善未来adapter调用的来源事实，不能证明旧PID角色，也不提供警告影响范围证书。
本结论不是认定Nsight必然全局失效或永远不支持范围证明；是当前证据不足以设计一次
保证补齐该缺口的最小执行。没有为此恢复全capture零丢失认证要求。

## 1. 实际调用覆盖（源码可核验，不是服务器运行断言）

`gate8_target_python.model_entry`在导入模型入口前开启记录，模型入口返回/异常后闭合。
`run_diagnostic`成功走到模型前，显式应用调用为：

| 调用路径 | 新记录器覆盖 | 边界 |
|---|---|---|
| `run_diagnostic` → `validate_pre_model_identity` → adapter.git `rev-parse HEAD` | 是 | 一个直接子进程，GIT_COMMIT_QUERY |
| 同上 → adapter.git `status --porcelain` | 是 | 一个直接子进程，GIT_DIRTY_QUERY |
| `run_diagnostic` → `TorchBackend.identity` → adapter.nvidia_smi GPU index/UUID/PCI查询 | 是 | 一个直接子进程，NVIDIA_SMI_QUERY；在模型加载/drain前 |
| prepare阶段Git/manifest/GPU查询及显式解释器probe | 否 | 发生在外层prepare进程，model_entry记录会话之外 |
| collector的nsys版本查询/profile/export及Nsight创建目标进程 | 否 | 外层launcher/原生工具，不走目标adapter |
| PyTorch/Transformers导入或加载中第三方Popen、native创建进程、子进程再创建后代 | 否 | 不猴子补丁、不监控进程树；即使有此行为也不能从空记录排除 |
| current()、文件hash、Torch CUDA身份API、模型/warmup/request | 非子进程记录对象 | 不为这些操作编造STARTED；其中若间接经adapter则按真实调用记录 |

定位：`exposedpath_v141/gate8_target_python.py:model_entry`、
`exposedpath/gate8_diagnostic.py:run_diagnostic/prepare_diagnostic`、
`scripts/gate7_smoke_validation.py:validate_pre_model_identity`、
`exposedpath_v141/gate8_source_probe.py:TorchBackend.identity`、
`scripts/gate8_diagnostic_collect.py:profile_argv/main`。
`runner`另有parity/telemetry的nvidia-smi函数，但这条`run_gate8_requests_to_files`路径不调用它们；
不能把全文件命中当成本attempt调用次数。异常提前退出也可能少于上述三次。

两个旧未知PID10988/54228可能来自上述工具或未覆盖来源，**三次命令不对应两个PID**，
不能按数量/时间/NSys线程标签认领。未来匹配记录至多证明某个Popen实例及发起用途；
解析启动文件不是OS最终映像认证，call_id不是OS出生时间。父单调时钟也未与诊断
HostTimestamp建立换算，PID复用/namespace关联仍不能靠数字相等替代。
所以新增一次执行可能回答“哪些adapter工具确实启动”，但不能保证回答
“旧两个PID是谁”或“新warning是否不影响目标request”。

## 2. 四类warning逐项判定

原SQLite `DIAGNOSTIC_EVENT` rowid与globalPid见[封存审计](gate8_qwen_diagnostic_scope_audit_v0_1.md)。
本轮再次只读查询实际字段：timestamp、timestampType、source、severity、text、globalPid；
没有affectedPid、丢失区间、buffer scope、宿主exe/parent或dependency影响字段。
八行均severity=2/source=3/timestampType=2；globalPid给出记录关联对象，不能单独证明排他影响。

| 类别／原行 | 现有事实能证明 | 能否支持“影响仅限已识别进程” |
|---|---|---|
| NVTX可能未收全，2/5 | 与两个globalPid关联的潜在NVTX不完整警告；不是已证实零丢失 | **不能**：没有丢失范围/数量，资料未定义该消息的排他作用域；身份已知不补齐此项 |
| 未采到NVTX并询问是否使用，3/6 | 该诊断报告未收到NVTX事件，可能与无instrumentation相容 | **不能据现有包放行**：如另有可验证的纯辅助用途，可说明零事件不意外，但不能抵消同行“可能未收全”或证明collector隔离 |
| CUDA profiling可能未正确启动，7/10 | 关联进程的启动异常可能性，而非确定根因 | **不能**：未给出失败组件、影响context/进程边界；无依据认定共享采集功能未受影响，也不反向断言必然受影响 |
| 未采到CUDA并询问是否使用，8/11 | 该诊断报告零CUDA事件 | **不能据现有包放行**：已证明无目标依赖的非CUDA辅助程序可以解释零事件，但无事件本身不证明未调用CUDA，且不解除启动警告 |

不是四类一律认定全局错误；后两种“零事件”消息存在可解释的非故障情形，
但本包缺宿主事实，且每个PID同时伴随两个不完整/启动警告，现有组合不能局部豁免。
不通过“目标事件非零”“约2.78% unknown很低”或身份白名单跨过这个缺口。

## 3. 版本资料与准入依据

目标CLI版本2026.2.1.210-262137639646v0。已传回安装资料为版本锚，不把在线滚动页冒充该build：

- UserGuide.html SHA256 `5B100930126F3A3A819F13DD8335EFC0BC2CD7F8BF0207A7063D57ACB4C33E7C`：
  原HTML行785的`--cuda-trace-scope`明确process-tree含目标及子进程；证明为何辅助子进程可能被追踪，
  **不定义warning的影响隔离**。CUDA Troubleshooting / Flush CUDA Profile Data，行10205–10213，
  描述异步buffer及context flush；不为本次四消息提供进程排他性保证。
- ReleaseNotes.html SHA256 `9D007C391B840BD5CCCC5EC7D5C54673E9CCF573DC5047A57E6F7AB5ED1B71FE`：
  CUDA Trace Issues行590–614的teardown loss有CC-DevTools/libcrypto条件；不是本包根因或范围证书。
- AnalysisGuide.html SHA256 `BDCF574189E7EB687D4DC7C52BCEBACAE9C700C5A93A9E3AED8FF674960CBB11`：
  行5875附近lost events属于CPU sampling/thread utilization，不能迁移为CUDA/NVTX证据。
- export_schema_version_notes.txt SHA256 `F396286BDB91EF40BC40741CAB81876BA731FEC2ED8D07B53D4E9E6D52B536A1`：
  行444记载加入DIAGNOSTIC_EVENT，未给四消息排他影响合同。实际schema亦缺上述范围字段。
- 对照[官方User Guide](https://docs.nvidia.com/nsight-systems/UserGuide/)的同名选项和troubleshooting；
  本轮有界官方检索没有找到这四条消息在目标Windows build中的排他作用域定义。
  旧Linux/不同版本论坛案例不作该build依据，不再继续泛化搜索。

已批准依据是[Engineering sufficiency 0.1](gate8_engineering_sufficiency_amendment_v0_1.md)
“诊断与unknown”及“0.1实现合同”：外PID不是自动OUT_OF_SCOPE，影响不明拒绝。
[路线A质量门0.1](gate8_route_a_quality_amendment_v0_1.md)允许有证据界定的局部缺口，
不允许将进程身份直接变成影响证书；也不要求全capture厂商认证。
目前没有需要修复的已证实scope adapter丢字段问题。本轮不修改这些合同或warning门。

## 4. 有限备选与停止点（都不自动执行）

1. **窄范围语义澄清，信息价值最高**：若协调窗口决定解除询证暂停，只询问目标build四类消息
   的globalPid是否等于受影响范围、是否存在共享collector失败传播、无CUDA/NVTX辅助进程的预期行为。
   不要求零丢失认证，不传Raw。代价是外部答复不确定；明确答复后才判断记录器是否足够及是否需
   小范围规则amendment。无答复/仍模糊就停止，不无限等待。本轮不发询证。
2. **避免已知辅助进程进入被profile目标，改变执行组织而非忽略警告**：将Git/nvidia-smi预检放外层，
   目标内部用固定输入/code bytes与GPU原生身份核验绑定；必须保留执行前一致性，不能直接删掉检查。
   代价是需要另行设计/批准身份新鲜度与TOCTOU防护并做CPU回归；不改模型/窗口语义的可行性仍待明确。
   它消除三个显式候选，不证明第三方/native不启动，也不解释旧warning；**目前不是已就绪的一次执行方案**。
   若未来新attempt仍有影响不明警告，立即停止，不能再次以加监控/重采循环推进。
3. **停止此模型链的验收投入**：保留限定受控资格和模型反事实诊断，明确未取得可信真实模型A。
   无新增执行成本，但路线A的真实request与信息增益claim尚不成立，不能用受控例替代。

推荐协调窗口先在1（仅消息范围的有限澄清）与3（暂停该链）间决定；若坚持自主推进，2需要先解决
具体身份替代合同，而不是先跑模型碰碰运气。现有记录器保留为已验证的可选Engineering基础设施，
不再扩展、也不作为重采理由。此处没有重新要求一般工程授权，而是明确当前方案不能保证取得缺失证据。

反事实A仍隔离于独立v0.2目录，trusted_a=false。6171条局部缺口4988324ns约4.99ms/2.78%，
不改分类、不用低比例证明warning安全。原BLOCKED、UNKNOWN、物理S/B及封存产物不改。
Gate7 PASS、限定受控资格不变；完整新版Q0/Gate8 NOT_RUN，D/Signature关闭。
