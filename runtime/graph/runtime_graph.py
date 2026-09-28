# -*- coding: utf-8 -*-
"""
runtime/graph/runtime_graph.py
O orquestrador principal do grafo de dependências.
Unifica Nodes, Connections e o DirtyTracker num motor de avaliação (Pull-Based).
"""
import logging

logger = logging.getLogger("Runtime.Graph.Engine")

class RuntimeGraph(object):
    """
    Equivalente ao nemo::Runtime (Motor Central).
    Permite sujar inputs (push dirty) e extrair outputs (pull evaluate).
    """
    __slots__ = ['nodes', 'connections', 'dirty_tracker', '_task_inputs']

    def __init__(self, connections_instance, dirty_tracker_instance):
        self.nodes = {}                 # dict[int: ComputeTask]
        # Injeção das dependências centrais para manter o design Desacoplado:
        self.connections = connections_instance
        self.dirty_tracker = dirty_tracker_instance
        
        # Necessário para backtracing durante a avaliação Pull-Based
        self._task_inputs = {}          # dict[int: list[int]] mapeia task_id -> inputs 

    def add_task(self, task, inputs):
        """
        Registra uma tarefa no motor e a mapeia na topologia estrutural.
        """
        self.nodes[task.task_id] = task
        self._task_inputs[task.task_id] = inputs
        self.connections.add_dependency(task.task_id, inputs, task.outputs)
        logger.debug("[RuntimeGraph] Task adicionada: %s (ID:%d)", task.name, task.task_id)

    def dirty_input(self, input_id):
        """
        Informa ao motor que um dado fundancional mudou (ex: frame do Blender mudou).
        O motor propaga a sujeira em cascata.
        """
        logger.debug("[RuntimeGraph] Recebido flag DIRTY para o Input ID:%d", input_id)
        self.dirty_tracker.propagate_dirty(input_id)

    def evaluate(self, output_id, ctx_in, ctx_out):
        """
        Avaliação preguiçosa puxada por demanda (Lazy Pull).
        Pede o valor de um output e recalcula estritamente a árvore suja anterior a ele.
        """
        logger.info("[RuntimeGraph] Solicitada avaliação do Output ID:%d", output_id)
        
        producers = self.connections.get_tasks_affecting(output_id)
        if not producers:
            logger.debug("[RuntimeGraph] Nenhum nó produz o Output ID:%d. Entregando o que está no cache.", output_id)
            return

        visited = set()
        
        def _pull_evaluate(task_id):
            """DFS Recursivo retrocedendo a árvore para garantir topologia."""
            if task_id in visited:
                return
            visited.add(task_id)

            task = self.nodes.get(task_id)
            if not task or not task.dirty:
                return  # Pulado: já está atualizado (Limpo) ou não existe

            # Antes de executar este nó, exigimos que seus PAIS (inputs) estejam atualizados!
            for in_id in self._task_inputs.get(task_id, []):
                upstream_producers = self.connections.get_tasks_affecting(in_id)
                for producer_id in upstream_producers:
                    _pull_evaluate(producer_id)

            # Só agora, com pais calculados e limpos, executamos este nível da árvore
            task.execute(ctx_in, ctx_out)

        # Disparar a demanda "puxando" as origens dos nós criadores desse output 
        for prod_id in producers:
            _pull_evaluate(prod_id)
