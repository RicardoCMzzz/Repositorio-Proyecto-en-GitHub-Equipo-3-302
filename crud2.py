import tkinter as tk 
from tkinter import messagebox 
import mysql.connector 
 
def conectar(): 
    return mysql.connector.connect( 
        host="localhost", 
        user="root", 
        password="",  
        database="crud2" 
    ) 
 
def guardar(): 
    id_docente = entry_id_docente.get() 
    id_usuario = entry_id_usuario.get() 
    nombre = entry_nombre.get() 
    apellidos = entry_apellidos.get() 
 
    if id_docente == "" or id_usuario == "" or nombre == "" or apellidos == "": 
        messagebox.showwarning("Faltan datos", "Llena todos los campos") 
        return 
 
    try: 
        con = conectar() 
        cursor = con.cursor() 
        sql = "INSERT INTO docentes (id_docente, id_usuario, nombre, apellidos) VALUES (%s, %s, %s, %s)" 
        valores = (id_docente, id_usuario, nombre, apellidos) 
        cursor.execute(sql, valores) 
        con.commit() 
        con.close() 
        messagebox.showinfo("Guardado", "Docente guardado en XAMPP correctamente") 
        limpiar() 
    except mysql.connector.Error as e: 
        messagebox.showerror("Error", f"No se pudo guardar:\n{e}") 
 
def limpiar(): 
    entry_id_docente.delete(0, tk.END) 
    entry_id_usuario.delete(0, tk.END) 
    entry_nombre.delete(0, tk.END) 
    entry_apellidos.delete(0, tk.END) 
 
ventana = tk.Tk() 
ventana.title("Registro de Docentes") 
ventana.geometry("350x280") 
 
tk.Label(ventana, text="REGISTRO DE DOCENTES", font=("Arial", 14, 
"bold")).pack(pady=10) 
tk.Label(ventana, text="ID Docente (PK):").pack() 
entry_id_docente = tk.Entry(ventana)
entry_id_docente.pack() 
tk.Label(ventana, text="ID Cargo (FK):").pack() 
entry_id_usuario = tk.Entry(ventana) 
entry_id_usuario.pack() 
tk.Label(ventana, text="Nombre:").pack() 
entry_nombre = tk.Entry(ventana) 
entry_nombre.pack() 
tk.Label(ventana, text="Apellidos:").pack() 
entry_apellidos = tk.Entry(ventana) 
entry_apellidos.pack() 
tk.Button(ventana, text="Guardar en XAMPP", bg="green", fg="white", 
command=guardar).pack(pady=15) 
ventana.mainloop() 