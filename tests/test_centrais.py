import unittest
from datetime import date
from atualizar_centrais import extrair_ceagesp, extrair_campinas_texto, extrair_na, integrar
D=date(2026,10,20)
CEAGESP='''<table class="contacao_lista"><tr><td colspan="7">Categoria: FRUTAS Data: 19/10/2026</td></tr>
<tr><td>LIMÃO TAITI</td><td>15 A 18 DZ</td><td>KG</td><td>8,1</td><td>8,47</td><td>8,85</td><td>1</td></tr>
<tr><td>LIMÃO SICILIANO</td><td>-</td><td>KG</td><td>4,23</td><td>4,55</td><td>4,87</td><td>1</td></tr></table>'''
CAMPINAS='Cotação Realizada em: 19/10/2026\nLIMAO - KG TAHITI EXTRA 9.00 9.50 10.00 ME\nLIMAO - KG SICILIANO 7.00 8.00 9.00 ME'
NA='''<div><h3>Fechamento: 19/10/2026</h3><table><tr><td>Ceasa - Campinas/SP</td><td>***</td></tr>
<tr><td>Extra</td><td>9,50</td><td>0,00</td></tr><tr><td>Ceasa - Belo Horizonte/MG</td><td>***</td></tr><tr><td>Extra</td><td>10,00</td></tr></table></div>'''
class CentraisTest(unittest.TestCase):
 def test_ceagesp_classificacao_e_faixa(self):
  r=extrair_ceagesp(CEAGESP,'2026-10-19',D);self.assertEqual(len(r),1);self.assertEqual(r[0]['valor'],8.47);self.assertEqual(r[0]['valor_minimo'],8.1)
 def test_ceagesp_rejeita_data_e_unidade(self):
  with self.assertRaises(ValueError):extrair_ceagesp(CEAGESP,'2026-10-16',D)
  with self.assertRaises(ValueError):extrair_ceagesp(CEAGESP.replace('<td>KG</td>','<td>CX</td>'),hoje=D)
 def test_pdf_filtra_tahiti(self):
  r=extrair_campinas_texto(CAMPINAS,'https://exemplo.test/boletim.pdf',D);self.assertEqual(len(r),1);self.assertEqual(r[0]['valor'],9.5);self.assertEqual(r[0]['classificacao'],'EXTRA')
 def test_pdf_faixa_invalida(self):
  with self.assertRaises(ValueError):extrair_campinas_texto(CAMPINAS.replace('9.50','12.00'),'fonte',D)
 def test_republicacao_separa_campinas_bh(self):
  r=extrair_na(NA,D);self.assertEqual(len(r),1);self.assertEqual(r[0]['valor'],9.5);self.assertNotIn('valor_minimo',r[0]);self.assertEqual(r[0]['tipo_preco'],'republicado')
 def test_oficial_tem_prioridade(self):
  b={'mercados':{},'registros':[]};r=extrair_campinas_texto(CAMPINAS,'oficial',D);integrar(b,r,'campinas');integrar(b,extrair_na(NA,D),'campinas');self.assertEqual(b['registros'][0]['fonte'],'oficial')
