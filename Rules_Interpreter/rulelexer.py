from sly import Lexer

class RuleLexer(Lexer):
    tokens = { 
            SI,ERES ,ENTONCES,TIENES_LA_ESTRATEGIA, AND, OR,NO, VENDER, MANTENER, COMPRAR ,  
            SENTIMIENTO, PRECIO,CONOCIMIENTO,EXPERIENCIA,ANALIZAR_GRAFICO,
            NOVATO,AVANZADO,EXPERTO,IMPULSIVO,TENDENCIA,
            INVERSOR,ANALISTA,FASTTRADER,TERCO,NOTICIAS,
            ALTO, MEDIO, BAJO, POSITIVO, NEUTRO, NEGATIVO,
            ES, NO_ES, MAYOR_QUE, MENOR_QUE, MAYOR_IGUAL_QUE, MENOR_IGUAL_QUE,
            CAPITAL, TODO, NUMBER,  MULT 
        }
    
    # Palabras clave
    SI = r'SI'
    ERES=r'ERES'
    ENTONCES = r'ENTONCES'
    TIENES_LA_ESTRATEGIA=r'TIENES_LA_ESTRATEGIA'
    AND = r'Y'
    OR = r'O'
    NO= r'NO'

    #tokens de creencias
    NOVATO=r'novato'
    AVANZADO=r'avanzado'
    EXPERTO=r'experto'
    IMPULSIVO=r'impulsivo'
    TENDENCIA=r'tendencia'
    NOTICIAS=r'noticias'
    INVERSOR=r'inversor'
    ANALISTA=r'analista'
    FASTTRADER=r'fasttrader'
    TERCO=r'terco'

    # Tokens específicos para las variables financieras
    CAPITAL = r'capital'
    TODO = r'todo'
    PRECIO = r'precio'
    CONOCIMIENTO=r'conocimiento'
    EXPERIENCIA=r'experiencia'
    ANALIZAR_GRAFICO=r'Analizar\s+Grafico'

    # Tokens para sentimiento y valores
    SENTIMIENTO = r'sentimiento'
    ALTO = r'alto'
    MEDIO = r'medio'
    BAJO = r'bajo'
    POSITIVO = r'positivo'
    NEUTRO = r'neutro'
    NEGATIVO = r'negativo'
    
    # Comparadores (es, no es, mayor que, etc.)
    ES = r'es'
    NO_ES = r'no\s+es'
    MAYOR_QUE = r'mayor\s+que'
    MENOR_QUE = r'menor\s+que'
    MAYOR_IGUAL_QUE = r'mayor\s+o\s+igual\s+que'
    MENOR_IGUAL_QUE = r'menor\s+o\s+igual\s+que'
    
    # Acciones permitidas: vender, mantener, comprar
    VENDER = r'VENDER'
    MANTENER = r'MANTENER'
    COMPRAR = r'COMPRAR'

    # Token para multiplicación
    MULT = r'\*'
    
    # Token para números (incluye decimales)
    NUMBER = r'\d+(\.\d+)?'

    # Ignorar espacios en blanco y tabs
    ignore = ' \t'
    
    # Captura nuevas líneas para contar
    @_(r'\n+')
    def newline(self, t):
        self.lineno += len(t.value)

    # Ignora comentarios
    ignore_comment = r'\#.*'
    
    # Manejo de errores
    def error(self, t):
        self.index += 1