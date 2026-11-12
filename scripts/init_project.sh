#!/bin/bash
# TeleGhost Project Initialization Script
# Создаёт структуру проекта по Clean Architecture

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "=== TeleGhost Project Initialization ==="
echo "Project directory: $PROJECT_DIR"

# Создаём структуру директорий
echo ""
echo "[1/5] Creating directory structure..."

mkdir -p cmd/app
mkdir -p internal/core
mkdir -p internal/repository/sqlite
mkdir -p internal/network/sam
mkdir -p internal/network/embedded
mkdir -p internal/proto
mkdir -p internal/service
mkdir -p pkg/crypto
mkdir -p proto

echo "  ✓ cmd/app          - Application entry point"
echo "  ✓ internal/core    - Business logic and models"
echo "  ✓ internal/repository - Data access layer (SQLite)"
echo "  ✓ internal/network - I2P networking layer"
echo "  ✓ internal/proto   - Generated protobuf code"
echo "  ✓ internal/service - Application services"
echo "  ✓ pkg/crypto       - Cryptographic utilities"
echo "  ✓ proto            - Protocol definitions"

# Инициализация Wails (если ещё не сделано)
echo ""
echo "[2/5] Checking Wails initialization..."

if [ ! -f "wails.json" ]; then
    echo "  Initializing Wails project with Svelte..."
    wails init -n teleghost -t svelte -d .
    echo "  ✓ Wails project initialized"
else
    echo "  ✓ Wails already initialized"
fi

# Инициализация Go модулей
echo ""
echo "[3/5] Initializing Go modules..."

if [ ! -f "go.mod" ]; then
    go mod init teleghost
    echo "  ✓ Go module initialized"
else
    echo "  ✓ Go module already exists"
fi

# Добавляем зависимости
echo ""
echo "[4/5] Adding dependencies..."

go get google.golang.org/protobuf@latest
go get github.com/mattn/go-sqlite3@latest
go get github.com/go-i2p/sam3@latest

echo "  ✓ Dependencies added"

# Генерируем protobuf код (если protoc установлен)
echo ""
echo "[5/5] Generating protobuf code..."

if command -v protoc &> /dev/null; then
    if [ -f "proto/teleghost.proto" ]; then
        protoc --go_out=. --go_opt=paths=source_relative proto/teleghost.proto
        mv proto/*.pb.go internal/proto/ 2>/dev/null || true
        echo "  ✓ Protobuf code generated"
    else
        echo "  ⚠ proto/teleghost.proto not found, skipping generation"
    fi
else
    echo "  ⚠ protoc not installed, skipping protobuf generation"
    echo "  Install: go install google.golang.org/protobuf/cmd/protoc-gen-go@latest"
fi

# Финал
echo ""
echo "=== Initialization Complete ==="
echo ""
echo "Project structure:"
echo ""
find . -type d -name ".*" -prune -o -type d -print | head -20 | sed 's|./||' | sed 's|^|  |'
echo ""
echo "Next steps:"
echo "  1. Run 'wails dev' to start development server"
echo "  2. Implement repository layer in internal/repository/sqlite"
echo "  3. Implement network layer in internal/network/sam"
echo ""
