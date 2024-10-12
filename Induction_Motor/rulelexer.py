from sly import Lexer

class RuleLexer(Lexer):
    tokens = {
            SI,ERES ,ENTONCES, AND, OR,NO, VENDER, MANTENER, COMPRAR ,
            SENTIMIENTO, PRECIO,CONOCIMIENTO,EXPERIENCIA,ANALIZAR_GRAFICO,
            ALTO, MEDIO, BAJO, POSITIVO, NEUTRO, NEGATIVO,
            ES, NO_ES, MAYOR_QUE, MENOR_QUE, MAYOR_IGUAL_QUE, MENOR_IGUAL_QUE,
            CAPITAL, TODO, NUMBER,  MULT, LPAREN, RPAREN, COMA, ELIMINAR, PUNTOCOMA, LCOR, RCOR, COTA, ID, CUANDO,
            BOLLINGER, SOBRECOMPRA, SOBREVENTA, NORMAL, SMATENDENCIA,  ALCISTA, BAJISTA, MACDTENDENCIA, SMA5, SMA10, RSI, MACD
        }

    # Palabras clave
    SI = r'SI'
    ERES=r'ERES'
    ENTONCES = r'ENTONCES'
    ELIMINAR = r'ELIMINAR'
    AND = r'Y'
    OR = r'O'
    NO= r'NO'
    CUANDO= r'CUANDO'

    LPAREN = r'\('
    RPAREN = r'\)'
    COMA  = r','
    PUNTOCOMA= r';'

    
    
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

    BOLLINGER = r'bollinger'
    SOBRECOMPRA = r'sobrecompra' 

    SOBREVENTA = r'sobreventa' 
    NORMAL = r'normal'
    SMATENDENCIA = r'sma_tendencia'
    ALCISTA = r'alcista'
                
    BAJISTA = r'bajista'
    MACDTENDENCIA = r'macd_tendencia'
    SMA5 = r'sma_5'  
    SMA10 = r'sma_10'
    RSI = r'rsi'
    MACD = r'macd'


    # Token para multiplicación
    MULT = r'\*'

    #COTA = r'\[\s*(?:(?P<limite_inferior>-?\d+(\.\d+)?)\s*(<|<=)\s*X\s*(<|<=)\s*(?P<limite_superior>-?\d+(\.\d+)?)|X\s*(==|!=)\s*(-?\d+(\.\d+)?)|\s*X\s*(>|>=)\s*(?P<limite_inferior>-?\d+(\.\d+)?)\s*(<|<=)\s*X\s*(>|>=)\s*(?P<limite_superior>-?\d+(\.\d+)?)\s*)\]'
    LCOR = r'\['
    RCOR = r'\]'
    COTA = r'\d+(\.\d+)? (<|<=) X (<|<=) \d+(\.\d+)?|X (==|!=) \d+(\.\d+)?'
    # Token para números (incluye decimales)
    NUMBER = r'\d+(\.\d+)?'
    
    ID = r'[a-zA-Z_][a-zA-Z0-9_]*'

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
        print(t)
        self.index += 1


rules = """SI ERES novato ENTONCES ERES impulsivo Y tendencia Y terco
        SI ERES avanzado ENTONCES ERES tendencia Y analista Y noticias
        SI ERES experto ENTONCES ERES fasttrader O inversor
        SI ERES avanzado ENTONCES ERES NO novato
        SI ERES novato Y conocimiento es medio ENTONCES ERES avanzado
        SI ERES novato Y experiencia es medio ENTONCES ERES noticias
        SI ERES novato Y conocimiento es alto ENTONCES ERES experto
        SI ERES avanzado Y conocimiento es alto ENTONCES ERES experto
        SI ERES avanzado Y experiencia es alto ENTONCES ERES fasttrader O inversor"""

rules = "CUANDO sentimiento ES alto ENTONCES ALEGRE"

if __name__ == '__main__':
    lex = RuleLexer()

    result = lex.tokenize(rules)
    for r in result:
        print(r)

