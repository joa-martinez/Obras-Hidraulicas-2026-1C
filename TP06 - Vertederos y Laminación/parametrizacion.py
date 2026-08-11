import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

# ==========================================
# 1. Parametrización Q_fondo = d * sqrt(Cota - C0)
# ==========================================
df_q = pd.read_csv('datos/curva_descarga_H-Q.csv')
cotas_q = df_q['Tirante (H) [m]'].values + 21.0
q_vals = df_q['Caudal (Q) [m3/s]'].values

# Ajuste de Tres Parámetros (Fondo + Vertedero)
def func_global(cota, d, c0, e):
    # El caudal de fondo se satura al alcanzar la cota del vertedero (29.30m)
    cota_efectiva = np.where(cota > 29.30, 29.30, cota)
    q_fondo = d * np.sqrt(np.maximum(0, cota_efectiva - c0))
    q_vert = np.where(cota > 29.30, e * (np.maximum(0, cota - 29.30))**1.5, 0.0)
    return q_fondo + q_vert

popt, _ = curve_fit(func_global, cotas_q, q_vals, p0=[25.0, 22.0, 100.0])
d_opt, c0_opt, e_opt = popt

print(f"--- Parametrización Global (Fondo + Vertedero) ---")
print(f"Coeficiente fondo d: {d_opt:.6f}")
print(f"Cota de Origen fondo (C0): {c0_opt:.6f} m IGN")
print(f"Coeficiente vertedero e: {e_opt:.6f}")
print(f"Q_fondo (Cota < 29.30) = {d_opt:.4f} * sqrt(Cota - {c0_opt:.4f})")
print(f"Q_fondo (Cota >= 29.30) = constante")
print(f"Q_vert = {e_opt:.4f} * (Cota - 29.30)^1.5\n")

# ==========================================
# 2. Parametrización V(Z) con suavizado C1 en Z=3 (Cota 24)
# ==========================================
cotas_v = np.array([24.00, 25.00, 26.25, 27.50, 28.75, 30.00, 30.50])
volumen_v = np.array([0.00, 1.25, 6.35, 17.87, 38.11, 67.29, 81.0])

Z_v = cotas_v - 21.00
m = 0.01 / (24.00 - c0_opt)

# V(Z) = a*(Z-3)^2 + m*(Z-3) + 0.01
def func_volumen_suavizado(Z, a_param):
    return a_param * (Z - 3.00)**2 + m * (Z - 3.00) + 0.01

popt_v, _ = curve_fit(func_volumen_suavizado, Z_v, volumen_v)
a_opt = popt_v[0]

# Variables exportadas para mantener compatibilidad con V = a*Z^2 + b*Z + c
a = a_opt
b = m - 6.0 * a_opt
c = 0.01 - 3.0 * m + 9.0 * a_opt

print("--- Parametrización Cota-Volumen (Continuidad C1 en Z=3) ---")
print(f"V = {a_opt:.6f} * (Z - 3.00)^2 + {m:.6f} * (Z - 3.00) + 0.01")
print(f"Equivalente a: V = {a:.6f}*Z^2 + {b:.6f}*Z + {c:.6f}")

# ==========================================
# 3. Validación Visual (Eje Y = Cota IGN)
# ==========================================
plt.figure(figsize=(12, 6))

# Plot Volumen
plt.subplot(1, 2, 1)
plt.scatter(volumen_v, cotas_v, color='blue', label='Datos Originales', alpha=0.6)
cota_v_smooth = np.linspace(cotas_v.min(), cotas_v.max(), 100)
z_smooth = cota_v_smooth - 21.00
v_fit = a * z_smooth**2 + b * z_smooth + c

# Rama lineal
cota_v_linear = np.linspace(c0_opt, 24.0, 50)
v_linear = (0.01 / (24.0 - c0_opt)) * (cota_v_linear - c0_opt)

# Graficar como una sola curva continua
cota_v_full = np.concatenate([cota_v_linear[:-1], cota_v_smooth])
v_full = np.concatenate([v_linear[:-1], v_fit])
plt.plot(v_full, cota_v_full, 'r-', linewidth=2, label='Ajuste Completo')

eq_v_quad = fr'$V = {a_opt:.4f} (Z-3)^2 + {m:.4f} (Z-3) + 0.01$'
pendiente = 0.01 / (24.0 - c0_opt)
eq_v_lin = fr'$V = {pendiente:.6f} \cdot (Cota - {c0_opt:.4f})$'
eq_text = eq_v_quad + '\n' + eq_v_lin

plt.text(0.05, 0.95, eq_text, transform=plt.gca().transAxes, fontsize=10, 
         verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

plt.ylabel('Cota IGN [m]')
plt.xlabel('Volumen [hm3]')
plt.title('Curva Cota-Volumen')
plt.ylim(21.0, 31.0)
plt.legend(loc='lower right')
plt.grid(True, linestyle='--', alpha=0.7)

# Plot Caudal
plt.subplot(1, 2, 2)
plt.scatter(q_vals, cotas_q, color='blue', label='Datos Originales', s=5, alpha=0.3)

cota_q_smooth = np.linspace(c0_opt, 30.50, 300)
q_fit = func_global(cota_q_smooth, d_opt, c0_opt, e_opt)
plt.plot(q_fit, cota_q_smooth, 'g-', linewidth=2, label=r'Ajuste Global Optimizado')

eq_q1 = fr'$Q_f = {d_opt:.2f} \cdot \sqrt{{Cota - {c0_opt:.2f}}}$'
eq_q2 = fr'$Q_v = {e_opt:.2f} \cdot (Cota - 29.30)^{{1.5}}$'
plt.text(0.05, 0.95, eq_q1 + '\n' + eq_q2, transform=plt.gca().transAxes, fontsize=10, 
         verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

plt.ylabel('Cota IGN [m]')
plt.xlabel('Caudal [m3/s]')
plt.title('Curva Cota-Caudal (Total)')
plt.ylim(21.0, 31.0)
plt.legend(loc='lower right')
plt.grid(True, linestyle='--', alpha=0.7)

plt.tight_layout()
plt.savefig('validacion_parametrizacion.png')
print("\nGráfica de validación (Cota-Volumen y Cota-Caudal) guardada en 'validacion_parametrizacion.png'")

# ==========================================
# 4. Gráfica Separada: Volumen vs Caudal
# ==========================================
plt.figure(figsize=(8, 6))

cota_common = np.linspace(c0_opt, 30.50, 300)
v_common = np.where(cota_common < 24.0, 
                    m * (cota_common - c0_opt), 
                    a * (cota_common - 21.00)**2 + b * (cota_common - 21.00) + c)
q_common = func_global(cota_common, d_opt, c0_opt, e_opt)

plt.plot(v_common, q_common, color='purple', linewidth=2, label='Relación V-Q')
plt.xlabel('Volumen [hm3]')
plt.ylabel('Caudal [m3/s]')
plt.title('Curva Volumen-Caudal')
plt.legend(loc='lower right')
plt.grid(True, linestyle='--', alpha=0.7)

plt.tight_layout()
plt.savefig('relacion_volumen_caudal.png')
print("Gráfica de relación Volumen-Caudal guardada en 'relacion_volumen_caudal.png'")

# ==========================================
# 5. Gráfica Separada: Cota vs Caudal Detallada
# ==========================================
import matplotlib.ticker as ticker

plt.figure(figsize=(10, 8))

plt.plot(q_fit, cota_q_smooth, 'g-', linewidth=2, label=r'Ajuste Global Optimizado')
plt.scatter(q_vals, cotas_q, color='blue', label='Datos Originales', s=15, alpha=0.6)

ax = plt.gca()
# Ticks Y (Cota): Mayores cada 0.5 m, menores cada 0.1 m
ax.yaxis.set_major_locator(ticker.MultipleLocator(0.5))
ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.1))

# Ticks X (Caudal): Mayores cada 50 m3/s, menores cada 10 m3/s
ax.xaxis.set_major_locator(ticker.MultipleLocator(50))
ax.xaxis.set_minor_locator(ticker.MultipleLocator(10))

plt.ylabel('Cota IGN [m]')
plt.xlabel('Caudal [m3/s]')
plt.title('Curva Cota-Caudal Detallada')
plt.ylim(21.0, 31.0)
plt.xlim(left=0)
plt.legend(loc='lower right')

# Activar la cuadrícula tanto para los ticks mayores como menores
plt.grid(True, which='major', color='gray', linestyle='-', alpha=0.7)
plt.grid(True, which='minor', color='lightgray', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig('curva_cota_caudal_detallada.png')
print("Gráfica de Cota-Caudal detallada guardada en 'curva_cota_caudal_detallada.png'")
