# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import subprocess

from PySide6.QtCore import QProcess, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QMessageBox
)

CHECK_BIN = "/usr/local/bin/mobpsy-update-check"
UPDATE_BIN = "/usr/local/bin/mobpsy-update"
RELEASES_URL = "https://github.com/alvarosr/mobpsy/releases"

class MobPsyUpdatePage(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.check_process = None
        self.install_process = None
        self.latest = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)

        title = QLabel("Actualizaciones")
        title.setStyleSheet("font-size: 28px; font-weight: 700;")
        layout.addWidget(title)

        desc = QLabel(
            "Actualiza una OVA de MobPsy directamente desde GitHub Releases, "
            "sin Vagrant y sin descargar una OVA nueva."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.version_label = QLabel(self._installed_text())
        self.version_label.setWordWrap(True)
        layout.addWidget(self.version_label)

        row = QHBoxLayout()
        self.check_btn = QPushButton("Buscar actualizaciones")
        self.install_btn = QPushButton("Descargar e instalar")
        self.install_btn.setEnabled(False)
        self.rollback_btn = QPushButton("Restaurar última copia")
        self.github_btn = QPushButton("Abrir GitHub Releases")
        row.addWidget(self.check_btn)
        row.addWidget(self.install_btn)
        row.addWidget(self.rollback_btn)
        row.addWidget(self.github_btn)
        row.addStretch(1)
        layout.addLayout(row)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("Aquí aparecerá el estado de las actualizaciones.")
        layout.addWidget(self.output, 1)

        self.check_btn.clicked.connect(self.check_updates)
        self.install_btn.clicked.connect(self.install_update)
        self.rollback_btn.clicked.connect(self.rollback)
        self.github_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(RELEASES_URL)))

    def _installed_text(self):
        try:
            version = Path("/etc/mobpsy/version").read_text(encoding="utf-8").strip()
        except Exception:
            version = "1.0.0"
        return f"Versión instalada: {version}\nRepositorio: alvarosr/mobpsy"

    def check_updates(self):
        if not Path(CHECK_BIN).is_file():
            self.output.setPlainText("El actualizador interno no está instalado.")
            return
        self.output.setPlainText("Consultando GitHub Releases...\n")
        self.check_btn.setEnabled(False)
        self.check_process = QProcess(self)
        self.check_process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.check_process.finished.connect(self._check_finished)
        self.check_process.start(CHECK_BIN, ["--json"])

    def _check_finished(self, code, _status):
        self.check_btn.setEnabled(True)
        raw = bytes(self.check_process.readAllStandardOutput()).decode("utf-8", errors="replace").strip()
        if code != 0:
            self.output.appendPlainText(raw or "No se pudo consultar GitHub.")
            return
        try:
            data = json.loads(raw)
        except Exception:
            self.output.appendPlainText(raw)
            return

        self.latest = data.get("latest")
        status = data.get("status")
        self.output.setPlainText(data.get("message") or "")
        if data.get("url"):
            self.output.appendPlainText("\n" + str(data.get("url")))

        can_install = status == "update_available" and bool(data.get("guest_asset"))
        self.install_btn.setEnabled(can_install)
        if status == "update_available":
            self.output.appendPlainText(
                "\nEl paquete será verificado por SHA-256 y se creará una copia de seguridad antes de instalarlo."
            )

    def install_update(self):
        if not self.latest:
            return
        answer = QMessageBox.question(
            self,
            "Actualizar MobPsy",
            f"Se instalará MobPsy {self.latest}.\n\n"
            "Se creará un backup antes de modificar /opt/mobpsy.\n"
            "Los casos y evidencias del usuario no se borrarán.\n\n"
            "¿Continuar?"
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self.output.setPlainText(f"Instalando MobPsy {self.latest}...\n")
        self.install_btn.setEnabled(False)
        self.check_btn.setEnabled(False)
        self.install_process = QProcess(self)
        self.install_process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.install_process.readyReadStandardOutput.connect(self._install_read)
        self.install_process.finished.connect(self._install_finished)
        self.install_process.start(UPDATE_BIN, ["--version", str(self.latest)])

    def _install_read(self):
        data = bytes(self.install_process.readAllStandardOutput()).decode("utf-8", errors="replace")
        if data:
            self.output.insertPlainText(data)

    def _install_finished(self, code, _status):
        self._install_read()
        self.check_btn.setEnabled(True)
        if code == 0:
            self.version_label.setText(self._installed_text())
            QMessageBox.information(
                self,
                "MobPsy actualizado",
                "Actualización completada.\n\nCierra y vuelve a abrir MobPsy."
            )
        else:
            self.output.appendPlainText("\n[ERROR] La actualización no se completó.")

    def rollback(self):
        answer = QMessageBox.question(
            self,
            "Restaurar actualización",
            "Se restaurará el backup más reciente creado por el actualizador.\n\n¿Continuar?"
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        subprocess.Popen(["gnome-terminal", "--", UPDATE_BIN, "--rollback"])
