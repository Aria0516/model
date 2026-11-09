param(
    [string]$OutputDirectory = (Join-Path $PSScriptRoot 'data\zenodo_3737795\qDII-CLV3-DR5'),
    [string]$Pattern = '^qDII-CLV3-DR5-'
)
# The 21 qDII-CLV3-DR5 meristems (3 time points each) of Galvan-Ampudia et al. 2020 from Zenodo record 3737795.
# Resumable; every file is checked against the MD5 published by Zenodo.

$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$listing = Join-Path $OutputDirectory 'zenodo_record_3737795.json'
& curl.exe -s --fail --retry 10 --max-time 120 --output $listing 'https://zenodo.org/api/records/3737795'
if ($LASTEXITCODE -ne 0) { throw 'could not read the Zenodo record' }
$files = (Get-Content -Raw $listing | ConvertFrom-Json).files | Where-Object { $_.key -match $Pattern } | Sort-Object key
Write-Host ("{0} files, {1:N2} GB" -f $files.Count, (($files | Measure-Object size -Sum).Sum / 1e9))

foreach ($f in $files) {
    $target = Join-Path $OutputDirectory $f.key
    $md5 = $f.checksum -replace '^md5:', ''
    if ((Test-Path -LiteralPath $target) -and ((Get-Item -LiteralPath $target).Length -eq $f.size) -and
        ((Get-FileHash -LiteralPath $target -Algorithm MD5).Hash.ToLowerInvariant() -eq $md5)) {
        Write-Host ('done already: ' + $f.key)
        continue
    }
    $t0 = Get-Date
    & curl.exe -s -L --fail --retry 20 --retry-all-errors --retry-delay 5 -C - --output $target $f.links.self
    if ($LASTEXITCODE -ne 0) { throw ('curl failed for ' + $f.key) }
    if ((Get-Item -LiteralPath $target).Length -ne $f.size) { throw ('size mismatch: ' + $f.key) }
    if ((Get-FileHash -LiteralPath $target -Algorithm MD5).Hash.ToLowerInvariant() -ne $md5) { throw ('MD5 mismatch: ' + $f.key) }
    $s = ((Get-Date) - $t0).TotalSeconds
    Write-Host ("ok {0}  {1:N0} MB in {2:N0} s ({3:N1} MB/s)" -f $f.key, ($f.size / 1e6), $s, ($f.size / 1e6 / [math]::Max($s, 1)))
}
Write-Host 'ALL FILES DOWNLOADED AND MD5-VERIFIED'
