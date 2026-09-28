"""User-authorized conditional hypothesis, never a scope proof or formal exemption."""
ASSUMPTION='FOUR_OTHER_PROCESS_WARNINGS_NO_TARGET_IMPACT/0.1'
MESSAGES=frozenset((
    'Not all NVTX events might have been collected.',
    'No NVTX events collected. Does the process use NVTX?',
    'CUDA profiling might have not been started correctly.',
    'No CUDA events collected. Does the process use CUDA?',
))


def select_assumed_warnings(diagnostic, dispositions, assumption):
    if assumption!=ASSUMPTION:
        raise ValueError('WARNING_ASSUMPTION_VERSION')
    blocked={r['source_rowid'] for r in dispositions if r['disposition']!='INFORMATION_ONLY'}
    rows=[r for r in diagnostic['records'] if r['source_rowid'] in blocked]
    if (len(rows)!=4 or {r['text'] for r in rows}!=MESSAGES
            or len({r['global_pid'] for r in rows})!=1
            or any(r['process_relation']!='OTHER_PROCESS' or r['process_id'] is None
                   or r['severity_id']!=2 or r['source_id']!=3 or r['timestamp_type']!=2 for r in rows)):
        raise ValueError('WARNING_ASSUMPTION_OUT_OF_SCOPE')
    return dict(version=ASSUMPTION,scope_proven=False,records=rows,
        basis='USER_AUTHORIZED_HYPOTHESIS_NOT_VENDOR_EVIDENCE',
        source_sqlite_sha256=diagnostic['source_sqlite_sha256'])


def main():
    import argparse
    import json
    from pathlib import Path
    from .gate8_engineering_scope import process_conditional_scope
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('formal-result','input-receipt','execution-receipt','output-dir'):
        parser.add_argument('--'+name,required=True,type=Path)
    parser.add_argument('--assumption',required=True,choices=[ASSUMPTION])
    a=parser.parse_args()
    result=process_conditional_scope(a.formal_result,a.input_receipt,a.execution_receipt,a.output_dir,assumption=a.assumption)
    value=json.loads(result.read_text(encoding='utf-8'))
    print(value['status'])
    return 0 if value['status']=='CONDITIONAL_A_ONLY_NOT_ACCEPTED' else 1


if __name__=='__main__': raise SystemExit(main())
