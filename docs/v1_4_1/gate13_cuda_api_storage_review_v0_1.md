# Gate13 CUDA API内部阻塞与服务器存储收口 0.1

2026-10-11；`G13-API-STORAGE-EXPLANATION/0.1`。解释审查和定向清理准备，不改变G12-ROUTEA/0.1.1、S/A/B、Formal结果或[Gate13限定PASS](gate13_closeout_v0_1.json)；Gate14 NOT_RUN。执行99f3bae、分析e19c308不由本次工具/文档提交替换。

## 复制/同步：对此前表述的更正

不是“`.cpu()`返回后才执行stream sync”。[实际producer（runner.py:82）](../../exposedpath/runner.py)执行`detach().cpu().reshape(-1).tolist()`，之后才取得host整数token、记录完成时间。[PyTorch v2.6.0 CPU/GPU复制路径](https://github.com/pytorch/pytorch/blob/v2.6.0/aten/src/ATen/native/cuda/Copy.cu#L341-L377)的阻塞分支调用`memcpy_and_sync`；目标机保存的2.6.0+cu124 `CUDAFunctions.h`明确依次调用`cudaMemcpyAsync`和`cudaStreamSynchronize`。头文件4027 bytes，SHA256 `343d0cd132554849db0825f03834912bb2d82ebd6785908662838452ad0dd84a`，与已核验安装快照及wheel RECORD一致。

因此这次stream sync是**`.cpu()`复制helper内部的同步**，不是用户在读取成功后额外调用的边界同步；它由natural token-ready范围承载，不是N1干预。源路径、同线程API顺序和范围一致支持该解释；没有native callstack，不声称实测了完整C++调用栈或driver内部每个调用。

block1/G512/P1/token0，PID66320/TID50484，context1/stream7。全部时间为同一`NSYS_TRACE_RELATIVE_NS`，相对request point `26660130438ns`，单位ms；不是Host perf-counter时钟平移值。

| 原始证据 | 起点～终点 | 时长 | 对应关系/解释 |
|---|---:|---:|---|
| argmax kernel | 88.608445～88.687869 | 0.079424 | 必要设备活动；已在本次复制API内结束 |
| `cudaMemcpyAsync_v3020` runtime37815 | 86.897104～88.771602 | **1.874498** | correlation197682，成功；当前registry为submit CUDA API预算 |
| D2H activity347，8 bytes | 88.689277～88.689821 | 0.000544 | 同correlation197682、context1/stream7；是复制活动，不是CPU函数返回 |
| `cudaStreamSynchronize_v3020` runtime37816 | 88.772503～88.808056 | 0.035553 | correlation197683，成功；复制helper内部，natural token-ready身份 |
| physical sync354 | 88.776850～88.807796 | 0.030946 | correlation197683唯一映射runtime37816；event包络与runtime API包络分别保留 |
| token-ready/Prefill共同point NVTX2 | 91.390771 | 点 | host-readable完成后发出的非同步marker，不独立证明GPU完成 |

两个runtime记录均在`CUPTI_ACTIVITY_KIND_RUNTIME`。复制区间内，同PID/TID的已观测其他API重叠数量为0；复制与sync相邻，不互相嵌套。**Raw没有`CUPTI_ACTIVITY_KIND_DRIVER`表且callchain为空**，runtime→driver嵌套关系保持NOT_COLLECTED/UNKNOWN，不凭无记录认定driver内部没有等待。原row、correlation、API返回码及Canonical字段在忽略的本地`copy_api_evidence.json`中定位到原SQLite；不提交私有trace。

### 三种量不能混同

- **已观察API总时长**：复制API为1.874498ms，包含该API调用包络内所有耗时；不能全部叫CPU计算、GPU纯提交开销或已恢复Device wait。
- **当前S/A支持的Device wait**：既有合格FIFO后缀/terminal证明这次sync必要成员已在入口前完成，因此该token-ready sync的wait为0；35.553µs保留在sync residual。G512该block Prefill另一个内部sync有15.200µs wait，不能把token-ready的零推广为整窗零。
- **尚不可分离的内部等待**：argmax和D2H在复制API期间推进，但时间重叠不能证明Host具体何时、因何被阻塞。1.874498ms中设备相关等待、驱动/资源管理、调度、profiler及其他Host工作各多少，现有证据不能分离。D2H比sync入口早82.682µs，**仅证明该活动已完成，不证明`.cpu()`已经返回**。

Host完成在复制/sync返回以及tolist/整数提取之后；point还包含完成后准备延迟。原Host/trace两钟不直接相减，已知2～4ms的point准备诊断不反写成同步前成本。

结论：**CUDA API预算不等纯CPU计算；submit/non-submit不等阻塞/非阻塞；Device wait不是全部GPU相关Host阻塞；unattributed=0不表示所有内部机制都已解释。** opaque allocation继续是资源管理API总成本，内部等待NOT_DECOMPOSED，不伪造W/B。这些解释限制不改变本批记账与机制支持范围。

若未来确需拆复制API内部等待，最小下一版应先定义确有completion/阻塞证据的API子域及可观察锚点，再以独立受控的依赖/无依赖、不同Host内存语义及嵌套反例验证；证据不能定位的部分仍opaque。必须新合同/资格和新采数据，不按API全长或重叠事后补预算；本轮不实施。

## 服务器长期空间政策与一次性范围

用户要求YLQ长期占用低于**50GB（十进制）**；临时分析可更大。用户回传盘点为73.33GiB，evidence61.298GiB、JSON60.793GiB，另有2项跳过/错误；本轮未直接取得该盘点原件，不能称已核实两项异常。仅处理30个已归档`batch/<run>/collection/analyzed/domain.json`：**41820242784 bytes=38.948136GiB**。若当前字节仍一致、删除成功，按盘点估算约34.38GiB（约36.92GB），不等完整无遗漏的新盘点或实测空闲空间。

完整归档1381808437 bytes，SHA256 `a3f2e05bbfbdda8bbba025fd016bdc60c7652cd001b1dd54f5a0aec65435e6ef`；manifest `87f60c7841c1a71225a4ccffa297503fdfc63e193d9c4f99c2b9c1c8488d42fa`，外部终态回执 `b4f5f8eef7cfbf1dec47be0285b0d39c12c3503b82e3e464b62227ea8dc46172`。此前全包CRC/覆盖/哈希验证已完成，不重复完整分析。候选清单30项、每项member/长度/hash固定；具体机器路径只保存在`.local`交付。

[一次性PowerShell5.1脚本](../../scripts/gate13_archived_domain_cleanup.ps1)默认只预检查；显式Apply及操作者确认当前分析/采集已停止后才可删除。它：

1. 读取现有盘点的两条错误/跳过记录（仅该目录的有限JSON/CSV，不重扫YLQ），记录其文件hash和候选相交关系；路径/格式/数量不能识别即停止。无关异常不追查、不清理；相关目标须当前逐文件检查成功，不能假设false就是无关。
2. 绑定归档/清单/外部回执，并逐项核对archive member真实内容；明确30条、绝对路径/允许根/闭集/reparse检查，目标缺失或变化即停止，不用新hash替换期望。
3. 所有30项在读取锁下预检查完毕后才允许第一项删除；逐项释放锁、复核字节并`Remove-Item -LiteralPath`，不用递归/通配/force。删除失败立即停，回执保留已删、未删、DELETE_PENDING和已确认删除字节，不自动重试。
4. 归档保持只读锁并保留；新receipt在源树之外。释放目标锁到删除存在非原子间隙，操作者须保证没有同时运行针对该树的工作；不声称证明全机不存在所有写者。历史writer UNKNOWN/BLOCKED、marker、原manifest不修改；不调用旧retention/pack。

清理后的展开源树不再完整，恢复依据为保留ZIP内的精确member/hash及新清理回执。**本轮只交付命令，无本地或服务器研究数据删除**。Raw、REP、SQLite、Canonical、输入/身份、历史报告、完整ZIP、最终统计及用户DOCX均保留；不清理虚拟环境或其他Gate。

今后默认“临时展开分析→审查→完整归档核验→清理已绑定的重复派生副本”。未归档且唯一的最终结果不能因为可重建就删除；只维护现有归档/清理索引，不新增长期监控或存储平台。达到本次预算后即停，不借清理扩展实验。

## 本地验证边界

只读SQLite/Canonical聚焦核对exit0，未运行analyzer/模型/CUDA/Nsight。清理工具先红测再实现；真实Windows PowerShell临时fixture验证**15项通过**（19.12s），包括全部预检查、hash/路径/归档/回执错配、缺文件、reparse、读取占用、部分删除失败与未删清单、两项盘点问题的范围关联；不等服务器执行或实际38.95GiB释放。测试临时目录权限及Windows长路径问题改用任务内短basetemp解决，没有放宽脚本门槛。无全量/Q0重跑。
