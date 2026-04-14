"""
Script de ingestão e limpeza dos dados brutos.

Centralizo aqui toda a lógica de carregamento para que os notebooks
não precisem repetir as mesmas transformações. Qualquer mudança no
formato do dado bruto tem um único ponto de manutenção.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RAW_PATH = Path(__file__).parents[2] / 'data' / 'raw'
PROCESSED_PATH = Path(__file__).parents[2] / 'data' / 'processed'


def carregar_online_retail(caminho: Path = None) -> pd.DataFrame:
    """
    Carrega e une as duas abas do dataset UCI Online Retail II.
    
    Retorna o dataset com colunas renomeadas para minúsculo e snake_case,
    sem nenhuma limpeza aplicada — isso é responsabilidade de limpar_dados().
    """
    if caminho is None:
        caminho = RAW_PATH / 'online_retail_II.xlsx'
    
    logger.info(f'Carregando dataset de {caminho}')
    
    df_2009 = pd.read_excel(caminho, sheet_name='Year 2009-2010')
    df_2010 = pd.read_excel(caminho, sheet_name='Year 2010-2011')
    
    df = pd.concat([df_2009, df_2010], ignore_index=True)
    
    df.columns = [col.lower().replace(' ', '_') for col in df.columns]
    
    logger.info(f'Dataset carregado: {len(df):,} linhas, {df.shape[1]} colunas')
    return df


def limpar_dados(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica a limpeza definida durante a EDA.
    
    Decisões tomadas:
    - Removo cancelamentos (Invoice começando com 'C') — não representam demanda real
    - Removo quantity e price negativos ou zero — podem ser ajustes contábeis
    - Removo linhas sem customer_id — sem identificador não consigo rastrear comportamento
    - Removo duplicatas exatas
    """
    n_inicial = len(df)
    
    # Cancelamentos
    df = df[~df['invoice'].astype(str).str.startswith('C')]
    logger.info(f'Após remover cancelamentos: {len(df):,} linhas')
    
    # Valores inválidos
    df = df[(df['quantity'] > 0) & (df['price'] > 0)]
    logger.info(f'Após remover quantity/price inválidos: {len(df):,} linhas')
    
    # Sem customer ID
    df = df.dropna(subset=['customer_id'])
    logger.info(f'Após remover sem customer_id: {len(df):,} linhas')
    
    # Duplicatas
    df = df.drop_duplicates()
    logger.info(f'Após remover duplicatas: {len(df):,} linhas')
    
    # Conversão de tipos
    df['invoicedate'] = pd.to_datetime(df['invoicedate'])
    df['customer_id'] = df['customer_id'].astype(int)
    df['revenue'] = df['quantity'] * df['price']
    
    n_final = len(df)
    logger.info(f'Limpeza concluída: {n_inicial - n_final:,} linhas removidas ({(1 - n_final/n_inicial)*100:.1f}%)')
    
    return df


def agregar_diario(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega o dataset de transações na granularidade diária por SKU.
    
    Essa é a granularidade de entrada para os modelos de forecasting.
    """
    df_diario = df.groupby(
        ['stockcode', pd.Grouper(key='invoicedate', freq='D')]
    ).agg(
        quantidade=('quantity', 'sum'),
        receita=('revenue', 'sum'),
        n_transacoes=('invoice', 'nunique'),
        preco_medio=('price', 'mean')
    ).reset_index()
    
    df_diario.columns = ['sku', 'data', 'quantidade', 'receita', 'n_transacoes', 'preco_medio']
    
    logger.info(f'Agregação diária: {len(df_diario):,} registros, {df_diario["sku"].nunique():,} SKUs únicos')
    return df_diario


def pipeline_completo() -> pd.DataFrame:
    """
    Executa o pipeline completo de ingestão e retorna o dataset diário pronto.
    
    Uso como ponto de entrada nos notebooks para evitar repetição de código.
    """
    df_raw = carregar_online_retail()
    df_limpo = limpar_dados(df_raw)
    df_diario = agregar_diario(df_limpo)
    
    # Salvo o processado para evitar reprocessar toda vez
    output = PROCESSED_PATH / 'dados_diarios.parquet'
    df_diario.to_parquet(output, index=False)
    logger.info(f'Dataset diário salvo em {output}')
    
    return df_diario


if __name__ == '__main__':
    pipeline_completo()
