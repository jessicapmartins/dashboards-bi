"""Gera os dados sintéticos do fluxo de caixa da rede fictícia Clínicas Aurora (2025).

Tudo aqui é inventado, com premissas explícitas. A taxa de falta foi calibrada pela
base real do projeto previsao-faltas-consultas (20,2% em 110 mil consultas da rede
pública de Vitória, ES). Rode:  python gerar_dados.py
"""
import json, os
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
AQUI = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- premissas
UNIDADES = {   # vagas por dia útil, ajuste da taxa de falta (p.p.), custos fixos mensais (R$)
    'Centro':     {'vagas': 80, 'ajuste_falta': -0.010, 'adm': 28000, 'aluguel': 18000, 'servicos': 5200, 'marketing': 3000},
    'Zona Norte': {'vagas': 55, 'ajuste_falta': +0.025, 'adm': 20000, 'aluguel': 11500, 'servicos': 3900, 'marketing': 2200},
    'Litoral':    {'vagas': 40, 'ajuste_falta': -0.005, 'adm': 16000, 'aluguel': 9800,  'servicos': 3100, 'marketing': 2000},
}
ESPECIALIDADES = {   # participação na agenda, preço de tabela (R$), ajuste da taxa de falta
    'Clínica geral': (0.34, 120, +0.010),
    'Pediatria':     (0.20, 140, -0.005),
    'Ginecologia':   (0.15, 170, +0.000),
    'Cardiologia':   (0.12, 230, -0.025),
    'Dermatologia':  (0.11, 190, +0.020),
    'Ortopedia':     (0.08, 210, -0.010),
}
TAXA_FALTA_BASE = 0.202          # calibrada pela base real do projeto de faltas
CENTRALIZA = -0.014              # compensa a média dos ajustes para a taxa geral ficar perto de 20,2%
OCUPACAO_MES = [0.86, 0.90, 0.93, 0.94, 0.95, 0.93, 0.88, 0.94, 0.95, 0.95, 0.93, 0.85]
AJUSTE_FALTA_MES = [0.020, 0.005, 0, 0, 0, 0.005, 0.015, 0, 0, 0, 0.005, 0.025]
AJUSTE_FALTA_DIA = {0: 0.012, 1: 0.0, 2: -0.004, 3: -0.004, 4: 0.015, 5: 0.020}   # seg..sáb
PARTICULAR = 0.30                # 30% particular (preço cheio), 70% convênio
DESCONTO_CONVENIO = 0.25         # convênio paga 75% da tabela
REPASSE_MEDICO = 0.45            # médicos recebem 45% da receita líquida da consulta
INSUMOS_CONSULTA = 7.0           # R$ por consulta realizada
SISTEMAS = 1800                  # R$ por unidade por mês

# ---------------------------------------------------------------- simulação diária
dias = pd.bdate_range('2025-01-01', '2025-12-31', freq='C', weekmask='Mon Tue Wed Thu Fri Sat')
feriados = pd.to_datetime(['2025-01-01', '2025-03-03', '2025-03-04', '2025-04-18', '2025-04-21', '2025-05-01',
                           '2025-06-19', '2025-09-07', '2025-10-12', '2025-11-02', '2025-11-15', '2025-11-20', '2025-12-25'])
dias = dias[~dias.isin(feriados)]

linhas = []
for d in dias:
    m, dow = d.month - 1, d.dayofweek
    for u, cu in UNIDADES.items():
        vagas = cu['vagas'] * (0.5 if dow == 5 else 1.0)          # sábado: meio período
        agendadas_dia = rng.binomial(int(vagas), OCUPACAO_MES[m])
        partes = rng.multinomial(agendadas_dia, [v[0] for v in ESPECIALIDADES.values()])
        for (esp, (_, preco, aj_esp)), n in zip(ESPECIALIDADES.items(), partes):
            p = TAXA_FALTA_BASE + CENTRALIZA + cu['ajuste_falta'] + AJUSTE_FALTA_MES[m] + AJUSTE_FALTA_DIA[dow] + aj_esp
            faltas = rng.binomial(n, min(max(p, 0.02), 0.6))
            linhas.append((d.date(), u, esp, int(n), int(faltas), preco))

df = pd.DataFrame(linhas, columns=['data', 'unidade', 'especialidade', 'agendadas', 'faltas', 'preco_tabela'])
df['realizadas'] = df['agendadas'] - df['faltas']
preco_liq = df['preco_tabela'] * (PARTICULAR + (1 - PARTICULAR) * (1 - DESCONTO_CONVENIO))
df['receita_bruta'] = df['realizadas'] * df['preco_tabela']
df['receita_liquida'] = df['realizadas'] * preco_liq
df['receita_perdida'] = df['faltas'] * preco_liq
df['repasse_medico'] = df['receita_liquida'] * REPASSE_MEDICO
df['insumos'] = df['realizadas'] * INSUMOS_CONSULTA
# margem que cada falta tira: receita líquida - repasse - insumos que deixariam de existir
df['margem_perdida'] = df['faltas'] * (preco_liq * (1 - REPASSE_MEDICO) - INSUMOS_CONSULTA)
df['mes'] = pd.to_datetime(df['data']).dt.month
df['dia_semana'] = pd.to_datetime(df['data']).dt.dayofweek

os.makedirs(os.path.join(AQUI, 'dados'), exist_ok=True)
df.to_csv(os.path.join(AQUI, 'dados', 'consultas_diarias.csv'), index=False)

# ---------------------------------------------------------------- agregados para o painel
mensal = (df.groupby(['unidade', 'especialidade', 'mes'])
            [['agendadas', 'faltas', 'realizadas', 'receita_bruta', 'receita_liquida', 'receita_perdida',
              'repasse_medico', 'insumos', 'margem_perdida']].sum().round(2).reset_index())
fixos = [{'unidade': u, 'mes': m, 'adm': c['adm'], 'aluguel': c['aluguel'], 'servicos': c['servicos'],
          'marketing': c['marketing'], 'sistemas': SISTEMAS}
         for u, c in UNIDADES.items() for m in range(1, 13)]
semana = (df.groupby(['unidade', 'mes', 'dia_semana'])[['agendadas', 'faltas']].sum().reset_index())

saida = {
    'gerado_em': '2025 (dados sintéticos, semente 42)',
    'premissas': {'taxa_falta_base': TAXA_FALTA_BASE, 'particular': PARTICULAR, 'desconto_convenio': DESCONTO_CONVENIO,
                  'repasse_medico': REPASSE_MEDICO, 'insumos_consulta': INSUMOS_CONSULTA},
    'mensal': mensal.to_dict(orient='records'),
    'fixos': fixos,
    'semana': semana.to_dict(orient='records'),
}
json.dump(saida, open(os.path.join(AQUI, 'dados', 'painel.json'), 'w', encoding='utf-8'), ensure_ascii=False)

# resumo no terminal
tot = df[['agendadas', 'faltas', 'receita_liquida', 'receita_perdida', 'margem_perdida', 'repasse_medico', 'insumos']].sum()
fixo_ano = sum(c['adm'] + c['aluguel'] + c['servicos'] + c['marketing'] + SISTEMAS for c in UNIDADES.values()) * 12
resultado = tot['receita_liquida'] - tot['repasse_medico'] - tot['insumos'] - fixo_ano
print(f"{len(dias)} dias úteis · {int(tot['agendadas']):,} consultas agendadas · falta {tot['faltas']/tot['agendadas']:.1%}")
print(f"Receita líquida R$ {tot['receita_liquida']:,.0f} · resultado R$ {resultado:,.0f} ({resultado/tot['receita_liquida']:.1%})")
print(f"Receita perdida com faltas R$ {tot['receita_perdida']:,.0f} · margem perdida R$ {tot['margem_perdida']:,.0f}")
