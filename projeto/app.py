from pathlib import Path
import json
import uuid
from flask import Flask, render_template, request
from dados import ler, analisar, tabelas_simples, COLUNAS_ENTRADA, NOMES_CAMPOS, LIMITES_CAMPOS
from modelo import prever

# Onde ficam os arquivos que este código precisa abrir ou salvar.
ARQUIVO_DADOS = Path(__file__).resolve().with_name('data') / 'cleveland.csv'
ARQUIVO_AVALIACAO = Path(__file__).resolve().with_name('models') / 'avaliacao.json'
PASTA_UPLOADS = Path(__file__).resolve().with_name('uploads')

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

@app.route('/')
# Abre a página inicial, onde dá para enviar um CSV ou usar a base incluída.
def index():
    return render_template('index.html')

@app.route('/analise', methods=['GET', 'POST'])
# Analisa o arquivo enviado. Se não houver upload, usa o CSV que já vem no projeto.
def analise():
    try:
        arquivo_csv = ARQUIVO_DADOS.read_bytes()
        fonte = 'Cleveland incluído no projeto'
        if request.method == 'POST':
            arquivo = request.files.get('arquivo')
            if not arquivo or not arquivo.filename or (not arquivo.filename.lower().endswith('.csv')):
                raise ValueError('Selecione um arquivo .csv.')
            arquivo_csv = arquivo.read()
            fonte = arquivo.filename
        dados, info = ler(arquivo_csv)
        if request.method == 'POST':
            PASTA_UPLOADS.mkdir(exist_ok=True)
            # Cada envio recebe um nome próprio para não sobrescrever outro arquivo.
            identificador = uuid.uuid4().hex
            (PASTA_UPLOADS / (identificador + '.csv')).write_bytes(arquivo_csv)
            (PASTA_UPLOADS / (identificador + '.json')).write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
        graficos, interpretacoes = analisar(dados)
        amostra, estatisticas = tabelas_simples(dados)
        return render_template('analise.html', info=info, plots=graficos, findings=interpretacoes, source=fonte, sample=amostra, stats=estatisticas)
    except ValueError as e:
        return (render_template('index.html', error=str(e)), 400)

@app.route('/avaliacao')
# Lê os resultados salvos no treinamento e mostra a comparação dos modelos.
def avaliacao():
    avaliacao = json.loads(ARQUIVO_AVALIACAO.read_text(encoding='utf-8'))
    return render_template('avaliacao.html', r=avaliacao)

@app.route('/previsao', methods=['GET', 'POST'])
# Recebe os valores do formulário e mostra a resposta do modelo treinado.
def previsao():
    resultado = None
    erro = None
    if request.method == 'POST':
        try:
            resultado = prever(request.form)
        except ValueError as e:
            erro = str(e)
    return (render_template('previsao.html', fields=list(zip(COLUNAS_ENTRADA, NOMES_CAMPOS, LIMITES_CAMPOS)), result=resultado, error=erro), 400 if erro else 200)

@app.errorhandler(413)
# Mostra uma mensagem se o arquivo enviado passar do limite de 2 MB.
def grande(e):
    return (render_template('index.html', error='O limite é 2 MB por CSV.'), 413)
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
