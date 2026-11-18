import mysql.connector
import tkinter as tk
from tkinter import messagebox
from datetime import date

def conectar():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="302",
    )

# GUARDAR ALUMNO (REGISTRO)
def guardar_alumno():
    if matricula.get() == "" or nombre.get() == "":
        messagebox.showwarning("ALUMNOS", "Llena matrícula y nombre")
        return
    con = conectar()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO alumnos (matricula, nombre, apellido, grupo) VALUES (%s, %s, %s, %s)",
        (matricula.get(), nombre.get(), apellido.get(), grupo.get()),
    )
    con.commit()
    cur.close()
    con.close()
    messagebox.showinfo("ALUMNOS", "Alumno registrado")
    matricula.delete(0, tk.END)
    nombre.delete(0, tk.END)
    apellido.delete(0, tk.END)
    grupo.delete(0, tk.END)

# REGISTRAR ASISTENCIA
def guardar_asistencia():
    if id_alumno.get() == "":
        messagebox.showwarning("ASISTENCIA", "Pon el ID del alumno")
        return
    con = conectar()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO asistencia (id_alumno, fecha, estado, observaciones) VALUES (%s, %s, %s, %s)",
        (id_alumno.get(), fecha.get(), estado.get(), observaciones.get()),
    )
    con.commit()
    cur.close()
    con.close()
    messagebox.showinfo("ASISTENCIA", "Asistencia guardada")

# VER ASISTENCIA DE HOY
def ver_asistencia():
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        SELECT a.matricula, a.nombre, a.apellido, asis.estado, asis.fecha
        FROM asistencia asis
        JOIN alumnos a ON asis.id_alumno = a.id
        WHERE asis.fecha = %s
    """, (fecha.get(),))
    datos = cur.fetchall()
    cur.close()
    con.close()

    lista.delete(0, tk.END)
    if not datos:
        lista.insert(tk.END, "No hay registros en esa fecha")
    else:
        for d in datos:
            lista.insert(tk.END, f"{d[0]} - {d[1]} {d[2]} - {d[3]} - {d[4]}")

# VENTANA PRINCIPAL
ventana = tk.Tk()
ventana.title("REGISTRO Y ASISTENCIA")
ventana.geometry("420x520")

# REGISTRO ALUMNOS
tk.Label(ventana, text="REGISTRO DE ALUMNOS", font=("Arial", 11, "bold")).grid(row=0, column=0, columnspan=2, pady=5)

tk.Label(ventana, text="Matrícula").grid(row=1, column=0)
matricula = tk.Entry(ventana)
matricula.grid(row=1, column=1)

tk.Label(ventana, text="Nombre").grid(row=2, column=0)
nombre = tk.Entry(ventana)
nombre.grid(row=2, column=1)

tk.Label(ventana, text="Apellido").grid(row=3, column=0)
apellido = tk.Entry(ventana)
apellido.grid(row=3, column=1)

tk.Label(ventana, text="Grupo").grid(row=4, column=0)
grupo = tk.Entry(ventana)
grupo.grid(row=4, column=1)

tk.Button(ventana, text="Guardar Alumno", command=guardar_alumno).grid(row=5, column=0, columnspan=2, pady=5)

# ASISTENCIA
tk.Label(ventana, text="ASISTENCIA", font=("Arial", 11, "bold")).grid(row=6, column=0, columnspan=2, pady=5)

tk.Label(ventana, text="ID Alumno").grid(row=7, column=0)
id_alumno = tk.Entry(ventana)
id_alumno.grid(row=7, column=1)

tk.Label(ventana, text="Fecha (AAAA-MM-DD)").grid(row=8, column=0)
fecha = tk.Entry(ventana)
fecha.grid(row=8, column=1)
fecha.insert(0, str(date.today()))

tk.Label(ventana, text="Estado (Presente/Falta/Retardo)").grid(row=9, column=0)
estado = tk.Entry(ventana)
estado.grid(row=9, column=1)

tk.Label(ventana, text="Observaciones").grid(row=10, column=0)
observaciones = tk.Entry(ventana)
observaciones.grid(row=10, column=1)

tk.Button(ventana, text="Guardar Asistencia", command=guardar_asistencia).grid(row=11, column=0, columnspan=2, pady=5)
tk.Button(ventana, text="Ver Asistencia del día", command=ver_asistencia).grid(row=12, column=0, columnspan=2, pady=5)

lista = tk.Listbox(ventana, width=55)
lista.grid(row=13, column=0, columnspan=2, pady=10)

ventana.mainloop()