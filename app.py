import streamlit as st
import pdfplumber
import re

st.title("Revisor Automático de Provas (Colégio Êxodo)")

st.markdown("""
Envie o PDF da prova para uma análise automática:<br>
- Entre 15 e 20 questões;<br>
- Cada questão deve ter exatamente 5 alternativas rotuladas (a)-(e) ou A)-E);<br>
- Questões contextualizadas;<br>
- Alternativas não repetidas.
""", unsafe_allow_html=True)

def extrair_texto_pdf(pdf_file):
    texto = ''
    with pdfplumber.open(pdf_file) as pdf:
        for pagina in pdf.pages:
            page_text = pagina.extract_text()
            if page_text:
                texto += page_text + '\n'
    return texto

def checar_alternativas(questao):
    # Aceita (a), (A), a), A), a., A., a-, A-, etc.
    alternativas = re.findall(
        r'[\(\[]?\s*([a-eA-E])\s*[\)\]\.\-:]|([a-eA-E])\)', questao)
    # O findall acima retorna uma lista de tuplas, precisamos pegar o grupo correto
    alternativas = [a or b for a, b in alternativas]
    alternativas = [alt.lower() for alt in alternativas]
    set_esperado = {'a', 'b', 'c', 'd', 'e'}
    set_encontrado = set(alternativas)
    if len(alternativas) < 5:
        faltando = set_esperado - set_encontrado
        return f"Só tem {len(alternativas)} alternativa(s). Faltando: {', '.join(sorted(faltando))}."
    if len(alternativas) > 5:
        return "Tem mais de cinco alternativas."
    if len(set_encontrado) != 5:
        repetidas = [x for x in alternativas if alternativas.count(x) > 1]
        return f"Alternativas repetidas: {', '.join(sorted(set(repetidas)))}."
    return None

def analisar_prova(texto):
    status = "APROVADA ✅"
    relatorio = []
    padrao_questao = re.compile(r'(?:Questão|Questao|Q)\s*\d+.*?(?=(?:Questão|Questao|Q)\s*\d+|$)', re.DOTALL | re.IGNORECASE)
    questoes = padrao_questao.findall(texto)
    if not (15 <= len(questoes) <= 20):
        relatorio.append(f"Número de questões fora do padrão: {len(questoes)} (deve ter entre 15 e 20).")
        status = "REVISAR ❌"
    for idx, q in enumerate(questoes):
        erro_alt = checar_alternativas(q)
        if erro_alt:
            relatorio.append(f"Questão {idx+1}: {erro_alt}")
            status = "REVISAR ❌"
        # Checagem simples de contextualização (adapte os termos se quiser)
        if not re.search(r'(situa[cç][ãa]o|contexto|hist[oó]ria|caso|cen[aá]rio|exemplo|baseado)', q, re.IGNORECASE):
            relatorio.append(f"Questão {idx+1}: Pode faltar contextualização.")
            status = "REVISAR ❌"
    return status, relatorio

pdf_file = st.file_uploader("Envie o PDF da prova", type=["pdf"])

if pdf_file:
    st.info("Extraindo texto do PDF...")
    texto = extrair_texto_pdf(pdf_file)
    status, relatorio = analisar_prova(texto)
    st.subheader("Diagnóstico automático:")
    if status == "APROVADA ✅":
        st.success("APROVADA ✅ Sua prova está de acordo com todos os critérios!")
    else:
        st.error("REVISAR ❌ Sua prova apresenta pendências:")
        for item in relatorio:
            st.write(item)

    with st.expander("Mostrar texto extraído do PDF"):
        st.write(texto)
