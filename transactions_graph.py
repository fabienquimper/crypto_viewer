import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np

class TransactionsGraphWindow(tk.Toplevel):
    def __init__(self, parent, df):
        super().__init__(parent)
        self.title("Graph: Transactions by Currency")
        self.geometry("1000x600")
        self.df = df.copy()
        self.selected_currencies = []
        self._prepare_data()
        self._setup_ui()
        self._draw_graph()

    def _prepare_data(self):
        # Nettoyage et préparation des données
        if 'Date' not in self.df.columns:
            raise ValueError("Le fichier doit contenir la colonne 'Date'")
        self.df['Date'] = pd.to_datetime(self.df['Date'], errors='coerce')
        self.df = self.df.dropna(subset=['Date'])
        self.df = self.df.sort_values('Date')
        # On va construire un DataFrame avec toutes les opérations par currency
        events = []
        for idx, row in self.df.iterrows():
            ttype = row.get('Type', '')
            label = row.get('Label', '')
            # Trade : Sent (sortie), Received (entrée)
            if ttype == 'Trade':
                if pd.notna(row.get('Sent Currency')) and pd.notna(row.get('Sent Amount')):
                    events.append({'Date': row['Date'], 'Currency': row['Sent Currency'], 'Delta': -abs(float(row['Sent Amount']))})
                if pd.notna(row.get('Received Currency')) and pd.notna(row.get('Received Amount')):
                    events.append({'Date': row['Date'], 'Currency': row['Received Currency'], 'Delta': float(row['Received Amount'])})
            # Receive Reward : entrée
            elif ttype == 'Receive' and label == 'Reward':
                if pd.notna(row.get('Received Currency')) and pd.notna(row.get('Received Amount')):
                    events.append({'Date': row['Date'], 'Currency': row['Received Currency'], 'Delta': float(row['Received Amount'])})
            # Buy : Sent (EUR, sortie), Received (entrée)
            elif ttype == 'Buy':
                if pd.notna(row.get('Sent Currency')) and pd.notna(row.get('Sent Amount')):
                    events.append({'Date': row['Date'], 'Currency': row['Sent Currency'], 'Delta': -abs(float(row['Sent Amount']))})
                if pd.notna(row.get('Received Currency')) and pd.notna(row.get('Received Amount')):
                    events.append({'Date': row['Date'], 'Currency': row['Received Currency'], 'Delta': float(row['Received Amount'])})
            # Deposit : Received (EUR, sortie)
            elif ttype == 'Deposit':
                if pd.notna(row.get('Received Currency')) and pd.notna(row.get('Received Amount')):
                    events.append({'Date': row['Date'], 'Currency': row['Received Currency'], 'Delta': -abs(float(row['Received Amount']))})
        self.events_df = pd.DataFrame(events)
        self.currencies = sorted(self.events_df['Currency'].unique()) if not self.events_df.empty else []

    def _setup_ui(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=4)
        main_frame.columnconfigure(1, weight=1)

        graph_frame = ttk.Frame(main_frame)
        graph_frame.grid(row=0, column=0, sticky="nsew")

        control_frame = ttk.Frame(main_frame, padding=10)
        control_frame.grid(row=0, column=1, sticky="ns")

        lbl = ttk.Label(control_frame, text="Currencies:")
        lbl.pack(anchor="w")
        self.currency_listbox = tk.Listbox(control_frame, selectmode=tk.MULTIPLE, exportselection=False, height=20)
        for cur in self.currencies:
            self.currency_listbox.insert(tk.END, cur)
        self.currency_listbox.pack(fill=tk.BOTH, expand=True)
        self.currency_listbox.bind('<<ListboxSelect>>', lambda e: self._draw_graph())

        btns_frame = ttk.Frame(control_frame)
        btns_frame.pack(fill=tk.X, pady=5)
        btn_all = ttk.Button(btns_frame, text="Tout sélectionner", command=self._select_all)
        btn_all.pack(side=tk.LEFT, padx=2)
        btn_none = ttk.Button(btns_frame, text="Tout désélectionner", command=self._deselect_all)
        btn_none.pack(side=tk.LEFT, padx=2)

        self.fig, self.ax = plt.subplots(figsize=(8, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.tooltip = None

        # Label dynamique sous le graphique
        self.info_label = ttk.Label(graph_frame, text="", anchor="w", font=("Courier", 10))
        self.info_label.pack(fill=tk.X, pady=(5, 0))

    def _select_all(self):
        self.currency_listbox.select_set(0, tk.END)
        self._draw_graph()

    def _deselect_all(self):
        self.currency_listbox.selection_clear(0, tk.END)
        self._draw_graph()

    def _draw_graph(self):
        self.ax.clear()
        selected_indices = self.currency_listbox.curselection()
        if not selected_indices or self.events_df.empty:
            self.ax.set_title("Sélectionnez une ou plusieurs currencies à afficher.")
            self.canvas.draw()
            return
        selected_currencies = [self.currencies[i] for i in selected_indices]
        df = self.events_df[self.events_df['Currency'].isin(selected_currencies)]
        if df.empty:
            self.ax.set_title("Aucune donnée pour la sélection.")
            self.canvas.draw()
            return
        # Pivot pour avoir une colonne par currency, indexé par date
        pivot = df.pivot_table(index='Date', columns='Currency', values='Delta', aggfunc='sum').fillna(0)
        pivot = pivot.sort_index()
        cum = pivot.cumsum()
        for cur in selected_currencies:
            self.ax.plot(cum.index, cum[cur], label=cur)
        self.ax.set_xlabel("Date")
        self.ax.set_ylabel("Solde cumulé")
        self.ax.set_title("Solde cumulé par currency dans le temps")
        self.ax.legend()
        self.fig.autofmt_xdate()
        self.canvas.draw()
        self._cum = cum

    def _on_hover(self, event):
        if event.inaxes != self.ax:
            if self.tooltip:
                self.tooltip.set_visible(False)
                self.tooltip = None
            self.info_label.config(text="")
            return
        if not hasattr(self, '_cum') or self._cum is None:
            self.info_label.config(text="")
            return
        if event.xdata is None:
            self.info_label.config(text="")
            return
        xdata = self._cum.index
        if len(xdata) == 0:
            self.info_label.config(text="")
            return
        idx = np.searchsorted(xdata, pd.to_datetime(event.xdata), side='left')
        if idx >= len(xdata):
            idx = len(xdata) - 1
        date = xdata[idx]
        vals = self._cum.iloc[idx]
        text = f"{date.strftime('%Y-%m-%d')}  " + "  ".join([f"{cur}: {vals[cur]:.8f}" for cur in self._cum.columns])
        self.info_label.config(text=text)
        if self.tooltip:
            self.tooltip.set_visible(False)
        self.tooltip = self.ax.annotate(f"{date.strftime('%Y-%m-%d')}\n" + "\n".join([f"{cur}: {vals[cur]:.8f}" for cur in self._cum.columns]), xy=(event.xdata, event.ydata), xytext=(20, 20), textcoords='offset points', bbox=dict(boxstyle="round", fc="w"), arrowprops=dict(arrowstyle="->"))
        self.canvas.draw_idle()

# Fonction utilitaire pour ouvrir la fenêtre depuis transactions.py

def show_graph_window(parent, df):
    TransactionsGraphWindow(parent, df) 