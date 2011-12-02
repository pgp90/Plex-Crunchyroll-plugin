
def getQueueList():
	queueURL = BASE_URL+"/queue"
	req = HTTP.Request(queueURL,cacheTime=10,immediate=True)
	queueHtml = HTML.ElementFromString(req.content)
	queueList = []
	items = queueHtml.xpath("//div[@class='queue-container clearfix']/ul[@id='sortable']/li")
	for item in items:
		title = item.xpath("./div[@class='title']/a")[0].text.replace("\\\\","").lstrip("\n ").rstrip(" ")
		mediaId = int(item.xpath(".")[0].get('id').replace("queue_item_",""))
		epToPlay = BASE_URL+"/"+item.xpath("./div[@class='play']/button")[0].get('onclick').replace("window.location=\"\\/","").split("?t=")[0].replace("\\/","/")
		try:
			seriesStatus = item.xpath("./div[@class='status']/span")[0].text.lstrip("\n ").rstrip(" ")
		except:
			seriesStatus = item.xpath("./div[@class='status']")[0].text.lstrip("\n ").rstrip(" ")
		if "Complete" in seriesStatus:
			seriesStatus = "Complete"
		else:
			seriesStatus = "Ongoing"
		queueItem = {
			"title": title,
			"mediaId": mediaId,
			"epToPlay": epToPlay,
			"seriesStatus": seriesStatus
		}
		queueList.append(queueItem)
	return queueList


def getSeriesListFromFeed(feed):
	feedURL = FEED_BASE_URL+feed
	feedHtml = HTML.ElementFromURL(feedURL)
	seriesList = []
	items = feedHtml.xpath("//item")
	seriesDict = Dict['series']
	if seriesDict is None:
		seriesDict = {}
	for item in items:
		mediaId = int(item.xpath("./guid")[0].text.split(".com/")[1])
		if not (str(mediaId) in seriesDict):
			title = item.xpath("./title")[0].text
			description = item.xpath("./description")[0].text
			thumb = str(item.xpath("./property")[0].text).replace("_large",THUMB_QUALITY[Prefs['thumb_quality']])
			series = {
				"title": title,
				"seriesId": mediaId,
				"tvdbId": None,
				"description": description,
				"thumb": thumb
			}
			dictInfo = series
			dictInfo['epsRetrived'] = None
			dictInfo['epList'] = []
			seriesDict[str(mediaId)] = dictInfo
		else:
			seriesDict[str(mediaId)]['thumb'] = str(item.xpath("./property")[0].text).replace("_large",THUMB_QUALITY[Prefs['thumb_quality']])
			series = {
				"title": seriesDict[str(mediaId)]['title'],
				"seriesId": mediaId,
				"tvdbId": seriesDict[str(mediaId)]['tvdbId'],
				"description": seriesDict[str(mediaId)]['description'],
				"thumb": seriesDict[str(mediaId)]['thumb']
			}
		seriesList.append(series)
	Dict['series'] = seriesDict
	sortedSeriesList = sorted(seriesList, key=lambda k: k['title'])
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
			Dict['playerXml'][str(mediaId)] = episodeInfo
		else:
			episodeInfo = Dict['playerXml'][str(mediaId)]
	except:
		episodeInfo = None
	return episodeInfo


def getEpisodeListForSeries(seriesId):
	#Log.Debug("Dict['episodes']: %s"%Dict['episodes'])
	seriesData = Dict['series'][str(seriesId)]
	#Log.Debug("seriesData: %s"%seriesData)
	if seriesData['epsRetrived'] is None or seriesData['epsRetrived']+Datetime.Delta(minutes=60) <= Datetime.Now():
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


def getEpisodeListFromFeed(feed):
	episodeList = []
	PLUGIN_NAMESPACE = {"media":"http://search.yahoo.com/mrss/", "crunchyroll":"http://www.crunchyroll.com/rss"}
	feedHtml = XML.ElementFromURL(feed)
	items = feedHtml.xpath("//item")
	seriesTitle = feedHtml.xpath("//channel/title")[0].text.replace(" Episodes", "")
	hasSeasons = True
	for item in items:
		mediaId = int(item.xpath("./guid")[0].text.split("-")[1])
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
			publisher = item.xpath("./crunchyroll:publisher", namespaces=PLUGIN_NAMESPACE)[0].text
			thumb = str(item.xpath("./media:thumbnail", namespaces=PLUGIN_NAMESPACE)[0].get('url')).replace("_large",THUMB_QUALITY[Prefs['thumb_quality']])
			keywords = item.xpath("./media:keywords", namespaces=PLUGIN_NAMESPACE)[0].text
			availableResolutions = []#getAvailResFromPage(link, ['12'])
			try:
				season = int(item.xpath("./crunchyroll:season", namespaces=PLUGIN_NAMESPACE)[0].text)
			except:
				season = None
				hasSeasons = False
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
				"type": mediaType
			}
			Dict['episodes'][str(mediaId)] = episode
		else:
			episode = Dict['episodes'][str(mediaId)]
		episodeList.append(episode)	
	sortedEpisodeList = sorted(episodeList, key=lambda k: k['episodeNum'])
	return sortedEpisodeList


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
	epList = tmp['seasons'][season]
	return epList


def getVideoInfo(baseUrl, mediaId, availRes):
	url = "http://www.crunchyroll.com/xml/?req=RpcApiVideoPlayer_GetStandardConfig&media_id=%s&video_format=102&video_quality=10&auto_play=1&show_pop_out_controls=1&pop_out_disable_message=Only+All-Access+Members+and+Anime+Members+can+pop+out+this" % mediaId
	html = HTML.ElementFromURL(url)
	episodeInfo = {}
	episodeInfo['baseUrl'] = baseUrl
	episodeInfo['availRes'] = availRes
	width = html.xpath("//stream_info/metadata/width")[0].text
	height = html.xpath("//stream_info/metadata/height")[0].text
	try:
		episodeInfo['duration'] = int(float(html.xpath("//stream_info/metadata/duration")[0].text)*1000)
	except:
		episodeInfo['duration'] = 0
	try:
		episodeInfo['episodeNum'] = int(html.xpath("//media_metadata/episode_number")[0].text)
	except:
		episodeInfo['episodeNum'] = 0
	ratio = float(width)/float(height)
	episodeInfo['wide'] = (ratio > 1.5)
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
	availResNames = []
	for resN in availRes:
		availResNames.append(RES_NAMES[resN])
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
	if title.endswith("-"):
		title = title.rstrip("-")
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
