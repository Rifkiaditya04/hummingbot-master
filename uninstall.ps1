param()

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

$condaExe = Get-CondaCommand
$envExists = & $condaExe env list | Select-String -Pattern "^\s*hummingbot\s"

if ($envExists) {
    & $condaExe env remove -n hummingbot -y
    Write-Host "Environment 'hummingbot' sudah dihapus."
} else {
    Write-Host "Environment 'hummingbot' tidak ditemukan."
}
