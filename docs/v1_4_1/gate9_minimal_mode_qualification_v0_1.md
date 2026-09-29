# Gate9 最小执行方式—资格适用表 0.1

> 7.91纠正：下文以N1接线缺失判Gate9 BLOCKED的依据撤回，接线属于实验准备。
> 当前唯一平台适用缺口与精简Gate计划见[Gate9入口](gate9_platform_assessment_v0_1.md)顶部；
> 本表候选保留，不自动启动接线或目标机采集。

2026-09-29；基线d7eef44；本地源码/合同审查，不是实验。Gate8已收尾，不再核验官方网页。
Gate9整体BLOCKED，具体缺口为N1执行/观测接线尚未实现和资格未验证；不是平台不可用。

## 研究依据与最小候选

研究设计v7.1 §3.3及方法语义：N1检验局部同步时长能否代表request增量；G1检验自然workload的activity与exposure关系。
实验协议v2.1（Pre-Pilot）§4.1–4.5明确V0、Vmarker必做，V16先做，V8/V24仅在有稳定信息后考虑；
§5.1改变输入/输出/batch。原文7B/双平台/大矩阵由用户路线A缩减决定覆盖：本轮沿用已有Qwen2.5-1.5B、
单RTX4090、eager/SDPA、既有精度与模型内容身份，不回退扩大矩阵。以下是候选，不是Formal配置冻结。

| 执行方式 | 最小改变与研究问题 | 已有资格与真实差异 |
|---|---|---|
| G1/V0自然基线 | 先复用32输入/2输出、batch1、natural_token_ready；保持原host-readable边界 | 36ed952真实配对、1733ff3分析、限定NULL-FIFO-D2H资格直接支持当前工程执行；不是信息增益结论 |
| G1单轴候选 | 同输入前缀生成规则，仅输入32→64，输出2/batch1不变；比较prefill工作增加与暴露变化，不声称decode已充分代表 | 32/64是本轮最小候选，不是原文规定点。长度变化本身不改completion定义；实际API/stream/依赖集合仍须检查。可行性/重复数归Gate10/11，不为此提前重跑Q0 |
| N1 Vmarker | decode单位置，与干预完全相同分支/标记但不sync，控制包装开销 | 既有NVTX身份构造可复用；实际插入位置、计数、输出一致性和作用域尚未接通 |
| N1 V16 | 每次decode第16层后只做current-stream sync；对比V0/Vmarker，检验等待迁移或真实E2E增加 | 协议的首候选；必须先核对当前模型确有该层、层编号与实际current stream，不能把device sync替代stream sync。新同步进入request，改变必要集合与per-sync provenance，不能继承A-only资格即宣称B有效 |

Vnatural是可选冗余同步控制，不作为先决条件；V8/V24、其他长度/输出/batch扫描后移。
不增加第二平台、compile/graph、G2。warmup1/repeat1只可用于未来Engineering接线检查，不是Pilot/正式重复数。
V16若不适用当前模型，停止该候选并报告具体层位差异，不能静默换层。

## 已完成本地对应审查

- `exposedpath/runner.py:881–885`明确拒绝非G1_NATURAL；不是已可执行的N1 runner。
- `exposedpath/nvtx.py:73`只构造intervention身份；`validation.py:224`仅校验模式互斥与字段。
  `docs/pilot_runner_contract.md`也明确EP-G7-08不执行N1。身份测试不能证明干预接线。
- `exposedpath_v141/gate8_engineering_scope.py`已有cudaStreamSynchronize映射检查及双默认流计算，
  不需要再造同步分析器；但文件明确A交集不认证物理S标记/callsite或B，不能把此分支当新N1的B资格。
- [限定受控资格](gate8_bounded_qualification_review_v0_1.md)已补D1/身份/drain/默认流条件等价/六窗A与独立拒绝反例。
  [Gate6](gate6_closeout_v0_1.md)保留原物理S/B语义与oracle证据；它不自动证明新request projection下干预stream-sync的S/B。
- [non-submit审查](gate8_non_submit_api_review_v0_1.md)覆盖实际API分类遗漏；[配对收尾](gate8_conditional_closeout_v0_1.md)覆盖模型身份/边界/drain/同步集合/三窗A。
  [warning裁决](gate8_warning_evidence_review_v0_1.md)依用户提供答复已关闭工程阻塞，不再调查。旧报告/UNKNOWN不变。
- 后续文档提交不改变上述执行/分析字节。没有修改runner、没有运行模型或重复测试。

## 真正缺口与最小验证，不混入Pilot

1. **先本地N1接线**：固定variant/callsite/层号与decode-only插入；Vmarker和V16相同包装，分别0次/每decode1次同步。
   用CPU替身通过真实入口证明计数、G1无插入、模式互斥、异常保留；验证加载配置层数与声明匹配。
   同一输入输出token必须一致，不能只检查token数量。不得只删掉当前拒绝分支。
2. **只补新stream-sync命题**：独立手算两个顺序提交和一次中间stream-sync，核对其W(s)、terminal、A和单sync B；
   另一流无依赖、缺correlation/错stream/错ownership/缺completion必须保留拒绝。复用Gate6已有同类oracle，
   只桥接新producer→projection→S/A/B，既有负例直接引用，不完整重跑Q0。不以A守恒代替B正确性。
3. **然后才判断目标机资格增量**：若本地接线完成且现有真实受控记录没有该新callsite的stream-sync证据，
   最小受控kernel→中间current-stream sync→D2H，固定操作与独立oracle，单次Engineering采集即可回答工具映射问题；
   不直接以完整模型N1实验替代资格。缺映射/非唯一流/未知影响/输出不一致即停止，不自动重试。
   此时才提供固定执行commit、整段脚本和单ZIP（manifest、producer/receipt、Raw、日志、oracle结果、清单）。

当前N1可执行入口不存在，因此**本轮不提供不可运行的服务器脚本或部署包**。服务器重复现有G1不能消除此缺口。
新server步骤的必要性在接线后按已有真实stream-sync证据决定，不预先要求重采。
当前用户无需操作服务器；下一项是主窗口本地最小N1接线与上述独立预期。

## Gate边界

EP-G9-01平台身份和EP-G9-03当前eager点可复用完成；EP-G9-02自然基线工程范围有依据，N1新增范围未合格；
EP-G9-04本次结论BLOCKED，限定到上述具体差异。Gate9资格不负责挑选统计repeat、解释度阈值、
overhead政策或Formal样本：这些仍归Pilot和Protocol Freeze。D/Signature不启用，现Engineering产物不升级。
