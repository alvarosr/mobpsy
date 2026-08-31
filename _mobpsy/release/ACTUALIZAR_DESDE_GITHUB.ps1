param([string]$Version='latest')
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$ReleaseDir=Split-Path -Parent $MyInvocation.MyCommand.Path
$InternalDir=Split-Path -Parent $ReleaseDir
$Root=Split-Path -Parent $InternalDir
$Config=Get-Content (Join-Path $ReleaseDir 'release-config.json') -Raw | ConvertFrom-Json
if($Config.github_repo -like 'CAMBIA_ESTO/*'){throw 'Configura primero release\release-config.json o ejecuta RELEASES_MOBPSY.bat -> opcion 1.'}
if(-not (Test-Path (Join-Path $Root 'Vagrantfile'))){throw 'Ejecuta este actualizador desde la raiz de MobPsy.'}

$api = if($Version -eq 'latest'){"https://api.github.com/repos/$($Config.github_repo)/releases/latest"}else{"https://api.github.com/repos/$($Config.github_repo)/releases/tags/v$Version"}
Write-Host '[1/6] Consultando GitHub Releases...' -ForegroundColor Cyan
$r=Invoke-RestMethod -Uri $api -Headers @{'User-Agent'='MobPsy-Updater'}
$tag=$r.tag_name
$ver=$tag -replace '^v',''
$assetName="MobPsy-update-v$ver.zip"
$hashName="$assetName.sha256"
$a=$r.assets|Where-Object name -eq $assetName|Select-Object -First 1
$h=$r.assets|Where-Object name -eq $hashName|Select-Object -First 1
if(-not $a -or -not $h){throw "La release $tag no contiene $assetName y su SHA256."}

$tmp=Join-Path $env:TEMP ('mobpsy_update_'+[guid]::NewGuid().ToString('N'));New-Item -ItemType Directory $tmp|Out-Null
$zip=Join-Path $tmp $assetName;$sha=Join-Path $tmp $hashName
Write-Host "[2/6] Descargando $tag..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $a.browser_download_url -OutFile $zip -UseBasicParsing
Invoke-WebRequest -Uri $h.browser_download_url -OutFile $sha -UseBasicParsing
Write-Host '[3/6] Verificando SHA256...' -ForegroundColor Cyan
$expected=((Get-Content $sha -Raw).Trim().Split()[0]).ToLowerInvariant();$actual=(Get-FileHash $zip -Algorithm SHA256).Hash.ToLowerInvariant()
if($expected -ne $actual){throw 'SHA256 incorrecto. Actualizacion cancelada.'}

$backup=Join-Path $Root ('_backup_release_'+(Get-Date -Format 'yyyyMMdd_HHmmss'));New-Item -ItemType Directory $backup|Out-Null
Write-Host '[4/6] Creando backup de archivos actualizables...' -ForegroundColor Cyan
foreach($item in @('Vagrantfile','MOBPSY.bat','_mobpsy','provision','mobpsy_app','mobpsy_cli','mobpsy_analysis','mobpsy_cases','bookmarks','assets')){
 $p=Join-Path $Root $item;if(Test-Path $p){Copy-Item $p (Join-Path $backup $item) -Recurse -Force}
}

Write-Host '[5/6] Aplicando actualizacion SIN tocar .vagrant ni datos...' -ForegroundColor Cyan
$extract=Join-Path $tmp 'extract';Expand-Archive -LiteralPath $zip -DestinationPath $extract -Force
Get-ChildItem $extract -Force|ForEach-Object{Copy-Item $_.FullName (Join-Path $Root $_.Name) -Recurse -Force}
Write-Host '[6/6] Actualizacion aplicada.' -ForegroundColor Cyan
Write-Host "[OK] MobPsy actualizado a $tag" -ForegroundColor Green
Write-Host "     Backup: $backup"
Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
