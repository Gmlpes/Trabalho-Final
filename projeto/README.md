# Doença cardíaca — Tema 11

Trabalho de Tópicos Especiais em Ciência da Computação. A aplicação permite analisar um CSV, visualizar gráficos e fazer uma previsão de presença ou ausência de doença cardíaca registrada.

## Grupo

- Guilherme Matos
- Lucas de Albuquerque
- Vitor Bruno


# Como usar

Na página inicial, escolha um CSV ou clique em Explorar a base incluída. A página de análise mostra o tratamento dos dados, três gráficos, uma amostra e um resumo das medidas.

Em Comparar modelos, aparecem os resultados do treinamento e os erros de cada modelo. Em Fazer previsão, preencha idade, pressão em repouso, colesterol e frequência máxima durante o exercício.

O upload muda a análise e os gráficos. O modelo continua usando o treinamento feito com cleveland.csv.

# Dados utilizados

Usamos o [Heart Disease do Kaggle](https://www.kaggle.com/datasets/redwankarimsony/heart-disease-data), que reúne dados de diferentes centros. O arquivo completo está em `data/heart_disease_uci_kaggle.csv` e tem 920 registros.

Selecionamos somente os registros identificados como Cleveland. Essa versão tem 304 registros, enquanto a publicação original da UCI informa 303. O projeto usa o recorte da versão Kaggle, salvo em `data/cleveland.csv`.

A pergunta do trabalho é: **idade, pressão em repouso, colesterol e frequência máxima no exercício ajudam a classificar presença ou ausência de doença registrada nessa base?**

# Leitura e limpeza

O upload aceita CSV em UTF-8, separado por vírgula ou ponto e vírgula, com ponto decimal e até 2 MB. As colunas necessárias são as cinco descritas acima; o arquivo completo do Kaggle também é aceito.

O código confere as colunas, os tipos e os valores ausentes. Arquivos vazios, textos em campos numéricos e valores incompatíveis geram uma mensagem de erro.

- Células vazias e `?` são tratadas como ausentes.
- Registros sem `num` são removidos porque não têm resultado conhecido.
- Linhas repetidas nas cinco colunas utilizadas são removidas.
- Uma entrada totalmente vazia é rejeitada.
- Os gráficos e as estatísticas ignoram medidas ausentes.
- No modelo, medidas ausentes recebem a mediana aprendida somente no treino.

Os limites de entrada são: idade de 1 a 120 anos, pressão de 1 a 350 mmHg, colesterol de 1 a 1000 mg/dL e frequência de 1 a 300 bpm. Esses limites servem para validar os dados, não para indicar valores saudáveis.

O CSV enviado é preservado em `uploads/`, junto de um resumo da limpeza. No recorte incluído, os 304 registros foram mantidos: não houve duplicatas nem valores ausentes nas cinco colunas usadas.

## Gráficos

1. Quantidade de registros por faixa de idade.
2. Quantidade de registros com presença e ausência de doença.
3. Média da frequência máxima no exercício em cada grupo.

Na base incluída, a faixa de 50 a 59 anos tem mais registros: 125. São 165 casos de ausência e 139 de presença. A frequência máxima média é de 158,5 bpm no grupo de ausência e 139,3 bpm no grupo de presença. Essas comparações descrevem a amostra e não demonstram uma relação de causa.

## Treinamento

Comparamos **regressão logística** e **Random Forest**. A regressão usa as medidas para estimar a classe. A floresta combina várias árvores de decisão e consegue representar relações não lineares entre as medidas.

A divisão é estratificada, com 80% para treino e 20% para teste, usando `random_state=42`: 243 registros para aprender e 61 para avaliar. O teste contém 33 casos de ausência e 28 de presença.

A regressão usa preenchimento pela mediana, padronização e até 2.000 iterações. A floresta usa preenchimento pela mediana, 200 árvores, profundidade máxima 5 e mínimo de 3 registros por folha. O preparo fica junto do modelo em um pipeline para ser repetido na previsão.

A escolha usa validação cruzada em cinco partes do treino. Comparamos a acurácia balanceada média, que dá o mesmo peso às duas classes. O teste fica separado dessa escolha. Os dois modelos usam a mesma divisão.

## Resultados

Os dois modelos foram testados nos mesmos 61 registros:

- Regressão logística: acertou 45 e errou 16, com 73,8% de acertos.
- Random Forest: acertou 44 e errou 17, com 72,1% de acertos.

Escolhemos a regressão logística porque ela teve o melhor resultado na validação feita com os dados de treino: 68,5%, contra 66,4% da Random Forest. Essa comparação dá o mesmo peso aos casos com e sem doença. Os dados de teste não foram usados para escolher o modelo.

Nos erros da regressão logística, 9 casos com doença foram classificados como ausência e 7 casos sem doença foram classificados como presença. Na Random Forest, foram 6 e 11, respectivamente. Ou seja, a floresta reconheceu mais casos com doença, mas também apontou presença em mais casos sem doença.

Os detalhes e as matrizes de confusão podem ser vistos na página de comparação dos modelos. Os resultados também ficam salvos em avaliacao.json

## Fontes e ferramentas

- [Heart Disease no Kaggle](https://www.kaggle.com/datasets/redwankarimsony/heart-disease-data): arquivo utilizado.
- [Heart Disease na UCI](https://archive.ics.uci.edu/dataset/45/heart+disease): origem dos dados, de Janosi, Steinbrunn, Pfisterer e Detrano (1988), DOI [10.24432/C52P4X](https://doi.org/10.24432/C52P4X). A UCI informa licença CC BY 4.0.
- [Flask](https://flask.palletsprojects.com/), [Pandas](https://pandas.pydata.org/docs/), [Matplotlib](https://matplotlib.org/stable/) e [scikit-learn](https://scikit-learn.org/stable/): bibliotecas utilizadas.
- OpenAI/Codex: apoio ao desenvolvimento e à organização do código.
