"""
Linha de comando (adaptador de entrada para tarefas offline).

    python Code/cli.py coletar-noticias [--max-paginas 3]   # scraping + reconstrói o corpus
    python Code/cli.py gerar-corpus                          # corpus e contexto a partir das notícias salvas
    python Code/cli.py baixar-modelo                         # baixa o GGUF do Hugging Face (≈2,5 GB)
    python Code/cli.py status                                # mostra configuração e estado do modelo
"""

import argparse
import sys

from dengue.container import Container
from dengue.core.domain.erros import ErroDengue


def _coletar(c: Container, args) -> None:
    print(f"Coletando notícias (até {args.max_paginas} páginas)... pode levar um minuto.")
    n = c.coletar_noticias.executar(args.max_paginas)
    print(f"✔ {n} notícias salvas e corpus atualizado.")


def _corpus(c: Container, _args) -> None:
    r = c.preparar_corpus.executar()
    print(f"✔ Corpus pronto: {r.noticias} notícias em {r.trechos} trechos (Data/Processed/).")


def _baixar(c: Container, _args) -> None:
    from dengue.adapters.outbound.modelo_download import baixar_modelo

    cfg = c.config.llm
    print(f"Baixando {cfg.arquivo} de {cfg.repo_id} (≈2,5 GB) para {cfg.pasta_modelos} ...")
    print(f"✔ Modelo salvo em {baixar_modelo(cfg)}")


def _status(c: Container, _args) -> None:
    cfg, e = c.config.llm, c.modelo.estado()
    print(f"Backend: {e.backend} | Modelo: {e.nome}\nArquivo: {cfg.caminho_modelo}\n"
          f"Pronto: {'sim' if e.pronto else 'NÃO'} {('— ' + e.detalhe) if e.detalhe else ''}\n"
          f"n_ctx={cfg.n_ctx} threads={cfg.n_threads or 'auto'} gpu_layers={cfg.n_gpu_layers} timeout={cfg.timeout_s:.0f}s")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="comando", required=True)
    s = sub.add_parser("coletar-noticias"); s.add_argument("--max-paginas", type=int, default=3); s.set_defaults(f=_coletar)
    sub.add_parser("gerar-corpus").set_defaults(f=_corpus)
    sub.add_parser("baixar-modelo").set_defaults(f=_baixar)
    sub.add_parser("status").set_defaults(f=_status)
    args = p.parse_args(argv)
    try:
        args.f(Container(), args)
        return 0
    except ErroDengue as e:
        print(f"✖ {e.mensagem}\n  → {e.sugestao}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
