"""
Conteúdo da apresentação/argumentação do TP5 (fonte única para o Markdown e para o PDF).

Gerar:  python Docs/Apresentacao/gerar_pdf.py --nome "Seu Nome" --saida nome_sobrenome_PB_TP5.pdf
Prints: coloque os arquivos em Docs/Apresentacao/prints/ (dashboard.png, chat.png, mensurado.png, midia.png)
e gere de novo: eles entram automaticamente no lugar dos quadros "INSERIR PRINT".
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "Code"))

from dengue.adapters.outbound.infodengue import montar_url  # noqa: E402
from dengue.core.domain.chat import PERGUNTAS_EXEMPLO  # noqa: E402
from dengue.core.domain.planejamento import planejar_por_regras  # noqa: E402

REPO_URL = "https://github.com/GVO8/Projeto_de_Bloco_Dengue_Joinville"


def _consultas_de_exemplo(ano_atual: int) -> list[list[str]]:
    linhas = []
    for pergunta in PERGUNTAS_EXEMPLO:
        plano = planejar_por_regras(pergunta, ano_atual)
        linhas.append([pergunta, plano.intencao, f"{plano.ano_inicio} a {plano.ano_fim}",
                       f"ey_start={plano.ano_inicio}, ey_end={plano.ano_fim}, ew 1 a 53"])
    return linhas


def construir(nome: str, ano_atual: int | None = None) -> list[tuple]:
    ano_atual = ano_atual or date.today().year
    url = montar_url(ew_start=1, ew_end=53, ey_start=ano_atual - 1, ey_end=ano_atual)
    url_quebrada = url.replace("&", "\n   &").replace("?\n   &", "?&", 1)
    B: list[tuple] = []
    add = B.append

    add(("title", "Dengue em Joinville: dados, mídia e IA em linguagem natural"))
    add(("subtitle", "Projeto de Bloco · Ciência de Dados Aplicada · TP5 — Solução final"))
    add(("meta", [("Autor", nome), ("Repositório", REPO_URL), ("Data", date.today().strftime("%d/%m/%Y")),
                  ("Caminho escolhido", "Opção 1 — memória conversacional com LLM local (Qwen3-4B)")]))
    add(("nota", "**Em uma frase:** qualquer pessoa pergunta em português sobre os casos de dengue em Joinville; uma IA que roda no próprio "
                 "computador transforma a pergunta em uma consulta ao InfoDengue e redige a resposta a partir de números calculados em código, "
                 "enquanto um dashboard cruza a curva de casos com o tom da mídia."))

    add(("h1", "1. O problema de negócio"))
    add(("p", "A dengue cresce no Sul do Brasil, e os dados para acompanhá-la são públicos: o **InfoDengue** publica por API a série semanal "
              "de casos de cada município. O problema é que esses dados são difíceis de usar. Responder *“foi o ano com mais casos?”* exige "
              "conhecer a API, a semana epidemiológica e programar. Além disso, os números não dizem **o que a população está sendo levada a "
              "sentir**: a mídia local é o canal pelo qual a maioria toma conhecimento da situação."))
    add(("nota", "**Pergunta de negócio:** como tornar os dados públicos de dengue de Joinville acessíveis a qualquer pessoa, em linguagem natural, "
                 "e relacioná-los à preocupação veiculada pela mídia, com uma IA local, auditável e que não invente números?"))
    add(("h2", "Por que esta solução"))
    add(("ul", ["**Democratiza o acesso à informação:** quem não sabe programar obtém insights dos dados públicos perguntando em português.",
                "**Usa a mídia como fonte:** notícias reais são classificadas por IA quanto à preocupação que transmitem (análise de sentimento).",
                "**É confiável por construção:** a IA não faz contas; ela interpreta a pergunta e redige. Cada resposta mostra a requisição feita e os fatos usados."]))

    add(("h1", "2. Alinhamento com ESG e os ODS"))
    add(("table", ["Pilar / ODS", "Como o projeto se conecta"], [
        ["**Social (S)**", "Saúde pública e acesso à informação: o cidadão consulta a situação da dengue sem conhecimento técnico."],
        ["**Governança (G)**", "Transparência e uso responsável de IA: modelo **local** (nenhum texto sai da máquina), escopo restrito (só dengue em Joinville), "
                               "números auditáveis, aviso de limitações e erros tratados com orientação."],
        ["**ODS 3** — Saúde e Bem-Estar (3.3)", "Combate à dengue, doença tropical negligenciada: informação para acompanhar e agir."],
        ["**ODS 16** — Instituições Eficazes (16.10)", "Acesso público à informação: dados abertos tornados consultáveis em linguagem natural."],
        ["**ODS 17** — Parcerias e Meios", "Uso exclusivo de dados abertos (InfoDengue e notícias públicas)."],
    ], [30, 70]))
    add(("p", "O pilar Ambiental aparece só de forma indireta: o InfoDengue incorpora clima em seus modelos, mas este projeto não trata indicadores ambientais."))

    add(("h1", "3. O ciclo completo de ciência de dados"))
    add(("table", ["Etapa", "O que foi feito", "Por que importa"], [
        ["**1. Coleta**", "API do InfoDengue (Joinville, dengue, semanas 1–53, vários anos) e *web scraping* de notícias do NSC Total (BeautifulSoup).",
         "Duas fontes reais e complementares: o *quê* (números) e o *como é contado* (mídia)."],
        ["**2. Preparação**", "Limpeza do texto raspado (rodapé, cookies, manchetes de outras matérias), divisão em trechos; cálculo dos fatos em código.",
         "Sem limpeza a IA resumiria assuntos alheios; sem cálculo em código ela erraria as contas."],
        ["**3. Modelagem / IA**", "LLM local Qwen3-4B: planeja a consulta (JSON), redige a resposta, classifica sentimento, resume e responde sobre notícias.",
         "Transforma linguagem natural em consulta e dado em frase."],
        ["**4. Insights**", "Dashboard: KPIs, sazonalidade por ano, total por ano, semanas por nível de alerta, tom da mídia × casos.",
         "Mostra o resultado de forma simples, com profundidade."],
        ["**5. Interação**", "Página *Converse com os dados* com memória: perguntas de continuação (“e em 2024?”).",
         "O usuário investiga por conta própria e em tempo real."],
    ], [18, 47, 35]))

    add(("h1", "4. A solução: conversar com os dados do InfoDengue (Opção 1)"))
    add(("h2", "4.1 Como uma pergunta vira uma resposta"))
    add(("ol", ["**Guarda de escopo** (sem custo de IA): barra outra cidade, outro território, assunto sem relação com dengue e tentativas de alterar as regras.",
                "**Planejamento** (1ª chamada à IA, em modo JSON com 4 exemplos): a pergunta vira um plano (`intencao`, `ano_inicio`, `ano_fim`), "
                "validado e reconciliado com regras; se o JSON falhar, as regras assumem.",
                "**Requisição ao InfoDengue**: sempre `geocode=4209102` (Joinville) e `disease=dengue`.",
                "**Fatos calculados em código**: total por ano, pico (semana e data), ano com mais/menos casos, comparação com o ano anterior.",
                "**Resposta** (2ª chamada à IA): redigida só a partir dos fatos e dos últimos 3 turnos da conversa; o turno é guardado na memória da sessão."]))
    add(("h2", "4.2 As perguntas-modelo e as consultas que elas geram"))
    add(("p", f"A tabela abaixo é gerada pelo próprio código (planejador por regras, ano atual = {ano_atual}); no uso real o plano vem da IA e é conferido pelas regras."))
    add(("table", ["Pergunta", "Intenção", "Anos consultados", "Parâmetros enviados ao InfoDengue"], _consultas_de_exemplo(ano_atual), [33, 21, 14, 32]))
    add(("p", "Exemplo de requisição completa (ano anterior e atual):"))
    add(("code", url_quebrada))
    add(("h2", "4.3 Por que os números não vêm da IA"))
    add(("p", "Um modelo de 4 bilhões de parâmetros erra aritmética e comparações. Por isso os números são calculados com pandas e entregues à IA como texto pronto. Regras de negócio que isso permite garantir e testar:"))
    add(("ul", ["**Anos completos × em andamento:** o ranking (mais/menos casos) só considera anos completos; o ano corrente é tratado à parte.",
                "**Comparação nas mesmas semanas:** 2026 (até a semana 40) é comparado com as semanas 1–40 de 2025, não com o ano inteiro.",
                "**Auditável:** a tela mostra a requisição, os fatos calculados e o tempo de cada etapa."]))
    add(("h2", "4.4 Escopo restrito e segurança"))
    add(("table", ["Camada", "O que faz", "Exemplo"], [
        ["1. Regras determinísticas", "Barra, sem gastar IA, o que é claramente de fora", "“Casos em Blumenau?”, “E no Brasil?”, “Ignore as instruções…”"],
        ["2. Plano da IA", "O JSON também sinaliza `assunto_valido` e `cidade`", "Cidade pequena fora da lista; assunto ambíguo"],
        ["3. Resposta ancorada", "O redator só recebe os dados de Joinville e é instruído a dizer quando não há a informação", "Pergunta sobre algo que a série não tem (ex.: óbitos)"],
    ], [24, 42, 34]))
    add(("p", "Perguntas fora do escopo recebem uma recusa educada com exemplos do que perguntar. Não há dado sintético nas respostas: se o InfoDengue estiver fora do ar, o aplicativo informa o erro."))
    add(("print", "Conversa com os dados: resposta real e painel “Como a resposta foi obtida”", "chat.png",
         "Rode a API e a interface, pergunte “Qual foi o ano com mais casos de dengue?” e tire um print expandindo “Como a resposta foi obtida”."))

    add(("h1", "5. O dashboard"))
    add(("p", "Uma página inicial que mostra, de cima para baixo: **situação atual** (casos do ano, pico, variação contra o mesmo período do ano anterior, nível de alerta), "
              "o **ciclo de dados** com contadores reais, a **sazonalidade** (um ano sobreposto ao outro), o **total por ano**, as **semanas por nível de alerta** e a **mídia**."))
    add(("table", ["Visualização", "Pergunta que responde", "Origem"], [
        ["KPIs", "Como estamos agora em relação ao ano passado?", "Calculado em código"],
        ["Casos por semana, por ano", "Há sazonalidade? Este ano está acima ou abaixo?", "InfoDengue"],
        ["Total por ano (ano em andamento destacado)", "Qual ano teve mais casos?", "Calculado em código"],
        ["Semanas por nível de alerta", "Quanto tempo cada ano passou em alerta alto?", "InfoDengue"],
        ["Tom das notícias", "A mídia transmite preocupação ou alívio?", "IA (sentimento)"],
        ["Casos × notícias no tempo", "O tom da mídia acompanha a curva de casos?", "InfoDengue + IA"],
    ], [34, 44, 22]))
    add(("p", "O que é **calculado** e o que é **IA** vem sempre identificado, e a seção de mídia declara que o tom das notícias é um indicador **indireto** da preocupação."))
    add(("print", "Dashboard completo", "dashboard.png", "Tire um print da página Dashboard com os gráficos carregados."))
    add(("print", "Seção de mídia (após rodar `python Code/cli.py analisar-sentimentos`)", "midia.png", "Tire um print da seção “A mídia como termômetro de preocupação”."))

    add(("h1", "6. A IA: modelo local e engenharia de prompts"))
    add(("h2", "Modelo e hardware"))
    add(("p", "**Qwen3-4B-Instruct-2507** quantizado (GGUF Q4_K_M, 2,5 GB), executado com llama.cpp. Escolhido para o hardware do projeto (i7-7500U, 24 GB de RAM, 4 GB de VRAM): "
              "cabe na memória, roda em CPU, é de instruções (sem modo de raciocínio, logo mais rápido), tem bom português e licença Apache-2.0. "
              "Alternativas descartadas e a comparação completa estão em `Docs/Project/escolha_modelo_llm.md`."))
    add(("h2", "Engenharia de prompts (versionada no código)"))
    add(("table", ["Prompt", "Função", "Técnicas"], [
        ["Planejador", "Converte a pergunta em plano JSON", "Esquema explícito, 4 exemplos (*few-shot*), modo JSON do llama.cpp, validação e reconciliação por regras"],
        ["Redator", "Redige a resposta", "Contexto fechado (só os fatos), limite de 4 frases, instrução de admitir ausência de dado, memória dos 3 últimos turnos"],
        ["Sentimento", "Classifica a preocupação da notícia", "Rótulos definidos do ponto de vista da população (NEGATIVO = preocupante, POSITIVO = tranquilizador)"],
        ["Resumo / perguntas / relatório", "Operações sobre uma notícia", "Texto limpo e truncado em fronteira de frase; contexto numérico com aviso quando os dados são de exemplo"],
    ], [20, 28, 52]))
    add(("p", "Temperatura 0,2 (respostas fiéis), uma chamada por vez (fila), limite de tempo real por *streaming* e erros traduzidos para mensagens que dizem o que fazer."))

    add(("h1", "7. Robustez e qualidade de engenharia"))
    add(("ul", ["**Arquitetura hexagonal:** núcleo sem frameworks; a IA, o InfoDengue, os arquivos e o scraper são adaptadores intercambiáveis. Um teste automático verifica a regra de dependência.",
                "**Mais de 300 testes automatizados**, incluindo o modelo simulado (FakeLLM), o adaptador do llama.cpp com um `Llama` falso, as rotas da API, as páginas e a CLI.",
                "**Verificação por mutação:** quebras propositais em comportamentos críticos (escopo, cálculo de fatos, memória, cache, modo JSON) foram todas detectadas pelos testes.",
                "**Erros amigáveis:** 18 códigos de erro, cada um com mensagem, sugestão, categoria e HTTP próprios (404, 422, 429, 502, 503, 504). Erros de IA começam com “Houve um problema com a IA (modelo …)”."]))

    add(("h1", "8. Resultados e insights"))
    add(("p", "O painel e a conversa respondem, a partir dos dados reais do InfoDengue, perguntas como: em que semana e data ocorreu o pico do ano, qual ano teve mais e menos casos, "
              "e se o ano corrente está acima ou abaixo do anterior nas mesmas semanas. A mídia adiciona uma segunda camada: quando e com que tom o assunto aparece."))
    add(("nota", "**Resultados reais: preencher após executar.** Este documento foi preparado sem acesso ao InfoDengue nem ao modelo real, por isso **não traz números de casos nem respostas "
                 "da IA inventados**. Preencha a tabela abaixo com o que o seu painel mostrar e inclua os prints."))
    add(("table", ["Pergunta", "Resposta obtida no sistema (preencher)"], [
        [PERGUNTAS_EXEMPLO[0], "_____________________________"],
        [PERGUNTAS_EXEMPLO[1], "_____________________________"],
        [PERGUNTAS_EXEMPLO[2], "_____________________________"],
        [PERGUNTAS_EXEMPLO[3], "_____________________________"],
    ], [55, 45]))
    add(("print", "Medição real do modelo (saída de `python Code/cli.py medir-modelo`)", "mensurado.png",
         "Rode `python Code/cli.py medir-modelo --pergunta \"Qual foi o ano com mais casos de dengue?\"` e tire um print do terminal, ou anexe o arquivo de Docs/Evidencias/."))

    add(("h1", "9. Limitações e próximos passos"))
    add(("ul", ["**Sentimento é indicador indireto:** mede o tom das notícias, não a opinião da população; não foi validado contra uma amostra rotulada à mão.",
                "**Amostra pequena de notícias (6):** o gráfico de mídia é ilustrativo. Ampliar a coleta é o caminho.",
                "**Casos notificados são revisados:** as últimas semanas podem mudar; as respostas avisam.",
                "**Modelo pequeno em hardware modesto:** pode errar a interpretação, e uma pergunta usa duas chamadas à IA, levando alguns minutos em CPU (tempos reais a medir).",
                "**Consulta de vários anos ao InfoDengue** implementada conforme o exemplo oficial, mas ainda não confirmada no serviço real.",
                "**Guarda de escopo heurística**, memória só em RAM e API sem autenticação (uso local).",
                "**Próximos passos:** avaliar a qualidade das respostas com perguntas conferidas manualmente, validar o sentimento com amostra rotulada, ampliar as notícias e persistir conversas."]))

    add(("h1", "10. Como executar e checklist da entrega"))
    add(("p", "O passo a passo completo para Windows está no `README.md` do repositório. Resumo: Python 3.12 → `pip install -r requirements.txt -r requirements-llm.txt` → "
              "`python Code/cli.py baixar-modelo` → `python Code/run_api.py` (Terminal 1) → `python -m streamlit run Code/streamlit_app.py` (Terminal 2)."))
    add(("table", ["Item da entrega", "Situação"], [
        ["Código no GitHub, com link neste documento", "Pronto após o `git push`"],
        ["Project Charter e Data Summary Report atualizados", "Pronto"],
        ["Opção 1 (memória conversacional) integrada ao dashboard", "Pronto"],
        ["Documentação de arquitetura, API e escolha do modelo", "Pronto"],
        ["Evidência real do modelo (medição na máquina do projeto)", "**Pendente — executar `medir-modelo`**"],
        ["Prints do dashboard, da conversa e da mídia", "**Pendente — colocar em `Docs/Apresentacao/prints/`**"],
        ["Respostas reais na tabela da seção 8", "**Pendente — preencher**"],
    ], [64, 36]))

    add(("pagebreak",))
    add(("h1", "Apêndice — Roteiro de apresentação (5 a 7 minutos)"))
    add(("ol", ["**(30 s) O problema.** Dados públicos de dengue existem, mas exigem técnica; e ninguém mede o que a mídia faz a população sentir.",
                "**(45 s) A ideia.** Perguntar em português; IA local; números calculados em código; mídia como termômetro. ESG: Social e Governança; ODS 3, 16 e 17.",
                "**(60 s) O ciclo.** Mostrar a tabela da seção 3: coleta, preparação, IA, insights, interação. Destacar a limpeza do texto e o cálculo em código.",
                "**(2 min) Demonstração.** No Dashboard: KPIs e sazonalidade. Em *Converse com os dados*: perguntar o ano com mais casos; abrir “Como a resposta foi obtida”; "
                "perguntar “e em 2024?” (memória); perguntar sobre outra cidade (recusa).",
                "**(45 s) A IA.** Qwen3-4B local; por que cabe no hardware; planejador JSON + redator ancorado; mostrar o tempo medido.",
                "**(45 s) Qualidade e honestidade.** Arquitetura hexagonal, mais de 300 testes, erros amigáveis; limitações: sentimento indireto, amostra pequena, modelo pequeno.",
                "**(30 s) Fecho.** Qualquer cidadão consegue interrogar os dados públicos de dengue de Joinville, com transparência sobre o que é cálculo e o que é IA."]))
    return B
