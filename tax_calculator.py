import tkinter as tk
from tkinter import ttk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from datetime import datetime

class TaxCalculatorWindow(tk.Toplevel):
    def __init__(self, parent, df):
        super().__init__(parent)
        self.title("Tax Calculator - Portfolio Analysis")
        self.geometry("1200x800")
        self.df = df.copy()
        self.selected_currencies = []
        self._prepare_data()
        self._setup_ui()
        self._calculate_tax()
        self._draw_graph()

    def _prepare_data(self):
        # Nettoyage et préparation des données
        if 'Date' not in self.df.columns:
            raise ValueError("Le fichier doit contenir la colonne 'Date'")
        
        # Convertir les dates et trier chronologiquement
        self.df['Date'] = pd.to_datetime(self.df['Date'], errors='coerce')
        self.df = self.df.dropna(subset=['Date'])
        self.df = self.df.sort_values('Date')
        
        # Extraire l'année pour le regroupement fiscal
        self.df['Year'] = self.df['Date'].dt.year
        
        # Séparer les transactions EUR des transactions crypto
        self.eur_transactions = self.df[
            ((self.df['Type'] == 'Deposit') & (self.df['Received Currency'] == 'EUR')) |
            ((self.df['Type'] == 'Buy') & (self.df['Sent Currency'] == 'EUR')) |
            ((self.df['Type'] == 'Sell') & (self.df['Received Currency'] == 'EUR'))
        ].copy()

        # Filtrer les transactions crypto (exclure EUR)
        self.crypto_df = self.df[
            ~(((self.df['Type'] == 'Deposit') & (self.df['Received Currency'] == 'EUR')) |
              ((self.df['Type'] == 'Buy') & (self.df['Sent Currency'] == 'EUR')) |
              ((self.df['Type'] == 'Sell') & (self.df['Received Currency'] == 'EUR')))
        ].copy()
        
        # Identifier les actifs crypto uniques (exclure EUR)
        self.currencies = sorted(set(
            self.crypto_df['Sent Currency'].dropna().unique().tolist() +
            self.crypto_df['Received Currency'].dropna().unique().tolist()
        ) - {'EUR'})

    def _setup_ui(self):
        # Frame principal avec panneau divisé
        main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True)

        # Panneau de gauche (contrôles et rapports)
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)

        # Panneau de droite (graphiques)
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=2)

        # Contrôles dans le panneau de gauche
        controls_frame = ttk.LabelFrame(left_frame, text="Contrôles", padding="5")
        controls_frame.pack(fill=tk.X, pady=5)

        # Filtres
        filter_frame = ttk.LabelFrame(controls_frame, text="Filtres", padding="5")
        filter_frame.pack(fill=tk.X, pady=5)

        # Filtre par année
        year_frame = ttk.Frame(filter_frame)
        year_frame.pack(fill=tk.X, pady=2)
        ttk.Label(year_frame, text="Année:").pack(side=tk.LEFT)
        self.year_var = tk.StringVar(value="Toutes")
        self.year_combo = ttk.Combobox(year_frame, textvariable=self.year_var, state="readonly")
        self.year_combo['values'] = ["Toutes"] + sorted(self.df['Year'].unique().tolist())
        self.year_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.year_combo.bind('<<ComboboxSelected>>', lambda e: self._update_display())

        # Filtre par devise
        currency_frame = ttk.Frame(filter_frame)
        currency_frame.pack(fill=tk.X, pady=2)
        ttk.Label(currency_frame, text="Devise:").pack(side=tk.LEFT)
        self.currency_var = tk.StringVar(value="Toutes")
        self.currency_combo = ttk.Combobox(currency_frame, textvariable=self.currency_var, state="readonly")
        self.currency_combo['values'] = ["Toutes"] + self.currencies
        self.currency_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.currency_combo.bind('<<ComboboxSelected>>', lambda e: self._update_display())

        # Rapport fiscal
        report_frame = ttk.LabelFrame(left_frame, text="Rapport Fiscal", padding="5")
        report_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Zone de texte pour le rapport avec scrollbar
        self.report_text = tk.Text(report_frame, wrap=tk.WORD, height=20)
        scrollbar = ttk.Scrollbar(report_frame, orient="vertical", command=self.report_text.yview)
        self.report_text.configure(yscrollcommand=scrollbar.set)
        self.report_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Graphiques dans le panneau de droite
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(8, 10))
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _calculate_tax(self):
        """Calcule les plus-values et moins-values selon la méthode du PMP"""
        self.portfolio_history = {}
        self.tax_summary = {}
        self.eur_summary = {}
        self.eur_curve = []  # Pour la courbe EUR

        # Initialiser l'historique pour chaque devise crypto
        for currency in self.currencies:
            self.portfolio_history[currency] = {
                'stock': 0,
                'cost': 0,
                'pmp': 0,
                'transactions': []
            }

        # Pour la courbe EUR : cumul dépenses et gains
        eur_dates = []
        eur_deposits = []
        eur_gains = []
        cum_deposit = 0
        cum_gain = 0

        # Traiter les transactions EUR séparément
        for _, row in self.eur_transactions.iterrows():
            date = row['Date']
            year = date.year

            if year not in self.eur_summary:
                self.eur_summary[year] = {
                    'deposits': 0,
                    'withdrawals': 0,
                    'buys': 0,
                    'sells': 0
                }

            year_summary = self.eur_summary[year]

            if row['Type'] == 'Deposit':
                year_summary['deposits'] += float(row['Received Amount'])
                cum_deposit += float(row['Received Amount'])
                eur_dates.append(date)
                eur_deposits.append(cum_deposit)
                eur_gains.append(cum_gain)
            elif row['Type'] == 'Buy':
                year_summary['buys'] += float(row['Sent Amount'])
                cum_deposit += float(row['Sent Amount'])
                eur_dates.append(date)
                eur_deposits.append(cum_deposit)
                eur_gains.append(cum_gain)
            elif row['Type'] == 'Sell':
                year_summary['sells'] += float(row['Received Amount'])
                cum_gain += float(row['Received Amount'])
                eur_dates.append(date)
                eur_deposits.append(cum_deposit)
                eur_gains.append(cum_gain)

        self.eur_curve = (eur_dates, eur_deposits, eur_gains)

        # Traiter chaque transaction crypto chronologiquement
        for _, row in self.crypto_df.iterrows():
            date = row['Date']
            year = date.year

            # Traiter les sorties (ventes/échanges)
            if pd.notna(row.get('Sent Currency')) and pd.notna(row.get('Sent Amount')):
                currency = row['Sent Currency']
                if currency == 'EUR':
                    continue  # Ignorer les transactions EUR

                amount = float(row['Sent Amount'])
                fees = float(row.get('Fee Amount', 0))

                # Correction : si vente contre EUR, utiliser Received Amount comme prix de vente
                if row.get('Type') == 'Sell' and row.get('Received Currency') == 'EUR' and pd.notna(row.get('Received Amount')):
                    price = float(row['Received Amount']) / amount if amount != 0 else 0
                else:
                    price = float(row.get('Sent Price', 0))

                if currency in self.portfolio_history:
                    history = self.portfolio_history[currency]
                    if history['stock'] > 0:
                        # Calculer la plus/moins-value
                        pv = (price - history['pmp']) * amount - fees
                        
                        # Mettre à jour le stock et le coût
                        history['stock'] -= amount
                        history['cost'] -= (history['pmp'] * amount)
                        
                        # Enregistrer la transaction
                        transaction = {
                            'date': date,
                            'type': 'Sell',
                            'amount': amount,
                            'price': price,
                            'fees': fees,
                            'pmp': history['pmp'],
                            'pv': pv
                        }
                        history['transactions'].append(transaction)

                        # Mettre à jour le résumé fiscal
                        if year not in self.tax_summary:
                            self.tax_summary[year] = {
                                'total_pv': 0,
                                'total_mv': 0,
                                'total_fees': 0,
                                'currencies': {}
                            }
                        
                        year_summary = self.tax_summary[year]
                        if pv > 0:
                            year_summary['total_pv'] += pv
                        else:
                            year_summary['total_mv'] += abs(pv)
                        year_summary['total_fees'] += fees

                        if currency not in year_summary['currencies']:
                            year_summary['currencies'][currency] = {
                                'pv': 0,
                                'mv': 0,
                                'fees': 0,
                                'transactions': []
                            }
                        
                        currency_summary = year_summary['currencies'][currency]
                        if pv > 0:
                            currency_summary['pv'] += pv
                        else:
                            currency_summary['mv'] += abs(pv)
                        currency_summary['fees'] += fees
                        currency_summary['transactions'].append(transaction)

            # Traiter les entrées (achats/échanges)
            if pd.notna(row.get('Received Currency')) and pd.notna(row.get('Received Amount')):
                currency = row['Received Currency']
                if currency == 'EUR':
                    continue  # Ignorer les transactions EUR

                amount = float(row['Received Amount'])
                fees = float(row.get('Fee Amount', 0))

                # Correction : si achat contre EUR, utiliser Sent Amount comme prix d'achat
                if row.get('Type') == 'Buy' and row.get('Sent Currency') == 'EUR' and pd.notna(row.get('Sent Amount')):
                    price = float(row['Sent Amount']) / amount if amount != 0 else 0
                else:
                    price = float(row.get('Received Price', 0))

                if currency in self.portfolio_history:
                    history = self.portfolio_history[currency]
                    
                    # Mettre à jour le stock et le coût
                    new_stock = history['stock'] + amount
                    new_cost = history['cost'] + (amount * price) + fees
                    
                    # Calculer le nouveau PMP
                    if new_stock > 0:
                        new_pmp = new_cost / new_stock
                    else:
                        new_pmp = 0

                    history['stock'] = new_stock
                    history['cost'] = new_cost
                    history['pmp'] = new_pmp

                    # Enregistrer la transaction
                    transaction = {
                        'date': date,
                        'type': 'Buy',
                        'amount': amount,
                        'price': price,
                        'fees': fees,
                        'pmp': new_pmp
                    }
                    history['transactions'].append(transaction)

    def _update_display(self):
        """Met à jour l'affichage en fonction des filtres sélectionnés"""
        self._update_report()
        self._draw_graph()

    def _update_report(self):
        """Met à jour le rapport fiscal"""
        self.report_text.delete("1.0", tk.END)
        
        # Filtrer les données selon les sélections
        selected_year = self.year_var.get()
        selected_currency = self.currency_var.get()

        # Afficher le résumé des transactions EUR
        self.report_text.insert(tk.END, "=== Résumé des Transactions EUR ===\n\n")
        
        for year, summary in sorted(self.eur_summary.items()):
            if selected_year != "Toutes" and str(year) != selected_year:
                continue

            self.report_text.insert(tk.END, f"\n=== Année {year} ===\n")
            self.report_text.insert(tk.END, f"  Dépôts: {summary['deposits']:.2f} EUR\n")
            self.report_text.insert(tk.END, f"  Achats: {summary['buys']:.2f} EUR\n")
            self.report_text.insert(tk.END, f"  Ventes: {summary['sells']:.2f} EUR\n")
            self.report_text.insert(tk.END, f"  Net: {summary['deposits'] + summary['sells'] - summary['buys']:.2f} EUR\n")

        # Afficher le résumé fiscal des cryptomonnaies
        self.report_text.insert(tk.END, "\n=== Résumé Fiscal des Cryptomonnaies ===\n\n")
        
        total_pv = 0
        total_mv = 0
        total_fees = 0

        for year, summary in sorted(self.tax_summary.items()):
            if selected_year != "Toutes" and str(year) != selected_year:
                continue

            self.report_text.insert(tk.END, f"\n=== Année {year} ===\n")
            
            for currency, currency_summary in summary['currencies'].items():
                if selected_currency != "Toutes" and currency != selected_currency:
                    continue

                self.report_text.insert(tk.END, f"\n{currency}:\n")
                self.report_text.insert(tk.END, f"  Plus-values: {currency_summary['pv']:.2f} EUR\n")
                self.report_text.insert(tk.END, f"  Moins-values: {currency_summary['mv']:.2f} EUR\n")
                self.report_text.insert(tk.END, f"  Frais: {currency_summary['fees']:.2f} EUR\n")
                
                net = currency_summary['pv'] - currency_summary['mv']
                self.report_text.insert(tk.END, f"  Net imposable: {net:.2f} EUR\n")

                # Afficher les détails des transactions
                self.report_text.insert(tk.END, "\n  Détail des transactions:\n")
                for tx in currency_summary['transactions']:
                    self.report_text.insert(tk.END, f"    {tx['date'].strftime('%Y-%m-%d %H:%M:%S')} - ")
                    self.report_text.insert(tk.END, f"{tx['type']} {tx['amount']:.8f} @ {tx['price']:.2f} EUR")
                    if 'pv' in tx:
                        self.report_text.insert(tk.END, f" (PV: {tx['pv']:.2f} EUR)")
                    self.report_text.insert(tk.END, f" [PMP: {tx['pmp']:.2f} EUR]\n")

            year_total = summary['total_pv'] - summary['total_mv']
            self.report_text.insert(tk.END, f"\nTotal {year}:\n")
            self.report_text.insert(tk.END, f"  Plus-values: {summary['total_pv']:.2f} EUR\n")
            self.report_text.insert(tk.END, f"  Moins-values: {summary['total_mv']:.2f} EUR\n")
            self.report_text.insert(tk.END, f"  Frais: {summary['total_fees']:.2f} EUR\n")
            self.report_text.insert(tk.END, f"  Net imposable: {year_total:.2f} EUR\n")

            total_pv += summary['total_pv']
            total_mv += summary['total_mv']
            total_fees += summary['total_fees']

        # Afficher le total global
        self.report_text.insert(tk.END, "\n=== Total Global ===\n")
        self.report_text.insert(tk.END, f"Plus-values totales: {total_pv:.2f} EUR\n")
        self.report_text.insert(tk.END, f"Moins-values totales: {total_mv:.2f} EUR\n")
        self.report_text.insert(tk.END, f"Frais totaux: {total_fees:.2f} EUR\n")
        self.report_text.insert(tk.END, f"Net imposable global: {total_pv - total_mv:.2f} EUR\n")

    def _draw_graph(self):
        """Dessine les graphiques d'évolution du portefeuille"""
        self.ax1.clear()
        self.ax2.clear()

        # Filtrer les données selon les sélections
        selected_year = self.year_var.get()
        selected_currency = self.currency_var.get()

        # Graphique 1: Évolution du stock par devise
        for currency, history in self.portfolio_history.items():
            if selected_currency != "Toutes" and currency != selected_currency:
                continue

            dates = []
            stocks = []
            current_stock = 0

            for transaction in history['transactions']:
                if selected_year != "Toutes" and transaction['date'].year != int(selected_year):
                    continue

                dates.append(transaction['date'])
                if transaction['type'] == 'Buy':
                    current_stock += transaction['amount']
                else:
                    current_stock -= transaction['amount']
                stocks.append(current_stock)

            if dates:
                self.ax1.plot(dates, stocks, label=currency)

        self.ax1.set_title("Évolution du stock par devise")
        self.ax1.set_xlabel("Date")
        self.ax1.set_ylabel("Stock")
        self.ax1.legend()
        self.ax1.grid(True)

        # Graphique 2: Évolution des plus/moins-values
        years = []
        pvs = []
        mvs = []

        for year, summary in sorted(self.tax_summary.items()):
            if selected_year != "Toutes" and str(year) != selected_year:
                continue

            years.append(year)
            pvs.append(summary['total_pv'])
            mvs.append(summary['total_mv'])

        if years:
            x = np.arange(len(years))
            width = 0.35

            self.ax2.bar(x - width/2, pvs, width, label='Plus-values')
            self.ax2.bar(x + width/2, mvs, width, label='Moins-values')

            self.ax2.set_title("Évolution des plus/moins-values par année")
            self.ax2.set_xlabel("Année")
            self.ax2.set_ylabel("Montant (EUR)")
            self.ax2.set_xticks(x)
            self.ax2.set_xticklabels(years)
            self.ax2.legend()
            self.ax2.grid(True)

        # Nouveau graphique 3 : Dépenses et gains EUR
        if hasattr(self, 'eur_curve') and self.eur_curve[0]:
            ax3 = self.fig.add_subplot(313)
            ax3.plot(self.eur_curve[0], self.eur_curve[1], label='Dépenses cumulées (EUR)', color='blue')
            ax3.plot(self.eur_curve[0], self.eur_curve[2], label='Gains cumulés (EUR)', color='green')
            ax3.set_title("Dépenses et gains EUR sur la plateforme")
            ax3.set_xlabel("Date")
            ax3.set_ylabel("Montant cumulé (EUR)")
            ax3.legend()
            ax3.grid(True)

        self.fig.tight_layout()
        self.canvas.draw()

def show_tax_calculator(parent, df):
    """Fonction utilitaire pour ouvrir la fenêtre de calcul fiscal"""
    TaxCalculatorWindow(parent, df) 