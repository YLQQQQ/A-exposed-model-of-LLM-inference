# ExposedPath v1.4.1

研究异步 LLM 推理中的 request-visible Host–device exposure。
方法链：Raw → Canonical → S → A/B → D / Exposure Signature。
Activity cost 不等于请求可见延迟贡献。

**Gate0–7 PASS；Gate8 NOT_RUN、待独立规划与授权。** Gate7 仅通过 Windows/RTX4090 Engineering integration；legacy-only、A结构验证、coverage unknown 与 measurement validity NOT_ASSESSED 限制保留。

## 唯一入口

- [科研进度与下一步](docs/v1_4_1/research_progress.md)（唯一进度事实源）
- [研究设计与实验协议](docs/current/)、[领域模型](CONTEXT.md)、[协作规范](AGENTS.md)
- [Measurement Contract](docs/v1_4_1/measurement_contract_v0_2.md)
- [Gate6 closeout](docs/v1_4_1/gate6_closeout_v0_1.md)、[Gate7 closeout](docs/v1_4_1/gate7_closeout_v0_1.md)
- [目录、部署与证据保留约定](docs/repository_layout.md)

日常只在本仓库根目录 `main` 工作。临时 worktree 必须有明确隔离理由，完成后整合移除；不按 Gate 复制仓库。机器绝对路径与私有交接仅存于忽略的 `.local/`、`AI_HANDOFF.md`。

## 代码职责

| 目录 | 职责 |
|---|---|
| `exposedpath/` | runner、manifest、执行身份、completion/parity |
| `exposedpath_v141/` | Canonical/S/A/B/D、Q0评估；不是legacy analyzer别名 |
| `analysis/` | legacy 工程分析及诊断 |
| `q0/` | 受控微程序与独立oracle |
| `scripts/` | 平台adapter、启动与只读validation |
| `tests/` | CPU/合成回归、显式工具链检查 |
| `docs/` | 当前合同、计划、closeout及标注的历史资料 |

Gate7执行commit为 `8d64f7580d43d7c8e1cb7a416b459cec8f60b011`，收尾文档commit为 `16604d59b05ee6d7e8415f75dbaaa1be3be7cf8a`；后续目录整理commit不是实验执行身份。

## 非实验验证

使用已确认的 Python 解释器执行（不要依赖服务器 PATH 的默认 Python）：

```text
python -m compileall -q exposedpath analysis exposedpath_v141 scripts
python -m pytest -q -p no:cacheprovider
python -m exposedpath_v141 validate-contract
python scripts/verify_canonical_raw_boundary.py
python scripts/verify_q0_oracle_independence.py
```

pytest 在存在 nvcc 时包含无GPU编译检查；CPU-only环境不暴露CUDA工具链时相关测试按原有规则skip，必须如实报告。上列静态检查不授权模型/GPU/Nsight或任何后续Gate。

旧版 [v3 README](docs/prototype_archive/README_v3_pilot.md)、根目录其他 `README_*`、`dist/`、`SERVER_SYNC_MANIFEST.json` 仅为历史 Prototype/部署资料，不是当前部署入口。原始 trace、模型、服务器日志包与本机配置不进入Git。
