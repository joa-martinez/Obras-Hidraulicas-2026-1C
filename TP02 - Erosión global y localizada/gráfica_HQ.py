import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve

def calc_Q_reducida(H):
    """Calcula el caudal total Q usando las expresiones matemáticas actualizadas (Bfl = 9.9m)."""
    if H <= 0:
        return 0.0
    elif H <= 1.0:
        # Tramo 1: H <= 1m (Canal Central)
        numerador = ((7.50 + H) * H)**(5/3)
        denominador = (7.50 + 2 * np.sqrt(2) * H)**(2/3)
        factor = (4 * np.sqrt(2)) / 7
        return factor * (numerador / denominador)
    elif H <= 3.0:
        # Tramo 2: 1m < H <= 3m (Central + Laterales ampliados)
        term_central = 0.1704 * (8.5 + 9.5 * (H - 1))**(5/3)
        term_lateral_num = (9.9 * (H - 1) + 0.5 * (H - 1)**2)**(5/3) # Actualizado: 9.9m
        term_lateral_den = (H + 8.9)**(2/3)                          # Actualizado: Perímetro
        return term_central + 1.6162 * (term_lateral_num / term_lateral_den)
    else:
        # Tramo 3: H > 3m (Central + Laterales ampliados + Valle)
        term_central = 0.1704 * (8.5 + 9.5 * (H - 1))**(5/3)
        term_lateral = 0.3100 * (11.9 * H - 13.9)**(5/3)             # Actualizado: Constantes nuevas
        term_valle = 89.09 * (H - 3)**(8/3)
        return term_central + term_lateral + term_valle

# ==========================================
# 1. Encontrar el H exacto para Q = 300 m3/s
# ==========================================
def buscar_tirante_maximo(H):
    return calc_Q_reducida(H) - 300

# Usamos fsolve para encontrar la altura final de la gráfica
H_max_exacto = fsolve(buscar_tirante_maximo, 4.0)[0]
print(f"El tirante H máximo para Q=300 m3/s es: {H_max_exacto:.4f} m")

# ==========================================
# 2. Generar datos y Plotear
# ==========================================
# Creamos el rango de valores de X (Tirante) hasta el máximo calculado
H_plot = np.linspace(0, H_max_exacto, 500)
Q_plot = [calc_Q_reducida(h) for h in H_plot]

plt.figure(figsize=(10, 7))

# Trazar la curva
plt.plot(H_plot, Q_plot, linewidth=2.5, color='#1f77b4', label='Curva de Descarga')

# Configurar marcas del eje X para que sigan viéndose ordenadas cada 0.5m
ticks_x = np.arange(0.0, np.ceil(H_max_exacto*2)/2 + 0.5, 0.5)
plt.xticks(ticks_x, rotation=45)

# --- Configurar marcas del eje Y forzadas de 0 a 300 cada 25 ---
ticks_y = np.arange(0, 301, 25)
plt.yticks(ticks_y)

# Líneas de referencia para los desbordes
plt.axvline(1.0, color='red', linestyle='--', alpha=0.7, label='Desborde a Laterales (H=1m)')
plt.axvline(3.0, color='green', linestyle='--', alpha=0.7, label='Desborde a Valle (H=3m)')

# Estilos y etiquetas
plt.xlabel('Tirante Total H (m)', fontsize=12, fontweight='bold')
plt.ylabel('Caudal Q ($m^3/s$)', fontsize=12, fontweight='bold')
plt.title('Curva de Descarga (H-Q) hasta 300 $m^3/s$', fontsize=14, fontweight='bold')
plt.grid(True, which='both', linestyle='--', alpha=0.5)
plt.legend(fontsize=10, loc='upper left')

# Guardar figura
plt.savefig('curva_HQ_300_actualizada.png', dpi=300, bbox_inches='tight')
print("¡Gráfica guardada como 'curva_HQ_300_actualizada.png'!")