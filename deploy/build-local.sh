#!/usr/bin/env bash
# 在本地/CI 构建可部署 jar（独立目录 .build/server，避免 target 被占用）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/.build/server"

cd "$ROOT/demo/web"
[ -d node_modules ] || npm ci
npm run build

rm -rf "$BUILD"
mkdir -p "$BUILD"
cp "$ROOT/demo/server/pom.xml" "$ROOT/demo/server/mvnw" "$ROOT/demo/server/mvnw.cmd" "$BUILD/"
cp -R "$ROOT/demo/server/.mvn" "$BUILD/"
cp -R "$ROOT/demo/server/src" "$BUILD/"
mkdir -p "$BUILD/src/main/resources/static"
cp -R dist/. "$BUILD/src/main/resources/static/"

cd "$BUILD"
./mvnw -DskipTests package

mkdir -p "$ROOT/deploy/build"
cp target/game24-demo.jar "$ROOT/deploy/build/game24-demo.jar"
echo "构建完成: $ROOT/deploy/build/game24-demo.jar"
