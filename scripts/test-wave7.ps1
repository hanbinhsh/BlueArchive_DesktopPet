param([string]$StartAt = 'roster-test', [switch]$SizeFix)
$ErrorActionPreference = 'Stop'
$env:BA_EXECUTABLE = Join-Path (Get-Location) 'release/v0.1.18/win-unpacked/BA Desktop Pet.exe'
$wave7Ids = (Get-Content scripts/roster-wave7.json -Raw | ConvertFrom-Json).PSObject.Properties.Name
$checks = @('roster-test','hold-test','expressions-test','transitions-test','furniture-test','wave7-panel-test')
$start = [array]::IndexOf($checks, $StartAt)
if ($start -lt 0) { throw "Unknown test $StartAt" }
$outcomes = @()
if ($start -gt 0) {
  $outcomes = @(Get-Content test-results/wave7-runtime-suite.json -Raw | ConvertFrom-Json | Where-Object { $_.exitCode -eq 0 -and [array]::IndexOf($checks, $_.test) -lt $start })
}
$checks = $checks[$start..($checks.Length - 1)]
foreach ($check in $checks) {
  Write-Output "START $check"
  if ($check -eq 'hold-test' -and $env:BA_RESUME_HOLD) {
    $passed = @((Get-Content test-results/hold.json -Raw | ConvertFrom-Json).character)
    $env:BA_RESUME = '1'
    $remaining = @($wave7Ids | Where-Object { $_ -notin $passed })
    node scripts/hold-test.mjs @remaining *> test-results/wave7-hold-test.log
    Remove-Item Env:BA_RESUME
  } else {
    $targets = if ($SizeFix -and $check -in @('roster-test','hold-test','expressions-test','transitions-test')) { @('hifumi','izuna') } else { $wave7Ids }
    node "scripts/$check.mjs" @targets *> "test-results/wave7-$check.log"
  }
  $outcomes += @{ test = $check; exitCode = $LASTEXITCODE; completed = (Get-Date).ToUniversalTime().ToString('o') }
  $outcomes | ConvertTo-Json -Depth 5 | Set-Content test-results/wave7-runtime-suite.json -Encoding utf8
  if ($LASTEXITCODE -ne 0) { throw "Failed $check; see test-results/wave7-$check.log" }
  Write-Output "PASS $check"
}
