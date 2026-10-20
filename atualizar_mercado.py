"""Importa a tabela pública de Tahiti/Cepea, preservando região e unidade."""
import json
import re
import unicodedata
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from bs4 import BeautifulSoup

FONTE = 'https://hfbrasil.org.br/citros'
MESES = dict(zip('jan fev mar abr mai jun jul ago set out nov dez'.split(), range(1, 13)))
REGIOES = {'araraquara': 'Araraquara', 'bebedouro': 'Bebedouro', 'mogiana': 'Mogiana', 'limeira': 'Limeira'}

def normalizar(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', s.lower()) if not unicodedata.combining(c))

def data_coluna(texto, hoje):
    m = re.fullmatch(r'\s*(\d{1,2})\s*/\s*([a-zA-Zç]{3})(?:\s*/\s*(\d{4}))?\s*', texto)
    if not m or normalizar(m[2]) not in MESES:
        return None
    ano = int(m[3]) if m[3] else hoje.year
    d = date(ano, MESES[normalizar(m[2])], int(m[1]))
    if d > hoje and not m[3]:
        d = d.replace(year=ano - 1)
    if not 0 <= (hoje-d).days <= 60:
        raise ValueError('Data futura ou antiga demais na tabela: '+texto)
    return d.isoformat()

def extrair(html, hoje=None):
    hoje = hoje or date.today()
    soup = BeautifulSoup(html, 'html.parser')
    registros = {}
    for table in soup.find_all('table'):
        linhas = [[c.get_text(' ', strip=True) for c in tr.find_all(['th', 'td'], recursive=False)] for tr in table.find_all('tr')]
        colunas = None
        for cells in linhas:
            datas = {i: data_coluna(v, hoje) for i, v in enumerate(cells) if re.fullmatch(r'\s*\d{1,2}\s*/\s*[a-zA-Zç]{3}(?:\s*/\s*\d{4})?\s*', v)}
            if datas:
                colunas = datas
                continue
            if not colunas or len(cells) < 4:
                continue
            produto = normalizar(cells[0])
            if 'lima acida tahiti' not in produto or 'colhida' not in produto:
                continue
            regiao = next((k for k in REGIOES if k in normalizar(cells[1])), None)
            if not regiao:
                raise ValueError('Região Tahiti não reconhecida: '+cells[1])
            peso = re.fullmatch(r'caixa\s+(\d+(?:[.,]\d+)?)\s*kg', normalizar(cells[2]))
            if not peso:
                raise ValueError('Unidade não reconhecida: '+cells[2])
            kg = float(peso[1].replace(',', '.'))
            if not 1 <= kg <= 100:
                raise ValueError('Peso inválido')
            for i, dia in colunas.items():
                if i >= len(cells):
                    raise ValueError('Número de colunas divergente')
                v = cells[i].strip()
                if not v or re.fullmatch(r'[\s\-–—]+', v):
                    continue
                if not re.fullmatch(r'\d+(?:\.\d{3})*,\d{2}', v):
                    raise ValueError('Preço inválido: '+v)
                preco = float(v.replace('.', '').replace(',', '.'))
                if not 0 < preco < 10000:
                    raise ValueError('Preço fora do intervalo esperado')
                identificador = f'hf-{regiao}-{dia}'
                registro = {'id':identificador, 'inicio':dia, 'fim':dia, 'periodo':date.fromisoformat(dia).strftime('%d/%m/%Y'), 'frequencia':'diária', 'valor':preco, 'mercado':'hf-'+regiao, 'peso_kg':kg, 'unidade':'R$/caixa de '+str(kg).removesuffix('.0').replace('.', ',')+' kg', 'publicacao':dia, 'fonte':FONTE}
                if identificador in registros and registros[identificador] != registro:
                    raise ValueError('Preços conflitantes na tabela')
                registros[identificador] = registro
    if not registros:
        raise ValueError('Tabela de Tahiti ausente ou formato alterado; histórico preservado.')
    return list(registros.values())

def integrar(base, registros, agora=None):
    agora = agora or datetime.now(timezone.utc)
    por_id = {r['id']: r for r in base['registros']}
    novos = sum(por_id.get(r['id']) != r for r in registros)
    for r in registros:
        por_id[r['id']] = r
        regiao = r['mercado'].removeprefix('hf-')
        base['mercados'][r['mercado']] = {'nome':'Hortifruti Brasil/Cepea', 'local':REGIOES[regiao]+' (região) · Tahiti colhida', 'nota':'Referência regional publicada pelo Cepea, para fruta colhida. Regiões, datas e pesos diferentes não são diretamente comparáveis. Uso educativo não comercial; fonte: Hortifruti/Cepea, CC BY-NC 4.0.'}
    base['registros'] = sorted(por_id.values(), key=lambda r:(r['fim'], r['id']))
    base['consulta'] = agora.date().isoformat()
    base['atualizacao_hf'] = {'verificado_em':agora.isoformat(), 'ultima_cotacao':max(r['fim'] for r in registros), 'fonte':FONTE, 'status':'ok'}
    return novos

def main():
    erro = None
    for url in [FONTE, 'https://www.hfbrasil.org.br/citros']:
        try:
            req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 (compatible; GeoTerra-Educacional/1.0)', 'Accept':'text/html'})
            with urllib.request.urlopen(req, timeout=45) as resposta:
                html = resposta.read().decode('utf-8-sig')
            registros = extrair(html)
            break
        except Exception as e:
            erro = e
    else:
        raise RuntimeError('Falha na consulta Cepea. Nenhum dado foi sobrescrito.') from erro
    path = Path('data/mercado.json')
    base = json.loads(path.read_text(encoding='utf-8'))
    novos = integrar(base, registros)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(base, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    temp.replace(path)
    print(f'Cepea: {len(registros)} registros consultados; {novos} novos ou revisados.')

if __name__ == '__main__': main()
