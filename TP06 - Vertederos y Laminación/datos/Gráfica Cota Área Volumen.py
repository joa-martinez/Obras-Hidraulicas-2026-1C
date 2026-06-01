import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator
import os

# ==========================================
# 0. Directorio y Datos
# ==========================================
directorio_script = os.path.dirname(os.path.abspath(__file__))

cotas = np.array([24.00, 25.00, 26.25, 27.50, 28.75, 30.00, 31.25])
area = np.array([0.00, 249.10, 567.46, 1275.30, 1963.96, 2705.31, 3486.73])
volumen = np.array([0.00, 1.25, 6.35, 17.87, 38.11, 67.29, 105.99])

# ==========================================
# 1. Funciones de Interpolación
# ==========================================
interp_area = PchipInterpolator(cotas, area)
interp_vol = PchipInterpolator(cotas, volumen)

cotas_suaves = np.linspace(cotas.min(), cotas.max(), 300)
area_suave = interp_area(cotas_suaves)
volumen_suave = interp_vol(cotas_suaves)

# ==========================================
# 2. Cálculo de valores para Cota 29.3 m
# ==========================================
cota_objetivo = 29.3
area_obj = 2288.2
vol_obj = 50.88

# ==========================================
# 3. Configurar y Plotear
# ==========================================
fig, (ax1, ax2) = plt.subplots(1, 2, sharey=True, figsize=(10, 7), gridspec_kw={'wspace': 0})

color_linea = '#1f77b4'
grosor_linea = 2.5
color_rojo = 'red'

# ---------------------------------------------------------
# Subgráfico Izquierdo: ÁREA
# ---------------------------------------------------------
ax1.plot(area_suave, cotas_suaves, linewidth=grosor_linea, color=color_linea)
ax1.scatter(area, cotas, color=color_linea, marker='o', s=40, zorder=5)

# Líneas y marcador rojo
ax1.hlines(cota_objetivo, xmin=0, xmax=area_obj, colors=color_rojo, linestyles='--', alpha=0.7)
ax1.vlines(area_obj, ymin=cotas.min(), ymax=cota_objetivo, colors=color_rojo, linestyles='--', alpha=0.7)
ax1.plot(area_obj, cota_objetivo, marker='s', color=color_rojo, markersize=6)

# Texto acomodado (Desplazado -80 en X para alejarlo de la línea, subido +0.3 en Y para despegarlo del eje)
ax1.text(area_obj - 150, cotas.min() + 0.3, f'{area_obj:.1f} $hm^2$', 
         color=color_rojo, rotation=90, va='bottom', ha='center', fontsize=11, fontweight='bold')

ax1.set_xlim(area.max() * 1.05, 0)
ax1.set_ylim(bottom=cotas.min(), top=cotas.max() + 0.2) # Fijar el límite inferior exacto en 24.0
ax1.set_ylabel('Cota IGN (m)', fontsize=12, fontweight='bold')
ax1.set_xlabel('Superficie ($hm^2$)', fontsize=12, fontweight='bold')
ax1.grid(True, which='both', linestyle='--', alpha=0.5)

# ---------------------------------------------------------
# Subgráfico Derecho: VOLUMEN
# ---------------------------------------------------------
ax2.plot(volumen_suave, cotas_suaves, linewidth=grosor_linea, color=color_linea)
ax2.scatter(volumen, cotas, color=color_linea, marker='o', s=40, zorder=5)

# Líneas y marcador rojo
ax2.hlines(cota_objetivo, xmin=0, xmax=vol_obj, colors=color_rojo, linestyles='--', alpha=0.7)
ax2.vlines(vol_obj, ymin=cotas.min(), ymax=cota_objetivo, colors=color_rojo, linestyles='--', alpha=0.7)
ax2.plot(vol_obj, cota_objetivo, marker='s', color=color_rojo, markersize=6)

# Texto acomodado (Desplazado +5 en X)
ax2.text(vol_obj + 7, cotas.min() + 0.3, f'{vol_obj:.2f} $hm^3$', 
         color=color_rojo, rotation=90, va='bottom', ha='center', fontsize=11, fontweight='bold')

# Texto de la cota central
ax2.text(5, cota_objetivo + 0.15, f'{cota_objetivo} m', color=color_rojo, 
         fontsize=11, fontweight='bold', ha='left', va='bottom')

ax2.set_xlim(0, volumen.max() * 1.05)
ax2.set_xlabel('Volumen acumulado ($hm^3$)', fontsize=12, fontweight='bold')
ax2.grid(True, which='both', linestyle='--', alpha=0.5)

# ---------------------------------------------------------
# Detalles finales (Sin cuadro de referencias)
# ---------------------------------------------------------
ax2.spines['left'].set_visible(False)
ax2.tick_params(axis='y', which='both', left=False) 

# --- NUEVO: Hacer la línea central (Cota) más gruesa y visible ---
ax1.spines['right'].set_linewidth(3)   # Ajusta este número para darle más grosor
ax1.spines['right'].set_color('black') # Color de la línea central (puedes usar '#333333' o 'black')
# -----------------------------------------------------------------

# Ajuste de márgenes
plt.subplots_adjust(top=0.92, bottom=0.12, left=0.1, right=0.9)

ax2.spines['left'].set_visible(False)
ax2.tick_params(axis='y', which='both', left=False) 

# Ajuste de márgenes
plt.subplots_adjust(top=0.92, bottom=0.12, left=0.1, right=0.9)

ruta_imagen = os.path.join(directorio_script, 'curvas_cota_area_volumen_final.png')
plt.savefig(ruta_imagen, dpi=300, bbox_inches='tight')
print(f"¡Gráfica guardada en:\n -> {ruta_imagen}")

plt.show()