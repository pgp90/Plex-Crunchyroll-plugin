from constants import *
import api
import re

HTTP.CacheTime = 3600
HTTP.Headers["User-agent"] = "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_6; en-gb) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16"
HTTP.Headers["Accept-Encoding"] = "gzip, deflate"

import scrapper
	
def makeSeriesItem(series):
	#a = scrapper.selectArt(url=series['art'],tvdbId=series['tvdbId'])
	#Log.Debug("art url for %s: %s"%(series['title'],a))#,series['art']))
	art = series['art']
	if art is None: art = ""

	try:
		summaryString = series['description'].encode("utf-8")
	except AttributeError:
		summaryString = ""
		
	seriesItem =  Function(
		DirectoryItem(
			SeriesMenu, 
			title = series['title'],
			summary=summaryString,
			thumb=scrapper.getThumbUrl(series['thumb'], tvdbId=series['tvdbId']), #Function(getThumb,url=series['thumb'],tvdbId=series['tvdbId']),
			art = Function(GetArt,url=art,tvdbId=series['tvdbId'])
		), seriesId=series['seriesId'], seriesTitle=series['title'])
	return seriesItem

def makeSeasonItem(season):
	"""
	Create a directory item showing a particular season in a series.
	Seasons contain episodes, so this passes responsibility on to
	SeasonMenu() to construct that list.
	"""
	art = R(CRUNCHYROLL_ART)
	if Dict['series'][str(season['seriesId'])]['tvdbId'] is not None:
		artUrl = scrapper.getSeasonThumb(Dict['series'][str(season['seriesId'])]['tvdbId'], season['seasonnum'])
		Log.Debug("arturl: %s"%artUrl)
		if artUrl is not None:
			art = Function(GetArt,url=artUrl)
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
		#Log.Debug("Quality is not Ask")
		giveChoice = False
	elif not Prefs['password'] or not Prefs['username']:
		Log.Debug("User wants to choose res, but password is missing")
		giveChoice = False
	elif not api.isPremium():
		Log.Debug("User wants to choose res, but not a premium member")
		giveChoice = False

#	if giveChoice:
#		Log.Debug("###############Giving Choice to user")
#	else:
#		Log.Debug("##################Not giving choice to user")
	episodeItem = []
	summary = makeEpisodeSummary(episode)
	
	# check the rating
	if episode['rating'] and episode['rating'] > 4: # adult supervision from 5 up
		if Prefs['hideMature'] is True:
			episodeItem = Function(DirectoryItem(
				AdultWarning,
				title = episode['title'],
				subtitle = "Season %s"%episode['season'],
				summary = createRatingString(episode['rating']) + summary,
				thumb = Function(GetThumb,url=episode['thumb']),
				art=Function(GetArt,url=scrapper.getEpisodeArt(episode))
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
				thumb = Function(GetThumb,url=episode['thumb']),
				art=Function(GetArt,url=scrapper.getEpisodeArt(episode))
			),
			episode=episode
		)
	else:
		episodeItem = Function(
			WebVideoItem(PlayVideo, 
				title = episode['title'],
				subtitle = "Season %s"%episode['season'],
				summary = createRatingString(episode['rating']) + summary,
				thumb = Function(GetThumb,url=episode['thumb']),
				art=Function(GetArt,url=scrapper.getEpisodeArt(episode))
			), 
				# sadly, duration requires extra fetch, so it's not good to 
				# do per episode
				url=episode['link'], title=episode['title'], duration=0, summary=createRatingString(episode['rating']) + " " + summary,
				mediaId = episode['mediaId'],
				modifyUrl=True
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
	if episode['keywords'] != '':
		summary = "%sKeywords: %s\n" % (summary, episode['keywords'])
	if summary != '':
		summary = "%s\n%s" % (summary, episode['description'])

	#Log.Debug(summary)
	return summary
	
def Start():
	"""
	Let's roll.
	"""
	Plugin.AddPrefixHandler(CRUNCHYROLL_PLUGIN_PREFIX, TopMenu, "CrunchyRoll", CRUNCHYROLL_ICON, CRUNCHYROLL_ART)
	Plugin.AddViewGroup("List", viewMode = "List", mediaType = "Reverse Engineer the kinds of values allowed here someday")
	MediaContainer.art = R(CRUNCHYROLL_ART)
	MediaContainer.title1 = "CrunchyRoll"
	MediaContainer.viewGroup = "List"
	DirectoryItem.thumb = R(CRUNCHYROLL_ICON)
	
	if Dict['Authentication'] is None:
		api.resetAuthInfo()
		
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
		scrapper.cacheAllSeries()
		listAllEpTitles()

	if False: # doesn't work because cache won't accept a timeout value
		for cacheThis in PRECACHE_URLS:
			HTTP.PreCache(cacheThis, cacheTime=60*60*10)

def CreatePrefs():
	Prefs.Add(id='loginemail', type='text', default="", label='Login Email')
	Prefs.Add(id='password', type='text', default="", label='Password', option='hidden')
	Prefs.Add(id='quality', type='enum', values=["SD", "480P", "720P", "1080P", "Highest Available"], default="Highest Available", label="Quality")
	Prefs.Add(id='video_source', type='enum', values=["Web Player", "Boxee Stream", "Direct"], default="Boxee Stream", label="Video Source")
	Prefs.Add(id='thumb_quality', type='enum', values=["Low", "Medium", "High"], default="High", label="Thumbnail Quality")
	Prefs.Add(id='restart', type='enum', values=["Resume", "Restart"], default="Restart", label="Resume or Restart")
	Prefs.Add(id='hideMature', type='bool', default="true", label="Hide mature content?")
	Prefs.Add(id='fanart', type='bool', default="false", label="Use Fanart.tv when possible?")


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
			api.logout()
		except: pass
		
		if Prefs['quality'] != "SD" and Prefs['quality'] != "Highest Available":
			mc = MessageContainer("Quality Warning", "Only premium members can watch in high definition. Your videos will show in standard definiton only.")
		else:
			mc = MessageContainer("Success",
				"Preferences Saved."
				)
		return mc

def TopMenu():
	api.login()

	if CHECK_PLAYER is True:
		scrapper.returnPlayer()
	Log.Debug("art: %s"%R(CRUNCHYROLL_ART))

	dir = MediaContainer(disabledViewModes=["Coverflow"], title1="Crunchyroll")
	if api.isPremium():
		dir.Append(Function(DirectoryItem(QueueMenu,"View Queue", thumb=R(QUEUE_ICON), ART=R(CRUNCHYROLL_ART))))

	dir.Append(Function(DirectoryItem(RecentAdditionsMenu,"Recent Additions", title1="RecentAdditions", thumb=R(CRUNCHYROLL_ICON), art=R(CRUNCHYROLL_ART))))	
	dir.Append(Function(DirectoryItem(BrowseMenu,"Browse Anime", title1="Browse Anime", thumb=R(ANIME_ICON), art=R(CRUNCHYROLL_ART)), type=ANIME_TYPE))
	dir.Append(Function(DirectoryItem(BrowseMenu,"Browse Drama", title1="Browse Drama", thumb=R(DRAMA_ICON), art=R(CRUNCHYROLL_ART)), type=DRAMA_TYPE))
	dir.Append(Function(InputDirectoryItem(SearchMenu, "Search...", thumb=R(SEARCH_ICON), prompt=L("Search for videos..."), ART=R(CRUNCHYROLL_ART))))

	dir.Append(PrefsItem(L('Preferences...'), thumb=R(PREFS_ICON), ART=R(CRUNCHYROLL_ART)))
	if ENABLE_DEBUG_MENUS:
		dir.Append(Function(DirectoryItem(DebugMenu, "Debug...", thumb=R(DEBUG_ICON))) )
	if ENABLE_DEBUG_MENUS:
		# dir.noCache = 0 # ad hoc
		pass
	
	return dir

def QueueMenu(sender):
	"""
	Show series titles that the user has in her queue
	"""
	dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="Series", noCache=True)
	queueList = scrapper.getQueueList()
	for queue in queueList:
		dir.Append(makeQueueItem(queue))
	dir.noCache = 1
	return dir


def makeQueueItem(queueInfo):
	"""
	construct a directory item for a series existing in user's queue.
	Selecting this item leads to more details about the series, and the ability
	to remove it from the queue.
	"""
	Log.Debug("queueinfo: %s" % queueInfo)
	s = Dict['series']
	sId = str(queueInfo['seriesId'])
	thumb = (s[sId]['thumb'] if (sId in s and s[sId]['thumb'] is not None) else R(CRUNCHYROLL_ICON))
	art = (s[sId]['art'] if (sId in s and s[sId]['art'] is not None) else R(CRUNCHYROLL_ART))
	queueItem = Function(DirectoryItem(
		QueueItemMenu,
		title=queueInfo['title'],
		summary=s[sId]['description'],
		thumb=Function(GetThumb,url=thumb),
		art=Function(GetArt,url=art)
		), queueInfo=queueInfo)
	return queueItem


def QueuePopupMenu(sender, queueInfo):
	#FIXME this is skipped for now, we go straight into QueueItemMenu
	dir = MediaContainer(title1="Play Options",title2=sender.itemTitle,disabledViewModes=["Coverflow"])#, noCache=True)
	ViewQueueItem = Function(DirectoryItem(QueueItemMenu, "View"), queueInfo=queueInfo)
	RemoveSeries = Function(DirectoryItem(RemoveFromQueue, title="Remove from queue"), seriesId=queueInfo['seriesId'])
	dir.Append(ViewQueueItem)
	dir.Append(RemoveSeries)
	dir.noCache=1
	return dir


def QueueItemMenu(sender,queueInfo):
	"""
	show episodes in a queued series that are ready to watch. Also,
	allow user to remove the series from queue or view the
	entire series if she wishes.
	"""
	dir = MediaContainer(title1="Play Options",title2=sender.itemTitle,disabledViewModes=["Coverflow"], noCache=True)
	seriesurl = scrapper.seriesTitleToUrl(queueInfo['title'])
	s = Dict['series']
	sId = str(queueInfo['seriesId'])
	thumb = (s[sId]['thumb'] if (sId in s and s[sId]['thumb'] is not None) else R(CRUNCHYROLL_ICON))
	art = (s[sId]['art'] if (sId in s and s[sId]['art'] is not None) else R(CRUNCHYROLL_ART))
	if queueInfo['epToPlay'] is not None:
		nextEp = scrapper.getEpInfoFromLink(queueInfo['epToPlay'])
		PlayNext = makeEpisodeItem(nextEp)
		dir.Append(PlayNext)
	RemoveSeries = Function(DirectoryItem(RemoveFromQueue, title="Remove series from queue"), seriesId=sId)
	ViewSeries = Function(DirectoryItem(SeriesMenu, "View Series", thumb=thumb, art=Function(GetArt,url=art)), seriesId=queueInfo['seriesId'])
	dir.Append(RemoveSeries)
	dir.Append(ViewSeries)
	dir.noCache = 1
	return dir

def RecentAdditionsMenu(sender):
	"""
	show recently added videos
	"""
	episodeList = scrapper.getRecentVideos()
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
	search boxee_feeds and return results in a media container
	"""
	episodeList = scrapper.getEpisodeListFromQuery(query)
	if episodeList:
		dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2=query)
		for episode in episodeList:
			#Log.Debug("#################################\n")
			#Log.Debug(episode)
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
	
	if type== ANIME_TYPE:
		dir.Append(Function(DirectoryItem(AlphaListMenu,"All", title1="All", thumb=R(all_icon)), type=type))

	else:
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
			seriesList = scrapper.getAnimeSeriesList()
		else:
			seriesList = scrapper.getDramaSeriesList()
			
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

def RecentListMenu(sender, type=None):
	startTime = Datetime.Now()
	dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="Recent")
	episodeList = []
	if type==ANIME_TYPE:
		episodeList = scrapper.getRecentAnimeEpisodes()
	elif type==DRAMA_TYPE:
		episodeList = scrapper.getRecentDramaEpisodes()
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
		seriesList = scrapper.getPopularAnimeSeries()
	elif type==DRAMA_TYPE:
		#FIXME: this returns an empty list.
		seriesList = scrapper.getPopularDramaSeries()
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
			seriesList = scrapper.getAnimeSeriesByGenre(genre)
		elif type == DRAMA_TYPE:
			seriesList = scrapper.getDramaSeriesByGenre(genre)
		else:
			seriesList = scrapper.getSeriesByGenre(genre)
			
		for series in seriesList:
			dir.Append(makeSeriesItem(series))
		dtime = Datetime.Now()-startTime
		Log.Debug("GenreListMenu %s (%s) execution time: %s"%(type, genre, dtime))
	else:
		dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2=sender.itemTitle)
		keyList = genreList.keys()
		keyList.sort()
		for genre in keyList:
			Log.Debug("genre: %s" % genre)
			dir.Append(Function(DirectoryItem(GenreListMenu,"%s" % genre, thumb=R(CRUNCHYROLL_ICON)), type=type, genre=genre))
	return dir
	
def SeriesMenu(sender,seriesId=None, seriesTitle="Series"):
	"""
	show the episodes available for seriesId. Use seriesTitle for
	the breadcrumb display.
	"""
	startTime = Datetime.Now()
	dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2=seriesTitle)
	
	if api.login() and api.isPremium():
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

def SeasonMenu(sender,seriesId=None,season=None):
	"""
	Display a menu showing episodes available in a particular season.
	"""
	dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="Series")
	epList = scrapper.getSeasonEpisodeListFromFeed(seriesId, season)
	for episode in epList:
		dir.Append(makeEpisodeItem(episode))
	return dir

	
def DebugMenu(sender):
	dir = MediaContainer(disabledViewModes=["Coverflow"], title1="Crunchyroll")
	dir.Append(Function(DirectoryItem(DumpInfo, "Dump info to console")) )
	dir.Append(Function(DirectoryItem(ClearAllData, "Clear all data", summary="This removes cached metadata, and plex's cookies and cache. Prefs will still exist.")) )
	dir.Append(Function(DirectoryItem(VideoTestMenu, "Test Videos...")) )
	dir.Append(Function(DirectoryItem(LogoutFromMenu, "Logout now")) )
	dir.Append(Function(DirectoryItem(LoginFromMenu, "Login now")) )
	dir.Append(Function(DirectoryItem(ClearCookiesItem, "Clear Cookies", summary="This will remove the cookies from Plex's internal cookie storage.")) )
	dir.Append(Function(DirectoryItem(KillSafariCookiesItem, "Kill Safari Cookies", summary="This will remove all crunchyroll.com cookies from Safari's cookie file. Useful if login status is not synced.")) )
	dir.Append(Function(DirectoryItem(TransferCookiesItem, "Transfer cookies to Safari", summary="This transfers Plex's crunchyroll cookies into safari's plist.")) )
	
	return dir

def DumpInfo(sender):

	debugDict()
	Log.Debug("###########CURRENT COOKIES")
	Log.Debug(HTTP.GetCookiesForURL(BASE_URL))
	return MessageContainer("Whew", "Thanks for dumping on me.")

def ClearAllData(sender):
	HTTP.ClearCookies()
	HTTP.ClearCache()
	Dict.Reset()
	Dict.Save()
	Log.Debug(Prefs)
#	Prefs = {}
#	CreatePrefs()
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
	api.logout()
	if not api.loggedIn():
		dir = MessageContainer("Logout", "You are now logged out")
	else:
		dir = MessageContainer("Logout Failure", "Nice try, but logout failed.")
		Log.Debug("####LOGOUT FAILED, HERE'S YOUR COOKIE")
		Log.Debug(HTTP.GetCookiesForURL(BASE_URL) )

	return dir

def LoginFromMenu(sender):
	if not Prefs['username'] or not Prefs['password']:
		dir = MessageContainer("Login Brain Fart", "You cannot login because your username or password are blank.")
	else:
		result = login(force = True)
		if not result:
			dir = MessageContainer("Auth failed", "Authentication failed at crunchyroll.com")
		elif api.isPremium():
			dir = MessageContainer("Login", "You are logged in, congrats.")
		else:
			dir = MessageContainer("Login Failure", "Sorry, bro, you didn't login!")
		
	return dir

def ClearCookiesItem(sender):
	HTTP.ClearCookies()
	return MessageContainer("Cookies Cleared", "For whatever it's worth, cookies are gone now.")

def KillSafariCookiesItem(sender):
	killSafariCookies()
	return MessageContainer("Cookies Cleared", "All cookies from crunchyroll.com have been removed from Safari")

def TransferCookiesItem(sender):
	if api.transferCookiesToSafari():
		return MessageContainer("Cookies Transferred.", "Done.")
	else:
		return MessageContainer("Transfer Failed.", "Nastiness occured, check the console.")
	
def ConstructTestVideo(episode)	:
	episodeItem = \
		WebVideoItem(url=episode['link'],
			title = episode['title'],
			subtitle = "Season %s"%episode['season'],
			summary = episode['summary'],
			#thumb = Function(GetThumb,url=episode['thumb']),
			#art=Function(GetArt,url=scrapper.getEpisodeArt(episode))
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
			 'summary': "480p Boxee feed. This needs a premium account. No ads should show! Plex client should show a resolution of 720x480, must not have any black edges on top or bottom. Play, pause, and seeking should work.",
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
			  'summary': '480p web page version. This needs a premium account. No ads should show! Plex client should show a resolution of 720x478, must not have black edges on top or bottom. Play, pause, and seek should work.',
			  'link': 'http://www.crunchyroll.com/blue-exorcist/-blue-exorcist-blue-exorcist-official-trailer-577928?p480=1&small=0&wide=0',
			  'mediaId': "577928"
			},
			{'title': 'Blue Exorcist Episode 1',
			  'season': 'None',
			  'summary': '360p web page version.  You really should log out to test this. You should get ads. Plex client should show resolution of ...',
			  'link': 'http://www.crunchyroll.com/blue-exorcist/episode-1-the-devil-resides-in-human-souls-573636?p360=1&small=0&wide=0',
			  'mediaId': "577928"
			},
			{'title': "Bleach 274 1080p",
			'season': 'None',
			'summary': "1080p direct stream. You need to log in and have your preference at CR.com set to view 1080p. No ads should show. Plex should report a resolution of 1920x1080. There MIGHT be small black bars at top and bottom due to ratio difference (but really shouldn't happen). Seek, play and pause should work.",
			'link': "http://www.crunchyroll.com/swf/vidplayer.swf?config_url=http%3A%2F%2Fwww.crunchyroll.com%2Fxml%2F%3Freq%3DRpcApiVideoPlayer_GetStandardConfig%26media_id%3D542596%26video_format%3D0%26video_quality%3D0%26auto_play%3D1%26click_through%3D1&__qual=1080",
			'mediaId': '542596'
			},
			{'title': "Puffy AmiYumi Interview",
			'season': 'None',
			'summary': "Freebie web content with standard URL. Currently nukes PMS alltogether with EXC_BAD_ACCESS.",
			'link':"http://www.crunchyroll.com/puffy-amiyumi/-puffy-amiyumi-puffy-amiyumi-interview-565187?p360=1&t=0&small=0&wide=0",
			'mediaId': '565187'
			}
			
			
			
		]
		

		for episode in testEpisodes:
			dir.Append(ConstructTestVideo(episode))
		#rtmpe://cp150757.edgefcs.net/ondemand/?auth=daEc0dAbLdwa7atdKbHbxaOcDaacdbUd_bC-bpl6F5-dHa-nDJxstJAGuD&amp;aifp=0009&amp;slist=c6/s/ve709961/video.mp4
		dir.Append(RTMPVideoItem(
			url="rtmpe://cp150757.edgefcs.net/ondemand/?auth=daEc0dAbLdwa7atdKbHbxaOcDaacdbUd_bC-bpl6F5-dHa-nDJxstJAGuD&amp;aifp=0009&amp;slist=c6/s/ve709961/video.mp4",
#			clip="mp4:c6/s/ve709961/video.mp4", 
			width=656,height=368, 
			auth="daEc0dAbLdwa7atdKbHbxaOcDaacdbUd_bC-bpl6F5-dHa-nDJxstJAGuD",
			aifp="0009",
			title="The Mighty Chilwu Episode 1",
			summary="This is an RTMPE stream. It shouldn't play, but if it does it should show ads and fit the borders." 
			)
		)
		
		vid = VideoClipObject(
						url="http://www.crunchyroll.com/another/episode-1-rough-sketch-589572",
						title="Another episode 1, services",
						summary = "This video will be fetched through services. It may just bug out. Who knows."
					)
		# this actually borks consistently. I actually don't understand the point of VideoClipObject.
		#dir.Append(VideoItem("http://www.crunchyroll.com/another/episode-1-rough-sketch-589572", title="Test services", summary="This is a test of url services. It should play."))

#import fanartScrapper

def AdultWarning(sender, rating=5):
	"""
	return a message container warning the user that she's about to 
	try something naughty, and if she wants to do this naughty thing,
	she must give herself permission to do it.
	"""
	return MessageContainer("Adult Content", "Cannot play mature content unless you change your preferences.")


def RemoveFromQueue(sender,seriesId):
	"""
	remove seriesID from queue
	"""
	api.login()
	result = api.removeFromQueue(seriesId)
	if result:
		return MessageContainer("Success",'Removed from Queue')
	else:
		return MessageContainer("Failure", 'Could not remove from Queue.')
	

def AddToQueue(sender,seriesId,url=None):
	"""
	Add seriesId to the queue.
	"""
	api.login()
	result = api.addToQueue(seriesId)
	
	if result:
		return MessageContainer("Success",'Added to Queue')
	else:
		return MessageContainer("Failure", 'Could not add to Queue.')

def QueueChangePopupMenu(sender, seriesId):
	"""
	Popup a Menu asking user if she wants to
	add or remove this series from her queue
	"""
	api.login()
	dir = MediaContainer(title1="Queue",title2=sender.itemTitle,disabledViewModes=["Coverflow"])
	if api.isPremium():
		queueList = scrapper.getQueueList()
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
	

def SeriesPopupMenu(sender, url, seriesId):
	#FIXME: Now unused
	dir = MediaContainer(title1="Play Options",title2=sender.itemTitle,disabledViewModes=["Coverflow"])
	ViewSeries = Function(DirectoryItem(SeriesMenu, "View Episodes"), seriesId=seriesId)
	AddSeries = Function(DirectoryItem(AddToQueue, title="Add To queue"), seriesId=seriesId, url=url.replace(".rss",""))
	dir.Append(ViewSeries)
	dir.Append(AddSeries)
	#dir.Append(Function(DirectoryItem(DirMenu, "Save Local Link"), folderPath=os.path.join(os.path.expanduser("~"),"TV"), seriesId=seriesId, replace=False))
	return dir


def GetThumb(url, tvdbId=None):
	"""
	find a better thumb and return result
	"""
	return scrapper.getThumb(url,tvdbId)

def GetArt(url,tvdbId=None):
	"""
	find a fanart url
	"""
	return scrapper.getArt(url, tvdbId)


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


def constructMediaObject(episode):
	"""
	Construct media objects from an episode.
	"""
	if True or len(episode['availableResolutions']) == 0:
		episode['availableResolutions'] = scrapper.getAvailResFromPage(episode['link'])
		Log.Debug("####available resolutions:")
		Log.Debug(episode['availableResolutions'])
		# FIXME I guess it's better to have something than nothing? It was giving Key error
		# on episode number
		if str(episode['mediaId']) not in Dict['episodes']:
			Dict['episodes'][str(episode['mediaId'])] = episode
	
		Dict['episodes'][str(episode['mediaId'])]['availableResolutions'] = episode['availableResolutions']
	
	videoInfo = scrapper.getVideoInfo(episode['link'], episode['mediaId'], episode['availableResolutions'])
	videoInfo['small'] = api.isPremium(episode['type']) is False
	
	epsObject = EpisodeObject(
		url = videoInfo['baseUrl'], #dunno if this will work
		title = episode['title'],
		summary = episode['description']
	)

	for q in episode['availableResolutions']:

		mo = MediaObject(
				# duration = episode['duration'], #grr stupid duration isn't available w/o extra fetch
				video_resolution = q,
				protocol = Protocol.WebKit,
				parts = [
					PartObject(				
						key = WebVideoURL(getVideoUrl(videoInfo, q))
					)
				]
			)
		epsObject.add(mo)
	dir = ObjectContainer( objects = [epsObject])
	return dir

def PlayVideoMenu2(sender, episode):
	"""
	use more code to accomplish less.
	"""
	return constructMediaObject(episode)
	
def PlayVideoMenu(sender, episode):
	"""
	construct and return a MediaContainer that will ask the user
	which resolution of video she'd like to play for episode
	"""
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
	videoInfo['small'] = api.isPremium(episode['type']) is False

	if Prefs['quality'] == "Ask":
		for q in episode['availableResolutions']:
			videoUrl = getVideoUrl(videoInfo, q)
			episodeItem = Function(WebVideoItem(PlayVideo, title=Resolution2Quality[q]), url=videoUrl, title=episode['title'], duration=videoInfo['duration'], summary=episode['description'])
			dir.Append(episodeItem)
	else:
		Log.Debug("##############QUALITY IS NOT ASK")
		prefRes = scrapper.getPrefRes(episode['availableResolutions'])
		videoUrl = getVideoUrl(videoInfo, prefRes)
		buttonText = "Play at %sp" % str(prefRes)
		episodeItem = Function(WebVideoItem(PlayVideo, title=buttonText), url=videoUrl, title=episode['title'], duration=videoInfo['duration'], summary=episode['description'])
		dir.Append(episodeItem)
	dtime = Datetime.Now()-startTime
	Log.Debug("PlayVideoMenu (%s) execution time: %s"%(episode['title'], dtime))
	return dir

def PlayVideo(sender, url, title, duration, summary = None, mediaId=None, modifyUrl=False, premium=False):
	if Prefs['video_source'] == "Direct" and api.isPremium():
		return PlayVideoPremium(sender,url, title, duration, summary=summary, mediaId=mediaId, modifyUrl=modifyUrl, premium=premium)
	else:
		return PlayVideoFreebie(sender,url, title, duration, summary=summary, mediaId=mediaId, modifyUrl=modifyUrl, premium=premium)

def PlayVideoPremium(sender, url, title, duration, summary = None, mediaId=None, modifyUrl=False, premium=False):
	# mkayy, new strategy. It's difficult to know how to acheive 1080p with boxee (or web player!). 
	# It's really easy to set resolution with direct grab of stream.
	# Only premium members get better resolutions.
	# so the solution is to have 2 destinations: freebie (web player), or premium (direct).
	
	theUrl = url
	resolutions = scrapper.getAvailResFromPage(url)
	vidInfo = scrapper.getVideoInfo(url, mediaId, resolutions)
	vidInfo['small'] = 0
	duration = vidInfo['duration'] # need this because duration isn't known until now

	bestRes = 360

	if Prefs['quality'] == "Ask":
		m = re.search(r'\?p(\d+)', url)
		if m:
			bestRes = m.group(1)
	else:	
		bestRes = scrapper.getPrefRes(resolutions)
	
	bestRes = int(bestRes)
	
	Log.Debug("Best res: " + str(bestRes))
	
	if api.isPremium(): # direct stream for premium users
		# FIXME: have to account for drama vs anime premium!
		req = HTTP.Request(theUrl, immediate=True, cacheTime=10*60*60)	#hm, cache time might mess up login/logout
		#Log.Debug("###########")
		#Log.Debug(req.content)

		match = re.match(r'^.*(<link *rel *= *"video_src" *href *= *")(http:[^"]+).*$', repr(req.content), re.MULTILINE)
		if not match:
			# bad news
			Log.Error("###########Could not find direct swf link, trying hail mary pass...")
			theUrl = theUrl
		else:
			theUrl = match.group(2)	+ "&__qual=" + str(bestRes)
	else: # web player
		Log.Debug("#######Using web player")
		if modifyUrl is True:
			theUrl = getVideoUrl(vidInfo, bestRes)

	Log.Debug("##########final URL is '%s'" % theUrl)
	Log.Debug("##########duration: %s" % str(duration))
	
	#req = HTTP.Request(theUrl, immediate=True, cacheTime=0)
	#Log.Debug(req.content)
	return Redirect(WebVideoItem(theUrl, title = title, duration = duration, summary = summary))
	
def PlayVideoFreebie(sender, url, title, duration, summary = None, mediaId=None, modifyUrl=False, premium=False):
	"""
	The video has been chosen! Whew. Only thing left is to munge the URL so site configs
	do the Right Thing, and redirect to WebVideoItem()
	"""
	# Current issues:
	# Crunchyroll.com  pops up an ad on the web page and crashes PMS entirely. Welcome to the
	# wonderful world of HTML 5 -- indestructable popups!
	# I try to get around this by setting the cookie temp_ad_closed to 1 in site config,
	# but I'm sure the situation will change with the wind; boxee stream is best
	# choice ATM if crashing happens.
	
	theUrl = url
	resolutions = scrapper.getAvailResFromPage(url)
	vidInfo = scrapper.getVideoInfo(url, mediaId, resolutions)
	duration = vidInfo['duration'] # need this because duration isn't known until now
	
	
	if modifyUrl is True:
		vidInfo['small'] = False # let's just blow all the checks, man. If res isn't shown on the page, it can't be played		
		bestRes = scrapper.getPrefRes(resolutions)
		theUrl = getVideoUrl(vidInfo, bestRes)


	# theUrl = theUrl + "&small=1"


	# grab the .swf file directly
	# example element:
	#<link rel="video_src" href="http://www.crunchyroll.com/swf/vidplayer.swf?config_url=http%3A%2F%2Fwww.crunchyroll.com%2Fxml%2F%3Freq%3DRpcApiVideoPlayer_GetStandardConfig%26media_id%3D591521%26video_format%3D0%26video_quality%3D0%26auto_play%3D1%26click_through%3D1" />

	
	if Prefs['video_source'] == "Direct":
		if api.isPremium(): # only premium users should grab directly
			req = HTTP.Request(theUrl, immediate=True, cacheTime=10*60*60)	#hm, cache time might mess up login/logout
			#Log.Debug("###########")
			#Log.Debug(req.content)
	
			match = re.match(r'^.*(<link *rel *= *"video_src" *href *= *")(http:[^"]+).*$', repr(req.content), re.MULTILINE)
			if not match:
				# bad news
				Log.Error("###########Could not find direct swf link, trying hail mary pass...")
				theUrl = theUrl
			else:
				theUrl = match.group(2)
	elif Prefs['video_source'] == "Boxee Stream":
		#req = HTTP.Request(theUrl, immediate=True, cacheTime=10*60*60)	#hm, cache time might mess up login/logout

		# example: http://www.crunchyroll.com/angelic-layer/episode-26-454040?p480=1
		pieces = theUrl.split('/')
		name = pieces[3]
		id = re.sub(r'.*-|\?.*', r'', pieces[4])
		mediapath = pieces[4].split('?')[0]
		
		#http://www.crunchyroll.com/boxee_showmedia/588306&amp;bx-ourl=http://www.crunchyroll.com/naruto-shippuden/episode-246-the-orange-spark-588306
		
		theUrl = "http://www.crunchyroll.com/boxee_showmedia/%s&amp;bx-ourl=http://www.crunchyroll.com/%s/%s" % (id, name, mediapath)

		req = HTTP.Request(theUrl, immediate=True, cacheTime=0, encoding='utf8')

		#FIXME use xpath instead of re.search()
		m = re.search(r'\'video_player\',\'([^\']+)\', *\'([^\']+)\'', req.content, re.MULTILINE) ;m

		if m:
			height = m.group(2) # only care about height
			theUrl=theUrl + "&__qual=%s" % height # this is bogus param for site config recognition
		else:
			Log.Error("#####could not find user resolution settings for %s" % theUrl)
			Log.Debug(req.content)
			# but we go with it anyway...			
 			
	Log.Debug("##########final URL is '%s'" % theUrl)
	Log.Debug("##########duration: %s" % str(duration))
	
	#req = HTTP.Request(theUrl, immediate=True, cacheTime=0)
	#Log.Debug(req.content)
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
	#scrapper.CacheAll()
	#Log.Debug("num of eps: %s"%(len(Dict['episodes'])))
	#Log.Debug("num of shows: %s"%(len(Dict['series'])))
	
	if 1==0:
		Dict['episodes'] = Data.LoadObject("episodes")
		Dict['series'] = Data.LoadObject("series")
		Dict['fanart'] = Data.LoadObject("fanart")

		
def msToRuntime(ms):
	"""
	convert miliseconds into a time string in the form
	HH:MM:SS
	"""
	if ms is None or ms <= 0:
		return None
		
	ret = []
	
	sec = int(ms/1000) % 60
	min = int(ms/1000/60) % 60
	hr  = int(ms/1000/60/60)
	
	return "%02d:%02d:%02d" % (hr,min,sec)

########## OLD STUFF FOR REFERENCE OR REVERT ####
def loginAtStart_old():
	global GlobalWasLoggedIn
	global AnimePremium
	global DramaPremium
	#HTTP.ClearCookies() # FIXME put this back in after debugging
	if api.loginNotBlank():
		data = { "name": Prefs['username'], "password": Prefs['password'], "req": "RpcApiUser_Login" }
		response = api.makeAPIRequest(data)
		Log.Debug("loginResponse:%s"%response)
		response = JSON.ObjectFromString(response)
		GlobalWasLoggedIn = (response.get('result_code') == 1)
		if GlobalWasLoggedIn:
			AnimePremium = (response.get('data').get('premium').get(PREMIUM_TYPE_ANIME) == 1)
			DramaPremium = (response.get('data').get('premium').get(PREMIUM_TYPE_DRAMA) == 1)
	return GlobalWasLoggedIn


def loggedIn_old():
	return GlobalWasLoggedIn


def login_old():
	if api.loginNotBlank():
		data = { "name": Prefs['username'], "password": Prefs['password'], "req": "RpcApiUser_Login" }
		response = api.makeAPIRequest(data)
