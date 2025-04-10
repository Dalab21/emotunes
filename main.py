# Librairies standards 
import os
import re
import json
from datetime import datetime
from io import BytesIO

# Librairies (ORM, Cryptage, Spotify, requests, Pillow)
import psycopg2
import bcrypt
import requests
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from PIL import Image

# Librairie Kivy et ses imports
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import ButtonBehavior, CoverBehavior
from kivy.uix.camera import Camera
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.properties import StringProperty, ObjectProperty, NumericProperty, BooleanProperty, ListProperty
from kivy.animation import Animation
from kivy.network.urlrequest import UrlRequest
from kivy.core.text import LabelBase   # Police
from kivy.core.audio import SoundLoader # Audio
from kivy.logger import Logger   #Logger


# Librairie KivyMD et ses imports
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import OneLineAvatarListItem, ImageLeftWidget



# Imports des modules personnels
from connect_db import conn, roles
from models import Song
from storage_manager import StorageManager

# Config Spotify
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
client_credentials_manager = SpotifyClientCredentials(
    client_id=client_id, 
    client_secret=client_secret)

sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
#  End Config

current_date = datetime.now() # date du moment enregistrement de fichiers json

# Connexion à la BDD
cursor = conn.cursor()
# Fonction de hachage des MDP avec bcrypt
def hash_password(password):
    """ Cryptage des MDP """
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')



class CaptureScreen(Screen):
    error_message = StringProperty("")
    
    def on_enter(self):
        """Vérifie si la caméra est prête quand on arrive sur écran camera"""
        camera = self.ids['camera']
        if not camera.texture:
            Clock.schedule_once(lambda dt: self.check_camera_ready(), 1)
    
    def check_camera_ready(self):
        """Vérifie si la caméra est initialisée et fonctionne"""
        camera = self.ids['camera']
        if not camera.texture:
            Logger.error('Camera: Camera ne fonctionne pas ou non reconnue')
            self.error_message = "Caméra non disponible. Permissions à vérifier."
            return False
        return True
    
    def capture(self):
        try:
            camera = self.ids['camera']
            
            # Vérification si caméra OK 
            if not self.check_camera_ready():
                return
            
            # Capture frame de la cam
            texture = camera.texture
            if not texture:
                Logger.error('Camera: pas de texture image valable')
                self.error_message = " impossible de capturer image "
                return
                
            size = texture.size
            pixels = texture.pixels
            
            # Création image PIL avec gestion des erreurs
            try:
                image = Image.frombytes(mode='RGBA', size=size, data=pixels)
                image = image.convert('RGB')
            except Exception as e:
                Logger.error(f'Camera: Erreur conversion image: {str(e)}')
                self.error_message = "Erreur lors du traitement de l'image"
                return
            
            # Enregistrement image dans fichier temporaire
            temp_image_path = os.path.join(os.path.dirname(__file__), 'temp_image.jpg')
            try:
                image.save(temp_image_path)
                self.analyze_emotion(temp_image_path)
            except Exception as e:
                Logger.error(f'Camera: Erreur enregistrement image : {str(e)}')
                self.error_message = "Erreur durant sauvegarde image"
                return
                
        except Exception as e:
            Logger.error(f'Camera: erreur général : {str(e)}')
            self.error_message = "Une erreur est survenue"
    
    def analyze_emotion(self, image_path):
        try:
            url = 'https://emodetect.onrender.com/predict'
            
            if not os.path.exists(image_path):
                Logger.error('Camera: Image non trouvée')
                self.error_message = "Image non trouvée"
                return
                
            with open(image_path, 'rb') as img_file:
                try:
                    response = requests.post(url, files={'file': img_file}, timeout=10)
                    response.raise_for_status()  # Lève une exception pour les codes d'erreur HTTP
                except requests.exceptions.RequestException as e:
                    Logger.error(f'Camera: requête API request échoué: {str(e)}')
                    self.error_message = "Erreur de connexion à l'API"
                    return
            
            if response.status_code == 200:
                prediction = response.json().get('emotion', 'inconnu')
            else:
                prediction = 'erreur'
                self.error_message = f"Erreur API: {response.status_code}"
                return
                
            # MAJ de l'écran
            emotion_screen = self.manager.get_screen('emotion')
            emotion_screen.ids['emotion_label'].text = f"Vous êtes : {prediction}"
            
            playlist_screen = self.manager.get_screen('playlist')
            playlist_screen.set_prediction(prediction)
            
            # Nettoyage et changement de l'écran
            try:
                os.remove(image_path)
                self.error_message = ""  # Réinitialisation du message d'erreur
                self.manager.current = 'emotion'
            except Exception as e:
                Logger.error(f'Camera: messages erreur effacés: {str(e)}')
                
        except Exception as e:
            Logger.error(f'Camera: Erreur prediction emotion : {str(e)}')
            self.error_message = "Erreur lors de analyse emotion"

#________

class MainScreen(Screen):
    pass
    
class LoginScreen(Screen):
    error_message = StringProperty("")  # customisation des msg d'erreur (en fct de type erreur)

    def login_user(self, username, password):
        cursor.execute("SELECT password, role_id FROM utilisateur WHERE username=%s", (username,))
        result = cursor.fetchone()
        if result:
            if bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8')):
                app = MDApp.get_running_app()
                app.set_current_user(username)
                self.manager.get_screen('space').username = username
                self.manager.current = 'space'
                self.error_message = ""  # Réinitialisation du message erreur
            else:
                self.error_message = "password incorrect"
        else:
            self.error_message = "Username non trouvé"

class  SignUpScreen(Screen):
    def signup(self, username, email, password):
        hashed_password = hash_password(password)
        try:
            if not username or not email or not password:
                self.show_popup("Erreur", "Tous les champs sont requis")
                return

            # Regex pour vérifier adresse mail 
            email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
            if not re.match(email_regex, email):
                self.show_popup("Erreur", "email invalide")
                return
            cursor.execute(
                "INSERT INTO utilisateur (username, email, password, role_id) VALUES (%s, %s, %s, %s)",
                (username, email, hashed_password, roles['user'])
            )
            conn.commit()
            print(" Compte crée avec succes")
            self.manager.current = "login"
        except psycopg2.Error as e:
            print(f"Erreur lors de la création de compte: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

        print(f"Signup avec: {username}, {email}, {password}, {roles['user']}")
        self.show_popup("Success", "Signup avec succes!")


    def show_popup(self, title, message):
        content = MDLabel(text=message)
        popup = Popup(title=title, content=content, size_hint=(0.75, 0.3), auto_dismiss=True)
        popup.open()

class SpaceScreen(Screen):
    username = StringProperty("")

    def on_enter(self, *args):
        app = MDApp.get_running_app()
        if not app.get_current_user():
            self.manager.current = 'login'
        else:
            self.username = app.get_current_user()


class EmotionScreen(Screen):
    pass

# Screen PlaylistEmotionScreen
class PlaylistEmotionScreen(Screen):
    prediction = StringProperty("")
    song = StringProperty("")
    artiste = StringProperty("")
    album = StringProperty("")
    genre = StringProperty("")
    cover = StringProperty("")
    recycleView = ObjectProperty(None)
    error_str = StringProperty("")
    current_file = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data_folder = 'data'
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)

    def set_prediction(self, prediction):
        self.prediction = prediction
        self.get_playlist(prediction)

    def get_playlist(self, prediction):
        url = f"https://music-search-jxd8.onrender.com/songs/emotions/{prediction}"
        UrlRequest(url, 
                  on_success=self.data_received,
                  on_error=self.data_error,
                  on_failure=self.data_failure)

    def data_received(self, req, result):
        playlist_dict = []
        for p in result:
            # Recherche de la chanson sur Spotify
            query = f"track:{p.get('song')} artist:{p.get('artiste')}"
            spotify_results = sp.search(q=query, type='track', limit=1)

            if spotify_results['tracks']['items']:
                track = spotify_results['tracks']['items'][0]
                spotify_uri = track['uri']
                preview_url = track['preview_url']
            else:
                spotify_uri = None
                preview_url = None

            playlist_dict.append({
                "artiste": p.get("artiste"),
                "album": p.get("album"),
                "song": p.get("song"),
                "genre": p.get("genre"),
                "cover": p.get("cover"),
                "date_publication": p.get("date_publication"),
                "spotify_uri": spotify_uri,
                "preview_url": preview_url
            })

        current_date = datetime.now().strftime("%Y-%m-%d")
        self.current_file = f"playlist_du_{current_date}.json"
        file_path = os.path.join(self.data_folder, self.current_file)

        with open(file_path, 'w') as file:
            json.dump(playlist_dict, file, indent=4)

        self.recycleView.data = playlist_dict

    def data_error(self, req, result):
        print(f"Error: {result}")
        self.error_str = f"Error: {result}"

    def data_failure(self, req, result):
        print(f"Failure: {result}")
        self.error_str = f"Failure: {result}"
        playlist_dict = []  # Initialisation de playlist_dict (liste vide)
        self.recycleView.data = playlist_dict


    def play_on_spotify(self, spotify_uri):
        # Transmettre les données au Screen PlayerSongScreen
        player_screen = self.manager.get_screen('player')
        player_screen.play_track(spotify_uri)
#__________________________________FIN__________________

class PlaylistDetailScreen(Screen):
    songs = ListProperty([])

    def update_playlist(self, data):
        self.songs = data
        songs_list = self.ids.songs_list
        songs_list.data = [{
            'song': song['song'],
            'artiste': song['artiste'],
            'album': song['album'],
            'date_publication': song['date_publication'],
            'genre': song.get('genre', 'Unknown'),
            'sentiment': song.get('sentiment', 'Unknown')
        } for song in self.songs]

    def return_to_historic(self):
        self.manager.current = 'historic'

#Historique de playlists
class HistoricScreen(Screen):
    files = ListProperty([])
    playlist_count = NumericProperty(0)

    def __init__(self, **kwargs):
        super(HistoricScreen, self).__init__(**kwargs)
        Clock.schedule_once(self.update_file_list, 0)

    def update_file_list(self, *args):
        directory = "data"
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        # Récupérer la liste des fichiers
        self.files = [f for f in os.listdir(directory) if f.endswith(".json")]
        
        # Mettre à jour le nombre de playlists
        self.playlist_count = len(self.files)
        
        # MAJ des données du RecycleView
        if hasattr(self, 'ids') and 'file_list' in self.ids:
            self.ids.file_list.data = [
                {
                    'text': self.format_filename(f),
                    'on_release': lambda x=f: self.open_file(x)
                } 
                for f in self.files
            ]

    def format_filename(self, filename):
        name = filename.replace('.json', '')
        return f"Playlist du {name}"

    def open_file(self, filename):
        try:
            file_path = os.path.join("data", filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
            # Naviguation vers screen de détails
            detail_screen = self.manager.get_screen('playlist_detail')
            detail_screen.update_playlist(data)
            self.manager.current = 'playlist_detail'
        except Exception as e:
            print(f"Erreur lors de l'ouverture du fichier: {e}")


class PlaylistFileButton(Button):
    filename = StringProperty('')


#  PlayerSongScreen
class PlayerSongScreen(Screen):
    current_track = StringProperty("")
    current_artist = StringProperty("")
    current_album = StringProperty("")
    current_cover = StringProperty("")
    current_uri = StringProperty("")
    is_playing = BooleanProperty(False)
    sound = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data_folder = 'data'
        
    def play_track(self, spotify_uri):
        # Arrêter la lecture en cours si elle existe
        if self.sound:
            self.sound.stop()
            self.sound.unload()
            self.sound = None
            
        try:
            track = sp.track(spotify_uri)
            self.current_track = track['name']
            self.current_artist = track['artists'][0]['name']
            self.current_album = track['album']['name']
            self.current_cover = track['album']['images'][0]['url']
            self.current_uri = spotify_uri
            
            if track['preview_url']:
                # Charger et jouer le preview
                self.sound = SoundLoader.load(track['preview_url'])
                if self.sound:
                    self.sound.bind(on_stop=self._on_sound_finished)
                    self.sound.play()
                    self.is_playing = True
                    self.ids.sc.rotate()
                else:
                    print("Impossible de charger l'audio")
            else:
                # Ouvrir Spotify si pas de preview disponible
                import webbrowser
                webbrowser.open(track['external_urls']['spotify'])
                
        except Exception as e:
            print(f"Erreur lors de la lecture : {e}")
            
    def toggle_play(self):
        if self.sound:
            if self.is_playing:
                self.sound.stop()
                self.ids.sc.stop_rotation()
            else:
                self.sound.play()
                self.ids.sc.rotate()
            self.is_playing = not self.is_playing
            
    def _on_sound_finished(self, instance):
        """Callback appelé quand la lecture est terminée"""
        self.is_playing = False
        self.ids.sc.stop_rotation()
        
    def on_leave(self):
        """Appelé quand on quitte l'écran"""
        if self.sound:
            self.sound.stop()
            self.sound.unload()
            self.sound = None



class SongCover(MDBoxLayout):
    angle = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.anim = Animation(angle=-360, duration=3)
        self.anim.bind(on_complete=self.on_complete)
        
    def rotate(self):
        self.anim.start(self)
        
    def stop_rotation(self):
        self.anim.stop(self)
        
    def on_complete(self, *args):
        if self.parent.parent.is_playing:
            self.rotate()

class PlaylistWidget(BoxLayout):
    song = StringProperty()
    artiste = StringProperty()
    album = StringProperty()
    cover = StringProperty()
    genre = StringProperty()


class SongItem(BoxLayout):
    song = StringProperty("")
    artiste = StringProperty("")
    album = StringProperty("")
    genre = StringProperty("")
    cover = StringProperty("")
    
   
class CircleButton(ButtonBehavior, Widget):
    pass

class ScreenManagement(ScreenManager):
    pass

# Lancement de l'application
class EmoTunesApp(MDApp):
    def build(self):
        Window.size = (360, 640)  # Taille de la fenêtre
        return Builder.load_file('capture_movie.kv')

    def set_current_user(self, username):
        self.current_user = username

    def get_current_user(self):
        return self.current_user

    def logout(self):
        self.current_user = None
        self.root.current = 'main'

if __name__ == '__main__':
    LabelBase.register(name="MPoppins", fn_regular="poppins/Poppins-Medium.ttf")
    LabelBase.register(name="BPoppins", fn_regular="poppins/Poppins-SemiBold.ttf")
    EmoTunesApp().run()
