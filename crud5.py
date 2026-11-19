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

# REPORTE 1: ASISTENCIAS POR FECHA
def reporte_por_fecha():
    if fecha.get() == "":
        messagebox.showwarning("REPORTES", "Pon la fecha AAAA-MM-DD")
        return
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        SELECT a.matricula, a.nombre, a.apellido, asis.estado
        FROM asistencia asis
        JOIN alumnos a ON asis.id_alumno = a.id
        WHERE asis.fecha = %s
        ORDER BY a.nombre
    """, (fecha.get(),))
    datos = cur.fetchall()
    cur.close()
    con.close()
    lista.delete(0, tk.END)
    if not datos:
        lista.insert(tk.END, "No hay registros en esa fecha")
    else:
        for d in datos:
            lista.insert(tk.END, f"{d[0]} - {d[1]} {d[2]} - {d[3]}")

# REPORTE 2: HISTORIAL POR ALUMNO (POR MATRÍCULA)
def reporte_por_alumno():
    if matricula.get() == "":
        messagebox.showwarning("REPORTES", "Pon la matrícula del alumno")
        return
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        SELECT asis.fecha, asis.estado, asis.observaciones
        FROM asistencia asis
        JOIN alumnos a ON asis.id_alumno = a.id
        WHERE a.matricula = %s
        ORDER BY asis.fecha DESC
    """, (matricula.get(),))
    datos = cur.fetchall()
    cur.close()
    con.close()
    lista.delete(0, tk.END)
    if not datos:
        lista.insert(tk.END, "Ese alumno no tiene asistencias")
    else:
        for d in datos:
            lista.insert(tk.END, f"{d[0]} - {d[1]} - {d[2]}")

# REPORTE 3: RESUMEN GENERAL
def reporte_resumen():
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        SELECT estado, COUNT(*) 
        FROM asistencia 
        GROUP BY estado
    """)
    datos = cur.fetchall()
    cur.close()
    con.close()
    lista.delete(0, tk.END)
    if not datos:
        lista.insert(tk.END, "No hay datos todavía")
    else:
        for d in datos:
            lista.insert(tk.END, f"{d[0]}: {d[1]}")

# REPORTE 4: SOLO FALTAS Y RETARDOS
def reporte_faltas():
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        SELECT a.matricula, a.nombre, a.apellido, asis.fecha, asis.estado
        FROM asistencia asis
        JOIN alumnos a ON asis.id_alumno = a.id
        WHERE asis.estado != 'Presente'
        ORDER BY asis.fecha DESC
    """)
    datos = cur.fetchall()
    cur.close()
    con.close()
    lista.delete(0, tk.END)
    if not datos:
        lista.insert(tk.END, "No hay faltas ni retardos")
    else:
        for d in datos:
            lista.insert(tk.END, f"{d[0]} - {d[1]} {d[2]} - {d[3]} - {d[4]}")

# VENTANA PRINCIPAL
ventana = tk.Tk()
ventana.title("REPORTES - 302")
ventana.geometry("460x460")

tk.Label(ventana, text="REPORTES DE ASISTENCIA", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

tk.Label(ventana, text="Fecha (AAAA-MM-DD)").grid(row=1, column=0)
fecha = tk.Entry(ventana)
fecha.grid(row=1, column=1)
fecha.insert(0, str(date.today()))

tk.Label(ventana, text="Matrícula (para historial)").grid(row=2, column=0)
matricula = tk.Entry(ventana)
matricula.grid(row=2, column=1)

tk.Button(ventana, text="1. Ver Asistencias por Fecha", command=reporte_por_fecha).grid(row=3, column=0, columnspan=2, pady=3)
tk.Button(ventana, text="2. Historial por Alumno", command=reporte_por_alumno).grid(row=4, column=0, columnspan=2, pady=3)
tk.Button(ventana, text="3. Resumen General", command=reporte_resumen).grid(row=5, column=0, columnspan=2, pady=3)
tk.Button(ventana, text="4. Solo Faltas y Retardos", command=reporte_faltas).grid(row=6, column=0, columnspan=2, pady=3)

lista = tk.Listbox(ventana, width=60)
lista.grid(row=7, column=0, columnspan=2, pady=10)

ventana.mainloop()