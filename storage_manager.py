import json
import os
from datetime import datetime



class StorageManager:
    def __init__(self, directory="data"):
        # Répertoire par défaut pour stocker les fichiers
        self.directory = directory
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
    
    def get_filename(self, data_name):
        # Générer un nom de fichier avec la date courante
        current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return f"{data_name}_{current_date}.json"

    def save_data(self, data_name, data_content):
        filename = self.get_filename(data_name)
        file_path = os.path.join(self.directory, filename)
        
        # Sérialisation des données
        data_str = json.dumps(data_content)
        
        # Enregistrement des données dans le fichier data
        with open(file_path, "w") as file:
            file.write(data_str)

        print(f"Les données ont été enregistrées sous le nom : {filename}")

    def load_last_file(self, data_name):
        # Recherche du dernier fichier enregistré pour un data_name donné
        files = [f for f in os.listdir(self.directory) if f.startswith(data_name) and f.endswith(".json")]
        
        if not files:
            print("Aucun fichier trouvé.")
            return None
        
        # Tri des fichiers par ordre décroissant de modification
        files.sort(key=lambda f: os.path.getmtime(os.path.join(self.directory, f)), reverse=True)
        latest_file = files[0]
        file_path = os.path.join(self.directory, latest_file)
        
        # Chargement du contenu du fichier JSON
        with open(file_path, "r") as file:
            data = json.load(file)

        print(f"Les données ont été chargées depuis : {latest_file}")
        return data
