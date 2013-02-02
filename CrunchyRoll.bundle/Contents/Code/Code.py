# -*- coding: utf-8 -*-
import re
import urllib2
import time, os, re
from Cookie import BaseCookie
import plistlib
from datetime import datetime, timedelta

from constants2 import *


from CrunchyrollAPI import *

#from CrunchyrollUserAPI import *
#from CrunchyrollDataAPI import *
#from DebugCode import *
#from Artwork import *



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
        
    
#    Dict['episodes'] = None
#    Dict['series'] = None
#    Dict['seasons'] = None
    #loginAtStart()
    if 'episodes' not in Dict: Dict['episodes'] = {}
    if 'series' not in Dict: Dict['series'] = {}
    if 'fanart' not in Dict: Dict['fanart'] = {}
    
    if False: # doesn't work because cache won't accept a timeout value
        for cacheThis in PRECACHE_URLS:
            HTTP.PreCache(cacheThis, cacheTime=60*60*10)

def ValidatePrefs():
    u = Prefs['username']
    p = Prefs['password']
    h = Prefs['quality']
    if u and p:
        loginSuccess = CRAPI.Login(force = True)
        if not loginSuccess:
            mc = MessageContainer("Login Failure", "Failed to login, check your username and password, and that you've read your confirmation email.")
            return mc
        else:
            mc = MessageContainer("Success", "Preferences Saved.")
            return mc

    elif u or p:
        mc = MessageContainer("Login Failure", "Please specify both a username and a password.")
        return mc
    else:
        # no username or password
        try:
            CRAPI.Logout()
        except: pass
        
        if Prefs['quality'] != "SD": # and Prefs['quality'] != "Highest Available":
            mc = MessageContainer("Quality Warning", "Only premium members can watch in high definition. Your videos will show in standard definiton only.")
        else:
            mc = MessageContainer("Success", "Preferences Saved.")
        return mc


def TopMenu():
    "from which all greatness springs."
    CRAPI.Login()

    Log.Debug("art: %s"%R(CRUNCHYROLL_ART))

    dir = MediaContainer(disabledViewModes=["Coverflow"], title1="Crunchyroll", noCache=True)
    
    if CRAPI.IsRegistered():
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
    if CRAPI.IsRegistered():
        dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="Series", noCache=True)
        queueList = CRAPI.GetQueueList()
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
    sId = str(queueInfo['seriesId'])
    series = CRAPI.GetSeriesDict(sId)
    for seasonId in series['seasonList']:
        CRAPI._cacheEpisodeListForSeason(seasonId)
        
    thumb = getSeriesThumbUrl(series)
    art = getSeriesArtUrl(series)
    if queueInfo['upNextMediaId'] is not None:
        nextEp = CRAPI.GetEpisodeDict(queueInfo['upNextMediaId'])#getEpInfoFromLink(queueInfo['epToPlay'])
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
    episodeList = CRAPI.GetPopularVideos()
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
    episodeList = CRAPI.GetRecentVideos()
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
        startTime = datetime.utcnow()
        if query=="#":
            queryCharacters = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')
        elif query=="All":
            queryCharacters = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z')
        else:
            queryCharacters = (query.lower(), query.upper())
        dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2=query)
        if type==ANIME_TYPE:
            seriesList = CRAPI.GetAnimeSeriesList()
        elif type==DRAMA_TYPE:
            seriesList = CRAPI.GetDramaSeriesList()
        else:
            seriesList = CRAPI.GetAllSeries()

        seriesList = sorted(seriesList, key=lambda k: getSortTitle(k)) 
                   
        for series in seriesList:
            sortTitle =  getSortTitle(series)
            if sortTitle.startswith(queryCharacters):
                dir.Append(MakeSeriesItem(series))
        dtime = datetime.utcnow()-startTime
        Log.Debug("AlphaListMenu %s (%s) execution time: %s"%(type, query, dtime))
        #listThumbs2()    
    else:
        dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2=sender.itemTitle)
        characters = ['All', '#', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
        for character in characters:
            dir.Append(Function(DirectoryItem(AlphaListMenu,"%s" % character, thumb=R(CRUNCHYROLL_ICON)), type=type, query=character))
    return dir

def RecentListMenu(sender, type=None):
    startTime = datetime.utcnow()
    dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="Recent")
    episodeList = []
    if type==ANIME_TYPE:
        episodeList = CRAPI.GetRecentAnimeEpisodes()
    elif type==DRAMA_TYPE:
        episodeList = CRAPI.GetRecentDramaEpisodes()
    else:
        episodeList = CRAPI.GetRecentVideos()
        
    for episode in episodeList:
        dir.Append(MakeEpisodeItem(episode))

    dtime = datetime.utcnow()-startTime
    Log.Debug("RecentListMenu %s execution time: %s"%(type, dtime))
    return dir

def PopularListMenu(sender,type=None):
    #FIXME: support drama popular, too?
    startTime = datetime.utcnow()
    dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="Popular")
    seriesList = []
    if type==ANIME_TYPE:
        seriesList = CRAPI.GetPopularAnimeSeries()
    elif type==DRAMA_TYPE:
        seriesList = CRAPI.GetPopularDramaSeries()
    else:
        seriesList = CRAPI.GetPopularVideos()
        
    for series in seriesList:
        dir.Append(MakeSeriesItem(series))
    dtime = datetime.utcnow()-startTime
    Log.Debug("PopularListMenu %s execution time: %s"%(type, dtime))
    return dir

def GenreListMenu(sender,type=None,genre=None):
    """
    Browse type of series (ANIME_TYPE or DRAMA_TYPE) by a genre key that
    exists in DRAMA_GENRE_LIST or ANIME_GENRE_LIST
    """
    #example: http://www.crunchyroll.com/boxee_feeds/genre_drama_romance
    startTime = datetime.utcnow()
    genreList = ANIME_GENRE_LIST if type==ANIME_TYPE else DRAMA_GENRE_LIST
    if genre is not None:
        dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2=genre)
            
        if type == ANIME_TYPE:
            seriesList = CRAPI.GetAnimeSeriesByGenre(genre)
        elif type == DRAMA_TYPE:
            seriesList = CRAPI.GetDramaSeriesByGenre(genre)
        else:
            seriesList = CRAPI.GetSeriesByGenre(genre)
            
        for series in seriesList:
            dir.Append(MakeSeriesItem(series))
        dtime = datetime.utcnow()-startTime
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
    startTime = datetime.utcnow()
    dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2=seriesTitle)
    
    if CRAPI.Login() and CRAPI.IsRegistered():
        dir.Append(
            Function(PopupDirectoryItem(
                    QueueChangePopupMenu, 
                    title="Queue...", 
                    summary="Add or remove this series from your queue."
                ), 
                seriesId=seriesId )
            )

    Log.Debug("Loading episode list for series number " + str(seriesId))
    seasonList = CRAPI.GetListOfSeasonsInSeries(seriesId)
#    Log.Debug("season nums: %s" % seasonNums)
    for seasonId in seasonList:
        season = CRAPI.GetSeasonDict(seasonId)
        dir.Append(MakeSeasonItem(season))
    dtime = datetime.utcnow()-startTime
    Log.Debug("SeriesMenu (%s) execution time: %s"%(seriesId, dtime))
    return dir

def SeasonMenu(sender,seasonId):
    """
    Display a menu showing episodes available in a particular season.
    """
    Log.Debug(str(seasonId))
    season = CRAPI.GetSeasonDict(seasonId)
    dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="%s - Season %s"%(sender.title2,str(season['seasonNumber'])))
    epList = CRAPI.GetListOfEpisodesInSeason(seasonId)#getEpisodeListForSeason(seasonId)
    Log.Debug("len %s"%str(len(epList)))
    
    for episodeId in epList:
        episode = CRAPI.GetEpisodeDict(episodeId)
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
    CRAPI.Login()
    result = CRAPI.RemoveSeriesFromQueue(seriesId)
    if result:
        return MessageContainer("Success",'Removed from Queue')
    else:
        return MessageContainer("Failure", 'Could not remove from Queue.')

def AddToQueue(sender,seriesId,url=None):
    """
    Add seriesId to the queue.
    """
    CRAPI.Login()
    result = CRAPI.AddSeriesToQueue(seriesId)
    
    if result:
        return MessageContainer("Success",'Added to Queue')
    else:
        return MessageContainer("Failure", 'Could not add to Queue.')

def QueueChangePopupMenu(sender, seriesId):
    """
    Popup a Menu asking user if she wants to
    add or remove this series from her queue
    """
    CRAPI.Login()
    dir = MediaContainer(title1="Queue",title2=sender.itemTitle,disabledViewModes=["Coverflow"])
    if CRAPI.IsRegistered():
        queueList = CRAPI.GetQueueList()
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
    if not CRAPI.HasPaid() or Prefs['quality'] != "Ask":
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
            giveChoice = CRAPI.IsPremium(ANIME_TYPE)
        elif kind.lower() == "drama":
            giveChoice = CRAPI.IsPremium(DRAMA_TYPE)
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

    if CRAPI.HasPaid() and CRAPI.IsPremium(checkCat):
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
    series = CRAPI.GetSeriesDict(queueInfo['seriesId'])
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
    CRAPI.Logout()
    if not CRAPI.LoggedIn():
        dir = MessageContainer("Logout", "You are now logged out")
    else:
        dir = MessageContainer("Logout Failure", "Nice try, but logout failed.")
        Log.Debug("####LOGOUT FAILED, HERE'S YOUR COOKIE")
        Log.Debug(HTTP.CookiesForURL(CRAPI._BASE_URL) )

    return dir

def LoginFromMenu(sender):
    if not Prefs['username'] or not Prefs['password']:
        dir = MessageContainer("Login Brain Fart", "You cannot login because your username or password are blank.")
    else:
        result = CRAPI.Login(force = True)
        if not result:
            dir = MessageContainer("Auth failed", "Authentication failed at crunchyroll.com")
        elif CRAPI.IsRegistered():
            dir = MessageContainer("Login", "You are logged in, congrats.")
        else:
            dir = MessageContainer("Login Failure", "Sorry, bro, you didn't login!")
        
    return dir

def ClearCookiesItem(sender):
    HTTP.ClearCookies()
    return MessageContainer("Cookies Cleared", "For whatever it's worth, cookies are gone now.")

    
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

def PlayVideoMenu(sender, mediaId):
    """
    construct and return a MediaContainer that will ask the user
    which resolution of video she'd like to play for episode
    """
    episode = CRAPI.GetEpisodeDict(mediaId)
    startTime = datetime.utcnow()
    dir = MediaContainer(title1="Play Options",title2=sender.itemTitle,disabledViewModes=["Coverflow"])
    if len(episode['availableResolutions']) == 0:
        episode['availableResolutions'] = GetAvailResForMediaId(mediaId)
        
        # FIXME I guess it's better to have something than nothing? It was giving Key error
        # on episode number (kinda silly now since we require the cache...)
        if str(mediaId) not in Dict['episodes']:
            Dict['episodes'][str(mediaId)] = episode
    
        Dict['episodes'][str(mediaId)]['availableResolutions'] = episode['availableResolutions']
    videoInfo = CRAPI.GetVideoInfo(mediaId, episode['availableResolutions'])
    videoInfo['small'] = (CRAPI.HasPaid() and CRAPI.IsPremium(episode.get("category"))) is False

    # duration must be specified before the redirect in PlayVideo()! If not, your device
    # will not recognize the play time.
    try:
        duration = int(episode.get('duration'))
    except TypeError:
        duration = 0

    if Prefs['quality'] == "Ask":
        for q in episode['availableResolutions']:
            videoUrl = CRAPI.GetVideoUrl(videoInfo, q)
            episodeItem = Function(WebVideoItem(PlayVideo, title=Resolution2Quality[q], duration=duration), mediaId=mediaId, resolution=q )
            dir.Append(episodeItem)
    else:
        prefRes = GetPrefRes(episode['availableResolutions'])
        videoUrl = GetVideoUrl(videoInfo, prefRes)
        buttonText = "Play at %sp" % str(prefRes)
        episodeItem = Function(WebVideoItem(PlayVideo, title=buttonText, duration=duration), mediaId=mediaId, resolution = prefRes)
        dir.Append(episodeItem)
    dtime = datetime.utcnow()-startTime
    Log.Debug("PlayVideoMenu (%s) execution time: %s"%(episode['title'], dtime))
    return dir

def PlayVideo(sender, mediaId, resolution=360): # url, title, duration, summary = None, mediaId=None, modifyUrl=False, premium=False):
    from datetime import datetime
    
    if Prefs['restart'] == "Restart":
        CRAPI.DeleteFlashJunk()

    episode = CRAPI.GetEpisodeDict(mediaId)
    if episode:
        
        cat = episode.get("category")
        if cat == "Anime":
            checkCat = ANIME_TYPE
        elif cat == "Drama":
            checkCat = DRAMA_TYPE
        else:
            checkCat = None

                    
        if CRAPI.HasPaid() and CRAPI.IsPremium(checkCat):
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

    CRAPI.Login()
    episode = CRAPI.GetEpisodeDict(mediaId)
    theUrl = CRAPI._MEDIA_URL + str(mediaId)
    resolutions = CRAPI.GetAvailResForMediaId(mediaId)
    vidInfo = CRAPI.GetVideoInfo(mediaId, resolutions)
    vidInfo['small'] = 0

    if episode.get('duration') and episode['duration'] > 0:
        duration = episode['duration']
    else:
        duration = vidInfo['duration'] # need this because duration isn't known until now

    bestRes = resolution

    if Prefs['quality'] != "Ask":
        bestRes = CRAPI.GetPrefRes(resolutions)
    
    bestRes = int(bestRes)
    
    Log.Debug("Best res: " + str(bestRes))

    # we need to tell server so they send the right quality
    CRAPI.SetPrefResolution(int(bestRes))
            
    # FIXME: have to account for drama vs anime premium!
    modUrl = CRAPI.GetVideoUrl(vidInfo, bestRes) # get past mature wall... hacky I know
    
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
    episode = CRAPI.GetEpisodeDict(mediaId)
    infoUrl = CRAPI._MEDIA_URL + str(mediaId) + "?p360=1&skip_wall=1&t=0&small=0&wide=0"

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
