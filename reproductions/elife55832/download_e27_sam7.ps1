param(
    [string]$OutputDirectory = (Join-Path $PSScriptRoot 'data\E27_SAM7'),
    [switch]$IncludeRawCzi
)

$ErrorActionPreference = 'Stop'

$files = @(
    @{
        Name = 'qDII-CLV3-DR5-E27-LD-SAM7-No-organs.tif'
        Size = 377620885
        Sha256 = '259d5fed95dfd88108e2717191ac08a638a3a73bc7d2575a4e93af2639c63566'
    },
    @{
        Name = 'qDII-CLV3-DR5-E27-LD-SAM7-T5-No-organs.tif'
        Size = 377622023
        Sha256 = 'dfb42f593eb8b6d34947e6d38cde67efe8ce1d2f5be9ee14dc108d225f42e7bd'
    },
    @{
        Name = 'qDII-CLV3-DR5-E27-LD-SAM7-T10-No-organs.tif'
        Size = 377622355
        Sha256 = 'b3c72e3301316b3f7d9eb356c9fef522de946966afead469e8686a236752aad2'
    }
)

New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null

foreach ($file in $files) {
    $target = Join-Path $OutputDirectory $file.Name
    $url = 'https://flower.ens-lyon.fr/sam_patterning/data/' + $file.Name

    if ((Test-Path -LiteralPath $target -PathType Leaf) -and ((Get-Item -LiteralPath $target).Length -eq $file.Size)) {
        Write-Host ('Already complete: ' + $file.Name)
    }
    else {
        Write-Host ('Downloading with resume: ' + $file.Name)
        & curl.exe --http1.1 -L --fail --retry 20 --retry-all-errors --retry-delay 1 -C - --output $target $url
        if ($LASTEXITCODE -ne 0) {
            throw ('curl failed for ' + $file.Name)
        }
    }
    $actualSize = (Get-Item -LiteralPath $target).Length
    if ($actualSize -ne $file.Size) {
        throw ('Size mismatch for ' + $file.Name + ': got ' + $actualSize + ', expected ' + $file.Size)
    }
    $actualHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualHash -ne $file.Sha256) {
        throw ('SHA-256 mismatch for ' + $file.Name)
    }
}

Write-Host 'E27/SAM7 input set is complete and byte-size/SHA-256 validated.'

if ($IncludeRawCzi) {
    $layoutDirectory = Join-Path $OutputDirectory 'original_layout'
    $rawDirectory = Join-Path $layoutDirectory 'RAW'
    $croppedDirectory = Join-Path $layoutDirectory 'TIF-No-organs'
    New-Item -ItemType Directory -Path $rawDirectory, $croppedDirectory -Force | Out-Null

    foreach ($file in $files) {
        $source = Join-Path $OutputDirectory $file.Name
        $target = Join-Path $croppedDirectory $file.Name
        if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
            New-Item -ItemType HardLink -Path $target -Target $source | Out-Null
        }
        if ((Get-Item -LiteralPath $target).Length -ne $file.Size) {
            throw ('Historic-layout TIFF size mismatch for ' + $file.Name)
        }
    }

    $cziFiles = @(
        @{
            Name = 'qDII-CLV3-DR5-E27-LD-SAM7.czi'
            Size = 377766528
            Sha256 = '263966c82a08b8e5fcb46113cfb0dbc1e4ed7bca3242dc9d41f813e91dcfa253'
        },
        @{
            Name = 'qDII-CLV3-DR5-E27-LD-SAM7-T5.czi'
            Size = 377764864
            Sha256 = 'fb2f3c745bda7284869448463fd0b94d66264fef608bf592e54d50c73e723133'
        },
        @{
            Name = 'qDII-CLV3-DR5-E27-LD-SAM7-T10.czi'
            Size = 377762912
            Sha256 = '67d53b7894e595c2496a74bbcae51beb0269743de599190b4b56b9dad64027eb'
        }
    )

    foreach ($file in $cziFiles) {
        $target = Join-Path $rawDirectory $file.Name
        $url = 'https://flower.ens-lyon.fr/sam_patterning/data/' + $file.Name
        if (-not ((Test-Path -LiteralPath $target -PathType Leaf) -and ((Get-Item -LiteralPath $target).Length -eq $file.Size))) {
            Write-Host ('Downloading raw CZI with resume: ' + $file.Name)
            & curl.exe --http1.1 -L --fail --retry 20 --retry-all-errors --retry-delay 1 -C - --output $target $url
            if ($LASTEXITCODE -ne 0) {
                throw ('curl failed for ' + $file.Name)
            }
        }
        if ((Get-Item -LiteralPath $target).Length -ne $file.Size) {
            throw ('Size mismatch for ' + $file.Name)
        }
        $actualHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualHash -ne $file.Sha256) {
            throw ('SHA-256 mismatch for ' + $file.Name)
        }
    }

    Write-Host 'Historic six-file E27/SAM7 input layout is complete and SHA-256 validated.'
}
