import sys; sys.path.insert(0, 'lots/specs')
import construire, hommes, femmes, extras
import json
L = {'nom': '2026-11-18_26', 'note': "Lot du 18 au 26/11 : 9 Léo (Benjamin) + 9 Inès (Koraly), 2 vidéos par jour. Construit par lots/specs/construire.py.", 'episodes': []}
for S in construire.SPECS:
    for k, t in enumerate(S['tenues']):
        t['astuce'] = t['astuce'].rstrip() + ' ' + extras.X[S['id']][k]
    s = construire.build(S); print(f"{S['id']:30} {len(s.strip()):5} car.")
    L['episodes'].append({'id': S['id'], 'date': S['date']})
json.dump(L, open('lots/2026-11-18_26.json', 'w'), ensure_ascii=False, indent=1)
