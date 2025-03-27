import mysql.connector
import math
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
import time
from tkinter import messagebox, simpledialog
from datetime import datetime

#Conexión a la BD
def conectar():
    try:
        conexion = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="series_db"
        )
        print("Conexión exitosa a la base de datos")
        return conexion
    except mysql.connector.Error as err:
        print(f"Error de conexión: {err}")
        if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            try:
                conexion = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    password=""
                )
                cursor = conexion.cursor()
                cursor.execute("CREATE DATABASE series_db")
                print("Base de datos 'series_db' creada exitosamente")
                conexion.close()
                return mysql.connector.connect(
                    host="localhost",
                    user="root",
                    password="",
                    database="series_db"
                )
            except mysql.connector.Error as err:
                print(f"Error al crear la base de datos: {err}")
                return None
        return None

#Cálculo de funciones
def taylor_coseno(x, n):
    return sum(((-1) ** k) * (x ** (2 * k)) / math.factorial(2 * k) for k in range(n))

def fourier_serie(n):
    x = np.linspace(-np.pi, np.pi, 400)
    y = np.zeros_like(x)
    for k in range(1, n * 2, 2):
        y += np.sin(k * x) / k
    y *= 4 / np.pi
    return x, y

def fibonacci(n):
    serie = [0, 1]
    for _ in range(n - 2):
        serie.append(serie[-1] + serie[-2])
    return serie[:n]

#Crear tablas en la BD
def crear_tablas():
    try:
        conexion = conectar()
        cursor = conexion.cursor()
        #Tabla usuarios
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(100) NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        
        #Tabla serie Taylor
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS taylor_terminos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            x FLOAT NOT NULL,
            termino_num INT NOT NULL,
            valor_termino FLOAT NOT NULL,
            suma_parcial FLOAT NOT NULL,
            error_parcial FLOAT NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES usuarios(id)
        )""")
        
        #Tabla serie Fourier
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS fourier_terminos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            termino_num INT NOT NULL,
            k_valor INT NOT NULL,  # Valor de k en el término sin(kx)/k
            amplitud FLOAT NOT NULL,  # 4/(πk)
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES usuarios(id)
        )""")
        
        #Tabla serie Fibonacci
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS fibonacci_terminos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            termino_num INT NOT NULL,
            valor INT NOT NULL,
            razon_aurea FLOAT,  # φ ≈ 1.618 (opcional, para análisis)
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES usuarios(id)
        )""")
        
        conexion.commit()
        print("Tablas creadas exitosamente")
    except Exception as e:
        print(f"Error al crear tablas: {e}")
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()

#Funciones de insersión a la BD
            
#Insertar Taylor
def insertar_taylor(user_id, x, n):
    try:
        conexion = conectar()
        cursor = conexion.cursor()
        
        suma_parcial = 0
        for k in range(n):
            termino = ((-1) ** k) * (x ** (2 * k)) / math.factorial(2 * k)
            suma_parcial += termino
            error_parcial = abs(suma_parcial - math.cos(x))
            
            sql = """INSERT INTO taylor_terminos 
                     (user_id, x, termino_num, valor_termino, suma_parcial, error_parcial) 
                     VALUES (%s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, (user_id, x, k+1, termino, suma_parcial, error_parcial))
        
        conexion.commit()
        print(f"Insertados {n} términos de Taylor para x={x}")
    except Exception as e:
        print(f"Error al insertar Taylor: {e}")
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()

#Insertar Fourier
def insertar_fourier(user_id, n):
    try:
        conexion = conectar()
        cursor = conexion.cursor()
        
        termino_num = 1
        for k in range(1, n * 2, 2):  # Solo términos impares
            amplitud = 4 / (np.pi * k)
            
            sql = """INSERT INTO fourier_terminos 
                     (user_id, termino_num, k_valor, amplitud) 
                     VALUES (%s, %s, %s, %s)"""
            cursor.execute(sql, (user_id, termino_num, k, amplitud))
            termino_num += 1
        
        conexion.commit()
        print(f"Insertados {n} términos de Fourier")
    except Exception as e:
        print(f"Error al insertar Fourier: {e}")
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()

#Insertar Fibonacci
def insertar_fibonacci(user_id, n):
    try:
        serie = fibonacci(n)
        if not serie:
            print("Error: Serie Fibonacci vacía")
            return
            
        conexion = conectar()
        if not conexion:
            print("Error: No se pudo conectar a la base de datos")
            return
            
        cursor = conexion.cursor()
        
        for i, valor in enumerate(serie, start=1):
            razon_aurea = None
            if i > 1 and serie[i-2] != 0:
                razon_aurea = serie[i-1] / serie[i-2]
            
            sql = """INSERT INTO fibonacci_terminos 
                     (user_id, termino_num, valor, razon_aurea) 
                     VALUES (%s, %s, %s, %s)"""
            cursor.execute(sql, (user_id, i, valor, razon_aurea))
        conexion.commit()
        print(f"Se insertaron correctamente {n} términos de Fibonacci")
        
    except mysql.connector.Error as err:
        print(f"Error de MySQL al insertar Fibonacci: {err}")
        if 'conexion' in locals() and conexion.is_connected():
            conexion.rollback()
    except Exception as e:
        print(f"Error inesperado al insertar Fibonacci: {e}")
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()
            
#Gráficas de las series

#Gráfica de coseno de Taylor
# Gráfica de coseno de Taylor con error en tiempo real
def graficar_taylor(n):
    """Muestra gráfica de la serie de Taylor para coseno con error en tiempo real"""
    plt.ion()  # Activar modo interactivo
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()
    
    x = np.linspace(-2*np.pi, 2*np.pi, 100)
    y_real = np.cos(x)
    
    # Dibujar la función real una sola vez
    ax1.plot(x, y_real, label="Coseno real", linestyle="dashed", color='blue')
    
    y_taylor = np.zeros_like(x)
    for k in range(n):
        termino = ((-1) ** k) * (x ** (2 * k)) / math.factorial(2 * k)
        y_taylor += termino
        error = np.abs(y_taylor - y_real)
        
        # Limpiar y actualizar gráfica
        ax1.clear()
        ax2.clear()
        
        # Volver a dibujar todo
        ax1.plot(x, y_real, label="Coseno real", linestyle="dashed", color='blue')
        ax1.plot(x, y_taylor, label=f"Aprox. Taylor (n={k+1})", color='red')
        ax1.set_xlabel('x')
        ax1.set_ylabel('Valor de la función', color='black')
        ax1.tick_params(axis='y', labelcolor='black')
        ax1.set_title(f"Aproximación de Taylor para cos(x) con {k+1}/{n} términos")
        ax1.grid(True)
        
        ax2.plot(x, error, label="Error absoluto", color='green', linestyle=':')
        ax2.set_ylabel('Error absoluto', color='green')
        ax2.tick_params(axis='y', labelcolor='green')
        
        # Combinar leyendas
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        plt.pause(0.5)  # Pausa para visualización
    
    plt.ioff()
    plt.show()

# Gráfica de Fourier en tiempo real
def graficar_fourier(n):
    """Muestra gráfica de la serie de Fourier para onda cuadrada en tiempo real"""
    plt.ion()
    fig, ax = plt.subplots(figsize=(10, 5))
    
    x = np.linspace(-np.pi, np.pi, 400)
    y = np.zeros_like(x)
    
    termino_actual = 0
    for k in range(1, n * 2, 2):  # Solo términos impares
        y += np.sin(k * x) / k
        y_actual = y * (4 / np.pi)
        termino_actual += 1
        
        ax.clear()
        ax.plot(x, y_actual, label=f"Aprox. Fourier (n={termino_actual})", color="blue")
        ax.set_title(f"Serie de Fourier - Aproximación de Onda Cuadrada (término {termino_actual}/{n})")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.legend()
        ax.grid()
        
        plt.pause(0.5)
    
    plt.ioff()
    plt.show()

#Gráfica de Fibonacci
# Gráfica de Fibonacci con número áureo en tiempo real
def graficar_fibonacci(n):
    """Muestra gráfica de la serie de Fibonacci y su convergencia al número áureo en tiempo real"""
    plt.ion()
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()
    
    serie = [0, 1]
    razones = []
    aureo = (1 + math.sqrt(5)) / 2
    
    for i in range(2, n):
        serie.append(serie[-1] + serie[-2])
        
        # Calcular razón actual si es posible
        if serie[-2] != 0:
            razones.append(serie[-1]/serie[-2])
        
        ax1.clear()
        ax2.clear()
        
        # Gráfica de la serie Fibonacci
        color_fib = 'green'
        ax1.set_xlabel('Índice')
        ax1.set_ylabel('Valor Fibonacci', color=color_fib)
        fib_line = ax1.plot(serie, marker="o", linestyle="-", color=color_fib, label="Serie Fibonacci")
        ax1.tick_params(axis='y', labelcolor=color_fib)
        ax1.grid(True)
        
        # Gráfica de las razones si hay datos
        if razones:
            color_ratio = 'purple'
            color_aureo = 'red'
            
            ax2.set_ylabel('Razón F(n+1)/F(n)', color=color_ratio)
            ratio_line = ax2.plot(range(1, len(razones)+1), razones, marker="o", linestyle="-", 
                                color=color_ratio, label="Razón Fibonacci")
            aureo_line = ax2.axhline(y=aureo, color=color_aureo, linestyle="--", label="Número áureo (φ)")
            ax2.tick_params(axis='y', labelcolor=color_ratio)
            
            # Combinar leyendas
            lines = fib_line + ratio_line + [aureo_line]
            labels = [l.get_label() for l in lines]
            ax1.legend(lines, labels, loc='upper left')
        
        ax1.set_title(f"Serie de Fibonacci (primeros {i+1} términos) y Convergencia al Número Áureo")
        plt.pause(0.5)
    
    plt.ioff()
    plt.show()

class Aplicacion:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Series Matemáticas")
        self.root.geometry("400x300")
        
        #Verificar/Crear tablas al iniciar
        crear_tablas()
        self.frame = tk.Frame(root)
        self.frame.pack(pady=20)
        tk.Label(self.frame, text="Bienvenido al Sistema", font=("Arial", 14)).grid(row=0, column=0, columnspan=2, pady=10)
        
        #Botones
        tk.Button(self.frame, text="Registrarse", command=self.registrar_usuario, width=20).grid(row=1, column=0, pady=5, padx=5)
        tk.Button(self.frame, text="Iniciar Sesión", command=self.iniciar_sesion, width=20).grid(row=1, column=1, pady=5, padx=5)
        tk.Button(self.frame, text="Salir", command=root.quit, width=20).grid(row=2, column=0, columnspan=2, pady=10)
        
        #Variable para almacenar el ID del usuario
        self.user_id = None

    #Función de registro de usuario
    def registrar_usuario(self):
        """Ventana de registro de usuario"""
        ventana = tk.Toplevel(self.root)
        ventana.title("Registro")
        ventana.geometry("300x200")
        
        tk.Label(ventana, text="Usuario:").pack(pady=5)
        self.entry_user = tk.Entry(ventana)
        self.entry_user.pack(pady=5)
        
        tk.Label(ventana, text="Contraseña:").pack(pady=5)
        self.entry_pass = tk.Entry(ventana, show="*")
        self.entry_pass.pack(pady=5)
        
        tk.Button(ventana, text="Registrar", command=self.guardar_usuario).pack(pady=10)
    
    def guardar_usuario(self):
        """Guarda un nuevo usuario en la base de datos"""
        username = self.entry_user.get()
        password = self.entry_pass.get()
        
        if not username or not password:
            messagebox.showwarning("Error", "Todos los campos son obligatorios")
            return
        
        try:
            conexion = conectar()
            cursor = conexion.cursor()
            sql = "INSERT INTO usuarios (username, password) VALUES (%s, %s)"
            cursor.execute(sql, (username, password))
            conexion.commit()
            messagebox.showinfo("Éxito", "Usuario registrado correctamente")
            self.entry_user.delete(0, tk.END)
            self.entry_pass.delete(0, tk.END)
        except mysql.connector.IntegrityError:
            messagebox.showerror("Error", "El usuario ya existe")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error: {e}")
        finally:
            if conexion.is_connected():
                cursor.close()
                conexion.close()
    
    #Inicio de Sesión
    def iniciar_sesion(self):
        """Ventana de inicio de sesión"""
        ventana = tk.Toplevel(self.root)
        ventana.title("Inicio de Sesión")
        ventana.geometry("300x200")
        
        tk.Label(ventana, text="Usuario:").pack(pady=5)
        self.entry_login_user = tk.Entry(ventana)
        self.entry_login_user.pack(pady=5)
        
        tk.Label(ventana, text="Contraseña:").pack(pady=5)
        self.entry_login_pass = tk.Entry(ventana, show="*")
        self.entry_login_pass.pack(pady=5)
        
        tk.Button(ventana, text="Iniciar Sesión", command=self.verificar_usuario).pack(pady=10)
    
    #Verificación de usuario y contraseña
    def verificar_usuario(self):
        """Verifica las credenciales del usuario"""
        username = self.entry_login_user.get()
        password = self.entry_login_pass.get()
        
        try:
            conexion = conectar()
            cursor = conexion.cursor()
            sql = "SELECT id FROM usuarios WHERE username = %s AND password = %s"
            cursor.execute(sql, (username, password))
            usuario = cursor.fetchone()
            
            if usuario:
                self.user_id = usuario[0]
                messagebox.showinfo("Éxito", "Inicio de sesión exitoso")
                self.mostrar_menu_series()
                self.entry_login_user.delete(0, tk.END)
                self.entry_login_pass.delete(0, tk.END)
                cursor.close()
                conexion.close()
            else:
                messagebox.showerror("Error", "Usuario o contraseña incorrectos")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error: {e}")
        finally:
            if conexion.is_connected():
                cursor.close()
                conexion.close()
    
    #Menu
    def mostrar_menu_series(self):
        """Muestra el menú de selección de series"""
        ventana = tk.Toplevel(self.root)
        ventana.title("Seleccionar Serie")
        ventana.geometry("350x250")
        
        tk.Label(ventana, text="Seleccione una serie:", font=("Arial", 12)).pack(pady=10)
        
        tk.Button(ventana, text="Serie de Taylor (Coseno)", 
                 command=lambda: self.pedir_parametros("Taylor"), width=30).pack(pady=5)
        tk.Button(ventana, text="Serie de Fourier (Onda Cuadrada)", 
                 command=lambda: self.pedir_parametros("Fourier"), width=30).pack(pady=5)
        tk.Button(ventana, text="Serie de Fibonacci", 
                 command=lambda: self.pedir_parametros("Fibonacci"), width=30).pack(pady=5)
    
    def pedir_parametros(self, serie):
        """Pide parámetros y muestra la gráfica correspondiente"""
        n = simpledialog.askinteger("Parámetros", f"Ingrese número de términos para {serie}:", minvalue=1)
        
        if n is not None:
            if serie == "Taylor":
                x = simpledialog.askfloat("Parámetros", "Ingrese valor de x (en radianes):")
                if x is not None:
                    insertar_taylor(self.user_id, x, n)
                    graficar_taylor(n)
            elif serie == "Fourier":
                insertar_fourier(self.user_id, n)
                graficar_fourier(n)
            elif serie == "Fibonacci":
                insertar_fibonacci(self.user_id, n)
                graficar_fibonacci(n)
                

if __name__ == "__main__":
    root = tk.Tk()
    app = Aplicacion(root)
    root.mainloop()

