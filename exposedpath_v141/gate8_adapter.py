"""Gate8 SQLite identity adapter, isolated from the frozen Q0 adapter path."""
from copy import deepcopy
import hashlib
import json
import re

from exposedpath.gate8_identity import (
    ADAPTER_VERSION, IDENTITY_FIELDS, PASS_FIELDS, PROFILE,
    validate_pass_identity, validate_shape,
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_uuid(value):
    if not isinstance(value, str):
        raise ValueError("DEVICE_MAPPING_UNPROVEN: missing UUID")
    value = value.lower().removeprefix("gpu-")
    if re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", value) is None:
        raise ValueError("DEVICE_MAPPING_UNPROVEN: malformed UUID")
    return value


def normalized_pci(value):
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-fA-F]{4,8}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-7]", value) is None:
        raise ValueError("DEVICE_MAPPING_UNPROVEN: malformed PCI")
    domain, bus, slot = value.split(":")
    device, function = slot.split(".")
    d, b, s, f = (int(x, 16) for x in (domain, bus, device, function))
    if d > 65535 or b > 255 or s > 31:
        raise ValueError("DEVICE_MAPPING_UNPROVEN: PCI out of range")
    return f"{d:04x}:{b:02x}:{s:02x}.{f}"


def _rows(connection, table):
    try:
        return [dict(r) for r in connection.execute(f'SELECT rowid AS source_rowid,* FROM "{table}"')]
    except Exception as exc:
        raise ValueError(f"DEVICE_MAPPING_UNPROVEN: required {table}: {exc}") from exc


def resolve_device_mapping(connection, *, sqlite_sha256, preflight, probe, pid,
                           preflight_sha256, probe_sha256, records):
    """Join four namespaces by affirmative UUID/PCI/process/context evidence."""
    try:
        physical = preflight["gpu_index_physical"]
        logical = probe["gpu_index_logical"]
        if type(physical) is not int or physical < 0 or type(logical) is not int or logical < 0:
            raise ValueError("invalid ordinal")
        mask = preflight["cuda_visible_devices"]
        if (preflight["cuda_device_order"] != "PCI_BUS_ID"
                or probe["cuda_device_order"] != "PCI_BUS_ID"
                or probe["cuda_visible_devices"] != mask or probe["pid"] != pid):
            raise ValueError("probe process/mask/order mismatch")
        masked = mask.split(",")
        if any(not x.isdecimal() for x in masked) or len(set(masked)) != len(masked):
            raise ValueError("ambiguous physical-index mask")
        if logical >= len(masked) or int(masked[logical]) != physical:
            raise ValueError("logical probe does not resolve masked physical ordinal")
        uuid = normalized_uuid(preflight["gpu_uuid"])
        pci = normalized_pci(preflight["pci_bus_id"])
        if normalized_uuid(probe["gpu_uuid"]) != uuid or normalized_pci(probe["pci_bus_id"]) != pci:
            raise ValueError("physical/logical hardware mismatch")
        cuda = [r for r in _rows(connection, "TARGET_INFO_CUDA_DEVICE")
                if r["pid"] == pid and normalized_uuid(r["uuid"]) == uuid]
        if len(cuda) != 1:
            raise ValueError("CUDA device absent/ambiguous")
        cuda = cuda[0]
        inventory = [r for r in _rows(connection, "TARGET_INFO_GPU") if r["id"] == cuda["gpuId"]]
        if len(inventory) != 1:
            raise ValueError("inventory join absent/ambiguous")
        inventory = inventory[0]
        if normalized_uuid(inventory["uuid"]) != uuid or normalized_pci(inventory["busLocation"]) != pci:
            raise ValueError("inventory hardware mismatch")
        trace_device = cuda["cudaId"]
        contexts = [r for r in _rows(connection, "TARGET_INFO_CUDA_CONTEXT_INFO") if r["processId"] == pid]
        if not contexts or any(r["deviceId"] != trace_device for r in contexts):
            raise ValueError("context device mapping missing/conflicting")
        ids = [r["contextId"] for r in contexts]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate context mapping")
        for kind in ("device_activity", "cuda_sync", "cuda_event"):
            for record in records[kind]:
                if record.get("process_id") is None and (
                    record.get("device_id") == trace_device or record.get("context_id") in ids
                ):
                    raise ValueError("activity/sync process mapping missing")
                if record.get("process_id") == pid and (
                    record.get("device_id") != trace_device or record.get("context_id") not in ids
                ):
                    raise ValueError("activity/sync context/device conflict")

        def ref(table, row):
            return {"source_sqlite_sha256": sqlite_sha256,
                    "record_id": f"gate8:{table}:{row['source_rowid']}",
                    "source_table": table, "source_rowid": row["source_rowid"]}

        mapping = {
            "schema_version": "exposedpath-device-mapping/0.1.0",
            "source_sqlite_sha256": sqlite_sha256, "pid": pid,
            "gpu_index": physical, "gpu_index_physical": physical,
            "gpu_index_logical": logical, "trace_device_id": trace_device,
            "nsys_inventory_gpu_id": cuda["gpuId"], "gpu_uuid": uuid, "pci_bus_id": pci,
            "cuda_device_order": "PCI_BUS_ID", "cuda_visible_devices": mask,
            "preflight_ref": {"sha256": preflight_sha256, "selector": "$"},
            "cuda_probe_ref": {"sha256": probe_sha256, "selector": "$"},
            "cuda_device_ref": ref("TARGET_INFO_CUDA_DEVICE", cuda),
            "inventory_ref": ref("TARGET_INFO_GPU", inventory),
            "context_refs": [ref("TARGET_INFO_CUDA_CONTEXT_INFO", r) for r in contexts],
        }
        validate_shape("device_mapping", mapping)
        return mapping
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"DEVICE_MAPPING_UNPROVEN: {exc}") from exc


def prepare_identity(connection, records, sources, sqlite_sha256, raw_sha256, staging):
    if set(sources) != {"pass_identity", "preflight", "cuda_probe"}:
        raise ValueError("IDENTITY_CONFLICT: explicit Gate8 source set required")
    ledger, preflight, probe = [json.loads(sources[k].read_text(encoding="utf-8"))
                              for k in ("pass_identity", "preflight", "cuda_probe")]
    validate_pass_identity(ledger)
    from exposedpath.formal_protocol import reference
    formal_ref=reference(ledger['formal']) if ledger['run_role']=='FORMAL' else None
    if ledger["pass_id"] != "pass1" or not isinstance(raw_sha256, str) or not re.fullmatch("[0-9a-fA-F]{64}", raw_sha256):
        raise ValueError("IDENTITY_CONFLICT: Canonical requires pass1 and Raw hash")
    requests = {r["identity"]["request_id"]: r["identity"] for r in ledger["requests"]}
    for row in records["nvtx"]:
        identity = row["structured_identity"]
        if identity is None:
            if row["text"].startswith("EXPOSEDPATH_JSON_V1:"):
                raise ValueError("IDENTITY_CONFLICT: malformed structured marker")
            continue
        expected = requests.get(identity.get("request_id"))
        # Older sync payloads omit data_role; run_role is still required.
        if expected is None or any(identity.get(k) != expected[k] for k in IDENTITY_FIELDS if k != "data_role"):
            raise ValueError("IDENTITY_CONFLICT: NVTX request/pass/attempt")
        if "data_role" in identity and identity["data_role"] != expected["data_role"]:
            raise ValueError("IDENTITY_CONFLICT: NVTX data_role")
        if formal_ref is not None and identity.get('formal_reference')!=formal_ref:
            raise ValueError('IDENTITY_CONFLICT: Formal NVTX protocol')
        if row["process_id"] != ledger["pid"]:
            raise ValueError("IDENTITY_CONFLICT: NVTX process")
    mapping = resolve_device_mapping(
        connection, sqlite_sha256=sqlite_sha256, preflight=preflight, probe=probe,
        pid=ledger["pid"], preflight_sha256=digest(sources["preflight"]),
        probe_sha256=digest(sources["cuda_probe"]), records=records,
    )

    def write(name, document):
        path = staging / name
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(document, handle, sort_keys=True, indent=2)
            handle.write("\n")
        return {"filename": name, "sha256": digest(path)}

    mapping_ref = write("gate8_device_mapping.json", mapping)
    final = deepcopy(ledger)
    if ledger["raw_artifact_sha256"] not in (None, raw_sha256.lower()) or ledger["device_mapping_sha256"] not in (None, mapping_ref["sha256"]):
        raise ValueError("SOURCE_HASH_MISMATCH: finalized pass lineage")
    final.update(raw_artifact_sha256=raw_sha256.lower(), device_mapping_sha256=mapping_ref["sha256"])
    validate_pass_identity(final, finalized=True)
    pass_ref = write("gate8_pass_identity.json", final)
    return {
        "observation_profile": PROFILE, "gate8_adapter_version": ADAPTER_VERSION,
        "gate8_sources": {"pass_identity": pass_ref, "device_mapping": mapping_ref,
                          "producer_pass_sha256": digest(sources["pass_identity"])},
        "identity": {"status": "VALID", "values": {k: final[k] for k in PASS_FIELDS},
                     "requests": final["requests"], "missing_fields": [],
                     "filename_inference_used": False, "nvtx_status": "VALID", "issues": []},
        "selected_device_id": mapping["trace_device_id"],
        **({'formal_reference':formal_ref} if formal_ref is not None else {}),
    }
