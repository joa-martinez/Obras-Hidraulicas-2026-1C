import math
import numpy as np
from scipy.optimize import fsolve
from typing import Tuple, List
from .models import (
    ResultadoHidraulico, 
    ResultadoOrificio, 
    ResultadoOptimizacion, 
    ResultadoCurvaDescarga, 
    TramoCurva, 
    PuntoCurva
)

# ==========================================
# Constantes y Parámetros Hidráulicos
# ==========================================
L_DEFAULT = 15.0
H_DEFAULT = 3.1125
G = 9.81
ETA_DEFAULT = 0.015
SUM_XI_DEFAULT = 0.05
COTA_CCV_DEFAULT = 8.30
S_DEFAULT = 0.005

class MotorHidraulico:
    def __init__(self, 
                 longitud: float = L_DEFAULT, 
                 rugosidad: float = ETA_DEFAULT, 
                 cota_aguas_arriba: float = COTA_CCV_DEFAULT):
        self.L = longitud
        self.eta = rugosidad
        self.cota_ccv = cota_aguas_arriba

    def calc_q_reducida(self, h_val: float) -> float:
        """Calcula el caudal total Q usando las expresiones de la curva H-Q aguas abajo."""
        if h_val <= 0:
            return 0.0
        elif h_val <= 1.0:
            numerador = ((7.50 + h_val) * h_val)**(5/3)
            denominador = (7.50 + 2 * math.sqrt(2) * h_val)**(2/3)
            factor = (4 * math.sqrt(2)) / 7
            return factor * (numerador / denominador)
        elif h_val <= 3.0:
            term_central = 0.1704 * (8.5 + 9.5 * (h_val - 1))**(5/3)
            term_lateral_num = (9.9 * (h_val - 1) + 0.5 * (h_val - 1)**2)**(5/3)
            term_lateral_den = (h_val + 8.9)**(2/3)
            return term_central + 1.6162 * (term_lateral_num / term_lateral_den)
        else:
            term_central = 0.1704 * (8.5 + 9.5 * (h_val - 1))**(5/3)
            term_lateral = 0.3100 * (11.9 * h_val - 13.9)**(5/3)
            term_valle = 89.09 * (h_val - 3)**(8/3)
            return term_central + term_lateral + term_valle

    def calcular_h_desde_q(self, q_target: float) -> float:
        """Invierte la curva H-Q para encontrar H dado un Q."""
        if q_target <= 0: return 0.0
        def residuo(h_guess):
            h_val = float(h_guess[0])
            if h_val <= 0: return -q_target + (h_val * 100)
            return self.calc_q_reducida(h_val) - q_target
        return fsolve(residuo, max(0.5, q_target / 100.0))[0]

    def calcular_caudal_orificios(self, d: float, n: int, h: float) -> ResultadoOrificio:
        """Calcula el caudal de salida para orificios de pared gruesa."""
        z0 = self.cota_ccv - h
        area = (math.pi * d**2) / 4
        f_l_d = ((124.52 * self.eta**2) / (d**(1/3))) * (self.L / d)
        mu = 1 / math.sqrt(1 + SUM_XI_DEFAULT + f_l_d)
        
        signo_z0 = 1 if z0 >= 0 else -1
        q_salida = signo_z0 * n * mu * area * math.sqrt(2 * G * abs(z0))
        
        return ResultadoOrificio(
            caudal=q_salida,
            tirante_h=h,
            longitud_conducto=self.L,
            carga_efectiva_z0=z0,
            cantidad_orificios=n,
            rugosidad_manning=self.eta,
            coeficiente_xi=SUM_XI_DEFAULT,
            factor_f_l_d=f_l_d,
            coeficiente_mu=mu,
            diametro=d
        )

    def optimizar_diametro(self, q_target: float, n: int) -> ResultadoOptimizacion:
        """Encuentra el diámetro óptimo y el constructivo (redondeado a 5cm)."""
        h_val = self.calcular_h_desde_q(q_target)
        
        def residual_d(d_guess):
            d_val = float(d_guess[0])
            if d_val <= 0: return 1e6
            res = self.calcular_caudal_orificios(d_val, n, h_val)
            return res.caudal - q_target
            
        d_exacto = fsolve(residual_d, 1.0)[0]
        d_redondeado = math.ceil(round(d_exacto / 0.05, 4)) * 0.05
        
        # Recalcular con el redondeado
        res_final = self.calcular_caudal_orificios(d_redondeado, n, h_val)
        
        return ResultadoOptimizacion(
            caudal=res_final.caudal,
            tirante_h=res_final.tirante_h,
            longitud_conducto=res_final.longitud_conducto,
            carga_efectiva_z0=res_final.carga_efectiva_z0,
            cantidad_orificios=res_final.cantidad_orificios,
            rugosidad_manning=res_final.rugosidad_manning,
            coeficiente_xi=res_final.coeficiente_xi,
            factor_f_l_d=res_final.factor_f_l_d,
            coeficiente_mu=res_final.coeficiente_mu,
            diametro=d_redondeado,
            caudal_objetivo=q_target,
            diametro_exacto=d_exacto
        )

    def calcular_equilibrio(self, d: float, n: int, h_inicial: float) -> ResultadoOrificio:
        """Encuentra el punto de equilibrio donde Q_orificio == Q_canal."""
        def equilibrio(h_guess):
            h_g = float(h_guess[0])
            res_ori = self.calcular_caudal_orificios(d, n, h_g)
            return res_ori.caudal - self.calc_q_reducida(h_g)
        
        h_final = fsolve(equilibrio, h_inicial)[0]
        return self.calcular_caudal_orificios(d, n, h_final)

    def generar_curva_descarga(self, d: float, n: int, elevacion_base: float = None) -> ResultadoCurvaDescarga:
        """Genera los tres tramos de la curva de descarga."""
        if elevacion_base is None:
            elevacion_base = d
            
        # TRAMO 1: Descarga Libre (Canal)
        h0_max_libre = elevacion_base + 0.938 * d
        h0_t1 = np.linspace(elevacion_base, h0_max_libre, 100)
        
        y_t1 = np.clip(h0_t1 - elevacion_base, 0, d * 0.938)
        theta = 2 * np.arccos(1 - (2 * y_t1) / d)
        a_t1 = (d**2 / 8) * (theta - np.sin(theta))
        
        term_sin_theta_div_theta = np.zeros_like(theta)
        mask = theta > 0
        term_sin_theta_div_theta[mask] = np.sin(theta[mask]) / theta[mask]
        r_t1 = (d / 4) * (1 - term_sin_theta_div_theta)
        
        q_t1 = n * (1 / self.eta) * a_t1 * (r_t1**(2/3)) * np.sqrt(S_DEFAULT)
        
        t1 = TramoCurva(
            nombre="Tramo 1: Descarga Libre",
            puntos=[PuntoCurva(q, h) for q, h in zip(q_t1, h0_t1)],
            datos_adicionales={
                "theta": theta.tolist(),
                "area": a_t1.tolist(),
                "radio_hidraulico": r_t1.tolist()
            }
        )

        # TRAMO 3: Orificio Ahogado
        h0_min_t3 = elevacion_base + 2 * d
        h0_max_t3 = self.cota_ccv
        
        def residuo_t3(y_guess, h0_target):
            y_g = float(y_guess[0])
            if y_g <= 0: return -h0_target + (y_g * 100)
            q_val = self.calc_q_reducida(y_g)
            res_ori = self.calcular_caudal_orificios(d, n, y_g)
            # Z0 = (Q / (N * mu * A))^2 / (2 * g)
            # H0 = Z0 + y
            # Pero ya tenemos calcular_caudal_orificios que nos da Z0
            z0 = (q_val / (n * res_ori.coeficiente_mu * (math.pi * d**2 / 4)))**2 / (2 * G)
            return (z0 + y_g) - h0_target

        y_min_t3 = fsolve(residuo_t3, 1.0, args=(h0_min_t3,))[0]
        y_max_t3 = fsolve(residuo_t3, 1.0, args=(h0_max_t3,))[0]
        
        y_t3 = np.linspace(y_min_t3, y_max_t3, 100)
        q_t3 = np.array([self.calc_q_reducida(y) for y in y_t3])
        
        # Recalcular Z0 y H0 para el tramo 3
        area_full = (math.pi * d**2) / 4
        # f_l_d y mu son constantes para un D dado en tramo 3
        f_l_d = ((124.52 * self.eta**2) / (d**(1/3))) * (self.L / d)
        mu = 1 / math.sqrt(1 + SUM_XI_DEFAULT + f_l_d)
        
        z0_t3 = (q_t3 / (n * mu * area_full))**2 / (2 * G)
        h0_t3 = z0_t3 + y_t3
        
        t3 = TramoCurva(
            nombre="Tramo 3: Orificio Ahogado",
            puntos=[PuntoCurva(q, h) for q, h in zip(q_t3, h0_t3)],
            datos_adicionales={
                "tirante_y": y_t3.tolist(),
                "z0": z0_t3.tolist()
            }
        )

        # TRAMO 2: Transición
        q_t2 = np.linspace(q_t1[-1], q_t3[0], 50)
        h0_t2 = np.linspace(h0_t1[-1], h0_t3[0], 50)
        
        t2 = TramoCurva(
            nombre="Tramo 2: Transición",
            puntos=[PuntoCurva(q, h) for q, h in zip(q_t2, h0_t2)]
        )
        
        q_total = np.concatenate((q_t1, q_t2, q_t3)).tolist()
        h_total = np.concatenate((h0_t1, h0_t2, h0_t3)).tolist()
        
        return ResultadoCurvaDescarga(t1=t1, t2=t2, t3=t3, q_total=q_total, h_total=h_total)
