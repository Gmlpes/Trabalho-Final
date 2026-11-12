from pathlib import Path
import math

import joblib
import pandas as pd
from dados import COLUNAS_ENTRADA, LIMITES_CAMPOS

# Onde ficam os arquivos que este código precisa abrir ou salvar.
ARQUIVO_MODELO = Path(__file__).resolve().with_name('models') / 'modelo.joblib'


# Confere os valores preenchidos e usa o modelo salvo para fazer a previsão.
def prever(formulario):
    valores = []
    for coluna, (minimo, maximo) in zip(COLUNAS_ENTRADA, LIMITES_CAMPOS):
        try:
            valor = float(formulario.get(coluna, ''))
        except (TypeError, ValueError):
            raise ValueError('Preencha todos os campos com números.')
        if not math.isfinite(valor) or not minimo <= valor <= maximo:
            raise ValueError(f'{coluna}: valor permitido de {minimo} a {maximo}.')
        valores.append(valor)
    modelo = joblib.load(ARQUIVO_MODELO)
    # O modelo precisa receber as mesmas colunas, na mesma ordem do treino.
    dados_preenchidos = pd.DataFrame([valores], columns=COLUNAS_ENTRADA)
    previsao = modelo.predict(dados_preenchidos)
    return int(previsao[0])
