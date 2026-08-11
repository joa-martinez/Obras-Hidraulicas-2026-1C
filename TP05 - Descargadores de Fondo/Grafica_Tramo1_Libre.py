import numpy as np
import matplotlib.pyplot as plt

def calcular_Q_descarga_libre_completa(H0, D, N, Z_inv=None, eta=0.015, S=0.005):
    """
    Calcula el caudal (Q) para una sección circular funcionando como canal libre,
    permitiendo el cálculo hasta la sección plena (y = D).
    """
    if Z_inv is None:
        Z_inv = D
    y = H0 - Z_inv
    
    # Restringimos el dominio hasta D (sección plena)
    y = np.clip(y, 0, D)
    
    # Protegemos el arcocoseno ante posibles errores de punto flotante en y=D
    arg_arccos = np.clip(1 - (2 * y) / D, -1.0, 1.0)
    theta = 2 * np.arccos(arg_arccos)
    
    A = (D**2 / 8) * (theta - np.sin(theta))
    
    term_sin_theta_div_theta = np.zeros_like(theta)
    non_zero_mask = theta > 0
    term_sin_theta_div_theta[non_zero_mask] = np.sin(theta[non_zero_mask]) / theta[non_zero_mask]
    R = (D / 4) * (1 - term_sin_theta_div_theta)
    
    Q = N * (1 / eta) * A * (R**(2/3)) * np.sqrt(S)
    
    return Q, y

# ==========================================
# Parámetros 
# ==========================================
D_constructivo = 1.0
elevacion_base = D_constructivo
N = 10

# Cota para Sección Plena (y = D)
H0_max_plena = elevacion_base + D_constructivo
H0_vals = np.linspace(elevacion_base, H0_max_plena, 200)

Q_vals, _ = calcular_Q_descarga_libre_completa(H0_vals, D_constructivo, N, Z_inv=elevacion_base)

# ==========================================
# Encontrar puntos notables
# ==========================================
y_max_q = 0.938 * D_constructivo
H0_max_q = elevacion_base + y_max_q
Q_max_q, _ = calcular_Q_descarga_libre_completa(np.array([H0_max_q]), D_constructivo, N, Z_inv=elevacion_base)
Q_max_q = Q_max_q[0]

Q_plena = Q_vals[-1]
H0_plena = H0_vals[-1]

# ==========================================
# Gráfica
# ==========================================
plt.figure(figsize=(9, 7))
plt.plot(Q_vals, H0_vals, linewidth=2.5, color='#1f77b4', label='Curva de Descarga (Canal)')
plt.plot(Q_max_q, H0_max_q, marker='o', color='#ff7f0e', markersize=7, zorder=5, label=f'Caudal Máximo (y = 0.938D)\nQ = {Q_max_q:.2f} ($m^3/s$)')
plt.plot(Q_plena, H0_plena, marker='o', color='#d62728', markersize=7, zorder=5, label=f'Sección Plena (y = D)\nQ = {Q_plena:.2f} ($m^3/s$)')
plt.title('Descarga Libre en Conductos Circulares (Tramo 1)', fontsize=14, fontweight='bold')
plt.xlabel('Caudal Total $Q$ ($m^3/s$)', fontsize=12, fontweight='bold')
plt.ylabel('Tirante de embalse $H_0$ (m)', fontsize=12, fontweight='bold')
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend(loc='lower right', fontsize=10)

plt.xlim(0, max(Q_vals) * 1.1)
plt.ylim(elevacion_base * 0.9, H0_max_plena * 1.1)

plt.show()