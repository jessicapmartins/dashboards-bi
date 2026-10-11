# Clínicas Aurora · fluxo de caixa

Painel de fluxo de caixa de uma **rede fictícia de três clínicas**, com foco no quanto as faltas às consultas custam e no quanto vale reduzi-las.

> **Projeto autoral com dados sintéticos.** A empresa e os números são inventados por um script com semente fixa. A taxa de falta foi calibrada pela base real do projeto [previsão de faltas em consultas](https://github.com/jessicapmartins/previsao-faltas-consultas) (20,2% em 110 mil consultas).

## O que o painel mostra
- Receita líquida, despesas, resultado e margem, com filtro por unidade e período
- Receita e margem que as faltas tiram da operação, por mês e por especialidade
- DRE simplificada: desconto de convênios, repasse médico, insumos e custos fixos
- Mapa de calor da taxa de falta por unidade e dia da semana
- Simulador: quanto se ganha reduzindo as faltas, descontando o custo dos contatos

## Premissas (todas ajustáveis em `gerar_dados.py`)
| Item | Valor |
|---|---|
| Unidades | Centro (80 vagas/dia), Zona Norte (55), Litoral (40); sábado meio período |
| Especialidades | Clínica geral, Pediatria, Ginecologia, Cardiologia, Dermatologia, Ortopedia (R$ 120 a R$ 230) |
| Convênio | 70% das consultas, pagando 75% da tabela |
| Repasse médico | 45% da receita líquida |
| Insumos | R$ 7 por consulta realizada |
| Taxa de falta | 20,2% de base, com ajustes por unidade, mês, dia da semana e especialidade |

## Como rodar
```bash
python gerar_dados.py      # gera dados/consultas_diarias.csv e dados/painel.json
python montar_painel.py    # injeta os dados e gera index.html
```
`index.html` é um arquivo único (HTML + Chart.js). Para publicar na Vercel: **Add New → Project → importar o repositório `dashboards-bi` → Root Directory `fluxo-caixa-clinicas` → Framework "Other" → Deploy**.

---
Jéssica Priscila de Oliveira Martins · [Portfólio](https://claude.ai/artifact/YPyaaqo16QuwKBKGw9VF5m)
