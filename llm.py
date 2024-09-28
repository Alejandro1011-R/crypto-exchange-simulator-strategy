import os
import time
import openai
from dotenv import load_dotenv
from typing import Optional, Tuple
from market import *
import concurrent.futures
import random
import numpy as np
from messages import CryptoTradingAgent



MAX_RETRIES = 5  # Número máximo de intentos para la API de Fireworks AI

class SentimentAnalyzer:
    def __init__(self, config_file='.env'):
        """
        Inicializa el analizador de sentimientos configurando la API de Fireworks AI.
        """
        # Cargar las variables de entorno desde el archivo .env
        load_dotenv(config_file)

        # Configurar la API de Fireworks AI utilizando la clave de API
        self.api_key = os.environ['FIREWORKS_API_KEY']
        self.base_url = "https://api.fireworks.ai/inference/v1"

        self.client = openai.OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

        # Definir el modelo a utilizar
        self.model = "accounts/fireworks/models/mixtral-8x7b-instruct"

    def analyze(self, message: str) -> Optional[float]:
        """
        Analiza el sentimiento de un mensaje utilizando Fireworks AI y devuelve un puntaje de sentimiento.
        El puntaje oscila entre -2 (muy bajista) y 2 (muy alcista).

        Args:
            message (str): El mensaje a analizar.

        Returns:
            Optional[float]: El puntaje de sentimiento o None si no se pudo analizar.
        """

        prompt = (
            "You are a crypto trading expert. Analyze the following message and rate its sentiment "
            "on a scale from -2 (very bearish) to 2 (very bullish). Only return the integer number "
            "without any explanation or extra text. Do not say any world in the dicctionary, just return the number.\n\n"
            "Example: Message: 'Donald T says that the bitcoin is the future of the economy' Your answer: '2'"
            f"Message: {message}\n\n"
            "ONLY return the integer number between -2 and 2."
        )

        try:
            completion = self.client.completions.create(
                model=self.model,
                prompt=prompt,
                max_tokens=10,  # Limitar la respuesta a solo un número
            )

            # Post-procesar para asegurarse de que solo se devuelve un número
            sentiment_text = completion.choices[0].text.strip()
            print(sentiment_text)

            # Extraer el número si hay texto adicional
            sentiment_score = self.extract_number(sentiment_text)

            return sentiment_score
        except openai.OpenAIError as e:
            print(f"Error al analizar el sentimiento: {e}")
            return None
        except ValueError:
            print(f"Respuesta inesperada del modelo: {completion.choices[0].text}")
            return None

    @staticmethod
    def extract_number(text: str) -> float:
        """
        Extrae el número de una cadena de texto que pueda tener caracteres adicionales.

        Args:
            text (str): Texto devuelto por el modelo.

        Returns:
            float: Número extraído del texto.
        """
        try:
            # Filtra solo los números de la respuesta
            number = float(text.split()[0])  # Tomar el primer elemento numérico que aparezca
            if -2 <= number <= 2:  # Verificar que esté en el rango esperado
                return number
        except (ValueError, IndexError):
            pass
        # Si no se puede extraer un número válido, devolver None
        return None

    def evaluate_message(self, message: str, score: int, num_comments: int, max_score: int, max_comments: int) -> float:
        """
        Evalúa la relevancia de un mensaje combinando el sentimiento con otros factores.

        Args:
            message (str): El mensaje a evaluar.
            score (int): El puntaje del post.
            num_comments (int): Número de comentarios del post.
            max_score (int): Puntaje máximo en el conjunto de posts.
            max_comments (int): Número máximo de comentarios en el conjunto de posts.

        Returns:
            float: Relevancia del mensaje.
        """
        sentiment = self.analyze(message)
        if sentiment is None:
            sentiment = 0  # Asignar neutral si no se pudo analizar

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
    def sigmoid_normalize(value: int, max_value: int) -> float:
        """
        Normaliza un valor utilizando una función sigmoide.

        Args:
            value (int): El valor a normalizar.
            max_value (int): El valor máximo posible.

        Returns:
            float: Valor normalizado entre 0 y 1.
        """
        return 1 / (1 + np.exp(-5 * (value / max_value - 0.5)))


    def process_post(self, post: Dict, max_score: int, max_num_comments: int) -> Optional[Tuple[str, float]]:
        """
        Procesa un solo post, evaluando su relevancia.

        Args:
            post (Dict): Datos del post.
            max_score (int): Puntaje máximo en el conjunto de posts.
            max_num_comments (int): Número máximo de comentarios en el conjunto de posts.

        Returns:
            Optional[Tuple[str, float]]: Tupla con el mensaje y su relevancia o None.
        """
        message = post.get('selftext', '')
        if not message:
            return None

        score = post.get('score', 0)
        num_comments = post.get('num_comments', 0)

        relevance = self.evaluate_message(message, score, num_comments, max_score, max_num_comments)
        return (message, relevance)

    def process_posts(self, posts_subset: List[Dict], max_score: int, max_num_comments: int) -> List[Tuple[str, float]]:
        """
        Procesa múltiples posts en paralelo.

        Args:
            posts_subset (List[Dict]): Subconjunto de posts a procesar.
            max_score (int): Puntaje máximo en el conjunto de posts.
            max_num_comments (int): Número máximo de comentarios en el conjunto de posts.

        Returns:
            List[Tuple[str, float]]: Lista de tuplas con mensajes y sus relevancias.
        """
        influences = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self.process_post, post, max_score, max_num_comments) for post in posts_subset]
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

    influences = trainer.process_posts(posts_subset, max_score, max_num_comments)

    print(len(influences))
    # for inf in influences:
    #     print(f'Message: {inf[0][:100]}...\nRelevance: {inf[1]}\n\n')
    # return sum(influences)/len(influences)
    return sum(inf[1] for inf in influences)/len(influences) if len(influences) else 0


# def main():
#     # Inicializar el analizador de sentimientos
#     analyzer = SentimentAnalyzer(config_file='.env')

#     # Inicializar la instancia de Reddit (simulada)
#     reddit = CryptoTradingAgent()

#     # Configurar parámetros de búsqueda
#     subreddit_names = ['cryptocurrency', 'Bitcoin', 'Ethereum', 'Ripple', 'Litecoin', 'Cardano']
#     post_limit = 50
#     search_query = 'market trends'

#     # Buscar posts
#     posts = reddit.search_posts(subreddit_names, post_limit, search_query)

#     # Seleccionar una muestra aleatoria de 10 posts para analizar
#     posts_subset = random.sample(posts, min(50, len(posts)))

#     # Obtener los puntajes y comentarios máximos
#     scores = [post['score'] for post in posts_subset]
#     num_comments_list = [post['num_comments'] for post in posts_subset]

#     max_score = max(scores) if scores else 1
#     max_num_comments = max(num_comments_list) if num_comments_list else 1

#     # Procesar los posts y obtener las influencias
#     influences = analyzer.process_posts(posts_subset, max_score, max_num_comments)

#     # Imprimir los resultados
#     print(f"Total de influencias analizadas: {len(influences)}\n")
#     for idx, (message, relevance) in enumerate(influences, start=1):
#         # print(f"Post {idx}:")
#         # print(f"Mensaje: {message}")
#         print(f'Message: {message[:100]}...\nRelevance: {relevance}\n\n')
#         # print(f"Relevancia: {relevance:.4f}\n")

#     # Calcular y mostrar el puntaje promedio de relevancia
#     if influences:
#         promedio_relevancia = sum(relevance for _, relevance in influences) / len(influences)
#         print(f"Puntaje promedio de relevancia: {promedio_relevancia:.4f}")
#     else:
#         print("No se analizaron influencias.")

# if __name__ == "__main__":
#     main()



# import os
# import time
# import google.generativeai as genai
# from google.api_core.exceptions import ResourceExhausted
# from dotenv import load_dotenv
# from messages import CryptoTradingAgent
# import concurrent.futures
# import random
# import numpy as np

# MAX_RETRIES = 5  # Número máximo de intentos para la API de Gemini

# class SentimentAnalyzer:
#     def __init__(self, config_file='.env'):
#         # Cargar las variables de entorno desde el archivo .env
#         load_dotenv(config_file)

#         # Configurar la API de Gemini AI utilizando la clave de API
#         self.api_key = os.environ['GENAI_API_KEY']
#         genai.configure(api_key=self.api_key)

#         # Configurar las opciones de seguridad para la API de Gemini
#         safety_settings = [
#             {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
#             {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
#             {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
#             {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
#         ]

#         # Inicializar el modelo generativo de Gemini AI con instrucciones específicas
#         self.chat = genai.GenerativeModel(
#             model_name="gemini-1.5-flash",
#             safety_settings=safety_settings,
#             system_instruction=[
#                 """
#                 You are a crypto trading expert. Analyze the following message and rate its sentiment
#                 on a scale from -2 (very bearish) to 2 (very bullish). Consider these factors:
#                 1. Market trends mentioned
#                 2. Technical analysis indicators
#                 3. Fundamental news about cryptocurrencies
#                 4. Overall tone and confidence of the message
#                 5. If the message is not relevant or not about cryptocurrencies the sentiment is 0
#                 Only return the numeric score without any explanation.
#                 """,
#                 "You must only return the numeric score without any explanation. Do not return anything else but a number"
#             ]
#         ).start_chat(history=[])

#     def analyze(self, message):
#         # Analizar el mensaje utilizando Gemini AI y devolver el puntaje de sentimiento
#         gemini_score = int(float(self.get_gemini_score(message).text.strip()))
#         return gemini_score

#     def get_gemini_score(self, message, retry_count=0):
#         # Obtener el puntaje de sentimiento de Gemini AI
#         try:
#             response = self.chat.send_message(f'Only return the number of the sentiment of the following message:\n\n{message}')
#             return response
#         except genai.types.BlockedPromptException as e:
#             # Manejar la excepción si la solicitud es bloqueada
#             print(f"The prompt was blocked: {e}")
#             return None
#         except ResourceExhausted as e:
#             # Reintentar si se alcanza el límite de recursos
#             if retry_count < MAX_RETRIES:
#                 time.sleep(2 ** retry_count)  # Implementar un retroceso exponencial
#                 return self.get_gemini_score(message, retry_count + 1)
#             else:
#                 raise e

#     def evaluate_message(self, message, score, num_comments, max_score, max_comments):
#         # Evaluar el mensaje combinando el sentimiento con otros factores
#         sentiment = self.analyze(message)

#         # Normalizar el puntaje y el número de comentarios
#         normalized_score = self.sigmoid_normalize(score, max_score)
#         normalized_comments = self.sigmoid_normalize(num_comments, max_comments)

#         # Parámetros de ajuste para ponderación
#         alpha = 0.3
#         gamma = 1.2

#         # Calcular el sentimiento ponderado
#         weighted_sentiment = sentiment * (1 + gamma * normalized_score + alpha * normalized_comments)

#         # Aplicar una función de activación para mantener el resultado en un rango razonable
#         relevance = np.tanh(weighted_sentiment)

#         return relevance

#     @staticmethod
#     def sigmoid_normalize(value, max_value):
#         # Normalizar usando una función sigmoide
#         return 1 / (1 + np.exp(-5 * (value / max_value - 0.5)))

#     def process_post(self, post, max_score, max_num_comments):
#         # Procesar un solo post, evaluando su relevancia
#         message = post.get('selftext', '')
#         if not message:
#             return None

#         score = post['score']
#         num_comments = post['num_comments']

#         relevance = self.evaluate_message(message, score, num_comments, max_score, max_num_comments)
#         return (message, relevance)

#     @staticmethod
#     def process_posts(trainer, posts_subset, max_score, max_num_comments):
#         # Procesar múltiples posts en paralelo
#         influences = []
#         with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
#             futures = [executor.submit(trainer.process_post, post, max_score, max_num_comments) for post in posts_subset]
#             for future in concurrent.futures.as_completed(futures):
#                 result = future.result()
#                 if result:
#                     influences.append(result)
#         return influences

# def Process(trainer,reddit_instance,subreddit_names,post_limit,search_query):
#     posts = reddit_instance.search_posts(subreddit_names, post_limit, search_query)

#     posts_subset = random.sample(posts, 10)

#     scores = [post['score'] for post in posts_subset]
#     num_comments_list = [post['num_comments'] for post in posts_subset]

#     max_score = max(scores) if scores else 1
#     max_num_comments = max(num_comments_list) if num_comments_list else 1

#     influences = trainer.process_posts(trainer, posts_subset, max_score, max_num_comments)

#     print(len(influences))
#     for inf in influences:
#         print(f'Message: {inf[0][:100]}...\nRelevance: {inf[1]}\n\n')
#     # return sum(influences)/len(influences)
#     return sum(inf[1] for inf in influences)/len(influences)