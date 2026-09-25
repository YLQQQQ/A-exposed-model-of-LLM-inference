# Gate8 Coverage Reporting Amendment v0.1

**ID `G8-COVERAGE/0.1.0`；2026-09-25，D2方向已批准；本地第一批实现见[实现状态](gate8_local_implementation_v0_1.md)。** 增补实验协议v2.1 §3.6及Measurement Contract v0.2 §6/9–12的报告细则，不覆盖冻结正文、S/A/B公式或旧结果。仅适用于显式绑定本版本的新Engineering报告，Gate8 NOT_RUN；确定性测试不是新Q0或真实workload验收。

Schema：[coverage_reporting_schema_v0_1.json](contracts/gate8/coverage_reporting_schema_v0_1.json)，记录版本`exposedpath-sync-call-coverage/0.1.0`。独立sidecar读取版本绑定的projection、Canonical、S和A/B；不从legacy analyzer字段猜测，不让D/Signature默认把新增字段作为新指标。

## 1. Universe、支持性与去重

physical候选集合必须复用冻结registry和`build_semantic_sync_candidates()`的mapped/API-backed单点规则。UID=`source_sqlite_sha256 + ':' + sync_id`；禁止以NVTX标记、函数名、callsite或时间重合去重。同physical sync重复引用且内容完全相同只计一次；内容冲突拒绝coverage。mapped同步与API-backed副本不得并列成两条。未知API/时间/ownership使目标分母完整性不能确定时，保留观察项并标INCOMPLETE/UNKNOWN，不通过删除未知项得到高比例。

supported集合P由既有S最终`validity ∈ {VALID_NONEMPTY,VALID_EMPTY}`决定，不仅按registry支持类型；不从原因文本重建新状态。B集合V由一一匹配的`B_VALID`行决定，必须V⊆P；其他映射冲突拒绝报告。VALID_EMPTY计P不计V；terminal tie即使存在候选W也不升级supported。invalid/ambiguous/unsupported留分母和失败分布，不填零时间。

## 2. 窗口membership与四个精确比例

合法窗口W=[a,b)。正时长sync s=[x,y)只在`max(a,x)<min(b,y)`时属于U(W)。零时长x=y时，若a≤x<b则计count，duration=0；空W没有成员。x>y非法。membership基于已证明request身份及scope，不把仅时间相交的其他request同步归本request；外部/无法确认归属的候选可能影响W时须保留失效证据，不能借membership筛掉它后声称分母完整。

每个成员`d(s,W)=max(0,min(b,y)-max(a,x))`，所有端点来自同一trace clock。四个比例以**整数numerator/denominator**保存，显示百分比只在status=VALID时由比值×100得到；不得把显示舍入反写精确整数。

| 字段 | numerator | denominator |
|---|---|---|
| supported_count_coverage | P∩U的数量 | U数量 |
| supported_duration_coverage | Σ d(s,W)，s∈P∩U | Σ d(s,W)，s∈U |
| b_valid_count_coverage | V∩U数量 | P∩U数量 |
| b_valid_duration_coverage | Σ d(s,W)，s∈V∩U | Σ d(s,W)，s∈P∩U |

协议§3.6已规定B-valid分母=支持sync；本版本仅明确相同分母规则的duration报告。不同调用重叠时分别计裁剪duration，不做union，数值可大于T_window。这是**调用时长加权coverage，不是request-visible exposure**；不产生B hidden/exposed/tail跨同步加总字段。A仍按原有互斥union、invalid优先及unattributed规则，绝不从此duration总数扣Host。

跨phase sync在每个相交phase各有membership；S的sync_owner_phase不改，B只保留原一行，coverage members引用它。full_request独立按UID集合重算，不相加phase count。相邻phase半开裁剪保证同一调用的时长不因边界重复，但不同调用重叠仍按调用计权。

## 3. 空、未知与输出校验

- denominator_status=COMPLETE需要身份/窗口/候选universe/时间完备且必需完整性证据确认；已证明无调用可输出observed_unique_count=0、members=[]。
- 每个比例分母>0为VALID；分母=0则NOT_APPLICABLE，整数对0/0用于保存已知空计数，**显示值null而不是0%**。零时长调用可能count比例VALID而duration NOT_APPLICABLE。
- INCOMPLETE/UNKNOWN时四个比例均UNKNOWN、numerator/denominator=null。observed_unique_count只表示已观察可去重数量；members=null表示完整membership不可确定，不用[]假装空。可另附原S失败分布，不把它命名完整coverage。
- `dropped=UNKNOWN`不能得到COMPLETE；不能把当前observation的valid直接翻译为肯定零丢失。局部S invalid但membership、时间和总universe已完整时，分母仍可COMPLETE，该invalid留在分母，P/V不计它。
- 必需S/B行缺失/重复冲突、V非P子集、比例整数与member计数不一致、hash/版本不匹配、负duration → COVERAGE_INPUT_INVALID/拒绝报告。未知证据→报告UNKNOWN并阻塞相应科学验收，非崩溃或假PASS。

JSON Schema只验证类型/版本/null政策；UID唯一、subset、算术、hash解引用、COMPLETE充分证据必须额外语义验证。不可把schema通过称为测量有效。

## 4. 资格边界

Coverage用于暴露A归属与B解释证据缺口、限制claim，不是新增研究贡献指标；不代替A整数守恒/validity，不是完整request可解释比例。数值质量阈值仍由Pilot冻结。

D2不改变W(s)/terminal/A/B，独立手算fixture足以验证报告算法的数值约定，但不等于真实universe完整性已验证。实现若改candidate集合、S validity或ownership，则超出纯报告实现，必须走D1/相关Q0影响审查。旧Gate6 PASS不撤销，新版本不能自动继承资格。完整预期见[测试规格](gate8_design_test_expectations_v0_1.md)。
