import pytest
from unittest.mock import MagicMock, patch
import psycopg2
from main import SignUpScreen, hash_password

@pytest.fixture
def signup_screen():
    """Fixture pour initialiser l'écran SignUpScreen"""
    screen = SignUpScreen()
    screen.manager = MagicMock()
    screen.show_popup = MagicMock()
    return screen

@patch('main.cursor')
@patch('main.conn')
@patch('main.roles', {'user': 2})
def test_signup_success(mock_conn, mock_cursor, signup_screen):
    """Test pour vérifier qu'un utilisateur peut créer un compte avec des données valides"""
    # Données de test
    username = "userLive"
    email = "usertest@dijon.com"
    password = "password123"
    
    # Appel de la méthode d'inscription
    signup_screen.signup(username, email, password)
    
    # Vérifie que la requête SQL est correcte
    mock_cursor.execute.assert_called_once_with(
        "INSERT INTO utilisateur (username, email, password, role_id) VALUES (%s, %s, %s, %s)",
        (username, email, mock_cursor.execute.call_args[0][1][2], 2)  # Hashage du mdp réel
    )
    
    # Vérifie que la transaction a été validée
    mock_conn.commit.assert_called_once()
    
    # Vérifie que le curseur et la connexion ont été fermés
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()
    
    # Vérifie que l'interface navigue vers l'écran de connexion
    assert signup_screen.manager.current == "login"
    
    # Vérifie que la popup de succès a été affichée
    signup_screen.show_popup.assert_called_once_with("Success", "Signup avec succes!")

@patch('main.cursor')
@patch('main.conn')
def test_signup_empty_fields(mock_conn, mock_cursor, signup_screen):
    """Test pour vérifier que l'inscription échoue avec des champs vides"""
    # Appel de la méthode avec des champs vides
    signup_screen.signup("", "", "")
    
    # Vérifie que la popup d'erreur est affichée avec le bon message
    signup_screen.show_popup.assert_called_once_with("Erreur", "Tous les champs sont requis")
    
    # Vérifie qu'aucune interaction avec la base de données n'a eu lieu
    mock_cursor.execute.assert_not_called()
    mock_conn.commit.assert_not_called()

@patch('main.cursor')
@patch('main.conn')
def test_signup_invalid_email(mock_conn, mock_cursor, signup_screen):
    """Test pour vérifier que l'inscription échoue avec un email invalide"""
    # Appel de la méthode avec un email invalide
    signup_screen.signup("tesLive", "invalid-email", "password")
    
    # Vérifie que la popup d'erreur est affichée avec le bon message
    signup_screen.show_popup.assert_called_once_with("Erreur", "email invalide")
    
    # Vérifie qu'aucune interaction avec la base de données n'a eu lieu
    mock_cursor.execute.assert_not_called()
    mock_conn.commit.assert_not_called()

@patch('main.cursor')
@patch('main.conn')
def test_signup_database_error(mock_conn, mock_cursor, signup_screen):
    """Test pour vérifier la gestion des erreurs de base de données"""
    # Configuration du mock pour lever une exception
    mock_cursor.execute.side_effect = psycopg2.Error("Erreur BDD")
    
    # Données de test
    username = "tesLive"
    email = "usertest@simplon.co"
    password = "password123"
    
    # Appel de la méthode d'inscription
    signup_screen.signup(username, email, password)
    
    # Vérification de la transaction annulée
    mock_conn.rollback.assert_called_once()
    
    # Vérification : cursuer et connexion ont été fermés
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()

