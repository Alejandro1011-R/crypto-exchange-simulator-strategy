import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import numpy as np
import random
import pandas as pd
from datetime import datetime

from rules_interpreter import RuleInterpreter
from agents import Agent
from utils import *
from simulation import Simulation



# Simulación del mercado



# Cargar reglas desde archivos de texto
rules_buy_low_sell_high = load_rules_from_file('rules_buy_low_sell_high.txt')
rules_momentum = load_rules_from_file('rules_momentum.txt')

# Crear brokers con diferentes estrategias
brokers = [
    Agent('Broker 1', rules_buy_low_sell_high),
    Agent('Broker 2', rules_momentum)
]

# Variables globales para la simulación
initial_price = 10000  # precio inicial de la criptomoneda
price_history = [initial_price]
rule_interpreter = RuleInterpreter(price_history)



simulation = Simulation(brokers,price_history,rule_interpreter)
simulation.run()
