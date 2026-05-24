$SourceDir = "C:\Users\kbula\Downloads"

$DestDir = "C:\Users\kbula\Documents\Data Science Analysis\Project\Data Science Project\galah"



# Ensure destination exists

if (-not (Test-Path $DestDir)) { 

    New-Item -ItemType Directory -Force -Path $DestDir | Out-Null

}



# ---------------------------------------------------------

# HELPER FUNCTION: Safely move and rename if collision occurs

# ---------------------------------------------------------

function Move-WithRename {

    param (

        [string]$ItemPath,

        [string]$TargetFolder

    )

    $Item = Get-Item -Path $ItemPath

    $BaseName = $Item.BaseName

    $Extension = $Item.Extension

    

    # Handle folder names properly (they don't have extensions)

    if ($Item.PSIsContainer) {

        $BaseName = $Item.Name

        $Extension = ""

    }



    $NewPath = Join-Path $TargetFolder ($BaseName + $Extension)

    $Counter = 1



    # If file/folder exists, keep incrementing the number until we find a free name

    while (Test-Path $NewPath) {

        $NewPath = Join-Path $TargetFolder ("{0}_{1}{2}" -f $BaseName, $Counter, $Extension)

        $Counter++

    }



    Move-Item -Path $ItemPath -Destination $NewPath -Force

}



# ---------------------------------------------------------

# STAGE 1: Extract source .tar.gz files and delete them

# ---------------------------------------------------------

Write-Host "--- STAGE 1: Processing Initial Downloads ---" -ForegroundColor Cyan

$InitialFiles = Get-ChildItem -Path $SourceDir -Filter "*.tar.gz"



foreach ($File in $InitialFiles) {

    Write-Host "Extracting: $($File.Name)" -ForegroundColor Yellow

    

    # Create a unique temporary folder to hold the extraction safely

    $TempFolder = Join-Path $DestDir ([guid]::NewGuid().ToString())

    New-Item -ItemType Directory -Force -Path $TempFolder | Out-Null

    

    # Extract to the temp folder

    tar.exe -xzf $File.FullName -C $TempFolder

    

    if ($LASTEXITCODE -eq 0) {

        # Move extracted items safely to the final destination

        $ExtractedItems = Get-ChildItem -Path $TempFolder

        foreach ($Extracted in $ExtractedItems) {

            Move-WithRename -ItemPath $Extracted.FullName -TargetFolder $DestDir

        }

        

        # Cleanup

        Remove-Item -Path $File.FullName -Force

        Write-Host "Success! Deleted original: $($File.Name)" -ForegroundColor Green

    } else {

        Write-Host "Error extracting $($File.Name). Skipping deletion." -ForegroundColor Red

    }

    

    # Destroy the temporary folder

    Remove-Item -Path $TempFolder -Recurse -Force

}





# ---------------------------------------------------------

# STAGE 2: Extract inner archives and delete them

# ---------------------------------------------------------

Write-Host "`n--- STAGE 2: Processing Inner Archive Files ---" -ForegroundColor Cyan



# Look for .tar, .tar.gz, or .gz files

$InnerFiles = Get-ChildItem -Path $DestDir -Include "*.tar", "*.tar.gz", "*.gz" -Recurse



if ($InnerFiles.Count -eq 0) {

    Write-Host "No inner archive files found. Skipping Stage 2." -ForegroundColor DarkGray

}



foreach ($InnerFile in $InnerFiles) {

    Write-Host "Extracting Inner File: $($InnerFile.Name)" -ForegroundColor Yellow

    $InnerFileDir = $InnerFile.DirectoryName

    

    # Create a unique temporary folder

    $TempFolder = Join-Path $InnerFileDir ([guid]::NewGuid().ToString())

    New-Item -ItemType Directory -Force -Path $TempFolder | Out-Null

    

    # Extract using -xzf to force decompression

    tar.exe -xzf $InnerFile.FullName -C $TempFolder

    

    if ($LASTEXITCODE -eq 0) {

        # Move extracted items safely back to the folder the archive was sitting in

        $ExtractedItems = Get-ChildItem -Path $TempFolder

        foreach ($Extracted in $ExtractedItems) {

            Move-WithRename -ItemPath $Extracted.FullName -TargetFolder $InnerFileDir

        }

        

        # Cleanup

        Remove-Item -Path $InnerFile.FullName -Force

        Write-Host "Success! Deleted archive: $($InnerFile.Name)" -ForegroundColor Green

    } else {

        Write-Host "Error extracting $($InnerFile.Name). Skipping deletion." -ForegroundColor Red

    }

    

    # Destroy the temporary folder

    Remove-Item -Path $TempFolder -Recurse -Force

}



Write-Host "`nAll extractions, auto-renaming, and cleanups completed successfully!" -ForegroundColor Cyan