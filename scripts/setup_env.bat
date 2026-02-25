@echo off
setlocal
chcp 65001 >nul

set ENV_NAME=my_env
set PYTHON_VERSION=3.11
set REQUIREMENTS=..\requirements.txt
set SMOKE_TEST=..\broken_env.py

set CONDA_PATH=C:\Users\lasti\anaconda3\condabin\conda.bat

if not exist "%CONDA_PATH%" (
    echo [ERROR] Не найден conda.bat. Проверьте путь: %CONDA_PATH%
    pause
    exit /b 1
)

echo Используется conda: %CONDA_PATH%

cmd /c ""%CONDA_PATH%" info --envs > temp_envs.txt"
findstr /b /c:"%ENV_NAME%" temp_envs.txt >nul
if %errorlevel%==0 (
    echo Окружение "%ENV_NAME%" уже существует, пропускаем создание.
) else (
    cmd /c ""%CONDA_PATH%" tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main""
    cmd /c ""%CONDA_PATH%" tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r""
    cmd /c ""%CONDA_PATH%" tos accept --override-channels --channel https://repo.anaconda.com/pkgs/msys2""
    echo Окружение "%ENV_NAME%" не найдено. Создаем...
    cmd /c ""%CONDA_PATH%" create -y -n %ENV_NAME% python=%PYTHON_VERSION%""
    if exist "%USERPROFILE%\anaconda3\envs\%ENV_NAME%" (
        echo [OK] Окружение "%ENV_NAME%" создано.
    ) else (
        echo [ERROR] Не удалось создать окружение.
        pause
        exit /b 1
    )
)
del temp_envs.txt

if exist %REQUIREMENTS% (
    echo Устанавливаем зависимости из %REQUIREMENTS%...
    cmd /c ""%CONDA_PATH%" run -n %ENV_NAME% pip install -r %REQUIREMENTS%""
    if %errorlevel% neq 0 (
        echo [ERROR] Ошибка при установке зависимостей.
        pause
        exit /b 1
    )
) else (
    echo [ERROR] Файл %REQUIREMENTS% не найден.
    pause
    exit /b 1
)

if exist %SMOKE_TEST% (
    echo Запускаем smoke test: %SMOKE_TEST%...
    cmd /c ""%CONDA_PATH%" run -n %ENV_NAME% python %SMOKE_TEST%""
    if %errorlevel% neq 0 (
        echo [ERROR] Smoke test не прошел.
        pause
        exit /b 1
    ) else (
        echo [OK] Smoke test прошел.
    )
) else (
    echo [ERROR] Файл smoke test %SMOKE_TEST% не найден.
    pause
    exit /b 1
)

echo [OK] Все шаги выполнены успешно.
pause
exit /b 0