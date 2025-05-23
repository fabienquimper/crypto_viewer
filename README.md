# Application de Visualisation de Transactions Crypto

Cette application permet de visualiser et d'analyser des fichiers CSV contenant des transactions crypto-monnaies Binance (Binance Tax). L'avantage principale évite d'ouvrir sous Excel mais aussi d'ouvrir "plusieurs ficheirs" car Binance en génère un par an.

Cela permet de faire un résumé.

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

## Fonctionnalités

- Chargement de fichiers CSV
- Filtrage par type, label, devise envoyée et reçue
- Affichage des totaux (frais, montants envoyés et reçus)
- Visualisation détaillée des données par fichier
