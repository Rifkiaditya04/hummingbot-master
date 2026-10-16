param(
    [string]$Password,
    [string]$ConfigFileName,
    [string]$Config,
    [string]$V2,
    [switch]$Headless,
    [switch]$SkipPreflight
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

function Test-BinanceConnectivity {
    param(
        [int]$TimeoutSec = 10
    )

    $results = [ordered]@{
        ApiRestOk = $false
        StreamWsOk = $false
        ApiDetails = ""
        StreamDetails = ""
    }

    try {
        $dns = Resolve-DnsName -Name "api.binance.com" -Type A -ErrorAction Stop | Select-Object -First 1
        $results.ApiDetails = "DNS OK: api.binance.com -> $($dns.IPAddress)"
    } catch {
        $results.ApiDetails = "DNS FAIL: api.binance.com -> $($_.Exception.Message)"
    }

    try {
        $response = Invoke-WebRequest -Uri "https://api.binance.com/api/v3/time" -Method Get -TimeoutSec $TimeoutSec -UseBasicParsing -ErrorAction Stop
        $results.ApiRestOk = $true
        $results.ApiDetails = "REST OK: api.binance.com/api/v3/time -> HTTP $($response.StatusCode)"
    } catch {
        $results.ApiDetails = "REST FAIL: api.binance.com/api/v3/time -> $($_.Exception.Message)"
    }

    try {
        $tcp = Test-NetConnection -ComputerName "stream.binance.com" -Port 9443 -WarningAction SilentlyContinue -InformationLevel Quiet
        if ($tcp) {
            $results.StreamWsOk = $true
            $results.StreamDetails = "WS OK: stream.binance.com:9443 reachable"
        } else {
            $results.StreamDetails = "WS FAIL: stream.binance.com:9443 unreachable"
        }
    } catch {
        $results.StreamDetails = "WS FAIL: stream.binance.com:9443 -> $($_.Exception.Message)"
    }

    return [pscustomobject]$results
}

if (-not (Test-Path "bin/hummingbot_quickstart.py")) {
    throw "File bin/hummingbot_quickstart.py tidak ditemukan. Pastikan Anda menjalankan script dari root project."
}

if (-not $SkipPreflight) {
    $binanceCheck = Test-BinanceConnectivity
    Write-Host "[preflight] $($binanceCheck.ApiDetails)"
    Write-Host "[preflight] $($binanceCheck.StreamDetails)"

    if (-not $binanceCheck.ApiRestOk -or -not $binanceCheck.StreamWsOk) {
        Write-Error @"
Preflight Binance gagal.
Bot dihentikan sebelum start agar tidak masuk loop error di Hummingbot.

Detail:
  $($binanceCheck.ApiDetails)
  $($binanceCheck.StreamDetails)

Tindakan yang biasanya diperlukan:
  - Pastikan DNS/route tidak mengubah api.binance.com menjadi host lain.
  - Pastikan tidak ada captive portal, proxy, atau SSL interception aktif.
  - Uji ulang dari jaringan lain jika perlu.
  - Jika Anda sengaja ingin lanjut untuk debugging, jalankan lagi dengan -SkipPreflight.
"@
        exit 1
    }
}

$condaExe = Get-CondaCommand
$argsList = @("run", "--no-capture-output", "-n", "hummingbot", "python", "bin/hummingbot_quickstart.py")

if ($Password) {
    $argsList += @("-p", $Password)
}
if ($ConfigFileName) {
    $argsList += @("-f", $ConfigFileName)
}
if ($Config) {
    $argsList += @("-c", $Config)
}
if ($V2) {
    $argsList += @("--v2", $V2)
}
if ($Headless) {
    $argsList += @("--headless", "true")
}

& $condaExe @argsList
