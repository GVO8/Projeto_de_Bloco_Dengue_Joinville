import streamlit as st

st.title("🦟 Dengue em Múltiplas Dimensões — Joinville/SC")
st.caption("TP4 · Projeto de IA Generativa e ESG · alinhado ao ODS 3 (Saúde e Bem-Estar)")

c1, c2 = st.columns([2, 1])
with c1:
    st.markdown(
        """
        **Problema de negócio:** indicadores públicos de dengue para Joinville/SC existem, mas estão
        dispersos e difíceis de interpretar. Este painel os reúne e, agora, usa uma **IA local** para
        ajudar a ler as notícias.

        **O que o app faz:**
        - 📈 **Painel InfoDengue:** nível de alerta semanal, uma linha por nível.
        - 📰 **Notícias:** em cada notícia, botões para **resumir, classificar o sentimento, perguntar e gerar relatório**
          com um modelo de linguagem que roda no seu computador.
        - 📂 **Upload e Download:** complementa os dados com CSVs no formato do InfoDengue.
        - 🔌 **API FastAPI:** os mesmos dados e a IA, disponíveis por rotas HTTP.

        **ODS:** 3 (Saúde e Bem-Estar), 11 (Cidades Sustentáveis), 17 (Parcerias e dados abertos).
        """
    )
with c2:
    st.info("**Público-alvo (fictício)**\n\nPerfis hipotéticos de gestor de saúde pública e morador local, "
            "sem contato ou validação com órgãos públicos reais.")
    st.warning("As respostas da IA podem conter erros. Confira sempre a notícia original.")

st.subheader("Fontes e referências")
st.markdown(
    "- [InfoDengue — API pública](https://info.dengue.mat.br/)\n"
    "- [NSC Total — notícias sobre Dengue](https://www.nsctotal.com.br/tag/dengue)\n"
    "- [Modelo: Qwen3-4B-Instruct-2507 (GGUF)](https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF)"
)
