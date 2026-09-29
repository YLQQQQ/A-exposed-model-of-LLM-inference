# Gate10 128/2离线超时审查 0.1

范围：Engineering；执行76ef717，分析为本审查提交。只使用封存副本、本地CPU；没有服务器/GPU/Nsight/export/模型执行。原超时及UNKNOWN后代状态不改。

## 原件与身份

回传 `gate10_g1_76ef717_timeout_review.zip`，2175403 bytes，SHA256 `D6A0F34DEABDCAAC61C7E8C0BA0EA9A1B47CAAE70F4BF5E03448A35E596461C4`。直接核验CRC、86项唯一路径及安全解压；此诊断包没有独立总清单，不能声称验证了不存在的清单。输入receipt的13项hash/size和producer身份链通过；最终86项解压文件与ZIP逐字节一致。

run `run-20260929T104308Z-1ad61e11`，WMPC `wmpc-668c6eeda23e7618`，target PID63500。执行commit `76ef7179b93ffcc51db70e7fdb002fd276f6aaa3`、clean；Git二进制NUL清单536项与seal路径集合相等。159项与Git blob字节相等，377项仅LF→CRLF可精确复现其hash，不伪称全部blob字节相同。实际runner副本/manifest/prompt、目标解释器/PID/CUDA/配置、preflight claim/final、阶段与drain按既有inspect_execution和input receipt验证通过。

服务器原日志相关CPU121 passed（不是本轮本地测试）；采集36.406秒、exit0，producer COMPLETE；export一次PASS。原point driver900.016秒超时，无最终collection report；512 NOT_RUN。未从事后快照反推超时时后代已退出。

## 定位与最小修复

原件规模：21470 API、350 sync、7390 device activity、13 NVTX、19 diagnostic。45秒有界cProfile显示候选分类约22170次重复读取同一registry，以及重复建图；中断profile不用于精确总耗时分摊。

源码和独立工作量反例进一步定位：A每个原子片段全扫API/sync，覆盖API又扫一遍，复杂度约O(片段数×记录数)；LEGACY默认流建边两两扫描后才排除同流，单流也付平方成本。100个不重叠API的真实A入口旧版调用覆盖谓词30100次；新入口避免全表逐片扫描。100个同流活动旧版get读取40500次，改为一次分组过滤。

修复仅为：每次candidate batch加载一次registry（不跨运行缓存）；按context预过滤不能产生default跨流边的同流/nonblocking项，保留其余边/冲突顺序；A用排序端点活动集合取覆盖项，保持原始顺序、半开区间和同步优先级。所有记录仍经过原始时间校验；W、terminal、ownership、validity、API分类与公式不变。保留物理S/B计算和load_domain重新计算校验，没有跳过检查。

新增flush阶段日志区分collection/export/Canonical/projection/physical S/request A/physical B/复读；日志COMPLETE仅表示函数返回，不替代机器准入。

## 同一SQLite的新派生审查

独立目录 `gate10_timeout_v0_1/analysis_v0_1`（机器定位见本地handoff），domain SHA256 `67dea56069687652fef9521f603580ab57d4e548b97c9c5593240ed6cdc7e41e`。
完整process_domain及load_domain复读186.206秒：Canonical1.793、projection/diagnostics0.502、首轮physical S45.821/request A9.215/B0.011秒；复读82.773秒（其中S55.684/A14.795/B0.010）。其余包含加载、序列化及文件校验。与服务器不同机器，不宣称精确加速倍数。此前单轮诊断64.231秒不等于完整文件链耗时。

| trace窗口(ns) | 总时长 | Host | CUDA API | device wait | sync residual | unattributed |
|---|---:|---:|---:|---:|---:|---:|
| Request | 179524256 | 116863864 | 62442678 | 12320 | 205394 | 0 |
| Prefill | 91969319 | 59800304 | 31979212 | 12320 | 177483 | 0 |
| Decode | 87554937 | 57063560 | 30463466 | 0 | 27911 | 0 |

互斥守恒和逐分量Request=Prefill+Decode成立；实际128输入/2输出、非early EOS，warmup1/repeat1。host观察时长179109500/91958300/87151200ns，和trace锚点时钟分开，不能混算。边界/drain/必要集合、双模式成员/边和其他质量门通过；官方同类诊断review仍保留原始消息。状态QUALITY_CHECK_PASSED_NOT_QUALIFICATION，UNKNOWN/NOT_ASSESSED不变。

128/2现可记为**离线修复后一次可行性通过**，不是原失败driver被追认成功，更不是统计稳定性、科学A或Formal资格。无新增语义/数据阻塞。完整domain仍有936897038 bytes，主要是重复逐sync/proof证据；本轮不改变schema或删证据，存储成本是已知工程限制，不再扩展优化项目。

## 验证与下一步

测试先复现registry重复读取和同流平方扫描；独立负/跨零/相等边界/嵌套区间、同步优先级、未知API/ownership/缺依赖回归保持。实际A入口用Git旧实现内存加载重放，工作量反例失败30100次；新实现通过。CPU回归及静态检查的最终结果见research_progress 7.101。未运行完整Q0、全量测试或新实验。

Gate7～9限定PASS保持；Gate10 NOT_RUN，尚缺512/2实物及最终workload审查。只准备`--remaining-512-only`新目录单点方案；未修改900秒上限，不重新运行128/2、不恢复旧目录。先交协调窗口审查固定包，未来任何失败即停止、无自动重试，单ZIP回传。N1功能准备、Pilot/Freeze/Formal仍另行，不由本结果授予。
