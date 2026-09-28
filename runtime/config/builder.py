# -*- coding: utf-8 -*-
"""
runtime/config/builder.py
O "Factory" (Fábrica) do Grafo.
Converte os manifestos decodificados (JSON/XML) em instâncias vivas de RuntimeGraph.
"""
import logging
from runtime.graph.runtime_graph import RuntimeGraph
from runtime.graph.connections import GraphConnections
from runtime.graph.dirty_tracker import DirtyTracker
from runtime.graph.node import ComputeTask

logger = logging.getLogger("Runtime.Config.GraphBuilder")

class GraphBuilder(object):
    """
    Construtor que traduz o dicionário Blueprint em objetos Python reais interligados.
    """

    @staticmethod
    def build_from_json(blueprint_dict, task_registry):
        """
        Monta um RuntimeGraph a partir do dicionário gerado pelo JSONParser.
        
        Args:
            blueprint_dict (dict): Dicionário contendo 'plugs' e 'tasks'.
            task_registry (dict): Mapeamento de 'TaskName' -> Callback Python (func)
                                Registrado pelo usuário/sistema de plugins para não ter hardcoding.
                                Ex: {'MultiplyMatrix': my_matmul_func}
                                
        Returns:
            RuntimeGraph: O Grafo montado pronto para avaliação (Lazy Pull).
        """
        logger.info("[GraphBuilder] Iniciando montagem do Grafo de Execução...")
        
        # 1. Instanciar núcleo desacoplado
        connections = GraphConnections()
        dirty_tracker = DirtyTracker(connections, {}) # Nós vazios por enquanto
        engine = RuntimeGraph(connections, dirty_tracker)
        
        # Sincroniza a referência circular do Dictionary de Nodes forma segura
        dirty_tracker.nodes = engine.nodes 
        
        # 2. Registrar Plugs 
        # Num contexto real os Plugs ditam os buffers do DataStorage. Guardamos como metadados por enquanto.
        registered_plugs = blueprint_dict.get('plugs', [])
        logger.debug("[GraphBuilder] Recebidos %d Plugs globais do manifesto.", len(registered_plugs))
        
        # 3. Instanciar Nodes (Tarefas do usuário)
        tasks_data = blueprint_dict.get('tasks', [])
        built_tasks = 0
        
        for t_info in tasks_data:
            t_id = t_info.get('id')
            t_name = t_info.get('name')
            inputs = t_info.get('inputs', [])
            outputs = t_info.get('outputs', [])
            
            # Buscar a função de matemática/ação associada a este Nome predefinido no registro
            execute_func = task_registry.get(t_name)
            
            if not execute_func:
                logger.error("[GraphBuilder] Função de injeção INEXISTENTE para a Task '%s'. Callback abortado.", t_name)
                continue
                
            # Materializa o ComputeTask
            compute_task = ComputeTask(t_id, t_name, execute_func)
            compute_task.outputs = outputs
            
            # Submete a tarefa à engine, populando as LUT_Connections (afeta / é afetado)
            engine.add_task(compute_task, inputs)
            built_tasks += 1

        logger.info("[GraphBuilder] Grafo montado com SUCESSO. Embutidas %d ComputeTasks ativas.", built_tasks)
        return engine
