class Song:
    artiste : ""
    album : ""
    song : ""
    genre : ""
    cover : ""
    date_publication : ""

    def __init__(self, song, artiste, album, genre, cover, date_publication):
        self.song : song
        self.artiste : artiste
        self.album : album
        self.genre : genre
        self.cover : cover
        self.date_publication = date_publication
        

    def get_dictionnary(self):
        return {"song":self.song, "artiste" : self.artiste, "album": self.album,  "genre": self.genre, "cover": self.cover, "date_publication" : self.date_publication }
