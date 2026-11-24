import streamlit as st

st.title("📌 Sobre o projeto")
st.caption("Projeto de Bloco · Ciência de Dados Aplicada · alinhado ao ODS 3 (Saúde e Bem-Estar)")

c1, c2 = st.columns([2, 1])
with c1:
    st.markdown(
        """
        **Problema:** a dengue é um problema de saúde pública crescente no Sul do Brasil, e os dados sobre ela existem, mas
        exigem conhecimento técnico para serem consultados e interpretados — e quase não se sabe **o que a população está sendo levada a sentir** sobre o assunto.

        **O que o projeto faz:**
        - 📡 **Dados reais do InfoDengue** (Joinville/SC): casos por semana epidemiológica e nível de alerta. O InfoDengue já consolida
          notificações do SINAN, dados climáticos e estimativas populacionais do IBGE.
        - 📰 **A mídia como fonte:** notícias reais coletadas por *web scraping* e classificadas por uma IA local quanto à **preocupação** que transmitem
          (análise de sentimento), um indicador indireto da preocupação veiculada à população.
        - 💬 **Dados em linguagem natural:** qualquer pessoa pode perguntar *“qual foi o ano com mais casos?”* e receber uma resposta baseada nos dados,
          sem saber programar — democratizando o acesso à informação.

        **ODS:** 3 (Saúde e Bem-Estar, meta 3.3) · 16 (meta 16.10: acesso público à informação) · 17 (parcerias e dados abertos).
        """
    )
with c2:
    st.info("**Público-alvo (fictício)**\n\nGestores de saúde pública e moradores interessados em entender a dengue em Joinville, "
            "sem vínculo com órgãos públicos reais.")
    st.warning("As respostas da IA podem conter erros. Os números, porém, são **calculados em código** a partir dos dados do InfoDengue.")

st.subheader("Fontes e referências")
st.markdown(
    "- [InfoDengue — API pública](https://info.dengue.mat.br/)\n"
    "- [NSC Total — notícias sobre Dengue](https://www.nsctotal.com.br/tag/dengue)\n"
    "- [Modelo de IA: Qwen3-4B-Instruct-2507 (GGUF)](https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF)"
)
