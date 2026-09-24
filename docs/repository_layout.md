# Repository and server layout v1

2026-09-24，Engineering目录治理；不修改测量语义，不授权Gate8或GPU/Nsight。

## 单一代码入口

本地：仓库根 `main` 是唯一日常入口。代码包、测试、当前合同和closeout保持现有相对路径，不另复制源码。临时worktree只用于明确的短期隔离，先核验独有提交/用户修改/ignored文件，整合后用 `git worktree remove` 移除，禁止force。分支/tag与目录独立保留。

服务器：`$ServerRoot` 是用户指定的 YLQ 单根，其绝对路径只写本机配置。`$CodeRoot` 固定为一个已存在的 Git checkout，以后原地fetch、核对和正常更新，不能每个Gate创建 `repo_<commit>`。本次建议**复用已验证的现有Gate7 checkout、不搬动其venv**；原目录名即使含旧短SHA也只是历史名称，执行身份始终取真实HEAD，不能据名称推断。无需另clone到看似整洁的路径。

```text
$ServerRoot/
  <固定CodeRoot>/          # 现有checkout及其venv；具体位置在本机配置
  evidence/<gate>/<run>/   # 新Raw、日志、manifest、machine report；每run独立
  diagnostics/<task>/      # 非采集诊断，独立派生输出
  logs/<operation>/       # 部署/静态操作回执
  transfer/               # Git增量包和证据传输件
```

测试代码仍在 `$CodeRoot/tests`；临时测试输出用独立诊断目录。所有新执行应显式传Python、输出根与已批准输入，不复用旧run，不覆盖产物。更新代码必须先确认clean、无运行任务、固定批准commit、环境与模型身份仍适用。新代码commit不自动继承旧commit的实验验收。

服务器实际操作由用户/协调窗口执行，本轮仅提供本地 `.local/server_layout_setup.ps1` 草案：既有checkout→同一个固定checkout（不搬迁/复制），创建单根下的缺失容器并写回执；不fetch/checkout、不安装、不调用CUDA、不改旧证据。后续代码更新需另核对目标commit。

## 新默认与历史例外

- 旧服务器Gate6目录、既有模型位置、已冻结Gate7 evidence路径保持原样；不搬模型、不改旧manifest/receipt内路径、不全仓替换字符串。
- Gate6 `final-04` 的身份及外部归档原位置见 [closeout](v1_4_1/gate6_closeout_v0_1.md)。本次移除的Gate6 worktree只有已提交源码/缓存，没有唯一Raw；保留 `codex/gate6-canonical-baseline` 和冻结commit。
- Gate7唯一PASS仍是fresh8d64f75，其执行commit、ZIP/清单身份见 [closeout](v1_4_1/gate7_closeout_v0_1.md)。本地 `server_evidence_inbox/gate7/` 不移动，不删ZIP/解包件；旧失败attempt不追认。
- `nsys_results/`、`results/`、`pilot_clock_diag/`、`engineering_evidence/` 的历史身份不升级；已有跟踪的摘要保留，私有Raw与新日志不加入Git。
- `dist/` 是已有测试明确标注的冻结payload，保持字节，不当作当前代码。根 `SERVER_SYNC_MANIFEST.json`（2026-07-21）及旧overwrite installer只描述该历史发布，**禁止用于更新当前checkout**；当前以Git commit/tree为代码身份，避免手工刷新旧manifest或引入第二套覆盖部署规范。

## 本次保留/整合/归档/删除

| 对象 | 处置及依据 |
|---|---|
| main b18bf7e → 16604d5 | 快进整合135提交，无覆盖冲突；origin刷新后无分叉 |
| gate7-postprocessing / runner / gate6基线 | 内容已在main；移除退休worktree，保留分支与全部commit |
| gate6-warmup-clean @3dae79d | 四个非祖先commit经git cherry确认patch-equivalent；不重复套用，保留历史分支 |
| gate7-audit用户四份未提交文档 | 原样提交到历史分支a867d541d01f683ccfc462fcdec31afeeefbaecf；两份事故说明带历史横幅整合，旧进度/launcher文档不覆盖当前版本 |
| 唯一Gate5审查笔记、私有handoff/交付草案 | 原件移至忽略的`.local/history/`；不是新代码副本，不作为下一窗口命令 |
| 9个旧增量bundle | 核对refs/prerequisite及Git可恢复身份后删除；不影响历史commit或证据 |
| `交付文档/`两份DOCX | 与`docs/current/`逐文件SHA256一致后删重复件；当前文档不改 |
| bytecode/pytest缓存、临时PID测试venv | 明确可再生成且无唯一资料后清除；不修改系统Python |
| Raw/原报告/ZIP及未知唯一文件 | 保留；本轮不为节省少量空间改变审计定位 |

本地细项清单/核验回执在`.local/`，包含私有路径不上传。历史分支不是日常入口。原型tag `prototype-windows-v0.1` 保持不变；不改写任何既有Git历史。

## 发布与验证边界

提交前审查路径、大小和内容，拒绝凭证、原始trace、模型、证据包及本机配置。旧冻结文档中已有历史路径属于provenance，不批量改写；本次新增公共文档只使用相对路径/变量。正常fetch/merge/push，保留他人提交，不force push。分支保护要求PR时走PR。

目录治理只验证根目录可导入、CPU回归、合同内部一致性及文档入口；不重跑Gate6/7、不将目录整理commit冒充实验执行commit。Gate7 PASS及legacy限制保持，Gate8只待规划。

### 本次验证回执

- 在根目录Python3.12.7执行：显式CPU-only（Python进程内mask=-1、PATH不含CUDA、断言nvcc不可见）全量 `pytest -q -p no:cacheprovider`：1036 passed、5 skipped，140.48s；5项是原有nvcc编译检查，无修改skip规则。
- 首次及仅在外层PowerShell过滤PATH的尝试均为1036 passed、1 failed、4 errors；Python仍发现本机CUDA13/CP936编译栈，与此前本机故障一致，未修Q0/工具链。这些失败保留，不冒充服务器验证或无条件全量通过。
- compileall、validate-contract37/37、Canonical boundary7模块、oracle independence通过；仅内部一致性/静态边界，不是新资格采集。
- 从根目录重新只读验证Gate7 77文件及冻结legacy acceptance通过；本次保存的全部243个本地证据/Prototype文件逐项大小与SHA256不变。
- 生产代码、测试、冻结合同、Gate6/7 closeout相对16604d5为zero diff；没有GPU/Nsight执行。服务器布局草案只经PowerShell语法解析，未在服务器执行。
- 清理已完成：五个worktree正常移除，九个bundle在确认远端main可恢复其全部refs后删除，两份DOCX在相同SHA256核验后删除，缓存/空临时venv删除。分支/tag、唯一笔记及原始证据保留。普通push同步，不重写历史。
