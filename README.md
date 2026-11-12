# Moteur vidéo Style Astuce

Style officiel des vidéos Style Astuce (format « N tenues à moins de X € » avec Léo).
Un épisode = un dossier `episodes/<id>/` avec un `episode.json`, un `script.txt` et ses médias.
Une commande enchaîne tout : prix, voix, mots, silences, vignettes, timeline, audio, rendu, QA.

## Arborescence

```
moteur/
  README.md            ce fichier
  package.json         Remotion 4.0.535, React 19, TypeScript
  remotion.config.ts   rendu jpeg, concurrence 3
  requirements.txt     dépendances Python
  fonts/               Fraunces, Fraunces italique, Inter (licence OFL)
  src/
    index.ts           point d'entrée Remotion
    Root.tsx           composition « Episode » (1080x1920, 30 i/s, durée lue dans les props)
    Episode.tsx        tout le montage, paramétré par les props (règles figées en tête de fichier)
  cli/
    sa.py              la ligne de commande (une sous-commande par étape + « tout »)
    musique.py         musique originale générée (120 BPM, sans droits)
  episodes/
    leo-4-tenues-50e/  épisode de référence (reconstruit la vidéo v3)
      episode.json
      script.txt
      media/           images, rotations, voix (NON versionné)
  out/<id>/            sorties (NON versionné) : props.json, public/, prix.json, <id>.mp4, qa/
```

## Prérequis (une seule fois)

1. Node 20 ou plus, puis dans `moteur/` : `npm install`
2. ffmpeg et ffprobe dans le PATH
3. Python 3.11 ou plus dans un venv : `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
   (sur la box, le venv existant `/workspace/styleastuce/.venv-maquette` contient déjà tout)
4. Le premier détourage télécharge le modèle rembg `isnet-general-use`, la première QA le modèle whisper `small`.

Dans la suite, `PY` désigne le python du venv (ex. `PY=/workspace/styleastuce/.venv-maquette/bin/python`).

## Pas à pas pour une nouvelle vidéo

1. Copier l'épisode de référence : `cp -r episodes/leo-4-tenues-50e episodes/<nouvel-id>` puis vider `media/voix/`.
2. Écrire le script dans `script.txt` (texte continu, tel qu'il sera lu). Le faire valider par Aymane.
3. Remplir `episode.json` (schéma plus bas) : pièces, prix, enseignes, URL, images, rotations, astuces, et pour chaque élément le mot du script qui le déclenche.
4. Déposer les médias dans `media/` : une photo de Léo par tenue (portrait, 1080 de large conseillé) et une rotation 360° par tenue (mp4 vertical, 1088 ou 720 de large).
5. Vérifier les prix : `$PY cli/sa.py prix episodes/<id>`. Tout écart arrête la chaîne : corriger l'épisode ET le script.
6. Générer la voix (payant, seulement après le feu vert d'Aymane) :
   `$PY cli/sa.py voix episodes/<id> --depenser-credits`
   Sans `--depenser-credits` la commande refuse de dépenser. Si `media/voix/voice-raw.mp3` existe déjà elle ne refait rien (`--voix-neuve` pour forcer un nouvel essai).
7. Lancer le reste : `$PY cli/sa.py tout episodes/<id>`
8. Ouvrir la QA dans `out/<id>/qa/` (planche 1 i/s, planches masques TikTok et Reels, `qa.json`) et la planche `out/<id>/planche-vignettes.png`, écouter au casque, puis envoyer `out/<id>/<id>.mp4` à Aymane. Ne jamais publier ni programmer depuis ce moteur.

## Les commandes

Toutes s'écrivent `$PY cli/sa.py <commande> episodes/<id> [options]`.

| Commande | Ce qu'elle fait | Sortie |
|---|---|---|
| `prix` | relit chaque URL, compare au prix de l'épisode (et au prix barré) | `out/<id>/prix.json` |
| `voix` | ElevenLabs avec les réglages Benjamin (endpoint with-timestamps) | `media/voix/voice-raw.mp3`, `alignment.json`, `tts-essaiN.json` |
| `mots` | alignement caractère par caractère vers mots | `media/voix/words-raw.json` |
| `silences` | silences de plus de 0,32 s ramenés à 0,32 s (fondu 10 ms), temps des mots recalés | `media/voix/voice.wav`, `words.json`, `silence-cuts.json` |
| `vignettes` | Léo détouré, vignettes haut et bas sans mains, rotations à 30 i/s | `out/<id>/public/`, `planche-vignettes.png` |
| `timeline` | place chaque élément sur son mot (visuels 3 images en avance) | `out/<id>/props.json` |
| `audio` | musique originale, effets sonores, réduction auto de la musique sous la voix | `out/<id>/public/mix.wav` |
| `rendu` | rendu Remotion puis loudnorm deux passes (-13 LUFS, crête -1,5) | `out/<id>/<id>.mp4` |
| `qa` | planches 1 i/s, masques TikTok et Reels, LUFS, zones, rythme, sync des prix (whisper) | `out/<id>/qa/` |
| `tout` | prix, voix (sans dépenser si absente : arrêt), mots, silences, vignettes, timeline, audio, rendu, qa | tout ce qui précède |

Options : `--depenser-credits`, `--voix-neuve`, `--cle-fichier <fichier.env>`, `--refaire` (refait détourage et rotations), `--sans-whisper`, `--sans-prix`.

## La clé ElevenLabs

- Aucune clé n'est dans ce dépôt, et le `.gitignore` exclut tous les `.env`.
- La clé est lue en mémoire seulement : variable d'environnement `ELEVENLABS_API_KEY`, ou `--cle-fichier chemin.env` qui lit UNIQUEMENT la ligne `ELEVENLABS_API_KEY` de ce fichier.
- Elle n'est jamais affichée, écrite, ni copiée. `tts-essaiN.json` garde seulement les réglages, les crédits facturés et l'identifiant de requête.
- Crédits : le script de référence (1 454 caractères) a coûté 639 crédits en eleven_v4, soit environ 0,45 crédit par caractère. Une génération plus un nouvel essai au maximum, avec l'accord d'Aymane.

## Règles figées (ne pas modifier sans accord d'Aymane)

- Zone utile commune TikTok et Reels : x 108..940, y 220..1420. La QA compte tout bord net hors zone.
- Aucun zoom, aucune pulsation, aucun rebond lié à la parole. Léo reste stable et ne bouge qu'aux changements de tenue et aux rotations.
- Le rythme vient d'éléments informatifs (étiquettes, prix, vignettes, soulignements, titres) : au moins un événement par seconde.
- Ouverture sur la tenue finale portée (`ouverture`).
- Aucune mention en bas de l'écran.
- Polices Fraunces (titres) et Inter (texte). Palette Momwise (crème, encre, orange), sans réutiliser d'image ni de code Momwise.
- Prix : datés, hors chaussures et livraison, jamais « look complet », jamais un chiffre affiché qui n'est pas dit dans la voix.
- Voix : on ne l'accélère jamais, on raccourcit seulement les silences.
- Son : -14 à -12 LUFS, musique environ 18 dB sous la voix.

## Schéma de `episode.json`

Chaque champ `mot...` est un mot du script (comparé sans accents ni ponctuation) : l'élément apparaît à cet instant. Les mots sont cherchés dans l'ordre, chacun après le précédent de sa section.

```
id, titre, date_releve, script ("script.txt"), ouverture (numéro de la tenue de l'accroche)
voix        { voice_id, voice_name, model_id, language_code, stability, similarity_boost, output_format }
accroche    { l1, pre, kw, post, mot_surligne }           titre « l1 / pre + kw surligné + post »
promesse    { mot, l1, pre, kw, post, mot_surligne, sous_titre { texte, surligne, mot } }
tenues[]    { label, total, mot, mot_label, image, rotation,
              coupe { ourlet_y, chaussures_y, peau_cotes_seulement?, haut_marge_bas? },
              sous_titre { texte, surligne, mot },
              pieces[] { nom, enseigne, prix, prix_barre?, zone ("haut"|"bas"), url,
                         mot, mot_prix, mot_enseigne?, mot_barre? },
              mot_total,
              astuce { mot, titre { l1, pre, kw, post, mot_surligne },
                       sous_titres[] { mot, texte, surligne, mot_surligne } } }
mention     { mot, l1, l2, mot_l2 }                       date du relevé et « hors chaussures et livraison »
fin         { mot, titre {...}, sous_titre { mot, texte, surligne, mot_surligne }, mots_numeros[] }
```

`coupe` : `ourlet_y` est la ligne (en px de la photo) qui sépare le haut du bas, `chaussures_y` celle où commencent les chaussures (exclues des vignettes). Régler en regardant `planche-vignettes.png`, puis relancer `vignettes --refaire`.

## Test de référence

`$PY cli/sa.py tout episodes/leo-4-tenues-50e` reconstruit la vidéo v3 de la maquette en réutilisant la voix existante (aucun crédit) : 80,3 s, mêmes mots, même audio, SSIM image 0,999 avec `maquette-v1/video-leo-v3.mp4`. Les médias de cet épisode ne sont pas versionnés : ils viennent de `/workspace/styleastuce/maquette-v1/`.
