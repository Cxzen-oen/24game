# 在本地（Windows）构建可部署 jar：前端 dist 打进 Spring Boot，再产出 deploy/build/game24-demo.jar
# 使用独立构建目录 .build/server，避免本机 8080 运行中的 jar 被占用
# 用法：powershell -ExecutionPolicy Bypass -File deploy/build-local.ps1
$ErrorActionPreference = 'Stop'
$Root = Resolve-Path (Join-Path $PSScriptRoot '..')
$Build = Join-Path $Root '.build\server'

try {
  Set-Location (Join-Path $Root 'demo\web')
  if (-not (Test-Path 'node_modules')) { npm ci }
  npm run build
  if ($LASTEXITCODE -ne 0) { throw '前端构建失败' }

  if (Test-Path $Build) { Remove-Item $Build -Recurse -Force }
  New-Item -ItemType Directory -Path $Build | Out-Null
  Copy-Item '..\server\pom.xml','..\server\mvnw','..\server\mvnw.cmd' $Build
  Copy-Item '..\server\.mvn' $Build -Recurse
  Copy-Item '..\server\src' $Build -Recurse

  $Static = Join-Path $Build 'src\main\resources\static'
  New-Item -ItemType Directory -Force -Path $Static | Out-Null
  Copy-Item -Path 'dist\*' -Destination $Static -Recurse -Force

  Set-Location $Build
  & .\mvnw.cmd -DskipTests package
  if ($LASTEXITCODE -ne 0) { throw 'Maven 构建失败' }

  $Out = Join-Path $Root 'deploy\build'
  New-Item -ItemType Directory -Force -Path $Out | Out-Null
  Copy-Item 'target\game24-demo.jar' (Join-Path $Out 'game24-demo.jar') -Force
  Write-Host ('构建完成: ' + (Join-Path $Out 'game24-demo.jar'))
} finally {
  # 构建目录保留，便于下次增量；不污染 demo/server/src
}
