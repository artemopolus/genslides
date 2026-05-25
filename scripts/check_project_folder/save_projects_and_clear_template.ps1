param (
    [Parameter(Mandatory=$true, HelpMessage="Укажите путь к b-root")]
    [string]$BRoot
)

# 1. Убеждаемся, что в конце пути нет лишних слэшей для корректного извлечения имени
$CleanBRoot = $BRoot.TrimEnd('\').TrimEnd('/')

# 2. Извлекаем имя последней папки
$FolderName = Split-Path $CleanBRoot -Leaf

# 3. Базовый фиксированный путь для a-file
$AFixedPath = "впишите сюда путь к папке session"

# 4. Формируем полный путь к JSON-файлу
$AFile = Join-Path $AFixedPath "$FolderName.json"

# 5. Гарантируем, что b-root заканчивается на обратный слэш (как в вашем примере)
$BRootFinal = $CleanBRoot + "\"

# 6. Собираем итоговую команду
$PythonScript = ".\scripts\check_project_folder\save_projects_and_clear.py"
$Arguments = @(
    "--a-file", $AFile,
    "--b-root", $BRootFinal,
    "--dry-run"
)

# 7. Выводим команду для проверки и запускаем её
Write-Host "Запуск команды:" -ForegroundColor Cyan
Write-Host "python $PythonScript $($Arguments -join ' ')" -ForegroundColor Yellow

& python $PythonScript $Arguments