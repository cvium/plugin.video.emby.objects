# -*- coding: utf-8 -*-

#################################################################################################

import logging

import xbmc
import xbmcgui

from objects import Objects
from helper import _, api

#################################################################################################

LOG = logging.getLogger("EMBY."+__name__)

#################################################################################################


class BaseListItem(object):

    def __init__(self, obj_type, art, listitem, item, *args, **kwargs):

        self.li = listitem
        self.server = server
        self.server_id = server_id
        self.item = item
        self.objects = Objects()
        self.api = api.API(item, server)

        self.obj = self._get_objects(obj_type)
        self.obj['Artwork'] = self._get_artwork(art)

        self.format()
        self.set()

    def _get_objects(self, key):
        return  self.objects.map(self.item, key)

    def _get_artwork(self, key):
        return  self.api.get_all_artwork(self.objects.map(self.item, key))

    def format(self):

        ''' Format object values. Override.
        '''
        pass

    def set(self):

        ''' Set the listitem values based on object. Override.
        '''
        pass

    @classmethod
    def art(cls):

        ''' Return artwork mapping for object. Override if needed.
        '''
        return  {
            'poster': "Primary",
            'clearart': "Art",
            'clearlogo': "Logo",
            'discart': "Disc",
            'fanart_image': "Backdrop",
            'landscape': "Thumb",
            'thumb': "Primary",
            'fanart': "Backdrop"
        }

    def set_art(self):

        artwork = self.obj['Artwork']
        art = self.art()

        for kodi, emby in art.items():

            if emby == 'Backdrop':
                self._set_art(self.li, kodi, artwork[emby][0] if artwork[emby] else " ")
            else:
                self._set_art(self.li, kodi, artwork.get(emby, " "))

    def _set_art(self, art, path, *args, **kwargs):
        LOG.debug(" [ art/%s ] %s", art, path)

        if art in ('fanart_image', 'small_poster', 'tiny_poster',
                   'medium_landscape', 'medium_poster', 'small_fanartimage',
                   'medium_fanartimage', 'fanart_noindicators', 'tvshow.poster'):

            self.li.setProperty(art, path)
        else:
            self.li.setArt({art: path})


class Playlist(BaseListItem):

    def __init__(self, *args, **kwargs):
        BaseListItem.__init__(self, 'BrowseFolder', 'Artwork', *args, **kwargs)

    def set(self):

        self.li.setProperty('path', self.obj['Artwork']['Primary'])
        self.li.setProperty('IsFolder', 'true')
        self.li.setThumbnailImage(self.obj['Artwork']['Primary'])
        self.li.setIconImage('DefaultFolder.png')

        self.li.setProperty('IsPlayable', 'false')
        self.li.setLabel(self.obj['Title'])
        self.li.setContentLookup(False)


class Channel(BaseListItem):

    def __init__(self, *args, **kwargs):
        BaseListItem.__init__(self, 'BrowseChannel', 'Artwork', *args, **kwargs)

    @staticmethod
    def art():
        return  {
            'fanart_image': "Backdrop",
            'thumb': "Primary",
            'fanart': "Backdrop"
        }

    def format(self):

        self.obj['Title'] = "%s - %s" % (self.obj['Title'], self.obj['ProgramName'])
        self.obj['Runtime'] = round(float((self.obj['Runtime'] or 0) / 10000000.0), 6)
        self.obj['PlayCount'] = self.api.get_playcount(self.obj['Played'], self.obj['PlayCount']) or 0
        self.obj['Overlay'] = 7 if self.obj['Played'] else 6
        self.obj['Artwork']['Primary'] = self.obj['Artwork']['Primary'] or "special://home/addons/plugin.video.emby/icon.png"
        self.obj['Artwork']['Thumb'] = self.obj['Artwork']['Thumb'] or "special://home/addons/plugin.video.emby/icon.jpg"
        self.obj['Artwork']['Backdrop'] = self.obj['Artwork']['Backdrop'] or ["special://home/addons/plugin.video.emby/fanart.jpg"]

    def set(self):

        metadata = {
            'title': self.obj['Title'],
            'originaltitle': self.obj['Title'],
            'playcount': self.obj['PlayCount'],
            'overlay': self.obj['Overlay']
        }
        self.li.setIconImage('DefaultVideo.png')
        self.li.setThumbnailImage(self.obj['Artwork']['Primary'])
        self.set_art()

        self.li.setProperty('totaltime', str(self.obj['Runtime']))
        self.li.setProperty('IsPlayable', 'true')
        self.li.setProperty('IsFolder', 'false')

        self.li.setLabel(self.obj['Title'])
        self.li.setInfo('video', metadata)
        self.li.setContentLookup(False)


class Photo(BaseListItem):

    def __init__(self, *args, **kwargs):
        BaseListItem.__init__(self, 'BrowsePhoto', 'Artwork', *args, **kwargs)

    def format(self):

        self.obj['Overview'] = self.api.get_overview(self.obj['Overview'])
        self.obj['FileDate'] = "%s.%s.%s" % tuple(reversed(self.obj['FileDate'].split('T')[0].split('-')))

    def set(self):

        metadata = {
            'title': self.obj['Title'],
            'picturepath': self.obj['Artwork']['Primary'],
            'date': self.obj['FileDate'],
            'exif:width': str(self.obj.get('Width', 0)),
            'exif:height': str(self.obj.get('Height', 0)),
            'size': self.obj['Size'],
            'exif:cameramake': self.obj['CameraMake'],
            'exif:cameramodel': self.obj['CameraModel'],
            'exif:exposuretime': str(self.obj['ExposureTime']),
            'exif:focallength': str(self.obj['FocalLength'])
        }
        self.li.setProperty('path', self.obj['Artwork']['Primary'])
        self.li.setThumbnailImage(self.obj['Artwork']['Primary'])
        self.li.setProperty('plot', self.obj['Overview'])
        self.li.setProperty('IsFolder', 'false')
        self.li.setIconImage('DefaultPicture.png')
        self.li.setProperty('IsPlayable', 'false')
        self.li.setLabel(self.obj['Title'])
        self.li.setInfo('pictures', metadata)
        self.li.setContentLookup(False)


class Music(BaseListItem):

    def __init__(self, *args, **kwargs):
        BaseListItem.__init__(self, 'BrowseAudio', ('ArtworkMusic', True,), *args, **kwargs)

    @classmethod
    def art(cls):
        return  {
            'clearlogo': "Logo",
            'discart': "Disc",
            'fanart': "Backdrop",
            'fanart_image': "Backdrop", # in case
            'thumb': "Primary"
        }

    def format(self):

        self.obj['Runtime'] = round(float((self.obj['Runtime'] or 0) / 10000000.0), 6)
        self.obj['PlayCount'] = self.api.get_playcount(self.obj['Played'], self.obj['PlayCount']) or 0
        self.obj['Rating'] = self.obj['Rating'] or 0

        if self.obj['FileDate'] or self.obj['DatePlayed']:
            self.obj['DatePlayed'] = (self.obj['DatePlayed'] or self.obj['FileDate']).split('.')[0].replace('T', " ")

        self.obj['FileDate'] = "%s.%s.%s" % tuple(reversed(self.obj['FileDate'].split('T')[0].split('-')))

    def set(self):

        metadata = {
            'title': self.obj['Title'],
            'genre': self.obj['Genre'],
            'year': self.obj['Year'],
            'album': self.obj['Album'],
            'artist': self.obj['Artists'],
            'rating': self.obj['Rating'],
            'comment': self.obj['Comment'],
            'date': self.obj['FileDate'],
            'mediatype': "music"
        }
        self.set_art()


class PhotoAlbum(Photo):

    def __init__(self, *args, **kwargs):
        Photo.__init__(self, *args, **kwargs)

    def set(self):

        metadata = {
            'title': self.obj['Title']
        }
        self.li.setProperty('path', self.obj['Artwork']['Primary'])
        self.li.setThumbnailImage(self.obj['Artwork']['Primary'])
        self.li.setProperty('IsFolder', 'true')
        self.li.setIconImage('DefaultFolder.png')
        self.li.setProperty('IsPlayable', 'false')
        self.li.setLabel(self.obj['Title'])
        self.li.setInfo('pictures', metadata)
        self.li.setContentLookup(False)


class Video(BaseListItem):

    def __init__(self, *args, **kwargs):

        BaseListItem.__init__(self, 'BrowseVideo', ('ArtworkParent', True,), *args, **kwargs)

        if 'PlaybackInfo' in self.item:

            if self.item['LI']['Seektime']:
                self.item['PlaybackInfo']['CurrentPosition'] = self.obj['Resume']

            if 'SubtitleUrl' in self.item['PlaybackInfo']:

                LOG.info("[ subtitles ] %s", self.item['PlaybackInfo']['SubtitleUrl'])
                self.li.setSubtitles([self.item['PlaybackInfo']['SubtitleUrl']])

    def format(self):

        self.obj['Genres'] = " / ".join(self.obj['Genres'] or [])
        self.obj['Studios'] = [self.api.validate_studio(studio) for studio in (self.obj['Studios'] or [])]
        self.obj['Studios'] = " / ".join(self.obj['Studios'])
        self.obj['Mpaa'] = self.api.get_mpaa(self.obj['Mpaa'])
        self.obj['People'] = self.obj['People'] or []
        self.obj['Countries'] = " / ".join(self.obj['Countries'] or [])
        self.obj['Directors'] = " / ".join(self.obj['Directors'] or [])
        self.obj['Writers'] = " / ".join(self.obj['Writers'] or [])
        self.obj['Plot'] = self.api.get_overview(self.obj['Plot'])
        self.obj['ShortPlot'] = self.api.get_overview(self.obj['ShortPlot'])
        self.obj['DateAdded'] = self.obj['DateAdded'].split('.')[0].replace('T', " ")
        self.obj['Rating'] = self.obj['Rating'] or 0
        self.obj['FileDate'] = "%s.%s.%s" % tuple(reversed(self.obj['DateAdded'].split('T')[0].split('-')))
        self.obj['Runtime'] = round(float((self.obj['Runtime'] or 0) / 10000000.0), 6)
        self.obj['Resume'] = self.api.adjust_resume((self.obj['Resume'] or 0) / 10000000.0)
        self.obj['PlayCount'] = self.api.get_playcount(self.obj['Played'], self.obj['PlayCount']) or 0
        self.obj['Overlay'] = 7 if self.obj['Played'] else 6
        self.obj['Video'] = self.api.video_streams(self.obj['Video'] or [], self.obj['Container'])
        self.obj['Audio'] = self.api.audio_streams(self.obj['Audio'] or [])
        self.obj['Streams'] = self.api.media_streams(self.obj['Video'], self.obj['Audio'], self.obj['Subtitles'])
        self.obj['ChildCount'] = self.obj['ChildCount'] or 0
        self.obj['RecursiveCount'] = self.obj['RecursiveCount'] or 0
        self.obj['Unwatched'] = self.obj['Unwatched'] or 0
        self.obj['Artwork']['Backdrop'] = self.obj['Artwork']['Backdrop'] or []
        self.obj['Artwork']['Thumb'] = self.obj['Artwork']['Thumb'] or ""
        self.obj['Artwork']['Primary'] = self.obj['Artwork']['Primary'] or "special://home/addons/plugin.video.emby/icon.png"

        if self.obj['Premiere']:
            self.obj['Premiere'] = self.obj['Premiere'].split('T')[0]

        if self.obj['DatePlayed']:
            self.obj['DatePlayed'] = self.obj['DatePlayed'].split('.')[0].replace('T', " ")

    def set(self):

        self.set_art()
        self.li.setIconImage('DefaultVideo.png')
        self.li.setThumbnailImage(self.obj['Artwork']['Primary'])

        metadata = {
            'title': self.obj['Title'],
            'originaltitle': self.obj['Title'],
            'sorttitle': self.obj['SortTitle'],
            'country': self.obj['Countries'],
            'genre': self.obj['Genres'],
            'year': self.obj['Year'],
            'rating': self.obj['Rating'],
            'playcount': self.obj['PlayCount'],
            'overlay': self.obj['Overlay'],
            'director': self.obj['Directors'],
            'mpaa': self.obj['Mpaa'],
            'plot': self.obj['Plot'],
            'plotoutline': self.obj['ShortPlot'],
            'studio': self.obj['Studios'],
            'tagline': self.obj['Tagline'],
            'writer': self.obj['Writers'],
            'premiered': self.obj['Premiere'],
            'votes': self.obj['Votes'],
            'dateadded': self.obj['DateAdded'],
            'aired': self.obj['Year'],
            'date': self.obj['Premiere'] or self.obj['FileDate'],
            'dbid': self.item['LI']['DbId'],
            'mediatype': "video",
            'lastplayed': self.obj['DatePlayed'],
            'year': self.obj['Year'],
            'duration': self.obj['Runtime']
        }
        self.li.setCast(self.api.get_actors())
        self.set_playable()
        self.li.setLabel(self.obj['Title'])
        self.li.setInfo('video', metadata)
        self.li.setContentLookup(False)

    def set_playable(self):

        self.li.setProperty('totaltime', str(self.obj['Runtime']))
        self.li.setProperty('IsPlayable', 'true')
        self.li.setProperty('IsFolder', 'false')

        if self.obj['Resume'] and self.obj['Runtime'] and self.item['LI']['Seektime'] != False:

            self.li.setProperty('resumetime', str(self.obj['Resume']))
            self.li.setProperty('StartPercent', str(((self.obj['Resume']/self.obj['Runtime']) * 100)))
        else:
            self.li.setProperty('resumetime', '0')
            self.li.setProperty('StartPercent', '0')

        for track in self.obj['Streams']['video']:
            self.li.addStreamInfo('video', {
                'duration': self.obj['Runtime'],
                'aspect': track['aspect'],
                'codec': track['codec'],
                'width': track['width'],
                'height': track['height']
            })

        for track in self.obj['Streams']['audio']:
            self.li.addStreamInfo('audio', {'codec': track['codec'], 'channels': track['channels']})

        for track in self.obj['Streams']['subtitle']:
            self.li.addStreamInfo('subtitle', {'language': track})


class Audio(Music):

    def __init__(self, *args, **kwargs):
        Music.__init__(self, *args, **kwargs)

    def set(self):

        metadata = {
            'title': self.obj['Title'],
            'genre': self.obj['Genre'],
            'year': self.obj['Year'],
            'album': self.obj['Album'],
            'artist': self.obj['Artists'],
            'rating': self.obj['Rating'],
            'comment': self.obj['Comment'],
            'date': self.obj['FileDate'],
            'mediatype': "song",
            'tracknumber': self.obj['Index'],
            'discnumber': self.obj['Disc'],
            'duration': self.obj['Runtime'],
            'playcount': self.obj['PlayCount'],
            'lastplayed': self.obj['DatePlayed'],
            'musicbrainztrackid': self.obj['UniqueId']
        }
        self.set_art()
        self.li.setProperty('IsPlayable', 'true')
        self.li.setProperty('IsFolder', 'false')
        self.li.setLabel(self.obj['Title'])
        self.li.setInfo('music', metadata)
        self.li.setContentLookup(False)

class Album(Music):

    def __init__(self, *args, **kwargs):
        Music.__init__(self, *args, **kwargs)

    def set(self):

        metadata = {
            'title': self.obj['Title'],
            'genre': self.obj['Genre'],
            'year': self.obj['Year'],
            'album': self.obj['Album'],
            'artist': self.obj['Artists'],
            'rating': self.obj['Rating'],
            'comment': self.obj['Comment'],
            'date': self.obj['FileDate'],
            'mediatype': "album",
            'musicbrainzalbumid': self.obj['UniqueId']
        }
        self.set_art()
        self.li.setLabel(self.obj['Title'])
        self.li.setInfo('music', metadata)
        self.li.setContentLookup(False)

class Artist(Music):

    def __init__(self, *args, **kwargs):
        Music.__init__(self, *args, **kwargs)

    def set(self):

        metadata = {
            'title': self.obj['Title'],
            'genre': self.obj['Genre'],
            'year': self.obj['Year'],
            'album': self.obj['Album'],
            'artist': self.obj['Artists'],
            'rating': self.obj['Rating'],
            'comment': self.obj['Comment'],
            'date': self.obj['FileDate'],
            'mediatype': "artist",
            'musicbrainzartistid': self.obj['UniqueId']
        }
        self.set_art()
        self.li.setLabel(self.obj['Title'])
        self.li.setInfo('music', metadata)
        self.li.setContentLookup(False)


class Episode(Video):

    def __init__(self, *args, **kwargs):
        Video.__init__(self, *args, **kwargs)

    @classmethod
    def art(cls):
        return  {
            'poster': "Series.Primary",
            'tvshow.poster': "Series.Primary",
            'clearart': "Art",
            'tvshow.clearart': "Art",
            'clearlogo': "Logo",
            'tvshow.clearlogo': "Logo",
            'discart': "Disc",
            'fanart_image': "Backdrop",
            'landscape': "Thumb",
            'tvshow.landscape': "Thumb",
            'thumb': "Primary",
            'fanart': "Backdrop"
        }

    def set(self):
        
        self.set_art()
        self.li.setIconImage('DefaultVideo.png')
        self.li.setThumbnailImage(self.obj['Artwork']['Primary'])

        metadata = {
            'title': self.obj['Title'],
            'originaltitle': self.obj['Title'],
            'sorttitle': self.obj['SortTitle'],
            'country': self.obj['Countries'],
            'genre': self.obj['Genres'],
            'year': self.obj['Year'],
            'rating': self.obj['Rating'],
            'playcount': self.obj['PlayCount'],
            'overlay': self.obj['Overlay'],
            'director': self.obj['Directors'],
            'mpaa': self.obj['Mpaa'],
            'plot': self.obj['Plot'],
            'plotoutline': self.obj['ShortPlot'],
            'studio': self.obj['Studios'],
            'tagline': self.obj['Tagline'],
            'writer': self.obj['Writers'],
            'premiered': self.obj['Premiere'],
            'votes': self.obj['Votes'],
            'dateadded': self.obj['DateAdded'],
            'aired': self.obj['Year'],
            'date': self.obj['Premiere'] or self.obj['FileDate'],
            'dbid': self.item['LI']['DbId'],
            'mediatype': "episode",
            'tvshowtitle': self.obj['SeriesName'],
            'season': self.obj['Season'] or 0,
            'sortseason': self.obj['Season'] or 0,
            'episode': self.obj['Index'] or 0,
            'sortepisode': self.obj['Index'] or 0,
            'lastplayed': self.obj['DatePlayed'],
            'duration': self.obj['Runtime'],
            'aired': self.obj['Premiere']
        }
        self.li.setCast(self.api.get_actors())
        self.set_playable()
        self.li.setLabel(self.obj['Title'])
        self.li.setInfo('video', metadata)
        self.li.setContentLookup(False)

        if 'PlaybackInfo' in self.item:

            self.item['PlaybackInfo']['CurrentEpisode'] = self.objects.map(self.item, "UpNext")
            self.item['PlaybackInfo']['CurrentEpisode']['art'] = {
                'tvshow.poster': self.obj['Artwork'].get('Series.Primary'),
                'thumb': self.obj['Artwork'].get('Primary'),
                'tvshow.fanart': None
            }
            if self.obj['Artwork']['Backdrop']:
                self.item['PlaybackInfo']['CurrentEpisode']['art']['tvshow.fanart'] = self.obj['Artwork']['Backdrop'][0]

class Season(Video):

    def __init__(self, *args, **kwargs):
        Video.__init__(self, *args, **kwargs)

    def set(self):
        
        self.set_art()
        self.li.setIconImage('DefaultVideo.png')
        self.li.setThumbnailImage(self.obj['Artwork']['Primary'])

        metadata = {
            'title': self.obj['Title'],
            'originaltitle': self.obj['Title'],
            'sorttitle': self.obj['SortTitle'],
            'country': self.obj['Countries'],
            'genre': self.obj['Genres'],
            'year': self.obj['Year'],
            'rating': self.obj['Rating'],
            'playcount': self.obj['PlayCount'],
            'overlay': self.obj['Overlay'],
            'director': self.obj['Directors'],
            'mpaa': self.obj['Mpaa'],
            'plot': self.obj['Plot'],
            'plotoutline': self.obj['ShortPlot'],
            'studio': self.obj['Studios'],
            'tagline': self.obj['Tagline'],
            'writer': self.obj['Writers'],
            'premiered': self.obj['Premiere'],
            'votes': self.obj['Votes'],
            'dateadded': self.obj['DateAdded'],
            'aired': self.obj['Year'],
            'date': self.obj['Premiere'] or self.obj['FileDate'],
            'dbid': self.item['LI']['DbId'],
            'mediatype': "season",
            'tvshowtitle': self.obj['SeriesName'],
            'season': self.obj['Index'] or 0,
            'sortseason': self.obj['Index'] or 0
        }
        self.li.setCast(self.api.get_actors())
        self.li.setProperty('NumEpisodes', str(self.obj['RecursiveCount']))
        self.li.setProperty('WatchedEpisodes', str(self.obj['RecursiveCount'] - self.obj['Unwatched']))
        self.li.setProperty('UnWatchedEpisodes', str(self.obj['Unwatched']))
        self.li.setProperty('IsFolder', 'true')
        self.li.setLabel(self.obj['Title'])
        self.li.setInfo('video', metadata)
        self.li.setContentLookup(False)

class Series(Video):

    def __init__(self, *args, **kwargs):
        Video.__init__(self, *args, **kwargs)

    def format(self):
        super(Video, self).format()

        if self.obj['Status'] != 'Ended':
            self.obj['Status'] = None

    def set(self):
        
        self.set_art()
        self.li.setIconImage('DefaultVideo.png')
        self.li.setThumbnailImage(self.obj['Artwork']['Primary'])

        metadata = {
            'title': self.obj['Title'],
            'originaltitle': self.obj['Title'],
            'sorttitle': self.obj['SortTitle'],
            'country': self.obj['Countries'],
            'genre': self.obj['Genres'],
            'year': self.obj['Year'],
            'rating': self.obj['Rating'],
            'playcount': self.obj['PlayCount'],
            'overlay': self.obj['Overlay'],
            'director': self.obj['Directors'],
            'mpaa': self.obj['Mpaa'],
            'plot': self.obj['Plot'],
            'plotoutline': self.obj['ShortPlot'],
            'studio': self.obj['Studios'],
            'tagline': self.obj['Tagline'],
            'writer': self.obj['Writers'],
            'premiered': self.obj['Premiere'],
            'votes': self.obj['Votes'],
            'dateadded': self.obj['DateAdded'],
            'aired': self.obj['Year'],
            'date': self.obj['Premiere'] or self.obj['FileDate'],
            'dbid': self.item['LI']['DbId'],
            'mediatype': "tvshow",
            'tvshowtitle': self.obj['Title'],
            'status': self.obj['Status']
        }
        self.li.setCast(self.api.get_actors())

        self.li.setProperty('TotalSeasons', str(self.obj['ChildCount']))
        self.li.setProperty('TotalEpisodes', str(self.obj['RecursiveCount']))
        self.li.setProperty('WatchedEpisodes', str(self.obj['RecursiveCount'] - self.obj['Unwatched']))
        self.li.setProperty('UnWatchedEpisodes', str(self.obj['Unwatched']))
        self.li.setProperty('IsFolder', 'true')
        self.li.setLabel(self.obj['Title'])
        self.li.setInfo('video', metadata)
        self.li.setContentLookup(False)

class Movie(Video):

    def __init__(self, *args, **kwargs):
        Video.__init__(self, *args, **kwargs)

    def set(self):
        
        self.set_art()
        self.li.setIconImage('DefaultVideo.png')
        self.li.setThumbnailImage(self.obj['Artwork']['Primary'])

        metadata = {
            'title': self.obj['Title'],
            'originaltitle': self.obj['Title'],
            'sorttitle': self.obj['SortTitle'],
            'country': self.obj['Countries'],
            'genre': self.obj['Genres'],
            'year': self.obj['Year'],
            'rating': self.obj['Rating'],
            'playcount': self.obj['PlayCount'],
            'overlay': self.obj['Overlay'],
            'director': self.obj['Directors'],
            'mpaa': self.obj['Mpaa'],
            'plot': self.obj['Plot'],
            'plotoutline': self.obj['ShortPlot'],
            'studio': self.obj['Studios'],
            'tagline': self.obj['Tagline'],
            'writer': self.obj['Writers'],
            'premiered': self.obj['Premiere'],
            'votes': self.obj['Votes'],
            'dateadded': self.obj['DateAdded'],
            'aired': self.obj['Year'],
            'date': self.obj['Premiere'] or self.obj['FileDate'],
            'dbid': self.item['LI']['DbId'],
            'mediatype': "movie",
            'imdbnumber': self.obj['UniqueId'],
            'lastplayed': self.obj['DatePlayed'],
            'duration': self.obj['Runtime'],
            'userrating': self.obj['CriticRating']
        }
        self.li.setCast(self.api.get_actors())
        self.set_playable()
        self.li.setLabel(self.obj['Title'])
        self.li.setInfo('video', metadata)
        self.li.setContentLookup(False)

class BoxSet(Video):

    def __init__(self,*args, **kwargs):
        Video.__init__(self, *args, **kwargs)

    def set(self):
        
        self.set_art()
        self.li.setIconImage('DefaultVideo.png')
        self.li.setThumbnailImage(self.obj['Artwork']['Primary'])

        metadata = {
            'title': self.obj['Title'],
            'originaltitle': self.obj['Title'],
            'sorttitle': self.obj['SortTitle'],
            'country': self.obj['Countries'],
            'genre': self.obj['Genres'],
            'year': self.obj['Year'],
            'rating': self.obj['Rating'],
            'playcount': self.obj['PlayCount'],
            'overlay': self.obj['Overlay'],
            'director': self.obj['Directors'],
            'mpaa': self.obj['Mpaa'],
            'plot': self.obj['Plot'],
            'plotoutline': self.obj['ShortPlot'],
            'studio': self.obj['Studios'],
            'tagline': self.obj['Tagline'],
            'writer': self.obj['Writers'],
            'premiered': self.obj['Premiere'],
            'votes': self.obj['Votes'],
            'dateadded': self.obj['DateAdded'],
            'aired': self.obj['Year'],
            'date': self.obj['Premiere'] or self.obj['FileDate'],
            'dbid': self.item['LI']['DbId'],
            'mediatype': "set"
        }
        self.li.setCast(self.api.get_actors())
        self.li.setProperty('IsFolder', 'true')
        self.li.setLabel(self.obj['Title'])
        self.li.setInfo('video', metadata)
        self.li.setContentLookup(False)

class MusicVideo(Video):

    def __init__(self, *args, **kwargs):
        Video.__init__(self, *args, **kwargs)

    def set(self):
        
        self.set_art()
        self.li.setIconImage('DefaultVideo.png')
        self.li.setThumbnailImage(self.obj['Artwork']['Primary'])

        metadata = {
            'title': self.obj['Title'],
            'originaltitle': self.obj['Title'],
            'sorttitle': self.obj['SortTitle'],
            'country': self.obj['Countries'],
            'genre': self.obj['Genres'],
            'year': self.obj['Year'],
            'rating': self.obj['Rating'],
            'playcount': self.obj['PlayCount'],
            'overlay': self.obj['Overlay'],
            'director': self.obj['Directors'],
            'mpaa': self.obj['Mpaa'],
            'plot': self.obj['Plot'],
            'plotoutline': self.obj['ShortPlot'],
            'studio': self.obj['Studios'],
            'tagline': self.obj['Tagline'],
            'writer': self.obj['Writers'],
            'premiered': self.obj['Premiere'],
            'votes': self.obj['Votes'],
            'dateadded': self.obj['DateAdded'],
            'aired': self.obj['Year'],
            'date': self.obj['Premiere'] or self.obj['FileDate'],
            'dbid': self.item['LI']['DbId'],
            'mediatype': "musicvideo",
            'album': self.obj['Album'],
            'artist': self.obj['Artists'] or [],
            'lastplayed': self.obj['DatePlayed'],
            'duration': self.obj['Runtime']
        }
        self.li.setCast(self.api.get_actors())
        self.set_playable()
        self.li.setLabel(self.obj['Title'])
        self.li.setInfo('video', metadata)
        self.li.setContentLookup(False)

class Intro(Video):

    def __init__(self, *args, **kwargs):
        Video.__init__(self, *args, **kwargs)

    def format(self):

        self.obj['Artwork']['Primary'] = self.obj['Artwork']['Primary'] or self.obj['Artwork']['Thumb'] or (self.obj['Artwork']['Backdrop'][0] if len(self.obj['Artwork']['Backdrop']) else "special://home/addons/plugin.video.emby/fanart.jpg")
        self.obj['Artwork']['Primary'] += "?KodiCinemaMode=true"
        self.obj['Artwork']['Backdrop'] = [self.obj['Artwork']['Primary']]

        super(Intro, self).format()

    def set(self):
        
        self.set_art()
        self.li.setArt({'poster': ""}) # Clear the poster value for intros / trailers to prevent issues in skins
        self.li.setIconImage('DefaultVideo.png')
        self.li.setThumbnailImage(self.obj['Artwork']['Primary'])

        metadata = {
            'title': self.obj['Title'],
            'originaltitle': self.obj['Title'],
            'sorttitle': self.obj['SortTitle'],
            'country': self.obj['Countries'],
            'genre': self.obj['Genres'],
            'year': self.obj['Year'],
            'rating': self.obj['Rating'],
            'playcount': self.obj['PlayCount'],
            'overlay': self.obj['Overlay'],
            'director': self.obj['Directors'],
            'mpaa': self.obj['Mpaa'],
            'plot': self.obj['Plot'],
            'plotoutline': self.obj['ShortPlot'],
            'studio': self.obj['Studios'],
            'tagline': self.obj['Tagline'],
            'writer': self.obj['Writers'],
            'premiered': self.obj['Premiere'],
            'votes': self.obj['Votes'],
            'dateadded': self.obj['DateAdded'],
            'aired': self.obj['Year'],
            'date': self.obj['Premiere'] or self.obj['FileDate'],
            'mediatype': "video",
            'lastplayed': self.obj['DatePlayed'],
            'year': self.obj['Year'],
            'duration': self.obj['Runtime']
        }
        self.li.setCast(self.api.get_actors())
        self.set_playable()
        self.li.setLabel(self.obj['Title'])
        self.li.setInfo('video', metadata)
        self.li.setContentLookup(False)

class Trailer(Intro):

    def __init__(self, *args, **kwargs):
        Intro.__init__(self, *args, **kwargs)

    def format(self):

        self.obj['Artwork']['Primary'] = self.obj['Artwork']['Primary'] or self.obj['Artwork']['Thumb'] or (self.obj['Artwork']['Backdrop'][0] if len(self.obj['Artwork']['Backdrop']) else "special://home/addons/plugin.video.emby/fanart.jpg")
        self.obj['Artwork']['Primary'] += "?KodiTrailer=true"
        self.obj['Artwork']['Backdrop'] = [self.obj['Artwork']['Primary']]

        super(Video, self).format()


#################################################################################################

MUSIC = {
    'Artist': Artist,
    'MusicArtist': Artist,
    'MusicAlbum': Album,
    'Audio': Audio,
    'Music': Music
}
PHOTO = {
    'Photo': Photo,
    'PhotoAlbum': PhotoAlbum
}
VIDEO = {
    'Episode': Episode,
    'Season': Season,
    'Series': Series,
    'Movie': Movie,
    'MusicVideo': MusicVideo,
    'BoxSet': BoxSet,
    'Trailer': Trailer,
    'AudioBook': Video,
    'Video': Video
}
BASIC = {
    'Playlist': Playlist,
    'TvChannel': Channel
}

#################################################################################################


class ListItem(object):

    ''' Translate an emby item into a Kodi listitem.
    '''

    def __init__(self, server, server_id, *args, **kwargs):

        self.server = server
        self.server_id = server_id

    def _detect_type(self):

        item_type = self.item['Type']

        for typ in (VIDEO, MUSIC, PHOTO, BASIC):
            if item_type in typ:
                return typ[item_type]
        else:
            return VIDEO['Video']

    def set(self, item, listitem=None, intro=False, db_id=None, seektime=None, *args, **kwargs):
        
        listitem = listitem or xbmcgui.ListItem()
        item['LI'] = {
            'DbId': db_id,
            'Seektime': seektime,
            'Server': self.server,
            'ServerId': self.server_id
        }
        if intro:
            func = VIDEO['Trailer'] if self.item['Type'] == 'Trailer' else VIDEO['Intro']
        else:
            func = self._detect_type()

        func(listitem, self.item, *args, **kwargs)
        item.pop('LI')

        return listitem
