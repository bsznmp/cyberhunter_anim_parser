# -*- coding: utf-8 -*-
"""
runtime/evaluation/evaluator.py
A Fachada Principal (Facade API) do Runtime.
Atua como a "API Pública" do nosso motor interligando Grafo, Memória e Assets.
"""
import logging
from runtime.evaluation.data_storage import DataStorage
from runtime.evaluation.resource_pool import ResourcePool
from runtime.config.parsers.json_parser import NemoJSONDecoder
from runtime.config.builder import GraphBuilder

logger = logging.getLogger("Runtime.Eval.Evaluator")

class BaseEvaluator(object):
    """
    O Orquestrador Máximo.
    É isso que o 'app.py' (GUI) ou 'main.py' (CLI exporter) vai instanciar para animar malhas.
    Equivalente exato ao nemo::Evaluator.
    """
    __slots__ = ['engine', 'storage', 'pool', 'config_plugs', '_task_registry']

    def __init__(self, task_registry_callbacks):
        """
        Args:
            task_registry_callbacks (dict): Dicionário de injeção de dependência mapeando as funções reais.
        """
        self.storage = DataStorage()
        self.pool = ResourcePool()
        self.engine = None
        self.config_plugs = []
        self._task_registry = task_registry_callbacks
        
    def load_blueprint(self, json_filepath):
        """
        Lê um arquivo de manifesto JSON e constrói literalmente todo o Runtime State.
        """
        logger.info("[BaseEvaluator] Iniciando Bootstrapping via blueprint: %s", json_filepath)
        
        # 1. Parsear o Manifesto (Segregado p/ fácil manutenção)
        blueprint = NemoJSONDecoder.parse_file(json_filepath)
        self.config_plugs = blueprint.get('plugs', [])
        
        # 2. Requisitar as matrizes de Buffers no Storage Base (Zero Alloc)
        self.storage.init_from_plugs(self.config_plugs)
        
        # 3. Fábrica: Instancia o RuntimeGraph com todos os nós matemáticos
        self.engine = GraphBuilder.build_from_json(blueprint, self._task_registry)
        
        logger.info("[BaseEvaluator] Sistema Base Online e Armado.")

    def update_time(self, frame_time, time_plug_id=0):
        """
        Avança o tempo da engine. Injeta a 'Sujeira' (Dirty) estritamente
        na variável de Tempo do Grafo, engatilhando as cascatas de recálculo apenas 
        onde há mutação de animação.
        """
        logger.debug("[BaseEvaluator] ======== FRAME UPDATE: %f ========", frame_time)
        self.storage.set_value(time_plug_id, frame_time)
        # Empurra sujeira top-down
        self.engine.dirty_input(time_plug_id)

    def get_evaluated_output(self, output_id):
        """
        Extrai um resultado validado das garras do motor (Lazy Evaluation / Puxada bottom-up).
        Substitui o app.py sujo pelo app.py blindado.
        """
        # Exige do Graph a resolução pendente do output:
        self.engine.evaluate(output_id, ctx_in=self.storage, ctx_out=self.storage)
        
        # Recupera o dado mastigado
        return self.storage.get_value(output_id)
