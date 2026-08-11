import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

# Importamos los parámetros dinámicamente desde el script provisto
import parametrizacion as param

def main():
    # 1. Parámetros de la parametrización
    a = param.a
    b = param.b
    c = param.c
    d = param.d_opt
    C0 = param.c0_opt
    
    # Parámetro del vertedero, obtenido de la parametrización global
    e = param.e_opt
    
    # 2. Cargar hidrograma de entrada
    df_in = pd.read_csv('datos/Q_e100.csv')
    t_in = df_in['T(seg)'].values
    Q_in = df_in['Qe(m3/s)'].values
    
    # Función de interpolación para el caudal de entrada
    I_func = interp1d(t_in, Q_in, bounds_error=False, fill_value=(0.0, Q_in[-1]))
    
    # 3. Condiciones iniciales y configuración del modelo numérico
    # Asumimos que el nivel del agua arranca en la cota de cresta del vertedero (embalse lleno)
    Z_inicial = 29.30 - 21.00
    t_inicial = t_in[0]
    t_final = t_in[-1]
    
    dt = 30.0 # Paso de tiempo de integración en segundos
    tiempos = np.arange(t_inicial, t_final + dt, dt)
    
    Z_sim = np.zeros(len(tiempos))
    Q_out_sim = np.zeros(len(tiempos))
    V_sim = np.zeros(len(tiempos))
    
    Z_sim[0] = Z_inicial
    
    # 4. Funciones Hidráulicas (según datos/ecuaciones.md)
    def dV_dZ(Z):
        # Derivada del volumen respecto a Z [hm3/m]
        Cota = Z + 21.00
        if Cota < 24.00:
            return 0.01 / (24.00 - C0)
        return 2 * a * Z + b

    def get_volumen(Z):
        Cota = Z + 21.00
        if Cota < C0:
            return 0.0
        elif Cota < 24.00:
            return (0.01 / (24.00 - C0)) * (Cota - C0)
        else:
            return a * Z**2 + b * Z + c

    def Q_fondo(Z):
        Cota = Z + 21.00
        if Cota > 29.30:
            return d * np.sqrt(29.30 - C0)
        elif Cota > C0:
            return d * np.sqrt(Cota - C0)
        return 0.0
        
    def Q_vert(Z):
        # Descarga libre del vertedero, cota de cresta 29.30m (Z = 8.30m)
        if Z > 8.30:
            return e * (np.maximum(0, Z - 8.30))**1.5
        return 0.0

    def Q_total(Z):
        return Q_fondo(Z) + Q_vert(Z)
        
    # 5. Bucle de Integración Numérica (Esquema Explícito)
    print("\nIniciando cálculo de laminación...")
    for j in range(len(tiempos) - 1):
        Z_actual = Z_sim[j]
        I_actual = I_func(tiempos[j])
        Q_actual = Q_total(Z_actual)
        
        Q_out_sim[j] = Q_actual
        V_sim[j] = get_volumen(Z_actual)
        
        derivada_volumen_hm3 = dV_dZ(Z_actual)
        
        # Limitar derivada para evitar inestabilidades en cotas muy bajas
        if derivada_volumen_hm3 < 1e-3:
            derivada_volumen_hm3 = 1e-3
            
        # Convertir a m3/m multiplicando por 10^6
        derivada_volumen_m3 = derivada_volumen_hm3 * 1e6
        
        # Ecuación diferencial: dZ = ((I - Q) / V') * dt
        delta_Z = ((I_actual - Q_actual) / derivada_volumen_m3) * dt
        Z_sim[j+1] = Z_actual + delta_Z
        
    # Completar el último paso
    Q_out_sim[-1] = Q_total(Z_sim[-1])
    V_sim[-1] = get_volumen(Z_sim[-1])
    
    # 6. Graficar Resultados
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    
    ax1.plot(tiempos / 3600, I_func(tiempos), 'b-', label='Caudal Ingreso (I)')
    ax1.plot(tiempos / 3600, Q_out_sim, 'r-', label='Caudal Salida (Q total)')
    
    # Marcar Q máximo (intersección)
    q_max = np.max(Q_out_sim)
    idx_qmax = np.argmax(Q_out_sim)
    t_qmax_horas = tiempos[idx_qmax] / 3600
    ax1.plot(t_qmax_horas, q_max, 'ko') # Punto negro
    ax1.annotate(f'Q máx: {q_max:.2f} m3/s',
                 xy=(t_qmax_horas, q_max),
                 xytext=(10, -10), textcoords='offset points',
                 color='black', fontweight='bold')

    ax1.set_ylabel('Caudal [m3/s]')
    ax1.set_title('Laminación del Embalse - Hidrogramas (Embalse Lleno)')
    ax1.legend()
    ax1.grid(True)
    
    cota_sim = Z_sim + 21.00
    ax2.plot(tiempos / 3600, cota_sim, 'g-', label='Cota del Embalse (IGN)')
    ax2.axhline(C0, color='k', linestyle='--', label=f'Cota Fondo ({C0:.2f} m)')
    ax2.axhline(29.30, color='orange', linestyle='--', label='Cota Vertedero (29.30 m)')
    
    # Marcar Cota Máxima
    cota_max = np.max(cota_sim)
    idx_max = np.argmax(cota_sim)
    t_max_horas = tiempos[idx_max] / 3600
    ax2.plot(t_max_horas, cota_max, 'ro') # Punto rojo en el máximo
    ax2.annotate(f'Cota Máx: {cota_max:.2f} m',
                 xy=(t_max_horas, cota_max),
                 xytext=(10, 5), textcoords='offset points',
                 color='red', fontweight='bold')
                 
    ax2.set_xlabel('Tiempo [horas]')
    ax2.set_ylabel('Cota IGN [m]')
    ax2.legend()
    ax2.grid(True)
    
    plt.tight_layout()
    plt.savefig('./resultados_laminacion100_lleno.png')
    print("Simulación completada con éxito.")
    print("Gráfico de laminación guardado en './resultados_laminacion100_lleno.png'.")
    
    # 7. Exportar métricas de continuidad a CSV
    import os
    vol_entrada_hm3 = np.trapezoid(I_func(tiempos), tiempos) / 1e6
    vol_salida_hm3 = np.trapezoid(Q_out_sim, tiempos) / 1e6
    delta_almacenamiento_hm3 = V_sim[-1] - V_sim[0]
    
    error_continuidad_pct = np.abs(vol_entrada_hm3 - (vol_salida_hm3 + delta_almacenamiento_hm3)) / vol_entrada_hm3 * 100.0 if vol_entrada_hm3 > 0 else 0.0
    
    q_max_entrada = np.max(I_func(tiempos))
    q_max_salida = np.max(Q_out_sim)
    vol_maximo = np.max(V_sim)
    
    archivo_csv = 'resultados_continuidad.csv'
    nueva_fila = pd.DataFrame([{
        'Escenario': 'R=100 Lleno',
        'Q max Entrada (m3/s)': round(q_max_entrada, 2),
        'Q max Salida (m3/s)': round(q_max_salida, 2),
        'Vol Entrada (hm3)': round(vol_entrada_hm3, 4),
        'Vol Salida (hm3)': round(vol_salida_hm3, 4),
        'Error Continuidad (%)': round(error_continuidad_pct, 4),
        'Maximo Volumen (hm3)': round(vol_maximo, 4),
        'Maxima Cota (m IGN)': round(cota_max, 2)
    }])
    
    file_exists = os.path.isfile(archivo_csv)
    nueva_fila.to_csv(archivo_csv, mode='a', index=False, header=not file_exists)
    print(f"Métricas de continuidad guardadas en '{archivo_csv}'.\n")

if __name__ == '__main__':
    main()
