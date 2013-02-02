# -*- coding: utf-8 -*-
import re
import urllib2
import time, os, re
from Cookie import BaseCookie
import plistlib
from datetime import datetime, timedelta

from constants2 import *

#from CrunchyrollUserAPI import *
#from CrunchyrollDataAPI import *
#from DebugCode import *
#from Artwork import *

HTTP.CacheTime = 3600
HTTP.Headers["User-Agent"] = "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_6; en-gb) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16"
HTTP.Headers["Accept-Encoding"] = "gzip, deflate"


def testEmbed(mediaId):
    """
    just a simple test of the ajax request to get the html for embedding a 720p video....
    """
    login()
    
    try:
        valuesDict = { "req": "RpcApiMedia_GetEmbedCode", "media_id": str(mediaId), "width": "1280", "height": "752" }
        response = makeAPIRequest(valuesDict)
#        Log.Debug(response)
        response = JSON.ObjectFromString(response)
        
        Log.Debug("response...")
        if response.get('result_code') == 1:
            Log.Debug(response.get('data'))
        else:
            Log.Debug("bad....")
    except Exception, arg:
        Log.Error("####Sorry, an error occured when logging in:")
        Log.Error(repr(Exception) + " "  + repr(arg))
    
    return


def Start():
    """
    Let's roll.
    """
    Plugin.AddPrefixHandler(CRUNCHYROLL_PLUGIN_PREFIX, TopMenu, "CrunchyRoll", CRUNCHYROLL_ICON, CRUNCHYROLL_ART)
    Plugin.AddViewGroup("List", viewMode = "List", mediaType = "List")
    MediaContainer.art = R(CRUNCHYROLL_ART)
    MediaContainer.title1 = "CrunchyRoll"
    MediaContainer.viewGroup = "List"
    DirectoryItem.thumb = R(CRUNCHYROLL_ICON)
    
    if Dict['Authentication'] is None:
        resetAuthInfo()
        
    
    Dict['episodes'] = None
    Dict['series'] = None
    Dict['seasons'] = None
    #loginAtStart()
    if 'episodes' not in Dict:
        Dict['episodes'] = {}
    if 'series' not in Dict:
        Dict['series'] = {}
    if 'fanart' not in Dict:
        Dict['fanart'] = {}
    if 1==0:
        testCacheAll()
    if False is True:
        cacheAllSeries()
        listAllEpTitles()
    
    if False: # doesn't work because cache won't accept a timeout value
        for cacheThis in PRECACHE_URLS:
            HTTP.PreCache(cacheThis, cacheTime=60*60*10)

def ValidatePrefs():
    u = Prefs['username']
    p = Prefs['password']
    h = Prefs['quality']
    if u and p:
        loginSuccess = login(force = True)
        if not loginSuccess:
            mc = MessageContainer("Login Failure",
                "Failed to login, check your username and password, and that you've read your confirmation email."
                )
            return mc
        else:
            mc = MessageContainer("Success",
                "Preferences Saved."
                )
            return mc

    elif u or p:
        mc = MessageContainer("Login Failure",
            "Please specify both a username and a password."
            )
        return mc
    else:
        # no username or password
        try:
            logout()
        except: pass
        
        if Prefs['quality'] != "SD": # and Prefs['quality'] != "Highest Available":
            mc = MessageContainer("Quality Warning", "Only premium members can watch in high definition. Your videos will show in standard definiton only.")
        else:
            mc = MessageContainer("Success",
                "Preferences Saved."
                )
        return mc



def TopMenu():
    "from which all greatness springs."
    login()

    Log.Debug("art: %s"%R(CRUNCHYROLL_ART))

    dir = MediaContainer(disabledViewModes=["Coverflow"], title1="Crunchyroll", noCache=True)
    
    # show queue menu even if not logged in, since the cache will keep it hidden
    # if user logs in later. Not ideal, but whatev. CR.com gets some advertising.
    if isRegistered():
        dir.Append(Function(DirectoryItem(QueueMenu,"View Queue", thumb=R(QUEUE_ICON), ART=R(CRUNCHYROLL_ART))))
        
    dir.Append(Function(DirectoryItem(RecentAdditionsMenu,"Recent Additions", title1="Recent Additions", thumb=R(CRUNCHYROLL_ICON), art=R(CRUNCHYROLL_ART))))
    dir.Append(Function(DirectoryItem(PopularVideosMenu,"Popular Videos", title1="Popular Videos", thumb=R(CRUNCHYROLL_ICON), art=R(CRUNCHYROLL_ART))))    
    dir.Append(Function(DirectoryItem(BrowseMenu,"Browse Anime", title1="Anime", thumb=R(ANIME_ICON), art=R(CRUNCHYROLL_ART)), type=ANIME_TYPE))
    dir.Append(Function(DirectoryItem(BrowseMenu,"Browse Drama", title1="Drama", thumb=R(DRAMA_ICON), art=R(CRUNCHYROLL_ART)), type=DRAMA_TYPE))
    dir.Append(Function(InputDirectoryItem(SearchMenu, "Search...", thumb=R(SEARCH_ICON), prompt=L("Search for videos..."), ART=R(CRUNCHYROLL_ART))))

    dir.Append(PrefsItem(L('Preferences...'), thumb=R(PREFS_ICON), ART=R(CRUNCHYROLL_ART)))

    if ENABLE_DEBUG_MENUS:
        dir.Append(Function(DirectoryItem(DebugMenu, "Debug...", thumb=R(DEBUG_ICON)), advanced=True) )
    elif ENABLE_UTILS:
        # limited set of utilities, for production
        dir.Append(Function(DirectoryItem(DebugMenu, "Utilities...", thumb=R(UTILS_ICON)), advanced=False))    

    return dir

def QueueMenu(sender):
    """
    Show series titles that the user has in her queue
    """
    # FIXME plex seems to cache this, so removing/adding doesn't give feedback
    if isRegistered():
        dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="Series", noCache=True)
        queueList = GetQueueList()
        for queueInfo in queueList:
            dir.Append(MakeQueueMenuItem(queueInfo))
        return dir
    else:
        return MessageContainer("Log in required", "You must be logged in to view your queue.")

def QueueEntryMenu(sender,queueInfo):
    """
    show episodes in a queued series that are ready to watch. Also,
    allow user to remove the series from queue or view the
    entire series if she wishes.
    """
    dir = MediaContainer(title1="Play Options",title2=sender.itemTitle,disabledViewModes=["Coverflow"], noCache=True)
#    seriesurl = seriesTitleToUrl(queueInfo['title'])
    s = Dict['series']
    sId = str(queueInfo['seriesId'])
    series = GetSeriesDict(sId)
    for seasonId in series['seasonList']:
		cacheEpisodeListForSeason(seasonId)
		
    thumb = getSeriesThumbUrl(series)#(s[sId]['thumb'] if (sId in s and s[sId]['thumb'] is not None) else R(CRUNCHYROLL_ICON))
    art = getSeriesArtUrl(series)#(s[sId]['art'] if (sId in s and s[sId]['art'] is not None) else R(CRUNCHYROLL_ART))
    if queueInfo['upNextMediaId'] is not None:
        nextEp = GetEpisodeDict(queueInfo['upNextMediaId'])#getEpInfoFromLink(queueInfo['epToPlay'])
        PlayNext = MakeEpisodeItem(nextEp)
        dir.Append(PlayNext)
    RemoveSeries = Function(DirectoryItem(RemoveFromQueue, title="Remove series from queue"), seriesId=sId)
    ViewSeries = Function(DirectoryItem(SeriesMenu, "View Series", thumb=thumb, art=Function(getArt,url=art)), seriesId=queueInfo['seriesId'])
    dir.Append(RemoveSeries)
    dir.Append(ViewSeries)
    dir.noCache = 1
    return dir

def PopularVideosMenu(sender):
    """
    show popular videos.
    """
    episodeList = GetPopularVideos()
    if episodeList:
        dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="Popular")
        for episode in episodeList:
            dir.Append(MakeEpisodeItem(episode))
        dir.noCache = 1
        return dir
    else:
        return MessageContainer("No recent additions", "No recent videos found.")
    
def RecentAdditionsMenu(sender):
    """
    show recently added videos
    """
    episodeList = GetRecentVideos()
    if episodeList:
        dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="Recent")
        for episode in episodeList:
            dir.Append(MakeEpisodeItem(episode))
        dir.noCache = 1
        return dir
    else:
        return MessageContainer("No recent additions", "No recent videos found.")

def SearchMenu(sender, query=""):
    """
    search cruncyroll.com/rss and return results in a media container
    """
    episodeList = GetEpisodeListFromQuery(query)
    if episodeList:
        dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2=query)
        for episode in episodeList:
            if episode.has_key('seriesTitle') and episode['seriesTitle'].lower() not in episode['title'].lower():
                episode['title'] = episode['seriesTitle'] + ": " + episode['title']
            dir.Append(MakeEpisodeItem(episode))
    else:
        dir = MessageContainer("Nothing Found", "Could not find what you were looking for. Apologies.")
    
    return dir    
    
def BrowseMenu(sender,type=None):
    """
    Show menu for browsing content of type=ANIME_TYPE or DRAMA_TYPE
    """
    if type==ANIME_TYPE:
        all_icon = ANIME_ICON
    elif type==DRAMA_TYPE:
        all_icon = DRAMA_ICON
        
    dir = MediaContainer(disabledViewModes=["coverflow"], title1="Browse %s" % type)
    
    dir.Append(Function(DirectoryItem(AlphaListMenu,"All", title1="All", thumb=R(all_icon)), type=type))
    dir.Append(Function(DirectoryItem(RecentListMenu,"Recent", title1="Recent", thumb=R(all_icon)), type=type))
    dir.Append(Function(DirectoryItem(PopularListMenu,"Popular" , title1="Popular", thumb=R(all_icon)), type=type))
    dir.Append(Function(DirectoryItem(GenreListMenu,"by Genre", title1="by Genre", thumb=R(CRUNCHYROLL_ICON)), type=type))
    #dir.noCache = 1
    return dir

def AlphaListMenu(sender,type=None,query=None):
    """
    Browse using the alphabet.
    """
    if query is not None:
        startTime = Datetime.Now()
        if query=="#":
            queryCharacters = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')
        elif query=="All":
            queryCharacters = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z')
        else:
            queryCharacters = (query.lower(), query.upper())
        dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2=query)
        if type==ANIME_TYPE:
            seriesList = GetAnimeSeriesList()
        elif type==DRAMA_TYPE:
            seriesList = GetDramaSeriesList()
        else:
            seriesList = GetAllSeries()

        seriesList = sorted(seriesList, key=lambda k: getSortTitle(k)) 
                   
        for series in seriesList:
            sortTitle =  getSortTitle(series)
            if sortTitle.startswith(queryCharacters):
                dir.Append(MakeSeriesItem(series))
        dtime = Datetime.Now()-startTime
        Log.Debug("AlphaListMenu %s (%s) execution time: %s"%(type, query, dtime))
        #listThumbs2()    
    else:
        dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2=sender.itemTitle)
        characters = ['All', '#', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
        for character in characters:
            dir.Append(Function(DirectoryItem(AlphaListMenu,"%s" % character, thumb=R(CRUNCHYROLL_ICON)), type=type, query=character))
    return dir

def RecentListMenu(sender, type=None):
    startTime = Datetime.Now()
    dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="Recent")
    episodeList = []
    if type==ANIME_TYPE:
        episodeList = GetRecentAnimeEpisodes()
    elif type==DRAMA_TYPE:
        episodeList = GetRecentDramaEpisodes()
    else:
        episodeList = GetRecentVideos()
        
    for episode in episodeList:
        dir.Append(MakeEpisodeItem(episode))

    dtime = Datetime.Now()-startTime
    Log.Debug("RecentListMenu %s execution time: %s"%(type, dtime))
    return dir

def PopularListMenu(sender,type=None):
    #FIXME: support drama popular, too?
    startTime = Datetime.Now()
    dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="Popular")
    seriesList = []
    if type==ANIME_TYPE:
        seriesList = GetPopularAnimeSeries()
    elif type==DRAMA_TYPE:
        seriesList = GetPopularDramaSeries()
    else:
        seriesList = GetPopularVideos()
        
    for series in seriesList:
        dir.Append(MakeSeriesItem(series))
    dtime = Datetime.Now()-startTime
    Log.Debug("PopularListMenu %s execution time: %s"%(type, dtime))
    return dir

def GenreListMenu(sender,type=None,genre=None):
    """
    Browse type of series (ANIME_TYPE or DRAMA_TYPE) by a genre key that
    exists in DRAMA_GENRE_LIST or ANIME_GENRE_LIST
    """
    #example: http://www.crunchyroll.com/boxee_feeds/genre_drama_romance
    startTime = Datetime.Now()
    genreList = ANIME_GENRE_LIST if type==ANIME_TYPE else DRAMA_GENRE_LIST
    if genre is not None:
        dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2=genre)
            
        if type == ANIME_TYPE:
            seriesList = GetAnimeSeriesByGenre(genre)
        elif type == DRAMA_TYPE:
            seriesList = GetDramaSeriesByGenre(genre)
        else:
            seriesList = GetSeriesByGenre(genre)
            
        for series in seriesList:
            dir.Append(MakeSeriesItem(series))
        dtime = Datetime.Now()-startTime
        Log.Debug("GenreListMenu %s (%s) execution time: %s"%(type, genre, dtime))
    else:
        dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2=sender.itemTitle)
        keyList = genreList.keys()
        keyList.sort()
        for genre in keyList:
            #Log.Debug("genre: %s" % genre)
            dir.Append(Function(DirectoryItem(GenreListMenu,"%s" % genre, thumb=R(CRUNCHYROLL_ICON)), type=type, genre=genre))
    return dir
   
def SeriesMenu(sender,seriesId=None, seriesTitle="Series"):
    """
    show the episodes available for seriesId. Use seriesTitle for
    the breadcrumb display.
    """
    startTime = Datetime.Now()
    dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2=seriesTitle)
    
    if login() and isRegistered():
        dir.Append(
            Function(PopupDirectoryItem(
                    QueueChangePopupMenu, 
                    title="Queue...", 
                    summary="Add or remove this series from your queue."
                ), 
                seriesId=seriesId )
            )

    Log.Debug("Loading episode list for series number " + str(seriesId))
    seasonList = GetListOfSeasonsInSeries(seriesId)
#    Log.Debug("season nums: %s" % seasonNums)
    for seasonId in seasonList:
        season = GetSeasonDict(seasonId)
        dir.Append(MakeSeasonItem(season))
    dtime = Datetime.Now()-startTime
    Log.Debug("SeriesMenu (%s) execution time: %s"%(seriesId, dtime))
    return dir

def SeasonMenu(sender,seasonId):
    """
    Display a menu showing episodes available in a particular season.
    """
    Log.Debug(str(seasonId))
    season = GetSeasonDict(seasonId)
    dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="%s - Season %s"%(sender.title2,str(season['seasonNumber'])))
    epList = GetListOfEpisodesInSeason(seasonId)#getEpisodeListForSeason(seasonId)
    Log.Debug("len %s"%str(len(epList)))
    
    for episodeId in epList:
        episode = GetEpisodeDict(episodeId)
#        Log.Debug(episode)
        dir.Append(MakeEpisodeItem(episode))
    return dir

def AdultWarning(sender, rating=5):
    """
    return a message container warning the user that she's about to 
    try something naughty, and if she wants to do this naughty thing,
    she must give herself permission to do it.
    """
    return MessageContainer("Adult Content", "Cannot play mature content unless you change your preferences.")

def NotAvailable(sender, reason):
    return MessageContainer("Not Available", reason)

def RemoveFromQueue(sender,seriesId):
    """
    remove seriesID from queue
    """
    login()
    result = removeFromQueue(seriesId)
    if result:
        return MessageContainer("Success",'Removed from Queue')
    else:
        return MessageContainer("Failure", 'Could not remove from Queue.')

def AddToQueue(sender,seriesId,url=None):
    """
    Add seriesId to the queue.
    """
    login()
    result = addToQueue(seriesId)
    
    if result:
        return MessageContainer("Success",'Added to Queue')
    else:
        return MessageContainer("Failure", 'Could not add to Queue.')

def QueueChangePopupMenu(sender, seriesId):
    """
    Popup a Menu asking user if she wants to
    add or remove this series from her queue
    """
    login()
    dir = MediaContainer(title1="Queue",title2=sender.itemTitle,disabledViewModes=["Coverflow"])
    if isRegistered():
        queueList = GetQueueList()
        inQ = False
        for item in queueList:
            if item['seriesId'] == seriesId:
                inQ = True
            break
        
        if inQ:
            dir.Append(
                Function(DirectoryItem(RemoveFromQueue, title="Remove From Queue", summary="Remove this series from your queue"), seriesId=seriesId)
            )
        else:
            dir.Append(
                Function(DirectoryItem(AddToQueue, title="Add To Queue", summary="Add this series to your queue" ), seriesId=seriesId)
            )
    return dir


def PlayVideoMenu(sender, mediaId):
    """
    construct and return a MediaContainer that will ask the user
    which resolution of video she'd like to play for episode
    """
    episode = GetEpisodeDict(mediaId)
    startTime = Datetime.Now()
    dir = MediaContainer(title1="Play Options",title2=sender.itemTitle,disabledViewModes=["Coverflow"])
    if len(episode['availableResolutions']) == 0:
        episode['availableResolutions'] = GetAvailResForMediaId(mediaId)
        
        # FIXME I guess it's better to have something than nothing? It was giving Key error
        # on episode number (kinda silly now since we require the cache...)
        if str(mediaId) not in Dict['episodes']:
            Dict['episodes'][str(mediaId)] = episode
    
        Dict['episodes'][str(mediaId)]['availableResolutions'] = episode['availableResolutions']
    videoInfo = GetVideoInfo(mediaId, episode['availableResolutions'])
    videoInfo['small'] = (hasPaid() and isPremium(episode.get("category"))) is False

    # duration must be specified before the redirect in PlayVideo()! If not, your device
    # will not recognize the play time.
    try:
        duration = int(episode.get('duration'))
    except TypeError:
        duration = 0

    if Prefs['quality'] == "Ask":
        for q in episode['availableResolutions']:
            videoUrl = GetVideoUrl(videoInfo, q)
            episodeItem = Function(WebVideoItem(PlayVideo, title=Resolution2Quality[q], duration=duration), mediaId=mediaId, resolution=q )
            dir.Append(episodeItem)
    else:
        prefRes = GetPrefRes(episode['availableResolutions'])
        videoUrl = GetVideoUrl(videoInfo, prefRes)
        buttonText = "Play at %sp" % str(prefRes)
        episodeItem = Function(WebVideoItem(PlayVideo, title=buttonText, duration=duration), mediaId=mediaId, resolution = prefRes)
        dir.Append(episodeItem)
    dtime = Datetime.Now()-startTime
    Log.Debug("PlayVideoMenu (%s) execution time: %s"%(episode['title'], dtime))
    return dir

def PlayVideo(sender, mediaId, resolution=360): # url, title, duration, summary = None, mediaId=None, modifyUrl=False, premium=False):
    from datetime import datetime
    
    if Prefs['restart'] == "Restart":
        deleteFlashJunk()

    episode = GetEpisodeDict(mediaId)
    if episode:
        
        cat = episode.get("category")
        if cat == "Anime":
            checkCat = ANIME_TYPE
        elif cat == "Drama":
            checkCat = DRAMA_TYPE
        else:
            checkCat = None

                    
        if hasPaid() and isPremium(checkCat):
            return PlayVideoPremium(sender, mediaId, resolution) #url, title, duration, summary=summary, mediaId=mediaId, modifyUrl=modifyUrl, premium=premium)
        else:
            return PlayVideoFreebie(sender, mediaId) # (sender,url, title, duration, summary=summary, mediaId=mediaId, modifyUrl=modifyUrl, premium=premium)
    else:
        # hm....
        return None # messagecontainer doesn't work here.
        
def PlayVideoPremium(sender, mediaId, resolution):
    # It's really easy to set resolution with direct grab of stream.
    # Only premium members get better resolutions.
    # so the solution is to have 2 destinations: freebie (web player), or premium (direct).

    login()
    episode = GetEpisodeDict(mediaId)
    theUrl = MEDIA_URL + str(mediaId)
    resolutions = GetAvailResForMediaId(mediaId)
    vidInfo = GetVideoInfo(mediaId, resolutions)
    vidInfo['small'] = 0

    if episode.get('duration') and episode['duration'] > 0:
        duration = episode['duration']
    else:
        duration = vidInfo['duration'] # need this because duration isn't known until now

    bestRes = resolution

    if Prefs['quality'] != "Ask":
        bestRes = GetPrefRes(resolutions)
    
    bestRes = int(bestRes)
    
    Log.Debug("Best res: " + str(bestRes))

    # we need to tell server so they send the right quality
    setPrefResolution(int(bestRes))
            
    # FIXME: have to account for drama vs anime premium!
    modUrl = GetVideoUrl(vidInfo, bestRes) # get past mature wall... hacky I know
    
    req = HTTP.Request(modUrl, immediate=True, cacheTime=10*60*60)    #hm, cache time might mess up login/logout

    match = re.match(r'^.*(<link *rel *= *"video_src" *href *= *")(http:[^"]+).*$', repr(req.content), re.MULTILINE)
    if not match:
        # bad news
        Log.Error("###########Could not find direct swf link, trying hail mary pass...")
        Log.Debug(req.content)
        theUrl = theUrl
    else:
        theUrl = match.group(2)    + "&__qual=" + str(bestRes)

    # try a manual redirect since redirects crash entire PMS
    import urllib2
    req = urllib2.urlopen(theUrl)
    theUrl = req.geturl() 
    req.close()
    
    Log.Debug("##########final URL is '%s'" % theUrl)
    #Log.Debug("##########duration: %s" % str(duration))
    
    testEmbed(mediaId)

    return Redirect(WebVideoItem(theUrl, title = episode['title'], duration = duration, summary = makeEpisodeSummary(episode) ))
    
def PlayVideoFreebie(sender, mediaId):
    """
    Play a freebie video using the direct method. As long as crunchyroll.com delivers ads
    through the direct stream (they do as of Feb 14 2012), this is okay IMO. This gets
    around crashes with redirects/content changes of video page, and sacrifices the ability
    to use javascript in the site config.
    """
    episode = GetEpisodeDict(mediaId)
    infoUrl = MEDIA_URL + str(mediaId) + "?p360=1&skip_wall=1&t=0&small=0&wide=0"

    req = HTTP.Request(infoUrl, immediate=True, cacheTime=10*60*60)    #hm, cache time might mess up login/logout

    match = re.match(r'^.*(<link *rel *= *"video_src" *href *= *")(http:[^"]+).*$', repr(req.content), re.MULTILINE)
    if not match:
        # bad news
        Log.Error("###########Could not find direct swf link, trying hail mary pass...")
        Log.Debug(req.content)
        theUrl = infoUrl
    else:
        theUrl = match.group(2)    + "&__qual=360"

    Log.Debug("###pre-redirect URL: %s" % theUrl)

    # try a manual redirect since redirects crash entire PMS
    import urllib2
    req = urllib2.urlopen(theUrl)
    theUrl = req.geturl() 
    req.close()

    Log.Debug("####Final URL: %s" % theUrl)
    duration = episode.get('duration')
    if not duration:  duration = 0
    
    return Redirect(WebVideoItem(theUrl, title = episode['title'], duration = duration, summary = makeEpisodeSummary(episode) ))
    

def getSortTitle(dictList):
    """
    get the 'title' key and return the sortable title as string
    """
    title = dictList['title'].lower().strip()
    firstword = title.split(" ",1)[0]
    if firstword in ['a', 'an', 'the']:
        title = title.split(firstword, 1)[-1]
    return title.strip()


def MakeSeriesItem(series):
    """
    create a directory item out of the passed dict 
    that the user can click on to enter its episode list
    """
    artUrl = getSeriesArtUrl(series)
    thumbUrl = getSeriesThumbUrl(series)

    try:
        summaryString = series['description'].encode("utf-8")
    except AttributeError:
        summaryString = ""
        
    # check the rating
    if Prefs['hideMature'] is True and series['simpleRating'] and series['simpleRating'] == 'adult':
        seriesItem = Function(DirectoryItem(
            AdultWarning,
            title = series['title'],
            summary = createRatingString(series['rating']) + summary,
            thumb = Function(getThumb,url=thumbUrl),
            art=Function(getArt,url=artUrl)
            ),
            rating = episode['rating']
        )
        return seriesItem
    
    seriesItem =  Function(
        DirectoryItem(
            SeriesMenu, 
            title = series['title'],
            summary=summaryString,
            thumb=Function(getThumb,url=thumbUrl),
            art = Function(getArt,url=artUrl)),
        seriesId=series['seriesId'],
        seriesTitle=series['title'])
    return seriesItem

def MakeSeasonItem(season):
    """
    Create a directory item showing a particular season in a series.
    Seasons contain episodes, so this passes responsibility on to
    SeasonMenu() to construct that list.
    """
    artUrl = getSeasonArtUrl(season)
    thumbUrl = getSeasonThumbUrl(season)
    
    seasonItem = Function(
        DirectoryItem(
            SeasonMenu,
            season['title'],
            summary=season['description'].encode("utf-8"),
            thumb=Function(getThumb,url=thumbUrl),
            art=Function(getArt,url=artUrl)),
        seasonId=season['seasonId'])
    return seasonItem

def MakeEpisodeItem(episode):
    """
    Create a directory item that will play the video.
    If the user is logged in and has requested to choose resolution,
    this will lead to a popup menu. In all other cases, the user
    need not make a choice, so go straight to the video (with a little
    URL munging beforehand in PlayVideo())
    """
    
    giveChoice = True
    if not hasPaid() or Prefs['quality'] != "Ask":
        #Log.Debug("Quality is not Ask")
        giveChoice = False
    elif not Prefs['password'] or not Prefs['username']:
        Log.Debug("User wants to choose res, but password is missing")
        giveChoice = False
    else:
        # we need to check if this content has higher res for premium users
        giveChoice = False

        kind = str(episode.get('category'))
        
        if kind.lower() == "anime":
            giveChoice = isPremium(ANIME_TYPE)
        elif kind.lower() == "drama":
            giveChoice = isPremium(DRAMA_TYPE)
        else:
            giveChoice = True # no category, so assume they get the choice.
    
    cat = episode.get("category")
    
    if cat == "Anime":
        checkCat = ANIME_TYPE
    elif cat == "Drama":
        checkCat = DRAMA_TYPE
    else:
        checkCat = None
    
    available = True
    reason = "No date, assuming it's available"

    if hasPaid() and isPremium(checkCat):
        availableAt = episode.get("premiumPubDate")
        if availableAt != None:
            if availableAt < datetime.utcnow():
                available = True
            else:
                available = False
                reason = "This video will be aired for premium users on %s GMT." % availableAt.strftime("%a, %d %b %Y %H:%M:%S %Z")
    else:
        availableAt = episode.get("freePubDate")
        if availableAt != None:
            if availableAt < datetime.utcnow():
                available = True
            else:
                available = False
                # anything over 60 days we can call "unavailable". This eliminates crazy
                # "available in year 2043" messages
                if (availableAt - datetime.utcnow()).days > 60:
                    reason = "Sorry, this video is currently unavailable to free users."
                else:
                    timeString = availableAt.strftime("%a, %d %b %Y %H:%M:%S %Z") + " GMT"
                    reason = "Sorry, this video will be available for free users on %s" % timeString
    
    summary = createRatingString(episode['rating']) + makeEpisodeSummary(episode)

    if not available:
        episodeItem = Function(DirectoryItem(
                        NotAvailable,
                        title = episode['title'] + " (Not Yet Available)",
                        subtitle = "Season %s"%episode['season'],
                        summary = summary,
                        thumb = Function(getThumb,url=getEpisodeThumbUrl(episode)),
                        art=Function(getArt,url=getEpisodeArtUrl(episode))
                        ),
                        reason = reason
                    )
        return episodeItem

    # check the rating
    if Prefs['hideMature'] is True and episode['simpleRating'] and episode['simpleRating'] == 'adult':
        episodeItem = Function(DirectoryItem(
            AdultWarning,
            title = episode['title'],
            subtitle = "Season %s"%episode['season'],
            summary = summary,
            thumb = Function(getThumb,url=getEpisodeThumbUrl(episode)),
            art=Function(getArt,url=getEpisodeArtUrl(episode))
            ),
            rating = episode['rating']
        )
        return episodeItem
    
    
    if giveChoice:
        episodeItem = Function(
            PopupDirectoryItem(
                PlayVideoMenu,
                title = episode['title'],
                subtitle = "Season %s"%episode['season'],
                summary = summary,
                thumb = Function(getThumb,url=getEpisodeThumbUrl(episode)),
                art=Function(getArt,url=getEpisodeArt(episode)),                
            ),
            mediaId=episode['mediaId']
        )
    else:
        duration = episode.get('duration')
        if not duration:
            duration = 0
        episodeItem = Function(
            WebVideoItem(PlayVideo, 
                title = episode['title'],
                subtitle = "Season %s"%episode['season'],
                summary = summary,
                thumb = Function(getThumb,url=getEpisodeThumbUrl(episode)),
                art=Function(getArt,url=getEpisodeArtUrl(episode)),
                duration = duration
            ), 
                mediaId=episode['mediaId']
        )
    return episodeItem


def createRatingString(ratingLevel, append="\n"):
    """
    Given a safe surf rating level integer, return a human-understandable string in a form like:
    [PG-14]. Note: THESE ARE APPROXIMATIONS. Some Tv-14 content shows up as G!
    It also appends a linefeed if there is indeed a rating. If you need a better character to append,
    use append=whateveryourstringis.
    """
    theString ="["
    if ratingLevel and SAFESURF_MAP.has_key(ratingLevel):
        theString = theString + SAFESURF_MAP[ratingLevel]
        theString = theString + "]" + append
        return theString
    else:
        return "[NR]" + append
        
def makeEpisodeSummary(episode):
    """
    construct a string summarizing the episode using its metadata,
    or just return the episode's description if needed.
    """
    # using inverted pyramid strategy; more detail at bottom of description
    summary = episode['description'] + "\n\n"
    if episode['publisher'] != '':
        summary = "%sPublisher: %s\n" % (summary, episode['publisher'])
    if episode['season'] != '':
        summary = "%sSeason: %s\n" % (summary, episode['season'])
#    if episode['keywords'] != '':
#        summary = "%sKeywords: %s\n" % (summary, episode['keywords'])
    if summary != '':
        summary = "%s\n%s" % (summary, episode['description'])

    #Log.Debug(summary)
    return summary

def MakeQueueMenuItem(queueInfo):
    """
    construct a directory item for a series existing in user's queue.
    Selecting this item leads to more details about the series, and the ability
    to remove it from the queue.
    """
    Log.Debug("queueinfo: %s" % queueInfo)
    series = GetSeriesDict(queueInfo['seriesId'])
    thumb = getSeriesThumbUrl(series)#(s[sId]['thumb'] if (sId in s and s[sId]['thumb'] is not None) else R(CRUNCHYROLL_ICON))
    art = getSeriesArtUrl(series)#(s[sId]['art'] if (sId in s and s[sId]['art'] is not None) else R(CRUNCHYROLL_ART))
    queueItem = Function(DirectoryItem(
        QueueEntryMenu,
        title=queueInfo['title'],
        summary=series['description'],#queueInfo['nextUpText'] + queueInfo['episodeDescription'],
        thumb=Function(getThumb,url=thumb),
        art=Function(getArt,url=art)
        ), queueInfo=queueInfo)
    return queueItem


"""
                "title": title,
                "upNextMediaId": episodeMediaId,
                "seriesId": seriesId#,
"""
"""
schema inside Dict{}
    all items (even movies) can be referenced by a the series dict.
    series are known by seriesID (a unique number), provided by crunchyroll.com
    Dict['series'] =
    { seriesId: {
        "title": title,
        "seriesId": seriesId,
        "tvdbId": tvdbId,
        "description": seriesDescription,
        "thumb": thumb,
        "art": art,
        "rating": rating,
        "simpleRating": simpleRating,
        "dateUpdated": dateUpdated,
        "seasonList": []
        }
    }
"""
"""
    Dict['seasons'] =
    { seasonId: {
        "title": title,
        "seasonId": seasonId,
        "seriesId": seriesId,
        "thumb": thumb,
        "art": art,
        "epsRetreived": None,
        "epList": [],
        "dateUpdated": dateUpdated,
        "seasonNumber": seasonNumber,
        "description": description
        }
    }
"""
""" 
    episodesList contains playable media (it's actually a dict, but let's not get finicky).
    episodes are known by mediaId (a unique number), provided at crunchyroll.com
    This is an episode entry in the list:
    Dict['episodes'] =
    { mediaId: {
        "title": episodeTitle,
        "description": episodeDescription,
        "mediaId": mediaId,
        "episodeNumber": episodeNumber,
        "freePubDate": freePubDate,
        "freePubDateEnd": freePubDateEnd,
        "premiumPubDate": premiumPubDate,
        "premiumPubDateEnd": premiumPubDateEnd,
        "publisher": publisher,
        "duration": duration,
        "subtitleLanguages": subtitleLanguages,
        "rating": rating,
        "simpleRating": simpleRating,
        "countries": countries,
        "dateUpdated": dateUpdated,
        "season": season,
        "seasonId": seasonId,
        "mediaLink": mediaLink,
        "category": category,
        "thumb": thumb,
        "art": art,
        "seriesTitle": seriesTitle,
        "availableResolutions": availableResolutions
        }
    }
"""

def debugFeedItem(item):
    for sub in list(item):
        text1 = "%s: %s" % (sub.tag, sub.text)
        Log.Debug(text1)
        for sub2 in list(sub):
            text2 = "\t%s/%s: %s\n%s" % (sub.tag, sub2.tag, sub2.text, list(sub2))
            Log.Debug(text2)
            for sub3 in list(sub2):
                text3 = "\t\t%s/%s/%s: %s\n%s" % (sub.tag, sub2.tag, sub3.tag, sub3.text, list(sub3))
                Log.Debug(text3)
                for sub4 in list(sub3):
                    text4 = "\t\t\t%%s/%s/%s: %s\n%s" % (sub.tag, sub2.tag, sub3.tag, sub4.tag, sub4.text, list(sub4))
                    Log.Debug(text4)


PLUGIN_NAMESPACE = {"media":"http://search.yahoo.com/mrss/", "crunchyroll":"http://www.crunchyroll.com/rss"}

def cacheFullSeriesList():
    #startTime = Datetime.Now()
    PLUGIN_NAMESPACE = {"media":"http://search.yahoo.com/mrss/", "crunchyroll":"http://www.crunchyroll.com/rss"}
    feedHtml = XML.ElementFromURL(SERIES_FEED_URL,cacheTime=SERIES_FEED_CACHE_TIME)
#    Log.Debug(str(feedHtml))
    items = feedHtml.xpath("//item")
    if Dict['series'] is None:
        Dict['series'] = {}
    
    if Dict['seasons'] is None:
        Dict['seasons'] = {}
    
    dateUpdated = datetime.utcnow()
    
    for item in items:
#        debugFeedItem(item.xpath("."))
        seasonId = int(item.xpath("./guid")[0].text.split(".com/")[1].split("-")[1])
        try:
            seasonNumber = int(item.xpath("./crunchyroll:season", namespaces=PLUGIN_NAMESPACE)[0].text)
        except:
            seasonNumber = None
        thumb = str(item.xpath("./media:thumbnail", namespaces=PLUGIN_NAMESPACE)[0].get('url')).split("_")[0]+"_full.jpg"
        art = thumb
        seasonTitle = item.xpath("./title")[0].text
        seriesId = int(item.xpath("./crunchyroll:series-guid", namespaces=PLUGIN_NAMESPACE)[0].text.split(".com/series-")[1])
        simpleRating = item.xpath("./media:rating", namespaces=PLUGIN_NAMESPACE)[0].text
        tvdbId = None
        description = item.xpath("./description")[0].text
        seriesDescription = None
        
        if not str(seriesId) in Dict['series'] or Dict['series'][str(seriesId)] is None:
            series = {
                "title": seasonTitle,
                "seriesId": seriesId,
                "tvdbId": tvdbId,
                "description": seriesDescription,
                "thumb": thumb,
                "art": art,
                "rating": None,
                "simpleRating": simpleRating,
                "dateUpdated": dateUpdated,
                "seasonList": []
            }
            Dict['series'][str(seriesId)] = series
        
        if not seasonId in Dict['series'][str(seriesId)]['seasonList']:
            Dict['series'][str(seriesId)]['seasonList'].append(seasonId)
        
        Dict['series'][str(seriesId)]['dateUpdated'] = dateUpdated
        
        if not str(seasonId) in Dict['seasons'] or Dict['seasons'][str(seasonId)] is None:
            season = {
                "title": seasonTitle,
                "seasonId": seasonId,
                "seriesId": seriesId,
                "thumb": thumb,
                "art": art,
                "epsRetreived": None,
                "epList": [],
                "dateUpdated": dateUpdated,
                "seasonNumber": seasonNumber,
                "description": description
            }
            Dict['seasons'][str(seasonId)] = season
        
    
    #make sure that the season list for each series is in order
    for seriesid in Dict['series'].keys():
        series = Dict['series'][seriesid]
#        Log.Debug(series['seasonList'])
        newSeasonList = sorted(series['seasonList'], key=lambda k: Dict['seasons'][str(k)]['seasonNumber'])
        Dict['series'][seriesid]['seasonList'] = newSeasonList
    
def cacheEpisodeListForSeason(seasonId):
    from datetime import datetime, timedelta
#    from collections import OrderedDict
    
    if str(seasonId) in BAD_SEASON_IDS:
    	return
    
    Log.Debug("running cacheEpisodeListForSeason")

    #startTime = Datetime.Now()
    feed =  "%s%s" % (SEASON_FEED_BASE_URL, str(seasonId))
    feedHtml = XML.ElementFromURL(feed,cacheTime=SERIES_FEED_CACHE_TIME)
    items = feedHtml.xpath("//item")
    if len(items) == 0:
    	return
    if Dict['episodes'] is None:
        Dict['episodes'] = {}
    
    dateUpdated = datetime.utcnow()
    
    try:
        rating = feedHtml.xpath("//rating")[0].text
#        Log.Debug(rating)
        
        # see http://www.classify.org/safesurf/
        #SS~~000. Age Range
        #1) All Ages
        #2) Older Children
        #3) Teens
        #4) Older Teens
        #5) Adult Supervision Recommended
        #6) Adults
        #7) Limited to Adults
        #8) Adults Only
        #9) Explicitly for Adults

        # just pluck the age value from text that looks like:
        # (PICS-1.1 &quot;http://www.classify.org/safesurf/&quot; l r (SS~~000 5))
        ageLimit = re.sub(r'(.*\(SS~~\d{3}\s+)(\d)(\).*)', r'\2', rating)
        rating = int(ageLimit) # we don't care about the categories

    except (ValueError, IndexError, TypeError):
        rating = None
    
    seriesTitle = feedHtml.xpath("//crunchyroll:seriesTitle", namespaces=PLUGIN_NAMESPACE)[0].text
    seriesId = Dict['seasons'][str(seasonId)]["seriesId"]
    if not Dict['series'][str(seriesId)]["title"] == seriesTitle:
        Log.Debug("Series (%s) title (%s) does not match the one on the season (%s) feed (%s)." % (str(seriesId), Dict['series'][str(seriesId)]["title"], str(seasonId), seriesTitle))
        Dict['series'][str(seriesId)]["title"] = seriesTitle
    episodeList = Dict['seasons'][str(seasonId)]["epList"]
    for item in items:
        mediaId = int(item.xpath("./crunchyroll:mediaId", namespaces=PLUGIN_NAMESPACE)[0].text)
#        Log.Debug("mediaId: %s"%str(mediaId))
        modifiedDate = item.xpath("./crunchyroll:modifiedDate", namespaces=PLUGIN_NAMESPACE)[0].text
#        Log.Debug(modifiedDate)
        feedEntryModified = datetime.strptime(modifiedDate, "%a, %d %b %Y %H:%M:%S %Z")
        
        if not str(mediaId) in Dict['episodes'] or Dict['episodes'][str(mediaId)]["dateUpdated"] <= feedEntryModified:
            #TODO: should use <title> or <crunchyroll:episodeTitle> for the title?
#            episodeTitle = " "
#            Log.Debug(episodeTitle)
            try: episodeTitle = item.xpath("./crunchyroll:episodeTitle", namespaces=PLUGIN_NAMESPACE)[0].text
            except: episodeTitle = item.xpath("./title")[0].text
            if episodeTitle is None:
            	episodeTitle = item.xpath("./title")[0].text
#            Log.Debug(episodeTitle)
            if episodeTitle.startswith("%s - " % seriesTitle):
                episodeTitle = episodeTitle.replace("%s - " % seriesTitle, "")
            elif episodeTitle.startswith("%s Season " % seriesTitle):
                episodeTitle = episodeTitle.replace("%s Season " % seriesTitle, "")
                episodeTitle = episodeTitle.split(" ", 1)[1].lstrip("- ")

            episodeDescription = item.xpath("./description")[0].text
            if "/><br />" in episodeDescription:
                episodeDescription = episodeDescription.split("/><br />")[1]
            
            try: episodeNumber = int(item.xpath("./crunchyroll:episodeNumber", namespaces=PLUGIN_NAMESPACE)[0].text)
            except: episodeNumber = 0
            freePubDate = datetime.strptime(item.xpath("./crunchyroll:freePubDate", namespaces=PLUGIN_NAMESPACE)[0].text, FEED_DATE_FORMAT)
            freePubDateEnd = datetime.strptime(item.xpath("./crunchyroll:freeEndPubDate", namespaces=PLUGIN_NAMESPACE)[0].text, FEED_DATE_FORMAT)
            premiumPubDate = datetime.strptime(item.xpath("./crunchyroll:premiumPubDate", namespaces=PLUGIN_NAMESPACE)[0].text, FEED_DATE_FORMAT)
            premiumPubDateEnd = datetime.strptime(item.xpath("./crunchyroll:premiumEndPubDate", namespaces=PLUGIN_NAMESPACE)[0].text, FEED_DATE_FORMAT)
            try: publisher = item.xpath("./crunchyroll:publisher", namespaces=PLUGIN_NAMESPACE)[0].text
            except: publisher = ""
            try: duration = int(item.xpath("./crunchyroll:duration", namespaces=PLUGIN_NAMESPACE)[0].text) * 1000
            except: duration = 0
            try: subtitleLanguages = item.xpath("./crunchyroll:subtitleLanguages", namespaces=PLUGIN_NAMESPACE)[0].text.split(",")
            except: subtitleLanguages = ""
            simpleRating = item.xpath("./media:rating", namespaces=PLUGIN_NAMESPACE)[0].text
            countries = item.xpath("./media:restriction", namespaces=PLUGIN_NAMESPACE)[0].text.strip().split(" ")
            try: season = int(item.xpath("./crunchyroll:season", namespaces=PLUGIN_NAMESPACE)[0].text)
            except: season = 0
            mediaLink = item.xpath(EPISODE_MEDIA_LINK_XPATH)[0].text.strip()
            category = item.xpath("./category")[0].text
            try: thumb = str(item.xpath("./enclosure")[0].get('url')).split("_")[0]+"_full.jpg"
            except: thumb = None
            art = thumb
            
            #FIXME: figure out how to deal with video resolutions
            availableResolutions = None
            
            episode = {
                "title": episodeTitle,
                "description": episodeDescription,
                "mediaId": mediaId,
                "episodeNumber": episodeNumber,
                "freePubDate": freePubDate,
                "freePubDateEnd": freePubDateEnd,
                "premiumPubDate": premiumPubDate,
                "premiumPubDateEnd": premiumPubDateEnd,
                "publisher": publisher,
                "duration": duration,
                "subtitleLanguages": subtitleLanguages,
                "rating": rating,
                "simpleRating": simpleRating,
                "countries": countries,
                "dateUpdated": dateUpdated,
                "season": season,
                "seasonId": seasonId,
                "mediaLink": mediaLink,
                "category": category,
                "thumb": thumb,
                "art": art,
                "seriesTitle": seriesTitle,
                "availableResolutions": availableResolutions
            }
            
            Dict['episodes'][str(mediaId)] = episode
            if not str(mediaId) in episodeList:
				episodeList.append(mediaId)
        
#    list(OrderedDict.fromkeys('abracadabra'))
#	episodeList = list(set(episodeList))
    Dict['seasons'][str(seasonId)]["epList"] = episodeList
    Dict['seasons'][str(seasonId)]["epsRetreived"] = dateUpdated
    Dict['seasons'][str(seasonId)]["epList"] = sorted(Dict['seasons'][str(seasonId)]["epList"], key=lambda k: Dict['episodes'][str(k)]["episodeNumber"])
#    
#    
#    @parallelize
#    def parseSeriesItems():
#        for item in items:
#            seriesId = int(item.xpath("./guid")[0].text.split(".com/")[1])
#            @task
#            def parseSeriesItem(item=item,seriesId=seriesId):
#                if not (str(seriesId) in Dict['series']):
#                    title = item.xpath("./title")[0].text
#                    if Prefs['fanart'] is True:
#                        tvdbIdr = tvdbscrapper.GetTVDBID(title, Locale.Language.English)
#                        tvdbId = tvdbIdr['id']
#                    else:
#                        tvdbId = None
#                        
#                    description = item.xpath("./description")[0].text
#                    thumb = str(item.xpath("./property")[0].text).replace("_large",THUMB_QUALITY[Prefs['thumb_quality']])
#                    
#                    if ART_SIZE_LIMIT is False:
#                        art = thumb
#                    else:
#                        art = None
#                    series = {
#                        "title": title,
#                        "seriesId": seriesId,
#                        "tvdbId": tvdbId,
#                        "description": description,
#                        "thumb": thumb,
#                        "art": art
#                    }
#                    dictInfo = series
#                    dictInfo['epsRetrived'] = None
#                    dictInfo['epList'] = []
#                    Dict['series'][str(seriesId)] = dictInfo
#                else:
#                    title = item.xpath("./title")[0].text
#                    thumb = str(item.xpath("./property")[0].text).replace("_large",THUMB_QUALITY[Prefs['thumb_quality']])
#
#                    if ART_SIZE_LIMIT is False:
#                        art = thumb
#                    else:
#                        art = None
#                    seriesDict = Dict['series'][str(seriesId)]
#                    seriesDict['thumb'] = thumb
#                    seriesDict['art'] = art
#                    Dict['series'][str(seriesId)] = seriesDict
#                    series = {
#                        "title": seriesDict['title'],
#                        "seriesId": seriesId,
#                        "tvdbId": seriesDict['tvdbId'],
#                        "description": seriesDict['description'],
#                        "thumb": seriesDict['thumb'],
#                        "art": seriesDict['art']
#                    }
#                seriesList.append(series)

def getEpisodeListFromFeed(feed, sort=True):
#    import datetime
    try:
    	#TODO: find a way to get season/series ids for the episodes....
        episodeList = []
        dateUpdated = datetime.utcnow()
        
        # timeout errors driving me nuts, so
        req = HTTP.Request(feed, timeout=100)
        feedHtml = XML.ElementFromString(req.content)
#        feedHtml = XML.ElementFromURL(feed)
        items = feedHtml.xpath("//item")
#        seriesTitle = feedHtml.xpath("//channel/title")[0].text.replace(" Episodes", "")
        @parallelize
        def parseEpisodeItems():
            for item in items:
                mediaId = int(item.xpath("./guid")[0].text.split("-")[-1])
                feedEntryModified = datetime.strptime(item.xpath("./crunchyroll:modifiedDate", namespaces=PLUGIN_NAMESPACE)[0].text, FEED_DATE_FORMAT)
                @task
                def parseEpisodeItem(item=item,mediaId=mediaId,feedEntryModified=feedEntryModified):
                    if not str(mediaId) in Dict['episodes'] or Dict['episodes'][str(mediaId)]["dateUpdated"] <= feedEntryModified:
                        seriesTitle = item.xpath("./crunchyroll:seriesTitle", namespaces=PLUGIN_NAMESPACE)[0].text
                        #TODO: should use <title> or <crunchyroll:episodeTitle> for the title?
                        title = item.xpath("./crunchyroll:episodeTitle", namespaces=PLUGIN_NAMESPACE)[0].text
#                        if title.startswith("%s - " % seriesTitle):
#                            title = title.replace("%s - " % seriesTitle, "")
#                        elif title.startswith("%s Season " % seriesTitle):
#                            title = title.replace("%s Season " % seriesTitle, "")
#                            title = title.split(" ", 1)[1].lstrip("- ")
                        
                        episodeDescription = item.xpath("./description")[0].text
                        if "/><br />" in episodeDescription:
                            episodeDescription = episodeDescription.split("/><br />")[1]
                        episodeDescription = stripHtml(episodeDescription)
                        
                        try:
                            episodeNumber = int(item.xpath("./crunchyroll:episodeNumber", namespaces=PLUGIN_NAMESPACE)[0].text)
                        except:
                            episodeNumber = None
                        
                        freePubDate = datetime.strptime(item.xpath("./crunchyroll:freePubDate", namespaces=PLUGIN_NAMESPACE)[0].text, FEED_DATE_FORMAT)
                        freePubDateEnd = datetime.strptime(item.xpath("./crunchyroll:freeEndPubDate", namespaces=PLUGIN_NAMESPACE)[0].text, FEED_DATE_FORMAT)
                        premiumPubDate = datetime.strptime(item.xpath("./crunchyroll:premiumPubDate", namespaces=PLUGIN_NAMESPACE)[0].text, FEED_DATE_FORMAT)
                        premiumPubDateEnd = datetime.strptime(item.xpath("./crunchyroll:premiumEndPubDate", namespaces=PLUGIN_NAMESPACE)[0].text, FEED_DATE_FORMAT)
                        try: publisher = item.xpath("./crunchyroll:publisher", namespaces=PLUGIN_NAMESPACE)[0].text
                        except: publisher = ""
                        duration = int(item.xpath("./crunchyroll:duration", namespaces=PLUGIN_NAMESPACE)[0].text) * 1000
                        subtitleLanguages = item.xpath("./crunchyroll:subtitleLanguages", namespaces=PLUGIN_NAMESPACE)[0].text.split(",")
                        simpleRating = item.xpath("./media:rating", namespaces=PLUGIN_NAMESPACE)[0].text
                        countries = item.xpath("./media:restriction", namespaces=PLUGIN_NAMESPACE)[0].text.strip().split(" ")
                        try: season = int(item.xpath("./crunchyroll:season", namespaces=PLUGIN_NAMESPACE)[0].text)
                        except: season = None
                        mediaLink = item.xpath(EPISODE_MEDIA_LINK_XPATH)[0].text.strip()
                        category = item.xpath("./category")[0].text
                        try: thumb = str(item.xpath("./media:thumbnail", namespaces=PLUGIN_NAMESPACE)[0].get('url')).split("_")[0]+THUMB_QUALITY[Prefs['thumb_quality']]+".jpg"
                        except IndexError:
                            if "http://static.ak.crunchyroll.com/i/coming_soon_new_thumb.jpg" in description:
                                thumb = "http://static.ak.crunchyroll.com/i/coming_soon_new_thumb.jpg"
                            else:
                                thumb = "" # FIXME happens on newbie content, could be a bad idea b/c of cache.
                        art = thumb
                        
                        try:
                            rating = item.xpath("../rating")[0].text
                            Log.Debug(rating)
                            
                            # see http://www.classify.org/safesurf/
                            #SS~~000. Age Range
                            #1) All Ages
                            #2) Older Children
                            #3) Teens
                            #4) Older Teens
                            #5) Adult Supervision Recommended
                            #6) Adults
                            #7) Limited to Adults
                            #8) Adults Only
                            #9) Explicitly for Adults

                            # just pluck the age value from text that looks like:
                            # (PICS-1.1 &quot;http://www.classify.org/safesurf/&quot; l r (SS~~000 5))
                            ageLimit = re.sub(r'(.*\(SS~~\d{3}\s+)(\d)(\).*)', r'\2', rating)
                            rating = int(ageLimit) # we don't care about the categories
                            
                        except (ValueError, IndexError, TypeError):
                            rating = None

                        if Dict['episodes'][str(mediaId)]["dateUpdated"] <= feedEntryModified:
                            seasonId = Dict['episodes'][str(mediaId)]["seasonId"]
                        #FIXME: figure out how to deal with getting resolutions.
                        availableResolutions = None
                        
                        episode = {
                            "title": title,
                            "description": episodeDescription,
                            "mediaId": mediaId,
                            "episodeNumber": episodeNumber,
                            "freePubDate": freePubDate,
                            "freePubDateEnd": freePubDateEnd,
                            "premiumPubDate": premiumPubDate,
                            "premiumPubDateEnd": premiumPubDateEnd,
                            "publisher": publisher,
                            "duration": duration,
                            "subtitleLanguages": subtitleLanguages,
                            "rating": rating,
                            "simpleRating": simpleRating,
                            "countries": countries,
                            "dateUpdated": dateUpdated,
                            "season": season,
                            "seasonId": seasonId,
                            "mediaLink": mediaLink,
                            "category": category,
                            "thumb": thumb,
                            "art": art,
                            "seriesTitle": seriesTitle,
                            "availableResolutions": availableResolutions
                        }
                        
                        Dict['episodes'][str(mediaId)] = episode
                    else:
                        episode = Dict['episodes'][str(mediaId)]
                    episodeList.append(episode)
        if sort:
            return sorted(episodeList, key=lambda k: k['episodeNum'])
        else:
            return episodeList

    except Exception, arg:
        Log.Error("#####We got ourselves a dagnabbit exception:")
        Log.Error(repr(Exception) + repr(arg))
        Log.Error("feed: %s" % feed)
        #Log.Error("Content:")
        #Log.Error(req.content) # too verbose, uncomment if needed
        # maybe just pass the exception up the chain here
        # instead of returning None
        return None

def getSeriesListFromFeed(feed, sort=True, sortBy="title"):
    #TODO: implement a check to eliminate need for call if series were cached recently
    cacheFullSeriesList()
    
    feedHtml = HTML.ElementFromURL(feed,cacheTime=SERIES_FEED_CACHE_TIME)
    seriesList = []
    items = feedHtml.xpath("//item")
    for item in items:
        seriesGUID = item.xpath("./guid")[0].text.replace("http://www.crunchyroll.com/", "")
        if not seriesGUID in Dict['series']:
            #TODO: figure out what to do if the series can't be found in Dict['series']
            Log.Debug("Could not find series with seriesGUID %s in Dict['series'].")
        else:
            seriesList.append(Dict['series'][str(seriesGUID)])
        
    if sort:
#        if sortBy == title:
#            return sorted(seriesList, key=lambda k: getSortTitle(k))
#        else:
            return sorted(seriesList, key=lambda k: k[sortBy])
    else:
        return seriesList



def GetEpisodeListFromQuery(queryString):
    "return a list of relevant episode dicts matching queryString"
    return getEpisodeListFromFeed(SEARCH_URL+queryString.strip().replace(' ', '%20'), sort=False)


def GetQueueList():
    login()
    queueHtml = HTML.ElementFromURL(QUEUE_URL,cacheTime=QUEUE_LIST_CACHE_TIME)
    queueList = []
    items = queueHtml.xpath("//div[@id='main_content']/ul[@id='sortable']/li[@class='queue-item']")
    for item in items:
        title = item.xpath(".//span[@class='series-title ellipsis']")[0].text
        seriesId = int(item.xpath("@series_id")[0].replace("queue_item_",""))
#        epToPlay = BASE_URL+item.xpath(".//a[@itemprop='url']/@href")[0].split("?t=")[0]
        
#        episodeTitle= item.xpath(".//a[@itemprop='url']/@title")[0]
#        episodeDescription = item.xpath(".//p[@itemprop='description']")

#        if episodeDescription:
#            episodeDescription = episodeDescription[0].text.strip('\n').strip()
#        else:
#            episodeDescription = ""
        """
        make sure item has an ID and does not error out from an empty string.
        This happens for series that were on cruncyroll but cruchyroll nolonger has rights to show.
        """
        episodeMediaIDStr = item.xpath("@media_id")[0]
        if not (episodeMediaIDStr == ""):
            episodeMediaID = int(episodeMediaIDStr)
            
            nextUpText = item.xpath(".//span[@class='series-data ellipsis']")[0].text
            fixit = ""
            for line in nextUpText.split('\n'):
                fixit = fixit + line.strip('\n').strip() +'\n'

            nextUpText = fixit


            queueItem = {
                "title": title,
                "upNextMediaId": episodeMediaID,
                "seriesId": seriesId#,
            }
            queueList.append(queueItem)
        
    return queueList


def recoverEpisodeDict(mediaId):
    """
    try everything possible to recover the episode info for
    mediaId and save it in Dict{}. If it fails, return none.
    """
    Log.Debug("#######recovering episode dictionary for mediaID %s" % str(mediaId))
    # make sure the series list is up to date
    cacheFullSeriesList()
	
    #FIXME: needs work ASAP!!!!
    # figure out method of getting the seriesId that the episode is in...
    # get all the seasons that are in that series
	#    seasonList = GetListOfSeasonsInSeries(seriesId)
	#	hackish meathod...
    for seasonId in Dict['seasons'].keys():
        cacheEpisodeListForSeason(seasonId)
	
    
#    # get a link with title in it.
#    #import urllib2
#    req = urllib2.urlopen(BASE_URL+"/media-" + str(mediaId) + "?pskip_wall=1")
#    redirectedUrl = req.geturl()
#    req.close
#    #FIXME: update for new system
#    redirectedUrl = redirectedUrl.replace("?pskip_wall=1", "")    
#    seriesName = redirectedUrl.split(".com/")[1].split("/")[0]
#    seriesUrl = seriesTitleToUrl(seriesName)
#    getEpisodeListFromFeed(seriesUrl) # for side-effect of caching episode
    
    if str(mediaId) in Dict['episodes']:
        return Dict['episodes'][str(mediaId)]
    
    # FIXME: blah
    # not good so far, we need a feed that provides full episodes. Yikes.
    # try grabbing from boxee_feeds
    # need seriesID as in boxee_feeds/showseries/384855
    # which can be retrieved from the seriesUrl contents, whew...
    # alternatively, use http://www.crunchyroll.com/series-name/episodes
    # which gives full episodes, but, well, is HTML and has less media info
    return None


def GetPopularAnimeEpisodes():
    "return a list of anime episode dicts that are currently popular"
    return getEpisodeListFromFeed(POPULAR_ANIME_FEED, sort=False)

def GetPopularDramaEpisodes():
    "return a list of drama episode dicts that are currenly popular"
    return getEpisodeListFromFeed(POPULAR_DRAMA_FEED, sort=False)

def GetPopularVideos():
    "return the most popular videos."
    return getEpisodeListFromFeed(POPULAR_FEED, sort=False)

def GetRecentVideos():
    "return a list of episode dicts of recent videos of all types"
    return getEpisodeListFromFeed(RECENT_VIDEOS_FEED, sort=False)

def GetRecentAnimeEpisodes():
    "return a list of episode dicts of recently added anime episodes"
    return getEpisodeListFromFeed(RECENT_ANIME_FEED, sort=False)

def GetRecentDramaEpisodes():
    "return a list of recently added drama videos"
    return getEpisodeListFromFeed(RECENT_DRAMA_FEED, sort=False)

def GetAnimeSeriesList():
    "return a list of all available series in anime"
    return getSeriesListFromFeed(SERIES_FEED_BASE_URL + "genre_anime_all", sort=True)

def GetDramaSeriesList():
    "return a list of all available series in Drama"
    return getSeriesListFromFeed(SERIES_FEED_BASE_URL + "drama", sort=True)

def GetAllSeries():
    "return a list of series dicts that represent all available series"
    list = []
    anime = getAnimeSeriesList()
    drama = getDramaSeriesList()
    # FIXME: if there's overlap, we'll have dupes...
    list = anime + drama
#    list = sorted(list, key=lambda k: getSortTitle(k))
    return list

def GetPopularDramaSeries():
    "return a list of series dicts of most popular drama"
    return getSeriesListFromFeed(SERIES_FEED_BASE_URL + "drama_popular", sort=False)

def GetPopularAnimeSeries():
    "return a list of series dicts of most popular anime"
    return getSeriesListFromFeed(SERIES_FEED_BASE_URL + "anime_popular", sort=False)

def GetAnimeSeriesByGenre(genre):
    queryStr = ANIME_GENRE_LIST[genre].replace(' ', '%20')
    feed = SERIES_FEED_BASE_URL + "anime_withtag/" + queryStr
    return getSeriesListFromFeed(feed)

def GetDramaSeriesByGenre(genre):
    queryStr = DRAMA_GENRE_LIST[genre].replace(' ', '%20')
    feed = SERIES_FEED_BASE_URL + "genre_drama_" + queryStr
    return getSeriesListFromFeed(feed)

def GetSeriesByGenre(genre):
    list = []
    drama, anime = [],[]
    try:
        drama = getDramaSeriesByGenre(genre)
    except KeyError: # may not have that genre
        drama = []
    try:
        anime = getAnimeSeriesByGenre(genre)
    except KeyError:
        anime = []

    # FIXME: if there's overlap, we'll have dupes...    
    return anime + drama


def GetSeriesDict(seriesId):
    """
    return an series dict object identified by seriesId.
    If you know the seriesId, it SHOULD be in the cache already.
    If not, you could get None if recovery doesn't work. This might 
    happen with seriesId's that come from the great beyond 
    (queue items on server, e.g.)
    Sry bout that.
    """
    if Dict['series'] is None or str(seriesId) not in Dict['series']:
        # get brutal
        Log.Debug("#######recovering series dictionary for seriesID %s" % str(seriesId))
        cacheFullSeriesList()
#        # get a link with title in it.
#        #import urllib2
#        req = urllib2.urlopen(BASE_URL+"/media-" + str(mediaId) + "?pskip_wall=1")
#        redirectedUrl = req.geturl()
#        req.close
#        #FIXME: update for new system
#        redirectedUrl = redirectedUrl.replace("?pskip_wall=1", "")    
#        seriesName = redirectedUrl.split(".com/")[1].split("/")[0]
#        seriesUrl = seriesTitleToUrl(seriesName)
#        getEpisodeListFromFeed(seriesUrl) # for side-effect of caching episode
        
        if str(mediaId) in Dict['episodes']:
            return Dict['episodes'][str(mediaId)]
        
        # FIXME: blah
        # not good so far, we need a feed that provides full episodes. Yikes.
        # try grabbing from boxee_feeds
        # need seriesID as in boxee_feeds/showseries/384855
        # which can be retrieved from the seriesUrl contents, whew...
        # alternatively, use http://www.crunchyroll.com/series-name/episodes
        # which gives full episodes, but, well, is HTML and has less media info
        
    return Dict['series'].get(str(seriesId))

def GetListOfSeasonsInSeries(seriesId):
    # make sure the seriesId is in the cache
    if not str(seriesId) in Dict['series']:
        Log.Debug("Did not find seriesID %s in the cache. refreshing the cache now"%str(seriesId))
        cacheFullSeriesList()
        # check again since the cache was just updated
        if not str(seriesId) in Dict['series']:
            Log.Warning("Unable to locate seriesID %s on crunchyroll.com"%str(seriesId))
            return []
    
    # the seriesId is in the cache so return the list of seasonIds
    return Dict['series'][str(seriesId)]['seasonList']

def GetSeasonDict(seasonId):
    # make sure the seasonId is in the cache
    if not str(seasonId) in Dict['seasons']:
        Log.Debug("Did not find seasonsID %s in the cache. refreshing the cache now"%str(seasonId))
        cacheFullSeriesList()
        # check again since the cache was just updated
        if not str(seasonId) in Dict['seasons']:
            Log.Warning("Unable to locate seasonID %s on crunchyroll.com"%str(seasonId))
            return []
    
    # the seriesId is in the cache so return the list of seasonIds
    return Dict['seasons'][str(seasonId)]

def GetListOfEpisodesInSeason(seasonId):
    # make sure the seasonId is in the cache
    Log.Debug("running GetListOfEpisodesInSeason %s"%str(seasonId))
    if not str(seasonId) in Dict['seasons']:
        Log.Debug("Did not find seasonID %s in the cache. refreshing the cache now"%str(seasonId))
        cacheFullSeriesList()
        # check again since the cache was just updated
        if not str(seasonId) in Dict['seasons']:
            Log.Debug("Unable to locate seasonID %s on crunchyroll.com"%str(seasonId))
            return []
    
    # the seriesId is in the cache so return the list of seasonIds
    #TODO: should probably add some code to make sure that the list is up to date.
#    if Dict['seasons'][str(seasonId)]['epsRetreived'] is None or (datetime.utcnow() - Dict['seasons'][str(seasonId)]['epsRetreived']) >= timedelta(hours=5):
#        cacheEpisodeListForSeason(seasonId)
#        Dict['seasons'][str(seasonId)]['epsRetreived'] = datetime.utcnow()

	Log.Debug("running GetListOfEpisodesInSeason %s  part 2"%str(seasonId))
    cacheEpisodeListForSeason(seasonId)
    Dict['seasons'][str(seasonId)]['epsRetreived'] = datetime.utcnow()
        
    return Dict['seasons'][str(seasonId)]['epList']

def GetEpisodeDict(mediaId):
    """
    return an episode dict object identified by mediaId.
    If you know the mediaId, it SHOULD be in the cache already.
    If not, you could get None if recovery doesn't work. This might 
    happen with mediaId's that come from the great beyond 
    (queue items on server, e.g.) and are in series with a lot of episodes.
    Sry bout that.
    """
    if str(mediaId) not in Dict['episodes']:
        # get brutal
        recoverEpisodeDict(mediaId)
        
    return Dict['episodes'].get(str(mediaId))



def SeriesTitleToUrl(title):
    toremove = ["!", ":", "'", "?", ".", ",", "(", ")", "&", "@", "#", "$", "%", "^", "*", ";", "~", "`"]
    for char in toremove:
        title = title.replace(char, "")
    title = title.replace("  ", " ").replace(" ", "-").lower()
    while "--" in title:
        title = title.replace("--","-")
    if title in SERIES_TITLE_URL_FIX.keys():
        title = SERIES_TITLE_URL_FIX[title]
    url = "%s/%s.rss" % (BASE_URL, title)
    Log.Debug("Series URL:" + url)
    return url

def GetVideoInfo(mediaId, availRes):

    if not mediaId:
        #occasionally this happens, so make sure it's noisy
        raise Exception("#####getVideoInfo(): NO MEDIA ID, SORRY!")
        
    url = "http://www.crunchyroll.com/xml/?req=RpcApiVideoPlayer_GetStandardConfig&media_id=%s&video_format=102&video_quality=10&auto_play=1&show_pop_out_controls=1&pop_out_disable_message=Only+All-Access+Members+and+Anime+Members+can+pop+out+this" % mediaId
    html = HTML.ElementFromURL(url)
    episodeInfo = {}
    episodeInfo['baseUrl'] = MEDIA_URL + str(mediaId)
    episodeInfo['availRes'] = availRes
    # width and height may not exist or may be bogus (Bleach eps 358)
    try:
        width = float(html.xpath("//stream_info/metadata/width")[0].text)
        height = float(html.xpath("//stream_info/metadata/height")[0].text)
        ratio = width/height
    except (IndexError, ValueError, TypeError):
        ratio = 1
        
    d = html.xpath("//stream_info/metadata/duration")
    if len(d):
        try: episodeInfo['duration'] = int(float(d[0].text)*1000)
        except Exception, arg:
            Log.Debug(repr(arg) + "\nsetting duration to 0")
            episodeInfo['duration'] = 0
    else:
        Log.Debug("#########Couldnt find duration")
        episodeInfo['duration'] = 0
    
    n = html.xpath("//media_metadata/episode_number")
    if len(n):
        try: episodeInfo['episodeNum'] = int(html.xpath("//media_metadata/episode_number")[0].text)
        except (ValueError, TypeError): episodeInfo['episodeNum'] = 0
    else: episodeInfo['duration'] = 0
    
    episodeInfo['wide'] = (ratio > 1.5)
    return episodeInfo

def GetAvailResForMediaId(mediaId):
    """
    given an mediaId, return a list of integers
    of available heights.
    
    If user is a guest, just return 360, which
    is all they get ;-)
    """
    
    if not Prefs['username'] or not Prefs['password']:
        return [360]

    login()

    availRes = [360]
    url = "%s/media-%s"%(BASE_URL,str(mediaId))
    link = url.replace(BASE_URL, "")
    req = HTTP.Request(url=url, immediate=True, cacheTime=3600*24)
    html = HTML.ElementFromString(req)
    
    try: 
        small = not isPremium()

    except: small = False

    if small is False:
        try:
            if len(html.xpath("//a[@token='showmedia.480p']")) > 0:
                availRes.append(480)
            if len(html.xpath("//a[@token='showmedia.720p']")) > 0:
                availRes.append(720)        
            if len(html.xpath("//a[@token='showmedia.1080p']")) > 0:
                availRes.append(1080)

        except Exception,arg:
            Log.Error("####getAvalResFromPage() we got ourselves an exception:")
            Log.Error(repr(Exception) + repr(arg))
    
    return availRes

def GetVideoMediaIdFromLink(link):
    mtmp = link.split(".com/")[1].split("/")[1].split("-")
    mediaId = int(mtmp[len(mtmp)-1])
    return mediaId

def GetEpInfoFromLink(link):
    #FIXME: currently this works fine for Queue items, which include
    # the title in the link, but should fail horribly
    # with "www.crunchyroll.com/media-45768" style links
    # which are given by feedburner, et. al.
    # furthermore, rss feeds that we use to populate the Dict{} may not contain all episodes.
    mediaId = getVideoMediaIdFromLink(link)
    if not str(mediaId) in Dict['episodes']:
        seriesname = link.split(".com/")[1].split("/")[0]
        url = seriesTitleToUrl(seriesname)
        getEpisodeListFromFeed(url) #TODO: investigate reason for calling this...
    episode = getEpisodeDict(mediaId)
    return episode

def GetMetadataFromUrl(url):
    episodeId = url.split(".com/")[1].split("/")[1].split("-")
    episodeId = episodeId[len(episodeId)-1]
    if not str(episodeId) in Dict['episodes']:
        seriesName=url.split(".com/")[1].split("/")[0]
        getEpisodeListFromFeed(BASE_URL+"/%s.rss"%seriesName)
    episodeData = getEpisodeDict(mediaId)
    metadata = {
        "title": episodeData['title']
    }
    return metadata


def GetPrefRes(availRes):

    if not Prefs['username'] or not Prefs['password']:
        return 360 # that's all you get
    login()
    preferredRes = 360

    if Prefs['quality'] == "Ask":
        #bwaaat? shouldn't call this
        Log.Error("####Can't determine preferred res because user wants to choose!")
    else:
        # the assumption is that the user chooses a resolution
        # (instead of "highest available") to control bandwidth/cpu use
        # so pick the highest res that is <= user's selection
        preferredRes = Quality2Resolution[Prefs['quality']]    
    
    if len(availRes):
        reslist = availRes

        # lowest first
        reslist.sort()
        
        chosenRes = 360 # in case reslist is empty
        for res in reslist:
            if res <= preferredRes:
                chosenRes = res
            else:
                break
    
    return chosenRes

def GetVideoUrl(videoInfo, resolution):
    """
    construct a URL to display at resolution based on videoInfo
    without checking for coherence to what the site's got
    or if the resolution is valid
    """
    url = videoInfo['baseUrl']+"?p" + str(resolution) + "=1"
    url = url + "&skip_wall=1"
    url = url + ("&t=0" if Prefs['restart'] == 'Restart' else "")
    url = url + "&small="+("1" if videoInfo['small'] is True else "0")
    url = url + "&wide="+("1" if videoInfo['wide'] is True or JUST_USE_WIDE is True else "0")
    return url









def DebugMenu(sender, advanced=True):
    if advanced: title = "Debug"
    else: title = "Utilities"
    dir = MediaContainer(disabledViewModes=["Coverflow"], title1=title)
    if advanced: 
        dir.Append(Function(DirectoryItem(DumpInfo, "Dump info to console")) )
        #FIXME: clear all data is useful, but allows anybody to clear all info, so let's keep it advanced for now
        dir.Append(Function(DirectoryItem(ClearAllData, "Clear all data", summary="This removes cached metadata, and plex's cookies and cache. Prefs will still exist.")) )
    if advanced:
        dir.Append(Function(DirectoryItem(VideoTestMenu, "Test Videos...")) )
    dir.Append(Function(DirectoryItem(LogoutFromMenu, "Log out now", summary="This will log you out and remove all related cookies.")) )
    dir.Append(Function(DirectoryItem(LoginFromMenu, "Log in now", summary="This will force a clean login.")) )
    if advanced:
        dir.Append(Function(DirectoryItem(ClearCookiesItem, "Clear Cookies", summary="This will remove the cookies from Plex's internal cookie storage.")) )
#        dir.Append(Function(DirectoryItem(KillSafariCookiesItem, "Kill Safari Cookies", summary="This will remove all crunchyroll.com cookies from Safari's cookie file. Useful if login status is not synced.")) )
#        dir.Append(Function(DirectoryItem(TransferCookiesItem, "Transfer cookies to Safari", summary="This transfers Plex's crunchyroll cookies into safari's plist.")) )
        dir.Append(Function(InputDirectoryItem(SetPreferredResolution, "Set Preferred Resolution", prompt=L("Type in resolution"), summary="This sets the preferred resolution server-side. Valid values are 360,480,720,and 1080")) )
    
    return dir
    
def DumpInfo(sender):

    debugDict()
    Log.Debug("###########CURRENT COOKIES")
    Log.Debug(HTTP.CookiesForURL(BASE_URL))
    Log.Debug("#############PREFERENCES:")
    Log.Debug(Prefs)

    return MessageContainer("Whew", "Thanks for dumping on me.")

def ClearAllData(sender):
    HTTP.ClearCookies()
    HTTP.ClearCache()
#    Dict = {}
#    Dict.Reset() #OMG this doesn't work. Just delete the file at Plug-in support/com.plexapp.plugins.CrunchyRoll
#    Dict.Save()
    Log.Debug(Prefs)
#    Prefs = {}
#    CreatePrefs()
    return MessageContainer("Huzzah", "You are now sparklie clean.")


def VideoTestMenu(sender, query=None):
    if query:
        Log.Debug("#########so, you're sending me superflous info, eh?")
        Log.Debug(query)
        
    dir = MediaContainer(disabledViewModes=["Coverflow"], title1="Crunchyroll Video Tests")
    
    # object containers don't take WebVideoItems, so screw it
    #dir = ObjectContainer(title1="Crunchyroll Video Tests")
    addMediaTests(dir)
    dir.noCache=1
    return dir
    
def LogoutFromMenu(sender):
    """
    logout and return a message container with the result
    """
    logout()
    if not loggedIn():
        dir = MessageContainer("Logout", "You are now logged out")
    else:
        dir = MessageContainer("Logout Failure", "Nice try, but logout failed.")
        Log.Debug("####LOGOUT FAILED, HERE'S YOUR COOKIE")
        Log.Debug(HTTP.CookiesForURL(BASE_URL) )

    return dir

def LoginFromMenu(sender):
    if not Prefs['username'] or not Prefs['password']:
        dir = MessageContainer("Login Brain Fart", "You cannot login because your username or password are blank.")
    else:
        result = login(force = True)
        if not result:
            dir = MessageContainer("Auth failed", "Authentication failed at crunchyroll.com")
        elif isRegistered():
            dir = MessageContainer("Login", "You are logged in, congrats.")
        else:
            dir = MessageContainer("Login Failure", "Sorry, bro, you didn't login!")
        
    return dir

def ClearCookiesItem(sender):
    HTTP.ClearCookies()
    return MessageContainer("Cookies Cleared", "For whatever it's worth, cookies are gone now.")

def SetPreferredResolution(sender, query):
    try:
        q = int(query)
    except:
        q = 0
    
    if q not in [360, 480, 720, 1080]:
        return MessageContainer("Bad input", "You need to input one of 360, 480, 720, or 1080")
    
    if setPrefResolution(q):
        return MessageContainer("Success", "Resolution changed to %i" % q)
    else:
        return MessageContainer("Failure", "Failed to change resolution, sorry!")
    
def ConstructTestVideo(episode)    :
    episodeItem = \
        WebVideoItem(url=episode['link'],
            title = episode['title'],
            subtitle = "Season %s"%episode['season'],
            summary = episode['summary'],
            #thumb = Function(GetThumb,url=episode['thumb']),
            #art=Function(GetArt,url=getEpisodeArt(episode))
        )
    return episodeItem

def addMediaTests(dir):
    """
    add some video tests to a MediaContainer
    """
    if ENABLE_DEBUG_MENUS:
        testEpisodes = [
            {'title': 'Bleach Episode 1',
             'season': 'One',
             'summary': "480p Boxee feed. This needs a premium account. No ads should show! Plex client should show a resolution of 853x480. (I do not know the 480p url, or if there is one, so it'll probably display at 720p). It must not have any black edges on top or bottom. Play, pause, and seeking should work.",
             'link': 'http://www.crunchyroll.com/boxee_showmedia/543611&amp;bx-ourl=http://www.crunchyroll.com/bleach/543611',
             'mediaId': '543611',
            },

            {'title': 'Gintama 187',
             'season': 'None',
             'summary': "720p Boxee feed. This needs a premium account. No ads should show! Plex client should show a resolution of 1280x720, must not have any black edges on top or bottom. Play, pause, and seeking should work.",
             'link': 'http://www.crunchyroll.com/boxee_showmedia/537056&amp;bx-ourl=http://www.crunchyroll.com/gintama/537056',
             'mediaId': '537056',
            },
            {'title': 'Bleach Episode 357',
             'season': 'None',
             'summary': "1080p Boxee feed. This needs a premium account. No ads should show! Plex client should show a resolution of exactly 1920x1080, must not have any black edges on top or bottom. Play, pause, and seeking should work.",
             'link': 'http://www.crunchyroll.com/boxee_showmedia/588328&amp;bx-ourl=http://www.crunchyroll.com/bleach/588328',
             'mediaId': '588328',
            },
            {'title': 'Blue Exorcist Trailer',
              'season': 'None',
              'summary': '480p web page version. This needs a premium account. No ads should show! Should crop badly, as it is not a direct stream (we go direct with premium accounts).',
              'link': 'http://www.crunchyroll.com/blue-exorcist/-blue-exorcist-blue-exorcist-official-trailer-577928?p480=1&small=0&wide=0',
              'mediaId': "577928"
            },
            {'title': 'Blue Exorcist Episode 1',
              'season': 'None',
              'summary': '360p web page version.  You really should log out to test this. You should get ads. Plex client should show resolution of 619x348',
              'link': 'http://www.crunchyroll.com/blue-exorcist/episode-1-the-devil-resides-in-human-souls-573636?p360=1&small=0&wide=0',
              'mediaId': "577928"
            },
            {
              'title':'Shugo Chara Episode 1',
              'season': "One",
              'summary': "360p default web page version, freebie. Should show resolution of 619x348. Should look borked if you're logged in.",
              'link': 'http://www.crunchyroll.com/shugo-chara/episode-1-a-guardian-character-is-born-509988?p360',
              'mediaId': '509988'
            },
            {'title': "Bleach 274 1080p",
            'season': 'None',
            'summary': "1080p direct stream. You need to log in and have your preference at CR.com set to view 1080p. No ads should show. Plex should report a resolution of 1920x1080. There MIGHT be small black bars at top and bottom due to ratio difference (but really shouldn't happen). Seek, play and pause should work.",
            'link': "http://www.crunchyroll.com/swf/vidplayer.swf?config_url=http%3A%2F%2Fwww.crunchyroll.com%2Fxml%2F%3Freq%3DRpcApiVideoPlayer_GetStandardConfig%26media_id%3D542596%26video_format%3D0%26video_quality%3D0%26auto_play%3D1%26click_through%3D1&__qual=1080",
            'mediaId': '542596'
            },
            {'title': "Puffy AmiYumi Interview",
            'season': 'None',
            'summary': "Freebie web content with standard URL. You need to be logged out to view this without nasty cropping. LIKES TO CRASH PMS with BAD_ACCESS",
            #'link':"http://www.crunchyroll.com/media-565187?p360=1&t=0&small=0&wide=0",
            'link':"http://www.crunchyroll.com/puffy-amiyumi/-puffy-amiyumi-puffy-amiyumi-interview-565187?p360=1&t=0&small=0&wide=0",
            'mediaId': '565187'
            },
            {'title': "Puffy AmiYumi Interview Redirected",
            'season': 'None',
            'summary': "Freebie web content with standard URL. This URL redirects at CrunchyRoll.com, and will probably crash PMS with BAD_ACCESS.",
            'link':"http://www.crunchyroll.com/media-565187?p360=1&t=0&small=0&wide=0",
            #'link':"http://www.crunchyroll.com/puffy-amiyumi/-puffy-amiyumi-puffy-amiyumi-interview-565187?p360=1&t=0&small=0&wide=0",
            'mediaId': '565187'
            }            
            
            
        ]
        

        for episode in testEpisodes:
            dir.Append(ConstructTestVideo(episode))

        
        vid = VideoClipObject(
                        url="http://www.crunchyroll.com/another/episode-1-rough-sketch-589572",
                        title="Another episode 1, services",
                        summary = "This video will be fetched through services. It may just bug out. Who knows."
                    )
        # this actually borks consistently. I actually don't understand the point of VideoClipObject.
        #dir.Append(VideoItem("http://www.crunchyroll.com/another/episode-1-rough-sketch-589572", title="Test services", summary="This is a test of url services. It should play."))

def listElt(url):
    page = HTML.ElementFromURL(url)
    for a in list(page):
        Log.Debug(a.tag)
        for b in list(a):
            Log.Debug("    %s" % b.tag)
            for c in list(b):
                Log.Debug("        %s" % c.tag)
                for d in list(c):
                    Log.Debug("            %s" % d.tag)

def debugFeedItem(item):
    for sub in list(item):
        text1 = "%s: %s" % (sub.tag, sub.text)
        Log.Debug(text1)
        for sub2 in list(sub):
            text2 = "\t%s/%s: %s\n%s" % (sub.tag, sub2.tag, sub2.text, list(sub2))
            Log.Debug(text2)
            for sub3 in list(sub2):
                text3 = "\t\t%s/%s/%s: %s\n%s" % (sub.tag, sub2.tag, sub3.tag, sub3.text, list(sub3))
                Log.Debug(text3)
                for sub4 in list(sub3):
                    text4 = "\t\t\t%%s/%s/%s: %s\n%s" % (sub.tag, sub2.tag, sub3.tag, sub4.tag, sub4.text, list(sub4))
                    Log.Debug(text4)

def listThumbs():
    Log.Debug("list thumbs")
    withs = []
    withouts = []
    for sk in Dict['series'].keys():
        s = Dict['series'][str(sk)]
        if s['tvdbId'] is not None:
            if " " in s['thumb']:
                withs.append('"%s": "%s"'%(s['title'], s['thumb']))
            else:
                withouts.append('"%s": "%s"'%(s['title'], s['thumb']))
    s = "with"
    for l in withs:
        s = '%s\n%s'%(s,l)
    s = '%s\nwithout'%s
    for l in withouts:
        s = '%s\n%s'%(s,l)
    Log.Debug(s)

def listThumbs2():
    Log.Debug("list thumbs")
    withs = []
    for sk in Dict['series'].keys():
        s = Dict['series'][str(sk)]
        if s['tvdbId'] is not None:
            if "%20" in s['thumb'] or " " in s['thumb']:
                withs.append('"%s": "%s"'%(s['title'], s['thumb']))
    s = "with"
    for l in withs:
        s = '%s\n%s'%(s,l)
    Log.Debug(s)


def debugDict():
    """
    Dump the global Dict{} object to the console.
    """
    for key in Dict:
        Log.Debug("####### %s" % repr(key))
        Log.Debug(Dict[key])

def testCacheAll():
    if 1==1:
        Data.SaveObject("episodes", Dict['episodes'])
        Data.SaveObject("series", Dict['series'])
        Data.SaveObject("fanart", Dict['fanart'])
    #Dict.Reset()
    #Dict['episodes'] = {}
    #Dict['series'] = {}
    #Dict['fanart'] = {}
    #HTTP.ClearCache()
    #CacheAll()
    #Log.Debug("num of eps: %s"%(len(Dict['episodes'])))
    #Log.Debug("num of shows: %s"%(len(Dict['series'])))
    
    if 1==0:
        Dict['episodes'] = Data.LoadObject("episodes")
        Dict['series'] = Data.LoadObject("series")
        Dict['fanart'] = Data.LoadObject("fanart")



def jsonRequest(valuesDict, referer=None):
    """
    convenience function. Return API request result as dict.
    """
    response = makeAPIRequest(valuesDict, referer)
    response = JSON.ObjectFromString(response)
    return response

def makeAPIRequest(valuesDict,referer=None):
    """
    make a crunchyroll.com API request with the passed
    dictionary. Optionally, specify referer to prevent request
    from choking.
    """
    h = API_HEADERS
    if not referer is None:
        h['Referer'] = referer
    h['Cookie']=HTTP.CookiesForURL(BASE_URL)
    req = HTTP.Request("https"+API_URL,values=valuesDict,cacheTime=0,immediate=True, headers=h)
    response = re.sub(r'\n\*/$', '', re.sub(r'^/\*-secure-\n', '', req.content))
    return response

def makeAPIRequest2(data,referer=None):
    """
    using raw data string, make an API request. Return the result.
    """
    h = API_HEADERS
    if not referer is None:
        h['Referer'] = referer
    h['Cookie']=HTTP.CookiesForURL(BASE_URL)
    req = HTTP.Request("https"+API_URL,data=data,cacheTime=0,immediate=True, headers=h)
    response = re.sub(r'\n\*/$', '', re.sub(r'^/\*-secure-\n', '', req.content))
    return response

def loginViaApi(authInfo):
    loginSuccess = False
    try:
        response = jsonRequest(
            { "name": Prefs['username'], "password": Prefs['password'], "req": "RpcApiUser_Login" }
            )
        
        if response.get('result_code') != 1:
            Log.Error("###an error occured when logging in:")
            Log.Error(response)
        else:
            Log.Debug(response)
            authInfo['AnimePremium'] = (response.get('data').get('premium').get(PREMIUM_TYPE_ANIME) == 1)
            authInfo['DramaPremium']= (response.get('data').get('premium').get(PREMIUM_TYPE_DRAMA) == 1)
            loginSuccess = True
            HTTP.Headers['Cookie'] = HTTP.CookiesForURL('https://www.crunchyroll.com/')
    except Exception, arg:
        Log.Error("####Sorry, an error occured when logging in:")
        Log.Error(repr(Exception) + " "  + repr(arg))
        return False
    
    return loginSuccess

    
def loggedIn():
    """
    Immediately check if user is logged in, and change global values to reflect status. 
    DO NOT USE THIS A LOT. It requires a web fetch.
    """
    #FIXME: a better way would be to use API, but I don't know how to request status
    # alternatively, might as well just login anyway if you're going to touch the network.
    if not Dict['Authentication']:
        resetAuthInfo()
        
    try:
        req = HTTP.Request(url="https://www.crunchyroll.com/acct/?action=status", immediate=True, cacheTime=0)
    except Exception, arg:
        Log.Error("####Error checking status:")
        Log.Error(repr(Exception) + " "  + repr(arg))
        return False
    
    authorized = False
    if "Profile Information" in req.content:
        authorized = True
    
    authInfo = Dict['Authentication']
    
    if authorized:
        Log.Debug(HTTP.CookiesForURL('https://www.crunchyroll.com/'))
        if "Anime Member!" in req.content:
            authInfo['AnimePremium'] = True
        if "Drama Member!" in req.content: #FIXME: untested!
            authInfo['DramaPremium'] = True
        
        Dict['Authentication'] = authInfo #FIXME: needed?
        
        #Log.Debug("#####You are authorized for premium content, have a nice day.")
        #Log.Debug("#####AnimePremium member: %s" % ("yes" if authInfo['AnimePremium'] else "no"))
        #Log.Debug("#####DramaPremium member: %s" % ("yes" if authInfo['DramaPremium'] else "no"))
        if not authInfo['AnimePremium'] and not authInfo['DramaPremium']: #possible if user is just registered
            Log.Error("####Programmer does not know what to do with freebie registered users. Apologies.")
            #Log.Debug(req.content)
            
    return authorized

def resetAuthInfo():
    """
    put a default authentication status structure into
    the global Dict{}. Every datum is least permissions on default.
    """
    Dict['Authentication'] =  {'loggedInSince':0.0, 'failedLoginCount':0, 'AnimePremium': False, 'DramaPremium': False}

def login(force=False):
    """
    Log the user in if needed. Returns False on authentication failure,
    otherwise True. Feel free to call this anytime you think logging in
    would be useful -- it assumes you will do so.

    Guest users don't log in, therefore this will always return true for them.
    See IsPremium() if you want to check permissions. or LoggedIn() if you 
    want to fetch a web page NOW (use conservatively!)
    """

    loginSuccess = False
    if not Dict['Authentication'] : resetAuthInfo()
    
    authInfo = Dict['Authentication'] #dicts are mutable, so authInfo is a reference & will change Dict presumably
    if Prefs['username'] and Prefs['password']:

        # fifteen minutes is reasonable.
        # this also prevents spamming server
        if (force == False) and (time.time() - authInfo['loggedInSince']) < LOGIN_GRACE:
            Log.Debug("loggedin cookies:")
            Log.Debug(HTTP.CookiesForURL('https://www.crunchyroll.com/'))
            return True

        if force: 
            HTTP.ClearCookies()
            authInfo['loggedInSince'] = 0
            authInfo['failedLoginCount'] = 0
            #Dict['Authentication'] = authInfo

        if not force and authInfo['failedLoginCount'] > 2:
            return False # Don't bash the server, just inform caller
        
        if loggedIn():
            authInfo['failedLoginCount'] = 0
            authInfo['loggedInSince'] = time.time()
            #Dict['Authentication'] = authInfo
            Log.Debug("loggedin cookies:")
            Log.Debug(HTTP.CookiesForURL('https://www.crunchyroll.com/'))
            return True
        else:
            Log.Debug("#####WEB LOGIN CHECK FAILED, MUST LOG IN MANUALLY")

        # if we reach here, we must manually log in.
        if not force:
            #save about 2 seconds
            HTTP.ClearCookies()

        loginSuccess = loginViaApi(authInfo)
            
        #check it
        if loginSuccess or loggedIn():
            authInfo['loggedInSince'] = time.time()
            authInfo['failedLoginCount'] = 0
            #Dict['Authentication'] = authInfo
            Log.Debug("loggedin cookies:")
            Log.Debug(HTTP.CookiesForURL('https://www.crunchyroll.com/'))
            return True
        else:
            Log.Error("###WHOAH DOGGIE, LOGGING IN DIDN'T WORK###")
            Log.Debug("COOKIIEEEE:")
            Log.Debug(HTTP.Headers['Cookie'])
            Log.Debug("headers: %s" % req.headers)
            #Log.Debug("content: %s" % req.content) # Too much info
            authInfo['failedLoginCount'] = failedLoginCount + 1
            authInfo['loggedInSince'] = 0
            #Dict['Authentication'] = authInfo
            return False
    else:
        authInfo['failedLoginCount'] = 0
        #Dict['Authentication'] = authInfo

        return True # empty user is not authentication failure

def isRegistered():
    """
    is the user a registered user?
    Registered users get to use their queue.
    """
    if not login():
        return False

    if loginNotBlank():
        return True

def hasPaid():
    """
    does the user own a paid account of any type?
    """
    login()
    if not Dict['Authentication']: resetAuthInfo()
    
    authInfo = Dict['Authentication']
    
    if (time.time() - authInfo['loggedInSince']) < LOGIN_GRACE:
        if authInfo['AnimePremium'] is True or authInfo['DramaPremium'] is True:
            return True

    return False
    
def isPremium(epType=None):
    """
    return True if the user is logged in and has permissions to view extended content.
    You can pass ANIME_TYPE or DRAMA_TYPE to check specifically.
    
    Passing type=None will return True if the user is logged in. Any other type
    returns false.
    """
    #FIXME I thoroughly misunderstood the meaning of being logged in (ack!).
    # One can be freebie, yet log in. This borks the logic used to choose
    # resolution. 

    login()
    if not Dict['Authentication']: resetAuthInfo()
    
    authInfo = Dict['Authentication']
    
    if (time.time() - authInfo['loggedInSince']) < LOGIN_GRACE:
        if epType is None: return True

        if epType == ANIME_TYPE and authInfo['AnimePremium'] is True:
            return True
        elif epType == DRAMA_TYPE and authInfo['DramaPremium'] is True:
            return True
        Log.Debug("#####isPremium() neither Anime nor Drama Premium is set?")

        return False #FIXME actually this should be an exception

    #Log.Debug("####you're not in the login grace period, too bad. t = %f" % (time.time()-authInfo['loggedInSince']))
    return False

def logout():
    """
    Immediately log the user out and clear all authentication info.
    """
    response = jsonRequest({'req':"RpcApiUser_Logout"}, referer="https://www.crunchyroll.com")
    HTTP.ClearCookies()
    resetAuthInfo()

def loginNotBlank():
    if Prefs['username'] and Prefs['password']: return True
    return False

def setPrefResolution(res):
    """
    change the preferred resolution serverside to integer res
    """
    if hasPaid():
        res2enum = {360:'12', 480:'20', 720:'21', 1080:'23'}
        
        response = jsonRequest(
            { 'req': "RpcApiUser_UpdateDefaultVideoQuality",
              'value': res2enum[res]
            }
            )
    
        if response.get('result_code') == 1:
            return True
        else:
            return False

    return False

def removeFromQueue(seriesId):
    """
    remove seriesID from queue
    """
    login()
    if not isRegistered():
        return False
    
    response = makeAPIRequest2("req=RpcApiUserQueue_Delete&group_id=%s"%seriesId)
    #FIXME response should have meaning; do something here?
    Log.Debug("remove response: %s"%response)
    return True

def addToQueue(seriesId):
    """
    Add seriesId to the queue.
    """
    login()
    if not isRegistered():
        return False
        
    Log.Debug("add mediaid: %s"%seriesId)
    response = makeAPIRequest2("req=RpcApiUserQueue_Add&group_id=%s"%seriesId)
    Log.Debug("add response: %s"%response)
    return True


def deleteFlashJunk(folder=None):
    """
    remove flash player storage from crunchyroll.com.
    We need to remove everything, as just removing
    'PersistentSettingsProxy.sol' (playhead resume info) leads 
    to buggy player behavior.
    """
    #FIXME: does this also need to be implemented for windows? is it even needed to begin with?
    # in xp:
    # C:\Documents and Settings\[Your Profile]\Application Data\Macromedia\Flash Player\#SharedObjects\[Random Name]\[Web Site Path]
    # in Vista/7:
    # C:\Users\[Your Profile]\AppData\Roaming\Macromedia\Flash Player\#SharedObjects\[Random Name]\[Web Site Path]
    import platform
    if "darwin" in platform.system().lower():
        import os 
        if not folder:
            folder = os.path.expanduser('~/Library/Preferences/Macromedia/Flash Player/#SharedObjects')
        try:
            filelist = os.listdir(folder)
        except OSError, e:
            Log.Debug(e)
            return False
        
        for the_file in filelist:
            file_path = os.path.join(folder, the_file)
            if os.path.isdir(file_path):
                deleteFlashJunk(file_path)
            elif os.path.isfile(file_path):
                if "www.crunchyroll.com" in file_path:
                    Log.Debug("#####Found flash junk at %s" % file_path)
                    if True or "PersistentSettingsProxy.sol" in os.path.basename(file_path):
                        Log.Debug("#######Deleting %s" % file_path)
                        try:
                            os.unlink(file_path)
                            return True
                        except Exception, e:
                            Log.Debug( "Well, we tried")
                            Log.Debug(e)
    return False




def getEpisodeArtUrl(episode):
    """
    return the best background art URL for the passed episode.
    """
    #TODO: consider reimplementing the fanart part
    artUrl = episode['art']
    if artUrl == "" or artUrl is None:
        artUrl = R(CRUNCHYROLL_ART)
#    Log.Debug("episode art url: %s"%artUrl)
    return artUrl

def getEpisodeThumbUrl(episode):
    """
    return the best thumbnail URL for the passed episode.
    """
    #TODO: consider reimplementing the fanart part
    thumbUrl = episode['thumb']
    if thumbUrl == "" or thumbUrl is None:
        thumbUrl = R(CRUNCHYROLL_ICON)
#    Log.Debug("episode thumb url: %s"%thumbUrl)
    return thumbUrl

def getSeasonArtUrl(season):
    """
    return the best background art URL for the passed season.
    """
    #TODO: consider reimplementing the fanart part
    artUrl = season['art']
    if artUrl == "" or artUrl is None:
        artUrl = R(CRUNCHYROLL_ART)
#    Log.Debug("season art url: %s"%artUrl)
    return artUrl

def getSeasonThumbUrl(season):
    """
    return the best thumbnail URL for the passed season.
    """
    #TODO: consider reimplementing the fanart part
    thumbUrl = season['thumb']
    if thumbUrl == "" or thumbUrl is None:
        thumbUrl = R(CRUNCHYROLL_ICON)
#    Log.Debug("season thumb url: %s"%thumbUrl)
    return thumbUrl

def getSeriesArtUrl(series):
    """
    return the best background art URL for the passed series.
    """
    #TODO: consider reimplementing the fanart part
    artUrl = series['art']
    if artUrl == "" or artUrl is None:
        artUrl = R(CRUNCHYROLL_ART)
#    Log.Debug("series art url: %s"%artUrl)
    return artUrl

def getSeriesThumbUrl(series):
    """
    return the best thumbnail URL for the passed series.
    """
    #TODO: consider reimplementing the fanart part
    thumbUrl = series['thumb']
    if thumbUrl == "" or thumbUrl is None:
        thumbUrl = R(CRUNCHYROLL_ICON)
#    Log.Debug("series thumb url: %s"%thumbUrl)
    return thumbUrl

def getThumb(url):
    """
    Try to find a better thumb than the one provided via url.
    The thumb data returned is either an URL or the image data itself.
    """
    ret = None
    if url==R(CRUNCHYROLL_ICON):
        ret = url
    else:
        if url is not None:
            try:
                data = HTTP.Request(url, cacheTime=CACHE_1WEEK).content
                if url.endswith(".jpg"):
                    ret = DataObject(data, 'image/jpeg')
                elif url.endswith(".png"):
                    ret = DataObject(data, 'image/png')
            except Exception, arg:
                Log.Error("#####Thumbnail couldn't be retrieved:")
                Log.Error("#####" + repr(Exception) + repr(arg) + url)
                ret = None

    if ret is None:
        return R(CRUNCHYROLL_ICON)
    else:
        return ret

def getArt(url):
    ret = None
    if url==R(CRUNCHYROLL_ART) or url is None or url is "":
        req = urllib2.Request("http://127.0.0.1:32400"+R(CRUNCHYROLL_ART))
        ret = DataObject(urllib2.urlopen(req).read(), 'image/jpeg')
    else:
        try:
            #Log.Debug("url: %s"%url)
            data = HTTP.Request(url, cacheTime=CACHE_1WEEK).content
            if url.endswith(".jpg"):
                ret = DataObject(data, 'image/jpeg')
            elif url.endswith(".png"):
                ret = DataObject(data, 'image/png')
        except Exception,arg: 
            Log.Error("####Exception when grabbing art at '%s'" % url)
            Log.Error(repr(Exception) + repr(arg))
        

    if ret is None:
        req = urllib2.Request("http://127.0.0.1:32400"+R(CRUNCHYROLL_ART))
        return DataObject(urllib2.urlopen(req).read(), 'image/jpeg')
    else:
        return ret

def stripHtml(html):
	"""
	return a string stripped of html tags
	"""
	# kinda works
	res = html.replace("&lt;", "<")
	res = res.replace("&gt;", ">")
	res = re.sub(r'<[^>]+>', '', res)
	return res
