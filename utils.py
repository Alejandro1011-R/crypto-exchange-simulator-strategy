
def load_rules_from_file(file_path):
    with open(file_path, 'r') as file:
        rules = file.readlines()
    return [rule.strip() for rule in rules]

# Operadores lógicos difusos
def fuzzy_and(a, b):
    return min(a, b)

def fuzzy_or(a, b):
    return max(a, b)

def fuzzy_not(a):
    return 1 - a

def boolean_to_fuzzy(value, high_confidence):
    if value == True:
        return 0.9 if high_confidence else 0.7  # Representa un "verdadero" difuso
    else:
        return 0.1 if high_confidence else 0.3  # Representa un "falso" difuso