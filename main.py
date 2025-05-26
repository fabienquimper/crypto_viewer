import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from income_gains import IncomeGainsViewer
from realized_gains import RealizedGainsViewer
from transactions import TransactionsViewer

class CryptoBinanceViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Crypto Binance Viewer")
        self.current_directory = str(Path.home())

        # Configuration du style
        self.style = ttk.Style()
        # Essayer différents thèmes disponibles
        available_themes = self.style.theme_names()
        preferred_themes = ['clam', 'alt', 'default', 'classic']
        
        for theme in preferred_themes:
            if theme in available_themes:
                self.style.theme_use(theme)
                break
        
        # Configuration de la fenêtre principale
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        self.setup_ui()

    def setup_ui(self):
        # Frame principal avec padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Notebook (onglets)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Onglet Transactions
        self.transactions_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.transactions_tab, text="Transactions")

        # Onglet Realized Capital Gains
        self.capital_gains_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.capital_gains_tab, text="Realized Capital Gains")

        # Onglet Income Gains
        self.income_gains_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.income_gains_tab, text="Income Gains")

        # Séparateur redimensionnable
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=5)

        # Résumé dans un LabelFrame
        summary_frame = ttk.LabelFrame(main_frame, text="Résumé", padding="5")
        summary_frame.pack(fill=tk.BOTH, expand=True)

        self.summary = tk.Text(summary_frame, height=6, wrap=tk.WORD)
        self.summary.pack(fill=tk.BOTH, expand=True)

        # Initialiser les onglets après avoir créé le résumé
        self.transactions_viewer = TransactionsViewer(self.transactions_tab, self.summary)
        self.income_gains_viewer = IncomeGainsViewer(self.income_gains_tab, self.summary)
        self.realized_gains_viewer = RealizedGainsViewer(self.capital_gains_tab, self.summary)

if __name__ == "__main__":
    root = tk.Tk()
    app = CryptoBinanceViewer(root)
    root.mainloop()