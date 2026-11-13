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
    leo-jean-3-tenues/ lundi 16/11 (phase 1 prête)
    leo-rdv-3-erreurs/ mardi 17/11 (phase 1 prête)
  lots/                un fichier par lot (dates de publication), MODELE-hebdo.json
  SUJETS.md            banque de sujets d'avance pour les lots hebdo
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
| `verifier` | phase 1, sans réseau ni crédit : interdits (tiret cadratin, « look complet », mention IA, appâts), chiffres dans le script, totaux = somme des pièces, chaque prix affiché est dit dans sa section, prix des titres jamais avant d'être dits, date du relevé dite et affichée, durée estimée (cible 65 à 75 s), crédits ElevenLabs estimés, timeline simulée (tous les mots trouvés, cartes de l'intro avant 5 s), médias à générer | `out/<id>/verif.json`, `props-simule.json` |
| `prompts` | prompts GenerateImage (Léo en tenue, références identité + photos produit téléchargées) et GenerateVideo (rotation 360°) pour chaque tenue | `media/prompts.md`, `media/produits/` |
| `nouveau` | `sa.py nouveau <id> --depuis <modèle>` : squelette d'épisode copié d'un modèle | `episodes/<id>/` |
| `lot` | `sa.py lot lots/<nom>.json --etape prix,verifier,prompts` : enchaîne une ou plusieurs étapes sur tous les épisodes d'un lot, continue si un épisode échoue | `out/lots/<nom>/rapport.md` et `.json` |

Options : `--depenser-credits`, `--voix-neuve`, `--cle-fichier <fichier.env>`, `--refaire` (refait détourage et rotations), `--sans-whisper`, `--sans-prix`, `--sans-reseau` (prompts), `--etape` (lot), `--depuis` (nouveau), `--oui-aymane` (lot qui dépense des crédits : obligatoire en plus de `--depenser-credits`, seulement après son accord écrit).

`prix` contrôle aussi le stock (fiche Jules « InStock », au moins une taille Uniqlo dans le coloris) et écrit `episodes/<id>/produits.md` (URL, prix lu, date et heure, stock).
Attention : sur Jules, le nom du coloris ne correspond pas toujours à la photo. Regarder les photos téléchargées par `prompts` avant d'écrire une couleur dans la voix.

## Lot hebdomadaire (chaque mercredi, 7 vidéos du mercredi au mardi)

1. Choisir 7 sujets dans `SUJETS.md` (banque d'avance), en alternant les formes d'accroche (jamais la même deux jours de suite).
2. Pour chaque sujet : `$PY cli/sa.py nouveau <id> --depuis leo-jean-3-tenues` (3 tenues) ou `--depuis leo-4-tenues-50e` (4 tenues), puis écrire `script.txt`, `episode.json` (pièces, mots déclencheurs, `desc_en` pour les prompts, `publication.date_prevue`).
3. Copier `lots/MODELE-hebdo.json` en `lots/<date>_hebdo.json` et lister les 7 épisodes avec leur date.
4. Phase 1 (gratuite) : `$PY cli/sa.py lot lots/<nom>.json --etape prix,verifier,prompts`. Corriger jusqu'à « ok » partout. Le rapport donne caractères, durée, crédits et nombre d'images et de rotations à générer.
5. Envoyer à Aymane le tableau du rapport et le chiffrage. Attendre son oui.
6. Phase 2 (payante) : images et rotations avec `media/prompts.md` (GenerateImage, GenerateVideo), puis `$PY cli/sa.py lot lots/<nom>.json --etape tout --depenser-credits --oui-aymane --cle-fichier <fichier.env>`.
7. QA de chaque vidéo, envoi à Aymane, programmation Buffer seulement après son oui explicite (organisation Style Astuce uniquement).

Calibrage de la durée : 0,054 s par caractère de script (référence : 1 453 caractères donnent 80,3 s). Crédits : environ 0,44 crédit par caractère en eleven_v4.

Gabarit 3 tenues : la grille de cartes passe en 1 et 3 à gauche, 2 au milieu à droite (positions dans `Episode.tsx`, `CARD_POS_3`).

## La clé ElevenLabs

- Aucune clé n'est dans ce dépôt, et le `.gitignore` exclut tous les `.env`.
- La clé est lue en mémoire seulement : variable d'environnement `ELEVENLABS_API_KEY`, ou `--cle-fichier chemin.env` qui lit UNIQUEMENT la ligne `ELEVENLABS_API_KEY` de ce fichier.
- Elle n'est jamais affichée, écrite, ni copiée. `tts-essaiN.json` garde seulement les réglages, les crédits facturés et l'identifiant de requête.
- Crédits : le script de référence (1 454 caractères) a coûté 639 crédits en eleven_v4, soit environ 0,45 crédit par caractère. Une génération plus un nouvel essai au maximum, avec l'accord d'Aymane.

## Règles figées (ne pas modifier sans accord d'Aymane)

- Zone utile commune TikTok et Reels : x 108..940, y 220..1420. La QA compte tout bord net hors zone.
- Aucun zoom, aucune pulsation, aucun rebond lié à la parole. Léo reste stable et ne bouge qu'aux changements de tenue et aux rotations.
- Le rythme vient d'éléments informatifs (étiquettes, prix, vignettes, soulignements, titres) : au moins un événement par seconde.
- Ouverture sur la tenue finale portée (`ouverture`), puis les cartes des tenues entrent une par une sur la voix, toutes posées avant 5 s.
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
intro       { mots_cartes { "<n° tenue>": mot }, fin_s (5), duree_images (12), numeros (true) }
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

`coupe.ourlet_y` accepte `"auto"` : la commande `vignettes` détecte la rupture de couleur haut / bas et affiche la valeur trouvée (la recopier ensuite pour la figer). `coupe.bas_marge_haut` (48 par défaut) fait démarrer la vignette du bas plus bas : la mettre sous la ceinture ou sous le bout des doigts si une main ou une ceinture reste visible. Le bas n'utilise plus la détection de peau globale (un chino écru ou beige y ressemble) : les mains sont retirées par chromaticité, puis le trou est comblé par symétrie, sans jamais sortir du contour de la jambe.

`coupe` : `ourlet_y` est la ligne (en px de la photo) qui sépare le haut du bas, `chaussures_y` celle où commencent les chaussures (exclues des vignettes). Régler en regardant `planche-vignettes.png`, puis relancer `vignettes --refaire`.

## Intro standard (0 à 5 s)

Léo est en tenue d'ouverture au centre dès la première image, avec l'accroche. Les cartes des tenues entrent une par une autour de lui (glissé de 40 px vers le haut et fondu, 12 images, aucun zoom), chacune sur un mot de l'intro donné dans `intro.mots_cartes`, avec leur numéro (qui s'efface juste avant 5 s). La commande `timeline` refuse un mot qui ferait arriver une carte après `fin_s` (et jamais après le début de la tenue 1). Sans bloc `intro`, la tenue d'ouverture entre d'abord puis les autres sont réparties régulièrement. Après 5 s la vidéo suit le déroulé normal. Les totaux ne sont pas montrés dans l'intro : un prix n'apparaît que quand il est dit.

## Test de référence

`$PY cli/sa.py tout episodes/leo-4-tenues-50e` reconstruit la vidéo v3 de la maquette en réutilisant la voix existante (aucun crédit) : 80,3 s, mêmes mots, même audio, SSIM image 0,999 avec `maquette-v1/video-leo-v3.mp4`. Les médias de cet épisode ne sont pas versionnés : ils viennent de `/workspace/styleastuce/maquette-v1/`.

## Logo anti-vol (standard, actif par défaut)

Petit cartouche « SA Style Astuce » en Fraunces (SA orange #D9662B sur crème), fixe pendant toute la vidéo, sans animation, dans le coin bas droit de la zone commune TikTok + Reels (boîte x 770..934, y 1346..1412 pour 164 px de large). Réglage dans `episode.json` :

```json
"logo": {"actif": true, "variante": "creme", "opacite": 0.8, "largeur": 164}
```

`variante` : `creme` (défaut) ou `blanc` (blanc avec ombre douce) ; `opacite` 0.5..1 ; `largeur` 120..200 px. La QA (`qa.json` → `logo`) vérifie qu'aucun bord net n'entre dans un anneau de 10 à 22 px autour du logo (donc qu'il ne masque ni Léo, ni les cartes, ni les prix, ni les sous-titres).

## Pastille « 360° » (désactivée par défaut)

Depuis le 13/11 (demande d'Aymane), aucune étiquette « 360° » n'est affichée sur la rotation ; la rotation elle-même reste. Pour la réactiver sur un épisode : `"pastille_360": true` dans `episode.json`.

## Vignettes produit : segmentation des vêtements (défaut)

`sa.py vignettes` découpe maintenant le haut et le bas grâce au modèle `u2net_cloth_seg` (rembg, téléchargé une fois dans `~/.rembg`), carte mise en cache dans `public/leo/vet-<n>.png`. L'ancienne détection de peau par couleur mangeait les hauts beige, camel, rose ou rouge et gardait les cheveux longs d'Inès. Règles ajoutées : la classe « robe » (ensemble d'une seule couleur) est coupée à l'ourlet détecté ; un bas de haut classé « pantalon » revient au haut s'il est au-dessus de l'ourlet et que les deux couleurs diffèrent ; les mèches sombres reliées au bord supérieur du haut sont retirées (sauf sur un haut noir). Pour revenir à l'ancienne méthode sur une tenue : `"coupe": {"segmentation": "peau"}`.

## Mannequins et voix

`"mannequin": "leo"` (défaut) ou `"ines"` dans `episode.json` : `prompts` prend alors les références et le prompt de base dans `/workspace/styleastuce/<mannequin>/` (identite/maitre-visage.jpg, identite/maitre-corps.jpg, prompts.md) et accorde le texte (his/her, young man/young woman). `"chaussures_en"` (épisode ou tenue) remplace les baskets blanches par défaut dans le prompt (ex. bottines par temps de pluie). La voix vient du bloc `voix` : Benjamin `F9KUTOne5xOKqAbIU7yg` pour Léo, Koraly - Promo Video `rbFGGoDXFHtVghjHuS3E` pour Inès. `prompts` télécharge aussi la photo produit Uniqlo du coloris (`colorDisplayCode`).

## Ombre de contact (pieds posés au sol)

`sa.py timeline` lit le détourage de chaque tenue (`public/leo/cut-<n>.png`) et enregistre dans `props.json` → `looks[k].pieds` le bas des semelles (dernière ligne opaque) et, pour chaque chaussure, son propre bas et sa largeur. `Episode.tsx` (`ContactShadow`) cale dessus une ombre courte et dense sous chaque chaussure, qui remonte de 4 px derrière la semelle, plus une ombre ambiante légère sur la ligne de sol. Pendant un balayage de tenue, l'ombre suit la tenue dont les pieds sont visibles ; pendant une rotation 360°, elle s'efface avec Léo (la vidéo de rotation a son propre sol).

QA : `qa.json` → `ombre_contact` mesure, image par image (10 i/s, hors balayages et rotations), le nombre de lignes claires entre la semelle et l'ombre. Échec au-delà de 4 px (« Léo flotte »).
