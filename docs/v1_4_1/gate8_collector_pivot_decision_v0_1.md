# Route A 技术转向：一页 Go／No-Go 草案

**推荐：停止当前Nsight科学链推进；仅将“单一自有collector受控可行性原型”列为下一项可授权工作。**
原型研究为条件性GO，不代表目标Windows可运行已被证明；自然Qwen正式接链现在NO-GO。
本提案未授权实现/采集，不改变合同。Gate7 PASS，新Q0/Gate8 NOT_RUN。

## 首选：替换Nsight，而非并挂

第一方API提供足够具体的原型起点：Runtime/Driver callback的`functionParams`、callback ID、
correlation/context可与activity关联；resource callback提供context/stream创建销毁；
NVTX injection/callback及marker activity提供同次request标记；`cuptiGetTimestamp`提供
activity同域时间；dropped计数与flush提供质量记录入口。
依据：[CallbackData](https://docs.nvidia.com/cupti/12.9/api/structCUpti__CallbackData.html)、
[Resource API](https://docs.nvidia.com/cupti/12.9/api/group__CUPTI__CALLBACK__API.html)、
[NVTX及buffer生命周期](https://docs.nvidia.com/cupti/12.9/main/main.html)、
[Activity API](https://docs.nvidia.com/cupti/12.9/api/group__CUPTI__ACTIVITY__API.html)。

**尚不能承诺：** 当前DLL/driver/SDK ABI兼容；全部implicit PTDS生命周期；可区分TID复用的
thread epoch；NVTX3在目标Torch的实际初始化；所有必要API参数及动态入口mode对应关系。
不能仅因Nsight内置cupti64_129.dll就将其作为可独立链接且兼容现driver的SDK。
mode仍须由实际入口/参数推导，不读取一个虚构的全进程mode变量。
dropped数只覆盖文档所述activity丢弃，不能认证NVTX/callback/自有队列完整；
collector须有自己的溢出、序列及未完成记录状态，强制flush的残缺记录不能算合格。

**最小原型及停止线：** 单进程、单GPU、两个可区分寿命的Host线程，独立写定LEGACY/PTDS
敏感构造及一次资源重建反例；同次采集API参数→correlation→activity、epoch、三个completion
point与NVTX，完整/缺失/溢出故障注入有明确拒绝。成功必须恢复独立W/terminal及逐段A，
无不可解释的身份复用；任一关键路径不可观测、ABI不兼容或资格依赖猜测即停止，不先上Qwen。
原型需native DLL、版本化Raw writer和最小reader，是新collector工程，不是几行launcher修复。
仅在它通过后才决定是否承担完整Canonical adapter、观测合同amendment及受影响新Q0资格。
旧W/A/B公式、oracle预期可复用；旧Nsight observation资格不可继承。

保留自然eager的前提是不插同步/换流/改API结果；callback会扰动Host时序，必须用相同受控
输入比较无collector/有collector，记录耗时与调度差异，禁用重入与callback内磁盘阻塞。
不能承诺零扰动，异常或显著改变执行形态时停止，不靠校正系数掩盖。成功后才可能支撑
自然Qwen A及有限信息增益，不提前宣称该claim成立。

## 备选：受控显式流的真实模型合同

明确创建、持有及记录nondefault stream，把受支持调用限制在可证明的执行域，可能降低
模式歧义；但仅包一层Python stream context不能保证加载worker/库内调用都服从它。
需要证明调用闭包、初始化历史和真实completion，仍有观测/新Q0成本。改变流会改变
隐式依赖或并发行为，必须标成“受控执行合同下的真实模型”，不能称自然eager。
它可支持该受限域的A正确性及相对常规指标的有限信息增益，不能外推自然Qwen行为；
只在用户接受这一claim收缩后考虑，遇到域外调用不能静默换流或忽略。

## 唯一下一步

用户若愿意继续保留自然模型目标，**只授权一个受控collector可行性原型工作包**，
按上述明确数据与反例检验能否获得缺失证据；不同时授权Qwen采集或正式collector建设。
本轮不实施，亦无服务器操作步骤。若不承担这一新增工程成本，当前平台自然模型目标保持
NO-GO，转为受控执行合同需明确收缩claim；不再继续Nsight小修/盲重跑/空准入审批。
