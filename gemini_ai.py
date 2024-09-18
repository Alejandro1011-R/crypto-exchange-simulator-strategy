import os
import time
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from dotenv import load_dotenv
from messages import CryptoTradingAgent
import concurrent.futures
import random
import numpy as np

MAX_RETRIES = 5  # Número máximo de intentos para la API de Gemini

class SentimentAnalyzer:
    def __init__(self, config_file='.env'):
        # Cargar las variables de entorno desde el archivo .env
        load_dotenv(config_file)

        # Configurar la API de Gemini AI utilizando la clave de API
        self.api_key = os.environ['GENAI_API_KEY']
        genai.configure(api_key=self.api_key)

        # Configurar las opciones de seguridad para la API de Gemini
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        # Inicializar el modelo generativo de Gemini AI con instrucciones específicas
        self.chat = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            safety_settings=safety_settings,
            system_instruction=[
                """
                You are a crypto trading expert. Analyze the following message and rate its sentiment
                on a scale from -2 (very bearish) to 2 (very bullish). Consider these factors:
                1. Market trends mentioned
                2. Technical analysis indicators
                3. Fundamental news about cryptocurrencies
                4. Overall tone and confidence of the message
                5. If the message is not relevant or not about cryptocurrencies the sentiment is 0
                Only return the numeric score without any explanation.
                """,
                "You must only return the numeric score without any explanation. Do not return anything else but a number"
            ]
        ).start_chat(history=[])

    def analyze(self, message):
        # Analizar el mensaje utilizando Gemini AI y devolver el puntaje de sentimiento
        gemini_score = int(float(self.get_gemini_score(message).text.strip()))
        return gemini_score

    def get_gemini_score(self, message, retry_count=0):
        # Obtener el puntaje de sentimiento de Gemini AI
        try:
            response = self.chat.send_message(f'Only return the number of the sentiment of the following message:\n\n{message}')
            return response
        except genai.types.BlockedPromptException as e:
            # Manejar la excepción si la solicitud es bloqueada
            print(f"The prompt was blocked: {e}")
            return None
        except ResourceExhausted as e:
            # Reintentar si se alcanza el límite de recursos
            if retry_count < MAX_RETRIES:
                time.sleep(2 ** retry_count)  # Implementar un retroceso exponencial
                return self.get_gemini_score(message, retry_count + 1)
            else:
                raise e

    def evaluate_message(self, message, score, num_comments, max_score, max_comments):
        # Evaluar el mensaje combinando el sentimiento con otros factores
        sentiment = self.analyze(message)

        # Normalizar el puntaje y el número de comentarios
        normalized_score = self.sigmoid_normalize(score, max_score)
        normalized_comments = self.sigmoid_normalize(num_comments, max_comments)

        # Parámetros de ajuste para ponderación
        alpha = 0.3
        gamma = 1.2

        # Calcular el sentimiento ponderado
        weighted_sentiment = sentiment * (1 + gamma * normalized_score + alpha * normalized_comments)

        # Aplicar una función de activación para mantener el resultado en un rango razonable
        relevance = np.tanh(weighted_sentiment)

        return relevance

    @staticmethod
    def sigmoid_normalize(value, max_value):
        # Normalizar usando una función sigmoide
        return 1 / (1 + np.exp(-5 * (value / max_value - 0.5)))

    def process_post(self, post, max_score, max_num_comments):
        # Procesar un solo post, evaluando su relevancia
        message = post.get('selftext', '')
        if not message:
            return None

        score = post['score']
        num_comments = post['num_comments']

        relevance = self.evaluate_message(message, score, num_comments, max_score, max_num_comments)
        return (message, relevance)

    @staticmethod
    def process_posts(trainer, posts_subset, max_score, max_num_comments):
        # Procesar múltiples posts en paralelo
        influences = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(trainer.process_post, post, max_score, max_num_comments) for post in posts_subset]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    influences.append(result)
        return influences

def Process(trainer,reddit_instance,subreddit_names,post_limit,search_query):
    posts = reddit_instance.search_posts(subreddit_names, post_limit, search_query)

    posts_subset = random.sample(posts, 10)

    scores = [post['score'] for post in posts_subset]
    num_comments_list = [post['num_comments'] for post in posts_subset]

    max_score = max(scores) if scores else 1
    max_num_comments = max(num_comments_list) if num_comments_list else 1

    influences = trainer.process_posts(trainer, posts_subset, max_score, max_num_comments)

    print(len(influences))
    for inf in influences:
        print(f'Message: {inf[0][:100]}...\nRelevance: {inf[1]}\n\n')
    # return sum(influences)/len(influences)
    return sum(inf[1] for inf in influences)/len(influences)    