import string
import time
import re

BASE_URL                     = "http://www.crunchyroll.com"

CRUNCHYROLL_PLUGIN_PREFIX    = "/video/CrunchyRoll"
CRUNCHYROLL_ART              = 'art-default.jpeg'
CRUNCHYROLL_ICON             = 'icon-default.jpg'

ANIME_ICON                   = CRUNCHYROLL_ICON#'icon-anime.png'
DRAMA_ICON                   = CRUNCHYROLL_ICON#'icon-drama.png'
QUEUE_ICON                   = CRUNCHYROLL_ICON#'icon-queue.png'
PREFS_ICON                   = 'icon-prefs.png'

FEED_BASE_URL                = "http://www.crunchyroll.com/boxee_feeds/"

THUMB_QUALITY                = {"Low":"_medium","Medium":"_large","High":"_full"}
VIDEO_QUALITY                = {"SD":"360","480P":"480","720P":"720"}

LAST_PLAYER_VERSION = "20111130163346.fb103f9787f179cd0f27be64da5c23f2"
PREMIUM_TYPE_ANIME = '2'
PREMIUM_TYPE_DRAMA = '4'
ANIME_TYPE = "Anime"
DRAMA_TYPE = "Drama"
RES_NAMES = {'12':'SD', '20':'480P', '21':'720P'}

ANIME_GENRE_LIST = {
	'Action':'action',
	'Adventure':'adventure',
	'Comedy':'comedy',
	'Drama':'drama',
	'Ecchi':'ecchi',
	'Fantasy':'fantasy',
	'Harem':'harem',
	'Horror':'horror',
	'Magic':'magic',
	'Martial Arts':'martial_arts',
	'Mecha':'mecha',
	'Military':'military',
	'Parody':'parody',
	'Psychological':'psychological',
	'Romance':'romance',
	'Science Fiction':'science_fiction',
	'Shoujo':'shoujo',
	'Slice of Life':'slice_of_life',
	'Space':'space',
	'Sports':'sports',
	'Supernatural':'supernatural',
	'Tournament':'tournament'
}

DRAMA_GENRE_LIST = {
	'Action':'action',
	'Adventure':'adventure',
	'Comedy':'comedy',
	'Drama':'drama',
	'Ecchi':'ecchi',
	'Fantasy':'fantasy',
	'Harem':'harem',
	'Horror':'horror',
	'Magic':'magic',
	'Martial Arts':'martial_arts',
	'Mecha':'mecha',
	'Military':'military',
	'Parody':'parody',
	'Psychological':'psychological',
	'Romance':'romance',
	'Science Fiction':'science_fiction',
	'Shoujo':'shoujo',
	'Slice of Life':'slice_of_life',
	'Space':'space',
	'Sports':'sports',
	'Supernatural':'supernatural',
	'Tournament':'tournament'
}

USING_BOXEE_FEEDS = False
GET_EXTRA_INFO = False
USE_LOGIN_AT_START = True
USE_DURATION = True
JUST_USE_WIDE = False
SPLIT_LONG_LIST = True
DOUBLE_CHECK_AVAIL_RES = True

HTTP.CacheTime = 3600
HTTP.Headers["User-agent"] = "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_6; en-gb) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16"
HTTP.Headers["Accept-Encoding"] = "gzip, deflate"
HTTP.ClearCookies()

API_URL = "://www.crunchyroll.com/ajax/"
API_HEADERS = {
'User-Agent':"Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_6; en-gb) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16",
'Host':"www.crunchyroll.com",
'Accept-Language':"en,en-US;q=0.9,ja;q=0.8,fr;q=0.7,de;q=0.6,es;q=0.5,it;q=0.4,pt;q=0.3,pt-PT;q=0.2,nl;q=0.1,sv;q=0.1,nb;q=0.1,da;q=0.1,fi;q=0.1,ru;q=0.1,pl;q=0.1,zh-CN;q=0.1,zh-TW;q=0.1,ko;q=0.1",
'Accept-Encoding':"gzip, deflate",
'Cookie':"",
'Accept':"*/*",
'X-Requested-With':"XMLHttpRequest",
'Content-Transfer-Encoding':"binary",
'Content-Type':"application/x-www-form-urlencoded"
}

def makeAPIRequest(values,referer=None):
	h = API_HEADERS
	if not referer is None:
		h['Referer'] = referer
	h['Cookie']=HTTP.GetCookiesForURL(BASE_URL)
	req = HTTP.Request("https"+API_URL,values=values,cacheTime=0,immediate=True, headers=h)
	response = re.sub(r'\n\*/$', '', re.sub(r'^/\*-secure-\n', '', req.content))
	return response


def makeAPIRequest2(data,referer=None):
	h = API_HEADERS
	if not referer is None:
		h['Referer'] = referer
	h['Cookie']=HTTP.GetCookiesForURL(BASE_URL)
	req = HTTP.Request("http"+API_URL,data=data,cacheTime=0,immediate=True, headers=h)
	response = re.sub(r'\n\*/$', '', re.sub(r'^/\*-secure-\n', '', req.content))
	return response


def LoginAtStart():
	global GlobalWasLoggedIn
	global AnimePremium
	global DramaPremium
	if LoginNotBlank():
		data = { "name": Prefs['username'], "password": Prefs['password'], "req": "RpcApiUser_Login" }
		response = makeAPIRequest(data)
		Log.Debug("loginResponse:%s"%response)
		response = JSON.ObjectFromString(response)
		GlobalWasLoggedIn = (response.get('result_code') == 1)
		AnimePremium = (response.get('data').get('premium').get(PREMIUM_TYPE_ANIME) == 1)
		DramaPremium = (response.get('data').get('premium').get(PREMIUM_TYPE_DRAMA) == 1)
	return GlobalWasLoggedIn


def LoggedIn():
	return GlobalWasLoggedIn


def Login():
	if LoginNotBlank():
		data = { "name": Prefs['username'], "password": Prefs['password'], "req": "RpcApiUser_Login" }
		response = makeAPIRequest(data)


def Logout():
	req = HTTP.Request(url='https://www.crunchyroll.com/logout', immediate=True, cacheTime=10, headers={'Referer':'https://www.crunchyroll.com'})
	GlobalWasLoggedIn = False


def LoginNotBlank():
	r = False
	if Prefs['username'] is not None and Prefs['password'] is not None:
		r = True
	return r


def isPremium(epType):
	return (epType is ANIME_TYPE and AnimePremium is True) or (epType is DRAMA_TYPE and DramaPremium is True)


import scrapper

def Start():
	global GlobalWasLoggedIn
	GlobalWasLoggedIn = None
	Plugin.AddPrefixHandler(CRUNCHYROLL_PLUGIN_PREFIX, TopMenu, "CrunchyRoll", CRUNCHYROLL_ICON, CRUNCHYROLL_ART)
	#Plugin.AddViewGroup("List", viewMode = "List", mediType = )
	MediaContainer.art = R(CRUNCHYROLL_ART)
	MediaContainer.title1 = "CrunchyRoll"
	#MediaContainer.viewGroup = "List"
	#DirectoryItem.thumb = R(CRUNCHYROLL_ICON)
	LoginAtStart()
	if 'episodes' not in Dict:
		Dict['episodes'] = {}
	if 'playerXmp' not in Dict:
		Dict['playerXml'] = {}
	if 'series' not in Dict:
		Dict['series'] = {}


def CreatePrefs():
	Prefs.Add(id='loginemail', type='text', default="", label='Login Email')
	Prefs.Add(id='password', type='text', default="", label='Password', option='hidden')
	Prefs.Add(id='quality', type='enum', values=["SD", "480P", "720P", "Highest Avalible"], default="Highest Avalible", label="Quality")
	Prefs.Add(id='thumb_quality', type='enum', values=["Low", "Medium", "High"], default="High", label="Thumbnail Quality")
	Prefs.Add(id='restart', type='enum', values=["Resume", "Restart"], default="Restart", label="Resume or Restart")


def ValidatePrefs():
	u = Prefs['username']
	p = Prefs['password']
	if GlobalWasLoggedIn:
		Logout()
	lf = LoginNotBlank()
	if lf:
		lv = LoginAtStart()
		if lv is True:
			mc = MessageContainer("Success", "Details have been saved.")
		else:
			mc = MessageContainer("Error", "Could not login with the provided username and password.")
	else:
		if u is not None or p is not None:
			if u is not None and p is None:
				mc = MessageContainer("Error", "Username provided but no password.")
			elif p is not None and u is None:
				mc = MessageContainer("Error", "Password provided but no username.")
		else:
			mc = MessageContainer("Success", "Details have been saved.")
	return mc


def TopMenu():
	global GlobalWasLoggedIn
	scrapper.returnPlayer()
	dir = MediaContainer(disabledViewModes=["Coverflow"], title1="Crunchyroll")
	dir.Append(Function(DirectoryItem(Menu,"Browse Anime", thumb=R(ANIME_ICON)), type=ANIME_TYPE))
	dir.Append(Function(DirectoryItem(Menu,"Browse Drama", thumb=R(DRAMA_ICON)), type=DRAMA_TYPE))
	if LoggedIn() is True:
		dir.Append(Function(DirectoryItem(QueueMenu,"Browse Queue", thumb=R(QUEUE_ICON))))
	dir.Append(PrefsItem(L('Preferences'), thumb=R(PREFS_ICON)))
	#dir.nocache = 1
	
	return dir


def Menu(sender,type=None):
	if type==ANIME_TYPE:
		all_icon = ANIME_ICON
	elif type==DRAMA_TYPE:
		all_icon = DRAMA_ICON
		
	dir = MediaContainer(disabledViewModes=["coverflow"], title1=sender.title1)
	dir.Append(Function(DirectoryItem(AlphaListMenu,"All %s" % type, thumb=R(all_icon)), type=type))
	if type=="Anime":
		dir.Append(Function(DirectoryItem(PopularListMenu,"Popular %s" % type, thumb=R(all_icon)), type=type))
		#dir.Append(Function(DirectoryItem(RecentListMenu,"Recent %s" % type, thumb=R(all_icon)), type=type))
		dir.Append(Function(DirectoryItem(GenreListMenu,"%s by Genres" % type, thumb=R(CRUNCHYROLL_ICON)), type=type))
	return dir


def AlphaListMenu(sender,type=None,query=None):
	if query is not None:
		if query=="#":
			queryCharacters = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')
		elif query=="All":
			queryCharacters = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z')
		else:
			queryCharacters = (query.lower(), query.upper())
		dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2=query)
		seriesList = scrapper.getSeriesListFromFeed("genre_anime_all" if ANIME_TYPE==type else "drama")
		for series in seriesList:
			if series['title'].startswith(queryCharacters):
				dir.Append(makeSeriesItem(series))		
	else:
		dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2=sender.itemTitle)
		characters = ['All', '#', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
		for character in characters:
			dir.Append(Function(DirectoryItem(AlphaListMenu,"%s" % character, thumb=R(CRUNCHYROLL_ICON)), type=type, query=character))
	return dir


def PopularListMenu(sender,type=None):
	listRoot = BASE_URL + "/" + type.lower()
	dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="Popular")
	seriesList = scrapper.getSeriesListFromFeed("anime_popular")
	for series in seriesList:
		dir.Append(makeSeriesItem(series))
	return dir


def GenreListMenu(sender,type=None,query=None):
	genreList = ANIME_GENRE_LIST if type==ANIME_LIST else DRAMA_GENRE_LIST
	if query is not None:
		dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2=query)
		queryStr = genreList[query].replace('_', '%20')
		feed = "anime_withtag/" + queryStr
		seriesList = scrapper.getSeriesListFromFeed(feed)
		for series in seriesList:
			dir.Append(makeSeriesItem(series))
	else:
		dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2=sender.itemTitle)
		keyList = genreList.keys()
		keyList.sort()
		for genre in keyList:
			Log.Debug("genre: %s" % genre)
			dir.Append(Function(DirectoryItem(GenreListMenu,"%s" % genre, thumb=R(CRUNCHYROLL_ICON)), type=type, query=genre))
	return dir



def ShowMenu(sender,seriesId=None):
	dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="Series")
	episodes = scrapper.getEpisodeListForSeries(seriesId)
	if episodes['useSeasons'] is True:
		seasonNums = episodes['seasons'].keys()
		Log.Debug("season nums: %s" % seasonNums)
		for seasonNum in seasonNums:
			seasonName = "Season %s" % seasonNum
			season = {}
			#season['episodes'] = episodes['seasons'][seasonNum]
			season['url'] = scrapper.seriesTitleToUrl(Dict['series'][str(seriesId)]['title'])
			season['title'] = seasonName
			season['description'] = ""
			season['seasonnum'] = seasonNum
			season['seriesId'] = seriesId
			#season['thumb'] = 
			dir.Append(makeSeasonItem(season))
	else:
		for episode in episodes['episodeList']:
			dir.Append(makeEpisodeItem(episode))
	return dir


def SeasonMenu(sender,seriesId=None,season=None):
	dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="Series")
	epList = scrapper.getSeasonEpisodeListFromFeed(seriesId, season)
	for episode in epList:
		dir.Append(makeEpisodeItem(episode))
	return dir


def QueueMenu(sender):
	dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="Series", noCache=True)
	queueList = scrapper.getQueueList()
	for queue in queueList:
		dir.Append(makeQueueItem(queue))
	dir.noCache = 1
	return dir


def makeSeriesItem(series):
	url = scrapper.seriesTitleToUrl(series['title'])
	seriesItem = Function(
		PopupDirectoryItem(
			SeriesPopoutMenu,
			series['title'],
			summary=series['description'],
			thumb=series['thumb'],
			art=series['thumb'],
		),
		url=url,
		seriesId=series['seriesId']
	)
	return seriesItem


def makeSeasonItem(season):
	seasonItem = Function(
		DirectoryItem(
			SeasonMenu,
			season['title'],
			summary=season['description']#,
			#thumb=season['thumb'],
			#art=season['thumb'],
		),
		seriesId=season['seriesId'],
		season=season['seasonnum']
	)
	return seasonItem


def makeEpisodeItem(episode):
	summary = makeEpisodeSummary(episode)
	episodeItem = Function(
		PopupDirectoryItem(
			playVideoMenu,
			title = episode['title'],
			subtitle = episode['season'],
			summary = summary,
			thumb = episode['thumb']
		),
		episode=episode
	)
	return episodeItem

def makeEpisodeSummary(episode):
	summary = ""
	if episode['publisher'] != '':
		summary = "%sPublisher: %s\n" % (summary, episode['publisher'])
	if episode['season'] != '':
		summary = "%sSeason: %s\n" % (summary, episode['season'])
	if episode['keywords'] != '':
		summary = "%sKeywords: %s\n" % (summary, episode['keywords'])
	if summary != '':
		summary = "%s\n%s" % (summary,episode['description'])
	else:
		summary = episode['description']
	return summary


def makeQueueItem(queueInfo):
	Log.Debug("queueinfo: %s" % queueInfo)
	queueItem = Function(PopupDirectoryItem(QueueItemMenu, title=queueInfo['title']), queueInfo=queueInfo)
	return queueItem

def removeFromQueue(sender,mediaId):
	response = makeAPIRequest2("req=RpcApiUserQueue_Delete&group_id=%s"%mediaId)
	Log.Debug("remove response: %s"%response)
	return MessageContainer("Success",'Removed from Queue')

def addToQueue(sender,mediaId,url):
	Log.Debug("add mediaid: %s"%mediaId)
	response = makeAPIRequest2("req=RpcApiUserQueue_Add&group_id=%s"%mediaId)
	Log.Debug("add response: %s"%response)
	return MessageContainer("Success",'Added to Queue')


def QueueItemMenu(sender, queueInfo):
	dir = MediaContainer(title1="Play Options",title2=sender.itemTitle,disabledViewModes=["Coverflow"])#, noCache=True)
	seriesurl = scrapper.seriesTitleToUrl(queueInfo['title'])
	nextEp = scrapper.getEpInfoFromLink(queueInfo['epToPlay'])
	PlayNext = Function(
		DirectoryItem(
			playVideoMenu,
			title="Play Next",
			subtitle=nextEp['title'],
			summary=nextEp['description'],
			thumb=nextEp['thumb']
		),
		episode=nextEp
	)
	ViewSeries = Function(DirectoryItem(ShowMenu, "View Series"), url=seriesurl)
	RemoveSeries = Function(DirectoryItem(removeFromQueue, title="Remove from queue"), mediaId=queueInfo['mediaId'])
	dir.Append(PlayNext)
	dir.Append(ViewSeries)
	dir.Append(RemoveSeries)
	return dir


def SeriesPopoutMenu(sender, url, seriesId):
	dir = MediaContainer(title1="Play Options",title2=sender.itemTitle,disabledViewModes=["Coverflow"])
	ViewSeries = Function(DirectoryItem(ShowMenu, "View Episodes"), seriesId=seriesId)
	AddSeries = Function(DirectoryItem(addToQueue, title="Add To queue"), mediaId=seriesId, url=url.replace(".rss",""))
	dir.Append(ViewSeries)
	dir.Append(AddSeries)
	return dir


def getVideoUrl(videoInfo, quality):
	url = videoInfo['baseUrl']+"?p"+VIDEO_QUALITY[RES_NAMES[quality]]+"=1"
	Log.Debug("pref: %s"%Prefs['restart'])
	url = url + ("&t=0" if Prefs['restart'] == 'Restart' else "")
	url = url + "&small="+("1" if videoInfo['small'] is True else "0")
	url = url + "&wide="+("1" if videoInfo['wide'] is True or JUST_USE_WIDE is True else "0")
	return url


def playVideoMenu(sender, episode):
	dir = MediaContainer(title1="Play Options",title2=sender.itemTitle,disabledViewModes=["Coverflow"])
	if len(episode['availableResolutions']) == 0:
		episode['availableResolutions'] = scrapper.getAvailResFromPage(episode['link'], ['12'])
		Dict['episodes'][str(episode['mediaId'])]['availableResolutions'] = episode['availableResolutions']
	videoInfo = scrapper.getVideoInfo(episode['link'], episode['mediaId'], episode['availableResolutions'])
	videoInfo['small'] = (GlobalWasLoggedIn is True and isPremium(episode['type']) is True)
	if Prefs['quality'] is "Ask":
		for q in episode['availableResolutions']:
			videoUrl = getVideoUrl(videoInfo, q)
			episodeItem = Function(WebVideoItem(PlayVideo, title=RES_NAMES[q]), url=videoUrl, title=episode['title'], duration=videoInfo['duration'])
			dir.Append(episodeItem)
	else:
		prefRes = scrapper.getPrefRes(episode['availableResolutions'])
		videoUrl = getVideoUrl(videoInfo, prefRes)
		episodeItem = Function(WebVideoItem(PlayVideo, title="Play"), url=videoUrl, title=episode['title'], duration=videoInfo['duration'])
		dir.Append(episodeItem)
	return dir


def PlayVideo(sender, url, title, duration):
	return Redirect(WebVideoItem(url, title = title, duration = duration))


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


def msToRuntime(ms):
	
    if ms is None or ms <= 0:
        return None
		
    ret = []
	
    sec = int(ms/1000) % 60
    min = int(ms/1000/60) % 60
    hr  = int(ms/1000/60/60)
	
    return "%02d:%02d:%02d" % (hr,min,sec)

	
