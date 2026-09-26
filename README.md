# GeoTerra · Limão em São Paulo

WebGIS gerado em Python com Folium, pronto para Google Colab e GitHub Pages.

[Abrir no Google Colab](https://colab.research.google.com/github/geovanemariotto123-coder/-webgis-limao-sao-paulo/blob/main/WebGIS_Limao_SP.ipynb)

## Usar

Abra o notebook e execute as células em ordem. Ele copia o projeto, instala Folium e gera `index.html` usando o retrato dos dados incluído no repositório. Ative `ATUALIZAR_IBGE = True` para consultar novamente a fonte oficial.

No computador: `pip install -r requirements.txt`, depois `python gerar.py`.
Para atualizar os dados: `python coletar.py` e `python gerar.py`.

## Publicar

O arquivo `index.html` já está na raiz. No GitHub: **Settings → Pages → Deploy from a branch → main → / (root) → Save**.

Endereço esperado após ativação: https://geovanemariotto123-coder.github.io/-webgis-limao-sao-paulo/

A presença do arquivo no repositório não confirma que o Pages foi ativado.

## Conteúdo

- 645 municípios na malha IBGE simplificada.
- Série PAM 2020–2025 consultada em 26/09/2026. O ano de 2026 ainda não está disponível na PAM.
- Produção (t), área destinada à colheita (ha), área colhida (ha), rendimento (kg/ha) e valor da produção (mil R$ correntes).
- Busca, ranking, série municipal no clique, escala comparável entre anos e CSV do ano selecionado.

Fonte: https://sidra.ibge.gov.br/tabela/1613. Endereços exatos e data da coleta em `data/fontes.json`. Respostas originais preservadas em `data/`. A geometria atual é usada para todos os anos; não representa alterações históricas dos limites. Ausências não são convertidas em zero; o símbolo SIDRA `-` é zero absoluto. Dados monetários podem apresentar diferenças de arredondamento entre soma municipal e total estadual; `data/validacao.json` registra a comparação.

“Limão” é a categoria da PAM e não separa Tahiti, Siciliano e outros tipos. Área destinada à colheita não mede novos plantios. Valor da produção não é preço de venda nem volume comercializado. Há registros selecionados de preços da CEAGESP e do Hortifruti Brasil/Cepea em uma seção separada. Eles não formam uma série contínua nem medem o volume comercializado, que ainda não está integrado.

O HTML usa Leaflet/Folium e mapa-base OpenStreetMap, com recursos externos; precisa de conexão para carregar essas dependências. O recorte municipal e a série de dados estão incorporados no HTML.
