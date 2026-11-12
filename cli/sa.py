#!/usr/bin/env python3
"""Moteur Style Astuce : une commande par étape, et « tout » qui enchaîne.

Usage : python3 cli/sa.py <commande> episodes/<id> [options]
Commandes : prix, voix, mots, silences, timeline, vignettes, audio, rendu, qa, tout,
           verifier, prompts, nouveau (épisode) et lot (plusieurs épisodes, voir README)
Aucune clé n'est écrite ni affichée : la clé ElevenLabs est lue en mémoire (variable ELEVENLABS_API_KEY,
ou --cle-fichier qui ne lit QUE la ligne ELEVENLABS_API_KEY du fichier indiqué).
"""
import argparse, base64, datetime, hashlib, json, math, os, re, shutil, subprocess, sys, time, urllib.request, wave
from pathlib import Path
import numpy as np

MOTEUR = Path(__file__).resolve().parent.parent
FPS = 30
SHIFT = -3                 # visuels 100 ms en avance sur le mot (mesure whisper sur v2 : -87 ms médian)
SILENCE_GARDEE = 0.32      # silences plus longs ramenés à 0,32 s (aucune accélération de la voix)
SAFE = dict(TikTok=(60, 940, 150, 1470), Reels=(108, 960, 220, 1420), commune=(108, 940, 220, 1420))
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36'

def log(*a): print('[sa]', *a, flush=True)
class SAErreur(Exception): pass
def stop(msg): raise SAErreur(msg)
def run(cmd, **kw):
    r = subprocess.run(cmd, **kw)
    if r.returncode: stop('commande en échec : ' + ' '.join(map(str, cmd))[:300])
    return r

class Ep:
    def __init__(self, d):
        self.dir = Path(d).resolve()
        if not (self.dir / 'episode.json').exists(): stop(f'{self.dir}/episode.json introuvable')
        self.E = json.load(open(self.dir / 'episode.json', encoding='utf-8'))
        self.id = self.E['id']
        self.media = self.dir / 'media'; self.voix = self.media / 'voix'
        self.out = MOTEUR / 'out' / self.id; self.pub = self.out / 'public'
        for p in (self.voix, self.out, self.pub): p.mkdir(parents=True, exist_ok=True)
    def p(self, rel):
        return Path(rel) if os.path.isabs(rel) else (self.dir / rel)
    def script(self):
        return self.p(self.E['script']).read_text(encoding='utf-8').strip()

# ------------------------------------------------------------------ prix
def prix_num(s): return float(s.replace('€', '').replace(',', '.').strip())
def lire_url(req, essais=4):
    for k in range(essais):
        try: return urllib.request.urlopen(req, timeout=30).read()
        except Exception:
            if k == essais - 1: raise
            time.sleep(2 * (k + 1))
def cmd_prix(ep, a):
    res = []; ok = True
    for t in ep.E['tenues']:
        for pc in t['pieces']:
            url = pc['url']; attendu = prix_num(pc['prix']); barre = prix_num(pc['prix_barre']) if pc.get('prix_barre') else None
            trouve = base = None; note = ''; note_stock = ''
            try:
                if 'jules.com' in url:
                    h = lire_url(urllib.request.Request(url, headers={'User-Agent': UA})).decode('utf-8', 'ignore')
                    for m in re.finditer(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', h, re.S):
                        try: d = json.loads(m.group(1))
                        except Exception: continue
                        for x in (d if isinstance(d, list) else [d]):
                            if x.get('@type') == 'Product':
                                o = x.get('offers'); o = o[0] if isinstance(o, list) else o; trouve = float(o['price'])
                                if 'InStock' not in str(o.get('availability', 'InStock')): note_stock = 'rupture de stock sur la fiche'
                elif 'uniqlo.com' in url:
                    pid = re.search(r'/products/(E\d+-\d+)/(\d+)', url); col = re.search(r'colorDisplayCode=(\d+)', url)
                    api = f'https://www.uniqlo.com/fr/api/commerce/v5/fr/products/{pid.group(1)}/price-groups/{pid.group(2)}/l2s?withPrices=true&withStocks=true&httpFailure=true'
                    d = json.loads(lire_url(urllib.request.Request(api, headers={'User-Agent': UA, 'x-fr-clientid': 'uq.fr.web-spa'})))['result']
                    for l2 in d['l2s']:
                        if not col or l2['color']['displayCode'] == col.group(1):
                            pr = d['prices'].get(l2['l2Id'], {}); base = pr.get('base', {}).get('value')
                            trouve = (pr.get('promo') or {}).get('value') or base
                            ids = [x['l2Id'] for x in d['l2s'] if x['color']['displayCode'] == l2['color']['displayCode']]; sts = [d.get('stocks', {})[i] for i in ids if i in d.get('stocks', {})]
                            if sts and not any(v.get('statusCode') != 'STOCK_OUT' and v.get('quantity', 1) > 0 for v in sts): note_stock = 'rupture : aucune taille en stock dans ce coloris'
                            break
                else:
                    note = 'enseigne non automatisée : vérifier à la main'
            except Exception as e:
                note = f'lecture impossible ({type(e).__name__})'
            bon = trouve is not None and abs(trouve - attendu) < 0.005 and (barre is None or (base is not None and abs(base - barre) < 0.005))
            ok &= bon or bool(note)
            res.append(dict(piece=pc['nom'], enseigne=pc['enseigne'], attendu=attendu, trouve=trouve, prix_de_base=base, ok=bon, note=note, stock=note_stock or 'ok', url=url))
            log(f"{'OK ' if bon else '!! '} {pc['nom']:<28} attendu {attendu:6.2f}  trouvé {trouve}  {('base ' + str(base)) if base else ''} {note} {note_stock}")
    stamp = datetime.datetime.now().astimezone().isoformat(timespec='minutes')
    json.dump(dict(verifie_le=stamp, pieces=res), open(ep.out / 'prix.json', 'w'), ensure_ascii=False, indent=1)
    if not all(r['ok'] for r in res if not r['note']): stop('au moins un prix a changé : corriger episode.json (et le script si le prix est dit)')
    rup = [r['piece'] for r in res if r['stock'] != 'ok']
    if rup: stop('pièce(s) en rupture, à remplacer : ' + ', '.join(rup))
    nl = [r['piece'] for r in res if r['note']]
    if nl: log('ATTENTION, prix non lus, à vérifier à la main avant envoi :', ', '.join(nl))
    # produits.md versionné avec l'épisode : URL, prix lu, date et heure du relevé, stock
    md = [f"# Produits : {ep.E['titre']}\n", f"Relevé automatique `sa.py prix` le {stamp} (heure de Paris). Prix TTC lus sur la fiche, hors chaussures et livraison.\n",
          '| Tenue | Pièce | Enseigne | Prix épisode | Prix lu | Prix de base | Stock | Fiche |', '|---|---|---|---|---|---|---|---|']
    k = 0
    for t in ep.E['tenues']:
        for pc in t['pieces']:
            r = res[k]; k += 1
            md.append(f"| {t['label']} ({t['total']}) | {pc['nom']} | {pc['enseigne']} | {pc['prix']} | {r['trouve'] if r['trouve'] is not None else 'non lu'} | {r['prix_de_base'] or ''} | {r['stock']} | {pc['url']} |")
    (ep.dir / 'produits.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    log('prix vérifiés ->', ep.out / 'prix.json', '+', ep.dir / 'produits.md')

# ------------------------------------------------------------------ voix (ElevenLabs, réglages Benjamin)
def lire_cle(fichier):
    v = os.environ.get('ELEVENLABS_API_KEY')
    if v: return v
    if fichier:
        for l in open(fichier):
            l = l.strip()
            if l.startswith('#') or '=' not in l: continue
            k, val = l.split('=', 1)
            if k.strip().removeprefix('export ').strip() == 'ELEVENLABS_API_KEY': return val.strip().strip('"').strip("'")
    stop("aucune clé : exporter ELEVENLABS_API_KEY ou passer --cle-fichier (seule cette variable y est lue)")
def cmd_voix(ep, a):
    mp3 = ep.voix / 'voice-raw.mp3'
    if mp3.exists() and not a.voix_neuve: log('voix déjà présente, rien à générer (--voix-neuve pour forcer)'); return
    if not a.depenser_credits: stop('la génération coûte des crédits : relancer avec --depenser-credits après accord d’Aymane')
    V = ep.E['voix']; text = ep.script(); K = lire_cle(a.cle_fichier)
    body = {'text': text, 'model_id': V['model_id'], 'language_code': V['language_code'], 'voice_settings': {'stability': V['stability'], 'similarity_boost': V['similarity_boost']}}
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{V['voice_id']}/with-timestamps?output_format={V['output_format']}"
    t0 = time.time()
    r = urllib.request.urlopen(urllib.request.Request(url, data=json.dumps(body).encode(), headers={'xi-api-key': K, 'Content-Type': 'application/json'}), timeout=300)
    h = {k.lower(): v for k, v in r.headers.items()}; d = json.load(r); del K
    mp3.write_bytes(base64.b64decode(d['audio_base64']))
    json.dump(d['alignment'], open(ep.voix / 'alignment.json', 'w'), ensure_ascii=False)
    n = len(list(ep.voix.glob('tts-essai*.json'))) + 1
    json.dump(dict(essai=n, **{k: V[k] for k in ('voice_id', 'voice_name', 'model_id', 'language_code', 'stability', 'similarity_boost', 'output_format')},
                   caracteres_envoyes=len(text), credits_factures=h.get('character-cost'), request_id=h.get('request-id'),
                   script_sha256=hashlib.sha256(text.encode()).hexdigest(), latence_s=round(time.time() - t0, 1),
                   le=datetime.datetime.now().astimezone().isoformat(timespec='seconds')), open(ep.voix / f'tts-essai{n}.json', 'w'), ensure_ascii=False, indent=1)
    log('voix générée, crédits facturés :', h.get('character-cost'))

# ------------------------------------------------------------------ mots + silences
def cmd_mots(ep, a):
    al = json.load(open(ep.voix / 'alignment.json'))
    words = []; cur = ''; cs = pe = None
    for c, st, en in zip(al['characters'], al['character_start_times_seconds'], al['character_end_times_seconds']):
        if c.isspace():
            if cur: words.append({'w': cur, 's': cs, 'e': pe}); cur = ''
            continue
        if not cur: cs = st
        cur += c; pe = en
    if cur: words.append({'w': cur, 's': cs, 'e': pe})
    json.dump(words, open(ep.voix / 'words-raw.json', 'w'), ensure_ascii=False)
    log(len(words), 'mots ->', ep.voix / 'words-raw.json')

def lire_audio(path, sr=48000, ch=1):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'f32le', '-ac', str(ch), '-ar', str(sr), '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch) if ch > 1 else np.frombuffer(raw, np.float32)
def ecrire_wav(path, x, sr=48000):
    x = np.atleast_2d(x.T).T if x.ndim == 1 else x
    with wave.open(str(path), 'wb') as f:
        f.setnchannels(x.shape[1] if x.ndim > 1 else 1); f.setsampwidth(2); f.setframerate(sr)
        f.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())
def cmd_silences(ep, a):
    SR = 48000; src = ep.voix / 'voice-raw.mp3'
    tmp = ep.out / 'voice-raw.wav'; run(['ffmpeg', '-v', 'error', '-y', '-i', str(src), '-ar', str(SR), '-ac', '1', str(tmp)])
    lg = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(tmp), '-af', 'silencedetect=n=-38dB:d=0.2', '-f', 'null', '-'], capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r'silence_start: ([0-9.]+)', lg)]; en = [float(x) for x in re.findall(r'silence_end: ([0-9.]+)', lg)]
    x = lire_audio(tmp, SR); K = SILENCE_GARDEE
    cuts = [(s + K / 2, e - K / 2) for s, e in zip(st, en) if s >= 0.05 and e - s > K]
    out = []; pos = 0; F = int(0.01 * SR)
    for s, e in cuts:
        seg = x[pos:int(s * SR)].copy()
        if out: seg[:F] *= np.linspace(0, 1, F)
        seg[-F:] *= np.linspace(1, 0, F); out.append(seg); pos = int(e * SR)
    seg = x[pos:].copy(); seg[:F] *= np.linspace(0, 1, F); out.append(seg); y = np.concatenate(out)
    def m(t):
        r = 0
        for s, e in cuts:
            if t >= e: r += e - s
            elif t > s: r += t - s
        return t - r
    w = json.load(open(ep.voix / 'words-raw.json'))
    for it in w: it['s'] = round(m(it['s']), 3); it['e'] = round(m(it['e']), 3)
    json.dump(w, open(ep.voix / 'words.json', 'w'), ensure_ascii=False)
    json.dump({'cuts': cuts, 'gardee_s': K}, open(ep.voix / 'silence-cuts.json', 'w'))
    ecrire_wav(ep.voix / 'voice.wav', y, SR); tmp.unlink()
    log(f'{len(cuts)} silences raccourcis (-{sum(e - s for s, e in cuts):.2f} s), voix {len(y) / SR:.2f} s')

# ------------------------------------------------------------------ timeline (script + words.json -> props.json)
norm = lambda s: re.sub(r"[.,:;!?«»\"]", '', s.lower()).strip()
def cmd_timeline(ep, a, W=None, sortie=None):
    E = ep.E; W = W if W is not None else json.load(open(ep.voix / 'words.json'))
    def F(i): return max(0, round(W[i]['s'] * FPS) + SHIFT)
    def idx(word, start=0, stop_=None):
        for i in range(start, stop_ or len(W)):
            if norm(W[i]['w']) == norm(word): return i
        stop(f'mot « {word} » introuvable après l’index {start} dans words.json (vérifier episode.json)')
    T = E['tenues']; nT = len(T)
    if not 1 <= nT <= 4: stop('le gabarit prévoit 1 à 4 tenues')
    i_prom = idx(E['promesse']['mot'])
    starts = []; c = i_prom
    for t in T: c = idx(t['mot'], c + 1); starts.append(c)
    i_ment = idx(E['mention']['mot'], starts[-1]); i_fin = idx(E['fin']['mot'], i_ment)
    looks, data, titles, subs = [], [], [], [[0, '']]
    titles.append(dict(at=0, **{k: E['accroche'][k] for k in ('l1', 'pre', 'kw', 'post')}, hl=F(idx(E['accroche']['mot_surligne']))))
    P = E['promesse']; titles.append(dict(at=F(i_prom), **{k: P[k] for k in ('l1', 'pre', 'kw', 'post')}, hl=F(idx(P['mot_surligne'], i_prom))))
    st = P['sous_titre']; subs.append([F(i_prom), st['texte'], st.get('surligne'), F(idx(st['mot'], i_prom)) if st.get('surligne') else None])
    for k, t in enumerate(T):
        s0 = starts[k]; s1 = starts[k + 1] if k + 1 < nT else i_ment
        a_ = F(s0); b_ = F(s1)
        lk = dict(n=k + 1, a=a_, b=b_); pd = []; c = s0
        for j, pc in enumerate(t['pieces'][:2]):
            ip = idx(pc['mot'], c); ipr = idx(pc['mot_prix'], ip)
            lk[f'piece{j + 1}'] = F(ip); lk[f'price{j + 1}'] = F(ipr)
            pd.append(dict(name=pc['nom'], brand=pc['enseigne'], price=pc['prix'], was=pc.get('prix_barre'),
                           brandAt=F(idx(pc['mot_enseigne'], ip)) if pc.get('mot_enseigne') else None,
                           wasAt=F(idx(pc['mot_barre'], ipr)) if pc.get('mot_barre') else None))
            c = ipr
        itot = idx(t.get('mot_total', 'Total'), c); lk['total'] = F(itot)
        ast = t['astuce']; ia = idx(ast['mot'], itot)
        lk['rot0'] = F(ia) - 6; lk['rot1'] = b_ - 8
        if t.get('rotation'):
            lk['rotSrc'] = f'rot-{k + 1}.mp4'; info = json.load(open(ep.pub / f'rot-{k + 1}.json')) if (ep.pub / f'rot-{k + 1}.json').exists() else {'frames': 181, 'ar': 1920 / 1080}
            lk['rotFrames'] = info['frames']; lk['rotAR'] = info['ar']
        else: lk['rotSrc'] = None
        looks.append(lk); data.append(dict(key=str(k + 1), label=t['label'], total=t['total'], pieces=pd))
        sl = t['sous_titre']; subs.append([a_, sl['texte'], sl.get('surligne'), F(idx(sl['mot'], s0)) if sl.get('surligne') else None])
        for s_ in t.get('sous_titres', []):   # pastilles en plus avant les pièces (rythme : un événement par seconde au moins)
            im_ = idx(s_['mot'], s0); subs.append([F(im_), s_['texte'], s_.get('surligne'), F(idx(s_['mot_surligne'], im_)) if s_.get('surligne') else None])
        titles.append(dict(at=a_, l1=t.get('titre_l1', f'Tenue {k + 1}'), pre='', kw=t['label'], post='', hl=F(idx(t.get('mot_label', t['label']), s0))))
        tt = ast['titre']; titles.append(dict(at=lk['rot0'] + 6, **{x: tt[x] for x in ('l1', 'pre', 'kw', 'post')}, hl=F(idx(tt['mot_surligne'], ia))))
        subs.append([F(ia) + 6, '', None, None])
        for s_ in ast.get('sous_titres', []):
            im = idx(s_['mot'], ia)
            subs.append([F(im), s_['texte'], s_.get('surligne'), F(idx(s_['mot_surligne'], im)) if s_.get('surligne') else None])
    M = E['mention']; titles.append(dict(at=F(i_ment), **{k: P[k] for k in ('l1', 'pre', 'kw', 'post')}))
    subs.append([F(i_ment), M['l1'] + ', ' + M['l2'], None, None])
    Fn = E['fin']; tt = Fn['titre']; titles.append(dict(at=F(i_fin), **{x: tt[x] for x in ('l1', 'pre', 'kw', 'post')}, type=True, hl=F(idx(tt['mot_surligne'], i_fin))))
    sf = Fn['sous_titre']; ir = idx(sf['mot'], i_fin)
    subs.append([F(ir), sf['texte'], sf.get('surligne'), F(idx(sf['mot_surligne'], ir)) if sf.get('surligne') else None])
    nums = []; c = ir
    for w_ in Fn['mots_numeros'][:nT]: c = idx(w_, c); nums.append(F(c))
    subs.sort(key=lambda x: x[0])
    # intro : les cartes des tenues entrent une par une sur des mots de l'intro, toutes posées avant intro.fin_s (5 s par défaut)
    I = E.get('intro', {}); duree = int(I.get('duree_images', 12)); fin = min(round(float(I.get('fin_s', 5)) * FPS), looks[0]['a'] - 6)
    mots = I.get('mots_cartes')
    if mots:
        ats = [None] * nT
        for key, w_ in mots.items():
            n_ = int(key)
            if not 1 <= n_ <= nT: stop(f'intro : tenue {key} inexistante')
            ats[n_ - 1] = F(idx(w_, 0, starts[0]))
        if None in ats: stop('intro : il faut un mot pour chaque tenue dans intro.mots_cartes')
    else:  # par défaut : la tenue de l'accroche d'abord, puis les autres réparties régulièrement
        ordre = [E['ouverture']] + [n_ for n_ in range(1, nT + 1) if n_ != E['ouverture']]
        ats = [0] * nT; span = fin - duree - 18
        for j, n_ in enumerate(ordre): ats[n_ - 1] = 6 + round(j * (span - 6) / max(1, nT - 1))
    late = [k + 1 for k, t_ in enumerate(ats) if t_ + duree > fin]
    if late: stop(f'intro : carte(s) {late} posée(s) après {fin / FPS:.2f} s, choisir des mots plus tôt')
    intro = dict(at=ats, duree=duree, fin=fin, numeros=bool(I.get('numeros', True)))
    log('intro : cartes ' + ', '.join(f"{k + 1}@{t_ / FPS:.2f}s" for k, t_ in enumerate(ats)) + f' ; posées avant {fin / FPS:.2f} s')
    props = dict(fps=FPS, total=math.ceil((W[-1]['e'] + 1.6) * FPS), openLook=E['ouverture'], looks=looks, looksData=data, titles=titles, subs=subs,
                 promise=F(i_prom), mention=F(i_ment), hors=F(idx(M['mot_l2'], i_ment)), mentionL1=M['l1'], mentionL2=M['l2'],
                 end=F(i_fin), reponds=F(ir), nums=nums, intro=intro, audio='mix.wav')
    sortie = sortie or ep.out / 'props.json'
    json.dump({'data': props}, open(sortie, 'w'), ensure_ascii=False, indent=1)
    log(f"timeline : {props['total']} images ({props['total'] / FPS:.1f} s) ->", sortie)
    return props

# ------------------------------------------------------------------ images : Léo détouré, vignettes sans peau ni chaussures, rotations
def peau(im):
    r, g, b = im[..., 0], im[..., 1], im[..., 2]; mx = np.maximum(np.maximum(r, g), b); mn = np.minimum(np.minimum(r, g), b)
    return (r > 95) & (g > 40) & (b > 20) & (mx - mn > 15) & (r > g + 12) & (r > b) & (r - b > 30)
def chroma_rb(rgb):
    return (rgb[..., 0] - rgb[..., 2]) / (rgb.sum(-1) + 1) * 3
def sans_mains(c):
    """Retire les mains posées contre le pantalon : pixels nettement plus « rouge-orangé » que la couleur médiane du tissu,
    dans la moitié haute du bas. Fonctionne aussi pour un tissu beige ou écru (la peau reste bien plus saturée)."""
    m0 = c[..., 3] > 40
    if m0.sum() < 100: return c
    H_, W_ = m0.shape; ys, xs = np.where(m0); cx = (xs.min() + xs.max()) / 2; hw = (xs.max() - xs.min()) / 2
    X = np.arange(W_)[None, :]; Y = np.arange(H_)[:, None]
    core = m0 & (np.abs(X - cx) < 0.3 * hw) & (Y > 0.1 * H_) & (Y < 0.6 * H_)
    med = np.median(chroma_rb(c[..., :3])[core]) if core.any() else 0
    main = m0 & (chroma_rb(c[..., :3]) - med > 0.2) & (c[..., 0] > c[..., 1]) & (Y < 0.5 * H_)
    from scipy import ndimage
    main = ndimage.binary_dilation(ndimage.binary_opening(main, iterations=2), iterations=7) & (Y < 0.55 * H_)
    c[..., 3] = np.where(main, 0, c[..., 3]); return c
def ourlet_auto(im, y0=700, y1=1200):
    """Ligne de séparation haut / bas : rupture de couleur la plus nette sur une bande centrale (x 455..625)."""
    band = im[y0:y1, 455:625]; a = band[..., 3] > 200
    rows = np.array([band[i][a[i], :3].mean(0) if a[i].sum() > 20 else [np.nan] * 3 for i in range(len(band))])
    ok = ~np.isnan(rows[:, 0]); best, by = -1, (y0 + y1) // 2
    for i in range(30, len(rows) - 30):
        if not ok[i]: continue
        up = rows[max(0, i - 40):i][ok[max(0, i - 40):i]]; dn = rows[i:i + 40][ok[i:i + 40]]
        if len(up) < 10 or len(dn) < 10: continue
        d = np.linalg.norm(np.median(up, 0) - np.median(dn, 0))
        if d > best: best, by = d, y0 + i
    return int(by)
def cmd_vignettes(ep, a):
    from PIL import Image, ImageFilter
    from scipy import ndimage
    (ep.pub / 'leo').mkdir(exist_ok=True); (ep.pub / 'produits').mkdir(exist_ok=True); (ep.pub / 'fonts').mkdir(exist_ok=True)
    for f in (MOTEUR / 'fonts').glob('*.ttf'): shutil.copy(f, ep.pub / 'fonts' / f.name)
    sess = None
    for k, t in enumerate(ep.E['tenues'], 1):
        cut_p = ep.pub / 'leo' / f'cut-{k}.png'
        if not cut_p.exists() or a.refaire:
            if sess is None:
                from rembg import remove, new_session; sess = new_session('isnet-general-use')
            im = Image.open(ep.p(t['image'])).convert('RGB').resize((1080, 1920), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.6, percent=70, threshold=2))
            remove(im, session=sess).save(cut_p)
        C = t.get('coupe', {}); SHOE = C.get('chaussures_y', 1590)
        im = np.array(Image.open(cut_p).convert('RGBA')).astype(float); brut = im.copy()
        HEM = C.get('ourlet_y', 890)
        if HEM == 'auto': HEM = ourlet_auto(brut); log(f'tenue {k} : ourlet détecté à y={HEM} (mettre cette valeur dans coupe.ourlet_y pour la figer)')
        sk = peau(im)
        if C.get('peau_cotes_seulement'):
            lim = np.zeros_like(sk); lim[:HEM + 5, :] = True; lim[:, :385] = True; lim[:, 690:] = True; sk &= lim
        al = Image.fromarray(np.where(sk, 0, im[..., 3]).astype(np.uint8)).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(5))
        im[..., 3] = np.minimum(np.array(al), im[..., 3]); o = Image.fromarray(im.astype(np.uint8))
        for name, (y0, y1) in {'haut': (270, HEM - C.get('haut_marge_bas', 4)), 'bas': (HEM + C.get('bas_marge_haut', 48), SHOE)}.items():
            c = np.array(o.crop((0, y0, 1080, y1))).astype(float)
            if name == 'bas': c = sans_mains(brut[y0:y1].copy())   # bas : pas de détection de peau globale (un chino écru y ressemble), mains retirées par chromaticité
            m = c[..., 3] > 40; m = ndimage.binary_opening(m, iterations=(9 if name == 'haut' else 4)); lab, n = ndimage.label(m)
            if n:
                sz = ndimage.sum(m, lab, range(1, n + 1))
                m = np.isin(lab, np.where(sz >= (0.25 * sz.max() if name == 'bas' else sz.max()))[0] + 1)   # bas : les deux jambes si elles sont séparées
            if name == 'bas':
                row = m[int((y1 - y0) * 0.45)]; xs = np.where(row)[0]; bx0, bx1 = xs.min() + 2, xs.max() - 2; m[:, :bx0] = False; m[:, bx1:] = False
            c[..., 3] = np.where(m, c[..., 3], 0)
            ys, xs = np.where(m); cx = int(round((xs.min() + xs.max()) / 2)); Wd = c.shape[1]
            mir = c[:, np.clip(2 * cx - np.arange(Wd), 0, Wd - 1)]; hole = (c[..., 3] < 40) & (mir[..., 3] > 200)
            if name == 'bas':
                zone = np.zeros_like(hole); zone[:int(c.shape[0] * 0.36)] = True
                zone &= (np.abs(np.arange(Wd) - cx)[None, :] > 0.62 * (xs.max() - xs.min()) / 2)
                zone[:, :bx0] = False; zone[:, bx1:] = False   # jamais de remplissage hors du contour de la jambe (évite les bosses)
                hole &= zone; c[hole] = mir[hole]
            c = Image.fromarray(c.astype(np.uint8)); c.crop(c.getchannel('A').point(lambda v: 255 if v > 40 else 0).getbbox()).save(ep.pub / 'produits' / f'{name}-{k}.png')
        if t.get('rotation'):
            src = ep.p(t['rotation']); dst = ep.pub / f'rot-{k}.mp4'
            w_, h_ = map(int, subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', str(src)], capture_output=True, text=True).stdout.strip().split(','))
            vf = 'fps=30' if w_ % 2 == 0 and w_ <= 1080 else 'crop=1080:1920:(iw-1080)/2:0,fps=30'
            if not dst.exists() or a.refaire:
                run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-i', str(src), '-an', '-vf', vf, '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', str(dst)])
            info = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames,width,height', '-of', 'json', str(dst)], capture_output=True, text=True).stdout)['streams'][0]
            nb, ww, hh = int(info['nb_read_frames']), int(info['width']), int(info['height'])
            json.dump({'frames': nb, 'ar': hh / ww}, open(ep.pub / f'rot-{k}.json', 'w'))
    # planche de contrôle des vignettes
    sheet = Image.new('RGB', (220 * len(ep.E['tenues']), 600), (246, 235, 223))
    for k in range(1, len(ep.E['tenues']) + 1):
        for r_, z in enumerate(('haut', 'bas')):
            v = Image.open(ep.pub / 'produits' / f'{z}-{k}.png').convert('RGBA'); v.thumbnail((210, 290))
            sheet.paste(v, ((k - 1) * 220 + (220 - v.width) // 2, r_ * 300 + (300 - v.height) // 2), v)
    sheet.save(ep.out / 'planche-vignettes.png'); log('vignettes + Léo détouré + rotations prêts ; contrôle :', ep.out / 'planche-vignettes.png')

# ------------------------------------------------------------------ audio : musique originale + effets discrets + réduction sous la voix
def cmd_audio(ep, a):
    sys.path.insert(0, str(MOTEUR / 'cli')); import musique
    T = json.load(open(ep.out / 'props.json'))['data']; SR = 48000; N = int(T['total'] / FPS * SR)
    musique.generer(T['total'], str(ep.out / 'music.wav'))
    def rd(p, ch):
        x = lire_audio(p, SR, ch); x = x.reshape(-1, ch); o = np.zeros((N, ch), np.float32); o[:min(N, len(x))] = x[:N]; return o
    voice = rd(ep.voix / 'voice.wav', 1)[:, 0]; music = rd(ep.out / 'music.wav', 2)
    rng = np.random.default_rng(7)
    def whoosh(l=0.42, amp=0.10):
        n = int(l * SR); x = np.arange(n) / SR; nz = np.convolve(rng.standard_normal(n), np.ones(12) / 12, 'same'); return nz * np.sin(np.pi * x / l) ** 2 * amp
    def pop(f=880, amp=0.07):
        n = int(0.09 * SR); x = np.arange(n) / SR; fr = f * (1 + 0.6 * np.exp(-x * 60)); return np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-x * 45) * amp
    def chime(amp=0.05):
        n = int(1.0 * SR); x = np.arange(n) / SR; return sum(np.sin(2 * np.pi * f * x) * np.exp(-x * 4) * g for f, g in [(1318, 1), (1976, .5), (2637, .25)]) * amp
    sfx = np.zeros((N, 2), np.float32); ev = []
    def add(s, frame, pan=0.0, kind=''):
        i = int(frame / FPS * SR); n = min(len(s), N - i)
        if n <= 0: return
        sfx[i:i + n, 0] += s[:n] * (1 - pan); sfx[i:i + n, 1] += s[:n] * (1 + pan); ev.append((int(frame), kind))
    for k, l in enumerate(T['looks']):
        add(whoosh(), l['a'] - 6, 0.2 * (-1) ** k, 'whoosh')
        add(pop(784), l['piece1'] - 2, -0.3, 'pop'); add(pop(880), l['piece2'] - 2, 0.3, 'pop')
        add(pop(1046, 0.06), l['total'] - 1, 0, 'pop')
        if l.get('rotSrc'): add(whoosh(0.5, 0.08), l['rot0'], 0, 'whoosh'); add(chime(), l['rot0'] + 10, 0, 'chime')
    add(pop(988, 0.07), T['end'] + 2, 0, 'pop'); add(chime(0.045), T['nums'][-1] + 16, 0, 'chime')
    env = np.abs(voice); w = int(0.02 * SR); env = np.sqrt(np.convolve(env ** 2, np.ones(w) / w, 'same'))
    g = np.zeros_like(env); a_att = np.exp(-1 / (0.03 * SR)); a_rel = np.exp(-1 / (0.30 * SR)); s = 0.0; act = (env > 0.02).astype(np.float32)
    for i in range(0, N, 48):
        tgt = act[i]; c = (a_att if tgt > s else a_rel) ** 48; s = tgt + (s - tgt) * c; g[i:i + 48] = s
    mg = 0.2 - (0.2 - 0.055) * g
    mix = music * mg[:, None] + 0.45 * sfx + np.stack([voice, voice], 1); mix = mix / max(1e-9, np.abs(mix).max()) * 0.89
    ecrire_wav(ep.pub / 'mix.wav', mix, SR); json.dump(sorted(ev), open(ep.out / 'sfx-events.json', 'w'))
    db = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12); vm = act > 0.5
    log(f"{len(ev)} effets ; musique {db((music * mg[:, None])[vm, 0]) - db(voice[vm]):.1f} dB sous la voix ; crête effets {20 * np.log10(0.45 * np.abs(sfx).max()):.1f} dBFS (voix RMS {db(voice[vm]):.1f})")

# ------------------------------------------------------------------ rendu + mastering
def cmd_rendu(ep, a):
    raw = ep.out / 'rendu-brut.mp4'; final = ep.out / f'{ep.id}.mp4'
    run(['nice', '-n', '10', 'npx', 'remotion', 'render', 'src/index.ts', 'Episode', str(raw), f'--props={ep.out / "props.json"}', f'--public-dir={ep.pub}',
         '--codec=h264', '--crf=16', '--audio-codec=aac', '--log=error'], cwd=MOTEUR)
    lg = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(raw), '-af', 'loudnorm=I=-13:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
    d = json.loads(lg[lg.rindex('{'):lg.rindex('}') + 1])
    ln = f"loudnorm=I=-13:TP=-1.5:LRA=11:measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}:measured_thresh={d['input_thresh']}:offset={d['target_offset']}:linear=true"
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(raw), '-c:v', 'copy', '-af', ln, '-ar', '48000', '-c:a', 'aac', '-b:a', '192k', str(final)])
    raw.unlink(); log('rendu ->', final)

# ------------------------------------------------------------------ QA
def cmd_qa(ep, a):
    V = ep.out / f'{ep.id}.mp4'; q = ep.out / 'qa'; q.mkdir(exist_ok=True); R = {}
    pr = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_name,width,height,r_frame_rate,sample_rate', '-show_entries', 'format=duration', '-of', 'json', str(V)], capture_output=True, text=True).stdout)
    R['format'] = dict(duree_s=float(pr['format']['duration']), flux=[{k: s.get(k) for k in ('codec_name', 'width', 'height', 'r_frame_rate', 'sample_rate')} for s in pr['streams']])
    eb = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(V), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    R['lufs'] = float(re.findall(r'I:\s+(-?[0-9.]+) LUFS', eb)[-1]); R['crete_dbfs'] = float(re.findall(r'Peak:\s+(-?[0-9.]+) dBFS', eb)[-1])
    tile = '10x8' if R['format']['duree_s'] > 64 else '8x8'
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(V), '-vf', f"fps=1,scale=216:-1,drawtext=text='%{{pts\\:hms}}':fontcolor=yellow:fontsize=16:box=1:boxcolor=black,tile={tile}", '-frames:v', '1', str(q / 'planche-1ips.png')])
    def masque(x0, x1, y0, y1, col):
        return ','.join([f'drawbox=x=0:y=0:w={x0}:h=1920:c={col}@0.45:t=fill', f'drawbox=x={x1}:y=0:w={1080 - x1}:h=1920:c={col}@0.45:t=fill',
                         f'drawbox=x=0:y=0:w=1080:h={y0}:c={col}@0.45:t=fill', f'drawbox=x=0:y={y1}:w=1080:h={1920 - y1}:c={col}@0.45:t=fill'])
    for nom, col in (('TikTok', 'red'), ('Reels', 'blue')):
        run(['ffmpeg', '-v', 'error', '-y', '-i', str(V), '-vf', f"fps=1,{masque(*SAFE[nom], col)},scale=216:-1,tile={tile}", '-frames:v', '1', str(q / f'planche-masque-{nom.lower()}.png')])
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(V), '-frames:v', '1', str(q / 'frame-000.png')])
    # zones : bords nets hors zone, image par image à 10 i/s
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(V), '-vf', 'fps=10', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, 1920, 1080)
    R['zones'] = {}
    for nom, (x0, x1, y0, y1) in SAFE.items():
        bad = []
        for i, f in enumerate(fr):
            f = f.astype(np.int16); e = np.maximum(np.abs(np.diff(f, axis=1))[:-1, :], np.abs(np.diff(f, axis=0))[:, :-1]) > 28
            msk = np.ones_like(e); msk[y0:y1, x0:x1] = False; n = int((e & msk).sum())
            if n > 40: bad.append(round(i / 10, 1))
        R['zones'][nom] = dict(images_hors_zone=len(bad), instants=bad[:20])
    # événements informatifs (bloc de 60 px qui change) et passages figés
    sm = fr[:, ::4, ::4].astype(float); d = np.abs(np.diff(sm, axis=0)); B = 15
    blk = d[:, :480 // B * B, :270 // B * B].reshape(len(d), 480 // B, B, 270 // B, B).mean(axis=(2, 4)).max(axis=(1, 2))
    ev = blk >= 12; n = len(sm) // 10; per = [int(ev[i * 10:(i + 1) * 10].sum()) for i in range(n)]
    best = cur = 0
    for s in blk < 2.0: cur = cur + 1 if s else 0; best = max(best, cur)
    R['rythme'] = dict(evenements_par_s_moyenne=round(float(ev.sum()) / n, 2), secondes_sans_evenement=[i for i, p in enumerate(per) if p == 0], plus_long_fige_s=best / 10)
    # sync des prix : whisper sur la piste finale, comparé à l'instant d'affichage
    if not a.sans_whisper:
        from faster_whisper import WhisperModel
        au = lire_audio(V, 16000); m = WhisperModel('small', device='cpu', compute_type='int8', cpu_threads=4)
        seg, _ = m.transcribe(au, language='fr', beam_size=5, word_timestamps=True); ws = [(w.word.strip(), w.start) for s in seg for w in s.words]
        T = json.load(open(ep.out / 'props.json'))['data']; S = []
        for k, l in enumerate(T['looks']):
            for key in ('price1', 'price2'):
                t = l[key] / FPS; near = min(ws, key=lambda x: abs(x[1] - t)); S.append(dict(tenue=k + 1, quoi=key, affiche_s=round(t, 2), entendu=near[0], ecart_ms=round((near[1] - t) * 1000)))
        R['sync_prix'] = dict(detail=S, ecart_max_ms=max(abs(x['ecart_ms']) for x in S))
    json.dump(R, open(q / 'qa.json', 'w'), ensure_ascii=False, indent=1)
    log(f"QA : {R['format']['duree_s']:.1f} s, {R['lufs']} LUFS, crête {R['crete_dbfs']} dBFS, zones {[(k, v['images_hors_zone']) for k, v in R['zones'].items()]}, "
        f"rythme {R['rythme']}, sync prix max {R.get('sync_prix', {}).get('ecart_max_ms')} ms -> {q}")
    pb = []
    if not -14 <= R['lufs'] <= -12: pb.append('niveau hors -14..-12 LUFS')
    if any(v['images_hors_zone'] for v in R['zones'].values()): pb.append('contenu hors zone sûre')
    if R.get('sync_prix') and R['sync_prix']['ecart_max_ms'] > 250: pb.append('prix décalé de plus de 250 ms')
    if pb: log('ATTENTION :', ' ; '.join(pb))

# ------------------------------------------------------------------ verifier (phase 1, sans réseau ni crédit)
S_PAR_CAR = 78.64 / 1453        # calibré sur l'épisode de référence (voix Benjamin, silences ramenés à 0,32 s)
CREDITS_PAR_CAR = 639 / 1454    # facturé en eleven_v4 sur le script de référence
DUREE_CIBLE = (65, 75)
UNITES = 'zéro un deux trois quatre cinq six sept huit neuf dix onze douze treize quatorze quinze seize'.split()
DIZ = {2: 'vingt', 3: 'trente', 4: 'quarante', 5: 'cinquante', 6: 'soixante'}
MOIS = 'janvier février mars avril mai juin juillet août septembre octobre novembre décembre'.split()
def fr_nombre(n):
    """0..99 en lettres, orthographe à traits d'union (comme dans les scripts)."""
    if n < 17: return UNITES[n]
    if n < 20: return 'dix-' + UNITES[n - 10]
    if n < 70:
        d, u = divmod(n, 10); return DIZ[d] + ('' if u == 0 else '-et-un' if u == 1 else '-' + UNITES[u])
    if n < 80: return 'soixante-' + ('et-onze' if n == 71 else fr_nombre(n - 60))
    return 'quatre-vingt' + ('s' if n == 80 else '-' + fr_nombre(n - 80))
def fr_variantes(n):
    v = fr_nombre(n); return {v, v.replace('-et-', ' et '), v.replace('-', ' ')}
def mots_simules(texte):
    """Faux words.json : temps proportionnels au nombre de caractères (calibrage de la référence)."""
    W = []; t = 0.0
    for w in texte.split():
        d = (len(w) + 1) * S_PAR_CAR; W.append({'w': w, 's': round(t, 3), 'e': round(t + d - S_PAR_CAR, 3)}); t += d
    return W
INTERDITS = [(r'\u2014', 'tiret cadratin'), (r'\u2013', 'tiret demi-cadratin (préférer « - » ou « : »)'), (r'look\s+complet', '« look complet » interdit'),
             (r'(?-i:\b(IA|AI|AIGC)\b)', 'mention IA (déclarée seulement via l’option de la plateforme)'), (r'intelligence artificielle|g[ée]n[ée]r[ée]e? par', 'mention IA'),
             (r'garanti|meilleur prix|le moins cher du march', 'promesse non prouvable'), (r'envoie (ça|cette vid[ée]o)|partage (à|a) ', 'appât d’engagement interdit')]
def textes_visibles(E):
    out = []
    def walk(x, chemin):
        if isinstance(x, dict):
            for k, v in x.items():
                if k in ('url', 'image', 'rotation', 'script', 'voix', 'id', 'date_releve', 'publication', 'desc_en') or k.startswith('mot'): continue
                walk(v, f'{chemin}.{k}')
        elif isinstance(x, list):
            for i, v in enumerate(x): walk(v, f'{chemin}[{i}]')
        elif isinstance(x, str): out.append((chemin, x))
    walk(E, 'episode'); return out
def cmd_verifier(ep, a):
    E = ep.E; txt = ep.script(); err = []; avert = []; R = {'id': ep.id}
    for chemin, t in [('script', txt)] + textes_visibles(E):
        for rx, why in INTERDITS:
            if re.search(rx, t, re.I): err.append(f'{chemin} : {why} -> « {t[:60]} »')
    if re.search(r'\d', txt): err.append('script : chiffres trouvés, écrire les nombres en lettres pour la voix')
    # chaque surlignage doit exister tel quel dans son texte (sinon le texte se duplique à l'écran)
    def surl(x, chemin):
        if isinstance(x, dict):
            if x.get('surligne') and x.get('texte') is not None and x['surligne'] not in x['texte']:
                err.append(f'{chemin} : surligne « {x["surligne"]} » absent de « {x["texte"]} » (respecter majuscules et accents)')
            for k_, v in x.items(): surl(v, f'{chemin}.{k_}')
        elif isinstance(x, list):
            for i_, v in enumerate(x): surl(v, f'{chemin}[{i_}]')
    surl(E, 'episode')
    # durée, crédits
    n = len(txt); dur = n * S_PAR_CAR + 1.6
    R.update(caracteres=n, duree_estimee_s=round(dur, 1), credits_estimes=round(n * CREDITS_PAR_CAR))
    if not DUREE_CIBLE[0] <= dur <= DUREE_CIBLE[1]: avert.append(f'durée estimée {dur:.1f} s hors cible {DUREE_CIBLE[0]}..{DUREE_CIBLE[1]} s ({n} caractères)')
    accroche = re.split(r'(?<=[.?!])\s', txt, maxsplit=1)[0]; R['accroche_mots'] = len(accroche.split())
    if len(accroche.split()) > 15: avert.append(f'accroche de {len(accroche.split())} mots (viser 12 au plus)')
    # totaux et prix dits
    paras = [norm(p_) for p_ in re.split(r'\n\s*\n', txt)]
    for k, t in enumerate(E['tenues'], 1):
        som = round(sum(prix_num(pc['prix']) for pc in t['pieces']), 2)
        if abs(som - prix_num(t['total'])) > 0.005: err.append(f'tenue {k} : total {t["total"]} mais somme des pièces {som:.2f}')
        sec = next((p_ for p_ in paras[1:] if p_.split()[0].rstrip(',') == norm(t['mot']).rstrip(',')), ' '.join(paras))
        for quoi, val in [(pc['nom'], pc['prix']) for pc in t['pieces']] + [('total', t['total'])] + [(pc['nom'] + ' (barré)', pc['prix_barre']) for pc in t['pieces'] if pc.get('prix_barre')]:
            e_, c_ = divmod(round(prix_num(val) * 100), 100)
            ok = any(v in sec for v in fr_variantes(e_)) and (c_ == 0 or any(v in sec for v in fr_variantes(c_)))
            if not ok: err.append(f'tenue {k} : prix {val} ({quoi}) affiché mais pas dit dans la section « {t["mot"]} »')
    # prix dans les titres : doivent être dits au plus tard quand le titre apparaît
    for bloc in ('accroche', 'promesse'):
        B = E[bloc]; full = ' '.join(B.get(x, '') for x in ('l1', 'pre', 'kw', 'post'))
        for m in re.finditer(r'(\d+)\s*€', full):
            mots_ = [norm(w) for w in txt.split()]; cible = fr_variantes(int(m.group(1)))
            pos = next((i for i, w in enumerate(mots_) if w in cible), None)
            lim = 0 if bloc == 'accroche' else next((i for i, w in enumerate(mots_) if w == norm(B['mot'])), 0)
            if pos is None: err.append(f'{bloc} : {m.group(0)} affiché mais jamais dit')
            elif bloc == 'accroche' and pos * 1.0 > 12: avert.append(f'accroche : {m.group(0)} affiché dès l’image 0 mais dit seulement au mot {pos + 1}')
            elif bloc == 'promesse' and pos > lim: err.append(f'promesse : {m.group(0)} affiché (mot « {B["mot"]} ») avant d’être dit')
    # date du relevé dite et affichée
    d = datetime.date.fromisoformat(E['date_releve'])
    if f'{d.day:02d}/{d.month:02d}' not in E['mention']['l1']: err.append(f'mention : la date {d:%d/%m} du relevé n’est pas dans « {E["mention"]["l1"]} »')
    if not any(f'{v} {MOIS[d.month - 1]}' in norm(txt) for v in fr_variantes(d.day) | ({'premier'} if d.day == 1 else set())): err.append(f'script : la date du relevé ({d.day} {MOIS[d.month - 1]}) n’est pas dite')
    if 'hors chaussures et livraison' not in norm(txt): err.append('script : « hors chaussures et livraison » absent')
    # timeline simulée (tous les mots déclencheurs trouvés, intro avant 5 s)
    try:
        W = mots_simules(txt); props = cmd_timeline(ep, a, W, ep.out / 'props-simule.json')
        fin_i = props['intro']['fin'] / FPS; last = max(props['intro']['at']) / FPS + props['intro']['duree'] / FPS
        R['intro_cartes_s'] = [round(x / FPS, 2) for x in props['intro']['at']]
        if last > 4.5: avert.append(f'intro : dernière carte posée vers {last:.1f} s (estimation), marge faible avant 5 s')
    except SAErreur as e: err.append(f'timeline simulée : {e}')
    # médias attendus (à générer en phase 2)
    manq = []
    for k, t in enumerate(E['tenues'], 1):
        for key, quoi in (('image', 'image Léo en tenue'), ('rotation', 'rotation 360°')):
            if t.get(key) and not ep.p(t[key]).exists(): manq.append(dict(tenue=k, type=quoi, fichier=t[key]))
    R['medias_manquants'] = manq; R['voix_presente'] = (ep.voix / 'voice-raw.mp3').exists()
    pr = ep.out / 'prix.json'
    R['prix_verifies_le'] = json.load(open(pr))['verifie_le'] if pr.exists() else None
    if not R['prix_verifies_le']: avert.append('prix jamais vérifiés : lancer « prix »')
    R['erreurs'] = err; R['avertissements'] = avert
    json.dump(R, open(ep.out / 'verif.json', 'w'), ensure_ascii=False, indent=1)
    for x in err: log('ERREUR  ', x)
    for x in avert: log('ATTENTION', x)
    log(f"{ep.id} : {n} caractères, ~{dur:.0f} s, ~{R['credits_estimes']} crédits ElevenLabs, {sum(1 for m in manq if m['type'].startswith('image'))} images et "
        f"{sum(1 for m in manq if m['type'].startswith('rotation'))} rotations à générer -> {ep.out / 'verif.json'}")
    if err: stop(f'{len(err)} erreur(s) de vérification')
    return R

# ------------------------------------------------------------------ prompts (images Léo + rotations, à passer à GenerateImage / GenerateVideo)
LEO = MOTEUR.parent / 'leo'
def bloc_prompt_base():
    t = (LEO / 'prompts.md').read_text(encoding='utf-8')
    m = re.search(r'## 1\..*?```\n(.*?)```', t, re.S)
    return m.group(1).strip() if m else ''
def cmd_prompts(ep, a):
    base = bloc_prompt_base(); E = ep.E; (ep.media / 'produits').mkdir(exist_ok=True); L_ = []
    L_.append(f"# Prompts de génération : {E['titre']}\n\nFichier produit par `sa.py prompts` le {datetime.date.today():%d/%m/%Y}. PAYANT : rien n'est généré sans le oui d'Aymane.\n"
              "Images : GenerateImage, `aspect_ratio` 9:16, références dans l'ordre indiqué. Rotations : GenerateVideo à partir de l'image validée (clip 6 s, vertical).\n"
              "Relire chaque image (visage de Léo, couleur et coupe des pièces, aucun logo) avant de lancer sa rotation. Déposer les fichiers aux chemins indiqués, puis `sa.py vignettes` et régler `coupe`.\n")
    for k, t in enumerate(E['tenues'], 1):
        refs = [str(LEO / 'identite' / 'maitre-visage.jpg'), str(LEO / 'identite' / 'maitre-corps.jpg')]
        for j, pc in enumerate(t['pieces'], 1):
            dst = ep.media / 'produits' / f'{k}-{j}-{pc["zone"]}.jpg'
            if not dst.exists() and 'jules.com' in pc['url'] and not a.sans_reseau:
                try:
                    h = lire_url(urllib.request.Request(pc['url'], headers={'User-Agent': UA})).decode('utf-8', 'ignore')
                    im = re.search(r'<meta property="og:image" content="([^"]+)"', h)
                    if im: dst.write_bytes(lire_url(urllib.request.Request(html_unescape(im.group(1)), headers={'User-Agent': UA})))
                except Exception as e: log('photo produit non téléchargée :', pc['nom'], type(e).__name__)
            if dst.exists(): refs.append(str(dst))
        tenue = '; '.join(('top: ' if pc['zone'] == 'haut' else 'bottom: ') + (pc.get('desc_en') or pc['nom']) for pc in t['pieces'])
        bloc = (f"CHANGE ONLY HIS CLOTHES. Outfit: {tenue}. Plain clean white low-top sneakers without logo. No jewelry, no hat, no glasses. "
                "The garments must match the product photos in the references: same color, same cut, same fabric look. No logo, no text, no brand label anywhere.")
        pose = ("Pose: standing straight, full body visible from hair to shoes, facing the camera almost front-on, arms relaxed at his sides, calm neutral expression "
                "with a very slight closed-mouth smile. Framing: centered, generous empty space above the head and below the shoes.")
        prompt = base.replace('[TENUE]', bloc).replace('[POSE ET CADRAGE]', pose) if base else bloc + '\n' + pose
        L_.append(f"\n## Tenue {k} : {t['label']} ({t['total']})\n\n### Image -> `{ep.dir.name}/{t['image']}`\n\nRéférences :\n" + '\n'.join(f'- `{r}`' for r in refs) +
                  "\n\n(Recadrer toute photo produit qui montre un logo ou un texte avant de la passer.)\n\n```\n" + prompt + "\n```\n")
        if t.get('rotation'):
            L_.append(f"### Rotation 360° -> `{ep.dir.name}/{t['rotation']}`\n\nImage de départ : l'image validée ci-dessus.\n\n```\n"
                      "The same young man, same outfit, same light gray studio, slowly turns a full 360 degrees in place like a fashion mannequin on a turntable, "
                      "at a constant speed, arms relaxed, feet staying on the same spot, ending facing the camera again. Static camera, no zoom, no cut, "
                      "full body always in frame with space above the head and below the shoes. No text, no logo.\n```\n")
    (ep.media / 'prompts.md').write_text(''.join(L_), encoding='utf-8')
    log('prompts ->', ep.media / 'prompts.md')
def html_unescape(s):
    import html; return html.unescape(s)

# ------------------------------------------------------------------ nouveau (squelette d'épisode)
def cmd_nouveau(a):
    dst = MOTEUR / 'episodes' / a.episode
    if dst.exists(): stop(f'{dst} existe déjà')
    src = MOTEUR / 'episodes' / (a.depuis or 'leo-4-tenues-50e')
    dst.mkdir(parents=True); (dst / 'media').mkdir()
    E = json.load(open(src / 'episode.json', encoding='utf-8')); E['id'] = a.episode; E['date_releve'] = f'{datetime.date.today():%Y-%m-%d}'
    for t in E['tenues']:
        slug = re.sub(r'[^a-z0-9]+', '-', t['label'].lower()).strip('-'); t['image'] = f'media/{a.episode}-{slug}.jpg'; t['rotation'] = f'media/rotation-{a.episode}-{slug}.mp4'
    E['publication'] = dict(date_prevue='AAAA-MM-JJ', plateformes=['TikTok', 'Instagram Reels'], forme_accroche='à remplir')
    json.dump(E, open(dst / 'episode.json', 'w'), ensure_ascii=False, indent=2)
    shutil.copy(src / 'script.txt', dst / 'script.txt')
    log(f'épisode créé depuis {src.name} -> {dst} (réécrire script.txt et episode.json, puis « verifier »)')

# ------------------------------------------------------------------ lot (plusieurs épisodes d'un coup)
ETAPES_LOT = ['verifier', 'prix', 'prompts', 'voix', 'tout', 'qa', 'rendu', 'timeline', 'vignettes']
def lire_lot(chemin):
    p = Path(chemin)
    if p.is_dir(): return dict(nom=p.name, episodes=[dict(id=d.name, dossier=str(d)) for d in sorted(p.iterdir()) if (d / 'episode.json').exists()])
    L = json.load(open(p, encoding='utf-8'))
    for e in L['episodes']: e.setdefault('dossier', str(MOTEUR / 'episodes' / e['id']))
    return L
def cmd_lot(a):
    L = lire_lot(a.episode); etapes = a.etape.split(',')
    for e_ in etapes:
        if e_ not in ETAPES_LOT: stop(f'étape « {e_} » inconnue pour un lot ({", ".join(ETAPES_LOT)})')
    if 'voix' in etapes or 'tout' in etapes:
        if a.depenser_credits and not a.oui_aymane: stop('lot avec crédits : ajouter --oui-aymane (à n’utiliser qu’après son accord écrit)')
    rows = []
    for e in L['episodes']:
        r = dict(id=e['id'], date=e.get('date', ''), statut='ok', detail='')
        try:
            ep = Ep(e['dossier'])
            for e_ in etapes:
                log(f'==== {e["id"]} : {e_}')
                res = {'verifier': cmd_verifier, 'prix': cmd_prix, 'prompts': cmd_prompts, 'voix': cmd_voix, 'tout': cmd_tout, 'qa': cmd_qa,
                       'rendu': cmd_rendu, 'timeline': cmd_timeline, 'vignettes': cmd_vignettes}[e_](ep, a)
            v = ep.out / 'verif.json'
            if v.exists():
                V = json.load(open(v)); r.update({k: V.get(k) for k in ('caracteres', 'duree_estimee_s', 'credits_estimes', 'medias_manquants', 'avertissements', 'prix_verifies_le')})
            r['titre'] = ep.E['titre']; r['tenues'] = ' / '.join(f"{t['label']} {t['total']}" for t in ep.E['tenues'])
            mp4 = ep.out / f'{ep.id}.mp4'; r['video'] = str(mp4) if mp4.exists() else ''
        except SAErreur as x: r['statut'] = 'ERREUR'; r['detail'] = str(x)
        except Exception as x: r['statut'] = 'ERREUR'; r['detail'] = f'{type(x).__name__}: {x}'
        rows.append(r)
    dl = MOTEUR / 'out' / 'lots' / L.get('nom', 'lot'); dl.mkdir(parents=True, exist_ok=True)
    tot_c = sum(r.get('caracteres') or 0 for r in rows); tot_cr = sum(r.get('credits_estimes') or 0 for r in rows)
    nimg = sum(1 for r in rows for m in (r.get('medias_manquants') or []) if m['type'].startswith('image'))
    nrot = sum(1 for r in rows for m in (r.get('medias_manquants') or []) if m['type'].startswith('rotation'))
    md = [f"# Lot {L.get('nom', '')} ({', '.join(etapes)}), {datetime.datetime.now().astimezone():%d/%m/%Y %H:%M} (heure de Paris)\n",
          '| Date | Épisode | Statut | Tenues | Caractères | Durée est. | Crédits est. | À générer | Remarques |', '|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        mm = r.get('medias_manquants') or []
        md.append(f"| {r['date']} | {r['id']} | {r['statut']} | {r.get('tenues', '')} | {r.get('caracteres', '')} | {r.get('duree_estimee_s', '')} s | {r.get('credits_estimes', '')} | "
                  f"{sum(1 for m in mm if m['type'].startswith('image'))} img, {sum(1 for m in mm if m['type'].startswith('rotation'))} rot | {r['detail'] or '; '.join(r.get('avertissements') or [])} |")
    md.append(f"\nTotal : {tot_c} caractères, environ {tot_cr} crédits ElevenLabs (une génération par épisode, sans nouvel essai), {nimg} images Léo et {nrot} rotations 360° à générer.\n")
    (dl / 'rapport.md').write_text('\n'.join(md), encoding='utf-8'); json.dump(rows, open(dl / 'rapport.json', 'w'), ensure_ascii=False, indent=1)
    log('rapport du lot ->', dl / 'rapport.md')
    if any(r['statut'] != 'ok' for r in rows): stop('au moins un épisode du lot est en erreur (voir le rapport)')

# ------------------------------------------------------------------ tout
def cmd_tout(ep, a):
    if not a.sans_prix: cmd_prix(ep, a)
    if not (ep.voix / 'voice-raw.mp3').exists() or a.voix_neuve: cmd_voix(ep, a)
    else: log('voix existante réutilisée (aucun crédit dépensé)')
    cmd_mots(ep, a); cmd_silences(ep, a); cmd_vignettes(ep, a); cmd_timeline(ep, a); cmd_audio(ep, a); cmd_rendu(ep, a); cmd_qa(ep, a)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('commande', choices=['prix', 'voix', 'mots', 'silences', 'timeline', 'vignettes', 'audio', 'rendu', 'qa', 'tout', 'verifier', 'prompts', 'nouveau', 'lot'])
    ap.add_argument('episode', help='episodes/<id> ; pour « nouveau » : le nouvel id ; pour « lot » : un fichier lots/<nom>.json ou un dossier d’épisodes')
    ap.add_argument('--depenser-credits', action='store_true', help='autorise la génération de voix payante')
    ap.add_argument('--oui-aymane', action='store_true', help='« lot » : confirme l’accord écrit d’Aymane pour dépenser des crédits sur tout le lot')
    ap.add_argument('--voix-neuve', action='store_true', help='régénère la voix même si elle existe')
    ap.add_argument('--cle-fichier', help='fichier .env où lire UNIQUEMENT ELEVENLABS_API_KEY')
    ap.add_argument('--refaire', action='store_true', help='refait le détourage et les rotations')
    ap.add_argument('--sans-whisper', action='store_true', help='QA sans vérification de sync par transcription')
    ap.add_argument('--sans-prix', action='store_true', help='« tout » sans revérifier les prix')
    ap.add_argument('--sans-reseau', action='store_true', help='« prompts » sans télécharger les photos produit')
    ap.add_argument('--etape', default='verifier', help='« lot » : étape(s) à enchaîner, séparées par des virgules (' + ', '.join(ETAPES_LOT) + ')')
    ap.add_argument('--depuis', help='« nouveau » : épisode modèle (défaut leo-4-tenues-50e)')
    a = ap.parse_args()
    try:
        if a.commande == 'nouveau': cmd_nouveau(a)
        elif a.commande == 'lot': cmd_lot(a)
        else:
            ep = Ep(a.episode)
            {'prix': cmd_prix, 'voix': cmd_voix, 'mots': cmd_mots, 'silences': cmd_silences, 'timeline': cmd_timeline, 'vignettes': cmd_vignettes,
             'audio': cmd_audio, 'rendu': cmd_rendu, 'qa': cmd_qa, 'tout': cmd_tout, 'verifier': cmd_verifier, 'prompts': cmd_prompts}[a.commande](ep, a)
    except SAErreur as e:
        print('[sa] ERREUR :', e, file=sys.stderr); sys.exit(1)
