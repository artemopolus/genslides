# 1. Определяем путь к скрипту активации
$activateScript = ".\.venv\Scripts\Activate.ps1"

# 2. Проверяем, активно ли уже виртуальное окружение
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Виртуальное окружение не активно. Активирую..." -ForegroundColor Yellow
    
    # Проверяем, существует ли вообще файл активации по указанному пути
    if (Test-Path $activateScript) {
        # Запускаем активацию (точка перед путем важна, чтобы скрипт выполнился в текущей сессии)
        . $activateScript
    } else {
        Write-Error "Файл активации не найден по пути: $activateScript. Проверьте правильность папки."
        Read-Host -Prompt "Нажмите Enter для выхода"
        exit
    }
} else {
    Write-Host "Виртуальное окружение уже запущено: $env:VIRTUAL_ENV" -ForegroundColor Green
}

# 3. Запуск вашей команды
Write-Host "Запуск genslides..." -ForegroundColor Cyan
python -m genslides --log-level WARNING
