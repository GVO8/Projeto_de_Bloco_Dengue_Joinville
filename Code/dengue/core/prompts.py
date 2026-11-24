"""
Templates de prompt (v0.2) das operações com LLM. Domínio puro: sem I/O.

Cada operação declara o prompt, os dados que o alimentam, o limite de tokens
da resposta e se exige uma pergunta do usuário. Os templates usam str.format.
"""

VERSAO = "0.3"

PROMPTS = {
    "resumo": {
        "titulo": "Resumo automático de notícia",
        "dados_de_entrada": "Corpo da notícia (Data/Processed/noticias_corpus.jsonl)",
        "max_tokens": 250,
        "exige_pergunta": False,
        "template": (
            "Você é um assistente de comunicação em saúde pública.\n"
            "Resuma a notícia abaixo em até 3 frases, em português claro, sem "
            "acrescentar informações que não estejam no texto.\n\n"
            "Título: {titulo}\nTexto:\n{texto}\n\nResumo:"
        ),
    },
    "sentimento": {
        "titulo": "Classificação de sentimento (preocupação com a dengue)",
        "dados_de_entrada": "Título + resumo da notícia",
        "max_tokens": 120,
        "exige_pergunta": False,
        "template": (
            "Classifique o sentimento da notícia abaixo quanto à preocupação com a dengue, do ponto de vista da população: "
            "NEGATIVO se ela transmite preocupação, risco ou piora; POSITIVO se transmite alívio, melhora ou controle; "
            "NEUTRO se for apenas informativa. Responda apenas com a classe (POSITIVO, NEGATIVO ou NEUTRO) "
            "e uma justificativa de uma frase.\n\n"
            "Título: {titulo}\nResumo: {resumo}\n\nClasse:"
        ),
    },
    "qa": {
        "titulo": "Perguntas e respostas sobre a notícia",
        "dados_de_entrada": "Texto da notícia + contexto numérico (Data/Processed/contexto_infodengue.json)",
        "max_tokens": 300,
        "exige_pergunta": True,
        "template": (
            "Responda à pergunta usando SOMENTE o contexto abaixo. Se a "
            "resposta não estiver no contexto, diga que não sabe.\n\n"
            "Contexto numérico (InfoDengue, Joinville): {contexto_numerico}\n\n"
            "Trechos de notícias:\n{trechos}\n\nPergunta: {pergunta}\nResposta:"
        ),
    },
    "relatorio": {
        "titulo": "Geração de relatório descritivo",
        "dados_de_entrada": "Resumo dos níveis de alerta + títulos das notícias recentes",
        "max_tokens": 350,
        "exige_pergunta": False,
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
