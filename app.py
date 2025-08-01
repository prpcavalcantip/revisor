import streamlit as st
import re

# Funções de checagem
def menciona_grafico_ou_imagem(texto):
    return bool(re.search(r'(gr[aá]fico|imagem|figura|tabela|diagrama)', texto, re.IGNORECASE))

def tem_contexto(texto):
    # Checagem simples: procura palavras indicativas de contexto
    return bool(re.search(r'(situa[cç][ãa]o|contexto|hist[oó]ria|caso|cen[aá]rio|exemplo|baseado)', texto, re.IGNORECASE))

def revisar_questao(q, idx):
    relatorio = []
    alternativas = [a.strip() for a in q['alternativas'] if a.strip()]
    if len(alternativas) != 5:
        relatorio.append(f"Questão {idx+1}: número de alternativas diferente de 5.")
    if len(set(alternativas)) != 5:
        relatorio.append(f"Questão {idx+1}: alternativas repetidas.")
    if not tem_contexto(q['enunciado']):
        relatorio.append(f"Questão {idx+1}: falta contextualização.")
    if menciona_grafico_ou_imagem(q['enunciado']) and not q['tem_imagem']:
        relatorio.append(f"Questão {idx+1}: menciona gráfico/imagem, mas não está presente.")
    # Simulação de checagem de gramática, ortografia e fluência
    if len(q['enunciado'].split()) < 8:
        relatorio.append(f"Questão {idx+1}: enunciado muito curto (pode prejudicar a fluência/contexto).")
    return relatorio

st.set_page_config(page_title="Revisor de Provas - Colégio Êxodo", layout="wide")
st.title("📝 Revisor de Provas - Colégio Êxodo")

st.markdown("""
Este aplicativo revisa automaticamente provas de múltipla escolha dos professores, analisando:
- Quantidade de questões (mínimo 15, máximo 20)
- Gramática, ortografia e fluência do enunciado (simulação)
- Todas as questões são de múltipla escolha e possuem 5 alternativas (a-e)
- Questões contextualizadas
- Não pode haver alternativas repetidas
- Se o enunciado mencionar gráfico/figura, a imagem deve estar presente
""")

with st.form("prova_form"):
    num_q = st.number_input("Quantidade de questões", min_value=1, max_value=30, value=15)
    questoes = []
    for i in range(num_q):
        st.markdown(f"---\n### Questão {i+1}")
        enunciado = st.text_area(f"Enunciado da questão {i+1}", key=f"enun_{i}")
        alternativas = []
        cols = st.columns(5)
        for j, letra in enumerate(['a', 'b', 'c', 'd', 'e']):
            alternativas.append(cols[j].text_input(f"{letra})", key=f"{i}_{letra}"))
        tem_imagem = st.checkbox("Possui gráfico/figura/imagem?", key=f"img{i}")
        questoes.append({
            "enunciado": enunciado,
            "alternativas": alternativas,
            "tem_imagem": tem_imagem
        })
    enviar = st.form_submit_button("Revisar Prova")

if enviar:
    relatorio_global = []
    if not (15 <= num_q <= 20):
        relatorio_global.append("A prova deve ter entre 15 e 20 questões.")
    for idx, q in enumerate(questoes):
        relatorio_global += revisar_questao(q, idx)
    st.markdown("## Resultado da Revisão")
    if not relatorio_global:
        st.success("APROVADO ✅ Sua prova está de acordo com todos os critérios!")
    else:
        st.error("REVISAR ❌ Sua prova apresenta pendências:")
        for item in relatorio_global:
            st.write("-", item)
