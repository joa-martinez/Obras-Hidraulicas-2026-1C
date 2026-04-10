import numpy as np
from scipy.optimize import fsolve

# ==========================================
# Constantes y Datos del Problema
# ==========================================
Q_TARGET_TOTAL = 74.0   # Caudal total objetivo en m3/s
H0_CENTRAL = 1          # Tirante central dado en metros
BF_CENTRAL = 7.50       # Base central dada en metros
N_RUGOSIDAD = 0.035     # Coeficiente de Manning (n)
S_PENDIENTE = 0.0008    # Pendiente de fondo (S)

# ==========================================
# Definición de Funciones Hidráulicas
# ==========================================

def calc_Q_central(H1, Bf, H0, n, S):
    """Calcula el caudal del canal central (Q_c) para un tirante H1 dado."""
    if H1 < 0: return 0.0
    A_c = (Bf + H0) * H0 + (Bf + 2 * H0) * H1
    P_c_geom = Bf + H0 * 2 * np.sqrt(2)
    R_c = A_c / P_c_geom
    
    Q_central_val = (1 / n) * A_c * (R_c**(2/3)) * np.sqrt(S)
    return Q_central_val

def calc_Q_lateral(Bfl, H1, n, S):
    """Calcula el caudal de UN floodplain lateral (Q_l)."""
    if Bfl <= 0 or H1 <= 0: return 0.0
    A_l = Bfl * H1 + (H1**2) / 2
    R_l = A_l / (Bfl + H1 * np.sqrt(2))
    
    Q_lateral_val = (1 / n) * A_l * (R_l**(2/3)) * np.sqrt(S)
    return Q_lateral_val

def fsolve_Bfl_residual(Bfl_guess, H1, Q_total_target, Bf_central, H0_central, n, S):
    """Residuo para encontrar Bfl dado un H1."""
    Q_c = calc_Q_central(H1, Bf_central, H0_central, n, S)
    Q_l = calc_Q_lateral(Bfl_guess, H1, n, S)
    return Q_total_target - (Q_c + 2 * Q_l)

def fsolve_H1_residual(H1_guess, Bfl_fixed, Q_total_target, Bf_central, H0_central, n, S):
    """Residuo para encontrar H1 dado un Bfl fijo (redondeado)."""
    # Si H1 es negativo, forzamos un error alto para que el solver vuelva a valores positivos
    if H1_guess <= 0:
        return 1e6
        
    Q_c = calc_Q_central(H1_guess, Bf_central, H0_central, n, S)
    Q_l = calc_Q_lateral(Bfl_fixed, H1_guess, n, S)
    return Q_total_target - (Q_c + 2 * Q_l)

def calcular_Hs(H):
    """
    Calcula el valor de erosión Hs según la fórmula geométrica/hidrodinámica.
    """
    eta = 0.035      # Asumimos que eta es igual a Manning (n)
    S = 0.0008       # Pendiente de fondo
    gamma_d = 1.650   # kg/m3
    beta = 1
    x = 0.31
    
    # Separamos la fórmula en partes
    numerador = (1 / eta) * (S**0.5) * (H**(5/3))
    denominador = 0.75 * (gamma_d**1.18) * beta
    
    # Aplicamos el exponente externo a toda la fracción
    Hs = (numerador / denominador)**(1 / (1 + x))
    return Hs

# ==========================================
# Ejecución Principal y Solver
# ==========================================

if __name__ == "__main__":
    print("-" * 65)
    print(" CÁLCULO DE CANAL COMPUESTO (Mantiene Q = 74 m3/s) ")
    print("-" * 65)
    
    try:
        h1_input = float(input("Ingrese el tirante inicial estimado sobre los laterales (H1) en m: "))
        
        if h1_input <= 0:
            print("Error: El tirante H1 debe ser mayor a 0.")
        else:
            # 1. Verificación inicial de capacidad del canal central
            Q_c_prelim = calc_Q_central(h1_input, BF_CENTRAL, H0_CENTRAL, N_RUGOSIDAD, S_PENDIENTE)
            if Q_c_prelim >= Q_TARGET_TOTAL:
                print(f"\nPara H1 = {h1_input}m, el canal central ya transporta {Q_c_prelim:.2f} m3/s.")
                print("No se requieren floodplains (Bfl matemático <= 0).")
            else:
                # 2. Encontrar Bfl exacto para el H1 ingresado
                Bfl_exacto = fsolve(
                    fsolve_Bfl_residual, 10.0, 
                    args=(h1_input, Q_TARGET_TOTAL, BF_CENTRAL, H0_CENTRAL, N_RUGOSIDAD, S_PENDIENTE)
                )[0]
                
                if Bfl_exacto < 0:
                    print("\nError: No hay solución de ancho positivo para estos datos.")
                else:
                    # 3. Redondear Bfl hacia arriba a múltiplos de 5 cm (0.05 m)
                    Bfl_redondeado = np.ceil(Bfl_exacto / 0.05) * 0.05
                    
                    # 4. RECALCULAR H1 usando el Bfl redondeado para mantener Q = 74
                    # Usamos el h1_input como valor inicial de búsqueda (guess)
                    H1_recalculado = fsolve(
                        fsolve_H1_residual, h1_input,
                        args=(Bfl_redondeado, Q_TARGET_TOTAL, BF_CENTRAL, H0_CENTRAL, N_RUGOSIDAD, S_PENDIENTE)
                    )[0]
                    
                    # 5. Verificación final de caudales con las nuevas geometrías
                    Q_c_final = calc_Q_central(H1_recalculado, BF_CENTRAL, H0_CENTRAL, N_RUGOSIDAD, S_PENDIENTE)
                    Q_l_final = calc_Q_lateral(Bfl_redondeado, H1_recalculado, N_RUGOSIDAD, S_PENDIENTE)
                    Q_total_final = Q_c_final + 2 * Q_l_final

                    # 6. Cálculo de Erosión Hs para cada sector
                    Hs_lateral = calcular_Hs(H1_recalculado)
                    Hs_central = calcular_Hs(H0_CENTRAL + H1_recalculado)
                    
                    # Imprimir Resultados
                    print("\n" + "=" * 55)
                    print("                RESULTADOS FINALES                ")
                    print("=" * 55)
                    print("--- 1. Diseño Geométrico ---")
                    print(f"H1 sobre laterales             : {h1_input:.4f} m")
                    print(f"Bfl                            : {Bfl_exacto:.4f} m")
                    print(f"Bfl REDONDEADO de diseño       : {Bfl_redondeado:.2f} m")
                    print(f"H1 RECALCULADO final           : {H1_recalculado:.4f} m")
                    
                    print("\n--- 2. Verificación Caudales ---")
                    print(f"Q Canal Central                : {Q_c_final:.3f} m3/s")
                    print(f"Q Laterales                    : {2 * Q_l_final:.3f} m3/s")
                    print("-" * 55)
                    print(f"CAUDAL TOTAL                   : {Q_total_final:.3f} m3/s")

                    print("\n--- 3. Verificación de Erosión (Hs) ---")
                    print(f"Tirante Lateral (H = {H1_recalculado:.4f} m)   -> Hs = {Hs_lateral:.4f} m")
                    print(f"Tirante Central (H = {H0_CENTRAL + H1_recalculado:.4f} m) -> Hs = {Hs_central:.4f} m")
                    print("=" * 55)

    except ValueError:
        print("Error: Ingrese un número válido para el tirante H1.")