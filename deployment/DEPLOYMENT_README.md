# ExposedPath v3 Pilot — Server Deployment

## Prerequisites

- Windows Server / 10 / 11 + PowerShell 5.1+
- Python 3.10+ with PyTorch CUDA already installed
- NVIDIA Nsight Systems installed
- Local model directory with `config.json`
- Target project directory exists (can be empty or contain the old version)

## Installation

```powershell
# 1. Extract the ZIP on the server
Expand-Archive `
    -Path ".\exposedpath_v3_pilot_deploy.zip" `
    -DestinationPath ".\exposedpath_v3_pilot_deploy"

Set-Location ".\exposedpath_v3_pilot_deploy"

# 2. Install (backs up existing files first)
.\deployment\install_on_server.ps1 `
    -ProjectRoot "D:\path\to\A-exposed-model-of-LLM-inference"
```

## Verification

```powershell
.\deployment\verify_deployment.ps1 `
    -ProjectRoot "D:\path\to\A-exposed-model-of-LLM-inference"
```

## Smoke Test (Dry Run)

```powershell
Set-Location "D:\path\to\A-exposed-model-of-LLM-inference"

.\scripts\run_server_smoke_test.ps1 `
    -ModelPath "D:\models\<model-name>" `
    -GpuId 0 `
    -NsysPath "C:\Program Files\NVIDIA Corporation\Nsight Systems <version>\target-windows-x64\nsys.exe" `
    -DryRun
```

## Rollback

The installer prints a `robocopy` command at the end.  Example:

```powershell
robocopy "D:\backups\20260721T120000Z_backup" "D:\A-exposed-model-of-LLM-inference" /E /IS /IT
```

## What the Installer Does

1. Backs up every existing file before overwriting
2. Copies new files, preserving relative paths
3. Verifies SHA-256 of every file after copy
4. Runs `python -m exposedpath --help`
5. Runs `python -m pytest -q` (unless `-SkipTests`)
6. Runs `python -m compileall exposedpath analysis`
7. Runs `.\scripts\verify_pilot_install.ps1`

## What the Installer NEVER Does

- Delete any files
- Modify models, DOCX, results/, traces, or SQLite
- Run GPU workloads
- Download models
- Change Python packages
