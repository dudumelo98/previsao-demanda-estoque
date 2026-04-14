"""
Treinamento e avaliação do modelo Prophet por SKU.

Encapsulo aqui a lógica de forecasting para que possa ser chamada
em batch para múltiplos SKUs sem reescrever código. Uso joblib para
paralelizar quando o número de SKUs for grande.
"""

import pandas as pd
import numpy as np
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import logging
from pathlib import Path
from typing import Dict, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODELS_PATH = Path(__file__).parents[2] / 'models'
MODELS_PATH.mkdir(exist_ok=True)


def preparar_serie_prophet(df: pd.DataFrame, sku: str) -> pd.DataFrame:
    """
    Filtra e formata a série temporal de um SKU para o formato Prophet.
    
    Prophet exige colunas ds (datetime) e y (valor). Preencho datas sem venda
    com zero — ausência de dado não significa dado ausente, significa que não vendeu.
    """
    serie = df[df['sku'] == sku][['data', 'quantidade']].copy()
    serie.columns = ['ds', 'y']
    serie = serie.sort_values('ds')
    
    # Preencho dias sem registro com zero
    datas_completas = pd.date_range(serie['ds'].min(), serie['ds'].max(), freq='D')
    serie = serie.set_index('ds').reindex(datas_completas, fill_value=0).reset_index()
    serie.columns = ['ds', 'y']
    
    return serie


def treinar_prophet(serie: pd.DataFrame, modo_sazonalidade: str = 'multiplicative') -> Prophet:
    """
    Treina um modelo Prophet com configuração padrão para demanda de varejo.
    
    Uso sazonalidade multiplicativa como padrão porque em varejo a amplitude
    da sazonalidade tende a crescer junto com a tendência de vendas.
    """
    modelo = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        seasonality_mode=modo_sazonalidade,
        changepoint_prior_scale=0.05,
        seasonality_prior_scale=10,
        interval_width=0.95
    )
    modelo.add_country_holidays(country_name='UK')
    modelo.fit(serie)
    
    return modelo


def avaliar_modelo(modelo: Prophet, serie: pd.DataFrame, horizonte_dias: int = 60) -> Dict:
    """
    Avalia o modelo no horizonte de previsão definido.
    
    Retorna MAE, MAPE e RMSE. Para o problema de ruptura, MAPE é a métrica
    mais interpretável para o time de operações — erro percentual por dia.
    """
    corte = serie['ds'].max() - pd.Timedelta(days=horizonte_dias)
    treino = serie[serie['ds'] <= corte]
    teste = serie[serie['ds'] > corte]
    
    if len(teste) == 0:
        logger.warning('Sem dados no período de teste')
        return {}
    
    futuro = modelo.make_future_dataframe(periods=horizonte_dias)
    previsao = modelo.predict(futuro)
    
    prev_teste = previsao[previsao['ds'].isin(teste['ds'])][['ds', 'yhat']]
    resultado = teste.merge(prev_teste, on='ds')
    
    # Evito divisão por zero no MAPE
    mask_nao_zero = resultado['y'] > 0
    
    metricas = {
        'mae': mean_absolute_error(resultado['y'], resultado['yhat']),
        'rmse': np.sqrt(mean_squared_error(resultado['y'], resultado['yhat'])),
        'mape': np.mean(np.abs(
            (resultado.loc[mask_nao_zero, 'y'] - resultado.loc[mask_nao_zero, 'yhat'])
            / resultado.loc[mask_nao_zero, 'y']
        )) * 100 if mask_nao_zero.sum() > 0 else None,
        'n_dias_teste': len(resultado)
    }
    
    return metricas


def prever_sku(df: pd.DataFrame, sku: str, horizonte: int = 30) -> pd.DataFrame:
    """
    Pipeline completo para um SKU: prepara, treina e retorna a previsão.
    
    Retorna DataFrame com ds, yhat, yhat_lower, yhat_upper para os próximos
    `horizonte` dias após o último dado disponível.
    """
    logger.info(f'Processando SKU: {sku}')
    
    serie = preparar_serie_prophet(df, sku)
    
    if len(serie) < 30:
        logger.warning(f'SKU {sku} tem menos de 30 dias de histórico — pulando')
        return pd.DataFrame()
    
    modelo = treinar_prophet(serie)
    
    futuro = modelo.make_future_dataframe(periods=horizonte)
    previsao = modelo.predict(futuro)
    
    # Retorno apenas os dias futuros — não preciso devolver o histórico
    previsao_futura = previsao[previsao['ds'] > serie['ds'].max()][
        ['ds', 'yhat', 'yhat_lower', 'yhat_upper']
    ].copy()
    
    # Garanto que a previsão não seja negativa
    previsao_futura['yhat'] = previsao_futura['yhat'].clip(lower=0)
    previsao_futura['yhat_lower'] = previsao_futura['yhat_lower'].clip(lower=0)
    previsao_futura['sku'] = sku
    
    return previsao_futura


def processar_skus_batch(df: pd.DataFrame, skus: list, n_jobs: int = -1) -> pd.DataFrame:
    """
    Processa múltiplos SKUs em paralelo usando joblib.
    
    Para datasets com centenas de SKUs prioritários (classe A da curva ABC),
    o processamento paralelo reduz o tempo de ~minutos para ~segundos.
    """
    resultados = joblib.Parallel(n_jobs=n_jobs, verbose=1)(
        joblib.delayed(prever_sku)(df, sku)
        for sku in skus
    )
    
    df_previsoes = pd.concat([r for r in resultados if not r.empty], ignore_index=True)
    
    logger.info(f'Previsões geradas para {df_previsoes["sku"].nunique()} SKUs')
    return df_previsoes
