import base64
import io
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

COLUNAS_ENTRADA = ['age', 'trestbps', 'chol', 'thalach']
NOMES_CAMPOS = ['Idade (anos)', 'Pressão em repouso (mmHg)', 'Colesterol (mg/dL)', 'Frequência máxima (bpm)']
LIMITES_CAMPOS = [(1, 120), (1, 350), (1, 1000), (1, 300)]

# Lê o arquivo enviado. Aceita vírgula ou ponto e vírgula como separador.
def abrir_csv(conteudo):
    if not conteudo.strip():
        raise ValueError('Arquivo vazio.')

    try:
        texto = conteudo.decode('utf-8-sig')
        separador = ','
        if ';' in texto.splitlines()[0]:
            separador = ';'
        return pd.read_csv(io.StringIO(texto), sep=separador, na_values=['?'])
    except (UnicodeError, ValueError, pd.errors.ParserError) as erro:
        raise ValueError('CSV inválido. Use UTF-8 e separador vírgula ou ponto e vírgula.') from erro


# O CSV do Kaggle mistura vários centros. Aqui ficamos só com Cleveland.
def selecionar_cleveland(dados):
    if 'dataset' in dados.columns:
        centros = dados['dataset'].astype(str).str.strip().str.lower()
        dados = dados[centros == 'cleveland'].copy()

    # No Kaggle, a frequência máxima vem com outro nome.
    if 'thalch' in dados.columns and 'thalach' not in dados.columns:
        dados = dados.rename(columns={'thalch': 'thalach'})
    return dados


# Confere se as colunas necessárias existem e se os valores fazem sentido.
def validar_colunas(dados):
    obrigatorias = COLUNAS_ENTRADA + ['num']
    for coluna in obrigatorias:
        if coluna not in dados.columns:
            raise ValueError('Colunas obrigatórias: ' + ', '.join(obrigatorias))

    if dados.empty:
        raise ValueError('CSV sem registros.')

    dados = dados[obrigatorias].copy()
    for coluna in obrigatorias:
        numeros = pd.to_numeric(dados[coluna], errors='coerce')
        texto_invalido = dados[coluna].notna() & numeros.isna()
        if texto_invalido.any():
            raise ValueError('Valor não numérico em ' + coluna)
        dados[coluna] = numeros

    resultados = dados['num'].dropna()
    if not resultados.isin([0, 1, 2, 3, 4]).all():
        raise ValueError('num deve ser inteiro entre 0 e 4.')

    for coluna, limites in zip(COLUNAS_ENTRADA, LIMITES_CAMPOS):
        minimo, maximo = limites
        valores = dados[coluna].dropna()
        if not valores.between(minimo, maximo).all():
            raise ValueError('Valor incompatível em ' + coluna)
    return dados


# Remove repetições e linhas sem resultado. Guarda as contagens para mostrar na página.
def limpar_dados(dados, resumo):
    resumo['alvos_ausentes'] = int(dados['num'].isna().sum())
    dados = dados.dropna(subset=['num'])

    resumo['duplicatas'] = int(dados.duplicated().sum())
    dados = dados.drop_duplicates()
    if len(dados) < 2:
        raise ValueError('São necessários pelo menos dois registros válidos distintos.')

    for coluna in COLUNAS_ENTRADA:
        if dados[coluna].isna().all():
            raise ValueError('Uma variável de entrada está totalmente vazia.')

    resumo['depois'] = len(dados)
    resumo['ausentes'] = dados.isna().sum().to_dict()
    # Ausência vira 0; presença (num de 1 a 4) vira 1.
    dados['alvo'] = (dados['num'] > 0).astype(int)
    return dados


# Junta as etapas: abrir o CSV, selecionar Cleveland, validar e limpar os dados.
def ler(conteudo_arquivo):
    dados = abrir_csv(conteudo_arquivo)
    recebidos = len(dados)
    dados = selecionar_cleveland(dados)

    resumo = {
        'recebidos': recebidos,
        'fora_cleveland': recebidos - len(dados),
        'antes': len(dados),
        'colunas': len(dados.columns),
        'tipos_originais': dados.dtypes.astype(str).to_dict(),
        'ausentes_originais': dados.isna().sum().to_dict(),
    }
    dados = validar_colunas(dados)
    dados = limpar_dados(dados, resumo)
    return dados, resumo


# Prepara o visual que os três gráficos usam: fundo, títulos e eixos.
def criar_grafico(titulo, nome_eixo_x, nome_eixo_y):
    figura = Figure(figsize=(9, 4.6), dpi=150, layout='constrained', facecolor='#e7e5df')
    eixo = figura.subplots()
    eixo.set_facecolor('#e7e5df')
    eixo.set_title(titulo, loc='left', fontsize=15, pad=20, color='#383a37')
    eixo.set_xlabel(nome_eixo_x, fontsize=11, labelpad=10)
    eixo.set_ylabel(nome_eixo_y, fontsize=11, labelpad=10)
    eixo.tick_params(colors='#53564f', labelsize=10, length=0, pad=8)
    for lado in ['top', 'right']:
        eixo.spines[lado].set_visible(False)
    for lado in ['bottom', 'left']:
        eixo.spines[lado].set_color('#b9bab2')
    eixo.grid(axis='y', color='#c8c9c1', linewidth=0.6)
    eixo.set_axisbelow(True)
    return (figura, eixo)

# Transforma o gráfico em uma imagem que pode ser colocada na página.
def imagem_do_grafico(figura):
    # O HTML recebe a imagem como texto, sem criar arquivos temporários.
    imagem = io.BytesIO()
    figura.savefig(imagem, format='png', bbox_inches='tight')
    return base64.b64encode(imagem.getvalue()).decode()


# Conta quantos registros existem em cada faixa de idade e monta as barras.
def grafico_por_idade(dados):
    # Gráfico 1: quantidade de registros por faixa de idade.
    faixas_etarias = pd.cut(dados.age, bins=[0, 39, 49, 59, 69, 120], labels=['Até 39', '40–49', '50–59', '60–69', '70 ou mais'])
    quantidade_por_faixa = faixas_etarias.value_counts(sort=False)
    figura, eixo = criar_grafico('Quantos registros há em cada faixa etária?', 'Faixa etária (anos)', 'Número de registros')
    barras = eixo.bar(quantidade_por_faixa.index.astype(str), quantidade_por_faixa.values, color='#657362', width=0.6)
    eixo.bar_label(barras, padding=6, fontsize=11)
    eixo.set_ylim(0, max(quantidade_por_faixa.max() * 1.2, 1))
    eixo.yaxis.set_major_locator(MaxNLocator(integer=True))
    return imagem_do_grafico(figura), quantidade_por_faixa

# Compara a quantidade de registros com e sem doença registrada.
def grafico_por_resultado(dados):
    # Gráfico 2: quantidade com e sem doença registrada.
    quantidade_por_grupo = dados.alvo.value_counts().reindex([0, 1], fill_value=0)
    figura, eixo = criar_grafico('Quantos têm presença de doença registrada?', 'Resultado registrado na base', 'Número de registros')
    barras = eixo.bar(['Ausência registrada', 'Presença registrada'], quantidade_por_grupo, width=0.5, color=['#657362', '#a16e55'])
    rotulos = []
    for quantidade in quantidade_por_grupo:
        porcentagem = quantidade / len(dados)
        rotulo = f'{quantidade} ({porcentagem:.1%})'
        rotulos.append(rotulo.replace('.', ','))
    eixo.bar_label(barras, labels=rotulos, padding=8, fontsize=11)
    eixo.set_ylim(0, max(quantidade_por_grupo.max() * 1.23, 1))
    eixo.yaxis.set_major_locator(MaxNLocator(integer=True))
    return imagem_do_grafico(figura), quantidade_por_grupo

# Compara a média da frequência máxima no exercício entre os dois grupos.
def grafico_frequencia(dados):
    # Gráfico 3: frequência máxima média em cada grupo.
    media_por_grupo = dados.groupby('alvo').thalach.mean().reindex([0, 1])
    medidas_por_grupo = dados.groupby('alvo').thalach.count().reindex([0, 1], fill_value=0)
    figura, eixo = criar_grafico('Como a frequência máxima varia entre os grupos?', 'Resultado registrado na base', 'Frequência máxima média (bpm)')
    barras = eixo.bar(['Ausência registrada', 'Presença registrada'], media_por_grupo.fillna(0), width=0.5, color=['#657362', '#a16e55'])
    rotulos = []
    for media in media_por_grupo:
        rotulo = 'Sem dados'
        if pd.notna(media):
            rotulo = f'{media:.1f} bpm'.replace('.', ',')
        rotulos.append(rotulo)
    eixo.bar_label(barras, labels=rotulos, padding=8, fontsize=11)
    eixo.set_ylim(0, max(float(media_por_grupo.max()) * 1.25, 1))
    return imagem_do_grafico(figura), media_por_grupo, medidas_por_grupo

# Monta as frases abaixo dos gráficos usando os números do CSV analisado.
def explicar_graficos(quantidade_por_faixa, quantidade_por_grupo, media_por_grupo, medidas_por_grupo):
    faixa_mais_comum = quantidade_por_faixa.idxmax()
    frases = []
    for codigo, grupo in [(0, 'Ausência'), (1, 'Presença')]:
        media = media_por_grupo[codigo]
        quantidade = medidas_por_grupo[codigo]
        if pd.isna(media):
            frase = f'{grupo}: sem medidas disponíveis'
        else:
            frase = f'{grupo}: {media:.1f} bpm ({quantidade} medidas válidas)'
            frase = frase.replace('.', ',')
        frases.append(frase)
    comparacao = '; '.join(frases)

    interpretacoes = [
        f'A faixa com mais registros é {faixa_mais_comum} anos, com {quantidade_por_faixa.max()} casos. Idades ausentes não entram neste gráfico.',
        f'A base contém {quantidade_por_grupo[0]} registros de ausência e {quantidade_por_grupo[1]} de presença. Esses números descrevem esta amostra, não a população em geral.',
        comparacao + '. As barras mostram médias, não todos os valores individuais. A diferença não demonstra causa nem permite diagnóstico.',
    ]
    return interpretacoes


# Gera os três gráficos e suas explicações para a página de análise.
def analisar(dados):
    grafico_idades, idades = grafico_por_idade(dados)
    grafico_classes, grupos = grafico_por_resultado(dados)
    grafico_medias, medias, quantidades = grafico_frequencia(dados)

    graficos = [grafico_idades, grafico_classes, grafico_medias]
    explicacoes = explicar_graficos(idades, grupos, medias, quantidades)
    return graficos, explicacoes


# Monta a amostra e o resumo das medidas, com os nomes das colunas em português.
def tabelas_simples(dados):
    """Tradução apenas para exibição: preserva o esquema usado pelo modelo."""
    nomes = dict(zip(COLUNAS_ENTRADA, NOMES_CAMPOS))
    amostra = dados[COLUNAS_ENTRADA + ['alvo']].head(10).copy()
    amostra['alvo'] = amostra['alvo'].map({0: 'Ausência registrada', 1: 'Presença registrada'})
    amostra = amostra.rename(columns={**nomes, 'alvo': 'Resultado na base'})
    resumo = dados[COLUNAS_ENTRADA].agg(['mean', 'min', 'max']).T
    resumo.columns = ['Média', 'Menor valor', 'Maior valor']
    resumo.index = resumo.index.map(nomes)
    resumo.index.name = None
    # Mostra uma casa decimal e usa vírgula, como em 54,4.
    def formatar_numero(valor):
        return f'{valor:.1f}'.replace('.', ',')
    tabela_amostra = amostra.to_html(
        index=False,
        classes='table',
        float_format=formatar_numero,
        na_rep='Não informado',
    )
    tabela_resumo = resumo.to_html(
        classes='table',
        float_format=formatar_numero,
        na_rep='Não informado',
    )
    return tabela_amostra, tabela_resumo
