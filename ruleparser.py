from sly import Parser
from rulelexer import *

class RuleParser(Parser):
    
    debugfile='debug.txt'

    tokens = RuleLexer.tokens

    precedence = (
        ('left', OR),
        ('left', AND),
        ('left', MULT),  
    )

    # Regla principal: Sentencia completa SI...ENTONCES
    @_('SI condiciones ENTONCES accion')
    def statement(self, p):
        return f"Si {p.condiciones} entonces {p.accion}"

     # Regla para condiciones compuestas con AND/OR
    @_('condicion AND condiciones')
    def condiciones(self, p):
        return f"{p.condicion} y {p.condiciones}"

    @_('condicion OR condiciones')
    def condiciones(self, p):
        return f"{p.condicion} o {p.condiciones}"

    # Regla para una sola condición
    @_('condicion')
    def condiciones(self, p):
        return p.condicion

    # Regla para cada condición con comparadores
    @_('expresion comparador expresion')
    def condicion(self, p):
        return f"{p.expresion0} {p.comparador} {p.expresion1}"

    # Comparadores: "es", "no es", "mayor que", etc.
    @_('ES', 'NO_ES', 'MAYOR_QUE', 'MENOR_QUE', 'MAYOR_IGUAL_QUE', 'MENOR_IGUAL_QUE')
    def comparador(self, p):
        return p[0]  # Retorna el comparador como tal

    # Expresiones con variables y multiplicaciones
    @_('variable MULT NUMBER')
    def expresion(self, p):
        return f"{p.variable} * {p.NUMBER}"

    @_('variable')
    def expresion(self, p):
        return p.variable

    # Variables financieras (excluyendo CANTIDAD_COMPRADA)
    @_('PRECIO', 'PRECIO_COMPRA', 'CAPITAL', 'SENTIMIENTO','ALTO', 'MEDIO', 'BAJO', 'POSITIVO', 'NEUTRO', 'NEGATIVO')
    def variable(self, p):
        return p[0]

    # Acción a realizar: COMPRAR, VENDER o MANTENER
    @_('COMPRAR accion_capital')
    def accion(self, p):
        return f"comprar {p.accion_capital}"

    @_('VENDER accion_cantidad')
    def accion(self, p):
        return f"vender {p.accion_cantidad}"

    @_('MANTENER')
    def accion(self, p):
        return "mantener"

    # Expresiones válidas en las acciones COMPRAR (solo CAPITAL)
    @_('CAPITAL MULT NUMBER')
    def accion_capital(self, p):
        return f"{p.CAPITAL} * {p.NUMBER}"

    @_('CAPITAL')
    def accion_capital(self, p):
        return p.CAPITAL

    # Expresiones válidas en las acciones VENDER (incluyendo CANTIDAD_COMPRADA)
    @_('CANTIDAD_COMPRADA MULT NUMBER')
    def accion_cantidad(self, p):
        return f"{p.CANTIDAD_COMPRADA} * {p.NUMBER}"

    @_('TODO MULT NUMBER')
    def accion_cantidad(self, p):
        return f"{p.TODO} * {p.NUMBER}"
    
    @_('CANTIDAD_COMPRADA')
    def accion_cantidad(self, p):
        return p.CANTIDAD_COMPRADA

    @_('TODO')
    def accion_cantidad(self, p):
        return p.TODO
    
    # Manejo de errores
    def error(self, p):
        if p:
            print(f"Error de sintaxis en el token '{p.value}'")
        else:
            print("Error de sintaxis en la entrada (fin inesperado)")