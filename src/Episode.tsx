import React from 'react';
import {AbsoluteFill, Img, OffthreadVideo, Audio, Sequence, staticFile, useCurrentFrame, useVideoConfig, interpolate, spring, Easing} from 'remotion';

// Moteur Style Astuce. Toutes les données viennent des props (props.json construit par « sa.py timeline »).
// RÈGLES FIGÉES : zone commune TikTok + Reels x 108..940, y 220..1420 ; aucun zoom, aucune pulsation ni rebond liés à la parole ou au rythme ;
// Léo ne bouge qu'aux changements de tenue (vignette qui se pose + balayage) et aux rotations ; ouverture sur la tenue finale portée ;
// aucune mention fixe en bas hormis le petit logo anti-vol (coin bas droit de la zone commune) ; polices Fraunces + Inter ; palette Momwise (crème, pêche, encre, orange).
const CREAM = '#F6EFE6', PEACH = '#F3DCC8', INK = '#1F1A17', ORANGE = '#D9662B';
const CX = 524, SAFE_L = 108, SAFE_R = 940, SAFE_W = SAFE_R - SAFE_L;
const S = 0.47, LEO_W = 1080 * S, LEO_H = 1920 * S, LEO_LEFT = CX - 549 * S, LEO_TOP = 500;
const CARD_W = 206, CARD_H = 334;
const CARD_POS: Record<number, [number, number, number]> = {1: [148, 560, -4], 2: [694, 590, 4], 3: [150, 970, 3], 4: [692, 1000, -3]};
// 3 tenues : la carte 2 descend au milieu à droite pour équilibrer (1 et 3 à gauche) ; 1 ou 2 tenues : positions de la grille 4
const CARD_POS_3: Record<number, [number, number, number]> = {1: [148, 560, -4], 2: [694, 770, 4], 3: [150, 980, 3]};
const cardPos = (n: number): [number, number, number] => (L.length === 3 ? CARD_POS_3 : CARD_POS)[n];
const TAG_W = 310, TAG_L = SAFE_L + 4, TAG_R = SAFE_R - 6 - TAG_W;
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const io = Easing.bezier(0.65, 0, 0.35, 1), out = Easing.bezier(0.16, 1, 0.3, 1), inn = Easing.bezier(0.5, 0, 0.75, 0);
// données de l'épisode (affectées à chaque rendu par le composant racine)
let T: any = null, L: any[] = [], LOOKS: any[] = [], TITLES: TitleDef[] = [];

const fontCss = `
@font-face{font-family:'Fraunces';src:url('${staticFile('fonts/Fraunces.ttf')}');font-style:normal;font-weight:100 900}
@font-face{font-family:'Fraunces';src:url('${staticFile('fonts/Fraunces-Italic.ttf')}');font-style:italic;font-weight:100 900}
@font-face{font-family:'Inter';src:url('${staticFile('fonts/Inter.ttf')}');font-style:normal;font-weight:100 900}`;

const lookIdx = (f: number) => { let i = -1; L.forEach((l, k) => { if (f >= l.a - 6 && f < l.b) i = k; }); return i; };
const inRotOf = (f: number) => L.findIndex((l) => !!l.rotSrc && f >= l.rot0 && f < l.rot1);

const Background: React.FC<{f: number}> = ({f}) => {
  const dx = Math.sin(f / 40) * 40, dy = Math.cos(f / 55) * 30;
  return (
    <AbsoluteFill style={{background: `linear-gradient(180deg,${CREAM} 0%, #F5E8DB 55%, ${PEACH} 100%)`}}>
      <div style={{position: 'absolute', left: 540 + dx, top: 1250 + dy, width: 900, height: 700, borderRadius: '50%',
        background: `radial-gradient(ellipse at center, ${PEACH} 0%, rgba(243,220,200,0) 70%)`}} />
      <div style={{position: 'absolute', left: -250 - dx, top: 250 - dy, width: 760, height: 620, borderRadius: '50%',
        background: 'radial-gradient(ellipse at center, #F8E2CE 0%, rgba(248,230,214,0) 70%)'}} />
    </AbsoluteFill>
  );
};

// ---------- Titres (gros titre Fraunces, mot clé en italique orange souligné) ----------
type TitleDef = {at: number; l1: string; pre: string; kw: string; post: string; type?: boolean; hl?: number};

const OneTitle: React.FC<{d: TitleDef; f: number; next: number}> = ({d, f, next}) => {
  const fe = f - d.at;
  const first = d.at === 0;
  const pin = first ? 1 : interpolate(fe, [0, 9], [0, 1], {...clamp, easing: out});
  const pout = interpolate(f, [next - 6, next], [0, 1], {...clamp, easing: inn});
  if (pout >= 1) return null;
  const ul = first ? interpolate(f, [0, 18], [0.2, 1], {...clamp, easing: out}) : interpolate(fe, [6, 20], [0, 1], {...clamp, easing: out});
  const full = `${d.l1} ${d.pre}${d.kw}${d.post}`;
  const chars = d.type ? Math.floor(interpolate(fe, [0, 16], [0, full.length], clamp)) : 999;
  const cut = (s: string, off: number) => s.slice(0, Math.max(0, chars - off));
  const o2 = d.l1.length + 1;
  return (
    <div style={{position: 'absolute', left: SAFE_L, width: SAFE_W, top: 228, textAlign: 'center', fontFamily: 'Fraunces', fontWeight: 500,
      fontSize: 88, lineHeight: 1.0, letterSpacing: '-0.02em', color: INK, fontVariationSettings: "'opsz' 144, 'SOFT' 50",
      opacity: pin * (1 - pout), translate: `0 ${(1 - pin) * 34 - pout * 26}px`}}>
      <div style={{whiteSpace: 'nowrap'}}>{cut(d.l1, 0)}</div>
      <div style={{position: 'relative', display: 'inline-block', whiteSpace: 'nowrap'}}>
        {cut(d.pre, o2)}
        <span style={{fontStyle: 'italic', color: ORANGE, position: 'relative', display: 'inline-block'}}>
          {d.hl !== undefined ? <span style={{position: 'absolute', left: -8, right: -8, top: '18%', bottom: '4%', borderRadius: 10, background: 'rgba(217,102,43,0.16)',
            clipPath: `inset(0 ${(1 - interpolate(f, [d.hl, d.hl + 9], [0, 1], {...clamp, easing: out})) * 100}% 0 0)`}} /> : null}
          <span style={{position: 'relative'}}>{cut(d.kw, o2 + d.pre.length)}</span>
          <svg width="100%" height="28" viewBox="0 0 300 28" preserveAspectRatio="none" style={{position: 'absolute', left: 0, bottom: -12, overflow: 'visible'}}>
            <path d="M4,17 C80,7 190,25 296,11" fill="none" stroke={ORANGE} strokeWidth={7} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - ul} />
          </svg>
        </span>
        {cut(d.post, o2 + d.pre.length + d.kw.length)}
      </div>
    </div>
  );
};
const Titles: React.FC<{f: number}> = ({f}) => (
  <>{TITLES.map((d, i) => { const next = TITLES[i + 1]?.at ?? 1e9; return f >= d.at - 1 && f < next ? <OneTitle key={i} d={d} f={f} next={next} /> : null; })}</>
);

// ---------- Sous-titre (pastille) ----------
const Subtitle: React.FC<{f: number}> = ({f}) => {
  let idx = 0; T.subs.forEach(([s], i) => { if (f >= (s as number)) idx = i; });
  const [s0, txt0] = T.subs[idx] as [number, string];
  if (!txt0 || f >= T.mention && f < T.reponds) return null;
  const n = Math.floor(interpolate(f - s0, [0, 10], [0, txt0.length], clamp));
  const nextStart = (T.subs[idx + 1]?.[0] as number) ?? 99999;
  const op = interpolate(f, [nextStart - 4, nextStart], [1, 0], clamp);
  return (
    <div style={{position: 'absolute', left: SAFE_L, width: SAFE_W, top: 436, textAlign: 'center', opacity: op}}>
      <span style={{display: 'inline-block', background: 'rgba(255,250,244,0.88)', borderRadius: 999, padding: '7px 24px', whiteSpace: 'nowrap',
        fontFamily: 'Inter', fontWeight: 700, fontSize: 38, color: INK, letterSpacing: '-0.01em', boxShadow: '0 6px 18px rgba(120,70,40,.10)'}}>
        {(() => {
          const sub = T.subs[idx]; const hi = sub[2] ? [sub[2], sub[3]] as [string, number] : undefined;
          if (!hi || n < txt0.length) return <>{txt0.slice(0, n)}<span style={{opacity: 0}}>{txt0.slice(n)}</span></>;
          let i = txt0.lastIndexOf(hi[0]);
          if (i < 0) i = txt0.toLowerCase().lastIndexOf(hi[0].toLowerCase());
          if (i < 0) return <>{txt0}</>;   // surlignage introuvable : texte simple (sa.py verifier le signale)
          hi[0] = txt0.slice(i, i + hi[0].length);
          const on = interpolate(f, [hi[1], hi[1] + 6], [0, 1], clamp);
          return <>{txt0.slice(0, i)}<span style={{background: `rgba(217,102,43,${on})`, color: on > 0.5 ? '#fff' : INK, borderRadius: 12, padding: '0 6px', margin: '0 -6px'}}>{hi[0]}</span>{txt0.slice(i + hi[0].length)}</>;
        })()}
      </span>
    </div>
  );
};

// mention des prix (dite à l'oral) : encart sombre en bas, dans la zone sûre
const Mention: React.FC<{f: number}> = ({f}) => {
  if (f < T.mention - 2 || f >= T.end + 4) return null;
  const p = interpolate(f, [T.mention, T.mention + 10], [0, 1], {...clamp, easing: out});
  const q = interpolate(f, [T.end - 4, T.end + 4], [1, 0], clamp);
  return (
    <div style={{position: 'absolute', left: CX - 330, width: 660, top: 1190, background: INK, color: '#fff', borderRadius: 28, padding: '16px 24px',
      textAlign: 'center', fontFamily: 'Inter', fontWeight: 700, fontSize: 36, lineHeight: 1.2, opacity: p * q, translate: `0 ${(1 - p) * 30}px`}}>
      {T.mentionL1}<br /><span style={{fontWeight: 500, opacity: interpolate(f, [T.hors - 2, T.hors + 6], [0, 1], clamp)}}>{T.mentionL2}</span>
    </div>
  );
};

// logo anti-vol : fixe toute la durée, coin bas droit de la zone commune (bord droit 934, bas 1412), aucune animation
const Logo: React.FC = () => {
  const lg = T.logo;
  if (!lg || !lg.actif) return null;
  const w = lg.largeur, blanc = lg.variante === 'blanc';
  return (
    <div style={{position: 'absolute', left: SAFE_R - 6 - w, top: 1412 - Math.round(w * 0.4), width: w, height: Math.round(w * 0.4), opacity: lg.opacite,
      display: 'flex', alignItems: 'center', justifyContent: 'center', gap: Math.round(w * 0.05), borderRadius: Math.round(w * 0.2),
      background: blanc ? 'transparent' : 'rgba(246,239,230,0.92)', border: blanc ? 'none' : `2px solid rgba(217,102,43,0.55)`,
      boxShadow: blanc ? 'none' : '0 4px 14px rgba(120,70,40,.12)', filter: blanc ? 'drop-shadow(0 2px 6px rgba(0,0,0,.45))' : 'none'}}>
      <span style={{fontFamily: 'Fraunces', fontStyle: 'italic', fontWeight: 700, fontSize: Math.round(w * 0.24), lineHeight: 1, color: blanc ? '#fff' : ORANGE, letterSpacing: '-0.04em'}}>SA</span>
      <span style={{fontFamily: 'Fraunces', fontWeight: 600, fontSize: Math.round(w * 0.105), lineHeight: 1.0, color: blanc ? '#fff' : INK}}>Style<br />Astuce</span>
    </div>
  );
};

// ---------- Cartes des 4 tenues ----------
const Card: React.FC<{f: number; n: number; fps: number}> = ({f, n, fps}) => {
  const [x, y, r] = cardPos(n);
  const look = LOOKS[n - 1], tl = L[n - 1];
  const bi = lookIdx(f);
  const ri = inRotOf(f);
  const active = bi === n - 1 || (f < L[0].a - 6 && n === T.openLook);
  let op = 1;
  if (bi >= 0 && !active) { const a = L[bi].a, b = L[bi].b; op = interpolate(f, [a - 6, a + 4, b - 8, b], [1, 0.38, 0.38, 1], clamp); }
  if (ri >= 0) { const l = L[ri]; op = Math.min(op, interpolate(f, [l.rot0, l.rot0 + 8, l.rot1 - 8, l.rot1], [1, 0.35, 0.35, 1], clamp)); }
  let border = active ? ORANGE : 'transparent';
  let badge = 0;
  if (f >= T.end) {
    badge = spring({frame: f - T.end - 6 - (n - 1) * 4, fps, config: {damping: 10, stiffness: 200}});
    const said = T.nums[n - 1];
    const d = f - said;
    
    border = f >= said && f < said + 18 ? ORANGE : 'transparent';
    const lastNum = T.nums[T.nums.length - 1];
    if (f >= lastNum + 18) { const k = Math.floor((f - lastNum - 18) / 15) % L.length; border = k + 1 === n ? ORANGE : 'transparent'; }
  }
  const flyOp = bi === n - 1 ? interpolate(f, [tl.a - 6, tl.a, tl.a + 12, tl.a + 22], [1, 0.25, 0.25, 1], clamp) : 1;
  
  // le total n'apparaît sur la carte qu'une fois prononcé
  const totP = spring({frame: f - tl.total, fps, config: {damping: 11, stiffness: 200}});
  // intro : chaque carte entre une par une sur son mot (glissé de bas en haut + fondu, aucun zoom), toutes posées avant T.intro.fin
  const ia = T.intro ? T.intro.at[n - 1] : -1;
  const ip = ia >= 0 ? interpolate(f, [ia, ia + T.intro.duree], [0, 1], {...clamp, easing: out}) : 1;
  const numOp = T.intro && T.intro.numeros ? Math.min(ip, interpolate(f, [T.intro.fin - 12, T.intro.fin], [1, 0], clamp)) : 0;
  return (
    <div style={{position: 'absolute', left: x, top: y, width: CARD_W, height: CARD_H, rotate: `${r}deg`, opacity: op * flyOp * ip, translate: `0 ${(1 - ip) * 40}px`,
      background: '#fff', borderRadius: 30, padding: 8, outline: `5px solid ${border}`, boxShadow: '0 18px 40px rgba(120,70,40,.18),0 3px 8px rgba(120,70,40,.10)'}}>
      <div style={{width: CARD_W - 16, height: 254, borderRadius: 22, overflow: 'hidden', background: 'linear-gradient(180deg,#FBF4EC 0%,#F2DFCD 100%)', position: 'relative'}}>
        <Img src={staticFile(`leo/cut-${look.key}.png`)} style={{position: 'absolute', width: 1080 * 0.155, left: (CARD_W - 16) / 2 - 549 * 0.155, top: -2}} />
      </div>
      <div style={{textAlign: 'center', fontFamily: 'Fraunces', fontStyle: 'italic', fontWeight: 600, fontSize: 34, marginTop: 0, color: f >= T.end && border === ORANGE ? '#fff' : INK, background: f >= T.end && border === ORANGE ? ORANGE : 'transparent', borderRadius: 14}}>{look.label}</div>
      {f >= tl.total ? (
        <div style={{position: 'absolute', left: '50%', bottom: -22, translate: '-50% 0', scale: String(totP), background: ORANGE, color: '#fff', borderRadius: 999,
          padding: '4px 16px', fontFamily: 'Inter', fontWeight: 800, fontSize: 30, whiteSpace: 'nowrap'}}>{look.total}</div>
      ) : null}
      {numOp > 0 ? (
        <div style={{position: 'absolute', left: -2, top: -16, width: 58, height: 58, borderRadius: 29, background: ORANGE, color: '#fff',
          fontFamily: 'Fraunces', fontWeight: 700, fontSize: 36, display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: numOp}}>{n}</div>
      ) : null}
      {f >= T.end ? (
        <div style={{position: 'absolute', left: -2, top: -16, width: 58, height: 58, borderRadius: 29, background: ORANGE, color: '#fff',
          fontFamily: 'Fraunces', fontWeight: 700, fontSize: 36, display: 'flex', alignItems: 'center', justifyContent: 'center', scale: String(badge)}}>{n}</div>
      ) : null}
    </div>
  );
};

// carte qui grandit et vient se poser sur Léo (démarre 6 frames avant « Un / Deux / Trois / Quatre »)
const FlyingCard: React.FC<{f: number}> = ({f}) => {
  const bi = lookIdx(f);
  if (bi < 0) return null;
  const a = L[bi].a; const n = bi + 1;
  if (f < a - 6 || f > a + 14) return null;
  const [x, y, r] = cardPos(n);
  const p = interpolate(f, [a - 6, a + 8], [0, 1], {...clamp, easing: io});
  const tx = interpolate(p, [0, 1], [x, LEO_LEFT + 292 * S - 20]);
  const ty = interpolate(p, [0, 1], [y, LEO_TOP + 60 * S - 20]);
  const w = interpolate(p, [0, 1], [CARD_W, (806 - 292) * S + 40]);
  const h = interpolate(p, [0, 1], [CARD_H, (1844 - 60) * S + 40]);
  const op = interpolate(f, [a + 6, a + 14], [1, 0], clamp);
  const iw = w / ((806 - 292) / 1080);
  return (
    <div style={{position: 'absolute', left: tx, top: ty, width: w, height: h, rotate: `${r * (1 - p)}deg`, opacity: op, borderRadius: 30,
      background: 'rgba(255,255,255,0.92)', boxShadow: '0 30px 60px rgba(120,70,40,.25)', overflow: 'hidden', outline: `5px solid ${ORANGE}`}}>
      <Img src={staticFile(`leo/cut-${LOOKS[n - 1].key}.png`)} style={{position: 'absolute', width: iw, left: w / 2 - (549 / 1080) * iw, top: -(60 / 1080) * iw + 8}} />
    </div>
  );
};

const Leo: React.FC<{f: number}> = ({f}) => {
  const bi = lookIdx(f);
  let cur = T.openLook; L.forEach((l, k) => { if (f >= l.a + 12) cur = k + 1; });
  let wipe = 1;
  if (bi >= 0) { const a = L[bi].a; wipe = interpolate(f, [a + 4, a + 18], [0, 1], {...clamp, easing: io}); }
  const newKey = bi >= 0 ? String(bi + 1) : String(cur);
  const oldKey = String(bi >= 0 ? (bi === 0 ? T.openLook : bi) : cur);
  
  const ri = inRotOf(f);
  const leoOp = ri >= 0 ? interpolate(f, [L[ri].rot0, L[ri].rot0 + 8, L[ri].rot1 - 6, L[ri].rot1], [1, 0, 0, 1], clamp) : 1;
  const st: React.CSSProperties = {position: 'absolute', left: LEO_LEFT, top: LEO_TOP, width: LEO_W, height: LEO_H};
  return (
    <>
      <div style={{position: 'absolute', left: CX - 170, top: LEO_TOP + 1830 * S, width: 340, height: 44, borderRadius: '50%', opacity: leoOp,
        background: 'radial-gradient(ellipse at center, rgba(90,55,30,.28) 0%, rgba(90,55,30,0) 70%)'}} />
      <div style={{...st, opacity: leoOp}}>
        <Img src={staticFile(`leo/cut-${oldKey}.png`)} style={{width: '100%', height: '100%', position: 'absolute', clipPath: `inset(${wipe * 100}% 0 0 0)`, opacity: wipe >= 1 ? 0 : 1}} />
        <Img src={staticFile(`leo/cut-${newKey}.png`)} style={{width: '100%', height: '100%', position: 'absolute', clipPath: `inset(0 0 ${(1 - wipe) * 100}% 0)`}} />
      </div>
      {bi >= 0 && wipe > 0 && wipe < 1 ? (
        <div style={{position: 'absolute', left: LEO_LEFT + 260 * S, width: 560 * S, top: LEO_TOP + wipe * LEO_H - 3, height: 6, borderRadius: 3,
          background: `linear-gradient(90deg, rgba(217,102,43,0), ${ORANGE}, rgba(217,102,43,0))`}} />
      ) : null}
    </>
  );
};

// ---------- Étiquettes pièce + prix (le prix apparaît quand il est prononcé) ----------
const Tag: React.FC<{f: number; at: number; priceAt: number; wasAt?: number; brandAt?: number; end: number; side: 'l' | 'r'; y: number; piece: any; target: [number, number]}> = ({f, at, priceAt, wasAt, brandAt, end, side, y, piece, target}) => {
  const p = interpolate(f, [at - 2, at + 8], [0, 1], {...clamp, easing: out});
  const q = interpolate(f, [end - 7, end], [1, 0], {...clamp, easing: inn});
  if (p <= 0 || q <= 0) return null;
  const x = side === 'l' ? TAG_L : TAG_R;
  const dx = (side === 'l' ? 36 : -36) * (1 - p);
  const lineP = interpolate(f, [at + 2, at + 12], [0, 1], clamp);
  const pp = spring({frame: f - priceAt, fps: 30, config: {damping: 11, stiffness: 210}});
  const wp = wasAt !== undefined ? interpolate(f, [wasAt, wasAt + 8], [0, 1], clamp) : 0;
  const ax = side === 'l' ? x + TAG_W : x, ay = y + 60;
  return (
    <>
      <svg width={1080} height={1920} style={{position: 'absolute', left: 0, top: 0, opacity: q}}>
        <path d={`M${ax},${ay} Q${(ax + target[0]) / 2},${ay - 30} ${target[0]},${target[1]}`} fill="none" stroke={ORANGE} strokeWidth={4}
          strokeDasharray="1" pathLength={1} strokeDashoffset={1 - lineP} strokeLinecap="round" />
        <circle cx={target[0]} cy={target[1]} r={9 * lineP} fill="#fff" stroke={ORANGE} strokeWidth={4} />
      </svg>
      <div style={{position: 'absolute', left: x + dx, top: y, width: TAG_W, opacity: p * q, background: 'rgba(255,255,255,0.96)', borderRadius: 26,
        padding: '12px 14px', display: 'flex', gap: 12, alignItems: 'center', boxShadow: '0 12px 30px rgba(120,70,40,.16)'}}>
        <div style={{width: 86, height: 104, borderRadius: 16, background: '#F6EBDF', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden', flex: 'none'}}>
          <Img src={staticFile(piece.img)} style={{maxWidth: 80, maxHeight: 98, clipPath: `inset(0 0 ${(1 - interpolate(f, [at + 4, at + 16], [0, 1], {...clamp, easing: out})) * 100}% 0)`}} />
        </div>
        <div style={{fontFamily: 'Inter', color: INK, minWidth: 0}}>
          <div style={{fontWeight: 650, fontSize: 30, lineHeight: 1.08}}>{piece.name}</div>
          <div style={{fontWeight: 600, fontSize: 30, lineHeight: 1.15}}><span style={{color: brandAt !== undefined && f >= brandAt ? '#fff' : '#6B5D53', background: brandAt !== undefined ? `rgba(217,102,43,${interpolate(f, [brandAt, brandAt + 6], [0, 1], clamp)})` : 'transparent', borderRadius: 10, padding: '0 6px', margin: '0 -6px'}}>{piece.brand}</span></div>
          <div style={{fontWeight: 800, fontSize: 40, color: ORANGE, lineHeight: 1.1, whiteSpace: 'nowrap', opacity: Math.min(1, pp * 1.5), scale: String(0.6 + 0.4 * pp), transformOrigin: 'left center'}}>{piece.price}</div>
          {piece.was ? <div style={{fontSize: 30, color: '#8C7D72', fontWeight: 600, whiteSpace: 'nowrap', opacity: wp, translate: `${(1 - wp) * 24}px 0`}}><span style={{position: 'relative'}}>{piece.was}<span style={{position: 'absolute', left: -2, top: '52%', height: 3, background: '#8C7D72', width: `${interpolate(f, [(wasAt ?? 0) + 4, (wasAt ?? 0) + 12], [0, 104], clamp)}%`}} /></span></div> : null}
        </div>
      </div>
    </>
  );
};

const LookTags: React.FC<{f: number}> = ({f}) => {
  const bi = lookIdx(f);
  if (bi < 0) return null;
  const l = L[bi]; const look = LOOKS[bi];
  const end = l.rot0 + 4; // tout s'efface quand la rotation commence
  const tp = interpolate(f, [l.total - 2, l.total + 8], [0, 1], {...clamp, easing: out});
  const tq = interpolate(f, [end - 7, end], [1, 0], clamp);
  const sp = spring({frame: f - l.total, fps: 30, config: {damping: 11, stiffness: 190}, from: 0.7, to: 1});
  const side: 'l' | 'r' = (bi + 1) % 2 === 1 ? 'r' : 'l';
  const v2 = (z: string, k: number) => `produits/${z}-${k}.png`;
  return (
    <>
      <Tag f={f} at={l.piece1} priceAt={l.price1} wasAt={look.pieces[0].wasAt ?? undefined} brandAt={look.pieces[0].brandAt ?? undefined} end={end} side={side} y={600} piece={{...look.pieces[0], img: v2('haut', bi + 1)}} target={[CX + (side === 'l' ? -40 : 40), LEO_TOP + 560 * S]} />
      <Tag f={f} at={l.piece2} priceAt={l.price2} wasAt={look.pieces[1].wasAt ?? undefined} brandAt={look.pieces[1].brandAt ?? undefined} end={end} side={side} y={880} piece={{...look.pieces[1], img: v2('bas', bi + 1)}} target={[CX + (side === 'l' ? -45 : 45), LEO_TOP + 1250 * S]} />
      {tp > 0 && tq > 0 ? (
        <div style={{position: 'absolute', left: side === 'l' ? TAG_L : TAG_R, top: 1180, width: TAG_W, opacity: tp * tq, scale: String(sp), transformOrigin: side === 'l' ? 'left center' : 'right center', background: INK, color: '#fff', borderRadius: 26, padding: '12px 22px'}}>
          <div style={{fontFamily: 'Inter', fontWeight: 600, fontSize: 30, opacity: 0.85}}>Total</div>
          <div style={{fontFamily: 'Fraunces', fontWeight: 600, fontSize: 60, lineHeight: 1.05}}>{look.total}</div>
        </div>
      ) : null}
    </>
  );
};

// ---------- Rotation à 360° pendant l'astuce ----------
const Rotation: React.FC<{f: number; k: number}> = ({f, k}) => {
  const {rot0: r0, rot1: r1} = L[k];
  const p = interpolate(f, [r0, r0 + 12], [0, 1], {...clamp, easing: io});
  const q = interpolate(f, [r1 - 12, r1], [0, 1], {...clamp, easing: io});
  const kk = p * (1 - q);
  const W0 = (806 - 292) * S + 40, ar = L[k].rotAR;
  const W1 = 460;
  const w = W0 + (W1 - W0) * kk, h = w * ar;
  const top0 = LEO_TOP + 60 * S - 20, top1 = 524;
  const top = top0 + (top1 - top0) * kk;
  const chip = spring({frame: f - r0 - 10, fps: 30, config: {damping: 12, stiffness: 200}});
  const rate = L[k].rotFrames / (r1 - r0);
  return (
    <div style={{position: 'absolute', left: CX - w / 2, top, width: w, height: h, borderRadius: 34, overflow: 'hidden', opacity: Math.min(1, kk * 2.5),
      boxShadow: '0 30px 70px rgba(120,70,40,.28)', outline: '6px solid #fff'}}>
      <OffthreadVideo src={staticFile(L[k].rotSrc)} muted playbackRate={rate} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      <div style={{position: 'absolute', right: 18, top: 18, background: ORANGE, color: '#fff', borderRadius: 999, padding: '6px 18px',
        fontFamily: 'Inter', fontWeight: 800, fontSize: 34, scale: String(chip)}}>360°</div>
    </div>
  );
};



export const Episode: React.FC<{data: any}> = ({data}) => {
  T = data; L = data.looks; LOOKS = data.looksData; TITLES = data.titles;
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill style={{fontFamily: 'Inter'}}>
      <style>{fontCss}</style>
      <Background f={f} />
      <AbsoluteFill>
        {L.map((_, i) => <Card key={i} f={f} n={i + 1} fps={fps} />)}
        <Leo f={f} />
        <FlyingCard f={f} />
        {L.map((l, k) => !l.rotSrc ? null : (
          <Sequence key={k} from={l.rot0} durationInFrames={l.rot1 - l.rot0} premountFor={fps}>
            <Rotation f={f} k={k} />
          </Sequence>
        ))}
      </AbsoluteFill>
      <LookTags f={f} />
      <Titles f={f} />
      <Subtitle f={f} />
      <Mention f={f} />
      <Logo />
      <Audio src={staticFile(T.audio)} />
    </AbsoluteFill>
  );
};
