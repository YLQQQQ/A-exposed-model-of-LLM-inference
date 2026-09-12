# Gate 5 Task 3 报告：共享半开区间工具

## 状态

- 任务：实现共享整数半开区间原语
- 研究阶段：Engineering / Pre-Pilot
- Gate 5：`NOT_RUN`
- Measurement Contract、A/B schema 与 Protocol Freeze：未改变
- 数据资格：未产生任何实验数据；不涉及 Q0、Pilot 或 Formal 资格

## 改动范围

- `exposedpath_v141/intervals.py`：新增纯整数、非负时间、半开区间的交、裁剪、union、union 长度和原子切分。
- `tests/test_v141_intervals.py`：新增 16 个确定性边界测试，覆盖相交、相邻/嵌套/重复/重叠 union、裁剪、空区间、类型与时间边界拒绝、原子切分及 union 长度。
- `docs/v1_4_1/research_progress.md`：记录 Task 3 已完成、A 记账仍未开始，并保持 Gate 5 `NOT_RUN`。

模块只依赖 Python 标准库，不包含 sync、A、B、CUDA、phase 或 Nsight 语义；区间长度按排序后的 union 直接求和，不枚举时间点。裁剪保留每个输入记录的交集，union 负责重叠与相邻合并；所有输出排序确定，空区间不产出正长度片段。

## TDD 证据

### RED

先写测试并运行：

```text
python -m pytest -q -p no:cacheprovider tests/test_v141_intervals.py
```

结果为收集错误：

```text
ModuleNotFoundError: No module named 'exposedpath_v141.intervals'
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
```

失败原因是目标生产模块尚不存在，符合预期的缺实现 RED。

### GREEN

实现最小模块后运行：

```text
python -m pytest -q -p no:cacheprovider tests/test_v141_intervals.py
```

结果：`16 passed`。

附加语法检查：

```text
python -m compileall exposedpath_v141
```

结果：成功完成，无错误。

## 全量回归

运行 `python -m pytest -q -p no:cacheprovider`：`447 passed, 2 failed`。两项失败为既有 PowerShell smoke 基线失败：

- `tests/test_server_smoke_script.py::test_dry_run`
- `tests/test_server_smoke_script.py::test_spaces`

本任务未修改 runner、benchmark 或该 smoke 脚本；区间定向测试和编译检查均通过。

## 未解决事项与下一步

本任务不实现 A/B 记账或任何研究分类；`EP-G5-02` 仍需在后续任务中基于这些原语实现 A 的原子片段优先级、守恒和 invalid 传播。Gate 5 不能因本任务通过而判定 `PASS`，真实 Q0 仍未运行且当前无 GPU。
