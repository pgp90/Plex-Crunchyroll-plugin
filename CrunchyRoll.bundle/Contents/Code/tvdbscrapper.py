# -*- coding: utf-8 -*-
import re, time, unicodedata, hashlib, types

# Define proxy for TVDB.
#TVDB_SITE	= 'thetvdb.com'
#TVDB_PROXY = 'thetvdb.plexapp.com'

# Define proxy for TV Rage.
#TVRAGE_SITE = 'tvrage.com'
#TVRAGE_PROXY = 'tvrage.plexapp.com'

#TVDB_API_KEY	= 'D4DDDAEFAD083E6F'
#TVDB_SEARCH_URL	= 'http://%s/api/GetSeries.php?seriesname=%%s&language=%%s' % TVDB_PROXY
#TVDB_ADVSEARCH_NETWORK  = 'http://%s/index.php?seriesname=%%s&fieldlocation=1&genre=&year=%%s&network=%%s&zap2it_id=&tvcom_id=&imdb_id=&order=translation&searching=Search&tab=advancedsearch&language=%%s' % TVDB_PROXY

#TVDB_GUID_SEARCH	= 'http://freebase.plexapp.com/tv/guid/'
TVDB_QUICK_SEARCH	= 'http://freebase.plexapp.com/tv/names/'
#TVDB_TITLE_SEARCH	= 'http://freebase.plexapp.com/tv/titles/'

#TVDB_SERIES_URL	= '%%s/api/%s/series/%%s' % TVDB_API_KEY
#TVDB_ZIP_URL	= '%s/all/%%s.zip' % TVDB_SERIES_URL
#TVDB_SERIES_URL	= '%s/%%s.xml' % TVDB_SERIES_URL
#TVDB_BANNER_URL	= '%s/banners/'

#GOOGLE_JSON_TVDB = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&rsz=large&q=%s+"thetvdb.com"+series+%s'
#GOOGLE_JSON_TVDB_TITLE = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&rsz=large&q=%s+"thetvdb.com"+series+info+%s'
#GOOGLE_JSON_BROAD = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&rsz=large&q=%s+site:thetvdb.com+%s'
#GOOGLE_JSON_IMDB = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&rsz=large&q=%s+site:imdb.com+tv+%s'

#TVRAGE_SEARCH = 'http://%s/feeds/search.php?show=%%s' % TVRAGE_PROXY

#SCRUB_FROM_TITLE_SEARCH_KEYWORDS = ['uk','us']
#NETWORK_IN_TITLE = ['bbc']
#EXTRACT_AS_KEYWORDS = ['uk','us','bbc']

netLock = Thread.Lock()

# Language table
# NOTE: if you add something here, make sure
# to add the language to the appropriate
# tvdb cache download script on the data
# processing servers
THETVDB_LANGUAGES_CODE = {
	'cs': '28',
	'da': '10',
	'de': '14',
	'el': '20',
	'en': '7',
	'es': '16',
	'fi': '11',
	'fr': '17',
	'he': '24',
	'hu': '19',
	'it': '15',
	'ja': '25',
	'nl': '13',
	'no': '9',
	'pl': '18',
	'pt': '26',
	'ru': '22',
	'sv': '8',
	'tr': '21',
	'zh': '6',
}

# Keep track of success/failures in a row.
successCount = 0
failureCount = 0

MIN_RETRY_TIMEOUT = 2
RETRY_TIMEOUT	= MIN_RETRY_TIMEOUT
TOTAL_TRIES		= 1
BACKUP_TRIES	= -1

headers = {'User-agent': 'Plex/Nine'}

ERROR_FIX = {
"Abunai Sisters": None,
"Adventures in Voice Acting": None,
"AniView": None,
"Artichoke and Peachies Show": None,
"BASToF Syndrome": None,
"Black Jack Motion Magazine": None,
"Break Ups": None,
"Canvas 2: Niji Iro no Sketch": None,
"Cat God": None,
"Catblue Dynamite": None,
"CATMAN": None,
"Dark Side Cat": None,
"DEMIAN": None,
"Digimon Adventure 02": None,
"Digimon Tamers": None,
"Dororo Motion Magazine": None,
"Egg Man": None,
"Glass Maiden": None,
"Go Lion": None,
"Greathunt": None,
"Japan Tourism Anime Channel": None,
"Japancast": None,
"Kaasan Mom's Life": None,
"Kaede New Town": None,
"Kid Kosmo": None,
"Kigurumikku": None,
"Kobo chan": None,
"La Maison en Petits Cubes": None,
"Lady Death": None,
"Memoirs of a Lady Ninja": None,
"My Ordinary Life": None,
"Naked Wolves": None,
"Neko Rahmen": None,
"Oreimo": None,
"Otaku No Video Podcast": None,
"Otaku-Verse Zero": None,
"Peeping Life": None,
"Phantom Thief Reinya": None,
"Ramen Fighter Miki": None,
"Shin Koihime Musou": None,
"Shin Koihime Musou - Otome Tairan": None,
"Sin The Movie": None,
"Soranowoto": None,
"Sumiko": None,
"The Idol Master": None,
"The Live Show": None,
"Uraboku": None,
"Valerian and Laureline": None,
"Wagnaria!!": None,
"We, Without Wings - under the innocent sky": None,
"Wonder Beat Scramble": None,
"Yasuhiro Yoshiura": None,
"Yatler  Matler Space Tyrants": None,
"Yonna in the Solitary Fortress": None,
"You and Me": None,
"11eyes": 117851,
"07 Ghost": 88651,
"Air Master": 79205,
"Angelic Layer": 78909,
"A Dark Rabbit has Seven Lives": 251234,
"Asura Cryin'": 87981,
"Astarotte's Toy": 247933,
"Asobi ni Ikuyo: Bombshells from the Sky": 173301,
"Beelzebub": 219771,
"Black Jack": 81092,
"Battle Girls - Time Paradox": 246971,
"Best Student Council": 83536,
"Bleach": 74796,
"BLASSREITER": 82116,
"Cardfight Vanguard": 245821,
"Blue Exorcist": 248035,
"Charger Girl Ju-den Chan": 103291,
"A Bridge to the Starry Skies - Hoshizora e Kakaru Hashi": 248012,
"Captain Harlock": 159421,
"Chihayafuru": 251982,
"Chance Pop Session": 97951,
"Chu-Bra": 133331,
"Cobra the Animation": 137151,
"Cosplay Complex OVA": 75510,
"CODE GEASS Lelouch of the Rebellion": 79525,
"Culture Japan": 233101,
"Dear Boys": 169991,
"Demonbane": 81105,
"Demon King Daimao": 140071,
"Deadman Wonderland": 247997,
"Durarara": 133341,
"Erin": 88911,
"Chi's Sweet Home - Chi's New Address": 81844,
"Dragon Crisis": 220541,
"Fairy Musketeers": 235591,
"Eureka Seven": 79360,
"Fate Zero": 79151,
"Eyeshield 21": 79183,
"Fairy Tail": 114801,
"Fortune Arterial": 196231,
"Fist of the North Star": 79156,
"GA Geijutsuka Art Design Class": 108401,
"Gaiking: Legend of Daiku-Maryu": 100161,
"Digimon Xros Wars - The Young Hunters Who Leapt Through Time": 84572,
"Galaxy Express 999": 100171,
"Galaxy High School": 74914,
"Gankutsuou": 79178,
"Gintama": 79895,
"gdgd Fairies": 252808,
"Good Luck! Ninomiya-kun": 82167,
"Giant Killing": 139631,
"Glass Mask": 179311,
"Gosick": 218191,
"Hanamaru Kindergarten": 134581,
"Girl's High": 81426,
"Hanasakeru Seishonen": 88661,
"H2O: Footprints in the Sand": 81732,
"Goshuushosama Ninomiya-kun": 82167,
"Happiness!": 130391,
"Hanasaku Iroha": 246521,
"Hourou Musuko Wandering Son": 221281,
"HEROMAN": 153331,
"Hyakko": 83317,
"Hunter x Hunter": 149081,
"Ikkitousen": 80158,
"Hayate no Gotoku": 80554,
"Interlude": 80466,
"Horizon in the Middle of Nowhere": 252345,
"Japanese Anime Classic Collection 1": 251099,
"Japanese Anime Classic Collection 2": 251099,
"Japanese Anime Classic Collection 4": 251099,
"Japanese Anime Classic Collection 3": 251099,
"Kemeko DX": 83360,
"Kanamemo": 107301,
"Kamisama Dolls": 249873,
"Kanokon": 81830,
"Kiddy GiRL-AND": 121381,
"Koihime Musou": 83314,
"Kite Liberator": 82950,
"La Corda d'Oro ~primo passo~ and ~secondo passo~": 159551,
"Lilpri": 246251,
"Kurokami The Animation": 84561,
"Level E": 220551,
"Kono Aozora ni Yakusoku wo": 84464,
"Maburaho": 75003,
"Linebarrels of Iron": 83321,
"Magicians Academy": 83940,
"Lucky Star": 80177,
"Magical Play": 115371,
"Mashiroiro Symphony": 252477,
"Mighty Max": 76413,
"Miracle Train": 128541,
"Majikoi Oh! Samurai Girls": 252343,
"Martian Successor Nadesico Prince of Darkness": 71313,
"Mitsudomoe": 173211,
"Mizu no Kotoba": 84850,
"Mobile Suit Gundam": 80675,
"MOBILE SUIT GUNDAM 00": 80675,
"Mobile Suit Gundam UC (Unicorn)": 142601,
"Moribito": 80044,
"Mouse": 83635,
"Mobile Suit Zeta Gundam": 71535,
"Mushi-Uta": 80380,
"Mobile Suit Gundam Wing": 79327,
"Myself; Yourself": 81484,
"Naruto Shippuden": 79824,
"Moritasan wa Mukuchi": 247461,
"Naruto": 78857,
"Natsume Yujincho": 82788,
"NATSU NO ARASHI !": 88391,
"No. 6": 250030,
"Neo Angelique Abyss": 84138,
"Occult Academy": 171701,
"Nogizaka Haruka no Himitsu": 82688,
"Omamori Himari": 133821,
"Otome Yokai Zakuro": 195271,
"Nurse Witch Komugi-chan Magikarte": 79109,
"Pale Cocoon": 82278,
"Nogizaka Haruka no Himitsu - Purezza -": 82688,
"Persona": 81490,
"Parasite Dolls": 112531,
"REBORN!": 80975,
"Pretty Cure": 84334,
"R-15": 249867,
"Queen's Blade": 87491,
"Rio Rainbow Gate": 218531,
"Sacred Seven": 249939,
"Saiyuki": 80587,
"Saki": 87841,
"Saint Seiya The Lost Canvas": 101271,
"Seitokai No Ichizon - Student Councils Discretion": 116001,
"Sasameki Koto": 117711,
"School Days": 80478,
"SHANGRI-LA": 87871,
"Sherlock Hound": 83248,
"Shugo Chara": 81427,
"Sketchbook": 81375,
"Skip Beat!": 83653,
"SKET Dance": 247805,
"Slam Dunk": 72491,
"Star Driver": 194951,
"Speed Racer": 77777,
"Squid Girl": 195721,
"Steel Angel Kurumi": 79452,
"Steel Angel Kurumi Zero": 79463,
"STEINS;GATE": 244061,
"Steel Angel Kurumi 2 Shiki": 79452,
"Tegami Bachi Letter Bee": 112521,
"Sekai Ichi Hatsukoi - World's Greatest First Love": 144951,
"The Book of Bantorra": 116931,
"Tantei Opera Milky Holmes": 197261,
"The Diary of Tortov Roddle": 85381,
"The Mystic Archives of Dantalian": 249868,
"Super Robot Wars OG The Inspector": 195141,
"The Melody of Oblivion": 75000,
"The Melancholy of Haruhi Suzumiya": 85438,
"Time of Eve": 84709,
"The Tower of DRUAGA -the Sword of URUK-": 81744,
"The Tower of DRUAGA -the Aegis of URUK-": 81744,
"Twin Angel: Twinkle Paradise": 250088,
"The World God Only Knows": 195711,
"Un-Go": 252472,
"Venus to Mamoru!": 84016,
"Web Ghosts PiPoPa": 227751,
"Tono to Issho": 168561,
"Usagi Drop": 249872,
"Viewtiful Joe": 75797,
"White Album": 84553,
"Yumeiro Patissiere": 119141,
"YuruYuri": 251016,
"Yokuwakaru Gendai Maho": 102481
}
"""
{
"Abunai Sisters": None,
"Adventures in Voice Acting": None,
"Artichoke and Peachies Show": None,
"Black Jack Motion Magazine": None,
"Break Ups": None,
"Cat God": None,
"Catblue Dynamite": None,
"Canvas 2: Niji Iro no Sketch": None,
"Dark Side Cat":  None,
"Digimon Adventure 02": None,
"Digimon Tamers": None,
"Dororo Motion Magazine": None,
"Egg Man": None,
"Glass Maiden": None,
"Go Lion": None,
"Japan Tourism Anime Channel": None,
"Kaede New Town": None,
"Kid Kosmo": None,
"Kaasan Mom's Life": None,
"Kobo chan": None,
"Lady Death": None,
"La Maison en Petits Cubes": None,
"Naked Wolves": None,
"Memoirs of a Lady Ninja": None,
"My Ordinary Life": None,
"Neko Rahmen": None,
"Otaku-Verse Zero": None,
"Otaku No Video Podcast": None,
"Phantom Thief Reinya": None,
"Peeping Life": None,
"Ramen Fighter Miki": None,
"Shin Koihime Musou": None,
"Sin The Movie": None,
"Shin Koihime Musou - Otome Tairan": None,
"The Idol Master": None,
"The Live Show": None,
"Valerian and Laureline": None,
"Wonder Beat Scramble": None,
"We, Without Wings - under the innocent sky": None,
"Yonna in the Solitary Fortress": None,
"Yatler  Matler Space Tyrants": None,
"You and Me": None,
"Charger Girl Ju-den Chan": 103291,
"Erin": 88911,
"Fairy Musketeers": 235591,
"Good Luck! Ninomiya-kun": 82167,
"Hourou Musuko Wandering Son": 221281,
"La Corda d'Oro ~primo passo~ and ~secondo passo~": 159551,
"Magicians Academy": 83940,
"Miracle Train": 128541,
"Natsume Yujincho": 82788,
"Persona": 81490,
"Tegami Bachi Letter Bee": 112521,
"Venus to Mamoru!": 84016,
"Web Ghosts PiPoPa": 227751,
"Cardfight Vanguard": 245821,
"Dear Boys": 169991,
"Demonbane": 81105,
"Demon King Daimao": 140071,
"Durarara": 133341,
"Fate Zero": 79151,
"Galaxy High School": 74914,
"Hanamaru Kindergarten": 134581,
"Lilpri": 246251,
"Moribito": 80044,
"Mushi-Uta": 80380,
"Myself; Yourself": 81484,
"Naruto Shippuden": 79824,
"NATSU NO ARASHI !": 88391,
"REBORN!": 80975,
"Sketchbook": 81375,
"Skip Beat!": 83653,
"Star Driver": 194951,
"Seitokai No Ichizon - Student Councils Discretion": 116001,
"The Mystic Archives of Dantalian": 249868,
"Twin Angel: Twinkle Paradise": 250088,
"Kemeko DX": 83360
}
"""
NOT_FOUND = ['AniView', 'BASToF Syndrome', 'CATMAN', 'DEMIAN', 'Greathunt', 'Japancast', 'Kigurumikku', 'Oreimo', 'Soranowoto', 'Sumiko', 'Uraboku', 'Wagnaria!!', 'Yasuhiro Yoshiura']

def replaceAccents(s):
	t = [("a", ["à","á","ã","ă","ä","å"]),
	("e", ["è","é","ê","ė"]),
	("e", ["ò","ó","ô","õ","ö"]),
	("e", ["ù","ú","û","ū","ü","ů"]),
	("e", ["ć","ç"]),
	("e", ["ŵ"]),
	("e", ["ŷ","ÿ"]),
	("e", ["ş"]),
	("e", ["ñ"]),
	("e", ["ğ"]),
	("e", ["ż"])]
	for l, al in t:
		for a in al:
			s = s.replace(a, l);
	return s

def fixExclimation(s):
	if s.endswith(" !"):
		s = s.replace(" !","!")
	return s

#àèòùáćéóúêôûŵŷçşãñõūăğėżäöüÿåů
def GetResultFromNetwork(url, fetchContent=True):
	global successCount, failureCount, RETRY_TIMEOUT
	
	# Not sure where this is introduced, but avoid spaces.
	#url = url.replace(' ','+')
	
	try:
		netLock.acquire()
		#Log("Retrieving URL: " + url)
		
		tries = TOTAL_TRIES
		while tries > 0:
			
			try:
				result = HTTP.Request(url, headers=headers, timeout=60, cacheTime=10)
				if fetchContent:
					result = result.content
				
				failureCount = 0
				successCount += 1
				
				if successCount > 20:
					RETRY_TIMEOUT = max(MIN_RETRY_TIMEOUT, RETRY_TIMEOUT/2)
					successCount = 0
				
				# DONE!
				return result
			
			except Exception, e:
				
				# Fast fail a not found.
				if e.code == 404:
					return None
				
				failureCount += 1
				Log("Failure (%d in a row)" % failureCount)
				successCount = 0
				time.sleep(RETRY_TIMEOUT)
				
				if failureCount > 5:
					RETRY_TIMEOUT = min(10, RETRY_TIMEOUT * 1.5)
					failureCount = 0
			
			# On the last tries, attempt to contact the original URL.
			tries = tries - 1
			if tries == BACKUP_TRIES:
				url = url.replace(TVDB_PROXY, TVDB_SITE)
				Log("Falling back to non-proxied URL: " + url)
	
	finally:
		netLock.release()
	
	return None

#def Start():
#	
#	Dict['ZIP_MIRROR'] = 'http://' + TVDB_PROXY
#	Dict['IMG_MIRROR'] = 'http://' + TVDB_PROXY
#	HTTP.CacheTime = CACHE_1HOUR * 24

def setuptime():
	global tsum
	global tc
	t = Datetime.Now()
	tsum = t - t
	tc = 0

def getavg():
	global tsum
	global tc
	return (tsum / tc)


def listNotListed():
	Log.Debug("looking for missing")
	for sk in Dict['series'].keys():
		s = Dict['series'][str(sk)]
		if str(s['title']) not in ERROR_FIX:
			Log.Debug('"%s": %s'%(s['title'], s['tvdbId']))


def GetTVDBID(seriesName, lang):
	#global tsum
	#global tc
	#tc = tc + 1
	#t1 = Datetime.Now()
	seriesName = fixExclimation(replaceAccents(seriesName))
	#t2 = Datetime.Now()
	#tsum = tsum + (t2 - t1)
	if re.sub(r'([ ]+\(?[0-9]{4}\)?)', '', seriesName) in NOT_FOUND:
		return {"id":None,"bestMatch":None}
	elif re.sub(r'([ ]+\(?[0-9]{4}\)?)', '', seriesName) in ERROR_FIX:
		return {"id":ERROR_FIX[re.sub(r'([ ]+\(?[0-9]{4}\)?)', '', seriesName)],"bestMatch":None}
	else:
		results = searchByWords(lang, seriesName, None)
		if len(results) >= 1:
			if results[0]['score'] >=95:
				return {"id":int(results[0]['id']),"bestMatch":results[0]}
			else:
				return {"id":None,"bestMatch":results[0]}
		else:
			return {"id":None,"bestMatch":None}

def searchByWords(lang, origTitle, year):
	results = []
	# Process the text.
	title = origTitle.lower()
	title = re.sub(r'[\'":\-&,.!~()]', ' ', title)
	title = re.sub(r'[ ]+', ' ', title)
	
	# Search for words.
	show_map = {}
	total_words = 0
	
	for word in title.split():
		if word not in ['a', 'the', 'of', 'and']:
			total_words += 1
			wordHash = hashlib.sha1()
			wordHash.update(word.encode('utf-8'))
			wordHash = wordHash.hexdigest()
			try:
				#matches = XML.ElementFromString(GetResultFromNetwork(TVDB_QUICK_SEARCH + lang + '/' + wordHash[0:2] + '/' + wordHash + '.xml'))
				matches = XML.ElementFromURL(TVDB_QUICK_SEARCH + lang + '/' + wordHash[0:2] + '/' + wordHash + '.xml', cacheTime=600)
				#Log.Debug("matches: %s"%matches)
				for match in matches.xpath('//match'):
					id = match.get('id')
					title = match.get('title')
					titleYear = match.get('year')
					
					if not show_map.has_key(id):
						show_map[id] = [id, title, titleYear, 1]
					else:
						show_map[id] = [id, title, titleYear, show_map[id][3] + 1]
			except:
				pass
	
	resultList = show_map.values()
	resultList.sort(lambda x, y: cmp(y[3],x[3]))
	#Log.Debug("resultList: %s"% resultList)
	
	score = 70
	for result in resultList:
		#Log.Debug("result: %s"%result)
		theYear = result[2]
		
		# Remove year suffixes that can mess things up.
		searchTitle = origTitle
		if len(origTitle) > 8:
			searchTitle = re.sub(r'([ ]+\(?[0-9]{4}\)?)', '', searchTitle)
			
		foundTitle = fixExclimation(replaceAccents(result[1]))
		if len(foundTitle) > 8:
			foundTitle = re.sub(r'([ ]+\(?[0-9]{4}\)?)', '', foundTitle)
		if not "**DUPLICATE " in foundTitle:
			# Remove prefixes that can screw things up.
			searchTitle = re.sub('^[Bb][Bb][Cc] ', '', searchTitle)
			foundTitle = re.sub('^[Bb][Bb][Cc] ', '', foundTitle)
			
			# Adjust if both have 'the' prefix by adding a prefix that won't be stripped.
			distTitle = searchTitle
			distFoundTitle = foundTitle
			if searchTitle.lower()[0:4] == 'the ' and foundTitle.lower()[0:4] == 'the ':
				distTitle = 'xxx' + searchTitle
				distFoundTitle = 'xxx' + foundTitle
				
			if distTitle.lower()==distFoundTitle.lower():
				theScore=100
			else:
				# Score adjustments.
				#Log.Debug("com string: %s"%Util.LongestCommonSubstring(distTitle, distFoundTitle))
				theScore = score + len(LongestCommonSubstring(distTitle, distFoundTitle))
				theScore = theScore + int(10 * lev_ratio(searchTitle, foundTitle)) + result[3] * 2
				
				if theYear != None and year != None:
					if theYear == year:
						theScore = theScore + 5
					elif theYear != year:
						theScore = theScore - 5
			
			if searchTitle.lower() in foundTitle.lower():
				theScore = theScore+1
				if foundTitle.lower().startswith(searchTitle.lower()) or foundTitle.lower().endswith(searchTitle.lower()):
					theScore = theScore + 2
				if searchTitle in foundTitle:
					theScore = theScore+1
					if foundTitle.startswith(searchTitle) or foundTitle.endswith(searchTitle):
						theScore = theScore + 2
					
			if len(searchTitle) <= 10 and len(foundTitle) <= 10:
				theScore = ((theScore-score-result[3] * 2) * 1.2)+score+result[3] * 2.1
						
			resultDict = {'id':result[0], 'name':result[1], 'year':result[2], 'lang':lang, 'score':theScore}
			results.append(resultDict)
		
	
	# Sort.
	results = sorted(results, key=lambda k: k['score'], reverse=True)
	#results.Sort('score', descending=True)
	
		
	# Only return at most 20 results.
	if len(results) > 20:
		del results[20:]
	return results

def parseResult2(title, year, result):
	#Log.Debug("result: %s"%result)
	theYear = result[2]
	
	# Remove year suffixes that can mess things up.
	searchTitle = origTitle
	if len(origTitle) > 8:
		searchTitle = re.sub(r'([ ]+\(?[0-9]{4}\)?)', '', searchTitle)
		
	foundTitle = result[1]
	if len(foundTitle) > 8:
		foundTitle = re.sub(r'([ ]+\(?[0-9]{4}\)?)', '', foundTitle)
		
	# Remove prefixes that can screw things up.
	searchTitle = re.sub('^[Bb][Bb][Cc] ', '', searchTitle)
	foundTitle = re.sub('^[Bb][Bb][Cc] ', '', foundTitle)
	
	# Adjust if both have 'the' prefix by adding a prefix that won't be stripped.
	distTitle = searchTitle
	distFoundTitle = foundTitle
	if searchTitle.lower()[0:4] == 'the ' and foundTitle.lower()[0:4] == 'the ':
		distTitle = 'xxx' + searchTitle
		distFoundTitle = 'xxx' + foundTitle
	
	# Score adjustments.
	theScore = score + len(Util.LongestCommonSubstring(distTitle, distFoundTitle))
	theScore = theScore + int(10 * lev_ratio(searchTitle, foundTitle)) + result[3] * 2
	
	if theYear != None and year != None:
		if theYear == year:
			theScore = theScore + 5
		elif theYear != year:
			theScore = theScore - 5
	
	resultDict = {'id':result[0], 'name':result[1], 'year':result[2], 'lang':lang, 'score':theScore}
	#Log.Debug("resultDict: %s"%resultDict)
	return resultDict

def lev_ratio(s1,s2):
	if safe_unicode(s1) is safe_unicode(s2):
		return float(1.0)
	elif ("!!" in s1 or "!!" in s2) and (s1.replace("!!","") is s2.replace("!!","")):
		#(len(s1) - len(s2) == 2 and s1.endswith("!!") and s1.startswith(s2)) or (len(s2) - len(s1) == 2 and s2.endswith("!!") and s2.startswith(s1)):
		return float(1.0)
	else:
		#Log.Debug("comparison: %s  %s %s"%(s1,Util.LevenshteinDistance(safe_unicode(s1),safe_unicode(s2)),
		#LevDist(safe_unicode(s1),safe_unicode(s2))))
		distance = LevDist(safe_unicode(s1),safe_unicode(s2))#Util.LevenshteinDistance(safe_unicode(s1),safe_unicode(s2))
		#Log('s1/s2: "%s" / "%s"' % (s1,s2))
		#Log('distance: %s' % distance)
		max_len	= float(max([ len(s1), len(s2) ]))
		#Log('max_len: %s' % max_len)
	
		ratio = 0.0
		try:
			ratio = float(1 - (distance/max_len))
		except:
			pass
	
		#Log('ratio: %s' % ratio)
		return ratio

def LongestCommonSubstring(S1, S2):
    M = [[0]*(1+len(S2)) for i in xrange(1+len(S1))]
    longest, x_longest = 0, 0
    for x in xrange(1,1+len(S1)):
        for y in xrange(1,1+len(S2)):
            if S1[x-1] == S2[y-1] or (S1[x-1] == "-" and S2[y-1] == " ") or (S1[x-1] == " " and S2[y-1] == "-"):
                M[x][y] = M[x-1][y-1] + 1
                if M[x][y]>longest:
                    longest = M[x][y]
                    x_longest  = x
            else:
                M[x][y] = 0
    return S1[x_longest-longest: x_longest]


def LevDist(s1, s2):
	d = []
	maxLen = max([len(s1),len(s2)])
	#make empty
	for i in range(len(s1)+1):
		d.append([])
		for j in range(len(s2)+1):
			d[i].append(maxLen)
	
	for i in range(len(s1)+1):
		d[i][0] = i
	for j in range(len(s2)+1):
		d[0][j] = j
	
	for i in range(len(s1)):
		for j in range(len(s2)):
			if (s1[i] == s2[j]) or (s1[i] == " " and s2[j] == "-") or (s1[i] == "-" and s2[j] == " "):
				d[i+1][j+1] = d[i][j]
			elif (s1[i].lower() == s2[j].lower()):
				d[i+1][j+1] = float(d[i][j] + 0.6)
			else:
				d[i+1][j+1] = min([d[i][j+1]+1,d[i+1][j]+1,d[i][j]+1])
	return d[len(s1)][len(s2)]


def safe_unicode(s,encoding='utf-8'):
	if s is None:
		return None
	if isinstance(s, basestring):
		if isinstance(s, types.UnicodeType):
			return s
		else:
			return s.decode(encoding)
	else:
		return str(s).decode(encoding)

"""
class TVDBAgent():
	
	name = 'TheTVDB'
	languages = [Locale.Language.English, 'fr', 'zh', 'sv', 'no', 'da', 'fi', 'nl', 'de', 'it', 'es', 'pl', 'hu', 'el', 'tr', 'ru', 'he', 'ja', 'pt', 'cs']
	
	def getGoogleResult(self, url):
		res = JSON.ObjectFromURL(url)
		if res['responseStatus'] != 200:
			res = JSON.ObjectFromURL(url, cacheTime=0)
		time.sleep(0.5)
		return res
	
	def dedupe(self, results):
		
		# make sure to keep the highest score for the id
		results.Sort('score', descending=True)
		
		toWhack = []
		resultMap = {}
		for result in results:
			if not resultMap.has_key(result.id):
				resultMap[result.id] = True
			else:
				toWhack.append(result)
		for dupe in toWhack:
			results.Remove(dupe)
	
	def searchByGuid(self, results, lang, title, year):
		
		# Compute the GUID
		guid = self.titleyear_guid(title,year)
		
		# Now see if we have any matches.
		score = 70
		maxLevBonus = 10
		maxPctBonus = 30
		try:
			res = XML.ElementFromURL(TVDB_GUID_SEARCH + guid[0:2] + '/' + guid + '.xml')
			matchesGroupedById = {}
			for match in res.xpath('//match'):
				id		= match.get('guid')
				count	= int(match.get('count'))
				pct		= int(match.get('percentage'))
				titleBonus	= int(self.lev_ratio(match.get('title'),title)*maxLevBonus)
				titleBonus	+= len(Util.LongestCommonSubstring(match.get('title'),title))
				bonus		= titleBonus
				if matchesGroupedById.has_key(id):
					i = matchesGroupedById.get(id).get('i')
					matchesGroupedById[id] = {
						 'guid': id,
						 'count':	matchesGroupedById.get(id).get('count') + count,
						 'pct':		matchesGroupedById.get(id).get('pct')   + pct,
						 'bonus':	matchesGroupedById.get(id).get('bonus') + bonus,
						 'i':		i + 1,
					}
				else:
					matchesGroupedById[id] = { 'guid': id, 'count': count, 'pct': pct, 'bonus': bonus, 'i': 1 }
			
			# get the summarized items sorted by the sumed 'count' field
			matches = matchesGroupedById.values()
			
			for match in matches:
				xml = XML.ElementFromString(GetResultFromNetwork(TVDB_SERIES_URL % (Dict['ZIP_MIRROR'], match.get('guid'), lang)))
				name = xml.xpath('//Data/Series/SeriesName')[0].text
				try: year = xml.xpath('//Data/Series/FirstAired')[0].text.split('-')[0]
				except: year = None
				levBonusAve = match.get('bonus') / 10 * (match.get('count')/10000)
				pctBonus	= int((match.get('pct')/100.0)*maxPctBonus)
				totalBonus	= levBonusAve+pctBonus
				results.Append(MetadataSearchResult(id=match.get('guid'), name=name, year=year, lang=lang, score=score+totalBonus))
		
		except Exception, e:
			Log(repr(e))
			pass
	
	def searchByWords(self, results, lang, origTitle, year):
		# Process the text.
		title = origTitle.lower()
		title = re.sub(r'[\'":\-&,.!~()]', ' ', title)
		title = re.sub(r'[ ]+', ' ', title)
		
		# Search for words.
		show_map = {}
		total_words = 0
		
		for word in title.split():
			if word not in ['a', 'the', 'of', 'and']:
				total_words += 1
				wordHash = hashlib.sha1()
				wordHash.update(word.encode('utf-8'))
				wordHash = wordHash.hexdigest()
				try:
					matches = XML.ElementFromURL(TVDB_QUICK_SEARCH + lang + '/' + wordHash[0:2] + '/' + wordHash + '.xml', cacheTime=60)
					for match in matches.xpath('//match'):
						id = match.get('id')
						title = match.get('title')
						titleYear = match.get('year')
						
						if not show_map.has_key(id):
							show_map[id] = [id, title, titleYear, 1]
						else:
							show_map[id] = [id, title, titleYear, show_map[id][3] + 1]
				except:
					pass
		
		resultList = show_map.values()
		resultList.sort(lambda x, y: cmp(y[3],x[3]))
		
		score = 70
		for result in resultList:
			theYear = result[2]
			
			# Remove year suffixes that can mess things up.
			searchTitle = origTitle
			if len(origTitle) > 8:
				searchTitle = re.sub(r'([ ]+\(?[0-9]{4}\)?)', '', searchTitle)
			
			foundTitle = result[1]
			if len(foundTitle) > 8:
				foundTitle = re.sub(r'([ ]+\(?[0-9]{4}\)?)', '', foundTitle)
			
			# Remove prefixes that can screw things up.
			searchTitle = re.sub('^[Bb][Bb][Cc] ', '', searchTitle)
			foundTitle = re.sub('^[Bb][Bb][Cc] ', '', foundTitle)
			
			# Adjust if both have 'the' prefix by adding a prefix that won't be stripped.
			distTitle = searchTitle
			distFoundTitle = foundTitle
			if searchTitle.lower()[0:4] == 'the ' and foundTitle.lower()[0:4] == 'the ':
				distTitle = 'xxx' + searchTitle
				distFoundTitle = 'xxx' + foundTitle
			
			# Score adjustments.
			theScore = score + len(Util.LongestCommonSubstring(distTitle, distFoundTitle))
			theScore = theScore + int(10 * self.lev_ratio(searchTitle, foundTitle)) + result[3] * 2
			
			if theYear != None and year != None:
				if theYear == year:
					theScore = theScore + 5
				elif theYear != year:
					theScore = theScore - 5
			
			results.Append(MetadataSearchResult(id=result[0], name=result[1], year=result[2], lang=lang, score=theScore))
		
		# Sort.
		results.Sort('score', descending=True)
		
		# Only return at most 20 results.
		if len(results) > 20:
			del results[20:]
	
	def searchForSeries(self, results, media, lang):
		
		doGoogleSearch = False
		
		# MAKE SURE WE USE precomposed form, since that seems to be what TVDB prefers.
		media.show = unicodedata.normalize('NFC', unicode(media.show)).strip()
		
		# If we got passed in something that looks like an ID, use it.
		#if len(media.show) > 3 and re.match('^[0-9]+$', media.show) is not None:
		#	url = TVDB_PROXY + '?tab=series&id=' + media.show
		#	self.TVDBurlParse(media, lang, results, 100, 0, url)
		
		if not doGoogleSearch:
			# GUID-based matches.
			self.searchByGuid(results, lang, media.show, media.year)
			
			# Try turbo word matches.
			self.searchByWords(results, lang, media.show, media.year)
			self.dedupe(results)
		Log.Debug(results)
		if len(results) == 0:
			doGoogleSearch = True
		
		mediaYear = ''
		if media.year is not None:
			mediaYear = ' (' + media.year + ')'
		w = media.show.lower().split(' ')
		keywords = ''
		for k in EXTRACT_AS_KEYWORDS:
			if k.lower() in w:
				keywords = keywords + k + '+'
		cleanShow =	self.util_cleanShow(media.show, SCRUB_FROM_TITLE_SEARCH_KEYWORDS)
		cs = cleanShow.split(' ')
		cleanShow = ''
		for x in cs:
			cleanShow = cleanShow + 'intitle:' + x + ' '
		
		cleanShow = cleanShow.strip()
		origShow = media.show
		SVmediaShowYear = {'normal':String.Quote((origShow + mediaYear).encode('utf-8'), usePlus=True).replace('intitle%3A', 'intitle:'),
							'clean': String.Quote((cleanShow + mediaYear).encode('utf-8'), usePlus=True).replace('intitle%3A','intitle:')}
		mediaShowYear = SVmediaShowYear['normal']
		
		if doGoogleSearch:
			searchVariations = [SVmediaShowYear]
			if media.year is not None:
				SVmediaShow = {'normal':String.Quote((origShow).encode('utf-8'), usePlus=True).replace('intitle%3A', 'intitle:'),
								'clean': String.Quote((cleanShow).encode('utf-8'), usePlus=True).replace('intitle%3A', 'intitle:')}
				searchVariations.append(SVmediaShow)
			
			#option to perform searches without the year, in the event we have no results over our match threshold
			for sv in searchVariations:
				#check to make sure we want to run these searches again WITHOUT the year hint, if there was one passed in
				if len(results) > 0:
					results.Sort('score', descending=True)
					if results[0].score >= 80:
						Log('skipping search engines')
						break #don't bother trying search without year, we have a match
				Log('hitting search engines')
				
				#run through several search engines
				resultDict = {}
				@parallelize
				def hitSearchEngines():
					for s in [GOOGLE_JSON_TVDB, GOOGLE_JSON_TVDB_TITLE, GOOGLE_JSON_IMDB, GOOGLE_JSON_BROAD]: #
						resultDict[s] = []
						@task
						def UpdateEpisode(s=s,sv=sv):
							hasResults = False
							if s in [GOOGLE_JSON_TVDB_TITLE]:
								tmpMediaShowYear = sv['clean'] #String.Quote((cleanShow + mediaYear).encode('utf-8'), usePlus=True).replace('intitle%3A','intitle:')
							else:
								tmpMediaShowYear = sv['normal']
							#make sure we have results and normalize
							if s.count('googleapis.com') > 0:
								jsonObj = self.getGoogleResult(s % (tmpMediaShowYear, keywords))['responseData']['results']
								if len(jsonObj) > 0:
									hasResults = True
							
							#loop through results
							if hasResults:
								for r in jsonObj:
									scorePenalty = 0
									url = None
									if s.count('googleapis.com') > 0:
										url = r['unescapedUrl']
									
									if url:
										resultDict[s].append((url, scorePenalty))
				
				@parallelize
				def loopResults():
					for s in resultDict:
						if s in [GOOGLE_JSON_TVDB, GOOGLE_JSON_IMDB, GOOGLE_JSON_TVDB_TITLE, GOOGLE_JSON_BROAD]:
							score = 99
						else:
							break
						for url, scorePenalty in resultDict[s]:
							@task
							def lookupResult(score=score, url=url, scorePenalty=scorePenalty):
								self.TVDBurlParse(media, lang, results, score, scorePenalty, url)
							score = score - 5
		
		#try an exact tvdb match
		try:
			Log('****************** mediaShowYear: ' + mediaShowYear)
			el = XML.ElementFromString(GetResultFromNetwork(TVDB_SEARCH_URL % (mediaShowYear, lang))).xpath('.//Series')[0]
			series_name = el.xpath('SeriesName')[0].text
			if series_name.lower().strip() == media.show.lower().strip():
				id = el.xpath('id')[0].text
				self.ParseSeries(media, el, lang, results, 99)
			elif series_name[:series_name.rfind('(')].lower().strip() == media.show.lower().strip():
				id = el.xpath('id')[0].text
				self.ParseSeries(media, el, lang, results, 96)
		except Exception, e:
			Log(repr(e))
			pass
		
		#run through tvRage -> tvdb name matches. the challenge with this is that it can only help a little...there is no tvrage->thetvdb lookup today.
		score = 100
		try:
			for r in XML.ElementFromString(GetResultFromNetwork(TVRAGE_SEARCH % mediaShowYear)).xpath('//show')[:4]:
				score = score - 3
				tvrageName = r.xpath('name')[0].text
				tvrageLink = r.xpath('link')[0].text
				network = HTML.ElementFromString(GetResultFromNetwork(tvrageLink.replace('www.tvrage.com', TVRAGE_PROXY))).xpath('//a[contains(@href,"/networks")]')[0].text_content()
				#Log("****************" + network	)
				try:
					ADVscore = 100
					year= ''
					if year:
						year = str(media.year)
					#language mapping by using http://www.thetvdb.com/wiki/index.php/Multi_Language :
					tvdbLang = THETVDB_LANGUAGES_CODE[lang]
					
					try:
						for el in HTML.ElementFromString(GetResultFromNetwork(TVDB_ADVSEARCH_NETWORK % (String.Quote(searchForTitle), year, String.Quote(network), tvdbLang))).xpath('//table[@id="listtable"]//tr')[1:3]:
							url = el.xpath('.//a')[0].get('href').replace('&amp;','&')
							self.TVDBurlParse(media, lang, results, ADVscore, 0, url)
							ADVscore = ADVscore - 5
					except:
						pass
				except:
					pass
		except Exception, e:
			Log(repr(e))
			pass
		
		self.dedupe(results)
		
		favorNewerShows = True
		if favorNewerShows:
			#hunt for duplicate shows with different years
			resultMap = {}
			for result in results:
				for check in results:
					if result.name == check.name and result.id != check.id:
						resultMap[result.year] = result
			
			years = resultMap.keys()
			years.sort(reverse=True)
			
			#bump the score of newer dupes
			i=0
			for y in years[:-1]:
				if resultMap[y].score <= resultMap[years[i+1]].score:
					resultMap[y].score = resultMap[years[i+1]].score + 1
		return results
	
	def TVDBurlParse(self, media, lang, results, score, scorePenalty, url):
		if url.count('tab=series&id='):
			seriesRx = 'tab=series&id=([0-9]+)'
			m = re.search(seriesRx, url)
		elif url.count('tab=seasonall&id='):
			seriesRx = 'tab=seasonall&id=([0-9]+)'
			m = re.search(seriesRx, url)
		else:
			seriesRx = 'seriesid=([0-9]+)'
			m = re.search(seriesRx, url)
		if m:
			id = m.groups(1)[0]
			try:
				xml = XML.ElementFromString(GetResultFromNetwork(TVDB_SERIES_URL % (Dict['ZIP_MIRROR'], id, lang)))
				if len(xml):
					self.ParseSeries(media, xml.xpath('//Series')[0], lang, results, score - scorePenalty)
			except:
				#somehow the tvdb id didn't work?
				Log('thetvdb.com series xml download exception.')
	
	def ParseSeries(self, media, el, lang, results, score):
		
		# Get attributes from the XML
		try:
			series_id = el.xpath('seriesid')[0].text
		except:
			series_id = el.xpath('id')[0].text
		
		series_name = el.xpath('SeriesName')[0].text
		try:
			series_year = el.xpath('FirstAired')[0].text[:4]
		except:
			series_year = None
		
		try:
			series_lang = el.xpath('language')[0].text
		except:
			series_lang = lang
		
		if not series_name:
			return
		
		if not media.year:
			clean_series_name = series_name.replace('(' + str(series_year) + ')','').strip().lower()
		else:
			clean_series_name = series_name.lower()
		
		cleanShow = self.util_cleanShow(media.show, NETWORK_IN_TITLE)
		
		#Log(media.show + ' | found: ' + series_name + ' score1: +[original] ' + str(score))
		
		substringLen = len(Util.LongestCommonSubstring(cleanShow.lower(), clean_series_name))
		cleanShowLen = len(cleanShow)
		
		maxSubstringPoints = 5.0 #use a float
		score = score + int((maxSubstringPoints * substringLen)/cleanShowLen) # max 15 for best substring match
		#Log(media.show + ' | found: ' + series_name + ' score2: +[longest substring]: ' + str(score))
		
		distanceFactor = .6
		score = score - int(distanceFactor * Util.LevenshteinDistance(cleanShow.lower(), clean_series_name))
		#Log(media.show + ' | found: ' + series_name + ' score3: +[levenshteindistance]: ' + str(score))
		
		if series_year and media.year:
			if media.year == series_year:
				score = score + 10
			else:
				score = score - 10
		
		#sanity check to make sure we have SOME common substring
		if (float(substringLen) / cleanShowLen) < .15: #if we don't have at least 15% in common, then penalize below the 80 point threshold
			score = score - 25
		
		#Log(media.show + ' | found: ' + series_name + ' score4: +[year match]: ' + str(score))
		
		# Add a result for this show
		results.Append(
			MetadataSearchResult(
				id		= series_id,
				name	= series_name,
				year	= series_year,
				lang	= series_lang,
				score	= score
			)
		)
	
	def readTags(self, element, list, name):
		try:
			el_text = lambda element, xp: element.xpath(xp)[0].text
			tag_text = el_text(element, name)
			if tag_text.find('|') != -1:
				tags = tag_text.split('|')
			else:
				tags = tag_text.split(',')
			
			tags = [tag.strip() for tag in tags if len(tag) > 0]
			list.clear()
			for tag in tags:
				if tag not in list:
					list.add(tag)
		except:
			pass
	
	def fixBrokenXml(self, xml):
		if xml.count('<?xml') > 1:
			xml = xml[xml.rfind('<?xml'):]
			if xml.count('</Data>') > 1:
				xml = xml[:-7]
		
		return xml
	
	def update(self, metadata, media, lang):
		Log("def update()")
		zip_url = TVDB_ZIP_URL % (Dict['ZIP_MIRROR'], metadata.id, lang)
		banner_root = TVDB_BANNER_URL % Dict['IMG_MIRROR']
		
		# Get the show's zipped data
		zip_data = GetResultFromNetwork(zip_url)
		zip_archive = Archive.Zip(zip_data)
		
		# Extract the XML files from the archive. Work around corrupt XML.
		root_el = XML.ElementFromString(self.fixBrokenXml(zip_archive[lang+'.xml']))
		actors_el = XML.ElementFromString(self.fixBrokenXml(zip_archive['actors.xml']))
		banners_el =XML.ElementFromString(self.fixBrokenXml(zip_archive['banners.xml']))
		
		# Close the archive
		del zip_archive
		
		# Get the root element
		series_el = root_el.xpath('Series')[0]
		
		# Convenience functions
		el_text = lambda element, xp: element.xpath(xp)[0].text if element.xpath(xp)[0].text else ''
		parse_date = lambda s: Datetime.ParseDate(s).date()
		
		# Copy attributes from the XML element to the metadata object
		metadata.title = el_text(series_el, 'SeriesName')
		metadata.summary = el_text(series_el, 'Overview')
		metadata.content_rating = el_text(series_el, 'ContentRating')
		metadata.studio = el_text(series_el, 'Network')
		try:
			originally_available_at = el_text(series_el, 'FirstAired')
			if len(originally_available_at) > 0:
				metadata.originally_available_at = parse_date(originally_available_at)
			else:
				metadata.originally_available_at = None
		except: pass
		try: metadata.duration = int(el_text(series_el, 'Runtime')) * 60 * 1000
		except: pass
		try: metadata.rating = float(el_text(series_el, 'Rating'))
		except: pass
		
		self.readTags(series_el, metadata.genres, 'Genre')
		
		# Get episode data
		@parallelize
		def UpdateEpisodes():
			
			for episode_el in root_el.xpath('Episode'):
				
				# Get the season and episode numbers
				season_num = el_text(episode_el, 'SeasonNumber')
				episode_num = el_text(episode_el, 'EpisodeNumber')
				
				if media is not None:
					# Also get the air date for date-based episodes.
					try:
						originally_available_at = parse_date(el_text(episode_el, 'FirstAired'))
						date_based_season = originally_available_at.year
					except:
						originally_available_at = date_based_season = None
					
					if not ((season_num in media.seasons and episode_num in media.seasons[season_num].episodes) or
									(originally_available_at is not None and date_based_season in media.seasons and originally_available_at in media.seasons[date_based_season].episodes) or
									(originally_available_at is not None and season_num in media.seasons and originally_available_at in media.seasons[season_num].episodes)):
						#Log("No media for season %s episode %s - skipping population of episode data", season_num, episode_num)
						continue
				
				# Get the episode object from the model
				episode = metadata.seasons[season_num].episodes[episode_num]
				
				# Create a task for updating this episode
				@task
				def UpdateEpisode(episode=episode, episode_el=episode_el):
					
					# Copy attributes from the XML
					episode.title = el_text(episode_el, 'EpisodeName')
					episode.summary = el_text(episode_el, 'Overview')
					
					try: episode.absolute_number = int(el_text(episode_el, 'absolute_number'))
					except: pass
					
					rating = el_text(episode_el, 'Rating')
					if rating != None and len(rating) > 0: episode.rating = float(rating)
					
					try:
						originally_available_at = el_text(episode_el, 'FirstAired')
						if originally_available_at != None and len(originally_available_at) > 0:
							episode.originally_available_at = parse_date(originally_available_at)
					except:
						pass
					
					self.readTags(episode_el, episode.directors, 'Director')
					self.readTags(episode_el, episode.writers, 'Writer')
					
					# Download the episode thumbnail
					valid_names = list()
					
					if len(episode_el.xpath('filename')) > 0:
						thumb_file = el_text(episode_el, 'filename')
						if thumb_file != None and len(thumb_file) > 0:
							thumb_url = banner_root + thumb_file
							thumb_data = GetResultFromNetwork(thumb_url, False)
							
							# Check that the thumb doesn't already exist before downloading it
							valid_names.append(thumb_url)
							if thumb_url not in episode.thumbs:
								try:
									episode.thumbs[thumb_url] = Proxy.Media(thumb_data)
								except:
									# tvdb doesn't have a thumb for this show
									pass
					
					episode.thumbs.validate_keys(valid_names)
		
		# Maintain a list of valid image names
		valid_names = list()
		
		@parallelize
		def DownloadImages():
			
			# Add a download task for each image
			i = 0
			for banner_el in banners_el.xpath('Banner'):
				i += 1
				@task
				def DownloadImage(metadata=metadata, banner_el=banner_el, i=i, valid_names=valid_names):
					
					# Parse the banner.
					banner_type, banner_path, banner_lang, banner_thumb, proxy = self.parse_banner(banner_el)
					
					# Check that the language matches
					if (banner_lang != lang) and (banner_lang != 'en'):
						return
					
					# Compute the banner name and prepare the data
					banner_name = banner_root + banner_path
					banner_url = banner_root + banner_thumb
					
					valid_names.append(banner_name)
					
					def banner_data(path):
						return GetResultFromNetwork(path, False)
					
					# Find the attribute to add to based on the image type, checking that data doesn't
					# already exist before downloading
					if banner_type == 'fanart' and banner_name not in metadata.art:
						try: metadata.art[banner_name] = proxy(banner_data(banner_url), sort_order=i)
						except: pass
					
					elif banner_type == 'poster' and banner_name not in metadata.posters:
						try: metadata.posters[banner_name] = proxy(banner_data(banner_url), sort_order=i)
						except: pass
					
					elif banner_type == 'series':
						if banner_name not in metadata.banners:
							try: metadata.banners[banner_name] = proxy(banner_data(banner_url), sort_order=i)
							except: pass
					
					elif banner_type == 'season':
						banner_type_2 = el_text(banner_el, 'BannerType2')
						season_num = el_text(banner_el, 'Season')
						
						# Need to check for date-based season (year) as well.
						try:
							date_based_season = (int(season_num) + metadata.originally_available_at.year - 1)
						except:
							date_based_season = None
						
						if media is None or season_num in media.seasons or date_based_season in media.seasons:
							if banner_type_2 == 'season' and banner_name not in metadata.seasons[season_num].posters:
								try: metadata.seasons[season_num].posters[banner_name] = proxy(banner_data(banner_url), sort_order=i)
								except: pass
							
							elif banner_type_2 == 'seasonwide' and banner_name not in metadata.seasons[season_num].banners:
								try: metadata.seasons[season_num].banners[banner_name] = proxy(banner_data(banner_url), sort_order=i)
								except: pass
						
						else:
							#Log('No media for season %s - skipping download of %s', season_num, banner_name)
							pass
		
		# Fallback to foreign art if localized art doesn't exist.
		if len(metadata.art) == 0 and lang == 'en':
			i = 0
			for banner_el in banners_el.xpath('Banner'):
				banner_type, banner_path, banner_lang, banner_thumb, proxy = self.parse_banner(banner_el)
				banner_name = banner_root + banner_path
				if banner_type == 'fanart' and banner_name not in metadata.art:
					try: metadata.art[banner_name] = proxy(self.banner_data(banner_root + banner_thumb), sort_order=i)
					except: pass
		
		# Check each poster, background & banner image we currently have saved. If any of the names are no longer valid, remove the image
		metadata.posters.validate_keys(valid_names)
		metadata.art.validate_keys(valid_names)
		metadata.banners.validate_keys(valid_names)
	
	def parse_banner(self, banner_el):
		el_text = lambda element, xp: element.xpath(xp)[0].text if element.xpath(xp)[0].text else ''
		
		# Get the image attributes from the XML
		banner_type = el_text(banner_el, 'BannerType')
		banner_path = el_text(banner_el, 'BannerPath')
		try:
			banner_thumb = el_text(banner_el, 'ThumbnailPath')
			proxy = Proxy.Preview
		except:
			banner_thumb = banner_path
			proxy = Proxy.Media
		banner_lang = el_text(banner_el, 'Language')
		
		return (banner_type, banner_path, banner_lang, banner_thumb, proxy)
	
	def banner_data(self, path):
		return GetResultFromNetwork(path, False)
	
	def util_cleanShow(self, cleanShow, scrubList):
		for word in scrubList:
			c = word.lower()
			l = cleanShow.lower().find('(' + c + ')')
			if l >= 0:
				cleanShow = cleanShow[:l] + cleanShow[l+len(c)+2:]
			l = cleanShow.lower().find(' ' + c)
			if l >= 0:
				cleanShow = cleanShow[:l] + cleanShow[l+len(c)+1:]
			l = cleanShow.lower().find(c + ' ')
			if l >= 0:
				cleanShow = cleanShow[:l] + cleanShow[l+len(c)+1:]
		return cleanShow
	
	def identifierize(self, string):
		string = re.sub( r"\s+", " ", string.strip())
		string = unicodedata.normalize('NFKD', self.safe_unicode(string))
		string = re.sub(r"['\"!?@#$&%^*\(\)_+\.,;:/]","", string)
		string = re.sub(r"[_ ]+","_", string)
		string = string.strip('_')
		return string.strip().lower()
	
	def safe_unicode(self, s,encoding='utf-8'):
		if s is None:
			return None
		if isinstance(s, basestring):
			if isinstance(s, types.UnicodeType):
				return s
			else:
				return s.decode(encoding)
		else:
			return str(s).decode(encoding)
	
	def guidize(self,string):
		hash = hashlib.sha1()
		hash.update(string.encode('utf-8'))
		return hash.hexdigest()
	
	def titleyear_guid(self, title, year=None):
		if title is None:
			title = ''
		
		if year == '' or year is None or not year:
			string = u"%s" % self.identifierize(title)
		else:
			string = u"%s_%s" % (self.identifierize(title), year)
		return self.guidize(string)
	
	def lev_ratio(self,s1,s2):
		distance = Util.LevenshteinDistance(self.safe_unicode(s1),self.safe_unicode(s2))
		#Log('s1/s2: "%s" / "%s"' % (s1,s2))
		#Log('distance: %s' % distance)
		max_len	= float(max([ len(s1), len(s2) ]))
		#Log('max_len: %s' % max_len)
		
		ratio = 0.0
		try:
			ratio = float(1 - (distance/max_len))
		except:
			pass
		
		#Log('ratio: %s' % ratio)
		return ratio
	
	def best_title_by_language(self, lang, localTitle, tvdbID ):
		
		## this returns not only the best title, but the best
		## levenshtien ratio found amongst all of the titles
		## in the title list... the lev ratio is to give an overall
		## confidence that the local title corresponds to the
		## tvdb id.. even if the picked title is in a language
		## other than the locally named title
		
		titles = { 'best_lev_ratio': { 'title': None, 'lev_ratio': -1.0 } } # -1 to force > check later
		try:
			res = XML.ElementFromURL(TVDB_TITLE_SEARCH + tvdbID[0:2] + '/' + tvdbID + '.xml')
			for row in res.xpath("/records/record"):
				t = row['title']
				l = row['lang']
				lev	 = self.lev_ratio(localTitle,t)
				titles[lang] = { 'title': t, 'lev_ratio': lev, 'lang': l }
				if lev > titles.get('best_lev_ratio').get('lev_ratio'):
					titles['best_lev_ratio'] = { 'title': t, 'lev_ratio': lev, 'lang': l }
		except Exception, e:
			Log(e)
			return (localTitle, lang, 0.0)
		
		bestLevRatio = titles.get('best_lev_ratio').get('lev_ratio')
		if bestLevRatio < 0:
			return (localTitle, lang, 0.0)
		
		useTitle = None
		if titles.has_key(lang):
			useTitle = titles.get(lang)
		elif titles.has_key('en'):
			useTitle = titles.get('en')
		else:
			useTitle = titles.get('best_lev_ratio')
		
		return (useTitle.get('title'), useTitle.get('lang'), useTitle.get('lev_ratio'))
	

"""