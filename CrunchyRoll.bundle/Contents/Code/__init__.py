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
PREFS_ICON                   = CRUNCHYROLL_ICON#'icon-prefs.png'

FEED_BASE_URL                = "http://www.crunchyroll.com/boxee_feeds/"

THUMB_QUALITY                = {"Low":"_medium","Medium":"_large","High":"_full"}
VIDEO_QUALITY                = {"SD":"360","480P":"480","720P":"720"}

GlobalCrunchyrollSession  = None

LAST_PLAYER_VERSION = "20111130163346.fb103f9787f179cd0f27be64da5c23f2"

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

DOUBLE_CHECK_AVAIL_RES = True

def LoginAtStart():
	global GlobalWasLoggedIn
	if LoginNotBlank():
		data = {'formname':'RpcApiUser_Login','fail_url':'http://www.crunchyroll.com/login','name':Prefs['username'],'password':Prefs['password']}
		req = HTTP.Request(url='https://www.crunchyroll.com/?a=formhandler', values=data, immediate=True, cacheTime=10, headers={'Referer':'https://www.crunchyroll.com'})
		req = HTTP.Request(url="https://www.crunchyroll.com/acct",cacheTime=10,immediate=True)
		if "Profile Information" in req.content:
			GlobalWasLoggedIn = True
		else:
			GlobalWasLoggedIn = False
		#Log.Debug("is loggedin? %s" % GlobalWasLoggedIn)
		return GlobalWasLoggedIn


def LoggedIn():
	global GlobalWasLoggedIn
	global lastLoginCheckTime
	if USE_LOGIN_AT_START:
		return GlobalWasLoggedIn
	else:
		if LoginNotBlank():
			if lastLoginCheckTime is not None and (time.time() - lastLoginCheckTime) > 60*60*6:
				LoggedIn2()
				lastLoginCheckTime = time.time()
		else:
			GlobalWasLoggedIn = False
		return GlobalWasLoggedIn


def LoggedIn2():
	global GlobalWasLoggedIn
	req = HTTP.Request(url="https://www.crunchyroll.com/acct",cacheTime=10,immediate=True)
	if "Profile Information" in req.content:
		GlobalWasLoggedIn = True
	else:
		GlobalWasLoggedIn = False
		lastLoginCheckTime = time.time()
	return GlobalWasLoggedIn


def Login():
	if Prefs['username'] != '' and Prefs['password'] != '':
		data = {'formname':'RpcApiUser_Login','fail_url':'http://www.crunchyroll.com/login','name':Prefs['username'],'password':Prefs['password']}
		req = HTTP.Request(url='https://www.crunchyroll.com/?a=formhandler', values=data, immediate=True, cacheTime=10, headers={'Referer':'https://www.crunchyroll.com'})

def Logout():
	req = HTTP.Request(url='https://www.crunchyroll.com/logout', immediate=True, cacheTime=10, headers={'Referer':'https://www.crunchyroll.com'})
	GlobalWasLoggedIn = False


def LoginNotBlank():
	r = False
	if Prefs['username'] is not None and Prefs['password'] is not None:
		r = True
	return r


import scrapper

lastLoginCheckTime = time.time()

HTTP.CacheTime = 3600
HTTP.Headers["User-agent"] = "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_6; en-gb) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16"
HTTP.ClearCookies()

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


def CreatePrefs():
	Prefs.Add(id='loginemail', type='text', default="", label='Login Email')
	Prefs.Add(id='password', type='text', default="", label='Password', option='hidden')
	Prefs.Add(id='quality', type='enum', values=["SD", "480P", "720P", "Highest Avalible"], default="Highest Avalible", label="Quality")
	Prefs.Add(id='thumb_quality', type='enum', values=["Low", "Medium", "High"], default="High", label="Thumbnail Quality")
	Prefs.Add(id='restart', type='enum', values=["Resume", "Restart"], default="Restart", label="Resume or Restart")



def getVideoQuality():
	if LoginNotBlank():
		q = THUMB_QUALITY[Prefs['thumb_quality']]
	else:
		q = THUMB_QUALITY['SD']
	return q


def ValidatePrefs():
	#Log.Debug("start_point: %s" % Prefs['restart'])
	u = Prefs['username']
	p = Prefs['password']
	#Log.Debug("username: '%s'" % u)
	#Log.Debug("password: '%s'" % p)
	if GlobalWasLoggedIn:
		Logout()
	lf = LoginNotBlank()
	if lf:
		lv = LoginAtStart()
		if lv:
			mc = MessageContainer(
				"Success",
				"Details have been saved."
			)
		else:
			mc = MessageContainer(
				"Error",
				"Could not login with the provided username and password."
			)
	else:
		if u is not None or p is not None:
			if u is not None and p is None:
				mc = MessageContainer(
					"Error",
					"Username provided but no password."
				)
			elif p is not None and u is None:
				mc = MessageContainer(
					"Error",
					"Password provided but no username."
				)
		else:
			mc = MessageContainer(
				"Success",
				"Details have been saved."
			)
	return mc


def TopMenu():
	returnPlayer()
	dir = MediaContainer(disabledViewModes=["Coverflow"], title1="Crunchyroll")
	dir.Append(Function(DirectoryItem(Menu,"Browse Anime", thumb=R(ANIME_ICON)), type="Anime"))
	dir.Append(Function(DirectoryItem(Menu,"Browse Drama", thumb=R(DRAMA_ICON)), type="Drama"))
	dir.Append(Function(DirectoryItem(QueueMenu,"Browse Queue", thumb=R(QUEUE_ICON))))
	dir.Append(PrefsItem(L('Preferences'), thumb=R(PREFS_ICON)))
	#dir.nocache = 1
	
	return dir



def returnPlayer():
	url='http://www.crunchyroll.com/naruto/episode-193-the-man-who-died-twice-567104'
	REGEX_PLAYER_REV = re.compile("(?<=swfobject\.embedSWF\(\").*(?:StandardVideoPlayer.swf)")
	response = HTTP.Request(url=url)
	match = REGEX_PLAYER_REV.search(str(response.content))
	if match:
		Log.Debug("CRUNCHYROLL: --> Found Match")
		playerTemp = str(match.group(0))
		player = playerTemp.split('\/')[4]
		if player==LAST_PLAYER_VERSION:
			Log.Debug("CRUNCHYROLL: --> Same Player Revision")
		else:
			Log.Debug("CRUNCHYROLL: --> Found new Player Revision")
			Log.Debug(player)
	else:
		Log.Debug("CRUNCHYROLL: --> NO MATCHES FOUND for new Player Revision")
		player = LAST_PLAYER_VERSION
	return player


def Menu(sender,type=None):
	if type=="Anime":
		all_icon = ANIME_ICON
	elif type=="Drama":
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
		if type=="Anime":
			seriesList = scrapper.getSeriesListFromFeed("genre_anime_all")
		else:
			seriesList = scrapper.getSeriesListFromFeed("drama")
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
	if type=="Anime":
		genreList = ANIME_GENRE_LIST
	else:
		genreList = DRAMA_GENRE_LIST
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



def ShowMenu(sender,url=None):
	dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="Series")
	
	if LoginNotBlank():
		loggedin = LoggedIn()
		if not loggedin:
			Login()
	
	episodes = scrapper.getEpisodeListFromFeed(url)
	if episodes['useSeasons'] is True:
		seasonNums = episodes['seasons'].keys()
		Log.Debug("season nums: %s" % seasonNums)
		for seasonNum in seasonNums:
			seasonName = "Season %s" % seasonNum
			season = {}
			#season['episodes'] = episodes['seasons'][seasonNum]
			season['url'] = url
			season['title'] = seasonName
			season['description'] = ""
			season['seasonnum'] = seasonNum
			#season['thumb'] = 
			dir.Append(makeSeasonItem(season))
	else:
		for episode in episodes['episodeList']:
			dir.Append(makeEpisodeItem(episode))
	#Log.Debug("testing: %s" % dir.parentIndex)
	return dir


def SeasonMenu(sender,url=None,season=None):
	dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="Series")
	
	if LoginNotBlank():
		loggedin = LoggedIn()
		if not loggedin:
			Login()
	epList = scrapper.getSeasonEpisodeListFromFeed(url, season)
	for episode in epList:
		dir.Append(makeEpisodeItem(episode))
	return dir


def QueueMenu(sender):
	dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="Series")
	
	if LoginNotBlank():
		loggedin = LoggedIn()
		if not loggedin:
			Login()
	queueList = scrapper.getQueueList()
	for queue in queueList:
		dir.Append(makeQueueItem(queue))
	return dir



def makeSeriesItem(series):
	if USING_BOXEE_FEEDS is True:
		url = "showseries/%s" % series['mediaId']
	else:
		seriesname = series['title']
		toremove = ["!", ":", "'", "?", ".", ",", "(", ")", "&", "@", "#", "$", "%", "^", "*", ";", "~", "`"]
		for char in toremove:
			seriesname = seriesname.replace(char, "")
		seriesname = seriesname.replace("  ", " ").replace(" ", "-").lower()
		while "--" in seriesname:
			seriesname = seriesname.replace("--","-")
		if seriesname.endswith("-"):
			seriesname = seriesname.rstrip("-")
		url = "%s/%s.rss" % (BASE_URL, seriesname)
		Log.Debug("makeSeriesItem url: %s" % url)
	seriesItem = Function(
		DirectoryItem(
			ShowMenu,
			series['title'],
			summary=series['description'],
			thumb=series['thumb'],
			art=series['thumb'],
		),
		url=url
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
		url=season['url'],
		season=season['seasonnum']
	)
	return seasonItem


def makeEpisodeItem(episode):
	if LoginNotBlank():
		loggedin = LoggedIn()
		if not loggedin:
			Login()
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


def makeQueueItem(queueInfo):
	#"title": title,
	#"mediaId": mediaId,
	#"epToPlay": epToPlay,
	#"seriesStatus": seriesStatus
	Log.Debug("queueinfo: %s" % queueInfo)
	queueItem = Function(
		DirectoryItem(
			QueueItemMenu,
			title=queueInfo['title']
		),
		queueInfo=queueInfo
	)
	return queueItem

def removeFromQueue(sender,mediaId):
	dir = MediaContainer(title1="Play Options",title2=sender.itemTitle,disabledViewModes=["Coverflow"], noCache=True,replaceParent=sender.parent)
	req = HTTP.Request(BASE_URL+"/ajax/",values={'req':"RpcApiUserQueue_Delete",'qroup_id':group_id},cacheTime=0,immediate=True)
	return dir


def QueueItemMenu(sender, queueInfo):
	dir = MediaContainer(title1="Play Options",title2=sender.itemTitle,disabledViewModes=["Coverflow"], noCache=True)
	if USING_BOXEE_FEEDS is True:
		seriesurl = "showseries/%s" % queueInfo['mediaId']
	else:
		seriesname = queueInfo['title']
		toremove = ["!", ":", "'", "?", ".", ",", "(", ")", "&", "@", "#", "$", "%", "^", "*", ";", "~", "`"]
		for char in toremove:
			seriesname = seriesname.replace(char, "")
		seriesname = seriesname.replace("  ", " ").replace(" ", "-").lower()
		while "--" in seriesname:
			seriesname = seriesname.replace("--","-")
		if seriesname.endswith("-"):
			seriesname = seriesname.rstrip("-")
		seriesurl = "%s/%s.rss" % (BASE_URL, seriesname)
	nextEp = scrapper.getEpInfoFromLink(queueInfo['epToPlay'])
	PlayNext = Function(
		PopupDirectoryItem(
			playVideoMenu,
			title="Play Next",
			subtitle=nextEp['title'],
			summary=nextEp['description'],
			thumb=nextEp['thumb']
		),
		episode=nextEp
	)
	ViewSeries = Function(
		DirectoryItem(
			ShowMenu,
			"View Series"
		),
		url=seriesurl
	)
	RemoveSeries = Function(
		PopupDirectoryItem(
			removeFromQueue,
			title="Remove from queue"
		),
		mediaId=queueInfo['mediaId']
	)
	dir.Append(PlayNext)
	dir.Append(ViewSeries)
	dir.Append(RemoveSeries)
	return dir




def getVideoUrl(videoInfo, quality):
	resNames = {'12':'SD', '20':'480P', '21':'720P'}
	url = videoInfo['baseUrl']+"?p"+VIDEO_QUALITY[resNames[quality]]+"=1"
	if videoInfo['small'] is True:
		url = url+"&small=1"
	if videoInfo['wide'] is True or JUST_USE_WIDE is True:
		url = url+"&wide=1"
	return url


def playVideoMenu(sender, episode):
	resNames = {"12":'SD', "20":'480P', "21":'720P'}
	dir = MediaContainer(title1="Play Options",title2=sender.itemTitle,disabledViewModes=["Coverflow"])
	availRes = episode['availableResolutions']
	if DOUBLE_CHECK_AVAIL_RES:
		availRes = scrapper.getAvailResFromPage(episode['link'], availRes)
	videoInfo = scrapper.getVideoInfo(episode['link'], episode['mediaId'], availRes)
	vi = {}
	vi['title'] = episode['title']
	vi['duration'] = videoInfo['duration']
	if Prefs['quality'] is "Ask":
		for q in availRes:
			videoUrl = getVideoUrl(videoInfo, q)
			vi['url'] = videoUrl
			episodeItem = Function(
				WebVideoItem(
					PlayVideo,
					title=resNames[q]
				),
				videoInfo=vi
			)
			dir.Append(episodeItem)
	else:
		prefRes = scrapper.getPrefRes(availRes)
		videoUrl = getVideoUrl(videoInfo, prefRes)
		vi['url'] = videoUrl
		episodeItem = Function(
			WebVideoItem(
				PlayVideo,
				title="Play"
			),
			videoInfo=vi
		)
		dir.Append(episodeItem)
		
	return dir


def PlayVideo(sender, videoInfo):
	return Redirect(
		WebVideoItem(
			videoInfo['url'],
    		title = videoInfo['title'],
			duration = videoInfo['duration']
    	)
	)


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

	
