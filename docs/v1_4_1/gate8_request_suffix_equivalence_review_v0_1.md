# Request后缀默认流等价性：有界只读审查 0.1

基线0295392；仅研究决策备忘录，不修改amendment、adapter或旧证据。

**结论：严格受证条件下，后缀W_Q及A交集可条件性等价；完整物理W/B不因此等价。
现有旧Qwen材料尚不能证明全部受证条件，不能开放默认流准入。当前无服务器动作。**

## 1. 本次实际读取的事实

输入为Gate7唯一PASS attempt `smoke_20260924T084657Z` 的只读SQLite，执行commit
8d64f75；复用已封存SHA256 `005cf068bff99c36585a91343d8841d12bb2cad41a94bdc9bc1478045691877c`。
本次用`mode=ro&immutable=1`查询白名单表，不重算整个档案、不读私有META、不写派生数据。
以下候选区间从成功drain Runtime返回到旧最后Token-ready Runtime返回，**不是新版D1窗口**：

| 事实 | request候选1 | request候选2 |
|---|---|---|
| 区间ns | [21865003036,22021160173) | [22975507384,23155653623) |
| drain Runtime rowid | 23796，return0 | 27103，return0 |
| stream sync Runtime rowid | 23806、25508、27102 | 27113、28815、30409 |
| kernel / memcpy / memset | 3492 / 3 / 3 | 3492 / 3 / 3 |
| 活动→Runtime correlation缺失或重复 | 0（仅已记录集合） | 0（仅已记录集合） |

四Token sync是每列后两个；额外内部sync **23806/27113不能丢掉**。各候选区间都有
cudaLaunchKernel3295、cuLaunchKernel197、cuKernelGetFunction6169、MemcpyAsync3、
MemsetAsync3、StreamIsCapturing2、StreamSynchronize3，全部同globalTid
282326252700592；已记录活动均device0/context1/stream7/同PID。无已记录跨drain活动，
区间内未发现Event/Create/Destroy/Reset/Ctx命名调用。它们是有限观测，不是不存在证明。

inventory有一个context（PID50740、context1、nullStreamId7），另有stream6/8/9/10/11/12，
所以不能写“整个进程只有一个stream”。stream7的CUPTI枚举flag3=**NULL**，不是CUDA原生
flags；不能推出每个调用的TU选择/显式handle。CUDA_EVENT及独立DRIVER表缺失，但
Runtime表确有`cuLaunchKernel`等Driver API名，不能以表缺失宣称无Driver调用。
现表无stream参数/TU/epoch；无新版D1、drain/stage/load-task来源证书。
drop/过滤影响范围仍未由这些事实证明。旧输入只用于兼容性审查，不追认Gate8。

## 2. 条件性结论与独立反例

依据[CUDA 12.4.1默认流规则](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/stream-sync-behavior.html)：
legacy与同context其它blocking streams同步；PTDS按thread/context独立，且与显式legacy
并存时仍有交互。模式按编译单元/显式handle选择，不是进程单一开关。

**充分条件（待证，不是把观测缺失改为肯定）：**有效drain证书封闭必要历史；从drain至
最后completion，所有目标及incoming依赖提交均受界定；一个实际提交TID、一个有效NULL
FIFO stream/context，无相关其它stream/event、混合显式默认handle、迟发提交或资源复用；
每个必要API的scope/correlation与时钟、同步成功、唯一terminal均有证据。

在这些条件下，两种纯mode在Q上的差异边无适用对象；相同FIFO提交前缀给出相同W_Q。
非空Q的唯一terminal若晚于drain，其identity/end相同；固定同一已观察时间线与completion
窗口，A的sync交集与其它类别相同。**不声称切换模式后的实际时延、调度或开销相等。**

三项手算反例界定结论：

1. **P不等价而A等价。**另一Host线程在drain前提交并完成P=[-30,-20)，d=[-10,-5)，
   本线程Q=[10,20)，s=[15,25)。legacy的W可能含P+Q，PTDS的W只有本线程Q；
   A_wait均5，但B hidden分别15与5。因此不能写W_full/B等价。
   若Q为空，drain只给完成上界，精确历史terminal仍可能不同或未知。
2. **只要多一个相关blocking stream，就可能不等价。**同一Host先在另一blocking
   stream提交E=[0,60)，再在默认流提交K=[60,70)，s=[30,75)。同一组已观察时间戳在
   两mode下均可发生；legacy的W={E,K}，wait union=40；PTDS的W={K}，wait=10。
   terminal都为K并不能挽救错误A。E若缺记录，单看主stream看不见这个反例。
3. **迟发不是前缀。**另一线程在d后提交E，不能用d的成功返回排除它；其default或
   event依赖可能改变Q。仅setup worker曾经完成、主线程相同、记录中未出现E都不够。

因此模式名称UNKNOWN本身不等于A永远不可算，但**当前“受证条件”缺口不能用条件性
数学结论代替**。本审查不修改0.1入口的DEFAULT_STREAM_NOT_SUPPORTED/SOURCE_NOT_QUALIFIED。

## 3. 现有producer能证明什么，唯一缺口是什么

runner源码只显示顺序forward/argmax/token-host-read，不包含对所有被调用库的CUDA提交
scope保证。已回传Transformers5.17.0源码中，`core_model_loading.py:970`消费future结果，
1634–1636选择thread pool，1730起提交materialize，1791–1793以`wait=False`关闭pool。
这既不证明必然有迟发，也不能凭loader返回排除所有迟发。现LoadTaskObserver的
AT_SEAL_NO_WAIT只覆盖登记job；没有目标真实receipt，不能替代其它producer范围证明。

**唯一最小缺失证据类别：绑定固定模型/实际backend与binary身份的request后缀来源闭合证明，
并与同次drain/D1/全部必要API活动对应。**它要覆盖上述内部sync，说明为何不可能有影响Q的
其它提交/依赖；不是全capture零丢失认证，也不是重新收集所有setup TU/thread历史。

当前没有已证实可直接取得并足以完成该证明的单一现成字段/回执。已有trace可免费复用作
正面绑定；已回传loader来源仅支持前缀的一部分。再复制Qwen Python源码或再采同profile
不能独立证明native后端的全部行为，因此不把“再传一个包”列成确定有效的服务器动作。
成本下界是一次**限定实际forward/backend范围的来源证明与独立反例审查**；是否能从固定
来源建立该证明须先本地明确，不能承诺靠现observer即可闭合。此处停在证据门，不扩安装
搜索、collector、CPU sampling或换流，不新增工具/测试/采集，也不继续要求用户抽象批准。

下一步若继续，仅针对这一来源闭合命题形成可核验依据；在它具体可执行之前，服务器无需
操作。Gate7历史PASS，新Q0/Gate8 NOT_RUN；B历史与UNKNOWN保留。
