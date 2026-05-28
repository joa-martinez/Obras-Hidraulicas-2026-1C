import tkinter as tk
from tkinter import ttk, messagebox
from scipy.optimize import fsolve
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import csv

# Importamos las funciones y constantes de tu script original
from Calculo_Q_salida_orificios import (
    calcular_caudal_orificios, 
    fsolve_D_residual, 
    calcular_H_desde_Q,
    calc_Q_reducida,
    exportar_a_csv,
    L, H
)
from Curva_descarga import (
    generar_curva_descarga,
    calcular_Q_descarga_libre,
    calcular_tramo3_pared_gruesa
)

class AplicacionOrificios:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculadora de Orificios")
        self.root.geometry("1050x560")
        self.root.resizable(False, False)

        # Crear Notebook
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)

        # Pestaña 1: Calculadora Principal
        self.tab1 = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab1, text='Cálculo Principal')

        # Pestaña 2: Curvas de Descarga
        self.tab2 = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab2, text='Curvas de Descarga')
        
        # Marco principal (Izquierdo)
        main_frame = ttk.Frame(self.tab1, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Marco Gráfico (Derecho)
        plot_frame = ttk.Frame(self.tab1, padding="15")
        plot_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Variables
        self.opcion = tk.StringVar(value="1")
        self.ultimo_resultado = None # Guardar datos para exportar a CSV
        
        # 1. Selector de Opciones
        ttk.Label(main_frame, text="Seleccione una operación:", font=("Helvetica", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        ttk.Radiobutton(main_frame, text="Calcular tirante aguas abajo (H) desde curva H-Q", 
                        variable=self.opcion, value="1", command=self.actualizar_ui).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)
        ttk.Radiobutton(main_frame, text="Optimizar diámetro (D) para caudal objetivo (Q)", 
                        variable=self.opcion, value="2", command=self.actualizar_ui).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=2)
        ttk.Radiobutton(main_frame, text="Calcular caudal (Q) a partir de diámetro (D)", 
                        variable=self.opcion, value="3", command=self.actualizar_ui).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # 2. Entrada de Datos
        frame_input = ttk.Frame(main_frame)
        frame_input.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=20)
        
        self.lbl_input = ttk.Label(frame_input, text="Diámetro (D) [m]:")
        self.lbl_input.grid(row=0, column=0, sticky=tk.W, padx=(0, 10), pady=2)
        
        self.entry_input = ttk.Entry(frame_input, width=15)
        self.entry_input.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # Entrada para la cantidad de orificios (N)
        ttk.Label(frame_input, text="Cantidad de orificios (N):").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=2)
        
        self.entry_n = ttk.Entry(frame_input, width=15)
        self.entry_n.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # Entrada para Tirante aguas abajo (H)
        self.lbl_h = ttk.Label(frame_input, text="Tirante aguas abajo (H) [m]:")
        self.lbl_h.grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=2)
        self.entry_h = ttk.Entry(frame_input, width=15)
        self.entry_h.grid(row=2, column=1, sticky=tk.W, pady=2)
        self.entry_h.insert(0, str(H))
        
        # 3. Botones de Acción
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Ejecutar Cálculo", command=self.calcular, width=20).grid(row=0, column=0, padx=10)
        ttk.Button(btn_frame, text="Exportar a CSV", command=self.exportar, width=20).grid(row=0, column=1, padx=10)
        
        # 4. Pantalla de Resultados
        ttk.Label(main_frame, text="Resultados:", font=("Helvetica", 10, "bold")).grid(row=6, column=0, sticky=tk.W, pady=(10, 5))
        self.text_out = tk.Text(main_frame, height=13, width=58, state='disabled', font=("Courier", 10), bg="#f4f4f4")
        self.text_out.grid(row=7, column=0, columnspan=2)
        
        # 5. Gráfico de H-Q
        self.fig = Figure(figsize=(5.2, 5.2), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.dibujar_curva_base()
        
        # Inicializamos el estado de la interfaz
        self.actualizar_ui()
        
        # Ejecutar cálculo al presionar Enter
        self.root.bind('<Return>', lambda event: self.calcular())
        
        self.setup_tab2()

    def setup_tab2(self):
        """Configura los widgets de la Pestaña 2."""
        frame_export = ttk.Frame(self.tab2, padding="10")
        frame_export.pack(pady=20, padx=20, fill="x")

        ttk.Label(frame_export, text="Parámetros para Curva de Descarga:", font=("Helvetica", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        ttk.Label(frame_export, text="Diámetro (D) [m]:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        self.entry_d_export = ttk.Entry(frame_export, width=15)
        self.entry_d_export.grid(row=1, column=1, sticky=tk.W, pady=5)

        ttk.Label(frame_export, text="Cantidad de orificios (N):").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        self.entry_n_export = ttk.Entry(frame_export, width=15)
        self.entry_n_export.grid(row=2, column=1, sticky=tk.W, pady=5)

        btn_frame_export = ttk.Frame(self.tab2, padding="10")
        btn_frame_export.pack(pady=10)

        ttk.Button(btn_frame_export, text="Exportar Tramo 1", command=self.exportar_tramo_1, width=25).grid(row=0, column=0, padx=10)
        ttk.Button(btn_frame_export, text="Exportar Tramo 2", command=self.exportar_tramo_2, width=25).grid(row=0, column=1, padx=10)
        ttk.Button(btn_frame_export, text="Exportar Tramo 3", command=self.exportar_tramo_3, width=25).grid(row=0, column=2, padx=10)

    def _get_export_params(self):
        try:
            d = float(self.entry_d_export.get())
            n = int(self.entry_n_export.get())
            if d <= 0 or n <= 0:
                messagebox.showerror("Error", "El diámetro y la cantidad de orificios deben ser positivos.")
                return None, None
            return d, n
        except ValueError:
            messagebox.showerror("Error", "Por favor ingrese números válidos para D y N.")
            return None, None

    def exportar_tramo_1(self):
        d, n = self._get_export_params()
        if d is None:
            return

        elevacion_base = d
        H0_max_libre = elevacion_base + 0.938 * d
        H0_tramo_libre = np.linspace(elevacion_base, H0_max_libre, 100)
        
        y = H0_tramo_libre - elevacion_base
        y = np.clip(y, 0, d * 0.938)
        
        theta = 2 * np.arccos(1 - (2 * y) / d)
        A = (d**2 / 8) * (theta - np.sin(theta))
        
        term_sin_theta_div_theta = np.zeros_like(theta)
        non_zero_mask = theta > 0
        term_sin_theta_div_theta[non_zero_mask] = np.sin(theta[non_zero_mask]) / theta[non_zero_mask]
        R = (d / 4) * (1 - term_sin_theta_div_theta)
        
        Q = n * (1 / 0.015) * A * (R**(2/3)) * np.sqrt(0.005)

        with open("descarga_tramo_1.csv", 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Cota H0", "Angulo theta", "Área", "Radio Hidráulico", "Caudal Q"])
            for i in range(len(H0_tramo_libre)):
                writer.writerow([H0_tramo_libre[i], theta[i], A[i], R[i], Q[i]])
        
        messagebox.showinfo("Éxito", "Resultados del Tramo 1 exportados a 'descarga_tramo_1.csv'")

    def exportar_tramo_2(self):
        d, n = self._get_export_params()
        if d is None:
            return

        data = generar_curva_descarga(d, n)
        tramo2 = data["T2"]

        with open("descarga_tramo_2.csv", 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["H0", "Q"])
            for i in range(len(tramo2["H"])):
                writer.writerow([tramo2["H"][i], tramo2["Q"][i]])

        messagebox.showinfo("Éxito", "Resultados del Tramo 2 exportados a 'descarga_tramo_2.csv'")

    def exportar_tramo_3(self):
        d, n = self._get_export_params()
        if d is None:
            return

        elevacion_base = d
        H0_min_tramo3 = elevacion_base + 2 * d
        H0_max_tramo3 = 8.30

        y_min_t3 = fsolve(lambda y: calcular_tramo3_pared_gruesa(y, d, n, L)[1][0] - H0_min_tramo3, 1.0)[0]
        y_max_t3 = fsolve(lambda y: calcular_tramo3_pared_gruesa(y, d, n, L)[1][0] - H0_max_tramo3, 1.0)[0]
        
        y_tramo3 = np.linspace(y_min_t3, y_max_t3, 100)
        
        g = 9.81
        A = (np.pi * d**2) / 4
        f_L_D = ((124.52 * 0.015**2) / (d**(1/3))) * (L / d)
        mu = 1 / np.sqrt(1 + 0.05 + f_L_D)
        
        Q_vals = np.array([calc_Q_reducida(y) for y in y_tramo3])
        Z0_vals = (Q_vals / (n * mu * A))**2 / (2 * g)
        H0_vals = Z0_vals + y_tramo3

        with open("descarga_tramo_3.csv", 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Tirante y aguas abajo", "Caudal Q (proveniente de la curva H-Q)", "Z0", "Cota H0"])
            for i in range(len(y_tramo3)):
                writer.writerow([y_tramo3[i], Q_vals[i], Z0_vals[i], H0_vals[i]])
        
        messagebox.showinfo("Éxito", "Resultados del Tramo 3 exportados a 'descarga_tramo_3.csv'")


    def actualizar_ui(self):
        """Cambia el texto de la entrada según la opción seleccionada."""
        if self.opcion.get() == "1":
            self.lbl_input.config(text="Caudal (Q) [m³/s]:")
            self.entry_n.config(state='disabled')
            self.entry_h.config(state='disabled')
        elif self.opcion.get() == "3":
            self.lbl_input.config(text="Diámetro (D) [m]:")
            self.entry_n.config(state='normal')
            self.entry_h.config(state='normal')
        elif self.opcion.get() == "2":
            self.lbl_input.config(text="Caudal objetivo (Q) [m³/s]:")
            self.entry_n.config(state='normal')
            self.entry_h.config(state='disabled')
        self.entry_input.delete(0, tk.END)

    def dibujar_curva_base(self):
        """Dibuja la curva H-Q inicial vacía al abrir el programa."""
        self.ax.clear()
        H_vals = np.linspace(0, 4.5, 100)
        Q_vals = [calc_Q_reducida(h) for h in H_vals]
        
        self.ax.plot(Q_vals, H_vals, label="Curva H-Q", color='#1f77b4', linewidth=2.5)
        self.ax.set_xlim(0, 320)
        self.ax.set_ylim(0, 4.5)
        self.ax.set_xlabel("Caudal (Q) [m³/s]", fontweight='bold')
        self.ax.set_ylabel("Tirante aguas abajo (H) [m]", fontweight='bold')
        self.ax.set_title("Curva H-Q del Canal")
        self.ax.grid(True, linestyle='--', alpha=0.6)
        self.canvas.draw()

    def actualizar_grafico(self, q_val, h_val):
        """Re-dibuja la gráfica y añade el punto rojo del cálculo actual."""
        self.ax.clear()
        H_vals = np.linspace(0, 4.5, 100)
        Q_vals = [calc_Q_reducida(h) for h in H_vals]
        
        self.ax.plot(Q_vals, H_vals, label="Curva H-Q", color='#1f77b4', linewidth=2.5)
        self.ax.plot(q_val, h_val, 'ro', markersize=8, label=f"Cálculo (Q={q_val:.2f}, H={h_val:.2f})")
        self.ax.axvline(q_val, color='red', linestyle='--', alpha=0.4)
        self.ax.axhline(h_val, color='red', linestyle='--', alpha=0.4)
        
        self.ax.set_xlim(0, 320)
        self.ax.set_ylim(0, 4.5)
        self.ax.set_xlabel("Caudal (Q) [m³/s]", fontweight='bold')
        self.ax.set_ylabel("Tirante aguas abajo (H) [m]", fontweight='bold')
        self.ax.set_title("Curva H-Q del Canal")
        self.ax.grid(True, linestyle='--', alpha=0.6)
        self.ax.legend(loc="upper left")
        self.canvas.draw()

    def mostrar_texto(self, texto):
        """Muestra texto en la caja de resultados."""
        self.text_out.config(state='normal')
        self.text_out.delete(1.0, tk.END)
        self.text_out.insert(tk.END, texto)
        self.text_out.config(state='disabled')

    def calcular(self):
        """Ejecuta la lógica de cálculo principal."""
        try:
            val = float(self.entry_input.get())
            if val <= 0:
                messagebox.showerror("Error", "El valor debe ser positivo.")
                return
            if self.opcion.get() in ["2", "3"]:
                n_val = int(self.entry_n.get())
                if n_val <= 0:
                    messagebox.showerror("Error", "La cantidad de orificios debe ser mayor a 0.")
                    return
        except ValueError:
            messagebox.showerror("Error", "Por favor ingrese números válidos.")
            return
            
        if self.opcion.get() == "3":
            try:
                h_val = float(self.entry_h.get())
                if h_val < 0:
                    messagebox.showerror("Error", "El tirante no puede ser negativo.")
                    return
            except ValueError:
                messagebox.showerror("Error", "Por favor ingrese un tirante H válido.")
                return

        if self.opcion.get() == "1":
            if val > 300:
                messagebox.showerror("Error", "La curva H-Q solo está desarrollada para caudales hasta 300 m³/s.")
                return
                
            H_calc = calcular_H_desde_Q(val)
            resultado = (f"Caudal objetivo (Q)               : {val:.2f} m³/s\n"
                         f"Tirante aguas abajo (H) calculado : {H_calc:.4f} m")
            self.ultimo_resultado = None # No exportamos a CSV esta opción simple
            self.actualizar_grafico(val, H_calc)
            
        elif self.opcion.get() == "3":
            # Encontrar el equilibrio exacto entre el orificio y la curva H-Q
            def equilibrio(h_guess):
                h_g = float(h_guess[0])
                Q_ori = calcular_caudal_orificios(val, n_val, h_g)[0]
                return Q_ori - calc_Q_reducida(h_g)
            h_val = fsolve(equilibrio, h_val)[0]
            Q, mu, Z0, f_friccion, xi, eta = calcular_caudal_orificios(val, n_val, h_val)
            
            if Q > 300:
                messagebox.showerror("Error", f"El caudal calculado ({Q:.2f} m³/s) supera el límite de 300 m³/s.")
                return
                
            resultado = (f"Longitud del conducto (L) [m] : {L:.2f}\n"
                         f"Tirante aguas abajo (H) [m]   : {h_val:.4f}\n"
                         f"Carga efectiva (Z0) [m]       : {Z0:.3f}\n"
                         f"Cantidad de orificios (N)     : {n_val}\n"
                         f"Rugosidad de Manning (η)      : {eta:.4f}\n"
                         f"Coeficiente xi (ξ)            : {xi:.2f}\n"
                         f"Factor f(L/D)                 : {f_friccion:.3f}\n"
                         f"Coeficiente mu (μ)            : {mu:.3f}\n"
                         f"Diámetro adoptado [m]         : {val:.2f}\n"
                         f"CAUDAL TOTAL calculado [m³/s] : {Q:.2f}")
            self.ultimo_resultado = {'args': (val, xi, n_val, f_friccion, mu, Q, L, eta, Z0, h_val), 'kwargs': {'archivo': "resultados_calculo_gui.csv"}}
            self.actualizar_grafico(Q, h_val)
            
        elif self.opcion.get() == "2":
            Q_target = val
            if Q_target > 300:
                messagebox.showerror("Error", "La curva H-Q solo está desarrollada para caudales hasta 300 m³/s.")
                return
                
            h_val = calcular_H_desde_Q(Q_target)
            
            D_exacto = fsolve(fsolve_D_residual, 1.0, args=(Q_target, n_val, h_val))[0]
            D_redondeado = np.ceil(round(D_exacto / 0.05, 4)) * 0.05
            Q_final, mu_final, Z0_final, f_friccion_final, xi_final, eta_final = calcular_caudal_orificios(D_redondeado, n_val, h_val)
            
            resultado = (f"Caudal objetivo [m³/s]        : {Q_target:.2f}\n"
                         f"Longitud del conducto (L) [m] : {L:.2f}\n"
                         f"Tirante aguas abajo (H) [m]   : {h_val:.4f}\n"
                         f"Carga efectiva (Z0) [m]       : {Z0_final:.3f}\n"
                         f"Cantidad de orificios (N)     : {n_val}\n"
                         f"Rugosidad de Manning (η)      : {eta_final:.4f}\n"
                         f"Coeficiente xi (ξ)            : {xi_final:.2f}\n"
                         f"Factor f(L/D)                 : {f_friccion_final:.3f}\n"
                         f"Coeficiente mu (μ)            : {mu_final:.3f}\n"
                         f"Diámetro calculado [m]        : {D_exacto:.4f}\n"
                         f"Diámetro constructivo (D) [m] : {D_redondeado:.2f}\n"
                         f"CAUDAL TOTAL resultante [m³/s]: {Q_final:.2f}")
            self.ultimo_resultado = {'args': (D_redondeado, xi_final, n_val, f_friccion_final, mu_final, Q_final, L, eta_final, Z0_final, h_val),
                                     'kwargs': {'Q_target': Q_target, 'D_exacto': D_exacto, 'archivo': "resultados_optimizacion_gui.csv"}}
            self.actualizar_grafico(Q_target, h_val)
            
            
        self.mostrar_texto(resultado)

    def exportar(self):
        if not self.ultimo_resultado:
            messagebox.showwarning("Aviso", "Primero debe realizar un cálculo antes de exportar.")
            return
        exportar_a_csv(*self.ultimo_resultado['args'], **self.ultimo_resultado['kwargs'])
        messagebox.showinfo("Éxito", f"Resultados exportados a: {self.ultimo_resultado['kwargs']['archivo']}")

if __name__ == "__main__":
    ventana = tk.Tk()
    app = AplicacionOrificios(ventana)
    ventana.mainloop()