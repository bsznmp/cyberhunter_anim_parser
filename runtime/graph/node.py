# -*- coding: utf-8 -*-
"""
runtime/graph/node.py
Define um nó isolado na topologia de execução.
"""
import logging

logger = logging.getLogger("Runtime.Graph.Node")

class ComputeTask(object):
    """
    Unidade atômica de execução no grafo.
    Equivalente a nemo::ComputeTask do C++.
    """
    __slots__ = ['task_id', 'name', 'dirty', 'outputs', '_execute_func']

    def __init__(self, task_id, name, execute_func):
        self.task_id = task_id          # int: identificador único
        self.name = name                # str: nome descritivo (para debug)
        self.dirty = True               # bool: começa sujo requerendo inicialização
        self.outputs = []               # list[int]: IDs das saídas geradas por esta task
        self._execute_func = execute_func # callable(inputs, outputs)

    def execute(self, ctx_in, ctx_out):
        """
        Executa a tarefa se ela estiver suja.
        """
        if not self.dirty:
            logger.debug("[ComputeTask] Task '%s' (ID:%d) PULADA (cached).", self.name, self.task_id)
            return False

        logger.debug("[ComputeTask] EXECUTANDO Task '%s' (ID:%d)...", self.name, self.task_id)
        
        try:
            # A função de execução fará a mutação no contexto através do ponteiro
            self._execute_func(ctx_in, ctx_out)
            logger.info("[ComputeTask] SUCESSO na Task '%s' (ID:%d). Outputs atualizados: %s", self.name, self.task_id, self.outputs)
            
            self.dirty = False
            return True
            
        except Exception as e:
            logger.error("[ComputeTask] FALHA ao executar Task '%s' (ID:%d): %s", self.name, self.task_id, str(e))
            raise

    def mark_dirty(self):
        """Sinaliza que os inputs desta task mudaram."""
        if not self.dirty:
            logger.debug("[ComputeTask] Task '%s' (ID:%d) marcada como DIRTY.", self.name, self.task_id)
            self.dirty = True
