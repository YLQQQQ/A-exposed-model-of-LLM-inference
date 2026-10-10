# Gate13 首槽 prepare 修复审查 0.1

2026-10-10。**原批次 BLOCKED；Gate13 BLOCKED，未通过。** 这是冻结后工程修复，
不改变输入、执行矩阵、研究 claim、completion/流/同步或 S/A/B。新执行锁和协议
补丁候选必须重新确认；原签署、失败报告和 Raw 不覆盖，不自动续采或替补。

## 原件与失败时序

直接核验 `gate13_e38fa91850b8_formal.zip`：172716 bytes，SHA256
`5279780d660f97668e3d7d73dde584a84a7d6ac5bc5524156656cac0a9b0faa0`。
39 文件/38 项清单，CRC、安全唯一路径、大小/hash 与完整覆盖均通过；清单 SHA256
`86aa6761a9e58eaaa7055726c1f6f28a8e375fe521e6e0b935277addb344ad49`。

`07_batch.log`（UTF-16）只有首槽 b1/G32/pass0、prepare START 和
`ValueError: FORMAL_INPUT_HASH`；`07_batch.exit.json` 为 exit1。
`batch/batch_report.json` 首槽 BLOCKED、其余 59 槽位 NOT_RUN、pairs=[]。
prepare 只留下输入及模型清单副本，没有 manifest、collection、producer、REP 或 SQLite。
锁定控制器仅在 prepare 返回后才启动目标模型/collector，所以未启动任何模型进程，
未发生 warmup/request 测量。prepare 已进行解释器和最小 CUDA 身份查询，**并非零
CUDA 交互**。包内 `05_nsys` 是 CLI 版本查询，不是采集。

执行/分析仍为 `e38fa91850b8f31e17cc0ee264987ef3c1313d7d`；
`source_bytes.json` 中 prepare 源码实际 hash
`77697d5ebac74d62bdda8f044a2c7cb1a7d422ccfe2bd50150c9589c75a3e2f9`
与签署 Git 锁一致，不是拿文档 HEAD 反推服务器源码。

## 比较双方与根因

| 对象 | 来源与字段 | 实际值/算法 |
|---|---|---|
| 冻结 G32 期望 | signed_release.json → protocol.input_hashes.G32 | `4dffd0ddcbd3185c656ae4a27efaf5aab302febba6ead5df4d37d903a2091920` |
| 原输入及 prepared/prompt.json | 两个文件的完整原始字节，2893 bytes | SHA256，均与上述期望完全相同 |
| Formal 校验所读实际值 | 未 finalise 的内存 manifest → prompt_tokens_sha256 | 字段缺失，`.get()` 返回 None；不是另一个文件哈希 |
| G512 输入 | signed_release.json → protocol.input_hashes.G512；prompt_512.json | 14994 bytes，SHA256 `36c507c56d1c851bab0238c30dfd7645a5ea7eef646310c01988ae2aaffbdd0a` |

`create_manifest()` 有意保留未完成的 hash/WMPC；实际文件 hash 由
`finalize_manifest(..., prompt_tokens_path=...)` 填入。Formal 分支却先调用
`formal.validate()`，故 None 与固定哈希比较失败。这不是 LF/CRLF、传输变化或
token 序列 canonical digest 冲突。当前函数名 `compute_prompt_tokens_sha256` 的
对象也是整个输入文件原字节；WMPC/manifest 文件身份和协议规范化内容 hash 是
另外的对象，不互换。

本地使用封存输入、原签署内容和 125 个锁定 Git blob，CPU 外部探测替身回放
原 prepare 源码：实际字段缺失/None、WMPC=None，同样报 FORMAL_INPUT_HASH。
仅移动 finalise/校验顺序的对照，重新读取真实 copied bytes 后通过该校验。
替身软件/GPU/模型事实不授予平台或 Formal 资格；回放未改原件，也不让旧签署
授权修复后源码运行。首个回放脚本缺少 Python 包上下文而失败，修正回放工具后
在新目录完成；这不是服务器失败原因。

## 最小修复及验证范围

prepare 在角色/配置声明完成后先 finalise，再调用原严格 Formal 校验，保存
manifest 前仍必须全部通过。不复制期望值，不归一化输入、不忽略差异。
五条件 × 两 pass 的实际 prepare → prepared 校验 → verified CPU 替身入口 →
producer 文件链覆盖；另外覆盖原输入和 copied input 篡改、未签署、未知版本、
role/hash/variant/config/commit 冲突以及 mixed-version ledger。实际三次暖机、
N1 三条 held 暖机流和 fresh measured 流也按文件核对，不只看配置值。
外部 CUDA/模型/解释器/Git 操作是 CPU 替身；原 seal 的独立反例复用相关回归。

tests-first 原错误红例 16 failed/3 passed；顺序修复后 19 passed。
新协议 reference 的闭集兼容测试发现旧 identity schema 装配只接受 0.1，
在新版本分派中修复，保留旧 schema 文件及 cross-record exact-reference 检查。
最终命令、计数、耗时和静态检查见唯一进度事实源 7.124。

## 冻结与资格关系

准备 `G12-ROUTEA/0.1.1` **未签署补丁候选**：只修 prepare 顺序及显式协议
版本/reference 兼容。元数据封套仍 G12-FORMAL-ENVELOPE/0.1，测量 schema/registry
及五条件/六 block/w3/repeat1 不变。新 formal reference schema 0.1.1 单列；
旧 0.1 schema、候选、签署和历史数据判定原样保存。未知版本拒绝，新协议还必须
锁定新 schema。producer 允许两个明确版本，实际 ledger reference 必须与自己
绑定的 protocol/approval 精确一致；不能混版本或 fallback。

先提交实现，再从真实 commit 绑定全部源码和新 schema、生成新候选 hash，
避免自引用。旧签署的内容 hash 不覆盖新 commit；旧 approval/实际字节 seal
均不能继承。没有改变研究输入或规则，无需重新裁决 claim、重跑已获资格实验；
但**必须确认并重新签署新的精确候选内容**后才可部署执行新批次。
Gate12 历史限定 PASS 保持，新补丁不是已签署发布；Gate13 仍 BLOCKED。

本地当前交付只有一个待审 ZIP，包含固定增量 bundle、未签署候选、原输入
和补丁/验证索引；不包含可默认启动的采集入口。不把无模型的失败首槽替补为
成功，不沿用旧输出目录；未来批次/预算和启动须在新绑定审查后明确。
UNKNOWN/NOT_ASSESSED、G1 只投影 A、N1 单 sync B、opaque 内部等待未拆、D 禁用保持。
