#!/bin/bash

# Vérifier si l'environnement virtuel existe
if [ ! -d "venv" ]; then
    echo "Création de l'environnement virtuel..."
    python -m venv venv
    
    echo "Activation de l'environnement virtuel..."
    source venv/bin/activate
    
    echo "Installation des dépendances..."
    pip install pandas tkinter
else
    echo "Activation de l'environnement virtuel..."
    source venv/bin/activate
fi

# Lancer l'application
echo "Lancement de l'application..."
python main.py 