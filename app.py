<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Revisão de Provas - Colégio Êxodo</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.9.359/pdf.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/mammoth/1.4.17/mammoth.browser.min.js"></script>
</head>
<body class="bg-gray-100 flex items-center justify-center min-h-screen">
  <div class="bg-white p-8 rounded-lg shadow-lg w-full max-w-2xl">
    <h1 class="text-2xl font-bold mb-6 text-center">Revisão de Provas - Colégio Êxodo</h1>
    <div class="mb-4">
      <label class="block text-sm font-medium text-gray-700">Carregar Prova (PDF ou DOCX)</label>
      <input type="file" id="fileInput" accept=".pdf,.docx" class="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100">
    </div>
    <button id="analyzeBtn" class="w-full bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600 disabled:bg-gray-400" disabled>Analisar Prova</button>
    <div id="result" class="mt-6 hidden">
      <h2 class="text-xl font-semibold mb-4">Resultado da Análise</h2>
      <p id="status" class="text-lg font-medium"></p>
      <ul id="suggestions" class="list-disc pl-5 mt-2"></ul>
    </div>
  </div>

  <script>
    const fileInput = document.getElementById('fileInput');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const resultDiv = document.getElementById('result');
    const statusP = document.getElementById('status');
    const suggestionsUl = document.getElementById('suggestions');

    fileInput.addEventListener('change', () => {
      analyzeBtn.disabled = !fileInput.files.length;
    });

    analyzeBtn.addEventListener('click', async () => {
      const file = fileInput.files[0];
      if (!file) return;

      let text;
      try {
        if (file.name.endsWith('.pdf')) {
          text = await parsePDF(file);
        } else if (file.name.endsWith('.docx')) {
          text = await parseDOCX(file);
        } else {
          alert('Formato de arquivo inválido. Use PDF ou DOCX.');
          return;
        }
      } catch (e) {
        alert('Erro ao processar o arquivo. Verifique o formato.');
        return;
      }

      const prova = analyzeWithGrok(text);
      console.log('Prova extraída:', prova); // Para depuração
      const analysis = await analyzeProva(prova);
      displayResults(analysis);
    });

    async function parsePDF(file) {
      const arrayBuffer = await file.arrayBuffer();
      const pdf = await pdfjsLib.getDocument(arrayBuffer).promise;
      let text = '';
      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const content = await page.getTextContent();
        text += content.items.map(item => item.str).join(' ') + '\n';
      }
      return text;
    }

    async function parseDOCX(file) {
      const arrayBuffer = await file.arrayBuffer();
      const result = await mammoth.extractRawText({ arrayBuffer });
      return result.value;
    }

    function analyzeWithGrok(text) {
      // Normaliza o texto
      text = text.replace(/\r\n/g, '\n').replace(/\n\s*\n+/g, '\n\n').trim();
      const lines = text.split('\n').filter(line => line.trim());

      const questions = [];
      let currentQuestion = null;
      let expectingAlternatives = false;

      // Padrões para identificar questões e alternativas
      const questionPatterns = [
        /^Questão\s+\d+/i, // Ex.: "Questão 01"
        /^\d+\.\s*(?!\))/, // Ex.: "1. "
        /^\d+\)\s*/, // Ex.: "1) "
      ];
      const alternativeRegex = /^[A-E][\)\.]\s+/i; // Ex.: "A) ", "B. "

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();

        // Verifica se é uma nova questão
        const isQuestion = questionPatterns.some(pattern => pattern.test(line));
        if (isQuestion) {
          if (currentQuestion && currentQuestion.alternativas.length > 0) {
            questions.push(currentQuestion);
          }
          currentQuestion = {
            enunciado: line.replace(questionPatterns.find(pattern => pattern.test(line)), ''),
            alternativas: [],
            hasImage: /(gráfico|imagem|figura)/i.test(line)
          };
          expectingAlternatives = true;
        } else if (currentQuestion && alternativeRegex.test(line) && expectingAlternatives) {
          // Adiciona alternativa
          currentQuestion.alternativas.push(line.replace(alternativeRegex, ''));
          if (currentQuestion.alternativas.length === 5) {
            expectingAlternatives = false;
          }
        } else if (currentQuestion) {
          // Adiciona ao enunciado
          currentQuestion.enunciado += ' ' + line;
          currentQuestion.hasImage = currentQuestion.hasImage || /(gráfico|imagem|figura)/i.test(line);
        }
      }

      if (currentQuestion && currentQuestion.alternativas.length > 0) {
        questions.push(currentQuestion);
      }

      return { questions };
    }

    async function analyzeProva(prova) {
      const suggestions = [];
      let approved = true;

      // Verificar número de questões
      const numQuestions = prova.questions.length;
      if (numQuestions < 15 || numQuestions > 20) {
        suggestions.push(`Número de questões inválido (${numQuestions}). Deve ter entre 15 e 20 questões.`);
        approved = false;
      }

      // Verificar cada questão
      for (let index = 0; index < prova.questions.length; index++) {
        const q = prova.questions[index];
        const i = index + 1;

        // Verificar 5 alternativas
        if (q.alternativas.length !== 5) {
          suggestions.push(`Questão ${i}: Deve ter exatamente 5 alternativas (encontrado: ${q.alternativas.length}).`);
          approved = false;
        }

        // Verificar alternativas repetidas
        const uniqueAlts = new Set(q.alternativas.map(alt => alt.toLowerCase().trim()));
        if (uniqueAlts.size !== q.alternativas.length) {
          suggestions.push(`Questão ${i}: Contém alternativas repetidas ou idênticas.`);
          approved = false;
        }

        // Verificar gramática e ortografia com LanguageTool
        const grammarIssues = await checkGrammar(q.enunciado);
        if (grammarIssues.length) {
          suggestions.push(`Questão ${i}: Problemas de gramática/ortografia no enunciado: ${grammarIssues.join(', ')}.`);
          approved = false;
        }

        // Verificar fluência de texto
        if (q.enunciado.split(/\s+/).length < 10) {
          suggestions.push(`Questão ${i}: Enunciado muito curto, pode não ser suficientemente contextualizado.`);
          approved = false;
        }

        // Verificar contextualização
        if (!q.enunciado.includes(' ') || q.enunciado.length < 50) {
          suggestions.push(`Questão ${i}: Enunciado não parece contextualizado (muito curto ou sem detalhes).`);
          approved = false;
        }

        // Verificar menção a gráficos ou imagens
        if (/(gráfico|imagem|figura)/i.test(q.enunciado) && !q.hasImage) {
          suggestions.push(`Questão ${i}: Menciona gráfico/imagem, mas nenhum foi detectado.`);
          approved = false;
        }
      }

      return { approved, suggestions };
    }

    async function checkGrammar(text) {
      try {
        const response = await fetch('https://api.languagetool.org/v2/check', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          },
          body: new URLSearchParams({
            'language': 'pt-BR',
            'text': text
          })
        });
        const data = await response.json();
        return data.matches.map(match => {
          const suggestion = match.replacements.length > 0 ? match.replacements[0].value : 'sem sugestão';
          return `${match.message} (encontrado: "${match.context.text.slice(match.context.offset, match.context.offset + match.context.length)}", sugerido: "${suggestion}")`;
        });
      } catch (e) {
        console.error('Erro ao chamar LanguageTool API:', e);
        return ['Erro ao verificar gramática. Tente novamente mais tarde.'];
      }
    }

    function displayResults({ approved, suggestions }) {
      resultDiv.classList.remove('hidden');
      statusP.textContent = approved ? 'Aprovado' : 'Revisar';
      statusP.classList.toggle('text-green-600', approved);
      statusP.classList.toggle('text-red-600', !approved);

      suggestionsUl.innerHTML = '';
      if (suggestions.length) {
        suggestions.forEach(s => {
          const li = document.createElement('li');
          li.textContent = s;
          suggestionsUl.appendChild(li);
        });
      } else {
        const li = document.createElement('li');
        li.textContent = 'Nenhuma sugestão de revisão.';
        suggestionsUl.appendChild(li);
      }
    }
  </script>
</body>
</html>
