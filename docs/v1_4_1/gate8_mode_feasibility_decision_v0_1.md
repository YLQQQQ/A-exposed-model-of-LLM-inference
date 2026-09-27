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
