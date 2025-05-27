import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np

class RealizedGainsGraphWindow(tk.Toplevel):
    def __init__(self, parent, df):
        super().__init__(parent)
        self.title("Graph: Realized Capital Gains by Currency")
        self.geometry("1000x600")
        self.df = df.copy()
        self.selected_currencies = []
        self._prepare_data()
        self._setup_ui()
        self._draw_graph()

    def _prepare_data(self):
        # Nettoyage et préparation des données
        if 'Sold' not in self.df.columns or 'Currency name' not in self.df.columns or 'Currency amount' not in self.df.columns:
            raise ValueError("Le fichier doit contenir les colonnes 'Sold', 'Currency name', 'Currency amount'")
        self.df['Sold'] = pd.to_datetime(self.df['Sold'], errors='coerce')
        self.df = self.df.dropna(subset=['Sold', 'Currency name', 'Currency amount'])
        self.df['Currency amount'] = pd.to_numeric(self.df['Currency amount'], errors='coerce').fillna(0)
        self.df = self.df.sort_values('Sold')
        self.currencies = sorted(self.df['Currency name'].unique())

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
        if not selected_indices:
            self.ax.set_title("Sélectionnez une ou plusieurs currencies à afficher.")
            self.canvas.draw()
            return
        selected_currencies = [self.currencies[i] for i in selected_indices]
        df = self.df[self.df['Currency name'].isin(selected_currencies)]
        if df.empty:
            self.ax.set_title("Aucune donnée pour la sélection.")
            self.canvas.draw()
            return
        # Grouper par date et currency, puis cumul
        pivot = df.pivot_table(index='Sold', columns='Currency name', values='Currency amount', aggfunc='sum').fillna(0)
        pivot = pivot.sort_index()
        cum = pivot.cumsum()
        for cur in selected_currencies:
            self.ax.plot(cum.index, cum[cur], label=cur)
        self.ax.set_xlabel("Date de cession (Sold)")
        self.ax.set_ylabel("Quantité cumulée")
        self.ax.set_title("Quantité cumulée par currency dans le temps")
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

# Fonction utilitaire pour ouvrir la fenêtre depuis realized_gains.py

def show_graph_window(parent, df):
    RealizedGainsGraphWindow(parent, df) 