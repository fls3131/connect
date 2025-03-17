import tkinter as tk
from tkinter import messagebox, filedialog, Menu, ttk
import subprocess
import os
import threading
import speedtest
import time
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem, Icon
import base64

class OpenVPNClient:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenVPN Client 0.02")
        self.root.geometry("400x300")
        self.process = None
        self.is_vpn_connected = False

        # Variáveis para o estado da internet
        self.internet_status = False

        # Check se o usuário pode executar sudo sem senha
        if not self.check_sudo():
            messagebox.showerror("Permission Denied", "Este aplicativo requer privilégios de sudo. Execute como um usuário autorizado.")
            self.root.quit()
            return

        # Carregar o último caminho de arquivo OVPN
        self.ovpn_file_path = self.load_last_config()

        # Criar menu
        self.create_menu()

        # Elementos da interface
        self.label = tk.Label(root, text="Selecione o arquivo de configuração OpenVPN:")
        self.label.pack(pady=10)

        self.file_button = tk.Button(root, text="Procurar", command=self.browse_file)
        self.file_button.pack(pady=10)

        self.connect_button = tk.Button(root, text="Conectar", command=self.connect_vpn, state=tk.DISABLED)
        self.connect_button.pack(pady=10)

        self.disconnect_button = tk.Button(root, text="Desconectar", command=self.disconnect_vpn, state=tk.DISABLED)
        self.disconnect_button.pack(pady=10)

        self.speedtest_button = tk.Button(root, text="Testar Velocidade", command=self.open_speed_test_window)
        self.speedtest_button.pack(pady=10)

        self.exit_button = tk.Button(root, text="Sair", command=self.root.quit)
        self.exit_button.pack(pady=10)

        # Preencher caminho do arquivo, se disponível
        if self.ovpn_file_path:
            messagebox.showinfo("Configuração Anteriormente Usada", f"Configuração anterior carregada: {self.ovpn_file_path}")
            self.connect_button.config(state=tk.NORMAL)

        # Iniciar monitoramento em uma thread separada
        threading.Thread(target=self.monitor_status, daemon=True).start()

        # Inicializar ícone na bandeja do sistema
        self.icon = Icon("OpenVPN Client", self.create_image(color='blue'))
        self.icon.menu = self.create_systray_menu()
        threading.Thread(target=self.icon.run, daemon=True).start()

    def create_menu(self):
        menu_bar = Menu(self.root)

        programs_menu = Menu(menu_bar, tearoff=0)
        programs_menu.add_command(label="Testar Velocidade", command=self.open_speed_test_window)
        programs_menu.add_command(label="Executar net.py", command=self.run_net_script)
        programs_menu.add_separator()
        programs_menu.add_command(label="Sobre", command=self.show_about_window)
        menu_bar.add_cascade(label="Programas", menu=programs_menu)

        self.root.config(menu=menu_bar)

    def check_sudo(self):
        try:
            subprocess.run(['sudo', '-v'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError:
            return False

    def load_last_config(self):
        try:
            with open("last_config.txt", "r") as f:
                # Decode the base64 encoded path
                encoded_path = f.readline().strip()
                decoded_path = base64.b64decode(encoded_path).decode('utf-8')
                return decoded_path if os.path.exists(decoded_path) else None
        except (FileNotFoundError, ValueError):
            return None

    def save_last_config(self):
        if self.ovpn_file_path:
            encoded_path = base64.b64encode(self.ovpn_file_path.encode('utf-8')).decode('utf-8')
            with open("last_config.txt", "w") as f:
                f.write(encoded_path)

    def browse_file(self):
        self.ovpn_file_path = filedialog.askopenfilename(
            title="Selecione a configuração OpenVPN (.ovpn)",
            filetypes=[("Arquivos OpenVPN", "*.ovpn")]
        )
        if self.ovpn_file_path:
            self.connect_button.config(state=tk.NORMAL)
            messagebox.showinfo("Arquivo Selecionado", f"Selecionado: {self.ovpn_file_path}")
            self.save_last_config()

    def connect_vpn(self):
        if not self.ovpn_file_path:
            messagebox.showwarning("Nenhum Arquivo", "Por favor, selecione um arquivo .ovpn.")
            return

        self.process = subprocess.Popen(
            ["sudo", "openvpn", "--config", self.ovpn_file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            text=True
        )
        
        self.is_vpn_connected = True
        self.connect_button.config(state=tk.DISABLED)
        self.disconnect_button.config(state=tk.NORMAL)
        self.exit_button.config(state=tk.DISABLED)  # Desabilita o botão de sair

        threading.Thread(target=self.read_output).start()

    def read_output(self):
        while True:
            output = self.process.stdout.readline()
            if output == '' and self.process.poll() is not None:
                break
            if output:
                print(output.strip())

        self.disconnect_vpn()

    def disconnect_vpn(self):
        if self.process:
            self.process.terminate()
            self.process = None
            
        self.is_vpn_connected = False
        self.connect_button.config(state=tk.NORMAL)
        self.disconnect_button.config(state=tk.DISABLED)
        self.exit_button.config(state=tk.NORMAL)  # Habilita o botão de sair
        messagebox.showinfo("Desconectado", "Você foi desconectado da VPN.")

    def open_speed_test_window(self):
        speed_test_window = tk.Toplevel(self.root)
        speed_test_app = SpeedTestApp(speed_test_window)

    def run_net_script(self):
        try:
            subprocess.Popen(["python3", "net.py"])
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível executar o script net.py.\n{str(e)}")

    def show_about_window(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("Sobre")
        about_window.geometry("400x200")

        about_text = (
            "OpenVPN Client 0.3\n"
            "Desenvolvido por:\n"
            "Fabio Lipel Schmit\n"
            "Hostmaster@bithostel.com.br\n"
            "Bithostel TI - https://bithostel.com.br"
        )

        label = tk.Label(about_window, text=about_text, justify=tk.LEFT, padx=10, pady=10)
        label.pack()

        close_button = tk.Button(about_window, text="Fechar", command=about_window.destroy)
        close_button.pack(pady=10)

    def create_image(self, color='blue'):
        # Criar um quadrado preenchido com a cor fornecida
        size = (16, 16)
        image = Image.new("RGB", size, "white")
        draw = ImageDraw.Draw(image)

        # Desenhar um quadrado da cor especificada
        draw.rectangle([0, 0, size[0], size[1]], fill=color)

        return image

    def create_systray_menu(self):
        return (MenuItem('Sair', self.quit_application),)

    def quit_application(self, icon):
        self.icon.stop()
        self.root.destroy()

    def monitor_status(self):
        while True:
            # Verificar status da internet
            self.check_internet()
            # Atualizar o ícone na bandeja com os status
            self.update_icon()
            time.sleep(5)  # Verificar a cada 5 segundos

    def check_internet(self):
        try:
            # Teste de conexão ao Google
            subprocess.run(["ping", "-c", "1", "google.com"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.internet_status = True
        except Exception:
            self.internet_status = False

    def update_icon(self):
        # Atualizar o ícone na bandeja com base no estado da VPN
        if self.is_vpn_connected:
            self.icon.icon = self.create_image(color='green')  # Cor verde quando conectado
        else:
            self.icon.icon = self.create_image(color='blue')  # Cor azul quando desconectado


# Aplicativo de teste de velocidade
class SpeedTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Teste de Velocidade da Internet")

        # Criar um Frame
        self.frame = tk.Frame(self.root)
        self.frame.pack(pady=20)

        # Criar um label para instruções
        self.label = tk.Label(self.frame, text="Clique no botão para testar a velocidade da internet.")
        self.label.pack(pady=10)

        # Criar um botão para iniciar o teste de velocidade
        self.start_button = tk.Button(self.frame, text="Iniciar Teste de Velocidade", command=self.start_test)
        self.start_button.pack(pady=10)

        # Criar uma barra de progresso
        self.progress = ttk.Progressbar(self.frame, orient="horizontal", mode="determinate", length=300)
        self.progress.pack(pady=10)

        # Criar label para resultados
        self.result_label = tk.Label(self.frame, text="")
        self.result_label.pack(pady=10)

    def start_test(self):
        # Desativar o botão de início para evitar múltiplos cliques
        self.start_button.config(state=tk.DISABLED)

        # Iniciar a barra de progresso
        self.progress.config(mode="indeterminate")
        self.progress.start()

        # Executar o teste de velocidade em uma thread separada
        thread = threading.Thread(target=self.run_speed_test)
        thread.start()

    def run_speed_test(self):
        # Criar um objeto Speedtest
        st = speedtest.Speedtest()

        # Simular progresso do teste de download
        for _ in range(10):  # Simular como se fossem 10 etapas (10% para cada iteração)
            time.sleep(0.5)  # Simular algum tempo gasto para cada parte do download
            self.root.after(0, self.progress.step, 10)  # Atualizar a barra de progresso

        # Realizar o teste de download real
        download_speed = st.download() / (10**6)  # Converter para Mbps

        # Simular progresso do teste de upload
        for _ in range(10):  # Simular como se fossem 10 etapas (10% para cada iteração)
            time.sleep(0.5)  # Simular algum tempo gasto para cada parte do upload
            self.root.after(0, self.progress.step, 10)  # Atualizar a barra de progresso

        # Realizar o teste de upload real
        upload_speed = st.upload() / (10**6)  # Converter para Mbps

        # Parar a barra de progresso
        self.progress.stop()

        # Atualizar o label de resultado e reabilitar o botão
        self.result_label.config(text=f"Velocidade de Download: {download_speed:.2f} Mbps\n"
                                       f"Velocidade de Upload: {upload_speed:.2f} Mbps")
        self.start_button.config(state=tk.NORMAL)


# Executar a aplicação
if __name__ == "__main__":
    root = tk.Tk()
    app = OpenVPNClient(root)
    root.mainloop()
