param(
    [string]$Password,
    [switch]$SkipPreflight
)

$ErrorActionPreference = "Stop"
$externalConfigPath = Join-Path $PSScriptRoot "..\Butterfly.ps1"

if (Test-Path $externalConfigPath) {
    . $externalConfigPath
}

$params = @{
    V2 = if ($script:ButterflyV2Config) { $script:ButterflyV2Config } else { "binance_btc_usdt_high_conf_bot.yml" }
}

if ($Password) {
    $params.Password = $Password
} elseif ($script:ButterflyPassword) {
    $params.Password = $script:ButterflyPassword
}

if ($script:ButterflyHeadless) {
    $params.Headless = $true
}

if ($SkipPreflight) {
    $params.SkipPreflight = $true
}

& "$PSScriptRoot\start.ps1" @params
