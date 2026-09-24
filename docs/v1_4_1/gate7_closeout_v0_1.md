# Gate 7 Closeout v0.1 — Engineering integration acceptance

日期：2026-09-24。**Gate7 = PASS；EP-G7-11 = completed。Gate8 = NOT_RUN，待规划，未授权启动。**

本结论依据用户批准的 `docs/superpowers/plans/2026-09-20-gate7-execution-plan.md` §§1–4、§6 `gate7-legacy-analyzer/1`，以及 `docs/pilot_runner_contract.md` 的输入、completion、parity及attempt合同。只验目标Windows/RTX4090执行链，不改变冻结Measurement Contract、Canonical/S/A/B/D、Q0或Gate6资格。EP-G7-08/09/10既有完成记录见research_progress §5。

## 1. 唯一合格attempt与执行身份

- Evidence logical ID：`fresh_8d64f75_20260924T084650Z_d75ef1b8a4fb46709dbb7cfc1c95d27f`。
- Smoke relative directory：`collection/smoke_20260924T084657Z`，下文简称`smoke/`。
- 执行commit：`8d64f7580d43d7c8e1cb7a416b459cec8f60b011`；parent：`dced3646b536430209224eb7e0e9f0896dc20a67`。
- 开始/完成：2026-09-24 08:46:57Z / 08:53:31Z；外层exit回执08:53:33Z。
- run_id：`run-20260924T085101Z-796d75a6`；wmpc_id：`wmpc-aa82f71d6e9dcf83`。
- `runner_git_dirty=false`；外层final_git HEAD相同，status为空。WMPC是配置身份，可与旧attempt相同；run_id和manifest字节身份区分本attempt，不按WMPC或prompt哈希单独合并attempt。
- data_role=`Engineering`，技术run_role=`PILOT`；eligible_for_final_statistics=false。
- 模型：Qwen2.5-1.5B-Instruct/qwen2；revision=`unknown`；32 input/2 output、batch1、warmup1/repeat2；eager/fp16/sdpa，do_sample=false，G1_NATURAL/natural_token_ready，n1_intervention=null。
- 平台：Windows/PowerShell5.1，Python3.11.16，torch2.6.0+cu124，CUDA runtime12.4/nvcc12.4.131，transformers5.17.0，Nsight2026.2.1.210-262137639646v0，driver555.99；VS2022 x64/MSVC14.38.33130。
- GPU physical3/logical0，UUID=`GPU-0d8fafe6-a1e9-33cc-25fb-632316736455`，PCI=`00000000:E1:00.0`；CUDA_DEVICE_ORDER=PCI_BUS_ID，CUDA_VISIBLE_DEVICES=3。

本文件所在提交是**文档收尾commit**，不是执行commit。服务器无需为文档收尾重新部署或重跑。原始私有目录/模型绝对路径和Raw文件不进入Git；此处使用逻辑产物名与hash定位。

## 2. 包、清单与核心产物SHA256

原始ZIP文件名：`fresh_8d64f75_20260924T084650Z_d75ef1b8a4fb46709dbb7cfc1c95d27f_transfer_90929c214015425695e22ed475fa7a4b.zip`，2082318 bytes。

| 产物 | SHA256 |
|---|---|
| 原始ZIP | `53fe5ce8004e025f5524fe7fe462d05ce91b88331f886928c76e80ee9d4a398a` |
| artifact_sha256.csv（76项） | `ea1476a2c785e301a72cbc26eece440685245771742d06ec9e84d2ce7b0dbc0d` |
| smoke/smoke_test_report.json | `0a082d5da27e92bb3582589be270233c6093418f5c6c5ea982af7ed5daa87a90` |
| smoke/wmpc_manifest.json | `36dac76945475615396892d6db37a21a264904d9bad8f81333719d7e2664fe07` |
| smoke/prompt_tokens.json | `4dffd0ddcbd3185c656ae4a27efaf5aab302febba6ead5df4d37d903a2091920` |
| pass1/pass1_profile.nsys-rep（948603 bytes） | `7d47d8f38a2069c816a8573b78d52c4932fbdd022013d532b5c1c23e78b6fa19` |
| pass1/pass1_profile.sqlite（2568192 bytes） | `005cf068bff99c36585a91343d8841d12bb2cad41a94bdc9bc1478045691877c` |
| analysis/analysis-20260924T085329Z-lwr3f60s/accounting_result.json | `4d4b416b38311ed904184612a9f04d370127afa422dff8807f0b615e87530633` |
| accounting_summary.csv | `8949e0666c4db3e4ccbbbad59b2c3d52fe3e847d676f58226c6022e5e1820e97` |
| b_sync_detail.csv | `ca4ca3e57ef483a1548abd5d781a98ee74dcace79a19377e7d0a88f7c97a707f` |

本地重新验证ZIP大小/hash、CRC、无重复/越界路径；77文件=清单自身+76产物。清单完整覆盖其他文件，76项大小/hash全匹配；解压77文件逐字节与ZIP一致。只读审计完成后再次逐文件和ZIP核对，未变。

## 3. 逐项acceptance核验

| 必需项 | 直接证据与核验结果 | 判定 |
|---|---|---|
| 执行commit/clean | manifest、run_plan、launch_transcript、final_git一致；新commit全SHA、dirty=false；不是文档HEAD替代执行身份 | PASS |
| 源码字节/输入身份 | 两pass runner_source_sha256=`f3765d96f161f13a879c44b1f98adf3c36c8a9a2fdc7ff136af929b98301a6c3`，与执行commit中runner.py的CRLF文件字节匹配；不是直接把LF/CRLF hash视作相等。实际manifest/prompt哈希分别与report/两parity一致；重新计算WMPC一致 | PASS |
| 本次全量/compileall/verify | 本attempt logs/03_pytest_stdout：1040 passed, 1 skipped/140.76s；launch_transcript相应exit0；04_compileall stdout/stderr无错误、exit0；08_verify_pilot包/环境检查成功exit0。verify内部SkipTests仅避免重复前面的pytest，不是跳过launcher全量 | PASS |
| 同commit补充静态 | preflight_snapshots/identity_8d64f75…082913Z：真实repo Python→Git、185定向、compileall、contract37/37、Canonical7模块、oracle及diff/show-check通过。它补充本commit静态门槛；旧dced364全量不是本次测试成绩 | PASS |
| pre-model gate | 10_create_manifest真实producer传UUID/PCI及严格Git参数；11_validate_manifest与12_pre_model_identity exit0，12报告PASS/issues=[]，先于20_pass0 | PASS |
| Pass0/Pass1计划与完成 | 每pass两个成功repeat，index0/1、retry0、无EOS/OOM/exclusion；实际32/2/batch1；warmup1的日志、before/after_warmup telemetry及planned count一致。无exclusion文件对应零exclusion，按既有attempt loader处理，不补造空文件 | PASS |
| Token-ready/phase | 四个measured request各两个单调completion点，首/后token机制均device_to_host_token_ids/natural_token_ready；request_end逐条等于最后completion，E2E与start/end相符，cleanup不入窗口；两pass phase policy相同 | PASS |
| parity/NVTX | 复用冻结六组validate_pair与attempt/evidence validator只读重算通过；SQLite目标PID50740有12个NVTX range（2 invocation、6 phase、4 structured sync），4个sync的run/wmpc/pass/repeat/token/自然身份齐全。request/phase仍是legacy label，不声称v1.4.1 Canonical科学映射已验收 | PASS |
| GPU identity/telemetry | preflight/manifest/run_plan固定physical3/logical0/UUID/PCI；逐条核对全部14条telemetry：requested/observed身份一致，query_exit0、identity_match=true，run/wmpc/pass一致 | PASS |
| Nsight观测profile | exact argv及profile为cuda,nvtx；sample/cpuctxsw=none，cuda-memory-usage=false，process-tree，isr=false，stats=false；无force-overwrite/GPU metrics/WDDM/system-wide采集；profile exit0，非空REP | PASS |
| REP→SQLite | 同attempt export1，PID65480，exit0/process_exited=true，0.265s，无timeout/kill/retry、issues=[]。REP hash与readiness/attempt一致；attempt1输出与canonical SQLite逐字节相同且报告hash一致 | PASS |
| SQLite只读门槛 | 本地mode=ro/immutable integrity_check=ok；既有Gate7必需表/列validator通过；保留原始DIAGNOSTIC_EVENT，不重新export或运行analyzer | PASS |
| analyzer/CSV/diagnostics | analyzer process exit0；本地用冻结validate_analyzer对原JSON/CSV/SQLite/manifest只读复核，严格schema、A结构、UID、CSV/JSON多重集和五份hash全部通过；重算acceptance与41日志及machine内acceptance完全相等 | PASS |
| final report | exit回执0，machine READY_FOR_SMALL_PILOT/errors=[]，环境门、两pass、后处理和analyzer一致；由本closeout审计作Gate7决定，而非直接把READY字符串当科学PASS | PASS |

本次pytest的`-q`输出未列skip node/reason，原样记录1 skipped，不声称它执行通过。执行代码`tests/test_python_source_portability.py`在pre-3.12有确定的tokenize.FSTRING_START skip条件，与Python3.11及此前记录相符；这是源码支持的解释，不是本次日志打印的node身份。冻结门槛是此命令成功且无失败，未设置零skip要求；不新增测试重跑来追补日志。

## 4. diagnostics审查与不可提升的限制

- Legacy trace_quality：fatal_errors=[]；唯一warning/missing_optional_table为已批准的`CUDA event activity table unavailable`。dropped_records_status=`unknown`，不能写成零丢记录。
- SQLite原始DIAGNOSTIC_EVENT共69行，44条warning涉及11个其他process-tree进程，内容包括no CUDA/NVTX events、profiling might not have started、not all NVTX events might have been collected。用现有globalPid解码规则并与CUDA context processId、NVTX/runtime身份交叉检查：目标runner PID50740无warning，具有12个NVTX range及CUDA记录。目标进程另有软件instrumented trace的info；不是hardware trace资格。
- 不静默删除或统一豁免这些原始warning，也不推断其工具/子进程根因。按已批准§6，Gate7验收校验legacy trace_quality且保存原始诊断，不重新定义完整trace科学有效性；上述非目标进程warning不构成已证实的目标required range缺失。Gate8应在独立设计中处理真实Canonical observation/validity，不能从本次结论得到dropped=0。
- acceptance_version=`gate7-legacy-analyzer/1`；analyzer_type=`legacy-only`；acceptance_scope=`ENGINEERING_INTEGRATION_ONLY`；measurement_validity=`NOT_ASSESSED`。
- A为`VALIDATED_STRUCTURE_ONLY`，window_coverage status=`unknown`、count/duration=null，原因`LEGACY_OUTPUT_LACKS_WINDOW_IDENTITY_AND_FROZEN_VALIDITY`；不把legacy coverage或B_valid比例解释为完整request可解释比例或科学守恒证据。
- 真实workload `Raw→Canonical→S→A/B→D/Exposure Signature`、完整request completion/accounting守恒/validity验收仍属Gate8 EP-G8-02，本轮未运行该链。
- 此次只证明export成功路径；真实timeout/kill/retry未触发，不证明历史即时export挂起或BugCheck根因已修复。所有旧BLOCKED/interrupted attempt保持原状态，未补写manifest、旧report或追认。
- repeat2只服务Engineering integration；不用于性能claim、统计充分性或Formal结论。仅声明该Windows目标栈，不声明Linux/第二平台支持。

## 5. 环境/模型来源与归档边界

snapshot_sources逐项区分本commit静态回执与dced364历史环境/模型/compiler/static：时间在目录逻辑ID和原始transcript内保留。执行时记录MSVC x64/14.38、nvcc12.4.131、目标GPU/driver和模型输入内容匹配。历史模型清单23文件/3098976006 bytes，SHA256=`72465c906baeb0cfa4fd94d21ef6c69c1cd8046bb68c61a94c02a1580d2541f9`。其中7项为loader输入候选，13项.cache、3项辅助文档不混作输入。

模型本体未传回，本地只核清单及服务器内容匹配回执，未复算服务器权重；revision unknown不据缓存名推断。compiler/两0-byte compatibility marker快照只作工具链provenance，不执行/修改marker。本次compute query为空只是当时可观察记录，不声称排除了所有WDDM/环境干扰或硬件因果因素。

本地审计复用了执行commit的只读validation函数（evidence、SQLite、analyzer）及Git blob字节比较，未调用模型、GPU、Nsight profile/export或科学analyzer执行。审计前后77文件与ZIP字节不变。提交只含收尾文档并保留此前7.17未提交进度；没有运行代码修改、原始产物或私有绝对路径。

**后续：Gate7收口无待用户补证/重跑事项。Gate8只记录为下一阶段待规划；需独立授权，不自动启动。**
