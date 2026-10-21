# CUPTI 提交效果桥与局部完成分析 0.1

阶段：Engineering 本地实现。权威方案仍为研究设计 v7.1、实验协议 v2.1 Pre-Pilot。
这是独立的新来源合同，不修改已有 Nsight Canonical、S/A/B、COE 或 Formal。

## 本轮解决的层次

原先的缺口在 API 实例到设备效果之间。stream/device/event 标识限定完成范围，却不能
单独说明某次 memset 是否请求了零字节，也不能把同流的邻近活动指定为该调用的效果。
本实现把两个关系分开：

1. ENTRY 参数快照、EXIT 返回、实际 runtime/driver 父子栈及分域 correlation，建立
   提交实例到设备效果的来源边。允许有实际 API 行的顶层 driver 提交，不虚构 runtime 父节点。
2. 实际物理同步及其提交边界，建立同步到必要设备效果的完成关系。已完成成员仍保留；
   不是仅选择与同步重叠的活动。

若记录到嵌在复制 API 内的真实 driver stream 同步，单独输出其成员、物理区间及活动交集。
缺 driver API 行时其 API 墙钟为 null，不把 callback 或物理同步区间伪造成缺失 API 行。
没有这种证据时，不假定复制 API 自带可分离的同步，更不把 memset 当作同步。

## 文件链与合同

- `scripts/native_cupti_timeline/`：固定 CUDA12.4 / CUPTI API22；预分配有界容量、逐线程
  父子栈，复制 kernel/Memcpy/Memset/API/sync/context/stream/event 结构，在缓冲返还前
  保存需要的字段和字符串。显式 open 才加载 CUPTI；DLL 导入和加载本身不初始化 CUDA。
- `exposedpath/cupti_timeline.py`：同进程显式会话；原 NVTX 调用仍在原位置发出，另记
  同一 CUPTI 时钟的原标签。不能与 Nsight/torch.profiler 同时订阅。此观测实现的开销
  不继承 Nsight 的资格，尚未在真实模型上评估。
- `analysis/cupti_timeline.py`：`cupti-timeline-capture/0.1.0` 到
  `submit-effect-evidence/0.1.0`；从原 producer 标签选择物理 drain、request、copy、
  sync 和 Host-token point。外部输入/producer/token 文件真实性仍须由运行合同绑定。
- `exposedpath_v141/submit_effect_bridge.py`：`submit-effect-bridge/0.1.0`。
  输出来源边、logical-zero、完整局部必要成员、terminal、COE及观察到的内部同步事实。
  复用旧 FIFO/区间算法，但不伪造 Nsight SQLite、clock、rowid 或 production A/B。

普通 runtime LaunchKernel/MemsetAsync/MemcpyAsync、stream synchronize，以及有实际
API 行的顶层 driver LaunchKernel/MemsetD8Async/MemcpyDtoHAsync 有显式窄域规则。
driver Memcpy 的 typed runtime correlation 必须与实际父子关系相符，或独立完整成立；
数值相同的跨域编号不构成关联。

count=0 保留逻辑调用与原 API 时间，不造活动。只在成功 drain 后、同一请求内、单线程
单 FIFO、无事件/图依赖、零调用在 copy 前返回、真实同步和 terminal 闭合的投影中允许空
设备效果节点。count>0 的效果缺失、payload 冲突、错流、缺父子、丢失或关闭失败仍拒绝。
历史 event 只有实际关联且被后续 context drain 闭合才列入前缀；请求内事件依赖不支持。
这不是对全部 CUDA API、并发、多流或所有输入长度的通用资格声明。

## 独立验证

手定小 trace 的必要成员为 kernel、64-byte memset、8-byte D2H，另有零 payload 逻辑节点。
物理同步 47–68ns，操作 40–70ns；独立预期 COE=20ns、原同步交集=15ns。真实 SDK 结构
Host 替身 → native JSON → 原标签/物理 drain → 来源桥 → 局部 S/COE 复现这些预期。
另有嵌套 driver 同步参考，物理交集为13ns，缺 driver API 行时墙钟保持 null。

本地新入口 **82 passed / 0 failed / 0 skipped**，包含实际头文件编译链接、DLL Host-only
加载、逐线程栈/参数快照、跨域冲突/孤儿/错 scope/缺效果等反例、PS5.1 禁采入口。
旧参数消费者、COE及预算等相关回归 **156 passed / 0 failed / 0 skipped**。
本地 MSVC14.44、Python3.12.7；目标 MSVC14.38、Python3.11.16 与真实 GPU 尚未验证。
命令/JUnit/build 记录在忽略的本地 `cupti_timeline_development_v0_1` 诊断目录。
这是 CPU 与 SDK 编译证据，不是 CUDA Q0、模型覆盖、平台资格或新的 Formal。

## 固定下一步

新 Stage A 仅部署、固定工具链/依赖字节核验、真实头文件构建及上述 CPU 文件链检查。
默认模型/微例/profile 预算均0，没有采集开关。目标机回执通过后，才能准备一个新运行的
同进程真实模型诊断；参数、所有必需活动、原标签、资源、丢失与关闭状态必须同次闭合。
不拿新参数补旧768/1024，也不恢复原七槽。若真实模型暴露新的未支持 API/事件/并发，
按具体来源拒绝并裁决，不据无效果填零或自动扩设施。

完整PS5.1正向启动演练发现本机缺`Get-FileHash`命令；新入口直接使用.NET SHA256，
不依赖该附加命令。正向CPU驱动替身及禁采参数均实测；不把它当成目标服务器证据。
完整包演练另发现`-I`忽略禁写bytecode环境变量；bootstrap在任何同目录导入前显式禁写，
独立子进程反例核对包目录没有新增`__pycache__`，保持精确文件清单。

82项本地成功不证明真实 PyTorch 已修复。新的采集来源、观测扰动和模型覆盖是剩余闸口；
`pure_host_blocking` 保持 null。旧 BLOCKED、UNKNOWN、Gate13限定PASS和Gate14 NOT_RUN不变。
