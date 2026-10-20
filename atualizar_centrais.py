"""Cotações de Tahiti: CEAGESP oficial e CEASA Campinas (boletim ou republicação identificada)."""
import io
import json
import re
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, unquote, urlparse
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

CEAGESP='https://ceagesp.gov.br/cotacoes/'
CAMPINAS='https://www.ceasacampinas.com.br/cotacoes-anteriores'
NA='https://www.noticiasagricolas.com.br/cotacoes/frutas/limao-tahiti-ceasas'

def norm(s):
    return ''.join(c for c in unicodedata.normalize('NFKD',s.lower()) if not unicodedata.combining(c))

def slug(s):return re.sub(r'[^a-z0-9]+','-',norm(s)).strip('-')

def numero(s):
    s=s.strip()
    if not re.fullmatch(r'\d+(?:[.,]\d+)?',s):raise ValueError('Preço ausente ou inválido: '+s)
    v=float(s.replace(',','.'))
    if not 0<v<10000:raise ValueError('Preço fora do intervalo esperado')
    return v

def data_valida(texto, hoje=None):
    hoje=hoje or date.today()
    m=re.search(r'\b(\d{2})/(\d{2})/(\d{4})\b',texto)
    if not m:raise ValueError('Data da cotação ausente')
    d=date(int(m[3]),int(m[2]),int(m[1]))
    if not 0<=(hoje-d).days<=45:raise ValueError('Data futura ou desatualizada')
    return d.isoformat()

def registro(central,classe,dia,comum,fonte,minimo=None,maximo=None,secundaria=False):
    key=central+'-'+slug(classe)
    r=dict(id=key+'-'+dia,mercado=key,inicio=dia,fim=dia,periodo=date.fromisoformat(dia).strftime('%d/%m/%Y'),frequencia='diária',valor=comum,peso_kg=1,unidade='R$/kg',publicacao=dia,fonte=fonte,classificacao=classe,central=central,tipo_preco='republicado' if secundaria else 'mais comum',origem='Notícias Agrícolas (republicação)' if secundaria else ('CEAGESP' if central=='ceagesp' else 'CEASA Campinas'))
    if minimo is not None:
        if not minimo<=comum<=maximo:raise ValueError('Faixa mínimo/comum/máximo incoerente')
        r.update(valor_minimo=minimo,valor_maximo=maximo)
    return r

def extrair_ceagesp(html,esperada=None,hoje=None):
    soup=BeautifulSoup(html,'html.parser')
    table=soup.select_one('table.contacao_lista')
    if not table:raise ValueError('Boletim CEAGESP ausente')
    dia=data_valida(table.get_text(' ',strip=True),hoje)
    if esperada and dia!=esperada:raise ValueError('CEAGESP devolveu data diferente da solicitada')
    out=[]
    for tr in table.find_all('tr'):
        c=[td.get_text(' ',strip=True) for td in tr.find_all('td',recursive=False)]
        if not c or norm(c[0])!='limao taiti':continue
        if len(c)!=7 or c[2].upper()!='KG' or numero(c[6])!=1:raise ValueError('Unidade CEAGESP inesperada')
        out.append(registro('ceagesp',c[1],dia,numero(c[4]),CEAGESP,numero(c[3]),numero(c[5])))
    if not out:raise ValueError('Limão Taiti ausente do boletim CEAGESP')
    return out

def coletar_ceagesp():
    s=requests.Session()
    html=s.get(CEAGESP,timeout=25);html.raise_for_status()
    m=re.search(r'var\s+Grupos\s*=\s*(\{.*?\});',html.text,re.S)
    if not m:raise ValueError('Calendário CEAGESP ausente')
    datas=sorted({data_valida(d) for d in json.loads(m[1]).get('FRUTAS',[])},reverse=True)
    if not datas:raise ValueError('Nenhuma data CEAGESP disponível')
    out=[]
    for dia in datas[:3]:
        r=s.post(CEAGESP,data={'cot_grupo':'FRUTAS','cot_data':date.fromisoformat(dia).strftime('%d/%m/%Y')},timeout=25)
        r.raise_for_status();out.extend(extrair_ceagesp(r.text,dia))
    return out

def extrair_campinas_texto(texto,fonte,hoje=None):
    m=re.search(r'Cota[çc][ãa]o\s+Realizada\s+em\s*:\s*(\d{2}/\d{2}/\d{4})',texto,re.I)
    if not m:raise ValueError('Data interna do PDF Campinas ausente')
    dia=data_valida(m[1],hoje)
    out=[]
    for linha in texto.splitlines():
        if not re.search(r'LIM[AÃ]O\s*-\s*KG\s+TAHITI\b',linha,re.I):continue
        m=re.search(r'LIM[AÃ]O\s*-\s*KG\s+TAHITI\s+(.*?)\s*(\d+[.,]\d+)\s+(\d+[.,]\d+)\s+(\d+[.,]\d+)\s+\w+\s*$',linha,re.I)
        if not m:raise ValueError('Linha Tahiti no PDF Campinas não reconhecida')
        classe=m[1].strip() or 'Sem classificação informada'
        if classe.upper() not in ['EXTRA','ESPECIAL','PRIMEIRA','SEM CLASSIFICAÇÃO INFORMADA']:
            raise ValueError('Classificação Campinas não reconhecida: '+classe)
        out.append(registro('campinas',classe,dia,numero(m[3]),fonte,numero(m[2]),numero(m[4])))
    if not out:raise ValueError('Tahiti ausente no PDF Campinas')
    return out

def coletar_campinas_oficial():
    r=requests.get(CAMPINAS,timeout=18);r.raise_for_status()
    soup=BeautifulSoup(r.text,'html.parser');candidatos=[]
    for a in soup.find_all('a',href=True):
        url=urljoin(CAMPINAS,a['href'])
        if urlparse(url).hostname not in ['ceasacampinas.com.br','www.ceasacampinas.com.br'] or not urlparse(url).path.lower().endswith('.pdf'):continue
        label=a.get_text(' ',strip=True)
        try:dia=data_valida(label)
        except ValueError:
            m=re.search(r'(\d{2})[ _-]+(\d{2})[ _-]+(\d{4})\.pdf',unquote(url),re.I)
            if not m:continue
            try:dia=data_valida('/'.join(m.groups()))
            except ValueError:continue
        candidatos.append((dia,url))
    if not candidatos:raise ValueError('Link do boletim Campinas não encontrado')
    dia,url=max(candidatos)
    pdf=requests.get(url,timeout=25);pdf.raise_for_status()
    if not pdf.content.startswith(b'%PDF'):raise ValueError('Resposta Campinas não é PDF')
    texto='\n'.join(p.extract_text(extraction_mode='layout') or '' for p in PdfReader(io.BytesIO(pdf.content)).pages)
    registros=extrair_campinas_texto(texto,url)
    if registros[0]['fim']!=dia:raise ValueError('Data do PDF Campinas difere do link')
    return registros

def extrair_na(html,hoje=None):
    soup=BeautifulSoup(html,'html.parser');out=[]
    for table in soup.find_all('table'):
        if 'campinas' not in norm(table.get_text(' ',strip=True)):continue
        # O fechamento pertence ao bloco da tabela, nunca ao relógio da página.
        container=table
        contexto=''
        for _ in range(5):
            container=container.parent
            if container is None:break
            text=container.get_text(' ',strip=True)
            if re.search(r'Fechamento\s*:\s*\d{2}/\d{2}/\d{4}',text,re.I):contexto=text;break
        if not contexto:continue
        dia=data_valida(re.search(r'Fechamento\s*:\s*(\d{2}/\d{2}/\d{4})',contexto,re.I)[1],hoje)
        campinas=False
        for tr in table.find_all('tr'):
            c=[x.get_text(' ',strip=True) for x in tr.find_all(['td','th'],recursive=False)]
            if not c:continue
            label=norm(c[0])
            if 'campinas' in label:campinas=True;continue
            if 'ceasa' in label or 'ceagesp' in label:campinas=False;continue
            if not campinas or label not in ['extra','especial','primeira']:continue
            if len(c)<2 or 'cotacao' in norm(c[1]):continue
            out.append(registro('campinas',c[0],dia,numero(c[1]),NA,secundaria=True))
        if out:break
    if not out:raise ValueError('Tabela Campinas republicada não reconhecida')
    return out

def coletar_campinas():
    try:return coletar_campinas_oficial()
    except Exception as e:
        print('Campinas: boletim oficial indisponível; tentando republicação identificada. '+type(e).__name__)
        r=requests.get(NA,headers={'User-Agent':'Mozilla/5.0'},timeout=25);r.raise_for_status()
        return extrair_na(r.text)

def integrar(base,registros,central,agora=None):
    agora=agora or datetime.now(timezone.utc)
    ids={r['id']:r for r in base['registros']}
    for r in registros:
        # A fonte oficial tem prioridade para a mesma classificação e data.
        anterior=ids.get(r['id'])
        if anterior and anterior.get('tipo_preco')=='mais comum' and r['tipo_preco']=='republicado':continue
        ids[r['id']]=r
        nome='CEAGESP · São Paulo' if central=='ceagesp' else 'CEASA Campinas'
        base['mercados'][r['mercado']]={'nome':nome,'local':'Tahiti · '+r['classificacao'],'nota':'Preço de venda no atacado; não é preço pago ao produtor. As classificações das centrais não são equivalentes.','atualizacao_chave':central,'central':central}
    base['registros']=sorted(ids.values(),key=lambda r:(r['fim'],r['id']))
    base.setdefault('atualizacoes',{})[central]={'status':'ok','verificado_em':agora.isoformat(),'ultima_cotacao':max(r['fim'] for r in registros)}

def main():
    path=Path('data/mercado.json');base=json.loads(path.read_text(encoding='utf-8'));falhas=[]
    for central,coletor in [('ceagesp',coletar_ceagesp),('campinas',coletar_campinas)]:
        try:
            rows=coletor();integrar(base,rows,central);print(f'{central}: {len(rows)} cotações integradas.')
        except Exception as e:
            anterior=base.setdefault('atualizacoes',{}).get(central,{})
            base['atualizacoes'][central]={**anterior,'status':'erro','tentativa_em':datetime.now(timezone.utc).isoformat(),'mensagem':'Consulta indisponível; mantido o último registro válido.'}
            falhas.append(central);print(f'{central}: {type(e).__name__}: {e}')
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(base,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(path)
    if falhas:raise RuntimeError('Consulta incompleta: '+', '.join(falhas))

if __name__=='__main__':main()
