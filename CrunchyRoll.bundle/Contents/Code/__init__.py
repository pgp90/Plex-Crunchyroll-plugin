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

LAST_PLAYER_VERSION = "20111118183226.fb103f9787f179cd0f27be64da5c23f2"

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

GET_EXTRA_INFO = True

USE_LOGIN_AT_START = True

USE_DURATION = True

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


def CreatePrefs():
	Prefs.Add(id='loginemail', type='text', default="", label='Login Email')
	Prefs.Add(id='password', type='text', default="", label='Password', option='hidden')
	Prefs.Add(id='quality', type='enum', values=["SD", "480P", "720P", "Highest Avalible"], default="Highest Avalible", label="Quality")
	Prefs.Add(id='thumb_quality', type='enum', values=["Low", "Medium", "High"], default="High", label="Thumbnail Quality")
	Prefs.Add(id='restart', type='enum', values=["Resume", "Restart"], default="Restart", label="Resume or Restart")


def LoginNotBlank():
	r = False
	if Prefs['username'] is not None and Prefs['password'] is not None:
		r = True
	return r


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
	#dir.Append(Function(DirectoryItem(Menu,"Browse Queue", thumb=R(QUEUE_ICON)), type="Queue"))
	dir.Append(PrefsItem(L('Preferences'), thumb=R(PREFS_ICON)))
	#dir.nocache = 1
	
	return dir

"""
def getRtmpStreamInfo(url):
	data = HTML.ElementFromURL(url)
	stream_info = data.xpath("//stream_info")
	if stream_info:
		try:
			host = stream_info.xpath("./host")[0].text
			clipFile = stream_info.xpath("./file")[0].text
			token = stream_info.xpath("./token")[0].text
			page_url
			swf_url = "http://static.lln.crunchyroll.com/flash/"+returnPlayer+"/"+player_url
			try:
				app = host.split('.net/')
				stream['app'] = app[1]
				#print "CRUNCHYROLL: --> App - " + stream['app']
			except:
				pass
		
			useSubs = False
			mediaid = vid_id
			subtitles = data.xpath("//subtitles")[0]
			#print "CRUNCHYROLL: --> Attempting to find subtitles..."
			if(subtitles):
				#print "CRUNCHYROLL: --> Found subtitles.  Continuing..."
				#impliment the decoder
				formattedSubs = crunchyDec().returnSubs(xmlSource)
				#find the plex equivalant to the .translatePath()
				subfile = open(xbmc.translatePath('special://temp/crunchy_'+mediaid+'.ass'), 'w')
				subfile.write(formattedSubs.encode('utf-8'))
				subfile.close()
				useSubs = True
			else:
				#print "CRUNCHYROLL: --> No subtitles available!"
				mediaid = ""
		
			self.playvideo(stream, mediaid, useSubs)
		except:
			if stream_info.find('upsell'):
				if stream_info.upsell.string == '1':
					ex = 'XBMC.Notification("Video restricted:","Video not available to your user account.", 3000)'
					xbmc.executebuiltin(ex)
					print "CRUNCHYROLL: --> Selected video quality is not available to your user account."
			elif stream_info.find('error'):
				if stream_info.error.code.string == '4':
					ex = 'XBMC.Notification("Mature Content:","Please login to view this video.", 3000)'
					xbmc.executebuiltin(ex)
					print "CRUNCHYROLL: --> This video is marked as Mature Content.  Please login to view it."
	else:
		print "Playback Failed!"


def playvideo(self, stream, mediaid, useSubs):
	rtmp_url = stream['url']+stream['file'].replace('&amp;','&') + " swfurl=" +stream['swf_url'] + " swfvfy=1 token=" +stream['token']+ " playpath=" +stream['file'].replace('&amp;','&')+ " pageurl=" +stream['page_url'] 
	item = xbmcgui.ListItem(stream['episode_display'])
	item.setProperty('IsPlayable', 'true')
	
	if(useSubs == True):
		print "CRUNCHYROLL: --> Playing video and setting subtitles to special://temp/crunchy_"+mediaid+".ass"
		xbmc.Player().play(rtmp_url)
		xbmc.Player().setSubtitles(xbmc.translatePath('special://temp/crunchy_'+mediaid+'.ass'))
	else:
		xbmc.Player().play(rtmp_url, item)

"""

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


def getShowsOnPage(url):
	listPage = HTML.ElementFromURL(url)
	items = listPage.xpath("//li[@class='clearfix'and@itemtype='http://schema.org/TVSeries']")
	showList = []
	for item in items:
		title = item.xpath(".//strong[@itemprop='name']")[0].text
		thumb = item.xpath(".//img[@itemprop='photo']")[0].get('src')
		href = item.xpath(".//a")[0].get('href')
		if href.startswith("http") == False:
		            href = BASE_URL + href
		
		rating = int(float(item.xpath(".//span[@class='ratings-widget']/span")[0].get('content'))*2)
		
		subData = item.xpath(".//noscript")[0]
		
		description = subData.xpath(".//p[1]")[0].text
		art = subData.xpath(".//img")[0].get('src')
		
		#episodes = ''
		#try:
		#	episodes = subData.xpath("./p[strong=='Episodes:']")[0].text
		#except:
		#	pass
		
		#genres = ''
		#try:
		#	genres = subData.xpath("./p[strong=='Tags:']")[0].text
		#except:
		#	pass
		
		#year = ''
		#try:
		#	year = subData.xpath("./p[strong=='Year:']")[0].text
		#except:
		#	pass
		
		show = {
			"title": title,
			"thumb": thumb,
			"art": art,
			"href": href,
			"description": description,
			#"duration": 25*60000,
			#"episodes": episodes,
			#"genres": genres,
			#"year": year,
			"rating": rating
		}
		showList.append(show)
		
	return showList


def getShowsOnPageAlpha(url, startsWith=None):
	if startsWith is None:
		showList = getShowsOnPage(url);
	else:
		listPage = HTML.ElementFromURL(url)
		items = listPage.xpath("//li[@class='clearfix'and@itemtype='http://schema.org/TVSeries']")
		#Log.Debug("number of items on the page: %d" % len(items))
		#Log.Debug(listPage.xpath("//li[@class='clearfix'and@itemtype='http://schema.org/TVSeries']//strong[@itemprop='name']//text()"))
		showList = []
		for item in items:
			title = item.xpath(".//strong[@itemprop='name']")[0].text.strip()
			if title.startswith(startsWith):
				thumb = item.xpath(".//img[@itemprop='photo']")[0].get('src')
				href = item.xpath(".//a")[0].get('href')
				if href.startswith("http") == False:
				            href = BASE_URL + href
				
				rating = int(float(item.xpath(".//span[@class='ratings-widget']/span")[0].get('content'))*2)
				
				subData = item.xpath(".//noscript")[0]
				
				description = subData.xpath(".//p[1]")[0].text
				art = subData.xpath(".//img")[0].get('src')
				
				#episodes = ''
				#try:
				#	episodes = subData.xpath("./p[strong=='Episodes:']")[0].text
				#except:
				#	pass
				
				#genres = ''
				#try:
				#	genres = subData.xpath("./p[strong=='Tags:']")[0].text
				#except:
				#	pass
				
				#year = ''
				#try:
				#	year = subData.xpath("./p[strong=='Year:']")[0].text
				#except:
				#	pass
				
				show = {
					"title": title,
					"thumb": thumb,
					"art": art,
					"href": href,
					"description": description,
					#"duration": 25*60000,
					#"episodes": episodes,
					#"genres": genres,
					#"year": year,
					"rating": rating
				}
				showList.append(show)
				
	return showList


def getShowInfo(url):
	showPage = HTML.ElementFromURL(url)
	
	description = showPage.xpath("//div[@class='series-section clearfix']/span[@itemprop='description']")[0].text
	
	detailedInfo = showPage.xpath("//ul[@class='series-detailed']")
	
	genres = detailedInfo.xpath("./li[@class='series-tags']/a").text
	episodes = detailedInfo.xpath("./li[strong=='Episodes:']/string()")[0]
	publisher = detailedInfo.xpath("./li[strong=='Publisher:']/string()")[0]
	year = detailedInfo.xpath("./li[strong=='Year:']/string()")[0]
	
	detailedDescription = ""
	detailedDescriptionParts = showPage.xpath("//div[@class='series-section clearfix'][5]")
	for part in detailedDescriptionParts:
		detailedDescription = ("%s\n\n%s" % (detailedDescription, part))
	
	showInfo = {
		"description": description,
		"genres": genres,
		"episodes": episodes,
		"publisher": publisher,
		"year": year,
		"detailedDescription": detailedDescription
	}
	return showInfo


def genEpRssUrlFromName(seriesName):
	url = "http://www.crunchyroll.com/"
	name = seriesName.lower().replace(" ", "-")
	toRemove = ["!", "'", ",", ".", "?", "&", "@", "#", "$", "%", "^", "*", "(", ")"]
	for char in toRemove:
		name = name.replace(char, "")
	url = url + name + ".rss"
	return url


def genEpRssUrlFromUrl(feedurl):
	url = "http://www.crunchyroll.com/"
	id = feedurl.split("showseries/")[1]
	url = "http://www.crunchyroll.com/syndication/feed?type=episodes&group_id=%s" % id
	return url


def getEpisodesList(url):
	showFeed = HTML.ElementFromURL(url)
	art = showFeed.xpath("//channel/image/url")[0].text
	items = showFeed.xpath("//channel/item")
	episodes = []
	#for num in range(1, len(items) + 1):
	#	episodes.append(num)
	series_name = showFeed.xpath("//channel/title")[0].text
	if " Episodes" in series_name:
		series_name = series_name.replace(" Episodes", "")
	for item in items:
		#subs = []
		#for sub in list(item):
		#	subs.append(sub.tag)
		#	if sub.tag=="link" or sub.tag=="guid":
		#		Log.Debug("sub: %s" % sub)
		#		Log.Debug("sub.text: %s" % sub.xpath("./string"))
		#		Log.Debug("sub.tag: %s" % sub.tag)
		#		for subb in list(sub):
		#			Log.Debug("subb.text: %s" % subb.text)
		#			Log.Debug("subb.tag: %s" % subb.tag)
		#Log.Debug(subs)
		try:
			duration = int(item.xpath("./duration")[0].text)*1000
			title = item.xpath("./title")[0].text
			href = item.xpath("./link/string")#[0].text
			guid = item.xpath("./guid")[0].text
			description = item.xpath("./description")[0].text
			if "/&gt;&lt;br /&gt;" in description:
				description = description.split("/&gt;&lt;br /&gt;")[1]
			elif "><br />" in description:
				description = description.split("><br />")[1]
			pubDate = item.xpath("./pubdate")[0].text
			episodeNumber = int(item.xpath("./episodenumber")[0].text)
			publisher = item.xpath("./publisher")[0].text
			seasonNumber = item.xpath("./season")[0].text
			contentRating = item.xpath("./rating")[0].text
			thumb = item.xpath("./thumbnail")[0].get('url')
			keywords = item.xpath("./keywords")[0].text
			href = ("http://www.crunchyroll.com/%s/episode-%s-%s" % (series_name, episodeNumber, guid.split("media-")[1]))
			
			#Log.Debug("episode number: %s" % episodeNumber)
			#Log.Debug("getEpisodesList href: %s" % href)
			
			episode = {
				"title": title,
				"series_name": series_name,
				"href": href,
				"guid": guid,
				"description": description,
				"pubDate": pubDate,
				"episodeNumber": episodeNumber,
				"duration": duration,
				"publisher": publisher,
				"seasonNumber": seasonNumber,
				"contentRating": contentRating,
				"thumb": thumb,
				"keywords": keywords,
				"art": art
			}
			
			#index = episodes.index(int(episodeNumber))
			#episodes.remove(index)
			#episodes.insert(index, episode)
			episodes.append(episode)
		except:
			pass
	
	newlist = sorted(episodes, key=lambda k: k['episodeNumber'])
	
	#tmp = []
	#for ep in newlist:
	#	tmp.append(ep['episodeNumber'])
	#Log.Debug(tmp)
	
	return newlist


def makeWebShowItem(show):
	webShowItem = Function(
		DirectoryItem(
			ShowMenu,
			show['title'],
			summary=show['description'],
			thumb=show['thumb'],
			art=show['art'],
			#duration=show['duration'],
			rating=show['rating'],
		),
		show['href']
	)
	return webShowItem


def makeWebVideoItem(episode):
	#Log.Debug("mWVI url: %s" % episode['guid'])
	infoLabel = msToRuntime(episode['duration'])
	dirItem = Function(
		DirectoryItem(
			BuildPlayerUrl,
			episode['title'],
			summary=episode['description'],
			subtitle='',
			duration=episode['duration'],
			thumb=episode['thumb'],
			art=episode['art'],
			#rating=episode['rating'],
			infoLabel=infoLabel
		),url="%s" % episode['guid']
	)
	return dirItem


def AlphaListMenu(sender,type=None,query=None):
	if query is not None:
		if query=="#":
			queryCharacters = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')
		elif query=="All":
			queryCharacters = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z')
		else:
			queryCharacters = (query.lower(), query.upper())
		
		#listRoot = BASE_URL + "/" + type.lower()
		
		dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2=query)
		
		#mainListPage = HTML.ElementFromURL(listRoot)
		#lastPage = int(mainListPage.xpath("//div[@class='%s-paginator clearfix'][1]//a[@class='paginator-lite'and@title='Last']" % type.lower())[0].get('href').split("=")[1])
		#showList = []
		#for pageNum in range(lastPage + 1):
		#	#showList.extend(getShowsOnPageAlpha("%s?pg=%d" % (listRoot, pageNum), queryCharacters))
		#	showList.extend(getShowsOnPageAlpha("%s?pg=%d" % (listRoot, pageNum), queryCharacters))
		
		if type=="Anime":
			seriesList = getSeriesListFromFeed("genre_anime_all")
		else:
			seriesList = getSeriesListFromFeed("drama")
		
		for series in seriesList:
			if series['title'].startswith(queryCharacters):
				dir.Append(makeSeriesItem(series))		
		#Log.Debug(len(dir))
		
	else:
		dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2=sender.itemTitle)
		characters = ['All', '#', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
		for character in characters:
			dir.Append(Function(DirectoryItem(AlphaListMenu,"%s" % character, thumb=R(CRUNCHYROLL_ICON)), type=type, query=character))
	return dir


def PopularListMenu(sender,type=None):
	listRoot = BASE_URL + "/" + type.lower()
		
	dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2="Popular")
	
	#mainListPage = HTML.ElementFromURL(listRoot)
	#lastPage = int(mainListPage.xpath("//div[@class='%s-paginator clearfix'][1]//a[@class='paginator-lite'and@title='Last']" % type.lower())[0].get('href').split("=")[1])
	#showList = []
	#for pageNum in range(lastPage + 1):
	#	showList.extend(getShowsOnPage("%s?pg=%d" % (listRoot, pageNum)))
	
	seriesList = getSeriesListFromFeed("anime_popular")
		
	for series in seriesList:
		dir.Append(makeSeriesItem(series))
		
	#Log.Debug(len(dir))
		
	return dir


def GenreListMenu(sender,type=None,query=None):
	if type=="Anime":
		genreList = ANIME_GENRE_LIST
	else:
		genreList = DRAMA_GENRE_LIST
	
	if query is not None:
		dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2=query)
		queryStr = genreList[query].replace('_', '%20')
		#Log.Debug("queryStr: %s" % queryStr)
		#Log.Debug("type: %s" % type)
		feed = "anime_withtag/" + queryStr
		#Log.Debug("feed: %s" % feed)
		#listElt(feed)
		seriesList = getSeriesListFromFeed(feed)
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
	#Log.Debug("url: %s" % url)
	
	if LoginNotBlank():
		loggedin = LoggedIn()
		#Log.Debug("BuildPlayerUrl - loggedIn: %s" % loggedin)
		if not loggedin:
			Login()
	
	episodes = getEpisodeListFromFeed(url)
	for episode in episodes:
		dir.Append(makeEpisodeItem(episode))
	#Log.Debug(len(dir))
	return dir


def getSeriesFeedUrlFromMediaId(mediaId):
	url = "showseries/%s" % mediaId
	return url


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


def getSeriesListFromFeed(feed):
	feedURL = FEED_BASE_URL+feed
	feedHtml = HTML.ElementFromURL(feedURL)
	seriesList = []
	items = feedHtml.xpath("//item")
	for item in items:
		title = item.xpath("./title")[0].text
		mediaId = int(item.xpath("./guid")[0].text.split(".com/")[1])
		description = item.xpath("./description")[0].text
		thumb = str(item.xpath("./property")[0].text).replace("_large",THUMB_QUALITY[Prefs['thumb_quality']])
		
		series = {
			"title": title,
			"mediaId": mediaId,
			"description": description,
			"thumb": thumb
		}
		seriesList.append(series)
	sortedSeriesList = sorted(seriesList, key=lambda k: k['title'])
	return sortedSeriesList


def getEpisodeInfoFromPlayerXml(mediaId):
	try:
		if LoginNotBlank():
			loggedin = LoggedIn()
			#Log.Debug("BuildPlayerUrl - loggedIn: %s" % loggedin)
			if not loggedin:
				Login()
		
		url = "http://www.crunchyroll.com/xml/?req=RpcApiVideoPlayer_GetStandardConfig&media_id=%s&video_format=102&video_quality=10&auto_play=1&show_pop_out_controls=1&pop_out_disable_message=Only+All-Access+Members+and+Anime+Members+can+pop+out+this" % mediaId
		#Log.Debug("getEpisodeInfoFromPlayerXml url: %s" % url)
		html = HTML.ElementFromURL(url)
		#debugFeedItem(html)
		episodeInfo = {}
		#episodeInfo['videoFormat'] = html.xpath("//videoformat")[0].text
		#episodeInfo['backgroundUrl'] = html.xpath("//backgroundurl")[0].text
		episodeInfo['initialVolume'] = int(html.xpath("//initialvolume")[0].text)
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
	except:
		episodeInfo = None
	return episodeInfo


def getEpisodeListFromFeed(feed):
	episodeList = []
	if USING_BOXEE_FEEDS:
		if LoginNotBlank():
			loggedin = LoggedIn()
			#Log.Debug("BuildPlayerUrl - loggedIn: %s" % loggedin)
			if not loggedin:
				Login()
		
		feedURL = FEED_BASE_URL+feed
		feedHtml = XML.ElementFromURL(feedURL)
		items = feedHtml.xpath("//item")
		for item in items:
			PLUGIN_NAMESPACE   = {'boxee':'http://boxee.tv/rss', 'media':"http://search.yahoo.com/mrss/"}
			#debugFeedItem(item)
			title = item.xpath("./title")[0].text
			link = item.xpath("./guid")[0].text
			mediaIdTmp = item.xpath("./guid")[0].text.split("-")
			mediaId = int(mediaIdTmp[len(mediaIdTmp)-1])
			description = item.xpath("./description")[0].text
			seriesTitle = item.xpath("./boxee:property[@name='custom:seriesname']", namespaces=PLUGIN_NAMESPACE)[0].text
			#Log.Debug("epNum: %s" % item.xpath("./boxee:property[@name='custom:episodenum']", namespaces=PLUGIN_NAMESPACE))
			#Log.Debug("epNum: %s" % item.xpath("./boxee:property[@name='custom:episodenum']", namespaces=PLUGIN_NAMESPACE)[0].text.replace("Episode ", ""))
			try:
				#Log.Debug("ep num text: %s" % item.xpath("./boxee:property[@name='custom:episodenum']", namespaces=PLUGIN_NAMESPACE)[0].text)
				episodeNum = int(item.xpath("./boxee:property[@name='custom:episodenum']", namespaces=PLUGIN_NAMESPACE)[0].text.replace("Episode ", ""))
			except:
				tmp = link.replace(BASE_URL, "")
				tmp = tmp.split("/")[1]
				if "/episode-" in tmp:
					episodeNum = int(tmp.split("-")[1])
				elif "episode" in title.lower():
					episodeNum = int(title.lower().split(" ")[1])
				else:
					episodeNum = None
			thumb = str(item.xpath("./media:thumbnail", namespaces=PLUGIN_NAMESPACE)[0].get('url')).replace("_large",THUMB_QUALITY[Prefs['thumb_quality']])
			availableResolutions = item.xpath("./boxee:property[@name='custom:available_resolutions']", namespaces=PLUGIN_NAMESPACE)[0].text.replace(" ", "").split(",")
			
			if GET_EXTRA_INFO:
				extraInfo = getEpisodeInfoFromPlayerXml(mediaId)
				if extraInfo is not None:
					duration = int(float(extraInfo['duration'])*1000)
					if episodeNum is None and extraInfo['episodeNum'] is not None:
						episodeNum = int(extraInfo['episodeNum'])
				else:
					duration = 1800000
			else:
				duration = 1800000
			
			publisher = ""
			season = ""
			keywords = ""
			episode = {
				"title": title,
				"link": link,
				"mediaId": mediaId,
				"description": description,
				"seriesTitle": seriesTitle,
				"episodeNum": episodeNum,
				"thumb": thumb,
				"availableResolutions": availableResolutions,
				"duration": duration,
				"publisher": publisher,
				"season": season,
				"keywords": keywords
			}
			episodeList.append(episode)
	else:
		PLUGIN_NAMESPACE   = {"media":"http://search.yahoo.com/mrss/", "crunchyroll":"http://www.crunchyroll.com/rss"}
		#Log.Debug("feed: %s" % feed)
		feedHtml = XML.ElementFromURL(feed)
		items = feedHtml.xpath("//item")
		seriesTitle = feedHtml.xpath("//channel/title")[0].text.replace(" Episodes", "")
		Log.Debug(seriesTitle)
		#seriesImage = feedHtml.xpath("//channel/image/url")[0].text
		#seriesRating = feedHtml.xpath("//channel/rating")[0].text
		for item in items:
			#debugFeedItem(item)
			title = item.xpath("./title")[0].text
			if title.startswith("%s - " % seriesTitle):
				title = title.replace("%s - " % seriesTitle, "")
			link = item.xpath("./link")[0].text
			mediaId = int(item.xpath("./guid")[0].text.split("-")[1])
			description = item.xpath("./description")[0].text
			if "/><br />" in description:
				description = description.split("/><br />")[1]
			try:
				episodeNum = int(item.xpath("./crunchyroll:episodeNumber", namespaces=PLUGIN_NAMESPACE)[0].text)
			except:
				episodeNum = None
			duration = int(item.xpath("./crunchyroll:duration", namespaces=PLUGIN_NAMESPACE)[0].text)*1000
			publisher = item.xpath("./crunchyroll:publisher", namespaces=PLUGIN_NAMESPACE)[0].text
			thumb = str(item.xpath("./media:thumbnail", namespaces=PLUGIN_NAMESPACE)[0].get('url')).replace("_large",THUMB_QUALITY[Prefs['thumb_quality']])
			keywords = item.xpath("./media:keywords", namespaces=PLUGIN_NAMESPACE)[0].text
			availableResolutions = ["12"]
			season = ""#item.xpath("./season")[0].text
			episode = {
				"title": title,
				"link": link,
				"mediaId": mediaId,
				"description": description,
				"seriesTitle": seriesTitle,
				"episodeNum": episodeNum,
				"thumb": thumb,
				"availableResolutions": availableResolutions,
				"duration": duration,
				"publisher": publisher,
				"season": season,
				"keywords": keywords
			}
			episodeList.append(episode)
	sortedEpisodeList = sorted(episodeList, key=lambda k: k['episodeNum'])
	#Log.Debug("episodeNum: %s" % sortedEpisodeList[0]['episodeNum'])
	return sortedEpisodeList


def getVideoUrlForQuality(baseUrl, availableResolutions):
	availRes = availableResolutions
	if not USING_BOXEE_FEEDS:
		if LoggedIn():
			req = HTTP.Request(url=baseUrl, immediate=True, cacheTime=3600)
			link = baseUrl.replace(BASE_URL, "")
			r1a = '<a href="%s?p360=1" token="showmedia.360p" class="showmedia-res-btn" title="Standard Definition">SD</a>' % link
			r1b = '<a href="%s?p360=1" token="showmedia.360p" class=" showmedia-res-btn-selected" title="Standard Definition">SD</a>' % link
			r2a = '<a href="%s?p480=1" token="showmedia.480p" class="showmedia-res-btn" title="480P">480P</a>' % link
			r2b = '<a href="%s?p480=1" token="showmedia.480p" class=" showmedia-res-btn-selected" title="480P">480P</a>' % link
			r3a = '<a href="%s?p720=1" token="showmedia.720p" class="showmedia-res-btn" title="720P">720P</a>' % link
			r3b = '<a href="%s?p720=1" token="showmedia.720p" class=" showmedia-res-btn-selected" title="720P">720P</a>' % link
			if r2a in req.content or r2b in req.content:
				availRes.append("20")
			if r3a in req.content or r3b in req.content:
				availRes.append("21")
	#Log.Debug("avail res: %s" % availRes)
	resNames = {"12":'SD', "20":'480P', "21":'720P'}
	availResNames = []
	for resN in availRes:
		availResNames.append(resNames[resN])
	if Prefs['quality'] == "Highest Avalible":
		resName = availResNames[len(availRes)-1]
	else:
		if Prefs['quality'] in availResNames:
			resName = Prefs['quality']
		else:
			resName = availResNames[len(availRes)-1]
	
	url = baseUrl+"?p"+VIDEO_QUALITY[resName]+"=1"
	#Log.Debug("qualityUrl: %s" % url)
	return url


def parseSeries(url):
	listPage = HTML.ElementFromURL(url)
	items = listPage.xpath("//item")
	seriesList = []
	for item in items:
		title = item.xpath("./title")[0].text
		guid = item.xpath("./guid")[0].text
		if guid.startswith("http") == False:
			guid = BASE_URL + guid
		link = FEED_BASE_URL + "showseries/" + guid.split(".com/")[1]
		description = item.xpath("./description")[0].text
		thumb = str(item.xpath("./property")[0].text).replace("_large",THUMB_QUALITY[Prefs['thumb_quality']])
		
		show = {
			"title": title,
			"guid": guid,
			"link": link,
			"description": description,
			"thumb": thumb
		}
		seriesList.append(show)
		
	return seriesList


def parseEpisodes(url):
	if USE_DURATION==False:
		episode_list = []
		listPage = HTML.ElementFromURL(url)
		items = listPage.xpath("//item")
		missingEpNums = False
		for item in items:
			#subs = []
			#for sub in list(item):
			#	subs.append(sub.tag)
			#	subs.append(sub.text)
			#	if sub.tag=="link" or sub.tag=="guid":
			#		Log.Debug("sub: %s" % sub)
			#		Log.Debug("sub.text: %s" % sub.text)
			#		Log.Debug("sub.tag: %s" % sub.tag)
			#		for subb in list(sub):
			#			Log.Debug("subb.text: %s" % subb.text)
			#			Log.Debug("subb.tag: %s" % subb.tag)
			#Log.Debug(subs)
			title = item.xpath("./title")[0].text
			series_name = item.xpath("./property[@name='custom:seriesname']")[0].text
			description = item.xpath("./description")[0].text
			thumb = str(item.xpath("./thumbnail")[0].get('url')).replace("_large",THUMB_QUALITY[Prefs['thumb_quality']])
			guid = item.xpath("./guid")[0].text
			pubdate = item.xpath("./pubdate")[0].text
			pubdate = time.strptime(pubdate, "%a, %d %b %Y %H:%M:%S")
			try:
				premium_only = item.xpath("./property[@name='custom:premium_only']")[0].text
			except:
				premium_only = ""
			try:
				available_resolutions = item.xpath("./property[@name='custom:available_resolutions']")[0].text
			except:
				available_resolutions = "12"
			try:
				episode_number = int(item.xpath("./property[@name='custom:episodenum']")[0].text)
			except:
				tmp = guid.replace(BASE_URL, "")
				tmp = tmp.split("/")[1]
				if "episode" in tmp:
					episode_number = int(tmp.split("-")[1])
				else:
					episode_number = None
					missingEpNums = True
		
			episode = {
				"title": title,
				"series_name": series_name,
				"description": description,
				"thumb": thumb,
				"guid": guid,
				"premium_only": premium_only,
				"available_resolutions": available_resolutions,
				"episode_number": episode_number,
				"pubdate": pubdate,
				"duration": None
			}
			episode_list.append(episode)
		if missingEpNums:
			sorted_episode_list = sorted(episode_list, key=lambda k: k['pubdate'])
		else:
			sorted_episode_list = sorted(episode_list, key=lambda k: k['episode_number'])
		return sorted_episode_list
	else:
		episode_lista = getEpisodesList(genEpRssUrlFromUrl(url))
		episode_list = []
		for episode in episode_lista:
			episode2 = {
				"title": episode['title'],
				"series_name": episode['series_name'],
				"description": episode['description'],
				"thumb": episode['thumb'],
				"guid": episode['href'],
				#"premium_only": episode['premium_only'],
				"available_resolutions": "",#episode['available_resolutions'],
				"episode_number": int(episode['episodeNumber']),
				"duration": int(episode['duration'])
			}
			episode_list.append(episode2)
		sorted_episode_list = sorted(episode_list, key=lambda k: k['episode_number'])
		return sorted_episode_list


def makeSeriesItem(series):
	if USING_BOXEE_FEEDS:
		url = getSeriesFeedUrlFromMediaId(series['mediaId'])
	else:
		seriesname = series['title']
		toremove = ["!", ":", "'", "?", ".", ",", "(", ")", "&", "@", "#", "$", "%", "^", "*"]
		for char in toremove:
			seriesname = seriesname.replace(char, "")
		seriesname = seriesname.replace("  ", " ").replace(" ", "-").lower()
		url = "%s/%s.rss" % (BASE_URL, seriesname)
	#Log.Debug("Url: %s" % url)
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


def makeEpisodeItem(episode):
	#Log.Debug("mEI url: %s" % episode['link'])
	if LoginNotBlank():
		loggedin = LoggedIn()
		#Log.Debug("BuildPlayerUrl - loggedIn: %s" % loggedin)
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
		summary = summary+"\n"+episode['description']
	else:
		summary = episode['description']
	episodeItem = WebVideoItem(
	            getVideoUrlForQuality(episode['link'],episode['availableResolutions']),
	            title = episode['title'],
	            subtitle = episode['season'],
	            summary = summary,
	            thumb = episode['thumb'],
				duration = episode['duration']
	)
	return episodeItem


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


"""
def makeEpisodeItem(episode):
	Log.Debug("mEI url: %s" % episode['guid'])
	#infoLabel = msToRuntime(episode['duration'])
	loggedin = LoggedIn2()
	Log.Debug("BuildPlayerUrl - loggedIn: %s" % loggedin)
	#if not loggedin:
	#	Login()
	
	dirItem = WebVideoItem(
	            episode['guid'],
	            title = episode['title'],
	            subtitle = '',
	            summary = episode['description'],
	            thumb = episode['thumb'],
				duration = episode['duration']
	)
	#dirItem = Function"("
	#	DirectoryItem"("
	#		BuildPlayerUrl,
	#		episode['title'],
	#		summary=episode['description'],
	#		subtitle='',
	#		thumb=episode['thumb'],
	#		art=episode['thumb']#,
	#		#infoLabel=infoLabel
	#	),url="%s" % episode['guid'],available_resolutions="%s" % episode['available_resolutions']
	#)
	return dirItem


def BuildPlayerUrl(sender,url='',available_resolutions='12,20,21'):
	loggedin = LoggedIn()
	Log.Debug("BuildPlayerUrl - loggedIn: %s" % loggedin)
	if not loggedin:
		Login()
	
	Log.Debug("BuildPlayerUrl: %s" % url)
	wvi = WebVideoItem(url)
	Log.Debug("wvi: %s" % wvi)
	#return Redirect(wvi)
	return wvi

"""

def msToRuntime(ms):
	
    if ms is None or ms <= 0:
        return None
		
    ret = []
	
    sec = int(ms/1000) % 60
    min = int(ms/1000/60) % 60
    hr  = int(ms/1000/60/60)
	
    return "%02d:%02d:%02d" % (hr,min,sec)

	
