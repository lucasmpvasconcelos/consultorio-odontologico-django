"""
filters_urls.py — Arquivo legado mantido para compatibilidade.
Use principal.filters para os FilterSets atualizados.
"""

# Re-exporta do novo módulo para não quebrar importações existentes
from .filters import (  # noqa: F401
    PacienteFilter,
    ConsultaFilter,
    FinanceiroFilter,
    EstoqueFilter,
    DentistaFilter,
    ProcedimentoFilter,
)