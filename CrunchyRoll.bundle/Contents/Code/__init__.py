import string
import time
import re
import os
import urllib

BASE_URL                     = "http://www.crunchyroll.com"

CRUNCHYROLL_PLUGIN_PREFIX    = "/video/CrunchyRoll"
CRUNCHYROLL_ART              = 'art-default3.jpg'
CRUNCHYROLL_ICON             = 'icon-default.png'

ANIME_ICON                   = CRUNCHYROLL_ICON#'icon-anime.png'
DRAMA_ICON                   = CRUNCHYROLL_ICON#'icon-drama.png'
QUEUE_ICON                   = CRUNCHYROLL_ICON#'icon-queue.png'
PREFS_ICON                   = 'icon-prefs.png'

FEED_BASE_URL                = "http://www.crunchyroll.com/boxee_feeds/"

THUMB_QUALITY                = {"Low":"_medium","Medium":"_large","High":"_full"}
VIDEO_QUALITY                = {"SD":"360","480P":"480","720P":"720", "1080P":"1080"}

LAST_PLAYER_VERSION = "20111130163346.fb103f9787f179cd0f27be64da5c23f2"
PREMIUM_TYPE_ANIME = '2'
PREMIUM_TYPE_DRAMA = '4'
ANIME_TYPE = "Anime"
DRAMA_TYPE = "Drama"


Boxee2Resolution = {'12':360, '20':480, '21':720}
Resolution2Quality = {360:"SD", 480: "480P", 720: "720P", 1080: "1080P"}
# NOTE: this is also in scrapper.py
Quality2Resolution = {"SD":360, "480P":480, "720P":720, "1080P": 1080, "Highest Available":1080, "Ask":360}

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

DRAMA_GENRE_LIST = {}

JUST_USE_WIDE = False
CHECK_PLAYER = False
SPLIT_LONG_LIST = True

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

import fanartScrapper
import urllib2

def getThumb(url,tvdbId=None):
	ret = None
	if (tvdbId is not None and Prefs['fanart'] is True):
		thumb = fanartScrapper.getRandImageOfTypes(tvdbId,['tvthumbs'])
		if thumb is None: thumb = url
		url=thumb
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
			except: pass
	if ret is None:
		return R(CRUNCHYROLL_ICON)
	else:
		return ret


def selectArt(url,tvdbId=None):
	ret = None
	if (tvdbId is not None and Prefs['fanart'] is True):
		art = fanartScrapper.getRandImageOfTypes(tvdbId,['clearlogos','cleararts'])
		if art is None: art = url
		url=art
	if url==R(CRUNCHYROLL_ART):
		ret = url
	else:
		if url is not None:
			ret = url
		else:
			ret = R(CRUNCHYROLL_ART)
	#Log.Debug("art: %s"%ret)
	return url#ret
	

def getArt(url,tvdbId=None):
	ret = None
	if (tvdbId is not None and Prefs['fanart'] is True):
		art = fanartScrapper.getRandImageOfTypes(tvdbId,['clearlogos','cleararts'])
		if art is None: art = url
		url=art
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
		except: pass
	if ret is None:
		req = urllib2.Request("http://127.0.0.1:32400"+R(CRUNCHYROLL_ART))
		return DataObject(urllib2.urlopen(req).read(), 'image/jpeg')
	else:
		return ret


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
	HTTP.ClearCookies()
	if LoginNotBlank():
		data = { "name": Prefs['username'], "password": Prefs['password'], "req": "RpcApiUser_Login" }
		response = makeAPIRequest(data)
		Log.Debug("loginResponse:%s"%response)
		response = JSON.ObjectFromString(response)
		GlobalWasLoggedIn = (response.get('result_code') == 1)
		if GlobalWasLoggedIn:
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
	if Prefs['username'] and Prefs['password']: return True
	return False


def isPremium(epType):
	return (epType is ANIME_TYPE and AnimePremium is True) or (epType is DRAMA_TYPE and DramaPremium is True)


import scrapper, tvdbscrapper

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
	if 'series' not in Dict:
		Dict['series'] = {}
	if 'fanart' not in Dict:
		Dict['fanart'] = {}
	if 1==0:
		testCacheAll()
	if False is True:
		scrapper.cacheAllSeries()
		listAllEpTitles()


def CreatePrefs():
	Prefs.Add(id='loginemail', type='text', default="", label='Login Email')
	Prefs.Add(id='password', type='text', default="", label='Password', option='hidden')
	Prefs.Add(id='quality', type='enum', values=["SD", "480P", "720P", "1080P", "Highest Available"], default="Highest Available", label="Quality")
	Prefs.Add(id='thumb_quality', type='enum', values=["Low", "Medium", "High"], default="High", label="Thumbnail Quality")
	Prefs.Add(id='restart', type='enum', values=["Resume", "Restart"], default="Restart", label="Resume or Restart")
	Prefs.Add(id='fanart', type='bool', default="true", label="Use Fanart.tv when possible?")


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
	#scrapper.CacheAll()
	#Log.Debug("num of eps: %s"%(len(Dict['episodes'])))
	#Log.Debug("num of shows: %s"%(len(Dict['series'])))
	
	if 1==0:
		Dict['episodes'] = Data.LoadObject("episodes")
		Dict['series'] = Data.LoadObject("series")
		Dict['fanart'] = Data.LoadObject("fanart")

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


def TopMenu():
	global GlobalWasLoggedIn
	if CHECK_PLAYER is True:
		scrapper.returnPlayer()
	Log.Debug("art: %s"%R(CRUNCHYROLL_ART))
	dir = MediaContainer(disabledViewModes=["Coverflow"], title1="Crunchyroll")
	dir.Append(Function(DirectoryItem(Menu,"Browse Anime", thumb=R(ANIME_ICON), art=R(CRUNCHYROLL_ART)), type=ANIME_TYPE))
	dir.Append(Function(DirectoryItem(Menu,"Browse Drama", thumb=R(DRAMA_ICON), art=R(CRUNCHYROLL_ART)), type=DRAMA_TYPE))
	if LoggedIn() is True:
		dir.Append(Function(DirectoryItem(QueueMenu,"Browse Queue", thumb=R(QUEUE_ICON), ART=R(CRUNCHYROLL_ART))))
	dir.Append(PrefsItem(L('Preferences...'), thumb=R(PREFS_ICON), ART=R(CRUNCHYROLL_ART)))
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
		startTime = Datetime.Now()
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
		dtime = Datetime.Now()-startTime
		Log.Debug("AlphaListMenu %s (%s) execution time: %s"%(type, query, dtime))
		#listThumbs2()	
	else:
		dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2=sender.itemTitle)
		characters = ['All', '#', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
		for character in characters:
			dir.Append(Function(DirectoryItem(AlphaListMenu,"%s" % character, thumb=R(CRUNCHYROLL_ICON)), type=type, query=character))
	return dir


def PopularListMenu(sender,type=None):
	startTime = Datetime.Now()
	listRoot = BASE_URL + "/" + type.lower()
	dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="Popular")
	seriesList = scrapper.getSeriesListFromFeed("anime_popular")
	for series in seriesList:
		dir.Append(makeSeriesItem(series))
	dtime = Datetime.Now()-startTime
	Log.Debug("PopularListMenu %s execution time: %s"%(type, dtime))
	return dir


def GenreListMenu(sender,type=None,query=None):
	startTime = Datetime.Now()
	genreList = ANIME_GENRE_LIST if type==ANIME_LIST else DRAMA_GENRE_LIST
	if query is not None:
		dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2=query)
		queryStr = genreList[query].replace('_', '%20')
		feed = "anime_withtag/" + queryStr
		seriesList = scrapper.getSeriesListFromFeed(feed)
		for series in seriesList:
			dir.Append(makeSeriesItem(series))
		dtime = Datetime.Now()-startTime
		Log.Debug("GenreListMenu %s (%s) execution time: %s"%(type, query, dtime))
	else:
		dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2=sender.itemTitle)
		keyList = genreList.keys()
		keyList.sort()
		for genre in keyList:
			Log.Debug("genre: %s" % genre)
			dir.Append(Function(DirectoryItem(GenreListMenu,"%s" % genre, thumb=R(CRUNCHYROLL_ICON)), type=type, query=genre))
	return dir


def makeSeriesItem(series):
	#a = selectArt(url=series['art'],tvdbId=series['tvdbId'])
	#Log.Debug("art url for %s: %s"%(series['title'],a))#,series['art']))
	art = series['art']
	if art is None: art = ""
	url = scrapper.seriesTitleToUrl(series['title'])
	artFetcher = Function(getArt,url=art)

	seriesItem =  Function(
		DirectoryItem(
			SeriesMenu, 
			title = series['title'],
			summary=series['description'].encode("utf-8"),
			thumb=Function(getThumb,url=series['thumb'],tvdbId=series['tvdbId']),
			art = Function(getArt,url=art,tvdbId=series['tvdbId'])
		), seriesId=series['seriesId'])
	return seriesItem
		
def SeriesMenu(sender,seriesId=None):
	startTime = Datetime.Now()
	dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="Series")
	
	if LoggedIn():
		dir.Append(
			Function(PopupDirectoryItem(
					QueueChangePopupMenu, 
					title="Queue...", 
					summary="Add or remove this series from your queue."
				), 
				seriesId=seriesId )
			)

	episodes = scrapper.getEpisodeListForSeries(seriesId)
	if episodes['useSeasons'] is True:
		seasonNums = episodes['seasons'].keys()
		Log.Debug("season nums: %s" % seasonNums)
		season = {}
		season['url'] = scrapper.seriesTitleToUrl(Dict['series'][str(seriesId)]['title'])
		season['description'] = ""
		season['seriesId'] = seriesId
		#season['episodes'] = episodes['seasons'][seasonNum]
		season['title'] = "All Seasons"
		season['seasonnum'] = "all"
		#season['thumb'] = 
		dir.Append(makeSeasonItem(season))
		for seasonNum in seasonNums:
			seasonName = "Season %s" % seasonNum
			#season['episodes'] = episodes['seasons'][seasonNum]
			season['title'] = seasonName
			season['seasonnum'] = seasonNum
			#season['thumb'] = 
			dir.Append(makeSeasonItem(season))
	else:
		for episode in episodes['episodeList']:
			dir.Append(makeEpisodeItem(episode))
	dtime = Datetime.Now()-startTime
	Log.Debug("SeriesMenu (%s) execution time: %s"%(seriesId, dtime))
	return dir

import fanartScrapper

def makeSeasonItem(season):
	art = R(CRUNCHYROLL_ART)
	if Dict['series'][str(season['seriesId'])]['tvdbId'] is not None:
		artUrl = fanartScrapper.getSeasonThumb(Dict['series'][str(season['seriesId'])]['tvdbId'], season['seasonnum'])
		Log.Debug("arturl: %s"%artUrl)
		if artUrl is not None:
			art = Function(getArt,url=artUrl)
	seasonItem = Function(

		DirectoryItem(
			SeasonMenu,
			season['title'],
			summary=season['description'].encode("utf-8"),
			#thumb=Function(getThumb,url=season['thumb']),
			art=art
		),
		seriesId=season['seriesId'],
		season=season['seasonnum']
	)
	return seasonItem


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


def makeQueueItem(queueInfo):
	Log.Debug("queueinfo: %s" % queueInfo)
	s = Dict['series']
	sId = str(queueInfo['seriesId'])
	thumb = (s[sId]['thumb'] if (sId in s and s[sId]['thumb'] is not None) else R(CRUNCHYROLL_ICON))
	art = (s[sId]['art'] if (sId in s and s[sId]['art'] is not None) else R(CRUNCHYROLL_ART))
	queueItem = Function(PopupDirectoryItem(
		QueuePopupMenu,
		title=queueInfo['title'],
		summary=s[sId]['description'],
		thumb=Function(getThumb,url=thumb),
		art=Function(getArt,url=art)
		), queueInfo=queueInfo)
	return queueItem


def QueuePopupMenu(sender, queueInfo):
	dir = MediaContainer(title1="Play Options",title2=sender.itemTitle,disabledViewModes=["Coverflow"])#, noCache=True)
	ViewQueueItem = Function(DirectoryItem(QueueItemMenu, "View"), queueItemInfo=queueInfo)
	RemoveSeries = Function(DirectoryItem(removeFromQueue, title="Remove from queue"), seriesId=queueInfo['seriesId'])
	dir.Append(ViewQueueItem)
	dir.Append(RemoveSeries)
	return dir


def QueueItemMenu(sender,queueItemInfo):
	dir = MediaContainer(title1="Play Options",title2=sender.itemTitle,disabledViewModes=["Coverflow"], noCache=True)
	seriesurl = scrapper.seriesTitleToUrl(queueItemInfo['title'])
	s = Dict['series']
	sId = str(queueItemInfo['seriesId'])
	thumb = (s[sId]['thumb'] if (sId in s and s[sId]['thumb'] is not None) else R(CRUNCHYROLL_ICON))
	art = (s[sId]['art'] if (sId in s and s[sId]['art'] is not None) else R(CRUNCHYROLL_ART))
	if queueItemInfo['epToPlay'] is not None:
		nextEp = scrapper.getEpInfoFromLink(queueItemInfo['epToPlay'])
		PlayNext_old = Function(
			PopupDirectoryItem(
				playVideoMenu,
				title="Play Next Episode",
				subtitle=nextEp['title'],
				summary=makeEpisodeSummary(nextEp),
				thumb=Function(getThumb,url=nextEp['thumb']),
				art=Function(getArt,url=art)
			),
			episode=nextEp
		)
		PlayNext = makeEpisodeItem(nextEp)
		dir.Append(PlayNext)
	ViewSeries = Function(DirectoryItem(SeriesMenu, "View Series", thumb=thumb, art=Function(getArt,url=art)), seriesId=queueItemInfo['seriesId'])
	dir.Append(ViewSeries)
	dir.noCache = 1
	return dir


def getEpisodeArt(episode):
	seriesId = None
	for sk in Dict['series'].keys():
		if Dict['series'][str(sk)]['title']==episode['seriesTitle']:
			seriesId = int(sk)
	if seriesId is not None:
		artUrl = ""
		if Dict['series'][str(seriesId)]['tvdbId'] is not None:
			artUrl = fanartScrapper.getSeasonThumb(Dict['series'][str(seriesId)]['tvdbId'], episode['season'], rand=False)
			#Log.Debug("arturl: %s"%artUrl)
			if artUrl is not None:
				art = Function(getArt,url=artUrl)
		if artUrl == "" or artUrl is None:
			artUrl = Dict['series'][str(seriesId)]['art']
		if artUrl == "" or artUrl is None:
			artUrl = R(CRUNCHYROLL_ART)
	else:
		artUrl = R(CRUNCHYROLL_ART)
	Log.Debug("artUrl: %s"%artUrl)
	return artUrl


def makeEpisodeItem(episode):
	"""
	Create a directory item that will play the video.
	If the user is logged in and has requested to choose resolution,
	this will lead to a popup menu. In all other cases, the user
	need not make a choice, so go straight to the video (with a little
	URL munging beforehand in PlayVideo())
	"""
	giveChoice = True
	if Prefs['quality'] != "Ask":
		giveChoice = False
	elif not Prefs['password'] or not Prefs['username']:
		giveChoice = False
	elif not LoggedIn():
		giveChoice = False

	episodeItem = []
	summary = makeEpisodeSummary(episode)
	if giveChoice:
		episodeItem = Function(
			PopupDirectoryItem(
				playVideoMenu,
				title = episode['title'],
				subtitle = "Season %s"%episode['season'],
				summary = summary,
				thumb = Function(getThumb,url=episode['thumb']),
				art=Function(getArt,url=getEpisodeArt(episode))
			),
			episode=episode
		)
	else:
		episodeItem = Function(
			WebVideoItem(PlayVideo, 
				title = episode['title'],
				subtitle = "Season %s"%episode['season'],
				summary = summary,
				thumb = Function(getThumb,url=episode['thumb']),
				art=Function(getArt,url=getEpisodeArt(episode))
			), 
				# sadly, duration requires extra fetch, so it's not good to 
				# do per episode
				url=episode['link'], title=episode['title'], duration=0, summary=summary,
				mediaId = episode['mediaId'],
				modifyUrl=True
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
		summary = "%s\n%s" % (summary, episode['description'])
	else:
		summary = episode['description']
	#Log.Debug(summary)
	return summary


def removeFromQueue(sender,seriesId):
	response = makeAPIRequest2("req=RpcApiUserQueue_Delete&group_id=%s"%seriesId)
	Log.Debug("remove response: %s"%response)
	return MessageContainer("Success",'Removed from Queue')

def addToQueue(sender,seriesId,url=None):
	#FIXME url not needed?
	Log.Debug("add mediaid: %s"%seriesId)
	response = makeAPIRequest2("req=RpcApiUserQueue_Add&group_id=%s"%seriesId)
	Log.Debug("add response: %s"%response)
	return MessageContainer("Success",'Added to Queue')

def QueueChangePopupMenu(sender, seriesId):
	"""
	Popup a Menu asking user if she wants to
	add or remove this series from her queue
	"""
	dir = MediaContainer(title1="Queue",title2=sender.itemTitle,disabledViewModes=["Coverflow"])
	if LoggedIn():
		queueList = scrapper.getQueueList()
		inQ = False
		for item in queueList:
			if item['seriesId'] == seriesId:
				inQ = True
			break
		
		if inQ:
			dir.Append(
				Function(DirectoryItem(removeFromQueue, title="Remove From Queue", summary="Remove this series from your queue"), seriesId=seriesId)
			)
		else:
			dir.Append(
				Function(DirectoryItem(addToQueue, title="Add To Queue", summary="Add this series to your queue" ), seriesId=seriesId)
			)
	return dir
	

def SeriesPopupMenu(sender, url, seriesId):
	#FIXME: Now unused
	dir = MediaContainer(title1="Play Options",title2=sender.itemTitle,disabledViewModes=["Coverflow"])
	ViewSeries = Function(DirectoryItem(SeriesMenu, "View Episodes"), seriesId=seriesId)
	AddSeries = Function(DirectoryItem(addToQueue, title="Add To queue"), seriesId=seriesId, url=url.replace(".rss",""))
	dir.Append(ViewSeries)
	dir.Append(AddSeries)
	#dir.Append(Function(DirectoryItem(DirMenu, "Save Local Link"), folderPath=os.path.join(os.path.expanduser("~"),"TV"), seriesId=seriesId, replace=False))
	return dir


def getVideoUrl(videoInfo, resolution):
	"""
	construct a URL to display at resolution based on videoInfo
	without checking for coherence to what the site's got
	or if the resolution is valid
	"""

	url = videoInfo['baseUrl']+"?p" + str(resolution) + "=1"
	url = url + ("&t=0" if Prefs['restart'] == 'Restart' else "")
	url = url + "&small="+("1" if videoInfo['small'] is True else "0")
	url = url + "&wide="+("1" if videoInfo['wide'] is True or JUST_USE_WIDE is True else "0")
	return url


def playVideoMenu(sender, episode):
	startTime = Datetime.Now()
	dir = MediaContainer(title1="Play Options",title2=sender.itemTitle,disabledViewModes=["Coverflow"])
	if len(episode['availableResolutions']) == 0:
		episode['availableResolutions'] = scrapper.getAvailResFromPage(episode['link'])
		
		# FIXME I guess it's better to have something than nothing? It was giving Key error
		# on episode number
		if str(episode['mediaId']) not in Dict['episodes']:
			Dict['episodes'][str(episode['mediaId'])] = episode
	
		Dict['episodes'][str(episode['mediaId'])]['availableResolutions'] = episode['availableResolutions']
	videoInfo = scrapper.getVideoInfo(episode['link'], episode['mediaId'], episode['availableResolutions'])
	videoInfo['small'] = not (GlobalWasLoggedIn is True and isPremium(episode['type']) is True)

	if Prefs['quality'] == "Ask":
		for q in episode['availableResolutions']:
			videoUrl = getVideoUrl(videoInfo, q)
			episodeItem = Function(WebVideoItem(PlayVideo, title=Resolution2Quality[q]), url=videoUrl, title=episode['title'], duration=videoInfo['duration'], summary=episode['description'])
			dir.Append(episodeItem)
	else:
		prefRes = scrapper.getPrefRes(episode['availableResolutions'])
		videoUrl = getVideoUrl(videoInfo, prefRes)
		buttonText = "Play at %sp" % str(prefRes)
		episodeItem = Function(WebVideoItem(PlayVideo, title=buttonText), url=videoUrl, title=episode['title'], duration=videoInfo['duration'], summary=episode['description'])
		dir.Append(episodeItem)
	dtime = Datetime.Now()-startTime
	Log.Debug("playVideoMenu (%s) execution time: %s"%(episode['title'], dtime))
	return dir


def PlayVideo(sender, url, title, duration, summary = None, mediaId=None, modifyUrl=False, premium=False):
	theUrl = url
	resolutions = scrapper.getAvailResFromPage(url)
	vidInfo = scrapper.getVideoInfo(url, mediaId, resolutions)
	duration = vidInfo['duration'] # need this because duration isn't known until now
	
	if modifyUrl:
		vidInfo['small'] = False # let's just blow all the checks, man. If res isn't shown on the page, it can't be played		
		bestRes = scrapper.getPrefRes(resolutions)
		theUrl = getVideoUrl(vidInfo, bestRes)
	
	return Redirect(WebVideoItem(theUrl, title = title, duration = duration, summary = summary))


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

	
