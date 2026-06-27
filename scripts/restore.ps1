param(
    [Parameter(Mandatory=$true)]
    [string]$BackupPath
)

$backup = Get-Item $BackupPath -ErrorAction Stop

# локальный файл = имя backup без .bak в конце
$localPath = $backup.FullName -replace '\.\d{8}_\d{6}\.bak$', ''

if (-not (Test-Path $localPath)) {
    throw "Local file not found: $localPath"
}

# проверка что файлы в одной папке
if ((Split-Path $backup.FullName) -ne (Split-Path $localPath)) {
    throw "Backup and local file must be in the same directory"
}

# восстановление (перезапись локального)
Copy-Item -Path $backup.FullName -Destination $localPath -Force

Write-Host "Restored: $localPath from $BackupPath"