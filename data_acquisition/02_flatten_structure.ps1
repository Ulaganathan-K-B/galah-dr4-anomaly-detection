# Lower process priority so it runs quietly in the background without lagging your PC

[System.Diagnostics.Process]::GetCurrentProcess().PriorityClass = 'BelowNormal'



$basePath = (Get-Location).Path

$targetComPath = Join-Path $basePath "com"



Write-Host "Running in PASSIVE mode. You can continue using your laptop." -ForegroundColor Cyan



# 1. Ensure the destination com_1 through com_4 folders exist

1..4 | ForEach-Object {

    $targetDir = Join-Path $targetComPath "com_$_"

    if (-not (Test-Path $targetDir)) { New-Item -ItemType Directory -Path $targetDir | Out-Null }

}



# 2. Find all galah folders (galah, galah_0, galah_1, etc.)

$galahFolders = Get-ChildItem -Path $basePath -Directory -Filter "galah*"



foreach ($folder in $galahFolders) {

    # Skip the master 'com' and 'all' folders if they happen to match somehow

    if ($folder.Name -eq "com" -or $folder.Name -eq "all") { continue }



    $sourceComPath = Join-Path $folder.FullName "dr4\spectra\hermes\com"

    

    if (Test-Path $sourceComPath) {

        $fitsFiles = Get-ChildItem -Path $sourceComPath -Filter *.fits -Recurse -File

        

        foreach ($file in $fitsFiles) {

            $baseName = $file.BaseName

            $lastDigit = $baseName.Substring($baseName.Length - 1, 1)



            if ($lastDigit -match "^[1-4]$") {

                $destPath = Join-Path $targetComPath "com_$lastDigit\$($file.Name)"

                

                if (Test-Path $destPath) {

                    # File already exists in target. Delete this duplicate source file.

                    Remove-Item -Path $file.FullName -Force

                } else {

                    # Move the file instantly

                    [System.IO.File]::Move($file.FullName, $destPath)

                }

            }

            # Micro-sleep to yield disk queue to your other laptop tasks

            Start-Sleep -Milliseconds 5

        }



        # 3. Safe Deletion Check

        # Check if ANY .fits files were left behind (e.g. ending in 5, 6, or errors)

        $remainingFiles = Get-ChildItem -Path $sourceComPath -Filter *.fits -Recurse -File

        

        if ($remainingFiles.Count -eq 0) {

            Remove-Item -Path $folder.FullName -Recurse -Force

            Write-Host "Safely processed and deleted: $($folder.Name)" -ForegroundColor DarkGray

        } else {

            Write-Host "Warning: Could not delete $($folder.Name) - $($remainingFiles.Count) .fits files were left behind." -ForegroundColor Yellow

        }

    }

}

Write-Host "`nPassive Integration Complete!" -ForegroundColor Green

