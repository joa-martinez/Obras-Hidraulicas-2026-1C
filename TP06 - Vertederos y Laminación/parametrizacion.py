import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import os
import sys

# ==========================================
# 1. Carga de Datos y Parametrización por Tramos (Piecewise)
# ==========================================
# Cargamos la tabla actualizada para los tramos 1, 2 y 3
df_q_act = pd.read_csv('datos/curva_descarga_H-Q Actualizada.csv')

# --- TRAMO 1 (Canal) ---
t1 = df_q_act[df_q_act['Tramo'].str.contains('Tramo 1')]
z1 = t1['Tirante (H) [m]'].values
q1 = t1['Caudal (Q) [m3/s]'].values
cota1 = z1 + 21.0

# Fijamos c0_1 en el primer valor donde Q=0 (Z = 0.60 m)
c0_1_z = 0.60
def func_t1(z, a, b):
    return a * np.maximum(0, z - c0_1_z)**b

popt1, _ = curve_fit(func_t1, z1, q1, p0=[20.0, 1.0])
a1_opt, b1_opt = popt1
c0_1_opt = c0_1_z + 21.0 # En cota IGN

print(f"--- Tramo 1 (Canal) ---")
print(f"Q1 = {a1_opt:.4f} * (Cota - {c0_1_opt:.4f})^{b1_opt:.4f}\n")

# --- TRAMO 2 (Transición) ---
t2 = df_q_act[df_q_act['Tramo'].str.contains('Tramo 2')]
z2 = t2['Tirante (H) [m]'].values
q2 = t2['Caudal (Q) [m3/s]'].values
cota2 = z2 + 21.0

# Ajuste polinómico de grado 2
poly2 = np.polyfit(z2, q2, 2)
p2_opt, p1_opt, p0_opt = poly2

print(f"--- Tramo 2 (Transición) ---")
print(f"Q2 = {p2_opt:.4f}*(Z)^2 + {p1_opt:.4f}*(Z) + {p0_opt:.4f}  (donde Z = Cota - 21)\n")

# --- TRAMO 3 (Orificio) ---
t3 = df_q_act[df_q_act['Tramo'].str.contains('Tramo 3')]
z3 = t3['Tirante (H) [m]'].values
q3 = t3['Caudal (Q) [m3/s]'].values
cota3 = z3 + 21.0

def func_t3(z, d, c0):
    return d * np.sqrt(np.maximum(0, z - c0))

popt3, _ = curve_fit(func_t3, z3, q3, p0=[30.0, 1.7])
d_opt, c0_3_z = popt3
c0_3_opt = c0_3_z + 21.0 # En cota IGN

print(f"--- Tramo 3 (Orificio) ---")
print(f"Q3 = {d_opt:.4f} * sqrt(Cota - {c0_3_opt:.4f})\n")

# --- TRAMO 4 (Vertedero) ---
q_orf_max = func_t3(8.30, d_opt, c0_3_z)

# Tomamos la longitud del vertedero del argumento o usamos 55.0 por defecto
print("\n--- Actualización del Vertedero ---")
try:
    L_str = sys.argv[1] if len(sys.argv) > 1 else "55.0"
    L_vertedero = float(L_str)
except ValueError:
    print("Valor inválido. Usando L = 55.0 m por defecto.")
    L_vertedero = 55.0

# Calculamos los puntos teóricos y los guardamos en el CSV
C_d = 4.03
e_teorico = 0.552 * C_d * L_vertedero
z_vert = np.linspace(8.31, 9.50, 50)
q_vert = q_orf_max + e_teorico * (z_vert - 8.30)**1.5

csv_path = 'datos/curva_descarga_H-Q.csv'
df_csv = pd.read_csv(csv_path)
df_csv = df_csv[~df_csv['Tramo'].str.contains('Vertedero')]
df_new_t4 = pd.DataFrame({
    'Caudal (Q) [m3/s]': q_vert,
    'Tirante (H) [m]': z_vert,
    'Tramo': ['Fondo (cte) + Vertedero'] * len(z_vert)
})
df_updated = pd.concat([df_csv, df_new_t4], ignore_index=True)
df_updated.to_csv(csv_path, index=False)
print(f"Archivo {csv_path} actualizado con L = {L_vertedero} m")

# Procedemos con la parametrización como se venía haciendo
t4 = df_updated[df_updated['Tramo'].str.contains('Vertedero')]
z4 = t4['Tirante (H) [m]'].values
q4 = t4['Caudal (Q) [m3/s]'].values
cota4 = z4 + 21.0

def func_t4(z, e):
    return q_orf_max + e * np.maximum(0, z - 8.30)**1.5

popt4, _ = curve_fit(func_t4, z4, q4, p0=[100.0])
e_opt = popt4[0]

print(f"\n--- Tramo 4 (Vertedero) ---")
print(f"Q4 = {q_orf_max:.4f} + {e_opt:.4f} * (Cota - 29.30)^1.5\n")

# ==========================================
# 2. Parametrización V(Z) con suavizado C1 en Z=3 (Cota 24)
# ==========================================
# Mantenemos el C0 del fondo (donde inicia el tramo 1) para el volumen
c0_opt = 21.60

cotas_v = np.array([24.00, 25.00, 26.25, 27.50, 28.75, 30.00, 30.50])
volumen_v = np.array([0.00, 1.25, 6.35, 17.87, 38.11, 67.29, 81.0])

Z_v = cotas_v - 21.00
m = 0.01 / (24.00 - c0_opt)

def func_volumen_suavizado(Z, a_param):
    return a_param * (Z - 3.00)**2 + m * (Z - 3.00) + 0.01

popt_v, _ = curve_fit(func_volumen_suavizado, Z_v, volumen_v)
a_opt = popt_v[0]

# Variables exportadas para mantener compatibilidad con V = a*Z^2 + b*Z + c
a = a_opt
b = m - 6.0 * a_opt
c = 0.01 - 3.0 * m + 9.0 * a_opt

print("--- Parametrización Cota-Volumen (Continuidad C1 en Z=3) ---")
print(f"V = {a:.6f}*Z^2 + {b:.6f}*Z + {c:.6f}\n")


if __name__ == '__main__':
    # ==========================================
    # 3. Gráfica Separada: Cota vs Caudal Detallada (Piecewise)
    # ==========================================
    plt.figure(figsize=(10, 8))

    # Generar puntos suaves para cada tramo
    z1_smooth = np.linspace(z1.min(), z1.max(), 100)
    q1_fit = func_t1(z1_smooth, a1_opt, b1_opt)

    z2_smooth = np.linspace(z2.min(), z2.max(), 100)
    q2_fit = np.polyval(poly2, z2_smooth)

    z3_smooth = np.linspace(z3.min(), z3.max(), 100)
    q3_fit = func_t3(z3_smooth, d_opt, c0_3_z)

    z4_smooth = np.linspace(8.30, z4.max(), 100)
    q4_fit = func_t4(z4_smooth, e_opt)

    # Plot de los ajustes
    plt.plot(q1_fit, z1_smooth + 21.0, 'r-', linewidth=2, label='Tramo 1 (Canal)')
    plt.plot(q2_fit, z2_smooth + 21.0, 'g-', linewidth=2, label='Tramo 2 (Transición)')
    plt.plot(q3_fit, z3_smooth + 21.0, 'm-', linewidth=2, label='Tramo 3 (Orificio)')
    plt.plot(q4_fit, z4_smooth + 21.0, 'c-', linewidth=2, label='Tramo 4 (Vertedero)')

    # Plot de los datos originales
    plt.scatter(q1, cota1, color='black', s=10, alpha=0.5, label='Datos Originales')
    plt.scatter(q2, cota2, color='black', s=10, alpha=0.5)
    plt.scatter(q3, cota3, color='black', s=10, alpha=0.5)
    plt.scatter(q4, cota4, color='black', s=10, alpha=0.5)

    # Text box con las ecuaciones (ubicado encima de la leyenda)
    eq_t1 = fr'$Q_1 = {a1_opt:.2f} \cdot (Cota - {c0_1_opt:.2f})^{{{b1_opt:.2f}}}$'
    eq_t2 = fr'$Q_2 = {p2_opt:.4f}(Z)^2 + {p1_opt:.2f}(Z) {p0_opt:+.2f}$'
    eq_t3 = fr'$Q_3 = {d_opt:.2f} \cdot \sqrt{{Cota - {c0_3_opt:.2f}}}$'
    eq_t4 = fr'$Q_4 = {q_orf_max:.2f} + {e_opt:.2f} \cdot (Cota - 29.30)^{{1.5}}$'

    eq_text = eq_t1 + '\n' + eq_t2 + '\n' + eq_t3 + '\n' + eq_t4
    plt.text(0.98, 0.30, eq_text, transform=plt.gca().transAxes, fontsize=10, 
             horizontalalignment='right', verticalalignment='bottom', 
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))

    ax = plt.gca()
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.5))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.1))
    ax.xaxis.set_major_locator(ticker.MultipleLocator(50))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(10))

    plt.ylabel('Cota IGN [m]')
    plt.xlabel('Caudal [m3/s]')
    plt.title('Curva Cota-Caudal Detallada (Por Tramos)')
    plt.ylim(21.0, 31.0)
    plt.xlim(left=0)
    plt.legend(loc='lower right')
    plt.grid(True, which='major', color='gray', linestyle='-', alpha=0.7)
    plt.grid(True, which='minor', color='lightgray', linestyle='--', alpha=0.5)

    plt.tight_layout()
    os.makedirs('Gráficas', exist_ok=True)
    plt.savefig('Gráficas/curva_cota_caudal_detallada.png')
    print("Gráfica de Cota-Caudal detallada (con ecuaciones) guardada en 'Gráficas/curva_cota_caudal_detallada.png'")

    # ==========================================
    # 4. Gráfica Combinada: Cota-Volumen y Cota-Caudal (Menos Detallada)
    # ==========================================
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # --- Subplot 1: Cota-Volumen ---
    cota_v_smooth = np.linspace(c0_opt, 31.0, 200)
    z_v_smooth = cota_v_smooth - 21.0
    v_smooth = np.zeros_like(cota_v_smooth)
    mask_v = cota_v_smooth >= 24.0
    v_smooth[mask_v] = a_opt * (z_v_smooth[mask_v] - 3.0)**2 + m * (z_v_smooth[mask_v] - 3.0) + 0.01
    v_smooth[~mask_v] = m * (cota_v_smooth[~mask_v] - c0_opt)
    v_smooth = np.maximum(0, v_smooth)
    
    ax1.scatter(volumen_v, cotas_v, color='blue', alpha=0.6, label='Datos Originales')
    ax1.plot(v_smooth, cota_v_smooth, 'r-', linewidth=2, label='Ajuste Completo')
    
    eq_v1 = fr'$V = {a_opt:.4f}(Z - 3)^2 + {m:.4f}(Z - 3) + 0.01$'
    eq_v2 = fr'$V = {m:.6f} \cdot (Cota - {c0_opt:.4f})$'
    
    ax1.text(0.05, 0.95, eq_v1 + '\n' + eq_v2, transform=ax1.transAxes, fontsize=10,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
    
    ax1.set_ylabel('Cota IGN [m]')
    ax1.set_xlabel('Volumen [hm3]')
    ax1.set_title('Curva Cota-Volumen')
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(loc='lower right')

    # --- Subplot 2: Cota-Caudal (Total) ---
    ax2.plot(q1_fit, z1_smooth + 21.0, 'r-', linewidth=2, label='Tramo 1 (Canal)')
    ax2.plot(q2_fit, z2_smooth + 21.0, 'g-', linewidth=2, label='Tramo 2 (Transición)')
    ax2.plot(q3_fit, z3_smooth + 21.0, 'm-', linewidth=2, label='Tramo 3 (Orificio)')
    ax2.plot(q4_fit, z4_smooth + 21.0, 'c-', linewidth=2, label='Tramo 4 (Vertedero)')
    
    ax2.scatter(q1, cota1, color='black', s=10, alpha=0.5, label='Datos Originales')
    ax2.scatter(q2, cota2, color='black', s=10, alpha=0.5)
    ax2.scatter(q3, cota3, color='black', s=10, alpha=0.5)
    ax2.scatter(q4, cota4, color='black', s=10, alpha=0.5)
    
    eq_t1 = fr'$Q_1 = {a1_opt:.2f} \cdot (Cota - {c0_1_opt:.2f})^{{{b1_opt:.2f}}}$'
    eq_t2 = fr'$Q_2 = {p2_opt:.4f}(Z)^2 + {p1_opt:.2f}(Z) {p0_opt:+.2f}$'
    eq_t3 = fr'$Q_3 = {d_opt:.2f} \cdot \sqrt{{Cota - {c0_3_opt:.2f}}}$'
    eq_t4 = fr'$Q_4 = {q_orf_max:.2f} + {e_opt:.2f} \cdot (Cota - 29.30)^{{1.5}}$'
    
    eq_text = eq_t1 + '\n' + eq_t2 + '\n' + eq_t3 + '\n' + eq_t4
    
    ax2.text(0.98, 0.30, eq_text, transform=ax2.transAxes, fontsize=10,
             horizontalalignment='right', verticalalignment='bottom', bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))

    ax2.set_ylabel('Cota IGN [m]')
    ax2.set_xlabel('Caudal [m3/s]')
    ax2.set_title('Curva Cota-Caudal (Total)')
    ax2.grid(True, linestyle='--', alpha=0.6)
    ax2.legend(loc='lower right')
    
    plt.tight_layout()
    plt.savefig('Gráficas/curva_cota_volumen_y_caudal.png')
    print("Gráfica combinada guardada en 'Gráficas/curva_cota_volumen_y_caudal.png'")

    # ==========================================
    # 5. Gráfica: Volumen vs Caudal
    # ==========================================
    plt.figure(figsize=(10, 6))
    
    # Calculate unified arrays for V-Q plot
    z_all_smooth = np.concatenate([z1_smooth, z2_smooth, z3_smooth, z4_smooth])
    cota_all_smooth = z_all_smooth + 21.0
    q_all_smooth = np.concatenate([q1_fit, q2_fit, q3_fit, q4_fit])
    
    sort_idx = np.argsort(cota_all_smooth)
    cota_all_smooth = cota_all_smooth[sort_idx]
    q_all_smooth = q_all_smooth[sort_idx]

    # Calculate volume for the smoothed cota array
    z_for_vq = cota_all_smooth - 21.0
    v_for_vq = np.zeros_like(cota_all_smooth)
    mask_vq = cota_all_smooth >= 24.0
    v_for_vq[mask_vq] = a_opt * (z_for_vq[mask_vq] - 3.0)**2 + m * (z_for_vq[mask_vq] - 3.0) + 0.01
    v_for_vq[~mask_vq] = m * (cota_all_smooth[~mask_vq] - c0_opt)
    v_for_vq = np.maximum(0, v_for_vq)
    
    plt.plot(v_for_vq, q_all_smooth, color='purple', linewidth=2.5, label='Relación V-Q')
    
    plt.ylabel('Caudal [m3/s]')
    plt.xlabel('Volumen [hm3]')
    plt.title('Curva Volumen-Caudal')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(loc='lower right')
    
    plt.tight_layout()
    plt.savefig('Gráficas/curva_volumen_caudal.png')
    print("Gráfica de Volumen-Caudal guardada en 'Gráficas/curva_volumen_caudal.png'")
