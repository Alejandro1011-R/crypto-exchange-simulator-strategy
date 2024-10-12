from sly import Parser
#from Rules_Interpreter.rulelexer import *
#from Rules_Interpreter.ast_1 import *
from rulelexer import *
from ast_1 import *

class RuleParser(Parser):
    tokens = RuleLexer.tokens
    debugfile = 'parser.txt'
    precedence = (
        ('left', OR),
        ('left', AND),
        ('left', MULT),
    )

    @_('instruccion_list')
    def programa(self, p):
        return p.instruccion_list

    @_('instruccion')
    def instruccion_list(self, p):
        return [p.instruccion]

    @_('instruccion_list instruccion')
    def instruccion_list(self, p):
        return p.instruccion_list + [p.instruccion]

    
    @_('statement_construct')
    @_('statement_rule')
    @_('creencia_construct')
    def instruccion(self, p):
        return p
        
    # Nueva regla para reconocer "SI ERES ... ENTONCES ERES ..."
    @_('SI ERES condicion ENTONCES ERES creencia_list')
    def statement_construct(self, p):
        return ("statement_ByEdges", p.condicion, p.creencia_list)
    
    @_('SI ERES condicion ENTONCES ERES creencia_list_comp')
    def statement_construct(self, p):
        return ("statement_ByEdges", p.condicion, p.creencia_list_comp)
    
    @_('SI ERES condicion ENTONCES statement_rule_list')
    def statement_construct(self, p):
        return ("statement_ByRules", p.condicion, p.statement_rule_list)

    @_('SI ERES condicion ENTONCES statement_rule_list_comp')
    def statement_construct(self, p):
        return ("statement_ByRules", p.condicion, p.statement_rule_list_comp)
    
    @_('SI condicion ENTONCES accion')
    def statement_rule(self, p):
        return ("statement_rule", p.condicion, p.accion)

    @_('statement_rule')
    def statement_rule_list(self, p):
        return [p.statement_rule]

    @_('statement_rule_list COMA statement_rule')
    def statement_rule_list(self, p):
        return p.statement_rule_list + [p.statement_rule]
    

    @_('ELIMINAR statement_rule_list PUNTOCOMA statement_rule_list')
    def statement_rule_list_comp(self, p):
        return [("eliminar",p.statement_rule_list0)] + p.statement_rule_list1
    
    # Nueva regla para reconocer "SI ERES ... ENTONCES ERES ..."
    @_('CUANDO condicion ENTONCES creencia_list')
    def creencia_construct(self, p):
        return ("creencia_construct", p.condicion, p.creencia_list)
    
    @_('creencia LCOR COTA RCOR')
    def creencia_list(self, p):
        return [(p.creencia, p.COTA )]
    

    @_('creencia_list COMA creencia LCOR COTA RCOR')
    def creencia_list(self, p):
        return p.creencia_list + [(p.creencia, p.COTA )]
    
    @_('creencia')
    def creencia_list(self, p):
        return [p.creencia]
    
    @_('NO creencia')
    def creencia_list(self, p):
        return [("NO", p.creencia)]

    @_('creencia_list COMA creencia')
    def creencia_list(self, p):
        return p.creencia_list + [p.creencia]

    @_('ELIMINAR creencia_list PUNTOCOMA creencia_list')
    def creencia_list_comp(self, p):
        return [("eliminar",p.creencia_list0)] + p.creencia_list1
    
    @_('condicion AND condicion')
    def condicion(self, p):
        return (p.condicion0, 'AND', p.condicion1)

    @_('condicion OR condicion')
    def condicion(self, p):
        return (p.condicion0, 'OR', p.condicion1)

    #@_('condicion')
    @_('LPAREN condicion RPAREN')
    def condicion(self, p):
        return p.condicion
    
    
    @_('expresion comparador expresion',
       'expresion',
       'creencia',    # Nueva opción para una creencia
       'NO creencia') # Nueva opción para NO creencia
    def condicion(self, p):
        if len(p) == 3:  # Si es la forma 'expresion comparador expresion'
            return ("comparador", p.expresion0, p.comparador, p.expresion1)
        elif len(p) == 1:  # Si es una creencia
            return p[0]
        elif len(p) == 2:  # Si es 'NO creencia'
            return ("NO", p.creencia)  # Puedes ajustar el manejo de "NO" según sea necesario
        
    @_('ID')
    def creencia(self, p):
        return ("creencia",p[0])
    

    @_('ES', 'NO_ES', 'MAYOR_QUE', 'MENOR_QUE', 'MAYOR_IGUAL_QUE', 'MENOR_IGUAL_QUE')
    def comparador(self, p):
        return ("comparador", p[0])

    @_('variable MULT NUMBER')
    def expresion(self, p):
        return ("multiplicar", p.variable, p.NUMBER)

    @_('variable')
    def expresion(self, p):
        return p.variable
    
    @_('NUMBER')
    def expresion(self, p):
        return ("number", p[0])

    @_('PRECIO', 'CAPITAL', 'CONOCIMIENTO','EXPERIENCIA','SENTIMIENTO','ALTO', 'MEDIO', 'BAJO', 'POSITIVO', 'NEUTRO', 'NEGATIVO','ANALIZAR_GRAFICO NUMBER')
    @_('BOLLINGER', 'SOBRECOMPRA', 'SOBREVENTA', 'NORMAL', 'SMATENDENCIA',  'ALCISTA', 'BAJISTA', 'MACDTENDENCIA', 'SMA5', 'SMA10', 'RSI', 'MACD')
    def variable(self, p):
        if len(p)==1:
            return ("variable",p[0])
        elif len(p)==2:
            return ("grafico",p[1])

    @_('COMPRAR accion_capital')
    def accion(self, p):
        return ("accion", "COMPRAR", p.accion_capital)

    @_('VENDER accion_cantidad')
    def accion(self, p):
        return ("accion", "VENDER", p.accion_cantidad)

    @_('MANTENER')
    def accion(self, p):
        return ("accion", "MANTENER", None)

    @_('CAPITAL MULT NUMBER')
    def accion_capital(self, p):
        return ("accion_capital","CAPITAL", p.NUMBER)

    @_('CAPITAL')
    def accion_capital(self, p):
        return ("accion_capital","CAPITAL")

    @_('TODO MULT NUMBER')
    def accion_cantidad(self, p):
        return ("accion_cantidad","TODO", p.NUMBER)

    @_('TODO')
    def accion_cantidad(self, p):
        return ("accion_cantidad","TODO")
    
    @_('ID LPAREN RPAREN')
    def funcion(self, p):
        return ('funcion', p.ID, [])

    @_('ID LPAREN parametro_list RPAREN')
    def funcion(self, p):
        return ('funcion', p.ID, p.parametro_list)
    
    @_('expresion')
    def parametro(self, p):
        return p.expresion

    @_('parametro')
    def parametro_list(self, p):
        return [p.parametro]

    @_('parametro_list COMA parametro')
    def parametro_list(self, p):
        return p.parametro_list + [p.parametro]


    @_('funcion')
    def expresion(self, p):
        return p.funcion
    
    def error(self, p):
        if p:
            print(f"Error de sintaxis en el token '{p.value}'")
        else:
            print("Error de sintaxis en la entrada (fin inesperado)")
 
def imprimir_resultado(resultado, nivel=0):
    """Imprime el resultado del parser de forma recursiva, considerando las etiquetas."""
    indentacion = '  ' * nivel  # Indentación para representar la jerarquía

    if isinstance(resultado, tuple):
        # Imprime la etiqueta (tipo)
        etiqueta = resultado[0]
        print(f"{indentacion}{etiqueta}:")

         # Manejo específico según la etiqueta
        if etiqueta == "statement_construct":
            condicion = resultado[1]
            acciones = resultado[2]
            print(f"{indentacion}  Condición: {condicion}")
            print(f"{indentacion}  Acciones:")
            for accion in acciones:
                imprimir_resultado(accion, nivel + 2)

        elif etiqueta == "statement_rule":
            condicion = resultado[1]
            accion = resultado[2]
            print(f"{indentacion}  Condición: {condicion}")
            print(f"{indentacion}  Acción: {accion}")

        elif etiqueta == "creencia":
            creencia_tipo = resultado[1]
            valor = resultado[2] if len(resultado) > 2 else None
            print(f"{indentacion}  Tipo de creencia: {creencia_tipo}")
            if valor:
                print(f"{indentacion}  Valor: {valor}")

        elif etiqueta == "comparador":
            comparador_tipo = resultado[1]
            print(f"{indentacion}  Comparador: {comparador_tipo}")

        elif etiqueta == "accion":
            accion_tipo = resultado[1]
            detalles_accion = resultado[2] if len(resultado) > 2 else None
            print(f"{indentacion}  Tipo de acción: {accion_tipo}")
            if detalles_accion:
                imprimir_resultado(detalles_accion, nivel + 2)

        # Agrega más condiciones aquí para otras etiquetas según sea necesario

        else:
            # Si no hay un manejo específico, imprime los elementos restantes
            for elemento in resultado[1:]:
                imprimir_resultado(elemento, nivel + 1)

    elif isinstance(resultado, list):
        # Si es una lista, llama a la función recursivamente para cada elemento
        for elemento in resultado:
            imprimir_resultado(elemento, nivel)
    else:
        # Imprime el valor directamente
        print(f"{indentacion}{resultado}")

# # Ejemplo de uso con el resultado del parser
# if name == 'main':
#     lex = RuleLexer()
#     par = RuleParser()

#     rules = """SI ERES NO novato Y experto ENTONCES SI novato ENTONCES COMPRAR capital , SI experto ENTONCES COMPRAR capital
#            SI ERES novato Y experto ENTONCES ELIMINAR SI novato ENTONCES COMPRAR capital, SI novato ENTONCES COMPRAR capital; SI experto ENTONCES COMPRAR capital
#            SI ERES NO novato Y experto ENTONCES ERES novato [0.5 <= X < 0.5] , avanzado [0.5 < X <= 0.5] , experto [0.5 < X < 0.5]
#            SI ERES novato Y experto ENTONCES ERES ELIMINAR novato, avanzado; experto [0.5 <= X < 0.5]
#            """

#     result = par.parse(lex.tokenize(rules))

#     # Imprimir el resultado del parser
#     imprimir_resultado(result)




# rules = """SI ERES NO novato Y experto ENTONCES SI novato ENTONCES COMPRAR capital , SI experto ENTONCES COMPRAR capital 
#            SI ERES novato Y experto ENTONCES ELIMINAR SI novato ENTONCES COMPRAR capital, SI novato ENTONCES COMPRAR capital; SI experto ENTONCES COMPRAR capital
#            SI ERES NO novato Y experto ENTONCES ERES novato [0.5 <= X < 0.5] , avanzado [0.5 < X <= 0.5] , experto [0.5 < X < 0.5]
#            SI ERES novato Y experto ENTONCES ERES ELIMINAR novato, avanzado; experto [0.5 <= X < 0.5]
#            """

if __name__ == '__main__':
    lex = RuleLexer()
    par = RuleParser()

    rules = """SI ERES NO novato Y experto ENTONCES SI novato ENTONCES COMPRAR capital , SI experto ENTONCES COMPRAR capital 
            SI ERES novato Y experto ENTONCES ELIMINAR SI novato ENTONCES COMPRAR capital, SI novato ENTONCES COMPRAR capital; SI experto ENTONCES COMPRAR capital
            SI ERES NO novato Y experto ENTONCES ERES novato [0.5 <= X < 0.5] , avanzado [0.5 < X <= 0.5] , experto [0.5 < X < 0.5]
            SI ERES novato Y experto ENTONCES ERES ELIMINAR novato, avanzado; experto [0.5 <= X < 0.5]
            SI ERES novato ENTONCES ERES impulsivo,tendencia, terco
            SI ERES avanzado ENTONCES ERES tendencia , analista , noticias
            SI ERES avanzado ENTONCES ERES NO novato

            
            SI ERES MIEDOSO ENTONCES ERES NO AVARICIOSO # ver regla MEjor poner NO y en la parte Lógica Negar
            SI ERES AVARICIOSO ENTONCES ERES NO MIEDOSO # [1.0 == X]
            SI ERES MIEDOSO O TERCO Y AVARICIOSO ENTONCES ERES NO ALEGRE
            SI ERES MIEDOSO Y NERVIOSO ENTONCES SI historia_precio(20) mayor que 5 ENTONCES COMPRAR capital * 0.20 , SI historia_precio(20) ENTONCES VENDER todo
            SI ERES AVARICIOSO Y TERCO ENTONCES SI historia_precio(20) ENTONCES COMPRAR capital , SI precio mayor que 500 ENTONCES VENDER todo
            CUANDO random() menor que 0.20 ENTONCES TERCO
            CUANDO random() mayor que 0.50 ENTONCES NERVIOSO
            CUANDO capital mayor que 5000 ENTONCES AVARICIOSO
            CUANDO capital menor que 100  ENTONCES MIEDOSO
            CUANDO sentimiento es alto ENTONCES ALEGRE, TONTO
           """
    result = par.parse(lex.tokenize(rules))
    for instruction in result:
        print(instruction)
    # Imprimir el resultado del parser
    #imprimir_resultado(result)