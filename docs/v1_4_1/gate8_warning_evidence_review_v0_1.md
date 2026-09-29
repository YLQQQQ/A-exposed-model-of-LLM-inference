# Gate8 warning 新证据裁决 0.1

2026-09-29；裁决版本 `G8-WARNING-EVIDENCE/0.1`。
**限定 Engineering Gate8 PASS（G8-ENGINEERING-EXIT/0.1范围）；本包四warning作用域工程阻塞关闭。**
依据由纯未证假设改为“用户回传的官方解释 + 已封存目标实物及既有审计”。
不声称已直接核验官方身份，不授完整新版Q0、模型科学有效性、Formal资格或信息增益。

## 来源与准确引文

来源状态：`USER_RELAYED_OFFICIAL_RESPONSE / WEB_NOT_VERIFIED`。
接收日期2026-09-29（不是官方发布日期）。用户指向
[NVIDIA主题384556](https://forums.developer.nvidia.com/t/nsight-systems-2026-2-1-windows-scope-of-cuda-nvtx-warnings-associated-with-another-process/384556)。
作者账号、NVIDIA身份/徽标、发布日期、楼层编号及回复永久链接：**未直接核实**；仅有主题链接，
不猜测`/2`或将接收日期代替发布时间。上下文是用户报告的Windows/Nsight2026.2.1四消息询证，
未直接读到完整线程，不能声称回复逐字确认了特定build或排除了未展示的附加条件。
公开网页与JSON读取工具无法访问；PowerShell公开JSON读取受限速，按等待提示仅重试一次仍受限，
就此停止。没有登录、追加询证、发送附件或操作服务器。

以下逐字保存用户提供的答复（不是本轮网页抓取）：

> Nsys runs at the process tree level, so if the process you launched then launches another process, we will follow the children as well.
> Those warnings indicate that there was at least one process that did not have any NVTX events or CUDA events generated. There are usually two circumstances where that can happen, either the process does not contain CUDA or NVTX or the process terminated so quickly that there was no time to read them.
> The fact that you have NVTX and CUDA data in your results is sufficient to show that the target process was collected successfully and correctly. And in fact all NVTX and CUDA events that could be read in the process tree were read.

## 与本包实物对照及裁决

本轮只复用[7.86封存审计](gate8_conditional_closeout_v0_1.md)及
[1733ff3分类修正/复算](gate8_non_submit_api_review_v0_1.md)，不重算、不重扫hash。

| 待决命题 | 回传答复及既有事实 | 裁决边界 |
|---|---|---|
| 为何会有另一PID的CUDA/NVTX warning | Nsys采集process tree；无相应事件或退出太快可能产生该类消息。实际row3/4/6/7关联OTHER_PROCESS PID64488 | 无需知道该PID程序用途才能解释消息；不能仅凭解释断言其确切身份/退出原因 |
| 四种消息是否自动否定目标采集 | 原消息为Not all NVTX events might have been collected；No NVTX events collected；CUDA profiling might have not been started correctly；No CUDA events collected（完整文本见原假设合同）。答复明确以目标NVTX/CUDA数据存在支持目标采集成功 | 答复内容覆盖该询证的消息组，不把每条孤立字面都当全局失败；适用性依赖用户提供的上下文，尚未网页核实 |
| 是否只有无事件关联PID而没有目标证据 | 目标PID60060，producer/入口exit0、身份链匹配；实际三NVTX共同点、drain、三内部/边界sync、CUDA提交/activity关联及必要集合已有逐行审计 | 不是只靠PID不同或analyzer自洽；答复解释与目标实物一致，无已记录具体矛盾，关闭本次工程作用域阻塞 |
| 能否推出无任何丢失 | 原文限定“could be read”；还明确短进程可能来不及读取 | 不能推出dropped=0、全capture绝对完整性、无未记录依赖或所有共享故障不可能存在 |

原配对执行36ed952b57f20651dd290fc484d7b21fc7dbbfc4；ZIP SHA256
`3c90764357547cfb28de3c16bc624664e36d58565dfa4dcb02f1063e0294940f`；
原formal SHA256 `83e24fe704b68db7a3b352b827c15413c52dda47a02fe52c591129b1a0de9eb4`。
分析1733ff3291bb3c44ad8dd6a3d90a96015d644bc1，派生 SHA256
`f0e81b5e3f1dba30f0e2c8b6a6d3f9542a361d4005b338b6905ae54696ec4928`。
身份/三窗/成功drain/后缀集合、三窗具体A及守恒、单次开销/存储/排除、lineage报告均沿用
已完成的退出检查，无其它已知工程缺口。本版是独立人工证据审查，不回写原BLOCKED或派生JSON。

## 对上一版本的改变与不变

7.88的事后工程退出政策及历史结论保留；**“只有未证假设、只能等待作用域裁决”不再是当前工程停点**。
本次有新外部解释证据，但来源等级明确是用户回传，不写“官网已核实”。原machine warning门未改，
旧运行仍BLOCKED、派生仍CONDITIONAL_A_ONLY_NOT_ACCEPTED/trusted_a=false/scope_proven=false；
这些历史字段不与新人工审查结论混成一个verdict。A依然受既定支持域与Engineering数据角色限制，
不改UNKNOWN/NOT_ASSESSED、不将unattributed=0当质量认证，不启用D/Signature。

如后续原帖附带不适用条件、消息类别不同、目标事件/身份有矛盾或出现具体相关依赖，重开对应命题，
而非一般性要求排除所有可能性。本结论不自动豁免未来目标/未知PID、额外warning或缺边界/同步。
官方来源元信息仍宜随可访问原帖/用户提供的完整回复页面补齐；不需要服务器采集，也不是继续
Gate9本地工作的前置。Gate9当前任务见[平台评估更新](gate9_platform_assessment_v0_1.md)。
