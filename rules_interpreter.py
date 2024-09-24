import numpy as np
import math
import operator
import re


class ParserReglas:
    def __init__(self, pertenencia_map):
        self.pertenencia_map = pertenencia_map
        self.operators = {
            '>': operator.gt,
            '<': operator.lt,
            '>=': operator.ge,
            '<=': operator.le,
            '==': operator.eq,
            '!=': operator.ne
        }

    def parse_rule(self, rule):
        # Patrón para extraer la condición y la acción
        pattern = r'SI (.+) ENTONCES (\w+)'
        match = re.match(pattern, rule)
        if not match:
            raise ValueError(f'Regla mal formada: {rule}')
        condition_str, action_str = match.groups()

        # Parsear la acción
        if action_str.lower() == 'comprar':
            accion = 1
        elif action_str.lower() == 'vender':
            accion = -1
        else:
            accion = 0  # Mantener

        # Parsear las condiciones
        # Soportar conectores lógicos AND (Y) y OR (O)
        conditions = re.split(r'\s+Y\s+|\s+O\s+', condition_str)
        connectors = re.findall(r'\s+(Y|O)\s+', condition_str)
        parsed_conditions = []
        for cond in conditions:
            # Patrón para extraer variable, operador y valor
            # Soporta operadores 'es', 'no es', '>', '<', '>=', '<=', '==', '!='
            pattern_cond = r'(\w+)\s*(es|no es|>|<|>=|<=|==|!=)\s*(\w+|\d+(\.\d+)?)'
            match_cond = re.match(pattern_cond, cond.strip())
            if not match_cond:
                raise ValueError(f'Condición mal formada: {cond}')
            var, operator, val, _ = match_cond.groups()
            parsed_conditions.append((var.lower(), operator, val.lower()))
        return (parsed_conditions, connectors), accion

    def aplicar_regla(self, parsed_conditions, accion, cripto, datos):
        (conditions, connectors) = parsed_conditions
        resultado = None
        idx = 0
        for var, operator, val in conditions:
            pertenencia_valor = self.evaluate_condition(var, operator, val, cripto, datos)
            if resultado is None:
                resultado = pertenencia_valor
            else:
                connector = connectors[idx - 1]
                if connector == 'Y':
                    resultado = min(resultado, pertenencia_valor)
                elif connector == 'O':
                    resultado = max(resultado, pertenencia_valor)
            idx += 1
        return resultado, accion

    def evaluate_condition(self, var, operator, val, cripto, datos):
        if var in datos:
            valor_actual = datos[var]
            # Si el valor actual es numérico
            if isinstance(valor_actual, (int, float)):
                if operator in self.operators:
                    val_num = float(val)
                    oper = self.operators[operator]
                    return 1 if oper(valor_actual, val_num) else 0
                elif operator == 'es':
                    # Usar funciones de pertenencia
                    if val in self.pertenencia_map[cripto][var]:
                        funcion_pertenencia = self.pertenencia_map[cripto][var][val]
                        return funcion_pertenencia(valor_actual)
                    else:
                        return 0
                else:
                    return 0
            # Si el valor actual es una cadena
            elif isinstance(valor_actual, str):
                if operator == 'es':
                    return 1 if valor_actual.lower() == val.lower() else 0
                elif operator == 'no es':
                    return 1 if valor_actual.lower() != val.lower() else 0
                else:
                    return 0
            # Si el valor actual es booleano
            elif isinstance(valor_actual, bool):
                val_bool = val.lower() in ['verdadero', 'true']
                if operator == 'es':
                    return 1 if valor_actual == val_bool else 0
                elif operator == 'no es':
                    return 1 if valor_actual != val_bool else 0
                else:
                    return 0
            else:
                return 0
        else:
            print(f"Advertencia: Parámetro {var} desconocido. Se omite.")
            return 0

class Map:
    def __init__(self):
        self.pertenencia_map = {
            "Bitcoin": {
                "precio": {
                    "bajo": lambda precio: self.pertenencia_precio_bajo(precio, limite_inferior=0, limite_superior=45000),
                    "medio": lambda precio: self.pertenencia_precio_medio(precio, limite_inferior=45000, limite_superior=60000),
                    "alto": lambda precio: self.pertenencia_precio_alto(precio, limite_inferior=60000, limite_superior=80000)
                },
                "volumen": {
                    "bajo": lambda volumen: self.pertenencia_volumen_bajo(volumen, limite_inferior=1000, limite_superior=5000),
                    "medio": lambda volumen: self.pertenencia_volumen_medio(volumen, limite_inferior=5000, limite_superior=10000),
                    "alto": lambda volumen: self.pertenencia_volumen_alto(volumen, limite_inferior=10000, limite_superior=15000)
                },
                "sentimiento": {
                    "negativo": lambda sentimiento: self.pertenencia_sentimiento_negativo(sentimiento),
                    "neutro": lambda sentimiento: self.pertenencia_sentimiento_neutro(sentimiento),
                    "positivo": lambda sentimiento: self.pertenencia_sentimiento_positivo(sentimiento)
                },
                "tendencia_precio": {
                    "alcista": lambda x: 1 if x == 'alcista' else 0,
                    "bajista": lambda x: 1 if x == 'bajista' else 0,
                    "estable": lambda x: 1 if x == 'estable' else 0
                },
                "rsi": {
                    "alto": lambda x: self.pertenencia_rsi_alto(x),
                    "medio": lambda x: self.pertenencia_rsi_medio(x),
                    "bajo": lambda x: self.pertenencia_rsi_bajo(x),
                    "sobrecompra": lambda x: 1 if x > 70 else 0,
                    "sobreventa": lambda x: 1 if x < 30 else 0
                },
                "macd_tendencia": {
                    "alcista": lambda x: 1 if x == 'alcista' else 0,
                    "bajista": lambda x: 1 if x == 'bajista' else 0
                },
                "sobrecompra": {
                    "verdadero": lambda x: 1 if x else 0,
                    "falso": lambda x: 1 if not x else 0
                },
                "sobreventa": {
                    "verdadero": lambda x: 1 if x else 0,
                    "falso": lambda x: 1 if not x else 0
                },
                "bollinger": {
                    "sobrecompra": lambda x: 1 if x == 'sobrecompra' else 0,
                    "sobreventa": lambda x: 1 if x == 'sobreventa' else 0,
                    "normal": lambda x: 1 if x == 'normal' else 0
                }
            },
            "Ethereum": {
                "precio": {
                    "bajo": lambda precio: self.pertenencia_precio_bajo(precio, limite_inferior=1000, limite_superior=2000),
                    "medio": lambda precio: self.pertenencia_precio_medio(precio, limite_inferior=2000, limite_superior=3000),
                    "alto": lambda precio: self.pertenencia_precio_alto(precio, limite_inferior=3000, limite_superior=5000)
                },
                "volumen": {
                    "bajo": lambda volumen: self.pertenencia_volumen_bajo(volumen, limite_inferior=1000, limite_superior=5000),
                    "medio": lambda volumen: self.pertenencia_volumen_medio(volumen, limite_inferior=5000, limite_superior=10000),
                    "alto": lambda volumen: self.pertenencia_volumen_alto(volumen, limite_inferior=10000, limite_superior=15000)
                },
                "sentimiento": {
                    "negativo": lambda sentimiento: self.pertenencia_sentimiento_negativo(sentimiento),
                    "neutro": lambda sentimiento: self.pertenencia_sentimiento_neutro(sentimiento),
                    "positivo": lambda sentimiento: self.pertenencia_sentimiento_positivo(sentimiento)
                },
                "tendencia_precio": {
                    "alcista": lambda x: 1 if x == 'alcista' else 0,
                    "bajista": lambda x: 1 if x == 'bajista' else 0,
                    "estable": lambda x: 1 if x == 'estable' else 0
                },
                "rsi": {
                    "alto": lambda x: self.pertenencia_rsi_alto(x),
                    "medio": lambda x: self.pertenencia_rsi_medio(x),
                    "bajo": lambda x: self.pertenencia_rsi_bajo(x),
                    "sobrecompra": lambda x: 1 if x > 70 else 0,
                    "sobreventa": lambda x: 1 if x < 30 else 0
                },
                "macd_tendencia": {
                    "alcista": lambda x: 1 if x == 'alcista' else 0,
                    "bajista": lambda x: 1 if x == 'bajista' else 0
                },
                "sobrecompra": {
                    "verdadero": lambda x: 1 if x else 0,
                    "falso": lambda x: 1 if not x else 0
                },
                "sobreventa": {
                    "verdadero": lambda x: 1 if x else 0,
                    "falso": lambda x: 1 if not x else 0
                },
                "bollinger": {
                    "sobrecompra": lambda x: 1 if x == 'sobrecompra' else 0,
                    "sobreventa": lambda x: 1 if x == 'sobreventa' else 0,
                    "normal": lambda x: 1 if x == 'normal' else 0
                }
            },
            "Ripple": {
                "precio": {
                    "bajo": lambda precio: self.pertenencia_precio_bajo(precio, limite_inferior=0.5, limite_superior=1.0),
                    "medio": lambda precio: self.pertenencia_precio_medio(precio, limite_inferior=1.0, limite_superior=1.5),
                    "alto": lambda precio: self.pertenencia_precio_alto(precio, limite_inferior=1.5, limite_superior=2.0)
                },
                "volumen": {
                    "bajo": lambda volumen: self.pertenencia_volumen_bajo(volumen, limite_inferior=500, limite_superior=2000),
                    "medio": lambda volumen: self.pertenencia_volumen_medio(volumen, limite_inferior=2000, limite_superior=5000),
                    "alto": lambda volumen: self.pertenencia_volumen_alto(volumen, limite_inferior=5000, limite_superior=10000)
                },
                "sentimiento": {
                    "negativo": lambda sentimiento: self.pertenencia_sentimiento_negativo(sentimiento),
                    "neutro": lambda sentimiento: self.pertenencia_sentimiento_neutro(sentimiento),
                    "positivo": lambda sentimiento: self.pertenencia_sentimiento_positivo(sentimiento)
                },
                "tendencia_precio": {
                    "alcista": lambda x: 1 if x == 'alcista' else 0,
                    "bajista": lambda x: 1 if x == 'bajista' else 0,
                    "estable": lambda x: 1 if x == 'estable' else 0
                },
                "rsi": {
                    "alto": lambda x: self.pertenencia_rsi_alto(x),
                    "medio": lambda x: self.pertenencia_rsi_medio(x),
                    "bajo": lambda x: self.pertenencia_rsi_bajo(x),
                    "sobrecompra": lambda x: 1 if x > 70 else 0,
                    "sobreventa": lambda x: 1 if x < 30 else 0
                },
                "macd_tendencia": {
                    "alcista": lambda x: 1 if x == 'alcista' else 0,
                    "bajista": lambda x: 1 if x == 'bajista' else 0
                },
                "sobrecompra": {
                    "verdadero": lambda x: 1 if x else 0,
                    "falso": lambda x: 1 if not x else 0
                },
                "sobreventa": {
                    "verdadero": lambda x: 1 if x else 0,
                    "falso": lambda x: 1 if not x else 0
                },
                "bollinger": {
                    "sobrecompra": lambda x: 1 if x == 'sobrecompra' else 0,
                    "sobreventa": lambda x: 1 if x == 'sobreventa' else 0,
                    "normal": lambda x: 1 if x == 'normal' else 0
                }
            },
            "Litecoin": {
                "precio": {
                    "bajo": lambda precio: self.pertenencia_precio_bajo(precio, limite_inferior=100, limite_superior=200),
                    "medio": lambda precio: self.pertenencia_precio_medio(precio, limite_inferior=200, limite_superior=300),
                    "alto": lambda precio: self.pertenencia_precio_alto(precio, limite_inferior=300, limite_superior=400)
                },
                "volumen": {
                    "bajo": lambda volumen: self.pertenencia_volumen_bajo(volumen, limite_inferior=300, limite_superior=1000),
                    "medio": lambda volumen: self.pertenencia_volumen_medio(volumen, limite_inferior=1000, limite_superior=3000),
                    "alto": lambda volumen: self.pertenencia_volumen_alto(volumen, limite_inferior=3000, limite_superior=6000)
                },
                "sentimiento": {
                    "negativo": lambda sentimiento: self.pertenencia_sentimiento_negativo(sentimiento),
                    "neutro": lambda sentimiento: self.pertenencia_sentimiento_neutro(sentimiento),
                    "positivo": lambda sentimiento: self.pertenencia_sentimiento_positivo(sentimiento)
                },
                "tendencia_precio": {
                    "alcista": lambda x: 1 if x == 'alcista' else 0,
                    "bajista": lambda x: 1 if x == 'bajista' else 0,
                    "estable": lambda x: 1 if x == 'estable' else 0
                },
                "rsi": {
                    "alto": lambda x: self.pertenencia_rsi_alto(x),
                    "medio": lambda x: self.pertenencia_rsi_medio(x),
                    "bajo": lambda x: self.pertenencia_rsi_bajo(x),
                    "sobrecompra": lambda x: 1 if x > 70 else 0,
                    "sobreventa": lambda x: 1 if x < 30 else 0
                },
                "macd_tendencia": {
                    "alcista": lambda x: 1 if x == 'alcista' else 0,
                    "bajista": lambda x: 1 if x == 'bajista' else 0
                },
                "sobrecompra": {
                    "verdadero": lambda x: 1 if x else 0,
                    "falso": lambda x: 1 if not x else 0
                },
                "sobreventa": {
                    "verdadero": lambda x: 1 if x else 0,
                    "falso": lambda x: 1 if not x else 0
                },
                "bollinger": {
                    "sobrecompra": lambda x: 1 if x == 'sobrecompra' else 0,
                    "sobreventa": lambda x: 1 if x == 'sobreventa' else 0,
                    "normal": lambda x: 1 if x == 'normal' else 0
                }
            },
            "Cardano": {
                "precio": {
                    "bajo": lambda precio: self.pertenencia_precio_bajo(precio, limite_inferior=1.0, limite_superior=2.0),
                    "medio": lambda precio: self.pertenencia_precio_medio(precio, limite_inferior=2.0, limite_superior=3.0),
                    "alto": lambda precio: self.pertenencia_precio_alto(precio, limite_inferior=3.0, limite_superior=4.0)
                },
                "volumen": {
                    "bajo": lambda volumen: self.pertenencia_volumen_bajo(volumen, limite_inferior=800, limite_superior=2500),
                    "medio": lambda volumen: self.pertenencia_volumen_medio(volumen, limite_inferior=2500, limite_superior=6000),
                    "alto": lambda volumen: self.pertenencia_volumen_alto(volumen, limite_inferior=6000, limite_superior=12000)
                },
                "sentimiento": {
                    "negativo": lambda sentimiento: self.pertenencia_sentimiento_negativo(sentimiento),
                    "neutro": lambda sentimiento: self.pertenencia_sentimiento_neutro(sentimiento),
                    "positivo": lambda sentimiento: self.pertenencia_sentimiento_positivo(sentimiento)
                },
                "tendencia_precio": {
                    "alcista": lambda x: 1 if x == 'alcista' else 0,
                    "bajista": lambda x: 1 if x == 'bajista' else 0,
                    "estable": lambda x: 1 if x == 'estable' else 0
                },
                "rsi": {
                    "alto": lambda x: self.pertenencia_rsi_alto(x),
                    "medio": lambda x: self.pertenencia_rsi_medio(x),
                    "bajo": lambda x: self.pertenencia_rsi_bajo(x),
                    "sobrecompra": lambda x: 1 if x > 70 else 0,
                    "sobreventa": lambda x: 1 if x < 30 else 0
                },
                "macd_tendencia": {
                    "alcista": lambda x: 1 if x == 'alcista' else 0,
                    "bajista": lambda x: 1 if x == 'bajista' else 0
                },
                "sobrecompra": {
                    "verdadero": lambda x: 1 if x else 0,
                    "falso": lambda x: 1 if not x else 0
                },
                "sobreventa": {
                    "verdadero": lambda x: 1 if x else 0,
                    "falso": lambda x: 1 if not x else 0
                },
                "bollinger": {
                    "sobrecompra": lambda x: 1 if x == 'sobrecompra' else 0,
                    "sobreventa": lambda x: 1 if x == 'sobreventa' else 0,
                    "normal": lambda x: 1 if x == 'normal' else 0
                }
            }
        }

    # Funciones de pertenencia para 'precio'
    def pertenencia_precio_bajo(self, precio, limite_inferior, limite_superior):
        if precio < limite_inferior:
            return 1
        elif limite_inferior <= precio <= limite_superior:
            return (limite_superior - precio) / (limite_superior - limite_inferior)
        else:
            return 0

    def pertenencia_precio_medio(self, precio, limite_inferior, limite_superior):
        # Suponiendo que 'medio' es un pico en el rango medio
        if limite_inferior <= precio <= limite_superior:
            return 1
        elif limite_superior < precio < limite_superior + (limite_superior - limite_inferior):
            return (precio - limite_superior) / (limite_superior - limite_inferior)
        elif limite_inferior - (limite_superior - limite_inferior) < precio < limite_inferior:
            return (limite_inferior - precio) / (limite_superior - limite_inferior)
        else:
            return 0

    def pertenencia_precio_alto(self, precio, limite_inferior, limite_superior):
        if precio > limite_superior:
            return 1
        elif limite_inferior <= precio <= limite_superior:
            return (precio - limite_inferior) / (limite_superior - limite_inferior)
        else:
            return 0

    # Funciones de pertenencia para 'volumen'
    def pertenencia_volumen_bajo(self, volumen, limite_inferior, limite_superior):
        if volumen < limite_inferior:
            return 1
        elif limite_inferior <= volumen <= limite_superior:
            return (limite_superior - volumen) / (limite_superior - limite_inferior)
        else:
            return 0

    def pertenencia_volumen_medio(self, volumen, limite_inferior, limite_superior):
        # Suponiendo que 'medio' es un pico en el rango medio
        if limite_inferior <= volumen <= limite_superior:
            return 1
        elif limite_superior < volumen < limite_superior + (limite_superior - limite_inferior):
            return (volumen - limite_superior) / (limite_superior - limite_inferior)
        elif limite_inferior - (limite_superior - limite_inferior) < volumen < limite_inferior:
            return (limite_inferior - volumen) / (limite_superior - limite_inferior)
        else:
            return 0

    def pertenencia_volumen_alto(self, volumen, limite_inferior, limite_superior):
        if volumen > limite_superior:
            return 1
        elif limite_inferior <= volumen <= limite_superior:
            return (volumen - limite_inferior) / (limite_superior - limite_inferior)
        else:
            return 0

    # Funciones de pertenencia para 'sentimiento'
    def pertenencia_sentimiento_negativo(self, sentimiento):
        return 1 if sentimiento == 'negativo' else 0

    def pertenencia_sentimiento_neutro(self, sentimiento):
        return 1 if sentimiento == 'neutro' else 0

    def pertenencia_sentimiento_positivo(self, sentimiento):
        return 1 if sentimiento == 'positivo' else 0

    # Funciones de pertenencia para 'rsi'
    def pertenencia_rsi_alto(self, x):
        if x > 70:
            return 1
        elif x > 50:
            return (x - 50) / 20
        else:
            return 0

    def pertenencia_rsi_medio(self, x):
        if 30 < x <= 50:
            return (x - 30) / 20
        elif 50 < x <= 70:
            return (70 - x) / 20
        else:
            return 0

    def pertenencia_rsi_bajo(self, x):
        if x < 30:
            return 1
        elif x < 50:
            return (50 - x) / 20
        else:
            return 0
