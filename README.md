# Application de Visualisation de Transactions Crypto

Cette application permet de visualiser et d'analyser des fichiers CSV contenant des transactions crypto-monnaies Binance (Binance Tax). L'avantage principale évite d'ouvrir sous Excel mais aussi d'ouvrir "plusieurs ficheirs" car Binance en génère un par an.

Cela permet de faire un résumé.

> **Note importante** : Ce projet est purement informatif et personnel, créé pour comprendre le fonctionnement des transactions crypto et leur impact fiscal. Les calculs et rapports générés ne constituent en aucun cas un conseil fiscal officiel. Pour vos déclarations fiscales, veuillez consulter un professionnel qualifié ou les services fiscaux compétents.

## Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

## Installation

1. Créer un environnement virtuel :

```bash
python -m venv venv
```

2. Activer l'environnement virtuel :

- Sur Windows :

```bash
.\venv\Scripts\activate
```

- Sur Linux/Mac :

```bash
source venv/bin/activate
```

3. Installer les dépendances :

```bash
pip install -r requirements.txt
```

## Utilisation

1. Lancer l'application :

```bash
python main.py
```

2. Utiliser le bouton "Charger CSV" pour sélectionner vos fichiers de transactions
3. Utiliser les filtres pour affiner l'affichage des données
4. Double-cliquer sur un fichier dans la liste pour voir son contenu détaillé

## Fonctionnalités

### Visualisation et Filtrage
- Chargement de fichiers CSV
- Filtrage par type, label, devise envoyée et reçue
- Affichage des totaux (frais, montants envoyés et reçus)
- Visualisation détaillée des données par fichier

### Calcul Fiscal
L'application permet de calculer les gains selon différentes méthodes :

1. **Gains Réalisés (Plus-values)**
   - Calcul basé sur la méthode du Prix Moyen Pondéré (PMP/ACB)
   - Séparation claire des transactions EUR/crypto
   - Rapports détaillés par année et par devise
   - Graphiques d'évolution des gains
   - Export des gains réalisés en CSV

   > **Note sur les calculs ACB** : La fonctionnalité de calcul automatique des plus-values selon la méthode ACB (Average Cost Basis) n'est pas encore fiable. Il est recommandé d'utiliser les rapports "Realized Capital Gain" générés directement par Binance et de les importer dans l'application via le bouton "Calculate Realized Gain". Cette méthode garantit des calculs plus précis et conformes aux données officielles de Binance.

2. **Gains de Revenus (Rewards)**
   - Calcul des récompenses par devise et par année
   - Export des gains de revenus en CSV
   - Filtrage par type de récompense

### Enrichissement et Correction des Données
- **Update CSV Transaction file** : Enrichissement automatique des fichiers CSV avec les prix EUR
  - Ajout des colonnes "Sent Price EUR", "Received Price EUR", "Sent Value EUR", "Received Value EUR"
  - Utilisation de l'API Binance pour obtenir les prix historiques
  - Conversion via USDT si nécessaire
  - Cache des prix pour optimiser les performances
  - Mode rapide disponible

- **Correct CSV** : Correction des montants EUR manquants
  - Conversion intermédiaire (ex: FET/USDT puis EUR/USDT)
  - Log détaillé des corrections
  - Affichage en temps réel des modifications

### Export et Fusion
- Export des transactions EUR
- Export des transactions de récompenses
- Export des données filtrées
- Fusion automatique de plusieurs fichiers CSV
- Validation de l'unicité des transactions

### Visualisation Graphique
- Graphiques d'évolution des soldes par devise
- Graphiques des gains réalisés
- Affichage interactif avec tooltips
- Zoom et navigation temporelle

## Création de l'exécutable

Pour créer un exécutable autonome :

1. S'assurer que toutes les dépendances sont installées :

```bash
pip install -r requirements.txt
```

2. Lancer le script de build :

```bash
python build.py
```

3. L'exécutable sera créé dans le dossier `dist` sous le nom `CryptoCSVViewer.exe`

## Notes Importantes

1. **Rewards (5KU)**
   - Les calculs de récompenses sont stables et fiables
   - Les montants peuvent être directement ajoutés en 5KU

2. **Plus-values (3BN ou Flat Tax)**
   - Les calculs utilisent la méthode ACB (Average Cost Basis)
   - Les rapports peuvent varier selon la source des données
   - À déclarer en 3BN ou en plus-value (flat tax)
