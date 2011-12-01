SPLIT_LONG_LIST = True

def getQueueList():
	queueURL = BASE_URL+"/queue"
	queueHtml = HTML.ElementFromURL(queueURL)
	queueList = []
	items = queueHtml.xpath("//div[@class='queue-container clearfix']/ul[@id='sortable']/li")
	for item in items:
		title = item.xpath("./div[@class='title']/a")[0].text.replace("\\\\","").lstrip("\n ").rstrip(" ")
		mediaId = int(item.xpath(".")[0].get('id').replace("queue_item_",""))
		epToPlay = BASE_URL+"/"+item.xpath("./div[@class='play']/button")[0].get('onclick').replace("window.location=\"\\/","").split("?t=")[0].replace("\\/","/")
		#try:
		#	seriesStatus = item.xpath("./div[@class='status']/span")[0].text.lstrip("\n ").rstrip(" ")
		#except:
		seriesStatus = item.xpath("./div[@class='status']")[0].text.lstrip("\n ").rstrip(" ")
		queueItem = {
			"title": title,
			"mediaId": mediaId,
			"epToPlay": epToPlay,
			"seriesStatus": seriesStatus
		}
		queueList.append(queueItem)
	#Log.Debug("list %s" % queueList)
	return queueList


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
		#Dict['series'][str(mediaId)] = series
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
		ratio = float(episodeInfo['width'])/float(episodeInfo['height'])
		if ratio < 1.5:
			episodeInfo['wide'] = False
		else:
			episodeInfo['wide'] = True
			
	except:
		episodeInfo = None
	return episodeInfo


def getEpisodeListFromFeed(feed):
	episodeList = []
	if USING_BOXEE_FEEDS is True:
		if LoginNotBlank():
			loggedin = LoggedIn()
			if not loggedin:
				Login()
				
		feedURL = FEED_BASE_URL+feed
		feedHtml = XML.ElementFromURL(feedURL)
		items = feedHtml.xpath("//item")
		for item in items:
			PLUGIN_NAMESPACE   = {'boxee':'http://boxee.tv/rss', 'media':"http://search.yahoo.com/mrss/"}
			mediaIdTmp = item.xpath("./guid")[0].text.split("-")
			mediaId = int(mediaIdTmp[len(mediaIdTmp)-1])
			if not str(mediaId) in Dict['episodes']:
				title = item.xpath("./title")[0].text
				link = item.xpath("./guid")[0].text
				description = item.xpath("./description")[0].text
				seriesTitle = item.xpath("./boxee:property[@name='custom:seriesname']", namespaces=PLUGIN_NAMESPACE)[0].text
				try:
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
						wide = extraInfo['wide']
						duration = int(float(extraInfo['duration'])*1000)
						if episodeNum is None and extraInfo['episodeNum'] is not None:
							episodeNum = int(extraInfo['episodeNum'])
					else:
						duration = 1800000
				else:
					duration = 1800000
					wide = True
				
				publisher = ""
				season = None
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
					"publisher": publisher,
					"season": season,
					"keywords": keywords
				}
				Dict['episodes'][str(mediaId)] = episode
			else:
				episode = Dict['episodes'][str(mediaId)]
			episodeList.append(episode)
		hasSeasons = False
	else:
		PLUGIN_NAMESPACE   = {"media":"http://search.yahoo.com/mrss/", "crunchyroll":"http://www.crunchyroll.com/rss"}
		feedHtml = XML.ElementFromURL(feed)
		items = feedHtml.xpath("//item")
		seriesTitle = feedHtml.xpath("//channel/title")[0].text.replace(" Episodes", "")
		Log.Debug(seriesTitle)
		hasSeasons = True
		for item in items:
			mediaId = int(item.xpath("./guid")[0].text.split("-")[1])
			if not str(mediaId) in Dict['episodes']:
				title = item.xpath("./title")[0].text
				if title.startswith("%s - " % seriesTitle):
					title = title.replace("%s - " % seriesTitle, "")
				elif title.startswith("%s Season " % seriesTitle):
					title = title.replace("%s Season " % seriesTitle, "")
					title = title.split(" ", 1)[1]
					if title.startswith("- "):
						title = title.split(" ",1)[1]
				link = item.xpath("./link")[0].text
				description = item.xpath("./description")[0].text
				if "/><br />" in description:
					description = description.split("/><br />")[1]
				try:
					episodeNum = int(item.xpath("./crunchyroll:episodeNumber", namespaces=PLUGIN_NAMESPACE)[0].text)
				except:
					episodeNum = None
				publisher = item.xpath("./crunchyroll:publisher", namespaces=PLUGIN_NAMESPACE)[0].text
				thumb = str(item.xpath("./media:thumbnail", namespaces=PLUGIN_NAMESPACE)[0].get('url')).replace("_large",THUMB_QUALITY[Prefs['thumb_quality']])
				keywords = item.xpath("./media:keywords", namespaces=PLUGIN_NAMESPACE)[0].text
				availableResolutions = ["12"]
				try:
					#Log.Debug("season: %s" % item.xpath("./crunchyroll:season", namespaces=PLUGIN_NAMESPACE)[0].text)
					season = int(item.xpath("./crunchyroll:season", namespaces=PLUGIN_NAMESPACE)[0].text)
				except:
					#Log.Debug("season: ERROR")
					season = None
					hasSeasons = False
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
					"keywords": keywords
				}
				Dict['episodes'][str(mediaId)] = episode
			else:
				episode = Dict['episodes'][str(mediaId)]
			episodeList.append(episode)
			
	sortedEpisodeList = sorted(episodeList, key=lambda k: k['episodeNum'])
	output = {}
	if SPLIT_LONG_LIST is True and hasSeasons is True and len(episodeList) > 50:
		seasonList = {}
		for e in sortedEpisodeList:
			s = e['season']
			if s not in seasonList:
				seasonList[s] = []
			seasonList[s].append(e)
		output['seasons'] = seasonList
		output['useSeasons'] = True
	else:
		output['useSeasons'] = False
		output['episodeList'] = sortedEpisodeList
	return output


def getSeasonEpisodeListFromFeed(feed,season):
	tmp = getEpisodeListFromFeed(feed)
	epList = tmp['seasons'][season]
	return epList


def getVideoInfo(baseUrl, mediaId, availRes):
	if LoginNotBlank():
		loggedin = LoggedIn()
		if not loggedin:
			Login()
	url = "http://www.crunchyroll.com/xml/?req=RpcApiVideoPlayer_GetStandardConfig&media_id=%s&video_format=102&video_quality=10&auto_play=1&show_pop_out_controls=1&pop_out_disable_message=Only+All-Access+Members+and+Anime+Members+can+pop+out+this" % mediaId
	html = HTML.ElementFromURL(url)
	episodeInfo = {}
	episodeInfo['baseUrl'] = baseUrl
	episodeInfo['availRes'] = availRes
	episodeInfo['small'] = False
	episodeInfo['initialVolume'] = int(html.xpath("//initialvolume")[0].text)
	episodeInfo['width'] = html.xpath("//stream_info/metadata/width")[0].text
	episodeInfo['height'] = html.xpath("//stream_info/metadata/height")[0].text
	try:
		episodeInfo['duration'] = int(float(html.xpath("//stream_info/metadata/duration")[0].text)*1000)
	except:
		episodeInfo['duration'] = 0
	episodeInfo['episodeNum'] = int(html.xpath("//media_metadata/episode_number")[0].text)
	ratio = float(episodeInfo['width'])/float(episodeInfo['height'])
	if ratio < 1.5:
		episodeInfo['wide'] = False
	else:
		episodeInfo['wide'] = True
	return episodeInfo


def getAvailResFromPage(url, availableRes):
	availRes = ['12']
	if LoggedIn():
		req = HTTP.Request(url=url, immediate=True, cacheTime=3600)
		link = url.replace(BASE_URL, "")
		r2a = '<a href="%s?p480=1" token="showmedia.480p" class="showmedia-res-btn" title="480P">480P</a>' % link
		r2b = '<a href="%s?p480=1" token="showmedia.480p" class=" showmedia-res-btn-selected" title="480P">480P</a>' % link
		r3a = '<a href="%s?p720=1" token="showmedia.720p" class="showmedia-res-btn" title="720P">720P</a>' % link
		r3b = '<a href="%s?p720=1" token="showmedia.720p" class=" showmedia-res-btn-selected" title="720P">720P</a>' % link
		if r2a in req.content or r2b in req.content:
			availRes.append("20")
		if r3a in req.content or r3b in req.content:
			availRes.append("21")
	for a in availableRes:
		availRes.append(a)
	availRes.sort()
	last = availRes[-1]
	for i in range(len(availRes)-2, -1, -1):
		if last == availRes[i]:
			del availRes[i]
		else:
			last = availRes[i]
	return availRes


def getPrefRes(availRes):
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
	invResNames = {'SD':"12", '480P':"20", '720P':"21"}
	return invResNames[resName]


def getEpInfoFromLink(link):
	mediaId = getVideoMediaIdFromLink(link)
	if not str(mediaId) in Dict['episodes']:
		seriesname = link.split(".com/")[1].split("/")[0]
		toremove = ["!", ":", "'", "?", ".", ",", "(", ")", "&", "@", "#", "$", "%", "^", "*", ";", "~", "`"]
		for char in toremove:
			seriesname = seriesname.replace(char, "")
		seriesname = seriesname.replace("  ", " ").replace(" ", "-").lower()
		while "--" in seriesname:
			seriesname = seriesname.replace("--","-")
		if seriesname.endswith("-"):
			seriesname = seriesname.rstrip("-")
		url = "%s/%s.rss" % (BASE_URL, seriesname)
		getEpisodeListFromFeed(url)
	
	episode = Dict['episodes'][str(mediaId)]
	#info = {}
	#info['episode'] = episode
	#info[]
	return episode


def getVideoMediaIdFromLink(link):
	mtmp = link.split(".com/")[1].split("/")[1].split("-")
	mediaId = int(mtmp[len(mtmp)-1])
	return mediaId
