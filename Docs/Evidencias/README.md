# Evidências de execução real

Esta pasta guarda as **provas de que o modelo real foi executado** na máquina do projeto (o que os testes automatizados, que usam FakeLLM, não mostram).

> **Status: PENDENTE.** Nenhuma medição real foi feita no ambiente de desenvolvimento deste projeto (sem acesso ao Hugging Face nem ao InfoDengue). Os arquivos `medicao_*.md` só aparecem depois que o aluno roda o comando abaixo.

## Como gerar

1. Ambiente com **Python 3.12** e `requirements-llm.txt` instalado (veja o README).
2. `python Code/cli.py baixar-modelo` (≈ 2,5 GB, uma vez).
3. Conexão com a internet (para a parte da conversa, que consulta o InfoDengue).
4. Rodar:
   ```powershell
   python Code/cli.py medir-modelo --hardware "i7-7500U, 24 GB RAM, GPU 4 GB" --pergunta "Qual foi o ano com mais casos de dengue?"
   ```
5. Abrir `Docs/Evidencias/medicao_*.md` e conferir tempos e respostas.

## O que anexar ao relatório do TP

- [ ] O arquivo `medicao_*.md` gerado.
- [ ] **Print** da página *Converse com os dados* com uma resposta real, mostrando o painel "Como a resposta foi obtida" (requisição ao InfoDengue, fatos e tempos por etapa).
- [ ] **Print** do dashboard com a seção de mídia preenchida (rode antes `python Code/cli.py analisar-sentimentos`).
- [ ] Os valores medidos no lugar das estimativas em `Docs/Project/escolha_modelo_llm.md` e no Charter.

## Se algo der errado
Mensagens de erro do comando trazem o que fazer (modelo não baixado, biblioteca ausente, sem notícias). Veja a seção "Problemas comuns" do README.
