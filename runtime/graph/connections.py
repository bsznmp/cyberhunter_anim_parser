# -*- coding: utf-8 -*-
"""
runtime/graph/connections.py
Gerencia a topologia do grafo através de Look-Up Tables (LUTs).
Mapeia quais dados afetam quais nós e vice-versa.
"""
import logging

logger = logging.getLogger("Runtime.Graph.Connections")

class GraphConnections(object):
    """
    Mantém o registro centralizado das dependências do grafo.
    Equivalente as propriedades de LUT do nemo::Runtime.
    """
    __slots__ = ['lut_tasks_affected', 'lut_tasks_affecting']

    def __init__(self):
        # key: input_id -> list[int: task_id]
        # Quais tasks são afetadas se este input mudar?
        self.lut_tasks_affected = {}
        
        # key: output_id -> list[int: task_id]
        # Quais tasks geram este output?
        self.lut_tasks_affecting = {}

    def add_dependency(self, task_id, inputs, outputs):
        """
        Registra uma tarefa no tecido do grafo.
        
        Args:
            task_id (int): O ID da ComputeTask
            inputs (list[int]): IDs dos dados que esta tarefa consome
            outputs (list[int]): IDs dos dados que esta tarefa produz
        """
        # Registrar o que a tarefa consome
        for in_id in inputs:
            if in_id not in self.lut_tasks_affected:
                self.lut_tasks_affected[in_id] = []
            if task_id not in self.lut_tasks_affected[in_id]:
                self.lut_tasks_affected[in_id].append(task_id)

        # Registrar o que a tarefa produz
        for out_id in outputs:
            if out_id not in self.lut_tasks_affecting:
                self.lut_tasks_affecting[out_id] = []
            if task_id not in self.lut_tasks_affecting[out_id]:
                self.lut_tasks_affecting[out_id].append(task_id)

        logger.debug(
            "[GraphConnections] Task ID:%d vinculada. Inputs: %s | Outputs: %s", 
            task_id, inputs, outputs
        )

    def get_tasks_affected_by(self, input_id):
        """Retorna as tarefas que dependem diretamente deste input."""
        return self.lut_tasks_affected.get(input_id, [])

    def get_tasks_affecting(self, output_id):
        """Retorna as tarefas que são responsáveis por gerar este output."""
        return self.lut_tasks_affecting.get(output_id, [])
