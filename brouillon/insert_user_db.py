import psycopg2
import bcrypt
import os
from dotenv import load_dotenv

# Load variables d'environnement dans .env
load_dotenv()

# Fonction de hachage du mot de passe avec bcrypt
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

# Connexion à la base de données PostgreSQL
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)

cursor = conn.cursor()

# Transformation de utilisateur_id en SERIAL 
cursor.execute("CREATE SEQUENCE IF NOT EXISTS utilisateur_id_seq;")
cursor.execute("ALTER TABLE utilisateur ALTER COLUMN utilisateur_id SET DEFAULT nextval('utilisateur_id_seq');")
cursor.execute("SELECT setval('utilisateur_id_seq', (SELECT COALESCE(MAX(utilisateur_id), 1) FROM utilisateur));")

# Vérification si utilisateur_id est déjà une clé primaire
cursor.execute("""
    SELECT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_name = 'utilisateur' AND constraint_type = 'PRIMARY KEY'
    );
""")
is_primary_key = cursor.fetchone()[0]

# Ajout de la clé primaire si elle n'existe pas
if not is_primary_key:
    cursor.execute("ALTER TABLE utilisateur ADD PRIMARY KEY (utilisateur_id);")

# Validation des transactions
conn.commit()

# Insertion des rôles
roles = {
    'admin': '1',
    'user': '2',
    'premium': '3'
}

# Insérer les rôles s'ils n'existent pas encore
for role, role_id in roles.items():
    cursor.execute("SELECT * FROM role WHERE role_id=%s", (role_id,))
    result = cursor.fetchone()
    if not result:
        cursor.execute("INSERT INTO role (role_id, name) VALUES (%s, %s)", (role_id, role))

# Insertion des utilisateurs
utilisateurs = [
    ('sdao', 'dubois007@whitehouse.gov', hash_password('123'), roles['admin']),
    ('alice', 'alice123@example.com', hash_password('password123'), roles['user']),
    ('Bob', 'bob@example.com', hash_password('securepwd'), roles['premium'])
]

query = """
    INSERT INTO utilisateur (username, email, password, role_id)
    VALUES (%s, %s, %s, %s)
"""

for utilisateur in utilisateurs:
    cursor.execute(query, utilisateur)

# Validation des transactions
conn.commit()

# Fermeture du curseur et de la connexion
cursor.close()
conn.close()
