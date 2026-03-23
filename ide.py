import customtkinter as ctk
import subprocess
import os
import serial
import threading
import webbrowser
import time
from serial.tools import list_ports

# --- IDENTIDADE VISUAL ---
AUTHOR = "Default"
APP_NAME = "University IDE"
VERSION = "1.2.5"
SITE_OFICIAL = "https://github.com/seu-usuario/university-ide" # Coloca seu link aqui depois

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLI_PATH = os.path.normcase(os.path.join(BASE_DIR, "bin", "arduino-cli.exe"))
SKETCH_DIR = os.path.normcase(os.path.join(BASE_DIR, "sketch_temp"))

class UniversityIDE(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} | Research & Development")
        self.geometry("1100x800")
        
        # Config de cores (Vibe Dark Academic)
        ctk.set_appearance_mode("dark")
        
        self.serial_obj = None
        self.lendo_serial = False

        # Grid System
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # SIDEBAR
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=3, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="UNIVERSITY", font=("Impact", 32)).pack(pady=(20, 0))
        ctk.CTkLabel(self.sidebar, text="V I R T U A L  L A B", font=("Arial", 10)).pack(pady=(0, 30))
        
        # Hardware
        ctk.CTkLabel(self.sidebar, text="BOARD SELECT:", font=("Arial", 12, "bold")).pack(anchor="w", padx=25)
        self.placa_var = ctk.StringVar(value="esp32:esp32:esp32")
        self.combo_placa = ctk.CTkComboBox(self.sidebar, values=["esp32:esp32:esp32", "arduino:avr:uno"], variable=self.placa_var, width=190)
        self.combo_placa.pack(pady=10)

        ctk.CTkLabel(self.sidebar, text="SERIAL PORT:", font=("Arial", 12, "bold")).pack(anchor="w", padx=25)
        self.porta_var = ctk.StringVar(value="Scan Ports...")
        self.combo_porta = ctk.CTkComboBox(self.sidebar, variable=self.porta_var, values=self.listar_portas(), width=190)
        self.combo_porta.pack(pady=10)
        
        ctk.CTkButton(self.sidebar, text="Refresh Hardware", command=self.atualizar_portas, fg_color="#3d3d3d").pack(pady=10)

        # Tools
        self.btn_serial = ctk.CTkButton(self.sidebar, text="Terminal Monitor", command=self.toggle_serial, fg_color="#2980b9")
        self.btn_serial.pack(pady=15, padx=25, fill="x")

        ctk.CTkButton(self.sidebar, text="Clear Console", command=self.limpar_console, fg_color="#c0392b").pack(pady=5, padx=25, fill="x")

        # Footer
        ctk.CTkButton(self.sidebar, text="Get Updates", command=lambda: webbrowser.open(SITE_OFICIAL), fg_color="transparent", text_color="gray").pack(side="bottom", pady=20)

        # EDITOR
        self.editor = ctk.CTkTextbox(self, font=("Consolas", 16), fg_color="#121212", text_color="#e0e0e0")
        self.editor.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.editor.insert("0.0", "// University IDE - Initializing...\n\nvoid setup() {\n  Serial.begin(115200);\n}\n\nvoid loop() {\n  \n}")

        # CONSOLE
        self.console = ctk.CTkTextbox(self, height=200, fg_color="#000", text_color="#00FF00", font=("Consolas", 12))
        self.console.grid(row=1, column=1, padx=20, pady=(0, 20), sticky="nsew")

        # EXECUTE BUTTON
        self.btn_flash = ctk.CTkButton(self, text="⚡ COMPILE & INJECT", command=self.executar_flash, 
                                       fg_color="#27ae60", hover_color="#2ecc71", height=50, font=("Arial", 16, "bold"))
        self.btn_flash.grid(row=2, column=1, pady=(0, 20))

    def log(self, msg):
        self.console.insert("end", f"\n[{time.strftime('%H:%M:%S')}] {msg}")
        self.console.see("end")

    def limpar_console(self):
        self.console.delete("0.0", "end")
        self.log("Console cleared.")

    def listar_portas(self):
        return [p.device for p in list_ports.comports()] or ["No Device Found"]

    def atualizar_portas(self):
        portas = self.listar_portas()
        self.combo_porta.configure(values=portas)
        self.log(f"Scan complete. Devices: {portas}")

    def toggle_serial(self):
        if not self.lendo_serial:
            try:
                porta = self.porta_var.get()
                self.serial_obj = serial.Serial(porta, 115200, timeout=0.1)
                self.lendo_serial = True
                self.btn_serial.configure(text="Disconnect", fg_color="#e67e22")
                threading.Thread(target=self.thread_leitura, daemon=True).start()
                self.log(f"Linked to {porta}")
            except Exception as e:
                self.log(f"Link failed: {e}")
        else:
            self.lendo_serial = False
            if self.serial_obj: self.serial_obj.close()
            self.btn_serial.configure(text="Terminal Monitor", fg_color="#2980b9")
            self.log("Link closed.")

    def thread_leitura(self):
        while self.lendo_serial:
            if self.serial_obj and self.serial_obj.in_waiting:
                texto = self.serial_obj.read(self.serial_obj.in_waiting).decode('utf-8', errors='ignore')
                self.console.insert("end", texto)
                self.console.see("end")

    def executar_flash(self):
        if not os.path.exists(CLI_PATH):
            self.log("Engine missing in /bin/ folder.")
            return

        if not os.path.exists(SKETCH_DIR): os.makedirs(SKETCH_DIR)
        with open(os.path.join(SKETCH_DIR, "sketch_temp.ino"), "w") as f:
            f.write(self.editor.get("0.0", "end"))
        
        porta = self.porta_var.get()
        placa = self.placa_var.get()
        
        self.log(f"Building payload for {placa}...")
        if self.lendo_serial: self.toggle_serial()
        
        # O PULO DO GATO: Aspas duplas protegendo o caminho do motor e do sketch
        comando = f'"{CLI_PATH}" compile --upload --fqbn {placa} --port {porta} "{SKETCH_DIR}"'
        
        try:
            proc = subprocess.run(comando, capture_output=True, text=True, shell=True)
            if proc.returncode == 0:
                self.log("INJECTION SUCCESS.")
                self.log(proc.stdout)
            else:
                self.log(f"INJECTION FAILED:\n{proc.stderr}")
        except Exception as e:
            self.log(f"System Error: {e}")

if __name__ == "__main__":
    app = UniversityIDE()
    app.mainloop()