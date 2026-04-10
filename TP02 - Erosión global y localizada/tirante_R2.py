import numpy as np
from scipy.optimize import fsolve

def calcular_altura_agua(B_f):
    """
    Calcula la altura del pelo de agua (H0) para un canal trapezoidal
    usando la ecuación de Manning.
    """
    n = 0.035
    S = 0.0008
    Q_objetivo = 6.0
    
    def funcion_manning(h):
        if h <= 0:
            return 1e6 
            
        A = (B_f + h) * h
        P = B_f + h * 2 * np.sqrt(2) 
        R = A / P
        
        Q_calculado = (1 / n) * A * (R**(2/3)) * np.sqrt(S)
        return Q_calculado - Q_objetivo
        
    h_inicial = 1.0 
    h_resultado = fsolve(funcion_manning, h_inicial)
    
    return h_resultado[0]

def calcular_base_fondo(h):
    """
    Calcula la base de fondo (Bf) para un canal trapezoidal
    dado un tirante (h) usando la ecuación de Manning.
    """
    n = 0.035
    S = 0.0008
    Q_objetivo = 6.0
    
    def funcion_manning_Bf(B_f):
        if B_f <= 0:
            return 1e6 
            
        A = (B_f + h) * h
        P = B_f + h * 2 * np.sqrt(2) 
        R = A / P
        
        Q_calculado = (1 / n) * A * (R**(2/3)) * np.sqrt(S)
        return Q_calculado - Q_objetivo
        
    B_f_inicial = 5.0 # Estimación inicial para la base
    B_f_resultado = fsolve(funcion_manning_Bf, B_f_inicial)
    
    return B_f_resultado[0]

def calcular_Hs(H0):
    """
    Calcula el valor de Hs según la fórmula geométrica/hidrodinámica.
    """
    eta = 0.035      # Asumimos que eta es igual a Manning (n)
    S = 0.0008       # Pendiente de fondo
    gamma_d = 1.65   # kg/m3
    beta = 0.82
    x = 0.31
    
    # Separamos la fórmula en partes para evitar errores de tipeo en Python
    numerador = (1 / eta) * (S**0.5) * (H0**(5/3))
    denominador = 0.75 * (gamma_d**1.18) * beta
    
    # Aplicamos el exponente externo a toda la fracción
    Hs = (numerador / denominador)**(1 / (1 + x))
    
    return Hs

# ==========================================
# Interfaz de Usuario
# ==========================================

if __name__ == "__main__":
    print("-" * 50)
    print(" CÁLCULO DE CANAL TRAPEZOIDAL ")
    print("-" * 50)
    print("¿Qué dato deseas ingresar como punto de partida?")
    print("1. Base de fondo del canal (Bf)")
    print("2. Tirante de agua (h / H0)")
    
    opcion = input("Selecciona 1 o 2: ")
    print("-" * 50)

    if opcion == '1':
        try:
            B_f_input = float(input("Ingresa la base de fondo (Bf) en metros: "))
            H0 = calcular_altura_agua(B_f_input)
            Hs = calcular_Hs(H0)
            
            print("\n--- RESULTADOS ---")
            print(f"Base de fondo (Bf) ingresada : {B_f_input:.2f} m")
            print(f"Tirante (H0) calculado       : {H0:.4f} m")
            print(f"Valor Hs calculado           : {Hs:.4f} m")
            
        except ValueError:
            print("Error: Por favor ingresa un número válido.")
            
    elif opcion == '2':
        try:
            h_input = float(input("Ingresa el tirante de agua deseado (h) en metros: "))
            
            # 1. Calculamos la base de fondo exacta
            B_f_exacto = calcular_base_fondo(h_input)
            
            # 2. Redondeamos hacia arriba a los 5 cm (0.05 m)
            B_f_redondeado = np.ceil(B_f_exacto / 0.05) * 0.05
            
            # 3. Recalculamos el tirante y Hs con la base redondeada
            H0_recalculado = calcular_altura_agua(B_f_redondeado)
            Hs = calcular_Hs(H0_recalculado)
            
            print("\n--- RESULTADOS ---")
            print(f"Tirante objetivo original    : {h_input:.4f} m")
            print(f"Base de fondo exacta         : {B_f_exacto:.4f} m")
            print(f"Base de fondo REDONDEADA (Bf): {B_f_redondeado:.2f} m")
            print(f"Tirante RECALCULADO (H0)     : {H0_recalculado:.4f} m")
            print(f"Valor Hs calculado           : {Hs:.4f} m")
            
        except ValueError:
            print("Error: Por favor ingresa un número válido.")
    else:
        print("Opción no válida. Por favor ejecuta el script nuevamente y elige 1 o 2.")

    print("-" * 50)