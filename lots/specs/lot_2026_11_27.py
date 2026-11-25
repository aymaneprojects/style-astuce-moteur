"""Specs du lot 27-29/11/2026 (format « look »), construites depuis les scripts validés par Aymane le 25/11/2026 à 11:08.
Les narrations viennent de lot-2026-11-27/narrations.py et sont contrôlées mot pour mot contre scripts.md (jamais modifiées ici).
Usage : python3 lots/specs/lot_2026_11_27.py   (écrit episodes/<id>/episode.json + script.txt, et lots/2026-11-27_29.json)"""
import json, pathlib, sys
MOTEUR = pathlib.Path(__file__).resolve().parents[2]
LOT = MOTEUR.parent / 'lot-2026-11-27'
sys.path.insert(0, str(LOT)); from narrations import N
SCRIPTS = (LOT / 'scripts.md').read_text(encoding='utf-8')
for k, t in N.items(): assert f'> {t}\n' in SCRIPTS, f'{k} : narration différente du script validé'

VOIX = dict(leo=dict(fournisseur='elevenlabs', voice_name='Benjamin', voice_id='F9KUTOne5xOKqAbIU7yg'),
            ines=dict(fournisseur='elevenlabs', voice_name='Koraly - Promo Video', voice_id='rbFGGoDXFHtVghjHuS3E'))
for v in VOIX.values(): v.update(model_id='eleven_v4', language_code='fr', stability=0.45, similarity_boost=0.75, output_format='mp3_44100_128')
LOGO = dict(actif=True, variante='creme', opacite=0.8, largeur=164)
KL = 'https://www.kiabi.com/'
L_MANTEAU_H, L_PULL_F, L_JEAN_F, L_JEAN_H, L_CHAUSS_H = KL + 'manteau-blouson-homme_200776', KL + 'pull-gilet-femme_201516', KL + 'jean-large-femme_413002', KL + 'jean-homme_200856', KL + 'chaussures-homme_200886'
HM_BOTTINES = 'https://www2.hm.com/fr_fr/femme/catalogue-par-produit/chaussures/bottines.html'
MENTION = dict(l1='Prix du 25/11', l2='chaussures comprises, hors livraison')

def P(nom, enseigne, prix, zone, url, mot, mot_prix, desc_en, liste_url=None, prix_barre=None, nom_fiche=None):
    d = dict(nom=nom, enseigne=enseigne, prix=prix, zone=zone, url=url, mot=mot, mot_prix=mot_prix, desc_en=desc_en, nom_fiche=nom_fiche or nom)
    if liste_url: d['liste_url'] = liste_url
    if prix_barre: d['prix_barre'] = prix_barre
    return d

def T(l1, kw, mot_surligne, pre='', post=''): return dict(l1=l1, pre=pre, kw=kw, post=post, mot_surligne=mot_surligne)
def ST(mot, texte, surligne=None, mot_surligne=None):
    d = dict(mot=mot, texte=texte)
    if surligne: d.update(surligne=surligne, mot_surligne=mot_surligne or mot)
    return d

EP = [
 dict(n='E1', id='leo-epaules-larges-grand-froid', mannequin='leo', titre='Épaules larges : partie 2', date='2026-11-27', heure='12:30',
      accroche=T('Épaules larges ?', 'Pas cette doudoune', 'doudoune'),
      ouverture=dict(type='erreur', marque='croix', mot_bascule='Partie', sous_titre=ST('Partie', 'Partie 2 : spécial grand froid', 'grand froid', 'grand'),
                     erreur_en='a shiny puffer jacket with very wide horizontal quilted bands in light silver gray, zipped up to a round crew neck, worn over a plain gray crew-neck sweatshirt, straight mid-blue jeans, plain white low sneakers'),
      label='Grand froid', total='119 €', pieces=[
        P('Manteau long gris', 'Kiabi', '60 €', 'manteau', 'https://www.kiabi.com/manteau-long-esprit-lainage-gris_P3570285C3570286', 'Manteau', 'soixante',
          'long single-breasted wool-look overcoat in mid heather gray, knee length, worn open', L_MANTEAU_H, nom_fiche='Manteau long esprit lainage gris'),
        P('Pull col zippé marine', 'Primark', '20 €', 'haut', 'https://www.primark.com/fr-fr/p/pull-en-maille-a-col-zippe-bleu-marine-991181017528', 'Pull', 'vingt',
          'navy blue knit sweater with a quarter-zip collar, zip slightly open forming a V', nom_fiche='Pull en maille à col zippé bleu marine'),
        P('Chino large gris foncé', 'Jules', '15 €', 'bas', 'https://www.jules.com/fr-fr/p/100648218817.html', 'Chino', 'quinze',
          'dark gray wide-leg chino trousers with seam details, full length touching the boots', nom_fiche='Pantalon chino large avec découpes gris foncé'),
        P('Bottines Chelsea noires', 'Primark', '24 €', 'chaussures', 'https://www.primark.com/fr-fr/p/bottines-chelsea-noir-991182976804', 'Bottines', 'vingt-quatre',
          'black Chelsea boots with elastic side panels and a low rubber sole', nom_fiche='Bottines Chelsea noir')],
      astuce=dict(mot='Le', titre=T("L'astuce", 'manteau ouvert', 'ouvert'), sous_titres=[ST('col', 'Col en V : buste plus long', 'plus long', 'allongent')]),
      teaser=dict(mot='Abonne-toi', titre=T('Ce soir', 'Inès et les petites', 'petites'), sous_titre=ST('Abonne-toi', 'Abonne-toi pour la suite', 'Abonne-toi'))),
 dict(n='E2', id='ines-petite-manteau-court', mannequin='ines', titre='Petite ? Pas ce manteau', date='2026-11-27', heure='19:00',
      accroche=T('Petite ?', 'Ce manteau te coupe en deux', 'coupe'),
      ouverture=dict(type='erreur', marque='trait', marque_y=0.5, mot_bascule='Mets', sous_titre=ST('Mets', 'Mets plutôt ça', 'plutôt ça', 'plutôt'),
                     erreur_en='a long black padded puffer coat reaching the ankles, closed, over straight blue jeans that are too long and pool on the floor, flat black ankle boots partly hidden'),
      label='Petite', total='103,99 €', pieces=[
        P('Veste courte marron', 'Primark', '24 €', 'manteau', 'https://www.primark.com/fr-fr/p/veste-courte-a-col-cheminee-marron-991184884616', 'Veste', 'vingt-quatre',
          'short brown jacket with a funnel neck, ending at the hip, worn open', nom_fiche='Veste courte à col cheminée marron'),
        P('Pull col montant beige', 'Kiabi', '18 €', 'haut', 'https://www.kiabi.com/pull-col-montant-en-rib-beige_P3499922C3499752', 'Pull', 'dix-huit',
          'beige ribbed knit sweater with a high mock neck, tucked in at the front', L_PULL_F, nom_fiche='Pull col montant en rib beige'),
        P('Jean large L30', 'Kiabi', '22 €', 'bas', 'https://www.kiabi.com/jean-wide-leg-l30-bleu_P833382C3071823', 'Jean', 'vingt-deux',
          'mid-blue wide-leg high-waist jeans, length just grazing the floor over the boots', L_JEAN_F, nom_fiche='Jean wide leg L30 bleu'),
        P('Bottines talon bloc', 'H&M', '39,99 €', 'chaussures', 'https://www2.hm.com/fr_fr/productpage.1366863001.html', 'Bottines', 'trente-neuf',
          'black smooth leather ankle boots with a long pointed toe and a short block heel', HM_BOTTINES, nom_fiche='Bottines à talon bloc noir')],
      astuce=dict(mot='La', titre=T("L'astuce", 'veste à la hanche', 'hanche'), sous_titres=[ST('tes', 'Jambes plus longues', 'plus longues', 'longues')]),
      teaser=dict(mot='Demain', titre=T('Demain midi', 'Léo par -2 °C', 'Léo'), sous_titre=None)),
 dict(n='E3', id='leo-haul-uniqlo-moins-2', mannequin='leo', titre='Haul Uniqlo : -2 °C', date='2026-11-28', heure='12:30',
      accroche=T('-2 °C dehors', 'Tenue Uniqlo', "d'Uniqlo"),
      ouverture=dict(type='rotation', marque=None, sous_titre=None),
      label='-2 °C', total='123,69 €', pieces=[
        P('Col roulé HEATTECH noir', 'Uniqlo', '24,90 €', 'haut', 'https://www.uniqlo.com/fr/fr/products/E481442-000/00?colorDisplayCode=09', 'Col', 'vingt-quatre',
          'black fine-knit turtleneck sweater', nom_fiche='Col roulé HEATTECH cachemire mélangé Extra Chaud noir'),
        P('Doudoune PUFFERTECH beige', 'Uniqlo', '59,90 €', 'manteau', 'https://www.uniqlo.com/fr/fr/products/E486171-000/00?colorDisplayCode=32', 'Doudoune', 'cinquante-neuf',
          'beige matte hip-length padded puffer jacket with narrow quilting, worn open', nom_fiche='Doudoune PUFFERTECH beige'),
        P('Pantalon flanelle gris', 'Uniqlo', '19,90 €', 'bas', 'https://www.uniqlo.com/fr/fr/products/E486822-000/00?colorDisplayCode=06', 'Pantalon', 'dix-neuf',
          'gray flannel relaxed trousers with an elastic waist, ankle length over the boots', nom_fiche='Pantalon Easy 7/8 flanelle gris'),
        P('Bottes de neige', 'Decathlon', '18,99 €', 'chaussures', 'https://www.decathlon.fr/p/bottes-de-randonnee-neige-chaudes-impermeables-homme-nh100-noir/342110/c382m8752017', 'Bottes', 'dix-huit',
          'black warm waterproof lace-up snow hiking boots, mid height, chunky lug sole', nom_fiche='Bottes de randonnée neige NH100 noir')],
      astuce=dict(mot='Le', titre=T("L'astuce", 'chaud sans épaisseur', 'chauffe'), sous_titres=[]),
      teaser=dict(mot='Ce', titre=T('Ce soir', 'Inès et les grandes', 'grandes'), sous_titre=None)),
 dict(n='E4', id='ines-grande-jean-trop-court', mannequin='ines', titre='Grande ? Ton jean est trop court', date='2026-11-28', heure='19:00',
      accroche=T('Grande ?', 'Ton jean est trop court', 'jean'),
      ouverture=dict(type='erreur', marque='fleche', marque_y=0.9, mot_bascule='solution', sous_titre=ST('solution', 'La solution : Kiabi', 'Kiabi')),
      erreur_en='straight blue jeans that are clearly too short, ending well above the ankle bone, bare ankles visible, a plain gray crew-neck sweater, flat white sneakers',
      label='Grande', total='113,99 €', pieces=[
        P('Jean large noir L34', 'Kiabi', '22 €', 'bas', 'https://www.kiabi.com/jean-wide-leg-l34-noir_P848310C848209', 'Jean', 'vingt-deux',
          'black wide-leg high-waist jeans, extra long length touching the top of the sneakers', L_JEAN_F, nom_fiche='Jean wide leg L34 noir'),
        P('Pull oversize crème', 'Primark', '18 €', 'haut', 'https://www.primark.com/fr-fr/p/pull-oversize-en-melange-de-laine-a-col-ras-du-cou-creme-991170923116', 'Pull', 'dix-huit',
          'cream oversized wool-blend crew-neck sweater', nom_fiche='Pull oversize en mélange de laine à col ras du cou crème'),
        P('Pardessus droit écru', 'Primark', '24 €', 'manteau', 'https://www.primark.com/fr-fr/p/pardessus-droit-ecru-991179296114', 'Pardessus', 'vingt-quatre',
          'straight long single-breasted overcoat in heathered oatmeal taupe wool-look fabric (Primark names the color ecru, follow the product photo), worn open', nom_fiche='Pardessus droit écru'),
        P('Baskets en cuir', 'Decathlon', '49,99 €', 'chaussures', 'https://www.decathlon.fr/p/baskets-femme-en-cuir-player-80-blanc/363390/c183c309m8960403', 'Baskets', 'quarante-neuf',
          'white leather low-top court sneakers with a flat sole', nom_fiche='Baskets femme en cuir Player 80 blanc')],
      astuce=dict(mot='Le', titre=T("L'astuce", "jean jusqu'à la basket", 'basket'), sous_titres=[ST('ta', 'Jambe longue', 'longue')]),
      teaser=dict(mot='Demain', titre=T('Demain midi', 'Léo et le petit ventre', 'ventre'), sous_titre=None)),
 dict(n='E5', id='leo-petit-ventre-pluie', mannequin='leo', titre='Petit ventre ? Pas ce pull', date='2026-11-29', heure='12:30',
      accroche=T('Petit ventre ?', 'Pas ce pull moulant', 'moulant'),
      ouverture=dict(type='erreur', marque='cercle', marque_y=0.43, mot_bascule='Voilà', sous_titre=ST('Voilà', 'Même sous la pluie', 'pluie', 'pluie')),
      erreur_en='a thin tight light gray fine-knit sweater clinging to the belly, tucked into light blue skinny jeans with a belt, plain white sneakers',
      label='Pluie', total='84,98 €', pieces=[
        P('Pull col zippé marine', 'Celio', '35,99 €', 'haut', 'https://www.celio.com/fr-fr/p/pull-col-zippe-100-coton-pique---marine/1120804.html', 'Pull', 'trente-cinq',
          'navy blue cotton pique quarter-zip sweater, straight fit, worn untucked', nom_fiche='Pull col zippé 100% coton piqué marine'),
        P('Jean brut droit', 'Kiabi', '12 €', 'bas', 'https://www.kiabi.com/jean-regular-brut-l32-brut_P468719C468718', 'Jean', 'douze',
          'dark raw denim straight regular jeans', L_JEAN_H, nom_fiche='Jean regular brut L32'),
        P('Veste imperméable', 'Decathlon', '14,99 €', 'manteau', 'https://www.decathlon.fr/p/veste-de-randonnee-coupe-vent-impermeable-homme-raincut-full-zip-noir/350837/c382m8844533', 'Veste', 'quatorze',
          'black lightweight waterproof full-zip rain jacket with a hood folded down, worn open', nom_fiche='Veste coupe-vent imperméable Raincut Full Zip noir'),
        P('Baskets marron', 'Kiabi', '22 €', 'chaussures', 'https://www.kiabi.com/baskets-basses-a-lacets-marron_P3402680C3402681', 'Baskets', 'vingt-deux',
          'brown low-top lace-up sneakers with a white sole', L_CHAUSS_H, nom_fiche='Baskets basses à lacets marron')],
      astuce=dict(mot='Un', titre=T("L'astuce", 'haut foncé, veste ouverte', 'ouverte'), sous_titres=[]),
      teaser=dict(mot='Ce', titre=T('Ce soir', 'Inès et les jambes courtes', 'jambes'), sous_titre=None)),
 dict(n='E6', id='ines-jambes-courtes-59e', mannequin='ines', titre='Jambes courtes : 59 €', date='2026-11-29', heure='19:00',
      accroche=T('Jambes courtes ?', '59 €, bottines comprises', 'Cinquante-neuf'),
      ouverture=dict(type='rotation', marque='ligne', marque_mot='centimètres', sous_titre=None),
      label='Tout en noir', total='59 €', pieces=[
        P('Pull col roulé noir', 'Kiabi', '13 €', 'haut', 'https://www.kiabi.com/pull-fine-jauge-col-roule-noir_P3547291C3547294', 'Pull', 'treize',
          'black fine-gauge turtleneck sweater, tucked in', L_PULL_F, nom_fiche='Pull fine jauge col roulé noir'),
        P('Jean large noir', 'Kiabi', '22 €', 'bas', 'https://www.kiabi.com/jean-wide-leg-coupe-large-noir_P3354247C3353076', 'Jean', 'vingt-deux',
          'black wide-leg high-waist jeans, long enough to cover the top of the boots', L_JEAN_F, nom_fiche='Jean wide leg coupe large noir'),
        P('Bottines à talon', 'Primark', '24 €', 'chaussures', 'https://www.primark.com/fr-fr/p/bottines-a-talon-en-simili-cuir-stretch-noir-991191742804', 'Bottines', 'vingt-quatre',
          'black stretch faux-leather sock ankle boots with a medium block heel and a square toe', nom_fiche='Bottines à talon en simili cuir stretch noir')],
      astuce=dict(mot="L'astuce", titre=T("L'astuce", 'du jean aux chaussures', 'chaussures'), sous_titres=[ST("L'œil", "L'œil ne voit plus la coupure", 'coupure', "s'arrête")]),
      teaser=dict(mot='Dis-moi', titre=T('Dis-moi', 'ta morphologie', 'morphologie'), sous_titre=ST('commentaire', 'En commentaire', 'commentaire'))),
]

def episode(d):
    i = d['id']; O = {k: v for k, v in d['ouverture'].items() if v is not None}
    if O['type'] == 'erreur':
        O['image_erreur'] = f'media/{i}-erreur.jpg'
        if 'erreur_en' not in O: O['erreur_en'] = d['erreur_en']
    E = dict(id=i, format='look', titre=d['titre'], mannequin=d['mannequin'], date_releve='2026-11-25', logo=LOGO, script='script.txt', voix=VOIX[d['mannequin']],
             accroche=d['accroche'], ouverture=O,
             look=dict(label=d['label'], total=d['total'], image=f'media/{i}-look.jpg', rotation=f'media/rotation-{i}-look.mp4', coupe={}, pieces=d['pieces']),
             mention=MENTION, astuce=d['astuce'], teaser={k: v for k, v in d['teaser'].items() if v is not None},
             publication=dict(date_prevue=d['date'], heure=d['heure'], plateformes=['TikTok', 'Instagram Reels'], script_valide='Aymane, 25/11/2026 11:08',
                              legende_source=f"lot-2026-11-27/scripts.md ({d['n']})"))
    return E

if __name__ == '__main__':
    lot = dict(nom='2026-11-27_29', note='Nouvelle formule 20-26 s (format look). Scripts validés par Aymane le 25/11 à 11:08. Relancer « prix » le 27/11 au matin (Black Friday) avant toute voix. Si les crédits arrivent tard, décaler toute la série d’un créneau.', episodes=[])
    for d in EP:
        dst = MOTEUR / 'episodes' / d['id']; (dst / 'media' / 'produits').mkdir(parents=True, exist_ok=True)
        E = episode(d); f = dst / 'episode.json'
        json.dump(E, open(f, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        (dst / 'script.txt').write_text(N[d['n']] + '\n', encoding='utf-8')
        lot['episodes'].append(dict(id=d['id'], date=d['date'], heure=d['heure']))
        print('->', f)
    json.dump(lot, open(MOTEUR / 'lots' / '2026-11-27_29.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
