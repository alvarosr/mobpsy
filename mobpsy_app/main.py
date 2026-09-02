from __future__ import annotations

# main.py se carga también mediante importlib durante el smoke test del instalador.
# En ese caso Python NO añade automáticamente /opt/mobpsy/app a sys.path.
# Añadimos primero el directorio de la aplicación y solo después importamos
# los módulos hermanos. Esto evita ModuleNotFoundError en instalaciones limpias.
import sys
from pathlib import Path

APP_SOURCE_DIR = Path(__file__).resolve().parent
if str(APP_SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(APP_SOURCE_DIR))

from mobpsy_runtime_pages import install_mobpsy_functional_pages

import hashlib
import os
import ipaddress
import json
import re
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime

from case_context import (
    active_case_label,
    get_active_case,
    register_execution,
    register_export,
)

from PySide6.QtCore import QProcess, QTimer, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QFont, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QFrame,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


APP_VERSION = "1.0.0"
SHERLOCK_BIN = "/usr/local/bin/mobpsy-sherlock"
MAIGRET_BIN = "/usr/local/bin/mobpsy-maigret"
HOLEHE_BIN = "/usr/local/bin/mobpsy-holehe"
PHONEINFOGA_BIN = "/usr/local/bin/mobpsy-phoneinfoga"
EXIFTOOL_BIN = "/usr/local/bin/mobpsy-exiftool"
MEDIAINFO_BIN = "/usr/local/bin/mobpsy-mediainfo"
SUBFINDER_BIN = "/usr/local/bin/mobpsy-subfinder"
DNSRECON_BIN = "/usr/local/bin/mobpsy-dnsrecon"
WHATWEB_BIN = "/usr/local/bin/mobpsy-whatweb"
WAFW00F_BIN = "/usr/local/bin/mobpsy-wafw00f"
PHOTON_BIN = "/usr/local/bin/mobpsy-photon"
THEHARVESTER_BIN = "/usr/local/bin/mobpsy-theharvester"
CROSSLINKED_BIN = "/usr/local/bin/mobpsy-crosslinked"
PROTOSINT_BIN = "/usr/local/bin/mobpsy-protosint"
ZEHEF_BIN = "/usr/local/bin/mobpsy-zehef"
CLATSCOPE_BIN = "/usr/local/bin/mobpsy-clatscope"
SOCIAL_ANALYZER_BIN = "/usr/local/bin/mobpsy-social-analyzer"
INSTALOADER_BIN = "/usr/local/bin/mobpsy-instaloader-profile"
SPIDERFOOT_BIN = "/usr/local/bin/mobpsy-spiderfoot-ui"
RECONNG_BIN = "/usr/local/bin/mobpsy-recon-ng"
SN0INT_BIN = "/usr/local/bin/mobpsy-sn0int"
MOBPSY_CLI_BIN = "/usr/local/bin/mobpsy-cli"
DIG_BIN = "/usr/local/bin/mobpsy-dig"
HOST_BIN = "/usr/local/bin/mobpsy-host"
WHOIS_BIN = "/usr/local/bin/mobpsy-whois"
GEOIPLOOKUP_BIN = "/usr/local/bin/mobpsy-geoiplookup"
EXPORT_DIR = Path.home() / "MobPsy" / "Exportaciones"
CASES_DIR = Path.home() / "MobPsy" / "Casos"
ACTIVE_CASE_FILE = CASES_DIR / ".active_case.json"
LOGO_PATH = APP_SOURCE_DIR / "assets" / "mobpsy.png"
MOBPSY_AI_BIN = "/usr/local/bin/mobpsy-ai"
MOBPSY_AI_SETUP_BIN = "/usr/local/bin/mobpsy-ai-setup"
UPDATE_CHECK_BIN = "/usr/local/bin/mobpsy-update-check"
UPDATE_REPOSITORY = os.environ.get("MOBPSY_UPDATE_REPOSITORY", "Alvarosr16/MobPsy")
UPDATE_RELEASES_URL = f"https://github.com/{UPDATE_REPOSITORY}/releases"


MANUAL_TEXT = """
MobPsy · Manual de uso
======================

Este manual resume el propósito, la entrada típica y un ejemplo rápido de
cada herramienta integrada. La ayuda detallada y exacta de cada versión
también puede consultarse desde MobPsy Terminal.

PERSONAS
--------

[01] Sherlock
- Qué hace: busca un mismo username en múltiples servicios.
- Entrada típica: username.
- Ejemplo: mobpsy-sherlock usuario123 --print-found --no-color

[02] Maigret
- Qué hace: genera un dossier de presencia pública a partir de un username.
- Entrada típica: username.
- Ejemplo: mobpsy-maigret usuario123 --no-color --no-progressbar

[03] CrossLinked
- Qué hace: relaciona nombres públicos con una organización.
- Entrada típica: nombre de empresa / dominio corporativo.
- Ejemplo: mobpsy-crosslinked --search bing -f "{first}.{last}" "Empresa Ejemplo"

[04] ClatScope
- Qué hace: suite multipropósito con menú interactivo propio.
- Entrada típica: depende del módulo elegido.
- Uso: lanzar la herramienta y usar su menú.

CORREOS
-------

[05] Holehe
- Qué hace: comprueba si un email aparece registrado en servicios compatibles.
- Entrada típica: dirección de correo.
- Ejemplo: mobpsy-holehe persona@ejemplo.com --only-used --no-color --no-clear

[06] ProtOSINT
- Qué hace: consulta señales OSINT asociadas a cuentas Proton.
- Entrada típica: correo Proton.
- Ejemplo: mobpsy-protosint persona@proton.me

[07] Zehef
- Qué hace: busca información pública asociada a un email.
- Entrada típica: dirección de correo.
- Ejemplo: mobpsy-zehef persona@ejemplo.com

TELÉFONOS
---------

[08] PhoneInfoga
- Qué hace: analiza números internacionales y ejecuta scanners de telefonía.
- Entrada típica: teléfono con prefijo internacional.
- Ejemplo: mobpsy-phoneinfoga scan -n "+34 600 000 000"

REDES SOCIALES
--------------

[09] Social-Analyzer
- Qué hace: busca un username en múltiples plataformas.
- Entrada típica: username.
- Ejemplo:
  mobpsy-social-analyzer --username usuario123 --websites all --mode fast
  --method find --filter good

[10] Instaloader
- Qué hace: consulta metadatos básicos de un perfil público de Instagram.
- Entrada típica: username de Instagram.
- Ejemplo: mobpsy-instaloader-profile usuarioinstagram

MULTIMEDIA
----------

[11] ExifTool
- Qué hace: extrae metadatos de archivos.
- Entrada típica: ruta de archivo.
- Ejemplo: mobpsy-exiftool -a -G1 -s "/ruta/archivo.jpg"

[12] MediaInfo
- Qué hace: muestra propiedades técnicas de audio y vídeo.
- Entrada típica: ruta de archivo.
- Ejemplo: mobpsy-mediainfo "/ruta/video.mp4"

DNS
---

[13] Subfinder
- Qué hace: enumeración pasiva de subdominios.
- Entrada típica: dominio.
- Ejemplo: mobpsy-subfinder -d example.com -silent

[14] DNSRecon
- Qué hace: enumera registros DNS y pruebas DNS típicas.
- Entrada típica: dominio.
- Ejemplo: mobpsy-dnsrecon -d example.com -t std

[15] dig
- Qué hace: consulta registros DNS específicos.
- Entrada típica: dominio o nombre de host.
- Ejemplo: mobpsy-dig example.com MX +short

[16] host
- Qué hace: resolución rápida y consultas DNS simples.
- Entrada típica: dominio o nombre de host.
- Ejemplo: mobpsy-host -t mx example.com

IPs
---

[17] Whois
- Qué hace: consulta WHOIS de una IP, dominio o ASN.
- Entrada típica: IP, dominio o ASN.
- Ejemplo: mobpsy-whois 8.8.8.8

[18] GeoIPLookup
- Qué hace: consulta geolocalización básica de una IP.
- Entrada típica: IP.
- Ejemplo: mobpsy-geoiplookup 8.8.8.8

WEB / INFRAESTRUCTURA
---------------------

[19] WhatWeb
- Qué hace: identifica tecnologías visibles de una web.
- Entrada típica: URL.
- Ejemplo: mobpsy-whatweb -a 1 --color=never https://example.com

[20] WAFW00F
- Qué hace: detecta WAF sobre un sitio web.
- Entrada típica: URL.
- Ejemplo: mobpsy-wafw00f https://example.com

[21] Photon
- Qué hace: rastrea un sitio y extrae URLs, correos, archivos y endpoints públicos.
- Entrada típica: URL.
- Ejemplo: mobpsy-photon -u https://example.com -l 2 -t 2 --timeout 5

[22] theHarvester
- Qué hace: recopila información de un dominio desde múltiples fuentes.
- Entrada típica: dominio.
- Ejemplo: mobpsy-theharvester -d example.com -b crtsh,certspotter,commoncrawl

FRAMEWORKS
----------

[23] SpiderFoot
- Qué hace: framework OSINT con interfaz web local.
- Entrada típica: uso desde navegador tras abrir la herramienta.
- URL local: http://127.0.0.1:5001

[24] Recon-ng
- Qué hace: framework modular de reconocimiento.
- Entrada típica: consola interactiva.
- Ejemplo inicial: marketplace search

[25] sn0int
- Qué hace: framework OSINT semiautomático con módulos y base de datos.
- Entrada típica: consola interactiva.
- Ejemplo inicial: --help

RECOMENDACIÓN DE USO
--------------------

1. Si quieres trabajar visualmente, usa la aplicación gráfica.
2. Si quieres ayuda dinámica, ejemplos y ejecución guiada, usa MobPsy Terminal.
3. Para las herramientas más complejas e interactivas (ClatScope, Recon-ng, sn0int),
   la terminal suele ser el flujo más natural.
4. Las nuevas categorías de Personas, DNS e IPs agrupan mejor búsquedas clave del analista.
5. Guarda siempre los resultados relevantes en el expediente/caso correspondiente.
"""



@dataclass(frozen=True)
class Section:
    key: str
    label: str
    title: str
    description: str


SECTIONS = [
    Section("home", "Inicio", "Centro de investigación",
            "MobPsy centraliza herramientas OSINT dentro de una interfaz gráfica."),
    Section("manual", "Manual", "Manual de uso",
            "Guía práctica de las herramientas instaladas y sus ejemplos de uso."),
    Section("identity", "Personas", "Personas e identidad",
            "Investigación de identidades públicas, usernames y organizaciones."),
    Section("email", "Correos", "Correos electrónicos",
            "Investigación OSINT a partir de direcciones de correo electrónico."),
    Section("phone", "Teléfonos", "Teléfonos",
            "Investigación OSINT de números internacionales mediante PhoneInfoga."),
    Section("social", "Redes sociales", "Redes sociales",
            "Búsqueda de perfiles públicos y metadatos sociales."),
    Section("multimedia", "Multimedia", "Multimedia y metadatos",
            "Análisis local de metadatos y características técnicas de archivos."),
    Section("dns", "DNS", "DNS y subdominios",
            "Resolución, registros DNS y enumeración pasiva de subdominios."),
    Section("ips", "IPs", "Direcciones IP",
            "Consultas WHOIS y geolocalización básica de direcciones IP."),
    Section("infra", "Web / Infraestructura", "Web e infraestructura",
            "Tecnologías web, WAF, crawling y recopilación OSINT de dominios."),
    Section("frameworks", "Frameworks", "Frameworks OSINT",
            "Frameworks multipropósito para investigaciones OSINT complejas."),
    Section("cases", "Casos", "Casos y evidencias",
            "Crea investigaciones, conserva evidencias y centraliza exportaciones."),
    Section("correlation", "Correlación", "Correlación",
            "Esta sección será la base de MobPsy Correlator."),
    Section("tools", "Herramientas", "Herramientas instaladas",
            "Aquí se mostrará el estado, versión y mantenimiento de cada herramienta."),
    Section("ai", "IA local", "Analista IA",
            "Análisis de casos mediante Ollama ejecutado localmente."),
    Section("settings", "Configuración", "Configuración",
            "Versión, actualizaciones y preferencias de MobPsy."),
]


STYLE = r"""
QWidget {
    background: #0d1117;
    color: #e6edf3;
    font-family: "Ubuntu", "DejaVu Sans", sans-serif;
    font-size: 14px;
}
QMainWindow { background: #0d1117; }
#sidebar {
    background: #111722;
    border-right: 1px solid #263041;
}
#brand {
    color: #f0f6fc;
    font-size: 26px;
    font-weight: 700;
}
#brandSub {
    color: #8b949e;
    font-size: 11px;
    letter-spacing: 1px;
}
#sectionLabel {
    color: #6e7681;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    padding-top: 12px;
}
QPushButton#navButton {
    background: transparent;
    border: 0;
    border-radius: 8px;
    color: #aeb8c4;
    text-align: left;
    padding: 10px 12px;
    font-size: 13px;
}
QPushButton#navButton:hover {
    background: #172033;
    color: #ffffff;
}
QPushButton#navButton:checked {
    background: #25314a;
    color: #ffffff;
    font-weight: 700;
    border-left: 3px solid #8b5cf6;
}
QPushButton#toolTab {
    background: #151b24;
    border: 1px solid #273244;
    border-radius: 8px;
    color: #aeb8c4;
    padding: 9px 14px;
    font-weight: 600;
}
QPushButton#toolTab:hover {
    background: #1b2430;
    color: white;
}
QPushButton#toolTab:checked {
    background: #6d5dfc;
    border: 1px solid #8b7cff;
    color: white;
}
#pageTitle {
    font-size: 30px;
    font-weight: 700;
    color: #f0f6fc;
}
#pageSubtitle {
    font-size: 14px;
    color: #8b949e;
}
#card {
    background: #151b24;
    border: 1px solid #273244;
    border-radius: 12px;
}
#cardTitle {
    color: #f0f6fc;
    font-size: 16px;
    font-weight: 700;
}
#cardText {
    color: #9da7b3;
    font-size: 12px;
}
#statusOk {
    color: #3fb950;
    font-size: 12px;
    font-weight: 700;
}
#statusPending {
    color: #d29922;
    font-size: 12px;
    font-weight: 700;
}
#placeholder {
    background: #121821;
    border: 1px dashed #303b4d;
    border-radius: 12px;
}
#placeholderTitle {
    color: #c9d1d9;
    font-size: 18px;
    font-weight: 700;
}
#placeholderText {
    color: #7d8590;
    font-size: 13px;
}
#version {
    color: #59636f;
    font-size: 10px;
}

#manualInfo {
    background: #131b27;
    border: 1px solid #273244;
    border-radius: 12px;
}

QListWidget#caseList, QListWidget#evidenceList {
    background: #0a0e14;
    border: 1px solid #273244;
    border-radius: 10px;
    color: #d0d7de;
    padding: 6px;
}
QListWidget#caseList::item, QListWidget#evidenceList::item {
    padding: 8px;
    border-radius: 6px;
}
QListWidget#caseList::item:selected, QListWidget#evidenceList::item:selected {
    background: #25314a;
    color: #ffffff;
}
#caseMeta {
    color: #8b949e;
    font-size: 12px;
}
#activeCase {
    color: #3fb950;
    font-size: 12px;
    font-weight: 700;
}

#manualText {
    background: #0a0e14;
    border: 1px solid #273244;
    border-radius: 10px;
    color: #d0d7de;
    padding: 10px;
    font-family: "Ubuntu Mono", "DejaVu Sans Mono", monospace;
    font-size: 12px;
}
QLineEdit {
    background: #0d1117;
    border: 1px solid #303b4d;
    border-radius: 8px;
    padding: 10px 12px;
    color: #f0f6fc;
    selection-background-color: #6d5dfc;
}
QLineEdit:focus {
    border: 1px solid #8b5cf6;
}
QPushButton#primaryButton {
    background: #6d5dfc;
    border: 0;
    border-radius: 8px;
    color: white;
    padding: 10px 18px;
    font-weight: 700;
}
QPushButton#primaryButton:hover { background: #7c6dfd; }
QPushButton#primaryButton:disabled {
    background: #343a46;
    color: #7d8590;
}
QPushButton#secondaryButton {
    background: #202938;
    border: 1px solid #303b4d;
    border-radius: 8px;
    color: #d0d7de;
    padding: 9px 16px;
}
QPushButton#secondaryButton:hover { background: #293547; }
QPushButton#caseActionButton {
    background: #6d5dfc;
    border: 1px solid #7567fc;
    border-radius: 8px;
    color: white;
    padding: 10px 16px;
    font-weight: 700;
}
QPushButton#caseActionButton:hover {
    background: #7869fd;
    border-color: #8478ff;
}
QPushButton#caseActionButton:pressed {
    background: #5f50e9;
    border-color: #6657ed;
}
QPushButton#caseActionButton:disabled {
    background: #343a46;
    border-color: #3d4450;
    color: #7d8590;
}
QPlainTextEdit {
    background: #0a0e14;
    border: 1px solid #273244;
    border-radius: 8px;
    color: #d0d7de;
    padding: 8px;
    font-family: "Ubuntu Mono", "DejaVu Sans Mono", monospace;
    font-size: 12px;
}
QProgressBar {
    background: #0a0e14;
    border: 1px solid #273244;
    border-radius: 6px;
    min-height: 10px;
    max-height: 10px;
    text-visible: false;
}
QProgressBar::chunk {
    background: #8b5cf6;
    border-radius: 5px;
}
"""


class StatusCard(QFrame):
    def __init__(self, title: str, text: str, status: str, ok: bool = True):
        super().__init__()
        self.setObjectName("card")
        self.setMinimumHeight(122)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(7)

        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        text_label = QLabel(text)
        text_label.setObjectName("cardText")
        text_label.setWordWrap(True)
        status_label = QLabel(status)
        status_label.setObjectName("statusOk" if ok else "statusPending")

        layout.addWidget(title_label)
        layout.addWidget(text_label)
        layout.addStretch(1)
        layout.addWidget(status_label)


class UsernameToolWidget(QWidget):
    URL_RE = re.compile(r"https?://[^\s\]\)>,]+")

    def __init__(self, tool_name: str, executable: str, description: str, extra_args: list[str]):
        super().__init__()
        self.tool_name = tool_name
        self.executable = executable
        self.description = description
        self.extra_args = extra_args
        self.process: QProcess | None = None
        self.urls: list[str] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)
        card_layout.setSpacing(10)

        header = QHBoxLayout()
        name = QLabel(tool_name)
        name.setObjectName("cardTitle")
        self.status = QLabel("● Preparado")
        self.status.setObjectName("statusOk")
        header.addWidget(name)
        header.addStretch(1)
        header.addWidget(self.status)
        card_layout.addLayout(header)

        desc = QLabel(description)
        desc.setObjectName("cardText")
        desc.setWordWrap(True)
        card_layout.addWidget(desc)

        input_row = QHBoxLayout()
        self.username = QLineEdit()
        self.username.setPlaceholderText("Introduce un username")
        self.username.returnPressed.connect(self.start_search)

        self.run_button = QPushButton("Ejecutar")
        self.run_button.setObjectName("primaryButton")
        self.run_button.clicked.connect(self.start_search)

        self.stop_button = QPushButton("Detener")
        self.stop_button.setObjectName("secondaryButton")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_search)

        input_row.addWidget(self.username, 1)
        input_row.addWidget(self.run_button)
        input_row.addWidget(self.stop_button)
        card_layout.addLayout(input_row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        card_layout.addWidget(self.progress)

        self.summary = QLabel("Sin búsquedas ejecutadas.")
        self.summary.setObjectName("cardText")
        card_layout.addWidget(self.summary)

        layout.addWidget(card)

        results_card = QFrame()
        results_card.setObjectName("card")
        results_layout = QVBoxLayout(results_card)
        results_layout.setContentsMargins(20, 18, 20, 18)
        results_layout.setSpacing(8)

        results_header = QHBoxLayout()
        title = QLabel("Resultados")
        title.setObjectName("cardTitle")
        self.open_first_button = QPushButton("Abrir primer resultado")
        self.open_first_button.setObjectName("secondaryButton")
        self.open_first_button.setEnabled(False)
        self.open_first_button.clicked.connect(self.open_first_result)
        results_header.addWidget(title)
        results_header.addStretch(1)
        results_header.addWidget(self.open_first_button)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText(
            f"La salida de {tool_name} aparecerá aquí. No se abrirá ninguna terminal."
        )

        results_layout.addLayout(results_header)
        results_layout.addWidget(self.output, 1)
        layout.addWidget(results_card, 1)

    def _valid_username(self, value: str) -> bool:
        return bool(value) and len(value) <= 100 and not any(ord(ch) < 32 for ch in value)

    def start_search(self):
        value = self.username.text().strip()
        if not self._valid_username(value):
            QMessageBox.warning(
                self, "Username no válido",
                "Introduce un nombre de usuario de entre 1 y 100 caracteres."
            )
            return

        if self.process is not None and self.process.state() != QProcess.ProcessState.NotRunning:
            return

        self.output.clear()
        self.urls.clear()
        self.open_first_button.setEnabled(False)
        self.progress.setRange(0, 0)
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.username.setEnabled(False)
        self.status.setText("● Ejecutando")
        self.status.setObjectName("statusPending")
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)
        self.summary.setText(f"Buscando: {value}")

        self.process = QProcess(self)
        self.process.setProgram(self.executable)
        self.process.setArguments([value, *self.extra_args])
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.finished.connect(self.finished)
        self.process.errorOccurred.connect(self.process_error)
        self.process.start()

    def read_output(self):
        if self.process is None:
            return
        data = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
        if not data:
            return

        self.output.moveCursor(self.output.textCursor().MoveOperation.End)
        self.output.insertPlainText(data)
        self.output.ensureCursorVisible()

        for url in self.URL_RE.findall(data):
            clean = url.rstrip(".,;:")
            if clean not in self.urls:
                self.urls.append(clean)

        self.summary.setText(f"Ejecutando · {len(self.urls)} URL(s) detectada(s)")

    def finished(self, exit_code: int, _exit_status):
        value = self.username.text().strip()
        self.progress.setRange(0, 100)
        self.progress.setValue(100 if exit_code == 0 else 0)
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.username.setEnabled(True)

        if exit_code == 0:
            self.status.setText("● Finalizado")
            self.status.setObjectName("statusOk")
        else:
            self.status.setText(f"● Finalizado con código {exit_code}")
            self.status.setObjectName("statusPending")

        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)

        self.summary.setText(
            f"Búsqueda finalizada · {len(self.urls)} URL(s) detectada(s)"
        )
        self.open_first_button.setEnabled(bool(self.urls))
        self.save_output(value, exit_code)
        self.process = None

    def process_error(self, error):
        if self.process is not None and error == QProcess.ProcessError.FailedToStart:
            QMessageBox.critical(
                self,
                f"No se puede ejecutar {self.tool_name}",
                f"MobPsy no encuentra el lanzador de {self.tool_name}. "
                "Ejecuta el diagnóstico o reprovisiona esta fase."
            )
            self.progress.setRange(0, 100)
            self.progress.setValue(0)
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.username.setEnabled(True)
            self.status.setText("● No disponible")
            self.status.setObjectName("statusPending")
            self.status.style().unpolish(self.status)
            self.status.style().polish(self.status)

    def stop_search(self):
        if self.process is None:
            return
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.terminate()
            if not self.process.waitForFinished(1500):
                self.process.kill()

    def save_output(self, username: str, exit_code: int):
        try:
            EXPORT_DIR.mkdir(parents=True, exist_ok=True)
            safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", username)[:60] or "username"
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prefix = self.tool_name.lower().replace(" ", "_")
            target = EXPORT_DIR / f"{prefix}_{safe}_{stamp}.txt"

            header = (
                f"MobPsy - {self.tool_name}\n"
                f"Usuario: {username}\n"
                f"Fecha: {datetime.now().isoformat(timespec='seconds')}\n"
                f"Código de salida: {exit_code}\n"
                f"URLs detectadas: {len(self.urls)}\n"
                + "-" * 60 + "\n"
            )
            target.write_text(header + self.output.toPlainText(), encoding="utf-8")
            self.summary.setText(self.summary.text() + f" · Guardado en {target.name}")
            case_info = register_export(
                target,
                tool_name=getattr(self, "tool_name", target.stem.split("_")[0]),
                interface="gui",
                exit_code=exit_code,
            )
            if case_info:
                self.summary.setText(
                    self.summary.text() + f" · Caso {case_info['case_id']}"
                )
        except Exception:
            pass

    def open_first_result(self):
        if self.urls:
            QDesktopServices.openUrl(QUrl(self.urls[0]))


class OrganizationToolWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.process: QProcess | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)
        card_layout.setSpacing(10)

        header = QHBoxLayout()
        name = QLabel("CrossLinked")
        name.setObjectName("cardTitle")
        self.status = QLabel("● Preparado")
        self.status.setObjectName("statusOk")
        header.addWidget(name)
        header.addStretch(1)
        header.addWidget(self.status)
        card_layout.addLayout(header)

        desc = QLabel(
            "Busca nombres públicos de empleados asociados a una organización "
            "mediante resultados de motores de búsqueda, sin acceder directamente a LinkedIn."
        )
        desc.setObjectName("cardText")
        desc.setWordWrap(True)
        card_layout.addWidget(desc)

        warning = QLabel(
            "MobPsy utiliza Bing por defecto porque el propio proyecto tiene reportes "
            "recientes de problemas con búsquedas de Google."
        )
        warning.setObjectName("cardText")
        warning.setWordWrap(True)
        card_layout.addWidget(warning)

        row = QHBoxLayout()
        self.company = QLineEdit()
        self.company.setPlaceholderText("Nombre de la organización")
        self.company.returnPressed.connect(self.start)

        self.run_button = QPushButton("Ejecutar")
        self.run_button.setObjectName("primaryButton")
        self.run_button.clicked.connect(self.start)

        self.stop_button = QPushButton("Detener")
        self.stop_button.setObjectName("secondaryButton")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop)

        row.addWidget(self.company, 1)
        row.addWidget(self.run_button)
        row.addWidget(self.stop_button)
        card_layout.addLayout(row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        card_layout.addWidget(self.progress)

        self.summary = QLabel("Sin búsquedas ejecutadas.")
        self.summary.setObjectName("cardText")
        card_layout.addWidget(self.summary)

        layout.addWidget(card)

        results = QFrame()
        results.setObjectName("card")
        results_layout = QVBoxLayout(results)
        results_layout.setContentsMargins(20, 18, 20, 18)

        title = QLabel("Resultados")
        title.setObjectName("cardTitle")
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("La salida de CrossLinked aparecerá aquí.")

        results_layout.addWidget(title)
        results_layout.addWidget(self.output, 1)
        layout.addWidget(results, 1)

    def start(self):
        company = self.company.text().strip()
        if not company or len(company) > 150 or any(ord(c) < 32 for c in company):
            QMessageBox.warning(self, "Organización no válida", "Introduce un nombre de organización válido.")
            return

        if self.process is not None and self.process.state() != QProcess.ProcessState.NotRunning:
            return

        self.output.clear()
        self.progress.setRange(0, 0)
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.company.setEnabled(False)
        self.status.setText("● Ejecutando")
        self.status.setObjectName("statusPending")
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)
        self.summary.setText(f"Organización: {company}")

        self.process = QProcess(self)
        self.process.setProgram(CROSSLINKED_BIN)
        self.process.setArguments([
            "--search", "bing",
            "-t", "15",
            "-j", "2",
            "-f", "{first}.{last}",
            company,
        ])
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.finished.connect(self.finished)
        self.process.errorOccurred.connect(self.process_error)
        self.process.start()

    def read_output(self):
        if self.process is None:
            return
        data = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
        if data:
            self.output.moveCursor(self.output.textCursor().MoveOperation.End)
            self.output.insertPlainText(data)
            self.output.ensureCursorVisible()

    def finished(self, exit_code: int, _exit_status):
        self.read_output()
        company = self.company.text().strip()

        self.progress.setRange(0, 100)
        self.progress.setValue(100 if exit_code == 0 else 0)
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.company.setEnabled(True)
        self.status.setText("● Finalizado" if exit_code == 0 else f"● Código {exit_code}")
        self.status.setObjectName("statusOk" if exit_code == 0 else "statusPending")
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)

        self.summary.setText("Búsqueda finalizada.")
        self.save_output(company, exit_code)
        self.process = None

    def process_error(self, error):
        if self.process is not None and error == QProcess.ProcessError.FailedToStart:
            QMessageBox.critical(self, "CrossLinked no disponible", "Reprovisiona la Fase 10.")
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.company.setEnabled(True)
            self.progress.setRange(0, 100)
            self.progress.setValue(0)

    def stop(self):
        if self.process is not None and self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.terminate()
            if not self.process.waitForFinished(1500):
                self.process.kill()

    def save_output(self, company: str, exit_code: int):
        try:
            EXPORT_DIR.mkdir(parents=True, exist_ok=True)
            safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", company)[:80] or "organization"
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target = EXPORT_DIR / f"crosslinked_{safe}_{stamp}.txt"
            header = (
                "MobPsy - CrossLinked\n"
                f"Organización: {company}\n"
                f"Fecha: {datetime.now().isoformat(timespec='seconds')}\n"
                f"Código de salida: {exit_code}\n"
                + "-" * 60 + "\n"
            )
            target.write_text(header + self.output.toPlainText(), encoding="utf-8")
            self.summary.setText(self.summary.text() + f" · Guardado en {target.name}")
            case_info = register_export(
                target,
                tool_name=getattr(self, "tool_name", target.stem.split("_")[0]),
                interface="gui",
                exit_code=exit_code,
            )
            if case_info:
                self.summary.setText(
                    self.summary.text() + f" · Caso {case_info['case_id']}"
                )
        except Exception:
            pass


class ExternalInteractiveToolWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.process: QProcess | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)
        card_layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("ClatScope")
        title.setObjectName("cardTitle")
        self.status = QLabel("● Preparado")
        self.status.setObjectName("statusOk")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.status)
        card_layout.addLayout(header)

        desc = QLabel(
            "ClatScope es una utilidad OSINT multipropósito con más de 70 funciones. "
            "Su proyecto original funciona mediante un menú interactivo, por lo que MobPsy "
            "lo integra como herramienta externa controlada desde la GUI."
        )
        desc.setObjectName("cardText")
        desc.setWordWrap(True)
        card_layout.addWidget(desc)

        note = QLabel(
            "La versión completa usa varias APIs externas. Algunas funciones requieren "
            "que el analista configure sus propias claves."
        )
        note.setObjectName("cardText")
        note.setWordWrap(True)
        card_layout.addWidget(note)

        row = QHBoxLayout()
        self.launch_button = QPushButton("Abrir ClatScope")
        self.launch_button.setObjectName("primaryButton")
        self.launch_button.clicked.connect(self.launch)
        row.addWidget(self.launch_button)
        row.addStretch(1)
        card_layout.addLayout(row)

        self.summary = QLabel(
            "ClatScope se abrirá en una consola independiente porque su interfaz original es interactiva."
        )
        self.summary.setObjectName("cardText")
        self.summary.setWordWrap(True)
        card_layout.addWidget(self.summary)

        layout.addWidget(card)

        explanation = QFrame()
        explanation.setObjectName("placeholder")
        exp_layout = QVBoxLayout(explanation)
        exp_layout.setContentsMargins(26, 26, 26, 26)

        title2 = QLabel("Integración deliberadamente distinta")
        title2.setObjectName("placeholderTitle")
        text = QLabel(
            "MobPsy mantiene instalación, actualización y acceso centralizado, "
            "pero no reimplementa en esta fase un menú original de más de 70 operaciones."
        )
        text.setObjectName("placeholderText")
        text.setWordWrap(True)

        exp_layout.addWidget(title2)
        exp_layout.addSpacing(8)
        exp_layout.addWidget(text)
        exp_layout.addStretch(1)

        layout.addWidget(explanation, 1)

    def launch(self):
        self.process = QProcess(self)
        self.process.setProgram("gnome-terminal")
        self.process.setArguments([
            "--",
            "bash",
            "-lc",
            f"{CLATSCOPE_BIN}; echo; echo 'Pulsa ENTER para cerrar'; read",
        ])
        self.process.start()
        case_info = register_execution(
            "ClatScope",
            command=[CLATSCOPE_BIN],
            interface="gui",
            status="launched",
        )
        self.summary.setText(
            "ClatScope iniciado."
            + (f" · Caso {case_info['case_id']}" if case_info else "")
        )


class IdentityPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(10)

        title = QLabel("Personas e identidad")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "Sherlock y Maigret trabajan con usernames. CrossLinked permite investigar "
            "personas públicas asociadas a una organización."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(12)

        tabs = QHBoxLayout()
        tabs.setSpacing(8)
        self.sherlock_tab = QPushButton("Sherlock")
        self.maigret_tab = QPushButton("Maigret")
        self.crosslinked_tab = QPushButton("CrossLinked")
        self.clatscope_tab = QPushButton("ClatScope")

        for btn in (self.sherlock_tab, self.maigret_tab, self.crosslinked_tab, self.clatscope_tab):
            btn.setObjectName("toolTab")
            btn.setCheckable(True)
            tabs.addWidget(btn)

        tabs.addStretch(1)
        layout.addLayout(tabs)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.group.addButton(self.sherlock_tab, 0)
        self.group.addButton(self.maigret_tab, 1)
        self.group.addButton(self.crosslinked_tab, 2)
        self.group.addButton(self.clatscope_tab, 3)

        self.stack = QStackedWidget()
        self.sherlock = UsernameToolWidget(
            "Sherlock",
            SHERLOCK_BIN,
            "Busca el mismo username en múltiples plataformas y muestra los perfiles encontrados.",
            ["--print-found", "--no-color"],
        )
        self.maigret = UsernameToolWidget(
            "Maigret",
            MAIGRET_BIN,
            "Construye un dossier de presencia pública a partir de un username.",
            ["--no-color", "--no-progressbar"],
        )
        self.crosslinked = OrganizationToolWidget()
        self.clatscope = ExternalInteractiveToolWidget()

        self.stack.addWidget(self.sherlock)
        self.stack.addWidget(self.maigret)
        self.stack.addWidget(self.crosslinked)
        self.stack.addWidget(self.clatscope)

        self.sherlock_tab.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.maigret_tab.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.crosslinked_tab.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.clatscope_tab.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        self.sherlock_tab.setChecked(True)

        layout.addWidget(self.stack, 1)


class HolehePage(QWidget):
    EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")

    def __init__(self):
        super().__init__()
        self.process: QProcess | None = None
        self.positive_count = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(10)

        title = QLabel("Correos electrónicos")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "Primera herramienta del módulo de correo: Holehe. "
            "Comprueba la presencia de una dirección de email en múltiples servicios públicos."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(14)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)
        card_layout.setSpacing(10)

        header = QHBoxLayout()
        tool_name = QLabel("Holehe")
        tool_name.setObjectName("cardTitle")
        self.status = QLabel("● Preparado")
        self.status.setObjectName("statusOk")
        header.addWidget(tool_name)
        header.addStretch(1)
        header.addWidget(self.status)
        card_layout.addLayout(header)

        desc = QLabel(
            "Introduce un correo y MobPsy ejecutará Holehe en segundo plano. "
            "Por defecto se muestran únicamente servicios en los que la herramienta "
            "detecta que la dirección parece estar registrada."
        )
        desc.setObjectName("cardText")
        desc.setWordWrap(True)
        card_layout.addWidget(desc)

        input_row = QHBoxLayout()
        self.email = QLineEdit()
        self.email.setPlaceholderText("correo@ejemplo.com")
        self.email.returnPressed.connect(self.start_search)

        self.run_button = QPushButton("Ejecutar")
        self.run_button.setObjectName("primaryButton")
        self.run_button.clicked.connect(self.start_search)

        self.stop_button = QPushButton("Detener")
        self.stop_button.setObjectName("secondaryButton")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_search)

        input_row.addWidget(self.email, 1)
        input_row.addWidget(self.run_button)
        input_row.addWidget(self.stop_button)
        card_layout.addLayout(input_row)

        self.no_recovery = QCheckBox(
            "Evitar comprobaciones basadas en recuperación de contraseña"
        )
        self.no_recovery.setChecked(True)
        self.no_recovery.setToolTip(
            "Reduce la cobertura, pero evita los módulos de Holehe que utilizan "
            "flujos de recuperación de contraseña."
        )
        card_layout.addWidget(self.no_recovery)

        warning = QLabel(
            "Nota: los servicios externos cambian y pueden aplicar rate limits. "
            "Los resultados deben verificarse antes de considerarlos concluyentes."
        )
        warning.setObjectName("cardText")
        warning.setWordWrap(True)
        card_layout.addWidget(warning)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        card_layout.addWidget(self.progress)

        self.summary = QLabel("Sin búsquedas ejecutadas.")
        self.summary.setObjectName("cardText")
        card_layout.addWidget(self.summary)

        layout.addWidget(card)

        results_card = QFrame()
        results_card.setObjectName("card")
        results_layout = QVBoxLayout(results_card)
        results_layout.setContentsMargins(20, 18, 20, 18)
        results_layout.setSpacing(8)

        results_title = QLabel("Resultados")
        results_title.setObjectName("cardTitle")

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText(
            "Los resultados de Holehe aparecerán aquí. No se abrirá ninguna terminal."
        )

        results_layout.addWidget(results_title)
        results_layout.addWidget(self.output, 1)
        layout.addWidget(results_card, 1)

    def _valid_email(self, value: str) -> bool:
        return bool(self.EMAIL_RE.fullmatch(value)) and len(value) <= 254

    def start_search(self):
        value = self.email.text().strip()

        if not self._valid_email(value):
            QMessageBox.warning(
                self,
                "Correo no válido",
                "Introduce una dirección de correo válida."
            )
            return

        if self.process is not None and self.process.state() != QProcess.ProcessState.NotRunning:
            return

        self.output.clear()
        self.positive_count = 0
        self.progress.setRange(0, 0)
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.email.setEnabled(False)
        self.no_recovery.setEnabled(False)

        self.status.setText("● Ejecutando")
        self.status.setObjectName("statusPending")
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)
        self.summary.setText(f"Analizando: {value}")

        args = [
            value,
            "--only-used",
            "--no-color",
            "--no-clear",
            "--timeout", "10",
        ]
        if self.no_recovery.isChecked():
            args.append("--no-password-recovery")

        self.process = QProcess(self)
        self.process.setProgram(HOLEHE_BIN)
        self.process.setArguments(args)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.finished.connect(self.finished)
        self.process.errorOccurred.connect(self.process_error)
        self.process.start()

    def read_output(self):
        if self.process is None:
            return

        data = bytes(self.process.readAllStandardOutput()).decode(
            "utf-8", errors="replace"
        )
        if not data:
            return

        self.output.moveCursor(self.output.textCursor().MoveOperation.End)
        self.output.insertPlainText(data)
        self.output.ensureCursorVisible()

        # Con --only-used, los hallazgos positivos aparecen como "[+]".
        self.positive_count += sum(
            1 for line in data.splitlines() if line.strip().startswith("[+]")
        )
        self.summary.setText(
            f"Ejecutando · {self.positive_count} coincidencia(s) positiva(s) mostrada(s)"
        )

    def finished(self, exit_code: int, _exit_status):
        value = self.email.text().strip()

        # Leer cualquier salida que haya quedado en el buffer.
        self.read_output()

        self.progress.setRange(0, 100)
        self.progress.setValue(100 if exit_code == 0 else 0)
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.email.setEnabled(True)
        self.no_recovery.setEnabled(True)

        if exit_code == 0:
            self.status.setText("● Finalizado")
            self.status.setObjectName("statusOk")
        else:
            self.status.setText(f"● Finalizado con código {exit_code}")
            self.status.setObjectName("statusPending")

        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)

        self.summary.setText(
            f"Búsqueda finalizada · {self.positive_count} coincidencia(s) positiva(s)"
        )
        self.save_output(value, exit_code)
        self.process = None

    def process_error(self, error):
        if self.process is not None and error == QProcess.ProcessError.FailedToStart:
            QMessageBox.critical(
                self,
                "No se puede ejecutar Holehe",
                "MobPsy no encuentra el lanzador de Holehe. "
                "Ejecuta el diagnóstico o reprovisiona la Fase 6."
            )
            self.progress.setRange(0, 100)
            self.progress.setValue(0)
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.email.setEnabled(True)
            self.no_recovery.setEnabled(True)
            self.status.setText("● No disponible")
            self.status.setObjectName("statusPending")
            self.status.style().unpolish(self.status)
            self.status.style().polish(self.status)

    def stop_search(self):
        if self.process is None:
            return

        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.terminate()
            if not self.process.waitForFinished(1500):
                self.process.kill()

    def save_output(self, email: str, exit_code: int):
        try:
            EXPORT_DIR.mkdir(parents=True, exist_ok=True)
            safe = re.sub(r"[^A-Za-z0-9_.@+-]+", "_", email)[:100] or "email"
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target = EXPORT_DIR / f"holehe_{safe}_{stamp}.txt"

            header = (
                "MobPsy - Holehe\n"
                f"Correo: {email}\n"
                f"Fecha: {datetime.now().isoformat(timespec='seconds')}\n"
                f"Código de salida: {exit_code}\n"
                f"Coincidencias positivas: {self.positive_count}\n"
                f"Recuperación de contraseña desactivada: "
                f"{'sí' if self.no_recovery.isChecked() else 'no'}\n"
                + "-" * 60 + "\n"
            )

            target.write_text(
                header + self.output.toPlainText(),
                encoding="utf-8"
            )
            self.summary.setText(
                self.summary.text() + f" · Guardado en {target.name}"
            )
            case_info = register_export(
                target,
                tool_name=getattr(self, "tool_name", target.stem.split("_")[0]),
                interface="gui",
                exit_code=exit_code,
            )
            if case_info:
                self.summary.setText(
                    self.summary.text() + f" · Caso {case_info['case_id']}"
                )
        except Exception:
            pass


class EmailProcessWidget(QWidget):
    EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")

    def __init__(
        self,
        tool_name: str,
        executable: str,
        description: str,
        argument_builder,
        warning_text: str = "",
    ):
        super().__init__()
        self.tool_name = tool_name
        self.executable = executable
        self.description = description
        self.argument_builder = argument_builder
        self.warning_text = warning_text
        self.process: QProcess | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)
        card_layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel(tool_name)
        title.setObjectName("cardTitle")
        self.status = QLabel("● Preparado")
        self.status.setObjectName("statusOk")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.status)
        card_layout.addLayout(header)

        desc = QLabel(description)
        desc.setObjectName("cardText")
        desc.setWordWrap(True)
        card_layout.addWidget(desc)

        if warning_text:
            warning = QLabel(warning_text)
            warning.setObjectName("cardText")
            warning.setWordWrap(True)
            card_layout.addWidget(warning)

        row = QHBoxLayout()
        self.email = QLineEdit()
        self.email.setPlaceholderText("correo@ejemplo.com")
        self.email.returnPressed.connect(self.start)

        self.run_button = QPushButton("Ejecutar")
        self.run_button.setObjectName("primaryButton")
        self.run_button.clicked.connect(self.start)

        self.stop_button = QPushButton("Detener")
        self.stop_button.setObjectName("secondaryButton")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop)

        row.addWidget(self.email, 1)
        row.addWidget(self.run_button)
        row.addWidget(self.stop_button)
        card_layout.addLayout(row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        card_layout.addWidget(self.progress)

        self.summary = QLabel("Sin búsquedas ejecutadas.")
        self.summary.setObjectName("cardText")
        card_layout.addWidget(self.summary)

        layout.addWidget(card)

        results = QFrame()
        results.setObjectName("card")
        results_layout = QVBoxLayout(results)
        results_layout.setContentsMargins(20, 18, 20, 18)

        title = QLabel("Resultados")
        title.setObjectName("cardTitle")
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText(f"La salida de {tool_name} aparecerá aquí.")

        results_layout.addWidget(title)
        results_layout.addWidget(self.output, 1)
        layout.addWidget(results, 1)

    def start(self):
        value = self.email.text().strip()
        if not self.EMAIL_RE.fullmatch(value) or len(value) > 254:
            QMessageBox.warning(self, "Correo no válido", "Introduce una dirección de correo válida.")
            return

        if self.process is not None and self.process.state() != QProcess.ProcessState.NotRunning:
            return

        self.output.clear()
        self.progress.setRange(0, 0)
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.email.setEnabled(False)
        self.status.setText("● Ejecutando")
        self.status.setObjectName("statusPending")
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)
        self.summary.setText(f"Analizando: {value}")

        self.process = QProcess(self)
        self.process.setProgram(self.executable)
        self.process.setArguments(self.argument_builder(value))
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.finished.connect(self.finished)
        self.process.errorOccurred.connect(self.process_error)
        self.process.start()

    def read_output(self):
        if self.process is None:
            return
        data = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
        if data:
            self.output.moveCursor(self.output.textCursor().MoveOperation.End)
            self.output.insertPlainText(data)
            self.output.ensureCursorVisible()

    def finished(self, exit_code: int, _exit_status):
        self.read_output()
        value = self.email.text().strip()
        self.progress.setRange(0, 100)
        self.progress.setValue(100 if exit_code == 0 else 0)
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.email.setEnabled(True)
        self.status.setText("● Finalizado" if exit_code == 0 else f"● Código {exit_code}")
        self.status.setObjectName("statusOk" if exit_code == 0 else "statusPending")
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)
        self.summary.setText("Búsqueda finalizada.")
        self.save_output(value, exit_code)
        self.process = None

    def process_error(self, error):
        if self.process is not None and error == QProcess.ProcessError.FailedToStart:
            QMessageBox.critical(self, f"{self.tool_name} no disponible", "Reprovisiona la Fase 10.")
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.email.setEnabled(True)
            self.progress.setRange(0, 100)
            self.progress.setValue(0)

    def stop(self):
        if self.process is not None and self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.terminate()
            if not self.process.waitForFinished(1500):
                self.process.kill()

    def save_output(self, email: str, exit_code: int):
        try:
            EXPORT_DIR.mkdir(parents=True, exist_ok=True)
            safe = re.sub(r"[^A-Za-z0-9_.@+-]+", "_", email)[:100] or "email"
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prefix = self.tool_name.lower().replace(" ", "")
            target = EXPORT_DIR / f"{prefix}_{safe}_{stamp}.txt"
            header = (
                f"MobPsy - {self.tool_name}\n"
                f"Correo: {email}\n"
                f"Fecha: {datetime.now().isoformat(timespec='seconds')}\n"
                f"Código de salida: {exit_code}\n"
                + "-" * 60 + "\n"
            )
            target.write_text(header + self.output.toPlainText(), encoding="utf-8")
            self.summary.setText(self.summary.text() + f" · Guardado en {target.name}")
            case_info = register_export(
                target,
                tool_name=getattr(self, "tool_name", target.stem.split("_")[0]),
                interface="gui",
                exit_code=exit_code,
            )
            if case_info:
                self.summary.setText(
                    self.summary.text() + f" · Caso {case_info['case_id']}"
                )
        except Exception:
            pass


class EmailPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(10)

        title = QLabel("Correos electrónicos")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "Holehe, ProtOSINT y Zehef ofrecen enfoques complementarios para investigar "
            "la presencia pública de una dirección de correo."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(12)

        tabs = QHBoxLayout()
        self.holehe_tab = QPushButton("Holehe")
        self.protosint_tab = QPushButton("ProtOSINT")
        self.zehef_tab = QPushButton("Zehef")

        for button in (self.holehe_tab, self.protosint_tab, self.zehef_tab):
            button.setObjectName("toolTab")
            button.setCheckable(True)
            tabs.addWidget(button)
        tabs.addStretch(1)
        layout.addLayout(tabs)

        group = QButtonGroup(self)
        group.setExclusive(True)
        group.addButton(self.holehe_tab, 0)
        group.addButton(self.protosint_tab, 1)
        group.addButton(self.zehef_tab, 2)
        self._group = group

        self.stack = QStackedWidget()

        # Reutilizamos la integración ya validada de Holehe.
        self.holehe = HolehePage()

        self.protosint = EmailProcessWidget(
            "ProtOSINT",
            PROTOSINT_BIN,
            "Consulta señales públicas de Proton Mail en modo API/key-server, "
            "sin pedir ni almacenar credenciales Proton.",
            lambda email: [email],
            "Este modo sin Selenium es indicativo. El propio proyecto considera la "
            "validación Selenium con una sesión Proton el método más fiable."
        )

        self.zehef = EmailProcessWidget(
            "Zehef",
            ZEHEF_BIN,
            "Busca información pública asociada a un email en servicios, pastes y fuentes externas.",
            lambda email: [email],
            "Zehef depende de múltiples servicios externos; algunos módulos pueden dejar de "
            "funcionar cuando esos servicios cambian."
        )

        self.stack.addWidget(self.holehe)
        self.stack.addWidget(self.protosint)
        self.stack.addWidget(self.zehef)

        self.holehe_tab.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.protosint_tab.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.zehef_tab.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.holehe_tab.setChecked(True)

        layout.addWidget(self.stack, 1)


class PhoneInfogaPage(QWidget):
    PHONE_RE = re.compile(r"^\+[0-9][0-9 ()\-]{5,30}$")

    def __init__(self):
        super().__init__()
        self.process: QProcess | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(10)

        title = QLabel("Teléfonos")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "PhoneInfoga analiza números internacionales y centraliza información "
            "de sus scanners disponibles."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(14)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)
        card_layout.setSpacing(10)

        header = QHBoxLayout()
        tool = QLabel("PhoneInfoga")
        tool.setObjectName("cardTitle")
        self.status = QLabel("● Preparado")
        self.status.setObjectName("statusOk")
        header.addWidget(tool)
        header.addStretch(1)
        header.addWidget(self.status)
        card_layout.addLayout(header)

        desc = QLabel(
            "Introduce el número con prefijo internacional, por ejemplo +34. "
            "Los scanners que requieren credenciales externas solo funcionarán "
            "cuando estén configurados."
        )
        desc.setObjectName("cardText")
        desc.setWordWrap(True)
        card_layout.addWidget(desc)

        input_row = QHBoxLayout()
        self.number = QLineEdit()
        self.number.setPlaceholderText("+34 600 000 000")
        self.number.returnPressed.connect(self.start_scan)

        self.run_button = QPushButton("Ejecutar")
        self.run_button.setObjectName("primaryButton")
        self.run_button.clicked.connect(self.start_scan)

        self.stop_button = QPushButton("Detener")
        self.stop_button.setObjectName("secondaryButton")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_scan)

        input_row.addWidget(self.number, 1)
        input_row.addWidget(self.run_button)
        input_row.addWidget(self.stop_button)
        card_layout.addLayout(input_row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        card_layout.addWidget(self.progress)

        self.summary = QLabel("Sin análisis ejecutados.")
        self.summary.setObjectName("cardText")
        card_layout.addWidget(self.summary)

        layout.addWidget(card)

        results = QFrame()
        results.setObjectName("card")
        results_layout = QVBoxLayout(results)
        results_layout.setContentsMargins(20, 18, 20, 18)

        result_title = QLabel("Resultados")
        result_title.setObjectName("cardTitle")
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText(
            "La salida de PhoneInfoga aparecerá aquí."
        )

        results_layout.addWidget(result_title)
        results_layout.addWidget(self.output, 1)
        layout.addWidget(results, 1)

    def _valid_phone(self, value: str) -> bool:
        return bool(self.PHONE_RE.fullmatch(value))

    def start_scan(self):
        value = self.number.text().strip()
        if not self._valid_phone(value):
            QMessageBox.warning(
                self,
                "Número no válido",
                "Introduce un número con código internacional, por ejemplo +34 600 000 000."
            )
            return

        if self.process is not None and self.process.state() != QProcess.ProcessState.NotRunning:
            return

        self.output.clear()
        self.progress.setRange(0, 0)
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.number.setEnabled(False)
        self.status.setText("● Ejecutando")
        self.status.setObjectName("statusPending")
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)
        self.summary.setText(f"Analizando: {value}")

        self.process = QProcess(self)
        self.process.setProgram(PHONEINFOGA_BIN)
        self.process.setArguments(["scan", "-n", value])
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.finished.connect(self.finished)
        self.process.errorOccurred.connect(self.process_error)
        self.process.start()

    def read_output(self):
        if self.process is None:
            return
        data = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
        if data:
            self.output.moveCursor(self.output.textCursor().MoveOperation.End)
            self.output.insertPlainText(data)
            self.output.ensureCursorVisible()

    def finished(self, exit_code: int, _exit_status):
        self.read_output()
        value = self.number.text().strip()
        self.progress.setRange(0, 100)
        self.progress.setValue(100 if exit_code == 0 else 0)
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.number.setEnabled(True)

        self.status.setText("● Finalizado" if exit_code == 0 else f"● Código {exit_code}")
        self.status.setObjectName("statusOk" if exit_code == 0 else "statusPending")
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)

        self.summary.setText("Análisis finalizado.")
        self.save_output(value, exit_code)
        self.process = None

    def process_error(self, error):
        if self.process is not None and error == QProcess.ProcessError.FailedToStart:
            QMessageBox.critical(
                self, "PhoneInfoga no disponible",
                "No se encuentra el lanzador de PhoneInfoga. Reprovisiona la Fase 7."
            )
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.number.setEnabled(True)
            self.progress.setRange(0, 100)
            self.progress.setValue(0)

    def stop_scan(self):
        if self.process is not None and self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.terminate()
            if not self.process.waitForFinished(1500):
                self.process.kill()

    def save_output(self, number: str, exit_code: int):
        try:
            EXPORT_DIR.mkdir(parents=True, exist_ok=True)
            safe = re.sub(r"[^0-9+]+", "_", number)[:50]
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target = EXPORT_DIR / f"phoneinfoga_{safe}_{stamp}.txt"
            header = (
                "MobPsy - PhoneInfoga\n"
                f"Número: {number}\n"
                f"Fecha: {datetime.now().isoformat(timespec='seconds')}\n"
                f"Código de salida: {exit_code}\n"
                + "-" * 60 + "\n"
            )
            target.write_text(header + self.output.toPlainText(), encoding="utf-8")
            self.summary.setText(self.summary.text() + f" · Guardado en {target.name}")
            case_info = register_export(
                target,
                tool_name=getattr(self, "tool_name", target.stem.split("_")[0]),
                interface="gui",
                exit_code=exit_code,
            )
            if case_info:
                self.summary.setText(
                    self.summary.text() + f" · Caso {case_info['case_id']}"
                )
        except Exception:
            pass


class FileToolWidget(QWidget):
    def __init__(
        self,
        tool_name: str,
        executable: str,
        description: str,
        argument_builder,
        file_filter: str = "Todos los archivos (*)",
    ):
        super().__init__()
        self.tool_name = tool_name
        self.executable = executable
        self.description = description
        self.argument_builder = argument_builder
        self.file_filter = file_filter
        self.process: QProcess | None = None
        self.selected_path = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)
        card_layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel(tool_name)
        title.setObjectName("cardTitle")
        self.status = QLabel("● Preparado")
        self.status.setObjectName("statusOk")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.status)
        card_layout.addLayout(header)

        desc = QLabel(description)
        desc.setObjectName("cardText")
        desc.setWordWrap(True)
        card_layout.addWidget(desc)

        file_row = QHBoxLayout()
        self.path_field = QLineEdit()
        self.path_field.setReadOnly(True)
        self.path_field.setPlaceholderText("Selecciona un archivo...")

        choose = QPushButton("Seleccionar archivo")
        choose.setObjectName("secondaryButton")
        choose.clicked.connect(self.choose_file)

        self.run_button = QPushButton("Analizar")
        self.run_button.setObjectName("primaryButton")
        self.run_button.setEnabled(False)
        self.run_button.clicked.connect(self.run_tool)

        file_row.addWidget(self.path_field, 1)
        file_row.addWidget(choose)
        file_row.addWidget(self.run_button)
        card_layout.addLayout(file_row)

        self.summary = QLabel("Ningún archivo analizado.")
        self.summary.setObjectName("cardText")
        card_layout.addWidget(self.summary)

        layout.addWidget(card)

        results = QFrame()
        results.setObjectName("card")
        result_layout = QVBoxLayout(results)
        result_layout.setContentsMargins(20, 18, 20, 18)

        result_title = QLabel("Resultados")
        result_title.setObjectName("cardTitle")
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)

        result_layout.addWidget(result_title)
        result_layout.addWidget(self.output, 1)
        layout.addWidget(results, 1)

    def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, f"Seleccionar archivo para {self.tool_name}", str(Path.home()), self.file_filter
        )
        if path:
            self.selected_path = path
            self.path_field.setText(path)
            self.run_button.setEnabled(True)

    def run_tool(self):
        if not self.selected_path:
            return

        path = Path(self.selected_path)
        if not path.is_file():
            QMessageBox.warning(self, "Archivo no encontrado", "El archivo seleccionado ya no existe.")
            return

        if self.process is not None and self.process.state() != QProcess.ProcessState.NotRunning:
            return

        self.output.clear()
        self.run_button.setEnabled(False)
        self.status.setText("● Analizando")
        self.status.setObjectName("statusPending")
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)
        self.summary.setText(path.name)

        self.process = QProcess(self)
        self.process.setProgram(self.executable)
        self.process.setArguments(self.argument_builder(str(path)))
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.finished.connect(self.finished)
        self.process.errorOccurred.connect(self.process_error)
        self.process.start()

    def read_output(self):
        if self.process is None:
            return
        data = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
        if data:
            self.output.moveCursor(self.output.textCursor().MoveOperation.End)
            self.output.insertPlainText(data)
            self.output.ensureCursorVisible()

    def finished(self, exit_code: int, _exit_status):
        self.read_output()
        self.run_button.setEnabled(True)
        self.status.setText("● Finalizado" if exit_code == 0 else f"● Código {exit_code}")
        self.status.setObjectName("statusOk" if exit_code == 0 else "statusPending")
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)

        self.summary.setText(
            f"{Path(self.selected_path).name} · análisis finalizado"
        )
        self.save_output(exit_code)
        self.process = None

    def process_error(self, error):
        if self.process is not None and error == QProcess.ProcessError.FailedToStart:
            QMessageBox.critical(
                self,
                f"{self.tool_name} no disponible",
                f"No se encuentra el lanzador de {self.tool_name}. Reprovisiona la Fase 7."
            )
            self.run_button.setEnabled(True)

    def save_output(self, exit_code: int):
        try:
            EXPORT_DIR.mkdir(parents=True, exist_ok=True)
            name = Path(self.selected_path).name
            safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", name)[:80]
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prefix = self.tool_name.lower().replace(" ", "_")
            target = EXPORT_DIR / f"{prefix}_{safe}_{stamp}.txt"
            header = (
                f"MobPsy - {self.tool_name}\n"
                f"Archivo: {self.selected_path}\n"
                f"Fecha: {datetime.now().isoformat(timespec='seconds')}\n"
                f"Código de salida: {exit_code}\n"
                + "-" * 60 + "\n"
            )
            target.write_text(header + self.output.toPlainText(), encoding="utf-8")
            self.summary.setText(self.summary.text() + f" · Guardado en {target.name}")
            case_info = register_export(
                target,
                tool_name=getattr(self, "tool_name", target.stem.split("_")[0]),
                interface="gui",
                exit_code=exit_code,
            )
            if case_info:
                self.summary.setText(
                    self.summary.text() + f" · Caso {case_info['case_id']}"
                )
        except Exception:
            pass


class SocialPage(QWidget):
    USER_RE = re.compile(r"^[A-Za-z0-9._-]{1,100}$")

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(10)

        title = QLabel("Redes sociales")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "Búsqueda de presencia pública en redes sociales y consulta de metadatos "
            "de perfiles públicos de Instagram."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(12)

        tabs = QHBoxLayout()
        self.social_tab = QPushButton("Social-Analyzer")
        self.insta_tab = QPushButton("Instaloader")

        for button in (self.social_tab, self.insta_tab):
            button.setObjectName("toolTab")
            button.setCheckable(True)
            tabs.addWidget(button)
        tabs.addStretch(1)
        layout.addLayout(tabs)

        group = QButtonGroup(self)
        group.setExclusive(True)
        group.addButton(self.social_tab, 0)
        group.addButton(self.insta_tab, 1)
        self._group = group

        self.stack = QStackedWidget()
        validator = lambda value: bool(self.USER_RE.fullmatch(value))

        self.social = TextTargetToolWidget(
            "Social-Analyzer",
            SOCIAL_ANALYZER_BIN,
            "Busca un username en múltiples redes y devuelve perfiles detectados con puntuación.",
            "usuario123",
            validator,
            lambda value: [
                "--username", value,
                "--websites", "all",
                "--mode", "fast",
                "--output", "pretty",
                "--options", "link,rate,title",
                "--method", "find",
                "--filter", "good",
            ],
            "social_analyzer",
            "MobPsy usa el modo fast y filtra inicialmente resultados de alta confianza."
        )

        self.instaloader = TextTargetToolWidget(
            "Instaloader",
            INSTALOADER_BIN,
            "Consulta metadatos básicos de un perfil público de Instagram sin descargar sus publicaciones.",
            "usuarioinstagram",
            validator,
            lambda value: [value],
            "instaloader_profile",
            "Instagram puede exigir autenticación o aplicar rate limits. MobPsy no almacena credenciales."
        )

        self.stack.addWidget(self.social)
        self.stack.addWidget(self.instaloader)

        self.social_tab.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.insta_tab.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.social_tab.setChecked(True)
        layout.addWidget(self.stack, 1)


class MultimediaPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(10)

        title = QLabel("Multimedia y metadatos")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "Analiza archivos localmente con ExifTool o MediaInfo. "
            "Los archivos no se suben a servicios externos."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(12)

        tabs = QHBoxLayout()
        self.exif_tab = QPushButton("ExifTool")
        self.media_tab = QPushButton("MediaInfo")
        for button in (self.exif_tab, self.media_tab):
            button.setObjectName("toolTab")
            button.setCheckable(True)
            tabs.addWidget(button)
        tabs.addStretch(1)
        layout.addLayout(tabs)

        group = QButtonGroup(self)
        group.setExclusive(True)
        group.addButton(self.exif_tab, 0)
        group.addButton(self.media_tab, 1)
        self._group = group

        self.stack = QStackedWidget()

        self.exif = FileToolWidget(
            "ExifTool",
            EXIFTOOL_BIN,
            "Extrae metadatos de imágenes, documentos, audio, vídeo y numerosos formatos.",
            lambda path: ["-a", "-G1", "-s", path],
        )
        self.media = FileToolWidget(
            "MediaInfo",
            MEDIAINFO_BIN,
            "Muestra información técnica y etiquetas de archivos de audio y vídeo.",
            lambda path: [path],
            "Multimedia (*.mp4 *.mkv *.avi *.mov *.webm *.mp3 *.wav *.flac *.ogg *.m4a);;Todos los archivos (*)",
        )

        self.stack.addWidget(self.exif)
        self.stack.addWidget(self.media)

        self.exif_tab.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.media_tab.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.exif_tab.setChecked(True)

        layout.addWidget(self.stack, 1)


class TextTargetToolWidget(QWidget):
    def __init__(
        self,
        tool_name: str,
        executable: str,
        description: str,
        placeholder: str,
        validator,
        argument_builder,
        export_prefix: str,
        warning_text: str = "",
    ):
        super().__init__()
        self.tool_name = tool_name
        self.executable = executable
        self.description = description
        self.placeholder = placeholder
        self.validator = validator
        self.argument_builder = argument_builder
        self.export_prefix = export_prefix
        self.warning_text = warning_text
        self.process: QProcess | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)
        card_layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel(tool_name)
        title.setObjectName("cardTitle")
        self.status = QLabel("● Preparado")
        self.status.setObjectName("statusOk")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.status)
        card_layout.addLayout(header)

        desc = QLabel(description)
        desc.setObjectName("cardText")
        desc.setWordWrap(True)
        card_layout.addWidget(desc)

        if warning_text:
            warning = QLabel(warning_text)
            warning.setObjectName("cardText")
            warning.setWordWrap(True)
            card_layout.addWidget(warning)

        input_row = QHBoxLayout()
        self.target = QLineEdit()
        self.target.setPlaceholderText(placeholder)
        self.target.returnPressed.connect(self.start)

        self.run_button = QPushButton("Ejecutar")
        self.run_button.setObjectName("primaryButton")
        self.run_button.clicked.connect(self.start)

        self.stop_button = QPushButton("Detener")
        self.stop_button.setObjectName("secondaryButton")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop)

        input_row.addWidget(self.target, 1)
        input_row.addWidget(self.run_button)
        input_row.addWidget(self.stop_button)
        card_layout.addLayout(input_row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        card_layout.addWidget(self.progress)

        self.summary = QLabel("Sin ejecuciones.")
        self.summary.setObjectName("cardText")
        card_layout.addWidget(self.summary)

        layout.addWidget(card)

        results = QFrame()
        results.setObjectName("card")
        results_layout = QVBoxLayout(results)
        results_layout.setContentsMargins(20, 18, 20, 18)

        title = QLabel("Resultados")
        title.setObjectName("cardTitle")
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText(
            f"La salida de {tool_name} aparecerá aquí."
        )

        results_layout.addWidget(title)
        results_layout.addWidget(self.output, 1)
        layout.addWidget(results, 1)

    def start(self):
        value = self.target.text().strip()

        if not self.validator(value):
            QMessageBox.warning(
                self,
                "Objetivo no válido",
                f"El valor introducido no es válido para {self.tool_name}."
            )
            return

        if self.process is not None and self.process.state() != QProcess.ProcessState.NotRunning:
            return

        self.output.clear()
        self.progress.setRange(0, 0)
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.target.setEnabled(False)

        self.status.setText("● Ejecutando")
        self.status.setObjectName("statusPending")
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)
        self.summary.setText(f"Objetivo: {value}")

        self.process = QProcess(self)
        self.process.setProgram(self.executable)
        self.process.setArguments(self.argument_builder(value))
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.finished.connect(self.finished)
        self.process.errorOccurred.connect(self.process_error)
        self.process.start()

    def read_output(self):
        if self.process is None:
            return

        data = bytes(self.process.readAllStandardOutput()).decode(
            "utf-8", errors="replace"
        )
        if data:
            self.output.moveCursor(self.output.textCursor().MoveOperation.End)
            self.output.insertPlainText(data)
            self.output.ensureCursorVisible()

    def finished(self, exit_code: int, _exit_status):
        self.read_output()
        value = self.target.text().strip()

        self.progress.setRange(0, 100)
        self.progress.setValue(100 if exit_code == 0 else 0)
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.target.setEnabled(True)

        self.status.setText(
            "● Finalizado" if exit_code == 0 else f"● Código {exit_code}"
        )
        self.status.setObjectName("statusOk" if exit_code == 0 else "statusPending")
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)

        lines = len([x for x in self.output.toPlainText().splitlines() if x.strip()])
        self.summary.setText(f"Finalizado · {lines} línea(s) de salida")
        self.save_output(value, exit_code)
        self.process = None

    def process_error(self, error):
        if self.process is not None and error == QProcess.ProcessError.FailedToStart:
            QMessageBox.critical(
                self,
                f"{self.tool_name} no disponible",
                f"MobPsy no encuentra el lanzador de {self.tool_name}. "
                "Reprovisiona la Fase 8."
            )
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.target.setEnabled(True)
            self.progress.setRange(0, 100)
            self.progress.setValue(0)

    def stop(self):
        if self.process is not None and self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.terminate()
            if not self.process.waitForFinished(1500):
                self.process.kill()

    def save_output(self, target_value: str, exit_code: int):
        try:
            EXPORT_DIR.mkdir(parents=True, exist_ok=True)
            safe = re.sub(r"[^A-Za-z0-9_.:-]+", "_", target_value)[:100] or "target"
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target = EXPORT_DIR / f"{self.export_prefix}_{safe}_{stamp}.txt"

            header = (
                f"MobPsy - {self.tool_name}\n"
                f"Objetivo: {target_value}\n"
                f"Fecha: {datetime.now().isoformat(timespec='seconds')}\n"
                f"Código de salida: {exit_code}\n"
                + "-" * 60 + "\n"
            )

            target.write_text(
                header + self.output.toPlainText(),
                encoding="utf-8"
            )
            self.summary.setText(
                self.summary.text() + f" · Guardado en {target.name}"
            )
            case_info = register_export(
                target,
                tool_name=getattr(self, "tool_name", target.stem.split("_")[0]),
                interface="gui",
                exit_code=exit_code,
            )
            if case_info:
                self.summary.setText(
                    self.summary.text() + f" · Caso {case_info['case_id']}"
                )
        except Exception:
            pass



class DNSPage(QWidget):
    DOMAIN_RE = re.compile(
        r"^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9\-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}$"
    )

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(10)

        title = QLabel("DNS y subdominios")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "Consultas DNS, resolución de nombres y enumeración pasiva de subdominios "
            "desde una única categoría."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(12)

        tabs = QHBoxLayout()
        tabs.setSpacing(6)
        self.subfinder_tab = QPushButton("Subfinder")
        self.dnsrecon_tab = QPushButton("DNSRecon")
        self.dig_tab = QPushButton("dig")
        self.host_tab = QPushButton("host")

        all_tabs = (
            self.subfinder_tab,
            self.dnsrecon_tab,
            self.dig_tab,
            self.host_tab,
        )
        for button in all_tabs:
            button.setObjectName("toolTab")
            button.setCheckable(True)
            tabs.addWidget(button)
        tabs.addStretch(1)
        layout.addLayout(tabs)

        group = QButtonGroup(self)
        group.setExclusive(True)
        for idx, button in enumerate(all_tabs):
            group.addButton(button, idx)
        self._group = group

        self.stack = QStackedWidget()
        domain_validator = lambda value: bool(self.DOMAIN_RE.fullmatch(value.lower()))

        self.subfinder = TextTargetToolWidget(
            "Subfinder", SUBFINDER_BIN,
            "Enumeración pasiva de subdominios mediante fuentes públicas.",
            "example.com", domain_validator,
            lambda value: ["-d", value, "-silent"],
            "subfinder",
            "MobPsy utiliza el modo pasivo por defecto."
        )

        self.dnsrecon = TextTargetToolWidget(
            "DNSRecon", DNSRECON_BIN,
            "Enumeración estándar de registros DNS públicos asociados a un dominio.",
            "example.com", domain_validator,
            lambda value: ["-d", value, "-t", "std"],
            "dnsrecon",
            "La configuración inicial usa enumeración estándar, sin fuerza bruta."
        )

        self.dig = TextTargetToolWidget(
            "dig", DIG_BIN,
            "Consulta directamente registros DNS. El modo gráfico muestra una consulta general del dominio.",
            "example.com", domain_validator,
            lambda value: [value, "ANY"],
            "dig",
            "Para MX, TXT, NS u otros tipos concretos utiliza MobPsy Terminal con argumentos personalizados."
        )

        self.host = TextTargetToolWidget(
            "host", HOST_BIN,
            "Resolución DNS rápida de dominios y nombres de host.",
            "example.com", domain_validator,
            lambda value: [value],
            "host",
        )

        for widget in (self.subfinder, self.dnsrecon, self.dig, self.host):
            self.stack.addWidget(widget)

        self.subfinder_tab.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.dnsrecon_tab.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.dig_tab.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.host_tab.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        self.subfinder_tab.setChecked(True)

        layout.addWidget(self.stack, 1)


class IPPage(QWidget):
    @staticmethod
    def is_valid_ip(value: str) -> bool:
        try:
            ipaddress.ip_address(value.strip())
            return True
        except ValueError:
            return False

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(10)

        title = QLabel("Direcciones IP")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "Consultas WHOIS y geolocalización básica para direcciones IP. "
            "La geolocalización IP es aproximada y no identifica la ubicación exacta de una persona."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(12)

        tabs = QHBoxLayout()
        tabs.setSpacing(6)
        self.whois_tab = QPushButton("Whois")
        self.geoip_tab = QPushButton("GeoIPLookup")

        for button in (self.whois_tab, self.geoip_tab):
            button.setObjectName("toolTab")
            button.setCheckable(True)
            tabs.addWidget(button)
        tabs.addStretch(1)
        layout.addLayout(tabs)

        group = QButtonGroup(self)
        group.setExclusive(True)
        group.addButton(self.whois_tab, 0)
        group.addButton(self.geoip_tab, 1)
        self._group = group

        self.stack = QStackedWidget()
        ip_validator = self.is_valid_ip

        self.whois = TextTargetToolWidget(
            "Whois", WHOIS_BIN,
            "Consulta información WHOIS disponible para una dirección IP.",
            "8.8.8.8", ip_validator,
            lambda value: [value],
            "whois_ip",
        )

        self.geoip = TextTargetToolWidget(
            "GeoIPLookup", GEOIPLOOKUP_BIN,
            "Consulta geolocalización básica mediante la base GeoIP instalada localmente.",
            "8.8.8.8", ip_validator,
            lambda value: [value],
            "geoiplookup",
            "El resultado depende de la base local y debe considerarse aproximado."
        )

        self.stack.addWidget(self.whois)
        self.stack.addWidget(self.geoip)

        self.whois_tab.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.geoip_tab.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.whois_tab.setChecked(True)

        layout.addWidget(self.stack, 1)


class InfrastructurePage(QWidget):
    DOMAIN_RE = re.compile(
        r"^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9\-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}$"
    )

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(10)

        title = QLabel("Web e infraestructura")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "Fingerprinting web, detección de WAF, crawling y recopilación OSINT de dominios. "
            "Las consultas DNS se han movido a su categoría propia."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(12)

        tabs = QHBoxLayout()
        tabs.setSpacing(6)
        self.whatweb_tab = QPushButton("WhatWeb")
        self.wafw00f_tab = QPushButton("WAFW00F")
        self.photon_tab = QPushButton("Photon")
        self.harvester_tab = QPushButton("theHarvester")

        all_tabs = (
            self.whatweb_tab,
            self.wafw00f_tab,
            self.photon_tab,
            self.harvester_tab,
        )
        for button in all_tabs:
            button.setObjectName("toolTab")
            button.setCheckable(True)
            tabs.addWidget(button)
        tabs.addStretch(1)
        layout.addLayout(tabs)

        group = QButtonGroup(self)
        group.setExclusive(True)
        for idx, button in enumerate(all_tabs):
            group.addButton(button, idx)
        self._group = group

        self.stack = QStackedWidget()
        domain_validator = lambda value: bool(self.DOMAIN_RE.fullmatch(value.lower()))

        def url_or_domain(value: str) -> bool:
            if not value or len(value) > 2048:
                return False
            if value.startswith(("http://", "https://")):
                return True
            return bool(self.DOMAIN_RE.fullmatch(value.lower()))

        self.whatweb = TextTargetToolWidget(
            "WhatWeb", WHATWEB_BIN,
            "Identifica tecnologías y características visibles de un sitio web.",
            "https://example.com", url_or_domain,
            lambda value: ["-a", "1", "--color=never", value],
            "whatweb",
            "Se fija agresividad 1, el modo más conservador de WhatWeb."
        )

        self.wafw00f = TextTargetToolWidget(
            "WAFW00F", WAFW00F_BIN,
            "Detecta y trata de identificar un Web Application Firewall delante de un sitio.",
            "https://example.com", url_or_domain,
            lambda value: [value],
            "wafw00f",
            "WAFW00F realiza peticiones HTTP de fingerprinting; úsalo solo sobre objetivos autorizados."
        )

        photon_output = str(Path.home() / "MobPsy" / "Temporal" / "photon-last")
        self.photon = TextTargetToolWidget(
            "Photon", PHOTON_BIN,
            "Crawler OSINT que extrae URLs, archivos, correos y otros datos públicos visibles en un sitio.",
            "https://example.com", url_or_domain,
            lambda value: [
                "-u", value, "-l", "2", "-t", "2",
                "--timeout", "5", "-v", "-o", photon_output,
            ],
            "photon",
            "MobPsy limita inicialmente Photon a profundidad 2 y 2 hilos."
        )

        self.harvester = TextTargetToolWidget(
            "theHarvester", THEHARVESTER_BIN,
            "Agrega OSINT de un dominio desde múltiples fuentes públicas.",
            "example.com", domain_validator,
            lambda value: ["-d", value, "-b", "crtsh,certspotter,commoncrawl"],
            "theharvester",
            "MobPsy usa por defecto fuentes pasivas sin API."
        )

        for widget in (self.whatweb, self.wafw00f, self.photon, self.harvester):
            self.stack.addWidget(widget)

        self.whatweb_tab.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.wafw00f_tab.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.photon_tab.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.harvester_tab.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        self.whatweb_tab.setChecked(True)

        layout.addWidget(self.stack, 1)


class FrameworkLauncherCard(QFrame):
    def __init__(self, title: str, description: str, button_text: str, mode: str, executable: str):
        super().__init__()
        self.setObjectName("card")
        self.mode = mode
        self.executable = executable
        self.tool_name = title
        self.process: QProcess | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(9)

        header = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        self.status = QLabel("● Preparado")
        self.status.setObjectName("statusOk")
        header.addWidget(title_label)
        header.addStretch(1)
        header.addWidget(self.status)

        desc = QLabel(description)
        desc.setObjectName("cardText")
        desc.setWordWrap(True)

        button = QPushButton(button_text)
        button.setObjectName("primaryButton")
        button.clicked.connect(self.launch)

        layout.addLayout(header)
        layout.addWidget(desc)
        layout.addStretch(1)
        layout.addWidget(button)

    def launch(self):
        if self.mode == "direct":
            self.process = QProcess(self)
            self.process.setProgram(self.executable)
            self.process.start()
        elif self.mode == "terminal":
            self.process = QProcess(self)
            self.process.setProgram("gnome-terminal")
            self.process.setArguments([
                "--",
                "bash",
                "-lc",
                f"{self.executable}; echo; echo 'Pulsa ENTER para cerrar'; read",
            ])
            self.process.start()




class CasesPage(QWidget):
    def __init__(self):
        super().__init__()
        self.current_case_dir: Path | None = None
        self.current_manifest: dict | None = None

        CASES_DIR.mkdir(parents=True, exist_ok=True)

        root = QVBoxLayout(self)
        root.setContentsMargins(36, 30, 36, 30)
        root.setSpacing(14)

        title = QLabel("Casos y evidencias")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "Gestiona investigaciones de forma reproducible. Cada caso conserva su manifest, "
            "evidencias, exportaciones, hashes SHA-256 y un informe resumen."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)

        root.addWidget(title)
        root.addWidget(subtitle)

        content = QHBoxLayout()
        content.setSpacing(14)

        # ---------------- Left: cases ----------------
        left = QFrame()
        left.setObjectName("card")
        left.setMinimumWidth(370)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(18, 18, 18, 18)
        left_layout.setSpacing(10)

        left_title = QLabel("Investigaciones")
        left_title.setObjectName("cardTitle")
        left_layout.addWidget(left_title)

        self.case_list = QListWidget()
        self.case_list.setObjectName("caseList")
        self.case_list.currentItemChanged.connect(self.on_case_selected)
        left_layout.addWidget(self.case_list, 1)

        new_title = QLabel("Nuevo caso")
        new_title.setObjectName("cardTitle")
        left_layout.addWidget(new_title)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Título del caso")

        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("Objetivo / persona / organización / dominio")

        self.notes_input = QPlainTextEdit()
        self.notes_input.setPlaceholderText("Notas iniciales, hipótesis o alcance...")
        self.notes_input.setMaximumHeight(100)

        self.create_button = QPushButton("Crear caso")
        self.create_button.setObjectName("caseActionButton")
        self.create_button.clicked.connect(self.create_case)

        self.refresh_button = QPushButton("Actualizar lista")
        self.refresh_button.setObjectName("caseActionButton")
        self.refresh_button.clicked.connect(self.refresh_cases)

        left_layout.addWidget(self.title_input)
        left_layout.addWidget(self.subject_input)
        left_layout.addWidget(self.notes_input)
        left_layout.addWidget(self.create_button)
        left_layout.addWidget(self.refresh_button)

        # ---------------- Right: selected case ----------------
        right = QFrame()
        right.setObjectName("card")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(20, 18, 20, 18)
        right_layout.setSpacing(10)

        header = QHBoxLayout()
        self.case_title = QLabel("Selecciona un caso")
        self.case_title.setObjectName("cardTitle")
        self.active_label = QLabel("")
        self.active_label.setObjectName("activeCase")
        header.addWidget(self.case_title)
        header.addStretch(1)
        header.addWidget(self.active_label)
        right_layout.addLayout(header)

        self.case_meta = QLabel("Todavía no hay un caso seleccionado.")
        self.case_meta.setObjectName("caseMeta")
        self.case_meta.setWordWrap(True)
        right_layout.addWidget(self.case_meta)

        self.case_notes = QPlainTextEdit()
        self.case_notes.setReadOnly(True)
        self.case_notes.setMaximumHeight(105)
        right_layout.addWidget(self.case_notes)

        ev_title = QLabel("Evidencias y exportaciones")
        ev_title.setObjectName("cardTitle")
        right_layout.addWidget(ev_title)

        self.evidence_list = QListWidget()
        self.evidence_list.setObjectName("evidenceList")
        right_layout.addWidget(self.evidence_list, 1)

        run_title = QLabel("Historial de ejecuciones")
        run_title.setObjectName("cardTitle")
        right_layout.addWidget(run_title)

        self.execution_list = QListWidget()
        self.execution_list.setObjectName("evidenceList")
        self.execution_list.setMaximumHeight(150)
        right_layout.addWidget(self.execution_list)

        row1 = QHBoxLayout()
        self.add_evidence_button = QPushButton("Añadir evidencia")
        self.add_evidence_button.setObjectName("caseActionButton")
        self.add_evidence_button.clicked.connect(self.add_evidence)

        self.add_export_button = QPushButton("Importar exportación")
        self.add_export_button.setObjectName("caseActionButton")
        self.add_export_button.clicked.connect(self.add_export)

        self.remove_item_button = QPushButton("Eliminar seleccionado")
        self.remove_item_button.setObjectName("caseActionButton")
        self.remove_item_button.clicked.connect(self.remove_selected_item)

        row1.addWidget(self.add_evidence_button)
        row1.addWidget(self.add_export_button)
        row1.addWidget(self.remove_item_button)
        right_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.active_button = QPushButton("Establecer como activo")
        self.active_button.setObjectName("caseActionButton")
        self.active_button.clicked.connect(self.set_active_case)

        self.clear_active_button = QPushButton("Quitar caso activo")
        self.clear_active_button.setObjectName("caseActionButton")
        self.clear_active_button.clicked.connect(self.clear_active_case)

        self.report_button = QPushButton("Generar informe")
        self.report_button.setObjectName("caseActionButton")
        self.report_button.clicked.connect(self.generate_report)

        row2.addWidget(self.active_button)
        row2.addWidget(self.clear_active_button)
        row2.addWidget(self.report_button)
        right_layout.addLayout(row2)

        row3 = QHBoxLayout()
        self.open_button = QPushButton("Abrir carpeta")
        self.open_button.setObjectName("caseActionButton")
        self.open_button.clicked.connect(self.open_case_folder)

        self.toggle_status_button = QPushButton("Cerrar caso")
        self.toggle_status_button.setObjectName("caseActionButton")
        self.toggle_status_button.clicked.connect(self.toggle_case_status)

        row3.addWidget(self.open_button)
        row3.addWidget(self.toggle_status_button)
        row3.addStretch(1)
        right_layout.addLayout(row3)

        content.addWidget(left, 0)
        content.addWidget(right, 1)
        root.addLayout(content, 1)

        self.set_case_actions_enabled(False)
        self.refresh_cases()

    @staticmethod
    def _safe_slug(value: str) -> str:
        value = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
        return value.strip("._-")[:70] or "caso"

    @staticmethod
    def _hash_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def set_case_actions_enabled(self, enabled: bool):
        for button in (
            self.add_evidence_button,
            self.add_export_button,
            self.remove_item_button,
            self.active_button,
            self.clear_active_button,
            self.report_button,
            self.open_button,
            self.toggle_status_button,
        ):
            button.setEnabled(enabled)

    def _manifest_path(self, case_dir: Path) -> Path:
        return case_dir / "case.json"

    def _load_manifest(self, case_dir: Path) -> dict:
        return json.loads(self._manifest_path(case_dir).read_text(encoding="utf-8"))

    def _save_manifest(self):
        if not self.current_case_dir or not self.current_manifest:
            return
        self.current_manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
        self._manifest_path(self.current_case_dir).write_text(
            json.dumps(self.current_manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _active_case_id(self) -> str:
        try:
            data = json.loads(ACTIVE_CASE_FILE.read_text(encoding="utf-8"))
            return str(data.get("case_id", ""))
        except Exception:
            return ""

    def refresh_cases(self):
        CASES_DIR.mkdir(parents=True, exist_ok=True)
        selected_id = self.current_manifest.get("case_id") if self.current_manifest else None

        rows = []
        for folder in CASES_DIR.iterdir():
            if not folder.is_dir():
                continue
            manifest = folder / "case.json"
            if not manifest.is_file():
                continue
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
            except Exception:
                continue
            rows.append((data.get("created_at", ""), folder, data))

        rows.sort(key=lambda x: x[0], reverse=True)

        self.case_list.clear()
        item_to_select = None
        active_id = self._active_case_id()

        for _, folder, data in rows:
            status = data.get("status", "abierto")
            active = " ★" if data.get("case_id") == active_id else ""
            text = f"{data.get('case_id', '?')} · {data.get('title', folder.name)} [{status}]{active}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, str(folder))
            self.case_list.addItem(item)
            if data.get("case_id") == selected_id:
                item_to_select = item

        if item_to_select:
            self.case_list.setCurrentItem(item_to_select)
        elif self.case_list.count() and not self.current_case_dir:
            self.case_list.setCurrentRow(0)

    def create_case(self):
        title = self.title_input.text().strip()
        subject = self.subject_input.text().strip()
        notes = self.notes_input.toPlainText().strip()

        if not title:
            QMessageBox.warning(self, "Título requerido", "Introduce un título para el caso.")
            return

        now = datetime.now()
        case_id = f"MOB-{now.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
        folder = CASES_DIR / f"{case_id}_{self._safe_slug(title)}"

        try:
            (folder / "Evidencias").mkdir(parents=True)
            (folder / "Exportaciones").mkdir()
            (folder / "Informes").mkdir()

            manifest = {
                "schema_version": 1,
                "case_id": case_id,
                "title": title,
                "subject": subject,
                "notes": notes,
                "status": "abierto",
                "created_at": now.isoformat(timespec="seconds"),
                "updated_at": now.isoformat(timespec="seconds"),
                "evidence": [],
                "executions": [],
            }

            (folder / "case.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            self.title_input.clear()
            self.subject_input.clear()
            self.notes_input.clear()

            self.current_case_dir = folder
            self.current_manifest = manifest
            self.set_active_case(silent=True)
            self.refresh_cases()
            self.display_current_case()

        except Exception as exc:
            QMessageBox.critical(self, "No se pudo crear el caso", str(exc))

    def on_case_selected(self, current, previous):
        if current is None:
            self.current_case_dir = None
            self.current_manifest = None
            self.set_case_actions_enabled(False)
            return

        case_dir = Path(current.data(Qt.ItemDataRole.UserRole))
        try:
            self.current_case_dir = case_dir
            self.current_manifest = self._load_manifest(case_dir)
            self.display_current_case()
        except Exception as exc:
            QMessageBox.critical(self, "Caso dañado", str(exc))

    def display_current_case(self):
        if not self.current_case_dir or not self.current_manifest:
            return

        data = self.current_manifest
        self.set_case_actions_enabled(True)

        self.case_title.setText(data.get("title", "Caso"))
        self.case_meta.setText(
            f"ID: {data.get('case_id', '?')}  ·  Estado: {data.get('status', 'abierto')}  ·  "
            f"Creado: {data.get('created_at', '?')}\n"
            f"Objetivo: {data.get('subject') or 'Sin especificar'}"
        )
        self.case_notes.setPlainText(data.get("notes", ""))

        active_id = self._active_case_id()
        active = data.get("case_id") == active_id
        self.active_label.setText("● CASO ACTIVO" if active else "")
        self.active_button.setEnabled(not active)
        self.clear_active_button.setEnabled(bool(active_id))

        status = data.get("status", "abierto")
        self.toggle_status_button.setText("Reabrir caso" if status == "cerrado" else "Cerrar caso")

        self.evidence_list.clear()
        for record in data.get("evidence", []):
            kind = "EVIDENCIA" if record.get("kind") == "evidence" else "EXPORTACIÓN"
            sha = record.get("sha256", "")
            short_sha = sha[:12] + "…" if sha else "sin hash"
            text = (
                f"{kind} · {record.get('stored_name', '?')}\n"
                f"SHA-256: {short_sha} · {record.get('added_at', '?')}"
            )
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, record)
            self.evidence_list.addItem(item)

        self.execution_list.clear()
        for execution in reversed(data.get("executions", [])[-25:]):
            command = execution.get("command") or []
            command_text = " ".join(command)
            if len(command_text) > 90:
                command_text = command_text[:87] + "..."
            status = execution.get("status", "?")
            code = execution.get("exit_code")
            code_text = "" if code is None else f" · exit={code}"
            target = execution.get("target") or ""
            target_text = f" · {target}" if target else ""
            text = (
                f"{execution.get('timestamp', '?')} · {execution.get('tool', '?')} "
                f"[{execution.get('interface', '?')}] · {status}{code_text}{target_text}"
            )
            if command_text:
                text += f"\n{command_text}"
            self.execution_list.addItem(QListWidgetItem(text))

    def _add_file(self, source: Path, kind: str):
        if not self.current_case_dir or not self.current_manifest:
            return
        if not source.is_file():
            QMessageBox.warning(self, "Archivo no válido", "Selecciona un archivo existente.")
            return

        dest_root = self.current_case_dir / ("Evidencias" if kind == "evidence" else "Exportaciones")
        dest_root.mkdir(parents=True, exist_ok=True)

        try:
            same_folder = source.resolve().parent == dest_root.resolve()
        except Exception:
            same_folder = False

        destination = source if same_folder else dest_root / source.name
        if not same_folder:
            counter = 1
            while destination.exists():
                destination = dest_root / f"{source.stem}_{counter}{source.suffix}"
                counter += 1

        try:
            original_path = str(source)
            if not same_folder:
                shutil.move(str(source), str(destination))

            sha256 = self._hash_file(destination)
            record = {
                "id": uuid.uuid4().hex,
                "kind": kind,
                "original_path": original_path,
                "stored_name": destination.name,
                "stored_path": str(destination.relative_to(self.current_case_dir)),
                "size_bytes": destination.stat().st_size,
                "sha256": sha256,
                "added_at": datetime.now().isoformat(timespec="seconds"),
            }
            self.current_manifest.setdefault("evidence", []).append(record)
            self._save_manifest()
            self.display_current_case()

            kind_label = "evidencia" if kind == "evidence" else "exportación"
            QMessageBox.information(
                self,
                "Archivo incorporado",
                f"La {kind_label} se ha movido al caso para evitar duplicados.\n\n"
                f"SHA-256: {sha256}",
            )
        except Exception as exc:
            QMessageBox.critical(self, "No se pudo incorporar el archivo", str(exc))

    def add_evidence(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar evidencia",
            str(Path.home()),
            "Todos los archivos (*)",
        )
        if path:
            self._add_file(Path(path), "evidence")

    def add_export(self):
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar exportación de MobPsy",
            str(EXPORT_DIR),
            "Todos los archivos (*)",
        )
        if path:
            self._add_file(Path(path), "export")

    def set_active_case(self, silent: bool = False):
        if not self.current_manifest or not self.current_case_dir:
            return

        CASES_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "case_id": self.current_manifest["case_id"],
            "case_dir": str(self.current_case_dir),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        ACTIVE_CASE_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self.display_current_case()
        self.refresh_cases()

        if not silent:
            QMessageBox.information(
                self,
                "Caso activo",
                f"{self.current_manifest['case_id']} es ahora el caso activo.",
            )

    def clear_active_case(self):
        active_id = self._active_case_id()
        if not active_id:
            QMessageBox.information(self, "Caso activo", "No hay ningún caso activo.")
            return

        answer = QMessageBox.question(
            self,
            "Quitar caso activo",
            f"Se quitará {active_id} como caso activo.\n\n"
            "Las herramientas dejarán de vincular resultados automáticamente hasta que actives otro caso.\n\n"
            "¿Continuar?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            ACTIVE_CASE_FILE.unlink(missing_ok=True)
            self.display_current_case()
            self.refresh_cases()
        except Exception as exc:
            QMessageBox.critical(self, "No se pudo quitar el caso activo", str(exc))

    def remove_selected_item(self):
        if not self.current_case_dir or not self.current_manifest:
            return

        item = self.evidence_list.currentItem()
        if item is None:
            QMessageBox.information(
                self,
                "Selecciona un elemento",
                "Selecciona primero una evidencia o exportación de la lista.",
            )
            return

        record = item.data(Qt.ItemDataRole.UserRole) or {}
        record_id = str(record.get("id", ""))
        stored_name = str(record.get("stored_name", "archivo"))
        kind_label = "evidencia" if record.get("kind") == "evidence" else "exportación"

        answer = QMessageBox.question(
            self,
            "Eliminar del caso",
            f"Se eliminará la {kind_label} «{stored_name}» del caso y también su archivo almacenado.\n\n"
            "Esta acción no se puede deshacer.\n\n¿Continuar?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            stored_rel = str(record.get("stored_path", ""))
            if stored_rel:
                target = (self.current_case_dir / stored_rel).resolve()
                case_root = self.current_case_dir.resolve()
                if target.is_relative_to(case_root) and target.is_file():
                    target.unlink()

            self.current_manifest["evidence"] = [
                rec for rec in self.current_manifest.get("evidence", [])
                if str(rec.get("id", "")) != record_id
            ]

            for execution in self.current_manifest.get("executions", []):
                if stored_rel and execution.get("output_path") == stored_rel:
                    execution["output_path"] = ""
                    execution["output_removed_at"] = datetime.now().isoformat(timespec="seconds")

            self._save_manifest()
            self.display_current_case()
        except Exception as exc:
            QMessageBox.critical(self, "No se pudo eliminar", str(exc))

    def toggle_case_status(self):
        if not self.current_manifest:
            return
        self.current_manifest["status"] = (
            "abierto" if self.current_manifest.get("status") == "cerrado" else "cerrado"
        )
        self._save_manifest()
        self.display_current_case()
        self.refresh_cases()

    def generate_report(self):
        if not self.current_case_dir or not self.current_manifest:
            return

        case_id = str(self.current_manifest.get("case_id") or "")
        if not case_id:
            QMessageBox.warning(self, "Informe", "El caso no tiene identificador.")
            return

        self.report_button.setEnabled(False)
        self.report_button.setText("Generando informe…")
        self.case_report_process = QProcess(self)
        self.case_report_process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)

        def report_finished(code, _status):
            output = bytes(self.case_report_process.readAllStandardOutput()).decode("utf-8", errors="replace")
            self.report_button.setEnabled(True)
            self.report_button.setText("Generar informe")
            if code != 0:
                QMessageBox.critical(
                    self,
                    "No se pudo generar el informe",
                    output.strip() or f"mobpsy-ai terminó con código {code}.",
                )
                return

            report_dir = self.current_case_dir / "Informes"
            html_report = report_dir / f"Informe_{case_id}.html"
            answer = QMessageBox.question(
                self,
                "Informe generado",
                "Informe profesional generado correctamente.\\n\\n¿Quieres abrirlo ahora?",
            )
            if answer == QMessageBox.StandardButton.Yes:
                if html_report.is_file():
                    QDesktopServices.openUrl(QUrl.fromLocalFile(str(html_report)))
                else:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(str(report_dir)))

        self.case_report_process.finished.connect(report_finished)
        self.case_report_process.start(MOBPSY_AI_BIN, ["report", case_id])

    def open_case_folder(self):
        if self.current_case_dir:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.current_case_dir)))



class ManualPage(QWidget):
    def __init__(self):
        super().__init__()

        self.process: QProcess | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(14)

        title = QLabel("Manual de uso")
        title.setObjectName("pageTitle")

        subtitle = QLabel(
            "Guía integrada para consultar de forma rápida qué hace cada herramienta, "
            "qué dato suele pedir y un ejemplo básico de ejecución."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)

        info = QFrame()
        info.setObjectName("manualInfo")
        info_box = QHBoxLayout(info)
        info_box.setContentsMargins(18, 18, 18, 18)
        info_box.setSpacing(12)

        left = QVBoxLayout()
        left.setSpacing(6)
        lt = QLabel("Dos formas de uso")
        lt.setObjectName("cardTitle")
        ld = QLabel(
            "• MobPsy gráfico para formularios guiados.\n"
            "• MobPsy Terminal para ayuda dinámica, ejemplos y ejecución avanzada."
        )
        ld.setObjectName("cardText")
        ld.setWordWrap(True)
        left.addWidget(lt)
        left.addWidget(ld)
        left.addStretch(1)

        right = QVBoxLayout()
        right.setSpacing(8)
        btn_terminal = QPushButton("Abrir MobPsy Terminal")
        btn_terminal.setObjectName("primaryButton")
        btn_terminal.clicked.connect(self.open_terminal)

        btn_exports = QPushButton("Abrir exportaciones")
        btn_exports.setObjectName("secondaryButton")
        btn_exports.clicked.connect(self.open_exports)

        right.addWidget(btn_terminal)
        right.addWidget(btn_exports)
        right.addStretch(1)

        info_box.addLayout(left, 1)
        info_box.addLayout(right)

        manual = QPlainTextEdit()
        manual.setObjectName("manualText")
        manual.setReadOnly(True)
        manual.setPlainText(MANUAL_TEXT)

        layout.addWidget(info)
        layout.addWidget(manual, 1)

    def open_terminal(self):
        self.process = QProcess(self)
        self.process.start("gnome-terminal", ["--maximize", "--", "bash", "-lc", f"{MOBPSY_CLI_BIN}; echo; echo 'Pulsa ENTER para cerrar'; read"])

    def open_exports(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(EXPORT_DIR)))



class CommandPage(QWidget):
    def __init__(self, title: str, subtitle: str):
        super().__init__()
        self.process = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(10)
        head = QLabel(title); head.setObjectName("pageTitle")
        desc = QLabel(subtitle); desc.setObjectName("pageSubtitle"); desc.setWordWrap(True)
        self.body = QVBoxLayout()
        self.output = QPlainTextEdit(); self.output.setObjectName("manualText"); self.output.setReadOnly(True)
        layout.addWidget(head); layout.addWidget(desc); layout.addSpacing(14); layout.addLayout(self.body); layout.addWidget(self.output, 1)

    def run_command(self, program, args):
        if self.process is not None and self.process.state() != QProcess.ProcessState.NotRunning:
            QMessageBox.information(self, "MobPsy", "Ya hay una operación en curso."); return
        self.output.clear()
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._read)
        self.process.finished.connect(self._finished)
        self.process.start(program, args)

    def _read(self):
        if self.process is None: return
        text = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
        self.output.insertPlainText(text)

    def _finished(self, code, _status):
        self._read()
        if code != 0: self.output.appendPlainText(f"\n[Proceso terminado con código {code}]")


class AIPage(CommandPage):
    def __init__(self):
        super().__init__(
            "Analista IA OSINT",
            "Asistente local especializado en OSINT y ciberinteligencia. "
            "Lee el caso activo, sus evidencias/exportaciones y los resultados de Correlator."
        )

        info = QLabel(
            "Las respuestas se basan en fuentes del expediente y deben distinguir hechos, "
            "inferencias e hipótesis."
        )
        info.setWordWrap(True)
        info.setObjectName("pageSubtitle")
        self.body.addWidget(info)

        self.question = QLineEdit()
        self.question.setPlaceholderText(
            "Pregunta sobre el caso activo, por ejemplo: ¿qué elementos relacionan las distintas fuentes?"
        )
        self.question.returnPressed.connect(self.ask_case)
        self.body.addWidget(self.question)

        qrow = QHBoxLayout()
        self.ask_button = QPushButton("Preguntar sobre el caso")
        self.ask_button.setObjectName("primaryButton")
        self.ask_button.clicked.connect(self.ask_case)
        self.status_button = QPushButton("Comprobar IA")
        self.status_button.setObjectName("secondaryButton")
        self.status_button.clicked.connect(lambda: self.run_command(MOBPSY_AI_BIN, ["status"]))
        qrow.addWidget(self.ask_button)
        qrow.addWidget(self.status_button)
        qrow.addStretch(1)
        self.body.addLayout(qrow)

        report_title = QLabel("Informe profesional")
        report_title.setStyleSheet("font-size: 17px; font-weight: 700; margin-top: 8px;")
        self.body.addWidget(report_title)

        report_info = QLabel(
            "Genera el mismo informe que el botón de Casos: resumen ejecutivo, hallazgos, "
            "correlaciones, cronología, confianza, limitaciones, próximos pasos e inventario técnico."
        )
        report_info.setWordWrap(True)
        self.body.addWidget(report_info)

        rrow = QHBoxLayout()
        self.report_button = QPushButton("Generar informe profesional")
        self.report_button.setObjectName("primaryButton")
        self.report_button.clicked.connect(lambda: self.run_command(MOBPSY_AI_BIN, ["report"]))
        self.open_reports_button = QPushButton("Abrir informes")
        self.open_reports_button.setObjectName("secondaryButton")
        self.open_reports_button.clicked.connect(self.open_reports)
        self.repair_button = QPushButton("Instalar / reparar IA")
        self.repair_button.setObjectName("secondaryButton")
        self.repair_button.clicked.connect(lambda: self.run_command(MOBPSY_AI_SETUP_BIN, []))
        rrow.addWidget(self.report_button)
        rrow.addWidget(self.open_reports_button)
        rrow.addWidget(self.repair_button)
        rrow.addStretch(1)
        self.body.addLayout(rrow)

    def ask_case(self):
        question = self.question.text().strip()
        if not question:
            QMessageBox.information(self, "Pregunta vacía", "Escribe una pregunta concreta.")
            return
        self.run_command(MOBPSY_AI_BIN, ["ask", question])

    def open_reports(self):
        try:
            data = json.loads(ACTIVE_CASE_FILE.read_text(encoding="utf-8"))
            case_dir = Path(str(data.get("case_dir") or "")).expanduser()
            if not case_dir.is_dir():
                raise ValueError
        except Exception:
            QMessageBox.information(self, "MobPsy", "No hay ningún caso activo.")
            return
        reports = case_dir / "Informes"
        reports.mkdir(exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(reports)))


class SettingsPage(CommandPage):
    def __init__(self):
        super().__init__("Configuración", "Versión y comprobación de nuevas versiones de MobPsy.")
        info=QLabel(f"Versión instalada: {APP_VERSION}\nRepositorio: {UPDATE_REPOSITORY}\n\nHasta la primera publicación, MobPsy permanece en 1.0.0.")
        info.setWordWrap(True); info.setObjectName("cardText"); self.body.addWidget(info)
        row=QHBoxLayout()
        check=QPushButton("Comprobar actualizaciones"); check.setObjectName("primaryButton")
        check.clicked.connect(lambda: self.run_command(UPDATE_CHECK_BIN, []))
        github=QPushButton("Abrir GitHub Releases"); github.setObjectName("secondaryButton")
        github.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(UPDATE_RELEASES_URL)))
        row.addWidget(check); row.addWidget(github); self.body.addLayout(row)


class FrameworksPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(10)

        title = QLabel("Frameworks OSINT")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "MobPsy centraliza tres frameworks completos. SpiderFoot utiliza su interfaz web "
            "local; Recon-ng y sn0int conservan sus consolas interactivas originales."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(18)

        row = QHBoxLayout()
        row.setSpacing(14)

        row.addWidget(FrameworkLauncherCard(
            "SpiderFoot",
            "Framework de automatización OSINT con más de 200 módulos y una interfaz web "
            "integrada. MobPsy levanta el servidor únicamente en 127.0.0.1.",
            "Abrir SpiderFoot",
            "direct",
            SPIDERFOOT_BIN,
        ))

        row.addWidget(FrameworkLauncherCard(
            "Recon-ng",
            "Framework modular de reconocimiento con marketplace de módulos y workspaces. "
            "Se abre en una terminal independiente porque su interfaz nativa es interactiva.",
            "Abrir Recon-ng",
            "terminal",
            RECONNG_BIN,
        ))

        row.addWidget(FrameworkLauncherCard(
            "sn0int",
            "Framework semiautomático y gestor de módulos OSINT con base de datos propia "
            "y módulos ejecutados en sandbox.",
            "Abrir sn0int",
            "terminal",
            SN0INT_BIN,
        ))

        layout.addLayout(row)
        layout.addSpacing(16)

        note = QFrame()
        note.setObjectName("placeholder")
        box = QVBoxLayout(note)
        box.setContentsMargins(26, 26, 26, 26)

        ntitle = QLabel("Catálogo núcleo completado")
        ntitle.setObjectName("placeholderTitle")
        ntext = QLabel(
            "Estos frameworks forman parte del catálogo actual de 25 herramientas integradas en MobPsy."
        )
        ntext.setObjectName("placeholderText")
        ntext.setWordWrap(True)

        box.addWidget(ntitle)
        box.addSpacing(8)
        box.addWidget(ntext)
        box.addStretch(1)

        layout.addWidget(note, 1)


class MobPsyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MobPsy")
        if LOGO_PATH.is_file():
            self.setWindowIcon(QIcon(str(LOGO_PATH)))
        self.resize(1600, 900)
        self.setMinimumSize(1080, 700)

        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = self._build_sidebar()
        self.stack = QStackedWidget()

        root.addWidget(self.sidebar)
        root.addWidget(self.stack, 1)

        self.pages: dict[str, QWidget] = {}
        for section in SECTIONS:
            if section.key == "home":
                page = self._build_home()
            elif section.key == "manual":
                page = ManualPage()
            elif section.key == "identity":
                page = IdentityPage()
            elif section.key == "email":
                page = EmailPage()
            elif section.key == "phone":
                page = PhoneInfogaPage()
            elif section.key == "social":
                page = SocialPage()
            elif section.key == "multimedia":
                page = MultimediaPage()
            elif section.key == "dns":
                page = DNSPage()
            elif section.key == "ips":
                page = IPPage()
            elif section.key == "infra":
                page = InfrastructurePage()
            elif section.key == "frameworks":
                page = FrameworksPage()
            elif section.key == "cases":
                page = CasesPage()
            elif section.key == "ai":
                page = AIPage()
            elif section.key == "settings":
                page = SettingsPage()
            else:
                page = self._build_placeholder(section)

            self.pages[section.key] = page
            self.stack.addWidget(page)

        self.show_section("home")
        QTimer.singleShot(1800, self._check_updates_on_startup)

    def _check_updates_on_startup(self):
        if not Path(UPDATE_CHECK_BIN).is_file(): return
        self.update_process = QProcess(self)
        self.update_process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.update_process.finished.connect(self._update_check_finished)
        self.update_process.start(UPDATE_CHECK_BIN, ["--json"])

    def _update_check_finished(self, code, _status):
        if code != 0 or not hasattr(self, "update_process"): return
        raw=bytes(self.update_process.readAllStandardOutput()).decode("utf-8", errors="replace").strip()
        try: data=json.loads(raw)
        except Exception: return
        if data.get("status")!="update_available": return
        box=QMessageBox(self); box.setWindowTitle("Actualización disponible")
        box.setText(f"MobPsy {data.get('latest')} está disponible.")
        box.setInformativeText(f"Versión instalada: {APP_VERSION}\nConsulta la Release antes de actualizar.")
        open_button=box.addButton("Abrir Release", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("Más tarde", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is open_button:
            QDesktopServices.openUrl(QUrl(str(data.get("url") or UPDATE_RELEASES_URL)))

    def _build_sidebar(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("sidebar")
        frame.setFixedWidth(235)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 24, 18, 18)
        layout.setSpacing(4)

        if LOGO_PATH.is_file():
            logo = QLabel()
            pixmap = QPixmap(str(LOGO_PATH))
            logo.setPixmap(pixmap.scaled(76, 76, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            layout.addWidget(logo)

        brand = QLabel("MobPsy")
        brand.setObjectName("brand")
        sub = QLabel("OSINT WORKSTATION")
        sub.setObjectName("brandSub")

        layout.addWidget(brand)
        layout.addWidget(sub)
        layout.addSpacing(24)

        self.nav_buttons: dict[str, QPushButton] = {}

        groups = [
            ("GENERAL", ["home", "manual"]),
            ("INVESTIGACIÓN", ["identity", "email", "phone", "social", "multimedia", "dns", "ips", "infra", "frameworks"]),
            ("ANÁLISIS", ["cases", "correlation", "ai"]),
            ("SISTEMA", ["tools", "settings"]),
        ]

        section_by_key = {s.key: s for s in SECTIONS}

        for group_name, keys in groups:
            group = QLabel(group_name)
            group.setObjectName("sectionLabel")
            layout.addWidget(group)

            for key in keys:
                section = section_by_key[key]
                button = QPushButton(section.label)
                button.setObjectName("navButton")
                button.setCheckable(True)
                button.setCursor(Qt.CursorShape.PointingHandCursor)
                button.clicked.connect(lambda _checked=False, k=key: self.show_section(k))
                self.nav_buttons[key] = button
                layout.addWidget(button)

        layout.addStretch(1)
        version = QLabel(f"MobPsy {APP_VERSION}")
        version.setObjectName("version")
        layout.addWidget(version)
        return frame

    def _page_shell(self, title: str, subtitle: str) -> tuple[QWidget, QVBoxLayout]:
        container = QWidget()
        outer = QVBoxLayout(container)
        outer.setContentsMargins(36, 30, 36, 30)
        outer.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("pageSubtitle")
        subtitle_label.setWordWrap(True)

        outer.addWidget(title_label)
        outer.addWidget(subtitle_label)
        outer.addSpacing(18)
        return container, outer

    def _build_home(self) -> QWidget:
        page, layout = self._page_shell(
            "Centro de investigación",
            "MobPsy dispone de 25 herramientas integradas, con módulos específicos de Personas, DNS e IPs."
        )

        row = QHBoxLayout()
        row.setSpacing(14)

        row.addWidget(StatusCard(
            "Workstation",
            "Ubuntu Desktop y entorno gráfico disponibles.",
            "● Operativa",
            True,
        ))
        row.addWidget(StatusCard(
            "Navegadores",
            "Firefox, Chromium y Tor Browser preparados.",
            "● Preparados",
            True,
        ))
        row.addWidget(StatusCard(
            "Herramientas OSINT",
            "25 herramientas integradas, incluidas utilidades específicas de DNS e IPs.",
            "● 25 integradas",
            True,
        ))

        layout.addLayout(row)
        layout.addSpacing(20)

        placeholder = QFrame()
        placeholder.setObjectName("placeholder")
        box = QVBoxLayout(placeholder)
        box.setContentsMargins(26, 28, 26, 28)

        title = QLabel("Catálogo núcleo completado")
        title.setObjectName("placeholderTitle")
        text = QLabel(
            "La interfaz gráfica dispone ahora de categorías reales para Personas, DNS, IPs, "
            "Web / Infraestructura y Frameworks, además del resto de módulos."
        )
        text.setObjectName("placeholderText")
        text.setWordWrap(True)

        box.addWidget(title)
        box.addSpacing(6)
        box.addWidget(text)
        box.addStretch(1)

        layout.addWidget(placeholder, 1)
        return page

    def _build_placeholder(self, section: Section) -> QWidget:
        page, layout = self._page_shell(section.title, section.description)

        placeholder = QFrame()
        placeholder.setObjectName("placeholder")
        placeholder.setMinimumHeight(300)

        box = QVBoxLayout(placeholder)
        box.setContentsMargins(30, 30, 30, 30)
        box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Módulo preparado")
        title.setObjectName("placeholderTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text = QLabel(
            "La pantalla y su navegación ya forman parte de MobPsy.\n"
            "Este módulo forma parte de la instalación actual de MobPsy."
        )
        text.setObjectName("placeholderText")
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text.setWordWrap(True)

        box.addWidget(title)
        box.addSpacing(8)
        box.addWidget(text)

        layout.addWidget(placeholder, 1)
        return page

    def show_section(self, key: str) -> None:
        page = self.pages.get(key)
        if page is None:
            return

        self.stack.setCurrentWidget(page)
        for button_key, button in self.nav_buttons.items():
            button.blockSignals(True)
            button.setChecked(button_key == key)
            button.blockSignals(False)

install_mobpsy_functional_pages(MobPsyWindow)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("MobPsy")
    app.setOrganizationName("MobPsy")
    app.setStyleSheet(STYLE)

    font = QFont("Ubuntu")
    font.setPointSize(10)
    app.setFont(font)

    window = MobPsyWindow()
    window.showMaximized()
    return app.exec()



if __name__ == "__main__":
    raise SystemExit(main())
