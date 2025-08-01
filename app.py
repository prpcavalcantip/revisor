import streamlit as st
import pdfplumber
import re

def extrair_texto_pdf(pdf_file):
    texto = ''
    with pdfplumber.open(pdf_file) as pdf:
        for pagina in pdf.pages:
            texto += pagina.extract_text() + '\n'
    return texto

def analisar_prova(texto):
    relatorio = []
    # Contagem de questões (simples: "Questão" ou "Q." ou "Q ")
    questoes = re.findall(r'(?i)(quest(ã|a)o\s*\d+|q[\.\s]\s*\d+)', texto)
    num_questoes = len(questoes)

    if num_questoes < 15 or num_questoes > 20:
        relatorio.append(f"Número de questões fora do padrão: {num_questoes} (deve ter entre 15 e 20).")

    # Cada questão deve ser de múltipla escolha e ter 5 alternativas (a-e)
    padrao_questao = re.compile(r'(Quest(ã|a)o\s*\d+|Q[\.\s]\s*\d+)(.*?)(?=Quest(ã|a)o\s*\d+|Q[\.\s]\s*\d+|$)', re.DOTALL | re.IGNORECASE)
    questoes_textos = padrao_questao.findall(texto)
    for idx, q in enumerate(questoes_textos):
        enunciado = q[2]
        alternativas = re.findall(r'\([a-eA-E]\)', enunciado)
        if len(alternativas) != 5:
            relatorio.append(f"Questão {idx+1}: não tem 5 alternativas (a-e).")
        if len(set(alternativas)) != len(alternativas):
            relatorio.append(f"Questão {idx+1}: alternativas repetidas.")
        # Contexto mínimo
        if not re.search(r'(situa[cç][ãa]o|contexto|hist[oó]ria|caso|cen[aá]rio|exemplo|baseado)', enunciado, re.IGNORECASE):
            relatorio.append(f"Questão {idx+1}: pode faltar contextualização.")
        # Gráfico/figura
        if re.search(r'(gr[aá]fico|imagem|figura|tabela|diagrama)', enunciado, re.IGNORECASE):
            if not re.search(r'(imagem|figura|tabela|diagrama|gr[aá]fico)\s*(\d+)?', texto):
                relatorio.append(f"Questão {idx+1}: menciona gráfico/imagem, mas pode não estar presente.")
    # Diagnóstico final
    if not relatorio:
        return "APROVADA ✅", []
    else:
        return "REVISAR ❌", relatorio

st.title("Diagnóstico Automático de Provas por PDF - Colégio Êxodo")

st.markdown("""
Faça upload do PDF da prova. O sistema vai diagnosticar automaticamente:
- Quantidade de questões (15 a 20)
- Todas as questões de múltipla escolha, com 5 alternativas (a-e)
- Sem alternativas repetidas
- Questões contextualizadas
- Se menciona gráfico/imagem, verifica se está presente
""")

pdf_file = st.file_uploader("Envie o PDF da prova", type=["pdf"])

if pdf_file:
    st.info("Processando o PDF...")
    texto_prova = extrair_texto_pdf(pdf_file)
    status, relatorio = analisar_prova(texto_prova)
    st.subheader("Diagnóstico da Prova:")
    if status == "APROVADA ✅":
        st.success("APROVADA ✅ Sua prova está de acordo com todos os critérios!")
    else:
        st.error("REVISAR ❌ Sua prova apresenta pendências:")
        for item in relatorio:
            st.write("-", item)

    st.markdown("----")
    st.markdown("**Visualização do texto extraído (opcional):**")
    with st.expander("Mostrar texto extraído do PDF"):
        st.write(texto_prova)
