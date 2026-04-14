# Documentação de Dados

Este diretório contém a estrutura de dados utilizada no projeto de Previsão de Demanda e Ruptura de Estoque. Seguindo as boas práticas de Ciência de Dados, os dados são divididos em camadas de processamento.

## Estrutura de Pastas

- **`raw/`**: Contém os dados originais, exatamente como foram extraídos das fontes. **Nunca modifique arquivos nesta pasta.**
- **`processed/`**: Contém os dados após limpeza, tratamento de valores nulos, engenharia de features e transformações para os modelos.
- **`external/`**: Fontes de dados complementares (ex: calendários de feriados, índices econômicos).

---

## Fontes de Dados

### 1. UCI Online Retail II (Dataset Principal)
Este é um dataset público contendo transações reais de um varejista online do Reino Unido entre 2009 e 2011.

- **Arquivo esperado**: `online_retail_II.xlsx`
- **Link para Download**: [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/502/online+retail+ii)
- **Localização**: Deve ser colocado em `data/raw/`.

**Colunas Principais:**
| Coluna | Descrição |
|---|---|
| `Invoice` | Número da transação (começa com 'C' para cancelamentos) |
| `StockCode` | Código identificador único do produto (SKU) |
| `Quantity` | Quantidade de itens na transação |
| `InvoiceDate` | Data e hora da venda |
| `Price` | Preço unitário do produto |
| `Customer ID` | Identificador único do cliente |

### 2. World Bank Commodity Markets
Utilizado para captar tendências de preços globais que podem influenciar a demanda de certos produtos.

- **Localização**: `data/external/`

---

## Como usar os dados neste projeto

1. Baixe o arquivo `online_retail_II.xlsx` do link acima.
2. Coloque-o na pasta `data/raw/`.
3. Execute o notebook `01_eda.ipynb` para iniciar a análise.
4. Os resultados processados serão salvos automaticamente em `data/processed/` nos formatos `.parquet` e `.csv`.

---
> [!NOTE]
> Por questões de privacidade e limites de tamanho do GitHub, arquivos grandes de dados estão incluídos no `.gitignore` e não são commitados.
