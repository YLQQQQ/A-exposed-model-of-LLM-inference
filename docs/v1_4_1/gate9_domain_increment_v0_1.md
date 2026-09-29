# Gate9 分域增量实现与单次桥接审查 0.1

依据：[G9-DOMAIN-QUALIFICATION/0.1.0](gate9_domain_qualification_contract_v0_1.md)。
本文件是 Engineering 实现/交付说明，不是新测量合同、Pilot或资格通过记录。
Gate8 PASS不变；Gate9须审查增量实物，当前BLOCKED。旧probe关闭，旧Raw和判定不改。

## 本地实现与证据范围

- `exposedpath-domain-qualification/0.1.0`封套要求执行前manifest显式profile；绑定receipt/源文件hash，独立输出、原子发布，读取时重新导出并比较。缺文件/未知版本/改写/跨身份不接受。
- N1 `exposedpath-stream-bridge/0.1.0`记录实际current handle、线程、device、持有生命周期、调用前后观察；原NVTX→API→correlation→activity/sync→context/trace stream逐项唯一连接。native handle与trace编号不按相等推断；实际flag=nonblocking且非null stream。生命周期冲突、未绑定submit/sync、其他流/线程、未知诊断拒绝。
- N1复用closed-prior和物理S/A/B，不截短物理W。当前只接通连续持有专用流、已映射measured前缀；旧schema不支持的warmup来源拒绝，不改标measured。未来模型采用合同首选“warmup/drain之后创建专用流”；复用含warmup历史的流不在本次桥接支持内。
- G1复用原Engineering边界/身份/drain/支持域检查，新增逐sync必要成员和依赖边的双模式一致性检查，再计算A。原physical S/B保留，不发布自然默认流B。相同A数值但成员不同必须拒绝。
- 逐request质量检查与资格结论分开。长度变体仍逐窗检查；不因长度变化重跑完整Q0。UNKNOWN/NOT_ASSESSED、非Formal、D/Signature禁止保持。

独立手算测试实现合同§4的三窗与长度变体、错成员同A、缺correlation/身份/边界/drain/未知诊断反例；局部5ns分类证据故障注入保留unattributed而不填Host。该故障注入不提供“任意未知API是局部缺口”的许可。
N1文件链检验第二request物理W保留已完成前缀及独立hidden/exposed/tail预期。
实际新producer由CPU替身生成Raw/sidecar后，经过Canonical、投影、S/A/B和独立Raw oracle；oracle不调用被测S/A函数。合成export/观测记录不是真实Nsight或零丢失证明。

## 单次目标桥接：仅待协调窗口审查

不加载模型、不实现N1矩阵。沿用目标机已记录的PyTorch 2.6.0+cu124、CUDA12.4、Windows4090、mask3、显式direct Python/site。
先核对固定commit、binary和源码、CPU定向回归；失败停止。显式授权后才编译并运行一次CUDA/Nsight，禁止重试/恢复/覆盖。

固定操作：初始化/分配在窗外，新建PyTorch非默认nonblocking流并持有；微程序warmup_count=0。
两个measured request，tokens分别[0,1]、[11,12]，各自成功device drain在request start之前。
每个request：submit K1 → current_stream().synchronize内部sync → D2H1 → current-stream sync → host读取token1 → first-ready；
submit K2 → D2H2 → current-stream sync → host读取token2 → last-ready。清理在last-ready之后。
所有native submit/copy用实际current handle，sync走实际PyTorch调用，不用手写cuda sync替代框架路径。

独立预期：每request四活动K1/M1/K2/M2，三个sync；按固定提交顺序，六个W的成员数为1、2、4、5、6、8，
terminal分别对应最新必要活动；第二request包含第一request已完成物理前缀，但不扩大第二request窗口。
三窗口由共同completion点确定；A由原始区间独立union/裁剪复算，B只逐sync比较。等待时长不用于判断默认流模式。

结果及决策：

- **MATCH_REVIEW_REQUIRED**：两个token序列、实际调用/流/context/身份/返回、边界/drain、完整必要集/terminal、六窗口A和六个B均与独立预期一致，文件身份/诊断门无冲突。支持关闭限定显式流调用桥接缺口，仍须人工审查后判Gate9；不自动给Formal或N1信息增益结论。
- **FAILED/BLOCKED**：token/身份/调用/ownership/算术矛盾、进程失败或超时；保存全部错误，立即停止，不重试。
- **证据不可判别**：必要字段/记录缺失或新warning作用域未定；机器保守BLOCKED，审查注明INCONCLUSIVE，不能据此判平台语义反例或修改门槛。先定位唯一缺口，不默认重采。

这个单次构造能直接回答显式handle是否对应观测中的非默认nonblocking流，以及实际PyTorch sync能否恢复预定物理集合；
它不判断全局LEGACY/PTDS模式，不证明框架任意其他流有ownership，不把微程序结果直接套到未检查的模型request。

服务器交付只含固定增量bundle、固定配置和一次脚本。输出到新`$ServerRoot/evidence/gate9/<run>`，
编译、环境/源码/库hash、CPU日志、plan/manifest、目标启动/退出/runtime、producer、REP/SQLite/export、独立oracle、分析结果及失败报告统一一个ZIP；
清单先快照再生成，避免自身入清单。服务器机器路径只在忽略的本地交付配置中。
本轮不执行目标步骤，不再重采Qwen。G1真实既有边界/drain/后缀事实可复用，新的文件链本地增量不追认旧产物。
