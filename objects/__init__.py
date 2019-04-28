version = "DEV"
embyversion = "3.1.27"

from movies import Movies
from musicvideos import MusicVideos
from tvshows import TVShows
from music import Music
from obj import Objects
from play import ListItem
from play.actions import Actions
from play.actions import PlaylistWorker
from play.actions import on_play, on_update, special_listener

Objects().mapping()
