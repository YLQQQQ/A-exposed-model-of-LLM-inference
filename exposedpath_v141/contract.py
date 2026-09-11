"""ExposedPath Measurement Contract 包的加载与一致性校验。"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


class ContractValidationError(ValueError):
    """Measurement Contract 包内部不一致。"""


_CONTRACT_RELATIVE_DIR = Path("docs") / "v1_4_1" / "contracts"
_CONTRACT_FILENAME = "measurement_contract_v0_2.json"
_REGISTRY_FILENAME = "sync_semantics_registry_v0_2.json"
_TEST_MAP_FILENAME = "measurement_contract_test_map_v0_2.json"

_A_CATEGORIES = {
    "A_host_path",
    "A_cuda_api",
    "A_device_wait",
    "A_sync_residual",
    "A_unattributed",
}
_SUPPORTED_SYNC_CLASS = "SUPPORTED_PHYSICAL_BLOCKING_SYNC"
_PLACEHOLDERS = ("todo", "tbd", "待定")
_VALIDITY_STATES = {"VALID_NONEMPTY", "VALID_EMPTY", "AMBIGUOUS", "INVALID"}


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractValidationError(f"{label} 必须是对象")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ContractValidationError(f"{label} 必须是数组")
    return value


def _require_nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractValidationError(f"{label} 必须是非空字符串")
    return value


def _ensure_unique(values: Sequence[str], label: str) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    if duplicates:
        joined = ", ".join(sorted(duplicates))
        raise ContractValidationError(f"{label} 重复: {joined}")


def _scan_placeholders(value: Any, path: str = "root") -> None:
    if isinstance(value, str):
        lowered = value.casefold()
        if any(token in lowered for token in _PLACEHOLDERS):
            raise ContractValidationError(f"发现占位文本: {path}")
        return
    if isinstance(value, Mapping):
        for key, child in value.items():
            _scan_placeholders(child, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            _scan_placeholders(child, f"{path}[{index}]")


def validate_contract_bundle(
    contract: Mapping[str, Any],
    registry: Mapping[str, Any],
    test_map: Mapping[str, Any],
) -> None:
    """验证合同、同步 registry 与测试映射之间的机器不变量。"""

    contract = _require_mapping(contract, "contract")
    registry = _require_mapping(registry, "registry")
    test_map = _require_mapping(test_map, "test_map")

    contract_version = _require_nonempty_string(
        contract.get("contract_version"), "contract.contract_version"
    )
    registry_version = _require_nonempty_string(
        registry.get("registry_version"), "registry.registry_version"
    )
    test_map_version = _require_nonempty_string(
        test_map.get("test_map_version"), "test_map.test_map_version"
    )
    if registry.get("contract_version") != contract_version:
        raise ContractValidationError("registry 与 contract 的版本绑定不一致")
    if test_map.get("contract_version") != contract_version:
        raise ContractValidationError("test_map 与 contract 的版本绑定不一致")
    if contract.get("registry_version") != registry_version:
        raise ContractValidationError("contract 引用的 registry 版本不一致")
    if contract.get("test_map_version") != test_map_version:
        raise ContractValidationError("contract 引用的 test_map 版本不一致")

    time_model = contract.get("time_model")
    if time_model is not None:
        time_model = _require_mapping(time_model, "contract.time_model")
        if (
            time_model.get("semantic_ordering_tolerance_ns") != 0
            or time_model.get("terminal_tie_tolerance_ns") != 0
        ):
            raise ContractValidationError("语义时间容差必须保持为 0 ns")

    s_layer = contract.get("s_layer")
    if s_layer is not None:
        s_layer = _require_mapping(s_layer, "contract.s_layer")
        validity = _require_mapping(s_layer.get("validity"), "contract.s_layer.validity")
        states = _require_list(validity.get("states"), "contract.s_layer.validity.states")
        if set(states) != _VALIDITY_STATES or len(states) != len(_VALIDITY_STATES):
            raise ContractValidationError("S 层 validity 状态必须恰好包含四个冻结状态")
        reason_priority = _require_list(
            s_layer.get("reason_priority"), "contract.s_layer.reason_priority"
        )
        ranks = [
            _require_mapping(item, "reason priority item").get("rank")
            for item in reason_priority
        ]
        if len(ranks) != len(set(ranks)):
            raise ContractValidationError("reason priority 的 rank 不得重复")

    rules = _require_list(contract.get("rules"), "contract.rules")
    rule_ids = [
        _require_nonempty_string(
            _require_mapping(rule, f"contract.rules[{index}]").get("rule_id"),
            f"contract.rules[{index}].rule_id",
        )
        for index, rule in enumerate(rules)
    ]
    _ensure_unique(rule_ids, "重复规则 ID")

    cases = _require_list(test_map.get("cases"), "test_map.cases")
    case_ids: list[str] = []
    referenced_rule_ids: set[str] = set()
    for index, case_value in enumerate(cases):
        case = _require_mapping(case_value, f"test_map.cases[{index}]")
        case_ids.append(
            _require_nonempty_string(case.get("case_id"), f"test_map.cases[{index}].case_id")
        )
        for rule_id in _require_list(
            case.get("rule_ids"), f"test_map.cases[{index}].rule_ids"
        ):
            referenced_rule_ids.add(_require_nonempty_string(rule_id, "case.rule_id"))
    _ensure_unique(case_ids, "验证案例 ID")

    unknown_rule_ids = referenced_rule_ids - set(rule_ids)
    if unknown_rule_ids:
        joined = ", ".join(sorted(unknown_rule_ids))
        raise ContractValidationError(f"测试映射引用不存在的合同规则: {joined}")
    unmapped_rule_ids = set(rule_ids) - referenced_rule_ids
    if unmapped_rule_ids:
        joined = ", ".join(sorted(unmapped_rule_ids))
        raise ContractValidationError(f"合同规则没有验证案例: {joined}")

    registry_rules = _require_list(registry.get("rules"), "registry.rules")
    registry_rule_ids: list[str] = []
    aliases: list[str] = []
    for index, rule_value in enumerate(registry_rules):
        rule = _require_mapping(rule_value, f"registry.rules[{index}]")
        registry_rule_ids.append(
            _require_nonempty_string(
                rule.get("registry_rule_id"),
                f"registry.rules[{index}].registry_rule_id",
            )
        )
        rule_aliases = _require_list(
            rule.get("aliases"), f"registry.rules[{index}].aliases"
        )
        aliases.extend(_require_nonempty_string(alias, "API alias") for alias in rule_aliases)
        if rule.get("universe_class") == _SUPPORTED_SYNC_CLASS:
            _require_nonempty_string(
                rule.get("completion_scope"),
                f"registry.rules[{index}].completion_scope",
            )
            evidence = _require_list(
                rule.get("required_evidence"),
                f"registry.rules[{index}].required_evidence",
            )
            if not evidence:
                raise ContractValidationError(
                    f"supported sync 缺少必需证据: {registry_rule_ids[-1]}"
                )
    _ensure_unique(registry_rule_ids, "registry rule ID")
    _ensure_unique(aliases, "API alias")

    a_layer = _require_mapping(contract.get("a_layer"), "contract.a_layer")
    categories = _require_list(
        a_layer.get("top_level_categories"), "contract.a_layer.top_level_categories"
    )
    priority = _require_list(a_layer.get("priority"), "contract.a_layer.priority")
    if set(categories) != _A_CATEGORIES or len(categories) != len(_A_CATEGORIES):
        raise ContractValidationError("A 层顶层类别必须恰好包含五个冻结类别")
    if set(priority) != _A_CATEGORIES or len(priority) != len(_A_CATEGORIES):
        raise ContractValidationError("A 层优先级必须恰好覆盖每个顶层类别一次")

    b_layer = _require_mapping(contract.get("b_layer"), "contract.b_layer")
    _require_list(b_layer.get("output_fields"), "contract.b_layer.output_fields")
    if b_layer.get("aggregation_policy") != "NO_CROSS_SYNC_SUM":
        raise ContractValidationError("B 层不得启用跨同步求和")
    if b_layer.get("enters_a_wall_clock_budget") is not False:
        raise ContractValidationError("B 层不得进入 A 的墙钟预算")

    derived = _require_mapping(contract.get("derived"), "contract.derived")
    for name, definition_value in derived.items():
        definition = _require_mapping(definition_value, f"contract.derived.{name}")
        inputs = _require_list(definition.get("inputs"), f"contract.derived.{name}.inputs")
        forbidden = [
            field
            for field in inputs
            if not isinstance(field, str)
            or not (field.startswith("A_") or field.startswith("b."))
        ]
        if forbidden:
            raise ContractValidationError(
                f"派生量 {name} 只能读取 A/B 字段: {forbidden}"
            )

    _scan_placeholders(contract, "contract")
    _scan_placeholders(registry, "registry")
    _scan_placeholders(test_map, "test_map")


def load_contract_bundle(root: Path | None = None) -> dict[str, Any]:
    """读取仓库内默认合同包，校验后返回三个 JSON 对象。"""

    repository_root = root if root is not None else Path(__file__).resolve().parents[1]
    contract_dir = repository_root / _CONTRACT_RELATIVE_DIR

    def read_json(filename: str) -> dict[str, Any]:
        path = contract_dir / filename
        try:
            with path.open("r", encoding="utf-8") as handle:
                value = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise ContractValidationError(f"无法读取合同文件 {path}: {exc}") from exc
        if not isinstance(value, dict):
            raise ContractValidationError(f"合同文件顶层必须是对象: {path}")
        return value

    contract = read_json(_CONTRACT_FILENAME)
    registry = read_json(_REGISTRY_FILENAME)
    test_map = read_json(_TEST_MAP_FILENAME)
    validate_contract_bundle(contract, registry, test_map)
    return {"contract": contract, "registry": registry, "test_map": test_map}
