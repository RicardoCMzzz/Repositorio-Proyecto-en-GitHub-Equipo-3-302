import mysql.connector
import tkinter as tk
from tkinter import messagebox

def conectar():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="302",
    )

# GUARDAR USUARIOS
def guardar_usuario():
    con = conectar()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO usuarios (usuario, contrasena, rol, estado) VALUES (%s, %s, %s, %s)",
        (usuario.get(), contrasena.get(), rol.get(), estado.get()),
    )
    con.commit()
    cur.close()
    con.close()
    messagebox.showinfo("USUARIOS", "Guardado")


# GUARDAR DIRECTORES
def guardar_director():
    con = conectar()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO directores (id_usuario, nombre, apellido) VALUES (%s, %s, %s)",
        (id_usuario.get(), nombre.get(), apellido.get()),
    )
    con.commit()
    cur.close()
    con.close()
    messagebox.showinfo("DIRECTORES", "Guardado")


# VENTANA PRINCIPAL
ventana = tk.Tk()
ventana.title("USUARIOS Y DIRECTORES")

# USUARIOS
tk.Label(ventana, text="CRUD USUARIOS").grid(row=0, column=0, columnspan=2)

tk.Label(ventana, text="Usuario").grid(row=1, column=0)
usuario = tk.Entry(ventana)
usuario.grid(row=1, column=1)

tk.Label(ventana, text="Contraseña").grid(row=2, column=0)
contrasena = tk.Entry(ventana)
contrasena.grid(row=2, column=1)

tk.Label(ventana, text="Rol").grid(row=3, column=0)
rol = tk.Entry(ventana)
rol.grid(row=3, column=1)

tk.Label(ventana, text="Estado").grid(row=4, column=0)
estado = tk.Entry(ventana)
estado.grid(row=4, column=1)

tk.Button(ventana, text="Guardar Usuario", command=guardar_usuario).grid(row=5, column=0, columnspan=2, pady=5)


# DIRECTORES
tk.Label(ventana, text="CRUD DIRECTORES").grid(row=6, column=0, columnspan=2)

tk.Label(ventana, text="ID Usuario").grid(row=7, column=0)
id_usuario = tk.Entry(ventana)
id_usuario.grid(row=7, column=1)

tk.Label(ventana, text="Nombre").grid(row=8, column=0)
nombre = tk.Entry(ventana)
nombre.grid(row=8, column=1)

tk.Label(ventana, text="Apellido").grid(row=9, column=0)
apellido = tk.Entry(ventana)
apellido.grid(row=9, column=1)

tk.Button(ventana, text="Guardar Director", command=guardar_director).grid(row=10, column=0, columnspan=2, pady=5)

ventana.mainloop()