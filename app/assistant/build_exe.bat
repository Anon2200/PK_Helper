@echo off
rem ============================================================
rem  Сборка автономной программы Assistant.exe (без Python у пользователя)
rem  Требуется: Windows x64 + Python 3.10-3.12
rem  Запуск:    двойной клик или build_exe.bat
rem ============================================================
setlocal
cd /d "%~dp0"

where python >nul 2>nul || where py >nul 2>nul
if errorlevel 1 (
  echo Не найден Python. Установите: winget install Python.Python.3.12
  pause & exit /b 1
)

echo [1/5] Создаю виртуальное окружение venv ...
if not exist venv (
  python -m venv venv 2>nul || py -3 -m venv venv
)
call venv\Scripts\activate.bat

echo [2/5] Обновляю pip и ставлю зависимости (займёт несколько минут) ...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt || (echo Ошибка установки зависимостей & pause & exit /b 1)
pip install "pyinstaller>=6.6" || (echo Ошибка установки PyInstaller & pause & exit /b 1)

echo [3/5] Собираю EXE через assistant.spec ...
pyinstaller assistant.spec --noconfirm --clean || (echo Ошибка сборки & pause & exit /b 1)

echo [4/5] Проверяю результат ...
if not exist dist\Assistant\Assistant.exe (
  echo Файл dist\Assistant\Assistant.exe не найден — сборка не удалась.
  pause & exit /b 1
)

echo [5/5] Готово!
echo   Программа:  dist\Assistant\Assistant.exe  (папку dist\Assistant целиком — это и есть программа)
echo   Ярлык/иконка: assets\icon.ico
echo   Для установщика запустите build_installer.bat (нужен Inno Setup).
echo   На первом запуске программа сама скачает голоса, модель распознавания речи и попросит установить Ollama.
pause
