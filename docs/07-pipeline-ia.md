# 7. Pipeline IA

Objectif : utiliser l'IA **massivement pour gagner du temps**, tout en gardant un contenu
**original** et donc monétisable (voir [02-monetisation.md](02-monetisation.md#ia-usage-important-dans-ce-projet)).

> Les outils cités sont des **exemples** : le marché bouge très vite. Avant de payer,
> vérifier (1) que l'outil existe toujours, (2) son prix, (3) que la licence autorise
> l'**usage commercial**.

## Où l'IA intervient (et où elle n'intervient pas)

| Étape | Rôle de l'IA | Gain | Ce qui reste à nous |
|---|---|---|---|
| **Idées & scripts** | Assistant conversationnel (Claude, etc.) : proposer des variantes de gags, trouver des chutes, vérifier la règle de trois | ⭐⭐⭐ | Choisir, réécrire, garder le ton |
| **Storyboard** | Générateur d'images pour visualiser une scène (usage interne, jamais publié) | ⭐⭐ | Cadrage et rythme |
| **Création des modèles 3D** | *Image/texte vers 3D* (ex. Meshy, Tripo, Rodin) pour une **base** de Bip et Mocha, puis **nettoyage et retopologie** dans Blender | ⭐⭐⭐ | Design final, proportions, rig |
| **Accessoires & décor** | Mêmes outils pour les objets (tasse, machine à café, plante, carton…) | ⭐⭐⭐ | Cohérence de style |
| **Textures** | Génération de textures et matériaux | ⭐⭐ | Palette de la chaîne |
| **Rig & animations de base** | Auto-rig + bibliothèques d'animations (ex. Mixamo pour Bip ; pour Mocha, un rig quadrupède à adapter) | ⭐⭐⭐ | Ajuster au personnage |
| **Animation** | *Capture de mouvement depuis une vidéo* (ex. Rokoko Vision, Move.ai, DeepMotion) : on se filme au téléphone en jouant Bip, l'IA convertit en animation | ⭐⭐⭐ | Le jeu d'acteur, le timing comique |
| **Poses & physique** | Outils d'animation assistée (ex. Cascadeur) pour chutes et sauts réalistes | ⭐⭐ | Exagération cartoon |
| **Bruitages** | Génération de sons à partir d'une description (ex. ElevenLabs Sound Effects) | ⭐⭐⭐ | Choix, mixage |
| **Voix de Bip** | Synthèse/traitement de sons robotiques à partir de nos propres bips | ⭐⭐ | Identité sonore cohérente |
| **Musique** | Génération musicale (ex. Suno, Udio) — **offre payante avec droits commerciaux obligatoire** | ⭐⭐ | Garder 3–4 thèmes récurrents |
| **Post-production** | Upscale, interpolation d'images (ex. Topaz), débruitage du rendu | ⭐⭐ | — |
| **Publication** | Proposer légendes et hashtags en anglais simple | ⭐ | Valider |

### Ce qu'on ne fait **pas**
- ❌ Générer l'épisode entier en *texte → vidéo* : les personnages changent d'un plan à
  l'autre, le résultat ressemble à des milliers d'autres vidéos IA, et c'est exactement
  le profil « non original ou synthétique » qui fait perdre la monétisation.
- ❌ Utiliser l'*image → vidéo* sur Bip et Mocha pour les plans principaux.
  Possible en appoint pour un **plan d'ambiance** (pluie à la fenêtre, ciel qui change),
  étiqueté IA.
- ❌ Copier le style d'un studio ou d'un personnage existant dans les prompts.

## Gain de temps estimé
| Étape | Sans IA | Avec IA |
|---|---|---|
| Création de Bip + Mocha (une seule fois) | 3–4 semaines | ~1 semaine |
| Décors + 30 accessoires (une seule fois) | 3 semaines | ~1 semaine |
| Animation d'un épisode | 4–6 h | ~1 h 30 |
| Sound design d'un épisode | 1 h 30 | ~30 min |

C'est ce qui permet de tenir **3 épisodes par semaine avec 2 h par jour**.

## Budget indicatif
- Démarrage possible à **0 €** (Blender, Mixamo, offres gratuites) pour la phase de test.
- Dès la publication : prévoir **un abonnement musique et un abonnement bruitages**
  avec droits commerciaux (les offres gratuites l'interdisent souvent).
- À ajouter selon les besoins : outil image→3D, capture de mouvement.
- Règle : **ne payer un outil que lorsqu'il fait gagner au moins 2 h par semaine.**

## Traçabilité (à remplir pour chaque épisode)
Dans `episodes/NN-titre/notes.md` :
```
Outils IA utilisés : …
Part générée par IA (estimation) : modèles 3D ?  animation ?  sons ?  musique ?  plans vidéo ?
Étiquette IA activée : oui / non
Monétisation : acceptée / refusée (motif)
```
Après 20 épisodes, ce tableau dira quel dosage d'IA TikTok accepte pour notre chaîne.
