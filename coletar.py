"""Coleta PAM/IBGE: limão, municípios de SP, apenas períodos publicados."""
import json, gzip, time, urllib.request
from pathlib import Path
from datetime import datetime, timezone

BASE = 'https://servicodados.ibge.gov.br/api/v3/agregados/1613'

def get_json(url):
    for tentativa in range(3):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                b = r.read()
            if b[:2] == b'\x1f\x8b': b = gzip.decompress(b)
            return json.loads(b)
        except Exception:
            if tentativa == 2: raise
            time.sleep(2)

def coletar():
    pasta = Path('data'); pasta.mkdir(exist_ok=True)
    fontes = []
    def baixar(nome, url):
        dados = get_json(url)
        (pasta / nome).write_text(json.dumps(dados, ensure_ascii=False), encoding='utf-8')
        fontes.append({'arquivo': nome, 'url': url})
        return dados
    meta = baixar('metadados.json', BASE + '/metadados')
    periodos = baixar('periodos.json', BASE + '/periodos')
    anos = sorted(int(p['id']) for p in periodos if p['id'].isdigit() and 2020 <= int(p['id']) <= 2026)
    if not anos: raise RuntimeError('Nenhum período de 2020 a 2026 disponível na PAM.')
    categoria = [(c['id'], x['id']) for c in meta['classificacoes'] for x in c['categorias'] if x['nome'] == 'Limão']
    assert len(categoria) == 1, 'Categoria Limão ambígua ou ausente'
    cl, cat = categoria[0]
    ps = '|'.join(map(str, anos))
    for nivel, local in [('municipios', 'N6[N3[35]]'), ('estado', 'N3[35]')]:
        url = f'{BASE}/periodos/{ps}/variaveis/214|216|2313|215|112?localidades={local}&classificacao={cl}[{cat}]'
        baixar(nivel + '.json', url)
    baixar('malha_sp.geojson', 'https://servicodados.ibge.gov.br/api/v3/malhas/estados/35?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=municipio')
    manifest = {'consulta_utc': datetime.now(timezone.utc).isoformat(), 'anos': anos, 'fontes': fontes, 'tabela': 'https://sidra.ibge.gov.br/tabela/1613', 'produto': 'Limão (categoria IBGE; não separa cultivares)', 'limites': 'Área destinada à colheita não mede novos plantios. Valor da produção em mil R$ correntes não é cotação nem volume comercializado.'}
    (pasta/'fontes.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Dados coletados:', anos)
    return manifest

if __name__ == '__main__': coletar()
