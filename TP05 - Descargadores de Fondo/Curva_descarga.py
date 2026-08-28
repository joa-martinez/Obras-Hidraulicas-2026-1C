import numpy as np
from scipy.optimize import fsolve
from Calculo_Q_salida_orificios import calc_Q_reducida, L

def calcular_Q_descarga_libre(H0, D, N, Z_inv=None, eta=0.015, S=0.005):
    """
    Calcula el caudal (Q) para una sección circular funcionando como canal libre.
    Emplea relaciones geométricas de una sección parcialmente llena (ángulo central theta,
    radio hidráulico) y la ecuación de Chezy-Manning para determinar el caudal cuando el
    nivel del agua no presuriza el conducto (hasta y=0.938*D).
    """
    if Z_inv is None:
        Z_inv = D / 2
    y = H0 - Z_inv
    y = np.clip(y, 0, D*0.938)
    theta = 2 * np.arccos(1 - (2 * y) / D)
    A = (D**2 / 8) * (theta - np.sin(theta))
    
    term_sin_theta_div_theta = np.zeros_like(theta)
    non_zero_mask = theta > 0
    term_sin_theta_div_theta[non_zero_mask] = np.sin(theta[non_zero_mask]) / theta[non_zero_mask]
    R = (D / 4) * (1 - term_sin_theta_div_theta)
    
    Q = N * (1 / eta) * A * (R**(2/3)) * np.sqrt(S)
    return Q

def calcular_Q_descarga_libre_completa(H0, D, N, Z_inv=None, eta=0.015, S=0.005):
    """
    Calcula el caudal (Q) para una sección circular funcionando como canal libre,
    permitiendo el cálculo hasta la sección plena (y = D).
    """
    if Z_inv is None:
        Z_inv = D / 2
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

def calcular_tramo3_pared_gruesa(y_vals, D, N_orificios, L_cond, eta=0.015, sum_xi=0.05):
    """
    Calcula el Tramo 3: Orificio Ahogado (Pared Gruesa).
    Modela hidráulicamente los orificios trabajando a sección llena. 
    Relaciona los tirantes aguas abajo con la cota de energía aguas arriba (H0) 
    """
    g = 9.81
    A = (np.pi * D**2) / 4
    f_L_D = ((124.52 * eta**2) / (D**(1/3))) * (L_cond / D)
    mu = 1 / np.sqrt(1 + sum_xi + f_L_D)
    
    Q_vals = np.array([calc_Q_reducida(y) for y in y_vals])
    Z0_vals = (Q_vals / (N_orificios * mu * A))**2 / (2 * g)
    H0_vals = Z0_vals + y_vals
    
    return Q_vals, H0_vals

def encontrar_y_para_H0(H0_target, D, N_orificios, L_cond):
    """
    Encuentra el tirante 'y' aguas abajo necesario para equilibrar una cota H0 dada.
    Aplica fsolve para iterar: dado un nivel 
    fijo de embalse (H0_target), calcula cuál es el tirante aguas abajo que induce 
    exactamente esa carga de energía requerida.
    """
    def residuo(y_guess):
        y_g = float(y_guess[0])
        if y_g <= 0: return -H0_target + (y_g * 100)
        _, H0_calc = calcular_tramo3_pared_gruesa([y_g], D, N_orificios, L_cond)
        return H0_calc[0] - H0_target
    return fsolve(residuo, 1.0)[0]

def generar_curva_descarga(D_constructivo, N, elevacion_base=None):
    """
    Genera los datos de la curva de descarga H-Q para un diámetro y número de orificios dados.
    """
    if elevacion_base is None:
        elevacion_base = D_constructivo / 2
        
    # TRAMO 1: Descarga Libre (Canal)
    H0_max_libre = elevacion_base + 0.938 * D_constructivo
    H0_tramo_libre = np.linspace(elevacion_base, H0_max_libre, 100)
    Q_tramo_libre = calcular_Q_descarga_libre(H0_tramo_libre, D_constructivo, N, Z_inv=elevacion_base)

    # TRAMO 3: Orificio de Pared Gruesa (Ahogado)
    H0_min_tramo3 = elevacion_base + 2 * D_constructivo
    H0_max_tramo3 = 8.3

    y_min_t3 = encontrar_y_para_H0(H0_min_tramo3, D_constructivo, N, L)
    y_max_t3 = encontrar_y_para_H0(H0_max_tramo3, D_constructivo, N, L)

    y_tramo3 = np.linspace(y_min_t3, y_max_t3, 100)
    Q_tramo3, H0_tramo3 = calcular_tramo3_pared_gruesa(y_tramo3, D_constructivo, N, L)

    # TRAMO 2: Interpolación Lineal (Transición)
    Q_tramo2 = np.linspace(Q_tramo_libre[-1], Q_tramo3[0], 50)
    H0_tramo2 = np.linspace(H0_tramo_libre[-1], H0_tramo3[0], 50)
    
    # Combinar tramos
    H_total = np.concatenate((H0_tramo_libre, H0_tramo2, H0_tramo3))
    Q_total = np.concatenate((Q_tramo_libre, Q_tramo2, Q_tramo3))
    
    return {
        "H": H_total, "Q": Q_total,
        "T1": {"H": H0_tramo_libre, "Q": Q_tramo_libre},
        "T2": {"H": H0_tramo2, "Q": Q_tramo2},
        "T3": {"H": H0_tramo3, "Q": Q_tramo3}
    }

if __name__ == '__main__':
    # Ejemplo de uso si se ejecuta el script directamente
    import matplotlib.pyplot as plt

    D_constructivo = 0.95
    N = 8
    
    data = generar_curva_descarga(D_constructivo, N)
    
    plt.figure(figsize=(10, 8))
    plt.plot(data['Q'], data['H'] + 21.0, label=f"D={D_constructivo}m, N={N}")
    plt.title('Curva de Descarga H-Q')
    plt.xlabel('Caudal (Q) [m³/s]')
    plt.ylabel('Cota IGN [m]')
    plt.grid(True)
    plt.legend()
    plt.show()
