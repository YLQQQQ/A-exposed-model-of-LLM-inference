# 受控资格显式目标解释器合同 0.1

2026-09-27，用户批准的限定本地实现；不是新采集授权，不改变A/S/B、completion或诊断门。
仅新受控qualification封套`exposedpath-controlled-qualification/0.2.0`使用；旧0.1计划拒绝
进入新入口，不补写、不追认历史attempt。construction仍NULL-FIFO-D2H/0.1.0。

## 解释器与环境

prepare必传`--target-python <absolute-base-python>`及`--site-root <explicit-venv-purelib>`。
服务器草案由固定checkout的venv Python读取其`sys._base_executable`与purelib，先记录再传参，
不是搜索PATH或让服务器追随main。native构建及分析仍由原venv Python编排；新目标进程
显式使用base解释器的stdlib和指定venv依赖，不能宣称是完全相同的venv启动环境。

目标argv固定`<python> -I -S -c <versioned-bootstrap> <repo> <site-root> ...`。
bootstrap只将两条显式路径加入sys.path；不执行site/.pth/usercustomize，不用PYTHONHOME或
PYTHONPATH猜测环境。若依赖这种隐式初始化，明确失败，不自动改回venv launcher。
无模型或torch import；CPU probe导入JSON schema和受控代码所需依赖，不加载native DLL。

`exposedpath-target-python/0.1.0`预执行probe记录请求exe/hash、site、module root、nonce、
Popen.pid、子进程PID/parent PID及snapshot。snapshot含实际exe/base exe/hash、prefix、
Python完整版本、隔离/no-site标志、sys.path、jsonschema实际来源/hash、CUDA两变量、PATH hash。
这是一组明确的执行环境字段，不是所有包/环境变量的完整快照；不输出令牌或整个环境。
Popen PID必须等于实际PID，exe必须等于请求base exe；nonce/环境必须匹配，20秒超时拒绝无重试。

`plan.target_python`封存probe；实际producer在创建输出目录和加载DLL之前重新取snapshot，
逐字段相等才继续。`execution.target_runtime`记录实际PID/parent PID/snapshot，再与
pass_identity.pid绑定。probe PID与后来实际采集PID是不同进程，**不要求二者相等**。
离线reader验证各自产物关系，不要求服务器路径等于本地审计机器路径。

## 采集进程与producer的最后一段绑定

export后、oracle前，从原DIAGNOSTIC_EVENT读取精确的profiler启动通知：必须唯一、Daemon
source=2、severity=1，消息PID与globalPid编码一致，并等于实际producer PID。
NVTX完整global PID还必须属于同一namespace；缺记录、多条通知、跨PID/namespace均拒绝。
原SQLite hash及原rowid保存在候选结果target_launch中。只证明身份链，不证明诊断无害、
无隐藏子进程或零丢失；其它warning仍经过原oracle及Engineering质量门，不新增豁免。

CPU真实子进程验证隔离启动与producer实际落盘，native调用仅在测试辅助文件中替换；
另有nonce/路径/环境/PID、缺launch/重复launch/namespace、pre-native拒绝与文件篡改反例。
这些测试不证明目标Windows3.11/Nsight已通过，不重判原始失败包。

## 独立sync枚举修复

oracle输出版本`exposedpath-qualification-oracle/0.1.1`：只明确接受CONTEXT_SYNCHRONIZE、
STREAM_SYNCHRONIZE及它们带`CUPTI_ACTIVITY_SYNCHRONIZATION_TYPE_`的完整名称。
按导出enum名称映射，不固定数字，不任意去前缀/后缀；其它名称拒绝。实际全名前缀的
合成fixture证明预期集合/五类结果与短名相同；此修复不触及warning检查或冻结registry。

## 交付与停止

单一增量bundle基于服务器d4865d0。整段命令先供协调窗口审查，不运行服务器。
未来若批准，仍是新目录的一次2-request/2-token受控尝试及一次export，无模型、无自动retry。
静态/probe/环境/身份冲突、native失败、缺Raw映射、未知warning或oracle不符即停止。
probe通过不保证profiler注入后环境不变；后者不匹配也拒绝，不临时过滤字段放行。
完整产物封存为单ZIP并回传；审计GUI只能使用新副本，不能再把GUI改变后的REP混入原身份链。
旧ZIP与BLOCKED报告不变；Gate7 PASS，新Q0/Gate8 NOT_RUN，D/Signature关闭。
