import copy
import unittest
from datetime import date, datetime, timezone
from atualizar_mercado import extrair, integrar, data_coluna

# Fixture sintética do contrato da tabela; não é uma captura da fonte.
HTML='''<table><tr><th>Produto</th><th>Região</th><th>Unidade</th><th>16/out</th><th>19/out</th></tr>
<tr><td>Laranja Lima - Árvore - Mercado</td><td>Araraquara (região)</td><td>caixa 40,8 Kg</td><td>61,20</td><td>61,20</td></tr>
<tr><td>Lima Ácida Tahiti - Colhida - Mercado</td><td>Araraquara (região)</td><td>caixa 27 kg</td><td>156,07</td><td>156,89</td></tr>
<tr><td>Lima Ácida Tahiti - Colhida - Mercado</td><td>Mogiana (região)</td><td>caixa 27 kg</td><td>- - -</td><td>180,00</td></tr></table>'''
class MercadoTest(unittest.TestCase):
    def test_regioes_unidades_ausencias(self):
        r=extrair(HTML,date(2026,10,20));self.assertEqual(len(r),3)
        self.assertEqual(r[0]['valor'],156.07);self.assertEqual(r[0]['peso_kg'],27)
        self.assertEqual({x['mercado'] for x in r},{'hf-araraquara','hf-mogiana'})
    def test_erro_nao_vira_zero(self):
        with self.assertRaises(ValueError):extrair(HTML.replace('156,07','indisponível'),date(2026,10,20))
        with self.assertRaises(ValueError):extrair('<html>Access denied</html>',date(2026,10,20))
    def test_virada_do_ano(self):
        self.assertEqual(data_coluna('30/dez',date(2027,1,2)),'2026-12-30')
        with self.assertRaises(ValueError):data_coluna('21/out',date(2026,10,20))
    def test_integracao_idempotente_preserva_historico(self):
        b={'registros':[{'id':'antigo','valor':130.74,'fim':'2026-10-09'}],'mercados':{}}
        r=extrair(HTML,date(2026,10,20));agora=datetime(2026,10,20,tzinfo=timezone.utc)
        self.assertEqual(integrar(b,r,agora),3);self.assertEqual(integrar(b,r,agora),0)
        self.assertEqual(b['registros'][0]['id'],'antigo')
