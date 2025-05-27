import pandas as pd
import requests
import time
from datetime import datetime
import pytz
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar, Treeview, Scrollbar
import matplotlib.pyplot as plt
import threading

BINANCE_API_URL = "https://api.binance.com/api/v3/klines"

# Nouvelle fonction pour obtenir le prix EUR d'une crypto à une date donnée
def get_binance_price(symbol, timestamp_ms):
    params = {
        "symbol": symbol,
        "interval": "1m",
        "startTime": timestamp_ms,
        "limit": 1
    }
    try:
        r = requests.get(BINANCE_API_URL, params=params, timeout=10)
        data = r.json()[0]
        return float(data[4])  # close price
    except Exception as e:
        return None

def enrich_csv_with_eur_prices(filepath, requests_per_minute, progress_callback, log_callback, table_viewer=None, stop_flag=None, refresh_every=200, fast_mode=False):
    base, ext = os.path.splitext(filepath)
    output_path = f"{base}_enriched{ext}"
    delay = 60 / max(1, requests_per_minute)

    df = pd.read_csv(filepath)
    # Trier chronologiquement si la colonne 'Date' existe
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.sort_values('Date').reset_index(drop=True)
    total_rows = len(df)
    # Ajouter les colonnes vides si elles n'existent pas
    for col in ["Sent Price EUR", "Sent Value EUR", "Received Price EUR", "Received Value EUR"]:
        if col not in df.columns:
            df[col] = None
    # Sauvegarder le fichier enrichi initial (avec colonnes vides)
    df.to_csv(output_path, index=False)

    # Cache des prix (clé = (symbol, minute))
    price_cache = {}

    for i, row in df.iterrows():
        if stop_flag and stop_flag['stop']:
            log_callback(f"Traitement interrompu à la ligne {i+1}.")
            break
        date_str = row.get('Date') or row.get('datetime')
        if not date_str:
            continue
        try:
            dt = pd.to_datetime(date_str)
        except:
            dt = datetime.fromisoformat(date_str)
        dt = pytz.timezone('Europe/Paris').localize(dt) if dt.tzinfo is None else dt
        timestamp_ms = int(dt.timestamp() * 1000)
        minute_key = dt.strftime('%Y-%m-%d %H:%M')

        # Sent
        sent_cur = str(row.get('Sent Currency', '')).upper()
        sent_amt = row.get('Sent Amount')
        sent_price_eur = None
        sent_value_eur = None
        sent_api_msg = ''
        if sent_cur and sent_cur != 'EUR' and pd.notna(sent_amt):
            symbol = sent_cur + 'EUR'
            cache_key = (symbol, minute_key)
            if cache_key in price_cache:
                sent_price_eur = price_cache[cache_key]
                sent_api_msg = f"CACHE {symbol}={sent_price_eur}"
            else:
                sent_price_eur = get_binance_price(symbol, timestamp_ms)
                price_cache[cache_key] = sent_price_eur
                if sent_price_eur:
                    sent_api_msg = f"OK {symbol}={sent_price_eur}"
                else:
                    sent_api_msg = f"ERREUR {symbol} (prix non trouvé)"
            if sent_price_eur:
                sent_value_eur = float(sent_amt) * sent_price_eur
        elif sent_cur == 'EUR' and pd.notna(sent_amt):
            sent_price_eur = 1.0
            sent_value_eur = float(sent_amt)
            sent_api_msg = "EUR=1.0"

        # Received
        recv_cur = str(row.get('Received Currency', '')).upper()
        recv_amt = row.get('Received Amount')
        recv_price_eur = None
        recv_value_eur = None
        recv_api_msg = ''
        if recv_cur and recv_cur != 'EUR' and pd.notna(recv_amt):
            symbol = recv_cur + 'EUR'
            cache_key = (symbol, minute_key)
            if cache_key in price_cache:
                recv_price_eur = price_cache[cache_key]
                recv_api_msg = f"CACHE {symbol}={recv_price_eur}"
            else:
                recv_price_eur = get_binance_price(symbol, timestamp_ms)
                price_cache[cache_key] = recv_price_eur
                if recv_price_eur:
                    recv_api_msg = f"OK {symbol}={recv_price_eur}"
                else:
                    recv_api_msg = f"ERREUR {symbol} (prix non trouvé)"
            if recv_price_eur:
                recv_value_eur = float(recv_amt) * recv_price_eur
        elif recv_cur == 'EUR' and pd.notna(recv_amt):
            recv_price_eur = 1.0
            recv_value_eur = float(recv_amt)
            recv_api_msg = "EUR=1.0"

        # Mettre à jour la ligne dans le DataFrame
        df.at[i, 'Sent Price EUR'] = sent_price_eur
        df.at[i, 'Sent Value EUR'] = sent_value_eur
        df.at[i, 'Received Price EUR'] = recv_price_eur
        df.at[i, 'Received Value EUR'] = recv_value_eur

        # Log détaillé
        log_callback(f"Ligne {i+1}/{total_rows} : {date_str} | Sent {sent_cur} {sent_api_msg} | Received {recv_cur} {recv_api_msg}")
        progress_callback(i + 1, total_rows)

        # Mise à jour visuelle de la ligne courante dans le tableau (Treeview)
        if table_viewer is not None and hasattr(table_viewer, 'tree'):
            try:
                # Met à jour la ligne courante dans le Treeview
                iid = table_viewer.tree.get_children()[i]
                values = [df.at[i, col] for col in df.columns]
                table_viewer.tree.item(iid, values=values)
                table_viewer.tree.selection_remove(table_viewer.tree.selection())
                table_viewer.tree.see(iid)
                table_viewer.tree.selection_set(iid)
            except Exception:
                pass
        time.sleep(delay)

    # Sauvegarde finale
    df.to_csv(output_path, index=False)
    if table_viewer is not None and hasattr(table_viewer, 'tree'):
        try:
            table_viewer.df = pd.read_csv(output_path)
            table_viewer.tree.delete(*table_viewer.tree.get_children())
            for _, row2 in table_viewer.df.iterrows():
                values = [row2[col] for col in table_viewer.df.columns]
                table_viewer.tree.insert("", "end", values=values)
        except Exception:
            pass
    if stop_flag and stop_flag['stop']:
        log_callback(f"Traitement interrompu. Le fichier enrichi est à jour jusqu'à la ligne {i+1}.")
    else:
        log_callback(f"Fichier enrichi sauvegardé : {output_path}")
    return df

# Interface graphique adaptée
class App:
    def __init__(self, root):
        self.root = root
        root.title("Enrichir CSV avec prix EUR Binance")

        self.filepath = None
        self.csv_viewer = None
        self.stop_flag = {'stop': False}
        self.thread = None
        self.fast_mode = tk.BooleanVar(value=False)
        self.refresh_every = 200

        tk.Button(root, text="Sélectionner un fichier CSV", command=self.select_file).pack(pady=10)
        self.rate_label = tk.Label(root, text="Requêtes/minute (par défaut 500) :")
        self.rate_label.pack()
        self.rate_entry = tk.Entry(root)
        self.rate_entry.insert(0, "500")
        self.rate_entry.pack(pady=5)
        self.chk_fast = tk.Checkbutton(root, text="Mode rapide (pas de rafraîchissement visuel)", variable=self.fast_mode)
        self.chk_fast.pack(pady=2)
        self.btn_start = tk.Button(root, text="Démarrer l'enrichissement", command=self.run_processing)
        self.btn_start.pack(pady=10)
        tk.Button(root, text="Aperçu CSV", command=self.show_csv_viewer).pack(pady=5)
        self.progress = Progressbar(root, orient="horizontal", mode="determinate", length=300)
        self.progress.pack(pady=10)
        self.progress_label = tk.Label(root, text="")
        self.progress_label.pack()
        self.log = tk.Text(root, height=15, width=80)
        self.log.pack(pady=10)

    def select_file(self):
        self.filepath = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if self.filepath:
            self.log_message(f"Fichier sélectionné : {self.filepath}")

    def update_progress(self, current, total):
        def _update():
            self.progress['maximum'] = total
            self.progress['value'] = current
            self.progress_label.config(text=f"Traitement ligne {current}/{total}...")
        self.root.after(0, _update)

    def log_message(self, message):
        def _log():
            self.log.insert(tk.END, message + "\n")
            self.log.see(tk.END)
        self.root.after(0, _log)

    def show_csv_viewer(self):
        if not self.filepath:
            messagebox.showwarning("Fichier manquant", "Veuillez sélectionner un fichier CSV.")
            return
        if self.csv_viewer is not None and self.csv_viewer.winfo_exists():
            self.csv_viewer.lift()
            return
        self.csv_viewer = CSVTableViewer(self.root, self.filepath, title="Aperçu CSV")

    def run_processing(self):
        if not self.filepath:
            messagebox.showwarning("Fichier manquant", "Veuillez sélectionner un fichier CSV.")
            return
        try:
            rate = int(self.rate_entry.get())
        except ValueError:
            messagebox.showwarning("Entrée invalide", "Le taux de requêtes doit être un entier.")
            return
        self.log_message("Début de l'enrichissement...")
        self.btn_start.config(state=tk.DISABLED)
        self.stop_flag['stop'] = False
        if self.csv_viewer is None or not self.csv_viewer.winfo_exists():
            self.csv_viewer = CSVTableViewer(self.root, self.filepath, title="Aperçu CSV (avant update)")
        fast_mode = self.fast_mode.get()
        refresh_every = self.refresh_every
        def progress_callback(current, total):
            def _progress():
                self.update_progress(current, total)
                if not fast_mode and self.csv_viewer is not None and self.csv_viewer.winfo_exists():
                    try:
                        self.csv_viewer.tree.selection_remove(self.csv_viewer.tree.selection())
                        iid = self.csv_viewer.tree.get_children()[current-1]
                        self.csv_viewer.tree.see(iid)
                        self.csv_viewer.tree.selection_set(iid)
                    except Exception:
                        pass
            self.root.after(0, _progress)
        def log_callback(msg):
            self.log_message(msg)
        def thread_target():
            enrich_csv_with_eur_prices(
                self.filepath,
                rate,
                progress_callback,
                log_callback,
                table_viewer=self.csv_viewer,
                stop_flag=self.stop_flag,
                refresh_every=refresh_every,
                fast_mode=fast_mode
            )
            def _finish():
                if self.csv_viewer is not None and self.csv_viewer.winfo_exists():
                    try:
                        self.csv_viewer.df = pd.read_csv(self.filepath.replace('.csv', '_enriched.csv'))
                        self.csv_viewer.tree.delete(*self.csv_viewer.tree.get_children())
                        for _, row in self.csv_viewer.df.iterrows():
                            values = [row[col] for col in self.csv_viewer.df.columns]
                            self.csv_viewer.tree.insert("", "end", values=values)
                    except Exception:
                        pass
                self.btn_start.config(state=tk.NORMAL)
            self.root.after(0, _finish)
        self.thread = threading.Thread(target=thread_target, daemon=True)
        self.thread.start()

class CSVTableViewer(tk.Toplevel):
    """
    Fenêtre d'affichage d'un DataFrame/CSV en lecture seule, scrollable horizontalement et verticalement.
    """
    def __init__(self, parent, df_or_path, title="Aperçu CSV"):
        super().__init__(parent)
        self.title(title)
        self.geometry("1200x600")
        if isinstance(df_or_path, str):
            self.df = pd.read_csv(df_or_path)
        else:
            self.df = df_or_path.copy()
        self._setup_table()

    def _setup_table(self):
        frame = tk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True)

        # Table
        self.tree = Treeview(frame, columns=list(self.df.columns), show="headings")
        for col in self.df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")

        # Scrollbars
        vsb = Scrollbar(frame, orient="vertical", command=self.tree.yview)
        hsb = Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # Remplir la table
        for _, row in self.df.iterrows():
            values = [row[col] for col in self.df.columns]
            self.tree.insert("", "end", values=values)

        # Lecture seule : pas d'édition par l'utilisateur
        def block_edit(event):
            return "break"
        self.tree.bind('<Double-1>', block_edit)
        self.tree.bind('<Key>', block_edit)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
