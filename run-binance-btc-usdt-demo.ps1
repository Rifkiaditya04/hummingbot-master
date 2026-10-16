param(
    [switch]$SkipPreflight
)

$ErrorActionPreference = "Stop"

function Test-BinanceDemoConnectivity {
    param([int]$TimeoutSec = 10)

    $results = [ordered]@{
        ApiRestOk = $false
        StreamWsOk = $false
        ApiDetails = ""
        StreamDetails = ""
    }

    try {
        $dns = Resolve-DnsName -Name "demo-api.binance.com" -Type A -ErrorAction Stop | Select-Object -First 1
        $results.ApiDetails = "DNS OK: demo-api.binance.com -> $($dns.IPAddress)"
    } catch {
        $results.ApiDetails = "DNS FAIL: demo-api.binance.com -> $($_.Exception.Message)"
    }

    try {
        $response = Invoke-WebRequest -Uri "https://demo-api.binance.com/api/v3/time" -Method Get `
            -TimeoutSec $TimeoutSec -UseBasicParsing -ErrorAction Stop
        $results.ApiRestOk = $true
        $results.ApiDetails = "REST OK: demo-api.binance.com/api/v3/time -> HTTP $($response.StatusCode)"
    } catch {
        $results.ApiDetails = "REST FAIL: demo-api.binance.com/api/v3/time -> $($_.Exception.Message)"
    }

    try {
        $tcp = Test-NetConnection -ComputerName "demo-stream.binance.com" -Port 9443 `
            -WarningAction SilentlyContinue -InformationLevel Quiet
        if ($tcp) {
            $results.StreamWsOk = $true
            $results.StreamDetails = "WS OK: demo-stream.binance.com:9443 reachable"
        } else {
            $results.StreamDetails = "WS FAIL: demo-stream.binance.com:9443 unreachable"
        }
    } catch {
        $results.StreamDetails = "WS FAIL: demo-stream.binance.com:9443 -> $($_.Exception.Message)"
    }

    return [pscustomobject]$results
}

if (-not $SkipPreflight) {
    $demoCheck = Test-BinanceDemoConnectivity
    Write-Host "[preflight] $($demoCheck.ApiDetails)"
    Write-Host "[preflight] $($demoCheck.StreamDetails)"

    if (-not $demoCheck.ApiRestOk -or -not $demoCheck.StreamWsOk) {
        Write-Error @"
Binance Demo preflight gagal.
Bot dihentikan sebelum start agar tidak masuk loop error.

Detail:
  $($demoCheck.ApiDetails)
  $($demoCheck.StreamDetails)

Jika koneksi sudah diperiksa dan Anda memang ingin melewati preflight:
  .\run-binance-btc-usdt-demo.ps1 -SkipPreflight
"@
        exit 1
    }
}

& "$PSScriptRoot\start.ps1" -V2 "binance_btc_usdt_high_conf_demo.yml" -SkipPreflight
