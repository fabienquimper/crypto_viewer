@echo off

REM Vérifier si l'environnement virtuel existe
if not exist venv (
    echo Création de l'environnement virtuel...
    python -m venv venv
    
    echo Activation de l'environnement virtuel...
    call venv\Scripts\activate.bat
    
    echo Installation des dépendances...
    pip install pandas tkinter
) else (
    echo Activation de l'environnement virtuel...
    call venv\Scripts\activate.bat
)

REM Lancer l'application
echo Lancement de l'application...
python main.py

pause 