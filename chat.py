import socket
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog, colorchooser, scrolledtext
from cryptography.fernet import Fernet
import random
import time

# Génération de la clé de chiffrement
key = Fernet.generate_key()
cipher_suite = Fernet(key)

clients = []  # Liste des clients connectés
serveur = None  # Référence au serveur
serveur_en_cours = False  # Indicateur de l'état du serveur


def gerer_client(client_socket, adresse):
    try:
        info_connexion = client_socket.recv(1024)
        if info_connexion:
            decrypted_info = cipher_suite.decrypt(info_connexion).decode('utf-8')
            afficher_message_systeme(f"{decrypted_info} connecté depuis {adresse}")
    except Exception as e:
        print(f"Erreur de connexion: {e}")
    
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
            print(f"Erreur client: {e}")
            retirer(client_socket)
            break


def diffuser(message, client_socket):
    for client in clients:
        if client != client_socket:
            try:
                encrypted_message = cipher_suite.encrypt(message.encode('utf-8'))
                client.send(encrypted_message)
            except Exception as e:
                print(f"Erreur de diffusion: {e}")
                retirer(client)


def retirer(client_socket):
    if client_socket in clients:
        clients.remove(client_socket)
        client_socket.close()


def demarrer_serveur(hote, port):
    global serveur, serveur_en_cours
    try:
        serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serveur.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serveur.bind((hote, port))
        serveur.listen(5)
        serveur_en_cours = True
        afficher_message_systeme(f"Serveur démarré sur {hote}:{port}")

        def accepter_clients():
            while serveur_en_cours:
                try:
                    client_socket, adresse = serveur.accept()
                    clients.append(client_socket)
                    threading.Thread(target=gerer_client, args=(client_socket, adresse), daemon=True).start()
                except Exception as e:
                    print(f"Erreur acceptation client: {e}")
                    break
        
        threading.Thread(target=accepter_clients, daemon=True).start()
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de démarrer le serveur: {e}")


def recevoir_messages(client_socket):
    while True:
        try:
            message = client_socket.recv(1024)
            if message:
                afficher_message(cipher_suite.decrypt(message).decode('utf-8'))
            else:
                break
        except:
            break


def envoyer_messages(client_socket, message):
    if message:
        try:
            client_socket.send(cipher_suite.encrypt(message.encode('utf-8')))
        except:
            client_socket.close()


def demarrer_client(hote, port, pseudo):
    global client_socket
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((hote, port))
        info_connexion = f"{pseudo}"
        client_socket.send(cipher_suite.encrypt(info_connexion.encode('utf-8')))
        threading.Thread(target=recevoir_messages, args=(client_socket,), daemon=True).start()
    except Exception as e:
        afficher_message(f"Erreur de connexion: {e}")


def envoyer():
    global client_socket
    message = message_entry.get()
    pseudo = pseudo_entry.get()
    if client_socket:
        envoyer_messages(client_socket, f"{pseudo}: {message}")
    message_entry.delete(0, tk.END)


def afficher_message(message):
    chat_box.config(state=tk.NORMAL)
    chat_box.insert(tk.END, message + "\n")
    chat_box.config(state=tk.DISABLED)
    chat_box.yview(tk.END)


def afficher_message_systeme(message):
    historique_box.config(state=tk.NORMAL)
    historique_box.insert(tk.END, message + "\n")
    historique_box.config(state=tk.DISABLED)
    historique_box.yview(tk.END)


# Interface graphique
root = tk.Tk()
root.title("Chat Réseau")

frame_connexion = tk.LabelFrame(root, text="Connexion")
frame_connexion.pack(pady=10)

tk.Label(frame_connexion, text="IP:").grid(row=0, column=0)
ip_entry = tk.Entry(frame_connexion)
ip_entry.grid(row=0, column=1)
ip_entry.insert(0, "127.0.0.1")

tk.Label(frame_connexion, text="Port:").grid(row=1, column=0)
port_entry = tk.Entry(frame_connexion)
port_entry.grid(row=1, column=1)
port_entry.insert(0, "12345")

tk.Label(frame_connexion, text="Pseudo:").grid(row=2, column=0)
pseudo_entry = tk.Entry(frame_connexion)
pseudo_entry.grid(row=2, column=1)

serveur_button = tk.Button(frame_connexion, text="Démarrer Serveur", command=lambda: demarrer_serveur(ip_entry.get(), int(port_entry.get())))
serveur_button.grid(row=3, column=0, pady=5)

client_button = tk.Button(frame_connexion, text="Rejoindre", command=lambda: demarrer_client(ip_entry.get(), int(port_entry.get()), pseudo_entry.get()))
client_button.grid(row=3, column=1, pady=5)

frame_chat = tk.LabelFrame(root, text="Chat")
frame_chat.pack(pady=10)

chat_box = tk.Text(frame_chat, state=tk.DISABLED, width=50, height=15)
chat_box.pack(padx=5, pady=5)

message_entry = tk.Entry(frame_chat, width=40)
message_entry.pack(padx=5, pady=5)
message_entry.bind("<Return>", lambda event: envoyer())

envoyer_button = tk.Button(frame_chat, text="Envoyer", command=envoyer)
envoyer_button.pack(pady=5)

historique_box = tk.Text(root, state=tk.DISABLED, width=50, height=5)
historique_box.pack(pady=5)

root.mainloop()
