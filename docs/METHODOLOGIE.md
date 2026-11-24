# Méthodologie

Ce document détaille les données retenues, les traitements appliqués et ce que les résultats permettent, ou non, de conclure. Pour une vue d'ensemble, commencez par le [README](../README.md).

## 1. Question

Le projet cherche à mesurer la sécheresse de 2026 en Bretagne et à la situer par rapport aux années précédentes. Il suit la chaîne qui va de la ressource à la décision : le niveau des nappes d'abord, les arrêtés de restriction ensuite.

Le périmètre couvre les quatre départements de la région administrative : Côtes-d'Armor, Finistère, Ille-et-Vilaine et Morbihan, soit 1 202 communes.

## 2. Les données

| Source | Contenu | Période | Maille |
|---|---|---|---|
| VigiEau, historique communal | Niveau de restriction quotidien par type de ressource | 2012 au 24 novembre 2026 | Commune |
| Hub'Eau Piézométrie | Niveau quotidien des nappes | Depuis 2008 | Station |
| API Découpage administratif | Communes, intercommunalités, coordonnées du centre | Situation actuelle | Commune |

### Lecture en flux de VigiEau

L'historique communal est un fichier national : près de 600 Mo compressés et 12 Go décompressés. Les communes bretonnes n'en représentent qu'une petite partie. Le pipeline lit donc l'archive pendant son téléchargement, découpe le JSON commune par commune et ne conserve que les jours avec une restriction en Bretagne. Il s'arrête dès que le fichier, trié par code INSEE, dépasse le Morbihan. Rien de volumineux n'est écrit sur le disque. Un test unitaire vérifie ce découpage avec des coupures arbitraires dans le flux.

## 3. Nettoyage

| Problème constaté | Traitement | Raison |
|---|---|---|
| Quelques communes VigiEau absentes du référentiel actuel | Écartées | Ce sont d'anciennes communes ; leur commune de rattachement a son propre historique |
| Îles sans intercommunalité | La commune sert d'intercommunalité | Le graphique dépliable a besoin d'un niveau intermédiaire pour chaque commune |
| Stations piézométriques au passé court | Exclues du calcul des centiles sous 8 années de mesure | Un centile sur trois ou quatre années n'a pas de sens |

## 4. Indicateurs

### Niveau de restriction d'une commune

Un arrêté peut viser séparément l'eau potable, les eaux souterraines et les eaux de surface. Pour chaque commune et chaque jour, le niveau retenu est le plus sévère des trois. L'échelle VigiEau compte quatre niveaux : vigilance, alerte, alerte renforcée et crise. La vigilance n'impose pas de restriction en elle-même : elle n'apparaît pas dans le rapport.

### Jours par commune

Les jours sont comptés par niveau, par commune et par mois. Un indicateur régional ou départemental est la moyenne par commune : le total des jours divisé par le nombre de communes du périmètre. Ce choix donne le même poids à une petite commune rurale et à une ville.

La part des communes en crise d'un mois compte les communes qui ont eu au moins un jour de crise ce mois-là.

### Niveau des nappes

Une nappe est naturellement plus basse en automne qu'au printemps. Comparer un niveau brut d'un mois à l'autre n'aurait donc pas de sens. Chaque mois d'une station est situé par rapport aux mêmes mois de sa propre chronique depuis 2008, sous forme de centile :

- 100 : le plus haut niveau observé pour ce mois ;
- 50 : la normale du mois ;
- 0 : le plus bas.

La valeur départementale est la médiane des stations du département. La moyenne régionale affichée dans le rapport est la moyenne des quatre départements. Le seuil de 20 qui délimite les « nappes basses » est une convention de lecture.

## 5. Modèle Power BI

Le modèle est en étoile :

| Table | Rôle |
|---|---|
| `dim_commune` | Commune, département, intercommunalité, coordonnées ; porte toutes les mesures |
| `dim_departement` | Les quatre départements |
| `dim_mois` | Calendrier mensuel 2008-2026 |
| `fact_restrictions_mois` | Jours d'alerte, d'alerte renforcée et de crise par commune et par mois |
| `fact_nappes_mois` | Centile médian par département et par mois |

Les tables sont lues depuis le classeur Excel publié dans ce dépôt, ce qui permet d'actualiser le rapport en ligne sans passerelle. Les mesures sont regroupées dans [`mesures.dax`](../powerbi/mesures.dax).

## 6. Contrôles automatiques

Le pipeline refuse d'écrire les tables si l'un de ces contrôles échoue :

- clé unique dans chacune des cinq tables ;
- toutes les communes des restrictions présentes dans le référentiel ;
- tous les mois présents dans le calendrier ;
- jamais plus de jours comptés que le mois n'en compte ;
- centiles présents et compris entre 0 et 100 ;
- coordonnées présentes pour chaque commune.

## 7. Vérifications

**2017 était-elle un artefact ?** Avec 207 jours de restriction par commune, cette année dépasse toutes les autres en durée. Les arrêtés s'enchaînent pourtant de février à octobre, et un document préfectoral cite l'état d'alerte du Morbihan dès le 3 février 2017. Le chiffre est conservé. C'est pour cette raison que le rapport distingue les niveaux : 2017 a été longue, mais sans aucun jour de crise.

**Le record de 2026 est-il dû à un département ?** Non. Les quatre départements se situent entre 105 et 110 jours de crise par commune, et 95 % des communes dépassent 100 jours.

## 8. Limites

- Les arrêtés traduisent une décision préfectorale, pas seulement l'état de la ressource. Une partie des écarts entre communes vient des pratiques de chaque département.
- Le centile situe une nappe par rapport à 19 années au plus : il dit si elle est basse pour la saison, pas si elle est vide.
- La médiane départementale masque les écarts entre stations d'un même département.
- Une concordance entre nappes et arrêtés ne décrit pas le processus de décision, qui tient aussi compte des débits des cours d'eau.
- Les moyennes par commune ne sont pas pondérées par la population.
- L'année 2026 est incomplète : les données s'arrêtent au 24 novembre.
- Seules les publications officielles des préfectures font foi pour les restrictions.

## 9. Pistes d'amélioration

- Ajouter les débits des cours d'eau (Hub'Eau Hydrométrie), qui pèsent dans les arrêtés bretons.
- Pondérer les indicateurs par la population pour mesurer le nombre d'habitants concernés.
- Compléter l'année 2026 une fois décembre écoulé.
