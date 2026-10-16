param(
    [switch]$Dydx
)

$ErrorActionPreference = "Stop"

function Get-CondaCommand {
    $conda = Get-Command conda -ErrorAction SilentlyContinue
    if ($null -ne $conda) {
        return $conda.Source
    }

    $candidates = @(
        "$env:USERPROFILE\miniconda3\Scripts\conda.exe",
        "$env:USERPROFILE\anaconda3\Scripts\conda.exe",
        "C:\ProgramData\miniconda3\Scripts\conda.exe",
        "C:\ProgramData\anaconda3\Scripts\conda.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw "Conda tidak ditemukan. Install Miniconda/Anaconda lalu pastikan 'conda' ada di PATH."
}

function Ensure-LogsDirectory {
    if (-not (Test-Path "logs")) {
        New-Item -ItemType Directory -Path "logs" | Out-Null
    }
}

$condaExe = Get-CondaCommand
$envFile = if ($Dydx) { "setup/environment_dydx.yml" } else { "setup/environment.yml" }

Ensure-LogsDirectory

Write-Host "Menggunakan conda: $condaExe"
Write-Host "Menggunakan environment file: $envFile"

$envExists = & $condaExe env list | Select-String -Pattern "^\s*hummingbot\s"
if ($envExists) {
    & $condaExe env update -n hummingbot -f $envFile
} else {
    & $condaExe env create -n hummingbot -f $envFile
}

& $condaExe run -n hummingbot conda develop .
& $condaExe run -n hummingbot python -m pip install --no-deps -r setup/pip_packages.txt
& $condaExe run -n hummingbot pre-commit install
& $condaExe run -n hummingbot python setup.py build_ext --inplace

Write-Host "Install selesai. Jalankan .\start.ps1 untuk memulai Hummingbot."
