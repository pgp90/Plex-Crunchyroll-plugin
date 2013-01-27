# -*- coding: utf-8 -*-
from constants import *
import re
import fanartScrapper #needed to prevent errors if the user ends up activating the fanart
from datetime import datetime # more robust than Datetime

HTTP.CacheTime = 3600
HTTP.Headers["User-Agent"] = "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_6; en-gb) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16"
HTTP.Headers["Accept-Encoding"] = "gzip, deflate"

	
def makeSeriesItem(series):
	"""
	create a directory item out of the passed dict 
	that the user can click on to enter its episode list
	"""
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
			thumb=getThumbUrl(series['thumb'], tvdbId=series['tvdbId']), #Function(getThumb,url=series['thumb'],tvdbId=series['tvdbId']),
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
		artUrl = getSeasonThumb(Dict['series'][str(season['seriesId'])]['tvdbId'], season['seasonnum'])
		#Log.Debug("arturl: %s"%artUrl)
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
	from datetime import datetime
	
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

	episodeItem = []
	summary = makeEpisodeSummary(episode)
	
	# check if it's available.
	# FIXME it's enjoyable to watch simulcasts count down, so
	# maybe allow going to video if premium.

	# FIXME: directory caching could block recently available episodes?
	if episode: #HUH? why check if episode is valid here, I forget...
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
					timeString = availableAt.strftime("%a, %d %b %Y %H:%M:%S %Z") + " GMT"
					reason = "This video will be aired for premium users on %s." % timeString
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
		
		if not available:
			episodeItem = Function(DirectoryItem(
							NotAvailable,
							title = episode['title'] + " (Not Yet Available)",
							subtitle = "Season %s"%episode['season'],
							summary = createRatingString(episode['rating']) + summary,
							thumb = Function(GetThumb,url=episode['thumb']),
							art=Function(GetArt,url=getEpisodeArt(episode))
							),
							reason = reason
						)
			return episodeItem
						
	# check the rating
	if episode['rating'] and episode['rating'] > 4: # adult supervision from 5 up
		if Prefs['hideMature'] is True:
			episodeItem = Function(DirectoryItem(
				AdultWarning,
				title = episode['title'],
				subtitle = "Season %s"%episode['season'],
				summary = createRatingString(episode['rating']) + summary,
				thumb = Function(GetThumb,url=episode['thumb']),
				art=Function(GetArt,url=getEpisodeArt(episode))
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
				thumb = Function(GetThumb,url=episode['thumb']),
				art=Function(GetArt,url=getEpisodeArt(episode)),
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
"""
def CreatePrefs():
	Prefs.Add(id='loginemail', type='text', default="", label='Login Email')
	Prefs.Add(id='password', type='text', default="", label='Password', option='hidden')
	Prefs.Add(id='quality', type='enum', values=["SD", "480P", "720P", "1080P", "Highest Available"], default="Highest Available", label="Quality")
	Prefs.Add(id='video_source', type='enum', values=["Web Player", "Boxee Stream", "Direct"], default="Boxee Stream", label="Video Source")
	Prefs.Add(id='thumb_quality', type='enum', values=["Low", "Medium", "High"], default="High", label="Thumbnail Quality")
	Prefs.Add(id='restart', type='enum', values=["Resume", "Restart"], default="Restart", label="Resume or Restart")
	Prefs.Add(id='hideMature', type='bool', default="true", label="Hide mature content?")
	Prefs.Add(id='fanart', type='bool', default="false", label="Use Fanart.tv when possible?")
"""

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

	if CHECK_PLAYER is True:
		returnPlayer()
	Log.Debug("art: %s"%R(CRUNCHYROLL_ART))

	dir = MediaContainer(disabledViewModes=["Coverflow"], title1="Crunchyroll")
	
	# show queue menu even if not logged in, since the cache will keep it hidden
	# if user logs in later. Not ideal, but whatev. CR.com gets some advertising.
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

def QueueMenu(sender):
	"""
	Show series titles that the user has in her queue
	"""
	# FIXME plex seems to cache this, so removing/adding doesn't give feedback
	if isRegistered():
		dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="Series", noCache=True)
		queueList = getQueueList()
		for queueInfo in queueList:
			dir.Append(makeQueueItem(queueInfo))
		return dir
	else:
		return MessageContainer("Log in required", "You must be logged in to view your queue.")

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
		summary=queueInfo['nextUpText'] + queueInfo['episodeDescription'],
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
	seriesurl = seriesTitleToUrl(queueInfo['title'])
	s = Dict['series']
	sId = str(queueInfo['seriesId'])
	thumb = (s[sId]['thumb'] if (sId in s and s[sId]['thumb'] is not None) else R(CRUNCHYROLL_ICON))
	art = (s[sId]['art'] if (sId in s and s[sId]['art'] is not None) else R(CRUNCHYROLL_ART))
	if queueInfo['epToPlay'] is not None:
		nextEp = getEpInfoFromLink(queueInfo['epToPlay'])
		PlayNext = makeEpisodeItem(nextEp)
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
			seriesList = getAnimeSeriesList() + getDramaSeriesList()
			#sort again:
			seriesList = titleSort(seriesList)
			
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
	episodes = getEpisodeListForSeries(seriesId)
	if episodes['useSeasons'] is True:
		seasonNums = episodes['seasons'].keys()
		Log.Debug("season nums: %s" % seasonNums)
		season = {}
		season['url'] = seriesTitleToUrl(Dict['series'][str(seriesId)]['title'])
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
	epList = getSeasonEpisodeListFromFeed(seriesId, season)
	for episode in epList:
		dir.Append(makeEpisodeItem(episode))
	return dir

	
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
		dir.Append(Function(DirectoryItem(KillSafariCookiesItem, "Kill Safari Cookies", summary="This will remove all crunchyroll.com cookies from Safari's cookie file. Useful if login status is not synced.")) )
		dir.Append(Function(DirectoryItem(TransferCookiesItem, "Transfer cookies to Safari", summary="This transfers Plex's crunchyroll cookies into safari's plist.")) )
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
	Dict.Reset() #OMG this doesn't work. Just delete the file at Plug-in support/com.plexapp.plugins.CrunchyRoll
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

def KillSafariCookiesItem(sender):
	killSafariCookies()
	return MessageContainer("Cookies Cleared", "All cookies from crunchyroll.com have been removed from Safari")

def TransferCookiesItem(sender):
	if transferCookiesToSafari():
		return MessageContainer("Cookies Transferred.", "Done.")
	else:
		return MessageContainer("Transfer Failed.", "Nastiness occured, check the console.")

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
	
def ConstructTestVideo(episode)	:
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

#import fanartScrapper

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
	return getThumb(url,tvdbId)

def GetArt(url,tvdbId=None):
	"""
	find a fanart url
	"""
	return getArt(url, tvdbId)


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
		episode['availableResolutions'] = getAvailResFromPage(episode['link'])

		# FIXME I guess it's better to have something than nothing? It was giving Key error
		# on episode number
		if str(episode['mediaId']) not in Dict['episodes']:
			Dict['episodes'][str(episode['mediaId'])] = episode
	
		Dict['episodes'][str(episode['mediaId'])]['availableResolutions'] = episode['availableResolutions']
	
	videoInfo = getVideoInfo(episode['link'], episode['mediaId'], episode['availableResolutions'])
	videoInfo['small'] = (isPaid() and isPremium(episode.get('category'))) is False
	
	epsObject = EpisodeObject(
		url = videoInfo['baseUrl'], #dunno if this will work
		title = episode['title'],
		summary = episode['description']
	)

	for q in episode['availableResolutions']:
		dur = episode.get('duration')
		if not (dur and dur > 0):
			dur = 0
			
		mo = MediaObject(
				duration = dur,
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

def PlayVideoMenu2(sender, mediaId):
	"""
	use more code to accomplish less.
	"""
	episode = getEpisodeDict(mediaId)
	return constructMediaObject(mediaId)
	
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
			return PlayVideoFreebie2(sender, mediaId) # (sender,url, title, duration, summary=summary, mediaId=mediaId, modifyUrl=modifyUrl, premium=premium)
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
	
	req = HTTP.Request(modUrl, immediate=True, cacheTime=10*60*60)	#hm, cache time might mess up login/logout

	match = re.match(r'^.*(<link *rel *= *"video_src" *href *= *")(http:[^"]+).*$', repr(req.content), re.MULTILINE)
	if not match:
		# bad news
		Log.Error("###########Could not find direct swf link, trying hail mary pass...")
		Log.Debug(req.content)
		theUrl = theUrl
	else:
		theUrl = match.group(2)	+ "&__qual=" + str(bestRes)

	# try a manual redirect since redirects crash entire PMS
	import urllib2
	req = urllib2.urlopen(theUrl)
	theUrl = req.geturl() 
	req.close()
	
	Log.Debug("##########final URL is '%s'" % theUrl)
	#Log.Debug("##########duration: %s" % str(duration))
	

	return Redirect(WebVideoItem(theUrl, title = episode['title'], duration = duration, summary = makeEpisodeSummary(episode) ))
	
def PlayVideoFreebie(sender, mediaId): # url, title, duration, summary = None, mediaId=None, modifyUrl=False, premium=False):
	"""
	Freebie video is easy.
	"""
	episode = getEpisodeDict(mediaId)
	theUrl = episode['link']
	vidInfo = getVideoInfo(theUrl, mediaId, [360])	# need this for duration

	if episode.has_key('duration') and episode['duration'] > 0:
		duration = episode['duration']
	else:
		duration = vidInfo['duration']
		
	theUrl = theUrl+ "?p360=1&skip_wall=1&t=0&small=0&wide=0"

	Log.Debug("###pre-redirect URL: %s" % theUrl)
	# try a manual redirect since redirects crash entire PMS
	import urllib2
	req = urllib2.urlopen(theUrl)
	theUrl = req.geturl() 
	req.close()

	Log.Debug("####Final URL: %s" % theUrl)
	Log.Debug("##########duration: %s" % str(duration))
	#req = urllib2.urlopen(theUrl)
	#html = req.read()
	#Log.Debug(html)
	
	return Redirect(WebVideoItem(theUrl, title = episode['title'], duration = duration, summary = makeEpisodeSummary(episode)))

def PlayVideoFreebie2(sender, mediaId):
	"""
	Play a freebie video using the direct method. As long as crunchyroll.com delivers ads
	through the direct stream (they do as of Feb 14 2012), this is okay IMO. This gets
	around crashes with redirects/content changes of video page, and sacrifices the ability
	to use javascript in the site config.
	"""
	episode = getEpisodeDict(mediaId)
	infoUrl = episode['link'] + "?p360=1&skip_wall=1&t=0&small=0&wide=0"

	req = HTTP.Request(infoUrl, immediate=True, cacheTime=10*60*60)	#hm, cache time might mess up login/logout

	match = re.match(r'^.*(<link *rel *= *"video_src" *href *= *")(http:[^"]+).*$', repr(req.content), re.MULTILINE)
	if not match:
		# bad news
		Log.Error("###########Could not find direct swf link, trying hail mary pass...")
		Log.Debug(req.content)
		theUrl = infoUrl
	else:
		theUrl = match.group(2)	+ "&__qual=360"

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
	if loginNotBlank():
		data = { "name": Prefs['username'], "password": Prefs['password'], "req": "RpcApiUser_Login" }
		response = makeAPIRequest(data)
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
	if loginNotBlank():
		data = { "name": Prefs['username'], "password": Prefs['password'], "req": "RpcApiUser_Login" }
		response = makeAPIRequest(data)

########################################################################################
# web and json api stuff
########################################################################################

import time, os, re

#for cookie wrangling:
from Cookie import BaseCookie
import plistlib
from datetime import datetime, timedelta
import scrapper

PREMIUM_TYPE_ANIME = '2'
PREMIUM_TYPE_DRAMA = '4'

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

def loginViaWeb():
	# backup plan in case cookies go bonkers, not used.
	data = {'formname':'RpcApiUser_Login','fail_url':'http://www.crunchyroll.com/login','name':Prefs['username'],'password':Prefs['password']}
	req = HTTP.Request(url='https://www.crunchyroll.com/?a=formhandler', values=data, immediate=True, cacheTime=10, headers={'Referer':'https://www.crunchyroll.com'})
	HTTP.Headers['Cookie'] = HTTP.CookiesForURL('https://www.crunchyroll.com/')

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
#			killSafariCookies()
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
#			killSafariCookies()
			HTTP.ClearCookies()

		loginSuccess = loginViaApi(authInfo)
			
		#check it
		if loginSuccess or loggedIn():
			authInfo['loggedInSince'] = time.time()
			authInfo['failedLoginCount'] = 0
			#Dict['Authentication'] = authInfo
#			transferCookiesToSafari()
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
#	killSafariCookies()
	
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

#def transferCookiesToSafari():
#	"""
#	Copy all crunchyroll cookies from Plex's cookie storage
#	into Safari's Plist
#	"""
#	import platform
#	if "darwin" in platform.system().lower():
#		
#		cookieString = HTTP.CookiesForURL(BASE_URL)
#		if not cookieString: return True
#	
#		try:
#			theCookies = BaseCookie(cookieString)
#			appendThis = []
#			tomorrow = datetime.now() + timedelta((1))
#			for k, v in theCookies.items():
#				#Plex doesn't supply these, so:
#				cookieDict = {'Domain':".crunchyroll.com", 
#					'Path':"/", 
#					'Expires': tomorrow, 
#					'Created': time.time(),
#					'Name': k,
#					'Value': v.value
#				}
#				appendThis.append(cookieDict)
#			#Log.Debug("#######Transferring these cookies:")
#			#Log.Debug(appendThis)
#			
#			filename = os.path.expanduser("~/Library/Cookies/Cookies.plist")
#			theList = plistlib.readPlist(filename)
#			finalCookies = appendThis
#			
#			# brute force replace
#			for item in theList:
#				if not "crunchyroll.com" in item['Domain']:
#					finalCookies.append(item)
#	
#			plistlib.writePlist(finalCookies, filename)
#			return True
#		except Exception, arg:
#			Log.Error("#########transferCookiesToSafari() Exception occured:")
#			Log.Error(repr(Exception) + " " + repr(arg))
#			return False
#	else:
#		Log.Error("####Removing webkit cookies from a non-Darwin system is unsupported.")
#		return False
#
#def killSafariCookies():
#	"""
#	remove all cookies from ~/Library/Cookies/Cookies.plist matching the domain of .*crunchyroll.com
#	and save the result.
#	"""
#	import os
#	import plistlib
#	#Plex's sandboxing doesn't allow me to import platform,
#	# so let's not check for darwin and just fail.
#	try:
#		import platform
#		isDarwin = "darwin" in platform.system().lower()
#	except:
#		isDarwin = True # assume
#		
#	if isDarwin:
#		filename = os.path.expanduser("~/Library/Cookies/Cookies.plist")
#		try:
#			theList = plistlib.readPlist(filename)
#		except IOError:
#			#hm, okay, whatev, no file or gimpiness, let's bail
#			return
#			
#		theSavedList = []
#		for item in theList:
#			if not "crunchyroll.com" in item['Domain']:
#				theSavedList.append(item)
#			else:
#				#Log.Debug("######removing cookie:")
#				#Log.Debug(item)
#				pass
#		plistlib.writePlist(theSavedList, filename)
#	
#	
#def transferCookiesToPlex():
#	"""
#	grab all crunchyroll.com cookies from Safari
#	and transfer them to Plex. You shouldn't do this
#	because Plex needs to be the master to
#	keep the cookie situation <= fubar.
#	"""
#	# This function does nothing ATM
#	return
#	
#	import os.path, plistlib
#	filename = os.path.expanduser("~/Library/Cookies/Cookies.plist")
#	try:
#		theList = plistlib.readPlist(filename)
#	except IOError:
#		#hm, okay, whatev, no file or gimpiness, let's bail
#		return
#		
#	cookieList = []
#	for item in theList:
#		if "crunchyroll.com" in item['Domain']:
#			cookieList.append(item)
#	
#	s = SimpleCookie()
#	for cookie in cookieList:
#		#FIXME: should I bother?
#		pass

def deleteFlashJunk(folder=None):
	"""
	remove flash player storage from crunchyroll.com.
	We need to remove everything, as just removing
	'PersistentSettingsProxy.sol' (playhead resume info) leads 
	to buggy player behavior.
	"""
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

import re

import urllib2
import datetime # more robust than Datetime

"""
schema inside Dict{}
	all items (even movies) can be referenced by a the series dict.
	series are known by seriesID (a unique number), provided by crunchyroll.com
	Dict['series'] =
	{ seriesId: {
		"title": title,
		"seriesId": seriesId,
		"tvdbId": tvdbId,
		"description": description,
		"thumb": thumb,
		"art": art,
		'epsRetrived': None,
		'epList': None
		}
	}
	
	episodesList contains playable media (it's actually a dict, but let's not get finicky).
	episodes are known by mediaId (a unique number), provided at crunchyroll.com
	This is an episode entry in the list:
	Dict['episodes'] =
	{ '371594': {'seriesTitle': 'Egg Man', 
		'publisher': 'T.O Entertainment', 
		'mediaId': 371594, 
		'description': 'few images of the movie Egg Man\r\n ', 
		'episodeNum': None, 
		'rating': 1, 
		'season': None, 
		'title': 'Egg Man Trailer 1', 
		'link': 'http://www.crunchyroll.com/egg-man/-egg-man-egg-man-trailer-1-371594'
		}
	}
	another episode schema [! make these consistent!]
	episode = {
		"title": title,
		"link": link,
		"mediaId": mediaId,
		"description": description,
		"seriesTitle": seriesTitle,
		"episodeNum": episodeNum,
		"thumb": thumb,
		"availableResolutions": availableResolutions,
		"publisher": publisher,
		"season": season,
		"keywords": keywords,
		"type": mediaType,
		"rating": rating
	}
						
						
	season list contains seasons, and its parent is a "series".
	
"""


USE_RANDOM_FANART = True
SERIES_FEED_CACHE_TIME = 3600 # 1 hour
QUEUE_LIST_CACHE_TIME = 15 # 15 seconds
ART_SIZE_LIMIT = True
SPLIT_LONG_LIST = True

SERIES_TITLE_URL_FIX = {
"goshuushosama-ninomiya-kun":"good-luck-ninomiya-kun"
}

Boxee2Resolution = {'12':360, '20':480, '21':720, '23':1080}
Quality2Resolution = {"SD":360, "480P":480, "720P":720, "1080P": 1080, "Highest Available":1080, "Ask":360}

###########
# these bad boys are here to keep __init__.py from manipulating rss feeds directly
# and to keep feed handling in one place.
###########

def getPopularAnimeEpisodes():
	"return a list of anime episode dicts that are currently popular"
	return getEpisodeListFromFeed(POPULAR_ANIME_FEED, sort=False)

def getPopularDramaEpisodes():
	"return a list of drama episode dicts that are currenly popular"
	return getEpisodeListFromFeed(POPULAR_DRAMA_FEED, sort=False)

def getPopularVideos():
	"return the most popular videos."
	return getEpisodeListFromFeed(POPULAR_FEED, sort=False)

def getRecentVideos():
	"return a list of episode dicts of recent videos of all types"
	return getEpisodeListFromFeed(RECENT_VIDEOS_FEED, sort=False)

def getRecentAnimeEpisodes():
	"return a list of episode dicts of recently added anime episodes"
	return getEpisodeListFromFeed(RECENT_ANIME_FEED, sort=False)

def getRecentDramaEpisodes():
	"return a list of recently added drama videos"
	return getEpisodeListFromFeed(RECENT_DRAMA_FEED, sort=False)

def getEpisodeListFromQuery(queryString):
	"return a list of relevant episode dicts matching queryString"
	return getEpisodeListFromFeed(SEARCH_URL+queryString.strip().replace(' ', '%20'), sort=False)

# series feeds use boxee_feeds url, so the parsing is quite different
def getAnimeSeriesList():
	"return a list of all available series in anime"
	return getSeriesListFromFeed(SERIES_FEED_BASE_URL + "genre_anime_all", sort=True)

def getDramaSeriesList():
	"return a list of all available series in Drama"
	return getSeriesListFromFeed(SERIES_FEED_BASE_URL + "drama", sort=True)

def getAllSeries():
	"return a list of series dicts that represent all available series"
	list = []
	anime = getAnimeSeriesList()
	drama = getDramaSeriesList()
	# FIXME: if there's overlap, we'll have dupes...
	list = anime + drama
	return list

def getPopularDramaSeries():
	"return a list of series dicts of most popular drama"
	return getSeriesListFromFeed(SERIES_FEED_BASE_URL + "drama_popular", sort=False)

def getPopularAnimeSeries():
	"return a list of series dicts of most popular anime"
	return getSeriesListFromFeed(SERIES_FEED_BASE_URL + "anime_popular", sort=False)

def getAnimeSeriesByGenre(genre):
	queryStr = ANIME_GENRE_LIST[genre].replace(' ', '%20')
	feed = SERIES_FEED_BASE_URL + "anime_withtag/" + queryStr
	return getSeriesListFromFeed(feed)

def getDramaSeriesByGenre(genre):
	queryStr = DRAMA_GENRE_LIST[genre].replace(' ', '%20')
	feed = SERIES_FEED_BASE_URL + "genre_drama_" + queryStr
	return getSeriesListFromFeed(feed)

def getSeriesByGenre(genre):
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

def getQueueList():
	login()
	queueURL = BASE_URL+"/queue"
	queueHtml = HTML.ElementFromURL(queueURL,cacheTime=QUEUE_LIST_CACHE_TIME)
	queueList = []
	items = queueHtml.xpath("//div[@id='main_content']/ul[@id='sortable']/li[@class='queue-item']")
	for item in items:
		title = item.xpath(".//span[@class='series-title ellipsis']")[0].text
		seriesId = int(item.xpath("@series_id")[0].replace("queue_item_",""))
		epToPlay = BASE_URL+item.xpath(".//a[@itemprop='url']/@href")[0].split("?t=")[0]
		
		episodeTitle= item.xpath(".//a[@itemprop='url']/@title")[0]
		episodeDescription = item.xpath(".//p[@itemprop='description']")

		if episodeDescription:
			episodeDescription = episodeDescription[0].text.strip('\n').strip()
		else:
			episodeDescription = ""
		"""
		make sure item has an ID and does not error out from an empty string.
		Semms to be a very rare problem caused by some media renaming and reorganization.
		"""
		episodeMediaIDStr = item.xpath("@media_id")[0]
		if not (episodeMediaIDStr == ""):
			episodeMediaID = int(item.xpath("@media_id")[0])
			
			nextUpText = item.xpath(".//span[@class='series-data ellipsis']")[0].text
			fixit = ""
			for line in nextUpText.split('\n'):
				fixit = fixit + line.strip('\n').strip() +'\n'

			nextUpText = fixit

			Log.Debug("##################################")
				
			queueItem = {
				"title": title,
				"seriesId": seriesId,
				"epToPlay": epToPlay,
				"episodeTitle": episodeTitle,
				"episodeDescription": episodeDescription,
				"nextUpText": nextUpText,
				"mediaID": episodeMediaID,
				"seriesStatus": None
			}
			queueList.append(queueItem)
		
	return queueList
	
def getEpisodeDict(mediaId):
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

def recoverEpisodeDict(mediaId):
	"""
	try everything possible to recover the episode info for
	mediaId and save it in Dict{}. If it fails, return none.
	"""
	Log.Debug("#######recovering episode dictionary for mediaID %s" % str(mediaId))
	# get a link with title in it.
	#import urllib2
	req = urllib2.urlopen(BASE_URL+"/media-" + str(mediaId) + "?pskip_wall=1")
	redirectedUrl = req.geturl()
	req.close

	redirectedUrl = redirectedUrl.replace("?pskip_wall=1", "")	
	seriesName = redirectedUrl.split(".com/")[1].split("/")[0]
	seriesUrl = seriesTitleToUrl(seriesName)
	getEpisodeListFromFeed(seriesUrl) # for side-effect of caching episode
	
	if str(mediaId) in Dict['episodes']:
		return Dict['episodes'][str(mediaId)]
	
	# FIXME
	# not good so far, we need a feed that provides full episodes. Yikes.
	# try grabbing from boxee_feeds
	# need seriesID as in boxee_feeds/showseries/384855
	# which can be retrieved from the seriesUrl contents, whew...
	# alternatively, use http://www.crunchyroll.com/series-name/episodes
	# which gives full episodes, but, well, is HTML and has less media info
	return None

def titleSort(dictList):
	"""
	sort list of dict by key 'title' and return the result
	"""
	res = sorted(dictList, key=lambda k: getSortTitle(k))
	return res

def getSortTitle(dictList):
	"""
	get the 'title' key and return the sortable title as string
	"""
	title = dictList['title'].lower().strip()
	firstword = title.split(" ",1)[0]
	if firstword in ['a', 'an', 'the']:
		title = title.split(firstword, 1)[-1]
	return title.strip()

def cacheAllSeries():
	#startTime = Datetime.Now()
	seriesDict = Dict['series']
	for feed in ["genre_anime_all", "drama"]:
		feedHtml = HTML.ElementFromURL(SERIES_FEED_BASE_URL+feed,cacheTime=SERIES_FEED_CACHE_TIME)
		items = feedHtml.xpath("//item")
		if seriesDict is None:
			seriesDict = {}
		@parallelize
		def parseSeriesItems():
			for item in items:
				seriesId = int(item.xpath("./guid")[0].text.split(".com/")[1])
				@task
				def parseSeriesItem(item=item,seriesId=seriesId):
					if not (str(seriesId) in seriesDict):
						title = item.xpath("./title")[0].text
						description = item.xpath("./description")[0].text
						if Prefs['fanart'] is True:
							tvdbIdr = tvdbscrapper.GetTVDBID(title, Locale.Language.English)
							tvdbId = tvdbIdr['id']
						else:
							tvdbId = None
						#if USE_RANDOM_FANART is True and tvdbId is not None:
						#	thumb = fanartScrapper.getRandImageOfTypes(tvdbId,['tvthumbs'])
						#	art = fanartScrapper.getRandImageOfTypes(tvdbId,['clearlogos','cleararts'])
						#	if thumb is None:
						#		thumb = str(item.xpath("./property")[0].text).replace("_large",THUMB_QUALITY[Prefs['thumb_quality']])
						#	if art is None:
						#		art = str(item.xpath("./property")[0].text).replace("_large",THUMB_QUALITY[Prefs['thumb_quality']])
						#else:
						thumb = str(item.xpath("./property")[0].text).replace("_large",THUMB_QUALITY[Prefs['thumb_quality']])
						art = thumb
						dictInfo = {
							"title": title,
							"seriesId": seriesId,
							"tvdbId": tvdbId,
							"description": description,
							"thumb": thumb,
							"art": art,
							'epsRetrived': None,
							'epList': None
						}
						seriesDict[str(seriesId)] = dictInfo
					else:
						#tvdbId = seriesDict[str(seriesId)]['tvdbId']
						#if USE_RANDOM_FANART is True and tvdbId is not None:
						#	thumb = fanartScrapper.getRandImageOfTypes(tvdbId,['clearlogos','cleararts','tvthumbs'])
						#	art = fanartScrapper.getRandImageOfTypes(tvdbId,['clearlogos','cleararts'])
						#	if thumb is None:
						#		thumb = str(item.xpath("./property")[0].text).replace("_large",THUMB_QUALITY[Prefs['thumb_quality']])
						#	if art is None:
						#		art = str(item.xpath("./property")[0].text).replace("_large",THUMB_QUALITY[Prefs['thumb_quality']])
						#else:
						thumb = str(item.xpath("./property")[0].text).replace("_large",THUMB_QUALITY[Prefs['thumb_quality']])
						art = thumb
						seriesDict[str(seriesId)]['thumb'] = thumb
						seriesDict[str(seriesId)]['art'] = art
				
		
		Dict['series'] = seriesDict
		#endTime = Datetime.Now()
		#Log.Debug("start time: %s"%startTime)
		#Log.Debug("end time: %s"%endTime)


def getSeriesListFromFeed(feed, sort=True):
	"""
	given a proper feed url at http://www.crunchyroll.com/boxee_feeds/
	(not "http://www.crunchyroll.com/rss" !),
	construct a list of series dicts and return them.
	
	Also, put anything we find into the Dict{} cache.
	"""
	# sort=False is slightly bogus
	# since parallel tasks might jumble the order.
	# It's not too bad, though; popular items
	# and more relevant searches tend to show up on top...
	#startTime = Datetime.Now()
	feedURL = feed
	feedHtml = HTML.ElementFromURL(feedURL,cacheTime=SERIES_FEED_CACHE_TIME)
	seriesList = []
	items = feedHtml.xpath("//item")
	seriesDict = Dict['series']
	if Dict['series'] is None:
		Dict['series'] = {}
	@parallelize
	def parseSeriesItems():
		for item in items:
			seriesId = int(item.xpath("./guid")[0].text.split(".com/")[1])
			@task
			def parseSeriesItem(item=item,seriesId=seriesId):
				if not (str(seriesId) in Dict['series']):
					title = item.xpath("./title")[0].text
					if Prefs['fanart'] is True:
						tvdbIdr = tvdbscrapper.GetTVDBID(title, Locale.Language.English)
						tvdbId = tvdbIdr['id']
					else:
						tvdbId = None
						
					description = item.xpath("./description")[0].text
					#if USE_RANDOM_FANART is True and tvdbId is not None:
					#	thumb = fanartScrapper.getRandImageOfTypes(tvdbId,['tvthumbs'])
					#	art = fanartScrapper.getRandImageOfTypes(tvdbId,['clearlogos','cleararts'])
					#	if thumb is None:
					#		thumb = str(item.xpath("./property")[0].text).replace("_large",THUMB_QUALITY[Prefs['thumb_quality']])
					#	if art is None:
					#		art = str(item.xpath("./property")[0].text).replace("_large",THUMB_QUALITY[Prefs['thumb_quality']])
					#else:
					thumb = str(item.xpath("./property")[0].text).replace("_large",THUMB_QUALITY[Prefs['thumb_quality']])
					
					if ART_SIZE_LIMIT is False:
						art = thumb
					else:
						art = None
					series = {
						"title": title,
						"seriesId": seriesId,
						"tvdbId": tvdbId,
						"description": description,
						"thumb": thumb,
						"art": art
					}
					dictInfo = series
					dictInfo['epsRetrived'] = None
					dictInfo['epList'] = []
					Dict['series'][str(seriesId)] = dictInfo
				else:
					title = item.xpath("./title")[0].text
					#tvdbId = seriesDict[str(seriesId)]['tvdbId']
					#if USE_RANDOM_FANART is True and tvdbId is not None:
					#	thumb = fanartScrapper.getRandImageOfTypes(tvdbId,['tvthumbs'])
					#	art = fanartScrapper.getRandImageOfTypes(tvdbId,['clearlogos','cleararts'])
					#	if thumb is None:
					#		thumb = str(item.xpath("./property")[0].text).replace("_large",THUMB_QUALITY[Prefs['thumb_quality']])
					#	if art is None:
					#		art = str(item.xpath("./property")[0].text).replace("_large",THUMB_QUALITY[Prefs['thumb_quality']])
					#else:
					thumb = str(item.xpath("./property")[0].text).replace("_large",THUMB_QUALITY[Prefs['thumb_quality']])

					if ART_SIZE_LIMIT is False:
						art = thumb
					else:
						art = None
					seriesDict = Dict['series'][str(seriesId)]
					seriesDict['thumb'] = thumb
					seriesDict['art'] = art
					Dict['series'][str(seriesId)] = seriesDict
					series = {
						"title": seriesDict['title'],
						"seriesId": seriesId,
						"tvdbId": seriesDict['tvdbId'],
						"description": seriesDict['description'],
						"thumb": seriesDict['thumb'],
						"art": seriesDict['art']
					}
				seriesList.append(series)
			
	
	#midTime = Datetime.Now()
	#Dict['series'] = seriesDict
	if sort:
		sortedSeriesList = titleSort(seriesList)
	else:
		sortedSeriesList = seriesList
	#endTime = Datetime.Now()
	#Log.Debug("start time: %s"%startTime)
	#Log.Debug("mid time: %s"%midTime)
	#Log.Debug("end time: %s"%endTime)
	#Log.Debug("not found: %s"%notFoundList)
	
	if False:
		ls = "\n"
		for t in seriesList:
			if t['tvdbId'] is not None:
				ls = '%s"%s": %s,\n'%(ls,t['title'],t['tvdbId'])
		Log.Debug("list: %s"%ls)
		ls = "\n"
		for t in seriesList:
			if t['tvdbId'] is None:
				ls = '%s"%s": %s,\n'%(ls,t['title'],t['tvdbId'])
		Log.Debug("list: %s"%ls)
	
	return sortedSeriesList


def getEpisodeInfoFromPlayerXml(mediaId):
	#FIXME: playerXml will change if user changes preferences at Crunchyroll.com
	# it's delivered ad-hoc according to server-side account information 
	try:
		if not mediaId in Dict['playerXml']:
			url = "http://www.crunchyroll.com/xml/?req=RpcApiVideoPlayer_GetStandardConfig&media_id=%s&video_format=102&video_quality=10&auto_play=1&show_pop_out_controls=1&pop_out_disable_message=Only+All-Access+Members+and+Anime+Members+can+pop+out+this" % mediaId
			#Log.Debug("getEpisodeInfoFromPlayerXml url: %s" % url)
			html = HTML.ElementFromURL(url)
			#debugFeedItem(html)
			episodeInfo = {}
			#episodeInfo['videoFormat'] = html.xpath("//videoformat")[0].text
			#episodeInfo['backgroundUrl'] = html.xpath("//backgroundurl")[0].text
			#episodeInfo['initialVolume'] = int(html.xpath("//initialvolume")[0].text)
			#episodeInfo['initialMute'] = html.xpath("//initialmute")[0].text
			#episodeInfo['host'] = html.xpath("//stream_info//host")[0].text
			#episodeInfo['file'] = html.xpath("//stream_info/file")[0].text
			#episodeInfo['mediaType'] = html.xpath("//stream_info/media_type")[0].text
			#episodeInfo['videoEncodeId'] = html.xpath("//stream_info/video_encode_id")[0].text
			episodeInfo['width'] = html.xpath("//stream_info/metadata/width")[0].text
			episodeInfo['height'] = html.xpath("//stream_info/metadata/height")[0].text
			episodeInfo['duration'] = html.xpath("//stream_info/metadata/duration")[0].text
			#episodeInfo['token'] = html.xpath("//stream_info/token")[0].text
			episodeInfo['episodeNum'] = html.xpath("//media_metadata/episode_number")[0].text
			#Log.Debug("episodeNum: %s\nduration: %s" % (episodeInfo['episodeNum'], episodeInfo['duration']))
			ratio = float(episodeInfo['width'])/float(episodeInfo['height'])
			if ratio < 1.5:
				episodeInfo['wide'] = False
			else:
				episodeInfo['wide'] = True
			Dict['playerXml'][str(mediaId)] = episodeInfo
		else:
			episodeInfo = Dict['playerXml'][str(mediaId)]
	except:
		episodeInfo = None
	return episodeInfo


def getEpisodeListForSeries(seriesId):
	#FIXME the series-name-bleh.rss feeds
	# no longer provide us with all episodes, only the latest ~40
	#Log.Debug("Dict['episodes']: %s"%Dict['episodes'])
	if str(seriesId) not in Dict['series']:
		cacheAllSeries()
	seriesData = Dict['series'][str(seriesId)]
	#TODO return age time back to 60 minutes when done testing.
	if seriesData['epList'] is None or seriesData['epsRetrived'] is None or seriesData['epsRetrived']+Datetime.Delta(minutes=1) <= Datetime.Now():
		epList = getEpisodeListFromFeed(seriesTitleToUrl(seriesData['title']))
		seriesData['epsRetrived'] = Datetime.Now()
		epIdList = []
		for ep in epList:
			epIdList.append(ep['mediaId'])
		seriesData['epList'] = epIdList
		Dict['series'][str(seriesId)] = seriesData
	else:
		epList = []
		for epId in seriesData['epList']:
			epList.append(Dict['episodes'][str(epId)])
	hasSeasons = True
	for ep in epList:
		if ep['season'] is None:
			hasSeasons = False
	#Log.Debug("seriesData: %s"%Dict['series'][str(seriesId)])
	return formateEpList(epList,hasSeasons)


def CacheAll():
	global avgt
	global avgc
	tvdbscrapper.setuptime()
	t = Datetime.Now()
	avgt = t - t
	avgc = 0
	t1 = Datetime.Now()
	cacheAllSeries()
	t2 = Datetime.Now()
	@parallelize
	def cacheShowsEps():
		Log.Debug(str(Dict['series'].keys()))
		for sik in Dict['series'].keys():
			seriesId = sik
			@task
			def cacheShowEps(seriesId=seriesId):
				global avgt
				global avgc
				ta = Datetime.Now()
				seriesData = Dict['series'][str(seriesId)]
				if seriesData['epsRetrived'] is None or seriesData['epsRetrived']+Datetime.Delta(minutes=60) <= Datetime.Now():
					epList = getEpisodeListFromFeed(seriesTitleToUrl(seriesData['title']))
					seriesData['epsRetrived'] = Datetime.Now()
					epIdList = []
					for ep in epList:
						epIdList.append(ep['mediaId'])
					seriesData['epList'] = epIdList
					Dict['series'][str(seriesId)] = seriesData
					tb = Datetime.Now()
					avgt = avgt + (tb - ta)
					avgc = avgc + 1
			
	
	t3 = Datetime.Now()
	tavg = avgt / avgc
	idavg = tvdbscrapper.getavg()
	Log.Debug("cache series time: %s"%(t2-t1))
	Log.Debug("cache all ep time: %s"%(t3-t2))
	Log.Debug("cache ep avg time: %s"%(tavg))
	Log.Debug("cache id avg time: %s"%(idavg))
	


def getEpisodeListFromFeed(feed, sort=True):
	import datetime
	try:
		episodeList = []
		PLUGIN_NAMESPACE = {"media":"http://search.yahoo.com/mrss/", "crunchyroll":"http://www.crunchyroll.com/rss"}

		# timeout errors driving me nuts, so
		req = HTTP.Request(feed, timeout=100)
		feedHtml = XML.ElementFromString(req.content)
#		feedHtml = XML.ElementFromURL(feed)
		items = feedHtml.xpath("//item")
		seriesTitle = feedHtml.xpath("//channel/title")[0].text.replace(" Episodes", "")
		hasSeasons = True
		@parallelize
		def parseEpisodeItems():
			for item in items:
				mediaId = int(item.xpath("./guid")[0].text.split("-")[-1])
				@task
				def parseEpisodeItem(item=item,mediaId=mediaId):
					if not str(mediaId) in Dict['episodes']:
						title = item.xpath("./title")[0].text
						if title.startswith("%s - " % seriesTitle):
							title = title.replace("%s - " % seriesTitle, "")
						elif title.startswith("%s Season " % seriesTitle):
							title = title.replace("%s Season " % seriesTitle, "")
							title = title.split(" ", 1)[1].lstrip("- ")
						#link = item.xpath("./link")[0].text
						link = item.xpath("./guid")[0].text
						description = item.xpath("./description")[0].text
						
						if "/><br />" in description:
							description = description.split("/><br />")[1]
						try:
							episodeNum = int(item.xpath("./crunchyroll:episodeNumber", namespaces=PLUGIN_NAMESPACE)[0].text)
						except:
							episodeNum = None
						try: publisher = item.xpath("./crunchyroll:publisher", namespaces=PLUGIN_NAMESPACE)[0].text
						except: publisher = ""
						
						try: thumb = str(item.xpath("./media:thumbnail", namespaces=PLUGIN_NAMESPACE)[0].get('url')).replace("_large",THUMB_QUALITY[Prefs['thumb_quality']])
						except IndexError:
							if "http://static.ak.crunchyroll.com/i/coming_soon_new_thumb.jpg" in description:
								thumb = "http://static.ak.crunchyroll.com/i/coming_soon_new_thumb.jpg"
							else:
								thumb = "" # FIXME happens on newbie content, could be a bad idea b/c of cache.
							
						try: keywords = item.xpath("./media:keywords", namespaces=PLUGIN_NAMESPACE)[0].text
						except: keywords = ""
						availableResolutions = [] # this isn't available with rss script (it is with boxee_feeds)
						try:
							season = int(item.xpath("./crunchyroll:season", namespaces=PLUGIN_NAMESPACE)[0].text)
						except:
							season = None
							hasSeasons = False
						
						try:
							duration = int(item.xpath("./crunchyroll:duration", namespaces=PLUGIN_NAMESPACE)[0].text) * 1000
						except (ValueError, IndexError, TypeError):
							duration = -1
							
						try:
							category = item.xpath("./category", namespaces=PLUGIN_NAMESPACE)[0].text
						except IndexError:
							category = ""
							
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
							
						mediaType = item.xpath("./media:category", namespaces=PLUGIN_NAMESPACE)[0].get('label')
						episode = {
							"title": title,
							"link": link,
							"mediaId": mediaId,
							"description": stripHtml(description),
							"seriesTitle": seriesTitle,
							"episodeNum": episodeNum,
							"thumb": thumb,
							"availableResolutions": availableResolutions,
							"publisher": publisher,
							"season": season,
							"keywords": keywords,
							"type": mediaType,
							"rating": rating,
							"category": category
						}
						if duration > 0:
							episode['duration'] = duration
						
						try:
							#premiumPubDate = datetime.datetime.strptime(item.xpath("./crunchyroll:premiumPubDate", namespaces=PLUGIN_NAMESPACE)[0].text, "%a, %d %b %Y %H:%M:%S %Z")
							#episode['premiumPubDate'] = premiumPubDate
							pass
						except IndexError: pass
						
						try: 
							freePubDate = datetime.datetime.strptime(item.xpath("./crunchyroll:freePubDate", namespaces=PLUGIN_NAMESPACE)[0].text, "%a, %d %b %Y %H:%M:%S %Z")
							episode['freePubDate'] = freePubDate
						except IndexError: pass
						
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

def getEpisodeArt(episode):
	"""
	return the best background art URL for the passed episode.
	"""
	seriesId = None
	for sk in Dict['series'].keys():
		if Dict['series'][str(sk)]['title']==episode['seriesTitle']:
			seriesId = int(sk)
	if seriesId is not None:
		artUrl = ""
		if Dict['series'][str(seriesId)]['tvdbId'] is not None and Prefs['fanart'] is True:
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


def getThumb(url,tvdbId=None):
	"""
	Try to find a better thumb than the one provided via url.
	The thumb data returned is either an URL or the image data itself.
	"""
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
			except Exception, arg:
				Log.Error("#####Thumbnail couldn't be retrieved:")
				Log.Error("#####" + repr(Exception) + repr(arg) + url)
				ret = None

	if ret is None:
		return R(CRUNCHYROLL_ICON)
	else:
		return ret

def getThumbUrl(url, tvdbId=None):
	"""
	just get the best url instead of the image data itself.
	this can help 'larger thumbs missing' issue
	"""
	if (tvdbId is not None and Prefs['fanart'] is True):
		thumb = fanartScrapper.getRandImageOfTypes(tvdbId,['tvthumbs'])
		if thumb is not None: return thumb


	if url==R(CRUNCHYROLL_ICON):
		return url
	
	return url

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
		except Exception,arg: 
			Log.Error("####Exception when grabbing art at '%s'" % url)
			Log.Error(repr(Exception) + repr(arg))
		

	if ret is None:
		req = urllib2.Request("http://127.0.0.1:32400"+R(CRUNCHYROLL_ART))
		return DataObject(urllib2.urlopen(req).read(), 'image/jpeg')
	else:
		return ret


def getSeasonThumb(tvdbId, season, rand=True):
	"""
	pass it along to fanart scrapper
	"""
	return fanartScrapper.getSeasonThumb(tvdbId, season, rand)

def stripHtml(html):
	"""
	return a string stripped of html tags
	"""
	# kinda works
	res = html.replace("&lt;", "<")
	res = res.replace("&gt;", ">")
	res = re.sub(r'<[^>]+>', '', res)
	return res
	
def formateEpList(epList,hasSeasons):
	sortedEpList = sorted(epList, key=lambda k: k['episodeNum'])
	output = {}
	if SPLIT_LONG_LIST is True and hasSeasons is True and len(sortedEpList) > 50:
		seasonList = {}
		for e in sortedEpList:
			s = e['season']
			if s not in seasonList:
				seasonList[s] = []
			seasonList[s].append(e)
		output['seasons'] = seasonList
		output['useSeasons'] = True
	else:
		output['useSeasons'] = False
		output['episodeList'] = sortedEpList
	return output


def getSeasonEpisodeListFromFeed(seriesId,season):
	tmp = getEpisodeListForSeries(seriesId)
	if season == "all":
		epList = []
		for s in tmp['seasons'].keys():
			for e in tmp['seasons'][s]:
				epList.append(e)
	else:
		epList = tmp['seasons'][season]
	return epList


def getVideoInfo(baseUrl, mediaId, availRes):

	if not mediaId:
		#occasionally this happens, so make sure it's noisy
		raise Exception("#####getVideoInfo(): NO MEDIA ID, SORRY!")
		
	url = "http://www.crunchyroll.com/xml/?req=RpcApiVideoPlayer_GetStandardConfig&media_id=%s&video_format=102&video_quality=10&auto_play=1&show_pop_out_controls=1&pop_out_disable_message=Only+All-Access+Members+and+Anime+Members+can+pop+out+this" % mediaId
	html = HTML.ElementFromURL(url)
	episodeInfo = {}
	episodeInfo['baseUrl'] = baseUrl
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



def getAvailResFromPage(url):
	"""
	given an url of a page where video is watched,
	return a list of integers of available heights.
	
	If user is a guest, just return 360, which
	is all they get ;-)
	"""
	
	if not Prefs['username'] or not Prefs['password']:
		return [360]

	login()

	availRes = [360]
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


def getPrefRes(availRes):

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

def getEpInfoFromLink(link):
	#FIXME currently this works fine for Queue items, which include
	# the title in the link, but should fail horribly
	# with "www.crunchyroll.com/media-45768" style links
	# which are given by feedburner, et. al.
	# furthermore, rss feeds that we use to populate the Dict{} may not contain all episodes.
	mediaId = getVideoMediaIdFromLink(link)
	if not str(mediaId) in Dict['episodes']:
		seriesname = link.split(".com/")[1].split("/")[0]
		url = seriesTitleToUrl(seriesname)
		getEpisodeListFromFeed(url)
	episode = Dict['episodes'][str(mediaId)]
	return episode


def seriesTitleToUrl(title):
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


def getVideoMediaIdFromLink(link):
	mtmp = link.split(".com/")[1].split("/")[1].split("-")
	mediaId = int(mtmp[len(mtmp)-1])
	return mediaId


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


def getMetadataFromUrl(url):
	episodeId = url.split(".com/")[1].split("/")[1].split("-")
	episodeId = episodeId[len(episodeId)-1]
	if not str(episodeId) in Dict['episodes']:
		seriesName=url.split(".com/")[1].split("/")[0]
		getEpisodeListFromFeed(BASE_URL+"/%s.rss"%seriesName)
	episodeData = Dict['episodes'][str(episodeId)]
	metadata = {
		"title": episodeData['title']
	}
	return metadata
