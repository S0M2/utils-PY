import socket
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog, colorchooser, scrolledtext
from cryptography.fernet import Fernet
import random
import time

# Configuration par défaut
HOTE = '127.0.0.1'
PORT = 12345
clients = []
key = Fernet.generate_key()
cipher_suite = Fernet(key)
client_socket = None  # Initialisation de la variable client_socket
serveur = None  # Initialisation de la variable serveur
serveur_en_cours = False  # Indicateur pour savoir si le serveur est en cours d'exécution

def gerer_client(client_socket, adresse):
    try:
        # Recevoir les informations de connexion du client
        info_connexion = client_socket.recv(1024)
        if info_connexion:
            decrypted_info = cipher_suite.decrypt(info_connexion).decode('utf-8')
            afficher_message_systeme(f"{decrypted_info} connecté depuis {adresse}")
    except Exception as e:
        print(f"Erreur lors de la réception des informations de connexion: {e}")

    while True:
        try:
            message = client_socket.recv(1024)
            if message:
                decrypted_message = cipher_suite.decrypt(message).decode('utf-8')
                diffuser(decrypted_message, client_socket)
            else:
                retirer(client_socket)
                break
        except Exception as e:
            print(f"Erreur lors de la gestion du client: {e}")
            retirer(client_socket)
            break

def diffuser(message, client_socket):
    for client in clients:
        if client != client_socket:
            try:
                encrypted_message = cipher_suite.encrypt(message.encode('utf-8'))
                client.send(encrypted_message)
            except Exception as e:
                print(f"Erreur lors de la diffusion: {e}")
                retirer(client)

def retirer(client_socket):
    if client_socket in clients:
        clients.remove(client_socket)

def demarrer_serveur():
    global PORT, serveur, serveur_en_cours
    try:
        serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serveur.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serveur.bind((HOTE, PORT))
        serveur.listen(5)
        serveur_en_cours = True
        afficher_message_systeme(f"Serveur démarré sur le port {PORT}")

        ip_entry.delete(0, tk.END)
        ip_entry.insert(0, HOTE)
        port_entry.delete(0, tk.END)
        port_entry.insert(0, PORT)

        def accepter_clients():
            while serveur_en_cours:
                try:
                    client_socket, adresse = serveur.accept()
                    clients.append(client_socket)
                    thread = threading.Thread(target=gerer_client, args=(client_socket, adresse))
                    thread.daemon = True
                    thread.start()
                except ConnectionAbortedError:
                    break

        thread_accept = threading.Thread(target=accepter_clients)
        thread_accept.daemon = True
        thread_accept.start()
    except OSError as e:
        if e.errno == 48:  # Address already in use
            messagebox.showwarning("Port Occupé", f"Le port {PORT} est déjà utilisé. Tentative de liaison à un autre port.")
            PORT += 1
            demarrer_serveur()
        else:
            messagebox.showerror("Erreur", f"Erreur lors du démarrage du serveur: {e}")

def recevoir_messages(client_socket):
    while True:
        try:
            message = client_socket.recv(1024)
            if message:
                decrypted_message = cipher_suite.decrypt(message).decode('utf-8')
                afficher_message(decrypted_message)
            else:
                break
        except Exception as e:
            afficher_message(f"Erreur lors de la réception: {e}")
            client_socket.close()
            break

def envoyer_messages(client_socket, message):
    if message:
        try:
            encrypted_message = cipher_suite.encrypt(message.encode('utf-8'))
            client_socket.send(encrypted_message)
        except Exception as e:
            afficher_message(f"Erreur lors de l'envoi: {e}")
            client_socket.close()

def afficher_message(message):
    chat_box.config(state=tk.NORMAL)
    # Extraire le pseudo et le message
    try:
        pseudo, msg = message.split(":", 1)
    except ValueError:
        pseudo, msg = "Système", message

    # Appliquer la couleur au pseudo
    couleur = couleur_entry.get() if pseudo != "Système" else "#000000"
    chat_box.insert(tk.END, f"{pseudo}:", ("pseudo",))
    chat_box.tag_config("pseudo", foreground=couleur)

    # Afficher le message
    chat_box.insert(tk.END, f"{msg}\n")
    chat_box.config(state=tk.DISABLED)
    chat_box.yview(tk.END)

def afficher_message_systeme(message):
    historique_box.config(state=tk.NORMAL)
    historique_box.insert(tk.END, f"{message}\n")
    historique_box.config(state=tk.DISABLED)
    historique_box.yview(tk.END)

def demarrer_client():
    global client_socket
    try:
        hote = ip_entry.get()
        port = int(port_entry.get())
        pseudo = pseudo_entry.get()
        couleur = couleur_entry.get()

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Tentative de connexion avec plusieurs essais
        for _ in range(5):  # Essayer 5 fois
            try:
                client_socket.connect((hote, port))
                # Envoyer les informations de connexion au serveur
                info_connexion = f"{pseudo} (couleur: {couleur})"
                encrypted_info = cipher_suite.encrypt(info_connexion.encode('utf-8'))
                client_socket.send(encrypted_info)
                afficher_message(f"{pseudo} (couleur: {couleur}) connecté au serveur.")
                message_entry.config(state=tk.NORMAL)  # Activer le champ de saisie
                break
            except ConnectionRefusedError:
                afficher_message("Connexion refusée, nouvelle tentative...")
                time.sleep(1)  # Attendre 1 seconde avant de réessayer
        else:
            afficher_message("Impossible de se connecter au serveur après plusieurs tentatives.")
            return

        thread_reception = threading.Thread(target=recevoir_messages, args=(client_socket,))
        thread_reception.daemon = True
        thread_reception.start()
    except Exception as e:
        afficher_message(f"Erreur de connexion: {e}")

def envoyer():
    global client_socket
    message = message_entry.get()
    pseudo = pseudo_entry.get()
    couleur = couleur_entry.get()
    if client_socket:
        message_colored = f"{pseudo}: {message}"
        envoyer_messages(client_socket, message_colored)
    else:
        afficher_message("Erreur: Pas de connexion au serveur.")
    message_entry.delete(0, tk.END)

def choisir_couleur():
    couleur = colorchooser.askcolor(title="Choisir une couleur")[1]
    if couleur:
        couleur_entry.delete(0, tk.END)
        couleur_entry.insert(0, couleur)

def generer_pseudo_et_couleur():
    pseudo = f"User{random.randint(1000, 9999)}"
    couleur = "#{:06x}".format(random.randint(0, 0xFFFFFF))
    pseudo_entry.delete(0, tk.END)
    pseudo_entry.insert(0, pseudo)
    couleur_entry.delete(0, tk.END)
    couleur_entry.insert(0, couleur)

def fermer_serveur():
    global serveur, serveur_en_cours
    if serveur:
        serveur_en_cours = False
        serveur.close()
        afficher_message_systeme("Serveur arrêté.")
    # Réinitialiser le chat et désactiver le champ de saisie
    chat_box.config(state=tk.NORMAL)
    chat_box.delete(1.0, tk.END)
    chat_box.config(state=tk.DISABLED)
    message_entry.config(state=tk.DISABLED)
    ip_entry.delete(0, tk.END)
    port_entry.delete(0, tk.END)

def quitter_application():
    fermer_serveur()
    root.destroy()

# Interface graphique
root = tk.Tk()
root.title("Application de Chat")

# Cadre principal
main_frame = tk.Frame(root)
main_frame.pack(padx=10, pady=10)

# Cadre pour les informations de connexion
frame_connexion = tk.LabelFrame(main_frame, text="Informations de Connexion")
frame_connexion.grid(row=0, column=0, padx=10, pady=10, sticky="n")

tk.Label(frame_connexion, text="IP:").grid(row=0, column=0)
ip_entry = tk.Entry(frame_connexion)
ip_entry.grid(row=0, column=1)

tk.Label(frame_connexion, text="Port:").grid(row=1, column=0)
port_entry = tk.Entry(frame_connexion)
port_entry.grid(row=1, column=1)

tk.Label(frame_connexion, text="Pseudo:").grid(row=2, column=0)
pseudo_entry = tk.Entry(frame_connexion)
pseudo_entry.grid(row=2, column=1)

tk.Label(frame_connexion, text="Couleur:").grid(row=3, column=0)
couleur_entry = tk.Entry(frame_connexion)
couleur_entry.grid(row=3, column=1)

couleur_button = tk.Button(frame_connexion, text="Choisir Couleur", command=choisir_couleur)
couleur_button.grid(row=3, column=2)

serveur_button = tk.Button(frame_connexion, text="Démarrer Serveur", command=demarrer_serveur)
serveur_button.grid(row=4, column=0, columnspan=2, pady=5)

client_button = tk.Button(frame_connexion, text="Démarrer Client", command=demarrer_client)
client_button.grid(row=4, column=2, pady=5)

arreter_serveur_button = tk.Button(frame_connexion, text="Arrêter Serveur", command=fermer_serveur)
arreter_serveur_button.grid(row=5, column=0, columnspan=3, pady=5)

# Cadre pour l'historique des connexions
frame_historique = tk.LabelFrame(main_frame, text="Historique des Connexions")
frame_historique.grid(row=1, column=0, padx=10, pady=10, sticky="n")

historique_box = tk.Text(frame_historique, state=tk.DISABLED, width=50, height=15)
historique_box.pack(padx=5, pady=5)

# Cadre pour le chat
frame_chat = tk.LabelFrame(main_frame, text="Chat")
frame_chat.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="n")

chat_box = tk.Text(frame_chat, state=tk.DISABLED, width=50, height=20)
chat_box.pack(padx=5, pady=5)

message_entry = tk.Entry(frame_chat, width=40, state=tk.DISABLED)  # Désactivé par défaut
message_entry.pack(padx=5, pady=5)
message_entry.bind("<Return>", lambda event: envoyer())

envoyer_button = tk.Button(frame_chat, text="Envoyer", command=envoyer)
envoyer_button.pack(pady=5)

# Générer un pseudo et une couleur aléatoires après la création des widgets
generer_pseudo_et_couleur()

root.protocol("WM_DELETE_WINDOW", quitter_application)
root.mainloop()

class ChatApp:
    def __init__(self, parent):
        self.frame = parent
        self.setup_ui()

    def setup_ui(self):
        tk.Label(self.frame, text="Chat", font=('Helvetica', 16)).pack(pady=10)
        
        self.pseudo_entry = tk.Entry(self.frame, width=20)
        self.pseudo_entry.pack(pady=5)
        self.pseudo_entry.insert(0, "Pseudo")

        self.couleur_entry = tk.Entry(self.frame, width=20)
        self.couleur_entry.pack(pady=5)
        self.couleur_entry.insert(0, "#000000")

        self.message_entry = tk.Entry(self.frame, width=40)
        self.message_entry.pack(pady=5)

        self.envoyer_button = tk.Button(self.frame, text="Envoyer", command=self.envoyer_message)
        self.envoyer_button.pack(pady=5)

        self.chat_box = scrolledtext.ScrolledText(self.frame, width=50, height=10, state=tk.DISABLED)
        self.chat_box.pack(pady=5)

    def envoyer_message(self):
        message = self.message_entry.get()
        self.chat_box.config(state=tk.NORMAL)
        self.chat_box.insert(tk.END, f"{self.pseudo_entry.get()}: {message}\n")
        self.chat_box.config(state=tk.DISABLED)
        self.message_entry.delete(0, tk.END)
