# -*- coding: utf-8 -*-
"""
NeoX Mesh Viewer — Aplicação principal.
Uso: python app.py
"""

import sys
import os
import subprocess
import shutil

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QSplitter,
    QListWidget,
    QFileDialog,
    QAction,
    QStatusBar,
    QMessageBox,
    QListWidgetItem,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QLabel,
    QAbstractItemView,
    QToolBar,
    QSlider,
    QToolButton,
    QStyle,
    QDialog,
    QTreeWidget,
    QTreeWidgetItem,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon

from gui.viewer import ViewerWidget
from gui.style import DARK_THEME
from export.adapter import BlenderAdapter
from core.parser import parse_mesh
from core.gim_parser import parse_gim
from core.extract_mtg import parse_mtg
from core.exceptions import (
    NeoXError,
    FormatError,
    ValidationError,
    EOFError as NeoXEOFError,
    BlenderNotFoundError,
)


def _show_neox_error(parent, title, exc):
    """Exibe um QMessageBox com mensagem amigável e detalhes coluáveis."""
    import traceback

    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setIcon(QMessageBox.Critical)

    if isinstance(exc, FormatError):
        user_msg = (
            "O arquivo não é um formato NeoX válido.\n"
            "Verifique se selecionou o tipo correto de arquivo."
        )
    elif isinstance(exc, NeoXEOFError):
        user_msg = (
            "O arquivo está truncado ou corrompido e não pode ser lido completamente."
        )
    elif isinstance(exc, ValidationError):
        user_msg = (
            "Os dados do arquivo estão fora dos limites esperados.\n"
            "O arquivo pode estar corrompido."
        )
    elif isinstance(exc, BlenderNotFoundError):
        user_msg = (
            "Blender não encontrado.\n"
            "Instale o Blender 4.x ou 5.x, ou adicione-o ao PATH do sistema."
        )
    else:
        user_msg = "Ocorreu um erro inesperado."

    msg.setText(user_msg)
    msg.setDetailedText(
        "{0}: {1}\n\n{2}".format(type(exc).__name__, exc, traceback.format_exc())
    )
    msg.exec_()


class GimDetailDialog(QDialog):
    """Exibe os metadados de um manifesto .gim em uma árvore hirárquica."""

    def __init__(self, dto, parent=None):
        super(GimDetailDialog, self).__init__(parent)
        self.setWindowTitle("Ficha Técnica: Manifest .gim")
        self.setMinimumSize(600, 450)
        self._setup_ui(dto)

    def _setup_ui(self, dto):
        layout = QVBoxLayout(self)

        lbl_info = QLabel("<b>Fonte:</b> {0}".format(os.path.basename(dto.source_path)))
        layout.addWidget(lbl_info)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Atributo", "Valor"])
        self.tree.setColumnWidth(0, 200)
        layout.addWidget(self.tree)

        # 1. Assets
        root_asset = QTreeWidgetItem(self.tree, ["Assets Referenciados", ""])
        root_asset.setIcon(0, self.style().standardIcon(QStyle.SP_DirIcon))
        root_asset.setExpanded(True)

        for m in dto.mesh_paths:
            QTreeWidgetItem(root_asset, ["Model (.mesh)", m])
        for g in dto.gis_paths:
            QTreeWidgetItem(root_asset, ["Anim (.gis)", g])
        for s in dto.sfx_paths:
            QTreeWidgetItem(root_asset, ["Effect (.sfx)", s])
        for a in dto.audio_paths:
            QTreeWidgetItem(root_asset, ["Audio (.ags/.mp3)", a])
        for sc in dto.script_paths:
            QTreeWidgetItem(root_asset, ["Script (.lua/.act)", sc])
        for cf in dto.config_paths:
            QTreeWidgetItem(root_asset, ["Config (.xml/.json)", cf])
        for o in dto.other_paths:
            QTreeWidgetItem(root_asset, ["Extra Asset", o])
        if dto.mtg_path:
            QTreeWidgetItem(root_asset, ["Material (.mtg)", dto.mtg_path])

        # 2. Bounding (Matemática)
        root_bound = QTreeWidgetItem(self.tree, ["Bounding Box (Volume)", ""])
        root_bound.setIcon(0, self.style().standardIcon(QStyle.SP_FileDialogInfoView))
        root_bound.setExpanded(True)

        if dto.has_bounding:
            c = dto.bounding_center
            h = dto.bounding_half
            r = dto.bounding_radius
            QTreeWidgetItem(
                root_bound, ["Centro (X,Y,Z)", f"({c[0]:.3f}, {c[1]:.3f}, {c[2]:.3f})"]
            )
            QTreeWidgetItem(
                root_bound,
                ["Extensão (H_X,H_Y,H_Z)", f"({h[0]:.3f}, {h[1]:.3f}, {h[2]:.3f})"],
            )
            QTreeWidgetItem(root_bound, ["Raio da Esfera", f"{r:.3f}"])
        else:
            QTreeWidgetItem(root_bound, ["Status", "Sem metadados de volume"])

        # Botão Fechar
        from PyQt5.QtWidgets import QDialogButtonBox

        btns = QDialogButtonBox(QDialogButtonBox.Ok)
        btns.accepted.connect(self.accept)
        layout.addWidget(btns)


class MtgDetailDialog(QDialog):
    """Exibe os metadados de um material .mtg binário."""

    def __init__(self, dto, parent=None):
        super(MtgDetailDialog, self).__init__(parent)
        self.setWindowTitle("Ficha Técnica: Material .mtg")
        self.setMinimumSize(600, 500)
        self._setup_ui(dto)

    def _setup_ui(self, dto):
        layout = QVBoxLayout(self)

        lbl_info = QLabel("<b>Fonte:</b> {0}".format(os.path.basename(dto.source_path)))
        layout.addWidget(lbl_info)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Atributo", "Valor"])
        self.tree.setColumnWidth(0, 200)
        layout.addWidget(self.tree)

        # 1. Shaders
        root_sh = QTreeWidgetItem(self.tree, ["Shader / Técnica", ""])
        root_sh.setIcon(0, self.style().standardIcon(QStyle.SP_ComputerIcon))
        root_sh.setExpanded(True)
        for s in dto.shaders:
            QTreeWidgetItem(root_sh, ["Técnica", s])

        # 2. Texturas
        root_tx = QTreeWidgetItem(self.tree, ["Mapas / Texturas", ""])
        root_tx.setIcon(0, self.style().standardIcon(QStyle.SP_FileIcon))
        root_tx.setExpanded(True)
        for t in dto.textures:
            QTreeWidgetItem(root_tx, ["Sampler", t])

        # 3. Parâmetros (Hash XML)
        root_pr = QTreeWidgetItem(self.tree, ["Parâmetros de Hash", ""])
        root_pr.setIcon(0, self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        for p in dto.properties:
            QTreeWidgetItem(root_pr, ["Propriedade", p])

        from PyQt5.QtWidgets import QDialogButtonBox

        btns = QDialogButtonBox(QDialogButtonBox.Ok)
        btns.accepted.connect(self.accept)
        layout.addWidget(btns)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("NeoX Mesh Viewer")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)

        # Estado
        self.mesh_paths: dict[str, str] = {}  # nome → caminho absoluto
        self.gis_paths: dict[str, str] = {}  # nome → caminho absoluto
        self.current_dto = None
        self.current_path: str | None = None
        self.folder_path = ""
        self.blender = BlenderAdapter()

        # Sessão RGIS — carregado uma vez por pasta/personagem
        # Populado por _try_load_rgis() ao abrir uma pasta de assets
        self.rgis_session = None  # RGisDTO | None

        # Playback Runtime State
        self.timer = QTimer()
        self.timer.timeout.connect(self._on_timer_tick)
        self.is_playing = False
        self.current_frame = 0
        self.total_frames = 0

        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_timeline()
        self._setup_statusbar()
        self._apply_style()

    def _setup_ui(self):
        # Splitter principal
        splitter = QSplitter(Qt.Horizontal)

        # Painel esquerdo: lista de arquivos
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.folder_label = QLabel("Nenhuma pasta carregada")
        self.folder_label.setWordWrap(True)
        self.folder_label.setMaximumHeight(40)
        left_layout.addWidget(self.folder_label)

        self.asset_tabs = QTabWidget()

        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.file_list.currentItemChanged.connect(self._on_file_selected)
        self.asset_tabs.addTab(self.file_list, "Meshes")

        self.gis_list = QListWidget()
        self.gis_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.gis_list.currentItemChanged.connect(self._on_gis_selected)
        self.asset_tabs.addTab(self.gis_list, "GIS")

        left_layout.addWidget(self.asset_tabs)

        splitter.addWidget(left_panel)

        # Painel direito: viewport 3D
        self.viewer = ViewerWidget()
        self.viewer.mesh_loaded.connect(self._on_mesh_loaded)
        splitter.addWidget(self.viewer)

        self.viewport_stats_label = QLabel("Verts: - | Tris: -", self.viewer)
        self.viewport_stats_label.setStyleSheet(
            "padding: 4px 8px; font-weight: 600; color: #e8eef5;"
            "background-color: #0f1822;"
            "border: 1px solid #3b5166; border-radius: 4px;"
        )
        self.viewport_stats_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.viewport_stats_label.adjustSize()
        self.viewport_stats_label.move(12, 12)
        self.viewport_stats_label.raise_()

        # Proporção 1:3
        splitter.setSizes([280, 900])

        self.setCentralWidget(splitter)

    def _setup_menu(self):
        menubar = self.menuBar()

        # File
        file_menu = menubar.addMenu("&File")

        load_act = QAction("Load &Folder...", self)
        load_act.setShortcut("Ctrl+O")
        load_act.triggered.connect(self._load_folder)
        file_menu.addAction(load_act)

        file_menu.addSeparator()

        load_gis_act = QAction("Carregar Animação (.gis)...", self)
        load_gis_act.triggered.connect(self._on_action_open_gis)
        file_menu.addAction(load_gis_act)

        file_menu.addSeparator()

        exit_act = QAction("E&xit", self)
        exit_act.setShortcut("Ctrl+Q")
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        # Export
        export_menu = menubar.addMenu("&Export")

        fbx_act = QAction("Export &FBX...", self)
        fbx_act.setShortcut("Ctrl+E")
        fbx_act.triggered.connect(self._export_fbx)
        export_menu.addAction(fbx_act)

        merge_act = QAction("Export &Merge FBX...", self)
        merge_act.setShortcut("Ctrl+M")
        merge_act.setToolTip(
            "Exporta todos os arquivos selecionados em um único FBX mesclado"
        )
        merge_act.triggered.connect(self._export_merge_fbx)
        export_menu.addAction(merge_act)

        # Tools
        tools_menu = menubar.addMenu("&Tools")

        gim_act = QAction("Parse .gim File...", self)
        gim_act.setShortcut("Ctrl+G")
        gim_act.triggered.connect(self._on_action_parse_gim)
        tools_menu.addAction(gim_act)

        mtg_act = QAction("Analyze .mtg Material...", self)
        mtg_act.setShortcut("Ctrl+M")
        mtg_act.triggered.connect(self._on_action_parse_mtg)
        tools_menu.addAction(mtg_act)

    def _setup_toolbar(self):
        toolbar = QToolBar("Viewport")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        wireframe_act = QAction("Wireframe", self)
        wireframe_act.setCheckable(True)
        wireframe_act.setShortcut("W")
        wireframe_act.toggled.connect(self.viewer.set_wireframe)
        toolbar.addAction(wireframe_act)

        grid_act = QAction("Grid", self)
        grid_act.setCheckable(True)
        grid_act.setChecked(True)
        grid_act.setShortcut("G")
        grid_act.toggled.connect(self.viewer.set_show_grid)
        toolbar.addAction(grid_act)

        toolbar.addSeparator()

        self._submesh_act = QAction("Submeshes", self)
        self._submesh_act.setCheckable(True)
        self._submesh_act.toggled.connect(self._on_submesh_toggled)
        toolbar.addAction(self._submesh_act)

        self._weights_act = QAction("Weights", self)
        self._weights_act.setCheckable(True)
        self._weights_act.toggled.connect(self._on_weights_toggled)
        toolbar.addAction(self._weights_act)

        axes_act = QAction("Axes", self)
        axes_act.setCheckable(True)
        axes_act.setChecked(True)
        axes_act.toggled.connect(self.viewer.set_show_axes)
        toolbar.addAction(axes_act)

        arm_act = QAction("Armature", self)
        arm_act.setCheckable(True)
        arm_act.setShortcut("A")
        arm_act.toggled.connect(self.viewer.set_show_armature)
        toolbar.addAction(arm_act)

    def _setup_timeline(self):
        """Constrói a barra inferior de navegação de mídia (Timeline)."""
        self.timeline_toolbar = QToolBar("Timeline")
        self.timeline_toolbar.setMovable(False)
        self.addToolBar(Qt.BottomToolBarArea, self.timeline_toolbar)

        self.btn_play = QToolButton(self)
        self.btn_play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.btn_play.setCheckable(True)
        self.btn_play.toggled.connect(self._toggle_playback)
        self.timeline_toolbar.addWidget(self.btn_play)

        self.lbl_frame = QLabel("  Frame: 0 / 0  ")
        self.lbl_frame.setStyleSheet("font-weight: bold; color: #a4b8c6;")
        self.timeline_toolbar.addWidget(self.lbl_frame)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(0)
        self.slider.valueChanged.connect(self._on_slider_changed)
        self.timeline_toolbar.addWidget(self.slider)

    def _toggle_playback(self, checked):
        """Alterna as pulsações do Motor: Play ou Pause"""
        if self.total_frames <= 0:
            self.btn_play.setChecked(False)
            return

        self.is_playing = checked
        if self.is_playing:
            self.btn_play.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            self.timer.start(33)  # ~30.3 FPS
        else:
            self.btn_play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.timer.stop()

    def _on_timer_tick(self):
        """Avança Slider automaticamente a cada 33ms."""
        if self.current_frame < self.total_frames:
            self.slider.setValue(self.current_frame + 1)
        else:
            self.btn_play.setChecked(False)
            self.slider.setValue(0)

    def _on_slider_changed(self, value):
        """O arrasto da timeline."""
        self.current_frame = value
        self.lbl_frame.setText("  Frame: {0} / {1}  ".format(value, self.total_frames))

        if getattr(self, "evaluator", None) and getattr(self, "anim_sequence", None):
            fps = float(getattr(self.anim_sequence, "fps", 30.0) or 30.0)
            time_sec = value / fps
            bone_poses = self.anim_sequence.sample_all_channels(time_sec)
            # Sinalizar a variante para o skinning aplicar o flip se necessário
            if hasattr(self.anim_sequence.dto, "variant"):
                bone_poses["_variant"] = self.anim_sequence.dto.variant
            if hasattr(self.anim_sequence.dto, "rgis_bone_names"):
                bone_poses["_rgis_bone_names"] = self.anim_sequence.dto.rgis_bone_names
            if hasattr(self.anim_sequence.dto, "rgis_bone_trans"):
                bone_poses["_rgis_bone_trans"] = self.anim_sequence.dto.rgis_bone_trans

            from runtime.animation.skinning import compute_cpu_skinning

            verts = compute_cpu_skinning(
                self.current_dto, bone_poses, mapping_cache=self.bone_mapping
            )
            self.viewer.update_frame(verts)

    def _on_submesh_toggled(self, checked):
        if checked:
            self._weights_act.setChecked(False)
        self.viewer.set_submesh_debug(checked)

    def _on_weights_toggled(self, checked):
        if checked:
            self._submesh_act.setChecked(False)
        self.viewer.set_show_weights(checked)

    def _setup_statusbar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Pronto. Carregue uma pasta com arquivos .mesh")

    def _apply_style(self):
        self.setStyleSheet(DARK_THEME)

    # ------ Actions ------

    def _load_folder(self):
        path = QFileDialog.getExistingDirectory(
            self,
            "Selecionar pasta com arquivos .mesh",
            self.folder_path or os.path.expanduser("~"),
        )
        if not path:
            return

        self.folder_path = path
        self.folder_label.setText(os.path.basename(path))
        self.mesh_paths.clear()
        self.gis_paths.clear()
        self.file_list.clear()
        self.gis_list.clear()
        self.current_dto = None
        self._update_view_stats()

        # Buscar .mesh e .gis recursivamente
        for root, dirs, files in os.walk(path):
            for f in sorted(files):
                lower = f.lower()
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, path)
                if lower.endswith(".mesh"):
                    self.mesh_paths[rel_path] = full_path
                    self.file_list.addItem(rel_path)
                elif lower.endswith(".gis"):
                    self.gis_paths[rel_path] = full_path
                    self.gis_list.addItem(rel_path)

        mesh_count = len(self.mesh_paths)
        gis_count = len(self.gis_paths)
        self.statusbar.showMessage(
            "{0} mesh(es) e {1} gis encontrado(s)".format(mesh_count, gis_count)
        )
        self.asset_tabs.setCurrentIndex(0)

    def _on_file_selected(self, current, previous):
        if current is None:
            return

        name = current.text()
        path = self.mesh_paths.get(name)
        if not path:
            return

        self.statusbar.showMessage("Carregando {0}...".format(name))
        try:
            from core.parser import parse_mesh

            dto = parse_mesh(path)
            self.current_dto = dto
            self.current_path = path
            self._update_view_stats()
            self.viewer.load_mesh(dto)
            self.statusbar.showMessage(f"Carregado: {path}")

            # --- ANCORAR MOTOR RUNTIME ---
            gis_path = path.replace(".mesh", ".gis")
            import os

            if os.path.exists(gis_path):
                self._bind_runtime(gis_path)
            else:
                self._limpar_timeline()

        except NeoXError as e:
            _show_neox_error(self, "Erro ao carregar mesh", e)
        except Exception as e:
            import traceback

            err_str = traceback.format_exc()
            QMessageBox.critical(
                self, "Erro inesperado", f"Erro interno não tratado:\n{err_str}"
            )

    def _on_gis_selected(self, current, previous):
        if current is None:
            return
        if not self.current_dto:
            self.statusbar.showMessage(
                "Selecione um .mesh primeiro para aplicar o .gis"
            )
            return

        name = current.text()
        path = self.gis_paths.get(name)
        if not path:
            return

        self.statusbar.showMessage("Aplicando animação {0}...".format(name))
        self._bind_runtime(path)

    def _try_load_rgis(self, asset_dir: str) -> None:
        """
        Tenta carregar common.gis ou dongzuoku.gis a partir da pasta de assets.
        Popula self.rgis_session UMA VEZ — não recarrega se já carregado da mesma pasta.

        Candidatos em ordem de preferência:
          1. common.gis      (subconjunto compartilhado do personagem)
          2. dongzuoku.gis   (manifesto global do jogo inteiro)
        """
        import os
        from core.rgis_parser import is_rgis, parse_rgis

        # Não recarregar se a sessão já veio dessa pasta
        if self.rgis_session is not None:
            if os.path.dirname(self.rgis_session.source_path) == asset_dir:
                return

        candidates = ["common.gis", "dongzuoku.gis"]
        for name in candidates:
            candidate = os.path.join(asset_dir, name)
            if os.path.isfile(candidate) and is_rgis(candidate):
                try:
                    self.rgis_session = parse_rgis(candidate)
                    self.statusbar.showMessage(
                        "RGIS carregado: {0}  ({1} bones, {2} clipes)".format(
                            name,
                            self.rgis_session.bone_count,
                            self.rgis_session.anim_count,
                        )
                    )
                    return
                except Exception as e:
                    import logging

                    logging.getLogger("app").warning(
                        "Falha ao carregar RGIS %s: %s", candidate, e
                    )

    def _bind_runtime(self, gis_path):
        import os

        try:
            from core.anim_bridge import load_and_align_animation
            from runtime.evaluation.evaluator import BaseEvaluator
            from runtime.animation.skinning import build_bone_mapping
            from runtime.animation.sequence import AnimSequenceWrapper

            # Tentar carregar RGIS da mesma pasta (no-op se já carregado)
            self._try_load_rgis(os.path.dirname(gis_path))

            anim_dto = load_and_align_animation(gis_path, rgis_dto=self.rgis_session)
            self.anim_sequence = AnimSequenceWrapper(anim_dto)

            # CRIAR O MAPA DE BONES (Match agressivo uma única vez)
            self.bone_mapping = build_bone_mapping(
                self.current_dto.skeleton.bones, anim_dto.bone_tracks
            )

            self.evaluator = BaseEvaluator({})

            frames = int(self.anim_sequence.duration * self.anim_sequence.fps)
            self.total_frames = min(100000, max(0, frames))
            self.slider.setMaximum(self.total_frames)
            self.slider.setValue(0)
            self.btn_play.setEnabled(True)
            self.statusbar.showMessage(
                f"Animação Ativada: {os.path.basename(gis_path)}"
            )
        except NeoXError as e:
            _show_neox_error(self, "Erro ao carregar animação GIS", e)
            self._limpar_timeline()
        except Exception as ex:
            import traceback

            print("[Engine] Erro ao carregar animação:", traceback.format_exc())
            QMessageBox.critical(self, "Erro GIS", traceback.format_exc())
            self._limpar_timeline()

    def _limpar_timeline(self):
        self.evaluator = None
        self.total_frames = 0
        if hasattr(self, "slider"):
            self.slider.setMaximum(0)
            self.slider.setValue(0)
            self.btn_play.setChecked(False)

    def _on_mesh_loaded(self, info):
        name = os.path.basename(self.current_path) if self.current_path else ""
        self._update_view_stats()
        self.statusbar.showMessage("{0} — {1}".format(name, info))

    def _update_view_stats(self):
        if not self.current_dto:
            self.viewport_stats_label.setText("Verts: - | Tris: -")
            self.viewport_stats_label.adjustSize()
            self.viewport_stats_label.raise_()
            return

        self.viewport_stats_label.setText(
            "Verts: {0:,} | Tris: {1:,}".format(
                len(self.current_dto.positions), len(self.current_dto.faces)
            )
        )
        self.viewport_stats_label.adjustSize()
        self.viewport_stats_label.raise_()

    def _on_action_open_gis(self):
        """Ação de Menu: Abrir animação manualmente."""
        if not self.current_dto:
            QMessageBox.warning(self, "Aviso", "Carregue uma malha (.mesh) primeiro!")
            return

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Animação",
            os.path.dirname(self.current_path) if self.current_path else "",
            "NeoX Animation (*.gis)",
        )
        if path:
            self._bind_runtime(path)

    def _on_action_parse_gim(self):
        """Abre e analisa um manifesto .gim (GIM Analyzer)."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Analisar Manifesto GIM",
            self.folder_path or os.path.expanduser("~"),
            "NeoX Asset Manifest (*.gim);;All Files (*)",
        )
        if not path:
            return

        try:
            dto = parse_gim(path)
            dlg = GimDetailDialog(dto, self)
            dlg.exec_()
        except Exception as e:
            _show_neox_error(self, "Erro ao analisar GIM", e)

    def _on_action_parse_mtg(self):
        """Abre e analisa um material .mtg (BXML-Analyzer)."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Analisar Material NeoX",
            self.folder_path or os.path.expanduser("~"),
            "NeoX Material (*.mtg);;All Files (*)",
        )
        if not path:
            return

        try:
            dto = parse_mtg(path)
            dlg = MtgDetailDialog(dto, self)
            dlg.exec_()
        except Exception as e:
            _show_neox_error(self, "Erro ao analisar Material", e)

    def _export_fbx(self):
        if not self.current_path:
            QMessageBox.warning(self, "Aviso", "Nenhum mesh carregado para exportar.")
            return

        default_name = os.path.splitext(os.path.basename(self.current_path))[0] + ".fbx"
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar FBX", default_name, "FBX Files (*.fbx)"
        )
        if not path:
            return

        self.statusbar.showMessage("Exportando FBX via Blender...")
        QApplication.processEvents()

        ok, err = self.blender.export_fbx(self.current_path, path)
        if ok:
            self.statusbar.showMessage("Exportado: {0}".format(os.path.basename(path)))
        else:
            QMessageBox.critical(
                self, "Erro na exportação", "Blender retornou erro:\n{0}".format(err)
            )

    def _export_merge_fbx(self):
        """
        Exporta todos os arquivos .mesh selecionados como um único FBX mesclado.
        """
        selected = self.file_list.selectedItems()
        if len(selected) < 2:
            QMessageBox.warning(
                self,
                "Seleção insuficiente",
                "Selecione 2 ou mais arquivos .mesh para o merge.\n"
                "Use Ctrl+Click ou Shift+Click para selecionar múltiplos.",
            )
            return

        mesh_paths = [
            self.mesh_paths[item.text()]
            for item in selected
            if item.text() in self.mesh_paths
        ]
        if not mesh_paths:
            return

        default_name = (os.path.basename(self.folder_path) or "merge") + "_merge.fbx"
        out_path, _ = QFileDialog.getSaveFileName(
            self, "Salvar FBX mesclado", default_name, "FBX Files (*.fbx)"
        )
        if not out_path:
            return

        gis_path = self.blender.detect_gis(self.folder_path)
        self.statusbar.showMessage(
            "Exportando merge ({0} arquivos)...".format(len(mesh_paths))
        )
        QApplication.processEvents()

        ok, err = self.blender.export_merge_fbx(mesh_paths, out_path, gis_path)
        if ok:
            gis_info = " + GIS detectado" if gis_path else ""
            self.statusbar.showMessage(
                "Merge exportado: {0}{1}".format(os.path.basename(out_path), gis_info)
            )
        else:
            QMessageBox.critical(
                self,
                "Erro na exportação merge",
                "Blender retornou erro:\n{0}".format(err),
            )


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
