# Controlled launch construction 0.2.0

2026-09-26；Engineering 可观察性对齐，不是 A 科学验收或新 Q0 资格。
Gate7 PASS；Gate8 / 新 Q0 NOT_RUN。承接 [0.1 bridge](gate8_controlled_bridge_v0_1.md)。

## 真实失败与不变的边界

直接审计服务器执行 commit `7f61102e1313d298c64da44487373675e33b8fa5`
的离线后处理包：29 文件，清单覆盖其余 28 项，大小/hash 全匹配。
清单 SHA256 `ce0552af8525eb544a398c3fd6170dd341ae216233b29f1bef78235f6e20679c`。
REP SHA256 `10be1d6a92de0f223e622c7f8ad5e026de192eb34811e0ca2b31efe670571106`；
SQLite SHA256 `dd5431558ab58dacff327c7216fd869254d79ed454b5818a5c1b13bbc3225375`。
第一次 export 成功：exit0、0.125秒、323584 bytes、无 timeout/kill/retry；
audit exit1，停于 `EXPECTED_API_SET_MISSING_OR_EXTRA:controlled-0:0:submit`。
所有原输入与副本保持不变；不是 export 故障。

只读查询四个 submit NVTX 范围，均有一个完整包含于 marker 的 Runtime
`cudaLaunchKernel_v7000`，return0，无额外 Driver。目标 PID 的 Runtime 表没有
GetLastError/PeekAtLastError 记录。源字节确实调用 GetLastError；执行 receipt
只能证明 host 返回检查通过，不能提供该 API 的 Raw 起止时间。
因此缺失必需 API 的旧 0.1 attempt 正确 BLOCKED；不将未观测间隔补作 Host。
不能据此断言过滤的精确机制或工具永远不支持该 API。

## 最小新构造

新 construction 为 `CONTROLLED-D2H-REQUEST/0.2.0`，仅对新 plan、producer、
NVTX、operation ledger、sealed receipt 和新 Raw proof 生效。旧 0.1 输入显式拒绝，
可用原执行 commit 复查原来的拒绝；禁止修改旧 receipt 或重新标记旧结果。
文件 shape/schema 未变，construction 是语义兼容门，不静默 fallback。

原生 submit 从 triple-chevron + GetLastError 改为直接 `cudaLaunchKernel` 并返回
其错误码。kernel symbol 转为 `const void*`；args 是 `&device_token, &value` 两个
参数存储地址，生命周期覆盖 launch 调用；设备分配直到 wait/read/cleanup 后才释放。
单 block/单 thread、零动态共享内存、显式 nonblocking stream 不变。
copy/wait 的 CUDA 返回码检查不变；非零仍导致 INCOMPLETE/BLOCKED，无成功 receipt。
launch 成功不表示 kernel 完成，host-readable completion 仍在 D2H + stream wait + read 后。

依据 [CUDA Runtime 12.4.1 Execution Control](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/group__CUDART__EXECUTION.html)：
cudaLaunchKernel 接收设备函数 symbol 与指向参数存储的地址数组，并返回 CUDA 状态；
它也可能报告前序异步错误。因此保留后续 copy/wait 检查，不能把返回成功当 completion。
此处未通过本地不同版本 nvcc 冒充目标 12.4 编译。

Raw checker 对新 submit 要求恰好一个已支持的 Runtime launch、return0；
额外 GetLastError/Driver、缺失 launch、版本冲突仍拒绝。W(s)、terminal、
A 分类 registry、B timing、Derived 公式、observation profile 均未改变。
独立预期仍是 wait set 2/4/2/4、各 terminal 为对应 D2H。
这不是任意模型 GetLastError 的支持方案，也不解决跨 request 同流 epoch。

## 未选择的路线

- 旧记录可保留执行、export、可见 launch/copy/wait 诊断，不能发布合格 request A/D。
- 安装 UserGuide 有 all-APIs 选项，ReleaseNotes 却称 CLI subset 不可更改；
  未证明目标 binary 支持，不修改 profile，也不继续宽泛搜索。
- 标记 error-check span 并作为 unknown envelope 会需要显式观测/缺口合同，
  不能发明 API 精确时长或隐藏依赖。本次不采用。

## 验证与下一步

先修改确定性 fixture 为实际新构造预期，旧实现得到 5 failed / 28 passed；
其中 Raw/file-chain 重现同名 submit 错误，另外覆盖新版本与旧输入拒绝。
非零 launch/copy/wait 的 NativeBackend → producer 测试是已有保护的回归，
不是声称新发现其缺陷。源级 native 检查不是编译或运行证明。
新 fixture 仅包含真实新构造声明的 API，A unknown 应为零，仍明确 synthetic、
measurement_validity NOT_ASSESSED；未把 UNKNOWN collector 状态改为零丢失。

本地 Python 3.12.7：37 targeted passed（20.05s）；CPU-only 全量
1169 passed / 5 skipped（186.56s）。在测试子进程 PATH 排除 nvcc 并断言不可解析，
五个 skip 均为 CUDA source 编译相关测试；没有运行本机不同 CUDA 版本替代验证。
compileall、validate-contract 37/37、Canonical boundary（7模块）、oracle independence、
git diff --check 均通过。协调窗口只读审查未发现本批提交阻塞；旧 plan 在
execute 入口、旧 sealed construction 在 Raw 入口均被负例覆盖。

交付后先审查增量包，再由用户在固定 checkout 部署、目标 nvcc 编译及静态复验，
生成新的 source/DLL/hash/build receipt；旧 DLL 不复用。失败停止，不加载模型。
通过后另行限定授权一次新受控 capture。必须全新 run，重新验证实际 API 集合、
锚点、oracle 与文件链；不保证新 profile 一定采到所需记录。
本轮不部署服务器、不运行 GPU/Nsight；原件不修改、不上传。
