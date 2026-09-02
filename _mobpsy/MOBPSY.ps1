$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
Set-Location $ProjectDir

$Version = (Get-Content (Join-Path $ProjectDir "VERSION.txt") -ErrorAction SilentlyContinue | Select-Object -First 1)
if (-not $Version) { $Version = "1.0.0" }
$VmName = "MobPsy-Workstation"

function Pause-MobPsy {
 Write-Host ""
 Read-Host "Pulsa ENTER para continuar"
}

function Fail([string]$Message) {
 Write-Host ""
 Write-Host "[ERROR] $Message" -ForegroundColor Red
 Pause-MobPsy
 throw $Message
}

function Get-VBoxManage {
 if (Get-Command VBoxManage -ErrorAction SilentlyContinue) {
  return (Get-Command VBoxManage).Source
 }
 $candidate = Join-Path $env:ProgramFiles "Oracle\VirtualBox\VBoxManage.exe"
 if (Test-Path $candidate) { return $candidate }
 return $null
}

function Test-VirtualBox {
 $script:VBoxManage = Get-VBoxManage
 if (-not $script:VBoxManage) { Fail "No se ha encontrado Oracle VirtualBox." }
}

function Test-Vagrant {
 if (-not (Get-Command vagrant -ErrorAction SilentlyContinue)) {
  Fail "No se ha encontrado Vagrant. Solo es necesario para instalar MobPsy desde código."
 }
}

function Test-Prerequisites {
 Test-VirtualBox
 Test-Vagrant
 Write-Host "Vagrant: $(vagrant --version)" -ForegroundColor Green
 Write-Host "VirtualBox: $(& $script:VBoxManage --version)" -ForegroundColor Green
}

function Get-VagrantId {
 $idFile = Join-Path $ProjectDir ".vagrant\machines\default\virtualbox\id"
 if (Test-Path $idFile) {
  return (Get-Content $idFile -Raw).Trim()
 }
 return $null
}

function Test-RegisteredVm {
 Test-VirtualBox
 $raw = (& $script:VBoxManage list vms 2>$null | Out-String)
 return ($raw -match ('"' + [regex]::Escape($VmName) + '"'))
}

function Get-MobPsyMode {
 $id = Get-VagrantId
 if ($id) {
  Test-VirtualBox
  $raw = (& $script:VBoxManage list vms 2>$null | Out-String)
  if ($raw -match [regex]::Escape($id)) { return "SOURCE" }
 }
 if (Test-RegisteredVm) { return "OVA" }
 return "NONE"
}

function Get-VmState {
 Test-VirtualBox
 if (-not (Test-RegisteredVm)) { return "not-created" }
 $raw = (& $script:VBoxManage showvminfo $VmName --machinereadable 2>$null | Out-String)
 if ($raw -match '(?m)^VMState="([^"]+)"') { return $Matches[1] }
 return "unknown"
}

function Show-DetectedMode {
 $mode = Get-MobPsyMode
 $state = Get-VmState
 Write-Host ""
 switch ($mode) {
  "SOURCE" {
   Write-Host "Modo detectado: INSTALACIÓN DESDE CÓDIGO (Vagrant)" -ForegroundColor Green
   Write-Host "Estado VM: $state"
  }
  "OVA" {
   Write-Host "Modo detectado: OVA IMPORTADA" -ForegroundColor Green
   Write-Host "Estado VM: $state"
   Write-Host "La OVA se controla directamente con VirtualBox; no necesita .vagrant." -ForegroundColor DarkGray
  }
  default {
   Write-Host "MobPsy todavía no está instalado/importado." -ForegroundColor Yellow
   Write-Host "Puedes instalarlo desde código con la opción de Instalación." -ForegroundColor DarkGray
  }
 }
 return $mode
}

function Start-Ova {
 Test-VirtualBox
 if (-not (Test-RegisteredVm)) { Fail "No existe una VM importada llamada '$VmName'." }
 $state = Get-VmState
 if ($state -eq "running") {
  Write-Host "MobPsy ya está ejecutándose." -ForegroundColor Green
  return
 }
 Write-Host "Iniciando OVA MobPsy..." -ForegroundColor Cyan
 & $script:VBoxManage startvm $VmName --type gui
 if ($LASTEXITCODE -ne 0) { Fail "VirtualBox no pudo iniciar la OVA." }
}

function Stop-Ova {
 Test-VirtualBox
 if (-not (Test-RegisteredVm)) { Fail "No existe '$VmName'." }
 $state = Get-VmState
 if ($state -ne "running") {
  Write-Host "MobPsy no está ejecutándose." -ForegroundColor Yellow
  return
 }
 Write-Host "Solicitando apagado correcto a Ubuntu..." -ForegroundColor Cyan
 & $script:VBoxManage controlvm $VmName acpipowerbutton | Out-Null
 for ($i=0; $i -lt 60; $i++) {
  Start-Sleep -Seconds 2
  if ((Get-VmState) -ne "running") {
   Write-Host "MobPsy se ha apagado correctamente." -ForegroundColor Green
   return
  }
 }
 Write-Host "Ubuntu no terminó de apagarse en 2 minutos." -ForegroundColor Yellow
 Write-Host "No se realizará un poweroff forzado para evitar corrupción." -ForegroundColor Yellow
}

function Ensure-OvaRunning {
 if ((Get-VmState) -ne "running") {
  Start-Ova
  Start-Sleep -Seconds 10
 }
}

function Invoke-OvaGuestCommand {
 param(
  [Parameter(Mandatory=$true)][string]$Exe,
  [string[]]$Args = @(),
  [string]$Description = "comando dentro de la OVA"
 )
 Ensure-OvaRunning
 $pwd = Read-Host "Contraseña del usuario mobpsy (ENTER = mobpsy)"
 if ([string]::IsNullOrWhiteSpace($pwd)) { $pwd = "mobpsy" }

 Write-Host "Ejecutando $Description..." -ForegroundColor Cyan
 $cmdArgs = @(
  "guestcontrol",$VmName,"run",
  "--exe",$Exe,
  "--username","mobpsy",
  "--password",$pwd,
  "--wait-stdout","--wait-stderr",
  "--"
 ) + $Args
 & $script:VBoxManage @cmdArgs
 if ($LASTEXITCODE -ne 0) {
  Fail "No se pudo ejecutar el comando dentro de la OVA. Comprueba la contraseña y que Guest Additions esté activo."
 }
}

function Get-VirtualBoxMachineFolder {
 $raw = (& $script:VBoxManage list systemproperties 2>$null | Out-String)
 foreach ($line in ($raw -split "`r?`n")) {
 if ($line -match '^\s*Default machine folder:\s*(.+?)\s*$') {
 return $Matches[1].Trim()
 }
 }
 return (Join-Path $env:USERPROFILE "VirtualBox VMs")
}

function Prepare-CleanInstall {
 & vagrant global-status --prune *> $null

 $registered = ((& $script:VBoxManage list vms 2>$null | Out-String) -match '"MobPsy-Workstation"')

 if ($registered) {
 Write-Host ""
 Write-Host "Se ha detectado una instalación de MobPsy." -ForegroundColor Yellow
 $ans = Read-Host "¿Deseas reinstalar MobPsy desde cero? (S/N)"
 if ($ans -notmatch '^[sS]$') { Fail "Instalación cancelada." }

 try { & $script:VBoxManage controlvm "MobPsy-Workstation" poweroff 2>$null | Out-Null } catch {}
 Start-Sleep -Seconds 2
 & $script:VBoxManage unregistervm "MobPsy-Workstation" --delete
 if ($LASTEXITCODE -ne 0) { Fail "VirtualBox no pudo preparar la reinstalación." }
 }

 $vmFolder = Get-VirtualBoxMachineFolder
 $orphan = Join-Path $vmFolder "MobPsy-Workstation"
 if (Test-Path -LiteralPath $orphan) {
 $backup = Join-Path $vmFolder ("MobPsy-Workstation_backup_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
 Write-Host "[INFO] Se ha detectado una carpeta residual de VirtualBox:" -ForegroundColor Yellow
 Write-Host " $orphan" -ForegroundColor DarkGray
 Move-Item -LiteralPath $orphan -Destination $backup -Force
 }

 if (Test-Path ".vagrant") {
 $backup = ".vagrant_backup_" + (Get-Date -Format "yyyyMMdd_HHmmss")
 Write-Host "[INFO] Se ha detectado estado local residual. Se guardará en $backup" -ForegroundColor Yellow
 Move-Item ".vagrant" $backup -Force
 }
}

function Vagrant-UpNoProvision([bool]$Headless = $false) {
 if ($Headless) { $env:MOBPSY_HEADLESS = "1" }
 try {
 & vagrant up --no-provision --provider=virtualbox
 if ($LASTEXITCODE -ne 0) { Fail "No se pudo iniciar/crear la VM." }
 }
 finally {
 Remove-Item Env:MOBPSY_HEADLESS -ErrorAction SilentlyContinue
 }
}

function Provision([string]$Name) {
 Write-Host " -> $Name" -ForegroundColor Cyan
 & vagrant provision --provision-with $Name
 if ($LASTEXITCODE -ne 0) { Fail "Ha fallado la fase '$Name'." }
}

function Reload-MobPsy {
 Write-Host " Reiniciando la VM..." -ForegroundColor DarkGray
 & vagrant reload --no-provision
 if ($LASTEXITCODE -ne 0) { Fail "No se pudo reiniciar la VM." }
}

function Phase([string]$Title, [string[]]$Provisioners, [bool]$ReloadAfter = $false) {
 Write-Host ""
 Write-Host "============================================================" -ForegroundColor Cyan
 Write-Host " $Title" -ForegroundColor Cyan
 Write-Host "============================================================" -ForegroundColor Cyan
 foreach ($p in $Provisioners) { Provision $p }
 if ($ReloadAfter) { Reload-MobPsy }
}

function Install-MobPsy {
 Clear-Host
 Write-Host "============================================================" -ForegroundColor Cyan
 Write-Host " MobPsy $Version - INSTALACIÓN" -ForegroundColor Cyan
 Write-Host "============================================================" -ForegroundColor Cyan
 Write-Host ""
 Write-Host "El instalador configurará automáticamente la workstation y sus" -ForegroundColor White
 Write-Host "componentes. El proceso incluye los reinicios necesarios." -ForegroundColor White
 Write-Host ""

 Test-Prerequisites
 Prepare-CleanInstall

 Write-Host ""
 Write-Host "Preparando Ubuntu base..." -ForegroundColor Cyan
 Vagrant-UpNoProvision $true
 Phase "Instalando Ubuntu Desktop" @("desktop") $false

 Write-Host ""
 Write-Host "Preparando el escritorio gráfico..." -ForegroundColor Cyan
 & vagrant halt
 if ($LASTEXITCODE -ne 0) { Fail "No se pudo apagar la VM tras instalar el escritorio." }
 Vagrant-UpNoProvision $false
 Start-Sleep -Seconds 15

 Phase "Configurando workstation, idioma y navegadores" @("workstation","first_login_silent") $true
 Phase "Instalando Tor Browser" @("tor_browser") $true
 Phase "Instalando aplicación gráfica MobPsy" @("mobpsy_gui_files","mobpsy_gui") $true
 Phase "Configurando resolución e instalando Sherlock" @("display_resolution","sherlock","mobpsy_gui_files","mobpsy_gui") $true
 Phase "Instalando Maigret" @("maigret","mobpsy_gui_files","mobpsy_gui") $true
 Phase "Instalando Holehe" @("holehe","mobpsy_gui_files","mobpsy_gui") $true
 Phase "Instalando PhoneInfoga, ExifTool y MediaInfo" @("phoneinfoga","exiftool","mediainfo","mobpsy_gui_files","mobpsy_gui") $true
 Phase "Instalando Subfinder, DNSRecon y WhatWeb" @("subfinder","dnsrecon","whatweb","mobpsy_gui_files","mobpsy_gui") $true
 Phase "Instalando WAFW00F, Photon y theHarvester" @("wafw00f","photon","theharvester","mobpsy_gui_files","mobpsy_gui") $true
 Phase "Instalando CrossLinked, ProtOSINT y Zehef" @("crosslinked","protosint","zehef","mobpsy_gui_files","mobpsy_gui") $true
 Phase "Instalando ClatScope, Social-Analyzer e Instaloader" @("clatscope","social_analyzer","instaloader","mobpsy_gui_files","mobpsy_gui") $true
 Phase "Instalando SpiderFoot, Recon-ng y sn0int" @("spiderfoot","reconng","sn0int","mobpsy_gui_files","mobpsy_gui") $true
 Phase "Instalando MobPsy Terminal" @("mobpsy_cli_files","terminal_cli") $false
 Phase "Actualizando interfaces MobPsy" @("mobpsy_gui_files","mobpsy_gui","mobpsy_cli_files","terminal_cli") $false
 Phase "Instalando utilidades adicionales de IP y DNS" @("ip_dns_extra","mobpsy_gui_files","mobpsy_gui","mobpsy_cli_files","terminal_cli") $false
 Phase "Configurando marcadores" @("mobpsy_bookmarks_files","browser_bookmarks") $false
 Phase "Instalando extensiones OSINT del navegador" @("browser_extensions") $false
 Phase "Configurando casos y evidencias" @("mobpsy_cases_files","cases","mobpsy_gui_files","mobpsy_gui","mobpsy_cli_files","terminal_cli") $false
 Phase "Activando MobPsy Correlator" @("mobpsy_analysis_files","analysis","mobpsy_gui_files","mobpsy_gui","mobpsy_cli_files","terminal_cli") $true
 Phase "Integrando gestión de casos" @("mobpsy_cases_files","cases","mobpsy_gui_files","mobpsy_gui","mobpsy_cli_files","terminal_cli") $false

 Phase "Ajustando pantalla a alta resolución" @("display_resolution") $true
 Phase "Aplicando identidad visual de MobPsy" @("mobpsy_gui_files","mobpsy_gui","mobpsy_branding_assets","branding") $true
 Phase "Configurando IA local" @("mobpsy_analysis_files","ai_local","mobpsy_gui_files","mobpsy_gui","mobpsy_cli_files","terminal_cli") $true
 Phase "Configurando versiones y GitHub Releases" @("mobpsy_guest_updater_file","versioning","mobpsy_gui_files","mobpsy_gui") $false
 Phase "Aplicando revisión final de interfaces" @("mobpsy_cli_files","terminal_cli","mobpsy_gui_files","mobpsy_gui","mobpsy_branding_assets","branding") $true

 Write-Host ""
 Write-Host "============================================================" -ForegroundColor Cyan
 Write-Host " DIAGNÓSTICO DE INSTALACIÓN" -ForegroundColor Cyan
 Write-Host "============================================================" -ForegroundColor Cyan
 Provision "check"

 # Las mejoras nuevas se aplican solo cuando la instalación original ya ha terminado.
 # Nada anterior a este punto se modifica respecto a MEJORAS_POR_FASES.

 Write-Host ""
 Write-Host "Comprobando MobPsy Correlator..." -ForegroundColor Cyan
 & vagrant ssh -c 'command -v mobpsy-correlate >/dev/null 2>&1; mobpsy-correlate --help >/dev/null 2>&1'
 if ($LASTEXITCODE -ne 0) { Fail "Correlator no ha superado la comprobacion final." }

 Write-Host "Reinicio final..." -ForegroundColor Cyan
 Reload-MobPsy

 Write-Host ""
 Write-Host "============================================================" -ForegroundColor Green
 Write-Host " MOBPSY $Version INSTALADO CORRECTAMENTE" -ForegroundColor Green
 Write-Host "============================================================" -ForegroundColor Green
 Write-Host "Usuario: mobpsy"
 Write-Host "Contraseña: mobpsy"
 Write-Host ""
 Write-Host "" -ForegroundColor DarkGray
 Pause-MobPsy
}


function Require-SourceMode {
 if ((Get-MobPsyMode) -ne "SOURCE") {
  Fail "Esta opción granular solo se usa en instalaciones creadas desde código. En una OVA usa 'Actualizar MobPsy desde GitHub Releases'."
 }
}

function Start-MobPsy {
 $mode = Get-MobPsyMode
 switch ($mode) {
  "SOURCE" {
   Test-Prerequisites
   Write-Host "Iniciando MobPsy..." -ForegroundColor Cyan
   Vagrant-UpNoProvision $false
  }
  "OVA" { Start-Ova }
  default { Fail "MobPsy no está instalado. Usa la opción 'Instalar desde código' o importa la OVA." }
 }
 Pause-MobPsy
}

function Stop-MobPsy {
 $mode = Get-MobPsyMode
 switch ($mode) {
  "SOURCE" {
   Test-Prerequisites
   & vagrant halt
   if ($LASTEXITCODE -ne 0) { Fail "No se pudo apagar la VM." }
  }
  "OVA" { Stop-Ova }
  default { Fail "MobPsy no está instalado/importado." }
 }
 Pause-MobPsy
}

function Diagnostic {
 $mode = Get-MobPsyMode
 switch ($mode) {
  "SOURCE" {
   Test-Prerequisites
   Vagrant-UpNoProvision $false
   Provision "check"
  }
  "OVA" {
   Test-VirtualBox
   Show-DetectedMode | Out-Null
   Write-Host ""
   Write-Host "Comprobación interna de MobPsy:" -ForegroundColor Cyan
   Invoke-OvaGuestCommand -Exe "/bin/bash" -Args @("-lc","command -v mobpsy && command -v mobpsy-cli && command -v mobpsy-correlate && command -v mobpsy-ai && mobpsy-ai status") -Description "diagnóstico"
  }
  default { Fail "MobPsy no está instalado/importado." }
 }
 Pause-MobPsy
}

function UpdateUbuntu {
 Require-SourceMode
 Test-Prerequisites
 Vagrant-UpNoProvision $false
 Provision "system_update"
 Pause-MobPsy
}

function UpdateBookmarks {
 Require-SourceMode
 Test-Prerequisites
 Vagrant-UpNoProvision $false
 Provision "mobpsy_bookmarks_files"
 Provision "browser_bookmarks"
 Pause-MobPsy
}

function UpdateTools {
 Require-SourceMode
 Test-Prerequisites
 Vagrant-UpNoProvision $false
 Write-Host ""
 Write-Host "Actualizando herramientas OSINT..." -ForegroundColor Cyan
 $tools = @("sherlock","maigret","holehe","phoneinfoga","exiftool","mediainfo","subfinder","dnsrecon","whatweb","wafw00f","photon","theharvester","crosslinked","protosint","zehef","clatscope","social_analyzer","instaloader","spiderfoot","reconng","sn0int","ip_dns_extra")
 foreach ($tool in $tools) { Provision $tool }
 Provision "mobpsy_gui_files"; Provision "mobpsy_gui"
 Provision "mobpsy_cli_files"; Provision "terminal_cli"
 Write-Host "Herramientas actualizadas." -ForegroundColor Green
 Pause-MobPsy
}

function CheckUpdates {
 $mode = Get-MobPsyMode
 switch ($mode) {
  "SOURCE" {
   Test-Prerequisites
   Vagrant-UpNoProvision $false
   & vagrant ssh -c "/usr/local/bin/mobpsy-update-check"
   if ($LASTEXITCODE -ne 0) { Fail "No se pudo consultar el actualizador interno." }
  }
  "OVA" {
   Test-VirtualBox
   Invoke-OvaGuestCommand -Exe "/usr/local/bin/mobpsy-update-check" -Description "comprobación de actualizaciones"
  }
  default { Fail "MobPsy no está instalado/importado." }
 }
 Pause-MobPsy
}

function UpdateMobPsy {
 $mode = Get-MobPsyMode
 switch ($mode) {
  "SOURCE" {
   $updater = Join-Path $ScriptDir "release\ACTUALIZAR_DESDE_GITHUB.ps1"
   if (-not (Test-Path $updater)) { Fail "Falta el actualizador público." }
   & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $updater -Version latest
   if ($LASTEXITCODE -ne 0) { Fail "La actualización del proyecto ha fallado." }
  }
  "OVA" {
   Test-VirtualBox
   Invoke-OvaGuestCommand -Exe "/usr/local/bin/mobpsy-update" -Args @("latest") -Description "actualización de MobPsy"
  }
  default { Fail "MobPsy no está instalado/importado." }
 }
 Pause-MobPsy
}

function Show-Help {
 Clear-Host
 Write-Host "============================================================" -ForegroundColor Cyan
 Write-Host " MobPsy - AYUDA" -ForegroundColor Cyan
 Write-Host "============================================================" -ForegroundColor Cyan
 Write-Host ""
 Write-Host "Este único menú funciona de dos formas:" -ForegroundColor White
 Write-Host ""
 Write-Host "OVA IMPORTADA" -ForegroundColor Green
 Write-Host "  - Importa la OVA en VirtualBox con el nombre MobPsy-Workstation."
 Write-Host "  - Ejecuta MOBPSY.bat."
 Write-Host "  - No necesita Vagrant, Vagrantfile ni carpeta .vagrant para arrancar."
 Write-Host ""
 Write-Host "INSTALACIÓN DESDE CÓDIGO" -ForegroundColor Green
 Write-Host "  - Requiere VirtualBox + Vagrant."
 Write-Host "  - Elige 'Instalar MobPsy desde código'."
 Write-Host "  - Vagrant crea localmente la carpeta .vagrant."
 Write-Host ""
 Write-Host "La carpeta .vagrant NUNCA debe subirse a GitHub." -ForegroundColor Yellow
 Write-Host "El Vagrantfile sí se publica porque es necesario para quien instala desde código."
 Write-Host ""
 Pause-MobPsy
}

function Install-FromSource {
 $mode = Get-MobPsyMode
 if ($mode -eq "OVA") {
  Write-Host ""
  Write-Host "Ya existe una OVA de MobPsy importada." -ForegroundColor Yellow
  Write-Host "Instalar desde código reemplazará esa VM si continúas con la reinstalación." -ForegroundColor Yellow
 }
 Install-MobPsy
}

function Show-Menu {
 while ($true) {
  Clear-Host
  Write-Host "============================================================" -ForegroundColor Cyan
  Write-Host " MOBPSY $Version" -ForegroundColor Cyan
  Write-Host " OSINT WORKSTATION" -ForegroundColor Cyan
  Write-Host "============================================================" -ForegroundColor Cyan

  $mode = Get-MobPsyMode
  $modeText = switch ($mode) {
   "SOURCE" { "Código / Vagrant" }
   "OVA"    { "OVA importada" }
   default  { "No instalado" }
  }
  Write-Host " Modo: $modeText   Estado: $(Get-VmState)" -ForegroundColor DarkGray
  Write-Host ""

  Write-Host " INSTALACIÓN Y ESTADO" -ForegroundColor Cyan
  Write-Host " [1] Estado / detectar instalación"
  Write-Host " [2] Instalar MobPsy desde código"
  Write-Host ""
  Write-Host " WORKSTATION" -ForegroundColor Cyan
  Write-Host " [3] Iniciar MobPsy"
  Write-Host " [4] Apagar MobPsy"
  Write-Host " [5] Diagnóstico"
  Write-Host ""
  Write-Host " MANTENIMIENTO" -ForegroundColor Cyan
  Write-Host " [6] Comprobar actualizaciones"
  Write-Host " [7] Actualizar MobPsy desde GitHub Releases"
  Write-Host " [8] Actualizar herramientas (instalación desde código)"
  Write-Host " [9] Actualizar Ubuntu (instalación desde código)"
  Write-Host "[10] Actualizar marcadores (instalación desde código)"
  Write-Host ""
  Write-Host " AYUDA" -ForegroundColor Cyan
  Write-Host "[11] Cómo usar MobPsy / OVA / código"
  Write-Host ""
  Write-Host " [0] Salir"
  Write-Host ""

  $opt = Read-Host "Opción"
  try {
   switch ($opt) {
    "1"  { Show-DetectedMode | Out-Null; Pause-MobPsy }
    "2"  { Install-FromSource }
    "3"  { Start-MobPsy }
    "4"  { Stop-MobPsy }
    "5"  { Diagnostic }
    "6"  { CheckUpdates }
    "7"  { UpdateMobPsy }
    "8"  { UpdateTools }
    "9"  { UpdateUbuntu }
    "10" { UpdateBookmarks }
    "11" { Show-Help }
    "0"  { return }
    default { Write-Host "Opción no válida." -ForegroundColor Yellow; Start-Sleep 1 }
   }
  } catch {
   Write-Host ""
   Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
   Pause-MobPsy
  }
 }
}

Show-Menu
