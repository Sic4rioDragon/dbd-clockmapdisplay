param(
    [string]$InputDir = "$PSScriptRoot\originals",
    [string]$OutputDir = "$PSScriptRoot\assets\maps",
    [string]$MagickPath = ""
)

$ErrorActionPreference = "Stop"

function Find-Magick {
    param([string]$ExplicitPath)

    if ($ExplicitPath -and (Test-Path $ExplicitPath)) {
        return $ExplicitPath
    }

    $cmd = Get-Command magick -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    $commonPaths = @(
        "C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe",
        "C:\Program Files\ImageMagick-7.1.2-Q16\magick.exe",
        "C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe",
        "C:\Program Files\ImageMagick-7.1.1-Q16\magick.exe",
        "C:\Program Files\ImageMagick-7.1.0-Q16-HDRI\magick.exe",
        "C:\Program Files\ImageMagick-7.1.0-Q16\magick.exe",
        "C:\Program Files\ImageMagick*\magick.exe"
    )

    foreach ($path in $commonPaths) {
        $found = Get-ChildItem -Path $path -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found -and (Test-Path $found.FullName)) {
            return $found.FullName
        }
    }

    return $null
}

function Normalize-Name {
    param([string]$Name)

    $n = $Name.Trim()

    $map = @{
        "Azarovs Resting Place"   = "azarovs-resting-place"
        "Blood Lodge"             = "blood-lodge"
        "Gas Heaven"              = "gas-heaven"
        "Wreckers"                = "wreckers-yard"
        "Wreckers Yard"           = "wreckers-yard"
        "Wretched Shop"           = "wretched-shop"

        "Preschool 1"             = "badham-preschool-i"
        "Preschool 2"             = "badham-preschool-ii"
        "Preschool 3"             = "badham-preschool-iii"
        "Preschool 4"             = "badham-preschool-iv"
        "Preschool 5"             = "badham-preschool-v"

        "Fractured Cowshed"       = "fractured-cowshed"
        "Rancid Abbatoir"         = "rancid-abattoir"
        "Rancid Abattoir"         = "rancid-abattoir"
        "Rotten Fields"           = "rotten-fields"
        "The Thompson House"      = "thompson-house"
        "Thompson House"          = "thompson-house"
        "Torment Creek"           = "torment-creek"

        "Disturbed Ward"          = "disturbed-ward"
        "Father Campbells Chapel" = "father-campbells-chapel"

        "Nostromo Wreckage"       = "nostromo-wreckage"
        "Toba Landing"            = "toba-landing"

        "Dead Sands"              = "dead-sands"
        "Eyrie of Crows"          = "eyrie-of-crows"

        "Coal Tower"              = "coal-tower-i"
        "Coal Tower II"           = "coal-tower-ii"
        "Groaning Storehouse"     = "groaning-storehouse-i"
        "Groaning Storehouse II"  = "groaning-storehouse-ii"
        "Ironworks Of Misery"     = "ironworks-of-misery-i"
        "Ironworks of Misery II"  = "ironworks-of-misery-ii"
        "Shelter Woods"           = "shelter-woods-i"
        "Shelter Woods II"        = "shelter-woods-ii"
        "Suffocation Pit"         = "suffocation-pit-i"
        "Suffocation Pit II"      = "suffocation-pit-ii"

        "Ormond"                  = "mount-ormond-resort-i"
        "Ormond II"               = "mount-ormond-resort-ii"
        "Ormond III"              = "mount-ormond-resort-iii"
        "Ormond Lake Mine"        = "ormond-lake-mine"

        "Dead Dawg Saloon"        = "dead-dawg-saloon"
        "Haddonfield"             = "haddonfield"
        "Hawkins"                 = "hawkins-national-laboratory"
        "Lerys"                   = "lerys-memorial-institute"
        "Midwich"                 = "midwich-elementary-school"
        "THE GAME"                = "the-game"

        "Rpd East Wing"           = "raccoon-city-police-station-east-wing"
        "Rpd West Wing"           = "raccoon-city-police-station-west-wing"

        "Mothers Dwelling"        = "mothers-dwelling"
        "Temple of Purgation"     = "temple-of-purgation"

        "Trickster's Delusion"    = "tricksters-delusion"

        "Grim Pantry"             = "grim-pantry"
        "Pale Rose"               = "pale-rose"

        "Forgotten Ruins"         = "forgotten-ruins"
        "The Shattered Square"    = "shattered-square"

        "Fallen Refuge"           = "fallen-refuge"
        "Freddy Fazbears Pizza"   = "freddy-fazbears-pizza"
        "Garden of Joy"           = "garden-of-joy"
        "Greenville Square"       = "greenville-square"

        "Family Residence"        = "family-residence"
        "Sanctum of Wrath"        = "sanctum-of-wrath"
    }

    if ($map.ContainsKey($n)) {
        return $map[$n]
    }

    $slug = $n.ToLowerInvariant()
    $slug = $slug -replace "[’']", ""
    $slug = $slug -replace "[^a-z0-9]+", "-"
    $slug = $slug.Trim("-")
    return $slug
}

$ResolvedMagick = Find-Magick -ExplicitPath $MagickPath

if (-not $ResolvedMagick) {
    throw @"
ImageMagick not found.

Install ImageMagick 7 and make sure 'magick.exe' is available,
or pass the correct path manually.
"@
}

if (!(Test-Path $InputDir)) {
    throw "InputDir not found: $InputDir"
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
Get-ChildItem -Path $OutputDir -Recurse -File -ErrorAction SilentlyContinue | Remove-Item -Force

$allFiles = Get-ChildItem -Path $InputDir -Recurse -File

foreach ($file in $allFiles) {
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
    $slug = Normalize-Name -Name $baseName
    $outFile = Join-Path $OutputDir ($slug + ".webp")

    Write-Host "Converting: $($file.FullName) -> $($slug).webp"

    & $ResolvedMagick "$($file.FullName)[0]" `
        -trim +repage `
        -fuzz 10% -transparent "#282a42" `
        -fuzz 10% -transparent "#535781" `
        -resize x1280 `
        -quality 90 `
        $outFile
}

Write-Host ""
Write-Host "Done."
Write-Host "ImageMagick: $ResolvedMagick"
Write-Host "Converted files: $OutputDir"