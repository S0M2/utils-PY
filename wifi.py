import os
import sys

# Redirection des messages d'erreur
if sys.platform == 'darwin':  # Si on est sur macOS
    # Rediriger stderr vers /dev/null
    os.environ['TK_SILENCE_DEPRECATION'] = '1'  # Supprime les avertissements de dépréciation Tk
    devnull = open(os.devnull, 'w')
    sys.stderr = devnull

from CoreWLAN import CWInterface
import time
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import font

class WiFiScanner:
    def __init__(self):
        self.wifi_interface = CWInterface.interface()
        if not self.wifi_interface:
            raise Exception("Aucune interface Wi-Fi détectée")

    def scan_wifi(self):
        """Scanne les réseaux Wi-Fi disponibles"""
        try:
            error = None
            networks = self.wifi_interface.scanForNetworksWithName_error_(None, error)
            if networks:
                return networks[0]
            return []
        except Exception as e:
            print(f"Erreur lors du scan: {e}")
            return []

    def display_networks(self, networks):
        """Affiche les réseaux trouvés"""
        if not networks:
            print("Aucun réseau trouvé")
            return

        print("\n" + "=" * 80)
        print(f"{'SSID':<32}{'BSSID':<20}{'RSSI':<8}{'CANAL':<8}{'SÉCURITÉ'}")
        print("=" * 80)

        for network in networks:
            try:
                ssid = network.ssid() or "Réseau caché"
                bssid = network.bssid() or "Inconnu"
                rssi = str(network.rssiValue())
                channel = str(network.wlanChannel().channelNumber())
                security = "Oui" if network.securityMode() else "Non"
                
                print(f"{ssid:<32}{bssid:<20}{rssi:<8}{channel:<8}{security}")
            except Exception as e:
                continue

    def monitor_networks(self, interval=5):
        """Mode surveillance continue"""
        try:
            while True:
                print("\nRecherche de réseaux Wi-Fi...")
                networks = self.scan_wifi()
                self.display_networks(networks)
                self.network_statistics(networks)
                print(f"\nProchaine analyse dans {interval} secondes (Ctrl+C pour arrêter)")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nSurveillance arrêtée")

    def network_statistics(self, networks):
        """Affiche les statistiques des réseaux"""
        if not networks:
            return

        total = len(networks)
        secured = len([n for n in networks if n.securityMode()])
        
        print("\n=== Statistiques ===")
        print(f"Nombre total de réseaux : {total}")
        if total > 0:
            print(f"Réseaux sécurisés : {secured} ({(secured/total*100):.1f}%)")
            print(f"Réseaux non sécurisés : {total-secured} ({((total-secured)/total*100):.1f}%)")

class WiFiScannerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Scanner Wi-Fi")
        self.root.geometry("800x600")
        
        # Définir une palette de couleurs
        self.root.configure(bg='#f0f0f0')  # Couleur de fond
        
        # Définir une police moderne
        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(family="Helvetica", size=10)
        
        self.scanner = WiFiScanner()
        self.monitoring = False
        
        self.setup_gui()
        
    def setup_gui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10", style='Main.TFrame')
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Boutons de contrôle
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=0, column=0, pady=5, sticky=tk.W)
        
        ttk.Button(control_frame, text="Scan unique", command=self.single_scan, style='Accent.TButton').grid(row=0, column=0, padx=5)
        self.monitor_button = ttk.Button(control_frame, text="Démarrer surveillance", command=self.toggle_monitoring, style='Accent.TButton')
        self.monitor_button.grid(row=0, column=1, padx=5)
        
        # Intervalle de scan
        ttk.Label(control_frame, text="Intervalle (s):").grid(row=0, column=2, padx=5)
        self.interval_var = tk.StringVar(value="5")
        self.interval_entry = ttk.Entry(control_frame, textvariable=self.interval_var, width=5)
        self.interval_entry.grid(row=0, column=3, padx=5)
        
        # Tableau des réseaux
        self.tree = ttk.Treeview(main_frame, columns=("ssid", "bssid", "rssi", "channel", "security"), show="headings", style='Treeview')
        self.tree.grid(row=1, column=0, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configuration des colonnes
        self.tree.heading("ssid", text="SSID")
        self.tree.heading("bssid", text="BSSID")
        self.tree.heading("rssi", text="RSSI")
        self.tree.heading("channel", text="Canal")
        self.tree.heading("security", text="Sécurité")
        
        self.tree.column("ssid", width=200)
        self.tree.column("bssid", width=150)
        self.tree.column("rssi", width=100)
        self.tree.column("channel", width=100)
        self.tree.column("security", width=100)
        
        # Augmenter la taille du tableau
        self.tree.configure(height=15)  # Augmentez la hauteur du tableau
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Zone de statistiques
        self.stats_text = tk.Text(main_frame, height=5, width=70, bg='#e0e0e0', font=self.default_font)
        self.stats_text.grid(row=2, column=0, pady=5, sticky=(tk.W, tk.E))
        
        # Ajout de la barre de progression
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_frame, 
            variable=self.progress_var, 
            maximum=100,
            mode='indeterminate'
        )
        self.progress_bar.grid(row=3, column=0, pady=5, sticky=(tk.W, tk.E))
        
        # Ajout des filtres
        filter_frame = ttk.LabelFrame(main_frame, text="Filtres", padding="5", style='Filter.TLabelframe')
        filter_frame.grid(row=4, column=0, pady=5, sticky=(tk.W, tk.E))
        
        # Filtre SSID
        ttk.Label(filter_frame, text="SSID:").grid(row=0, column=0, padx=5)
        self.ssid_filter = ttk.Entry(filter_frame, width=20)
        self.ssid_filter.grid(row=0, column=1, padx=5)
        
        # Filtre force du signal
        ttk.Label(filter_frame, text="Signal min (dBm):").grid(row=0, column=2, padx=5)
        self.signal_filter = ttk.Entry(filter_frame, width=5)
        self.signal_filter.grid(row=0, column=3, padx=5)
        
        # Filtre sécurité
        self.security_var = tk.BooleanVar()
        ttk.Checkbutton(filter_frame, text="Réseaux sécurisés uniquement", 
                        variable=self.security_var).grid(row=0, column=4, padx=5)
        
        ttk.Button(filter_frame, text="Appliquer", 
                   command=self.apply_filters, style='Accent.TButton').grid(row=0, column=5, padx=5)
        
        # Frame pour les graphiques
        self.graph_frame = ttk.Frame(main_frame)
        self.graph_frame.grid(row=6, column=0, pady=5, sticky=(tk.W, tk.E))
        
        # Création du graphique
        self.fig = Figure(figsize=(6, 2))  # Réduire la taille du graphique
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Configuration du redimensionnement
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
    def update_network_list(self, networks):
        # Effacer la liste actuelle
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Ajouter les nouveaux réseaux
        for network in networks:
            try:
                ssid = network.ssid() or "Réseau caché"
                bssid = network.bssid() or "Inconnu"
                rssi = str(network.rssiValue())
                channel = str(network.wlanChannel().channelNumber())
                security = "Oui" if network.securityMode() else "Non"
                
                self.tree.insert("", tk.END, values=(ssid, bssid, rssi, channel, security))
            except Exception as e:
                continue
                
        # Mettre à jour les statistiques
        self.update_statistics(networks)
        
        # Ajouter cette ligne pour mettre à jour les graphiques
        self.update_graphs(networks)
        
    def update_statistics(self, networks):
        total = len(networks)
        secured = len([n for n in networks if n.securityMode()])
        
        stats = f"=== Statistiques ===\n"
        stats += f"Nombre total de réseaux : {total}\n"
        if total > 0:
            stats += f"Réseaux sécurisés : {secured} ({(secured/total*100):.1f}%)\n"
            stats += f"Réseaux non sécurisés : {total-secured} ({((total-secured)/total*100):.1f}%)"
            
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, stats)
        
    def single_scan(self):
        self.progress_bar.start(10)  # Démarre l'animation
        self.root.update()
        
        networks = self.scanner.scan_wifi()
        self.update_network_list(networks)
        
        self.progress_bar.stop()  # Arrête l'animation
        
    def toggle_monitoring(self):
        if not self.monitoring:
            try:
                interval = max(1, min(60, int(self.interval_var.get())))
                self.monitoring = True
                self.monitor_button.configure(text="Arrêter surveillance")
                self.interval_entry.configure(state="disabled")
                self.progress_bar.start(10)  # Démarre l'animation
                threading.Thread(target=self.monitor_networks, args=(interval,), daemon=True).start()
            except ValueError:
                messagebox.showerror("Erreur", "L'intervalle doit être un nombre entre 1 et 60")
        else:
            self.monitoring = False
            self.monitor_button.configure(text="Démarrer surveillance")
            self.interval_entry.configure(state="normal")
            self.progress_bar.stop()  # Arrête l'animation
            
    def monitor_networks(self, interval):
        while self.monitoring:
            networks = self.scanner.scan_wifi()
            self.root.after(0, self.update_network_list, networks)
            time.sleep(interval)

    def apply_filters(self):
        networks = self.scanner.scan_wifi()
        filtered_networks = []
        
        for network in networks:
            # Filtre SSID
            if self.ssid_filter.get():
                if not network.ssid() or self.ssid_filter.get().lower() not in network.ssid().lower():
                    continue
            
            # Filtre signal
            if self.signal_filter.get():
                try:
                    min_signal = int(self.signal_filter.get())
                    if network.rssiValue() < min_signal:
                        continue
                except ValueError:
                    pass
            
            # Filtre sécurité
            if self.security_var.get() and not network.securityMode():
                continue
            
            filtered_networks.append(network)
        
        self.update_network_list(filtered_networks)

    def update_graphs(self, networks):
        self.fig.clear()
        
        if not networks:
            return
            
        # Graphique des canaux
        channels = {}
        for network in networks:
            try:
                channel = network.wlanChannel().channelNumber()
                channels[channel] = channels.get(channel, 0) + 1
            except:
                continue
        
        if channels:  # Vérifier qu'il y a des données à afficher
            ax = self.fig.add_subplot(111)
            ax.bar(sorted(channels.keys()), [channels[k] for k in sorted(channels.keys())])
            ax.set_xlabel('Canal')
            ax.set_ylabel('Nombre de réseaux')
            ax.set_title('Distribution des réseaux par canal')
            
            # Ajuster les marges
            self.fig.tight_layout()
            
            # Rafraîchir le canvas
            self.canvas.draw()

def main():
    try:
        root = tk.Tk()
        app = WiFiScannerGUI(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Erreur", str(e))

if __name__ == "__main__":
    main()
