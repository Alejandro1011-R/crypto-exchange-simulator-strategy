from sly import Parser
from Rules_Interpreter.rulelexer import *
from Rules_Interpreter.ast_1 import *

class RuleParser(Parser):
    tokens = RuleLexer.tokens

    precedence = (
        ('left', OR),
        ('left', AND),
        ('left', MULT),
    )

    # Nueva regla para reconocer "SI ERES ... ENTONCES ERES ..."
    @_('SI ERES condiciones ENTONCES ERES condiciones')
    def statement_belief_to_belief(self, p):
        return StatementNode(p.condiciones, p.condiciones)
    

    @_('SI ERES condiciones TIENES_LA_ESTRATEGIA statement')
    def statement_belief_strategy(self, p):
        return "StatementNode(p.condiciones, p.statement)"

    @_('SI condiciones ENTONCES accion')
    def statement(self, p):
        return StatementNode(p.condiciones, p.accion)

    @_('condicion AND condiciones')
    def condiciones(self, p):
        return ConditionNode(p.condicion, 'AND', p.condiciones)

    @_('condicion OR condiciones')
    def condiciones(self, p):
        return ConditionNode(p.condicion, 'OR', p.condiciones)

    @_('condicion')
    def condiciones(self, p):
        return p.condicion

    @_('expresion comparador expresion',
       'creencia',    # Nueva opción para una creencia
       'NO creencia') # Nueva opción para NO creencia
    def condicion(self, p):
        if len(p) == 3:  # Si es la forma 'expresion comparador expresion'
            return ConditionNode(p.expresion0, p.comparador, p.expresion1)
        elif len(p) == 1:  # Si es una creencia
            return p.creencia
        elif len(p) == 2:  # Si es 'NO creencia'
            return ConditionNode("NO", p.creencia)  # Puedes ajustar el manejo de "NO" según sea necesario
        
    @_('NOVATO', 'AVANZADO', 'EXPERTO', 'IMPULSIVO', 'TENDENCIA', 'NOTICIAS','INVERSOR','ANALISTA','FASTTRADER','TERCO')
    def creencia(self, p):
        return p[0]

    @_('ES', 'NO_ES', 'MAYOR_QUE', 'MENOR_QUE', 'MAYOR_IGUAL_QUE', 'MENOR_IGUAL_QUE')
    def comparador(self, p):
        return p[0]

    @_('variable MULT NUMBER')
    def expresion(self, p):
        return ExpressionNode(p.variable, p.NUMBER)

    @_('variable')
    def expresion(self, p):
        return ExpressionNode(p.variable)
    
    @_('NUMBER')
    def expresion(self, p):
        return ExpressionNode(p[0])

    @_('PRECIO', 'CAPITAL', 'CONOCIMIENTO','EXPERIENCIA','SENTIMIENTO','ALTO', 'MEDIO', 'BAJO', 'POSITIVO', 'NEUTRO', 'NEGATIVO','ANALIZAR_GRAFICO NUMBER')
    def variable(self, p):
        if len(p)==1:
            return p[0]
        elif len(p)==2:
            return ("pon algo aqui mugeeeeeel esto es para la funcion d analizar el grafico los desde los ciclos anteriores",p[1])

    @_('COMPRAR accion_capital')
    def accion(self, p):
        return ActionNode("COMPRAR", p.accion_capital)

    @_('VENDER accion_cantidad')
    def accion(self, p):
        return ActionNode("VENDER", p.accion_cantidad)

    @_('MANTENER')
    def accion(self, p):
        return ActionNode("MANTENER", None)

    @_('CAPITAL MULT NUMBER')
    def accion_capital(self, p):
        return ExpressionNode("CAPITAL", p.NUMBER)

    @_('CAPITAL')
    def accion_capital(self, p):
        return ExpressionNode("CAPITAL")

    @_('TODO MULT NUMBER')
    def accion_cantidad(self, p):
        return ExpressionNode("TODO", p.NUMBER)

    @_('TODO')
    def accion_cantidad(self, p):
        return ExpressionNode("TODO")

    def error(self, p):
        if p:
            print(f"Error de sintaxis en el token '{p.value}'")
        else:
            print("Error de sintaxis en la entrada (fin inesperado)")