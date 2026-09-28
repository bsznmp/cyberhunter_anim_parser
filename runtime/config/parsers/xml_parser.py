# -*- coding: utf-8 -*-
"""
runtime/config/parsers/xml_parser.py
Módulo encarregado de decodificar e interpretar regras/filtros QA da ferramenta NeoX.
Aplica as extrações dinâmicas de 'xpath' sobre os DTOs em memória simulando um DOM.
"""
import logging

logger = logging.getLogger("Runtime.Config.XMLParser")

class NeoXPathResolver(object):
    """
    Faz a Extração de Dados Pela Chave. (Ref: Página 1 "Path to extract key data").
    Lê uma string como 'root/bone_count' ou '*/FileName:value' e extrai os dados crus 
    dos DTOs (como num DOM XML).
    """
    
    @staticmethod
    def resolve_xpath(data_root, xpath_expr):
        """
        Args:
            data_root (object/dict): O DTO base instanciado pelos parsers anteriores (ex GimDTO, MeshDTO).
            xpath_expr (str): Caminho a extrair, ex: 'root/skeleton/bone_count'.
            
        Returns:
            list: Conforme a documentação "Extracted content is stored in a list" (ex: [1,3]).
        """
        logger.debug("[NeoXPathResolver] Analisando expressão: '%s'", xpath_expr)
        
        clean_path = xpath_expr.replace('root/', '', 1) if xpath_expr.startswith('root/') else xpath_expr
        if clean_path.startswith('*/'):
            clean_path = clean_path.replace('*/', '', 1)

        tokens = clean_path.split('/')
        current_data = data_root

        for token in tokens:
            attr_name = token
            # Tratamento de regras da Página 2 e Página 3: .{dom} e :value
            if ':{value}' in token or ':value' in token:
                attr_name = token.split(':')[0]
            elif '.{dom}' in token:
                attr_name = token.split('.')[0]
                
            # Introspecção Limpa (Reflection) sem hardcoding
            if isinstance(current_data, dict):
                current_data = current_data.get(attr_name, None)
            elif hasattr(current_data, attr_name):
                current_data = getattr(current_data, attr_name)
            else:
                logger.warning("[NeoXPathResolver] Fallback: Atributo '%s' vazio no DTO.", attr_name)
                return []

        if isinstance(current_data, list):
            return current_data
        elif current_data is not None:
            return [current_data]
            
        return []

class NeoXConditionValidator(object):
    """
    Garante as condições (ex: ["satisfaz expressão", "d <= 5"]).
    """
    
    @staticmethod
    def evaluate(extracted_list, condition_array):
        """
        Avalia o array de extrações conforme os métodos globais da NeoX.
        
        Args:
            extracted_list (list): Lista com variáveis alvo obtida via xpath (o iterador 'd').
            condition_array (list): A regra limitante (ex: ['satisfaz expressão', 'len(d) > 0'])
            
        Returns:
            bool: Passou na regra de proteção?
        """
        if not condition_array or len(condition_array) < 2:
            return True
            
        operator = condition_array[0].lower()
        expression = condition_array[1]
        
        logger.debug("[ConditionValidator] Checando %d dados extraídos pelo operador '%s'. Expressão: %s", 
                     len(extracted_list), operator, expression)
        
        if "satisfaz" in operator or "satisfies" in operator:
            for d in extracted_list:    
                try:
                    # Avaliação super segura e mascarada: o 'd' assume a variável isolada do XPath e 'len' garante matrizes
                    allowed_glob = {'d': d, 'len': len, 'int': int, 'float': float, 'str': str}
                    result = eval(expression, {"__builtins__": {}}, allowed_glob)
                    if not result:
                        logger.error("[ConditionValidator] Regra FALHOU para a extração d=%s. Violou a expressão '%s'.", d, expression)
                        return False
                except Exception as e:
                    logger.error("[ConditionValidator] Sintaxe QA Quebrada na expressão '%s': %s", expression, str(e))
                    return False
            
            logger.info("[ConditionValidator] Todos os nós foram Aprovados nas restrições NeoX.")
            return True
        
        return True
