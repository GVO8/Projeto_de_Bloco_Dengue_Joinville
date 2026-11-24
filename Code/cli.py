"""
Linha de comando (adaptador de entrada para tarefas offline).

    python Code/cli.py coletar-noticias [--max-paginas 3]   # scraping + reconstrói o corpus
    python Code/cli.py gerar-corpus                          # corpus e contexto a partir das notícias salvas
    python Code/cli.py baixar-modelo                         # baixa o GGUF do Hugging Face (≈2,5 GB)
    python Code/cli.py status                                # mostra configuração e estado do modelo
    python Code/cli.py analisar-sentimentos [--todas]        # sentimento (preocupação) das notícias, para o dashboard
    python Code/cli.py medir-modelo [--pergunta "..."]       # chamada REAL ao modelo, com tempos medidos → Docs/Evidencias/
"""

import argparse
import os
import sys
import time
from datetime import datetime

from dengue.adapters.inbound.evidencia import coletar_ambiente, renderizar_markdown
from dengue.container import Container
from dengue.core.domain.erros import EntradaInvalidaError, ErroDengue


def _coletar(c: Container, args) -> int:
    print(f"Coletando notícias (até {args.max_paginas} páginas)... pode levar um minuto.")
    print(f"✔ {c.coletar_noticias.executar(args.max_paginas)} notícias salvas e corpus atualizado.")
    return 0


def _corpus(c: Container, _args) -> int:
    r = c.preparar_corpus.executar()
    print(f"✔ Corpus pronto: {r.noticias} notícias em {r.trechos} trechos (Data/Processed/).")
    return 0


def _baixar(c: Container, _args) -> int:
    from dengue.adapters.outbound.modelo_download import baixar_modelo

    cfg = c.config.llm
    print(f"Baixando {cfg.arquivo} de {cfg.repo_id} (≈2,5 GB) para {cfg.pasta_modelos} ...")
    print(f"✔ Modelo salvo em {baixar_modelo(cfg)}")
    return 0


def _status(c: Container, _args) -> int:
    cfg, e = c.config.llm, c.modelo.estado()
    print(f"Backend: {e.backend} | Modelo: {e.nome}\nArquivo: {cfg.caminho_modelo}\n"
          f"Pronto: {'sim' if e.pronto else 'NÃO'} {('— ' + e.detalhe) if e.detalhe else ''}\n"
          f"n_ctx={cfg.n_ctx} threads={cfg.n_threads or 'auto'} gpu_layers={cfg.n_gpu_layers} timeout={cfg.timeout_s:.0f}s")
    return 0


def _sentimentos(c: Container, args) -> int:
    print("Analisando o sentimento (preocupação) das notícias com a IA local... cada notícia pode levar alguns minutos.")
    r = c.analisar_sentimentos.executar(somente_pendentes=not args.todas, progresso=lambda n: print(f"  → {n.titulo[:80]}"))
    print(f"✔ {r.analisadas} analisadas · {r.ignoradas} já analisadas antes · {len(r.falhas)} falhas (resultados em Data/Processed/sentimentos_noticias.csv)")
    for noticia_id, motivo in r.falhas:
        print(f"  ✖ notícia {noticia_id}: {motivo}", file=sys.stderr)
    return 1 if r.falhas else 0


def _medir(c: Container, args) -> int:
    if c.config.llm.backend == "fake":
        raise EntradaInvalidaError("A medição precisa do modelo real, mas o backend está em 'fake' (simulado).",
                                   "Remova a variável DENGUE_LLM_BACKEND (ou use 'llamacpp'), baixe o modelo e rode de novo.")
    noticias = c.noticias.listar()
    if not noticias:
        raise EntradaInvalidaError("Não há notícias para usar na medição.", "Rode antes: python Code/cli.py coletar-noticias")
    noticia = next((n for n in noticias if n.id == args.noticia), noticias[0])
    execucoes = []
    for rotulo in ("1ª execução (inclui carregar o modelo)", "2ª execução (modelo já na memória)"):
        print(f"Executando: {rotulo} — operação '{args.operacao}' na notícia {noticia.id}…")
        inicio = time.perf_counter()
        r = c.processar_noticia.executar(noticia.id, args.operacao, args.pergunta_noticia)
        execucoes.append({"rotulo": rotulo, "entrada": f"notícia {noticia.id} · operação `{args.operacao}` · “{noticia.titulo}”",
                          "resposta": r.resultado, "metricas": r.metricas, "tempo_total_s": round(time.perf_counter() - inicio, 2)})
    if args.pergunta:
        print(f"Executando a conversa com os dados: “{args.pergunta}” (consulta o InfoDengue pela internet)…")
        inicio = time.perf_counter()
        r = c.conversar.executar(None, args.pergunta)
        execucoes.append({"rotulo": "Conversa com os dados (2 chamadas ao modelo + InfoDengue)", "entrada": f"pergunta: “{args.pergunta}” (tipo: {r.tipo})",
                          "resposta": r.resposta, "metricas": None, "tempo_total_s": round(time.perf_counter() - inicio, 2),
                          "etapas": [e.__dict__ for e in r.etapas]})
    pasta = c.config.raiz / "Docs" / "Evidencias"
    pasta.mkdir(parents=True, exist_ok=True)
    arquivo = pasta / f"medicao_{datetime.now():%Y%m%d_%H%M%S}.md"
    ambiente = coletar_ambiente(c.config, args.hardware or os.environ.get("DENGUE_HARDWARE", ""))
    arquivo.write_text(renderizar_markdown(ambiente, execucoes), encoding="utf-8")
    for e in execucoes:
        print(f"  {e['rotulo']}: {e['tempo_total_s']} s")
    print(f"✔ Evidência salva em {arquivo}\n  Anexe este arquivo (e um print da tela) ao relatório do TP.")
    return 0


def main(argv=None, container_factory=Container) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="comando", required=True)
    s = sub.add_parser("coletar-noticias"); s.add_argument("--max-paginas", type=int, default=3); s.set_defaults(f=_coletar)
    sub.add_parser("gerar-corpus").set_defaults(f=_corpus)
    sub.add_parser("baixar-modelo").set_defaults(f=_baixar)
    sub.add_parser("status").set_defaults(f=_status)
    s = sub.add_parser("analisar-sentimentos"); s.add_argument("--todas", action="store_true", help="refaz também as já analisadas"); s.set_defaults(f=_sentimentos)
    s = sub.add_parser("medir-modelo")
    s.add_argument("--noticia", type=int, default=0, help="id da notícia (padrão: a primeira)")
    s.add_argument("--operacao", default="resumo", choices=["resumo", "sentimento", "relatorio"])
    s.add_argument("--pergunta", default="", help="também mede uma pergunta da conversa com os dados")
    s.add_argument("--pergunta-noticia", default=None, help=argparse.SUPPRESS)
    s.add_argument("--hardware", default="", help='ex.: "i7-7500U, 24 GB RAM, GPU 4 GB"')
    s.set_defaults(f=_medir)
    args = p.parse_args(argv)
    try:
        return args.f(container_factory(), args)
    except ErroDengue as e:
        print(f"✖ {e.mensagem}\n  → {e.sugestao}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
