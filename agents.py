from typing import List, Dict, Tuple
from market import *  # Asegúrate de que este módulo exista y esté correctamente implementado
import random
import numpy as np
from rules_interpreter import *  # Asegúrate de que este módulo exista y esté correctamente implementado
import talib
from collections import deque, defaultdict

class Agente:
    def __init__(self, nombre: str, reglas: List[str], parser_reglas: ParserReglas, capital_inicial: float = 100000.0):
        self.nombre = nombre
        self.capital_inicial = float(capital_inicial)
        self.capital = float(capital_inicial)
        self.reglas = reglas
        self.parser_reglas = parser_reglas
        self.historia_ganancia = []
        self.portafolio: Dict[str, float] = {}  # Portafolio para almacenar las criptomonedas compradas
        self.ciclo = 1

        # **Componentes BDI**
        self.beliefs: Dict[str, Dict] = {}    # Creencias: Información del agente sobre su ambiente y predicciones
        self.desires: set = set()             # Deseos: Objetivos que el agente quiere lograr
        self.intentions: deque = deque()      # Intenciones: Acciones que el agente se compromete a realizar (FIFO)

        # Lista para registrar todas las intenciones a lo largo de la simulación
        self.historial_intenciones: List[Tuple[int, List[Tuple[str, str]]]] = []
        self.historia_ganancia.append(0)

    def brf(self, market_context: Market, sentiment_history: Dict[str, List[float]]):
        """
        Función de Revisión de Creencias (Belief Revision Function - brf):
        Actualiza las creencias del agente con el nuevo contexto del mercado y el historial de sentimientos.
        Incluye análisis técnicos para predicciones más realistas.
        """
        self.beliefs = {}

        #llamar metodo para generar belief ****************************************
        """ Obtain belief(motor,market_context,agente)

        retorna lista de creeencias y lista de reglas

        """

        # for name, crypto in market_context.cryptocurrencies.items():
        #     # Obtener historial de precios para análisis técnico
        #     price_history = crypto.price_history[-30:]  # Últimos 30 precios para mayor precisión

        #     # Asegurarse de tener suficientes datos para los indicadores técnicos
        #     if len(price_history) >= 14:
        #         prices = np.array(price_history)

        #         # Cálculo de indicadores técnicos
        #         # 1. Media Móvil Simple (SMA)
        #         sma_5 = talib.SMA(prices, timeperiod=5)[-1]
        #         sma_10 = talib.SMA(prices, timeperiod=10)[-1]

        #         # 2. Índice de Fuerza Relativa (RSI)
        #         rsi = talib.RSI(prices, timeperiod=14)[-1]

        #         # 3. MACD
        #         macd, macdsignal, macdhist = talib.MACD(prices, fastperiod=12, slowperiod=26, signalperiod=9)
        #         macd_current = macd[-1]
        #         macd_signal_current = macdsignal[-1]

        #         # 4. Bandas de Bollinger
        #         upperband, middleband, lowerband = talib.BBANDS(prices, timeperiod=20)

        #         # Interpretación básica de los indicadores
        #         tendencia = 'desconocida'

        #         # Análisis de cruces de medias móviles
        #         if sma_5 > sma_10:
        #             tendencia = 'alcista'
        #         elif sma_5 < sma_10:
        #             tendencia = 'bajista'

        #         # Análisis del RSI
        #         sobrecompra = rsi > 70
        #         sobreventa = rsi < 30

        #         # Análisis del MACD
        #         if macd_current > macd_signal_current:
        #             macd_tendencia = 'alcista'
        #         else:
        #             macd_tendencia = 'bajista'

        #         # Análisis de Bandas de Bollinger
        #         precio_actual = prices[-1]
        #         if precio_actual > upperband[-1]:
        #             bollinger = 'sobrecompra'
        #         elif precio_actual < lowerband[-1]:
        #             bollinger = 'sobreventa'
        #         else:
        #             bollinger = 'normal'
        #     else:
        #         sma_5 = sma_10 = rsi = macd_current = macd_signal_current = None
        #         tendencia = 'desconocida'
        #         sobrecompra = sobreventa = False
        #         macd_tendencia = 'desconocida'
        #         bollinger = 'normal'

        #     # Actualizar creencias con datos actuales y análisis técnico
        #     self.beliefs[name] = {
        #         'precio': float(crypto.price),
        #         'volumen': float(crypto.volume),
        #         'sentimiento': self.get_sentiment(name, sentiment_history),
        #         'historial_precios': price_history,
        #         'tendencia_precio': tendencia,
        #         'sma_5': sma_5,
        #         'sma_10': sma_10,
        #         'rsi': rsi,
        #         'macd_tendencia': macd_tendencia,
        #         'sobrecompra': sobrecompra,
        #         'sobreventa': sobreventa,
        #         'bollinger': bollinger
        #     }
        # # print(f"Creencias actualizadas: {self.beliefs}")


    # ES lo clásico por cada criptomoneda evaluar todas las reglas y meter en deseos 
    # por cada cripto la acción que salió con el mayor valo
    def options(self):
        """
        Función de Generación de Opciones:
        Genera posibles deseos basados en las creencias actuales y las reglas definidas.
        Ordena los deseos derivados de reglas por su resultado y añade los deseos basados en contexto al final.
        Mantiene 'self.desires' como un conjunto para evitar duplicados.
        """
        self.desires.clear()

        deseos = []
        deseos_contexto = []
        for cripto, datos in self.beliefs.items():
            belief_action = 0

            #metodo para evaluar reglas

            """Este es el que deberías crear en el caso de que no me de tiempo

                como entrada el agente,el mercado,
                 
                salida score,acción
            
            """
            #evaluar reglas
            if (datos['tendencia_precio'] == 'alcista' and not datos['sobrecompra']) or datos['sobreventa'] or datos['macd_tendencia'] == 'alcista':
                belief_action = 1
            elif datos['sobrecompra'] or datos['macd_tendencia'] == 'bajista' or datos['bollinger'] == 'sobrecompra':
                belief_action = -1
            else:
                belief_action = 0

            deseos_con_resultado = []
            matched = 0
            # Evaluar las reglas y almacenar los deseos con su resultado
            for regla in self.reglas:
                parsed_conditions, accion = self.parser_reglas.parse_rule(regla)
                if accion != belief_action:
                    continue
                resultado, _ = self.parser_reglas.aplicar_regla(parsed_conditions, accion, cripto, datos)
                # Si el resultado es positivo, agregar a la lista temporal
                if resultado > 0:
                    if accion == 1:
                        deseos_con_resultado.append((resultado, 'comprar', cripto))
                        matched = 1
                    elif accion == -1:
                        deseos_con_resultado.append((resultado, 'vender', cripto))
                        matched = 1
                    elif accion == 0:
                        deseos_con_resultado.append((resultado, 'mantener', cripto))
                        matched = 1

            # Ordenar los deseos derivados de reglas por resultado descendente
            deseos_con_resultado_sorted = sorted(deseos_con_resultado, key=lambda x: x[0], reverse=True)

            if matched:
                for resultado, accion, cripto in deseos_con_resultado_sorted:
                    deseos.append((resultado, accion, cripto))
                    break
                continue

            if belief_action == 1:
                deseos_contexto.append(('comprar', cripto))
            elif belief_action == -1:
                deseos_contexto.append(('vender', cripto))
            elif belief_action == 0:
                deseos_contexto.append(('mantener', cripto))

        deseos_sorted = sorted(deseos, key=lambda x: x[0], reverse=True)
        for _, accion, cripto in deseos_sorted:
            self.desires.add((accion, cripto))
            break
        for accion, cripto in deseos_contexto:
            self.desires.add((accion, cripto))
            break

        # Opcional: Registrar los deseos generados para depuración
        # print(f"Deseos generados: {self.desires}")


    #Me parece que este se podría hacer ejecutar las acciones con un valor mayor a una cota
    def filter_desires(self):
        """
        Filtra las intenciones actuales para mantener solo aquellas que están presentes en los deseos.
        Elimina las intenciones que ya no están en los deseos y añade nuevas intenciones basadas en los deseos restantes.
        Evita tener acciones conflictivas para la misma criptomoneda: solo una de 'comprar', 'vender', 'mantener'.
        """

        # Diccionario para mantener la acción con mayor prioridad por criptomoneda
        acciones_por_cripto = {}

        # Paso 1: Procesar las intenciones existentes y seleccionar la acción con mayor prioridad por cripto
        while self.intentions:
            accion, cripto = self.intentions.popleft()
            if cripto not in acciones_por_cripto:
                acciones_por_cripto[cripto] = accion
            else:
                if prioridad.get(accion, 0) > prioridad.get(acciones_por_cripto[cripto], 0):
                    acciones_por_cripto[cripto] = accion

        # Paso 2: Crear una nueva cola de intenciones basada en las acciones seleccionadas
        nuevas_intenciones = deque()
        criptos_procesadas = set()

        for cripto, accion in acciones_por_cripto.items():
            if (accion, cripto) in self.desires:
                # Verificar condiciones antes de añadir la intención
                if accion == 'comprar' and self.capital > 0:
                    nuevas_intenciones.append((accion, cripto))
                    self.desires.remove((accion, cripto))
                elif accion == 'vender' and self.portafolio.get(cripto, 0.0) > 0.0:
                    nuevas_intenciones.append((accion, cripto))
                    self.desires.remove((accion, cripto))
                elif accion == 'mantener':
                    nuevas_intenciones.append((accion, cripto))
                    self.desires.remove((accion, cripto))
                criptos_procesadas.add(cripto)
            else:
                # Eliminar intenciones que ya no están en los deseos
                print(f"Intención eliminada: {accion} {cripto}")

        # Paso 3: Añadir nuevas intenciones desde los deseos restantes, asegurando que no haya conflictos
        for accion, cripto in list(self.desires):
            if cripto not in criptos_procesadas:
                if accion == 'comprar' and self.capital > 0:
                    nuevas_intenciones.append((accion, cripto))
                    self.desires.remove((accion, cripto))
                elif accion == 'vender' and self.portafolio.get(cripto, 0.0) > 0.0:
                    nuevas_intenciones.append((accion, cripto))
                    self.desires.remove((accion, cripto))
                elif accion == 'mantener':
                    nuevas_intenciones.append((accion, cripto))
                    self.desires.remove((accion, cripto))
                criptos_procesadas.add(cripto)
            else:
                # Si ya existe una intención para esta cripto, reemplazarla si la nueva acción tiene mayor prioridad
                existing_accion = acciones_por_cripto.get(cripto)
                # Reemplazar la intención existente
                nuevas_intenciones = deque(
                    [(a, c) if c != cripto else (accion, cripto) for a, c in nuevas_intenciones]
                )
                self.desires.remove((accion, cripto))
                acciones_por_cripto[cripto] = accion

        # Paso 4: Limpiar los deseos ya procesados
        self.desires.clear()

        # Paso 5: Actualizar la cola de intenciones
        self.intentions.extend(nuevas_intenciones)

        # Paso 6: Registrar las intenciones actuales en el historial
        if self.intentions:
            self.historial_intenciones.append((self.ciclo, list(self.intentions)))
            print(f"Intenciones registradas en el historial para el ciclo {self.ciclo}: {list(self.intentions)}")
        else:
            print(f"No hay intenciones actuales para el ciclo {self.ciclo}.")

    # aquí tienes que calcular el precio de las compras y las ventas
    def execute_intention(self, market_context: Market, sentiment_history: Dict[str, List[float]]):
        """
        Ejecuta todas las intenciones en la cola FIFO.
        Verifica si cada intención sigue siendo válida antes de ejecutarla.
        """
        count = 0
        while self.intentions:
            count+=1
            accion, cripto = self.intentions.popleft()
            # Ejecutar la acción
            self.ejecutar_accion(accion, market_context, cripto)
            # Actualizar el mercado después de ejecutar la acción
            market_context.update(sentiment_history)
            # Actualizar ganancia
            self.actualizar_ganancia(market_context)
            # Revisar creencias después de actualizar el mercado
            self.brf(market_context, sentiment_history)
            # Actualizar deseos
            self.options()
            # Volver a filtrar las intenciones después de la actualización
            self.filter_desires()

            if count == 10: break


    def action(self, market_context: Market, sentiment_history: Dict[str, List[float]]):
        """
        Función principal de acción del agente BDI.
        Sigue el ciclo BDI: brf -> options -> filter_desires -> execute_intention
        """
        print(f"\nCiclo {self.ciclo} del agente {self.nombre}:")
        self.brf(market_context, sentiment_history)
        self.options()
        self.filter_desires()
        self.execute_intention(market_context, sentiment_history)
        self.ciclo += 1

    def get_sentiment(self, crypto_name: str, sentiment_history: Dict[str, List[float]]) -> float:
        """
        Obtiene el sentimiento actual para una criptomoneda específica.
        """
        if sentiment_history and crypto_name in sentiment_history:
            return sentiment_history[crypto_name][-1]
        return 0.0  # Ajustar según el formato de tus datos

    #cambiar método
    def ejecutar_accion(self, accion: str, contexto: Market, cripto: str):
        """
        Ejecuta la acción determinada ('comprar', 'vender' o 'mantener') para una criptomoneda específica.
        """
        precio = float(contexto.cryptocurrencies[cripto].price)
        if accion == "comprar":
            cantidad_a_comprar = self.calcular_cantidad_a_comprar(precio, cripto)
            # Validar que la cantidad a comprar sea mayor que un umbral mínimo
            if cantidad_a_comprar > 0 and self.capital >= cantidad_a_comprar * precio:
                # Realizar la compra
                self.capital -= cantidad_a_comprar * precio
                self.portafolio[cripto] = self.portafolio.get(cripto, 0.0) + cantidad_a_comprar
                print(f"{self.nombre} compró {cantidad_a_comprar:.8f} unidades de {cripto} a {precio:.2f} USD cada una, gastando un total de {(cantidad_a_comprar * precio):.2f} USD.")
                contexto.cryptocurrencies[cripto].add_order("buy", precio, cantidad_a_comprar)
            else:
                print(f"{self.nombre} no tiene suficiente capital para comprar {cantidad_a_comprar:.8f} unidades de {cripto}.")

        elif accion == "vender":
            cantidad_a_vender = self.calcular_cantidad_a_vender(cripto)
            # Validar que la cantidad a vender sea mayor que un umbral mínimo
            if cantidad_a_vender > 0 and self.portafolio.get(cripto, 0.0) >= cantidad_a_vender:
                # Realizar la venta
                self.capital += cantidad_a_vender * precio
                self.portafolio[cripto] -= cantidad_a_vender
                print(f"{self.nombre} vendió {cantidad_a_vender:.8f} unidades de {cripto} a {precio:.2f} USD cada una, ganando un total de {(cantidad_a_vender * precio):.2f} USD.")
                contexto.cryptocurrencies[cripto].add_order("sell", precio, cantidad_a_vender)
            else:
                print(f"{self.nombre} no tiene suficientes unidades de {cripto} para vender {cantidad_a_vender:.8f} unidades.")

        elif accion == "mantener":
            print(f"{self.nombre} mantiene su posición en {cripto}.")

        else:
            print(f"Acción '{accion}' desconocida para {cripto}.")

    # def calcular_cantidad_a_comprar(self, precio: float, cripto: str) -> float:
    #     """
    #     Calcula la cantidad de criptomoneda a comprar basada en métricas como RSI.
    #     Estrategia:
    #     - RSI < 30: Invertir el 15% del capital disponible
    #     - RSI > 70: Invertir el 5% del capital disponible
    #     - RSI entre 30 y 70: Invertir el 10% del capital disponible
    #     - RSI es None: Invertir el 10% del capital disponible
    #     """
    #     datos = self.beliefs[cripto]
    #     rsi = datos.get('rsi', None)

    #     if rsi is not None:
    #         if rsi < 30:
    #             porcentaje_inversion = 0.15  # 15%
    #         elif rsi > 70:
    #             porcentaje_inversion = 0.05  # 5%
    #         else:
    #             porcentaje_inversion = 0.10  # 10%
    #     else:
    #         porcentaje_inversion = 0.10  # 10% por defecto

    #     monto_a_invertir = self.capital * porcentaje_inversion
    #     cantidad = monto_a_invertir / precio
    #     cantidad = round(cantidad, 8)  # Redondear a 8 decimales para criptomonedas

    #     # Validar que la cantidad no sea demasiado pequeña
    #     if cantidad < 0.0001:
    #         cantidad = 0.0

    #     return cantidad

    # def calcular_cantidad_a_vender(self, cripto: str) -> float:
    #     """
    #     Calcula la cantidad de criptomoneda a vender basada en métricas como RSI.
    #     Estrategia:
    #     - RSI > 70: Vender el 50% de las holdings
    #     - RSI < 30: No vender
    #     - RSI entre 30 y 70: Vender el 25% de las holdings
    #     - RSI es None: Vender el 25% de las holdings
    #     """
    #     datos = self.beliefs[cripto]
    #     rsi = datos.get('rsi', None)
    #     cantidad_actual = self.portafolio.get(cripto, 0.0)

    #     if rsi is not None:
    #         if rsi > 70:
    #             porcentaje_vender = 0.50  # Vender el 50%
    #         elif rsi < 30:
    #             porcentaje_vender = 0.0   # No vender
    #         else:
    #             porcentaje_vender = 0.25  # Vender el 25%
    #     else:
    #         porcentaje_vender = 0.25  # Vender el 25% por defecto

    #     cantidad = cantidad_actual * porcentaje_vender
    #     cantidad = round(cantidad, 8)  # Redondear a 8 decimales para criptomonedas

    #     # Validar que la cantidad no sea demasiado pequeña
    #     if cantidad < 0.0001:
    #         cantidad = 0.0

    #     return cantidad

    def actualizar_ganancia(self, contexto: Market):
        """
        Actualiza el historial de ganancias del agente.
        """
        valor_portafolio = sum(
            contexto.cryptocurrencies[crypto].price * cantidad
            for crypto, cantidad in self.portafolio.items()
        )
        ganancia_actual = self.capital + valor_portafolio - self.capital_inicial
        self.historia_ganancia.append(ganancia_actual)
        print(f"Ganancia actual de {self.nombre}: {ganancia_actual:.2f} USD")

    def evaluar_desempeno(self, contexto: Market) -> float:
        """
        Evalúa el desempeño del agente basado en las ganancias obtenidas.
        """
        ganancia = 0.0
        for crypto, value in self.portafolio.items():
            ganancia += contexto.cryptocurrencies[crypto].price * value
        ganancia += self.capital
        desempeño = ((ganancia - self.capital_inicial) / self.capital_inicial) * 100  # Rendimiento porcentual
        return desempeño
