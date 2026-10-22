# Uji worker PDFBox dengan runtime Java BUNDLE (bukan Java eksternal).
# Semua operasi yang dipakai aplikasi dijalankan: inspect, extract, merge, fill_form, add_annotations.
# Output diverifikasi dengan PyMuPDF (pembaca independen).
param(
    [string]$Worker = "$PSScriptRoot\..\src-tauri\worker",
    [string]$Python = "$PSScriptRoot\..\..\..\.venv\Scripts\python.exe",
    [string]$Work = "$env:TEMP\unionpdf-jre-test"
)
$ErrorActionPreference = "Stop"
$java = Join-Path $Worker "jre\bin\java.exe"
if (-not (Test-Path $java)) { throw "runtime bawaan tidak ada: $java" }

Remove-Item $Work -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $Work | Out-Null
$fx = Resolve-Path "$PSScriptRoot\..\src-tauri\tests\fixtures"
$structure = Join-Path $fx "rs05_structure.pdf"
$form = Join-Path $fx "rs03_form.pdf"

# Jalankan worker dengan runtime bundel: satu proses, beberapa request.
$requests = @(
    '{"id":"1","op":"ping"}',
    ('{"id":"2","op":"inspect","params":{"input":"' + ($structure -replace '\\', '\\') + '"}}'),
    ('{"id":"3","op":"extract","params":{"input":"' + ($structure -replace '\\', '\\') + '","output":"' + ((Join-Path $Work "extract.pdf") -replace '\\', '\\') + '","pages":[1,2,3]}}'),
    ('{"id":"4","op":"fill_form","params":{"input":"' + ($form -replace '\\', '\\') + '","output":"' + ((Join-Path $Work "filled.pdf") -replace '\\', '\\') + '","values":{"nama":"Budi Santoso","setuju":true,"pilihan":"B","kota":"Surabaya"}}}'),
    ('{"id":"5","op":"add_annotations","params":{"input":"' + ($structure -replace '\\', '\\') + '","output":"' + ((Join-Path $Work "annot.pdf") -replace '\\', '\\') + '","annotations":[{"type":"highlight","page":0,"rect":[40,60,400,120],"quads":[[40,80,400,120]]},{"type":"note","page":0,"rect":[420,100,442,122],"contents":"Catatan uji runtime"}]}}'),
    ('{"id":"6","op":"merge","params":{"inputs":["' + ($structure -replace '\\', '\\') + '","' + ($form -replace '\\', '\\') + '"],"output":"' + ((Join-Path $Work "merge.pdf") -replace '\\', '\\') + '"}}'),
    '{"id":"7","op":"shutdown"}'
) -join "`n"

$out = $requests | & $java "-Dfile.encoding=UTF-8" "-Djava.awt.headless=true" -jar (Join-Path $Worker "unionpdf-worker.jar") 2>&1
$out | ForEach-Object { "  $_" }
$text = $out -join "`n"
if ($text -notmatch '"type":"ready"') { throw "worker tidak start dengan runtime bundel" }
foreach ($id in 1..6) {
    if ($text -notmatch ('"id":"' + $id + '","type":"result"')) { throw "request $id tidak menghasilkan result" }
}
if ($text -match '"type":"error"') { throw "ada request yang gagal" }

# Verifikasi output dengan PyMuPDF.
$check = & $Python "$PSScriptRoot\inspect_pdf.py" (Join-Path $Work "filled.pdf") | ConvertFrom-Json
$v = @{}; foreach ($f in $check.fields) { $v["$($f.name)|$($f.value)"] = $f.ap_contains_value }
foreach ($k in @("nama|Budi Santoso", "setuju|Yes", "kota|Surabaya")) {
    if (-not $v.ContainsKey($k)) { throw "nilai form hilang dengan runtime bundel: $k" }
}
if (-not ($check.fields | Where-Object { $_.name -eq "pilihan" -and $_.value -eq "B" })) { throw "radio B tidak terpilih" }
if (-not $v["nama|Budi Santoso"]) { throw "appearance field teks tidak memuat nilai baru" }

$ex = & $Python "$PSScriptRoot\inspect_pdf.py" (Join-Path $Work "extract.pdf") | ConvertFrom-Json
if ($ex.page_count -ne 3) { throw "extract: jumlah halaman $($ex.page_count) bukan 3" }
$toc = ($ex.toc | ForEach-Object { $_[1] }) -join ","
if ($toc -ne "Bab 3,Sub 3.1 ke hal 4") { throw "extract: bookmark tidak sesuai: $toc" }

$an = & $Python "$PSScriptRoot\inspect_pdf.py" (Join-Path $Work "annot.pdf") | ConvertFrom-Json
$types = ($an.annotations | ForEach-Object { $_.type }) -join ","
if ($types -notmatch "Highlight" -or $types -notmatch "Text") { throw "anotasi tidak lengkap: $types" }
$noAp = ($an.annotations | Where-Object { -not $_.has_ap }).Count
if ($noAp -gt 0) { throw "ada anotasi tanpa appearance stream: $noAp" }

$mg = & $Python "$PSScriptRoot\inspect_pdf.py" (Join-Path $Work "merge.pdf") | ConvertFrom-Json
if ($mg.page_count -ne 7) { throw "merge: jumlah halaman $($mg.page_count) bukan 7" }

Write-Output "OK: worker berjalan penuh dengan runtime Java bundel (inspect, extract, merge, fill_form, add_annotations)."
Write-Output "  filled: nama=Budi Santoso (AP berisi nilai), setuju=Yes, pilihan=B, kota=Surabaya"
Write-Output "  extract: 3 halaman, bookmark '$toc'"
Write-Output "  annot: $types (semua ada /AP)"
Write-Output "  merge: $($mg.page_count) halaman"
