import numpy as np
from scipy.optimize import fsolve

# ==========================================
# 1. Definición de Funciones Hidráulicas (Bfl = 9.9m)
# ==========================================
def calc_Q_reducida_actualizada(H):
    """Calcula el caudal total Q usando las expresiones matemáticas actualizadas."""
    if H <= 0:
        return 0.0
    elif H <= 1.0:
        # Tramo 1: Canal Central
        numerador = ((7.50 + H) * H)**(5/3)
        denominador = (7.50 + 2 * np.sqrt(2) * H)**(2/3)
        factor = (4 * np.sqrt(2)) / 7
        return factor * (numerador / denominador)
    elif H <= 3.0:
        # Tramo 2: Canal Central + Laterales (9.9m)
        term_central = 0.1704 * (8.5 + 9.5 * (H - 1))**(5/3)
        term_lateral_num = (9.9 * (H - 1) + 0.5 * (H - 1)**2)**(5/3)
        term_lateral_den = (H + 8.9)**(2/3)
        return term_central + 1.6162 * (term_lateral_num / term_lateral_den)
    else:
        # Tramo 3: Canal Central + Laterales + Valle
        term_central = 0.1704 * (8.5 + 9.5 * (H - 1))**(5/3)
        term_lateral = 0.3100 * (11.9 * H - 13.9)**(5/3)
        term_valle = 89.09 * (H - 3)**(8/3)
        return term_central + term_lateral + term_valle

def calcular_Hs(H_local, eta):
    """Calcula la erosión Hs para un tirante local y rugosidad dados."""
    if H_local <= 0: return 0.0
    S = 0.0008
    gamma_d = 1.650
    beta = 1.05
    x = 0.31
    numerador = (1 / eta) * (S**0.5) * (H_local**(5/3))
    denominador = 0.75 * (gamma_d**1.18) * beta
    return (numerador / denominador)**(1 / (1 + x))

# ==========================================
# 2. Ejecución Principal
# ==========================================
if __name__ == "__main__":
    print("=" * 75)
    print(" EVALUACIÓN DE EROSIÓN EN CANAL COMPUESTO ACTUALIZADO (Q = 200 m3/s) ")
    print("=" * 75)

    Q_objetivo = 200.0

    # Encontrar H total para Q = 200 usando fsolve
    def buscar_tirante_objetivo(H):
        return calc_Q_reducida_actualizada(H) - Q_objetivo

    # Estimación inicial de 4.0 metros
    H_total = fsolve(buscar_tirante_objetivo, 4.0)[0]
    
    print(f"\nCaudal de diseño (Q) : {Q_objetivo:.2f} m3/s")
    print(f"Tirante Total (H)    : {H_total:.4f} m\n")
    
    print("-" * 75)
    print(f"{'Punto Analizado':<18} | {'H Local [m]':<12} | {'Hs [m]':<10} | {'Δ Erosión [m]'}")
    print("-" * 75)

    # ---------------------------------------------------------
    # Análisis Punto 1 (Centro absoluto)
    # ---------------------------------------------------------
    H_p1 = H_total
    Hs_p1 = calcular_Hs(H_p1, eta=0.035)
    delta_1 = Hs_p1 - H_p1 if Hs_p1 > H_p1 else 0.0
    texto_delta_1 = f"{delta_1:.4f}" if delta_1 > 0 else "0 (sin erosión)"
    
    print(f"{'1. Canal Central':<18} | {H_p1:<12.4f} | {Hs_p1:<10.4f} | {texto_delta_1}")

    # ---------------------------------------------------------
    # Análisis Punto 2 (Planicie Lateral)
    # ---------------------------------------------------------
    H_p2 = H_total - 1.0 # Le restamos la altura de la banquina
    Hs_p2 = calcular_Hs(H_p2, eta=0.035)
    delta_2 = Hs_p2 - H_p2 if Hs_p2 > H_p2 else 0.0
    texto_delta_2 = f"{delta_2:.4f}" if delta_2 > 0 else "0 (sin erosión)"
    
    print(f"{'2. Lateral':<18} | {H_p2:<12.4f} | {Hs_p2:<10.4f} | {texto_delta_2}")

    # ---------------------------------------------------------
    # Análisis Punto 3 (Vértice del Valle)
    # ---------------------------------------------------------
    H_p3 = H_total - 3.0 # Le restamos la altura hasta el valle
    Hs_p3 = calcular_Hs(H_p3, eta=0.120) # Rugosidad de 0.120
    delta_3 = Hs_p3 - H_p3 if Hs_p3 > H_p3 else 0.0
    texto_delta_3 = f"{delta_3:.4f}" if delta_3 > 0 else "0 (sin erosión)"
    
    print(f"{'3. Valle':<18} | {H_p3:<12.4f} | {Hs_p3:<10.4f} | {texto_delta_3}")
    
    print("=" * 75)