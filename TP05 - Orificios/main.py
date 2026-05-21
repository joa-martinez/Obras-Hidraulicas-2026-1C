import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from scipy.optimize import fsolve
import numpy as np
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import os

# Importamos las funciones y constantes de tu script original
from Calculo_Q_salida_orificios import (
    calcular_caudal_orificios, 
    fsolve_D_residual, 
    calcular_H_desde_Q,
    calc_Q_reducida,
    exportar_a_csv,
    L, H
)
from Curva_descarga import generar_curva_descarga

class AplicacionOrificios:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculadora de Orificios con Curva H-Q")
        self.root.geometry("1050x600")
        self.root.resizable(False, False)

        # Crear Notebook para pestañas
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")

        # Pestaña 1: Calculadora de Orificios
        self.tab1 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text='Dimensionamiento y Optimización')
        self.crear_tab1()

        # Pestaña 2: Curva de Descarga H-Q
        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab2, text='Curva de Descarga H-Q')
        self.D_optimizado = None
        self.N_optimizado = None
        self.crear_tab2()

    def crear_tab1(self):
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
        self.export_button_tab1 = ttk.Button(btn_frame, text="Exportar a CSV", command=self.exportar_tab1, width=20)
        self.export_button_tab1.grid(row=0, column=1, padx=10)
        
        # 4. Pantalla de Resultados
        ttk.Label(main_frame, text="Resultados:", font=("Helvetica", 10, "bold")).grid(row=6, column=0, sticky=tk.W, pady=(10, 5))
        self.text_out = tk.Text(main_frame, height=13, width=58, state='disabled', font=("Courier", 10), bg="#f4f4f4")
        self.text_out.grid(row=7, column=0, columnspan=2)
        
        # 5. Gráfico de H-Q
        self.fig_tab1 = Figure(figsize=(5.2, 5.2), dpi=100)
        self.ax_tab1 = self.fig_tab1.add_subplot(111)
        self.canvas_tab1 = FigureCanvasTkAgg(self.fig_tab1, master=plot_frame)
        self.canvas_tab1.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.dibujar_curva_base()
        
        # Inicializamos el estado de la interfaz
        self.actualizar_ui()
        
        # Ejecutar cálculo al presionar Enter
        self.root.bind('<Return>', lambda event: self.calcular())

    def crear_tab2(self):
        # Marco principal para la Pestaña 2
        main_frame_tab2 = ttk.Frame(self.tab2, padding="15")
        main_frame_tab2.pack(expand=True, fill="both")

        # Botones
        button_frame = ttk.Frame(main_frame_tab2)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Generar Curva H-Q", command=self.generar_y_graficar_curva).pack(side=tk.LEFT, padx=10)
        self.export_button_tab2 = ttk.Button(button_frame, text="Exportar Curva a CSV", command=self.exportar_curva_csv, state="disabled")
        self.export_button_tab2.pack(side=tk.LEFT, padx=10)
        self.export_separados_button = ttk.Button(button_frame, text="Exportar Tramos Separados", command=self.exportar_tramos_separados, state="disabled")
        self.export_separados_button.pack(side=tk.LEFT, padx=10)

        # Gráfico para la curva H-Q
        self.fig_tab2 = Figure(figsize=(8, 6), dpi=100)
        self.ax_tab2 = self.fig_tab2.add_subplot(111)
        self.canvas_tab2 = FigureCanvasTkAgg(self.fig_tab2, master=main_frame_tab2)
        self.canvas_tab2.get_tk_widget().pack(expand=True, fill="both", pady=10)
        self.curva_data = None


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
        self.ax_tab1.clear()
        H_vals = np.linspace(0, 4.5, 100)
        Q_vals = [calc_Q_reducida(h) for h in H_vals]
        
        self.ax_tab1.plot(Q_vals, H_vals, label="Curva H-Q", color='#1f77b4', linewidth=2.5)
        self.ax_tab1.set_xlim(0, 320)
        self.ax_tab1.set_ylim(0, 4.5)
        self.ax_tab1.set_xlabel("Caudal (Q) [m³/s]", fontweight='bold')
        self.ax_tab1.set_ylabel("Tirante aguas abajo (H) [m]", fontweight='bold')
        self.ax_tab1.set_title("Relación de Descarga H-Q")
        self.ax_tab1.grid(True, linestyle='--', alpha=0.6)
        self.canvas_tab1.draw()

    def actualizar_grafico(self, q_val, h_val):
        """Re-dibuja la gráfica y añade el punto rojo del cálculo actual."""
        self.ax_tab1.clear()
        H_vals = np.linspace(0, 4.5, 100)
        Q_vals = [calc_Q_reducida(h) for h in H_vals]
        
        self.ax_tab1.plot(Q_vals, H_vals, label="Curva H-Q", color='#1f77b4', linewidth=2.5)
        self.ax_tab1.plot(q_val, h_val, 'ro', markersize=8, label=f"Cálculo (Q={q_val:.2f}, H={h_val:.2f})")
        self.ax_tab1.axvline(q_val, color='red', linestyle='--', alpha=0.4)
        self.ax_tab1.axhline(h_val, color='red', linestyle='--', alpha=0.4)
        
        self.ax_tab1.set_xlim(0, 320)
        self.ax_tab1.set_ylim(0, 4.5)
        self.ax_tab1.set_xlabel("Caudal (Q) [m³/s]", fontweight='bold')
        self.ax_tab1.set_ylabel("Tirante aguas abajo (H) [m]", fontweight='bold')
        self.ax_tab1.set_title("Relación de Descarga H-Q")
        self.ax_tab1.grid(True, linestyle='--', alpha=0.6)
        self.ax_tab1.legend(loc="upper left")
        self.canvas_tab1.draw()

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
            D_val = val
            def equilibrio(h_guess):
                h_g = float(h_guess[0])
                Q_ori = calcular_caudal_orificios(D_val, n_val, h_g)[0]
                return Q_ori - calc_Q_reducida(h_g)
            h_val = fsolve(equilibrio, float(self.entry_h.get()))[0]
            Q, mu, Z0, f_friccion, xi, eta = calcular_caudal_orificios(D_val, n_val, h_val)
            
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
                         f"Diámetro adoptado [m]         : {D_val:.2f}\n"
                         f"CAUDAL TOTAL calculado [m³/s] : {Q:.2f}")
            self.ultimo_resultado = {'args': (D_val, xi, n_val, f_friccion, mu, Q, L, eta, Z0, h_val), 'kwargs': {'archivo': "resultados_calculo_gui.csv"}}
            self.actualizar_grafico(Q, h_val)
            
        elif self.opcion.get() == "2":
            Q_target = val
            if Q_target > 300:
                messagebox.showerror("Error", "La curva H-Q solo está desarrollada para caudales hasta 300 m³/s.")
                return
                
            h_val = calcular_H_desde_Q(Q_target)
            
            D_exacto = fsolve(fsolve_D_residual, 1.0, args=(Q_target, n_val, h_val))[0]
            D_redondeado = np.ceil(round(D_exacto / 0.05, 4)) * 0.05
            self.D_optimizado = D_redondeado
            self.N_optimizado = n_val
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

    def exportar_tab1(self):
        if not self.ultimo_resultado:
            messagebox.showwarning("Aviso", "Primero debe realizar un cálculo antes de exportar.")
            return
        
        try:
            # Pide al usuario que elija la ubicación para guardar el archivo
            filepath = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=self.ultimo_resultado['kwargs']['archivo']
            )
            if not filepath:
                return # El usuario canceló
            
            # Actualizamos el nombre del archivo en los argumentos
            self.ultimo_resultado['kwargs']['archivo'] = filepath
            
            exportar_a_csv(*self.ultimo_resultado['args'], **self.ultimo_resultado['kwargs'])
            messagebox.showinfo("Éxito", f"Resultados exportados a: {filepath}")

        except Exception as e:
            messagebox.showerror("Error de Exportación", f"No se pudo exportar el archivo:\n{e}")

    def generar_y_graficar_curva(self):
        if self.D_optimizado is None or self.N_optimizado is None:
            messagebox.showerror("Error", "Primero debe optimizar un diámetro en la primera pestaña.")
            return

        self.curva_data = generar_curva_descarga(self.D_optimizado, self.N_optimizado)
        
        self.ax_tab2.clear()
        
        # Separar los datos en los tres tramos desde el diccionario generado
        Q_tramo_libre = self.curva_data["T1"]["Q"]
        H0_tramo_libre = self.curva_data["T1"]["H"]

        Q_tramo2 = self.curva_data["T2"]["Q"]
        H0_tramo2 = self.curva_data["T2"]["H"]

        Q_tramo3 = self.curva_data["T3"]["Q"]
        H0_tramo3 = self.curva_data["T3"]["H"]


        self.ax_tab2.plot(Q_tramo_libre, H0_tramo_libre, linewidth=2.5, color='#1f77b4', 
                          label='Tramo 1: Funcionamiento como Canal')
        self.ax_tab2.plot(Q_tramo2, H0_tramo2, linewidth=2.5, color='#ff7f0e',
                          label='Tramo 2: Funcionamiento como Alcantarilla')
        self.ax_tab2.plot(Q_tramo3, H0_tramo3, linewidth=2.5, color='#2ca02c', 
                          label='Tramo 3: Funcionamiento como Orificio')

        # Marcar el punto final del tramo (sección plena)
        self.ax_tab2.plot(Q_tramo_libre[-1], H0_tramo_libre[-1], marker='o', color='red', markersize=6, zorder=5)
        self.ax_tab2.annotate(f"({Q_tramo_libre[-1]:.2f}; {H0_tramo_libre[-1]:.2f})", 
                              (Q_tramo_libre[-1], H0_tramo_libre[-1]), 
                              textcoords="offset points", xytext=(10, -10), fontsize=9, color='darkred', fontweight='bold')

        # Marcar los límites del tramo 3
        self.ax_tab2.plot(Q_tramo3[0], H0_tramo3[0], marker='o', color='red', markersize=6, zorder=5)
        self.ax_tab2.annotate(f"({Q_tramo3[0]:.2f}; {H0_tramo3[0]:.2f})", 
                              (Q_tramo3[0], H0_tramo3[0]), 
                              textcoords="offset points", xytext=(-10, 10), ha='right', fontsize=9, color='darkred', fontweight='bold')
        self.ax_tab2.plot(Q_tramo3[-1], H0_tramo3[-1], marker='o', color='red', markersize=6, zorder=5)
        self.ax_tab2.annotate(f"({Q_tramo3[-1]:.2f}; {H0_tramo3[-1]:.2f})", 
                              (Q_tramo3[-1], H0_tramo3[-1]), 
                              textcoords="offset points", xytext=(-10, -12), ha='right', fontsize=9, color='darkred', fontweight='bold')

        # --- 1. Escala Eje X (Caudal) ---
        escala_x_tramos1y2 = 0.4      # Escala Tramos 1 y 2
        escala_x_tramo3 = 1/20      # Escala Tramo 3 (Ahogado)
        Q_limite_x = Q_tramo3[0]    # Punto de quiebre

        def forward_x(x):
            x = np.asarray(x, dtype=float)
            return np.where(x <= Q_limite_x, x * escala_x_tramos1y2, 
                            (Q_limite_x * escala_x_tramos1y2) + (x - Q_limite_x) * escala_x_tramo3)

        def inverse_x(x):
            x = np.asarray(x, dtype=float)
            X_limite = Q_limite_x * escala_x_tramos1y2
            return np.where(x <= X_limite, x / escala_x_tramos1y2, 
                            Q_limite_x + (x - X_limite) / escala_x_tramo3)

        self.ax_tab2.set_xscale('function', functions=(forward_x, inverse_x))

        # --- 2. Escala Eje Y (Tirante H0) ---
        escala_y_tramos1y2 = 3      # Escala ampliada para Tramos 1 y 2
        escala_y_tramo3 = 1         # Escala normal para Tramo 3
        H0_limite_y = H0_tramo3[0]  # Punto de quiebre

        def forward_y(y):
            y = np.asarray(y, dtype=float)
            return np.where(y <= H0_limite_y, y * escala_y_tramos1y2, 
                            (H0_limite_y * escala_y_tramos1y2) + (y - H0_limite_y) * escala_y_tramo3)

        def inverse_y(y):
            y = np.asarray(y, dtype=float)
            Y_limite = H0_limite_y * escala_y_tramos1y2
            return np.where(y <= Y_limite, y / escala_y_tramos1y2, 
                            H0_limite_y + (y - Y_limite) / escala_y_tramo3)

        self.ax_tab2.set_yscale('function', functions=(forward_y, inverse_y))

        # Ticks Dinámicos
        def obtener_paso_tick(escala, densidad_visual=1.0):
            """Devuelve un paso de tick amigable inversamente proporcional a la escala."""
            val = densidad_visual / escala
            for paso in [0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0]:
                if val <= paso: return paso
            return 100.0

        # Ticks para el eje X
        paso_x_t1y2 = obtener_paso_tick(escala_x_tramos1y2, densidad_visual=1.2)
        paso_x_t3 = obtener_paso_tick(escala_x_tramo3, densidad_visual=2.0)

        ticks_x_t1y2 = np.arange(0, Q_limite_x, paso_x_t1y2)
        ticks_x_t3 = np.arange(np.ceil(Q_limite_x / paso_x_t3) * paso_x_t3, max(Q_tramo3) * 1.1, paso_x_t3)

        # Filtrar ticks que están demasiado cerca del límite para evitar solapamiento visual
        umbral_x_t1y2 = paso_x_t1y2 * 0.4
        umbral_x_t3 = paso_x_t3 * 0.4

        ticks_x_t1y2 = ticks_x_t1y2[np.abs(Q_limite_x - ticks_x_t1y2) > umbral_x_t1y2]
        ticks_x_t3 = ticks_x_t3[np.abs(ticks_x_t3 - Q_limite_x) > umbral_x_t3]

        # Unimos, agregando explícitamente el límite de escala, y eliminamos duplicados
        ticks_x = np.unique(np.concatenate((ticks_x_t1y2, [Q_limite_x], ticks_x_t3)))
        etiquetas_x = [f"{t:.2f}".rstrip('0').rstrip('.') if t % 1 != 0 else f"{int(t)}" for t in ticks_x]
        self.ax_tab2.set_xticks(ticks_x)
        self.ax_tab2.set_xticklabels(etiquetas_x)


        # Ticks para el eje Y
        paso_y_t1y2 = obtener_paso_tick(escala_y_tramos1y2, densidad_visual=0.8)
        paso_y_t3 = obtener_paso_tick(escala_y_tramo3, densidad_visual=2.0)

        ticks_y_t1y2 = np.arange(0, H0_limite_y, paso_y_t1y2)
        ticks_y_t3 = np.arange(np.ceil(H0_limite_y / paso_y_t3) * paso_y_t3, max(H0_tramo3) * 1.05, paso_y_t3)

        # Filtrar ticks que están demasiado cerca del límite para evitar solapamiento visual
        umbral_t1y2 = paso_y_t1y2 * 0.4
        umbral_t3 = paso_y_t3 * 0.4

        ticks_y_t1y2 = ticks_y_t1y2[np.abs(H0_limite_y - ticks_y_t1y2) > umbral_t1y2]
        ticks_y_t3 = ticks_y_t3[np.abs(ticks_y_t3 - H0_limite_y) > umbral_t3]

        # Unimos, agregando explícitamente el límite de escala, y eliminamos duplicados
        ticks_y = np.unique(np.concatenate((ticks_y_t1y2, [H0_limite_y], ticks_y_t3)))
        etiquetas_y = [f"{t:.2f}".rstrip('0').rstrip('.') if t % 1 != 0 else f"{int(t)}" for t in ticks_y]
        self.ax_tab2.set_yticks(ticks_y)
        self.ax_tab2.set_yticklabels(etiquetas_y)


        self.ax_tab2.set_xlabel("Caudal (Q) [m³/s]")
        self.ax_tab2.set_ylabel("Tirante (H) [m]")
        self.ax_tab2.set_title("Curva de Descarga H-Q")
        self.ax_tab2.grid(True)
        self.ax_tab2.legend()
        self.canvas_tab2.draw()
        
        # Habilitar el botón de exportación
        self.export_button_tab2.config(state="normal")
        self.export_separados_button.config(state="normal")
        
    def exportar_curva_csv(self):
        if self.curva_data is None:
            messagebox.showwarning("Aviso", "Primero debe generar la curva H-Q.")
            return

        try:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile="curva_descarga_H-Q.csv"
            )
            if not filepath:
                return 

            # Preparar los datos aplanados para un CSV tabular tradicional
            tramos = (['Tramo 1 (Canal)'] * len(self.curva_data["T1"]["H"]) + 
                      ['Tramo 2 (Transición)'] * len(self.curva_data["T2"]["H"]) + 
                      ['Tramo 3 (Orificio)'] * len(self.curva_data["T3"]["H"]))

            df = pd.DataFrame({
                "Caudal (Q) [m3/s]": self.curva_data["Q"],
                "Tirante (H) [m]": self.curva_data["H"],
                "Tramo": tramos
            })
            df.to_csv(filepath, index=False)
            messagebox.showinfo("Éxito", f"Curva H-Q exportada a: {filepath}")

        except Exception as e:
            messagebox.showerror("Error de Exportación", f"No se pudo exportar el archivo:\n{e}")

    def exportar_tramos_separados(self):
        if self.curva_data is None or self.D_optimizado is None or self.N_optimizado is None:
            messagebox.showwarning("Aviso", "Primero debe generar la curva H-Q.")
            return

        try:
            directorio = filedialog.askdirectory(title="Seleccione la carpeta para guardar los CSV")
            if not directorio:
                return

            d = self.D_optimizado
            n = self.N_optimizado
            elevacion_base = 0.48
            
            # --- TRAMO 1 ---
            H0_t1 = self.curva_data["T1"]["H"]
            y = np.clip(H0_t1 - elevacion_base, 0, d * 0.938)
            theta = 2 * np.arccos(1 - (2 * y) / d)
            A = (d**2 / 8) * (theta - np.sin(theta))
            
            term_sin_theta_div_theta = np.zeros_like(theta)
            non_zero_mask = theta > 0
            term_sin_theta_div_theta[non_zero_mask] = np.sin(theta[non_zero_mask]) / theta[non_zero_mask]
            R = (d / 4) * (1 - term_sin_theta_div_theta)
            
            df1 = pd.DataFrame({"Cota H0": H0_t1, "Angulo theta": theta, "Área": A, "Radio Hidráulico": R, "Caudal Q": self.curva_data["T1"]["Q"]})
            df1.to_csv(os.path.join(directorio, "descarga_tramo_1.csv"), index=False)

            # --- TRAMO 2 ---
            df2 = pd.DataFrame({"H0": self.curva_data["T2"]["H"], "Q": self.curva_data["T2"]["Q"]})
            df2.to_csv(os.path.join(directorio, "descarga_tramo_2.csv"), index=False)

            # --- TRAMO 3 ---
            H0_t3 = self.curva_data["T3"]["H"]
            Q3 = self.curva_data["T3"]["Q"]
            
            g = 9.81
            Area_full = (np.pi * d**2) / 4
            f_L_D = ((124.52 * 0.015**2) / (d**(1/3))) * (L / d)
            mu = 1 / np.sqrt(1 + 0.05 + f_L_D)
            Z0_vals = (Q3 / (n * mu * Area_full))**2 / (2 * g)
            y_t3 = H0_t3 - Z0_vals
            
            df3 = pd.DataFrame({"Tirante y aguas abajo": y_t3, "Caudal Q (proveniente de la curva H-Q)": Q3, "Z0": Z0_vals, "Cota H0": H0_t3})
            df3.to_csv(os.path.join(directorio, "descarga_tramo_3.csv"), index=False)

            messagebox.showinfo("Éxito", f"Curvas exportadas exitosamente en:\n{directorio}")
            
        except Exception as e:
            messagebox.showerror("Error de Exportación", f"Ocurrió un error al exportar:\n{e}")

if __name__ == "__main__":
    ventana = tk.Tk()
    app = AplicacionOrificios(ventana)
    ventana.mainloop()