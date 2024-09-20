from abc import ABC
from rules_interpreter import *
from typing import List, Dict
from market import *
import random
import numpy as np

# Definición de la clase Agente
class Agente:
    def __init__(self, nombre, reglas, parser_reglas, capital_inicial=100000):
        # Inicializa el agente con un nombre, capital inicial, conjunto de reglas, parser de reglas y portafolio vacío
        self.nombre = nombre
        self.capital_inicial = capital_inicial
        self.capital = self.capital_inicial
        self.reglas = reglas
        self.parser_reglas = parser_reglas
        self.historia_ganancia = []
        self.portafolio = {}  # Portafolio para almacenar las criptomonedas compradas
        self.ciclo = 1

        # **Componentes BDI**
        self.beliefs = {}          # Creencias: Información actual del mercado
        self.desire = "Maximizar ganancias"  # Deseo fijo
        self.intentions = reglas   # Intenciones: Reglas de acción

    def update_beliefs(self, market_context, sentiment_history):
        """
        Actualiza las creencias del agente con el nuevo contexto del mercado.
        """
        self.beliefs = {
                name: {
                    'price': crypto.price,
                    'volume': crypto.volume,
                    'sentiment': self.get_sentiment(name, sentiment_history)  # Método para obtener el sentimiento actual
                }
                for name, crypto in market_context.cryptocurrencies.items()
            }
        print(self.beliefs)
        print(self.intentions)



    def get_sentiment(self, crypto_name, sentiment_history):
        """
        Obtiene el sentimiento actual para una criptomoneda específica.
        """
        # Asumiendo que tienes un historial de sentimientos almacenado
        if sentiment_history and crypto_name in sentiment_history:
            return sentiment_history[crypto_name][-1]
        return 0  # Sentimiento neutro por defecto si no hay datos

    def set_intentions(self, plans):
        """
        Establece las intenciones/plans del agente.
        """
        self.intentions = plans

    def tomar_decision(self, contexto):
        # Inicializa variables para rastrear la mejor acción y el mejor resultado
        mejor_resultado = (0, None)  # Tupla (valor, criptomoneda)
        mejor_accion = "mantener"

        # Itera sobre cada regla para evaluarla en el contexto actual
        for regla in self.reglas:
            # Analiza la regla y la aplica al contexto de mercado
            parsed_conditions, accion = self.parser_reglas.parse_rule(regla)
            resultado, cripto = self.parser_reglas.aplicar_regla(parsed_conditions, accion, contexto)

            # Actualiza la mejor acción si el resultado de esta regla es superior
            if abs(resultado) > abs(mejor_resultado[0]):
                mejor_resultado = (resultado, cripto)
                if resultado > 0:
                    mejor_accion = "comprar"
                elif resultado < 0:
                    mejor_accion = "vender"
                else:
                    mejor_accion = "mantener"

        # Interpreta el resultado y muestra la decisión tomada
        interpretacion = self.interpretar_resultado(mejor_resultado, mejor_accion)
        print(f"{self.nombre} decidió: {interpretacion}")

        # Retorna la mejor acción y el resultado asociado
        return mejor_accion, mejor_resultado,cripto

    def interpretar_resultado(self, resultado, accion):
        # Convierte la acción numérica en una cadena descriptiva
        if accion == "comprar":
            accion_str = "comprar"
        elif accion == "vender":
            accion_str = "vender"
        else:
            accion_str = "mantener"

        # Interpreta el resultado de la acción basada en la confianza (valor de resultado)
        valor = resultado[0]
        cripto = resultado[1]

        if valor == 0:
            return f"La regla sugiere no {accion_str} en este contexto."
        elif valor > 0:
            if valor >= 0.8:
                return f"Fuerte recomendación para {accion_str} {cripto} con confianza de {valor:.2f}."
            elif valor >= 0.5:
                return f"Moderada recomendación para {accion_str} {cripto} con confianza de {valor:.2f}."
            else:
                return f"Débil recomendación para {accion_str} {cripto} con confianza de {valor:.2f}."
        elif valor < 0:
            if valor <= -0.8:
                return f"Fuerte recomendación para no {accion_str} {cripto} con confianza de {valor:.2f}."
            elif valor <= -0.5:
                return f"Moderada recomendación para no {accion_str} {cripto} con confianza de {valor:.2f}."
            else:
                return f"Débil recomendación para no {accion_str} {cripto} con confianza de {valor:.2f}."

    def ejecutar_accion(self, accion, contexto, cripto):
        print("********* EJECUTAR ACCION*******")
        print(accion)
        # Obtiene el precio actual de la criptomoneda del contexto de mercado
        precio = contexto.cryptocurrencies[cripto].price
        print(precio)
        print(self.capital)
        if accion == "comprar" and self.capital > precio:
            # Calcula cuántas unidades se pueden comprar y actualiza el capital y portafolio del agente
            cantidad = self.capital // precio
            if cantidad > 0:
                self.capital -= cantidad * precio
                if cripto in self.portafolio:
                    self.portafolio[cripto] += cantidad
                else:
                    self.portafolio[cripto] = cantidad
                print(f"{self.nombre} compró {cantidad} unidades de {cripto} a {precio:.2f} USD cada una.")

                contexto.cryptocurrencies[cripto].add_order("buy", precio, cantidad)
            else:
                print(f"{self.nombre} no tiene suficiente capital para comprar {cripto}.")

        elif accion == "vender":
            # Verifica si el agente tiene unidades para vender
            if cripto in self.portafolio and self.portafolio[cripto] > 0:
                cantidad = self.portafolio[cripto]
                self.capital += cantidad * precio
                self.portafolio[cripto] = 0  # Vender todas las unidades
                print(f"{self.nombre} vendió {cantidad} unidades de {cripto} a {precio:.2f} USD cada una.")

                # Actualizar el precio en el contexto: la venta disminuye el precio ligeramente
                nuevo_precio = precio * (1 - cantidad / 100000)  # Simplificación: pequeña caída de precio

                contexto.cryptocurrencies[cripto].add_order("sell", precio, cantidad)
            else:
                print(f"{self.nombre} no tiene unidades de {cripto} para vender.")

    def evaluar_desempeno(self, contexto):
        """
        Evalúa el desempeño del agente basado en las ganancias obtenidas.
        """
        ganancia = 0
        for crypto, value in self.portafolio.items():
            ganancia += contexto.cryptocurrencies[crypto].price * value
        ganancia += self.capital
        desempeño = (ganancia - self.capital_inicial) / self.capital_inicial * 100  # Rendimiento porcentual
        return desempeño

    def actualizar_ganancia(self, contexto):
        """
        Actualiza el historial de ganancias del agente.
        """
        ganancia = 0
        for crypto, value in self.portafolio.items():
            ganancia += contexto.cryptocurrencies[crypto].price * value
        ganancia += self.capital
        self.historia_ganancia.append(ganancia - self.capital_inicial)
