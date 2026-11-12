from pathlib import Path
import json
import joblib
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import accuracy_score, recall_score, confusion_matrix
from dados import ler, COLUNAS_ENTRADA

# Onde ficam os arquivos que este código precisa abrir ou salvar.
ARQUIVO_DADOS = Path(__file__).resolve().with_name('data') / 'cleveland.csv'
ARQUIVO_MODELO = Path(__file__).resolve().with_name('models') / 'modelo.joblib'
ARQUIVO_AVALIACAO = Path(__file__).resolve().with_name('models') / 'avaliacao.json'
PASTA_MODELOS = Path(__file__).resolve().with_name('models')


# Treina os dois modelos, compara os resultados e salva o escolhido.
def treinar():
    arquivo_csv = ARQUIVO_DADOS.read_bytes()
    dados, limpeza = ler(arquivo_csv)
    # X são as medidas de entrada; y é o resultado que queremos prever.
    X = dados[COLUNAS_ENTRADA]
    y = dados.alvo
    # Separamos uma parte para testar com registros que o modelo ainda não viu.
    X_treino, X_teste, y_treino, y_teste = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    # O preenchimento de valores ausentes é aprendido só com o treino.
    # Na regressão, também colocamos as medidas na mesma escala.
    modelos = {
        'Regressão logística': make_pipeline(SimpleImputer(strategy='median'), StandardScaler(), LogisticRegression(max_iter=2000, random_state=42)),
        'Random Forest': make_pipeline(SimpleImputer(strategy='median'), RandomForestClassifier(n_estimators=200, max_depth=5, min_samples_leaf=3, random_state=42)),
    }
    validacao = StratifiedKFold(5, shuffle=True, random_state=42)
    resultados = {}
    # Os dois modelos usam a mesma divisão para a comparação ser justa.
    for nome, modelo in modelos.items():
        notas_validacao = cross_val_score(modelo, X_treino, y_treino, cv=validacao, scoring='balanced_accuracy')
        modelo.fit(X_treino, y_treino)
        previsoes = modelo.predict(X_teste)
        resultados[nome] = {
            'cv_media': notas_validacao.mean(),
            'acuracia_treino': accuracy_score(y_treino, modelo.predict(X_treino)),
            'acuracia': accuracy_score(y_teste, previsoes),

            'sensibilidade': recall_score(y_teste, previsoes, zero_division=0),
            'matriz': confusion_matrix(y_teste, previsoes, labels=[0, 1]).tolist(),
        }
    # Escolher pelo resultado da validação, sem usar o teste para decidir.
    melhor_modelo = None
    melhor_nota = -1
    for nome, resultado in resultados.items():
        if resultado['cv_media'] > melhor_nota:
            melhor_nota = resultado['cv_media']
            melhor_modelo = nome
    relatorio = {
        'modelo': melhor_modelo,
        'base': 'Cleveland da versão Kaggle incluída em data/cleveland.csv',
        'criterio': 'Maior acurácia balanceada média em validação cruzada somente no treino; teste reservado para avaliação final.',
        'treino': len(X_treino),
        'teste': len(X_teste),
        'classes_teste': y_teste.value_counts().to_dict(),
        'proporcao_majoritaria': float(y_teste.value_counts(normalize=True).max()),
        'limpeza': limpeza,
        'resultados': resultados,
    }
    PASTA_MODELOS.mkdir(exist_ok=True)
    joblib.dump(modelos[melhor_modelo], ARQUIVO_MODELO)
    ARQUIVO_AVALIACAO.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Modelo salvo: {melhor_modelo}. Resultados em models/avaliacao.json.')
if __name__ == '__main__':
    treinar()
