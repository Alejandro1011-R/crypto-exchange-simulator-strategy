from Rules_Interpreter.rulelexer import RuleLexer
from Rules_Interpreter.ruleparser import RuleParser
from Rules_Interpreter.ruleinterpreter import RuleInterpreter

context = {
    "pertenencia_precio_bajo": lambda precio, limite_inferior, limite_superior: 1 if precio < limite_inferior else (limite_superior - precio) / (limite_superior - limite_inferior) if limite_inferior <= precio <= limite_superior else 0,
    "pertenencia_precio_medio": lambda precio, limite_inferior, limite_superior: 1 if limite_inferior <= precio <= limite_superior else (precio - limite_superior) / (limite_superior - limite_inferior) if limite_superior < precio < limite_superior + (limite_superior - limite_inferior) else (limite_inferior - precio) / (limite_superior - limite_inferior) if limite_inferior - (limite_superior - limite_inferior) < precio < limite_inferior else 0,
    "pertenencia_precio_alto": lambda precio, limite_inferior, limite_superior: 1 if precio > limite_superior else (precio - limite_inferior) / (limite_superior - limite_inferior) if limite_inferior <= precio <= limite_superior else 0,
    
    "pertenencia_volumen_bajo": lambda volumen, limite_inferior, limite_superior: 1 if volumen < limite_inferior else (limite_superior - volumen) / (limite_superior - limite_inferior) if limite_inferior <= volumen <= limite_superior else 0,
    "pertenencia_volumen_medio": lambda volumen, limite_inferior, limite_superior: 1 if limite_inferior <= volumen <= limite_superior else (volumen - limite_superior) / (limite_superior - limite_inferior) if limite_superior < volumen < limite_superior + (limite_superior - limite_inferior) else (limite_inferior - volumen) / (limite_superior - limite_inferior) if limite_inferior - (limite_superior - limite_inferior) < volumen < limite_inferior else 0,
    "pertenencia_volumen_alto": lambda volumen, limite_inferior, limite_superior: 1 if volumen > limite_superior else (volumen - limite_inferior) / (limite_superior - limite_inferior) if limite_inferior <= volumen <= limite_superior else 0,

    "pertenencia_sentimiento_negativo": lambda sentimiento: 1 if sentimiento == 'negativo' else 0,
    "pertenencia_sentimiento_neutro": lambda sentimiento: 1 if sentimiento == 'neutro' else 0,
    "pertenencia_sentimiento_positivo": lambda sentimiento: 1 if sentimiento == 'positivo' else 0,

    "pertenencia_rsi_alto": lambda x: 1 if x > 70 else (x - 50) / 20 if x > 50 else 0,
    "pertenencia_rsi_medio": lambda x: (x - 30) / 20 if 30 < x <= 50 else (70 - x) / 20 if 50 < x <= 70 else 0,
    "pertenencia_rsi_bajo": lambda x: 1 if x < 30 else (50 - x) / 20 if x < 50 else 0,


    "precio": 0,
    "sentimiento": 0,
    

    "tendencia_precio_alcista": lambda x: 1 if x == 'alcista' else 0,
    "tendencia_precio_bajista": lambda x: 1 if x == 'bajista' else 0,
    "tendencia_precio_estable": lambda x: 1 if x == 'estable' else 0,

    "rsi_alto": lambda x: pertenencia_rsi_alto(x),
    "rsi_medio": lambda x: pertenencia_rsi_medio(x),
    "rsi_bajo": lambda x: pertenencia_rsi_bajo(x),
    "rsi_sobrecompra": lambda x: 1 if x > 70 else 0,
    "rsi_sobreventa": lambda x: 1 if x < 30 else 0,
    
    "beliefs" : {
        'novato': 0.9,
        'experto': 0.1,
        'miedo': 0.1,
        'avaricioso': 0.9,
        "sma_tendendia": 0
    }
}

if __name__ == '__main__':
    lex = RuleLexer()
    par = RuleParser()
    int = RuleInterpreter()



        
    rules = """SI miedo Y sma_tendendia es 0 ENTONCES COMPRAR capital
               SI avaricioso Y precio menor que 500 ENTONCES COMPRAR capital
"""
    
    result = par.parse(lex.tokenize(rules))
    print(result)
    for instruction in result:
        print(int.evaluate(instruction, context))
