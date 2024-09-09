from abc import ABC
from rules_interpreter import *
from typing import List, Dict
from market import *

# Definición de la clase Agente
class Agente:
    def __init__(self, nombre, reglas, parser_reglas , capital_inicial = 1000):#*****bien
        # Inicializa el agente con un nombre, capital inicial, conjunto de reglas, parser de reglas y portafolio vacío
        self.nombre = nombre
        self.capital_inicial = capital_inicial
        self.capital = self.capital_inicial
        self.reglas = reglas
        self.parser_reglas = parser_reglas
        self.mejor_reglas = []  # Almacena las mejores reglas seleccionadas
        self.portafolio = {}  # Portafolio para almacenar las criptomonedas compradas
    
    def tomar_decision(self, contexto):#ver
        # Inicializa variables para rastrear la mejor acción y el mejor resultado
        mejor_resultado = 0
        mejor_accion = "mantener"
        
        # Itera sobre cada regla para evaluarla en el contexto actual
        for regla in self.reglas:
            # Analiza la regla y la aplica al contexto de mercado
            parsed_conditions, accion = self.parser_reglas.parse_rule(regla)
            resultado = self.parser_reglas.aplicar_regla(parsed_conditions, accion, contexto)
            
            # Actualiza la mejor acción si el resultado de esta regla es superior
            if abs(resultado[0]) > abs(mejor_resultado[0]):
                mejor_resultado = resultado
                mejor_accion = accion
        
        # Interpreta el resultado y muestra la decisión tomada
        interpretacion = self.interpretar_resultado(mejor_resultado, mejor_accion)
        print(f"{self.nombre} decidió: {interpretacion}")
        
        # Retorna la mejor acción y el resultado asociado
        return mejor_accion, mejor_resultado
    
    def interpretar_resultado(self, resultado, accion):
        # Convierte la acción numérica en una cadena descriptiva
        if accion == 1:
            accion_str = "comprar"
        elif accion == -1:
            accion_str = "vender"
        else:
            accion_str = "mantener"
        
        # Interpreta el resultado de la acción basada en la confianza (valor de resultado)
        if resultado[0] == 0:
            return f"La regla sugiere no {accion_str} en este contexto."
        elif resultado[0] > 0:
            if resultado[0] >= 0.8:
                return f"Fuerte recomendación para {accion_str} {resultado[1]} con confianza de {resultado[0]:.2f}."
            elif resultado[0] >= 0.5:
                return f"Moderada recomendación para {accion_str} {resultado[1]} con confianza de {resultado[0]:.2f}."
            else:
                return f"Débil recomendación para {accion_str} {resultado[1]} con confianza de {resultado[0]:.2f}."
        elif resultado[0] < 0:
            if resultado[0] <= -0.8:
                return f"Fuerte recomendación para no {accion_str} {resultado[1]} con confianza de {resultado[0]:.2f}."
            elif resultado[0] <= -0.5:
                return f"Moderada recomendación para no {accion_str} {resultado[1]} con confianza de {resultado[0]:.2f}."
            else:
                return f"Débil recomendación para no {accion_str} {resultado[1]} con confianza de {resultado[0]:.2f}."
    
    def ejecutar_accion(self, accion, contexto, cripto):
        # Obtiene el precio actual de la criptomoneda del contexto de mercado
        precio = contexto.obtener_dato(cripto, "precio")
        
        if accion == "comprar" and self.capital > precio:
            # Calcula cuántas unidades se pueden comprar y actualiza el capital y portafolio del agente
            cantidad = self.capital // precio
            self.capital -= cantidad * precio
            if cripto in self.portafolio:
                self.portafolio[cripto] += cantidad
            else:
                self.portafolio[cripto] = cantidad
            print(f"{self.nombre} compró {cantidad} unidades de {cripto}.")
            
            contexto.cryptocurrencies[cripto].add_order("buy",precio,cantidad)

        elif accion == "vender":
            # Verifica si el agente tiene unidades para vender
            if cripto in self.portafolio and self.portafolio[cripto] > 0:
                cantidad = self.portafolio[cripto]
                self.capital += cantidad * precio
                self.portafolio[cripto] = 0  # Vender todas las unidades
                print(f"{self.nombre} vendió {cantidad} unidades de {cripto}.")
                
                # Actualizar el precio en el contexto: la venta disminuye el precio ligeramente
                nuevo_precio = precio * (1 - cantidad / 100000)  # Simplificación: pequeña caída de precio

                contexto.cryptocurrencies[cripto].add_order("sell",precio,cantidad)
            else:
                print(f"{self.nombre} no tiene unidades de {cripto} para vender.")

    def evaluar_desempeno(self,contexto):
        # Evalúa el desempeño del agente basado en las ganancias obtenidas
        ganancia = 0
        for crypto,value in self.portafolio:
            ganancia =  ganancia + (contexto.Cryptocurrency[crypto].price * value)
        ganancia = ganancia + capital

        return (self.nombre,ganancia/self.capital_inicial)