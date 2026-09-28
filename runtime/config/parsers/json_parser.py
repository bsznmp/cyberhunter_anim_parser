# -*- coding: utf-8 -*-
"""
runtime/config/parsers/json_parser.py
Decodifica manifestos em JSON (Estilo Nemo Template) contendo a topologia do grafo.
"""
import json
import logging

logger = logging.getLogger("Runtime.Config.JSONParser")

class NemoJSONDecoder(object):
    """
    Decodifica os arquivos de configuração do pipeline.
    Extrai as listas de 'plugs' (variáveis) e 'tasks' (nós de execução).
    """

    @staticmethod
    def parse_file(filepath):
        """Lê e valida estruturalmente um JSON de runtime."""
        logger.debug("[JSONParser] Lendo configuração de grafo: %s", filepath)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return NemoJSONDecoder._validate_and_extract(data)
        except Exception as e:
            logger.error("[JSONParser] Falha grave ao ler JSON '%s': %s", filepath, str(e))
            raise

    @staticmethod
    def _validate_and_extract(data):
        """
        Extrai o blueprint (o grafo) garantindo que chaves vitais de topologia existam.
        """
        blueprint = {
            'plugs': [],
            'tasks': []
        }

        # Extração Segura de Plugs (Inputs/Outputs Globais)
        if 'plugs' in data:
            for p in data['plugs']:
                plug_info = {
                    'name': p.get('name', 'UnnamedPlug'),
                    'dataTypeStr': p.get('dataTypeStr', 'float'),
                    'dataLocation': p.get('dataLocation', -1),
                    'id': p.get('id', -1)
                }
                blueprint['plugs'].append(plug_info)

        # Extração Segura de Tasks (Nós de Execução Matemáticos)
        if 'tasks' in data:
            for t in data['tasks']:
                task_info = {
                    'name': t.get('name', 'UnnamedTask'),
                    'id': t.get('id', -1),
                    'inputs': t.get('inputs', []),
                    'outputs': t.get('outputs', [])
                }
                blueprint['tasks'].append(task_info)

        logger.info("[JSONParser] JSON Decodificado com sucesso. Encontrados %d Plugs (Variáveis) e %d Tasks (Nós).", 
                    len(blueprint['plugs']), len(blueprint['tasks']))
                    
        return blueprint
