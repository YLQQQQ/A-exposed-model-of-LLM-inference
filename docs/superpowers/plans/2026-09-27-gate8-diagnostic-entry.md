# Gate8 单次诊断入口实现计划

> 执行方式：本窗口按 executing-plans 内联实施；不新建worktree。先失败测试，再实现。

目标：既有producer真实文件入口的单次NOT_QUALIFIED诊断封装；不是科学验收入口。
设计依据：[七源收口](../../v1_4_1/gate8_qwen_source_review_v0_1.md)。
架构：独立诊断模块验证新manifest/preflight/prompt并调用run_gate8_requests_to_files；保持runner同步语义，使用stage/drain记录；外层单次限时profile与已有export工具分离。

- [ ] 新增tests/test_gate8_diagnostic_entry.py：CPU doubles经真实producer，断言warmup1/request1、三个completion记录、stage/drain实物、始终NOT_QUALIFIED；错误身份/32token约束/已有输出在模型前拒绝，运行失败保留且无重试。
- [ ] 新增exposedpath/gate8_diagnostic.py：固定32/2/batch1配置，显式manifest/preflight/model/prompt/output参数；复用pre-model验证，写独立诊断报告，不调用A/B/D。未知backend不默认sdpa。
- [ ] 补实际attention/cache观测最小接口及测试（仅若现有producer不能承载），不切换backend/stream、不新增同步。
- [ ] 定向及CPU全量、compileall/contract/canonical/oracle/diff检查；只读审查后固定commit并推送。
- [ ] 生成增量包和服务器单次限时草案：新目录、不自动retry、不覆盖；先静态复验，由协调窗口审查和用户执行。BUGCHECK历史明确提示。

所有模型/GPU/Nsight仅用户另行执行，本窗口不执行。来源UNKNOWN不阻断诊断采集，但阻断合格A/B/D发布。Gate7 PASS、新Q0/Gate8 NOT_RUN。

完成记录：前四项本地实现/测试/审查已完成；定向71、全量1410 passed/5 skipped，静态合同/Canonical/oracle通过。第五项双脚本草案已AST检查，增量包随固定提交生成；服务器操作仍未执行。配置观察记录的是模型config，不宣称真实native backend/cache runtime资格；不为诊断扩展observer。
