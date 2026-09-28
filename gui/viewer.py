# -*- coding: utf-8 -*-
"""Viewport 3D com ModernGL integrado ao PyQt5."""

import os
import struct
import numpy as np
import moderngl

from PyQt5 import QtOpenGL, QtCore
from PyQt5.QtCore import Qt

from gui.camera import Camera


SHADER_DIR = os.path.join(os.path.dirname(__file__), "shaders")


def _load_shader(name):
    path = os.path.join(SHADER_DIR, name)
    with open(path, "r") as f:
        return f.read()


class ViewerWidget(QtOpenGL.QGLWidget):
    """Widget OpenGL 3D com câmera orbital e iluminação."""

    mesh_loaded = QtCore.pyqtSignal(str)  # sinal com info do mesh

    def __init__(self, parent=None):
        fmt = QtOpenGL.QGLFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QtOpenGL.QGLFormat.CoreProfile)
        fmt.setSamples(4)
        super(ViewerWidget, self).__init__(fmt, parent)

        self.camera = Camera()
        self.ctx = None
        self.mesh_prog = None
        self.grid_prog = None
        self.arm_prog = None
        self.mesh_vao = None
        self.grid_vao = None
        self.arm_vao = None
        self.axis_vao = None
        self.face_count = 0
        self.vertex_count = 0
        self._vbo = None
        self._ibo = None
        self._aux_vbo = None
        self._arm_vbo = None

        # View mode flags
        self._wireframe = False
        self._show_grid = True
        self._show_axes = True
        self._submesh_debug = False
        self._show_weights = False
        self._show_armature = False

        # Mouse state
        self._last_pos = None
        self._mouse_btn = None

        self.setMinimumSize(400, 300)
        self.setFocusPolicy(Qt.StrongFocus)

    def initializeGL(self):
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.CULL_FACE)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

        # Compilar shaders — grid primeiro para não depender do arm_prog
        self.mesh_prog = self.ctx.program(
            vertex_shader=_load_shader("mesh.vert"),
            fragment_shader=_load_shader("mesh.frag"),
        )
        self.grid_prog = self.ctx.program(
            vertex_shader=_load_shader("grid.vert"),
            fragment_shader=_load_shader("grid.frag"),
        )
        self._build_grid()

        try:
            self.arm_prog = self.ctx.program(
                vertex_shader=_load_shader("arm.vert"),
                fragment_shader=_load_shader("arm.frag"),
            )
            self._build_axes()
        except Exception as e:
            import traceback

            print("[viewer] arm_prog falhou:", e)
            traceback.print_exc()

    def resizeGL(self, w, h):
        self.ctx.viewport = (0, 0, w, h)
        self.camera.aspect = w / max(h, 1)

    def paintGL(self):
        self.ctx.clear(0.18, 0.18, 0.22, 1.0)

        if self._wireframe:
            self.ctx.wireframe = True
            self.ctx.disable(moderngl.CULL_FACE)
        else:
            self.ctx.wireframe = False
            self.ctx.enable(moderngl.CULL_FACE)

        mvp = self.camera.mvp()
        norm_mat = self.camera.normal_matrix()

        # Grid
        if self.grid_vao and self._show_grid:
            self.grid_prog["mvp"].write(mvp.tobytes())
            self.grid_vao.render(moderngl.LINES)

        # Mesh
        if self.mesh_vao and self.face_count > 0:
            mode = 1 if self._submesh_debug else (2 if self._show_weights else 0)
            self.mesh_prog["mvp"].write(mvp.tobytes())
            self.mesh_prog["normal_matrix"].write(norm_mat.astype("f4").tobytes())
            self.mesh_prog["u_mode"].value = mode
            self.mesh_vao.render(moderngl.TRIANGLES)

        # Eixos e Armature — sempre solid
        self.ctx.wireframe = False
        self.ctx.enable(moderngl.CULL_FACE)

        if self.arm_prog and self.axis_vao and self._show_axes:
            self.arm_prog["mvp"].write(mvp.tobytes())
            self.arm_prog["u_color"].value = (0.9, 0.25, 0.25)
            self.axis_vao.render(moderngl.LINES, vertices=2, first=0)
            self.arm_prog["u_color"].value = (0.25, 0.9, 0.25)
            self.axis_vao.render(moderngl.LINES, vertices=2, first=2)
            self.arm_prog["u_color"].value = (0.25, 0.5, 0.9)
            self.axis_vao.render(moderngl.LINES, vertices=2, first=4)

        if self.arm_prog and self.arm_vao and self._show_armature:
            self.arm_prog["mvp"].write(mvp.tobytes())
            self.arm_prog["u_color"].value = (1.0, 0.6, 0.1)
            self.arm_vao.render(moderngl.LINES)

    # ------ Mesh Loading ------

    def load_mesh(self, dto):
        """Carrega um MeshDTO no viewport."""
        self.release_mesh()

        if len(dto.positions) == 0 or len(dto.faces) == 0:
            return

        # NeoX Y-Up → Viewer Z-Up: (-x, z, y) — mesmo transform do Blender exporter
        pos = np.array(dto.positions, dtype="f4")
        pos_gl = np.column_stack([-pos[:, 0], pos[:, 2], pos[:, 1]])

        has_normals = len(dto.normals) == len(dto.positions)
        if has_normals:
            norm = np.array(dto.normals, dtype="f4")
            norm_gl = np.column_stack([-norm[:, 0], norm[:, 2], norm[:, 1]])
        else:
            norm_gl = np.zeros((len(dto.positions), 3), dtype="f4")
            norm_gl[:, 2] = 1.0

        self._current_normals_gl = norm_gl
        self._vbo = self.ctx.buffer(np.hstack([pos_gl, norm_gl]).astype("f4").tobytes())
        self._ibo = self.ctx.buffer(np.array(dto.faces, dtype="u4").flatten().tobytes())

        # VBO auxiliar: submesh index + max weight por vértice
        n_sub = max(len(dto.submeshes) - 1, 1)
        sub_vals = []
        for i, sub in enumerate(dto.submeshes):
            sub_vals.extend([i / n_sub] * sub.vertex_count)
        sub_arr = np.array(sub_vals[: len(dto.positions)], dtype="f4")

        if dto.joint_weights:
            w_arr = np.array([max(row) for row in dto.joint_weights], dtype="f4")
        else:
            w_arr = np.zeros(len(dto.positions), dtype="f4")

        self._aux_vbo = self.ctx.buffer(
            np.column_stack([sub_arr, w_arr]).astype("f4").tobytes()
        )

        self.mesh_vao = self.ctx.vertex_array(
            self.mesh_prog,
            [
                (self._vbo, "3f 3f", "in_position", "in_normal"),
                (self._aux_vbo, "1f 1f", "in_submesh", "in_weight"),
            ],
            index_buffer=self._ibo,
            index_element_size=4,
        )
        self.vertex_count = len(dto.positions)
        self.face_count = len(dto.faces)

        # Armature VAO (linhas pai→filho)
        if dto.has_skeleton:
            skel = dto.skeleton
            bone_pos = {}
            for bd in skel.bones:
                m = bd.bind_matrix
                bone_pos[bd.index] = (-m[3][0], m[3][2], m[3][1])
            arm_lines = []
            for bd in skel.bones:
                if bd.parent_index >= 0 and bd.parent_index in bone_pos:
                    arm_lines.extend(bone_pos[bd.index])
                    arm_lines.extend(bone_pos[bd.parent_index])
            if arm_lines:
                self._arm_vbo = self.ctx.buffer(
                    np.array(arm_lines, dtype="f4").tobytes()
                )
                self.arm_vao = self.ctx.vertex_array(
                    self.arm_prog,
                    [(self._arm_vbo, "3f", "in_position")],
                )

        # Auto-fit câmera
        self.camera.fit_to_mesh(pos_gl)

        info = "{0} verts | {1} faces".format(len(dto.positions), len(dto.faces))
        if dto.has_skeleton:
            info += " | {0} bones".format(dto.skeleton.bone_count)
        self.mesh_loaded.emit(info)

        self.update()

    def update_frame(self, pos_final_3d):
        """Atualiza dinamicamente as posições da malha mantendo buffer vivo."""
        if not self._vbo or pos_final_3d is None:
            return

        # Ajuste de eixos NeoX -> Tela (Z-Up) igual do load_mesh
        pos = np.array(pos_final_3d, dtype="f4")
        pos_gl = np.column_stack([-pos[:, 0], pos[:, 2], pos[:, 1]])

        # Entrelaça os novos vértices com as normais originais retidas na RAM
        vbo_bytes = np.hstack([pos_gl, self._current_normals_gl]).astype("f4").tobytes()
        self._vbo.write(vbo_bytes)

        self.update()

    def release_mesh(self):
        for attr in ("mesh_vao", "arm_vao"):
            obj = getattr(self, attr)
            if obj:
                obj.release()
                setattr(self, attr, None)
        for attr in ("_vbo", "_ibo", "_aux_vbo", "_arm_vbo"):
            obj = getattr(self, attr)
            if obj:
                obj.release()
                setattr(self, attr, None)
        self.face_count = 0
        self.vertex_count = 0

    # ------ View mode toggles ------

    def set_wireframe(self, enabled):
        self._wireframe = enabled
        self.update()

    def set_show_grid(self, enabled):
        self._show_grid = enabled
        self.update()

    def set_submesh_debug(self, enabled):
        self._submesh_debug = enabled
        if enabled:
            self._show_weights = False
        self.update()

    def set_show_weights(self, enabled):
        self._show_weights = enabled
        if enabled:
            self._submesh_debug = False
        self.update()

    def set_show_armature(self, enabled):
        self._show_armature = enabled
        self.update()

    def set_show_axes(self, enabled):
        self._show_axes = enabled
        self.update()

    # ------ Grid ------

    def _build_grid(self):
        lines = []
        grid_size = 500
        step = 50.0
        for i in range(-grid_size, grid_size + 1):
            v = i * step
            lines.extend([v, -grid_size * step, 0.0])
            lines.extend([v, grid_size * step, 0.0])
            lines.extend([-grid_size * step, v, 0.0])
            lines.extend([grid_size * step, v, 0.0])

        vbo = self.ctx.buffer(np.array(lines, dtype="f4").tobytes())
        self.grid_vao = self.ctx.vertex_array(
            self.grid_prog,
            [(vbo, "3f", "in_position")],
        )

    def _build_axes(self):
        axis_len = 150.0  # comprimento visível por eixo
        data = np.array(
            [
                0.0,
                0.0,
                0.0,
                axis_len,
                0.0,
                0.0,  # X
                0.0,
                0.0,
                0.0,
                0.0,
                axis_len,
                0.0,  # Y (cima)
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                axis_len,  # Z
            ],
            dtype="f4",
        )
        vbo = self.ctx.buffer(data.tobytes())
        self.axis_vao = self.ctx.vertex_array(
            self.arm_prog,
            [(vbo, "3f", "in_position")],
        )

    # ------ Mouse Events ------

    def mousePressEvent(self, event):
        self._last_pos = event.pos()
        self._mouse_btn = event.button()

    def mouseReleaseEvent(self, event):
        self._last_pos = None
        self._mouse_btn = None

    def mouseMoveEvent(self, event):
        if self._last_pos is None:
            return

        dx = event.x() - self._last_pos.x()
        dy = event.y() - self._last_pos.y()
        self._last_pos = event.pos()

        if self._mouse_btn == Qt.LeftButton:
            self.camera.orbit(dx, dy)
        elif self._mouse_btn == Qt.MiddleButton:
            self.camera.pan(dx, dy)
        elif self._mouse_btn == Qt.RightButton:
            self.camera.zoom(dy * 0.02)

        self.update()

    def wheelEvent(self, event):
        delta = event.angleDelta().y() / 120.0
        self.camera.zoom(delta)
        self.update()

    # ------ Keyboard ------

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_1:  # Front
            self.camera.azimuth = 0
            self.camera.elevation = 0
        elif key == Qt.Key_3:  # Right
            self.camera.azimuth = 90
            self.camera.elevation = 0
        elif key == Qt.Key_7:  # Top
            self.camera.azimuth = 0
            self.camera.elevation = 89
        elif key == Qt.Key_5:  # Reset
            self.camera.azimuth = 45
            self.camera.elevation = 25
        self.update()
