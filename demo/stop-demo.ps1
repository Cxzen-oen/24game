# 停止 24 点 Demo：前端(5173)、后端(8080)、数据库(55432)
$ports = @(8080, 5173)
foreach ($port in $ports) {
  $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  if ($conns) {
    foreach ($own in ($conns.OwningProcess | Select-Object -Unique)) {
      $proc = Get-Process -Id $own -ErrorAction SilentlyContinue
      if ($proc) {
        Write-Output ('STOP ' + $port + ' -> pid=' + $own + ' ' + $proc.ProcessName)
        Stop-Process -Id $own -Force -ErrorAction SilentlyContinue
      }
    }
  } else {
    Write-Output ('PORT ' + $port + ' free')
  }
}
Start-Sleep -Seconds 2
foreach ($port in $ports) {
  $c = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  if ($c) { Write-Output ('STILL LISTEN ' + $port) } else { Write-Output ('FREE ' + $port) }
}
$pg = 'C:\Users\cx\.pg0\installation\18.1.0\bin\pg_ctl.exe'
$data = 'C:\Users\cx\pgdata-game24'
if (Test-Path $pg) {
  & $pg -D $data stop -m fast 2>&1 | ForEach-Object { Write-Output ('PG: ' + $_) }
}
