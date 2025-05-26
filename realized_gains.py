import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

class RealizedGainsViewer:
    def __init__(self, parent_frame, summary_widget):
        self.parent_frame = parent_frame
        self.summary = summary_widget  # Référence à la zone de résumé globale
        self.dataframes = {}
        self.check_vars = {}
        self.current_directory = str(Path.home())
        
        self.setup_ui()

    def setup_ui(self):
        # Barre d'outils
        toolbar = ttk.Frame(self.parent_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        # Boutons de la barre d'outils
        btn_load = ttk.Button(toolbar, text="📂 Ouvrir", command=self.load_csv)
        btn_load.pack(side=tk.LEFT, padx=2)

        # Chemin actuel
        self.path_var = tk.StringVar(value=self.current_directory)
        path_entry = ttk.Entry(toolbar, textvariable=self.path_var, width=50)
        path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        path_entry.bind('<Return>', self.change_directory)

        # Bouton de calcul des gains
        btn_calculate = ttk.Button(toolbar, text="Calculate Realized Gains", command=self.calculate_realized_gains)
        btn_calculate.pack(side=tk.LEFT, padx=5)

        # Bouton d'export des gains
        btn_export = ttk.Button(toolbar, text="📤 Export Realized Gains CSV", command=self.export_realized_gains)
        btn_export.pack(side=tk.LEFT, padx=5)

        # Section principale avec panneau divisé
        paned = ttk.PanedWindow(self.parent_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Panneau de gauche (liste des fichiers chargés)
        left_frame = ttk.LabelFrame(paned, text="Fichiers chargés", padding="5")
        paned.add(left_frame, weight=1)

        # Frame pour les boutons de la liste
        list_buttons = ttk.Frame(left_frame)
        list_buttons.pack(fill=tk.X, pady=(0, 5))
        
        btn_select_all = ttk.Button(list_buttons, text="✓ Tout sélectionner", command=self.select_all_files)
        btn_select_all.pack(side=tk.LEFT, padx=2)
        
        btn_deselect_all = ttk.Button(list_buttons, text="✗ Tout désélectionner", command=self.deselect_all_files)
        btn_deselect_all.pack(side=tk.LEFT, padx=2)

        # Liste des fichiers avec cases à cocher
        self.files_listbox = tk.Listbox(left_frame, selectmode=tk.EXTENDED)
        self.files_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # Scrollbar pour la liste
        list_scroll = ttk.Scrollbar(left_frame, orient="vertical", command=self.files_listbox.yview)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.files_listbox.configure(yscrollcommand=list_scroll.set)

        # Dictionnaire pour stocker les variables des cases à cocher
        self.file_checkboxes = {}

        # Panneau de droite (filtres)
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)

        # Filtres dans un LabelFrame
        self.filters_frame = ttk.LabelFrame(right_frame, text="Filtres", padding="5")
        self.filters_frame.pack(fill=tk.BOTH, expand=True)

        # Création des filtres
        self.currency_filter = self.create_multiselect(self.filters_frame, "Currency name")
        self.transaction_type_filter = self.create_multiselect(self.filters_frame, "Transaction type")
        self.label_filter = self.create_multiselect(self.filters_frame, "Label")

        # Boutons de filtres
        filters_buttons_frame = ttk.Frame(self.filters_frame)
        filters_buttons_frame.pack(fill=tk.X, pady=5)
        
        apply_filter_btn = ttk.Button(filters_buttons_frame, text="Appliquer les filtres", command=self.update_summary)
        apply_filter_btn.pack(side=tk.LEFT, padx=5)
        
        reset_filter_btn = ttk.Button(filters_buttons_frame, text="Reset", command=self.reset_filters)
        reset_filter_btn.pack(side=tk.LEFT, padx=5)

    def create_multiselect(self, parent, label):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=2)
        
        lbl = ttk.Label(frame, text=label)
        lbl.pack(side=tk.LEFT, padx=(0, 5))
        
        lb = tk.Listbox(frame, selectmode=tk.MULTIPLE, exportselection=False, height=4)
        lb.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Ajout d'une scrollbar
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=lb.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        lb.configure(yscrollcommand=scrollbar.set)
        
        return lb

    def detect_decimal(self, filepath):
        with open(filepath, 'r') as f:
            sample = f.read(2048)
            return ',' if sample.count(',') > sample.count('.') else '.'

    def load_csv(self):
        """Ouvre la boîte de dialogue pour charger des fichiers CSV"""
        filepaths = filedialog.askopenfilenames(
            initialdir=self.current_directory,
            filetypes=[("CSV files", "*.csv")],
            title="Sélectionner des fichiers CSV"
        )
        for path in filepaths:
            self.load_single_file(path)

    def load_single_file(self, filepath):
        """Charge un seul fichier CSV"""
        if filepath not in self.dataframes:
            try:
                decimal = self.detect_decimal(filepath)
                df = pd.read_csv(filepath, decimal=decimal)
                name = os.path.basename(filepath)
                self.dataframes[name] = df
                
                # Ajouter le fichier à la liste avec une case à cocher
                self.create_checkbox(self.files_listbox, name)
                
                self.populate_filters()
                self.update_summary()
            except Exception as e:
                messagebox.showerror("Erreur de chargement", str(e))

    def create_checkbox(self, parent, filename):
        """Crée une case à cocher pour un fichier"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=5, pady=2)
        
        var = tk.BooleanVar(value=True)
        self.file_checkboxes[filename] = var
        
        cb = ttk.Checkbutton(frame, text=filename, variable=var, 
                            command=self.on_file_selection_change)
        cb.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        return frame

    def on_file_selection_change(self):
        """Appelé quand la sélection des fichiers change"""
        self.update_summary()

    def get_selected_values(self, listbox):
        return [listbox.get(i) for i in listbox.curselection()]

    def filter_df(self, df):
        for col, lb in [("Currency name", self.currency_filter),
                       ("Transaction type", self.transaction_type_filter),
                       ("Label", self.label_filter)]:
            selected = self.get_selected_values(lb)
            if selected:
                df = df[df[col].isin(selected)]
        return df

    def populate_filters(self):
        all_values = {
            "Currency name": set(),
            "Transaction type": set(),
            "Label": set()
        }
        
        for df in self.dataframes.values():
            for col in all_values:
                if col in df.columns:
                    all_values[col].update(df[col].dropna().unique())

        for lb, col in [(self.currency_filter, "Currency name"),
                        (self.transaction_type_filter, "Transaction type"),
                        (self.label_filter, "Label")]:
            lb.delete(0, tk.END)
            for val in sorted(all_values[col]):
                lb.insert(tk.END, val)

    def update_summary(self):
        total_proceeds = 0
        total_cost_basis = 0
        total_gains = 0

        for df in self.dataframes.values():
            df_filtered = self.filter_df(df)
            if 'Proceeds (EUR)' in df_filtered.columns:
                total_proceeds += pd.to_numeric(df_filtered['Proceeds (EUR)'], errors='coerce').sum()
            if 'Cost basis (EUR)' in df_filtered.columns:
                total_cost_basis += pd.to_numeric(df_filtered['Cost basis (EUR)'], errors='coerce').sum()
            if 'Gains (EUR)' in df_filtered.columns:
                total_gains += pd.to_numeric(df_filtered['Gains (EUR)'], errors='coerce').sum()

        self.summary.delete("1.0", tk.END)
        self.summary.insert(tk.END, f"Total Proceeds (EUR) : {total_proceeds:.2f} EUR\n")
        self.summary.insert(tk.END, f"Total Cost Basis (EUR) : {total_cost_basis:.2f} EUR\n")
        self.summary.insert(tk.END, f"Total Gains (EUR) : {total_gains:.2f} EUR\n")

    def reset_filters(self):
        """Réinitialise tous les filtres en désélectionnant toutes les options"""
        for lb in [self.currency_filter, self.transaction_type_filter, self.label_filter]:
            lb.selection_clear(0, tk.END)
        self.update_summary()

    def get_active_dataframes(self):
        """Retourne uniquement les dataframes des fichiers sélectionnés"""
        active_dfs = {}
        for filename, var in self.file_checkboxes.items():
            if var.get() and filename in self.dataframes:
                active_dfs[filename] = self.dataframes[filename]
        return active_dfs

    def calculate_realized_gains(self):
        """Calcule les gains réalisés totaux et par année"""
        if not self.dataframes:
            messagebox.showwarning("Calcul des gains", "Aucune donnée à analyser. Veuillez d'abord charger des fichiers CSV.")
            return

        try:
            # Concaténer uniquement les dataframes actifs
            all_data = pd.concat(self.get_active_dataframes().values(), ignore_index=True)
            
            # Convertir les colonnes de dates
            if 'Acquired' in all_data.columns:
                all_data['Acquired'] = pd.to_datetime(all_data['Acquired'], errors='coerce')
                all_data['Year'] = all_data['Acquired'].dt.year

            # Convertir les colonnes numériques
            numeric_columns = ['Currency amount', 'Proceeds (EUR)', 'Cost basis (EUR)', 'Gains (EUR)', 'Holding period (Days)']
            for col in numeric_columns:
                if col in all_data.columns:
                    all_data[col] = pd.to_numeric(all_data[col], errors='coerce')

            # Calculer les totaux globaux par devise
            self.summary.delete("1.0", tk.END)
            self.summary.insert(tk.END, "=== Gains Réalisés Globaux ===\n\n")

            # Calculer les totaux par devise
            gains_by_currency = all_data.groupby('Currency name').agg({
                'Currency amount': 'sum',
                'Proceeds (EUR)': 'sum',
                'Cost basis (EUR)': 'sum',
                'Gains (EUR)': 'sum'
            }).round(8)

            for currency, row in gains_by_currency.iterrows():
                self.summary.insert(tk.END, f"{currency}:\n")
                self.summary.insert(tk.END, f"  Montant: {row['Currency amount']:.8f}\n")
                self.summary.insert(tk.END, f"  Proceeds: {row['Proceeds (EUR)']:.2f} EUR\n")
                self.summary.insert(tk.END, f"  Cost Basis: {row['Cost basis (EUR)']:.2f} EUR\n")
                self.summary.insert(tk.END, f"  Gains: {row['Gains (EUR)']:.2f} EUR\n\n")

            # Calculer les totaux globaux
            total_proceeds = all_data['Proceeds (EUR)'].sum()
            total_cost_basis = all_data['Cost basis (EUR)'].sum()
            total_gains = all_data['Gains (EUR)'].sum()

            self.summary.insert(tk.END, "=== Totaux Globaux ===\n")
            self.summary.insert(tk.END, f"Total Proceeds: {total_proceeds:.2f} EUR\n")
            self.summary.insert(tk.END, f"Total Cost Basis: {total_cost_basis:.2f} EUR\n")
            self.summary.insert(tk.END, f"Total Gains: {total_gains:.2f} EUR\n")

            # Calculer les totaux par année
            if 'Year' in all_data.columns:
                self.summary.insert(tk.END, "\n=== Gains par Année ===\n\n")
                
                for year in sorted(all_data['Year'].unique()):
                    if pd.isna(year):
                        continue
                    
                    year_data = all_data[all_data['Year'] == year]
                    
                    # Calculer les totaux par devise pour cette année
                    year_gains = year_data.groupby('Currency name').agg({
                        'Currency amount': 'sum',
                        'Proceeds (EUR)': 'sum',
                        'Cost basis (EUR)': 'sum',
                        'Gains (EUR)': 'sum'
                    }).round(8)
                    
                    self.summary.insert(tk.END, f"\n=== {int(year)} ===\n")
                    
                    # Afficher les gains par devise pour cette année
                    for currency, row in year_gains.iterrows():
                        self.summary.insert(tk.END, f"{currency}:\n")
                        self.summary.insert(tk.END, f"  Montant: {row['Currency amount']:.8f}\n")
                        self.summary.insert(tk.END, f"  Proceeds: {row['Proceeds (EUR)']:.2f} EUR\n")
                        self.summary.insert(tk.END, f"  Cost Basis: {row['Cost basis (EUR)']:.2f} EUR\n")
                        self.summary.insert(tk.END, f"  Gains: {row['Gains (EUR)']:.2f} EUR\n\n")
                    
                    # Afficher les totaux pour cette année
                    year_total_proceeds = year_data['Proceeds (EUR)'].sum()
                    year_total_cost_basis = year_data['Cost basis (EUR)'].sum()
                    year_total_gains = year_data['Gains (EUR)'].sum()
                    
                    self.summary.insert(tk.END, f"Totaux {int(year)}:\n")
                    self.summary.insert(tk.END, f"  Proceeds: {year_total_proceeds:.2f} EUR\n")
                    self.summary.insert(tk.END, f"  Cost Basis: {year_total_cost_basis:.2f} EUR\n")
                    self.summary.insert(tk.END, f"  Gains: {year_total_gains:.2f} EUR\n")

        except Exception as e:
            messagebox.showerror("Erreur de calcul", f"Une erreur est survenue lors du calcul des gains :\n{str(e)}")

    def export_realized_gains(self):
        """Exporte les données de gains réalisés vers un fichier CSV trié par date d'acquisition"""
        if not self.dataframes:
            messagebox.showwarning("Export", "Aucune donnée à exporter. Veuillez d'abord charger des fichiers CSV.")
            return

        try:
            # Demander à l'utilisateur où sauvegarder le fichier
            filepath = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                title="Exporter les gains réalisés"
            )
            
            if not filepath:  # L'utilisateur a annulé
                return

            # Concaténer tous les dataframes actifs
            all_data = pd.concat(self.get_active_dataframes().values(), ignore_index=True)
            
            # Convertir la colonne Acquired en datetime si elle existe
            if 'Acquired' in all_data.columns:
                all_data['Acquired'] = pd.to_datetime(all_data['Acquired'], errors='coerce')
                # Trier par date d'acquisition
                all_data = all_data.sort_values('Acquired')
                # Reconvertir en format string pour l'export
                all_data['Acquired'] = all_data['Acquired'].dt.strftime('%Y-%m-%d %H:%M:%S')
                all_data['Sold'] = pd.to_datetime(all_data['Sold'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')

            # Exporter vers CSV
            all_data.to_csv(filepath, index=False)
            messagebox.showinfo("Export", f"Données exportées avec succès vers :\n{filepath}")
            
        except Exception as e:
            messagebox.showerror("Erreur d'export", f"Une erreur est survenue lors de l'export :\n{str(e)}")

    def change_directory(self, event=None):
        """Change le répertoire courant"""
        new_path = self.path_var.get()
        if os.path.isdir(new_path):
            self.current_directory = new_path
        else:
            messagebox.showerror("Erreur", "Chemin invalide")

    def select_all_files(self):
        """Sélectionne tous les fichiers dans la liste"""
        for filename in self.dataframes.keys():
            if filename in self.file_checkboxes:
                self.file_checkboxes[filename].set(True)
        self.update_summary()

    def deselect_all_files(self):
        """Désélectionne tous les fichiers dans la liste"""
        for filename in self.dataframes.keys():
            if filename in self.file_checkboxes:
                self.file_checkboxes[filename].set(False)
        self.update_summary() 