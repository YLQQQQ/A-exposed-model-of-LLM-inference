# ExposedPath 旧 Prototype 封存说明

## 封存结论

- 数据角色：`Prototype`。
- 研究目标版本：ExposedPath v1.4.1。
- 原型基准标签：`prototype-windows-v0.1`，对应提交 `abab013c5483109007ab5a2a232438d46bbaf02b`。
- Raw 完整性清单：见 `raw_trace_manifest_v1.json`。
- 封存完整性 Gate：`PASS`。原始报告已通过文件大小与 SHA-256 固定身份，并且没有被导出或分析过程覆盖。
- Q0：`NOT_RUN`。这些历史报告不能充当 v1.4.1 方法正确性证据。

## 已验证环境事实

- 三份 `.nsys-rep` 均报告采集器版本为 `2025.6.3.541-256337736014v0`。
- 报告内 GPU 信息为 NVIDIA GeForce RTX 4090。
- NVIDIA Nsight Systems `2026.1.1.204-261137176666v0` 能读取报告；`w01_p128_b1_o16.nsys-rep` 已成功只读导出为临时 SQLite。
- 采集器版本与导出器版本必须分别记录，不能把导出器版本误写成采集环境版本。

## 可复现的软件基线

- `python -m compileall exposedpath analysis`：通过。
- `python -m pytest -q -p no:cacheprovider`：218 项通过，2 项失败。
- 既有失败：`tests/test_server_smoke_script.py::test_dry_run`、`tests/test_server_smoke_script.py::test_spaces`。
- 上述失败属于封存时的历史基线；后续新版实现不得把新增失败混入这两个既有失败。

## 使用限制

1. 这些报告只用于旧实现回归、Canonical Raw/observation contract 调试和 Engineering 阶段验证。
2. 旧 analyzer 的同步依赖、wait-set、terminal、validity 和 A/B 语义不等同于 v1.4.1。
3. 文件名中的 workload 信息不能替代 manifest、request/repeat identity 或完整环境记录。
4. Raw 报告必须保持不可变。SQLite、表清单、Canonical Raw 和 analyzer 结果必须写入独立的版本化派生目录。
5. 没有独立 CUDA oracle 的离线测试不能将 Q0 状态改为 `PASS`。
