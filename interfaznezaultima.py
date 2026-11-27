'''CREATE DATABASE CRUD;
USE CRUD;

CREATE TABLE grupos (
    Id_grupo INT AUTO_INCREMENT PRIMARY KEY,
    Nombre VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE usuarios (
    Id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    Usuario VARCHAR(50) NOT NULL UNIQUE,
    Contrasena VARCHAR(255) NOT NULL,
    Rol VARCHAR(20) NOT NULL,
    Estado VARCHAR(20) NOT NULL
);

CREATE TABLE directores (
    Id_director INT AUTO_INCREMENT PRIMARY KEY,
    Id_usuario INT NOT NULL,
    Nombre VARCHAR(40),
    Apellido VARCHAR(40),
    FOREIGN KEY (id_usuario)
    REFERENCES usuarios(id_usuario)
);

CREATE TABLE docentes (
    Id_docente INT AUTO_INCREMENT PRIMARY KEY,
    Id_usuario INT NOT NULL,
    Nombre VARCHAR(40),
    Apellido VARCHAR(40),
    Id_grupo INT NULL,
    FOREIGN KEY (id_usuario)
    REFERENCES usuarios(id_usuario),
    FOREIGN KEY (id_grupo)
    REFERENCES grupos(id_grupo)
);

CREATE TABLE alumnos (
    Id_alumno INT AUTO_INCREMENT PRIMARY KEY,
    Matricula VARCHAR(30) NOT NULL UNIQUE,
    Nombre VARCHAR(40),
    Apellido VARCHAR(40),
    Id_grupo INT NOT NULL,
    Fecha_ingreso DATE NOT NULL,
    Estado VARCHAR(20) NOT NULL,
    FOREIGN KEY (id_grupo)
    REFERENCES grupos(id_grupo)
);

CREATE TABLE asistencias (
    Id_asistencia INT AUTO_INCREMENT PRIMARY KEY,
    Id_alumno INT NOT NULL,
    Fecha DATE NOT NULL,
    Estado VARCHAR(12) NOT NULL,
    UNIQUE KEY uq_asistencia_alumno_fecha (id_alumno, fecha),
    FOREIGN KEY (id_alumno)
    REFERENCES alumnos(id_alumno)
);

CREATE TABLE calificaciones (
    Id_calificacion INT AUTO_INCREMENT PRIMARY KEY,
    Id_alumno INT NOT NULL,
    Calificacion DECIMAL(4,2) NOT NULL,
    Fecha DATE NOT NULL,
    FOREIGN KEY (id_alumno)
    REFERENCES alumnos(id_alumno)
);

CREATE TABLE justificantes (
    Id_justificante INT AUTO_INCREMENT PRIMARY KEY,
    Id_alumno INT NOT NULL,
    Fecha DATE NOT NULL,
    Motivo VARCHAR(255) NOT NULL,
    FOREIGN KEY (id_alumno)
    REFERENCES alumnos(id_alumno)
);


CREATE TABLE reportes (
    Id_reporte INT AUTO_INCREMENT PRIMARY KEY,
    Id_alumno INT NOT NULL,
    Fecha DATE NOT NULL,
    Nivel VARCHAR(20) NOT NULL,
    Descripcion VARCHAR(255) NOT NULL,
    Registrado_por VARCHAR(30) NOT NULL,
    FOREIGN KEY (id_alumno)
    REFERENCES alumnos(id_alumno)
);

CREATE TABLE inscripciones (
    Id_inscripcion INT AUTO_INCREMENT PRIMARY KEY,
    Id_alumno INT NOT NULL,
    Ciclo_escolar VARCHAR(20) NOT NULL,
    Fecha_inscripcion DATE NOT NULL,
    FOREIGN KEY (id_alumno)
    REFERENCES alumnos(id_alumno)
); '''



import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from datetime import date, timedelta
import csv
import hashlib
import secrets
import hmac
import mysql.connector
from mysql.connector import Error

COLOR_FONDO = "#0B1726"
COLOR_PANEL = "#FFFFFF"
COLOR_AZUL = "#171C5D"
COLOR_AZUL_OSCURO = "#10243A"
COLOR_DORADO = "#B8D8F0"
COLOR_TEXTO = "#203449"
COLOR_SUAVE = "#667085"
COLOR_VERDE = "#2E7D32"
COLOR_ROJO = "#B71C1C"
COLOR_AMARILLO = "#DCEAF5"

FUENTE_TITULO = "Times New Roman"
FUENTE_TEXTO = "Arial"

ANCHO_INICIAL = 1050
ALTO_INICIAL = 760

ventana = tk.Tk()
ventana.title("SAT NEZA HQX - Sistema de Control Escolar")
ventana.geometry(f"{ANCHO_INICIAL}x{ALTO_INICIAL}")
ventana.minsize(640, 480)
ventana.configure(bg=COLOR_FONDO)

#SERGIO HIZO MODIFICACIÓN DE LOGIN DE USUARIOS

# En Windows abre maximizada; en otros sistemas usa casi toda la pantalla.
try:
    ventana.state("zoomed")
except tk.TclError:
    ancho = ventana.winfo_screenwidth()
    alto = ventana.winfo_screenheight()
    ventana.geometry(f"{int(ancho * 0.92)}x{int(alto * 0.88)}")


def crear_contenedor_con_scroll(parent, color_fondo=COLOR_FONDO):
    """Crea un contenedor vertical desplazable que se adapta al tamaño de la ventana."""
    canvas = tk.Canvas(parent, bg=color_fondo, highlightthickness=0)
    scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    marco = tk.Frame(canvas, bg=color_fondo)
    ventana_canvas = canvas.create_window((0, 0), window=marco, anchor="nw")

    def actualizar_ancho(evento):
        canvas.itemconfigure(ventana_canvas, width=evento.width)

    def actualizar_scroll(_evento=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def desplazar(evento):
        canvas.yview_scroll(-1 if evento.delta > 0 else 1, "units")

    canvas.bind("<Configure>", actualizar_ancho)
    marco.bind("<Configure>", actualizar_scroll)
    canvas.bind_all("<MouseWheel>", desplazar)
    return marco


def crear_hash(clave):
    """Protege una contraseña nueva sin cambiar la estructura de MySQL."""
    sal = secrets.token_hex(16)
    rondas = 200000
    resultado = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), sal.encode("utf-8"), rondas).hex()
    return f"pbkdf2${rondas}${sal}${resultado}"


def comprobar_clave(clave, guardada):
    """Acepta cuentas antiguas y las nuevas contraseñas protegidas."""
    if guardada.startswith("pbkdf2$"):
        try:
            _, rondas, sal, esperado = guardada.split("$", 3)
            calculado = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), sal.encode("utf-8"), int(rondas)).hex()
            return hmac.compare_digest(calculado, esperado)
        except (ValueError, TypeError):
            return False
    return hmac.compare_digest(clave, guardada)


def limpiar_ventana():
    """Elimina los widgets de la vista actual antes de abrir otra."""
    for widget in ventana.winfo_children():
        widget.destroy()


def crear_boton(parent, texto, comando, color=COLOR_AZUL):
    """Crea botones con el estilo general y tamaño adaptable."""
    return tk.Button(
        parent,
        text=texto,
        command=comando,
        bg=color,
        fg="white",
        activebackground=COLOR_DORADO,
        activeforeground="white",
        font=(FUENTE_TEXTO, 11, "bold"),
        relief="flat",
        padx=10,
        pady=7,
        cursor="hand2"
    )


def crear_titulo(parent, texto, color_fondo=COLOR_FONDO):
    """Muestra un título centrado."""
    return tk.Label(
        parent,
        text=texto,
        font=(FUENTE_TITULO, 20, "bold"),
        bg=color_fondo,
        fg="white"
    )


def crear_etiqueta(parent, texto, tamano=11, color_fondo=COLOR_FONDO,
                   color_texto="white", negrita=False):
    """Crea una etiqueta de texto con el estilo general."""
    estilo = "bold" if negrita else "normal"
    return tk.Label(
        parent,
        text=texto,
        font=(FUENTE_TEXTO, tamano, estilo),
        bg=color_fondo,
        fg=color_texto
    )


def crear_campo(parent, ancho=30, ocultar=False):
    """Crea un campo de entrada adaptable."""
    campo = tk.Entry(
        parent,
        width=ancho,
        font=(FUENTE_TEXTO, 12),
        relief="solid",
        bd=1
    )
    if ocultar:
        campo.configure(show="*")
    return campo


def crear_alumno(nombre):
    """Devuelve la estructura inicial para un alumno nuevo."""
    return {
        "nombre": nombre,
        "asistencia": {},
        "calificaciones": [],
        "justificantes": [],
        "conducta": []
    }


# CONFIGURACIÓN DE MYSQL: cambia estos datos si tu instalación es diferente.
CONFIG_BD = {
    "host": "localhost",
    "user": "root",
    "password": "",       # Escribe aquí tu contraseña de MySQL si tienes una.
    "database": "crud"
}

import mysql.connector

try:
    conexion = mysql.connector.connect(**CONFIG_BD)

    if conexion.is_connected():
        print("¡Conexion exitosa con MySQL!")

    conexion.close()

except mysql.connector.Error as error:
    print("Error de conexion:", error)
    
grupo_actual = "1A"
fecha_seleccionada = date.today()
grupos = {}


def conectar_bd():
    """Conecta el programa con la base de datos CRUD."""
    global conexion
    try:
        conexion = mysql.connector.connect(**CONFIG_BD)
        return True
    except Error as error:
        messagebox.showerror(
            "Conexión con MySQL",
            "No se pudo conectar con la base de datos CRUD.\n\n"
            f"Detalle: {error}\n\n"
            "Revisa que MySQL esté iniciado, que exista CRUD y que la contraseña sea correcta."
        )
        return False


def ejecutar_sql(consulta, valores=(), obtener=False):
    """Ejecuta una consulta sencilla y guarda los cambios en MySQL."""
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(consulta, valores)
        resultado = cursor.fetchall() if obtener else cursor.lastrowid
        if not obtener:
            conexion.commit()
        cursor.close()
        return resultado
    except Error as error:
        conexion.rollback()
        messagebox.showerror("Error de base de datos", str(error))
        return None


def cargar_datos():
    """Carga grupos, alumnos y sus registros desde MySQL."""
    global grupos, grupo_actual
    grupos = {}
    filas = ejecutar_sql("SELECT id_grupo, nombre FROM grupos ORDER BY nombre", obtener=True)
    if filas is None:
        return False
    for fila in filas:
        grupos[fila["nombre"]] = []

    alumnos = ejecutar_sql(
        "SELECT id_alumno, nombre, apellido, id_grupo FROM alumnos WHERE estado='Activo' ORDER BY apellido, nombre",
        obtener=True
    )
    if alumnos is None:
        return False

    por_id = {}
    ids_grupos = ejecutar_sql("SELECT id_grupo, nombre FROM grupos", obtener=True)
    mapa_grupos = {fila["id_grupo"]: fila["nombre"] for fila in ids_grupos}
    for fila in alumnos:
        grupo = mapa_grupos.get(fila["id_grupo"])
        if grupo is None:
            continue
        alumno = crear_alumno((fila["nombre"] + " " + fila["apellido"]).strip())
        alumno["id_alumno"] = fila["id_alumno"]
        grupos[grupo].append(alumno)
        por_id[fila["id_alumno"]] = alumno

    registros = [
        ("asistencias", "SELECT id_alumno, fecha, estado FROM asistencias"),
        ("calificaciones", "SELECT id_alumno, calificacion, fecha FROM calificaciones"),
        ("justificantes", "SELECT id_alumno, fecha, motivo FROM justificantes"),
        ("conducta", "SELECT id_alumno, fecha, nivel, descripcion, registrado_por FROM reportes")
    ]
    for tipo, consulta in registros:
        filas = ejecutar_sql(consulta, obtener=True)
        if filas is None:
            return False
        for fila in filas:
            alumno = por_id.get(fila["id_alumno"])
            if alumno is None:
                continue
            if tipo == "asistencias":
                alumno["asistencia"][str(fila["fecha"])] = fila["estado"]
            elif tipo == "calificaciones":
                alumno["calificaciones"].append(float(fila["calificacion"]))
            elif tipo == "justificantes":
                alumno["justificantes"].append(f"{fila['fecha']} — {fila['motivo']}")
            else:
                alumno["conducta"].append(
                    f"{fila['fecha']} | {fila['nivel']} | {fila['descripcion']} (registrado por {fila['registrado_por']})"
                )
    if grupos and grupo_actual not in grupos:
        grupo_actual = next(iter(grupos))
    return True


def importar_alumnos_csv():
    """Importa una lista CSV con nombre, apellido, matrícula y grupo."""
    ruta = filedialog.askopenfilename(
        title="Seleccionar lista de alumnos CSV",
        filetypes=[("Archivos CSV", "*.csv")]
    )
    if not ruta:
        return
    agregados = 0
    omitidos = 0
    try:
        with open(ruta, "r", encoding="utf-8-sig", newline="") as archivo:
            lector = csv.DictReader(archivo)
            columnas = {c.strip().lower() for c in (lector.fieldnames or [])}
            necesarias = {"nombre", "apellido", "matricula", "grupo"}
            if not necesarias.issubset(columnas):
                messagebox.showwarning(
                    "Formato incorrecto",
                    "El CSV debe tener estas columnas: nombre, apellido, matricula, grupo."
                )
                return
            for fila in lector:
                nombre = (fila.get("nombre") or "").strip()
                apellido = (fila.get("apellido") or "").strip()
                matricula = (fila.get("matricula") or "").strip()
                grupo = (fila.get("grupo") or "").strip().upper()
                if not nombre or not apellido or not matricula or grupo not in grupos:
                    omitidos += 1
                    continue
                id_grupo = ejecutar_sql("SELECT id_grupo FROM grupos WHERE nombre=%s", (grupo,), True)
                if not id_grupo:
                    omitidos += 1
                    continue
                existe = ejecutar_sql("SELECT id_alumno FROM alumnos WHERE matricula=%s", (matricula,), True)
                if existe:
                    omitidos += 1
                    continue
                fecha_ingreso = date.today()
                nuevo_id = ejecutar_sql(
                    "INSERT INTO alumnos (matricula, nombre, apellido, id_grupo, fecha_ingreso, estado) VALUES (%s,%s,%s,%s,%s,'Activo')",
                    (matricula, nombre, apellido, id_grupo[0]["id_grupo"], fecha_ingreso)
                )
                if nuevo_id:
                    ejecutar_sql(
                        "INSERT INTO inscripciones (id_alumno, ciclo_escolar, fecha_inscripcion) VALUES (%s,%s,%s)",
                        (nuevo_id, str(date.today().year) + "-" + str(date.today().year + 1), fecha_ingreso)
                    )
                    agregados += 1
        cargar_datos()
        actualizar_lista_director()
        messagebox.showinfo(
            "Importación terminada",
            f"Alumnos agregados: {agregados}\nFilas omitidas: {omitidos}"
        )
    except (OSError, csv.Error, UnicodeError) as error:
        messagebox.showerror("Error al importar", str(error))

def mostrar_encabezado(titulo, rol):
    """Barra superior reutilizada en las pantallas internas."""
    barra = tk.Frame(ventana, bg=COLOR_AZUL, padx=15, pady=10)
    barra.pack(fill="x")

    tk.Label(
        barra,
        text=titulo,
        font=(FUENTE_TITULO, 19, "bold"),
        bg=COLOR_AZUL,
        fg="white"
    ).pack(side="left")

    tk.Label(
        barra,
        text=rol,
        font=(FUENTE_TEXTO, 10, "bold"),
        bg=COLOR_AZUL,
        fg=COLOR_DORADO
    ).pack(side="left", padx=15)

    crear_boton(
        barra,
        "Cerrar sesión",
        mostrar_login,
        COLOR_AZUL_OSCURO
    ).pack(side="right")


def crear_area_contenido():
    """Crea el contenedor principal para los controles de cada pantalla."""
    area = tk.Frame(ventana, bg=COLOR_FONDO)
    area.pack(fill="both", expand=True, padx=12, pady=8)
    return area


def obtener_alumnos():
    """Obtiene los alumnos del grupo que está seleccionado."""
    return grupos.get(grupo_actual, [])


def buscar_alumno(nombre):
    """Busca un alumno por su nombre en el grupo actual."""
    for alumno in obtener_alumnos():
        if alumno["nombre"] == nombre:
            return alumno
    return None


def mostrar_selector_grupo(parent, funcion_cambio=None):
    """Agrega un selector de grupo que comparten las vistas."""
    fila = tk.Frame(parent, bg=COLOR_FONDO)
    fila.pack(fill="x", padx=12, pady=7)

    crear_etiqueta(
        fila,
        "Grupo escolar:",
        tamano=12,
        negrita=True
    ).pack(side="left", padx=(3, 8))

    variable = tk.StringVar(value=grupo_actual)
    selector = ttk.Combobox(
        fila,
        textvariable=variable,
        values=list(grupos.keys()),
        state="readonly",
        width=12
    )
    selector.pack(side="left")

    def cambiar_grupo(_evento=None):
        global grupo_actual
        grupo_actual = variable.get()
        if funcion_cambio:
            funcion_cambio()

    selector.bind("<<ComboboxSelected>>", cambiar_grupo)
    return selector


def mostrar_lista(parent, altura=10):
    """Crea una lista adaptable con barras de desplazamiento."""
    contenedor = tk.Frame(parent, bg=COLOR_FONDO)
    contenedor.pack(fill="both", expand=True, padx=12, pady=8)

    lista = tk.Listbox(
        contenedor,
        height=altura,
        font=(FUENTE_TEXTO, 11),
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO,
        selectbackground=COLOR_AZUL,
        selectforeground="white",
        relief="flat",
        xscrollcommand=None,
        yscrollcommand=None
    )

    scrollbar_vertical = tk.Scrollbar(contenedor, orient="vertical", command=lista.yview)
    scrollbar_horizontal = tk.Scrollbar(contenedor, orient="horizontal", command=lista.xview)
    lista.configure(yscrollcommand=scrollbar_vertical.set, xscrollcommand=scrollbar_horizontal.set)

    lista.grid(row=0, column=0, sticky="nsew")
    scrollbar_vertical.grid(row=0, column=1, sticky="ns")
    scrollbar_horizontal.grid(row=1, column=0, sticky="ew")
    contenedor.grid_rowconfigure(0, weight=1)
    contenedor.grid_columnconfigure(0, weight=1)
    return lista

def contar_estado(alumno, estado):
    """Cuenta cuántas veces aparece un estado de asistencia."""
    return sum(
        valor == estado
        for valor in alumno["asistencia"].values()
    )


def resumen_asistencia(alumno):
    """Devuelve un texto breve con el resumen de asistencia."""
    presentes = contar_estado(alumno, "Presente")
    retardos = contar_estado(alumno, "Retardo")
    faltas = contar_estado(alumno, "Falta")

    return (
        f"Presentes: {presentes} | "
        f"Retardos: {retardos} | "
        f"Faltas: {faltas}"
    )


def registrar_asistencia(alumno, estado, fecha=None):
    """Guarda la asistencia de un alumno para una fecha."""
    if fecha is None:
        fecha = date.today()

    alumno["asistencia"][str(fecha)] = estado


def seleccionar_alumno_dialogo(titulo):
    """Pide el nombre de un alumno y lo busca en el grupo actual."""
    if not obtener_alumnos():
        messagebox.showinfo(
            titulo,
            "No hay alumnos registrados en este grupo."
        )
        return None

    nombres = "\n".join(
        alumno["nombre"]
        for alumno in obtener_alumnos()
    )

    nombre = simpledialog.askstring(
        titulo,
        "Escribe el nombre exacto del alumno:\n\n" + nombres
    )

    if not nombre:
        return None

    alumno = buscar_alumno(nombre.strip())
    if alumno is None:
        messagebox.showwarning(
            titulo,
            "No se encontró ese alumno en el grupo seleccionado."
        )
    return alumno


def agregar_alumno():
    """Permite al directivo agregar un alumno al grupo actual."""
    nombre = simpledialog.askstring(
        "Agregar alumno",
        f"Nombre completo para el grupo {grupo_actual}:"
    )

    if not nombre or not nombre.strip():
        return

    nombre = nombre.strip()

    if any(a["nombre"].lower() == nombre.lower() for a in obtener_alumnos()):
        messagebox.showwarning(
            "Agregar alumno",
            "Ya existe un alumno con ese nombre en este grupo."
        )
        return

    partes = nombre.split(" ", 1)
    nombre_pila = partes[0]
    apellido = partes[1] if len(partes) > 1 else "Sin apellido"
    fila_grupo = ejecutar_sql("SELECT id_grupo FROM grupos WHERE nombre=%s", (grupo_actual,), True)
    if not fila_grupo:
        messagebox.showerror("Grupo", "No se encontró el grupo seleccionado.")
        return
    matricula = simpledialog.askstring("Matrícula", "Escribe la matrícula del alumno:")
    if not matricula or not matricula.strip():
        messagebox.showwarning("Matrícula", "La matrícula es obligatoria.")
        return
    nuevo_id = ejecutar_sql(
        "INSERT INTO alumnos (matricula,nombre,apellido,id_grupo,fecha_ingreso,estado) VALUES (%s,%s,%s,%s,%s,'Activo')",
        (matricula.strip(), nombre_pila, apellido, fila_grupo[0]["id_grupo"], date.today())
    )
    if nuevo_id:
        ejecutar_sql("INSERT INTO inscripciones (id_alumno,ciclo_escolar,fecha_inscripcion) VALUES (%s,%s,%s)",
                     (nuevo_id, str(date.today().year) + "-" + str(date.today().year + 1), date.today()))
        cargar_datos()
        actualizar_lista_director()


def eliminar_alumno():
    """Elimina un alumno seleccionado por nombre."""
    alumno = seleccionar_alumno_dialogo("Eliminar alumno")
    if alumno is None:
        return

    confirmar = messagebox.askyesno(
        "Confirmar eliminación",
        f"¿Deseas eliminar a {alumno['nombre']}?"
    )

    if confirmar:
        ejecutar_sql("UPDATE alumnos SET estado='Baja' WHERE id_alumno=%s", (alumno["id_alumno"],))
        cargar_datos()
        actualizar_lista_director()


def mostrar_reporte_conducta_director():
    """Panel de conducta del directivo: formulario arriba, lista abajo."""
    limpiar_ventana()
    mostrar_encabezado("SAT NEZA HQX", "DIRECTIVO")

    crear_titulo(ventana, "Reporte de conducta").pack(pady=(12, 4))
    mostrar_selector_grupo(ventana, mostrar_reporte_conducta_director)

    # --- FORMULARIO ARRIBA ---
    panel = tk.Frame(ventana, bg=COLOR_PANEL, padx=20, pady=15)
    panel.pack(fill="x", padx=25, pady=10)

    tk.Label(panel, text="Nuevo reporte de conducta", font=(FUENTE_TITULO, 15, "bold"),
             bg=COLOR_PANEL, fg=COLOR_AZUL).pack(anchor="w", pady=(0, 10))

    # Fila: Alumno + Nivel
    fila1 = tk.Frame(panel, bg=COLOR_PANEL)
    fila1.pack(fill="x", pady=3)

    tk.Label(fila1, text="Alumno:", font=(FUENTE_TEXTO, 11, "bold"),
             bg=COLOR_PANEL, fg=COLOR_TEXTO).pack(side="left")
    var_alumno = tk.StringVar(value=obtener_alumnos()[0]["nombre"] if obtener_alumnos() else "")
    ttk.Combobox(fila1, textvariable=var_alumno,
                 values=[a["nombre"] for a in obtener_alumnos()],
                 state="readonly", width=30).pack(side="left", padx=(5, 0))

    tk.Label(fila1, text="Nivel:", font=(FUENTE_TEXTO, 11, "bold"),
             bg=COLOR_PANEL, fg=COLOR_TEXTO).pack(side="left", padx=(15, 5))
    var_nivel = tk.StringVar(value="Leve")
    ttk.Combobox(fila1, textvariable=var_nivel, values=["Leve", "Medio", "Grave"],
                 state="readonly", width=12).pack(side="left")

    # Descripción
    tk.Label(panel, text="Descripción:", font=(FUENTE_TEXTO, 11, "bold"),
             bg=COLOR_PANEL, fg=COLOR_TEXTO).pack(anchor="w", pady=(10, 3))
    entrada_desc = tk.Entry(panel, font=(FUENTE_TEXTO, 11), width=70)
    entrada_desc.pack(fill="x", ipady=6)

    def guardar_desde_panel():
        alumno = buscar_alumno(var_alumno.get())
        descripcion = entrada_desc.get().strip()
        if alumno is None:
            messagebox.showwarning("Reporte", "Selecciona un alumno.")
            return
        if not descripcion:
            messagebox.showwarning("Reporte", "Escribe la descripción.")
            return
        nivel = var_nivel.get()
        alumno["conducta"].append(f"{date.today()} | {nivel} | {descripcion} (registrado por Directivo)")
        ejecutar_sql(
            "INSERT INTO reportes (id_alumno, fecha, nivel, descripcion, registrado_por) VALUES (%s,%s,%s,%s,'Directivo')",
            (alumno["id_alumno"], date.today(), nivel, descripcion)
        )
        mostrar_reporte_conducta_director()  # recarga y ya se ve abajo

    fila_botones_panel = tk.Frame(panel, bg=COLOR_PANEL)
    fila_botones_panel.pack(pady=(12, 0))
    crear_boton(fila_botones_panel, "Guardar reporte", guardar_desde_panel, COLOR_VERDE).pack(side="left", padx=4)
    crear_boton(fila_botones_panel, "Volver al panel", mostrar_director, COLOR_AZUL_OSCURO).pack(side="left", padx=4)

    # --- LISTA ABAJO ---
    crear_etiqueta(ventana, "Reportes del grupo seleccionado:", tamano=11).pack(pady=(5, 0))
    lista = mostrar_lista(ventana, altura=10)
    hay = False
    for alumno in obtener_alumnos():
        for reporte in alumno["conducta"]:
            lista.insert("end", f"{alumno['nombre']} — {reporte}")
            hay = True
    if not hay:
        lista.insert("end", "No hay reportes de conducta en este grupo.")

def exportar_reporte():
    """Guarda en un archivo de texto los registros del grupo actual."""
    ruta = filedialog.asksaveasfilename(
        title="Guardar reporte escolar",
        defaultextension=".txt",
        filetypes=[("Archivo de texto", "*.txt")]
    )

    if not ruta:
        return

    with open(ruta, "w", encoding="utf-8") as archivo:
        archivo.write("SAT NEZA HQX - REPORTE ESCOLAR\n")
        archivo.write(f"Grupo: {grupo_actual}\n")
        archivo.write(f"Fecha de generación: {date.today()}\n")
        archivo.write("=" * 55 + "\n\n")

        for alumno in obtener_alumnos():
            archivo.write(f"Alumno: {alumno['nombre']}\n")
            archivo.write(resumen_asistencia(alumno) + "\n")
            archivo.write(f"Calificaciones: {alumno['calificaciones']}\n")
            archivo.write("Justificantes:\n")

            for justificante in alumno["justificantes"]:
                archivo.write(f"  - {justificante}\n")

            archivo.write("Conducta:\n")
            for reporte in alumno["conducta"]:
                archivo.write(f"  - {reporte}\n")

            archivo.write("\n" + "-" * 55 + "\n\n")

    messagebox.showinfo(
        "Reporte exportado",
        "El reporte se guardó correctamente."
    )

lista_director = None
etiqueta_fecha_director = None

def agregar_grupo():
    """Permite al directivo crear un grupo nuevo."""
    nombre_grupo = simpledialog.askstring("Agregar grupo", "Nombre del grupo (ej: 1A, 2B):")
    if not nombre_grupo or not nombre_grupo.strip():
        return

    nombre_grupo = nombre_grupo.strip().upper()

    if nombre_grupo in grupos:
        messagebox.showwarning("Agregar grupo", f"El grupo {nombre_grupo} ya existe.")
        return

    nuevo_id = ejecutar_sql(
        "INSERT INTO grupos (nombre) VALUES (%s)",
        (nombre_grupo,)
    )
    if nuevo_id:
        cargar_datos()
        global grupo_actual
        grupo_actual = nombre_grupo
        actualizar_lista_director()
        # Recarga la pantalla para que el selector ya muestre el grupo nuevo
        mostrar_director()
        messagebox.showinfo("Grupo creado", f"Grupo {nombre_grupo} creado correctamente.")

def mostrar_director():
    """Construye la pantalla principal del directivo."""
    global lista_director, etiqueta_fecha_director

    limpiar_ventana()
    mostrar_encabezado("SAT NEZA HQX", "DIRECTIVO")

    crear_titulo(
        ventana,
        "Panel de control escolar"
    ).pack(pady=(12, 4))

    mostrar_selector_grupo(
        ventana,
        actualizar_lista_director
    )

    fila_botones = tk.Frame(ventana, bg=COLOR_FONDO)
    fila_botones.pack(fill="x", padx=12, pady=5)

    crear_boton(
        fila_botones,
        "Agregar grupo",
        agregar_grupo,
        COLOR_VERDE
    ).pack(side="left", padx=4)

    crear_boton(
        fila_botones,
        "Agregar alumno",
        agregar_alumno
    ).pack(side="left", padx=4)

    crear_boton(
        fila_botones,
        "Eliminar alumno",
        eliminar_alumno
    ).pack(side="left", padx=4)

    crear_boton(
        fila_botones,
        "Importar alumnos CSV",
        importar_alumnos_csv,
        COLOR_VERDE
    ).pack(side="left", padx=4)

    crear_boton(
        fila_botones,
        "Reporte de conducta",
        mostrar_reporte_conducta_director
    ).pack(side="left", padx=4)

    crear_boton(
        fila_botones,
        "Exportar reporte",
        exportar_reporte
    ).pack(side="left", padx=4)

    crear_boton(
        fila_botones,
        "Crear cuenta nueva",
        lambda: mostrar_registro(volver_a=mostrar_director),
        COLOR_VERDE
    ).pack(side="left", padx=4)

    fila_fecha = tk.Frame(ventana, bg=COLOR_FONDO)
    fila_fecha.pack(fill="x", padx=14, pady=5)

    crear_boton(
        fila_fecha,
        "Día anterior",
        lambda: mover_fecha_director(-1)
    ).pack(side="left", padx=4)

    etiqueta_fecha_director = tk.Label(
        fila_fecha,
        text=str(fecha_seleccionada),
        font=(FUENTE_TEXTO, 12, "bold"),
        bg=COLOR_FONDO,
        fg=COLOR_DORADO
    )
    etiqueta_fecha_director.pack(side="left", padx=10)

    crear_boton(
        fila_fecha,
        "Día siguiente",
        lambda: mover_fecha_director(1)
    ).pack(side="left", padx=4)

    lista_director = mostrar_lista(ventana, altura=12)
    actualizar_lista_director()

def mover_fecha_director(dias):
    """Cambia la fecha que se muestra en el panel de directivo."""
    global fecha_seleccionada
    fecha_seleccionada += timedelta(days=dias)

    if etiqueta_fecha_director and etiqueta_fecha_director.winfo_exists():
        etiqueta_fecha_director.config(text=str(fecha_seleccionada))

    actualizar_lista_director()

def actualizar_lista_director():
    """Actualiza la lista con el resumen de los alumnos del grupo."""
    if lista_director is None or not lista_director.winfo_exists():
        return

    lista_director.delete(0, "end")

    if not obtener_alumnos():
        lista_director.insert("end", "No hay alumnos registrados en este grupo.")
        return

    for alumno in obtener_alumnos():
        estado_fecha = alumno["asistencia"].get(
            str(fecha_seleccionada),
            "Sin registrar"
        )

        linea = (
            f"{alumno['nombre']}  |  "
            f"Fecha: {estado_fecha}  |  "
            f"{resumen_asistencia(alumno)}"
        )
        lista_director.insert("end", linea)

def agregar_alumno_profesor():
    """Permite al profesor agregar alumnos al grupo seleccionado."""
    nombre = simpledialog.askstring(
        "Agregar alumno",
        f"Nombre completo para el grupo {grupo_actual}:"
    )

    if not nombre or not nombre.strip():
        return

    nombre = nombre.strip()

    if any(a["nombre"].lower() == nombre.lower() for a in obtener_alumnos()):
        messagebox.showwarning(
            "Agregar alumno",
            "Ya existe un alumno con ese nombre en este grupo."
        )
        return

    partes = nombre.split(" ", 1)
    nombre_pila = partes[0]
    apellido = partes[1] if len(partes) > 1 else "Sin apellido"
    fila_grupo = ejecutar_sql("SELECT id_grupo FROM grupos WHERE nombre=%s", (grupo_actual,), True)
    matricula = simpledialog.askstring("Matrícula", "Escribe la matrícula del alumno:")
    if not matricula or not matricula.strip() or not fila_grupo:
        return
    nuevo_id = ejecutar_sql(
        "INSERT INTO alumnos (matricula,nombre,apellido,id_grupo,fecha_ingreso,estado) VALUES (%s,%s,%s,%s,%s,'Activo')",
        (matricula.strip(), nombre_pila, apellido, fila_grupo[0]["id_grupo"], date.today())
    )
    if nuevo_id:
        ejecutar_sql("INSERT INTO inscripciones (id_alumno,ciclo_escolar,fecha_inscripcion) VALUES (%s,%s,%s)",
                     (nuevo_id, str(date.today().year) + "-" + str(date.today().year + 1), date.today()))
        cargar_datos()
    messagebox.showinfo(
        "Alumno agregado",
        f"{nombre} se agregó al grupo {grupo_actual}."
    )
    mostrar_profesor("Inicio")


def mostrar_profesor(vista="Inicio"):
    """Abre la interfaz del profesor en la sección indicada."""
    limpiar_ventana()
    mostrar_encabezado("SAT NEZA HQX", "PROFESOR")

    menu = tk.Frame(ventana, bg=COLOR_FONDO)
    menu.pack(fill="x", padx=10, pady=8)

    secciones = (
        "Inicio",
        "Asistencias",
        "Justificantes",
        "Calificaciones",
        "Conducta"
    )

    for seccion in secciones:
        crear_boton(
            menu,
            seccion,
            lambda nombre=seccion: mostrar_profesor(nombre)
        ).pack(side="left", padx=3, pady=2)

    crear_boton(
        menu,
        "Agregar alumno",
        agregar_alumno_profesor,
        COLOR_AZUL_OSCURO
    ).pack(side="left", padx=3, pady=2)

    mostrar_selector_grupo(
        ventana,
        lambda: mostrar_profesor(vista)
    )

    crear_titulo(
        ventana,
        vista
    ).pack(pady=(8, 10))

    if vista == "Inicio":
        vista_inicio_profesor()
    elif vista == "Asistencias":
        vista_asistencias_profesor()
    elif vista == "Justificantes":
        vista_justificantes_profesor()
    elif vista == "Calificaciones":
        vista_calificaciones_profesor()
    elif vista == "Conducta":
        vista_conducta_profesor()

def vista_inicio_profesor():
    """Contenido de la página de inicio del profesor."""
    panel = tk.Frame(
        ventana,
        bg=COLOR_PANEL,
        padx=25,
        pady=25
    )
    panel.pack(fill="x", padx=25, pady=15)

    tk.Label(
        panel,
        text="Bienvenido al sistema de control escolar",
        font=(FUENTE_TITULO, 17, "bold"),
        bg=COLOR_PANEL,
        fg=COLOR_AZUL
    ).pack(pady=8)

    tk.Label(
        panel,
        text=f"Grupo seleccionado: {grupo_actual}",
        font=(FUENTE_TEXTO, 12),
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO
    ).pack(pady=4)

    tk.Label(
        panel,
        text=f"Alumnos registrados: {len(obtener_alumnos())}",
        font=(FUENTE_TEXTO, 12, "bold"),
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO
    ).pack(pady=4)

    tk.Label(
        panel,
        text="Utiliza el menú superior para registrar asistencias,\n"
             "justificantes, calificaciones y reportes de conducta.",
        font=(FUENTE_TEXTO, 11),
        bg=COLOR_PANEL,
        fg=COLOR_SUAVE,
        justify="center"
    ).pack(pady=8)

def crear_selector_alumno(parent):
    """Crea un selector con los nombres de los alumnos del grupo actual."""
    nombres = [
        alumno["nombre"]
        for alumno in obtener_alumnos()
    ]

    variable = tk.StringVar(
        value=nombres[0] if nombres else ""
    )

    selector = ttk.Combobox(
        parent,
        textvariable=variable,
        values=nombres,
        state="readonly",
        width=30
    )
    selector.pack(pady=6)

    return variable, selector

def vista_asistencias_profesor():
    """Permite registrar asistencia, retardo o falta para la fecha actual."""
    crear_etiqueta(
        ventana,
        "Selecciona al alumno y su estado de asistencia.",
        tamano=11
    ).pack(pady=4)

    nombre, selector = crear_selector_alumno(ventana)

    estado = tk.StringVar(value="Presente")
    opciones = tk.Frame(ventana, bg=COLOR_FONDO)
    opciones.pack(pady=6)

    for valor in ("Presente", "Retardo", "Falta"):
        tk.Radiobutton(
            opciones,
            text=valor,
            value=valor,
            variable=estado,
            font=(FUENTE_TEXTO, 11),
            bg=COLOR_FONDO,
            fg="white",
            selectcolor=COLOR_AZUL,
            activebackground=COLOR_FONDO,
            activeforeground="white"
        ).pack(side="left", padx=8)

    resultado = crear_etiqueta(
        ventana,
        "",
        tamano=11,
        color_texto=COLOR_DORADO
    )
    resultado.pack(pady=4)

    def guardar_asistencia():
        alumno = buscar_alumno(nombre.get())

        if alumno is None:
            messagebox.showwarning(
                "Asistencia",
                "Selecciona un alumno registrado."
            )
            return

        registrar_asistencia(
            alumno,
            estado.get(),
            date.today()
        )
        ejecutar_sql(
            "INSERT INTO asistencias (id_alumno,fecha,estado) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE estado=VALUES(estado)",
            (alumno["id_alumno"], date.today(), estado.get())
        )

        resultado.config(
            text=f"{alumno['nombre']}: {estado.get()} guardado."
        )
        actualizar_lista_director_si_existe()

    crear_boton(
        ventana,
        "Guardar asistencia de hoy",
        guardar_asistencia,
        COLOR_AZUL_OSCURO
    ).pack(pady=6)

    lista = mostrar_lista(ventana, altura=7)
    for alumno in obtener_alumnos():
        estado_hoy = alumno["asistencia"].get(
            str(date.today()),
            "Sin registrar"
        )
        lista.insert(
            "end",
            f"{alumno['nombre']} — {estado_hoy}"
        )

def actualizar_lista_director_si_existe():
    """Actualiza la lista del directivo si esa pantalla sigue abierta."""
    if lista_director is not None and lista_director.winfo_exists():
        actualizar_lista_director()


def vista_justificantes_profesor():
    """Permite guardar justificantes y ver los ya registrados."""
    crear_etiqueta(
        ventana,
        "Selecciona un alumno y escribe el motivo del justificante.",
        tamano=11
    ).pack(pady=4)

    nombre, selector = crear_selector_alumno(ventana)

    entrada_motivo = crear_campo(
        ventana,
        ancho=45
    )
    entrada_motivo.pack(pady=8)
    entrada_motivo.insert(0, "Motivo del justificante")

    def guardar_justificante():
        alumno = buscar_alumno(nombre.get())
        motivo = entrada_motivo.get().strip()

        if alumno is None:
            messagebox.showwarning(
                "Justificante",
                "Selecciona un alumno."
            )
            return

        if not motivo or motivo == "Motivo del justificante":
            messagebox.showwarning(
                "Justificante",
                "Escribe el motivo del justificante."
            )
            return

        alumno["justificantes"].append(
            f"{date.today()} — {motivo}"
        )
        ejecutar_sql(
            "INSERT INTO justificantes (id_alumno,fecha,motivo) VALUES (%s,%s,%s)",
            (alumno["id_alumno"], date.today(), motivo)
        )

        messagebox.showinfo(
            "Justificante",
            "El justificante se guardó correctamente."
        )
        mostrar_profesor("Justificantes")

    crear_boton(
        ventana,
        "Guardar justificante",
        guardar_justificante,
        COLOR_AZUL_OSCURO
    ).pack(pady=5)

    lista = mostrar_lista(ventana, altura=7)

    for alumno in obtener_alumnos():
        for justificante in alumno["justificantes"]:
            lista.insert(
                "end",
                f"{alumno['nombre']} — {justificante}"
            )


def vista_calificaciones_profesor():
    """Permite agregar calificaciones de 0 a 10 y consultar registros."""
    crear_etiqueta(
        ventana,
        "Selecciona un alumno y escribe una calificación de 0 a 10.",
        tamano=11
    ).pack(pady=4)

    nombre, selector = crear_selector_alumno(ventana)

    entrada_nota = crear_campo(
        ventana,
        ancho=14
    )
    entrada_nota.pack(pady=7)

    def guardar_calificacion():
        alumno = buscar_alumno(nombre.get())

        if alumno is None:
            messagebox.showwarning(
                "Calificaciones",
                "Selecciona un alumno."
            )
            return

        try:
            nota = float(entrada_nota.get())
            if nota < 0 or nota > 10:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Calificaciones",
                "Escribe una calificación válida entre 0 y 10."
            )
            return

        alumno["calificaciones"].append(nota)
        ejecutar_sql(
            "INSERT INTO calificaciones (id_alumno,calificacion,fecha) VALUES (%s,%s,%s)",
            (alumno["id_alumno"], nota, date.today())
        )

        messagebox.showinfo(
            "Calificaciones",
            f"Se guardó la calificación {nota:g} para {alumno['nombre']}."
        )
        mostrar_profesor("Calificaciones")

    crear_boton(
        ventana,
        "Guardar calificación",
        guardar_calificacion,
        COLOR_AZUL_OSCURO
    ).pack(pady=5)

    lista = mostrar_lista(ventana, altura=7)

    for alumno in obtener_alumnos():
        if alumno["calificaciones"]:
            notas = ", ".join(
                f"{nota:g}"
                for nota in alumno["calificaciones"]
            )
        else:
            notas = "Sin calificaciones"

        lista.insert(
            "end",
            f"{alumno['nombre']}: {notas}"
        )

def vista_conducta_profesor():
    """Reportes de conducta en un solo panel, sin ventanas emergentes."""
    # --- FORMULARIO ARRIBA ---
    panel = tk.Frame(ventana, bg=COLOR_PANEL, padx=20, pady=15)
    panel.pack(fill="x", padx=25, pady=10)

    tk.Label(panel, text="Nuevo reporte de conducta", font=(FUENTE_TITULO, 15, "bold"),
             bg=COLOR_PANEL, fg=COLOR_AZUL).pack(anchor="w", pady=(0, 10))

    # Fila 1: Alumno + Nivel
    fila1 = tk.Frame(panel, bg=COLOR_PANEL)
    fila1.pack(fill="x", pady=3)

    tk.Label(fila1, text="Alumno:", font=(FUENTE_TEXTO, 11, "bold"),
             bg=COLOR_PANEL, fg=COLOR_TEXTO).pack(side="left")
    var_alumno, _ = crear_selector_alumno(fila1)
    # Lo movemos para que quede bien en la fila
    # Si te queda raro, crear_selector_alumno hace pack, lo dejamos así

    tk.Label(fila1, text="Nivel:", font=(FUENTE_TEXTO, 11, "bold"),
             bg=COLOR_PANEL, fg=COLOR_TEXTO).pack(side="left", padx=(15, 5))
    var_nivel = tk.StringVar(value="Leve")
    ttk.Combobox(fila1, textvariable=var_nivel, values=["Leve", "Medio", "Grave"],
                 state="readonly", width=12).pack(side="left")

    # Fila 2: Descripción
    tk.Label(panel, text="Descripción:", font=(FUENTE_TEXTO, 11, "bold"),
             bg=COLOR_PANEL, fg=COLOR_TEXTO).pack(anchor="w", pady=(10, 3))
    entrada_desc = tk.Entry(panel, font=(FUENTE_TEXTO, 11), width=70)
    entrada_desc.pack(fill="x", ipady=6)

    def guardar_desde_panel():
        alumno = buscar_alumno(var_alumno.get())
        descripcion = entrada_desc.get().strip()
        if alumno is None:
            messagebox.showwarning("Reporte", "Selecciona un alumno.")
            return
        if not descripcion:
            messagebox.showwarning("Reporte", "Escribe la descripción.")
            return
        nivel = var_nivel.get()
        alumno["conducta"].append(f"{date.today()} | {nivel} | {descripcion} (registrado por profesor)")
        ejecutar_sql(
            "INSERT INTO reportes (id_alumno, fecha, nivel, descripcion, registrado_por) VALUES (%s,%s,%s,%s,'Profesor')",
            (alumno["id_alumno"], date.today(), nivel, descripcion)
        )
        entrada_desc.delete(0, "end")
        mostrar_profesor("Conducta")  # recarga y ya aparece en la lista de abajo

    crear_boton(panel, "Guardar reporte", guardar_desde_panel, COLOR_VERDE).pack(pady=(12, 0))

    # --- LISTA ABAJO ---
    crear_etiqueta(ventana, "Reportes del grupo seleccionado:", tamano=11).pack(pady=(5, 0))
    lista = mostrar_lista(ventana, altura=10)
    hay = False
    for alumno in obtener_alumnos():
        for reporte in alumno["conducta"]:
            lista.insert("end", f"{alumno['nombre']} — {reporte}")
            hay = True
    if not hay:
        lista.insert("end", "No hay reportes de conducta en este grupo.")

def mostrar_registro(volver_a=mostrar_login):
    """Permite registrar una cuenta de directivo o profesor."""
    limpiar_ventana()
    contenedor = crear_contenedor_con_scroll(ventana)

    tk.Label(contenedor, text="CREAR CUENTA", font=(FUENTE_TITULO, 30, "bold"),
             fg="white", bg=COLOR_FONDO).pack(pady=(25, 12))

    tarjeta = tk.Frame(contenedor, bg=COLOR_PANEL, padx=35, pady=25,
                       highlightbackground=COLOR_DORADO, highlightthickness=2)
    tarjeta.pack(padx=20, pady=10)

    tk.Label(tarjeta, text="Registro de usuario", font=(FUENTE_TITULO, 23, "bold"),
             fg=COLOR_AZUL, bg=COLOR_PANEL).pack(pady=(0, 18))

    campos = {}
    for etiqueta, clave in (("Nombre", "nombre"), ("Apellido", "apellido"),
                            ("Nombre de usuario", "usuario"), ("Contraseña", "clave"),
                            ("Confirmar contraseña", "confirmar")):
        tk.Label(tarjeta, text=etiqueta, font=(FUENTE_TEXTO, 12, "bold"),
                 fg=COLOR_TEXTO, bg=COLOR_PANEL).pack(anchor="w", pady=(7, 2))
        campos[clave] = crear_campo(tarjeta, ancho=38,
                                   ocultar=clave in ("clave", "confirmar"))
        campos[clave].pack(fill="x", pady=(0, 4), ipady=5)

    tk.Label(tarjeta, text="Tipo de cuenta", font=(FUENTE_TEXTO, 12, "bold"),
             fg=COLOR_TEXTO, bg=COLOR_PANEL).pack(anchor="w", pady=(12, 4))
    perfil = tk.StringVar(value="Profesor")
    fila = tk.Frame(tarjeta, bg=COLOR_PANEL)
    fila.pack(anchor="w")
    for rol in ("Directivo", "Profesor"):
        tk.Radiobutton(fila, text=rol, variable=perfil, value=rol,
                       font=(FUENTE_TEXTO, 11), bg=COLOR_PANEL,
                       fg=COLOR_TEXTO, activebackground=COLOR_PANEL).pack(side="left", padx=(0, 18))

    def guardar_cuenta():
        nombre = campos["nombre"].get().strip()
        apellido = campos["apellido"].get().strip()
        usuario = campos["usuario"].get().strip()
        clave = campos["clave"].get()
        confirmar = campos["confirmar"].get()
        if not all((nombre, apellido, usuario, clave, confirmar)):
            messagebox.showwarning("Registro", "Completa todos los campos.")
            return
        if len(usuario) < 4:
            messagebox.showwarning("Registro", "El usuario debe tener al menos 4 caracteres.")
            return
        if len(clave) < 8:
            messagebox.showwarning("Registro", "La contraseña debe tener al menos 8 caracteres.")
            return
        if clave != confirmar:
            messagebox.showwarning("Registro", "Las contraseñas no coinciden.")
            return
        existe = ejecutar_sql("SELECT id_usuario FROM usuarios WHERE usuario=%s", (usuario,), True)
        if existe is None:
            return
        if existe:
            messagebox.showwarning("Registro", "Ese nombre de usuario ya está ocupado.")
            return
        id_usuario = ejecutar_sql(
            "INSERT INTO usuarios (usuario, contrasena, rol, estado) VALUES (%s,%s,%s,'Activo')",
            (usuario, crear_hash(clave), perfil.get())
        )
        if not id_usuario:
            return
        if perfil.get() == "Directivo":
            ejecutar_sql("INSERT INTO directores (id_usuario, nombre, apellido) VALUES (%s,%s,%s)",
                         (id_usuario, nombre, apellido))
        else:
            ejecutar_sql("INSERT INTO docentes (id_usuario, nombre, apellido, id_grupo) VALUES (%s,%s,%s,NULL)",
                         (id_usuario, nombre, apellido))
        messagebox.showinfo("Cuenta creada", "Tu cuenta se creó correctamente.")
        volver_a()

    texto_volver = "Volver al panel" if volver_a == mostrar_director else "Volver al inicio de sesión"
    crear_boton(tarjeta, "Crear cuenta", guardar_cuenta, COLOR_VERDE).pack(fill="x", pady=(20, 7), ipady=5)
    crear_boton(tarjeta, texto_volver, volver_a, COLOR_AZUL_OSCURO).pack(fill="x", ipady=5)


def mostrar_login():
    """Muestra una pantalla inicial adaptable."""
    limpiar_ventana()
    contenedor = crear_contenedor_con_scroll(ventana)

    tk.Label(contenedor, text="SAT NEZA HQX", font=(FUENTE_TITULO, 34, "bold"),
             fg="white", bg=COLOR_FONDO).pack(pady=(25, 5))
    tk.Label(contenedor, text="SISTEMA DE CONTROL ESCOLAR", font=(FUENTE_TEXTO, 15, "bold"),
             fg=COLOR_DORADO, bg=COLOR_FONDO).pack(pady=(0, 15))

    tarjeta = tk.Frame(contenedor, bg=COLOR_PANEL, padx=35, pady=25,
                       highlightbackground=COLOR_DORADO, highlightthickness=2)
    tarjeta.pack(padx=20, pady=8)

    tk.Label(tarjeta, text="Inicio de sesión", font=(FUENTE_TITULO, 27, "bold"),
             fg=COLOR_AZUL, bg=COLOR_PANEL).pack(pady=(0, 5))
    tk.Label(tarjeta, text="Ingresa tus datos para continuar", font=(FUENTE_TEXTO, 12),
             fg=COLOR_SUAVE, bg=COLOR_PANEL).pack(pady=(0, 20))

    tk.Label(tarjeta, text="Usuario", font=(FUENTE_TEXTO, 12, "bold"),
             fg=COLOR_TEXTO, bg=COLOR_PANEL).pack(anchor="w")
    entrada_usuario = crear_campo(tarjeta, ancho=38)
    entrada_usuario.pack(fill="x", pady=(5, 14), ipady=6)

    tk.Label(tarjeta, text="Contraseña", font=(FUENTE_TEXTO, 12, "bold"),
             fg=COLOR_TEXTO, bg=COLOR_PANEL).pack(anchor="w")
    entrada_clave = crear_campo(tarjeta, ancho=38, ocultar=True)
    entrada_clave.pack(fill="x", pady=(5, 14), ipady=6)

    def revisar_acceso():
        usuario = entrada_usuario.get().strip()
        clave = entrada_clave.get()
        if not usuario or not clave:
            messagebox.showwarning("Inicio de sesión", "Escribe tu usuario y contraseña.")
            return
        usuario_bd = ejecutar_sql(
            "SELECT id_usuario, usuario, contrasena, rol FROM usuarios WHERE usuario=%s AND estado='Activo'",
            (usuario,), True
        )
        if not usuario_bd or not comprobar_clave(clave, usuario_bd[0]["contrasena"]):
            messagebox.showerror("Acceso denegado", "El usuario o la contraseña son incorrectos.")
            return
        rol_usuario = usuario_bd[0]["rol"]
        if not usuario_bd[0]["contrasena"].startswith("pbkdf2$"):
            ejecutar_sql("UPDATE usuarios SET contrasena=%s WHERE id_usuario=%s",
                         (crear_hash(clave), usuario_bd[0]["id_usuario"]))
        if rol_usuario.lower() == "directivo":
            mostrar_director()
        else:
            mostrar_profesor()

    crear_boton(tarjeta, "Ingresar", revisar_acceso, COLOR_AZUL_OSCURO).pack(fill="x", pady=(18, 8), ipady=7)


if __name__ == "__main__":
    if conectar_bd():
        if cargar_datos():
            mostrar_login()
            ventana.mainloop()
        if conexion and conexion.is_connected():
            conexion.close()