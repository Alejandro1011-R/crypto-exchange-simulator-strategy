import numpy as np
import random

class RuleInterpreter:
    def __init__(self, market_data):
        self.market_data = market_data

    def evaluate_condition(self, condition, agent, price, price_history):
        try:
            context = {
                'agent': agent,
                'market_data': self.market_data,
                'np': np,
                'random': random,
                'price': price,
                'price_history': price_history
            }
            return eval(condition, {}, context)
        except Exception as e:
            print(f"Error evaluating condition '{condition}': {e}")
            return False

    def execute_action(self, action, agent, price, price_history):
        try:
            context = {
                'agent': agent,
                'market_data': self.market_data,
                'np': np,
                'price': price,
                'price_history': price_history
            }
            exec(action, {}, context)
        except Exception as e:
            print(f"Error executing action '{action}': {e}")

    def run_rules(self, rules, agent, price, price_history):
        for rule in rules:
            condition, action = rule.split(' THEN ')
            condition = condition.replace('IF ', '').strip()
            action = action.strip()
            if self.evaluate_condition(condition, agent, price, price_history):
                self.execute_action(action, agent, price, price_history)