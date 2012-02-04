FANART_API_URL = "http://fanart.tv/api/fanart.php?id=%s&sort=nameasc"

SEASON_IMAGE_FIX_LIST = {
"79824":{"0":[0,16],"1":[1,8,18],"2":[2,9,19],"3":[3,10,24],"4":[4,11,21],"5":[5,12,22],"6":[6,13,23],"7":[14,17],"all":[7,15]},
"78857":{"0":[6],"1":[0],"2":[1],"3":[2],"4":[3],"5":[4],"all":[7]},
"74796":{"0":[0],"1":[1],"2":[2],"3":[3],"4":[4],"5":[5],"6":[6],"7":[7],"8":[8],"9":[9],"10":[10],"11":[],"12":[],"13":[],"14":[],"15":[],"16":[],"all":[]},
"100171":{"0":[],"1":[],"2":[],"3":[],"all":[]},
"80554":{"0":[],"1":[],"2":[],"all":[]},
"72491":{"0":[],"1":[],"2":[],"3":[],"all":[]},
"79183":{"0":[],"1":[],"2":[],"3":[],"all":[]},
"81844":{"0":[],"1":[],"2":[],"3":[],"4":[],"all":[]},
"80975":{"0":[],"1":[],"2":[],"3":[],"4":[],"5":[],"6":[],"7":[],"8":[],"9":[],"all":[]},
"81427":{"0":[],"1":[],"2":[],"3":[],"all":[]},
"79156":{"0":[],"1":[],"2":[],"3":[],"4":[],"5":[],"6":[],"all":[]},
"79895":{"0":[],"1":[],"2":[],"3":[],"4":[],"5":[],"all":[]},
}

def checkIfSeasonListNeedsUpdate():
	for key in SEASON_IMAGE_FIX_LIST.keys():
		webCount = len(getImagesForIdOfType(int(key), "seasonthumbs"))
		listCount = 0
		for sl in SEASON_IMAGE_FIX_LIST[key]:
			listCount = listCount + len(sl)
		if webCount != listCount:
			Log.Warn("Update season image list for id: %s"%key)


def checkIfAllSeriesWithSIListed(idList):
	for id in idList:
		if len(getImagesForIdOfType(id, "seasonthumbs")) >0 and str(id) not in SEASON_IMAGE_FIX_LIST:
			Log.Debug('id "%s" has season images but is not in list.'%key)


def getAllImagesForId(tvdbId):
	if str(tvdbId) in Dict['fanart'] and Dict['fanart'][str(tvdbId)]['retrived']+Datetime.Delta(hours=24) >= Datetime.Now():
		return Dict['fanart'][str(tvdbId)]['results']
	else:
		xml = XML.ElementFromURL("http://fanart.tv/api/fanart.php?id=%s&sort=nameasc"%tvdbId, cacheTime=86400) #keep cahced for 24 hours
		results = {'clearlogos':[],'cleararts':[],'tvthumbs':[],'seasonthumbs':[]}
		#debugFanartItem(xml.xpath("/fanart")[0])
		for t in ['clearlogo','clearart','tvthumb','seasonthumb']:
			imgs = xml.xpath("//%s"%t)
			#Log.Debug("imgs: %s"%imgs)
			for img in imgs:
				results["%ss"%t].append(img.get('url').replace(" ", "%20"))
		Dict['fanart'][str(tvdbId)] = {}
		Dict['fanart'][str(tvdbId)]['results'] = results
		Dict['fanart'][str(tvdbId)]['retrived'] = Datetime.Now()
		return results

def getImagesForIdOfType(tvdbId, type):
	return getAllImagesForId(tvdbId)[type]

def getRandImage(tvdbId):
	tmp = getAllImagesForId(tvdbId)
	images = []
	for t in ['clearlogos','cleararts','tvthumbs','seasonthumbs']:
		for img in tmp["%ss"%t]:
			images.append(img)
	del tmp
	if len(images) > 0:
		return Util.RandomItemFromList(images)
	else:
		return None

def getRandImageOfTypes(tvdbId,types):
	tmp = getAllImagesForId(tvdbId)
	#Log.Debug("tmp: %s"%tmp)
	images = []
	for t in types:
		for img in tmp[t]:
			images.append(img)
	del tmp
	if len(images) > 0:
		return Util.RandomItemFromList(images)
	else:
		return None

def debugFanartItem(item):
	for sub in list(item):
		text1 = "%s: %s" % (sub.tag, sub.text)
		Log.Debug(text1)
		for sub2 in list(sub):
			text2 = "\t%s/%s: %s" % (sub.tag, sub2.tag, sub2.attrib)
			Log.Debug(text2)

def getSeasonThumb(tvdbId, season, rand=True):
	images = getImagesForIdOfType(tvdbId, 'seasonthumbs')
	if str(tvdbId) in SEASON_IMAGE_FIX_LIST.keys():
		if str(season) in SEASON_IMAGE_FIX_LIST[str(tvdbId)].keys() and len(SEASON_IMAGE_FIX_LIST[str(tvdbId)][str(season)])>0:
			imageIds = SEASON_IMAGE_FIX_LIST[str(tvdbId)][str(season)]
			if len(imageIds) > 0 and rand is True:
				imgId = Util.RandomItemFromList(imageIds)
			else:
				imgId = imageIds[0]
			usep = False
			base = images[0].replace(".jpg","")
			for i in images:
				if i.replace(".jpg","").endswith(")"):
					usep = True
					base = i.split("(")[0]
			if imgId == 0:
				url = base+".jpg"
			else:
				url = base+("(%s).jpg"%(imgId+1) if usep else "%s.jpg"%(imgId+1))
			#url = base+ins
			if url in images:
				return url
			else:
				Log.Error("season %s, image %s missing from the SEASON_IMAGE_FIX_LIST for tvdbId %s"%(season, imgId, tvdbId))
				return None
		else:
			Log.Error("season %s missing from the SEASON_IMAGE_FIX_LIST for tvdbId %s"%(season, tvdbId))
			return None
	else:
		if len(images) > 0:
			usep = False
			base = images[0].replace(".jpg","")
			for i in images:
				if i.replace(".jpg","").endswith(")"):
					usep = True
					base = i.split("(")[0]
			if season == 1:
				url = base+".jpg"
			else:
				url = base+("(%s).jpg"%(season) if usep else "%s.jpg"%(season))
			if url in images:
				return url
		return None


"""	
	<fanart show="Bleach">
	<clearlogos>
	<clearlogo url="http://fanart.tv/fanart/74796/clearlogo/bleach-74796.png"/>
	<clearlogo url="http://fanart.tv/fanart/74796/clearlogo/bleach-4dcff95072e2c.png"/>
	</clearlogos>
	<cleararts>
	<clearart url="http://fanart.tv/fanart/74796/clearart/B_74796 (1).png"/>
	<clearart url="http://fanart.tv/fanart/74796/clearart/B_74796 (0).png"/>
	<clearart url="http://fanart.tv/fanart/74796/clearart/Bleach-74796-5.png"/>
	<clearart url="http://fanart.tv/fanart/74796/clearart/Bleach-74796-4.png"/>
	<clearart url="http://fanart.tv/fanart/74796/clearart/Bleach-74796-3.png"/>
	</cleararts>
	<tvthumbs>
	<tvthumb url="http://fanart.tv/fanart/74796/tvthumb/B_74796 (1).jpg"/>
	<tvthumb url="http://fanart.tv/fanart/74796/tvthumb/B_74796 (0).jpg"/>
	</tvthumbs>
	<seasonthumbs>
	<seasonthumb url="http://fanart.tv/fanart/74796/seasonthumb/Bleach.jpg"/>
	<seasonthumb url="http://fanart.tv/fanart/74796/seasonthumb/Bleach (9).jpg"/>
	<seasonthumb url="http://fanart.tv/fanart/74796/seasonthumb/Bleach (8).jpg"/>
	<seasonthumb url="http://fanart.tv/fanart/74796/seasonthumb/Bleach (7).jpg"/>
	<seasonthumb url="http://fanart.tv/fanart/74796/seasonthumb/Bleach (6).jpg"/>
	<seasonthumb url="http://fanart.tv/fanart/74796/seasonthumb/Bleach (5).jpg"/>
	<seasonthumb url="http://fanart.tv/fanart/74796/seasonthumb/Bleach (4).jpg"/>
	<seasonthumb url="http://fanart.tv/fanart/74796/seasonthumb/Bleach (3).jpg"/>
	<seasonthumb url="http://fanart.tv/fanart/74796/seasonthumb/Bleach (2).jpg"/>
	<seasonthumb url="http://fanart.tv/fanart/74796/seasonthumb/Bleach (11).jpg"/>
	<seasonthumb url="http://fanart.tv/fanart/74796/seasonthumb/Bleach (10).jpg"/>
	</seasonthumbs>
	</fanart>
"""