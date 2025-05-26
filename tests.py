import unittest
import pandas as pd
import tkinter as tk
from pathlib import Path
import tempfile
import os
import shutil
from transactions import TransactionsViewer
from income_gains import IncomeGainsViewer
from realized_gains import RealizedGainsViewer

class TestBase(unittest.TestCase):
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.root = tk.Tk()
        self.summary = tk.Text(self.root)
        self.temp_dir = tempfile.mkdtemp()
        
        # Créer des fichiers CSV de test
        self.create_test_files()
        
    def tearDown(self):
        """Nettoyage après chaque test"""
        self.root.destroy()
        shutil.rmtree(self.temp_dir)
        
    def create_test_files(self):
        """Crée des fichiers CSV de test"""
        # Transactions test data
        transactions_data = {
            'Date': ['2023-01-01', '2023-01-02', '2023-01-03'],
            'Type': ['Buy', 'Sell', 'Receive'],
            'Label': ['Trade', 'Trade', 'Reward'],
            'Sent Currency': ['EUR', 'BTC', ''],
            'Received Currency': ['BTC', 'EUR', 'ETH'],
            'Sent Amount': [1000.0, 0.1, 0.0],
            'Received Amount': [0.05, 500.0, 1.0],
            'Fee Amount': [10.0, 5.0, 0.0],
            'Transaction ID': ['TX1', 'TX2', 'TX3']
        }
        pd.DataFrame(transactions_data).to_csv(
            os.path.join(self.temp_dir, 'transactions.csv'), index=False
        )
        
        # Income gains test data
        income_data = {
            'Date': ['2023-01-01', '2023-01-02'],
            'Asset': ['ETH', 'BTC'],
            'Transaction Type': ['Staking', 'Interest'],
            'Label': ['Reward', 'Reward'],
            'Amount': [1.0, 0.1],
            'Value (EUR)': [2000.0, 3000.0],
            'Taxable': ['Yes', 'Yes']
        }
        pd.DataFrame(income_data).to_csv(
            os.path.join(self.temp_dir, 'income.csv'), index=False
        )
        
        # Realized gains test data
        realized_data = {
            'Currency name': ['BTC', 'ETH'],
            'Currency amount': [0.1, 1.0],
            'Acquired': ['2023-01-01', '2023-01-02'],
            'Sold': ['2023-01-03', '2023-01-04'],
            'Proceeds (EUR)': [5000.0, 2000.0],
            'Cost basis (EUR)': [4000.0, 1500.0],
            'Gains (EUR)': [1000.0, 500.0],
            'Holding period (Days)': [2, 2],
            'Transaction type': ['Trade', 'Trade'],
            'Label': ['Realized', 'Realized']
        }
        pd.DataFrame(realized_data).to_csv(
            os.path.join(self.temp_dir, 'realized.csv'), index=False
        )

class TestTransactionsViewer(TestBase):
    def setUp(self):
        super().setUp()
        self.viewer = TransactionsViewer(self.root, self.summary)
        
    def test_load_csv(self):
        """Test le chargement des fichiers CSV"""
        self.viewer.current_directory = self.temp_dir
        self.viewer.load_csv()
        self.assertGreater(len(self.viewer.dataframes), 0)
        
    def test_filter_df(self):
        """Test le filtrage des données"""
        # Charger les données
        self.viewer.current_directory = self.temp_dir
        self.viewer.load_csv()
        
        # Sélectionner un type
        self.viewer.type_filter.selection_set(0)  # Sélectionne 'Buy'
        
        # Appliquer le filtre
        df = self.viewer.filter_df(list(self.viewer.dataframes.values())[0])
        self.assertEqual(len(df), 1)  # Devrait ne garder que la transaction 'Buy'
        
    def test_calculate_eur_totals(self):
        """Test le calcul des totaux EUR"""
        self.viewer.current_directory = self.temp_dir
        self.viewer.load_csv()
        self.viewer.calculate_eur_totals()
        
        # Vérifier que le résumé contient les informations attendues
        summary_text = self.summary.get("1.0", tk.END)
        self.assertIn("EUR Spending Analysis", summary_text)
        self.assertIn("EUR spent on Buy orders", summary_text)

class TestIncomeGainsViewer(TestBase):
    def setUp(self):
        super().setUp()
        self.viewer = IncomeGainsViewer(self.root, self.summary)
        
    def test_load_csv(self):
        """Test le chargement des fichiers CSV"""
        self.viewer.current_directory = self.temp_dir
        self.viewer.load_csv()
        self.assertGreater(len(self.viewer.dataframes), 0)
        
    def test_calculate_income_gains(self):
        """Test le calcul des gains de revenus"""
        self.viewer.current_directory = self.temp_dir
        self.viewer.load_csv()
        self.viewer.calculate_income_gains()
        
        # Vérifier que le résumé contient les informations attendues
        summary_text = self.summary.get("1.0", tk.END)
        self.assertIn("Gains Globaux", summary_text)
        self.assertIn("ETH", summary_text)
        self.assertIn("BTC", summary_text)

class TestRealizedGainsViewer(TestBase):
    def setUp(self):
        super().setUp()
        self.viewer = RealizedGainsViewer(self.root, self.summary)
        
    def test_load_csv(self):
        """Test le chargement des fichiers CSV"""
        self.viewer.current_directory = self.temp_dir
        self.viewer.load_csv()
        self.assertGreater(len(self.viewer.dataframes), 0)
        
    def test_calculate_realized_gains(self):
        """Test le calcul des gains réalisés"""
        self.viewer.current_directory = self.temp_dir
        self.viewer.load_csv()
        self.viewer.calculate_realized_gains()
        
        # Vérifier que le résumé contient les informations attendues
        summary_text = self.summary.get("1.0", tk.END)
        self.assertIn("Gains Réalisés Globaux", summary_text)
        self.assertIn("BTC", summary_text)
        self.assertIn("ETH", summary_text)

    def test_realized_gains_by_year_and_currency(self):
        """Vérifie que les totaux globaux et par année/crypto sont corrects (année basée sur 'Sold')"""
        self.viewer.current_directory = self.temp_dir
        self.viewer.load_csv()
        self.viewer.calculate_realized_gains()

        # Charger le CSV de test manuellement
        df = pd.read_csv(os.path.join(self.temp_dir, 'realized.csv'))
        df['Sold'] = pd.to_datetime(df['Sold'], errors='coerce')
        df['Year'] = df['Sold'].dt.year

        # Totaux globaux attendus
        expected_proceeds = df['Proceeds (EUR)'].sum()
        expected_cost_basis = df['Cost basis (EUR)'].sum()
        expected_gains = df['Gains (EUR)'].sum()

        # Vérifier que le résumé contient les bons totaux globaux
        summary_text = self.summary.get("1.0", tk.END)
        self.assertIn(f"Total Proceeds: {expected_proceeds:.2f} EUR", summary_text)
        self.assertIn(f"Total Cost Basis: {expected_cost_basis:.2f} EUR", summary_text)
        self.assertIn(f"Total Gains: {expected_gains:.2f} EUR", summary_text)

        # Vérifier les totaux par année et par crypto
        for year in sorted(df['Year'].dropna().unique()):
            year_data = df[df['Year'] == year]
            year_proceeds = year_data['Proceeds (EUR)'].sum()
            year_cost_basis = year_data['Cost basis (EUR)'].sum()
            year_gains = year_data['Gains (EUR)'].sum()
            self.assertIn(f"=== {int(year)} ===", summary_text)
            self.assertIn(f"Totaux {int(year)}:", summary_text)
            self.assertIn(f"  Proceeds: {year_proceeds:.2f} EUR", summary_text)
            self.assertIn(f"  Cost Basis: {year_cost_basis:.2f} EUR", summary_text)
            self.assertIn(f"  Gains: {year_gains:.2f} EUR", summary_text)
            # Par crypto
            for currency in year_data['Currency name'].unique():
                cur_data = year_data[year_data['Currency name'] == currency]
                cur_proceeds = cur_data['Proceeds (EUR)'].sum()
                cur_cost_basis = cur_data['Cost basis (EUR)'].sum()
                cur_gains = cur_data['Gains (EUR)'].sum()
                self.assertIn(f"{currency}:", summary_text)
                self.assertIn(f"  Proceeds: {cur_proceeds:.2f} EUR", summary_text)
                self.assertIn(f"  Cost Basis: {cur_cost_basis:.2f} EUR", summary_text)
                self.assertIn(f"  Gains: {cur_gains:.2f} EUR", summary_text)

class TestExportFunctionality(TestBase):
    def setUp(self):
        super().setUp()
        self.transactions_viewer = TransactionsViewer(self.root, self.summary)
        self.income_viewer = IncomeGainsViewer(self.root, self.summary)
        self.realized_viewer = RealizedGainsViewer(self.root, self.summary)
        
    def test_export_transactions(self):
        """Test l'export des transactions"""
        self.transactions_viewer.current_directory = self.temp_dir
        self.transactions_viewer.load_csv()
        
        # Créer un fichier temporaire pour l'export
        export_path = os.path.join(self.temp_dir, 'export_transactions.csv')
        self.transactions_viewer.export_filtered_data()
        
        # Vérifier que le fichier a été créé
        self.assertTrue(os.path.exists(export_path))
        
    def test_export_income_gains(self):
        """Test l'export des gains de revenus"""
        self.income_viewer.current_directory = self.temp_dir
        self.income_viewer.load_csv()
        
        # Créer un fichier temporaire pour l'export
        export_path = os.path.join(self.temp_dir, 'export_income.csv')
        self.income_viewer.export_income_gains()
        
        # Vérifier que le fichier a été créé
        self.assertTrue(os.path.exists(export_path))
        
    def test_export_realized_gains(self):
        """Test l'export des gains réalisés"""
        self.realized_viewer.current_directory = self.temp_dir
        self.realized_viewer.load_csv()
        
        # Créer un fichier temporaire pour l'export
        export_path = os.path.join(self.temp_dir, 'export_realized.csv')
        self.realized_viewer.export_realized_gains()
        
        # Vérifier que le fichier a été créé
        self.assertTrue(os.path.exists(export_path))

if __name__ == '__main__':
    unittest.main() 