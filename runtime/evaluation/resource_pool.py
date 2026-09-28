# -*- coding: utf-8 -*-
"""
runtime/evaluation/resource_pool.py
Sistema de Instância Compartilhada para cache extremo de assets pesados.
"""
import logging

logger = logging.getLogger("Runtime.Eval.Pool")

class ResourcePool(object):
    """
    O Cache central de geometrias brutas (FaceSets, Vertices) e SkinWeights.
    Sua filosofia é isolar a memória de vídeo/CPU para que 10 zumbis iguais re-usem 1 ativo só.
    Otimização estrita (MemCache Pool).
    """
    __slots__ = ['_meshes', '_animations']

    def __init__(self):
        # Hash keys: nome/paths
        self._meshes = {}
        self._animations = {}

    def get_or_load_mesh(self, mesh_name, mesh_dto_factory):
        """
        Garante que o DTO da malha (altamente pesado) só é parseado do binário uma Única vez,
        não importa quantos nós matemáticos peçam ele.
        
        Args:
            mesh_name: Nome rastreável universal.
            mesh_dto_factory (callable): Callback que lê o Binário e retorna o DTO se não existir em cache.
        """
        if mesh_name in self._meshes:
            logger.debug("[ResourcePool] Cache Hit! Servindo a malha '%s' direto da RAM.", mesh_name)
            return self._meshes[mesh_name]
            
        logger.info("[ResourcePool] Cache Miss. Compilando alocação zero-copy da malha '%s'...", mesh_name)
        new_mesh = mesh_dto_factory()
        self._meshes[mesh_name] = new_mesh
        return new_mesh
    
    def get_or_load_animation(self, anim_name, anim_dto_factory):
        """Semelhante aos meshes, reaproveita trilhas cruas GIM/GIS."""
        if anim_name in self._animations:
            return self._animations[anim_name]
            
        logger.info("[ResourcePool] Loading animação raiz '%s' para RAM...", anim_name)
        new_anim = anim_dto_factory()
        self._animations[anim_name] = new_anim
        return new_anim
