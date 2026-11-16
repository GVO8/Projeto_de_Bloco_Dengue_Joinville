"""Dados de teste compartilhados."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

PARAGRAFO_A = ("A prefeitura de Joinville informou que o número de mortes por dengue chegou a zero em 2025, "
               "depois de 83 óbitos registrados em 2024, segundo a Secretaria da Saúde do município.")
PARAGRAFO_B = ("O método Wolbachia consiste em liberar mosquitos Aedes aegypti com uma bactéria que impede a "
               "transmissão do vírus, e será ampliado para todos os bairros da cidade ainda neste ano.")
RUIDO = ["Entre na comunidade exclusiva de colunistas do NSC Total", "Cidade litorânea de SC leiloa terrenos",
         "© 2026 NSC Total. Todos os direitos reservados.", "Este site usa cookies para fornecer serviços"]


def escrever_dados(raiz: Path) -> None:
    raw = raiz / "Data" / "Raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "nsc_noticias_joinville_dengue.csv").write_text(
        "id,titulo,data_publicacao,autor,url,resumo\n"
        "1,Joinville zera mortes por dengue,2026-01-09T10:00:00+00:00,Ana,https://exemplo.com/1,Resumo um\n"
        "2,Mosquitos de laboratório chegam a novos bairros,2026-08-13T10:00:00+00:00,,https://exemplo.com/2,\n",
        encoding="utf-8")
    (raw / "nsc_noticias_texto.txt").write_text(
        "### Joinville zera mortes por dengue\n" + "\n".join([PARAGRAFO_A, *RUIDO[:2], PARAGRAFO_B, *RUIDO[2:]]) + "\n\n"
        "### Mosquitos de laboratório chegam a novos bairros\n" + PARAGRAFO_B + "\n\n", encoding="utf-8")
    pd.DataFrame({
        "id": [f"4209102{202600 + i}" for i in range(1, 7)], "SE": [202600 + i for i in range(1, 7)],
        "nivel": [1, 1, 2, 3, 4, 2], "casos": [1, 2, 5, 20, 40, 8],
    }).to_csv(raw / "infodengue_sample.csv", index=False)
