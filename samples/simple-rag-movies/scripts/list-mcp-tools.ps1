$ErrorActionPreference = 'Stop'
$base = 'https://mongo-mcp-server.delightfulstone-4b0d5d27.eastus.azurecontainerapps.io/mcp'
$headers = @{ Accept = 'application/json, text/event-stream' }

$init = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"probe","version":"1.0"}}}'
$resp = Invoke-WebRequest -Uri $base -Method POST -Headers $headers -ContentType 'application/json' -Body $init -UseBasicParsing -TimeoutSec 25
$sid = $resp.Headers['mcp-session-id']
Write-Output "SESSION: $sid"

$initialized = '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}'
Invoke-WebRequest -Uri $base -Method POST -Headers @{ Accept = 'application/json, text/event-stream'; 'mcp-session-id' = $sid } -ContentType 'application/json' -Body $initialized -UseBasicParsing -TimeoutSec 25 | Out-Null

$list = '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
$r2 = Invoke-WebRequest -Uri $base -Method POST -Headers @{ Accept = 'application/json, text/event-stream'; 'mcp-session-id' = $sid } -ContentType 'application/json' -Body $list -UseBasicParsing -TimeoutSec 25
$content = $r2.Content
# SSE format: lines like 'data: {...}'
$dataLine = ($content -split "`n" | Where-Object { $_ -like 'data:*' } | Select-Object -First 1)
if ($dataLine) { $json = $dataLine.Substring(5).Trim() } else { $json = $content }
$obj = $json | ConvertFrom-Json
$obj.result.tools | ForEach-Object { Write-Output $_.name }
