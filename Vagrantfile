# -*- mode: ruby -*-
# vi: set ft=ruby :

# MobPsy
# Fase 0: Ubuntu Desktop grÃ¡fico mediante Vagrant + VirtualBox.
# Fase 1: preparar la workstation (idioma, estructura y navegadores bÃ¡sicos).
#
# IMPORTANTE:
# - "desktop" y "workstation" se ejecutan automÃ¡ticamente en una instalaciÃ³n nueva.
# - "system_update" y "check" son tareas manuales y NO se ejecutan en cada arranque.

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/jammy64"
  config.vm.hostname = "mobpsy-workstation"

  # Recursos para IA local. Disco dinÃ¡mico: 64 GB es el mÃ¡ximo virtual.
  # Disco para instalación inicial únicamente.
  # Una VM ya existente NO debe intentar redimensionarse en cada `vagrant up`.
  mobpsy_vagrant_id = File.join(__dir__, ".vagrant", "machines", "default", "virtualbox", "id")
  unless File.exist?(mobpsy_vagrant_id)
    config.vm.disk :disk, size: "64GB", primary: true
  end
  # Seguimos sin depender de carpetas compartidas para que el proyecto sea
  # menos sensible a rutas del host o a Guest Additions.
  config.vm.synced_folder ".", "/vagrant", disabled: true

  config.vm.provider "virtualbox" do |vb|
    vb.name = "MobPsy-Workstation"
    vb.memory = (ENV["MOBPSY_MEMORY_MB"] || "8192").to_i
    vb.cpus = 4

    # Solo la instalaciÃ³n inicial se hace sin mostrar la VM.
    vb.gui = ENV["MOBPSY_HEADLESS"] != "1"

    vb.customize ["modifyvm", :id, "--graphicscontroller", "vmsvga"]
    vb.customize ["modifyvm", :id, "--vram", "128"]
    vb.customize ["modifyvm", :id, "--clipboard-mode", "bidirectional"]
    vb.customize ["modifyvm", :id, "--draganddrop", "bidirectional"]
    vb.customize ["setextradata", :id, "GUI/LastGuestSizeHint", "1440,900"]
  end

  # InstalaciÃ³n base grÃ¡fica que ya hemos validado.
  config.vm.provision "desktop", type: "shell", path: "provision/desktop.sh",
    run: "never"

  # Fase 1: workstation. Idempotente: puede volver a ejecutarse.
  config.vm.provision "workstation", type: "shell", path: "provision/workstation.sh",
    run: "never"



  # Preparacion del primer login visible: espaÃƒÂ±ol, carpetas XDG y sin asistentes.

  config.vm.provision "first_login_silent", type: "shell",

    path: "provision/first_login_silent.sh",

    run: "never"  # Fase 2: Tor Browser oficial.
  config.vm.provision "tor_browser", type: "shell",
    path: "provision/tor_browser.sh",
    run: "never"

  # Fase 3: copiamos la aplicaciÃ³n desde el proyecto al guest.
  # El file provisioner permite mantener el cÃ³digo fuera de los scripts shell.
  config.vm.provision "mobpsy_gui_files", type: "file",
    source: "mobpsy_app",
    destination: "/home/vagrant/mobpsy_app_upload",
    run: "never"

  # DespuÃ©s se instala en /opt/mobpsy usando un venv aislado.
  config.vm.provision "mobpsy_gui", type: "shell",
    path: "provision/mobpsy_gui.sh",
    run: "never"

  # Fase 4: resoluciÃ³n grÃ¡fica preferida.
  config.vm.provision "display_resolution", type: "shell",
    path: "provision/display_resolution.sh",
    run: "never"

  # Fase 4: primera herramienta OSINT real.
  config.vm.provision "sherlock", type: "shell",
    path: "provision/sherlock.sh",
    run: "never"

  # Fase 5: segunda herramienta OSINT del mÃ³dulo Identidad.
  config.vm.provision "maigret", type: "shell",
    path: "provision/maigret.sh",
    run: "never"

  # Fase 6: primera herramienta del mÃ³dulo Correos.
  config.vm.provision "holehe", type: "shell",
    path: "provision/holehe.sh",
    run: "never"

  # Fase 7: tres integraciones en bloque.
  config.vm.provision "phoneinfoga", type: "shell",
    path: "provision/phoneinfoga.sh",
    run: "never"

  config.vm.provision "exiftool", type: "shell",
    path: "provision/exiftool.sh",
    run: "never"

  config.vm.provision "mediainfo", type: "shell",
    path: "provision/mediainfo.sh",
    run: "never"

  # Fase 8: infraestructura.
  config.vm.provision "subfinder", type: "shell",
    path: "provision/subfinder.sh",
    run: "never"

  config.vm.provision "dnsrecon", type: "shell",
    path: "provision/dnsrecon.sh",
    run: "never"

  config.vm.provision "whatweb", type: "shell",
    path: "provision/whatweb.sh",
    run: "never"

  # Fase 9: segundo lote de infraestructura.
  config.vm.provision "wafw00f", type: "shell",
    path: "provision/wafw00f.sh",
    run: "never"

  config.vm.provision "photon", type: "shell",
    path: "provision/photon.sh",
    run: "never"

  config.vm.provision "theharvester", type: "shell",
    path: "provision/theharvester.sh",
    run: "never"

  # Fase 10: identidad y correo.
  config.vm.provision "crosslinked", type: "shell",
    path: "provision/crosslinked.sh",
    run: "never"

  config.vm.provision "protosint", type: "shell",
    path: "provision/protosint.sh",
    run: "never"

  config.vm.provision "zehef", type: "shell",
    path: "provision/zehef.sh",
    run: "never"

  # Fase 11: multipropÃ³sito + redes sociales.
  config.vm.provision "clatscope", type: "shell",
    path: "provision/clatscope.sh",
    run: "never"

  config.vm.provision "social_analyzer", type: "shell",
    path: "provision/social_analyzer.sh",
    run: "never"

  config.vm.provision "instaloader", type: "shell",
    path: "provision/instaloader.sh",
    run: "never"

  # Fase 12: frameworks OSINT.
  config.vm.provision "spiderfoot", type: "shell",
    path: "provision/spiderfoot.sh",
    run: "never"

  config.vm.provision "reconng", type: "shell",
    path: "provision/reconng.sh",
    run: "never"

  config.vm.provision "sn0int", type: "shell",
    path: "provision/sn0int.sh",
    run: "never"

  # Fase 13: interfaz full-terminal de MobPsy.
  config.vm.provision "mobpsy_cli_files", type: "file",
    source: "mobpsy_cli",
    destination: "/home/vagrant/mobpsy_cli_upload",
    run: "never"

  config.vm.provision "terminal_cli", type: "shell",
    path: "provision/terminal_cli.sh",
    run: "never"

  # Fase 15: herramientas adicionales para categorÃ­as IPs y DNS.
  config.vm.provision "ip_dns_extra", type: "shell",
    path: "provision/ip_dns_extra.sh",
    run: "never"

  # Fase 16: catÃ¡logo reproducible de marcadores para Firefox, Chromium y Tor.
  config.vm.provision "mobpsy_bookmarks_files", type: "file",
    source: "bookmarks",
    destination: "/home/vagrant/mobpsy_bookmarks_upload",
    run: "never"

  config.vm.provision "browser_bookmarks", type: "shell",
    path: "provision/browser_bookmarks.sh",
    run: "never"

  # Fase 17: gestor de Casos y Evidencias.
  config.vm.provision "mobpsy_cases_files", type: "file",
    source: "mobpsy_cases",
    destination: "/home/vagrant/mobpsy_cases_upload",
    run: "never"

  config.vm.provision "cases", type: "shell",
    path: "provision/cases.sh",
    run: "never"


  # Assets corporativos: logo de app y wallpaper.

  config.vm.provision "mobpsy_branding_assets", type: "file",

    source: "assets",

    destination: "/home/vagrant/mobpsy_branding_assets_upload",

    run: "never"

  # Identidad visual.
  config.vm.provision "branding", type: "shell",
    path: "provision/branding.sh",
    run: "never"

  # Correlator funcional (backend historico que generaba mobpsy-correlate).

  config.vm.provision "analysis", type: "shell",

    path: "provision/analysis.sh",

    run: "never"

  # IA local.
  config.vm.provision "mobpsy_analysis_files", type: "file",
    source: "mobpsy_analysis",
    destination: "/home/vagrant/mobpsy_analysis_upload",
    run: "never"

  config.vm.provision "ai_local", type: "shell",
    path: "provision/ai_local.sh",
    run: "never"

  # Versionado y GitHub Releases.
  # El actualizador interno es un fichero Python y debe subirse explícitamente
  # porque MobPsy no utiliza carpetas compartidas (/vagrant está deshabilitado).
  config.vm.provision "mobpsy_guest_updater_file", type: "file",
    source: "provision/mobpsy_guest_updater.py",
    destination: "/tmp/mobpsy_guest_updater.py",
    run: "never"

  config.vm.provision "versioning", type: "shell",
    path: "provision/versioning.sh",
    run: "never"


  # ActualizaciÃ³n manual del sistema. Nunca se lanza automÃ¡ticamente.
  config.vm.provision "system_update", type: "shell",
    path: "provision/system_update.sh", run: "never"

  # DiagnÃ³stico manual. Tampoco modifica la mÃ¡quina.
  config.vm.provision "check", type: "shell",
    path: "provision/check.sh", run: "never"

  # Fase 20: extensiones OSINT / ciberseguridad.
  config.vm.provision "browser_extensions", type: "shell",
    path: "provision/browser_extensions.sh",
    run: "never"
end
