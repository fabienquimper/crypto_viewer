import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

class IncomeGainsViewer:
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
        self.asset_filter = self.create_multiselect(self.filters_frame, "Asset")
        self.transaction_type_filter = self.create_multiselect(self.filters_frame, "Transaction Type")
        self.label_filter = self.create_multiselect(self.filters_frame, "Label")
        self.taxable_filter = self.create_multiselect(self.filters_frame, "Taxable")

        # Boutons de filtres
        filters_buttons_frame = ttk.Frame(self.filters_frame)
        filters_buttons_frame.pack(fill=tk.X, pady=5)
        
        apply_filter_btn = ttk.Button(filters_buttons_frame, text="Appliquer les filtres", command=self.update_summary)
        apply_filter_btn.pack(side=tk.LEFT, padx=5)
        
        reset_filter_btn = ttk.Button(filters_buttons_frame, text="Reset", command=self.reset_filters)
        reset_filter_btn.pack(side=tk.LEFT, padx=5)

        export_btn = ttk.Button(filters_buttons_frame, text="📤 Exporter CSV", command=self.export_filtered_data)
        export_btn.pack(side=tk.LEFT, padx=5)

        # Séparateur
        separator = ttk.Separator(self.parent_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=5)

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
        for col, lb in [("Asset", self.asset_filter), 
                       ("Transaction Type", self.transaction_type_filter),
                       ("Label", self.label_filter),
                       ("Taxable", self.taxable_filter)]:
            selected = self.get_selected_values(lb)
            if selected:
                df = df[df[col].isin(selected)]
        return df

    def populate_filters(self):
        all_values = {
            "Asset": set(),
            "Transaction Type": set(),
            "Label": set(),
            "Taxable": set()
        }
        
        for df in self.dataframes.values():
            for col in all_values:
                if col in df.columns:
                    all_values[col].update(df[col].dropna().unique())

        for lb, col in [(self.asset_filter, "Asset"),
                        (self.transaction_type_filter, "Transaction Type"),
                        (self.label_filter, "Label"),
                        (self.taxable_filter, "Taxable")]:
            lb.delete(0, tk.END)
            for val in sorted(all_values[col]):
                lb.insert(tk.END, val)

    def update_summary(self):
        total_amount = 0
        total_value_eur = 0

        for df in self.dataframes.values():
            df_filtered = self.filter_df(df)
            if 'Amount' in df_filtered.columns:
                total_amount += pd.to_numeric(df_filtered['Amount'], errors='coerce').sum()
            if 'Value (EUR)' in df_filtered.columns:
                total_value_eur += pd.to_numeric(df_filtered['Value (EUR)'], errors='coerce').sum()

        self.summary.delete("1.0", tk.END)
        self.summary.insert(tk.END, f"Total Amount : {total_amount:.8f}\n")
        self.summary.insert(tk.END, f"Total Value (EUR) : {total_value_eur:.2f} EUR\n")

    def reset_filters(self):
        """Réinitialise tous les filtres en désélectionnant toutes les options"""
        for lb in [self.asset_filter, self.transaction_type_filter, 
                  self.label_filter, self.taxable_filter]:
            lb.selection_clear(0, tk.END)
        self.update_summary()

    def get_active_dataframes(self):
        """Retourne uniquement les dataframes des fichiers sélectionnés"""
        active_dfs = {}
        for filename, var in self.file_checkboxes.items():
            if var.get() and filename in self.dataframes:
                active_dfs[filename] = self.dataframes[filename]
        return active_dfs

    def export_filtered_data(self):
        """Exporte les données filtrées vers un nouveau fichier CSV"""
        if not self.dataframes:
            messagebox.showwarning("Export", "Aucune donnée à exporter. Veuillez d'abord charger des fichiers CSV.")
            return

        # Demander à l'utilisateur où sauvegarder le fichier
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Exporter les données filtrées"
        )
        
        if not filepath:  # L'utilisateur a annulé
            return

        try:
            # Concaténer tous les dataframes filtrés
            filtered_dfs = []
            for df in self.get_active_dataframes().values():
                df_filtered = self.filter_df(df)
                if not df_filtered.empty:
                    filtered_dfs.append(df_filtered)

            if not filtered_dfs:
                messagebox.showwarning("Export", "Aucune donnée ne correspond aux filtres actuels.")
                return

            # Concaténer tous les dataframes
            final_df = pd.concat(filtered_dfs, ignore_index=True)
            
            # Exporter vers CSV
            final_df.to_csv(filepath, index=False)
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