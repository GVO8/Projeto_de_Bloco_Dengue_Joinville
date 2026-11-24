"""Prompts da conversa com os dados do InfoDengue (v0.1). Domínio puro, sem I/O."""

VERSAO = "0.1"

PLANEJADOR = """Converta a pergunta do usuário em uma consulta ao InfoDengue sobre casos de dengue. O ano atual é {ano_atual}.
Responda SOMENTE com um JSON válido, com estas chaves:
"assunto_valido": true se a pergunta é sobre casos de dengue; false se for de outro assunto;
"cidade": "joinville", "nao_citada" ou "outra" (use "outra" se citar outra cidade, estado ou país);
"intencao": "pico", "ano_mais_casos", "ano_menos_casos", "comparar_anos", "total" ou "outra";
"ano_inicio" e "ano_fim": anos (números) necessários para responder, ou null para todos os anos.

Exemplos:
Pergunta: Qual foi o pico de casos em {ano_atual}?
JSON: {{"assunto_valido": true, "cidade": "nao_citada", "intencao": "pico", "ano_inicio": {ano_atual}, "ano_fim": {ano_atual}}}
Pergunta: Qual foi o ano com mais casos?
JSON: {{"assunto_valido": true, "cidade": "nao_citada", "intencao": "ano_mais_casos", "ano_inicio": null, "ano_fim": null}}
Pergunta: Os casos subiram em relação ao ano passado?
JSON: {{"assunto_valido": true, "cidade": "nao_citada", "intencao": "comparar_anos", "ano_inicio": {ano_anterior}, "ano_fim": {ano_atual}}}
Pergunta: Qual a capital da França?
JSON: {{"assunto_valido": false, "cidade": "nao_citada", "intencao": "outra", "ano_inicio": null, "ano_fim": null}}

Conversa até agora:
{historico}
Pergunta: {pergunta}
JSON:"""

RESPONDEDOR = """Você responde perguntas sobre casos de dengue em Joinville/SC usando SOMENTE os dados do InfoDengue abaixo.
Regras: responda em português, em até 4 frases; cite os números, anos e datas relevantes; não use conhecimento externo; \
se os dados não permitirem responder, diga que essa informação não está nos dados consultados; não fale de outras cidades nem de outros assuntos.

Conversa até agora:
{historico}
Dados do InfoDengue:
{fatos}

Pergunta: {pergunta}
Resposta:"""

TEMPLATES = {"planejador": PLANEJADOR, "respondedor": RESPONDEDOR}


def montar(chave: str, **campos) -> str:
    return TEMPLATES[chave].format(**campos)
