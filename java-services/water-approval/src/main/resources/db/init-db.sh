#!/bin/bash
# SmartWater 数据库初始化脚本
# 用法: ./init-db.sh [用户名] [密码]

DB_USER=${1:-root}
DB_PASSWORD=${2:-}
DB_NAME="smartwater"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "========================================"
echo "SmartWater 数据库初始化"
echo "========================================"
echo ""

if [ -z "$DB_PASSWORD" ]; then
    echo "正在初始化数据库（无密码）..."
    mysql -u "$DB_USER" < "$SCRIPT_DIR/init.sql"
else
    echo "正在初始化数据库..."
    mysql -u "$DB_USER" -p"$DB_PASSWORD" < "$SCRIPT_DIR/init.sql"
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 数据库初始化成功！"
    echo "数据库名: $DB_NAME"
    echo "表: review_task, material_slot, review_result"
else
    echo ""
    echo "❌ 数据库初始化失败！"
    echo "请检查 MySQL 服务是否运行，以及用户名密码是否正确。"
    exit 1
fi
