# -*- coding: utf-8 -*-
"""
Hierarquia de exceções centralizadas para o pipeline NeoX Parser.

Uso:
    from core.exceptions import FormatError, EOFError, ValidationError

Design:
    - NeoXError é a raiz. Catch-all para qualquer erro do projeto.
    - Subclasses fornecem categorização semântica para o caller.
    - Todas as exceções carregam `context` (dict) para debugging.
"""


class NeoXError(Exception):
    """Exceção base para todos os erros do projeto NeoX Parser."""

    def __init__(self, message, context=None):
        super(NeoXError, self).__init__(message)
        # Metadados de debugging — sempre um dict, nunca None
        self.context = context or {}

    def __str__(self):
        base = super(NeoXError, self).__str__()
        if self.context:
            ctx_str = ", ".join("{0}={1!r}".format(k, v) for k, v in sorted(self.context.items()))
            return "{0} [{1}]".format(base, ctx_str)
        return base


# =============================================================================
# Erros de Parsing Binário
# =============================================================================

class ParserError(NeoXError):
    """Erro genérico durante a leitura de um arquivo binário NeoX."""
    pass


class FormatError(ParserError):
    """
    O arquivo não corresponde ao formato NeoX esperado.

    Levantado quando:
    - O magic number não bate.
    - Um campo sentinel não tem o valor esperado.
    - A estrutura sequencial está corrompida.
    """
    pass


class EOFError(ParserError):
    """
    Fim-de-arquivo inesperado durante leitura sequencial.

    Levantado quando f.read(n) retorna menos bytes do que o esperado,
    indicando que o arquivo está truncado.
    """
    pass


# =============================================================================
# Erros de Validação Semântica
# =============================================================================

class ValidationError(NeoXError):
    """
    Dado lido é sintaticamente válido, mas semanticamente incoerente.

    Exemplos:
    - bone_count > 10.000 (implausível — provável corrupção).
    - vertex_count > 5.000.000 (implausível para assets deste engine).
    - Quaternion com norma muito fora de 1.0.
    - Frame count negativo ou zero numa animação com tracks.
    """
    pass


# =============================================================================
# Erros de Integração com Blender
# =============================================================================

class BlenderError(NeoXError):
    """
    Falha durante a execução headless do Blender ou exportação FBX.

    Levantado quando:
    - O executável do Blender não é encontrado.
    - O Blender retorna código de erro != 0.
    - O arquivo FBX de saída não é gerado.
    """
    pass


class BlenderNotFoundError(BlenderError):
    """O executável do Blender não foi encontrado no sistema."""
    pass
