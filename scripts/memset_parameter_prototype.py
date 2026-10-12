"""CPU-only parameter evidence spike. Not a collector, S/A adapter, or qualifier.

No model, torch, CUDA, CUPTI, process launch, or acquisition entry point.
Input records below are a prototype contract, not existing Nsight records.
"""
import json
from pathlib import Path

VERSION = 'memset-parameter-prototype/0.1.0'


def require(condition, reason):
    if not condition:
        raise ValueError('MEMSET_PROTOTYPE_' + reason)


def integer(value, low=0, high=2**64 - 1):
    return type(value) is int and low <= value <= high


def review_evidence(value):
    require(value.get('version') == VERSION, 'VERSION')
    require(value.get('role') == 'ENGINEERING_PARAMETER_FORENSICS', 'ROLE')
    require(value.get('source') == 'CPU_SYNTHETIC', 'SOURCE_NOT_TARGET_VALIDATED')
    require(value.get('dropped_records_status') == 'UNKNOWN', 'OBSERVED_LOSS')
    require(bool(value.get('clock_id')), 'CLOCK')
    identity = (value.get('run_id'), value.get('process_instance'))
    require(all(isinstance(x, str) and x for x in identity), 'IDENTITY_UNKNOWN')

    def same_run(record):
        require((record.get('run_id'), record.get('process_instance')) == identity, 'IDENTITY_CONFLICT')

    events = value['callback_events']
    require(bool(events), 'INCOMPLETE_CALLBACK')
    stacks, calls, complete, callback_ids = {}, {}, set(), set()
    previous_seq = -1
    for event in events:
        same_run(event)
        seq = event.get('seq')
        require(integer(seq) and seq > previous_seq, 'CALLBACK_ORDER')
        previous_seq = seq
        require(integer(event.get('thread_id')) and integer(event.get('context_uid')), 'IDENTITY_UNKNOWN')
        require(integer(event.get('correlation_id'), 0, 2**32-1), 'CALLBACK_IDENTITY')
        require(integer(event.get('time_ns'), -(2**63), 2**63-1), 'CLOCK')
        require(event.get('domain') in {'RUNTIME', 'DRIVER'}, 'UNSUPPORTED_DOMAIN')
        require(event.get('phase') in {'prefill', 'decode'} and bool(event.get('request_id')), 'SCOPE_UNKNOWN')
        key = event.get('call_id')
        require(isinstance(key, str) and bool(key), 'CALLBACK_IDENTITY')
        stack = stacks.setdefault(event['thread_id'], [])
        if event.get('site') == 'ENTER':
            require(key not in calls, 'CALLBACK_IDENTITY')
            # GPU effects have a domain/correlation, not a Host thread field.
            # A reused driver ID across threads cannot disambiguate an effect.
            correlation_key = (event['domain'], event['correlation_id'])
            require(correlation_key not in callback_ids, 'CORRELATION_REUSE')
            callback_ids.add(correlation_key)
            calls[key] = dict(entry=event, parent=stack[-1] if stack else None)
            if stack:
                parent = calls[stack[-1]]['entry']
                require(all(parent.get(f) == event.get(f) for f in
                            ['context_uid', 'request_id', 'phase']), 'CALLBACK_IDENTITY')
            stack.append(key)
        elif event.get('site') == 'EXIT':
            require(stack and stack[-1] == key and key not in complete, 'INCOMPLETE_CALLBACK')
            entry = calls[key]['entry']
            require(all(entry.get(f) == event.get(f) for f in
                        ['thread_id', 'context_uid', 'domain', 'correlation_id', 'name', 'request_id', 'phase']),
                    'CALLBACK_IDENTITY')
            require(entry['time_ns'] <= event['time_ns'], 'CLOCK')
            require(integer(event.get('return_code'), -(2**31), 2**31-1), 'RETURN_UNKNOWN')
            calls[key]['exit'] = event
            complete.add(key)
            stack.pop()
        else:
            require(False, 'CALLBACK_ORDER')
    require(all(not stack for stack in stacks.values()) and len(complete) == len(calls), 'INCOMPLETE_CALLBACK')

    api_index = {}
    for record in value['api_records']:
        same_run(record)
        key = (record.get('domain'), record.get('correlation_id'), record.get('thread_id'))
        require(key not in api_index and bool(record.get('record_id')), 'API_MAPPING')
        api_index[key] = record
    for call in calls.values():
        entry = call['entry']
        record = api_index.get((entry['domain'], entry['correlation_id'], entry['thread_id']))
        require(record is not None and all(record.get(f) == entry.get(f) for f in
                    ['context_uid', 'name', 'request_id', 'phase']), 'API_MAPPING')

    bindings = value['stream_bindings']
    effects = value['device_effects']
    effect_ids = set()
    for record in bindings + effects:
        same_run(record)
    for effect in effects:
        require(bool(effect.get('record_id')) and effect['record_id'] not in effect_ids, 'DEVICE_EFFECT_CONFLICT')
        effect_ids.add(effect['record_id'])
    results = []
    for key, call in calls.items():
        entry = call['entry']
        if entry['domain'] != 'RUNTIME':
            continue
        require(entry['name'] == 'cudaMemsetAsync', 'UNSUPPORTED_API')
        require(call['exit']['return_code'] == 0, 'API_FAILED')
        params = entry.get('params', {})
        require(integer(params.get('count')) and integer(params.get('stream_handle'))
                and integer(params.get('value'), -(2**31), 2**31-1)
                and isinstance(params.get('pointer_alias'), str) and bool(params['pointer_alias']), 'PARAMETERS_UNKNOWN')
        matches = [m for m in bindings if m.get('context_uid') == entry['context_uid']
                   and m.get('thread_id') == entry['thread_id']
                   and m.get('stream_handle') == params['stream_handle']
                   and m.get('source') == 'CUPTI_RESOURCE_QUERY'
                   and integer(m.get('start_ns'), -(2**63), 2**63-1)
                   and integer(m.get('end_ns'), -(2**63), 2**63-1)
                   and m['start_ns'] <= entry['time_ns'] <= call['exit']['time_ns'] <= m['end_ns']]
        require(len(matches) == 1, 'STREAM_MAPPING')
        stream = matches[0]
        require(integer(stream.get('stream_id')) and integer(stream.get('device_id')), 'STREAM_MAPPING')
        # Parentage comes from ordered entry/exit stacks, never adjacent times.
        descendants = []
        for child_key, child in calls.items():
            parent = child['parent']
            while parent is not None and parent != key:
                parent = calls[parent]['parent']
            if parent == key and child['entry']['domain'] == 'DRIVER':
                descendants.append(child_key)
        for child_key in descendants:
            require(calls[child_key]['exit']['return_code'] == 0, 'API_FAILED')
        driver_ids = {calls[k]['entry']['correlation_id'] for k in descendants}
        mapped = [e for e in effects if e.get('domain') == 'DRIVER' and e.get('correlation_id') in driver_ids]
        consistent = all(e.get('context_uid') == entry['context_uid']
                         and e.get('stream_id') == stream['stream_id']
                         and e.get('device_id') == stream['device_id']
                         and e.get('kind') == 'MEMSET' and integer(e.get('bytes'))
                         and e.get('timestamps_known') is True
                         and integer(e.get('start_ns')) and integer(e.get('end_ns'))
                         and (e['start_ns'], e['end_ns']) != (0, 0)
                         and e['end_ns'] >= e['start_ns'] for e in mapped)
        count = params['count']
        if count == 0:
            state = 'ZERO_LENGTH_EFFECT_CONFLICT' if mapped else 'ZERO_LENGTH_ARGUMENT_OBSERVED'
        elif not mapped:
            state = 'NONZERO_EFFECT_MISSING'
        elif not consistent or len(mapped) != 1 or mapped[0]['bytes'] != count:
            state = 'DEVICE_EFFECT_CONFLICT'
        else:
            state = 'NONZERO_DEVICE_EFFECT_MAPPED'
        results.append(dict(call_id=key, count=count, stream_handle=params['stream_handle'],
                            return_code=call['exit']['return_code'], state=state,
                            driver_call_ids=descendants, effect_record_ids=[e['record_id'] for e in mapped],
                            device_effect_completeness='NOT_PROVEN'))
    require(bool(results), 'INCOMPLETE_CALLBACK')
    return dict(version=VERSION, status='BLOCKED' if any(r['state'] in
                {'ZERO_LENGTH_EFFECT_CONFLICT', 'NONZERO_EFFECT_MISSING', 'DEVICE_EFFECT_CONFLICT'}
                for r in results) else 'PARAMETER_FACTS_ONLY_NOT_QUALIFICATION', calls=results,
                proof_scope='CPU_PROTOTYPE_NOT_TARGET_VALIDATION', a_admission='NOT_ASSESSED',
                dropped_records_status=value['dropped_records_status'])


def review_file(path):
    return review_evidence(json.loads(Path(path).read_text(encoding='utf-8')))
