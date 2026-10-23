import streamlit as st

st.title("🦟 Dengue em Múltiplas Dimensões — Joinville/SC")
st.caption("TP3 · Projeto de IA Generativa e ESG · alinhado ao ODS 3 (Saúde e Bem-Estar)")

c1, c2 = st.columns([2, 1])
with c1:
    st.markdown(
        """
        **Problema de negócio:** indicadores públicos de epidemiologia, clima,
        satélite e população para Joinville/SC existem, mas estão dispersos em
        plataformas técnicas distintas, sem uma camada única e acessível.

        **O que o app faz hoje:**
        - 📈 **Painel InfoDengue:** nível de alerta semanal de 2026, uma linha por nível.
        - 📰 **Notícias:** coleta por *web scraping* (Joinville + Dengue), nuvem de palavras e estatísticas.
        - 📂 **Upload e Download:** complementa os dados com CSVs no formato do InfoDengue.
        - 🔌 **API FastAPI:** os mesmos dados disponíveis por rotas GET/POST.
        - 🤖 **Preparação para LLM:** corpus e prompts prontos para a próxima etapa.

        **ODS:** 3 (Saúde e Bem-Estar), 11 (Cidades Sustentáveis), 17 (Parcerias e dados abertos).
        """
    )
with c2:
    st.info(
        "**Público-alvo (fictício)**\n\nPerfis hipotéticos de gestor de saúde "
        "pública e morador local, usados apenas para orientar o design — sem "
        "contato ou validação com órgãos públicos reais."
    )

st.subheader("Fontes e referências")
st.markdown(
    """
    - [InfoDengue — API pública](https://info.dengue.mat.br/)
    - [NSC Total — notícias sobre Dengue](https://www.nsctotal.com.br/tag/dengue)
    - [SINAN / OpenDataSUS](https://opendatasus.saude.gov.br/)
    - Fontes documentadas para etapas futuras: Copernicus, Google Earth Engine, IBGE
    """
)
