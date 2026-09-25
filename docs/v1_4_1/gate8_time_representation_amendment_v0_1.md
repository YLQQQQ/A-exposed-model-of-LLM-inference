# Gate8 时间表示 amendment v0.1

ID：`G8-TIME-REPRESENTATION/0.1.0`。用户明确批准，2026-09-25。
仅扩展时间**表示域**与文件兼容，不修改 Measurement Contract 正文、W(s)、A 分类/优先级/互斥守恒、B provenance 或 D/Signature 公式。历史 Gate6 PASS 不撤销，新版本资格不继承。

## 冲突及版本边界

Canonical Raw 0.2 的 `SIGNED_INT64`、`timestamp_normalization=DISABLED` 和 D1 的 trace-native point 要求保留原时间。冻结 A/B 0.2 却对 window/sync/terminal 时间戳设 `minimum=0`；旧 interval/B hidden-prefix 实现也假设非负域。这不能仅靠调用方改类型解决。

新增 [A/B 0.3](contracts/ab_schema_v0_3.json) 与 [Derived 0.3](contracts/derived_schema_v0_3.json)。旧 `ab_schema_v0_2.json`、`derived_schema_v0_2.json` 字节及默认读取规则保持。A/B 0.3 → Derived 0.3；0.2 → 0.2，未知版本、manifest/input version 不符均拒绝。禁止猜测版本或自动平移数据后冒充旧 schema。

## 数值域

- timestamp：整数 `[-9223372036854775808, 9223372036854775807]`；覆盖 window start/end、sync start/end、terminal end及活动端点。缺失值只在原 validity 允许 null 的字段保留 null，不能填0。bool/float不是整数时间。
- duration：A/B 的非负整数 `[0,18446744073709551615]`（uint64 表示域）。使用 Python 任意精度整数做减法/求和，再验证范围；不经 float、固定宽度有符号减法、取绝对值或截断。两合法 timestamp 的最大差恰好是 `2^64−1`，合法；超过此值或负duration拒绝。
- `end >= start`、半开区间保持；相等端点是零长度区间。D1 仍按其既有 point 顺序规则，不能以此放宽两个不同 completion point 的逆序/相等错误；单输出 token 的 decode 同一端点仍合法为空。
- B 的“sync 前”表示为合法时间域的下界至 sync start，即 signed 分支用 `INT64_MIN` 而非0。它等价于在有界 trace 域内取 `t < sync_start`，不改变 W(s)，不丢弃负时间 hidden progress。旧非负路径仍用0。
- D margin 是有符号差而非 duration，新字段域为 `[-(2^64−1),2^64−1]`；比例/统计公式不变。D2 调用加权聚合沿用其独立 schema 的任意精度非负 JSON integer，并非 A/B 单窗duration字段，不转为固定宽度或截断；调用累计仍不是request exposure。

## 实现选择与资格

`time_representation` 用 context-local 显式版本隔离；旧默认为0.2，文件 reader按明确manifest版本选择，作用域退出恢复。新 `analyze_ab(..., scope_manifest=...)` 选0.3并重读S文件、核验其来源和与相同projection重算的S记录一致；新 schema绑定scope/pass hash。Canonical、S原始clock与source引用不归一化。

新 A/B/Derived manifest 自带 `validation_role=LOCAL_DETERMINISTIC_ONLY`、`measurement_validity=NOT_ASSESSED`，Q0 NOT_RUN/Formal false。这些是防止把当前本地计算误读为资格的标签，不是科学validity通过。真实完整性provider尚未实现，Gate8编排入口保持阻塞。

验证：独立手算跨零 fixture 为 request `[-60,140)`、sync `[-20,10)`、activity `[-30,0)`；A Host/API/wait/residual/unattributed=`165/5/20/10/0 ns`；B hidden/exposed/terminal-pre/terminal-overlap/tail=`10/20/10/20/10 ns`；D margin=`−150 ns`、score=`−150/190`。测试覆盖全int64跨度、空窗、逆序、缺失、越界、schema/文件往返、未知版本/不兼容版本、旧默认拒绝负时间。

后续Q0须覆盖新表示下hidden/exposed/terminal、scope ownership/phase/device/event/correlation与完整性；23-case旧回归仅证明未破坏旧路径，不能代替新profile目标栈资格。无本轮Q0/GPU/Nsight执行。
