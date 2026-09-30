"""Delivery review checks, never invokes a model, CUDA or Nsight."""
from pathlib import Path
import subprocess
import pytest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/run_gate11_pilot.ps1'


def test_powershell51_parser_and_separate_collection_optin():
    result=subprocess.run(['powershell.exe','-NoProfile','-Command',
        "$e=$null;$t=$null;[System.Management.Automation.Language.Parser]::ParseFile('"+str(SCRIPT).replace("'","''")+"',[ref]$t,[ref]$e)>$null; if($e.Count){$e|Out-String|Write-Output;exit 1}"],capture_output=True)
    assert result.returncode==0,result.stdout+result.stderr
    text=SCRIPT.read_text()
    assert 'param([switch]$CollectReviewedPilot)' in text
    assert "if (!$CollectReviewedPilot)" in text
    assert "STATIC_READY_FOR_REVIEW" in text and "static_receipt_sha256" in text
    assert "--execute-reviewed-pilot" in text
    assert "FIRST_BATCH_COMPLETE_STOP_FOR_REVIEW" in text
    assert '35GB' in text
    assert 'UNKNOWN_STOP_AND_INSPECT_NO_RETRY' in text
    assert "@($Files |" in text  # snapshot BEFORE writing the checksum manifest
    assert "-Force" not in text and 'taskkill' not in text


def test_delivery_source_identity_is_explicit_not_arbitrary_current_hash():
    text=SCRIPT.read_text()
    assert 'source_representations' in text
    assert '$ActualHash' in text and '$ActualBytes' in text
    assert 'SOURCE_BYTES_CONFLICT' in text
    assert 'No resume, overwrite or retry' in text
    assert "CUDA_VISIBLE_DEVICES='-1'" in text
    assert "CUDA_VISIBLE_DEVICES='3'" in text
