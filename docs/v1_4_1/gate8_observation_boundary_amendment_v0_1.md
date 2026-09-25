# Gate8 Observation / Boundary Amendment v0.1

**ID `G8-OBS-BOUNDARY/0.1.0`；2026-09-25，D1方向已获用户批准，设计已编制、生产尚未实现。** 本轮授权只含amendment/schema/独立测试预期及文档提交，不含生产修改、服务器部署或Q0/GPU/Nsight采集。

## 1. 适用性与不变量

增补[Measurement Contract v0.2](measurement_contract_v0_2.md) §3–5、§9、§15的观测接口，不覆盖其正文，不改变host-readable语义、W(s)、terminal、A优先级、B/D公式。依据研究设计v7.1及实验协议v2.1 Pre-Pilot。仅用于实现本amendment、明确绑定版本后的**新Engineering attempt**；旧Gate7/Prototype不能改名升级。历史Gate6资格仍绑定原commit/adapter/schema，PASS不撤销。

JSON Schema：[observation_boundary_schema_v0_1.json](contracts/gate8/observation_boundary_schema_v0_1.json)，Draft2020-12，闭合对象、拒绝未知版本。它是**独立设计schema**，不是把现有Canonical0.2声明为已支持新字段。现有loader未消费它；实现时采用显式新profile `G8-OBS-BOUNDARY/0.1.0` 和独立sidecar，旧v0.2路径不静默fallback；生产package/adapter版本必须随实现另行发布并记录。Raw v0.2时间和record ID不改写。

| 记录schema | 职责与版本 |
|---|---|
| exposedpath-boundary-payload/0.1.0 | producer非同步point payload |
| exposedpath-completion-anchor/0.1.0 | 原NVTX record + producer ledger关联的观测事实 |
| exposedpath-scope-projection/0.1.0 | 仅由原锚点按冻结窗口公式派生的scope |
| exposedpath-pass-identity/0.1.0 | per-pass多request/attempt来源sidecar |
| exposedpath-device-mapping/0.1.0 | physical/logical/trace namespace映射 |
| exposedpath-observation-integrity/0.1.0 | 每channel完整性证据与unknown |
| exposedpath-gate8-design-error/0.1.0 | 适配层错误，不冒充S原因码 |

## 2. Producer与锚点

完整identity键为`experiment_id,wmpc_id,run_id,pass_id,attempt_id,request_id,repeat_id`；`data_role=Engineering,run_role=ENGINEERING`逐载体一致。新run与历史PILOT字符串分开，历史不重写。每request在同一Host线程顺序执行；跨线程GPU enqueue仍受现有S ownership规则，不因point而新增线程归属能力。

producer使用独立前缀`EXPOSEDPATH_BOUNDARY_V1:`携带schema中的boundary_payload；`kind=boundary,marker_role=non_sync_marker`，不改既有sync marker origin。新前缀由显式adapter版本支持，旧consumer遇到它不能宣称新版窗口已支持。

- `request_start`：predrain已返回、输入resident、紧邻首次forward，token_index=null。
- `token_ready(i)`：既有detach/cpu/Host值读取完成后的共同helper程序点，i从0连续到N-1；首/后token同路径；不额外CUDA sync/event。host值用于EOS，不二次GPU读取。
- helper记录`host_observed_ns`，在标记调用前/后采样`host_before_marker_ns/host_after_marker_ns`。全部为同进程`PYTHON_PERF_COUNTER_NS`；Pass0不发NVTX，保留等价helper语义/输入/同步及host时间。不得为追求时钟相等给Pass0加GPU操作。
- Pass1 NVTX point的原始`start`成为anchor.trace_ns。`raw_ref`含SQLite hash、table、rowid、record_id；pid/tid从原表解析，payload由原text重解析，不信缓存identity。
- ledger用boundary_id一一关联host记录、预期序列和trace record；ID不根据时间排序生成。缺点、重复、冲突或错request不合并。原始marker payload、clock与记录引用保持。

**观测延迟/开销：** host_observed≤before≤after，报告marker调用包络`after-before`和`before-host_observed`，不把它们当作真正Host可读物理瞬间的误差上界；操作完成与host采样之间的调度延迟仍不可由这三个值精确确定。Nsight point发生在调用内部，但不能直接与host数值相减。报告Pass0/1对应repeat的描述性延迟差，不据此扣除marker成本、不拟合clock offset、不设未经Pilot批准的误差阈值。缺clock/倒序阻塞；开销大但量化阈值未冻结时记录并等待审查，不能默认为零误差。

## 3. Canonical与Scope projection

原NVTX point留在Raw/Canonical，不伪造原始request/phase range；anchor sidecar关联Raw事实。全部semantic timestamp为signed-int64整数ns，clock=`NSYS_TRACE_RELATIVE_NS`，禁止归一化；host timestamps仅诊断。

每个COMPLETE measured request必须有唯一r及N个token锚点，r<t0，token序列严格递增（N=1仅r<t0）；request不能重叠，warmup不产生measured窗口。earlyEOS或token不足按原协议EXCLUDED，不用短窗口混入计划N。

从同一trace、identity、pid/tid的原始锚点计算：

| phase | start_ref / start_ns | end_ref / end_ns |
|---|---|---|
| full_request | r原record / r.trace_ns | tLast原record / tLast.trace_ns |
| prefill | 同一个r | t0原record / t0.trace_ns |
| decode | 同一个t0 | 同一个tLast；N=1为相同ref、零时长 |

projection同时绑定canonical manifest、anchor artifact及pass identity hash。schema字段相等、引用解引用后数值相等、hash/身份/clock相等均为**语义验证**，不是JSON shape检查可替代的。projection内`dependency_evidence=false`恒定：它只提供请求/phase窗口和ownership边界，绝不生成GPU边、W(s)成员或terminal。

S与A共同加载已验证scope。S继续用同线程覆盖/可信marker、correlation/context/stream/event等既有规则，外部activity保留并参与closure检验；完整范围外的初始化/尾部不是A窗口，也不能被删除来消除bleed。A直接按scope切片，B仍一条physical sync一行；所有输出lineage额外记录projection/profile/pass-identity hash，不能只写旧schema而隐藏新路径。若旧structured range与新projection同时声明相同request，必须显式选择新profile并验证其声明无冲突；不得混用两套边界悄悄选有利范围。

## 4. 身份、设备与hash闭环

WMPC保存共享输入/模型/commit，不填单个repeat。每pass采集前计划记录planned IDs/输入hash；完成后写不可覆盖的pass identity sidecar，含request ledger、outcome/actual tokens、pid、WMPC/prompt/runner hash、commit clean、Raw hash与device mapping hash。ledger的`expected_boundary_ids`与`observed_boundary_ids`分别保留，失败不能删计划项。warmup显式request_role，不计measured repeat。Pass0 raw/device mapping可null；Pass1完成且进入科学链时不得null。

Canonical/sidecar显式声明`identity.requests[]`来自pass identity，不能把一个repeat写到整个bundle顶层。重复request_id在同pass/attempt非法，跨pass配对使用run/wmpc/repeat/request计划键，attempt从不混合。请求排除理由不从文件名推断。Hash单向：WMPC/计划→producer ledger/Raw→完成pass identity与mapping→Canonical/anchor→projection→S→A/B→coverage；禁止反向把派生hash写回Raw/WMPC造成循环。host ledger不能引用尚不存在的anchor文件hash。

设备映射：preflight physical ordinal/UUID/PCI → 同进程logical probe UUID/PCI → SQLite `TARGET_INFO_CUDA_DEVICE(pid,cudaId,uuid,gpuId)` → `TARGET_INFO_GPU(id,uuid,busLocation)` → context/activity的process/device/context。`gpu_index=gpu_index_physical`只用于物理身份；`selected_device_id=trace_device_id`来自经核验trace scope，绝不fallback physical。保留preflight/probe artifact hash+selector及三类表record refs。UUID严格规范化，PCI按四元组解析（值超界拒绝，不能截断）；逻辑编号、inventory ID不要求等于physical。多候选、缺字段、pid/UUID/PCI不一致均拒绝run，禁止按显卡型号认卡。context/stream局部未知按现有S原因保留，不新增推断default-stream模式。

## 5. 错误与完整性

独立error记录保留stage/code/affected requests/source refs/action；坏产物不输出“VALID scope”。

| adapter错误码 | 处理 |
|---|---|
| IDENTITY_CONFLICT / DEVICE_MAPPING_UNPROVEN / SOURCE_HASH_MISMATCH / PROFILE_VERSION_UNSUPPORTED | REJECT_RUN |
| BOUNDARY_MISSING / BOUNDARY_DUPLICATE / BOUNDARY_ORDER_INVALID / BOUNDARY_IDENTITY_CONFLICT / CLOCK_DOMAIN_UNRESOLVED / PROJECTION_REF_MISMATCH | REJECT_WINDOW；缺必需measured窗阻塞run验收 |
| OBSERVATION_INTEGRITY_UNKNOWN / OBSERVATION_INTEGRITY_CONFLICT / OBSERVATION_LOSS_CONFIRMED | BLOCK_SCIENCE_ACCEPTANCE；保留独立状态，不把unknown称已丢失 |

integrity按CUDA_ACTIVITY/NVTX通道保存收集器版本、session、Raw/pass hash、pid/trace区间、finalized/coverage_complete、证据selector/hash。counter全会话肯定0或版本明确的等价完整性声明且无反证才ZERO_CONFIRMED；声明没有数值count时count=null，不能填0。正数NONZERO；缺证据UNKNOWN/count=null；矛盾CONFLICT。NVTX ledger双向完整匹配是附加必要条件，不替代CUDA完整性。针对其他PID的warning只有被证明不影响目标scope才可局部化，不能泛用Q0专用tail例外。

## 6. Q0影响与资格验证设计（本轮不执行）

| 路径 | 必须验证 |
|---|---|
| 新scope ownership/phase | Q0-PHASE-SPILL-001、EXTERNAL-001、INVOCATION-BLEED-001、MULTITHREAD-ORDERED-001、OVERLAPPING-HOST-SYNC-001；旧range路径结果不变，新projection独立fixture含跨线程和外部依赖 |
| device/context及关联 | Q0-STREAM-001、DEVICE-001、CONTEXT-001、EVENT-001、EVENT-XSTREAM-001、MISSING-CORR-001、MISSING-EVENT-001；额外三namespace不等、错PID/UUID合成负例 |
| 完整性/默认流 | Q0-DROPPED-001、DEFAULT-LEGACY-001、DEFAULT-PTDS-001；额外unknown/冲突/缺scope/clock负例 |
| 保持语义与D2联动 | COMPLETED-001、EMPTY-001、TERMINAL-TIE-001、SUBMISSION-RACE-001、SYNC-D2H-UNSUPPORTED-001、QUERY-001；其余既有case也纳入23case静态差异审查 |

先独立手算fixture与producer→adapter回归、既有Q0 oracle离线兼容验证；新profile上目标栈真实边界/identity/完整性验证及受影响真实Q0须**另行授权**。只有版本绑定、对应expected比对和qualification回执完成，才可声明新版本合格。哪些真实case需重采/哪些允许对不可变原输入重放，由实现diff后的影响矩阵明确，不自动全盘复跑，也不能用旧PASS取代新验证。旧Q0 phase-spill例外不扩展到新LLM；新LLM三个窗口仍严格共享端点。

测试预期见[独立手算规格](gate8_design_test_expectations_v0_1.md)。未发现必须修改冻结数学语义的需求；如果实现需要新增API支持、改变ownership例外/terminal/clock归一化，立即停下另行审批。
