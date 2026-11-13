"""Écrit out/lots/2026-11-18_26/progression.md (et une copie versionnée lots/2026-11-18_26-progression.md) à partir des fichiers sur disque."""
import json, os, glob, time, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)) + '/../..')
NOM = '2026-11-18_26'
lot = json.load(open(f'lots/{NOM}.json'))
usage_api = sys.argv[1] if len(sys.argv) > 1 else 'non relu'
notes = {}
if os.path.exists(f'lots/{NOM}-notes.json'):
    notes = json.load(open(f'lots/{NOM}-notes.json'))
L = []; SY = []; tot = 0; nimg = nrot = 0
def oui(b): return 'oui' if b else 'non'
for x in sorted(lot['episodes'], key=lambda x: (x['date'], x['id'][:3] != 'leo')):
    e = x['id']; ep = f'episodes/{e}'; o = f'out/{e}'
    ej = json.load(open(f'{ep}/episode.json')); n = len(ej['tenues'])
    img = sum(os.path.exists(f"{ep}/{t['image']}") or os.path.exists(f"{ep}/media/{os.path.basename(t['image'])}") for t in ej['tenues'])
    rot = sum(os.path.exists(f"{ep}/{t['rotation']}") or os.path.exists(f"{ep}/media/{os.path.basename(t['rotation'])}") for t in ej['tenues'])
    nimg += img; nrot += rot
    cr = 0
    for f in glob.glob(f'{ep}/media/voix/tts-essai*.json'):
        try: cr += int(json.load(open(f)).get('credits_factures') or 0)
        except Exception: pass
    tot += cr
    prix = 'non'
    if os.path.exists(f'{o}/prix.json'):
        prix = 'oui (' + time.strftime('%d/%m %H:%M', time.localtime(os.path.getmtime(f'{o}/prix.json'))) + ')'
    ver = 'non'
    if os.path.exists(f'{o}/verif.json'):
        v = json.load(open(f'{o}/verif.json')); ver = 'oui' if not v.get('erreurs') else 'erreurs'
    mp4 = f'{o}/{e}.mp4'
    rendu = os.path.exists(mp4)
    qa = 'non'
    if rendu and os.path.exists(f'{o}/qa/qa.json') and os.path.getmtime(f'{o}/qa/qa.json') >= os.path.getmtime(mp4) - 5:
        q = json.load(open(f'{o}/qa/qa.json')); pb = []
        if not (-14 <= q['lufs'] <= -12): pb.append(f"LUFS {q['lufs']}")
        if any(z['images_hors_zone'] for z in q['zones'].values()): pb.append('zones')
        if q['logo']['images_en_contact']: pb.append('logo')
        if q['ombre_contact']['ecart_max_px'] > 4: pb.append(f"ombre {q['ombre_contact']['ecart_max_px']} px")
        sp = q.get('sync_prix') or {}
        mx = max([abs(d.get('ecart_ms') or 0) for d in sp.get('detail', [])] or [0])
        if mx > 400: pb.append(f'sync whisper {mx} ms')
        if (sp.get('alignement_ecart_max_ms') or 0) > 150: pb.append(f"sync alignement {sp['alignement_ecart_max_ms']} ms")
        if 'alignement_ecart_max_ms' not in sp: pb.append('QA ancienne version')
        if sp.get('non_entendus'): pb.append(f"{sp['non_entendus']} prix non entendus par whisper")
        if json.load(open(f'{o}/props.json'))['data'].get('pastille360'): pb.append('étiquette 360° affichée')
        qa = 'oui' if not pb else 'ÉCHEC : ' + ', '.join(pb)
    dur = f"{q['format']['duree_s']:.1f} s" if qa != 'non' else ''
    SY.append(f"| {x['date']} | {e} | {ej['titre']} | {ej.get('publication', {}).get('meteo', '')} | {' / '.join(t['label'] + ' ' + t['total'] for t in ej['tenues'])} | {dur} | {mp4 if rendu else ''} | {qa} |")
    tot_t = ' / '.join(f"{t['label']} {t['total']}" for t in ej['tenues'])
    L.append(f"| {x['date']} | {e} | {'Léo' if ej.get('mannequin','leo')=='leo' else 'Inès'} | {prix} | {ver} | {oui(cr>0)} ({cr}) | {img}/{n} | {rot}/{n} | {oui(rendu)} | {qa} | {notes.get(e,'')} |")
H = [f"# Progression du lot {NOM}", '', f"Mise à jour : {time.strftime('%d/%m/%Y %H:%M')} (heure de Paris)", '',
     'Accord d’Aymane (13/11, 03:01) : 18 vidéos du 18 au 26/11, 12 000 crédits ElevenLabs au maximum, ne PAS programmer sur Buffer.', '',
     '| Date | Épisode | Mannequin | Prix ok | Verifier ok | Voix (crédits) | Images | Rotations | Rendu | QA ok | Remarques |',
     '|---|---|---|---|---|---|---|---|---|---|---|']
F = ['', f"Crédits ElevenLabs d’après les fichiers tts-essai*.json : {tot} sur 12 000.",
     f"Usage ElevenLabs relu par l’API (character-stats) : {usage_api}.",
     f"Images de mannequin présentes : {nimg} ; rotations 360° présentes : {nrot}."]
SYH = ['', '## Synthèse', '', '| Date | Épisode | Titre | Météo prévue | Tenues (total hors chaussures et livraison) | Durée | Vidéo | QA |', '|---|---|---|---|---|---|---|---|']
txt = '\n'.join(H + L + F + SYH + SY) + '\n'
os.makedirs(f'out/lots/{NOM}', exist_ok=True)
open(f'out/lots/{NOM}/progression.md', 'w').write(txt)
open(f'lots/{NOM}-progression.md', 'w').write(txt)
print(txt)
