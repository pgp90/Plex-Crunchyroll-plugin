
ENABLE_DEBUG_MENUS           = False
ENABLE_UTILS                 = True

BASE_URL                     = "http://www.crunchyroll.com"
API_URL                      = "://www.crunchyroll.com/ajax/"

# boxee search requires extra code, rss search returns less results,
# boxee feed has duration info.
# potatoh, potatah
SEARCH_URL                   = "http://www.crunchyroll.com/rss/search?q="
#SEARCH_URL                  = "http://www.crunchyroll.com/boxee_feeds/search?q="
SERIES_FEED_BASE_URL         = "http://www.crunchyroll.com/boxee_feeds/"
POPULAR_DRAMA_FEED           = "http://feeds.feedburner.com/crunchyroll/rss/drama/popular"
POPULAR_ANIME_FEED           = "http://feeds.feedburner.com/crunchyroll/rss/anime/popular"
POPULAR_FEED                 = "http://feeds.feedburner.com/crunchyroll/rss/popular"

RECENT_ANIME_FEED            = "http://feeds.feedburner.com/crunchyroll/rss/anime"
RECENT_DRAMA_FEED            = "http://feeds.feedburner.com/crunchyroll/rss/drama"
RECENT_VIDEOS_FEED           = "http://feeds.feedburner.com/crunchyroll/rss"

CRUNCHYROLL_PLUGIN_PREFIX    = "/video/CrunchyRoll"
CRUNCHYROLL_ART              = 'art-default3.jpg'
CRUNCHYROLL_ICON             = 'icon-default.png'

ANIME_ICON                   = CRUNCHYROLL_ICON#'icon-anime.png'
DRAMA_ICON                   = CRUNCHYROLL_ICON#'icon-drama.png'
QUEUE_ICON                   = CRUNCHYROLL_ICON#'icon-queue.png'
SEARCH_ICON                  = CRUNCHYROLL_ICON # FIXME: there has to be a standard search icon somewhere...

PREFS_ICON                   = 'icon-prefs.png'
DEBUG_ICON                   = PREFS_ICON
UTILS_ICON                   = PREFS_ICON

THUMB_QUALITY                = {"Low":"_medium","Medium":"_large","High":"_full"}
VIDEO_QUALITY                = {"SD":"360","480P":"480","720P":"720", "1080P":"1080"}

LAST_PLAYER_VERSION = "20111130163346.fb103f9787f179cd0f27be64da5c23f2"
PREMIUM_TYPE_ANIME = '2'
PREMIUM_TYPE_DRAMA = '4'
ANIME_TYPE = "Anime"
DRAMA_TYPE = "Drama"

# these USED to be long fetches, but now the rss feeds are truncated at cr.com to the latest 40 
# episodes or so. Therefore, precaching doesn't matter much now
PRECACHE_URLS = ["http://www.crunchyroll.com/bleach.rss", "http://www.crunchyroll.com/naruto-shippuden.rss"]

Boxee2Resolution = {'12':360, '20':480, '21':720, '23':1080}
Resolution2Quality = {360:"SD", 480: "480P", 720: "720P", 1080: "1080P"}
Quality2Resolution = {"SD":360, "480P":480, "720P":720, "1080P": 1080, "Highest Available":1080, "Ask":360}

# these don't map too well to the Movie-style ratings, but also don't have 
# a human-readable semantic, so:
SAFESURF_MAP = { 
#	0: "NR", # unused, 0 has no meaning in safe surf, so it is an error.
	1: "G",
	2: "Y7",
	3: "TEEN",   # kinda like PG, but doesn't suggest parental guidance, so whatev
	4: "TV-14",  # kids, you can get away with this one.
	5: "MA",     # this is mature content (Adult supervision). It includes horror movies [!]
	6: "MA",     # Adults
	7: "R",      # Adults ONLY
	8: "NC-17"   # Hardcore
}

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
	'Martial Arts':'martial arts',
	'Mecha':'mecha',
	'Military':'military',
	'Parody':'parody',
	'Psychological':'psychological',
	'Romance':'romance',
	'Science Fiction':'science fiction',
	'Shoujo':'shoujo',
	'Slice of Life':'slice of life',
	'Space':'space',
	'Sports':'sports',
	'Supernatural':'supernatural',
	'Tournament':'tournament'
}

DRAMA_GENRE_LIST = {
	'Chinese':'chinese',
	'Japanese':'japanese',
	'Korean':'korean',
	'Action':'action',
	'Comedy':'comedy',
	'Crime':'crime',
	'Family': 'family',
	'Food':'food',
	'Historical':'historical',
	'Horror':'horror',
	'Martial Arts': 'martial+arts',
	'Romance':'romance',
	'Thriller':'thriller'
	}

JUST_USE_WIDE = False
CHECK_PLAYER = False
SPLIT_LONG_LIST = True

LOGIN_GRACE = 1800

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

