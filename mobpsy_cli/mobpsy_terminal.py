#!/usr/bin/env python3
from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from case_context import (
    active_case_label,
    register_execution,
    register_export,
)


VERSION = "1.0.0"
EXPORT_DIR = Path.home() / "MobPsy" / "Exportaciones" / "terminal"

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

FG = "\033[38;5;252m"
MUTED = "\033[38;5;245m"
ACCENT = "\033[38;5;81m"
ACCENT_2 = "\033[38;5;117m"
SUCCESS = "\033[38;5;78m"
WARNING = "\033[38;5;221m"
ERROR = "\033[38;5;203m"


def use_color() -> bool:
    return sys.stdout.isatty() and os.environ.get("TERM", "") != "dumb"


if not use_color():
    RESET = BOLD = DIM = FG = MUTED = ACCENT = ACCENT_2 = SUCCESS = WARNING = ERROR = ""


def apply_terminal_theme() -> None:
    """
    Intenta forzar fondo negro y texto claro en terminales compatibles con VTE
    (como GNOME Terminal) usando secuencias OSC.
    """
    if use_color():
        try:
            sys.stdout.write("\033]11;#000000\007")   # fondo
            sys.stdout.write("\033]10;#d0d7de\007")   # texto
            sys.stdout.write("\033]12;#58a6ff\007")   # cursor
            sys.stdout.flush()
        except Exception:
            pass


def clear() -> None:
    os.system("clear")


def width() -> int:
    return min(max(shutil.get_terminal_size((120, 32)).columns, 90), 140)


def hr(char: str = "─") -> str:
    return char * width()


def center(text: str) -> str:
    return text.center(width())


def style(text: str, *tokens: str) -> str:
    return "".join(tokens) + text + RESET


def truncate(text: str, size: int) -> str:
    if len(text) <= size:
        return text
    if size <= 1:
        return text[:size]
    return text[: max(0, size - 1)] + "…"


def banner() -> None:
    w = width()
    print(style("╭" + "─" * (w - 2) + "╮", ACCENT))
    print(style("│", ACCENT) + style(" MOBPSY TERMINAL ".center(w - 2), BOLD, FG) + style("│", ACCENT))
    print(style("│", ACCENT) + style("Interfaz CLI/TUI para las 25 herramientas integradas".center(w - 2), MUTED) + style("│", ACCENT))
    print(style("│", ACCENT) + style(f"Versión {VERSION}".center(w - 2), MUTED) + style("│", ACCENT))
    print(style("╰" + "─" * (w - 2) + "╯", ACCENT))
    print()


def print_box(title: str, lines: list[str], tone: str = ACCENT) -> None:
    w = width()
    print(style("┌" + "─" * (w - 2) + "┐", tone))
    header = f" {title} "
    header = truncate(header, w - 2)
    print(style("│", tone) + style(header.ljust(w - 2), BOLD, FG) + style("│", tone))
    print(style("├" + "─" * (w - 2) + "┤", tone))
    for line in lines:
        for sub in (line.splitlines() or [""]):
            wrapped = textwrap.wrap(sub, width=w - 4) or [""]
            for part in wrapped:
                print(style("│", tone) + " " + part.ljust(w - 4) + " " + style("│", tone))
    print(style("└" + "─" * (w - 2) + "┘", tone))


@dataclass(frozen=True)
class Tool:
    index: int
    name: str
    category: str
    launcher: str
    description: str
    help_args: tuple[str, ...]
    examples: tuple[str, ...]
    guided: Callable[[], list[str] | None] | None = None
    interactive: bool = False
    note: str = ""


def ask(label: str, example: str = "") -> str:
    suffix = f" {style(f'(ej. {example})', MUTED)}" if example else ""
    value = input(f"{style(label, ACCENT, BOLD)}{suffix}: ").strip()
    return value


def username_args(base: list[str]) -> Callable[[], list[str] | None]:
    def inner():
        value = ask("Username", "usuario123")
        return [value, *base] if value else None
    return inner


def email_args(base: list[str]) -> Callable[[], list[str] | None]:
    def inner():
        value = ask("Email", "persona@ejemplo.com")
        return [value, *base] if value else None
    return inner


def domain_args(base: list[str], flag: str = "-d") -> Callable[[], list[str] | None]:
    def inner():
        value = ask("Dominio", "example.com")
        return [flag, value, *base] if value else None
    return inner


def url_args(base: list[str], prefix: list[str] | None = None) -> Callable[[], list[str] | None]:
    def inner():
        value = ask("URL", "https://example.com")
        if not value:
            return None
        return [*(prefix or []), *base, value]
    return inner


def file_args(base: list[str]) -> Callable[[], list[str] | None]:
    def inner():
        value = ask("Ruta del archivo", "/home/mobpsy/Descargas/archivo.jpg")
        return [*base, value] if value else None
    return inner



def ask_domain_any() -> list[str] | None:
    value = ask("Dominio", "example.com")
    return [value] if value else None

def ask_dns_any() -> list[str] | None:
    value = ask("Dominio", "example.com")
    return [value, "ANY"] if value else None

def ask_target_any() -> list[str] | None:
    value = ask("IP, dominio o ASN", "8.8.8.8")
    return [value] if value else None

def ask_ip_any() -> list[str] | None:
    value = ask("IP", "8.8.8.8")
    return [value] if value else None


def crosslinked_guided():
    company = ask("Organización", "Empresa Ejemplo")
    if not company:
        return None
    return ["--search", "bing", "-t", "15", "-j", "2", "-f", "{first}.{last}", company]


def phoneinfoga_guided():
    number = ask("Teléfono con prefijo internacional", "+34 600 000 000")
    return ["scan", "-n", number] if number else None


def social_guided():
    user = ask("Username", "usuario123")
    if not user:
        return None
    return [
        "--username", user,
        "--websites", "all",
        "--mode", "fast",
        "--output", "pretty",
        "--options", "link,rate,title",
        "--method", "find",
        "--filter", "good",
    ]


def photon_guided():
    url = ask("URL", "https://example.com")
    if not url:
        return None
    output = str(Path.home() / "MobPsy" / "Temporal" / "photon-terminal")
    return ["-u", url, "-l", "2", "-t", "2", "--timeout", "5", "-v", "-o", output]


def harvester_guided():
    domain = ask("Dominio", "example.com")
    if not domain:
        return None
    return ["-d", domain, "-b", "crtsh,certspotter,commoncrawl"]


TOOLS = [
    Tool(1, "Sherlock", "Personas", "/usr/local/bin/mobpsy-sherlock",
         "Busca un mismo username en múltiples servicios web.",
         ("--help",),
         ("mobpsy-sherlock usuario123 --print-found --no-color",
          "mobpsy-sherlock usuario123 --site GitHub --site Reddit"),
         username_args(["--print-found", "--no-color"])),

    Tool(2, "Maigret", "Personas", "/usr/local/bin/mobpsy-maigret",
         "Construye un dossier de presencia pública a partir de un username.",
         ("--help",),
         ("mobpsy-maigret usuario123 --no-color --no-progressbar",
          "mobpsy-maigret usuario123 --top-sites 100 --no-color"),
         username_args(["--no-color", "--no-progressbar"])),

    Tool(3, "CrossLinked", "Personas", "/usr/local/bin/mobpsy-crosslinked",
         "Busca nombres públicos asociados a una organización mediante motores de búsqueda.",
         ("-h",),
         ('mobpsy-crosslinked --search bing -f "{first}.{last}" "Empresa Ejemplo"',
          'mobpsy-crosslinked --search bing -t 20 "Empresa Ejemplo"'),
         crosslinked_guided),

    Tool(4, "ClatScope", "Personas", "/usr/local/bin/mobpsy-clatscope",
         "Suite OSINT multipropósito con menú interactivo propio.",
         (),
         ("mobpsy-clatscope",),
         interactive=True,
         note="ClatScope es interactivo y se ejecuta dentro de la propia terminal de MobPsy."),

    Tool(5, "Holehe", "Correos", "/usr/local/bin/mobpsy-holehe",
         "Comprueba si un email parece estar registrado en servicios públicos compatibles.",
         ("--help",),
         ("mobpsy-holehe persona@ejemplo.com --only-used --no-color --no-clear",
          "mobpsy-holehe persona@ejemplo.com --only-used --no-password-recovery"),
         email_args(["--only-used", "--no-color", "--no-clear", "--timeout", "10", "--no-password-recovery"])),

    Tool(6, "ProtOSINT", "Correos", "/usr/local/bin/mobpsy-protosint",
         "Consulta señales públicas asociadas a direcciones Proton Mail en el modo integrado por MobPsy.",
         ("-h",),
         ("mobpsy-protosint persona@proton.me",),
         email_args([]),
         note="La integración actual usa el flujo configurado por MobPsy sin almacenar credenciales Proton."),

    Tool(7, "Zehef", "Correos", "/usr/local/bin/mobpsy-zehef",
         "Busca información pública asociada a una dirección de correo.",
         ("-h",),
         ("mobpsy-zehef persona@ejemplo.com",),
         email_args([])),

    Tool(8, "PhoneInfoga", "Teléfonos", "/usr/local/bin/mobpsy-phoneinfoga",
         "Analiza números internacionales y ejecuta los scanners disponibles de PhoneInfoga.",
         ("--help",),
         ('mobpsy-phoneinfoga scan -n "+34 600 000 000"', "mobpsy-phoneinfoga version"),
         phoneinfoga_guided),

    Tool(9, "Social-Analyzer", "Redes sociales", "/usr/local/bin/mobpsy-social-analyzer",
         "Busca un username en múltiples plataformas.",
         ("--help",),
         ('mobpsy-social-analyzer --username usuario123 --websites all --mode fast --method find --filter good',),
         social_guided),

    Tool(10, "Instaloader", "Redes sociales", "/usr/local/bin/mobpsy-instaloader-profile",
         "Consulta metadatos básicos de un perfil público de Instagram.",
         ("--help",),
         ("mobpsy-instaloader-profile usuarioinstagram",),
         username_args([])),

    Tool(11, "ExifTool", "Multimedia", "/usr/local/bin/mobpsy-exiftool",
         "Extrae metadatos de imágenes, documentos, audio, vídeo y otros formatos.",
         ("-h",),
         ('mobpsy-exiftool -a -G1 -s "/ruta/archivo.jpg"',
          'mobpsy-exiftool -GPSLatitude -GPSLongitude "/ruta/foto.jpg"'),
         file_args(["-a", "-G1", "-s"])),

    Tool(12, "MediaInfo", "Multimedia", "/usr/local/bin/mobpsy-mediainfo",
         "Muestra características técnicas y etiquetas de audio y vídeo.",
         ("--Help",),
         ('mobpsy-mediainfo "/ruta/video.mp4"',
          'mobpsy-mediainfo --Output=JSON "/ruta/video.mp4"'),
         file_args([])),

    Tool(13, "Subfinder", "DNS", "/usr/local/bin/mobpsy-subfinder",
         "Enumeración pasiva de subdominios mediante fuentes públicas.",
         ("-h",),
         ("mobpsy-subfinder -d example.com -silent",
          "mobpsy-subfinder -d example.com -all -silent"),
         domain_args(["-silent"])),

    Tool(14, "DNSRecon", "DNS", "/usr/local/bin/mobpsy-dnsrecon",
         "Enumeración de registros DNS públicos de un dominio.",
         ("-h",),
         ("mobpsy-dnsrecon -d example.com -t std",
          "mobpsy-dnsrecon -d example.com -t axfr"),
         domain_args(["-t", "std"])),

    Tool(15, "dig", "DNS", "/usr/local/bin/mobpsy-dig",
         "Consulta directa de registros DNS específicos.",
         ("-h",),
         ("mobpsy-dig example.com ANY",
          "mobpsy-dig example.com MX +short"),
         guided=ask_dns_any),

    Tool(16, "host", "DNS", "/usr/local/bin/mobpsy-host",
         "Resolución simple de nombres y consultas DNS rápidas.",
         ("-h",),
         ("mobpsy-host example.com",
          "mobpsy-host -t mx example.com"),
         guided=ask_domain_any),

    Tool(17, "Whois", "IPs", "/usr/local/bin/mobpsy-whois",
         "Consulta WHOIS de una IP, dominio o ASN.",
         ("--help",),
         ("mobpsy-whois 8.8.8.8",
          "mobpsy-whois example.com"),
         guided=ask_target_any),

    Tool(18, "GeoIPLookup", "IPs", "/usr/local/bin/mobpsy-geoiplookup",
         "Consulta geolocalización básica de una dirección IP usando la base GeoIP local.",
         ("-h",),
         ("mobpsy-geoiplookup 8.8.8.8",),
         guided=ask_ip_any),

    Tool(19, "WhatWeb", "Web/Infraestructura", "/usr/local/bin/mobpsy-whatweb",
         "Identifica tecnologías visibles de un sitio web.",
         ("--help",),
         ("mobpsy-whatweb -a 1 --color=never https://example.com",
          "mobpsy-whatweb --log-json=resultado.json https://example.com"),
         url_args(["-a", "1", "--color=never"])),

    Tool(20, "WAFW00F", "Web/Infraestructura", "/usr/local/bin/mobpsy-wafw00f",
         "Detecta e intenta identificar un Web Application Firewall.",
         ("--help",),
         ("mobpsy-wafw00f https://example.com",
          "mobpsy-wafw00f -a https://example.com"),
         url_args([]),
         note="Realiza fingerprinting HTTP. Utilízalo solo sobre objetivos autorizados."),

    Tool(21, "Photon", "Web/Infraestructura", "/usr/local/bin/mobpsy-photon",
         "Crawler OSINT que extrae URLs, archivos, correos y otros elementos públicos de un sitio.",
         ("-h",),
         ("mobpsy-photon -u https://example.com -l 2 -t 2 --timeout 5",
          "mobpsy-photon -u https://example.com --only-urls"),
         photon_guided,
         note="El modo guiado limita profundidad e hilos para reducir carga sobre el objetivo."),

    Tool(22, "theHarvester", "Web/Infraestructura", "/usr/local/bin/mobpsy-theharvester",
         "Agrega OSINT de un dominio desde múltiples fuentes públicas.",
         ("-h",),
         ("mobpsy-theharvester -d example.com -b crtsh,certspotter,commoncrawl",
          "mobpsy-theharvester -d example.com -b all"),
         harvester_guided),

    Tool(23, "SpiderFoot", "Frameworks", "/usr/local/bin/mobpsy-spiderfoot-ui",
         "Framework OSINT con interfaz web local y más de 200 módulos.",
         (),
         ("mobpsy-spiderfoot-ui", "Navegador: http://127.0.0.1:5001"),
         guided=lambda: [],
         note="El lanzador inicia SpiderFoot en 127.0.0.1:5001 y abre su interfaz web local."),

    Tool(24, "Recon-ng", "Frameworks", "/usr/local/bin/mobpsy-recon-ng",
         "Framework modular de reconocimiento con workspaces y marketplace.",
         ("-h",),
         ("mobpsy-recon-ng", "Dentro de Recon-ng: marketplace search", "Dentro de Recon-ng: modules search"),
         interactive=True,
         note="Recon-ng conserva su consola interactiva original."),

    Tool(25, "sn0int", "Frameworks", "/usr/local/bin/mobpsy-sn0int",
         "Framework semiautomático OSINT con base de datos y módulos en sandbox.",
         ("--help",),
         ("mobpsy-sn0int", "mobpsy-sn0int --help"),
         interactive=True,
         note="sn0int conserva su consola interactiva original."),
]

BY_INDEX = {tool.index: tool for tool in TOOLS}
CATEGORY_ORDER = ["Personas", "Correos", "Teléfonos", "Redes sociales", "Multimedia", "DNS", "IPs", "Web/Infraestructura", "Frameworks"]


def status_label(tool: Tool) -> str:
    return style("INSTALADA", SUCCESS, BOLD) if os.path.exists(tool.launcher) else style("NO DISPONIBLE", ERROR, BOLD)


def capture_help(tool: Tool) -> str:
    if not tool.help_args:
        return "Esta herramienta no expone una ayuda CLI no interactiva en la integración actual."
    try:
        result = subprocess.run(
            [tool.launcher, *tool.help_args],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=25,
            errors="replace",
        )
        text = result.stdout.strip()
        return text or "(La herramienta no devolvió texto de ayuda.)"
    except FileNotFoundError:
        return f"No se encuentra {tool.launcher}"
    except subprocess.TimeoutExpired:
        return "La ayuda tardó demasiado y fue detenida."
    except Exception as exc:
        return f"No se pudo obtener la ayuda: {exc}"


def render_main() -> None:
    clear()
    banner()

    active = active_case_label()
    pills = [
        style(f"{len(TOOLS)} herramientas", BOLD, FG),
        style("GUI + Terminal", FG),
        style("Ayuda dinámica", FG),
        style("Modo guiado", FG),
        style(f"Caso: {active}" if active else "Sin caso activo", SUCCESS if active else WARNING, BOLD),
    ]
    print(style("  ".join(f"[ {p} ]" for p in pills), ACCENT_2))
    print()

    name_w = 18
    desc_w = width() - 8 - name_w - 6

    for category in CATEGORY_ORDER:
        print(style(f"┌─ {category.upper()} ", ACCENT, BOLD) + style("─" * max(10, width() - len(category) - 6), ACCENT))
        for tool in [t for t in TOOLS if t.category == category]:
            num = style(f"[{tool.index:02d}]", ACCENT_2, BOLD)
            name = style(tool.name.ljust(name_w), BOLD, FG)
            desc = style(truncate(tool.description, desc_w), MUTED)
            print(f"  {num} {name} {desc}")
        print()

    print(style("┌" + "─" * (width() - 2) + "┐", ACCENT))
    footer = (
        f"{style('[D]', ACCENT_2, BOLD)} Diagnóstico   "
        f"{style('[C]', ACCENT_2, BOLD)} Casos   "
        f"{style('[A]', ACCENT_2, BOLD)} IA local   "
        f"{style('[G]', ACCENT_2, BOLD)} Abrir MobPsy gráfico   "
        f"{style('[Q]', ACCENT_2, BOLD)} Salir"
    )
    print(style("│", ACCENT) + " " + truncate(footer, width() - 4).ljust(width() - 4) + " " + style("│", ACCENT))
    print(style("└" + "─" * (width() - 2) + "┘", ACCENT))
    print()


def print_tool_detail(tool: Tool) -> None:
    clear()
    banner()

    print_box(
        f"{tool.name} · {tool.category}",
        [
            f"Estado: {status_label(tool)}",
            f"Launcher: {tool.launcher}",
            "",
            tool.description,
            *(["", f"Nota: {tool.note}"] if tool.note else []),
        ],
    )

    help_text = capture_help(tool)
    print_box("Opciones de uso de la versión instalada", [help_text], ACCENT_2)

    examples = [f"$ {example}" for example in tool.examples]
    print_box("Ejemplos de uso", examples, ACCENT)

    actions = []
    if tool.interactive:
        actions.append("[1] Abrir herramienta interactiva")
        actions.append("[2] Ejecutar con argumentos personalizados")
    else:
        actions.append("[1] Ejecutar modo guiado")
        actions.append("[2] Ejecutar con argumentos personalizados")
        actions.append("[3] Volver a mostrar ayuda")
    actions.append("[0] Volver")
    print_box("Acciones", actions, ACCENT_2)


def save_output(tool: Tool, command: list[str], code: int, output: str) -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c.lower() if c.isalnum() else "_" for c in tool.name).strip("_")
    logfile = EXPORT_DIR / f"{safe_name}_{stamp}.txt"
    logfile.write_text(
        "MobPsy Terminal\n"
        f"Herramienta: {tool.name}\n"
        f"Fecha: {datetime.now().isoformat(timespec='seconds')}\n"
        f"Comando: {shlex.join(command)}\n"
        f"Código de salida: {code}\n"
        + "-" * 70 + "\n"
        + output,
        encoding="utf-8",
    )
    return logfile


def stream_command(tool: Tool, args: list[str], save: bool = True) -> int:
    if not os.path.exists(tool.launcher):
        print(style(f"ERROR: {tool.launcher} no existe.", ERROR, BOLD))
        return 127

    command = [tool.launcher, *args]
    print()
    print_box("Ejecución", [
        f"Comando: {shlex.join(command)}",
        "Pulsa Ctrl+C para detener la ejecución.",
    ])

    if tool.interactive:
        try:
            code = subprocess.call(command)
        except KeyboardInterrupt:
            print()
            code = 130

        case_info = register_execution(
            tool.name,
            command=command,
            interface="terminal",
            exit_code=code,
            status="finished",
        )
        if case_info:
            print(style(
                f"Ejecución registrada en el caso {case_info['case_id']}",
                SUCCESS,
                BOLD,
            ))
        return code

    output_lines: list[str] = []
    try:
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
            bufsize=1,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            print(line, end="")
            output_lines.append(line)
        code = proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except Exception:
            proc.kill()
        code = 130
        print(style("\nEjecución detenida por el usuario.", WARNING, BOLD))
    except Exception as exc:
        print(style(f"Error ejecutando {tool.name}: {exc}", ERROR, BOLD))
        return 1

    if save:
        logfile = save_output(tool, command, code, "".join(output_lines))
        print()
        print(style(f"Salida guardada en: {logfile}", SUCCESS))

        case_info = register_export(
            logfile,
            tool_name=tool.name,
            interface="terminal",
            exit_code=code,
            command=command,
        )
        if case_info:
            print(style(
                f"Vinculada automáticamente al caso {case_info['case_id']}",
                SUCCESS,
                BOLD,
            ))
    return code


def run_guided(tool: Tool) -> None:
    if tool.interactive:
        stream_command(tool, [], save=False)
        return

    if tool.guided is None:
        print(style("Esta herramienta no tiene modo guiado definido.", WARNING))
        return

    args = tool.guided()
    if args is None:
        print(style("Operación cancelada.", WARNING))
        return
    stream_command(tool, args, save=True)


def run_custom(tool: Tool) -> None:
    print()
    print(style("MobPsy añadirá automáticamente el launcher:", MUTED))
    print(style(tool.launcher, BOLD, FG))
    raw = input(style("Argumentos: ", ACCENT, BOLD)).strip()
    try:
        args = shlex.split(raw)
    except ValueError as exc:
        print(style(f"Argumentos no válidos: {exc}", ERROR, BOLD))
        return
    stream_command(tool, args, save=not tool.interactive)


def tool_menu(tool: Tool) -> None:
    while True:
        print_tool_detail(tool)
        choice = input(style("Selecciona opción: ", ACCENT, BOLD)).strip().lower()

        if choice in ("0", "b", "volver"):
            return
        elif choice == "1":
            run_guided(tool)
            input(style("\nPulsa ENTER para continuar...", MUTED))
        elif choice == "2":
            run_custom(tool)
            input(style("\nPulsa ENTER para continuar...", MUTED))
        elif choice == "3" and not tool.interactive:
            continue


def diagnose() -> None:
    clear()
    banner()
    rows = []
    ok = 0
    for tool in TOOLS:
        exists = os.path.exists(tool.launcher)
        if exists:
            ok += 1
        mark = style("✓", SUCCESS, BOLD) if exists else style("✗", ERROR, BOLD)
        rows.append(f"{mark} {tool.name:<18} {tool.launcher}")
    rows.append("")
    rows.append(f"Disponibles: {ok}/{len(TOOLS)}")
    print_box("Diagnóstico rápido", rows)
    input(style("\nPulsa ENTER para volver...", MUTED))



def open_cases() -> None:
    try:
        subprocess.call(["/usr/local/bin/mobpsy-case"])
    except Exception as exc:
        print(style(f"No se pudo abrir el gestor de casos: {exc}", ERROR, BOLD))
        input(style("\nPulsa ENTER para volver...", MUTED))



def open_ai() -> None:
    while True:
        clear(); banner()
        print_box("Analista IA", [
            "1. Resumen estructurado del caso activo",
            "2. Analizar caso activo con Ollama",
            "3. Comprobar estado de la IA",
            "4. Instalar / reparar IA local",
            "0. Volver",
        ])
        choice=input(style("Opción: ", ACCENT, BOLD)).strip()
        if choice=="0": return
        try:
            if choice=="1": subprocess.call(["/usr/local/bin/mobpsy-ai","summary"])
            elif choice=="2":
                q=input(style("Pregunta: ", ACCENT, BOLD)).strip()
                subprocess.call(["/usr/local/bin/mobpsy-ai","ask",q or "Analiza el caso y destaca los hallazgos más relevantes."])
            elif choice=="3": subprocess.call(["/usr/local/bin/mobpsy-ai","status"])
            elif choice=="4": subprocess.call(["/usr/local/bin/mobpsy-ai-setup"])
        except Exception as exc:
            print(style(f"No se pudo ejecutar MobPsy IA: {exc}", ERROR, BOLD))
        input(style("\nPulsa ENTER para continuar...", MUTED))


def open_gui() -> None:
    try:
        subprocess.Popen(["/usr/local/bin/mobpsy"])
        print(style("MobPsy gráfico iniciado.", SUCCESS, BOLD))
    except Exception as exc:
        print(style(f"No se pudo abrir MobPsy: {exc}", ERROR, BOLD))
    input(style("\nPulsa ENTER para volver...", MUTED))


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    apply_terminal_theme()

    while True:
        render_main()
        choice = input(style(f"Elige herramienta [01-{len(TOOLS):02d}] u opción: ", ACCENT, BOLD)).strip().lower()

        if choice in ("q", "quit", "salir", "0"):
            clear()
            return 0
        elif choice == "d":
            diagnose()
        elif choice == "c":
            open_cases()
        elif choice == "a":
            open_ai()
        elif choice == "g":
            open_gui()
        else:
            try:
                index = int(choice)
            except ValueError:
                continue
            tool = BY_INDEX.get(index)
            if tool:
                tool_menu(tool)


if __name__ == "__main__":
    raise SystemExit(main())
