import tvdbscrapper, fanartScrapper

"""
schema
	all items (even movies) can be referenced by a the series dict.
	series are known by seriesID (a unique number), provided by crunchyroll.com
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
	'371594': {'seriesTitle': 'Egg Man', 
		'publisher': 'T.O Entertainment', 
		'mediaId': 371594, 
		'description': 'few images of the movie Egg Man\r\n ', 
		'episodeNum': None, 
		'rating': 1, 
		'season': None, 
		'title': 'Egg Man Trailer 1', 
		'link': 'http://www.crunchyroll.com/egg-man/-egg-man-egg-man-trailer-1-371594'
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

Boxee2Resolution = {'12':360, '20':480, '21':720}
Quality2Resolution = {"SD":360, "480P":480, "720P":720, "1080P": 1080, "Highest Available":1080, "Ask":360}

def getQueueList():
	Login()
	queueURL = BASE_URL+"/queue"
	queueHtml = HTML.ElementFromURL(queueURL,cacheTime=QUEUE_LIST_CACHE_TIME)
	queueList = []
	items = queueHtml.xpath("//div[@class='queue-container clearfix']/ul[@id='sortable']/li")
	for item in items:
		title = item.xpath("./div[@class='title']/a")[0].text.replace("\\\\","").lstrip("\n ").rstrip(" ")
		seriesId = int(item.xpath(".")[0].get('id').replace("queue_item_",""))
		try: epToPlay = BASE_URL+"/"+item.xpath("./div[@class='play']/button")[0].get('onclick').replace("window.location=\"\\/","").split("?t=")[0].replace("\\/","/")
		except: epToPlay = None
		try: seriesStatus = item.xpath("./div[@class='status']/span")[0].text.lstrip("\n ").rstrip(" ")
		except: seriesStatus = item.xpath("./div[@class='status']")[0].text.lstrip("\n ").rstrip(" ")
		if "Complete" in seriesStatus:
			seriesStatus = "Complete"
		else:
			seriesStatus = "Ongoing"
		queueItem = {
			"title": title,
			"seriesId": seriesId,
			"epToPlay": epToPlay,
			"seriesStatus": seriesStatus
		}
		queueList.append(queueItem)
	return queueList


def cacheAllSeries():
	#startTime = Datetime.Now()
	seriesDict = Dict['series']
	for feed in ["genre_anime_all", "drama"]:
		feedHtml = HTML.ElementFromURL(FEED_BASE_URL+feed,cacheTime=SERIES_FEED_CACHE_TIME)
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


def getSeriesListFromFeed(feed):
	#startTime = Datetime.Now()
	feedURL = FEED_BASE_URL+feed
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
	sortedSeriesList = sorted(seriesList, key=lambda k: k['title'])
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
	#Log.Debug("Dict['episodes']: %s"%Dict['episodes'])
	if str(seriesId) not in Dict['series']:
		cacheAllSeries()
	seriesData = Dict['series'][str(seriesId)]
	if seriesData['epList'] is None or seriesData['epsRetrived'] is None or seriesData['epsRetrived']+Datetime.Delta(minutes=60) <= Datetime.Now():
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
	


def getEpisodeListFromFeed(feed):
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
				mediaId = int(item.xpath("./guid")[0].text.split("-")[1])
				@task
				def parseEpisodeItem(item=item,mediaId=mediaId):
					if not str(mediaId) in Dict['episodes']:
						title = item.xpath("./title")[0].text
						if title.startswith("%s - " % seriesTitle):
							title = title.replace("%s - " % seriesTitle, "")
						elif title.startswith("%s Season " % seriesTitle):
							title = title.replace("%s Season " % seriesTitle, "")
							title = title.split(" ", 1)[1].lstrip("- ")
						link = item.xpath("./link")[0].text
						description = item.xpath("./description")[0].text
						if "/><br />" in description:
							description = description.split("/><br />")[1]
						try:
							episodeNum = int(item.xpath("./crunchyroll:episodeNumber", namespaces=PLUGIN_NAMESPACE)[0].text)
						except:
							episodeNum = None
						try: publisher = item.xpath("./crunchyroll:publisher", namespaces=PLUGIN_NAMESPACE)[0].text
						except: publisher = ""
						thumb = str(item.xpath("./media:thumbnail", namespaces=PLUGIN_NAMESPACE)[0].get('url')).replace("_large",THUMB_QUALITY[Prefs['thumb_quality']])
						try: keywords = item.xpath("./media:keywords", namespaces=PLUGIN_NAMESPACE)[0].text
						except: keywords = ""
						availableResolutions = [] # this isn't available with rss script (it is with boxee_feeds)
						try:
							season = int(item.xpath("./crunchyroll:season", namespaces=PLUGIN_NAMESPACE)[0].text)
						except:
							season = None
							hasSeasons = False
						try:
							rating = item.xpath("../rating")[0].text
							Log.Debug(rating)
							
							# see http://www.classify.org/safesurf/
							# just pluck the age value from text that looks like:
							# (PICS-1.1 &quot;http://www.classify.org/safesurf/&quot; l r (SS~~000 5))
							ageLimit = re.sub(r'(.*\(SS~~\d{3}\s+)(\d)(\).*)', r'\2', rating)
							Log.Debug(ageLimit)							
							rating = int(ageLimit) # we don't care about the categories
							
						except (ValueError, IndexError, TypeError):
							rating = None
							
						mediaType = item.xpath("./media:category", namespaces=PLUGIN_NAMESPACE)[0].get('label')
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
						Dict['episodes'][str(mediaId)] = episode
					else:
						episode = Dict['episodes'][str(mediaId)]
					episodeList.append(episode)
				
		sortedEpisodeList = sorted(episodeList, key=lambda k: k['episodeNum'])
		return sortedEpisodeList
	except Exception, arg:
		Log.Error("#####We got ourselves a dagnabbit exception:")
		Log.Error(repr(Exception) + repr(arg))
		Log.Error("feed: %s" % feed)
		# maybe just pass the exception up the chain here
		# instead of returning None
		return None


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

	Login()

	availRes = [360]
	link = url.replace(BASE_URL, "")
	req = HTTP.Request(url=url, immediate=True, cacheTime=3600*24)
	html = HTML.ElementFromString(req)
	
	try: 
		small = not isPremium()
		if small:
			Log.Debug("#######HEY, WE ARE NOT SIGNED IN")

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
	
	Log.Debug("##############AVAILABLE RES:")
	Log.Debug(availRes)
	return availRes


def getPrefRes(availRes):

	if not Prefs['username'] or not Prefs['password']:
		return 360 # that's all you get
	Login()
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
