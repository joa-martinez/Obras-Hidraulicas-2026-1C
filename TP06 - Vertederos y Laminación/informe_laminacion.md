# Informe de Laminación de Embalse

## 1. Introducción
El presente informe documenta los procedimientos, constantes y ecuaciones gobernantes utilizados para simular la laminación de crecidas en un embalse para dos escenarios de recurrencia ($Tr = 100$ años y $Tr = 10000$ años). La simulación permite verificar si la estructura de evacuación (descargador de fondo + vertedero) es suficiente para erogar las crecidas sin producir el desborde por encima del coronamiento de la presa.

## 2. Parámetros y Constantes
La geometría del embalse y las obras de descarga se encuentran parametrizadas en función de la cota (sistema IGN).

### 2.1. Curva Cota-Volumen
El volumen del embalse se aproxima mediante una ecuación cuadrática de la cota:
$$ V(\text{Cota}) = a \cdot \text{Cota}^2 + b \cdot \text{Cota} + c $$
Donde los parámetros ajustados son:
- $a = 2.534278 \text{ hm}^3/\text{m}^2$
- $b = -125.728456 \text{ hm}^3/\text{m}$
- $c = 1559.150824 \text{ hm}^3$

### 2.2. Descargador de Fondo
La ley de descarga de fondo se asimila a un orificio con carga:
$$ Q_{fondo}(\text{Cota}) = d \cdot \sqrt{\text{Cota} - C_0} $$
Donde:
- $d = 26.6880 \text{ m}^{2.5}/\text{s}$ (coeficiente de descarga unificado)
- $C_0 = 22.10 \text{ m}$ (Cota de origen o solera del orificio)

### 2.3. Vertedero
El escurrimiento por el vertedero de cresta libre inicia cuando el nivel del agua supera la cota de la cresta.
- Cota de cresta del vertedero $= 29.30 \text{ m}$
- Cota de coronamiento de la presa ($CCP$) $= 30.50 \text{ m}$
- Longitud del vertedero ($L$) $= 45 \text{ m}$
- Coeficiente de descarga ($C_d$) $= 4.03$

La ley de descarga libre es:
$$ Q_{vert} = 0.552 \cdot C_d \cdot L \cdot H^{1.5} $$
Donde $H$ es la carga sobre el vertedero ($H = \text{Cota} - 29.30$). 
Agrupando las constantes para la simulación computacional ($e = 0.552 \cdot 4.03 \cdot 45 \approx 100.105$):
$$ Q_{vert}(\text{Cota}) = 100.105 \cdot (\text{Cota} - 29.30)^{1.5} $$

## 3. Formulación Matemática
Definiendo la variable auxiliar Carga Hidráulica como $Z = \text{Cota} - 21.00$. Transformando las funciones a esta variable, el modelo hidrológico se rige por la ecuación diferencial de continuidad volumétrica:
$$ \frac{dV}{dt} = I(t) - Q_{total}(Z) $$
Donde:
- $I(t)$ es el caudal de ingreso (hidrograma de crecida, para el escenario evaluado).
- $Q_{total}(Z)$ es el caudal total erogado, que se rige por la regla de negocio:
$$ Q_{total}(Z) = \begin{cases} 
Q_{fondo}(Z) & \text{si } Z \leq 8.30 \text{ m} \\
Q_{fondo}(Z) + Q_{vert}(Z) & \text{si } Z > 8.30 \text{ m}
\end{cases} $$

Aplicando la regla de la cadena ($\frac{dV}{dt} = \frac{dV}{dZ} \cdot \frac{dZ}{dt}$), se despeja la variación temporal del nivel del lago:
$$ \frac{dZ}{dt} = \frac{I(t) - Q_{total}(Z)}{\frac{dV}{dZ}} $$
Siendo $\frac{dV}{dZ} = 2a(Z+21.00) + b$ equivalente al área superficial del embalse.

*(Nota Analítica sobre Oscilaciones)*: Debido a la extrapolación matemática de la parábola de volumen por debajo de la cota $24.80 \text{ m}$, la derivada analítica $\frac{dV}{dZ}$ resulta negativa. Para evitar que el esquema de integración detone por división negativa o por ceros, se restringe computacionalmente el área a un valor mínimo ($10^{-3} \text{ hm}^2$). Esto genera una oscilación temporal en la gráfica de cotas a niveles bajos del embalse que se amortigua y desaparece completamente en cuanto el lago supera la cota $24.80 \text{ m}$ y el área superficial vuelve a reflejar hectáreas reales.


## 4. Procedimiento de Cálculo Computacional
Para resolver la ecuación diferencial se emplea un esquema explícito de Euler paso a paso, codificado en rutinas de simulación independientes, ejecutando iterativamente la siguiente secuencia:

1. **Configuración Inicial:** Se asume $Z_0 = C_0 - 21.00$ (el embalse arranca en el umbral mínimo del descargador).
2. **Paso Temporal:** Se define un $\Delta t = 60 \text{ s}$.
3. **Bucle de Iteración $j \to j+1$:**
   - **Paso A:** Interpolar el hidrograma de ingreso externo en $t_j$ para obtener $I(t_j)$.
   - **Paso B:** Calcular el caudal de salida $Q_{total}(Z_j)$.
   - **Paso C:** Calcular el área del embalse $A(Z_j) = \frac{dV}{dZ} \times 10^6$ (factor de conversión de $\text{hm}^2$ a $\text{m}^2$). Se aplica la cláusula protectora de área mínima si es necesario.
   - **Paso D:** Calcular la diferencia de cota: 
     $$ \Delta Z = \frac{I(t_j) - Q_{total}(Z_j)}{A(Z_j)} \cdot \Delta t $$
   - **Paso E:** Actualizar la carga de agua para el intervalo $j+1$: 
     $$ Z_{j+1} = Z_j + \Delta Z $$
4. **Verificación Estructural:** Al finalizar la integración en el tiempo total del hidrograma, el software filtra el arreglo de $Z_{sim}$ para hallar la cota pico. Se compara este máximo con la cota de coronamiento de la presa ($30.50 \text{ m}$). Si no se la supera, se informa el valor numérico de la revancha (freeboard disponible); si se la supera, el programa emite una advertencia crítica sobre el colapso (desborde) por rebase de la estructura. Este control de validez se aplicó tanto a $Tr=100$ como a $Tr=10000$ años.
