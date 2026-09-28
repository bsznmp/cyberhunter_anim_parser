# -*- coding: utf-8 -*-
"""Camera orbital para o viewport 3D."""
import math
import numpy as np
import pyrr


class Camera(object):
    def __init__(self):
        # Orbital parameters
        self.azimuth = 45.0       # graus (rotação horizontal)
        self.elevation = 30.0     # graus (rotação vertical)
        self.distance = 5.0       # distância do alvo
        self.target = np.array([0.0, 0.0, 1.0], dtype='f4')  # ponto de interesse

        # Projection
        self.fov = 45.0
        self.aspect = 1.0
        self.near = 0.01
        self.far = 1000.0

        # Sensibilidade
        self.orbit_speed = 0.3
        self.pan_speed = 0.005
        self.zoom_speed = 2.0  # Aumentado para escalas em centimetros

    def orbit(self, dx, dy):
        """Rotaciona a câmera ao redor do alvo."""
        self.azimuth += dx * self.orbit_speed
        self.elevation = max(-89.0, min(89.0, self.elevation - dy * self.orbit_speed))

    def pan(self, dx, dy):
        """Move o alvo (e a câmera) lateralmente."""
        right = self._right_vector()
        up = np.array([0.0, 0.0, 1.0], dtype='f4')
        self.target += right * (-dx * self.pan_speed * self.distance)
        self.target += up * (dy * self.pan_speed * self.distance)

    def zoom(self, delta):
        """Aproxima ou afasta a câmera."""
        self.distance = max(0.1, self.distance - delta * self.zoom_speed)

    def fit_to_mesh(self, positions):
        """Centraliza a câmera no mesh carregado."""
        if positions is None or len(positions) == 0:
            return
        arr = np.array(positions, dtype='f4')
        center = arr.mean(axis=0)
        extents = arr.max(axis=0) - arr.min(axis=0)
        size = max(extents)
        self.target = center
        self.distance = size * 1.5
        self.elevation = 30.0
        self.azimuth = 45.0

    def eye_position(self):
        """Posição da câmera no mundo."""
        az = math.radians(self.azimuth)
        el = math.radians(self.elevation)
        x = self.target[0] + self.distance * math.cos(el) * math.sin(az)
        y = self.target[1] + self.distance * math.cos(el) * math.cos(az)
        z = self.target[2] + self.distance * math.sin(el)
        return np.array([x, y, z], dtype='f4')

    def view_matrix(self):
        """Matriz view (lookAt)."""
        eye = self.eye_position()
        return pyrr.matrix44.create_look_at(
            eye, self.target, np.array([0.0, 0.0, 1.0], dtype='f4'),
            dtype='f4'
        )

    def projection_matrix(self):
        """Matriz projection (perspectiva)."""
        return pyrr.matrix44.create_perspective_projection(
            self.fov, self.aspect, self.near, self.far, dtype='f4'
        )

    def mvp(self, model=None):
        """Retorna a matriz MVP combinada."""
        if model is None:
            model = pyrr.matrix44.create_identity(dtype='f4')
        view = self.view_matrix()
        proj = self.projection_matrix()
        return pyrr.matrix44.multiply(pyrr.matrix44.multiply(model, view), proj)

    def normal_matrix(self, model=None):
        """Matriz 3x3 para transformar normais."""
        if model is None:
            model = pyrr.matrix44.create_identity(dtype='f4')
        view = self.view_matrix()
        mv = pyrr.matrix44.multiply(model, view)
        return np.linalg.inv(mv[:3, :3]).T

    def _right_vector(self):
        az = math.radians(self.azimuth)
        return np.array([math.cos(az), -math.sin(az), 0.0], dtype='f4')
