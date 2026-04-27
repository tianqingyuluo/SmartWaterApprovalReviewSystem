@echo off
chcp 65001 > nul
REM SmartWater 数据库初始化脚本（Windows）
REM 用法: init-db.bat [用户名] [密码]

set DB_USER=%1
if "%DB_USER%"=="" set DB_USER=root

set DB_PASSWORD=%2
set DB_NAME=smartwater

set SCRIPT_DIR=%~dp0

echo ========================================
echo SmartWater 数据库初始化
echo ========================================
echo.

if "%DB_PASSWORD%"=="" (
    echo 正在初始化数据库（无密码）...
    mysql -u %DB_USER% < "%SCRIPT_DIR%init.sql"
) else (
    echo 正在初始化数据库...
    mysql -u %DB_USER% -p%DB_PASSWORD% < "%SCRIPT_DIR%init.sql"
)

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 数据库初始化成功！
    echo 数据库名: %DB_NAME%
    echo 表: review_task, material_slot, review_result
) else (
    echo.
    echo ❌ 数据库初始化失败！
    echo 请检查 MySQL 服务是否运行，以及用户名密码是否正确。
    exit /b 1
)
