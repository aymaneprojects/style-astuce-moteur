"""Épisode de test hors ligne du format « look » : AUCUN crédit, AUCUNE génération.
- spec : copie d'une spec du lot (E1 par défaut) sous l'id test-look-<type>
- images : silhouettes dessinées (PIL), erreur et bonne tenue ; une photo produit factice (chaussure) pour tester le détourage produit
- rotation : la silhouette « tourne » (largeur en cosinus), 6 s à 30 i/s, encodée par ffmpeg
- voix : espeak-ng mot par mot (gratuit, local) + alignment.json au format ElevenLabs, pour faire tourner mots, silences, timeline, audio, rendu et QA réels
Usage : python tests/episode_test_look.py [leo-epaules-larges-grand-froid] [test-look-erreur]"""
import json, math, pathlib, shutil, subprocess, sys, wave, re
import numpy as np
from PIL import Image, ImageDraw
MOTEUR = pathlib.Path(__file__).resolve().parents[1]
src_id = sys.argv[1] if len(sys.argv) > 1 else 'leo-epaules-larges-grand-froid'
tid = sys.argv[2] if len(sys.argv) > 2 else 'test-look-erreur'
S = MOTEUR / 'episodes' / src_id; D = MOTEUR / 'episodes' / tid
if D.exists(): shutil.rmtree(D)
(D / 'media' / 'produits').mkdir(parents=True); V = D / 'media' / 'voix'; V.mkdir()
E = json.load(open(S / 'episode.json')); E['id'] = tid; E['titre'] = 'TEST hors ligne : ' + E['titre']
E['publication'] = dict(date_prevue='2099-01-01', plateformes=[], note='épisode de test, jamais publié')
E['look']['image'] = f'media/{tid}-look.jpg'; E['look']['rotation'] = f'media/rotation-{tid}-look.mp4'
if E['ouverture']['type'] == 'erreur': E['ouverture']['image_erreur'] = f'media/{tid}-erreur.jpg'
json.dump(E, open(D / 'episode.json', 'w'), ensure_ascii=False, indent=1)
txt = (S / 'script.txt').read_text(encoding='utf-8').strip(); (D / 'script.txt').write_text(txt + '\n', encoding='utf-8')

FOND = (226, 224, 221)
def silhouette(haut, bas, manteau, chaussures, bandes=False, w=1.0):
    im = Image.new('RGB', (1080, 1920), FOND); d = ImageDraw.Draw(im); cx = 549
    X = lambda dx: cx + dx * w
    d.ellipse([X(-70), 150, X(70), 330], fill=(198, 160, 130))                       # tête
    d.rectangle([X(-28), 320, X(28), 380], fill=(198, 160, 130))                      # cou
    d.rounded_rectangle([X(-150), 370, X(150), 1010], 40, fill=haut)                  # buste
    if manteau: d.rounded_rectangle([X(-175), 360, X(175), 1300 if not bandes else 1040], 50, fill=manteau); d.rectangle([X(-40), 380, X(40), 1300 if not bandes else 1040], fill=haut)
    if bandes:
        for y in range(400, 1040, 70): d.line([X(-175), y, X(175), y], fill=(150, 150, 155), width=8)
    for s_ in (-1, 1):
        d.rounded_rectangle([X(s_ * 205 - 32), 390, X(s_ * 205 + 32), 980], 30, fill=manteau or haut)   # bras
        d.rounded_rectangle([X(s_ * 70 - 58), 990, X(s_ * 70 + 58), 1790], 20, fill=bas)                   # jambes
        d.rounded_rectangle([X(s_ * 75 - 62), 1772, X(s_ * 75 + 72 * (1 if s_ > 0 else 1)), 1844], 24, fill=chaussures)  # chaussures, semelle à 1844
    return im
look = silhouette((30, 40, 80), (70, 70, 75), (150, 150, 150), (20, 20, 20))
look.save(D / 'media' / f'{tid}-look.jpg', quality=95)
if E['ouverture']['type'] == 'erreur':
    silhouette((120, 120, 125), (90, 120, 170), (200, 200, 205), (240, 240, 240), bandes=True).save(D / 'media' / f'{tid}-erreur.jpg', quality=95)
# photo produit factice : une bottine sur fond blanc (teste le détourage produit des chaussures)
j = next(i for i, pc in enumerate(E['look']['pieces'], 1) if pc['zone'] == 'chaussures')
pp = Image.new('RGB', (800, 800), (255, 255, 255)); dp = ImageDraw.Draw(pp)
dp.rounded_rectangle([250, 200, 420, 600], 30, fill=(25, 25, 25)); dp.rounded_rectangle([250, 480, 620, 610], 50, fill=(25, 25, 25)); dp.rectangle([240, 600, 630, 640], fill=(60, 50, 40))
pp.save(D / 'media' / 'produits' / f"{j}-chaussures.jpg", quality=95)
# rotation factice : 180 images, largeur en |cos|, puis ffmpeg
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x1920', '-r', '30', '-i', '-', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p',
                      str(D / 'media' / f'rotation-{tid}-look.mp4')], stdin=subprocess.PIPE)
for k in range(180):
    w = max(0.35, abs(math.cos(2 * math.pi * k / 180))); p.stdin.write(silhouette((30, 40, 80), (70, 70, 75), (150, 150, 150), (20, 20, 20), w=w).tobytes())
p.stdin.close(); p.wait()
# voix factice espeak-ng mot par mot + alignement caractère par caractère (format ElevenLabs with-timestamps)
SR = 22050; mots = txt.split(); audio = []; t = 0.0; chars, cs, ce = [], [], []
for i, m in enumerate(mots):
    r = subprocess.run(['espeak-ng', '-v', 'fr', '-s', '225', '--stdout', re.sub(r'[«»"]', '', m)], capture_output=True).stdout
    with wave.open(__import__('io').BytesIO(r)) as wv: x = np.frombuffer(wv.readframes(wv.getnframes()), '<i2').astype(np.float32) / 32768; sr = wv.getframerate()
    nz = np.nonzero(np.abs(x) > 0.01)[0]; x = x[nz[0]:nz[-1] + 1] if len(nz) else x[:int(0.15 * sr)]
    dur = len(x) / sr
    for k_, c in enumerate(m): chars.append(c); cs.append(round(t + dur * k_ / len(m), 3)); ce.append(round(t + dur * (k_ + 1) / len(m), 3))
    audio.append(x); t += dur
    gap = 0.45 if m[-1] in '.?!:' else 0.22 if m[-1] == ',' else 0.03
    if i < len(mots) - 1:
        chars.append(' '); cs.append(round(t, 3)); ce.append(round(t + gap, 3)); audio.append(np.zeros(int(gap * sr), np.float32)); t += gap
y = np.concatenate(audio)
with wave.open(str(V / 'dummy.wav'), 'wb') as wv: wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(sr); wv.writeframes((y * 32767 * 0.9).astype('<i2').tobytes())
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(V / 'dummy.wav'), '-ar', '44100', '-b:a', '128k', str(V / 'voice-raw.mp3')], check=True)
(V / 'dummy.wav').unlink()
json.dump(dict(characters=chars, character_start_times_seconds=cs, character_end_times_seconds=ce), open(V / 'alignment.json', 'w'), ensure_ascii=False)
(V / 'FACTICE.txt').write_text('Voix factice espeak-ng (locale, gratuite) : test uniquement, jamais publiée.\n', encoding='utf-8')
print(f'{tid} prêt : voix factice {t:.1f} s, {len(mots)} mots ->', D)
