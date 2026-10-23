import json

import streamlit as st

import common
import data_ops
from prompts import PROMPTS, VERSAO

st.title("🤖 Preparação para LLM")
st.caption("Nenhum modelo é chamado nesta etapa: aqui mapeamos dados → tarefas → prompts para a próxima entrega.")

st.subheader("Mapa de dados × tarefas")
st.table([
    {"Tarefa": v["titulo"], "Dados de entrada": v["dados_de_entrada"]} for v in PROMPTS.values()
])

corpus_path = data_ops.DATA_PROCESSED / "noticias_corpus.jsonl"
ctx_path = data_ops.DATA_PROCESSED / "contexto_infodengue.json"

st.subheader("Corpus preparado")
if corpus_path.exists():
    linhas = [json.loads(l) for l in corpus_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    c1, c2 = st.columns(2)
    c1.metric("Trechos (chunks)", len(linhas))
    c2.metric("Notícias", len({l["id_noticia"] for l in linhas}))
    st.dataframe([{k: l[k] for k in ("id_noticia", "chunk_id", "titulo", "texto")} for l in linhas])
    if ctx_path.exists():
        st.markdown("**Contexto numérico (InfoDengue)**")
        st.json(json.loads(ctx_path.read_text(encoding="utf-8")))
else:
    st.warning("Corpus ainda não gerado. Rode: `python Code/llm_prep/prepare_corpus.py`")

st.subheader(f"Templates de prompt (v{VERSAO})")
for chave, p in PROMPTS.items():
    with st.expander(p["titulo"]):
        st.code(p["template"], language="text")
