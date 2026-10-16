"""Reuse a pinned historical static report, not its BLOCKED readiness verdict."""
import argparse
import hashlib
import json
from pathlib import Path,PurePosixPath
import sys
import zipfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from scripts import coe_storage_binding as old


def require(ok,reason):
    if not ok:raise ValueError(reason)


def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def safe(root,relative):
    part=PurePosixPath(relative)
    require(not part.is_absolute() and '..' not in part.parts and ':' not in relative and '\\' not in relative,'REFERENCE_PATH')
    p=Path(root)/relative
    # The shared reader refuses reparse ancestors and missing files.
    old._read_file(p,'REFERENCE_MISSING:'+relative)
    return p


def verify(config,package,current_sources):
    archive=safe(package,config['reuse_static_archive'])
    old._static_reference(archive) # fixed ZIP/CRC/manifest/receipt/launcher references
    with zipfile.ZipFile(archive) as z:
        source=json.loads(z.read('source_bytes.json').decode('utf-8-sig'))
        original=ET.fromstring(z.read('cpu_results.xml'))
        previous_delivery=json.loads(z.read('delivery.json').decode('utf-8-sig'))
    require(all(config.get(k)==previous_delivery.get(k) for k in
        ('inventory_sha256','prompt_512_sha256','plan_sha256','analysis_contract_sha256',
         'gpu_uuid','gpu_pci_bus_id','target_python','site_root','model')),'REUSED_EXECUTION_CONTRACT_CONFLICT')
    suites=original.findall('testsuite') if original.tag!='testsuite' else [original]
    require(sum(int(s.attrib['tests']) for s in suites)==110 and all(int(s.attrib.get(k,0))==0 for s in suites for k in ('failures','errors','skipped')),'HISTORICAL_CPU_RECEIPT')
    receipt_path=Path(config['server_root'])/'logs/coe_4f1c3b55caf3_static/receipt.json'
    data=old._read_file(receipt_path,'OLD_RECEIPT_MISSING')
    require(hashlib.sha256(data).hexdigest()==old.RECEIPT_SHA,'OLD_RECEIPT_CHANGED')
    proof_path=safe(package,config['component_compatibility'])
    require(sha(proof_path)==config['component_compatibility_sha256'],'COMPATIBILITY_HASH')
    proof=read(proof_path)
    require(proof.get('schema_version')=='coe-component-reuse/0.1.0' and proof.get('baseline_commit')==old.EXPECTED_COMMIT
        and proof.get('execution_commit')==config['commit']==config['analysis_commit']==proof.get('analysis_commit'),'COMPATIBILITY_TARGET')
    previous={r['path']:r for r in source}
    require(len(previous)==len(source)==311 and set(proof['unchanged_sources'])==set(previous),'COMPATIBILITY_SCOPE')
    table={r['path']:r for r in current_sources}
    require(len(table)==len(current_sources) and set(table)==set(config['source_representations']),'CURRENT_SOURCE_CATALOG')
    for path,row in previous.items():
        forms=proof['unchanged_sources'][path]
        require(forms==row['expected'],'COMPATIBILITY_REFERENCE')
        actual=table.get(path,{})
        require(actual.get('matched') is True and any(actual.get('actual_bytes')==f['bytes'] and actual.get('actual_sha256')==f['sha256'] for f in forms),'REUSED_COMPONENT_CONFLICT')
    operational=proof['allowed_operational_changes']
    require(len(operational)==len(set(operational)) and {'scripts/run_coe_candidate_pilot.ps1','scripts/coe_startup_storage.py','scripts/coe_delivery_reuse.py'}<=set(operational),'OPERATIONAL_SCOPE')
    for path in operational:
        require(path not in previous,'CHANGED_REUSED_COMPONENT')
        forms=config['source_representations'].get(path,[]);actual=table.get(path,{})
        require(len(forms)==1 and actual.get('matched') is True and actual.get('actual_bytes')==forms[0]['bytes'] and actual.get('actual_sha256')==forms[0]['sha256'],'NEW_OPERATIONAL_SOURCE_CONFLICT')
    return dict(schema_version='coe-component-reuse-receipt/0.1.0',status='COMPONENT_REUSE_VERIFIED',
        baseline_commit=old.EXPECTED_COMMIT,execution_commit=config['commit'],analysis_commit=config['analysis_commit'],
        reference_archive_sha256=old.ARCHIVE_SHA,reference_manifest_sha256=old.MANIFEST_SHA,
        original_receipt_sha256=old.RECEIPT_SHA,historical_static_status='BLOCKED_UNCHANGED',
        reused_cpu_count=110,reused_compile=True,reused_actual_python311_helper=True,
        unchanged_source_count=311,component_compatibility_sha256=sha(proof_path),
        current_source_catalog='LAUNCHER_ACTUAL_BYTE_CHECKS_AGAINST_NEW_DELIVERY_REPRESENTATIONS',
        new_operational_paths=operational,new_launcher_equals_old_executed_required=False,
        collection_authorized=False)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--delivery',type=Path,required=True);p.add_argument('--sources',type=Path,required=True)
    p.add_argument('--receipt',type=Path,required=True)
    a=p.parse_args(argv);v=verify(read(a.delivery),a.delivery.parent,read(a.sources))
    with a.receipt.open('x',encoding='utf8') as f:json.dump(v,f,indent=2)
    print(v['status'],flush=True);return 0


if __name__=='__main__':raise SystemExit(main())
