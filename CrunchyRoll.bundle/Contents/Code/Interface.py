import re
import urllib2
import time, os, re
from Cookie import BaseCookie
import plistlib
from datetime import datetime, timedelta

from constants2 import *

from CrunchyrollUserAPI import *
from CrunchyrollDataAPI import *
from DebugCode import *
from Artwork import *

HTTP.CacheTime = 3600
HTTP.Headers["User-Agent"] = "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_6; en-gb) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16"
HTTP.Headers["Accept-Encoding"] = "gzip, deflate"


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
    thumb = getSeriesThumbUrl(series)#(s[sId]['thumb'] if (sId in s and s[sId]['thumb'] is not None) else R(CRUNCHYROLL_ICON))
    art = getSeriesArtUrl(series)#(s[sId]['art'] if (sId in s and s[sId]['art'] is not None) else R(CRUNCHYROLL_ART))
    if queueInfo['upNextMediaId'] is not None:
        nextEp = GetEpisodeDict(queueInfo['upNextMediaId'])#getEpInfoFromLink(queueInfo['epToPlay'])
        PlayNext = MakeEpisodeItem(nextEp)
        dir.Append(PlayNext)
    RemoveSeries = Function(DirectoryItem(RemoveFromQueue, title="Remove series from queue"), seriesId=sId)
    ViewSeries = Function(DirectoryItem(SeriesMenu, "View Series", thumb=thumb, art=Function(GetArt,url=art)), seriesId=queueInfo['seriesId'])
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
    season = GetSeasonDict(seasonId)
    dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="%s - Season %s"%(sender.title2,str(season['season'])))
    epList = GetListOfEpisodesInSeason(seasonId)#getEpisodeListForSeason(seasonId)
    for episodeId in epList:
        episode = GetEpisodeDict(episodeId)
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
        seriesId=season['seriesId'],
        season=season['seasonNumber'])
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
