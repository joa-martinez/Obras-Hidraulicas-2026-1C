import math
import csv
from scipy.optimize import fsolve

# ==========================================
# Constantes Globales
# ==========================================
L = 15.0         # Longitud del orificio (m)
H = 3.1125         # Tirante de agua aguas abajo (m)

# ==========================================
# Curva H-Q (Aguas abajo)
# ==========================================
def calc_Q_reducida(H_val):
    """
    Calcula el caudal total Q usando las expresiones matemáticas de la curva H-Q.
    Evalúa el caudal de descarga aguas abajo en función del tirante (H) mediante
    una curva de ajuste empírica dividida en tres tramos de comportamiento.
    """
    if H_val <= 0:
        return 0.0
    elif H_val <= 1.0:
        numerador = ((7.50 + H_val) * H_val)**(5/3)
        denominador = (7.50 + 2 * math.sqrt(2) * H_val)**(2/3)
        factor = (4 * math.sqrt(2)) / 7
        return factor * (numerador / denominador)
    elif H_val <= 3.0:
        term_central = 0.1704 * (8.5 + 9.5 * (H_val - 1))**(5/3)
        term_lateral_num = (9.9 * (H_val - 1) + 0.5 * (H_val - 1)**2)**(5/3)
        term_lateral_den = (H_val + 8.9)**(2/3)
        return term_central + 1.6162 * (term_lateral_num / term_lateral_den)
    else:
        term_central = 0.1704 * (8.5 + 9.5 * (H_val - 1))**(5/3)
        term_lateral = 0.3100 * (11.9 * H_val - 13.9)**(5/3)
        term_valle = 89.09 * (H_val - 3)**(8/3)
        return term_central + term_lateral + term_valle

def calcular_H_desde_Q(Q_target):
    """
    Obtiene el tirante H aguas abajo correspondiente a un caudal objetivo Q.
    Utiliza un método numérico (fsolve) para buscar la raíz (invertir la curva H-Q),
    iterando hasta encontrar el tirante exacto que satisface el caudal requerido.
    """
    if Q_target <= 0: return 0.0
    def residuo(h_guess):
        h_val = float(h_guess[0])
        if h_val <= 0: return -Q_target + (h_val * 100)
        return calc_Q_reducida(h_val) - Q_target
    return fsolve(residuo, max(0.5, Q_target / 100.0))[0]

def calcular_caudal_orificios(D, N, H=H):
    """
    Calcula el caudal de salida para orificios de pared gruesa.
    
    Determina la capacidad de descarga presurizada aplicando la ecuación de
    Torricelli/Bernoulli, utilizando un coeficiente de descarga (mu) que contempla
    pérdidas por fricción dependientes de la rugosidad de Manning y pérdidas localizadas.
    
    Parámetros:
    D : Diámetro del orificio (m)
    N : Número de orificios
    H : Tirante de agua aguas abajo (m)
    """
    # ==========================================
    # 1. Definición de Constantes y Datos
    # ==========================================
    g = 9.81         # Gravedad (m/s^2)
    eta = 0.015      # Rugosidad de Manning (hormigón)
    sum_xi = 0.05    # Pérdidas localizadas (bordes redondeados)
    cota_ccv = 29.30 # Cota del embalse aguas arriba (m)

    # ==========================================
    # 2. Cálculos Hidráulicos
    # ==========================================
    # Carga hidráulica efectiva (Diferencia de niveles)
    Z0 = cota_ccv - H
    
    # Área de la sección transversal de un orificio
    A = (math.pi * D**2) / 4
    
    # Pérdidas por fricción f(L/D) según la fórmula de la imagen
    # f(L/D) = [124.52 * n^2 / D^(1/3)] * (L / D)
    f_L_D = ((124.52 * eta**2) / (D**(1/3))) * (L / D)
    
    # Coeficiente de gasto (mu)
    mu = 1 / math.sqrt(1 + sum_xi + f_L_D)
    
    # Caudal total de salida (Q_salida)
    signo_Z0 = 1 if Z0 >= 0 else -1
    Q_salida = signo_Z0 * N * mu * A * math.sqrt(2 * g * abs(Z0))
    
    return Q_salida, mu, Z0, f_L_D, sum_xi, eta

def fsolve_D_residual(D_guess, Q_target, N, H=H):
    """
    Residuo para encontrar el diámetro D que da el caudal Q_target.
    Es la función objetivo minimizada numéricamente por fsolve: compara el caudal 
    generado por un diámetro de prueba frente al caudal deseado para converger al óptimo.
    """
    D_val = float(D_guess[0]) # fsolve pasa un array, extraemos el elemento para la librería 'math'
    if D_val <= 0:
        return 1e6
    Q_calc, _, _, _, _, _ = calcular_caudal_orificios(D_val, N, H)
    return Q_calc - Q_target

def mostrar_tabla_resultados(D, xi, N, f_L_D, mu, Q, L, eta, Z0, H, Q_target=None, D_exacto=None):
    """
    Muestra los resultados del cálculo en formato de tabla.
    """
    print("\n" + "=" * 62)
    print(f"| {'Parámetro':<35} | {'Valor':<20} |")
    print("-" * 62)
    if Q_target is None:
        print(f"| {'Longitud del conducto (L) [m]':<35} | {L:<20.2f} |")
        print(f"| {'Tirante aguas abajo (H) [m]':<35} | {H:<20.4f} |")
        print(f"| {'Carga efectiva (Z0) [m]':<35} | {Z0:<20.3f} |")
        print(f"| {'Cantidad de orificios (N)':<35} | {N:<20} |")
        print(f"| {'Rugosidad de Manning (η)':<35} | {eta:<20.4f} |")
        print(f"| {'Coeficiente xi (ξ)':<35} | {xi:<20.2f} |")
        print(f"| {'Factor f(L/D)':<35} | {f_L_D:<20.3f} |")
        print(f"| {'Coeficiente mu (μ)':<35} | {mu:<20.3f} |")
        print(f"| {'Diámetro adoptado [m]':<35} | {D:<20.2f} |")
        print(f"| {'Caudal calculado [m³/s]':<35} | {Q:<20.2f} |")
    else:
        print(f"| {'Caudal objetivo [m³/s]':<35} | {Q_target:<20.2f} |")
        print(f"| {'Longitud del conducto (L) [m]':<35} | {L:<20.2f} |")
        print(f"| {'Tirante aguas abajo (H) [m]':<35} | {H:<20.4f} |")
        print(f"| {'Carga efectiva (Z0) [m]':<35} | {Z0:<20.3f} |")
        print(f"| {'Cantidad de orificios (N)':<35} | {N:<20} |")
        print(f"| {'Rugosidad de Manning (η)':<35} | {eta:<20.4f} |")
        print(f"| {'Coeficiente xi (ξ)':<35} | {xi:<20.2f} |")
        print(f"| {'Factor f(L/D)':<35} | {f_L_D:<20.3f} |")
        print(f"| {'Coeficiente mu (μ)':<35} | {mu:<20.3f} |")
        if D_exacto is not None:
            print(f"| {'Diámetro calculado [m]':<35} | {D_exacto:<20.4f} |")
        print(f"| {'Diámetro constructivo (D) [m]':<35} | {D:<20.2f} |")
        print(f"| {'CAUDAL TOTAL resultante [m³/s]':<35} | {Q:<20.2f} |")
    print("=" * 62)

def exportar_a_csv(D, xi, N, f_L_D, mu, Q, L, eta, Z0, H, Q_target=None, D_exacto=None, archivo="resultados_orificios.csv"):
    """
    Exporta los resultados del cálculo y/o optimización a un archivo CSV.
    """
    with open(archivo, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Parámetro", "Valor"])
        if Q_target is None:
            writer.writerow(["Longitud del conducto (L) [m]", f"{L:.2f}"])
            writer.writerow(["Tirante aguas abajo (H) [m]", f"{H:.4f}"])
            writer.writerow(["Carga efectiva (Z0) [m]", f"{Z0:.3f}"])
            writer.writerow(["Cantidad de orificios (N)", N])
            writer.writerow(["Rugosidad de Manning (eta)", f"{eta:.4f}"])
            writer.writerow(["Coeficiente xi (xi)", f"{xi:.2f}"])
            writer.writerow(["Factor f(L/D)", f"{f_L_D:.3f}"])
            writer.writerow(["Coeficiente mu (mu)", f"{mu:.3f}"])
            writer.writerow(["Diámetro adoptado [m]", f"{D:.2f}"])
            writer.writerow(["Caudal calculado [m3/s]", f"{Q:.2f}"])
        else:
            writer.writerow(["Caudal objetivo [m3/s]", f"{Q_target:.2f}"])
            writer.writerow(["Longitud del conducto (L) [m]", f"{L:.2f}"])
            writer.writerow(["Tirante aguas abajo (H) [m]", f"{H:.4f}"])
            writer.writerow(["Carga efectiva (Z0) [m]", f"{Z0:.3f}"])
            writer.writerow(["Cantidad de orificios (N)", N])
            writer.writerow(["Rugosidad de Manning (eta)", f"{eta:.4f}"])
            writer.writerow(["Coeficiente xi (xi)", f"{xi:.2f}"])
            writer.writerow(["Factor f(L/D)", f"{f_L_D:.3f}"])
            writer.writerow(["Coeficiente mu (mu)", f"{mu:.3f}"])
            if D_exacto is not None:
                writer.writerow(["Diámetro calculado [m]", f"{D_exacto:.4f}"])
            writer.writerow(["Diámetro del orificio (D) constructivo [m]", f"{D:.2f}"])
            writer.writerow(["CAUDAL TOTAL resultante [m3/s]", f"{Q:.2f}"])
    print(f"\n[+] Resultados exportados exitosamente a '{archivo}'")

# ==========================================
# 3. Bloque Principal de Ejecución
# ==========================================
if __name__ == "__main__":
    print("-------------------------------------------------------")
    print("Cálculo de Caudal: Orificios de Pared Gruesa / Conductos")
    print("-------------------------------------------------------")
    print("1. Calcular tirante aguas abajo (H) desde curva H-Q")
    print("2. Optimizar diámetro (D) para un caudal objetivo (Q)")
    print("3. Calcular caudal (Q) a partir de un diámetro (D)")
    print("-------------------------------------------------------")
    
    try:
        opcion = input("Seleccione una opción (1, 2 o 3): ")
        
        if opcion == '1':
            Q_target = float(input("\nIngrese el caudal en m³/s (ej. 70): "))
            if Q_target <= 0:
                print("Error: El caudal debe ser positivo.")
            elif Q_target > 300:
                print("Error: La curva H-Q solo está desarrollada para caudales hasta 300 m³/s.")
            else:
                H_calc = calcular_H_desde_Q(Q_target)
                print("\n--- Resultados Curva H-Q ---")
                print(f"Caudal objetivo (Q)               : {Q_target:.2f} m³/s")
                print(f"Tirante aguas abajo (H) calculado : {H_calc:.4f} m")
                
        elif opcion == '3':
            D_input = float(input("\nIngrese el diámetro del orificio (D) en metros: "))
            N_input = int(input("Ingrese la cantidad de orificios (N): "))
            H_str = input(f"Ingrese el tirante aguas abajo (H) [Enter para usar {H}]: ")
            H_input = float(H_str) if H_str.strip() else H
            
            if D_input <= 0 or N_input <= 0:
                print("Error: El diámetro y la cantidad de orificios deben ser valores positivos.")
            else:
                # Encontrar el equilibrio exacto entre el orificio y la curva H-Q
                def equilibrio(h_guess):
                    h_g = float(h_guess[0])
                    Q_ori = calcular_caudal_orificios(D_input, N_input, h_g)[0]
                    return Q_ori - calc_Q_reducida(h_g)
                H_input = fsolve(equilibrio, H_input)[0]
                Q, mu, Z0, f_friccion, xi, eta = calcular_caudal_orificios(D_input, N_input, H_input)
                
                if Q > 300:
                    print(f"Error: El caudal calculado ({Q:.2f} m³/s) supera el límite de 300 m³/s.")
                else:
                    print("\n--- Resultados del Cálculo ---")
                    mostrar_tabla_resultados(D_input, xi, N_input, f_friccion, mu, Q, L, eta, Z0, H_input)
                    exportar_a_csv(D_input, xi, N_input, f_friccion, mu, Q, L, eta, Z0, H_input, archivo="resultados_calculo.csv")
                
        elif opcion == '2':
            Q_target = float(input("\nIngrese el caudal objetivo en m³/s (ej. 70): "))
            if Q_target > 300:
                print("Error: La curva H-Q solo está desarrollada para caudales hasta 300 m³/s.")
            else:
                N_input = int(input("Ingrese la cantidad de orificios (N): "))
                
                H_input = calcular_H_desde_Q(Q_target)
                print(f"   -> Tirante (H) calculado automáticamente: {H_input:.4f} m")

                if Q_target <= 0 or N_input <= 0:
                    print("Error: El caudal objetivo y la cantidad de orificios deben ser valores positivos.")
                else:
                    # Encontrar el D exacto
                    D_exacto = fsolve(fsolve_D_residual, 1.0, args=(Q_target, N_input, H_input))[0]
                    
                    # Redondear al múltiplo de 5cm (0.05m) superior
                    D_redondeado = math.ceil(round(D_exacto / 0.05, 4)) * 0.05
                    
                    # Recalcular parámetros con el D redondeado constructivo
                    Q_final, mu_final, Z0_final, f_friccion_final, xi_final, eta_final = calcular_caudal_orificios(D_redondeado, N_input, H_input)
                    
                    print("\n--- Resultados de la Optimización ---")
                    mostrar_tabla_resultados(D_redondeado, xi_final, N_input, f_friccion_final, mu_final, Q_final, L, eta_final, Z0_final, H_input, Q_target, D_exacto)
                    exportar_a_csv(D_redondeado, xi_final, N_input, f_friccion_final, mu_final, Q_final, L, eta_final, Z0_final, H_input, Q_target, D_exacto, archivo="resultados_optimizacion.csv")
            
        else:
            print("Opción no válida. Por favor ejecute de nuevo y seleccione 1, 2 o 3.")
            
    except ValueError:
        print("Error: Entrada no válida. Por favor use números válidos.")
