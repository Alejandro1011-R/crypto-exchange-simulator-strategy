import json
import os
from dotenv import load_dotenv
import praw
import random
import concurrent.futures

class CryptoTradingAgent:
    def __init__(self, config_file='.env'):
        # Cargar las variables de entorno desde el archivo .env
        load_dotenv(config_file)

        # Inicializar la instancia de Reddit utilizando las credenciales del archivo .env
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT'),
            username=os.getenv('REDDIT_USERNAME'),
            password=os.getenv('REDDIT_PASSWORD')
        )

    def search_subreddit(self, subreddit_name, post_limit, search_query):
        # Buscar posts en un subreddit específico utilizando una consulta de búsqueda
        subreddit = self.reddit.subreddit(subreddit_name)
        return [{
            'title': result.title,         # Título del post
            'selftext': result.selftext,   # Contenido del post
            'url': result.url,             # URL del post
            'score': result.score,         # Puntuación del post (likes - dislikes)
            'num_comments': result.num_comments  # Número de comentarios en el post
        } for result in subreddit.search(search_query, limit=post_limit)]

    def search_posts(self, subreddit_names, post_limit, search_query):
        # Buscar posts en varios subreddits en paralelo
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Crear tareas para buscar posts en cada subreddit
            future_to_subreddit = {executor.submit(self.search_subreddit, subreddit, post_limit, search_query): subreddit for subreddit in subreddit_names}
            posts = []
            # Recopilar los resultados a medida que se completen las tareas
            for future in concurrent.futures.as_completed(future_to_subreddit):
                posts.extend(future.result())
        return posts
