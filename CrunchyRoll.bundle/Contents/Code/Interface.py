import FeedScrapper
import constants2
import DebugCode
#import fanartScrapper
import re
import urllib2
import datetime # more robust than Datetime
import time, os, re
#for cookie wrangling:
from Cookie import BaseCookie
import plistlib
from datetime import datetime, timedelta
from datetime import datetime
#import scrapper



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

def getEpisodeArtUrl(episode):
    """
    return the best background art URL for the passed episode.
    """
    #TODO: consider reimplementing the fanart part
    artUrl = episode['art']
    if artUrl == "" or artUrl is None:
        artUrl = R(CRUNCHYROLL_ART)
    Log.Debug("episode art url: %s"%artUrl)
    return artUrl

def getEpisodeThumbUrl(episode):
    """
    return the best thumbnail URL for the passed episode.
    """
    #TODO: consider reimplementing the fanart part
    thumbUrl = episode['thumb']
    if thumbUrl == "" or thumbUrl is None:
        thumbUrl = R(CRUNCHYROLL_ICON)
    Log.Debug("episode thumb url: %s"%thumbUrl)
    return url

def getSeasonArtUrl(season):
    """
    return the best background art URL for the passed season.
    """
    #TODO: consider reimplementing the fanart part
    artUrl = season['art']
    if artUrl == "" or artUrl is None:
        artUrl = R(CRUNCHYROLL_ART)
    Log.Debug("season art url: %s"%artUrl)
    return artUrl

def getSeasonThumbUrl(season):
    """
    return the best thumbnail URL for the passed season.
    """
    #TODO: consider reimplementing the fanart part
    thumbUrl = season['thumb']
    if thumbUrl == "" or thumbUrl is None:
        thumbUrl = R(CRUNCHYROLL_ICON)
    Log.Debug("season thumb url: %s"%thumbUrl)
    return url

def getSeriesArtUrl(series):
    """
    return the best background art URL for the passed series.
    """
    #TODO: consider reimplementing the fanart part
    artUrl = series['art']
    if artUrl == "" or artUrl is None:
        artUrl = R(CRUNCHYROLL_ART)
    Log.Debug("series art url: %s"%artUrl)
    return artUrl

def getSeriesThumbUrl(series):
    """
    return the best thumbnail URL for the passed series.
    """
    #TODO: consider reimplementing the fanart part
    thumbUrl = series['thumb']
    if thumbUrl == "" or thumbUrl is None:
        thumbUrl = R(CRUNCHYROLL_ICON)
    Log.Debug("series thumb url: %s"%thumbUrl)
    return url


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

def getThumbUrl(url):
    """
    just get the best url instead of the image data itself.
    this can help 'larger thumbs missing' issue
    """
    if url==R(CRUNCHYROLL_ICON):
        return url
    return url

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

def selectArt(url):
    ret = None
    if url==R(CRUNCHYROLL_ART):
        ret = url
    else:
        if url is not None:
            ret = url
        else:
            ret = R(CRUNCHYROLL_ART)
    #Log.Debug("art: %s"%ret)
    return url#ret


def makeSeriesItem(series):
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
            thumb = Function(GetThumb,url=thumbUrl),
            art=Function(GetArt,url=artUrl)
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
            art = Function(GetArt,url=artUrl)),
        seriesId=series['seriesId'],
        seriesTitle=series['title'])
    return seriesItem

def makeSeasonItem(season):
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
            art=Function(GetArt,url=artUrl)),
        seriesId=season['seriesId'],
        season=season['seasonNumber'])
    return seasonItem

def makeEpisodeItem(episode):
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
    
    summary = makeEpisodeSummary(episode)

    if not available:
        episodeItem = Function(DirectoryItem(
                        NotAvailable,
                        title = episode['title'] + " (Not Yet Available)",
                        subtitle = "Season %s"%episode['season'],
                        summary = createRatingString(episode['rating']) + summary,
                        thumb = Function(GetThumb,url=getEpisodeThumbUrl(episode)),
                        art=Function(GetArt,url=getEpisodeArtUrl(episode))
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
            summary = createRatingString(episode['rating']) + summary,
            thumb = Function(GetThumb,url=getEpisodeThumbUrl(episode)),
            art=Function(GetArt,url=getEpisodeArtUrl(episode))
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
                summary = createRatingString(episode['rating']) + summary,
                thumb = Function(GetThumb,url=getEpisodeThumbUrl(episode)),
                art=Function(GetArt,url=getEpisodeArt(episode)),                
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
                summary = createRatingString(episode['rating']) + summary,
                thumb = Function(GetThumb,url=getEpisodeThumbUrl(episode)),
                art=Function(GetArt,url=getEpisodeArtUrl(episode)),
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
        #dir.noCache = 0 # ad hoc
    elif ENABLE_UTILS:
        # limited set of utilities, for production
        dir.Append(Function(DirectoryItem(DebugMenu, "Utilities...", thumb=R(UTILS_ICON)), advanced=False))    

    return dir

"""
                "title": title,
                "upNextMediaId": episodeMediaId,
                "seriesId": seriesId#,
"""

def QueueMenu(sender):
    """
    Show series titles that the user has in her queue
    """
    # FIXME plex seems to cache this, so removing/adding doesn't give feedback
    if isRegistered():
        dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="Series", noCache=True)
        queueList = getQueueList()
        for queueInfo in queueList:
            dir.Append(makeQueueMenuItem(queueInfo))
        return dir
    else:
        return MessageContainer("Log in required", "You must be logged in to view your queue.")

def makeQueueMenuItem(queueInfo):
    """
    construct a directory item for a series existing in user's queue.
    Selecting this item leads to more details about the series, and the ability
    to remove it from the queue.
    """
    Log.Debug("queueinfo: %s" % queueInfo)
    s = Dict['series']
    sId = str(queueInfo['seriesId'])
    series = getSeriesDict(queueInfo['seriesId'])
    thumb = getSeriesThumbUrl(series)#(s[sId]['thumb'] if (sId in s and s[sId]['thumb'] is not None) else R(CRUNCHYROLL_ICON))
    art = getSeriesArtUrl(series)#(s[sId]['art'] if (sId in s and s[sId]['art'] is not None) else R(CRUNCHYROLL_ART))
    queueItem = Function(DirectoryItem(
        QueueEntryMenu,
        title=queueInfo['title'],
        summary=series['description'],#queueInfo['nextUpText'] + queueInfo['episodeDescription'],
        thumb=Function(GetThumb,url=thumb),
        art=Function(GetArt,url=art)
        ), queueInfo=queueInfo)
    return queueItem

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
    thumb = getSeriesThumbUrl(s[sId])#(s[sId]['thumb'] if (sId in s and s[sId]['thumb'] is not None) else R(CRUNCHYROLL_ICON))
    art = getSeriesArtUrl(s[sId])#(s[sId]['art'] if (sId in s and s[sId]['art'] is not None) else R(CRUNCHYROLL_ART))
    if queueInfo['upNextMediaId'] is not None:
        nextEp = getEpisodeDict(queueInfo['upNextMediaId'])#getEpInfoFromLink(queueInfo['epToPlay'])
        PlayNext = makeEpisodeItem(nextEp)
        dir.Append(PlayNext)
    RemoveSeries = Function(DirectoryItem(RemoveFromQueue, title="Remove series from queue"), seriesId=sId)
    ViewSeries = Function(DirectoryItem(SeriesMenu, "View Series", thumb=thumb, art=Function(GetArt,url=art)), seriesId=queueInfo['seriesId'])
    dir.Append(RemoveSeries)
    dir.Append(ViewSeries)
    dir.noCache = 1
    return dir

"""
def QueuePopupMenu(sender, queueInfo):
    #FIXME this is skipped for now, we go straight into QueueItemMenu
    dir = MediaContainer(title1="Play Options",title2=sender.itemTitle,disabledViewModes=["Coverflow"])#, noCache=True)
    ViewQueueItem = Function(DirectoryItem(QueueItemMenu, "View"), queueInfo=queueInfo)
    RemoveSeries = Function(DirectoryItem(RemoveFromQueue, title="Remove from queue"), seriesId=queueInfo['seriesId'])
    dir.Append(ViewQueueItem)
    dir.Append(RemoveSeries)
    dir.noCache=1
    return dir
"""

def PopularVideosMenu(sender):
    """
    show popular videos.
    """
    episodeList = getPopularVideos()
    if episodeList:
        dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="Popular")
        for episode in episodeList:
            dir.Append(makeEpisodeItem(episode))
        dir.noCache = 1
        return dir
    else:
        return MessageContainer("No recent additions", "No recent videos found.")
    
def RecentAdditionsMenu(sender):
    """
    show recently added videos
    """
    episodeList = getRecentVideos()
    if episodeList:
        dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="Recent")
        for episode in episodeList:
            dir.Append(makeEpisodeItem(episode))
        dir.noCache = 1
        return dir
    else:
        return MessageContainer("No recent additions", "No recent videos found.")


def SearchMenu(sender, query=""):
    """
    search cruncyroll.com/rss and return results in a media container
    """
    episodeList = getEpisodeListFromQuery(query)
    if episodeList:
        dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2=query)
        for episode in episodeList:
            if episode.has_key('seriesTitle') and episode['seriesTitle'].lower() not in episode['title'].lower():
                episode['title'] = episode['seriesTitle'] + ": " + episode['title']
            dir.Append(makeEpisodeItem(episode))
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
    
    if type == ANIME_TYPE:
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
            seriesList = getAnimeSeriesList()
        elif type==DRAMA_TYPE:
            seriesList = getDramaSeriesList()
        else:
            seriesList = getAllSeries()

        seriesList = sorted(seriesList, key=lambda k: getSortTitle(k)) 
                   
        for series in seriesList:
            sortTitle =  getSortTitle(series)
            if sortTitle.startswith(queryCharacters):
                dir.Append(makeSeriesItem(series))
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
        episodeList = getRecentAnimeEpisodes()
    elif type==DRAMA_TYPE:
        episodeList = getRecentDramaEpisodes()
    else:
        episodeList = []
        
    for episode in episodeList:
        dir.Append(makeEpisodeItem(episode))

    dtime = Datetime.Now()-startTime
    Log.Debug("RecentListMenu %s execution time: %s"%(type, dtime))
    return dir


def PopularListMenu(sender,type=None):
    #FIXME: support drama popular, too?
    startTime = Datetime.Now()
    dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="Popular")
    seriesList = []
    if type==ANIME_TYPE:
        seriesList = getPopularAnimeSeries()
    elif type==DRAMA_TYPE:
        #FIXME: this returns an empty list.
        seriesList = getPopularDramaSeries()
    else:
        seriesList = []
        
    for series in seriesList:
        dir.Append(makeSeriesItem(series))
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
            seriesList = getAnimeSeriesByGenre(genre)
        elif type == DRAMA_TYPE:
            seriesList = getDramaSeriesByGenre(genre)
        else:
            seriesList = getSeriesByGenre(genre)
            
        for series in seriesList:
            dir.Append(makeSeriesItem(series))
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
    seasonList = getListOfSeasonsInSeries(seriesId)
#    Log.Debug("season nums: %s" % seasonNums)
    for seasonId in seasonList:
        season = getSeasonDict(seasonId)
        dir.Append(makeSeasonItem(season))
    dtime = Datetime.Now()-startTime
    Log.Debug("SeriesMenu (%s) execution time: %s"%(seriesId, dtime))
    return dir

def SeasonMenu(sender,seasonId):
    """
    Display a menu showing episodes available in a particular season.
    """
    season = getSeasonDict(seasonId)
    dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="%s - Season %s"%(sender.title2,str(season['season'])))
    epList = getListOfEpisodesInSeason(seasonId)#getEpisodeListForSeason(seasonId)
    for episodeId in epList:
        episode = getEpisodeDict(episodeId)
        dir.Append(makeEpisodeItem(episode))
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
        queueList = getQueueList()
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
    

"""
TODO: is this used anywhere
"""
def getVideoUrl(videoInfo, resolution):
    """
    construct a URL to display at resolution based on videoInfo
    without checking for coherence to what the site's got
    or if the resolution is valid
    """

    url = videoInfo['baseUrl']+"?p" + str(resolution) + "=1"
    # we always skip adult filtering (it's done in the presentation code before we reach here)
    url = url + "&skip_wall=1"
    url = url + ("&t=0" if Prefs['restart'] == 'Restart' else "")
    url = url + "&small="+("1" if videoInfo['small'] is True else "0")
    url = url + "&wide="+("1" if videoInfo['wide'] is True or JUST_USE_WIDE is True else "0")
    return url


    
def PlayVideoMenu(sender, mediaId):
    """
    construct and return a MediaContainer that will ask the user
    which resolution of video she'd like to play for episode
    """
    episode = getEpisodeDict(mediaId)
    startTime = Datetime.Now()
    dir = MediaContainer(title1="Play Options",title2=sender.itemTitle,disabledViewModes=["Coverflow"])
    if len(episode['availableResolutions']) == 0:
        episode['availableResolutions'] = getAvailResFromPage(episode['link'])
        
        # FIXME I guess it's better to have something than nothing? It was giving Key error
        # on episode number (kinda silly now since we require the cache...)
        if str(episode['mediaId']) not in Dict['episodes']:
            Dict['episodes'][str(episode['mediaId'])] = episode
    
        Dict['episodes'][str(episode['mediaId'])]['availableResolutions'] = episode['availableResolutions']
    videoInfo = getVideoInfo(episode['link'], episode['mediaId'], episode['availableResolutions'])
    videoInfo['small'] = (hasPaid() and isPremium(episode.get("category"))) is False

    # duration must be specified before the redirect in PlayVideo()! If not, your device
    # will not recognize the play time.
    try:
        duration = int(episode.get('duration'))
    except TypeError:
        duration = 0

    if Prefs['quality'] == "Ask":
        for q in episode['availableResolutions']:
            videoUrl = getVideoUrl(videoInfo, q)
            episodeItem = Function(WebVideoItem(PlayVideo, title=Resolution2Quality[q], duration=duration), mediaId=episode['mediaId'], resolution=q )
            dir.Append(episodeItem)
    else:
        prefRes = getPrefRes(episode['availableResolutions'])
        videoUrl = getVideoUrl(videoInfo, prefRes)
        buttonText = "Play at %sp" % str(prefRes)
        episodeItem = Function(WebVideoItem(PlayVideo, title=buttonText, duration=duration), mediaId=episode['mediaId'], resolution = prefRes)
        dir.Append(episodeItem)
    dtime = Datetime.Now()-startTime
    Log.Debug("PlayVideoMenu (%s) execution time: %s"%(episode['title'], dtime))
    return dir

def PlayVideo(sender, mediaId, resolution=360): # url, title, duration, summary = None, mediaId=None, modifyUrl=False, premium=False):
    from datetime import datetime
    
    if Prefs['restart'] == "Restart":
        deleteFlashJunk()

    episode = getEpisodeDict(mediaId)
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
    # It's difficult to know how to acheive 1080p with boxee (or web player!). 
    # It's really easy to set resolution with direct grab of stream.
    # Only premium members get better resolutions.
    # so the solution is to have 2 destinations: freebie (web player), or premium (direct).

    login()
    episode = getEpisodeDict(mediaId)
    theUrl = episode['link']
    resolutions = getAvailResFromPage(theUrl)
    vidInfo = getVideoInfo(theUrl, mediaId, resolutions)
    vidInfo['small'] = 0

    if episode.get('duration') and episode['duration'] > 0:
        duration = episode['duration']
    else:
        duration = vidInfo['duration'] # need this because duration isn't known until now

    bestRes = resolution

    if Prefs['quality'] != "Ask":
        bestRes = getPrefRes(resolutions)
    
    bestRes = int(bestRes)
    
    Log.Debug("Best res: " + str(bestRes))

    # we need to tell server so they send the right quality
    setPrefResolution(int(bestRes))
            
    # FIXME: have to account for drama vs anime premium!
    modUrl = getVideoUrl(vidInfo, bestRes) # get past mature wall... hacky I know
    
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
    episode = getEpisodeDict(mediaId)
    infoUrl = episode['link'] + "?p360=1&skip_wall=1&t=0&small=0&wide=0"

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
    
        


########################################################################################
# web and json api stuff
########################################################################################



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
    # FIXME a better way would be to use API, but I don't know how to request status
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
        if "Anime Member!" in req.content:
            authInfo['AnimePremium'] = True
        if "Drama Member!" in req.content: #FIXME untested!
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

    # this modifies Safari's cookies to be regular
    
    loginSuccess = False
    if not Dict['Authentication'] : resetAuthInfo()
    
    authInfo = Dict['Authentication'] #dicts are mutable, so authInfo is a reference & will change Dict presumably
    if Prefs['username'] and Prefs['password']:

        # fifteen minutes is reasonable.
        # this also prevents spamming server
        if (force == False) and (time.time() - authInfo['loggedInSince']) < LOGIN_GRACE:
            return True

        if force: 
            HTTP.ClearCookies()
#            killSafariCookies()
            authInfo['loggedInSince'] = 0
            authInfo['failedLoginCount'] = 0
            #Dict['Authentication'] = authInfo

        if not force and authInfo['failedLoginCount'] > 2:
            return False # Don't bash the server, just inform caller
        
        if loggedIn():
            authInfo['failedLoginCount'] = 0
            authInfo['loggedInSince'] = time.time()
            #Dict['Authentication'] = authInfo
            return True
        else:
            Log.Debug("#####WEB LOGIN CHECK FAILED, MUST LOG IN MANUALLY")

        # if we reach here, we must manually log in.
        if not force:
            #save about 2 seconds
#            killSafariCookies()
            HTTP.ClearCookies()

        loginSuccess = loginViaApi(authInfo)
            
        #check it
        if loginSuccess or loggedIn():
            authInfo['loggedInSince'] = time.time()
            authInfo['failedLoginCount'] = 0
            #Dict['Authentication'] = authInfo
#            transferCookiesToSafari()
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
    
    # this doesn't seem to help. Cookies still infect the system somewhere (and it's NOT
    # safari, i checked). So whatever. at best, we can try to be secure and fail. Good
    # faith, you know.
    HTTP.ClearCookies()
#    killSafariCookies()
    
    #this turns every permission off:
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

########################################################################################
# parsing of RSS feeds and so on (used to be scrapper.py)
########################################################################################




###########
# these bad boys are here to keep __init__.py from manipulating rss feeds directly
# and to keep feed handling in one place.
###########

def GetThumb(url, tvdbId=None):
    """
    find a better thumb and return result
    """
    return getThumb(url,tvdbId)

def GetArt(url,tvdbId=None):
    """
    find a fanart url
    """
    return getArt(url, tvdbId)

def getSortTitle(dictList):
    """
    get the 'title' key and return the sortable title as string
    """
    title = dictList['title'].lower().strip()
    firstword = title.split(" ",1)[0]
    if firstword in ['a', 'an', 'the']:
        title = title.split(firstword, 1)[-1]
    return title.strip()

