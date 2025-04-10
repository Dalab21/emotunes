import psycopg2
import os
from dotenv import load_dotenv

# Variables d'environnement  dans .env
load_dotenv()

# Connexion à BDD PostgreSQL
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)


# Dict de rôles
roles = {
    'admin': '1',
    'user': '2',
    'premium': '3'
}