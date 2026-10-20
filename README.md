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

## Atualização automática de preços

O workflow `atualizar-mercado.yml` consulta a tabela pública de citros do Hortifruti Brasil/Cepea de segunda a sexta às 19h17 (Brasília), além de permitir execução manual em Actions. Preserva regiões, datas, pesos e os registros históricos agregados. A CEAGESP continua identificada como histórico sem atualização automática. Não existe integração automática da PAM neste fluxo.

O coletor valida produto, região, unidade, datas e valores. Ausências não viram zero. Em caso de bloqueio da fonte ou mudança de formato, preserva o histórico e marca o workflow como falho, publicando a última base válida. O painel mostra a última consulta bem-sucedida e avisa quando a cotação tem mais de sete dias. A atualização depende da disponibilidade do portal e do GitHub Actions.

Execução local: `python atualizar_mercado.py` e `python gerar.py`. Testes: `python -m unittest discover -s tests`.

Dados regionais: Hortifruti/Cepea, licença CC BY-NC 4.0, para divulgação educativa não comercial. As cotações diárias regionais em caixa de 27 kg ficam separadas das notícias históricas de médias semanais em caixa de 27,2 kg.

## CEAGESP e CEASA Campinas

A rotina automática também consulta o formulário público da CEAGESP para FRUTAS, usando as últimas três datas disponibilizadas no calendário do próprio portal. Apenas Limão Taiti em KG é importado, com classificação, mínimo, mais comum e máximo. O valor principal no painel é o mais comum.

Para Campinas, busca o PDF mais recente ligado no portal oficial, confere a data interna e importa Tahiti por classificação. Se o boletim não estiver acessível, consulta a republicação do Notícias Agrícolas. Essa origem intermediária fica explícita no painel e no CSV, sem inventar mínimo/máximo. Um registro oficial tem prioridade sobre uma republicação da mesma data e classe.

Falhas de cada central são registradas separadamente, preservando os dados anteriores. O sucesso de uma central não depende do sucesso das outras. Não se misturam os preços das classes nem se calcula uma média entre Cepea, CEAGESP e Campinas.
