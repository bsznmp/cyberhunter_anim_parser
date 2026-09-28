# -*- coding: utf-8 -*-
"""
runtime/graph/dirty_tracker.py
Propaga iterativamente o estado 'sujo' (dirty) pelo grafo de nós.
"""
import logging

logger = logging.getLogger("Runtime.Graph.DirtyTracker")

class DirtyTracker(object):
    """
    Motor de Propagação Preguiçosa (Lazy).
    Inspeciona quem foi afetado por uma mudança e suja em cascata (Avaliação Topológica).
    """
    __slots__ = ['connections', 'nodes']

    def __init__(self, connections, nodes_dict):
        """
        Args:
            connections (GraphConnections): As LUTs de relação do grafo.
            nodes_dict (dict): Dicionário com os nós registrados {task_id: ComputeTask}.
        """
        self.connections = connections
        self.nodes = nodes_dict

    def propagate_dirty(self, input_id):
        """
        Ao alterar um Data_ID (ex: Mudança na Animação/Tempo), varre em profundidade
        os nós filhos e as dependências indiretas, sinalizando flag `dirty=True`.
        """
        affected_tasks = self.connections.get_tasks_affected_by(input_id)
        if not affected_tasks:
            logger.debug("[DirtyTracker] Ninguém depende do Input ID:%d. Cancelando propagação.", input_id)
            return

        logger.debug("[DirtyTracker] Input ID:%d mudou... Iniciando propagação em cascata.", input_id)
        
        # Pilha para DFS (Busca em Profundidade) sem recursão p/ evitar limite local
        stack = list(affected_tasks)
        visited = set()

        while stack:
            current_task_id = stack.pop()
            
            if current_task_id in visited:
                continue
            visited.add(current_task_id)

            task = self.nodes.get(current_task_id)
            if not task:
                continue

            was_dirty = task.dirty
            task.mark_dirty()

            # Otimização crucial: Só propaga se o nó AINDA NÃO estava sujo.
            # Se já estava sujo, os filhos dele já estarão sujos por tabela.
            if not was_dirty:
                # O que esse nó produz afeta outros nós? Se sim, empilha os afetados
                for out_id in task.outputs:
                    child_tasks = self.connections.get_tasks_affected_by(out_id)
                    for c_task_id in child_tasks:
                        if c_task_id not in visited:
                            stack.append(c_task_id)

        logger.info("[DirtyTracker] Cascata de 'Dirty' concluída! Input %d contaminou %d nós: %s", 
                    input_id, len(visited), list(visited))
