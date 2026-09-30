# N1 模型三组限定 Engineering 可行性收尾 0.1

2026-09-30；裁决：**PASS，仅限下述 N1 模型三组一次 Engineering 可行性**。
本记录关闭模型接线/实际支持域前置，不授 Pilot、Protocol Freeze、Formal、完整新版 Q0、
统计稳定性、干预收益或 Information Gain。它补足 N1 模型依赖，不改写
[Gate10 限定 G1 PASS](gate10_closeout_v0_1.md) 的范围，也不宣称 N1/G1 共同统计稳定域。

依据：[Gate9 分域资格](gate9_closeout_v0_1.md)、[N1 verified 模型合同](n1_model_wiring_v0_2.md)、
[内部 Raw 来源规则](n1_raw_provenance_allocation_v0_1.md)、[opaque allocation amendment](n1_opaque_allocation_v0_1.md)。
没有新研究语义或准入放宽；本次文档裁决与执行、分析版本严格分开。

## 1. 原件、版本与兼容

新原件 `n1_remaining_d25b4d1_once.zip`：38951058 bytes，SHA256
`e2fa13cf6fed9a46d9c61c2b78f2c2f083c64c45d3755ad93de4c645917849ea`。
清单 SHA256 `828b9fd5fe9101da8cb546620b308b04825f79252d385bd8cd31098c10fc8404`。
本地直接复核 CRC、安全/唯一路径、166 文件/165 项大小与哈希及完整覆盖；新审查副本不覆盖原件。

| 组 | 执行身份 | 分析/审查来源 | run_id |
|---|---|---|---|
| V0 | `c21d8358e42e764c37cf9b315d87235989a817e1` | 复用 7.108 新合同完整准入/复读及独立 Raw 审查；由 d51 交付绑定，非原 c21 失败分析 | `run-20260929T143145Z-94ec2e31` |
| Vmarker | `d25b4d1b782c9d5fd4c25bdc1d813aa24fa3dc7f` | 同版本服务器分析，当前本地独立交叉审查 | `run-20260930T082410Z-49b22a58` |
| V16 | 同上 | 同上 | `run-20260930T082813Z-74ba1f26` |

三组消费合同均为 N1 ownership `0.3.0`、S `0.4.0`、A/B `0.6.0`、API registry `0.2.0`，
opaque 预算 `N1_OPAQUE_ALLOCATION_BUDGET/0.1.0`。V0 review 记录 adapter 而非单独的 analyzer Git SHA，
不补造该字段；其已通过审查和内容身份见 7.108。d51→d25 仅续跑 reference/交付校验变化，未改 analyzer。

固定派生身份（分别为 V0 / Vmarker / V16 的 `domain.json` SHA256）：

- `aec788be61053c6edbdb6b262be5b19fbe9d5c25a5233159c1e3cd60bb011d08`
- `d275d89e6203edf7a0426e3b42640cd8b130f21ba284ae4e0df745c16622af28`
- `3434f5d8f798955003e6bc6e1353b976292c49ff2f81ce6cba25387faa737c27`

V0 被引用 review SHA256 `90d654334dcf28cfec670521516035c06c7a88a8949b82755c2ece250999a28b`；
原 ZIP 身份与旧 BLOCKED 保留于 [V0 原审查](n1_v0_review_v0_1.md)。
新包内 `baseline_reference.json`、`baseline_review.json`、四件 `baseline_binding` 原 preflight/claim/final/target，
与旧封存副本逐字节重联。四份 `reference_validation.*.json` 每份 57 项全部 PASS，
32 个 producer 文件的本次实际 hash/长度精确匹配旧执行字节；c21→d25 的 Git 内容逐文件相同。
24 个 LF→CRLF 表示、8 个 Git 原字节，仅用于解释已观测身份，运行时未归一化。
本次实际 `__init__.py` hash 为 `b46cf529e2c9e9d4b11d0c7f66ca755eedca1f942b82d59c2794da75e2f46268`；
7.109“当前服务器字节尚未观察”的缺口由这次原始回执关闭，而非反推上次失败。

## 2. 必需退出条件与直接证据

- **输入/执行/设备 PASS**：三组同内容 Qwen2.5-1.5B-Instruct、32/2、batch1、fp16/eager/SDPA/cache/greedy、
  warmup1/repeat1；公共 manifest/snapshot 相同，执行 commit 差异有上述兼容证明。
  实际输入 32、输出 2、非 early EOS，tokens 均 `[[463],[2529]]`；无自动 retry。
  模型 inventory SHA256 `72465c906baeb0cfa4fd94d21ef6c69c1cd8046bb68c61a94c02a1580d2541f9`，
  prompt SHA256 `4dffd0ddcbd3185c656ae4a27efaf5aab302febba6ead5df4d37d903a2091920`。
  复用固定 Windows/4090 栈；physical 3/logical 0、UUID/PCI、实际 CUDA probe、mask、解释器/PID和代码 seal逐项一致。
  模型本体未随包传回，复核的是服务器内容快照绑定，不冒称本地重新计算权重。
- **真实执行 PASS**：原服务器 CPU 日志 57 passed；两组 entry/driver/profile 均 exit0、无超时；
  producer COMPLETE，preflight claim/final、manifest/prompt、calls/ledger/source/input receipt 和派生文件引用一致。
  profile 分别 36.671 / 38.312 秒，driver 219.203 / 224.157 秒，均非 request 延迟或稳定开销估计。
  REP→一次 export→canonical SQLite 的 hash/退出记录一致；每组 15 个派生文件引用与封存清单吻合。
- **边界/ownership PASS**：warmup 与测量使用不同 held 显式非默认非阻塞流，实际锚点连接
  native handle/generation→成功 runtime sync→physical context1/stream17，不以编号相等推断映射。
  request 外成功 drain、两次 forward、两个 host-readable token completion 及三窗口的同 trace clock 原始锚点一致；
  Host ledger 与 trace 锚点分开保留，不声称 marker 延迟为零。模型加载/warmup/cleanup 不加入 request。
  局部 held 生命周期证据不改写全局 `stream_lifetime_status=UNKNOWN`。
- **干预 PASS**：V0 测量干预 0；Vmarker 在 decode token1/layer16(index15) 后 1 marker、0 runtime sync；
  V16 同位置 1 marker、1 成功 sync。V16 Runtime20193 / correlation105548 / physical sync351，
  PID66812/TID52604、context1/stream17 与实际调用相连，非只核配置值。
- **S/B/A PASS**：独立只读 SQLite→Canonical 原字段与记录覆盖、correlation/同流提交序列、完整 FIFO、terminal、
  区间 union 与保存结果交叉一致；不调用被审查 S/A/B 函数生成预期，不重跑完整 analyzer。
  Vmarker/V16 各 3498 个测量流 activity；没有观察到其他流提交或 event/graph incoming 依赖。
  旧 V0 复用已完成的独立检查，不重算、不重采；未记录 incoming 依赖仍属明确支持域假设。
- **诊断规则 PASS**：两组各 19 条诊断，四条既知 warning 分别关联其他进程 54104 / 64704；
  目标 62444 / 66812 均有实际 CUDA/NVTX，消息/rowid/原 SQLite 对应。
  沿用 `G8-WARNING-EVIDENCE/0.1` 用户回传官方依据，无新消息或目标冲突；未删除原诊断、追索 PID或追加询证。
  `dropped_records_status=UNKNOWN`、`measurement_validity=NOT_ASSESSED` 原样保留，不授零丢失认证。

## 3. 三窗口 A 与逐 sync B

以下全部为 trace 共同锚点窗口，单位 ns；不是三组性能比较。

| 组/窗口 | 总时长 | Host | CUDA API | Device wait | Sync residual | Unattributed |
|---|---:|---:|---:|---:|---:|---:|
| V0 Request | 212715004 | 119176616 | 92285548 | 223646 | 1029194 | 0 |
| V0 Prefill | 128172644 | 67308362 | 59637741 | 223646 | 1002895 | 0 |
| V0 Decode | 84542360 | 51868254 | 32647807 | 0 | 26299 | 0 |
| Vmarker Request | 200583364 | 107582899 | 91909546 | 35712 | 1055207 | 0 |
| Vmarker Prefill | 109012715 | 57698451 | 50251778 | 35712 | 1026774 | 0 |
| Vmarker Decode | 91570649 | 49884448 | 41657768 | 0 | 28433 | 0 |
| V16 Request | 235519187 | 150680836 | 82314243 | 813690 | 1710418 | 0 |
| V16 Prefill | 130748257 | 85483279 | 43597198 | 75328 | 1592452 | 0 |
| V16 Decode | 104770930 | 65197557 | 38717045 | 738362 | 117966 | 0 |

九窗均五类互斥守恒、API/等待子类守恒、边界连续，逐分量 Request=Prefill+Decode。
新两组还独立按已获支持的实际 API 类别、Raw 同步/必要 activity 的裁剪 union 验算顶层及 API 子类；
不存在以 unknown=0 代替准入、将未知转 Host 或重复计入 opaque 预算。

| 组/physical sync row | 身份 | 完整 W 数 | terminal | B exposed union(ns) | validity |
|---|---|---:|---|---:|---|
| V0 348 | 内部 Raw | 8 | Memcpy344 | 223646 | B_VALID |
| V0 349 | token0 | 1906 | Memcpy345 | 0 | B_VALID |
| V0 350 | token1 | 3498 | Memcpy346 | 0 | B_VALID |
| Vmarker 348 | 内部 Raw | 8 | Memcpy344 | 35712 | B_VALID |
| Vmarker 349 | token0 | 1906 | Memcpy345 | 0 | B_VALID |
| Vmarker 350 | token1 | 3498 | Memcpy346 | 0 | B_VALID |
| V16 349 | 内部 Raw | 8 | Memcpy344 | 75328 | B_VALID |
| V16 350 | token0 | 1906 | Memcpy345 | 0 | B_VALID |
| V16 351 | n1_intervention | 2814 | Kernel6302 | 738362 | B_VALID |
| V16 352 | token1 | 3498 | Memcpy346 | 0 | B_VALID |

内部同步保留 RAW_PHYSICAL 成功/进程/clock/request/phase 来源，源码 origin/callsite/ordinal 仍 null；
token-ready 和预定干预均 STRUCTURED，不能由宽泛 forward 范围伪造。
V16 干预的完整 W 包含其入口前已完成的 2802 项；独立 hidden union=32019118ns、return tail=28636ns。
decode W 保留 prefill 成员及原 phase，不按阶段截断物理依赖。
这些 B 仅解释各自同步，**不得跨同步相加，也不能把 hidden 解释为整个 request 未暴露**。

## 4. Opaque allocation 与结论限制

每组三次成功 `cudaMalloc_v3020` 均在 Prefill，逐调用完整区间/唯一归属、无嵌套相交、无关联 activity/sync 冲突、
真实 drain/非阻塞流和下游完整依赖已核。新两组实际 API 覆盖为四种 submit、两种已注册查询、cudaMalloc 和 stream sync；
每个 request API 均有唯一消费绑定，不靠名称或“无 activity”推断 allocation 非阻塞。

| 组 | Runtime rows | correlation IDs | 三次占据时间(ns) | 合计(ns) |
|---|---|---|---|---:|
| V0 | 17566/17579/17646 | 61737/61867/62931 | 773224 / 176954 / 686985 | 1637163 |
| Vmarker | 17566/17579/17646 | 61743/61873/62937 | 424413 / 388609 / 1181198 | 1994220 |
| V16 | 17567/17580/17647 | 61748/61878/62942 | 803309 / 234109 / 246157 | 1283575 |

全部大小为 null、内部等待 NOT_DECOMPOSED。该预算已含于 CUDA API non-submit，不能二次相加；
non-submit 不等于非阻塞；不构造 allocation W/B、不删先行活动。
`A_device_wait` 只覆盖受支持同步恢复的等待，不声称穷尽 allocation 内部等待。
实际 allocation 差异照实保留，不能将单次 E2E 差异归因全部同步干预或宣称稳定收益。

原 V0 BLOCKED、新包 `PENDING_REVIEW`/`NOT_QUALIFIED`/`NOT_ASSESSED` 等原字段不改；
它们是原执行/诊断状态，新的限定可行性裁决只存在于本独立审查记录。
D/Signature 仍禁用，完整新版 Q0 与科学有效性/信息增益未自动获得。

## 5. 收尾与唯一下一步

本次无生产代码/schema/合同变化，无测试重跑、全量分析、Q0、服务器/GPU/Nsight/模型操作；
仅直接读取回传原件、独立只读证据核对及文档更新。服务器 CPU57 是原日志，不是本地新成绩。
必要检查已满足，无新的部署、服务器补证或重采任务；用户 DOCX 修改保留在提交之外。

**Gate7～9及Gate10限定G1 PASS保持；N1三组限定Engineering可行性PASS；Gate11 NOT_RUN。**
7.111澄清：N1三组是独立准备依赖，不替代OOM探索；Gate10只证明固定配置下选定G1三点一次可行，容量和统计稳定域均未确定。
下列7.110本地准备已在[原workload计划的Gate11段](gate10_workload_plan_v0_1.md#gate11-local-preparation)具体化；角色/配对适配及Pilot数值依据仍待完成，不需要为本文档更新服务器。

7.110原准备项（保留来源）：

1. 从已有 G1 32/128/512 输入候选与 N1 固定32/2三组中，按研究问题选择最小代表集；不按本表比例/效果挑点，不扫描新位置。
2. 拟定有界 Pilot 的配对/组序、重复与停止规则、overhead/质量/排除评估方法及单批证据清单；
   正式 repeat/阈值需 Pilot 依据，不能由本次单次时长确定。
3. 形成最小 Protocol Freeze 输入缺口清单；Pilot 数据独立新采、另行审查授权，不把 Engineering 复制成 Pilot/Formal。

无需为此再做资格层、监控、整套 Q0 或当前服务器检查。
