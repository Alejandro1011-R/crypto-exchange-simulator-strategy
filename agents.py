from typing import List, Dict
from market import *
import random
import numpy as np
from rules_interpreter import *
import talib

class Agente:
    def __init__(self, nombre, reglas, parser_reglas, capital_inicial=100000.0):
        self.nombre = nombre
        self.capital_inicial = float(capital_inicial)
        self.capital = float(capital_inicial)
        self.reglas = reglas
        self.parser_reglas = parser_reglas
        self.historia_ganancia = []
        self.portafolio = {}  # Portafolio para almacenar las criptomonedas compradas
        self.ciclo = 1

        # **Componentes BDI**
        self.beliefs = {}          # Creencias: Información del agente sobre su ambiente y predicciones
        self.desires = set()       # Deseos: Objetivos que el agente quiere lograr
        self.intentions = set()    # Intenciones: Acciones que el agente se compromete a realizar

        # Lista para registrar todas las intenciones a lo largo de la simulación
        self.historial_intenciones = []

    def brf(self, market_context, sentiment_history):
        """
        Función de Revisión de Creencias (Belief Revision Function - brf):
        Actualiza las creencias del agente con el nuevo contexto del mercado y el historial de sentimientos.
        Incluye análisis técnicos para predicciones más realistas.
        """
        self.beliefs = {}
        for name, crypto in market_context.cryptocurrencies.items():
            # Obtener historial de precios para análisis técnico
            price_history = crypto.price_history[-30:]  # Últimos 30 precios para mayor precisión

            # Asegurarse de tener suficientes datos para los indicadores técnicos
            if len(price_history) >= 14:
                prices = np.array(price_history)

                # Cálculo de indicadores técnicos
                # 1. Media Móvil Simple (SMA)
                sma_5 = talib.SMA(prices, timeperiod=5)[-1]
                sma_10 = talib.SMA(prices, timeperiod=10)[-1]

                # 2. Índice de Fuerza Relativa (RSI)
                rsi = talib.RSI(prices, timeperiod=14)[-1]

                # 3. MACD
                macd, macdsignal, macdhist = talib.MACD(prices, fastperiod=12, slowperiod=26, signalperiod=9)
                macd_current = macd[-1]
                macd_signal_current = macdsignal[-1]

                # 4. Bandas de Bollinger
                upperband, middleband, lowerband = talib.BBANDS(prices, timeperiod=20)

                # Interpretación básica de los indicadores
                tendencia = 'desconocida'

                # Análisis de cruces de medias móviles
                if sma_5 > sma_10:
                    tendencia = 'alcista'
                elif sma_5 < sma_10:
                    tendencia = 'bajista'

                # Análisis del RSI
                sobrecompra = rsi > 70
                sobreventa = rsi < 30

                # Análisis del MACD
                if macd_current > macd_signal_current:
                    macd_tendencia = 'alcista'
                else:
                    macd_tendencia = 'bajista'

                # Análisis de Bandas de Bollinger
                precio_actual = prices[-1]
                if precio_actual > upperband[-1]:
                    bollinger = 'sobrecompra'
                elif precio_actual < lowerband[-1]:
                    bollinger = 'sobreventa'
                else:
                    bollinger = 'normal'
            else:
                sma_5 = sma_10 = rsi = macd_current = macd_signal_current = None
                tendencia = 'desconocida'
                sobrecompra = sobreventa = False
                macd_tendencia = 'desconocida'
                bollinger = 'normal'

            # Actualizar creencias con datos actuales y análisis técnico
            self.beliefs[name] = {
                'precio': float(crypto.price),
                'volumen': float(crypto.volume),
                'sentimiento': self.get_sentiment(name, sentiment_history),
                'historial_precios': price_history,
                'tendencia_precio': tendencia,
                'sma_5': sma_5,
                'sma_10': sma_10,
                'rsi': rsi,
                'macd_tendencia': macd_tendencia,
                'sobrecompra': sobrecompra,
                'sobreventa': sobreventa,
                'bollinger': bollinger
            }
        # print(f"Creencias actualizadas: {self.beliefs}")

    def options(self):
        """
        Función de Generación de Opciones:
        Genera posibles deseos basados en las creencias actuales y las reglas definidas.
        """
        self.desires.clear()
        for cripto, datos in self.beliefs.items():

            matched = 0
            # Utiliza el parser de reglas para evaluar las reglas en el contexto actual
            for regla in self.reglas:
                parsed_conditions, accion = self.parser_reglas.parse_rule(regla)
                resultado, _ = self.parser_reglas.aplicar_regla(parsed_conditions, accion, cripto, datos)
                # Si el resultado es positivo, agrega el deseo correspondiente
                if resultado > 0:
                    if accion == 1:
                        self.desires.add(('comprar', cripto))
                        matched = 1
                    elif accion == -1:
                        self.desires.add(('vender', cripto))
                        matched = 1
                    elif accion == 0:
                        self.desires.add(('mantener', cripto))

            if matched:
                continue

            # Generar deseos basados en análisis técnico
            if datos['tendencia_precio'] == 'alcista' and not datos['sobrecompra']:
                self.desires.add(('comprar', cripto))
            # Si el RSI indica sobreventa, desear comprar
            elif datos['sobreventa']:
                self.desires.add(('comprar', cripto))
            # Si el MACD indica tendencia alcista, desear comprar
            elif datos['macd_tendencia'] == 'alcista':
                self.desires.add(('comprar', cripto))
            # Si el RSI indica sobrecompra, desear vender
            elif datos['sobrecompra']:
                self.desires.add(('vender', cripto))
            # Si el MACD indica tendencia bajista, desear vender
            elif datos['macd_tendencia'] == 'bajista':
                self.desires.add(('vender', cripto))
            # Si el precio está por encima de la banda superior de Bollinger, desear vender
            elif datos['bollinger'] == 'sobrecompra':
                self.desires.add(('vender', cripto))
            else:
                self.desires.add(('mantener', cripto))

        # print(f"Deseos generados: {self.desires}")

    def filter(self):
        """
        Función de Filtrado (Deliberación):
        Filtra los deseos para actualizar las intenciones basadas en las creencias, deseos e intenciones actuales.
        - Elimina intenciones que ya no son válidas o cuyo costo supera los beneficios esperados.
        - Mantiene intenciones no logradas con posibles beneficios.
        - Adopta nuevas intenciones basadas en los deseos.
        """
        nuevas_intenciones = set()

        # Evaluar las intenciones actuales
        for accion, cripto in self.intentions:
            if accion == 'comprar':
                # Verificar si aún es factible y beneficioso comprar
                if self.capital >= self.beliefs[cripto]['precio']:
                    nuevas_intenciones.add((accion, cripto))
                else:
                    print(f"Intención de comprar {cripto} eliminada: capital insuficiente.")
            elif accion == 'vender':
                # Verificar si aún posee el activo
                if self.portafolio.get(cripto, 0.0) > 0.0:
                    nuevas_intenciones.add((accion, cripto))
                else:
                    print(f"Intención de vender {cripto} eliminada: no posee unidades.")

        # Adoptar nuevas intenciones basadas en deseos
        for deseo in self.desires:
            accion, cripto = deseo
            if accion == 'comprar' and self.capital >= self.beliefs[cripto]['precio']:
                nuevas_intenciones.add(deseo)
            elif accion == 'vender' and self.portafolio.get(cripto, 0.0) > 0.0:
                nuevas_intenciones.add(deseo)

        self.intentions = nuevas_intenciones
        # print(f"Intenciones después del filtrado: {self.intentions}")

        # Registrar las intenciones en el historial
        if self.intentions:
            self.historial_intenciones.append((self.ciclo, self.intentions.copy()))

    def execute(self, market_context):
        """
        Función de Ejecución:
        Determina y ejecuta acciones basadas en las intenciones actuales.
        """
        for accion, cripto in self.intentions:
            self.ejecutar_accion(accion, market_context, cripto)
        # Después de ejecutar, limpia las intenciones (asumiendo que se ejecutaron)
        self.intentions.clear()

    def action(self, market_context, sentiment_history):
        """
        Función principal de acción del agente BDI.
        Sigue el ciclo BDI: brf -> options -> filter -> execute
        """
        print(f"\nCiclo {self.ciclo} del agente {self.nombre}:")
        self.brf(market_context, sentiment_history)
        self.options()
        self.filter()
        self.execute(market_context)
        self.actualizar_ganancia(market_context)
        self.ciclo += 1

    def get_sentiment(self, crypto_name, sentiment_history):
        """
        Obtiene el sentimiento actual para una criptomoneda específica.
        """
        if sentiment_history and crypto_name in sentiment_history:
            return sentiment_history[crypto_name][-1]
        return 'neutral'  # Ajustar según el formato de tus datos

    def ejecutar_accion(self, accion, contexto, cripto):
        """
        Ejecuta la acción determinada ('comprar' o 'vender') para una criptomoneda específica.
        """
        precio = float(contexto.cryptocurrencies[cripto].price)
        if accion == "comprar":
            cantidad_a_comprar = self.calcular_cantidad_a_comprar(precio, cripto)
            if self.capital >= (cantidad_a_comprar * precio):
                # Realizar la compra
                self.capital -= cantidad_a_comprar * precio
                self.portafolio[cripto] = self.portafolio.get(cripto, 0.0) + cantidad_a_comprar
                print(f"{self.nombre} compró {cantidad_a_comprar:.8f} unidades de {cripto} a {precio:.2f} USD cada una, gastando un total de {(cantidad_a_comprar * precio):.2f}..")
                contexto.cryptocurrencies[cripto].add_order("buy", precio, cantidad_a_comprar)
            else:
                print(f"{self.nombre} no tiene suficiente capital para comprar {cantidad_a_comprar:.8f} unidades de {cripto}.")
        elif accion == "vender":
            cantidad_a_vender = self.calcular_cantidad_a_vender(cripto)
            if self.portafolio.get(cripto, 0.0) >= cantidad_a_vender:
                # Realizar la venta
                self.capital += cantidad_a_vender * precio
                self.portafolio[cripto] -= cantidad_a_vender
                print(f"{self.nombre} vendió {cantidad_a_vender:.8f} unidades de {cripto} a {precio:.2f} USD cada una, ganando un total de {(cantidad_a_vender * precio):.2f}.")
                contexto.cryptocurrencies[cripto].add_order("sell", precio, cantidad_a_vender)
            else:
                print(f"{self.nombre} no tiene suficientes unidades de {cripto} para vender {cantidad_a_vender:.8f} unidades.")
        # elif accion == "mantener":
        #     print(f"{self.nombre} mantiene su posición en {cripto}.")
        # else:
        #     print(f"Acción '{accion}' desconocida para {cripto}.")

    def calcular_cantidad_a_comprar(self, precio, cripto):
        """
        Calcula la cantidad de criptomoneda a comprar basada en métricas como RSI.
        Estrategia:
        - RSI < 30: Invertir el 15% del capital disponible
        - RSI > 70: Invertir el 5% del capital disponible
        - RSI entre 30 y 70: Invertir el 10% del capital disponible
        - RSI es None: Invertir el 10% del capital disponible
        """
        datos = self.beliefs[cripto]
        rsi = datos.get('rsi', None)

        if rsi is not None:
            if rsi < 30:
                porcentaje_inversion = 0.15  # 15%
            elif rsi > 70:
                porcentaje_inversion = 0.05  # 5%
            else:
                porcentaje_inversion = 0.10  # 10%
        else:
            porcentaje_inversion = 0.10  # 10% por defecto

        monto_a_invertir = self.capital * porcentaje_inversion
        cantidad = monto_a_invertir / precio
        cantidad = round(cantidad, 8)  # Redondear a 8 decimales para criptomonedas
        return cantidad

    def calcular_cantidad_a_vender(self, cripto):
        """
        Calcula la cantidad de criptomoneda a vender basada en métricas como RSI.
        Estrategia:
        - RSI > 70: Vender el 50% de las holdings
        - RSI < 30: No vender
        - RSI entre 30 y 70: Vender el 25% de las holdings
        - RSI es None: Vender el 25% de las holdings
        """
        datos = self.beliefs[cripto]
        rsi = datos.get('rsi', None)
        cantidad_actual = self.portafolio.get(cripto, 0.0)

        if rsi is not None:
            if rsi > 70:
                porcentaje_vender = 0.50  # Vender el 50%
            elif rsi < 30:
                porcentaje_vender = 0.0   # No vender
            else:
                porcentaje_vender = 0.25  # Vender el 25%
        else:
            porcentaje_vender = 0.25  # Vender el 25% por defecto

        cantidad = cantidad_actual * porcentaje_vender
        cantidad = round(cantidad, 8)  # Redondear a 8 decimales para criptomonedas
        return cantidad

    def actualizar_ganancia(self, contexto):
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

    def evaluar_desempeno(self, contexto):
        """
        Evalúa el desempeño del agente basado en las ganancias obtenidas.
        """
        ganancia = 0.0
        for crypto, value in self.portafolio.items():
            ganancia += contexto.cryptocurrencies[crypto].price * value
        ganancia += self.capital
        desempeño = ((ganancia - self.capital_inicial) / self.capital_inicial) * 100  # Rendimiento porcentual
        return desempeño
