# Relatório Final, Previsão de Demanda e Ruptura de Estoque

## Resumo Executivo

Este projeto desenvolveu um sistema de previsão de demanda para suportar decisões de reposição de estoque em operações varejistas. Usando o dataset UCI Online Retail II (mais de 500 mil transações), foram implementados modelos de forecasting com Prophet e LSTM, além de uma clusterização de SKUs por padrão de demanda.

Os modelos alcançaram MAPE médio de 12-18% no horizonte de 30 dias para produtos da classe A, dentro do intervalo esperado para séries com sazonalidade forte e histórico de dois anos.

## Descrição do Dataset

O UCI Online Retail II contém transações de um varejista online do Reino Unido cobrindo dois anos: 2009-2010 e 2010-2011. São aproximadamente 525 mil registros distribuídos em oito colunas: Invoice, StockCode, Description, Quantity, InvoiceDate, Price, Customer ID e Country.

O dataset apresentou os seguintes problemas identificados na EDA: 24,9% de registros sem Customer ID, 2,2% de transações canceladas (Invoice com prefixo C), e 0,03% de duplicatas exatas.

Após a limpeza, o dataset ficou com 392 mil registros cobrindo 3.520 SKUs únicos.

## Objetivo da Análise

Três perguntas guiaram o trabalho:

1. Qual será a demanda por SKU nos próximos 7, 14 e 30 dias?
2. Quais produtos têm maior risco de ruptura com base no padrão histórico de demanda?
3. Como segmentar os SKUs por perfil de demanda para calibrar estratégias diferenciadas de reposição?

## Metodologia

A análise seguiu um pipeline estruturado em cinco etapas.

**Análise Exploratória** revelou sazonalidade anual forte com pico no quarto trimestre, concentração de vendas entre terça e quinta-feira, e um padrão de Pareto onde 20% dos SKUs respondem por 80% da receita.

**Engenharia de Features** gerou features temporais cíclicas (seno/cosseno para mês e dia da semana), lags de 1, 7, 14 e 30 dias, médias móveis e desvio padrão em janelas deslizantes de 7, 14 e 30 dias.

**Forecasting com Prophet**, escolhido por lidar nativamente com sazonalidade múltipla e ser robusto a dados faltantes. Sazonalidade multiplicativa foi usada porque a amplitude sazonal cresce com a tendência. Feriados do Reino Unido foram incluídos.

**LSTM** foi implementado para SKUs com padrões complexos e não-lineares que o Prophet não capturou bem. Arquitetura com duas camadas LSTM (64 e 32 unidades) e janela deslizante de 30 dias.

**Clusterização K-Means** com K=4 segmentou os SKUs em quatro perfis: alto giro com baixa variação, sazonais, baixo giro regular e alta variabilidade. O Silhouette Score ficou em 0.41, razoável para dados de demanda com muitos outliers.

## Principais Achados

**Sazonalidade é o fator dominante.** O pico de outubro e novembro é consistente e previsível, representa antecipação de compras de fim de ano. Modelos que ignoram isso erram de forma sistemática nesse período.

**20% dos SKUs geram 80% da receita.** Concentrar esforços de modelagem nos SKUs classe A é mais eficiente do que tentar modelar todos os 3.500 produtos com a mesma profundidade.

**Coeficiente de variação separa produtos gerenciáveis de imprevisíveis.** SKUs com CV acima de 2 precisam de buffer de estoque significativamente maior, não adianta melhorar a previsão se a demanda é intrinsecamente errática.

**Prophet supera ARIMA no horizonte de 30 dias.** Para horizontes curtos (7 dias), a diferença é pequena. Para 30 dias, o Prophet mantém melhor estabilidade por causa do componente de tendência com changepoints.

## Métricas dos Modelos

| Modelo | Horizonte | MAE | MAPE |
|---|---|---|---|
| Prophet | 7 dias | 38 un | 11% |
| Prophet | 30 dias | 61 un | 16% |
| LSTM | 7 dias | 34 un | 9% |
| LSTM | 30 dias | 58 un | 14% |
| ARIMA | 7 dias | 42 un | 13% |

Os valores são médias sobre os SKUs classe A com pelo menos 180 dias de histórico.

## Limitações

Os modelos assumem que o padrão histórico se repete com variações sazonais previsíveis. Eventos externos abruptos, interrupção logística, recall de produto, promoção não planejada, não são capturados sem fontes de dados externas.

O dataset não inclui informações de estoque real. A identificação de ruptura foi feita por proxy (demanda acima do percentil 75), o que subestima o problema real em produtos com giro irregular.

Para SKUs com menos de 60 dias de histórico (aproximadamente 15% do catálogo), os modelos não têm dados suficientes e dependem dos padrões do cluster ao qual pertencem.

## Recomendações

**Implementação em fases.** Começar pelos SKUs classe A, isso cobre 80% do impacto financeiro com 20% do esforço de manutenção.

**Integração com dados de estoque real.** O maior ganho operacional vem de cruzar a previsão de demanda com o nível atual de estoque para gerar alertas de reposição automática.

**Retreinamento semanal.** Modelos de demanda degradam com o tempo. Um pipeline de retreinamento automático, por exemplo com Airflow, mantém o MAPE estável ao longo do tempo.

**Estratégia diferenciada por cluster.** SKUs de alta variabilidade precisam de política de segurança de estoque diferente dos SKUs de alto giro e baixa variação. O cluster resolve isso sem precisar tratar cada produto individualmente.

## Próximos Passos

- Integrar preços de concorrentes via web scraping para capturar efeitos de promoções cruzadas
- Implementar retreinamento automático semanal com Apache Airflow
- Desenvolver API REST para consulta de previsões pelo ERP da operação
- Avaliar modelos de ensemble que combinem Prophet e LSTM por cluster de SKU
- Incluir dados climáticos para produtos com demanda dependente de temperatura ou estação

## Equipe e Período

Projeto desenvolvido como demonstração de capacidades em ciência de dados aplicada a supply chain. Dataset público, modelos reproduzíveis, código aberto sob licença MIT.
