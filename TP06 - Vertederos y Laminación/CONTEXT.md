# Contexto: Laminación de Embalse

## Glosario

### Cota IGN
Elevación sobre el nivel del mar según el sistema del Instituto Geográfico Nacional (IGN), expresada en metros (m).

### Carga Hidráulica (Z)
Altura relativa del nivel del agua respecto a un plano de referencia (datum). El datum (Z=0) está en la cota 21.00 m IGN.
$Z = \text{Cota IGN} - 21.00$

### Volumen (V)
Volumen acumulado de agua en el embalse, expresado en hectómetros cúbicos ($hm^3$).

### Caudal (Q)
Volumen de agua que fluye por unidad de tiempo, expresado en metros cúbicos por segundo ($m^3/s$).

### Descargadores de fondo
Conductos u orificios diseñados para evacuar agua desde las cotas bajas del embalse. En este modelo se parametrizan como orificios de pared gruesa con una descarga proporcional a $Z^{0.5}$.
$Q_{fondo} = d \cdot Z^{0.5}$

### Vertedero de Cresta Curva
Estructura de alivio superficial cuya descarga comienza en la cota 29.30 m IGN ($Z = 8.3$ m). Su descarga es proporcional a la carga sobre el vertedero ($H = Z - 8.3$) elevada a la 1.5.
$Q_{vert} = e \cdot (Z - 8.3)^{1.5}$ para $Z > 8.3$

## Reglas de Negocio

1. **Curva Cota-Volumen**: Se parametriza mediante una ecuación cuadrática $V = a Z^2 + b Z + c$, donde $Z = \text{Cota IGN} - 21.00$.
2. **Curva de Descarga Total (Q_total)**:
   - Para $Z < 8.3$ m: $Q_{total} = Q_{fondo} = d \cdot Z^{0.5}$
   - Para $Z > 8.3$ m: $Q_{total} = Q_{fondo} + Q_{vert} = d \cdot Z^{0.5} + e \cdot (Z - 8.3)^{1.5}$
