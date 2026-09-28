# -*- coding: utf-8 -*-
"""
runtime/evaluation/data_storage.py
Armazena e gerencia os valores dinâmicos globais (Plugs) que circulam pelo grafo.
"""
import logging

logger = logging.getLogger("Runtime.Eval.Storage")

class DataStorage(object):
    """
    Equivalente as matrizes de memória estática do Nemo.
    As tarefas matemáticas injetam e consomem dados deste banco de estado universal.
    """
    __slots__ = ['_data_map']

    def __init__(self):
        # key: input_id/output_id -> variant value (float, matrix, array, object)
        self._data_map = {}

    def get_value(self, data_id, fallback=None):
        """Recupera o valor do plug e emite um possível warning se vazio."""
        if data_id not in self._data_map:
            logger.debug("[DataStorage] Aviso: Leitura do ID %d sem valor. Falta init? (Cache Miss)", data_id)
            return fallback
        return self._data_map.get(data_id)

    def set_value(self, data_id, value):
        """Salva a mutação de valor e o persiste na tabela hash central."""
        self._data_map[data_id] = value
        logger.debug("[DataStorage] Sinal verde: ID Memória %d atualizado.", data_id)
        
    def init_from_plugs(self, plugs_blueprint):
        """
        Inicializa alocações baseadas no manifesto JSON do Builder.
        Isso provê uma blindagem contra Missing Keys.
        """
        for p in plugs_blueprint:
            pid = p.get('id', -1)
            # Zera a memória de forma segura. Expansível p/ defaultDataType no futuro.
            self._data_map[pid] = None 
        logger.info("[DataStorage] Alocação blindada: %d Plugs (Variáveis) reservados em cache.", len(plugs_blueprint))
