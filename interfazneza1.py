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

-- Tabla de control: identifica al unico Director autorizado
-- y establece el limite de seis cuentas docentes.
-- Tabla de control de cuentas: ejecutar este bloque una sola vez al crear CRUD.
-- La aplicación valida y prepara esta estructura mediante su rutina de migración.
CREATE TABLE control_sistema (
    id_control TINYINT NOT NULL PRIMARY KEY,
    id_director INT NULL UNIQUE,
    limite_docentes TINYINT NOT NULL DEFAULT 6,
    CONSTRAINT fk_control_director
        FOREIGN KEY (id_director) REFERENCES directores(id_director)
) ENGINE=InnoDB;

INSERT INTO control_sistema (id_control, id_director, limite_docentes)
VALUES (1, NULL, 6);

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
    "database": "CRUD"
}

grupo_actual = "1A"
fecha_seleccionada = date.today()
grupos = {}
usuario_actual_id = None
rol_actual = None


def preparar_tabla_control():
    """Aplica una migración segura para el control del único Director autorizado.

    Consulta el catálogo de MySQL antes de crear la tabla; no depende de
    las instrucciones condicionales del DDL ni inserciones que ignoren errores.
    Si la tabla ya existe, conserva su contenido y solo completa lo que falte.
    """
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT TABLE_NAME FROM information_schema.tables "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s LIMIT 1",
            ("control_sistema",)
        )
        tabla_existente = cursor.fetchone()

        if not tabla_existente:
            try:
                cursor.execute("""
                    CREATE TABLE control_sistema (
                        id_control TINYINT NOT NULL PRIMARY KEY,
                        id_director INT NULL UNIQUE,
                        limite_docentes TINYINT NOT NULL DEFAULT 6,
                        CONSTRAINT fk_control_director
                            FOREIGN KEY (id_director)
                            REFERENCES directores(id_director)
                    ) ENGINE=InnoDB
                """)
            except Error as error:
                # Evita fallar si otra instancia creó la tabla simultáneamente.
                if getattr(error, "errno", None) != 1050:
                    raise

        # La fila singleton (id_control=1) se inserta solo cuando no existe.
        cursor.execute(
            "SELECT id_control, id_director FROM control_sistema "
            "WHERE id_control=%s FOR UPDATE",
            (1,)
        )
        control = cursor.fetchone()
        if control is None:
            # La clave primaria garantiza una sola fila de control, incluso
            # si dos instancias inician por primera vez casi al mismo tiempo.
            cursor.execute("""
                INSERT INTO control_sistema
                    (id_control, id_director, limite_docentes)
                VALUES (1, NULL, 6)
                ON DUPLICATE KEY UPDATE id_control = id_control
            """)
            cursor.execute(
                "SELECT id_control, id_director FROM control_sistema "
                "WHERE id_control=%s FOR UPDATE",
                (1,)
            )
            control = cursor.fetchone()

        if control is None:
            raise Error("No fue posible inicializar el control del Director.")
        director_controlado = control["id_director"]

        # Migración de instalaciones anteriores: vincula solo el primer
        # perfil directivo existente cuando todavía no hay uno autorizado.
        if director_controlado is None:
            cursor.execute(
                "SELECT id_director FROM directores ORDER BY id_director LIMIT 1"
            )
            director_existente = cursor.fetchone()
            if director_existente:
                cursor.execute(
                    "UPDATE control_sistema SET id_director=%s "
                    "WHERE id_control=1 AND id_director IS NULL",
                    (director_existente["id_director"],)
                )

        conexion.commit()
        return True
    except Error:
        conexion.rollback()
        raise
    finally:
        cursor.close()

def conectar_bd():
    """Conecta con CRUD y prepara la tabla de control de cuentas."""
    global conexion
    try:
        conexion = mysql.connector.connect(**CONFIG_BD)
        preparar_tabla_control()
        return True
    except Error as error:
        messagebox.showerror(
            "Conexión con MySQL",
            "No se pudo conectar o preparar la base de datos CRUD.\n\n"
            f"Detalle: {error}\n\n"
            "Revisa que MySQL esté iniciado, que exista CRUD, que las diez tablas estén creadas y que la contraseña sea correcta."
        )
        return False


def director_ya_registrado():
    """Devuelve True si el registro único está ocupado o no puede verificarse.

    Ante un error de consulta, la interfaz cierra el registro por seguridad.
    """
    filas = ejecutar_sql(
        "SELECT id_director FROM control_sistema WHERE id_control=1",
        obtener=True
    )
    return not filas or filas[0]["id_director"] is not None


def contar_docentes():
    filas = ejecutar_sql(
        "SELECT COUNT(*) AS total FROM docentes d "
        "INNER JOIN usuarios u ON u.id_usuario=d.id_usuario WHERE u.rol='Profesor'",
        obtener=True
    )
    if filas is None:
        return 6
    return int(filas[0]["total"])


def es_director_autorizado():
    if usuario_actual_id is None or (rol_actual or "").lower() != "directivo":
        return False
    filas = ejecutar_sql(
        "SELECT d.id_usuario FROM control_sistema c "
        "INNER JOIN directores d ON d.id_director=c.id_director "
        "WHERE c.id_control=1",
        obtener=True
    )
    return bool(filas) and filas[0]["id_usuario"] == usuario_actual_id


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

ventana = tk.Tk()
ventana.title("SAT NEZA HQX - Sistema de Control Escolar")
ventana.geometry("1250x850")
ventana.minsize(850, 620)
ventana.configure(bg=COLOR_FONDO)

# En Windows abre maximizada; en otros sistemas usa casi toda la pantalla.
try:
    ventana.state("zoomed")
except tk.TclError:
    ancho = ventana.winfo_screenwidth()
    alto = ventana.winfo_screenheight()
    ventana.geometry(f"{int(ancho * 0.92)}x{int(alto * 0.88)}")


def limpiar_ventana():
    """Elimina los widgets de la vista actual antes de abrir otra."""
    for widget in ventana.winfo_children():
        widget.destroy()


def crear_boton(parent, texto, comando, color=COLOR_AZUL):
    """Crea botones con el mismo estilo para todas las pantallas."""
    return tk.Button(
        parent,
        text=texto,
        command=comando,
        bg=color,
        fg="white",
        activebackground=COLOR_DORADO,
        activeforeground="white",
        font=(FUENTE_TITULO, 12, "bold"),
        relief="flat",
        padx=12,
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
    """Crea un campo de entrada."""
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
    """Crea una lista con el estilo usado en las pantallas."""
    lista = tk.Listbox(
        parent,
        height=altura,
        font=(FUENTE_TEXTO, 11),
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO,
        selectbackground=COLOR_AZUL,
        selectforeground="white",
        relief="flat"
    )
    lista.pack(fill="both", expand=True, padx=12, pady=8)
    return lista

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


def mostrar_registro():
    """Permite crear la unica cuenta inicial de Director."""
    if director_ya_registrado():
        messagebox.showinfo(
            "Registro cerrado",
            "La cuenta del Director ya fue creada. Los usuarios Docentes deben ser registrados por él."
        )
        mostrar_login()
        return

    limpiar_ventana()
    ventana.configure(bg=COLOR_FONDO)

    contenedor = tk.Frame(ventana, bg=COLOR_FONDO)
    contenedor.pack(fill="both", expand=True)

    tk.Label(contenedor, text="CONFIGURACIÓN INICIAL", font=(FUENTE_TITULO, 30, "bold"),
             fg="white", bg=COLOR_FONDO).pack(pady=(25, 12))

    tarjeta = tk.Frame(contenedor, bg=COLOR_PANEL, padx=45, pady=28,
                       highlightbackground=COLOR_DORADO, highlightthickness=2)
    tarjeta.pack(padx=20, pady=10)

    tk.Label(tarjeta, text="Crear cuenta del Director", font=(FUENTE_TITULO, 23, "bold"),
             fg=COLOR_AZUL, bg=COLOR_PANEL).pack(pady=(0, 18))
    tk.Label(tarjeta, text="Esta será la única cuenta con permisos de Dirección.",
             font=(FUENTE_TEXTO, 10), fg=COLOR_SUAVE, bg=COLOR_PANEL).pack(pady=(0, 10))

    campos = {}
    for etiqueta, clave in (("Nombre", "nombre"), ("Apellido", "apellido"),
                            ("Nombre de usuario", "usuario"), ("Contraseña", "clave"),
                            ("Confirmar contraseña", "confirmar")):
        tk.Label(tarjeta, text=etiqueta, font=(FUENTE_TEXTO, 12, "bold"),
                 fg=COLOR_TEXTO, bg=COLOR_PANEL).pack(anchor="w", pady=(7, 2))
        campos[clave] = crear_campo(tarjeta, ancho=38,
                                    ocultar=clave in ("clave", "confirmar"))
        campos[clave].pack(fill="x", pady=(0, 4), ipady=5)

    def guardar_director():
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

        cursor = conexion.cursor()
        try:
            conexion.start_transaction()
            cursor.execute(
                "SELECT id_director FROM control_sistema WHERE id_control=1 FOR UPDATE"
            )
            control = cursor.fetchone()
            if not control or control[0] is not None:
                conexion.rollback()
                messagebox.showwarning("Registro cerrado", "Ya existe una cuenta de Director.")
                mostrar_login()
                return

            cursor.execute("SELECT id_usuario FROM usuarios WHERE usuario=%s", (usuario,))
            if cursor.fetchone():
                conexion.rollback()
                messagebox.showwarning("Registro", "Ese nombre de usuario ya está ocupado.")
                return

            cursor.execute(
                "INSERT INTO usuarios (usuario, contrasena, rol, estado) VALUES (%s,%s,'Directivo','Activo')",
                (usuario, crear_hash(clave))
            )
            id_usuario = cursor.lastrowid
            cursor.execute(
                "INSERT INTO directores (id_usuario, nombre, apellido) VALUES (%s,%s,%s)",
                (id_usuario, nombre, apellido)
            )
            id_director = cursor.lastrowid
            cursor.execute(
                "UPDATE control_sistema SET id_director=%s WHERE id_control=1 AND id_director IS NULL",
                (id_director,)
            )
            if cursor.rowcount != 1:
                raise Error("No se pudo asignar la cuenta única de Director.")
            conexion.commit()
            messagebox.showinfo(
                "Cuenta creada",
                "La cuenta única del Director se creó correctamente. "
                "Ahora podrá iniciar sesión y registrar hasta seis Docentes."
            )
            mostrar_login()
        except Error as error:
            conexion.rollback()
            messagebox.showerror("Error al crear Director", str(error))
        finally:
            cursor.close()

    crear_boton(tarjeta, "Crear cuenta de Director", guardar_director, COLOR_VERDE).pack(
        fill="x", pady=(20, 7), ipady=5
    )
    crear_boton(tarjeta, "Volver al inicio de sesión", mostrar_login, COLOR_AZUL_OSCURO).pack(
        fill="x", ipady=5
    )
    tk.Label(contenedor, text="SAT NEZA HQX  •  CONTROL ESCOLAR",
             font=(FUENTE_TEXTO, 10, "bold"), fg=COLOR_DORADO,
             bg=COLOR_FONDO).pack(pady=12)


def mostrar_gestion_docentes():
    """Permite exclusivamente al Director crear hasta seis cuentas docentes."""
    if not es_director_autorizado():
        messagebox.showerror("Acceso restringido", "Solo el Director autorizado puede crear cuentas docentes.")
        mostrar_login()
        return

    limpiar_ventana()
    mostrar_encabezado("SAT NEZA HQX", "ADMINISTRACIÓN DE DOCENTES")
    crear_titulo(ventana, "Crear cuentas de Docentes").pack(pady=(15, 5))

    total = contar_docentes()
    limite = 6
    tk.Label(
        ventana,
        text=f"Cuentas docentes registradas: {total} de {limite}",
        font=(FUENTE_TEXTO, 13, "bold"), bg=COLOR_FONDO, fg=COLOR_DORADO
    ).pack(pady=5)

    tarjeta = tk.Frame(ventana, bg=COLOR_PANEL, padx=25, pady=18)
    tarjeta.pack(fill="x", padx=35, pady=12)
    campos = {}
    for etiqueta, clave in (("Nombre", "nombre"), ("Apellido", "apellido"),
                            ("Nombre de usuario", "usuario"), ("Contraseña", "clave"),
                            ("Confirmar contraseña", "confirmar")):
        tk.Label(tarjeta, text=etiqueta, font=(FUENTE_TEXTO, 11, "bold"),
                 bg=COLOR_PANEL, fg=COLOR_TEXTO).pack(anchor="w", pady=(5, 2))
        campos[clave] = crear_campo(tarjeta, ancho=42,
                                    ocultar=clave in ("clave", "confirmar"))
        campos[clave].pack(fill="x", pady=(0, 4), ipady=4)

    def guardar_docente():
        if not es_director_autorizado():
            messagebox.showerror("Acceso restringido", "Solo el Director puede realizar esta acción.")
            return
        nombre = campos["nombre"].get().strip()
        apellido = campos["apellido"].get().strip()
        usuario = campos["usuario"].get().strip()
        clave = campos["clave"].get()
        confirmar = campos["confirmar"].get()
        if not all((nombre, apellido, usuario, clave, confirmar)):
            messagebox.showwarning("Registro de Docente", "Completa todos los campos.")
            return
        if len(usuario) < 4:
            messagebox.showwarning("Registro de Docente", "El usuario debe tener al menos 4 caracteres.")
            return
        if len(clave) < 8:
            messagebox.showwarning("Registro de Docente", "La contraseña debe tener al menos 8 caracteres.")
            return
        if clave != confirmar:
            messagebox.showwarning("Registro de Docente", "Las contraseñas no coinciden.")
            return

        cursor = conexion.cursor()
        try:
            conexion.start_transaction()
            cursor.execute(
                "SELECT id_director, limite_docentes FROM control_sistema WHERE id_control=1 FOR UPDATE"
            )
            control = cursor.fetchone()
            cursor.execute(
                "SELECT id_director FROM directores WHERE id_usuario=%s",
                (usuario_actual_id,)
            )
            director = cursor.fetchone()
            if not control or not director or control[0] != director[0]:
                conexion.rollback()
                messagebox.showerror("Acceso restringido", "Tu cuenta no es el Director autorizado.")
                return

            cursor.execute(
                "SELECT COUNT(*) FROM docentes d "
                "INNER JOIN usuarios u ON u.id_usuario=d.id_usuario WHERE u.rol='Profesor'"
            )
            total_actual = int(cursor.fetchone()[0])
            maximo = int(control[1]) if control[1] is not None else 6
            if total_actual >= maximo:
                conexion.rollback()
                messagebox.showwarning(
                    "Límite alcanzado",
                    f"Ya se registraron las {maximo} cuentas docentes permitidas."
                )
                return

            cursor.execute("SELECT id_usuario FROM usuarios WHERE usuario=%s", (usuario,))
            if cursor.fetchone():
                conexion.rollback()
                messagebox.showwarning("Registro de Docente", "Ese nombre de usuario ya está ocupado.")
                return

            cursor.execute(
                "INSERT INTO usuarios (usuario, contrasena, rol, estado) VALUES (%s,%s,'Profesor','Activo')",
                (usuario, crear_hash(clave))
            )
            id_usuario = cursor.lastrowid
            cursor.execute(
                "INSERT INTO docentes (id_usuario, nombre, apellido, id_grupo) VALUES (%s,%s,%s,NULL)",
                (id_usuario, nombre, apellido)
            )
            conexion.commit()
            # Se muestran las credenciales una sola vez para que el Director
            # pueda entregárselas al docente. La contraseña no se guarda en texto plano.
            messagebox.showinfo(
                "Cuenta docente creada",
                f"La cuenta de {nombre} {apellido} se creó correctamente.\n\n"
                f"USUARIO: {usuario}\n"
                f"CONTRASEÑA INICIAL: {clave}\n\n"
                "Entrega estas credenciales directamente al docente. Por seguridad, "
                "la contraseña no podrá consultarse nuevamente desde el sistema."
            )
            mostrar_gestion_docentes()
        except Error as error:
            conexion.rollback()
            messagebox.showerror("Error al crear Docente", str(error))
        finally:
            cursor.close()

    crear_boton(tarjeta, "Crear cuenta de Docente", guardar_docente, COLOR_VERDE).pack(
        fill="x", pady=(14, 4), ipady=5
    )

    crear_etiqueta(ventana, "Docentes registrados:", tamano=12, negrita=True).pack(pady=(8, 2))
    lista = mostrar_lista(ventana, altura=7)
    filas = ejecutar_sql(
        "SELECT d.nombre, d.apellido, u.usuario, u.estado "
        "FROM docentes d INNER JOIN usuarios u ON u.id_usuario=d.id_usuario "
        "WHERE u.rol='Profesor' ORDER BY d.id_docente",
        obtener=True
    )
    if filas:
        for fila in filas:
            lista.insert("end", f"{fila['nombre']} {fila['apellido']} | Usuario: {fila['usuario']} | {fila['estado']}")
    else:
        lista.insert("end", "Todavía no hay cuentas docentes registradas.")

    crear_boton(ventana, "Volver al panel Directivo", mostrar_director, COLOR_AZUL_OSCURO).pack(pady=10)


def mostrar_cambiar_clave_director():
    """Permite al único Director autorizado cambiar su propia contraseña."""
    if not es_director_autorizado():
        messagebox.showerror(
            "Acceso restringido",
            "Solo el Director autorizado puede cambiar la contraseña de Dirección."
        )
        mostrar_login()
        return

    limpiar_ventana()
    mostrar_encabezado("SAT NEZA HQX", "SEGURIDAD DE LA CUENTA")
    crear_titulo(ventana, "Cambiar contraseña del Director").pack(pady=(18, 8))

    tarjeta = tk.Frame(ventana, bg=COLOR_PANEL, padx=35, pady=25,
                       highlightbackground=COLOR_DORADO, highlightthickness=1)
    tarjeta.pack(padx=25, pady=15)

    tk.Label(
        tarjeta,
        text="Para proteger la cuenta, confirma primero tu contraseña actual.",
        font=(FUENTE_TEXTO, 11), bg=COLOR_PANEL, fg=COLOR_SUAVE,
        wraplength=480, justify="center"
    ).pack(pady=(0, 12))

    campos = {}
    for etiqueta, clave in (
        ("Contraseña actual", "actual"),
        ("Nueva contraseña", "nueva"),
        ("Confirmar nueva contraseña", "confirmar")
    ):
        tk.Label(
            tarjeta, text=etiqueta, font=(FUENTE_TEXTO, 11, "bold"),
            bg=COLOR_PANEL, fg=COLOR_TEXTO
        ).pack(anchor="w", pady=(8, 2))
        campos[clave] = crear_campo(tarjeta, ancho=42, ocultar=True)
        campos[clave].pack(fill="x", ipady=5)

    def guardar_nueva_clave():
        if not es_director_autorizado():
            messagebox.showerror("Acceso restringido", "La sesión ya no corresponde al Director autorizado.")
            mostrar_login()
            return

        actual = campos["actual"].get()
        nueva = campos["nueva"].get()
        confirmar = campos["confirmar"].get()

        if not all((actual, nueva, confirmar)):
            messagebox.showwarning("Cambiar contraseña", "Completa todos los campos.")
            return
        if len(nueva) < 8:
            messagebox.showwarning(
                "Contraseña no válida",
                "La nueva contraseña debe tener al menos 8 caracteres."
            )
            return
        if nueva != confirmar:
            messagebox.showwarning("Cambiar contraseña", "La nueva contraseña y su confirmación no coinciden.")
            return
        if nueva == actual:
            messagebox.showwarning("Cambiar contraseña", "La nueva contraseña debe ser diferente de la actual.")
            return

        cursor = conexion.cursor(dictionary=True)
        try:
            conexion.start_transaction()
            cursor.execute(
                "SELECT contrasena FROM usuarios "
                "WHERE id_usuario=%s AND rol='Directivo' AND estado='Activo' FOR UPDATE",
                (usuario_actual_id,)
            )
            cuenta = cursor.fetchone()
            if not cuenta or not comprobar_clave(actual, cuenta["contrasena"]):
                conexion.rollback()
                messagebox.showerror("Contraseña incorrecta", "La contraseña actual no es correcta.")
                return

            cursor.execute(
                "UPDATE usuarios SET contrasena=%s "
                "WHERE id_usuario=%s AND rol='Directivo' AND estado='Activo'",
                (crear_hash(nueva), usuario_actual_id)
            )
            if cursor.rowcount != 1:
                raise Error("No se pudo actualizar la contraseña del Director.")

            conexion.commit()
            messagebox.showinfo(
                "Contraseña actualizada",
                "La contraseña del Director se cambió correctamente. "
                "La próxima vez tendrás que iniciar sesión con la nueva contraseña."
            )
            mostrar_director()
        except Error as error:
            conexion.rollback()
            messagebox.showerror("Error al cambiar contraseña", str(error))
        finally:
            cursor.close()

    crear_boton(
        tarjeta, "Guardar nueva contraseña", guardar_nueva_clave, COLOR_VERDE
    ).pack(fill="x", pady=(20, 7), ipady=6)
    crear_boton(
        tarjeta, "Cancelar y volver al panel", mostrar_director, COLOR_AZUL_OSCURO
    ).pack(fill="x", ipady=6)


def mostrar_login():
    """Inicio de sesión: detecta automáticamente si ingresa Director o Docente."""
    global usuario_actual_id, rol_actual
    usuario_actual_id = None
    rol_actual = None
    limpiar_ventana()
    ventana.configure(bg=COLOR_FONDO)

    contenedor = tk.Frame(ventana, bg=COLOR_FONDO)
    contenedor.pack(fill="both", expand=True)

    tk.Label(contenedor, text="SAT NEZA HQX", font=(FUENTE_TITULO, 34, "bold"),
             fg="white", bg=COLOR_FONDO).pack(pady=(35, 5))
    tk.Label(contenedor, text="SISTEMA DE CONTROL ESCOLAR", font=(FUENTE_TEXTO, 15, "bold"),
             fg=COLOR_DORADO, bg=COLOR_FONDO).pack(pady=(0, 18))
    tk.Label(contenedor, text="COMPROMETIDOS CON LA EDUCACIÓN Y EL FUTURO",
             font=(FUENTE_TEXTO, 11), fg="#D5DFEA", bg=COLOR_FONDO).pack(pady=(0, 20))

    tarjeta = tk.Frame(contenedor, bg=COLOR_PANEL, padx=55, pady=35,
                       highlightbackground=COLOR_DORADO, highlightthickness=2)
    tarjeta.pack(padx=20, pady=8)
    tk.Label(tarjeta, text="Inicio de sesión", font=(FUENTE_TITULO, 27, "bold"),
             fg=COLOR_AZUL, bg=COLOR_PANEL).pack(pady=(0, 5))
    tk.Label(tarjeta, text="Ingresa tus credenciales para continuar", font=(FUENTE_TEXTO, 12),
             fg=COLOR_SUAVE, bg=COLOR_PANEL).pack(pady=(0, 20))

    tk.Label(tarjeta, text="Usuario", font=(FUENTE_TEXTO, 12, "bold"),
             fg=COLOR_TEXTO, bg=COLOR_PANEL).pack(anchor="w")
    entrada_usuario = crear_campo(tarjeta, ancho=38)
    entrada_usuario.pack(fill="x", pady=(5, 14), ipady=6)

    tk.Label(tarjeta, text="Contraseña", font=(FUENTE_TEXTO, 12, "bold"),
             fg=COLOR_TEXTO, bg=COLOR_PANEL).pack(anchor="w")
    fila_clave = tk.Frame(tarjeta, bg=COLOR_PANEL)
    fila_clave.pack(fill="x", pady=(5, 14))
    entrada_clave = crear_campo(fila_clave, ancho=33, ocultar=True)
    entrada_clave.pack(side="left", fill="x", expand=True, ipady=6)
    mostrar_clave = tk.BooleanVar(value=False)

    def alternar_visibilidad_clave():
        mostrar_clave.set(not mostrar_clave.get())
        entrada_clave.configure(show="" if mostrar_clave.get() else "*")
        boton_ojo.configure(text="Ocultar" if mostrar_clave.get() else "👁")

    boton_ojo = tk.Button(
        fila_clave, text="👁", command=alternar_visibilidad_clave,
        font=(FUENTE_TEXTO, 10, "bold"), bg=COLOR_DORADO, fg=COLOR_AZUL,
        activebackground=COLOR_AMARILLO, relief="flat", cursor="hand2", padx=10
    )
    boton_ojo.pack(side="left", padx=(7, 0), ipady=5)

    def revisar_acceso():
        global usuario_actual_id, rol_actual
        usuario = entrada_usuario.get().strip()
        clave = entrada_clave.get()

        if not usuario or not clave:
            messagebox.showwarning("Inicio de sesión", "Escribe tu usuario y contraseña.")
            return

        usuario_bd = ejecutar_sql(
            "SELECT id_usuario, usuario, contrasena, rol FROM usuarios "
            "WHERE usuario=%s AND estado='Activo'",
            (usuario,), True
        )
        if not usuario_bd or not comprobar_clave(clave, usuario_bd[0]["contrasena"]):
            messagebox.showerror("Acceso denegado", "El usuario o la contraseña son incorrectos.")
            return

        rol = (usuario_bd[0]["rol"] or "").strip().lower()
        id_usuario = usuario_bd[0]["id_usuario"]

        # El cargo se consulta en MySQL: solo el Director vinculado a control_sistema
        # entra al panel Directivo; los profesores requieren perfil en docentes.
        if rol == "directivo":
            director = ejecutar_sql(
                "SELECT d.id_usuario FROM control_sistema c "
                "INNER JOIN directores d ON d.id_director=c.id_director "
                "WHERE c.id_control=1",
                obtener=True
            )
            if not director or director[0]["id_usuario"] != id_usuario:
                messagebox.showerror(
                    "Acceso denegado",
                    "Esta cuenta no corresponde al Director autorizado del sistema."
                )
                return
            abrir_panel = mostrar_director

        elif rol == "profesor":
            perfil_docente = ejecutar_sql(
                "SELECT id_docente FROM docentes WHERE id_usuario=%s",
                (id_usuario,), True
            )
            if not perfil_docente:
                messagebox.showerror(
                    "Acceso denegado",
                    "La cuenta no tiene un perfil de Docente registrado. Contacta al Director."
                )
                return
            abrir_panel = mostrar_profesor

        else:
            messagebox.showerror(
                "Acceso denegado",
                "Esta cuenta no tiene un perfil autorizado para ingresar al sistema."
            )
            return

        # Convierte contraseñas antiguas en texto normal al formato protegido.
        if not usuario_bd[0]["contrasena"].startswith("pbkdf2$"):
            ejecutar_sql(
                "UPDATE usuarios SET contrasena=%s WHERE id_usuario=%s",
                (crear_hash(clave), id_usuario)
            )

        usuario_actual_id = id_usuario
        rol_actual = usuario_bd[0]["rol"]
        abrir_panel()

    crear_boton(tarjeta, "Ingresar", revisar_acceso, COLOR_AZUL_OSCURO).pack(
        fill="x", pady=(18, 8), ipady=7
    )
    entrada_clave.bind("<Return>", lambda _evento: revisar_acceso())
    entrada_usuario.bind("<Return>", lambda _evento: entrada_clave.focus_set())

    if director_ya_registrado():
        tk.Label(
            tarjeta,
            text="Registro de Dirección cerrado. El Director administra las cuentas docentes.",
            font=(FUENTE_TEXTO, 10), fg=COLOR_SUAVE, bg=COLOR_PANEL,
            wraplength=360, justify="center"
        ).pack(fill="x", pady=(8, 0))
    else:
        crear_boton(
            tarjeta, "Crear cuenta del Director (registro único)",
            mostrar_registro, COLOR_VERDE
        ).pack(fill="x", ipady=7)
        tk.Label(
            tarjeta,
            text="Disponible únicamente durante la configuración inicial. "
                 "Después de crear al Director, este botón desaparecerá.",
            font=(FUENTE_TEXTO, 9), fg=COLOR_SUAVE, bg=COLOR_PANEL,
            wraplength=360, justify="center"
        ).pack(fill="x", pady=(7, 0))

    tk.Label(contenedor, text="ASISTENCIA  •  RETARDOS  •  FALTAS  •  CONDUCTA",
             font=(FUENTE_TEXTO, 10, "bold"), fg=COLOR_DORADO, bg=COLOR_FONDO).pack(pady=20)


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

    total_docentes = contar_docentes()
    crear_boton(
        fila_botones,
        f"Gestionar docentes ({total_docentes}/6)",
        mostrar_gestion_docentes,
        COLOR_VERDE
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

    # Acceso exclusivo del Director a la configuración de su contraseña.
    fila_seguridad = tk.Frame(ventana, bg=COLOR_FONDO)
    fila_seguridad.pack(fill="x", padx=14, pady=(0, 4))
    crear_boton(
        fila_seguridad,
        "Cambiar contraseña del Director",
        mostrar_cambiar_clave_director,
        COLOR_AZUL_OSCURO
    ).pack(side="right", padx=4)

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
    # Si te queda raro, es porque crear_selector_alumno hace pack, lo dejamos así

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

if __name__ == "__main__":
    if conectar_bd():
        if cargar_datos():
            mostrar_login()
            ventana.mainloop()
        if conexion and conexion.is_connected():
            conexion.close()
