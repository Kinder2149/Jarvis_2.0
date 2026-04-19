import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import socket
import time
import webbrowser
from pathlib import Path
import sys
import requests

class JarvisLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("JARVIS")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        self.root.configure(bg="#1a1a2e")
        
        # Déterminer la racine du projet (parent de launcher/)
        if getattr(sys, 'frozen', False):
            # --onedir : exe dans dist/JARVIS/, données à côté
            exe_dir = Path(sys.executable).parent

            # PyInstaller 6+ met les données dans _internal/
            internal_dir = exe_dir / '_internal'
            if internal_dir.exists():
                self.jarvis_root = internal_dir
            else:
                self.jarvis_root = exe_dir

            # DB et config dans exe_dir/backend/data/ (writable)
            self.data_dir = exe_dir / 'backend' / 'data'
            self.data_dir.mkdir(parents=True, exist_ok=True)

            # Rendre les modules importables
            for path in [str(self.jarvis_root), str(self.jarvis_root / 'backend')]:
                if path not in sys.path:
                    sys.path.insert(0, path)
        else:
            # Script Python
            self.jarvis_root = Path(__file__).parent.parent
            self.data_dir = self.jarvis_root / 'backend' / 'data'
        
        self.process = None
        self.status = "stopped"  # stopped, starting, running, error
        self.log_thread = None
        
        self._build_ui()
        self._check_server_on_startup()
        
        # Protocole de fermeture
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _build_ui(self):
        # Titre
        title_label = tk.Label(
            self.root,
            text="⚡ JARVIS",
            font=("Segoe UI", 24, "bold"),
            bg="#1a1a2e",
            fg="#e0e0e0"
        )
        title_label.pack(pady=20)
        
        # Frame statut
        status_frame = tk.Frame(self.root, bg="#1a1a2e")
        status_frame.pack(pady=10)
        
        self.status_indicator = tk.Canvas(status_frame, width=20, height=20, bg="#1a1a2e", highlightthickness=0)
        self.status_indicator.pack(side=tk.LEFT, padx=5)
        self.status_circle = self.status_indicator.create_oval(2, 2, 18, 18, fill="#e63946", outline="")
        
        self.status_label = tk.Label(
            status_frame,
            text="Serveur arrêté",
            font=("Segoe UI", 11),
            bg="#1a1a2e",
            fg="#e0e0e0"
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Bouton Démarrer/Arrêter
        self.toggle_button = tk.Button(
            self.root,
            text="▶ Démarrer",
            font=("Segoe UI", 12, "bold"),
            bg="#00b4d8",
            fg="#ffffff",
            activebackground="#0096c7",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._toggle_server
        )
        self.toggle_button.pack(fill=tk.X, padx=20, pady=10)
        
        # Zone de logs
        log_label = tk.Label(
            self.root,
            text="Logs serveur :",
            font=("Segoe UI", 9),
            bg="#1a1a2e",
            fg="#a8dadc",
            anchor="w"
        )
        log_label.pack(fill=tk.X, padx=20, pady=(10, 0))
        
        self.log_area = scrolledtext.ScrolledText(
            self.root,
            height=10,
            font=("Consolas", 8),
            bg="#0d0d1a",
            fg="#a8dadc",
            insertbackground="#a8dadc",
            relief=tk.FLAT,
            state=tk.DISABLED
        )
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        # Bouton Ouvrir navigateur
        self.browser_button = tk.Button(
            self.root,
            text="🌐 Ouvrir dans le navigateur",
            font=("Segoe UI", 10),
            bg="#4a4a5e",
            fg="#e0e0e0",
            activebackground="#5a5a6e",
            activeforeground="#e0e0e0",
            relief=tk.FLAT,
            cursor="hand2",
            state=tk.DISABLED,
            command=self._open_browser
        )
        self.browser_button.pack(fill=tk.X, padx=20, pady=(5, 20))
    
    def _check_server_on_startup(self):
        """Vérifie si un serveur tourne déjà au démarrage"""
        if self._is_port_open():
            self._update_status("running", "Serveur actif — localhost:8000")
            self.toggle_button.config(text="⏹ Arrêter", bg="#e63946", activebackground="#d62828")
            self.browser_button.config(state=tk.NORMAL)
            self._log("ℹ️ Serveur déjà actif détecté au démarrage")
    
    def _is_port_open(self, host="127.0.0.1", port=8000, timeout=1):
        """Vérifie si le port est occupé"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def _update_status(self, status, text):
        """Met à jour l'indicateur de statut"""
        self.status = status
        colors = {
            "stopped": "#e63946",
            "starting": "#f4a261",
            "running": "#2dc653",
            "error": "#e63946"
        }
        self.status_indicator.itemconfig(self.status_circle, fill=colors.get(status, "#e63946"))
        self.status_label.config(text=text)
    
    def _log(self, message):
        """Ajoute un message dans la zone de logs"""
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)
    
    def _toggle_server(self):
        """Démarre ou arrête le serveur"""
        if self.status in ["stopped", "error"]:
            self._start_server()
        elif self.status == "running":
            self._stop_server()
    
    def _start_server(self):
        """Démarre le serveur uvicorn"""
        # Vérifier si port déjà occupé
        if self._is_port_open():
            self._log("⚠️ Port 8000 déjà utilisé. JARVIS est peut-être déjà actif.")
            response = messagebox.askyesno(
                "Port occupé",
                "Le port 8000 est déjà utilisé.\nJARVIS est peut-être déjà actif.\n\nOuvrir quand même le navigateur ?"
            )
            if response:
                self._open_browser()
            return
        
        self._update_status("starting", "Démarrage...")
        self.toggle_button.config(state=tk.DISABLED)
        self._log("🚀 Démarrage du serveur JARVIS...")
        
        # Lancer uvicorn
        try:
            self.process = subprocess.Popen(
                ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"],
                cwd=str(self.jarvis_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Thread pour lire les logs
            self.log_thread = threading.Thread(target=self._read_logs, daemon=True)
            self.log_thread.start()
            
            # Thread pour vérifier le démarrage
            threading.Thread(target=self._wait_for_server, daemon=True).start()
            
        except Exception as e:
            self._log(f"❌ Erreur au démarrage : {e}")
            self._update_status("error", "Erreur — voir les logs")
            self.toggle_button.config(state=tk.NORMAL)
    
    def _read_logs(self):
        """Lit les logs du processus uvicorn"""
        try:
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.root.after(0, self._log, line.rstrip())
                if self.process.poll() is not None:
                    break
            
            # Processus terminé
            if self.status == "running":
                self.root.after(0, self._log, "⚠️ Serveur arrêté inopinément. Clic Démarrer pour relancer.")
                self.root.after(0, self._update_status, "error", "Erreur — serveur arrêté")
                self.root.after(0, lambda: self.toggle_button.config(
                    text="▶ Démarrer",
                    bg="#00b4d8",
                    activebackground="#0096c7",
                    state=tk.NORMAL
                ))
                self.root.after(0, lambda: self.browser_button.config(state=tk.DISABLED))
        except Exception as e:
            self.root.after(0, self._log, f"❌ Erreur lecture logs : {e}")
    
    def _wait_for_server(self):
        """Attend que le serveur réponde"""
        max_wait = 8  # 8 secondes max
        waited = 0
        
        while waited < max_wait:
            time.sleep(1)
            waited += 1
            
            try:
                response = requests.get("http://localhost:8000/docs", timeout=2)
                if response.status_code == 200:
                    # Serveur actif
                    self.root.after(0, self._update_status, "running", "Serveur actif — localhost:8000")
                    self.root.after(0, lambda: self.toggle_button.config(
                        text="⏹ Arrêter",
                        bg="#e63946",
                        activebackground="#d62828",
                        state=tk.NORMAL
                    ))
                    self.root.after(0, lambda: self.browser_button.config(state=tk.NORMAL))
                    self.root.after(0, self._log, "✅ Serveur actif — ouverture du navigateur...")
                    self.root.after(0, self._open_browser)
                    return
            except:
                pass
        
        # Timeout
        self.root.after(0, self._log, "⚠️ Le serveur ne répond pas après 8 secondes. Vérifiez les logs.")
        self.root.after(0, self._update_status, "error", "Erreur — voir les logs")
        self.root.after(0, lambda: self.toggle_button.config(state=tk.NORMAL))
    
    def _stop_server(self):
        """Arrête le serveur uvicorn"""
        if self.process:
            self._log("🛑 Arrêt du serveur...")
            self.toggle_button.config(state=tk.DISABLED)
            
            try:
                self.process.terminate()
                
                # Attendre jusqu'à 5 secondes
                for _ in range(50):
                    if not self._is_port_open():
                        break
                    time.sleep(0.1)
                
                self.process = None
                self._update_status("stopped", "Serveur arrêté")
                self.toggle_button.config(
                    text="▶ Démarrer",
                    bg="#00b4d8",
                    activebackground="#0096c7",
                    state=tk.NORMAL
                )
                self.browser_button.config(state=tk.DISABLED)
                self._log("✅ Serveur arrêté")
                
            except Exception as e:
                self._log(f"❌ Erreur à l'arrêt : {e}")
                self.toggle_button.config(state=tk.NORMAL)
    
    def _open_browser(self):
        """Ouvre le navigateur sur localhost:8000"""
        webbrowser.open("http://localhost:8000")
        self._log("🌐 Navigateur ouvert")
    
    def _on_close(self):
        """Gère la fermeture de la fenêtre"""
        if self.status == "running":
            response = messagebox.askyesnocancel(
                "JARVIS actif",
                "JARVIS est actif. Arrêter le serveur avant de quitter ?"
            )
            if response is True:
                # Oui : arrêter puis fermer
                self._stop_server()
                time.sleep(1)
                self.root.destroy()
            elif response is False:
                # Non : garder ouvert
                return
            # Cancel : ne rien faire
        else:
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = JarvisLauncher(root)
    root.mainloop()
