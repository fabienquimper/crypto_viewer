import PyInstaller.__main__
import os

# Chemin vers le fichier principal
main_script = os.path.join(os.path.dirname(__file__), 'main.py')

# Options pour PyInstaller
options = [
    main_script,  # Script principal
    '--name=CryptoCSVViewer',  # Nom de l'exécutable
    '--onefile',  # Créer un seul fichier exécutable
    '--windowed',  # Ne pas afficher la console
    '--clean',  # Nettoyer le cache
    '--add-data=README.md;.',  # Inclure le README
    '--icon=NONE',  # Pas d'icône pour l'instant
    '--noconfirm',  # Ne pas demander de confirmation
]

# Lancer PyInstaller
PyInstaller.__main__.run(options) 