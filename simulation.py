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

class Simulation:

    def __init__(self, brokers,price_history,rule_interpreter):
        self.brokers = brokers
        self.price_history = price_history
        self.rule_interpreter = rule_interpreter

    def simulate_market(self, num_minutes=1):
        for _ in range(num_minutes):
            current_price = self.price_history[-1] * (1 + random.uniform(-0.001, 0.001))  # pequeña variación del precio
            for broker in self.brokers:
                broker.decide(current_price, self.price_history, self.rule_interpreter)
            self.price_history.append(current_price)
    
    # Algoritmo de predicciones usando Monte Carlo
    def monte_carlo_prediction(self,current_price, num_simulations=1000, num_minutes=1):
        predictions = []
        for _ in range(num_simulations):
            price = current_price
            for _ in range(num_minutes):
                price *= (1 + random.uniform(-0.001, 0.001))
            predictions.append(price)
        return np.mean(predictions), np.std(predictions)

    # Generar noticias y tuits ficticios
    def generate_news_and_tweets(self):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        news = f"News at {timestamp}: Market is volatile."
        tweet = f"Tweet at {timestamp}: #CryptoMarket is moving!"
        return news, tweet

    # Inicialización de la aplicación Dash
    def run(self):
        app = dash.Dash(__name__)

        app.layout = html.Div([
            html.H1("Simulación del Mercado de Criptomonedas"),
            dcc.Interval(id='interval-component', interval=1000, n_intervals=0),
            dcc.Graph(id='price-graph'),
            html.Div(id='news-tweets', children=[
                html.H2("Noticias y Tweets"),
                html.Div(id='news'),
                html.Div(id='tweets')
            ]),
            html.Div(id='prediction', children=[
                html.H2("Predicciones de Precio"),
                html.Div(id='price-prediction')
            ])
        ])

        @app.callback(
            Output('price-graph', 'figure'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_graph_live(n):
            self.simulate_market()
            data = go.Scatter(x=list(range(len(self.price_history))), y= self.price_history, mode='lines', name='Precio de la Criptomoneda')
            return {'data': [data], 'layout': go.Layout(title='Simulación del Precio de la Criptomoneda', xaxis={'title': 'Minutos'}, yaxis={'title': 'Precio'})}
        
        @app.callback(
            Output('news', 'children'),
            Output('tweets', 'children'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_news_tweets(n):
            news, tweet = self.generate_news_and_tweets()
            return news, tweet

        @app.callback(
            Output('price-prediction', 'children'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_prediction(n):
            current_price = self.price_history[-1]
            mean_prediction, std_prediction = self.monte_carlo_prediction(current_price)
            return f"Predicción del precio para el próximo minuto: {mean_prediction:.2f} ± {std_prediction:.2f}"

        app.run_server(debug=True)