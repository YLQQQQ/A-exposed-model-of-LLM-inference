# Mode／epoch 有界可行性裁决 v0.1

**结论：当前未闭合低风险证据路径，暂停请求准入批准。**
不是工具绝不支持，也不是要求全capture认证。范围仅为目标必要依赖的调用语义和资源连续性。
[admission草案](gate8_target_scope_admission_draft_v0_1.md)继续未生效；不以批准文字代替技术证据。

## 已有材料的确定边界

本轮以只读 immutable SQLite 查询固定旧Gate7输入的schema和stream枚举：
Runtime有start/end/globalTid/correlationId/nameId/returnValue/callchainId，**没有stream参数或
编译单元字段**；Driver表不存在。context/stream inventory有ID、flag，但无起止epoch。
stream7为`CUPTI_ACTIVITY_STREAM_CREATE_FLAG_NULL`，不是完全没有流类型证据；
这条类型记录不能单独推出所有相关API的参数选择、混合模式不存在或context/thread未复用。
不得把CUPTI枚举中的`DEFAULT=1`当CUDA原生`cudaStreamDefault=0`直接互换。
固定输入身份及六sync引用见[实际差距表](gate8_target_sync_gap_audit_v0_1.md)。

CUDA默认语义受编译单元及显式handle影响，PTDS依赖thread/context：
[CUDA12.4.1](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/stream-sync-behavior.html)。
另一个看似可用的查询`cuptiGetStreamIdEx`需要调用者提供`perThreadStream`，它不是未知mode探测器：
[CUPTI接口说明](https://docs.nvidia.com/cupti/api/group__CUPTI__ACTIVITY__API.html)。
此处仅核验API含义，不声称滚动CUPTI版本等于目标安装实现，不新增collector调用。

## 只比较两条低风险候选

| 路径 | 真正需要的原始字段 | 当前可行性／失败条件 | 是否改变自然eager／新服务器运行 |
|---|---|---|---|
| 1. 现有Nsight导出事实绑定 | 每个必要调用可辨入口及实际stream种类→correlation/context/stream；context/thread/stream生命周期记录或同等有界连续性证据；marker只是辅助owner | API名及NULL类型可复用，但现有表缺参数/epoch，`_ptsz`在文档列表不代表目标调用；无证据不能补齐。当前不能实现完整adapter | 只读解析不改变执行，也不需运行服务器；重新按相同profile采集没有已知理由会补出缺字段，因此不建议盲采 |
| 2. 固定目标二进制的可审计来源证明＋已有trace绑定 | 对实际相关调用路径的binary/build/TU身份、预处理选择/显式handle、动态解析选择及调用绑定；对必要历史区间的context/thread资源持有和退出证据 | 目标header/PE已有但缺TU构建与实际路径绑定；Python current/default handle前后快照不是期间连续性。没有现成证据链，当前路线关闭，不再索取PDB/反汇编 | 取得已有构建证明本身不改eager，但当前没有该产物；重编Torch、native hook或补生命周期采集不属于这条只读路径，也不是本轮授权 |

两条都**未证明可执行**，不把第二条包装成“再收一个包就能成功”。
CPU采样栈即使有module/RVA，也未必有参数、mode与epoch；不默认恢复source profile。
修改collector／CUPTI callback／native interception可能提供不同证据，但属于新观测工程和风险，
本轮不列为低风险现成方案、不实现、不建议直接执行。

## 停止点与保守支持域

- 停止继续本地同类检索和抽象准入审批。当前既有材料不足以证明自然模型目标scope，
  不得声称已接通或只差一次模型采集。
- 可保留的研究支持域是已具备明确资源/提交/owner证明的受控构造及现有确定性文件链；
  它们支持正确性，不支持自然Qwen request低unattributed或信息增益claim。
- 已批准Route A真实模型目标仍未完成；本裁决不自动将研究降为仅受控案例。
  若继续自然模型，下一步必须是一项**具体且独立授权的证据获取改变**，或对现admission
  必要性作明确语义裁决；目前没有证据支持任选mode、A-only旁路或换流后称为自然行为。
- 先向用户报告这个技术事实，不再请求批准尚无adapter的抽象规则。没有服务器命令。

Gate7历史PASS；新Q0/Gate8 NOT_RUN。只读SQL/文档，无代码、合同、采集、部署变更。

## 最后两条替代路线裁决（7.52，未生效提案）

**结论：两条均未达到可执行方案条件；当前平台上的自然Qwen科学链仍阻塞。**
不再请求批准空adapter，也不把第二条当现合同已有许可。

### ① 新增最小观测adapter

CUPTI callback在机制上可读API参数，resource callback可通知context/stream创建销毁。
但这不自动覆盖implicit PTDS、Host thread epoch及所有mode选择路径；参数须在callback有效期内复制。
且官方12.9 Callback API的`cuptiSubscribe`明确单subscriber限制并列出与Nsight工具的冲突：
[版本化官方说明](https://docs.nvidia.com/cupti/12.9/api/group__CUPTI__CALLBACK__API.html)。
目标安装有cupti64_129.dll不等于可以与Nsight共用subscriber；CUDA12.4.1归档接口页本轮
不可访问，不能凭新版文档保证该Windows目标组合。未证明完整字段及共运行兼容。

- 自然eager：只观察理论上可不改调用语义，但callback扰动/线程时序和错误路径必须验证；
  不得承诺无扰动。替换Nsight或重编框架不是“最小sidecar”。
- 必须先证明：逐调用callback ID/参数与activity correlation、线程/context/stream epoch、
  implicit默认流对应关系、安装ABI和collector共存；任何一项缺失即停止，不能另次run补同次身份。
- 若有上述正面依据后，最小受控验证才是两线程模式敏感构造＋资源复用反例，独立W/A预期；
  对照无adapter与有adapter的同输入执行，记录overhead和时序变化，不预设容忍百分比。
- 当前判定：**目标“Nsight旁挂最小adapter”技术可行性未成立，不进入实现/实验**。
  成本至少涉及native观测、ABI、扰动与新增资格，不能伪装成普通字段接线。

### ② 所有兼容世界的A等价准入（B保持invalid）

这是新的研究准入/发布语义，不是删掉现有mode检查。原则上不改变自然eager，
但只能在目标Raw与必要历史具有可证明覆盖边界、clock/completion可信时建立候选世界集合。
所有兼容的mode、epoch、历史闭包和terminal可能性必须被穷尽或由独立证明包围；
只跑LEGACY/PTDS两个配置或只比较最终总量，不是证明。

- 所缺正面证据：候选集合完备性、遗漏/未知前缀的影响界限、各世界每个时间区间的A类别
  相同（不是仅五类总和相同）、terminal不确定性不会改变归属的独立证明。
  缺真实completion、无法界定Raw缺口、terminal可能导致不同分类，一律拒绝。
- 独立正例仅可人为构造：已知全部候选工作在sync之前完成、边界/历史完备，所有合法
  W都不产生sync内wait，可验证A一致而B的hidden不同。加入一个兼容但未排除的跨入sync
  必要活动，若可改变A，则必须拒绝。该正例不能证明现有模型满足前提。
- 最小成本：先独立证明和手算反例、版本化A-only有效性/输出限制，再确定性实现；
  真实证据仍需另行资格。旧analyzer重复运行不能作为集合完备性oracle。
- claim：若将来证明成立，最多保留可辨识A accounting；不能保留完整B机制解释、
  Exposure Signature或未经检验的信息增益claim。D发布须另定，不能沿用全资格标记。
- 当前判定：**历史闭包/epoch覆盖仍无界，现证据不能建立该候选集合，故不能放行自然Qwen**。
  不建议为解除一个未解决的技术阻塞先投入这条更复杂的新方法。

### 推荐停止点

本轮不推荐用户在两条未成熟路线间批准实验；不启动profile、native hook或collector替换。
研究已取得的正确性和工程结果保留，但Route A的自然模型A归属／有限信息增益尚无完成证据。
需要新增、具体且可核验的观测能力依据，或用户明确改变研究支持域后才能推进；
不是再写一份amendment即可解决。至此关闭这轮替代调查，不追加底层选择或服务器命令。
