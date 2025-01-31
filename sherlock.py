import json
import aiohttp
import asyncio
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk, filedialog
from PIL import Image, ImageTk
import os
import threading
import webbrowser
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class SherlockApp:
    def __init__(self, parent):
        self.frame = parent
        self.results = []
        self.setup_ui()

    def setup_ui(self):
        tk.Label(self.frame, text="Sherlock", font=('Helvetica', 16)).pack(pady=10)
        
        self.username_entry = tk.Entry(self.frame, width=20)
        self.username_entry.pack(pady=5)
        self.username_entry.insert(0, "Nom d'utilisateur")

        self.search_button = tk.Button(self.frame, text="Rechercher", command=self.on_search_async)
        self.search_button.pack(pady=5)

        self.result_display = scrolledtext.ScrolledText(self.frame, width=50, height=10, state=tk.DISABLED)
        self.result_display.pack(pady=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(pady=10, fill=tk.X)

    def load_sites(self, file_path):
        with open(file_path, 'r') as file:
            return json.load(file)

    async def check_username_availability_async(self, username, sites):
        total_sites = len(sites)
        async with aiohttp.ClientSession() as session:
            for index, site in enumerate(sites):
                url = site['url'].format(username=username)
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            self.results.append((f"{username} est pris sur {site['name']}", "red", url))
                        else:
                            self.results.append((f"{username} est disponible sur {site['name']}", "green", url))
                except Exception as e:
                    self.results.append((f"Erreur lors de la recherche sur {site['name']}: {e}", "black", url))
                
                self.progress_var.set((index + 1) / total_sites * 100)
                self.frame.update_idletasks()
        
        self.apply_filter()
        self.update_statistics()

    def on_search_async(self):
        username = self.username_entry.get()
        if username:
            file_path = os.path.join(os.path.dirname(__file__), 'site.json')
            sites = self.load_sites(file_path)
            self.progress_var.set(0)
            self.results.clear()
            threading.Thread(target=lambda: asyncio.run(self.check_username_availability_async(username, sites))).start()
        else:
            messagebox.showwarning("Avertissement", "Veuillez entrer un nom d'utilisateur.")

    def apply_filter(self):
        self.result_display.config(state=tk.NORMAL)
        self.result_display.delete(1.0, tk.END)
        for text, color, url in self.results:
            self.result_display.insert(tk.END, text + "\n", color)
        self.result_display.config(state=tk.DISABLED)

    def update_statistics(self):
        # Mettre à jour les statistiques
        pass

def load_sites(file_path):
    
    with open(file_path, 'r') as file:
        return json.load(file)

async def check_username_availability_async(username, sites, progress_var, results):
    total_sites = len(sites)
    async with aiohttp.ClientSession() as session:
        for index, site in enumerate(sites):
            url = site['url'].format(username=username)
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        results.append((f"{username} est pris sur {site['name']}", "red", url))
                    else:
                        results.append((f"{username} est disponible sur {site['name']}", "green", url))
            except Exception as e:
                results.append((f"Erreur lors de la recherche sur {site['name']}: {e}", "black", url))
            
            # Mettre à jour la barre de progression
            progress_var.set((index + 1) / total_sites * 100)
            root.update_idletasks()
    
    # Appliquer le filtre après la recherche
    apply_filter()
    # Mettre à jour le graphique des statistiques
    update_statistics()

def on_search_async():
    username = entry.get()
    if username:
        file_path = os.path.join(os.path.dirname(__file__), 'site.json')
        sites = load_sites(file_path)
        progress_var.set(0)
        results.clear()  # Clear previous results
        threading.Thread(target=lambda: asyncio.run(check_username_availability_async(username, sites, progress_var, results))).start()
    else:
        messagebox.showwarning("Avertissement", "Veuillez entrer un nom d'utilisateur.")

def apply_filter():
    filter_option = filter_var.get()
    filtered_results = []
    seen_urls = set()  # Pour suivre les URLs déjà vues
    for text, color, url in results:
        if url not in seen_urls:  # Vérifier si l'URL a déjà été vue
            if (filter_option == "Tous") or \
               (filter_option == "Disponibles" and "disponible" in text) or \
               (filter_option == "Pris" and "pris" in text):
                filtered_results.append((text, color, url))
                seen_urls.add(url)  # Ajouter l'URL au set des URLs vues
    
    # Afficher les résultats filtrés avec la couleur appropriée
    result_display.delete(1.0, tk.END)
    for text, color, url in filtered_results:
        start_index = result_display.index(tk.END)
        result_display.insert(tk.END, text + "\n", color)
        end_index = result_display.index(tk.END)
        result_display.tag_configure(color, foreground=color)
        result_display.tag_add(f"link{start_index}", start_index, end_index)
        result_display.tag_bind(f"link{start_index}", "<Button-1>", lambda e, url=url: webbrowser.open(url))

def update_statistics():
    # Compter les résultats
    pris_count = sum(1 for text, color, url in results if "pris" in text)
    disponible_count = sum(1 for text, color, url in results if "disponible" in text)
    erreur_count = sum(1 for text, color, url in results if "Erreur" in text)

    # Mettre à jour le graphique
    ax.clear()
    counts = [pris_count, disponible_count, erreur_count]
    ax.pie(counts, colors=['red', 'green', 'black'])
    canvas.draw()

def export_results():
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    if file_path:
        with open(file_path, 'w') as file:
            file.write(result_display.get(1.0, tk.END))

# Création de l'interface
root = tk.Tk()
root.title("Sherlock Amélioré")

# Style clair et harmonieux
root.configure(bg='#f0f0f0')  # Fond clair
style = ttk.Style()
style.theme_use('clam')  # Utilisation d'un thème moderne
style.configure('TButton', background='#e0e0e0', foreground='#333333', font=('Helvetica', 10, 'bold'), borderwidth=0)
style.map('TButton', background=[('active', '#cccccc')])
style.configure('TLabel', background='#f0f0f0', foreground='#333333', font=('Helvetica', 12))
style.configure('TEntry', fieldbackground='#ffffff', foreground='#333333')
style.configure('TProgressbar', troughcolor='#e0e0e0', background='#4caf50')

# Disposition des éléments
main_frame = tk.Frame(root, bg='#f0f0f0')
main_frame.pack(pady=5, fill=tk.X)

left_frame = tk.Frame(main_frame, bg='#f0f0f0')
left_frame.pack(side=tk.LEFT, padx=5)

right_frame = tk.Frame(main_frame, bg='#f0f0f0')
right_frame.pack(side=tk.RIGHT, padx=5)

label = ttk.Label(left_frame, text="Nom d'utilisateur :")
label.pack(pady=5)

entry = ttk.Entry(left_frame, width=20)
entry.pack(pady=5)

search_button = ttk.Button(left_frame, text="Rechercher", command=on_search_async, width=20)
search_button.pack(pady=5)

export_button = ttk.Button(left_frame, text="Exporter les résultats", command=export_results, width=20)
export_button.pack(pady=5)

filter_var = tk.StringVar(value="Tous")
filter_menu = ttk.OptionMenu(left_frame, filter_var, "Tous", "Tous", "Disponibles", "Pris", command=lambda _: apply_filter())
filter_menu.pack(pady=5)

# Initialiser le graphique vide
fig, ax = plt.subplots(figsize=(1, 1))
ax.pie([1], colors=['#f0f0f0'])
canvas = FigureCanvasTkAgg(fig, master=right_frame)
canvas.draw()
canvas.get_tk_widget().pack()

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100, style='TProgressbar')
progress_bar.pack(pady=10, fill=tk.X)

# Agrandir la taille de l'affichage des résultats
result_display = scrolledtext.ScrolledText(root, width=60, height=20, bg='#ffffff', fg='#333333', insertbackground='black')
result_display.pack(pady=10)

# Liste pour stocker les résultats
results = []

root.mainloop()