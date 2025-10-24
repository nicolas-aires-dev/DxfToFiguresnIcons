# =============================
# Imports
# =============================
import re
import shutil
from pathlib import Path
import ezdxf
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.properties import LayoutProperties
from ezdxf.addons.drawing.config import Configuration

import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading

# =============================
# Configurações de diretórios
# =============================
OUTPUT_DIR = Path("./output")
FIGURAS_DIR = OUTPUT_DIR / "figuras"
ICONES_DIR = OUTPUT_DIR / "icones"

# =============================
# Utilidades
# =============================
def carregar_dxf(path: str):
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    return doc, msp

def get_bbox(entity):
    try:
        if entity.dxftype() == "LWPOLYLINE":
            points = [(x, y) for x, y, *_ in entity.get_points()]
        else:
            points = [(x, y) for x, y, *_ in entity.points()]
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        return min(xs), min(ys), max(xs), max(ys)
    except Exception:
        return None

def ponto_no_bbox(x, y, bbox, margem=15):
    x1, y1, x2, y2 = bbox
    return (x1 - margem <= x <= x2 + margem) and (y1 - margem <= y <= y2 + margem)

def centro_bbox(bbox):
    x1, y1, x2, y2 = bbox
    return (x1 + x2) / 2, (y1 + y2) / 2

def distancia(p1, p2):
    return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**0.5

def is_quadrado(polyline):
    try:
        if polyline.dxftype() == "LWPOLYLINE":
            points = [(x, y) for x, y, *_ in polyline.get_points()]
        else:
            points = [(x, y) for x, y, *_ in polyline.points()]
        if len(points) != 4 or not polyline.closed:
            return False
        def dist(p1, p2):
            return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**0.5
        lados = [dist(points[i], points[(i + 1) % 4]) for i in range(4)]
        media = sum(lados) / 4
        return all(abs(l - media) < 1.0 for l in lados)
    except Exception:
        return False

def centralizar_em_moldura(img_path, tamanho_final=(500, 500)):
    with Image.open(img_path) as img:
        img = img.convert("RGBA")
        img.thumbnail(tamanho_final, Image.Resampling.LANCZOS)

        fundo = Image.new("RGBA", tamanho_final, (255, 255, 255, 255))
        x = (tamanho_final[0] - img.width) // 2
        y = (tamanho_final[1] - img.height) // 2

        fundo.paste(img, (x, y), img)
        fundo = fundo.convert("RGB")
        fundo.save(img_path)

def detectar_furos(msp, perfis):
    candidatos = [e for e in msp.query('LWPOLYLINE POLYLINE') if e.closed]

    for perfil in perfis:
        principal = perfil["polyline"]
        bbox_principal = get_bbox(principal)
        centro_principal = centro_bbox(bbox_principal)

        for furo in candidatos:
            if furo == principal:
                continue
            bbox_furo = get_bbox(furo)
            if not bbox_furo:
                continue
            centro_furo = centro_bbox(bbox_furo)
            if ponto_no_bbox(centro_furo[0], centro_furo[1], bbox_principal, margem=2):
                perfil["furos"].append(furo)

# =============================
# Processamento
# =============================
def filtrar_perfis(msp):
    perfis = []
    for e in msp.query('LWPOLYLINE POLYLINE'):
        if e.dxf.layer.upper() == "MOLDURA":
            continue
        perfis.append({
            "polyline": e,
            "texts": [],
            "dimensions": [],
            "furos": []
        })
    return perfis

def associar_entidades(msp, perfis):
    textos = [e for e in msp.query('TEXT MTEXT')]
    cotas = [e for e in msp.query('DIMENSION ROTATEDDIMENSION')]
    for perfil in perfis:
        bbox = get_bbox(perfil["polyline"])
        if not bbox:
            continue
        centro = centro_bbox(bbox)
        for t in textos:
            try:
                x, y, _ = t.dxf.insert
            except AttributeError:
                continue
            if ponto_no_bbox(x, y, bbox):
                conteudo = t.plain_text() if hasattr(t, "plain_text") else t.dxf.text
                perfil["texts"].append(conteudo)
        for d in cotas:
            try:
                x, y, _ = d.dxf.defpoint
            except AttributeError:
                continue
            if distancia((x, y), centro) < 100:
                perfil["dimensions"].append(d)
    return perfis

def extrair_nome(texts):
    for t in texts:
        if not re.search(r"Kg/m", t):
            return t.strip()
    return "perfil_sem_nome"

# =============================
# Renderização
# =============================
def desenhar_perfil_com_furos(ax, perfil, facecolor="#000000", edgecolor="#000000", furo_color="#FFFFFF", linewidth=1.5):
    """Desenha o perfil principal e seus furos em um eixo Matplotlib."""
    if perfil["polyline"].dxftype() == "LWPOLYLINE":
        pontos_principais = [(x, y) for x, y, *_ in perfil["polyline"].get_points()]
    else:
        pontos_principais = [(x, y) for x, y, *_ in perfil["polyline"].points()]
    
    poly_patch = patches.Polygon(pontos_principais, closed=True, facecolor=facecolor, edgecolor=edgecolor, linewidth=linewidth)
    ax.add_patch(poly_patch)

    for furo in perfil["furos"]:
        if furo.dxftype() == "LWPOLYLINE":
            pontos = [(x, y) for x, y, *_ in furo.get_points()]
        else:
            pontos = [(x, y) for x, y, *_ in furo.points()]
        
        furo_patch = patches.Polygon(pontos, closed=True, facecolor=furo_color, edgecolor=edgecolor, linewidth=1.0)
        ax.add_patch(furo_patch)

def criar_layout_temporario(doc, perfil):
    layout_name = "TEMP_LAYOUT"
    if layout_name in doc.layouts:
        doc.layouts.delete(layout_name)
    layout = doc.layouts.new(layout_name)
    for entidade in [perfil["polyline"]] + perfil["dimensions"]:
        layout.add_entity(entidade.copy())
    return layout

def render_completo_layout(layout, ax):
    ctx = RenderContext(layout.doc)
    layout_props = LayoutProperties.from_layout(layout)
    layout_props.set_colors(bg="#FFFFFF", fg="#000000")
    config = Configuration.defaults().with_changes(
        lineweight_scaling=3.0,
        min_lineweight=0.8
    )
    backend = MatplotlibBackend(ax)
    frontend = Frontend(ctx, backend, config=config)
    frontend.draw_layout(layout, finalize=True, layout_properties=layout_props)

def render_imagens(doc, perfil, nome_base):
    nome = f"{nome_base}"

    if perfil["polyline"].dxftype() == "LWPOLYLINE":
        points = [(x, y) for x, y, *_ in perfil["polyline"].get_points()]
    else:
        points = [(x, y) for x, y, *_ in perfil["polyline"].points()]
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    margem = 10

    # PNG com cotas
    fig, ax = plt.subplots(figsize=(5, 5), dpi=100)
    ax.set_facecolor("#FFFFFF")
    ax.set_axis_off()

    centro_x = (min_x + max_x) / 2
    centro_y = (min_y + max_y) / 2
    half_range = 50
    ax.set_xlim(centro_x - half_range, centro_x + half_range)
    ax.set_ylim(centro_y - half_range, centro_y + half_range)
    ax.set_aspect('equal')

    desenhar_perfil_com_furos(ax, perfil)
    layout_temp = criar_layout_temporario(doc, perfil)
    render_completo_layout(layout_temp, ax)

    path_png = FIGURAS_DIR / f"{nome}.png"
    fig.savefig(path_png, dpi=100, transparent=False)
    centralizar_em_moldura(path_png)
    plt.close(fig)

    # BMP sem cotas
    fig, ax = plt.subplots(figsize=(0.64, 0.64), dpi=100)
    ax.set_facecolor("#FFFFFF")
    ax.set_axis_off()

    desenhar_perfil_com_furos(ax, perfil)
    ax.set_xlim(min_x - margem, max_x + margem)
    ax.set_ylim(min_y - margem, max_y + margem)
    ax.set_aspect('equal')

    temp_icon_png = ICONES_DIR / f"{nome_base}_temp.png"
    fig.savefig(temp_icon_png, dpi=100, transparent=False)
    plt.close(fig)

    with Image.open(temp_icon_png) as img:
        path_bmp = ICONES_DIR / f"{nome_base}.bmp"
        img.save(path_bmp, format="BMP")
    temp_icon_png.unlink()

# =============================
# Exportação
# =============================
def iniciar_processo():
    pass

# =============================
# Função principal com caminhos
# =============================
def main_with_paths(input_path: Path, output_path: Path):
    # --- Preparação de diretórios ---
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURAS_DIR.mkdir(parents=True, exist_ok=True)
    ICONES_DIR.mkdir(parents=True, exist_ok=True)
    output_path.mkdir(parents=True, exist_ok=True)

    # --- Carregar arquivo ---
    doc, msp = carregar_dxf(input_path)

    # --- Detectar perfis ---
    perfis = filtrar_perfis(msp)
    perfis = associar_entidades(msp, perfis)
    detectar_furos(msp, perfis)

    # --- Renderizar cada perfil ---
    for perfil in perfis:
        nome = extrair_nome(perfil["texts"])
        render_imagens(doc, perfil, nome)

    # --- Inicia processo ---
    iniciar_processo()

    print(f"✅ Renderização concluída. Arquivos salvos em: {output_path}")


# =============================
# Tkinter Interface Visual
# =============================
ctk.set_appearance_mode("dark")  # ou "light"
ctk.set_default_color_theme("blue")  # opções: "blue", "green", "dark-blue"

def escolher_input():
    caminho = filedialog.askopenfilename(filetypes=[("Arquivos DXF", "*.dxf")])
    if caminho:
        input_var.set(caminho)

def escolher_output():
    caminho = filedialog.askdirectory()
    if caminho:
        output_var.set(caminho)

def rodar_processo():
    input_path = Path(input_var.get())
    output_path = Path(output_var.get() or "./output")

    if not input_path.exists():
        messagebox.showerror("Erro", "Arquivo DXF inválido.")
        return

    # Cria popup de carregamento
    popup = ctk.CTkToplevel()
    popup.title("Processando")
    popup.geometry("300x100")
    ctk.CTkLabel(popup, text="Renderização iniciada...").pack(pady=20)
    popup.grab_set()  # Bloqueia interação com a janela principal

    def processar():
        try:
            main_with_paths(input_path, output_path)
            popup.destroy()
            messagebox.showinfo("Concluído", f"Imagens geradas em: {output_path}")
        except Exception as e:
            popup.destroy()
            messagebox.showerror("Erro", str(e))

    threading.Thread(target=processar).start()



def iniciar_interface():
    global input_var, output_var

    root = ctk.CTk()
    root.title("Renderizador DXF")
    root.geometry("500x300")

    input_var = ctk.StringVar()
    output_var = ctk.StringVar()

    # Título
    ctk.CTkLabel(root, text="Renderizador de Arquivos DXF", font=("Arial", 20)).pack(pady=10)

    # Input DXF
    ctk.CTkLabel(root, text="Arquivo DXF:").pack(anchor="w", padx=20)
    frame_input = ctk.CTkFrame(root)
    frame_input.pack(fill="x", padx=20, pady=5)
    ctk.CTkEntry(frame_input, textvariable=input_var, width=350).pack(side="left", fill="x", expand=True, padx=5)
    ctk.CTkButton(frame_input, text="Selecionar", command=escolher_input).pack(side="right", padx=5)

    # Output
    ctk.CTkLabel(root, text="Diretório de saída:").pack(anchor="w", padx=20)
    frame_output = ctk.CTkFrame(root)
    frame_output.pack(fill="x", padx=20, pady=5)
    ctk.CTkEntry(frame_output, textvariable=output_var, width=350).pack(side="left", fill="x", expand=True, padx=5)
    ctk.CTkButton(frame_output, text="Selecionar", command=escolher_output).pack(side="right", padx=5)

    # Executar
    ctk.CTkButton(root, text="Executar", command=rodar_processo, fg_color="#1f6aa5", hover_color="#144e75").pack(pady=20)

    root.mainloop()


# =============================
# Execução principal (interface)
# =============================
if __name__ == "__main__":
    iniciar_interface()