from typing import List, Dict, Tuple
from market import *  # Asegúrate de que este módulo exista y esté correctamente implementado
import random
import numpy as np
from rules_interpreter import *  # Asegúrate de que este módulo exista y esté correctamente implementado
import talib
from collections import deque, defaultdict
from Induction_Motor.Motor import *
from Rules_Interpreter.rulelexer import RuleLexer
from Rules_Interpreter.ruleparser import RuleParser
from Rules_Interpreter.ruleinterpreter import RuleInterpreter


# context = {
#     "pertenencia_precio_bajo": lambda precio, limite_inferior, limite_superior: 1 if precio < limite_inferior else (limite_superior - precio) / (limite_superior - limite_inferior) if limite_inferior <= precio <= limite_superior else 0,
#     "pertenencia_precio_medio": lambda precio, limite_inferior, limite_superior: 1 if limite_inferior <= precio <= limite_superior else (precio - limite_superior) / (limite_superior - limite_inferior) if limite_superior < precio < limite_superior + (limite_superior - limite_inferior) else (limite_inferior - precio) / (limite_superior - limite_inferior) if limite_inferior - (limite_superior - limite_inferior) < precio < limite_inferior else 0,
#     "pertenencia_precio_alto": lambda precio, limite_inferior, limite_superior: 1 if precio > limite_superior else (precio - limite_inferior) / (limite_superior - limite_inferior) if limite_inferior <= precio <= limite_superior else 0,

#     "pertenencia_volumen_bajo": lambda volumen, limite_inferior, limite_superior: 1 if volumen < limite_inferior else (limite_superior - volumen) / (limite_superior - limite_inferior) if limite_inferior <= volumen <= limite_superior else 0,
#     "pertenencia_volumen_medio": lambda volumen, limite_inferior, limite_superior: 1 if limite_inferior <= volumen <= limite_superior else (volumen - limite_superior) / (limite_superior - limite_inferior) if limite_superior < volumen < limite_superior + (limite_superior - limite_inferior) else (limite_inferior - volumen) / (limite_superior - limite_inferior) if limite_inferior - (limite_superior - limite_inferior) < volumen < limite_inferior else 0,
#     "pertenencia_volumen_alto": lambda volumen, limite_inferior, limite_superior: 1 if volumen > limite_superior else (volumen - limite_inferior) / (limite_superior - limite_inferior) if limite_inferior <= volumen <= limite_superior else 0,

#     "pertenencia_sentimiento_negativo": lambda sentimiento: 1 if sentimiento == 'negativo' else 0,
#     "pertenencia_sentimiento_neutro": lambda sentimiento: 1 if sentimiento == 'neutro' else 0,
#     "pertenencia_sentimiento_positivo": lambda sentimiento: 1 if sentimiento == 'positivo' else 0,

#     "pertenencia_rsi_alto": lambda x: 1 if x > 70 else (x - 50) / 20 if x > 50 else 0,
#     "pertenencia_rsi_medio": lambda x: (x - 30) / 20 if 30 < x <= 50 else (70 - x) / 20 if 50 < x <= 70 else 0,
#     "pertenencia_rsi_bajo": lambda x: 1 if x < 30 else (50 - x) / 20 if x < 50 else 0,


#     "precio": 0,
#     "sentimiento": 0,


#     "tendencia_precio_alcista": lambda x: 1 if x == 'alcista' else 0,
#     "tendencia_precio_bajista": lambda x: 1 if x == 'bajista' else 0,
#     "tendencia_precio_estable": lambda x: 1 if x == 'estable' else 0,

#     "rsi_alto": lambda x: pertenencia_rsi_alto(x),
#     "rsi_medio": lambda x: pertenencia_rsi_medio(x),
#     "rsi_bajo": lambda x: pertenencia_rsi_bajo(x),
#     "rsi_sobrecompra": lambda x: 1 if x > 70 else 0,
#     "rsi_sobreventa": lambda x: 1 if x < 30 else 0,

#     "beliefs" : {
#         'novato': 0.9,
#         'experto': 0.9,
#         'miedo': 0.1,
#         'avaricioso': 0.9,
#         "sma_tendendia": 0
#     }
# }

# if __name__ == '__main__':
#     lex = RuleLexer()
#     par = RuleParser()
#     int = RuleInterpreter()




#     rules = """SI miedo Y sma_tendendia es 0 ENTONCES COMPRAR capital
#                SI avaricioso Y precio menor que 500 ENTONCES COMPRAR capital
# """

#     # result = par.parse(lex.tokenize(rules))
#     result = [('statement_rule', ('creencia', 'novato'), ('accion', 'COMPRAR', ('accion_capital', 'CAPITAL'))), ('statement_rule', ('creencia', 'experto'), ('accion', 'COMPRAR', ('accion_capital', 'CAPITAL'))), ('statement_rule', ('mayor que', ('funcion', 'historia_precio', [('number', '20')]), ('number', '5')), ('accion', 'COMPRAR', ('accion_capital', 'CAPITAL', '0.20'))), ('statement_rule', ('funcion', 'historia_precio', [('number', '20')]), ('accion', 'VENDER', ('accion_cantidad', 'TODO'))), ('statement_rule', ('funcion', 'historia_precio', [('number', '20')]), ('accion', 'COMPRAR', ('accion_capital', 'CAPITAL'))), ('statement_rule', ('mayor que', ('variable', 'precio'), ('number', '500')), ('accion', 'VENDER', ('accion_cantidad', 'TODO')))]

#     print(result)
#     for instruction in result:
#         print(int.evaluate(instruction, context))

# reglas: List[str], parser_reglas: ParserReglas
class Agente:
    def __init__(self, nombre: str, beliefs: List[str] ,inference_engine , interpreter, capital_inicial: float = 100000.0):
        self.nombre = nombre
        self.capital_inicial = float(capital_inicial)
        self.capital = float(capital_inicial)
        # self.reglas = reglas
        # self.parser_reglas = parser_reglas
        self.interpreter = interpreter
        self.historia_ganancia = []
        self.portafolio: Dict[str, float] = {}  # Portafolio para almacenar las criptomonedas compradas
        self.ciclo = 1

        # **Componentes BDI**
        self.beliefs: Dict[str, List[str]] = {}
        self.beliefs["asserts"] = beliefs
        self.beliefs["rules"] = []
        self.desires = []
        self.intentions = []

        self.inference_engine = inference_engine

        # Lista para registrar todas las intenciones a lo largo de la simulación
        self.historial_intenciones: List[Tuple[int, List[Tuple[str, str]]]] = []
        self.historia_ganancia.append(0)

    def brf(self, market_context: Market): #,sentiment_history: Dict[str, List[float]]):

        asserts_list = self.beliefs.get("asserts", [])
        rules = self.beliefs.get("rules", [])

        self.inference_engine.set_beliefs(asserts_list)
        self.inference_engine.apply_rules()

        self.beliefs["asserts"] = self.inference_engine.get_beliefs()
        self.beliefs["rules"] = self.inference_engine.generated_rules()



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

    def build_context(self, cripto_name: str, crypto: Cryptocurrency, market_context: Market) -> Dict:
        """
        Construye el contexto necesario para evaluar las reglas de una criptomoneda específica.

        Args:
            cripto_name (str): Nombre de la criptomoneda.
            crypto (CryptoCurrency): Objeto que contiene los datos de la criptomoneda.
            market_context (Market): Objeto que contiene el contexto general del mercado.

        Returns:
            Dict: Contexto construido para la regla.
        """
        # Definir las creencias que se esperan en el contexto
        posibles_creencias = ['novato', 'experto', 'miedo', 'avaricioso', 'sma_tendendia', 'avanzado', 'impulsivo', 'tendencia', 'terco', 'analista', 'noticias', 'TERCO', 'NERVIOSO', 'AVARICIOSO', 'ALEGRE', 'TONTO']

        # Normalizar las creencias del agente a minúsculas para evitar discrepancias
        creencias_agente = set(creencia.lower() for creencia in self.beliefs.get("asserts", []))

        # Construir el diccionario de creencias para el contexto
        creencias_contexto = {}
        for creencia in posibles_creencias:
            creencias_contexto[creencia] = 0.9 if creencia.lower() in creencias_agente else 0.1

        # Obtener datos actuales de la criptomoneda
        precio = float(crypto.price)
        volumen = float(crypto.volume)
        sentimiento = 1 #self.get_sentiment(cripto_name, market_context.sentiment_history)
        tendencia_precio = 'alticista' #self.get_tendencia_precio(cripto_name, market_context)
        rsi = 80 # self.get_rsi(cripto_name, market_context)

        # Construir el contexto completo
        context = {
            "precio": precio,
            "volumen": volumen,
            "sentimiento": sentimiento,
            "tendencia_precio_alcista": 1 if tendencia_precio == 'alcista' else 0,
            "tendencia_precio_bajista": 1 if tendencia_precio == 'bajista' else 0,
            "tendencia_precio_estable": 1 if tendencia_precio == 'estable' else 0,
            "rsi_alto": 1 if rsi > 70 else 0,
            "rsi_medio": 1 if 30 < rsi <= 70 else 0,
            "rsi_bajo": 1 if rsi < 30 else 0,
            "rsi_sobrecompra": 1 if rsi > 70 else 0,
            "rsi_sobreventa": 1 if rsi < 30 else 0,
            "beliefs": creencias_contexto
        }

        return context



    def options(self, market_context: Market):
        """
        Función de Generación de Opciones:
        Para cada criptomoneda en el mercado, evalúa todas las reglas definidas.
        Si una regla se aplica, extrae la acción y la cantidad a realizar.
        Actualiza las creencias del agente basadas en los resultados de las reglas.
        """
        self.desires.clear()  # Limpiar deseos anteriores

        for cripto_name, crypto in market_context.cryptocurrencies.items():
            # Construir el contexto específico para esta criptomoneda
            context = self.build_context(cripto_name, crypto, market_context)

            # Iterar sobre todas las reglas del agente
            for rule in self.beliefs.get("rules", []):
                print(f'LA REGLA: {rule}')
                if rule == ('statement_rule', ('mayor que', ('funcion', 'historia_precio', [('number', '20')]), ('number', '5')), ('accion', 'COMPRAR', ('accion_capital', 'CAPITAL', '0.20'))): continue
                if rule == ('statement_rule', ('funcion', 'historia_precio', [('number', '20')]), ('accion', 'VENDER', ('accion_cantidad', 'TODO'))): continue
                if rule == ('statement_rule', ('funcion', 'historia_precio', [('number', '20')]), ('accion', 'COMPRAR', ('accion_capital', 'CAPITAL'))): continue
                # Evaluar la regla con el contexto actual
                print(f'context: {context}')
                resultado = self.interpreter.evaluate(rule, context)


                if resultado is None:
                    print(f"Regla {rule} no pudo ser evaluada para {cripto_name}.")
                    continue  # Saltar a la siguiente regla si hay un error

                score, accion_info = resultado

                # Determinar si la regla se aplica
                if score >= 0.9:
                    accion, accion_detalles = accion_info[1], accion_info[2:]

                    # Determinar la cantidad basada en 'accion_capital'
                    if accion_detalles[0] == 'CAPITAL':
                        cantidad = 'CAPITAL'
                    else:
                        try:
                            # porcentaje = float(accion_detalles[0].strip('%'))
                            cantidad = accion_detalles[0]
                        except ValueError:
                            print(f"Formato de cantidad desconocido: {accion_detalles[0]}")
                            cantidad = 0.1  # Valor por defecto

                    # Añadir el deseo basado en la acción y la cantidad
                    desire = {
                        'cripto': cripto_name,
                        'accion': accion.lower(),  # 'comprar' o 'vender'
                        'cantidad': cantidad
                    }
                    self.desires.append(desire)

                #     # Actualizar las creencias (asserts) del agente
                #     belief_key = accion_info[1].lower()
                #     self.beliefs['asserts'][belief_key] = 0.9  # Aplicada
                # else:
                #     # Actualizar las creencias si la regla no se aplica
                #     belief_key = rule[1][1]  # Asumiendo que la segunda posición es la creencia
                #     self.beliefs['asserts'][belief_key] = 0.1  # No aplicada

        # Opcional: Imprimir los deseos generados para depuración
        print(f"Deseos generados: {self.desires}")

    # def options(self):
    #     """
    #     Función de Generación de Opciones:
    #     Genera posibles deseos basados en las creencias actuales y las reglas definidas.
    #     Ordena los deseos derivados de reglas por su resultado y añade los deseos basados en contexto al final.
    #     Mantiene 'self.desires' como un conjunto para evitar duplicados.
    #     """
    #     self.desires.clear()

    #     deseos = []
    #     for cripto, reglas in self.beliefs.items():
    #         deseos_con_resultado = []
    #         # Evaluar las reglas y almacenar los deseos con su resultado
    #         for regla in reglas:
    #             parsed_conditions, accion = self.parser_reglas.parse_rule(regla)
    #             if accion != belief_action:
    #                 continue
    #             resultado, _ = self.parser_reglas.aplicar_regla(parsed_conditions, accion, cripto, datos)
    #             # Si el resultado es positivo, agregar a la lista temporal
    #             if resultado > 0:
    #                 if accion == 1:
    #                     deseos_con_resultado.append((resultado, 'comprar', cripto))
    #                 elif accion == -1:
    #                     deseos_con_resultado.append((resultado, 'vender', cripto))
    #                 elif accion == 0:
    #                     deseos_con_resultado.append((resultado, 'mantener', cripto))

    #         # Ordenar los deseos derivados de reglas por resultado descendente
    #         deseos_con_resultado_sorted = sorted(deseos_con_resultado, key=lambda x: x[0], reverse=True)
    #         deseos.append(deseos_con_resultado_sorted[0])

    #     self.desires = deseos

    # def options(self):
    #     """
    #     Función de Generación de Opciones:
    #     Genera posibles deseos basados en las creencias actuales y las reglas definidas.
    #     Ordena los deseos derivados de reglas por su resultado y añade los deseos basados en contexto al final.
    #     Mantiene 'self.desires' como un conjunto para evitar duplicados.
    #     """
    #     self.desires.clear()

    #     deseos = []
    #     deseos_contexto = []
    #     for cripto, datos in self.beliefs.items():
    #         belief_action = 0

    #         #metodo para evaluar reglas

    #         """Este es el que deberías crear en el caso de que no me de tiempo

    #             como entrada el agente,el mercado,

    #             salida score,acción

    #         """
    #         #evaluar reglas
    #         if (datos['tendencia_precio'] == 'alcista' and not datos['sobrecompra']) or datos['sobreventa'] or datos['macd_tendencia'] == 'alcista':
    #             belief_action = 1
    #         elif datos['sobrecompra'] or datos['macd_tendencia'] == 'bajista' or datos['bollinger'] == 'sobrecompra':
    #             belief_action = -1
    #         else:
    #             belief_action = 0

    #         deseos_con_resultado = []
    #         matched = 0
    #         # Evaluar las reglas y almacenar los deseos con su resultado
    #         for regla in self.reglas:
    #             parsed_conditions, accion = self.parser_reglas.parse_rule(regla)
    #             if accion != belief_action:
    #                 continue
    #             resultado, _ = self.parser_reglas.aplicar_regla(parsed_conditions, accion, cripto, datos)
    #             # Si el resultado es positivo, agregar a la lista temporal
    #             if resultado > 0:
    #                 if accion == 1:
    #                     deseos_con_resultado.append((resultado, 'comprar', cripto))
    #
    #                 elif accion == -1:
    #                     deseos_con_resultado.append((resultado, 'vender', cripto))
    #
    #                 elif accion == 0:
    #                     deseos_con_resultado.append((resultado, 'mantener', cripto))
    #

    #         # Ordenar los deseos derivados de reglas por resultado descendente
    #         deseos_con_resultado_sorted = sorted(deseos_con_resultado, key=lambda x: x[0], reverse=True)

    #         if matched:
    #             for resultado, accion, cripto in deseos_con_resultado_sorted:
    #                 deseos.append((resultado, accion, cripto))
    #                 break
    #             continue

    #         if belief_action == 1:
    #             deseos_contexto.append(('comprar', cripto))
    #         elif belief_action == -1:
    #             deseos_contexto.append(('vender', cripto))
    #         elif belief_action == 0:
    #             deseos_contexto.append(('mantener', cripto))

    #     deseos_sorted = sorted(deseos, key=lambda x: x[0], reverse=True)
    #     for _, accion, cripto in deseos_sorted:
    #         self.desires.add((accion, cripto))
    #         break
    #     for accion, cripto in deseos_contexto:
    #         self.desires.add((accion, cripto))
    #         break

        # Opcional: Registrar los deseos generados para depuración
        # print(f"Deseos generados: {self.desires}")


    #Me parece que este se podría hacer ejecutar las acciones con un valor mayor a una cota
    def filter_desires(self):
        """
        Filtra los deseos actuales para mantener solo uno por criptomoneda.
        Prefiere acciones de mayor prioridad (por ejemplo, vender sobre comprar) o según algún criterio específico.
        """
        # Diccionario para almacenar el mejor deseo por criptomoneda
        mejores_deseos = {}

        for desire in self.desires:
            cripto = desire['cripto']
            accion = desire['accion']
            cantidad = desire['cantidad']

            # Definir prioridad de acciones: vender tiene mayor prioridad que comprar
            prioridad = {'vender': 2, 'comprar': 1, 'mantener': 0}
            accion_prioridad = prioridad.get(accion, 0)

            # Si la criptomoneda no está en mejores_deseos, añadirla
            if cripto not in mejores_deseos:
                mejores_deseos[cripto] = desire
            else:
                # Comparar prioridades y actualizar si el deseo actual tiene mayor prioridad
                deseo_existente = mejores_deseos[cripto]
                deseo_existente_prioridad = prioridad.get(deseo_existente['accion'], 0)

                if accion_prioridad > deseo_existente_prioridad:
                    mejores_deseos[cripto] = desire
                elif accion_prioridad == deseo_existente_prioridad:
                    # Opcional: Puedes definir un criterio adicional para romper empates
                    # Por ejemplo, seleccionar el deseo con mayor 'score' si está disponible
                    pass  # Aquí no se hace nada, se mantiene el deseo existente

        # Actualizar las intenciones del agente con los mejores deseos
        self.intentions.clear()
        for cripto, desire in mejores_deseos.items():
            accion = desire['accion']
            cantidad = desire['cantidad']
            self.intentions.append((accion, cripto, cantidad))

        # Limpiar los deseos después de filtrarlos
        self.desires.clear()

        # Opcional: Imprimir las intenciones filtradas para depuración
        print(f"Intenciones filtradas: {self.intentions}")

    # def filter_desires(self):
    #     """
    #     Filtra las intenciones actuales para mantener solo aquellas que están presentes en los deseos.
    #     Elimina las intenciones que ya no están en los deseos y añade nuevas intenciones basadas en los deseos restantes.
    #     Evita tener acciones conflictivas para la misma criptomoneda: solo una de 'comprar', 'vender', 'mantener'.
    #     """
    #     print("\nLOS DESEOS\n\n")
    #     print(self.desires)
    #     for cripto, accion in self.desires:
    #         # Verificar condiciones antes de añadir la intención
    #         if accion == 'comprar' and self.capital > 0:
    #             self.intentions.append((accion, cripto))
    #             self.desires.remove((accion, cripto))
    #         elif accion == 'vender' and self.portafolio.get(cripto, 0.0) > 0.0:
    #             self.intentions.append((accion, cripto))
    #             self.desires.remove((accion, cripto))
    #         elif accion == 'mantener':
    #             self.intentions.append((accion, cripto))
    #             self.desires.remove((accion, cripto))



    # aquí tienes que calcular el precio de las compras y las ventas
    def execute_intention(self, market_context: Market):
        """
        Ejecuta todas las intenciones basadas en los deseos filtrados.
        Cada intención incluye la acción, la criptomoneda y la cantidad.
        """
        for intention in self.intentions:
            accion, cripto, cantidad_info = intention

            if cantidad_info[0] == 'accion_capital' and cantidad_info[1] == 'CAPITAL':
                cantidad = 'CAPITAL'
            elif cantidad_info[0] == 'accion_cantidad' and cantidad_info[1] == 'TODO':
                cantidad = 'TODO'
            else:
                # Asumiendo que cualquier otro formato es un porcentaje numérico
                try:
                    cantidad = float(cantidad_info[1])
                except ValueError:
                    print(f"Cantidad desconocida en intención: {cantidad_info}")
                    cantidad = 0.1  # Valor por defecto si hay un error

            # Ejecutar la acción con la cantidad determinada
            self.ejecutar_accion(accion, market_context, cripto, cantidad)

        # Limpiar las intenciones después de ejecutarlas
        self.intentions.clear()

    # def execute_intention(self, market_context: Market): #, sentiment_history: Dict[str, List[float]]):
    #     """
    #     Ejecuta todas las intenciones en la cola FIFO.
    #     Verifica si cada intención sigue siendo válida antes de ejecutarla.
    #     """
    #     for cripto, action in self.intentions:
    #         accion, cripto = self.intentions
    #         # Ejecutar la acción
    #         self.ejecutar_accion(accion, market_context, cripto)
    #         # Actualizar el mercado después de ejecutar la acción
    #         # market_context.update(sentiment_history)
    #         # Actualizar ganancia
    #         self.actualizar_ganancia(market_context)
    #         # Revisar creencias después de actualizar el mercado
    #         # self.brf(market_context, sentiment_history)
    #         # # Actualizar deseos
    #         # self.options()
    #         # # Volver a filtrar las intenciones después de la actualización
    #         # self.filter_desires()



    def action(self, market_context: Market): #, sentiment_history: Dict[str, List[float]]):
        """
        Función principal de acción del agente BDI.
        Sigue el ciclo BDI: brf -> options -> filter_desires -> execute_intention
        """
        print(f"\nCiclo {self.ciclo} del agente {self.nombre}:")
        self.brf(market_context) #, sentiment_history)
        print("\n********** RESULTADOS MOTOR INFERENCIA **************\n")
        print("******************** NUEVAS CREENCIAS *************************\n")
        print(self.beliefs["asserts"])
        print('\n')
        print("****************** NUEVAS REGLAS ************************\n")
        print(self.beliefs["rules"])
        self.options(market_context)
        self.filter_desires()
        self.execute_intention(market_context )#, sentiment_history)

    def get_sentiment(self, crypto_name: str, sentiment_history: Dict[str, List[float]]) -> float:
        """
        Obtiene el sentimiento actual para una criptomoneda específica.
        """
        if sentiment_history and crypto_name in sentiment_history:
            return sentiment_history[crypto_name][-1]
        return 0.0  # Ajustar según el formato de tus datos

    def ejecutar_accion(self, accion: str, contexto: Market, cripto: str, cantidad):
        """
        Ejecuta la acción determinada ('comprar', 'vender' o 'mantener') para una criptomoneda específica.
        La cantidad puede ser:
            - Un número (porcentaje del capital para comprar).
            - 'CAPITAL' (comprar todo lo que el capital permita).
            - 'TODO' (vender todas las criptomonedas poseídas de ese tipo).
        """
        precio = float(contexto.cryptocurrencies[cripto].price)

        if accion == "comprar":
            if cantidad == 'CAPITAL':
                cantidad_valor = self.capital
                cantidad_a_comprar = cantidad_valor / precio
            else:
                # Asumiendo que 'cantidad' es un porcentaje decimal (por ejemplo, 0.20 para 20%)
                porcentaje = cantidad
                cantidad_valor = self.capital * porcentaje
                cantidad_a_comprar = cantidad_valor / precio

            # Validar que la cantidad a comprar sea mayor que un umbral mínimo
            if cantidad_a_comprar > 0 and self.capital >= cantidad_valor:
                # Realizar la compra
                self.capital -= cantidad_valor
                self.portafolio[cripto] = self.portafolio.get(cripto, 0.0) + cantidad_a_comprar
                print(f"{self.nombre} compró {cantidad_a_comprar:.8f} unidades de {cripto} a {precio:.2f} USD cada una, gastando un total de {cantidad_valor:.2f} USD.")
                contexto.cryptocurrencies[cripto].add_order("buy", precio, cantidad_a_comprar)
            else:
                print(f"{self.nombre} no tiene suficiente capital para comprar {cantidad_a_comprar:.8f} unidades de {cripto}.")

        elif accion == "vender":
            if cantidad == 'TODO':
                cantidad_a_vender = self.portafolio.get(cripto, 0.0)
                cantidad_valor = cantidad_a_vender * precio
            else:
                # Asumiendo que 'cantidad' es un porcentaje decimal (por ejemplo, 0.50 para vender el 50%)
                porcentaje = cantidad
                cantidad_a_vender = self.portafolio.get(cripto, 0.0) * porcentaje
                cantidad_valor = cantidad_a_vender * precio

            # Validar que la cantidad a vender sea mayor que un umbral mínimo
            if cantidad_a_vender > 0 and self.portafolio.get(cripto, 0.0) >= cantidad_a_vender:
                # Realizar la venta
                self.capital += cantidad_valor
                self.portafolio[cripto] -= cantidad_a_vender
                print(f"{self.nombre} vendió {cantidad_a_vender:.8f} unidades de {cripto} a {precio:.2f} USD cada una, ganando un total de {cantidad_valor:.2f} USD.")
                contexto.cryptocurrencies[cripto].add_order("sell", precio, cantidad_a_vender)
            else:
                print(f"{self.nombre} no tiene suficientes unidades de {cripto} para vender {cantidad_a_vender:.8f} unidades.")

        elif accion == "mantener":
            print(f"{self.nombre} mantiene su posición en {cripto}.")

        else:
            print(f"Acción '{accion}' desconocida para {cripto}.")

    # def ejecutar_accion(self, accion: str, contexto: Market, cripto: str, cantidad_valor: float):
    #     """
    #     Ejecuta la acción determinada ('comprar', 'vender' o 'mantener') para una criptomoneda específica.
    #     """
    #     precio = float(contexto.cryptocurrencies[cripto].price)
    #     if accion == "comprar":
    #         cantidad_a_comprar = cantidad_valor / precio
    #         # Validar que la cantidad a comprar sea mayor que un umbral mínimo
    #         if cantidad_a_comprar > 0 and self.capital >= cantidad_valor:
    #             # Realizar la compra
    #             self.capital -= cantidad_valor
    #             self.portafolio[cripto] = self.portafolio.get(cripto, 0.0) + cantidad_a_comprar
    #             print(f"{self.nombre} compró {cantidad_a_comprar:.8f} unidades de {cripto} a {precio:.2f} USD cada una, gastando un total de {cantidad_valor:.2f} USD.")
    #             contexto.cryptocurrencies[cripto].add_order("buy", precio, cantidad_a_comprar)
    #         else:
    #             print(f"{self.nombre} no tiene suficiente capital para comprar {cantidad_a_comprar:.8f} unidades de {cripto}.")

    #     elif accion == "vender":
    #         cantidad_a_vender = cantidad_valor / precio
    #         # Validar que la cantidad a vender sea mayor que un umbral mínimo
    #         if cantidad_a_vender > 0 and self.portafolio.get(cripto, 0.0) >= cantidad_a_vender:
    #             # Realizar la venta
    #             self.capital += cantidad_valor
    #             self.portafolio[cripto] -= cantidad_a_vender
    #             print(f"{self.nombre} vendió {cantidad_a_vender:.8f} unidades de {cripto} a {precio:.2f} USD cada una, ganando un total de {cantidad_valor:.2f} USD.")
    #             contexto.cryptocurrencies[cripto].add_order("sell", precio, cantidad_a_vender)
    #         else:
    #             print(f"{self.nombre} no tiene suficientes unidades de {cripto} para vender {cantidad_a_vender:.8f} unidades.")

    #     elif accion == "mantener":
    #         print(f"{self.nombre} mantiene su posición en {cripto}.")

    #     else:
    #         print(f"Acción '{accion}' desconocida para {cripto}.")

    #cambiar método
    # def ejecutar_accion(self, accion: str, contexto: Market, cripto: str):
    #     """
    #     Ejecuta la acción determinada ('comprar', 'vender' o 'mantener') para una criptomoneda específica.
    #     """
    #     precio = float(contexto.cryptocurrencies[cripto].price)
    #     if accion == "comprar":
    #         cantidad_a_comprar = self.calcular_cantidad_a_comprar(precio, cripto)
    #         # Validar que la cantidad a comprar sea mayor que un umbral mínimo
    #         if cantidad_a_comprar > 0 and self.capital >= cantidad_a_comprar * precio:
    #             # Realizar la compra
    #             self.capital -= cantidad_a_comprar * precio
    #             self.portafolio[cripto] = self.portafolio.get(cripto, 0.0) + cantidad_a_comprar
    #             print(f"{self.nombre} compró {cantidad_a_comprar:.8f} unidades de {cripto} a {precio:.2f} USD cada una, gastando un total de {(cantidad_a_comprar * precio):.2f} USD.")
    #             contexto.cryptocurrencies[cripto].add_order("buy", precio, cantidad_a_comprar)
    #         else:
    #             print(f"{self.nombre} no tiene suficiente capital para comprar {cantidad_a_comprar:.8f} unidades de {cripto}.")

    #     elif accion == "vender":
    #         cantidad_a_vender = self.calcular_cantidad_a_vender(cripto)
    #         # Validar que la cantidad a vender sea mayor que un umbral mínimo
    #         if cantidad_a_vender > 0 and self.portafolio.get(cripto, 0.0) >= cantidad_a_vender:
    #             # Realizar la venta
    #             self.capital += cantidad_a_vender * precio
    #             self.portafolio[cripto] -= cantidad_a_vender
    #             print(f"{self.nombre} vendió {cantidad_a_vender:.8f} unidades de {cripto} a {precio:.2f} USD cada una, ganando un total de {(cantidad_a_vender * precio):.2f} USD.")
    #             contexto.cryptocurrencies[cripto].add_order("sell", precio, cantidad_a_vender)
    #         else:
    #             print(f"{self.nombre} no tiene suficientes unidades de {cripto} para vender {cantidad_a_vender:.8f} unidades.")

    #     elif accion == "mantener":
    #         print(f"{self.nombre} mantiene su posición en {cripto}.")

    #     else:
    #         print(f"Acción '{accion}' desconocida para {cripto}.")

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
