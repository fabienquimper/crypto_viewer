import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

class CryptoBinanceViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Crypto Binance Viewer")
        self.dataframes = {}
        self.check_vars = {}
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
        self.setup_transactions_tab()

        # Onglet Realized Capital Gains
        self.capital_gains_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.capital_gains_tab, text="Realized Capital Gains")
        self.setup_capital_gains_tab()

        # Onglet Income Gains
        self.income_gains_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.income_gains_tab, text="Income Gains")
        self.setup_income_gains_tab()

        # Séparateur redimensionnable
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=5)

        # Résumé dans un LabelFrame
        summary_frame = ttk.LabelFrame(main_frame, text="Résumé", padding="5")
        summary_frame.pack(fill=tk.BOTH, expand=True)

        self.summary = tk.Text(summary_frame, height=6, wrap=tk.WORD)
        self.summary.pack(fill=tk.BOTH, expand=True)

    def setup_transactions_tab(self):
        """Configure l'onglet Transactions"""
        # Barre d'outils
        toolbar = ttk.Frame(self.transactions_tab)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        # Boutons de la barre d'outils
        btn_load = ttk.Button(toolbar, text="📂 Ouvrir", command=self.load_csv)
        btn_load.pack(side=tk.LEFT, padx=2)

        # Chemin actuel
        self.path_var = tk.StringVar(value=self.current_directory)
        path_entry = ttk.Entry(toolbar, textvariable=self.path_var, width=50)
        path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        path_entry.bind('<Return>', self.change_directory)

        # Bouton de calcul EUR
        btn_calc_eur = ttk.Button(toolbar, text="💰 Calculate all EUR spend", command=self.calculate_eur_totals)
        btn_calc_eur.pack(side=tk.LEFT, padx=5)

        # Bouton d'export EUR
        btn_export_eur = ttk.Button(toolbar, text="📤 Export EUR transactions", command=self.export_eur_transactions)
        btn_export_eur.pack(side=tk.RIGHT, padx=5)

        # Section principale avec panneau divisé
        paned = ttk.PanedWindow(self.transactions_tab, orient=tk.HORIZONTAL)
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

        # Création des filtres avec des styles améliorés
        self.type_filter = self.create_multiselect(self.filters_frame, "Type")
        self.label_filter = self.create_multiselect(self.filters_frame, "Label")
        self.send_currency_filter = self.create_multiselect(self.filters_frame, "Sent Currency")
        self.received_currency_filter = self.create_multiselect(self.filters_frame, "Received Currency")

        # Boutons de filtres
        filters_buttons_frame = ttk.Frame(self.filters_frame)
        filters_buttons_frame.pack(fill=tk.X, pady=5)
        
        apply_filter_btn = ttk.Button(filters_buttons_frame, text="Appliquer les filtres", command=self.update_summary)
        apply_filter_btn.pack(side=tk.LEFT, padx=5)
        
        reset_filter_btn = ttk.Button(filters_buttons_frame, text="Reset", command=self.reset_filters)
        reset_filter_btn.pack(side=tk.LEFT, padx=5)

        export_btn = ttk.Button(filters_buttons_frame, text="📤 Exporter CSV", command=self.export_filtered_data)
        export_btn.pack(side=tk.LEFT, padx=5)

        validate_btn = ttk.Button(filters_buttons_frame, text="✓ Valider unicité", command=self.validate_transaction_uniqueness)
        validate_btn.pack(side=tk.LEFT, padx=5)

    def setup_capital_gains_tab(self):
        """Configure l'onglet Realized Capital Gains"""
        # Frame temporaire avec un message
        frame = ttk.Frame(self.capital_gains_tab, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        label = ttk.Label(frame, text="Fonctionnalité à venir :\nCalcul des plus-values réalisées", 
                         justify=tk.CENTER, font=('Helvetica', 12))
        label.pack(expand=True)

    def setup_income_gains_tab(self):
        """Configure l'onglet Income Gains"""
        # Frame temporaire avec un message
        frame = ttk.Frame(self.income_gains_tab, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        label = ttk.Label(frame, text="Fonctionnalité à venir :\nCalcul des revenus", 
                         justify=tk.CENTER, font=('Helvetica', 12))
        label.pack(expand=True)

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

    def open_csv_viewer(self, filename):
        """Ouvre une fenêtre pour visualiser le contenu d'un fichier CSV"""
        df = self.dataframes.get(filename)
        if df is not None:
            new_win = tk.Toplevel(self.root)
            new_win.title(f"Données - {filename}")
            new_win.geometry("800x600")

            # Créer un Treeview pour afficher les données
            tree = ttk.Treeview(new_win)
            tree.pack(fill=tk.BOTH, expand=True)

            # Ajouter une scrollbar
            scrollbar = ttk.Scrollbar(new_win, orient="vertical", command=tree.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            tree.configure(yscrollcommand=scrollbar.set)

            # Configurer les colonnes
            tree["columns"] = list(df.columns)
            tree["show"] = "headings"

            # Configurer les en-têtes
            for column in df.columns:
                tree.heading(column, text=column)
                tree.column(column, width=100)

            # Ajouter les données
            for idx, row in df.iterrows():
                tree.insert("", "end", values=list(row))

    def get_selected_values(self, listbox):
        return [listbox.get(i) for i in listbox.curselection()]

    def filter_df(self, df):
        for col, lb in [("Type", self.type_filter), ("Label", self.label_filter),
                        ("Sent Currency", self.send_currency_filter),
                        ("Received Currency", self.received_currency_filter)]:
            selected = self.get_selected_values(lb)
            if selected:
                df = df[df[col].isin(selected)]
        return df

    def populate_filters(self):
        all_values = {"Type": set(), "Label": set(), "Sent Currency": set(), "Received Currency": set()}
        for df in self.dataframes.values():
            for col in all_values:
                if col in df.columns:
                    all_values[col].update(df[col].dropna().unique())

        for lb, col in [(self.type_filter, "Type"), (self.label_filter, "Label"),
                        (self.send_currency_filter, "Sent Currency"),
                        (self.received_currency_filter, "Received Currency")]:
            lb.delete(0, tk.END)
            for val in sorted(all_values[col]):
                lb.insert(tk.END, val)

    def update_summary(self):
        total_fee = 0
        total_sent = 0
        total_received = 0

        for df in self.dataframes.values():
            df_filtered = self.filter_df(df)
            for col, acc in [("Fee Amount", total_fee), ("Sent Amount", total_sent), ("Received Amount", total_received)]:
                if col in df_filtered.columns:
                    try:
                        val = pd.to_numeric(df_filtered[col], errors='coerce').sum()
                        if col == "Fee Amount":
                            total_fee += val
                        elif col == "Sent Amount":
                            total_sent += val
                        elif col == "Received Amount":
                            total_received += val
                    except Exception:
                        pass

        self.summary.delete("1.0", tk.END)
        self.summary.insert(tk.END, f"Total Fee Amount : {total_fee:.2f}\n")
        self.summary.insert(tk.END, f"Total Sent Amount : {total_sent:.2f}\n")
        self.summary.insert(tk.END, f"Total Received Amount : {total_received:.2f}\n")

    def reset_filters(self):
        """Réinitialise tous les filtres en désélectionnant toutes les options"""
        for lb in [self.type_filter, self.label_filter, self.send_currency_filter, self.received_currency_filter]:
            lb.selection_clear(0, tk.END)
        self.update_summary()

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
            for df in self.dataframes.values():
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

    def validate_transaction_uniqueness(self):
        """Vérifie l'unicité des transactions dans les données filtrées"""
        if not self.dataframes:
            messagebox.showwarning("Validation", "Aucune donnée à valider. Veuillez d'abord charger des fichiers CSV.")
            return

        try:
            # Concaténer tous les dataframes filtrés
            filtered_dfs = []
            for df in self.dataframes.values():
                df_filtered = self.filter_df(df)
                if not df_filtered.empty:
                    filtered_dfs.append(df_filtered)

            if not filtered_dfs:
                messagebox.showwarning("Validation", "Aucune donnée ne correspond aux filtres actuels.")
                return

            # Concaténer tous les dataframes
            final_df = pd.concat(filtered_dfs, ignore_index=True)
            
            # Créer une nouvelle fenêtre pour afficher les résultats
            result_window = tk.Toplevel(self.root)
            result_window.title("Validation des transactions")
            result_window.geometry("800x600")
            
            # Frame principal avec padding
            main_frame = ttk.Frame(result_window, padding="10")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Zone de texte pour les résultats
            result_text = tk.Text(main_frame, wrap=tk.WORD)
            result_text.pack(fill=tk.BOTH, expand=True)
            
            # Scrollbar pour la zone de texte
            scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=result_text.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            result_text.configure(yscrollcommand=scrollbar.set)
            
            # Vérifier les colonnes d'ID possibles
            id_columns = ['Transaction ID', 'ID', 'TransactionID', 'txid', 'TxID']
            found_id_column = None
            
            for col in id_columns:
                if col in final_df.columns:
                    found_id_column = col
                    break
            
            if not found_id_column:
                result_text.insert(tk.END, "❌ Aucune colonne d'ID trouvée dans les données.\n")
                result_text.insert(tk.END, "Colonnes disponibles :\n")
                for col in final_df.columns:
                    result_text.insert(tk.END, f"- {col}\n")
                return
            
            # Vérifier les doublons
            duplicates = final_df[final_df.duplicated(subset=[found_id_column], keep=False)]
            
            if duplicates.empty:
                result_text.insert(tk.END, "✅ Toutes les transactions sont uniques !\n\n")
                result_text.insert(tk.END, f"Nombre total de transactions : {len(final_df)}\n")
            else:
                result_text.insert(tk.END, "⚠️ Des transactions en double ont été trouvées !\n\n")
                result_text.insert(tk.END, f"Nombre total de transactions : {len(final_df)}\n")
                result_text.insert(tk.END, f"Nombre de transactions en double : {len(duplicates)}\n\n")
                
                # Grouper les doublons par ID
                grouped_duplicates = duplicates.groupby(found_id_column)
                
                result_text.insert(tk.END, "Détail des doublons :\n")
                result_text.insert(tk.END, "-" * 50 + "\n")
                
                for tx_id, group in grouped_duplicates:
                    result_text.insert(tk.END, f"\nID : {tx_id}\n")
                    result_text.insert(tk.END, f"Nombre d'occurrences : {len(group)}\n")
                    result_text.insert(tk.END, "Détails :\n")
                    
                    # Afficher les détails pertinents pour chaque doublon
                    for idx, row in group.iterrows():
                        result_text.insert(tk.END, f"\n  - Date : {row.get('Date', 'N/A')}\n")
                        result_text.insert(tk.END, f"    Type : {row.get('Type', 'N/A')}\n")
                        result_text.insert(tk.END, f"    Montant : {row.get('Amount', 'N/A')}\n")
                        result_text.insert(tk.END, f"    Devise : {row.get('Currency', 'N/A')}\n")
                    
                    result_text.insert(tk.END, "-" * 50 + "\n")
            
            # Rendre la zone de texte en lecture seule
            result_text.configure(state='disabled')
            
        except Exception as e:
            messagebox.showerror("Erreur de validation", f"Une erreur est survenue lors de la validation :\n{str(e)}")

    def change_directory(self, event=None):
        """Change le répertoire courant"""
        new_path = self.path_var.get()
        if os.path.isdir(new_path):
            self.current_directory = new_path
        else:
            messagebox.showerror("Erreur", "Chemin invalide")

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

    def on_file_double_click(self, event):
        """Gère le double-clic sur un élément de l'arborescence"""
        item = self.tree.selection()[0]
        text = self.tree.item(item)["text"]
        
        if text == "..":
            self.current_directory = str(Path(self.current_directory).parent)
        elif self.tree.item(item)["tags"][0] == "folder":
            self.current_directory = str(Path(self.current_directory) / text)
        elif self.tree.item(item)["tags"][0] == "file":
            filepath = str(Path(self.current_directory) / text)
            self.load_single_file(filepath)
            return
        
        self.path_var.set(self.current_directory)
        self.populate_tree()

    def populate_tree(self):
        """Remplit l'arborescence avec les fichiers du répertoire courant"""
        self.tree.delete(*self.tree.get_children())
        path = Path(self.current_directory)
        
        # Ajouter le dossier parent
        if path.parent != path:
            self.tree.insert("", "end", text="..", values=("", "Dossier"), tags=("parent",))
        
        # Ajouter les dossiers et fichiers
        for item in path.iterdir():
            if item.is_dir():
                self.tree.insert("", "end", text=item.name, values=("", "Dossier"), tags=("folder",))
            elif item.suffix.lower() == '.csv':
                size = f"{item.stat().st_size / 1024:.1f} KB"
                self.tree.insert("", "end", text=item.name, values=(size, "CSV"), tags=("file",))

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

    def get_active_dataframes(self):
        """Retourne uniquement les dataframes des fichiers sélectionnés"""
        active_dfs = {}
        for filename, var in self.file_checkboxes.items():
            if var.get() and filename in self.dataframes:
                active_dfs[filename] = self.dataframes[filename]
        return active_dfs

    def calculate_eur_totals(self):
        """Calcule les totaux des transactions en EUR"""
        if not self.dataframes:
            messagebox.showwarning("Calcul EUR", "Aucune donnée à analyser. Veuillez d'abord charger des fichiers CSV.")
            return

        try:
            # Concaténer uniquement les dataframes actifs
            all_data = pd.concat(self.get_active_dataframes().values(), ignore_index=True)
            
            # Convertir les colonnes numériques en float
            numeric_columns = ['Sent Amount', 'Received Amount']
            for col in numeric_columns:
                if col in all_data.columns:
                    all_data[col] = pd.to_numeric(all_data[col], errors='coerce').fillna(0)
            
            # Convertir la colonne Date en datetime si elle existe
            if 'Date' in all_data.columns:
                all_data['Date'] = pd.to_datetime(all_data['Date'], errors='coerce')
                all_data['Year'] = all_data['Date'].dt.year

            # Calculer les totaux globaux
            buy_mask = (all_data['Type'] == 'Buy') & (all_data['Sent Currency'] == 'EUR')
            deposit_mask = (all_data['Type'] == 'Deposit') & (all_data['Received Currency'] == 'EUR')
            sell_mask = (all_data['Type'] == 'Sell') & (all_data['Received Currency'] == 'EUR')

            all_EUR_sent = all_data.loc[buy_mask, 'Sent Amount'].sum()
            all_EUR_deposit = all_data.loc[deposit_mask, 'Received Amount'].sum()
            all_EUR_Sell = all_data.loc[sell_mask, 'Received Amount'].sum()
            all_EUR_to_binance = all_EUR_sent + all_EUR_deposit
            all_EUR_to_binance_REAL = all_EUR_sent + all_EUR_deposit - all_EUR_Sell

            # Afficher les résultats dans le résumé
            self.summary.delete("1.0", tk.END)
            self.summary.insert(tk.END, "=== EUR Spending Analysis ===\n\n")
            self.summary.insert(tk.END, f"EUR spent on Buy orders: {all_EUR_sent:.2f} EUR\n")
            self.summary.insert(tk.END, f"EUR received from Deposits: {all_EUR_deposit:.2f} EUR\n")
            self.summary.insert(tk.END, f"EUR received from Sells: {all_EUR_Sell:.2f} EUR\n")
            self.summary.insert(tk.END, f"Total EUR to Binance: {all_EUR_to_binance:.2f} EUR\n")
            self.summary.insert(tk.END, f"Real EUR to Binance (minus sells): {all_EUR_to_binance_REAL:.2f} EUR\n\n")

            # Calculer et afficher les totaux par année
            if 'Year' in all_data.columns:
                self.summary.insert(tk.END, "=== Yearly Analysis ===\n\n")
                for year in sorted(all_data['Year'].unique()):
                    if pd.isna(year):
                        continue
                    
                    year_data = all_data[all_data['Year'] == year]
                    
                    year_buy = year_data.loc[buy_mask, 'Sent Amount'].sum()
                    year_deposit = year_data.loc[deposit_mask, 'Received Amount'].sum()
                    year_sell = year_data.loc[sell_mask, 'Received Amount'].sum()
                    year_total = year_buy + year_deposit
                    year_real = year_buy + year_deposit - year_sell

                    self.summary.insert(tk.END, f"=== {int(year)} ===\n")
                    self.summary.insert(tk.END, f"EUR spent on Buy orders: {year_buy:.2f} EUR\n")
                    self.summary.insert(tk.END, f"EUR received from Deposits: {year_deposit:.2f} EUR\n")
                    self.summary.insert(tk.END, f"EUR received from Sells: {year_sell:.2f} EUR\n")
                    self.summary.insert(tk.END, f"Total EUR to Binance: {year_total:.2f} EUR\n")
                    self.summary.insert(tk.END, f"Real EUR to Binance (minus sells): {year_real:.2f} EUR\n\n")

        except Exception as e:
            messagebox.showerror("Erreur de calcul", f"Une erreur est survenue lors du calcul des totaux EUR :\n{str(e)}")

    def export_eur_transactions(self):
        """Exporte les transactions EUR vers un fichier CSV"""
        if not self.dataframes:
            messagebox.showwarning("Export EUR", "Aucune donnée à exporter. Veuillez d'abord charger des fichiers CSV.")
            return

        try:
            # Concaténer tous les dataframes
            all_data = pd.concat(self.dataframes.values(), ignore_index=True)
            
            # Filtrer les transactions EUR
            eur_mask = (
                ((all_data['Type'] == 'Buy') & (all_data['Sent Currency'] == 'EUR')) |
                ((all_data['Type'] == 'Deposit') & (all_data['Received Currency'] == 'EUR')) |
                ((all_data['Type'] == 'Sell') & (all_data['Received Currency'] == 'EUR'))
            )
            eur_transactions = all_data[eur_mask]

            if eur_transactions.empty:
                messagebox.showwarning("Export EUR", "Aucune transaction EUR trouvée.")
                return

            # Demander où sauvegarder le fichier
            filepath = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                title="Exporter les transactions EUR"
            )
            
            if not filepath:  # L'utilisateur a annulé
                return

            # Exporter vers CSV
            eur_transactions.to_csv(filepath, index=False)
            messagebox.showinfo("Export EUR", f"Transactions EUR exportées avec succès vers :\n{filepath}")
            
        except Exception as e:
            messagebox.showerror("Erreur d'export", f"Une erreur est survenue lors de l'export des transactions EUR :\n{str(e)}")

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

if __name__ == "__main__":
    root = tk.Tk()
    app = CryptoBinanceViewer(root)
    root.mainloop()