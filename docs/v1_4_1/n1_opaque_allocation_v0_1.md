# N1 opaque allocation预算 amendment与V0收口 0.1

2026-09-30；用户已批准；Engineering / Pre-Pilot。研究设计v7.1、实验协议v2.1。
本页是[7.107裁决稿](n1_raw_provenance_allocation_v0_1.md)批准后的现行窄域规则。
这是观察既有V0之后明确批准的测量解释例外，不追认旧BLOCKED报告，不适用于Formal。

7.110现行收尾：[N1模型三组限定Engineering可行性PASS](n1_model_feasibility_closeout_v0_1.md)。
本页amendment保持；§3为已复用V0审查，§4为当时续跑计划历史，不是新服务器操作指令。

## 1. 版本与准入

`N1_OPAQUE_ALLOCATION_BUDGET/0.1.0`；[API registry0.2](contracts/a_api_registry_v0_2.json)、
[A/B0.6](contracts/ab_schema_v0_6.json)、N1 adapter0.3.0；S仍0.4，Raw来源仍0.1。
基础MC0.2正文、旧registry0.1、旧schema及N10.1.1/0.2.0读取和判定保持。
未知版本、来源篡改、无逐调用准入证明不能继承新支持；Derived不消费新版本。

首版只支持精确`cudaMalloc`及合法`_v[1-9][0-9]*`后缀。
满足以下条件的实际调用归入CUDA API non-submit的`OPAQUE_RESOURCE_MANAGEMENT`子类：

- 成功返回，完整同clock Host区间，唯一process-instance/thread/request/phase归属；
  API及physical drain映射真实唯一，drain成功且在request外；实际专用非null NON_BLOCKING流已证明。
- 没有嵌套或相交API，没有allocation关联activity/sync冲突；不能用“没有activity”证明没有内部等待。
- 已观测必要submit/sync的correlation、实际scope、完整W、terminal和原validity均通过；
  任何可见跨流/event依赖、顺序不明、未消费sync、下游缺证据或影响范围不明均拒绝。
- 原结构token-ready/干预身份继续必需。内部同步只按已批准RAW_PHYSICAL来源规则恢复；
  不伪造origin/callsite/ordinal，不以allocation API区间代替下游依赖证明。

事实是Raw中记录的成功、区间、映射、实际stream与闭包；
“无未记录incoming依赖”仍是既有支持域假设，不宣称排除所有隐形工作。
判定proof保留原table/rowid/record/correlation、clock/global PID/TID、scope、request/repeat、
SQLite/pass SHA256、drain与下游sync引用，消费时按Raw重建后精确比较。

## 2. 解释与独立预期

non-submit只表示**不提交设备工作**，不表示非阻塞。
opaque预算是不拆内部等待的资源管理API占据时间；不能作为已恢复GPU等待或硬件根因。
五类A及API=submit+non-submit不变，按半开窗口裁剪、互斥union和原同步优先级；
opaque仅为non-submit内的标注预算，不能再加到五类总和。无新增barrier/W/B，无裁剪先行已完成活动。
`A_device_wait`仅覆盖受支持同步恢复的等待，不声称涵盖allocation内部所有等待。
B hidden仅相对于该次同步，不能解释为整个request未暴露。

独立手算正例request[0,100)：submit[10,20)、malloc[30,40)、sync[60,80)，
完整必要kernel[60,70)。A=(Host60,API20,wait10,residual10,unknown0)，opaque10已包含API。
prefill[0,35)：(20,15,0,0,0)，opaque5；decode[35,100)：(40,5,10,10,0)，opaque5。
expected由上述区间直接确定，不调用被测S/A生成。缺边界、失败、交叠/嵌套、
重复correlation、关联activity冲突、其他流/event、下游INVALID、drain/clock/owner冲突及proof篡改拒绝。
仅有名称注册、真正未知API或旧版本不能获得准入；不能普遍转Host/API。

## 3. 同一V0的新版本离线审查

执行提交`c21d8358e42e764c37cf9b315d87235989a817e1`不变；只消费封存副本，
新派生目录`continuation_opaque_v0_1`，完整准入55.555秒、文件重载全链复读37.399秒。
原ZIP/REP/SQLite/collection报告哈希与[原索引](n1_v0_review_v0_1.md)一致。
新`domain.json`及`review.json`明确关联来源和新分析合同；原attempt仍BLOCKED。

| 窗口 | 总ns | Host | CUDA API | Device wait | Sync residual | Unattributed |
|---|---:|---:|---:|---:|---:|---:|
| Request | 212715004 | 119176616 | 92285548 | 223646 | 1029194 | 0 |
| Prefill | 128172644 | 67308362 | 59637741 | 223646 | 1002895 | 0 |
| Decode | 84542360 | 51868254 | 32647807 | 0 | 26299 | 0 |

变化仅三次成功Prefill allocation：Runtime17566/17579/17646、correlation61737/61867/62931，
时长773224/176954/686985ns，总1637163ns，从原未知转明确opaque API。
每窗总时长/Host/wait/residual不变，各分量Request=Prefill+Decode、互斥守恒通过。
不是以unknown清零为准入条件；先完成来源、闭包和分类检查，再检查预算。
内部348与token349/350的完整W仍8/1906/3498、terminal仍Memcpy344/345/346，三条B_VALID；
没有allocation B，没有丢弃已完成前缀。实际32/2、tokens[[463],[2529]]及boundary/drain沿原实物核对。

**V0新合同下的限定Engineering支持域审查通过；不是整个N1三组可行性或科学效果PASS。**
allocation大小未观测保持null；`UNKNOWN`、`NOT_ASSESSED`、D/Signature禁用及历史资格边界保持。

## 4. 续跑及证据边界（历史计划，7.110已完成审查）

仅准备尚未运行的Vmarker/V16（32/2、batch1、fp16/eager/SDPA、warmup1/repeat1）；
各组专用流和第16层位置不变。producer/runner/输入/插桩/allocator/流政策与c21执行版本未改变，
新增代码只在采集外做版本消费/续跑调度，因此不因consumer提交不同重复V0。
7.109已纠正交付字节混淆：旧V0实际执行字节由原preflight证据绑定，old/new Git源码兼容另证；运行时不归一化。已改的domain模块只在窗外用于声明及离线分析，
其声明函数/常量保持一致。服务器校验旧V0来源hash、已审查新review及固定producer字节，
新组profile前比对公共manifest（仅允许已证明兼容的execution commit不同），再核对实际tokens。

每组保留实际allocation记录/预算，不能预设分配相同或将全部E2E差异归因干预。
Vmarker/V16仍须独立实际ownership、内部sync、干预次数和A/B准入；普通成功退出不等于PASS。
任何失败/超时/冲突立即停止后续组，不恢复、不重试、不杀无关进程；新输出、单ZIP回传。
仅交协调窗口审查，当前未操作服务器/模型/GPU/Nsight。Gate7～9及Gate10限定G1 PASS保持，Pilot不启动。
