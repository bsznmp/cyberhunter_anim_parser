# -*- coding: utf-8 -*-
"""
runtime/animation/channel.py
Motor de interpolação matemática para trilhas isoladas (Position, Rotation, Scale).
"""
import logging

logger = logging.getLogger("Runtime.Anim.Channel")

class AnimChannel(object):
    """
    Equivalente ao nemo::Channel.
    Acessa os keyframes de forma otimizada usando busca para interpolação segura.
    """
    __slots__ = ['bone_id', 'track_type', 'times', 'values']

    def __init__(self, bone_id, track_type, times, values):
        self.bone_id = bone_id          # ID ou path do joint alvo
        self.track_type = track_type    # 'P', 'R' (Quaternion), 'S'
        self.times = times              # list/array de floats (tempo real/frame)
        self.values = values            # list/array de vetores correspondentes

    def sample(self, time):
        """
        Retorna o valor interpolado matematicamente no tempo 'time'.
        Otimizado com busca binária (bisect) para alta performance.
        """
        if not self.times or not self.values:
            return None
            
        # Otimização 0: Trilha Estática ou Único Frame
        if len(self.values) == 1:
            return self.values[0]
            
        # Otimização 1: Out-of-bounds Head (Início)
        if time <= self.times[0]:
            return self.values[0]
            
        # Otimização 2: Out-of-bounds Tail (Fim)
        if time >= self.times[-1]:
            return self.values[-1]
            
        # Otimização 3: Busca Binária (O(log N))
        import bisect
        idx = bisect.bisect_right(self.times, time) - 1
        
        # Garantir índices válidos para interpolação
        i0 = max(0, min(idx, len(self.times) - 2))
        i1 = i0 + 1
        
        t0 = self.times[i0]
        t1 = self.times[i1]
        
        # Normalização do fator de interpolação [0.0, 1.0]
        ratio = (time - t0) / (t1 - t0)
        
        v0 = self.values[i0]
        v1 = self.values[i1]
        
        # Dispatch especializado por tipo de track
        if self.track_type == 'R':
            return self._interpolate_quat(v0, v1, ratio)
        return self._lerp_vector(v0, v1, ratio)

    def _lerp_vector(self, v0, v1, t):
        """Interpolação linear para Posição e Escala (Vec3)."""
        return [v0[i] + (v1[i] - v0[i]) * t for i in range(len(v0))]

    def _interpolate_quat(self, q0, q1, t):
        """
        NLerp (Normalized Linear Interpolation) para Quaternions.
        Mais rápido que Slerp e visualmente idêntico para deltas pequenos.
        """
        # 1. Dot product para garantir o caminho mais curto
        dot = sum(a * b for a, b in zip(q0, q1))
        
        # 2. Se dot < 0, os quaternions têm polaridade oposta (flip)
        q1_adj = q1 if dot >= 0.0 else [-x for x in q1]
        
        # 3. Lerp e Normalização
        res = [q0[i] + (q1_adj[i] - q0[i]) * t for i in range(4)]
        mag = (sum(x*x for x in res))**0.5
        if mag > 0.000001:
            return [x / mag for x in res]
        return q0
