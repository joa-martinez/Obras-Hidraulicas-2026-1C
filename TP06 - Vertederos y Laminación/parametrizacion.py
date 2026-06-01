import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

# ==========================================
# 1. Parametrización V = a*Cota^2 + b*Cota + c
# ==========================================
cotas_v = np.array([24.00, 25.00, 26.25, 27.50, 28.75, 30.00, 31.25])
volumen_v = np.array([0.00, 1.25, 6.35, 17.87, 38.11, 67.29, 105.99])

# Ajuste cuadrático usando Cota IGN directamente
coeffs_v = np.polyfit(cotas_v, volumen_v, 2)
a, b, c = coeffs_v

print("--- Parametrización Cota-Volumen ---")
print(f"V = {a:.6f} * Cota^2 + {b:.6f} * Cota + {c:.6f}")

# ==========================================
# 2. Parametrización Q_fondo = d * sqrt(Cota - C0)
# ==========================================
df_q = pd.read_csv('datos/curva_descarga_H-Q.csv')
cotas_q = df_q['Tirante (H) [m]'].values + 21.0
q_vals = df_q['Caudal (Q) [m3/s]'].values

# Ajuste de Dos Parámetros: Q = d * sqrt(Cota - C0)
def func_raiz_desplazada(cota, d, c0):
    return d * np.sqrt(np.maximum(0, cota - c0))

popt, _ = curve_fit(func_raiz_desplazada, cotas_q, q_vals, p0=[25, 22.0])
d_opt, c0_opt = popt

print(f"\n--- Parametrización Q_fondo (Modelo Optimizado) ---")
print(f"Coeficiente d: {d_opt:.6f}")
print(f"Cota de Origen (C0): {c0_opt:.6f} m IGN")
print(f"Ecuación: Q = {d_opt:.4f} * sqrt(Cota - {c0_opt:.4f})")

# ==========================================
# 3. Validación Visual (Eje Y = Cota IGN)
# ==========================================
plt.figure(figsize=(14, 6))

# Plot Volumen
plt.subplot(1, 2, 1)
plt.scatter(volumen_v, cotas_v, color='blue', label='Datos Originales', alpha=0.6)
cota_v_smooth = np.linspace(cotas_v.min(), cotas_v.max(), 100)
v_fit = a*cota_v_smooth**2 + b*cota_v_smooth + c
plt.plot(v_fit, cota_v_smooth, 'r-', linewidth=2, label='Ajuste Cuadrático')

eq_v = fr'$V = {a:.4f} \cdot Cota^2 {b:+.4f} \cdot Cota {c:+.4f}$'
plt.text(0.05, 0.95, eq_v, transform=plt.gca().transAxes, fontsize=10, 
         verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

plt.ylabel('Cota IGN [m]')
plt.xlabel('Volumen [hm3]')
plt.title('Curva Cota-Volumen')
plt.legend(loc='lower right')
plt.grid(True, linestyle='--', alpha=0.7)

# Plot Caudal
plt.subplot(1, 2, 2)
plt.scatter(q_vals, cotas_q, color='blue', label='Datos Originales', s=5, alpha=0.3)

# Se grafica Q en función de Cota empezando desde C0 para evitar la línea vertical en Q=0
cota_q_smooth = np.linspace(c0_opt, 29.3, 300)
q_fit = d_opt * np.sqrt(cota_q_smooth - c0_opt)
plt.plot(q_fit, cota_q_smooth, 'g-', linewidth=2, label=r'Ajuste Optimizado')

eq_q = fr'$Q = {d_opt:.4f} \cdot \sqrt{{Cota - {c0_opt:.4f}}}$'
plt.text(0.05, 0.95, eq_q, transform=plt.gca().transAxes, fontsize=10, 
         verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

plt.ylabel('Cota IGN [m]')
plt.xlabel('Caudal [m3/s]')
plt.title('Curva Cota-Caudal (Descarga de Fondo)')
plt.legend(loc='lower right')
plt.grid(True, linestyle='--', alpha=0.7)

plt.tight_layout()
plt.savefig('validacion_parametrizacion.png')
print("\nGráfica de validación consolidada guardada en 'validacion_parametrizacion.png'")
