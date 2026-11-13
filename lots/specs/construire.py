"""Construit script.txt + episode.json des épisodes du lot 18-26/11 à partir de specs compactes (aucun réseau, aucun crédit).
Usage : python3 lots/specs/construire.py  (depuis moteur/)"""
import json, re, sys, unicodedata, shutil
from pathlib import Path
sys.path.insert(0, 'cli'); import sa
M = Path('.').resolve()
BENJAMIN = {"fournisseur": "elevenlabs", "voice_name": "Benjamin", "voice_id": "F9KUTOne5xOKqAbIU7yg", "model_id": "eleven_v4", "language_code": "fr", "stability": 0.45, "similarity_boost": 0.75, "output_format": "mp3_44100_128"}
KORALY = {"fournisseur": "elevenlabs", "voice_name": "Koraly - Promo Video", "voice_id": "rbFGGoDXFHtVghjHuS3E", "model_id": "eleven_v4", "language_code": "fr", "stability": 0.45, "similarity_boost": 0.75, "output_format": "mp3_44100_128"}
def J(pid): return f'https://www.jules.com/fr-fr/p/{pid}.html'
def U(pid, c, g='00'): return f'https://www.uniqlo.com/fr/fr/products/{pid}/{g}?colorDisplayCode={c}'
def eur(p):
    e, c = divmod(round(p * 100), 100)
    return f'{sa.fr_nombre(e)} euros' if c == 0 else f'{sa.fr_nombre(e)} {sa.fr_nombre(c)}'
def fmt(p): return f'{p:.2f}'.replace('.', ',') + ' €'
def norm(w): return sa.norm(w)
NUM = ['Un', 'Deux', 'Trois']
STOP = {'le', 'la', 'les', 'un', 'une', 'toujours', 'même', 'encore'}

def build(S):
    eid = S['id']; d = M / 'episodes' / eid
    if not d.exists(): sa.cmd_nouveau(type('A', (), dict(episode=eid, depuis='leo-jean-3-tenues'))())
    paras = [S['p1']]; tenues = []
    for k, T in enumerate(S['tenues']):
        (h, b) = T['pieces']; tot = round(h[3] + b[3], 2)
        txt = (f"{NUM[k]}, {T['art']} {T['label']}. {h[0]}, {h[2]}, {eur(h[3])}. {b[0]}, {b[2]}, {eur(b[3])}. "
               f"Total : {eur(tot)}. {T['astuce']}")
        paras.append(txt)
        slug = re.sub(r'[^a-z0-9]+', '-', unicodedata.normalize('NFKD', T['label'].lower()).encode('ascii', 'ignore').decode()).strip('-')
        pcs = []
        for pc, zone in ((h, 'haut'), (b, 'bas')):
            pcs.append(dict(nom=pc[1], enseigne=pc[2], prix=fmt(pc[3]), zone=zone, url=pc[4], mot=next(w for w in pc[0].split() if norm(w) not in STOP), mot_prix=eur(pc[3]).split()[0], desc_en=pc[5]))
        at = T['titre']
        tenues.append(dict(label=T['label'], total=fmt(tot), mot=NUM[k], mot_label=T['label'].split()[0],
            image=f'media/{eid}-{k+1}-{slug}.jpg', rotation=f'media/rotation-{eid}-{k+1}-{slug}.mp4',
            coupe=dict(ourlet_y='auto', chaussures_y=1640), sous_titre=dict(texte=T['st'][0], surligne=T['st'][1], mot=T['label'].split()[0]),
            pieces=pcs, mot_total='Total',
            astuce=dict(mot=T['astuce'].split()[0], titre=dict(l1=at[0], pre='', kw=at[1], post=at[2], mot_surligne=at[3]),
                        sous_titres=[dict(mot=s[0], texte=s[1], surligne=s[2], mot_surligne=s[3]) for s in T['sts']])))
        if T.get('chaussures_en'): tenues[-1]['chaussures_en'] = T['chaussures_en']
    paras.append(f"Prix relevés le treize novembre, hors chaussures et livraison. Alors, {S['question']} Réponds un, deux ou trois en commentaire.")
    script = '\n\n'.join(paras) + '\n'
    E = json.load(open(d / 'episode.json', encoding='utf-8'))
    A, P = S['accroche'], S['promesse']
    E.update(id=eid, titre=S['titre'], date_releve='2026-11-13', mannequin=S['mannequin'], voix=S['voix'], ouverture=S['ouverture'],
        logo={"actif": True, "variante": "creme", "opacite": 0.8, "largeur": 164},
        accroche=dict(l1=A[0], pre='', kw=A[1], post=A[2], mot_surligne=A[3]),
        promesse=dict(mot=P['mot'], l1=P['l1'], pre='', kw=P['kw'], post='', mot_surligne=P['surl'], sous_titre=dict(texte=P['st'][0], surligne=P['st'][1], mot=P['st'][2])),
        intro=dict(mots_cartes={str(i + 1): w for i, w in enumerate(S['cartes'])}, fin_s=5, duree_images=12, numeros=True),
        tenues=tenues,
        mention=dict(mot='Prix', l1='Prix relevés le 13/11', l2='hors chaussures et livraison', mot_l2='hors'),
        fin=dict(mot='Alors', titre=dict(l1=S['fin'][0], pre=S['fin'][1], kw=S['fin'][2], post=S['fin'][3], mot_surligne=S['fin'][4]),
                 sous_titre=dict(mot='Réponds', texte='Réponds 1, 2 ou 3 en commentaire', surligne='commentaire', mot_surligne='commentaire'),
                 mots_numeros=['un', 'deux', 'trois']),
        publication=dict(date_prevue=S['date'], plateformes=['TikTok', 'Instagram Reels'], forme_accroche=S['forme'], meteo=S['meteo']))
    if S.get('chaussures_en'): E['chaussures_en'] = S['chaussures_en']
    E.pop('pastille_360', None)
    json.dump(E, open(d / 'episode.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    (d / 'script.txt').write_text(script, encoding='utf-8')
    # contrôles de position : chaque mot déclencheur doit tomber dans le bon paragraphe
    err = []
    words = [(norm(w), pi) for pi, p in enumerate(paras) for w in p.split()]
    def find(w, start=0):
        for i in range(start, len(words)):
            if words[i][0] == norm(w): return i
        return None
    ip = find(P['mot'])
    if ip is None or words[ip][1] != 0: err.append('promesse hors paragraphe 1')
    c = ip or 0
    for k, t in enumerate(tenues):
        c2 = find(t['mot'], c + 1)
        if c2 is None or words[c2][1] != k + 1 or (c2 > 0 and words[c2 - 1][1] == k + 1): err.append(f'tenue {k+1} : « {t["mot"]} » trouvé au mauvais endroit')
        c = c2 or c
    im = find('Prix', c)
    if im is None or words[im][1] != 4: err.append('« Prix » de la mention trouvé trop tôt')
    for x in err: print('!!', eid, x)
    return script

SPECS = []
def add(**k): SPECS.append(k)
