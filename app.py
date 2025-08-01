import streamlit as st
import pdfplumber
import re
import openai

# Obtenha a chave da OpenAI dos secrets do Streamlit Cloud
openai.api_key = st.secrets["openai_api_key"]

st.title("Diagnóstico Automático de Provas por PDF - Colégio Êxodo")

st.markdown("""
Faça upload do PDF da prova. O sistema irá diagnosticar automaticamente:
- Quantidade de questões (15 a 20)
- Cada questão deve ter exatamente 5 alternativas identificadas como (a), (b), (c), (d), (e)
- Sem alternativas repetidas
- Questões contextualizadas
- Caso deseje, análise de IA com ChatGPT
""")

def extrair_texto_pdf(pdf_file):
    texto = ''
    with pdfplumber.open(pdf_file) as pdf:
        for pagina in pdf.pages:
            page_text = pagina.extract_text()
            if page_text:
                texto += page_text + '\n'
    return texto

def checar_alternativas_personalizado(enunciado):
    # Busca alternativas (a)-(e) ou (A)-(E)
    alternativas = re.findall(r'\(([a-eA-E])\)', enunciado)
    alternativas = [alt.lower() for alt in alternativas]
    set_esperado = {'a', 'b', 'c', 'd', 'e'}
    set_encontrado = set(alternativas)

    if len(alternativas) < 5:
        faltando = set_esperado - set_encontrado
        if len(alternativas) == 4:
            return f"Só tem quatro alternativas. Faltando: {', '.join(sorted(faltando))}."
        elif len(alternativas) == 3:
            return f"Só tem três alternativas. Faltando: {', '.join(sorted(faltando))}."
        elif len(alternativas) == 2:
            return f"Só tem duas alternativas. Faltando: {', '.join(sorted(faltando))}."
        elif len(alternativas) == 1:
            return f"Só tem uma alternativa. Faltando: {', '.join(sorted(faltando))}."
        else:
            return f"Faltam as alternativas: {', '.join(sorted(faltando))}."
    elif len(alternativas) > 5:
        return "Tem mais de cinco alternativas."
    elif len(set_encontrado) != 5:
        repetidas = [x for x in alternativas if alternativas.count(x) > 1]
        return f"Alternativas repetidas: {', '.join(sorted(set(repetidas)))}."
    else:
        return None  # Está correto

def analisar_prova(texto):
    relatorio = []
    questoes = re.findall(r'(?i)(quest(ã|a)o\s*\d+|q[\.\s]\s*\d+)', texto)
    num_questoes = len(questoes)

    if num_questoes < 15 or num_questoes > 20:
        relatorio.append(f"Número de questões fora do padrão: {num_questoes} (deve ter entre 15 e 20).")

    # Divide o texto em blocos por questão
    padrao_questao = re.compile(r'(Quest(ã|a)o\s*\d+|Q[\.\s]\s*\d+)(.*?)(?=Quest(ã|a)o\s*\d+|Q[\.\s]\s*\d+|$)', re.DOTALL | re.IGNORECASE)
    questoes_textos = padrao_questao.findall(texto)

    for idx, q in enumerate(questoes_textos):
        enunciado = q[2]
        erro_alt = checar_alternativas_personalizado(enunciado)
        if erro_alt:
            relatorio.append(f"Questão {idx+1}: {erro_alt}")

        # Contextualização
        if not re.search(r'(situa[cç][ãa]o|contexto|hist[oó]ria|caso|cen[aá]rio|exemplo|baseado)', enunciado, re.IGNORECASE):
            relatorio.append(f"Questão {idx+1}: Pode faltar contextualização.")

        # Gráfico/figura
        if re.search(r'(gr[aá]fico|imagem|figura|tabela|diagrama)', enunciado, re.IGNORECASE):
            if not re.search(r'(imagem|figura|tabela|diagrama|gr[aá]fico)\s*(\d+)?', texto):
                relatorio.append(f"Questão {idx+1}: Menciona gráfico/imagem, mas pode não estar presente.")

    if not relatorio:
        return "APROVADA ✅", []
    else:
        return "REVISAR ❌", relatorio

def analisar_ia(texto):
    st.info("Enviando para análise do ChatGPT...")
    prompt = (
        "Você é um avaliador de provas. Analise o texto da seguinte prova e avalie se está de acordo com os critérios: "
        "1) Ter entre 15 e 20 questões; 2) Cada questão deve ter exatamente 5 alternativas identificadas como (a), (b), (c), (d), (e); "
        "3) Sem alternativas repetidas; 4) Questões devem ser contextualizadas; 5) Se houver menção a gráfico/figura, verifique se está presente. "
        "Dê um diagnóstico geral ('Aprovada' ou 'Revisar') e, se necessário, liste as correções necessárias. Texto da prova:\n"
        + texto
    )
    resposta = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Você é um especialista em avaliação de provas."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )
    return resposta.choices[0].message['content']

pdf_file = st.file_uploader("Envie o PDF da prova", type=["pdf"])

if pdf_file:
    st.info("Processando o PDF...")
    texto_prova = extrair_texto_pdf(pdf_file)
    status, relatorio = analisar_prova(texto_prova)
    st.subheader("Diagnóstico automático da Prova:")
    if status == "APROVADA ✅":
        st.success("APROVADA ✅ Sua prova está de acordo com todos os critérios!")
    else:
        st.error("REVISAR ❌ Sua prova apresenta pendências:")
        for item in relatorio:
            st.write(item)

    st.markdown("----")
    st.markdown("**Análise opcional com ChatGPT:**")
    if st.button("Analisar com ChatGPT"):
        resultado_ia = analisar_ia(texto_prova)
        st.info(resultado_ia)

    st.markdown("----")
    st.markdown("**Visualização do texto extraído (opcional):**")
    with st.expander("Mostrar texto extraído do PDF"):
        st.write(texto_prova)
