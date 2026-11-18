# CK Personal Finance - native Windows validation kit (RB6g kit - app commit unchanged: fbd2559; candidate rebuilt after artifact loss, new zip sha)
# Automates packaging/windows/native-windows-validation-runbook.md
# Clean Windows 10/11, Windows PowerShell 5.1 quoting, no installs, synthetic fixtures only.
param(
  [string]$ZipPath = "",
  [string]$WorkRoot = "C:\ck-test",
  [switch]$ForceWorkRoot,
  [switch]$NoPauses
)
$ErrorActionPreference = "Continue"
$KitDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$ResultsDir = Join-Path $KitDir "ck-validation-results-$Stamp"
New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
$RunLog = Join-Path $ResultsDir "run-log.txt"

$ExpectedZipSha  = "49e14af0a57c7b48ad6771d462f38755896b1a9b8cc5b632b1ff10966c27bf3d"
$ExpectedCommit  = "fbd255931e9fe3052f0f6ea6c4a6aab022b7b5aa"
$ExpectedFiles   = 1190
$BaseUrl         = "http://127.0.0.1:5002"
$BundleDir       = Join-Path $WorkRoot "ck-personal-finance"
$script:Steps = @()
$script:StopRun = $false

# WorkRoot safety (auditor LOW-2): default only, unless -ForceWorkRoot; never a
# drive root, never fewer than two path components. LOW-3: never a junction /
# symlink / reparse point - PS 5.1 Remove-Item -Recurse would delete the
# target's real contents.
$DefaultWorkRoot = "C:\ck-test"
$wrCheck = $WorkRoot.TrimEnd('\')
$wrComponents = @($wrCheck -split '\\' | Where-Object { $_ -ne "" })
if (($WorkRoot -ne $DefaultWorkRoot) -and (-not $ForceWorkRoot)) {
  Write-Host "REFUSED: -WorkRoot is '$WorkRoot'. The default is '$DefaultWorkRoot'. Pass -ForceWorkRoot to override."
  exit 2
}
if (($wrCheck -match '^[A-Za-z]:$') -or ($wrComponents.Count -lt 2)) {
  Write-Host "REFUSED: -WorkRoot '$WorkRoot' is a drive root or has fewer than two path components."
  exit 2
}
if ((Test-Path $WorkRoot) -and ((Get-Item $WorkRoot -Force).Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
  Write-Host "REFUSED: -WorkRoot '$WorkRoot' is a junction, symlink, or other reparse point. Deleting it could remove the target's real contents."
  exit 2
}

function Log([string]$msg) {
  $line = "[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $msg
  Add-Content -Path $RunLog -Value $line
  Write-Host $line
}
function Record([string]$id, [string]$name, [string]$status, [string]$observed) {
  $script:Steps += [pscustomobject]@{ step=$id; name=$name; status=$status; observed=$observed }
  Log ("{0} {1}: {2}" -f $status, $id, $name)
  if ($status -eq "FAIL") { $script:StopRun = $true }
}
function OperatorPause([string]$what) {
  if (-not $NoPauses) { Read-Host "OPERATOR SCREENSHOT: $what - take it, then press Enter" | Out-Null }
}
function Save-Out([string]$name, [string]$content) {
  Set-Content -Path (Join-Path $ResultsDir $name) -Value $content -Encoding UTF8
}
function Http-Up() {
  $code = & curl.exe -s -o NUL -w "%{http_code}" --max-time 3 "$BaseUrl/api/health" 2>$null
  return ($code -eq "200")
}
function Port-Free() {
  try {
    $c = New-Object System.Net.Sockets.TcpClient
    $c.Connect("127.0.0.1", 5002); $c.Close(); return $false
  } catch { return $true }
}
function Run-Bat([string]$bat, [string]$stdinLines, [string]$outName, [int]$timeoutSec) {
  # Written to a temp .cmd file: no cmd /c quote-stripping and no PowerShell
  # native-argument marshalling of embedded quotes (PS 5.1 and 7 differ).
  $outFile = Join-Path $ResultsDir $outName
  $cmdFile = Join-Path $env:TEMP ("ckpf-run-" + [guid]::NewGuid().ToString("N") + ".cmd")
  $lines = @("@echo off", "cd /d `"$BundleDir`"", "($stdinLines) | `"$bat`" > `"$outFile`" 2>&1")
  [System.IO.File]::WriteAllLines($cmdFile, $lines)
  try {
    $p = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "`"$cmdFile`"" -PassThru
    if (-not $p.WaitForExit($timeoutSec * 1000)) {
      try { $p.Kill() } catch {}
      return @{ ok=$false; text="TIMEOUT after ${timeoutSec}s running $bat" }
    }
    $txt = ""; if (Test-Path $outFile) { $txt = Get-Content $outFile -Raw }
    return @{ ok=$true; text=$txt }
  } finally {
    Remove-Item $cmdFile -Force -ErrorAction SilentlyContinue
  }
}
function Start-App() {
  Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "`"$BundleDir\Start-Ledger.bat`"" -WorkingDirectory $BundleDir | Out-Null
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  while ($sw.Elapsed.TotalSeconds -lt 60) { if (Http-Up) { return $sw.Elapsed.TotalSeconds }; Start-Sleep -Seconds 1 }
  return -1
}
function Stop-App([string]$outName) {
  $r = Run-Bat "$BundleDir\Stop-Ledger.bat" "echo." $outName 60
  Start-Sleep -Seconds 2
  return $r
}

Log "CK PF native Windows validation - results: $ResultsDir"

# S0 environment
$os = Get-CimInstance Win32_OperatingSystem
$envInfo = "OS: $($os.Caption) $($os.Version) $($os.OSArchitecture); PS: $($PSVersionTable.PSVersion); Computer: $env:COMPUTERNAME; Time: $(Get-Date -Format o)"
Save-Out "s0-environment.txt" $envInfo
Record "S0" "Environment recorded" "PASS" $envInfo

# S1 zip hash
if ($ZipPath -eq "") {
  $cand = Get-ChildItem -Path $KitDir -Filter "ck-personal-finance-windows-v1.0.zip" -ErrorAction SilentlyContinue
  if ($cand) { $ZipPath = $cand.FullName }
}
if (-not (Test-Path $ZipPath)) {
  Record "S1" "Candidate zip present" "FAIL" "zip not found; place it next to this script or pass -ZipPath"
} else {
  $zipSha = (Get-FileHash -Algorithm SHA256 $ZipPath).Hash.ToLower()
  $zipSize = (Get-Item $ZipPath).Length
  Save-Out "s1-zip-hash.txt" "zip: $ZipPath`nbytes: $zipSize`nsha256: $zipSha`nexpected: $ExpectedZipSha"
  if ($zipSha -eq $ExpectedZipSha) {
    Record "S1" "Candidate zip sha256 matches pinned rebuilt candidate (RB6g)" "PASS" "$zipSha ($zipSize bytes)"
  } else {
    Record "S1" "Candidate zip sha256 matches pinned rebuilt candidate (RB6g)" "FAIL" "got $zipSha, expected $ExpectedZipSha - wrong artifact"
  }
}

# S2 extract + bundle verify
if (-not $script:StopRun) {
  if (Test-Path $WorkRoot) { Remove-Item -Recurse -Force $WorkRoot }
  New-Item -ItemType Directory -Force -Path $WorkRoot | Out-Null
  try { Expand-Archive -Path $ZipPath -DestinationPath $WorkRoot -Force }
  catch { Record "S2" "Extract zip" "FAIL" "$_" }
  if (-not $script:StopRun) {
    $bi = Get-Content (Join-Path $BundleDir "BUILD-INFO.txt") -Raw
    Save-Out "s2-build-info.txt" $bi
    $r = Run-Bat "$BundleDir\Verify-Bundle.bat" "echo." "s2-verify-bundle.txt" 300
    $verified = ($r.text -match "BUNDLE VERIFIED") -and ($r.text -match "$ExpectedFiles")
    if ($verified -and ($bi -match $ExpectedCommit)) {
      Record "S2" "Bundle extracted and verified ($ExpectedFiles files, commit match)" "PASS" "BUNDLE VERIFIED"
    } else {
      Record "S2" "Bundle extracted and verified" "FAIL" ($r.text + "`nBUILD-INFO: " + $bi)
    }
    OperatorPause "S-A: the Verify-Bundle console output"
  }
}

# S3 first launch
if (-not $script:StopRun) {
  $secs = Start-App
  if ($secs -ge 0) {
    Record "S3" "App launches and serves on 127.0.0.1:5002" "PASS" ("healthy after {0:N1}s" -f $secs)
    OperatorPause "S-B: the app's first screen in the browser tab that opened"
  } else {
    Record "S3" "App launches and serves on 127.0.0.1:5002" "FAIL" "no /api/health 200 within 60s"
  }
}

# S4 process behaviour
if (-not $script:StopRun) {
  Start-Sleep -Seconds 35
  $procs = @(Get-Process -Name "ck-ledger" -ErrorAction SilentlyContinue)
  $names = ($procs | ForEach-Object { $_.ProcessName + " pid=" + $_.Id }) -join "; "
  Save-Out "s4-processes.txt" ("count=" + $procs.Count + "`n" + $names)
  if ($procs.Count -eq 1) {
    Record "S4" "Exactly one ck-ledger process remains" "PASS" $names
  } else {
    Record "S4" "Exactly one ck-ledger process remains" "FAIL" ("count=" + $procs.Count + ": " + $names)
  }
  OperatorPause "S-C: Task Manager showing the ck-ledger process list"
}

# S5 occupied port refusal
if (-not $script:StopRun) {
  $r = Run-Bat "$BundleDir\Start-Ledger.bat" "echo." "s5-second-launch.txt" 60
  if (($r.text -match "Port 5002 is already in use") -and (Http-Up)) {
    Record "S5" "Second launch refused; first instance keeps serving" "PASS" "refusal printed, first instance healthy"
  } else {
    Record "S5" "Second launch refused; first instance keeps serving" "FAIL" $r.text
  }
  OperatorPause "S-D: the port-refusal console output"
}

# S6 bundled OCR engine smoke
if (-not $script:StopRun) {
  $tver = & "$BundleDir\runtime\ocr\bin\tesseract.exe" --version 2>&1 | Out-String
  Save-Out "s6-tesseract-version.txt" $tver
  $binCount = @(Get-ChildItem "$BundleDir\runtime\ocr\bin").Count
  $tess = Test-Path "$BundleDir\runtime\ocr\tessdata\eng.traineddata"
  $licFiles = @(Get-ChildItem "$BundleDir\runtime\ocr\licenses" -File).Count
  $licTree = Test-Path "$BundleDir\runtime\ocr\licenses\mingw-per-file"
  $okVer = ($tver -match "tesseract 5\.5\.4") -and ($tver -match "leptonica-1\.87\.0") -and ($tver -match "libpng 1\.6\.59")
  if ($okVer -and $binCount -eq 7 -and $tess -and $licFiles -eq 11 -and $licTree) {
    Record "S6" "Bundled tesseract 5.5.4 runs natively; payload complete" "PASS" "version ok; bin=7, tessdata ok, licenses=11+tree"
  } else {
    Record "S6" "Bundled tesseract runs natively; payload complete" "FAIL" "version: $tver; bin=$binCount tess=$tess licFiles=$licFiles tree=$licTree"
  }
  OperatorPause "S-E: the tesseract --version output"
}

# S7 OCR through the app (synthetic only)
if (-not $script:StopRun) {
  $statusJson = & curl.exe -s "$BaseUrl/api/personal-finance/ocr/status"
  Save-Out "s7-ocr-status.json" $statusJson
  $ocrStatus = $statusJson | ConvertFrom-Json
  if (-not $ocrStatus.available) {
    Record "S7" "OCR available in app" "FAIL" $statusJson
  } else {
    $pngJson = & curl.exe -s -F "file=@$KitDir\fixtures\bill.png" "$BaseUrl/api/personal-finance/ocr/extract"
    Save-Out "s7-png-extract.json" $pngJson
    $png = $pngJson | ConvertFrom-Json
    $fields = @($png.fields_found) -join ","
    if ($png.status -eq "unverified" -and ($fields -match "vendor") -and ($fields -match "amount") -and ($fields -match "due_date")) {
      Record "S7a" "PNG bill OCR gives UNVERIFIED vendor/amount/due_date with source lines" "PASS" ("fields: $fields; engine: " + $png.engine)
    } else {
      Record "S7a" "PNG bill OCR gives UNVERIFIED vendor/amount/due_date" "FAIL" $pngJson
    }
    OperatorPause "S-F: the app's UNVERIFIED scan-results panel (open the bill scan screen in the app)"
  }
  if (-not $script:StopRun) {
    $eid = $png.extraction_id
    $bodyPath = Join-Path $ResultsDir "s7-confirm-body.json"
    [System.IO.File]::WriteAllText($bodyPath, '{"vendor":"Synthetic Energy","amount":142.50,"due_date":"2026-11-15","note":"windows validation kit"}')
    $confJson = & curl.exe -s -X POST -H "Content-Type: application/json" -d "@$bodyPath" "$BaseUrl/api/personal-finance/ocr/extractions/$eid/confirm"
    Save-Out "s7-confirm.json" $confJson
    $conf = $confJson | ConvertFrom-Json
    if ($conf.bill -and $conf.bill.id) {
      Record "S7b" "Confirm creates a bill (source=ocr)" "PASS" ("bill id " + $conf.bill.id + ", event " + $conf.event)
    } else {
      Record "S7b" "Confirm creates a bill" "FAIL" $confJson
    }
  }
  if (-not $script:StopRun) {
    $tifJson = & curl.exe -s -F "file=@$KitDir\fixtures\bill-4frame.tif" "$BaseUrl/api/personal-finance/ocr/extract"
    Save-Out "s7-tiff-extract.json" $tifJson
    $tif = $tifJson | ConvertFrom-Json
    if ($tif.pages_processed -eq 3 -and ($tif.processing_notice -match "Only the first 3 of 4")) {
      Record "S7c" "4-frame TIFF: 3 frames read, skip notice shown" "PASS" $tif.processing_notice
    } else {
      Record "S7c" "4-frame TIFF: 3 frames read, skip notice shown" "FAIL" $tifJson
    }
    $pdfJson = & curl.exe -s -F "file=@$KitDir\fixtures\bill-2page.pdf" "$BaseUrl/api/personal-finance/ocr/extract"
    Save-Out "s7-pdf-extract.json" $pdfJson
    $pdf = $pdfJson | ConvertFrom-Json
    if ($pdf.pages_processed -eq 2) {
      Record "S7d" "2-page PDF: both pages read" "PASS" ("pages_processed=2, fields: " + (@($pdf.fields_found) -join ","))
    } else {
      Record "S7d" "2-page PDF: both pages read" "FAIL" $pdfJson
    }
    $left = @(Get-ChildItem "$BundleDir\data\uploads\ocr" -Filter "*-normalised-*.png" -ErrorAction SilentlyContinue) +
            @(Get-ChildItem "$BundleDir\data\uploads\ocr" -Filter "*-page-*.png" -ErrorAction SilentlyContinue)
    if ($left.Count -eq 0) {
      Record "S7e" "No leftover working rasters in uploads\ocr" "PASS" "0 leftover files"
    } else {
      Record "S7e" "No leftover working rasters in uploads\ocr" "FAIL" (($left | ForEach-Object { $_.Name }) -join "; ")
    }
  }
}

# S8 Ask without Ollama
if (-not $script:StopRun) {
  $askOut = Join-Path $ResultsDir "s8-ask.json"
  $bodyPath = Join-Path $ResultsDir "s8-ask-body.json"
  [System.IO.File]::WriteAllText($bodyPath, '{"prompt":"What did I spend this month?"}')
  $code = & curl.exe -s -o "$askOut" -w "%{http_code}" -X POST -H "Content-Type: application/json" -d "@$bodyPath" "$BaseUrl/api/personal-finance/ai/complete"
  $askTxt = Get-Content $askOut -Raw
  if ($code -eq "503" -and ($askTxt -match "not installed|Ollama")) {
    Record "S8" "Ask without Ollama: clear message, no crash" "PASS" ("HTTP " + $code + ": " + $askTxt.Trim())
  } else {
    Record "S8" "Ask without Ollama: clear message, no crash" "FAIL" ("HTTP " + $code + ": " + $askTxt)
  }
  OperatorPause "S-G: the Ask feature's message in the app (no model installed)"
}

# S9 stop
if (-not $script:StopRun) {
  $r = Stop-App "s9-stop.txt"
  if (($r.text -match "Stopped\. Verified") -and (Port-Free)) {
    Record "S9" "Stop-Ledger stops the server; port 5002 free" "PASS" "stopped, port free"
  } else {
    Record "S9" "Stop-Ledger stops the server; port 5002 free" "FAIL" $r.text
  }
}

# S10 persistence across restart
if (-not $script:StopRun) {
  $secs = Start-App
  if ($secs -lt 0) {
    Record "S10" "Restart and bill persistence" "FAIL" "app did not come back within 60s"
  } else {
    $billsJson = & curl.exe -s "$BaseUrl/api/personal-finance/bills"
    Save-Out "s10-bills-after-restart.json" $billsJson
    $bills = $billsJson | ConvertFrom-Json
    $found = $false
    foreach ($b in $bills.bills) { if ($b.vendor -eq "Synthetic Energy" -and $b.source -eq "ocr") { $found = $true } }
    if ($found) {
      Record "S10" "Confirmed bill persists across restart" "PASS" "Synthetic Energy (source=ocr) present after restart"
    } else {
      Record "S10" "Confirmed bill persists across restart" "FAIL" "bill missing after restart"
    }
    Stop-App "s10-stop.txt" | Out-Null
  }
}

# S11 remove data + fresh first-run
if (-not $script:StopRun) {
  $r = Run-Bat "$BundleDir\Remove-Data.bat" "(echo YES&echo.)" "s11-remove-data.txt" 120
  $gone = -not (Test-Path "$BundleDir\data")
  if ($gone -and ($r.text -match "Data folder removed")) {
    Record "S11a" "Remove-Data deletes the data folder" "PASS" "data folder removed"
  } else {
    Record "S11a" "Remove-Data deletes the data folder" "FAIL" ($r.text + "; folder gone: $gone")
  }
  if (-not $script:StopRun) {
    $secs = Start-App
    $fresh = $false
    if ($secs -ge 0) {
      $bills = & curl.exe -s "$BaseUrl/api/personal-finance/bills" | ConvertFrom-Json
      $fresh = (@($bills.bills).Count -eq 0)
    }
    if ($fresh) {
      Record "S11b" "Next start after data removal is a fresh first-run" "PASS" ("no bills, healthy after {0:N1}s" -f $secs)
    } else {
      Record "S11b" "Next start after data removal is a fresh first-run" "FAIL" "bills present or app unhealthy"
    }
    Stop-App "s11-final-stop.txt" | Out-Null
  }
}

# S12 hashes, manifest, summary
$tessSha = ""
if (Test-Path "$BundleDir\runtime\ocr\bin\tesseract.exe") {
  $tessSha = (Get-FileHash -Algorithm SHA256 "$BundleDir\runtime\ocr\bin\tesseract.exe").Hash.ToLower()
}
$zipShaFinal = ""
if (Test-Path $ZipPath) { $zipShaFinal = (Get-FileHash -Algorithm SHA256 $ZipPath).Hash.ToLower() }
Save-Out "s12-hashes.txt" "candidate zip sha256: $zipShaFinal`ntesseract.exe sha256: $tessSha"

$script:Steps | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $ResultsDir "results.json") -Encoding UTF8
$passN = @($script:Steps | Where-Object { $_.status -eq "PASS" }).Count
$failN = @($script:Steps | Where-Object { $_.status -eq "FAIL" }).Count
$summary = "CK PF native Windows validation summary ($Stamp)`nOS: $($os.Caption) $($os.Version)`nPASS: $passN  FAIL: $failN`n`n"
foreach ($s in $script:Steps) { $summary += ("{0} {1}: {2}`n  observed: {3}`n" -f $s.status, $s.step, $s.name, $s.observed) }
Save-Out "SUMMARY.txt" $summary

$manifest = ""
Get-ChildItem $ResultsDir -File | ForEach-Object {
  $h = (Get-FileHash -Algorithm SHA256 $_.FullName).Hash.ToLower()
  $manifest += "$h  $($_.Name)`n"
}
Save-Out "RESULTS-MANIFEST.txt" $manifest

Write-Host ""
Write-Host $summary
Write-Host "Results folder: $ResultsDir"
Write-Host "Send back the whole results folder (it contains SUMMARY.txt and RESULTS-MANIFEST.txt)."
if ($failN -gt 0) { exit 1 } else { exit 0 }
