"""PowerShell entry safety only; not a server deployment or CUDA test."""
from pathlib import Path
import shutil
import subprocess
import pytest

SCRIPT=Path(__file__).resolve().parents[1]/'scripts/gate8_pair_server.ps1'

@pytest.mark.parametrize('stage',['Static','Pair'])
def test_delivery_never_executes_without_stage_authorization(stage):
    assert SCRIPT.is_file(), 'missing reviewed two-stage delivery'
    shell=shutil.which('powershell.exe') or shutil.which('pwsh')
    if not shell: pytest.skip('PowerShell unavailable; no server compatibility claim')
    result=subprocess.run([shell,'-NoProfile','-File',str(SCRIPT),'-Stage',stage],capture_output=True,timeout=20)
    assert result.returncode!=0
    assert b'STAGE_AUTHORIZATION_REQUIRED' in result.stdout+result.stderr


def test_pair_stage_stops_on_cpu_failure_before_creating_model_output(tmp_path):
    import json
    shell=shutil.which('powershell.exe') or shutil.which('pwsh')
    if not shell: pytest.skip('PowerShell unavailable')
    target='a'*40
    batch=tmp_path/'evidence/gate8'/('pair_'+target[:12]+'_delivery1')
    static=batch/'static'; static.mkdir(parents=True)
    (static/'receipt.json').write_text(json.dumps(dict(status='BLOCKED',commit=target)))
    result=subprocess.run([shell,'-NoProfile','-File',str(SCRIPT),'-Stage','Pair',
        '-PairAuthorizedAfterCpuReview','-Target',target,'-ServerRoot',str(tmp_path),
        '-CodeRoot',str(tmp_path/'not-a-repo')],capture_output=True,timeout=20)
    assert result.returncode!=0
    assert b'CPU receipt not accepted' in result.stdout+result.stderr
    assert not (batch/'pair').exists()
