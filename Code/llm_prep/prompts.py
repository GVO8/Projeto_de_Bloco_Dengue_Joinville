"""
Templates de prompt (v0.1) para as tarefas com LLM da próxima etapa.

NENHUM modelo é chamado no TP3: aqui apenas definimos, para cada cenário
do enunciado, qual dado alimenta o prompt e como ele será montado.
Os templates usam str.format; os campos {entre_chaves} são preenchidos
com dados de Data/Processed/.
"""

VERSAO = "0.1"

PROMPTS = {
    "resumo": {
        "titulo": "Resumo automático de notícia",
        "dados_de_entrada": "Corpo da notícia (Data/Processed/noticias_corpus.jsonl, campo 'texto')",
        "template": (
            "Você é um assistente de comunicação em saúde pública.\n"
            "Resuma a notícia abaixo em até 3 frases, em português claro, sem "
            "acrescentar informações que não estejam no texto.\n\n"
            "Título: {titulo}\nTexto:\n{texto}\n\nResumo:"
        ),
    },
    "sentimento": {
        "titulo": "Classificação de sentimento",
        "dados_de_entrada": "Título + resumo de cada notícia (nsc_noticias_joinville_dengue.csv)",
        "template": (
            "Classifique o sentimento do texto abaixo, do ponto de vista da "
            "saúde pública, como POSITIVO, NEGATIVO ou NEUTRO. Responda apenas "
            "com a classe e uma justificativa de uma frase.\n\n"
            "Título: {titulo}\nResumo: {resumo}\n\nClasse:"
        ),
    },
    "qa": {
        "titulo": "Perguntas e respostas sobre os dados",
        "dados_de_entrada": "Trechos das notícias + contexto numérico (Data/Processed/contexto_infodengue.json)",
        "template": (
            "Responda à pergunta usando SOMENTE o contexto abaixo. Se a "
            "resposta não estiver no contexto, diga que não sabe.\n\n"
            "Contexto numérico (InfoDengue, Joinville): {contexto_numerico}\n\n"
            "Trechos de notícias:\n{trechos}\n\nPergunta: {pergunta}\nResposta:"
        ),
    },
    "relatorio": {
        "titulo": "Geração de relatório descritivo",
        "dados_de_entrada": "Resumo semanal dos níveis de alerta + títulos das notícias recentes",
        "template": (
            "Escreva um boletim de até 150 palavras para gestores de saúde "
            "pública, descrevendo a situação da dengue em Joinville com base "
            "nos dados abaixo. Não faça previsões.\n\n"
            "Resumo dos níveis de alerta: {contexto_numerico}\n"
            "Notícias recentes: {titulos}\n\nBoletim:"
        ),
    },
}


def montar_prompt(chave: str, **campos) -> str:
    return PROMPTS[chave]["template"].format(**campos)
