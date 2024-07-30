
def load_rules_from_file(file_path):
    with open(file_path, 'r') as file:
        rules = file.readlines()
    return [rule.strip() for rule in rules]