# -*- coding: utf-8 -*-
from __future__ import annotations

from PySide6.QtWidgets import QLabel, QLayout, QWidget
from mobpsy_functional_pages import MobPsyToolsPage, MobPsyCorrelationPage
from mobpsy_update_page import MobPsyUpdatePage

TOOLS_TEXTS = (
    "Herramientas instaladas",
    "Aquí se mostrará el estado, versión y mantenimiento de cada herramienta.",
    "Aqui se mostrara el estado, version y mantenimiento de cada herramienta.",
)
SETTINGS_TEXTS = (
    "Versión y comprobación de nuevas versiones de MobPsy.",
    "Version y comprobacion de nuevas versiones de MobPsy.",
    "Versión instalada:",
    "Version instalada:",
)

CORR_TEXTS = (
    "Correlación",
    "Correlacion",
    "Esta sección será la base de MobPsy Correlator.",
    "Esta seccion sera la base de MobPsy Correlator.",
)

def _clear_layout(layout: QLayout):
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        child_layout = item.layout()
        if w is not None:
            w.setParent(None)
            w.deleteLater()
        elif child_layout is not None:
            _clear_layout(child_layout)

def _score_page(page: QWidget, texts):
    score = 0
    for lab in page.findChildren(QLabel):
        t = (lab.text() or "").strip()
        for marker in texts:
            if marker in t:
                score += 1
    return score

def _candidate_pages(window):
    # Buscar ancestros de labels hasta el widget que sea página completa:
    # normalmente es hijo directo de QStackedWidget/QStackedLayout.
    pages = set()
    for lab in window.findChildren(QLabel):
        txt = (lab.text() or "").strip()
        if not any(m in txt for m in TOOLS_TEXTS + CORR_TEXTS):
            continue
        w = lab
        best = None
        for _ in range(12):
            p = w.parentWidget()
            if p is None:
                break
            best = p
            par = p.parentWidget()
            if par is not None and par.metaObject().className() == "QStackedWidget":
                pages.add(p)
                break
            w = p
        if best is not None:
            pages.add(best)
    return list(pages)

def _replace_contents(page: QWidget, replacement: QWidget):
    layout = page.layout()
    if layout is None:
        # Muy raro, pero preservamos la página creando un layout.
        from PySide6.QtWidgets import QVBoxLayout
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
    else:
        _clear_layout(layout)
    layout.addWidget(replacement)

def patch_window(window):
    pages = _candidate_pages(window)
    tools_done = False
    corr_done = False
    settings_done = False

    # Primero elegir por contenido real, no por índice ni nombre de clase.
    for page in pages:
        ts = _score_page(page, TOOLS_TEXTS)
        cs = _score_page(page, CORR_TEXTS)

        # "Correlación" puede existir en navegación/sidebar, por eso exigimos
        # también el texto descriptivo o que sea claramente la página ganadora.
        if ts >= 1 and not tools_done:
            _replace_contents(page, MobPsyToolsPage())
            tools_done = True
            continue

        corr_desc = any(
            marker in (lab.text() or "")
            for lab in page.findChildren(QLabel)
            for marker in CORR_TEXTS[2:]
        )
        if corr_desc and not corr_done:
            _replace_contents(page, MobPsyCorrelationPage())
            corr_done = True

        settings_desc = any(
            marker in (lab.text() or "")
            for lab in page.findChildren(QLabel)
            for marker in SETTINGS_TEXTS
        )
        if settings_desc and not settings_done:
            _replace_contents(page, MobPsyUpdatePage())
            settings_done = True

    # Segundo intento más específico por descripciones, por si la página no era
    # hija directa de un QStackedWidget.
    if not tools_done or not corr_done or not settings_done:
        for lab in window.findChildren(QLabel):
            txt = (lab.text() or "").strip()
            is_tools = any(m in txt for m in TOOLS_TEXTS[1:])
            is_corr = any(m in txt for m in CORR_TEXTS[2:])
            is_settings = any(m in txt for m in SETTINGS_TEXTS)
            if (is_tools and not tools_done) or (is_corr and not corr_done) or (is_settings and not settings_done):
                w = lab.parentWidget()
                # subir hasta un contenedor razonablemente grande
                target = w
                for _ in range(5):
                    if target is None:
                        break
                    if target.layout() is not None and target.width() > 500 and target.height() > 300:
                        break
                    target = target.parentWidget()
                if target is not None:
                    if is_tools and not tools_done:
                        _replace_contents(target, MobPsyToolsPage())
                        tools_done = True
                    elif is_corr and not corr_done:
                        _replace_contents(target, MobPsyCorrelationPage())
                        corr_done = True
                    elif is_settings and not settings_done:
                        _replace_contents(target, MobPsyUpdatePage())
                        settings_done = True

    # Marcadores útiles para diagnóstico, sin romper si un nombre cambia.
    window.setProperty("mobpsyToolsFunctional", tools_done)
    window.setProperty("mobpsyCorrelationFunctional", corr_done)
    window.setProperty("mobpsyUpdatesFunctional", settings_done)

def install_mobpsy_functional_pages(window_class):
    if getattr(window_class, "_mobpsy_runtime_pages_installed", False):
        return

    original_init = window_class.__init__

    def wrapped_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        patch_window(self)

    window_class.__init__ = wrapped_init
    window_class._mobpsy_runtime_pages_installed = True
