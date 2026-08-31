# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess

from PySide6.QtCore import QProcess
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QPlainTextEdit
)

TOOLS = [
    ("Personas", "Sherlock", "mobpsy-sherlock"),
    ("Personas", "Maigret", "mobpsy-maigret"),
    ("Personas", "CrossLinked", "mobpsy-crosslinked"),
    ("Personas", "ClatScope", "mobpsy-clatscope"),
    ("Correos", "Holehe", "mobpsy-holehe"),
    ("Correos", "ProtOSINT", "mobpsy-protosint"),
    ("Correos", "Zehef", "mobpsy-zehef"),
    ("Teléfonos", "PhoneInfoga", "mobpsy-phoneinfoga"),
    ("Redes sociales", "Social-Analyzer", "mobpsy-social-analyzer"),
    ("Redes sociales", "Instaloader", "mobpsy-instaloader"),
    ("Multimedia", "ExifTool", "mobpsy-exiftool"),
    ("Multimedia", "MediaInfo", "mobpsy-mediainfo"),
    ("DNS", "Subfinder", "mobpsy-subfinder"),
    ("DNS", "DNSRecon", "mobpsy-dnsrecon"),
    ("DNS", "dig", "mobpsy-dig"),
    ("DNS", "host", "mobpsy-host"),
    ("IPs", "Whois", "mobpsy-whois"),
    ("IPs", "GeoIPLookup", "mobpsy-geoiplookup"),
    ("Web / Infraestructura", "WhatWeb", "mobpsy-whatweb"),
    ("Web / Infraestructura", "WAFW00F", "mobpsy-wafw00f"),
    ("Web / Infraestructura", "Photon", "mobpsy-photon"),
    ("Web / Infraestructura", "theHarvester", "mobpsy-theharvester"),
    ("Frameworks", "SpiderFoot", "mobpsy-spiderfoot"),
    ("Frameworks", "Recon-ng", "mobpsy-reconng"),
    ("Frameworks", "sn0int", "mobpsy-sn0int"),
]

class MobPsyToolsPage(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(10)

        title = QLabel("Herramientas instaladas")
        title.setStyleSheet("font-size: 28px; font-weight: 700;")
        layout.addWidget(title)

        desc = QLabel("Estado real de las 25 herramientas núcleo integradas en MobPsy.")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        buttons = QHBoxLayout()
        self.refresh_btn = QPushButton("Actualizar estado")
        self.version_btn = QPushButton("Consultar versión")
        self.help_btn = QPushButton("Abrir ayuda")
        buttons.addWidget(self.refresh_btn)
        buttons.addWidget(self.version_btn)
        buttons.addWidget(self.help_btn)
        buttons.addStretch(1)
        layout.addLayout(buttons)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Categoría", "Herramienta", "Comando", "Estado", "Versión"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table, 1)

        self.refresh_btn.clicked.connect(self.refresh_status)
        self.version_btn.clicked.connect(self.query_version)
        self.help_btn.clicked.connect(self.open_help)
        self.refresh_status()

    def refresh_status(self):
        self.table.setRowCount(0)
        for category, name, command in TOOLS:
            row = self.table.rowCount()
            self.table.insertRow(row)
            exe = shutil.which(command)
            vals = [category, name, command, "OK" if exe else "No detectada", "—"]
            for col, val in enumerate(vals):
                self.table.setItem(row, col, QTableWidgetItem(val))

    def _selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "MobPsy", "Selecciona una herramienta.")
            return None, None
        return row, self.table.item(row, 2).text()

    def query_version(self):
        row, command = self._selected()
        if command is None:
            return
        exe = shutil.which(command)
        if not exe:
            QMessageBox.warning(self, "MobPsy", f"No se encuentra {command}.")
            return
        result = "Instalada"
        for arg in ("--version", "-V", "version"):
            try:
                p = subprocess.run([exe, arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, timeout=4)
                lines = [x.strip() for x in p.stdout.splitlines() if x.strip()]
                if lines:
                    result = lines[0][:160]
                    break
            except Exception:
                pass
        self.table.setItem(row, 4, QTableWidgetItem(result))

    def open_help(self):
        _, command = self._selected()
        if command is None:
            return
        if not shutil.which(command):
            QMessageBox.warning(self, "MobPsy", f"No se encuentra {command}.")
            return
        safe = command.replace("'", "")
        subprocess.Popen(["gnome-terminal", "--", "bash", "-lc",
                          f"{safe} --help 2>&1 | less; exec bash"])



class MobPsyCorrelationPage(QWidget):
    ACTION_STYLE = """
    QPushButton {
        background: #6d5dfc;
        border: 1px solid #7567fc;
        border-radius: 8px;
        color: white;
        padding: 9px 14px;
        font-weight: 700;
    }
    QPushButton:hover { background: #7869fd; border-color: #8478ff; }
    QPushButton:pressed { background: #5f50e9; border-color: #6657ed; }
    QPushButton:disabled {
        background: #343a46;
        border-color: #3d4450;
        color: #7d8590;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self._stdout)
        self.process.readyReadStandardError.connect(self._stderr)
        self.process.finished.connect(self._finished)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(10)

        title = QLabel("Correlación")
        title.setStyleSheet("font-size: 28px; font-weight: 700;")
        layout.addWidget(title)

        desc = QLabel(
            "MobPsy Correlator compara las evidencias y exportaciones del caso activo. "
            "Detecta correos, dominios, IP, URL, teléfonos, usuarios y hashes y destaca "
            "las entidades que aparecen en varias fuentes."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.case_status = QLabel()
        self.case_status.setWordWrap(True)
        self.case_status.setStyleSheet(
            "padding: 10px 12px; border: 1px solid #263142; border-radius: 8px;"
        )
        layout.addWidget(self.case_status)

        self.metrics = QLabel("Archivos: —   ·   Entidades: —   ·   Relaciones: —   ·   Coincidencias: —")
        self.metrics.setStyleSheet("font-size: 15px; font-weight: 700; padding: 8px 2px;")
        layout.addWidget(self.metrics)

        top_row = QHBoxLayout()
        self.run_btn = QPushButton("Ejecutar correlación")
        self.refresh_btn = QPushButton("Actualizar resultados")
        self.cases_btn = QPushButton("Abrir caso activo")
        for button in (self.run_btn, self.refresh_btn, self.cases_btn):
            button.setStyleSheet(self.ACTION_STYLE)
            top_row.addWidget(button)
        top_row.addStretch(1)
        layout.addLayout(top_row)

        files_row = QHBoxLayout()
        self.report_btn = QPushButton("Informe")
        self.graph_btn = QPushButton("Grafo")
        self.entities_btn = QPushButton("Entidades CSV")
        self.relations_btn = QPushButton("Relaciones CSV")
        self.json_btn = QPushButton("JSON")
        self.analysis_btn = QPushButton("Carpeta Análisis")
        for button in (
            self.report_btn, self.graph_btn, self.entities_btn,
            self.relations_btn, self.json_btn, self.analysis_btn,
        ):
            button.setStyleSheet(self.ACTION_STYLE)
            files_row.addWidget(button)
        files_row.addStretch(1)
        layout.addLayout(files_row)

        table_title = QLabel("Coincidencias más relevantes")
        table_title.setStyleSheet("font-size: 17px; font-weight: 700; margin-top: 4px;")
        layout.addWidget(table_title)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Tipo", "Entidad", "Fuentes", "Apariciones"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setMinimumHeight(180)
        layout.addWidget(self.table, 1)

        output_title = QLabel("Actividad")
        output_title.setStyleSheet("font-size: 16px; font-weight: 700;")
        layout.addWidget(output_title)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setMaximumHeight(150)
        self.output.setPlaceholderText("Aquí aparecerá el progreso de MobPsy Correlator.")
        layout.addWidget(self.output)

        self.run_btn.clicked.connect(self.run_correlation)
        self.refresh_btn.clicked.connect(self.refresh_results)
        self.cases_btn.clicked.connect(self.open_active_case)
        self.report_btn.clicked.connect(lambda: self.open_result("report"))
        self.graph_btn.clicked.connect(lambda: self.open_result("graph"))
        self.entities_btn.clicked.connect(lambda: self.open_result("entities"))
        self.relations_btn.clicked.connect(lambda: self.open_result("relations"))
        self.json_btn.clicked.connect(lambda: self.open_result("json"))
        self.analysis_btn.clicked.connect(lambda: self.open_result("folder"))

        self.refresh_results()

    def cases_dir(self) -> Path:
        path = Path.home() / "MobPsy" / "Casos"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def active_case_dir(self) -> Path | None:
        active = self.cases_dir() / ".active_case.json"
        if not active.is_file():
            return None
        try:
            data = json.loads(active.read_text(encoding="utf-8"))
        except Exception:
            return None

        raw_path = str(data.get("case_dir") or "").strip()
        if raw_path:
            path = Path(raw_path).expanduser()
            if path.is_dir():
                return path

        wanted = str(data.get("case_id") or data.get("id") or "").strip()
        if wanted:
            for folder in self.cases_dir().iterdir():
                if not folder.is_dir():
                    continue
                manifest = folder / "case.json"
                if not manifest.is_file():
                    continue
                try:
                    case = json.loads(manifest.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if wanted in (
                    str(case.get("case_id") or ""),
                    str(case.get("id") or ""),
                    folder.name,
                ):
                    return folder
        return None

    def analysis_dir(self) -> Path | None:
        case = self.active_case_dir()
        return case / "Analisis" if case else None

    def _set_file_buttons(self, enabled: bool):
        for button in (
            self.report_btn, self.graph_btn, self.entities_btn,
            self.relations_btn, self.json_btn, self.analysis_btn,
        ):
            button.setEnabled(enabled)

    def refresh_results(self):
        exe = shutil.which("mobpsy-correlate")
        case = self.active_case_dir()

        if case is None:
            self.case_status.setText(
                "● Sin caso activo. Activa un caso desde «Casos» antes de ejecutar la correlación."
            )
            self.run_btn.setEnabled(False)
            self.cases_btn.setEnabled(False)
            self._set_file_buttons(False)
            self.metrics.setText("Archivos: —   ·   Entidades: —   ·   Relaciones: —   ·   Coincidencias: —")
            self.table.setRowCount(0)
            return

        manifest = {}
        try:
            manifest = json.loads((case / "case.json").read_text(encoding="utf-8"))
        except Exception:
            pass

        title = manifest.get("title") or case.name
        case_id = manifest.get("case_id") or manifest.get("id") or case.name
        self.case_status.setText(
            f"● Caso activo: {title}   ·   ID: {case_id}\\nRuta: {case}"
        )
        self.run_btn.setEnabled(bool(exe))
        self.cases_btn.setEnabled(True)

        out_dir = case / "Analisis"
        payload_path = out_dir / "correlation.json"
        if not payload_path.is_file():
            self._set_file_buttons(False)
            self.analysis_btn.setEnabled(out_dir.is_dir())
            self.metrics.setText("Todavía no hay resultados. Pulsa «Ejecutar correlación».")
            self.table.setRowCount(0)
            return

        try:
            payload = json.loads(payload_path.read_text(encoding="utf-8"))
        except Exception as exc:
            self.metrics.setText(f"No se pudo leer correlation.json: {exc}")
            self.table.setRowCount(0)
            return

        entities = payload.get("entities") or []
        relations = payload.get("relations") or []
        repeated = [e for e in entities if int(e.get("source_count") or 0) > 1]
        repeated.sort(
            key=lambda e: (
                -int(e.get("source_count") or 0),
                -int(e.get("occurrences") or 0),
                str(e.get("type") or ""),
                str(e.get("value") or ""),
            )
        )

        self.metrics.setText(
            f"Archivos: {payload.get('files_scanned', 0)}   ·   "
            f"Entidades: {len(entities)}   ·   Relaciones: {len(relations)}   ·   "
            f"Coincidencias: {len(repeated)}"
        )

        self.table.setRowCount(0)
        rows = repeated[:100] if repeated else sorted(
            entities,
            key=lambda e: (-int(e.get("occurrences") or 0), str(e.get("value") or "")),
        )[:50]
        for entity in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = (
                str(entity.get("type") or ""),
                str(entity.get("value") or ""),
                str(entity.get("source_count") or 0),
                str(entity.get("occurrences") or 0),
            )
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(value))

        self.report_btn.setEnabled(
            (out_dir / "correlation_report.html").is_file()
            or (out_dir / "correlation_report.md").is_file()
        )
        self.graph_btn.setEnabled(
            (out_dir / "correlation_graph.svg").is_file()
            or (out_dir / "correlation.graphml").is_file()
        )
        self.entities_btn.setEnabled((out_dir / "entities.csv").is_file())
        self.relations_btn.setEnabled((out_dir / "relations.csv").is_file())
        self.json_btn.setEnabled(payload_path.is_file())
        self.analysis_btn.setEnabled(out_dir.is_dir())

    def run_correlation(self):
        if self.process.state() != QProcess.ProcessState.NotRunning:
            return
        if self.active_case_dir() is None:
            self.refresh_results()
            return
        if not shutil.which("mobpsy-correlate"):
            QMessageBox.warning(self, "Correlator no disponible", "No se encuentra mobpsy-correlate.")
            return

        self.output.clear()
        self.output.appendPlainText("Ejecutando MobPsy Correlator...\\n")
        self.run_btn.setEnabled(False)
        self.process.start("/usr/bin/env", ["bash", "-lc", "mobpsy-correlate"])

    def _stdout(self):
        data = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
        if data:
            self.output.insertPlainText(data)

    def _stderr(self):
        data = bytes(self.process.readAllStandardError()).decode("utf-8", errors="replace")
        if data:
            self.output.insertPlainText(data)

    def _finished(self, code, _status):
        self.output.appendPlainText(f"\\nProceso finalizado con código {code}.")
        self.refresh_results()
        if code == 0:
            self.output.appendPlainText("\\nResultados actualizados. Usa los botones superiores para abrirlos.")

    def open_active_case(self):
        case = self.active_case_dir()
        if case:
            subprocess.Popen(["xdg-open", str(case)])

    def _open_path(self, path: Path, preferred: str | None = None):
        if not path.exists():
            QMessageBox.information(self, "Resultado no disponible", f"No existe todavía:\\n{path}")
            return
        try:
            if preferred and shutil.which(preferred):
                subprocess.Popen([preferred, str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:
            QMessageBox.critical(self, "No se pudo abrir", str(exc))

    def open_result(self, kind: str):
        out_dir = self.analysis_dir()
        if out_dir is None:
            self.refresh_results()
            return

        if kind == "folder":
            self._open_path(out_dir)
        elif kind == "report":
            html_report = out_dir / "correlation_report.html"
            md_report = out_dir / "correlation_report.md"
            self._open_path(html_report if html_report.is_file() else md_report)
        elif kind == "graph":
            svg = out_dir / "correlation_graph.svg"
            graphml = out_dir / "correlation.graphml"
            self._open_path(svg if svg.is_file() else graphml)
        elif kind == "entities":
            self._open_path(out_dir / "entities.csv", "libreoffice")
        elif kind == "relations":
            self._open_path(out_dir / "relations.csv", "libreoffice")
        elif kind == "json":
            editor = (
                "gnome-text-editor" if shutil.which("gnome-text-editor")
                else "gedit" if shutil.which("gedit")
                else None
            )
            self._open_path(out_dir / "correlation.json", editor)
