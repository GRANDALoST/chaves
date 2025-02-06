import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import os
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
import requests

# Configurações do backend
BACKEND_URL = "https://image-cropper-api-xynb.onrender.com"

class SplashScreen:
    def __init__(self, root):
        self.root = root
        self.splash = tk.Toplevel()
        self.splash.overrideredirect(True)
        self.splash.attributes("-topmost", True)  # Mantém a splash screen no topo
        # Centraliza a splash screen
        w = 400
        h = 300
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        x = (ws / 2) - (w / 2)
        y = (hs / 2) - (h / 2)
        self.splash.geometry(f'{w}x{h}+{int(x)}+{int(y)}')
        # Configuração do fundo
        self.splash.configure(bg='#2c3e50')
        # Logo ASCII
        self.ascii_art = """⠀⠀⠀⠀⣀⣠⣤⣤⣤⣤⣄⣀⠀⠀⠀⠀⠀
⠀⢀⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⡀⠀⠀
⠀⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⢿⣿⣷⡀⠀
⣸⣿⣿⣿⣿⣿⣿⣿⣿⠟⠁⠀⣴⢿⣿⣧⠀
⣿⣿⣿⣿⣿⡿⠛⣩⠍⠀⠀⠀⠐⠉⢠⣿⣿⡇
⣿⡿⠛⠋⠉⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⣿⣿⣿
⢹⣿⣤⠄⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⣿⣿⣿⡏
⠀⠻⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⢿⣿⣿⣿⣿⠟⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⠟⠁⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"""
        self.logo_label = tk.Label(
            self.splash,
            text=self.ascii_art,
            font=('Courier', 8),
            bg='#2c3e50',
            fg='white'
        )
        self.logo_label.pack(pady=20)
        # Título
        self.title_label = tk.Label(
            self.splash,
            text="Desenvolvido por TH.CPR - Lobo do HOT",
            font=('Arial', 12, 'bold'),
            bg='#2c3e50',
            fg='white'
        )
        self.title_label.pack(pady=10)
        # Barra de progresso
        self.progress = ttk.Progressbar(
            self.splash,
            length=300,
            mode='determinate'
        )
        self.progress.pack(pady=20)
        self.update_progress()

    def update_progress(self, i=0):
        if i < 100:
            self.progress['value'] = i
            self.splash.update()
            self.splash.after(30, lambda: self.update_progress(i + 1))
        else:
            self.splash.destroy()


class ImageCropper:
    def __init__(self, root):
        self.root = root
        self.root.title("Cortador de Imagens em Massa")
        self.root.configure(bg='#2c3e50')
        # Variáveis de controle
        self.images = []
        self.current_batch = []
        self.current_image_index = 0
        self.batches = defaultdict(list)
        self.crop_rect = None
        self.crop_start = None
        self.output_dir = os.path.join(os.path.expanduser("~"), "Desktop", "Imagens_Cortadas")
        self.setup_ui()
        self.bind_shortcuts()

    def setup_ui(self):
        # Frame principal
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(expand=True, fill='both', padx=10, pady=10)
        # Menu de configurações no canto superior direito
        self.settings_button = ttk.Button(
            self.main_frame,
            text="⚙️ Configurações",
            command=self.open_settings
        )
        self.settings_button.pack(side='right', padx=5, pady=5)
        # Botões superiores
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill='x', pady=5)
        self.load_button = ttk.Button(
            self.button_frame,
            text="Carregar Imagens (Ctrl+O)",
            command=self.load_images
        )
        self.load_button.pack(side='left', padx=5)
        self.crop_button = ttk.Button(
            self.button_frame,
            text="Aplicar Corte no Lote (Ctrl+C)",
            command=self.process_all_batches
        )
        self.crop_button.pack(side='left', padx=5)
        # Canvas para exibição da imagem
        self.canvas_frame = ttk.Frame(self.main_frame)
        self.canvas_frame.pack(expand=True, fill='both')
        self.canvas = tk.Canvas(
            self.canvas_frame,
            bg='#1a252f',
            width=800,
            height=600,
            highlightthickness=0
        )
        self.canvas.pack(expand=True, fill='both')
        # Barra de progresso
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.main_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(fill='x', pady=5)
        # Status
        self.status_label = ttk.Label(
            self.main_frame,
            text="Nenhuma imagem carregada"
        )
        self.status_label.pack(pady=5)
        # Logo no canto inferior
        self.logo_frame = ttk.Frame(self.main_frame)
        self.logo_frame.pack(fill='x', side='bottom')
        self.logo_label = tk.Label(
            self.logo_frame,
            text="LOBO DO HOT",
            font=('Arial', 8, 'bold'),
            bg='#2c3e50',
            fg='white'
        )
        self.logo_label.pack(side='left')

    def bind_shortcuts(self):
        self.root.bind('<Control-o>', lambda e: self.load_images())
        self.root.bind('<Control-c>', lambda e: self.process_all_batches())

    def open_settings(self):
        settings_window = tk.Toplevel()
        settings_window.title("Configurações")
        settings_window.geometry("400x200")
        settings_window.resizable(False, False)
        tk.Label(settings_window, text="Diretório de Saída:").pack(pady=10)
        output_dir_entry = tk.Entry(settings_window, width=50)
        output_dir_entry.insert(0, self.output_dir)
        output_dir_entry.pack(pady=5)

        def save_settings():
            new_output_dir = output_dir_entry.get().strip()
            if os.path.isdir(new_output_dir):
                self.output_dir = new_output_dir
                messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!")
                settings_window.destroy()
            else:
                messagebox.showerror("Erro", "Diretório inválido!")

        tk.Button(settings_window, text="Salvar", command=save_settings).pack(pady=10)

    def load_images(self):
        file_paths = filedialog.askopenfilenames(
            filetypes=[
                ("Imagens", "*.jpg *.jpeg *.png")
            ]
        )
        if not file_paths:
            return
        self.images = []
        self.batches.clear()
        for path in file_paths:
            try:
                img = Image.open(path)
                self.batches[(img.width, img.height)].append((path, img))
                self.images.append((path, img))
            except Exception as e:
                messagebox.showerror(
                    "Erro",
                    f"Erro ao carregar {path}: {str(e)}"
                )
        if self.images:
            self.current_batch = list(self.batches.values())[0]
            self.display_current_image()
            self.status_label.config(
                text=f"Carregadas {len(self.images)} imagens em {len(self.batches)} lotes"
            )

    def display_current_image(self):
        if not self.current_batch:
            return
        path, img = self.current_batch[self.current_image_index]
        # Redimensiona a imagem para caber no canvas
        display_size = (800, 600)
        img_aspect = img.width / img.height
        canvas_aspect = display_size[0] / display_size[1]
        if img_aspect > canvas_aspect:
            new_width = display_size[0]
            new_height = int(display_size[0] / img_aspect)
        else:
            new_height = display_size[1]
            new_width = int(display_size[1] * img_aspect)
        self.display_image = img.resize((new_width, new_height))
        self.photo = ImageTk.PhotoImage(self.display_image)
        self.canvas.delete("all")
        self.canvas.create_image(
            display_size[0] // 2,
            display_size[1] // 2,
            image=self.photo,
            anchor='center'
        )
        # Cria retângulo de corte inicial (totalmente transparente)
        margin = 50
        x1 = margin
        y1 = margin
        x2 = new_width - margin
        y2 = new_height - margin
        self.crop_rect = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline='',  # Sem borda visível
            width=0      # Largura da borda definida como 0
        )

    def get_crop_coordinates(self):
        if not self.crop_rect:
            return None
        coords = self.canvas.coords(self.crop_rect)
        return [int(c) for c in coords]

    def crop_and_save_image(self, img, coords, original_path, output_dir):
        try:
            cropped = img.crop(coords)
            filename = os.path.basename(original_path)
            base, ext = os.path.splitext(filename)
            output_path = os.path.join(output_dir, f"{base}_cropped{ext}")
            cropped.save(output_path, quality=95, optimize=True)
        except Exception as e:
            with open("error_log.txt", "a") as log_file:
                log_file.write(f"Erro ao processar {original_path}: {str(e)}\n")

    def process_batch(self, batch, batch_index, total_batches, folder_name):
        crop_coords = self.get_crop_coordinates()
        if not crop_coords:
            return
        output_dir = os.path.join(self.output_dir, folder_name)
        os.makedirs(output_dir, exist_ok=True)
        # Calcula as coordenadas relativas do corte
        display_img = batch[0][1]
        x_scale = display_img.width / self.display_image.width
        y_scale = display_img.height / self.display_image.height
        real_coords = [
            int(crop_coords[0] * x_scale),
            int(crop_coords[1] * y_scale),
            int(crop_coords[2] * x_scale),
            int(crop_coords[3] * y_scale)
        ]
        # Processa as imagens em paralelo
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for i, (path, img) in enumerate(batch):
                future = executor.submit(
                    self.crop_and_save_image,
                    img,
                    real_coords,
                    path,
                    output_dir
                )
                futures.append(future)
                # Atualiza a barra de progresso
                self.progress_var.set((i + 1) / len(batch) * 100)
                self.root.update()
            # Atualiza o status
            self.status_label.config(
                text=f"Processando lote {batch_index + 1}/{total_batches}"
            )
        return output_dir

    def process_all_batches(self):
        if not self.batches:
            messagebox.showinfo("Aviso", "Nenhuma imagem carregada")
            return
        # Solicita o nome da pasta para os recortes
        folder_name = simpledialog.askstring("Nome da Pasta", "Digite o nome da pasta para os recortes:")
        if not folder_name:
            messagebox.showerror("Erro", "Nome da pasta inválido!")
            return
        total_batches = len(self.batches)
        all_output_dirs = set()
        for batch_index, batch in enumerate(self.batches.values()):
            self.current_batch = batch
            self.current_image_index = 0
            self.display_current_image()
            output_dir = self.process_batch(batch, batch_index, total_batches, folder_name)
            all_output_dirs.add(output_dir)
        # Exibe a mensagem de conclusão com o botão "Visualizar Imagens"
        def open_folder():
            for output_dir in all_output_dirs:
                os.startfile(output_dir)

        messagebox.showinfo(
            "Concluído",
            "Todas as imagens foram processadas com sucesso!",
            parent=self.root
        )
        view_button = tk.Button(
            self.root,
            text="Visualizar Imagens",
            command=open_folder
        )
        view_button.pack(pady=10)


def validate_license_key(license_key):
    try:
        response = requests.post(
            f"{BACKEND_URL}/validate",
            json={"license_key": license_key}
        )
        if response.status_code == 200:
            return True
        return False
    except Exception as e:
        print(f"Erro ao validar chave: {e}")
        return False


def show_license_screen():
    license_window = tk.Toplevel()
    license_window.title("Ativação")
    license_window.geometry("400x200")
    license_window.resizable(False, False)
    tk.Label(license_window, text="Insira sua chave de licença:").pack(pady=10)
    license_entry = tk.Entry(license_window, width=50)
    license_entry.pack(pady=10)

    def activate():
        license_key = license_entry.get()
        if validate_license_key(license_key):
            # Cria uma nova janela temporária para exibir a mensagem
            success_window = tk.Toplevel()
            success_window.title("Sucesso")
            success_window.geometry("300x100")
            success_window.resizable(False, False)
            success_window.attributes("-topmost", True)  # Mantém a janela no topo
            tk.Label(success_window, text="Licença ativada com sucesso!").pack(pady=20)
            tk.Button(success_window, text="OK", command=lambda: [success_window.destroy(), license_window.destroy(), main_app()]).pack(pady=10)
        else:
            messagebox.showerror("Erro", "Chave de licença inválida!")

    tk.Button(license_window, text="Ativar", command=activate).pack(pady=10)


def main_app():
    global app
    app = ImageCropper(root)
    root.deiconify()  # Exibe a janela principal


def main():
    global root
    root = tk.Tk()
    root.withdraw()  # Esconde a janela principal
    # Mostra a splash screen
    splash = SplashScreen(root)
    # Após 3 segundos, mostra a tela de ativação
    root.after(3000, lambda: show_license_screen())
    root.mainloop()


if __name__ == "__main__":
    main()
