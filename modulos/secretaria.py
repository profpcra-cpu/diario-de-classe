# Altere isto:
from .conexao import executar_query
from .pdf_generator import (
    gerar_pdf_declaracao_escolaridade,
    gerar_pdf_historico_aluno,
    gerar_pdf_passe_estudantil,
    gerar_pdf_passes_turma_unificado,
    gerar_pdf_renovacao_matricula,
    gerar_pdf_renovacao_turma_unificado,
)

# Para isto (direto):
from conexao import executar_query
from pdf_generator import (
    gerar_pdf_declaracao_escolaridade,
    gerar_pdf_historico_aluno,
    gerar_pdf_passe_estudantil,
    gerar_pdf_passes_turma_unificado,
    gerar_pdf_renovacao_matricula,
    gerar_pdf_renovacao_turma_unificado,
)
