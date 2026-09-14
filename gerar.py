"""Gera um WebGIS estático com Folium e dados auditáveis."""
import json, csv, math
from pathlib import Path
import folium
from branca.element import MacroElement, Template, Element

METRICAS = {'214': ['Produção', 't'], '2313': ['Área destinada à colheita', 'ha'], '216': ['Área colhida', 'ha'], '112': ['Rendimento médio', 'kg/ha'], '215': ['Valor da produção', 'mil R$ correntes']}

def valor(s):
    # SIDRA: '-' é zero absoluto; '..', '...' e X não são zero.
    if s == '-': return 0.0
    try:
        v = float(s)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError): return None

def organizar(raw):
    dados = {}; nomes = {}; linhas = []
    for var in raw:
        vid = str(var['id'])
        if vid not in METRICAS: continue
        for resultado in var['resultados']:
            for serie in resultado['series']:
                loc = serie['localidade']; cod = str(loc['id'])
                nomes[cod] = loc['nome'].removesuffix(' - SP')
                for ano, original in serie['serie'].items():
                    v = valor(original)
                    dados.setdefault(ano, {}).setdefault(cod, {})[vid] = v
                    linhas.append([ano, cod, nomes[cod], vid, *METRICAS[vid], v, original])
    return dados, nomes, linhas

def gerar():
    p = Path('data')
    ler = lambda nome: json.loads((p/nome).read_text(encoding='utf-8'))
    info = ler('fontes.json'); dados, nomes, linhas = organizar(ler('municipios.json'))
    estado, _, _ = organizar(ler('estado.json'))
    geo = ler('malha_sp.geojson')
    for f in geo['features']:
        cod = str(f['properties'].get('codarea', f.get('id', '')))
        f['properties'] = {'codigo': cod, 'nome': nomes.get(cod, cod)}
    codigos = {f['properties']['codigo'] for f in geo['features']}
    assert len(codigos) == 645, f'Malha incompleta: {len(codigos)} municípios'
    assert all(c in codigos for a in dados.values() for c in a), 'Dados sem geometria'
    assert len(linhas) == len({(r[0], r[1], r[3]) for r in linhas}), 'Duplicatas'
    # Verificação independente contra totais estaduais; renda média não é aditiva.
    verificacao = []
    for ano, locais in dados.items():
        for vid in ['214', '216', '2313', '215']:
            vals = [v.get(vid) for v in locais.values()]
            soma = sum(v for v in vals if v is not None)
            oficial = estado[ano]['35'][vid]
            diferenca = None if oficial is None else soma - oficial
            verificacao.append({'ano': ano, 'indicador': vid, 'soma_municipios': soma, 'total_estadual': oficial, 'diferenca': diferenca})
            # Valor monetário tem arredondamento municipal em mil reais.
            if vid != '215' and all(v is not None for v in vals):
                assert abs(diferenca) < 1, (ano, vid, diferenca)
    (p/'validacao.json').write_text(json.dumps(verificacao, ensure_ascii=False, indent=2))
    with (p/'limao_sp.csv').open('w', newline='', encoding='utf-8-sig') as arq:
        w = csv.writer(arq); w.writerow(['ano','codigo_ibge','municipio','indicador_id','indicador','unidade','valor','valor_original']); w.writerows(linhas)
    mapa = folium.Map(location=[-22.3,-48.5], zoom_start=7, tiles='OpenStreetMap', control_scale=True)
    camada = folium.GeoJson(geo, name='Municípios de São Paulo', style_function=lambda f: {'fillColor':'#ddd','color':'#66796b','weight':0.5,'fillOpacity':0.8}).add_to(mapa)
    css = Path('interface.css').read_text()
    html = Path('painel.html').read_text()
    mapa.get_root().header.add_child(Element('{% raw %}<title>GeoTerra | Limão em São Paulo</title><style>'+css+'</style>{% endraw %}'))
    mapa.get_root().html.add_child(Element(html))
    js = Path('interface.js').read_text()
    payload = json.dumps({'dados':dados,'estado':estado,'nomes':nomes,'metricas':METRICAS,'info':info},ensure_ascii=False).replace('</','<\\/')
    js = js.replace('__PAYLOAD__', payload).replace('__MAPA__', mapa.get_name()).replace('__CAMADA__', camada.get_name())
    macro = MacroElement(); macro._template = Template('{% macro script(this, kwargs) %}'+js+'{% endmacro %}'); mapa.add_child(macro)
    mapa.save('index.html')
    print(f'Gerado: index.html | {len(codigos)} municípios | {len(linhas)} registros')
    return mapa

if __name__ == '__main__': gerar()
