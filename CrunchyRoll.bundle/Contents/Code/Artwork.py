def getEpisodeArtUrl(episode):
    """
    return the best background art URL for the passed episode.
    """
    #TODO: consider reimplementing the fanart part
    artUrl = episode['art']
    if artUrl == "" or artUrl is None:
        artUrl = R(CRUNCHYROLL_ART)
    Log.Debug("episode art url: %s"%artUrl)
    return artUrl

def getEpisodeThumbUrl(episode):
    """
    return the best thumbnail URL for the passed episode.
    """
    #TODO: consider reimplementing the fanart part
    thumbUrl = episode['thumb']
    if thumbUrl == "" or thumbUrl is None:
        thumbUrl = R(CRUNCHYROLL_ICON)
    Log.Debug("episode thumb url: %s"%thumbUrl)
    return url

def getSeasonArtUrl(season):
    """
    return the best background art URL for the passed season.
    """
    #TODO: consider reimplementing the fanart part
    artUrl = season['art']
    if artUrl == "" or artUrl is None:
        artUrl = R(CRUNCHYROLL_ART)
    Log.Debug("season art url: %s"%artUrl)
    return artUrl

def getSeasonThumbUrl(season):
    """
    return the best thumbnail URL for the passed season.
    """
    #TODO: consider reimplementing the fanart part
    thumbUrl = season['thumb']
    if thumbUrl == "" or thumbUrl is None:
        thumbUrl = R(CRUNCHYROLL_ICON)
    Log.Debug("season thumb url: %s"%thumbUrl)
    return url

def getSeriesArtUrl(series):
    """
    return the best background art URL for the passed series.
    """
    #TODO: consider reimplementing the fanart part
    artUrl = series['art']
    if artUrl == "" or artUrl is None:
        artUrl = R(CRUNCHYROLL_ART)
    Log.Debug("series art url: %s"%artUrl)
    return artUrl

def getSeriesThumbUrl(series):
    """
    return the best thumbnail URL for the passed series.
    """
    #TODO: consider reimplementing the fanart part
    thumbUrl = series['thumb']
    if thumbUrl == "" or thumbUrl is None:
        thumbUrl = R(CRUNCHYROLL_ICON)
    Log.Debug("series thumb url: %s"%thumbUrl)
    return url

def getThumb(url):
    """
    Try to find a better thumb than the one provided via url.
    The thumb data returned is either an URL or the image data itself.
    """
    ret = None
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

def getArt(url):
    ret = None
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
