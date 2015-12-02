"""
iPod for XBMC

Author: stafio
Original Author: Carles F. Julia
"""

import sys
import os
import xbmc
import xbmcplugin
import xbmcgui

WORKING_DIR = os.path.dirname(os.path.realpath(__file__))
BASE_RESOURCE_PATH = os.path.join(WORKING_DIR, 'resources')

sys.path.append (os.path.join(BASE_RESOURCE_PATH,'lib'))

import sys_utils
import os.path
import shelve
import base64

thisPlugin = None
thisPluginUrl='plugin://plugin.audio.ipod/'

ipodDB = os.path.join(BASE_RESOURCE_PATH,'data','ipodDB')

addon_handle = int(sys.argv[1])

xbmcplugin.setContent(addon_handle, 'audio')

def copyInfo(mp):
    "Copy all info from iPod Database to a local file"
    import gpod
    artists = dict()
    i_itdb = gpod.itdb_parse(mp,None)
    for track in gpod.sw_get_tracks(i_itdb):
        album = track.album
        artist = track.artist
        song = dict()
        song['file']=gpod.itdb_filename_on_ipod(track)
        song['title']=track.title
        song['track number']=track.track_nr
        if artist not in artists:
            artists[artist]=dict()
            artists[artist]['name']=artist
            artists[artist]['albums']=dict()
        if album not in artists[artist]['albums']:
            artists[artist]['albums'][album]=dict()
            artists[artist]['albums'][album]['title']=album
            artists[artist]['albums'][album]['songs']=list()
        artists[artist]['albums'][album]['songs'].append(song)
    pass
    d = shelve.open(ipodDB)
    d[mp]=artists
    d.close()


def MyAddDirectoryItem(url,caption,isFolder=False):
    "Helper for xbmcplugin.addDirectoryItem()"
    li = xbmcgui.ListItem(caption)
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=isFolder)

def isUrl(name):
    def register(f):
        global urls_views
        try:
            urls_views
        except NameError:
            urls_views = dict()
        urls_views[name]=f
        return f
    return register

def call_Url(u):
    global urls_views
    try:
        url = u
        url = url[len(thisPluginUrl):].split('/')
    except:
        url = ['']
    view = url[0]
    args = url[1:]

    if not view or view not in urls_views:
        view = 'list_ipods'
        args = []

    args = [base64.b64decode(a) for a in args if a]

    f = urls_views[view]
    f(*args)

def make_Url(f,*args):
    urls_views_inverse = dict((v,k) for k, v in urls_views.iteritems())
    base = urls_views_inverse[f]
    args = [base64.b64encode(a) for a in args if a]
    return thisPluginUrl+("/".join([base]+args))

@isUrl('main_menu_ipod')
def menuipod(m):
    MyAddDirectoryItem(make_Url(ListAllArtists,m),"All artists",isFolder=True)

#queries: artists

@isUrl('all_artists')
def ListAllArtists(mp):
    d = shelve.open(ipodDB)
    artists = d[mp]
    ViewListArtists(mp,sorted(artists))
    d.close()

def ViewListArtists(mp,artistList):
    for a in artistList:
        if a:
            MyAddDirectoryItem(make_Url(ListAllAlbumsFromArtist,mp,a),a,isFolder=True)
    xbmcplugin.endOfDirectory(thisPlugin)

#queries: albums

def ViewListAlbums(mp,artist,albumlist):
    for a in albumlist:
        if a:
            MyAddDirectoryItem(make_Url(ListAllSongsFromAlbum,mp,artist,a),a,isFolder=True)
    xbmcplugin.endOfDirectory(thisPlugin)


@isUrl('albums_from_artist')
def ListAllAlbumsFromArtist(mp,artist):
    d = shelve.open(ipodDB)
    artists = d[mp]
    d.close()
    ViewListAlbums(mp,artist,sorted(artists[artist]['albums']))


#queries: songs

@isUrl('songs_from_album')
def ListAllSongsFromAlbum(mp,artist,album):
    d = shelve.open(ipodDB)
    artists = d[mp]
    d.close()
    ViewListSongs(sorted(artists[artist]['albums'][album]['songs'],key=lambda s1: s1['track number']))


def ViewListSongs(songs):
    for s in songs:
        MyAddDirectoryItem(s['file'],s['title'])
    xbmcplugin.endOfDirectory(thisPlugin)

@isUrl('list_ipods')
def firstLevel():
	ipodList = [m for m in sys_utils.get_mounts() if os.path.exists(os.path.join(m,'iPod_Control','iTunes','iTunesDB'))]
	for m in ipodList:
		copyInfo(m)
		MyAddDirectoryItem(make_Url(menuipod,m),m,isFolder=True)

def main(a1,a2):
    global thisPlugin
    thisPlugin = int(a2)

    call_Url(a1)

main(sys.argv[0],sys.argv[1])

xbmcplugin.endOfDirectory(addon_handle)
