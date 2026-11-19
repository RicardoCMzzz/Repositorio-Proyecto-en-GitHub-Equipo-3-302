import mysql.connector
import tkinter as tk
from tkinter import messagebox

def conectar():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="crud",
    )

# GUARDAR GRUPO (CREATE)
def guardar_grupo():
    if id_docente.get() == "" or nombre_grupo.get() == "":
        messagebox.showwarning("GRUPOS", "Llena ID Docente y Nombre del Grupo")
        return
    con = conectar()
    cur = con.cursor()
    # Verifica que el docente si exista para que no truene como la otra vez
    cur.execute("SELECT id_docente FROM docentes WHERE id_docente = %s", (id_docente.get(),))
    if cur.fetchone() is None:
        messagebox.showerror("ERROR", f"El docente con ID {id_docente.get()} NO existe. Primero registralo en docentes.")
        cur.close()
        con.close()
        return
    cur.execute(
        "INSERT INTO grupos (id_docente, nombre_grupo) VALUES (%s, %s)",
        (id_docente.get(), nombre_grupo.get()),
    )
    con.commit()
    cur.close()
    con.close()
    messagebox.showinfo("GRUPOS", "Grupo guardado")
    limpiar()
    ver_grupos()

# VER GRUPOS (READ)
def ver_grupos():
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        SELECT g.id_grupo, d.nombre, d.apellido, g.nombre_grupo
        FROM grupos g
        JOIN docentes d ON g.id_docente = d.id_docente
    """)
    datos = cur.fetchall()
    cur.close()
    con.close()
    lista.delete(0, tk.END)
    if not datos:
        lista.insert(tk.END, "No hay grupos registrados")
    else:
        for d in datos:
            lista.insert(tk.END, f"ID: {d[0]} | Docente: {d[1]} {d[2]} | Grupo: {d[3]}")

# ACTUALIZAR GRUPO (UPDATE)
def actualizar_grupo():
    if id_grupo.get() == "":
        messagebox.showwarning("GRUPOS", "Pon el ID del grupo a actualizar")
        return
    con = conectar()
    cur = con.cursor()
    cur.execute(
        "UPDATE grupos SET id_docente = %s, nombre_grupo = %s WHERE id_grupo = %s",
        (id_docente.get(), nombre_grupo.get(), id_grupo.get()),
    )
    con.commit()
    cur.close()
    con.close()
    messagebox.showinfo("GRUPOS", "Grupo actualizado")
    limpiar()
    ver_grupos()

# ELIMINAR GRUPO (DELETE)
def eliminar_grupo():
    if id_grupo.get() == "":
        messagebox.showwarning("GRUPOS", "Pon el ID del grupo a eliminar")
        return
    con = conectar()
    cur = con.cursor()
    cur.execute("DELETE FROM grupos WHERE id_grupo = %s", (id_grupo.get(),))
    con.commit()
    cur.close()
    con.close()
    messagebox.showinfo("GRUPOS", "Grupo eliminado")
    limpiar()
    ver_grupos()

def limpiar():
    id_grupo.delete(0, tk.END)
    id_docente.delete(0, tk.END)
    nombre_grupo.delete(0, tk.END)

# VENTANA PRINCIPAL
ventana = tk.Tk()
ventana.title("CRUD GRUPOS")
ventana.geometry("420x420")

tk.Label(ventana, text="CRUD GRUPOS").grid(row=0, column=0, columnspan=2, pady=5)

tk.Label(ventana, text="ID Grupo (solo para actualizar / eliminar)").grid(row=1, column=0)
id_grupo = tk.Entry(ventana)
id_grupo.grid(row=1, column=1)

tk.Label(ventana, text="ID Docente").grid(row=2, column=0)
id_docente = tk.Entry(ventana)
id_docente.grid(row=2, column=1)

tk.Label(ventana, text="Nombre del Grupo").grid(row=3, column=0)
nombre_grupo = tk.Entry(ventana)
nombre_grupo.grid(row=3, column=1)

tk.Button(ventana, text="Guardar Grupo", command=guardar_grupo).grid(row=4, column=0, columnspan=2, pady=5)
tk.Button(ventana, text="Ver Grupos", command=ver_grupos).grid(row=5, column=0, columnspan=2, pady=2)
tk.Button(ventana, text="Actualizar Grupo", command=actualizar_grupo).grid(row=6, column=0, columnspan=2, pady=2)
tk.Button(ventana, text="Eliminar Grupo", command=eliminar_grupo).grid(row=7, column=0, columnspan=2, pady=2)

lista = tk.Listbox(ventana, width=55)
lista.grid(row=8, column=0, columnspan=2, pady=10)

ventana.mainloop()