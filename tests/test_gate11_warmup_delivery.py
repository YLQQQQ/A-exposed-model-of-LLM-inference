"""Delivery/control review only. No deployment or model execution."""
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/run_gate11_warmup.ps1'


def test_powershell51_parser_and_closed_optin():
    result=subprocess.run(['powershell.exe','-NoProfile','-Command',
        "$e=$null;$t=$null;[System.Management.Automation.Language.Parser]::ParseFile('"+str(SCRIPT).replace("'","''")+
        "',[ref]$t,[ref]$e)>$null; if($e.Count){$e|Out-String|Write-Output;exit 1}"],capture_output=True)
    assert result.returncode==0,result.stdout+result.stderr
    text=SCRIPT.read_text()
    assert 'param([switch]$RunReviewedWarmupControl)' in text and 'if (!$RunReviewedWarmupControl)' in text
    assert 'STATIC_READY_FOR_REVIEW' in text and 'static_receipt_sha256' in text
    assert '--execute-reviewed-warmup-control' in text and 'profile_budget=0' in text
    assert 'WARMUP_BATCH_COMPLETE_STOP_FOR_REVIEW' in text and "gate11='BLOCKED'" in text
    assert '512MB' in text and 'UNKNOWN_STOP_AND_INSPECT_NO_RETRY' in text
    assert '@($Files |' in text and '-Force' not in text and 'taskkill' not in text
    assert 'nsys' not in text.lower() and 'profile.py' not in text
    assert 'source_representations' in text and 'SOURCE_BYTES_CONFLICT' in text
    assert "CUDA_VISIBLE_DEVICES='-1'" in text and "CUDA_VISIBLE_DEVICES='3'" in text
