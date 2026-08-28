import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
import parametrizacion as param

def main():
    a = param.a
    b = param.b
    c = param.c
    c0_vol = param.c0_opt
    
    a1 = param.a1_opt
    b1 = param.b1_opt
    c0_1 = param.c0_1_opt
    
    p2 = param.p2_opt
    p1 = param.p1_opt
    p0 = param.p0_opt
    
    d3 = param.d_opt
    c0_3 = param.c0_3_opt
    
    q_orf_max = param.q_orf_max
    e = param.e_opt
    
    # 2. Cargar hidrograma de entrada R=100
    df_in = pd.read_csv('datos/Q_e100.csv')
    t_in = df_in['T(seg)'].values
    Q_in = df_in['Qe(m3/s)'].values
    I_func = interp1d(t_in, Q_in, bounds_error=False, fill_value=(0.0, Q_in[-1]))
    
    Z_inicial = max(0.0, c0_vol - 21.00)
    dt = 60.0
    tiempos = np.arange(t_in[0], t_in[-1] + dt, dt)
    
    Z_sim = np.zeros(len(tiempos))
    Z_sim[0] = Z_inicial
    
    def dV_dZ(Z):
        Cota = Z + 21.00
        if Cota < 24.00:
            return 0.01 / (24.00 - c0_vol)
        return 2 * a * Z + b

    def Q_total(Z):
        Cota = Z + 21.00
        if Cota <= c0_1:
            return 0.0
        elif Cota <= 22.7256: # Tramo 1 (Canal)
            return a1 * max(0, Cota - c0_1)**b1
        elif Cota <= 24.00: # Tramo 2 (Transición)
            H = Cota - 21.0
            return p2 * H**2 + p1 * H + p0
        elif Cota <= 29.30: # Tramo 3 (Orificio)
            return d3 * np.sqrt(max(0, Cota - c0_3))
        else: # Tramo 4 (Orificios max + Vertedero)
            return q_orf_max + e * max(0, Z - 8.30)**1.5
        
    volumen_laminado_m3 = 0.0
    
    for j in range(len(tiempos) - 1):
        Z_actual = Z_sim[j]
        I_actual = I_func(tiempos[j])
        Q_actual = Q_total(Z_actual)
        
        # Volumen acumulado almacenado en este dt: (I - Q) * dt
        volumen_laminado_m3 += (I_actual - Q_actual) * dt
        
        dv_hm3 = dV_dZ(Z_actual)
        if dv_hm3 < 1e-3:
            dv_hm3 = 1e-3
        dv_m3 = dv_hm3 * 1e6
        
        delta_Z = ((I_actual - Q_actual) / dv_m3) * dt
        Z_sim[j+1] = Z_actual + delta_Z
        
    cota_sim = Z_sim + 21.00
    cota_max = np.max(cota_sim)
    
    # Volumen almacenado acumulado en total hasta el pico:
    # Wait, the total volume accumulated until the peak is what we should compare.
    # The integration above goes until the END of the hydrograph, where volume might be depleted again.
    # Let's find the peak index:
    # Encontrar el indice exacto donde la cota cruza 29.30m
    indices_2930 = np.where(cota_sim >= 29.30)[0]
    if len(indices_2930) > 0:
        idx_2930 = indices_2930[0]
    else:
        # If it never reached 29.30, use the max cota reached
        idx_2930 = np.argmax(cota_sim)
    
    # Recalcular volumen almacenado solo hasta idx_2930
    volumen_almacenado_2930_m3 = 0.0
    for j in range(idx_2930):
        Z_actual = Z_sim[j]
        I_actual = I_func(tiempos[j])
        Q_actual = Q_total(Z_actual)
        volumen_almacenado_2930_m3 += (I_actual - Q_actual) * dt
        
    vol_almacenado_2930_hm3 = volumen_almacenado_2930_m3 / 1e6
    
    # Volumen de la curva a 29.30m (Z = 8.30m)
    Z_2930 = 29.30 - 21.00
    V_curva_2930 = a * (Z_2930**2) + b * Z_2930 + c
    
    # Imprimir reporte
    print(f"--- Verificacion de Volumen a Cota 29.30m ---")
    print(f"Cota en idx_2930: {cota_sim[idx_2930]:.3f} m")
    print(f"Volumen curva @ 29.30m: {V_curva_2930:.3f} hm3")
    print(f"Volumen almacenado (integral I-Q hasta cota 29.3m): {vol_almacenado_2930_hm3:.3f} hm3")
    
    diff = abs(V_curva_2930 - vol_almacenado_2930_hm3)
    pct = (diff / V_curva_2930) * 100 if V_curva_2930 > 0 else 0
    print(f"Diferencia: {diff:.4f} hm3 ({pct:.2f}%)")

if __name__ == '__main__':
    main()
