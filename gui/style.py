# -*- coding: utf-8 -*-
"""
Estilo QSS unificado para a aplicação NeoX Viewer.
"""

DARK_THEME = """
    QMainWindow {
        background-color: #2b2b30;
    }
    QMenuBar {
        background-color: #333338;
        color: #cccccc;
        border-bottom: 1px solid #444;
    }
    QMenuBar::item:selected {
        background-color: #4a6fa5;
    }
    QMenu {
        background-color: #333338;
        color: #cccccc;
        border: 1px solid #555;
    }
    QMenu::item:selected {
        background-color: #4a6fa5;
    }
    QLabel {
        color: #999;
        padding: 6px;
        font-size: 11px;
    }
    QListWidget {
        background-color: #252528;
        color: #cccccc;
        border: none;
        font-size: 12px;
        outline: 0;
    }
    QListWidget::item {
        padding: 6px 10px;
        border-bottom: 1px solid #333;
    }
    QListWidget::item:selected {
        background-color: #4a6fa5;
        color: white;
    }
    QListWidget::item:hover {
        background-color: #3a3a42;
    }
    QStatusBar {
        background-color: #333338;
        color: #999;
        font-size: 11px;
        border-top: 1px solid #444;
    }
    QSplitter::handle {
        background-color: #444;
        width: 2px;
    }
    QToolBar {
        background-color: #333338;
        border-bottom: 1px solid #444;
        spacing: 3px;
        padding: 3px 6px;
    }
    QToolBar::separator {
        background-color: #555;
        width: 1px;
        margin: 4px 4px;
    }
    QToolButton {
        background-color: #3a3a42;
        color: #aaaaaa;
        border: 1px solid #505058;
        border-radius: 3px;
        padding: 3px 12px;
        font-size: 11px;
    }
    QToolButton:checked {
        background-color: #4a6fa5;
        color: #ffffff;
        border-color: #3d5f8f;
    }
    QToolButton:hover:!checked {
        background-color: #45454f;
        color: #cccccc;
    }
"""
