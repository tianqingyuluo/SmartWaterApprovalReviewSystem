@echo off
chcp 65001 > nul
REM SmartWater 数据库初始化脚本（Windows）
REM 用法: init-db.bat [用户名] [密码]

set DB_USER=%1
if "%DB_USER%"=="" set DB_USER=root

set DB_PASSWORD=%2
set DB_NAME=smartwater
set SCRIPT_DIR=%~dp0
set SCHEMA_FILE=%SCRIPT_DIR%schema.sql

echo ========================================
echo SmartWater 数据库初始化
echo ========================================
echo.

if "%DB_PASSWORD%"=="" (
    echo 正在初始化数据库（无密码）...
    mysql -u %DB_USER% < "%SCHEMA_FILE%"
) else (
    echo 正在初始化数据库...
    mysql -u %DB_USER% -p%DB_PASSWORD% < "%SCHEMA_FILE%"
)

if %ERRORLEVEL% EQU 0 (
    echo.
    echo 初始化成功
    echo 数据库名: %DB_NAME%
    echo 数据源脚本: schema.sql
    echo 表: review_task, material_slot, review_result
) else (
    echo.
    echo 初始化失败
    echo 请检查 MySQL 服务、账号密码和 schema.sql 是否可访问
    exit /b 1
)
