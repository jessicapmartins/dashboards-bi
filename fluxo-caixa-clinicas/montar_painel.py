"""Injeta dados/painel.json no index_template.html e gera index.html (pronto para a Vercel)."""
import json, os
aqui = os.path.dirname(os.path.abspath(__file__))
dados = json.load(open(os.path.join(aqui, 'dados', 'painel.json'), encoding='utf-8'))
html = open(os.path.join(aqui, 'index_template.html'), encoding='utf-8').read()
html = html.replace('/*DATA*/null', json.dumps(dados, ensure_ascii=False, separators=(',', ':')))
open(os.path.join(aqui, 'index.html'), 'w', encoding='utf-8').write(html)
print('index.html', round(len(html) / 1024), 'KB')
