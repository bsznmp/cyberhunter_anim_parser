# -*- coding: utf-8 -*-
"""
runtime/animation/sequence.py
Cápsula de alta velocidade para o banco de dados extraído dos binários .gis.
"""
import logging
from runtime.animation.channel import AnimChannel

logger = logging.getLogger("Runtime.Anim.Sequence")

class AnimSequenceWrapper(object):
    """
    Abraçadeira (Wrapper) para o AnimClipDTO puro da camada `core/`.
    Equivalente ao `nemo::Animation`.
    Quebra arquivos pesadíssimos em minúsculas raias de corrida (Channels) otimizados.
    """
    __slots__ = ['name', 'duration', 'fps', 'channels', 'dto']

    def __init__(self, anim_dto):
        """Converte o DTO Estático numa estrutura Viva matematicamente."""
        self.dto = anim_dto # Mantém referência para acesso às variantes
        self.name = getattr(anim_dto, 'name', "UnnamedAnim")
        self.fps = float(getattr(anim_dto, 'fps', 30.0))
        self.channels = []
        
        self._build_channels(anim_dto)
        
        # Cálculo de duração robusto: pega o maior tempo entre todas as tracks
        max_duration = 0.0
        if hasattr(anim_dto, 'bone_tracks') and anim_dto.bone_tracks:
            for track in anim_dto.bone_tracks:
                if hasattr(track, 'times') and track.times and len(track.times) > 0:
                    last_time = float(track.times[-1])
                    if last_time > max_duration:
                        max_duration = last_time
        
        self.duration = max_duration

    def _build_channels(self, anim_dto):
        """
        Vassoura o AnimClipDTO e cria Canais Matemáticos apenas onde existir Tracking.
        Isto limpa ossos nulos da RAM imediatamente.
        """
        if not hasattr(anim_dto, 'bone_tracks') or not anim_dto.bone_tracks:
            logger.warning("[AnimSequence] DTO '%s' não possui matriz de Tracks. Cancelando.", self.name)
            return
            
        count = 0
        for track in anim_dto.bone_tracks:
            b_name = track.bone_name
            
            has_t = hasattr(track, 'times') and track.times is not None and len(track.times) > 0
            if has_t:
                # Posição
                if hasattr(track, 'positions') and track.positions is not None and len(track.positions) > 0:
                    self.channels.append(AnimChannel(b_name, 'P', track.times, track.positions))
                    count += 1
                # Rotação
                if hasattr(track, 'rotations') and track.rotations is not None and len(track.rotations) > 0:
                    self.channels.append(AnimChannel(b_name, 'R', track.times, track.rotations))
                    count += 1
                # Escala
                if hasattr(track, 'scales') and track.scales is not None and len(track.scales) > 0:
                    self.channels.append(AnimChannel(b_name, 'S', track.times, track.scales))
                    count += 1
                
        logger.info("[AnimSequence] Compilação finalizada em '%s'. Ativadas %d pistas vetoriais exclusivas.", 
                    self.name, count)

    def sample_all_channels(self, current_time):
        """
        Fotografa um instante específico `time` e devolve os ângulos perfeitos de todos ou ossos.
        É este Dictionary que vai alimentar as Tasks Matemáticas via o DataStorage!
        """
        out_state = {}
        # Em larga escala, só recalcula os channels usando o próprio dirtyTracker
        for ch in self.channels:
            if ch.bone_id not in out_state:
                out_state[ch.bone_id] = {'P': None, 'R': None, 'S': None}
            out_state[ch.bone_id][ch.track_type] = ch.sample(current_time)
            
        return out_state
