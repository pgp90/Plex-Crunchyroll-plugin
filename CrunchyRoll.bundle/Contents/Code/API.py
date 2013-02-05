# -*- coding: utf-8 -*-
import re
import urllib2
import time, os, re
from Cookie import BaseCookie
import plistlib
from datetime import datetime, timedelta

from constants2 import *

#from CrunchyrollUserAPI import *
#from CrunchyrollDataAPI import *
#from DebugCode import *
#from Artwork import *


PLUGIN_NAMESPACE = {"media":"http://search.yahoo.com/mrss/", "crunchyroll":"http://www.crunchyroll.com/rss"}
class API(object):
    @staticmethod
    def testEmbed(mediaId):
        """
        just a simple test of the ajax request to get the html for embedding a 720p video....
        """
        API.login()
        
        try:
            valuesDict = { "req": "RpcApiMedia_GetEmbedCode", "media_id": str(mediaId), "width": "1280", "height": "752" }
            response = API.makeAPIRequest(valuesDict)
    #        Log.Debug(response)
            response = JSON.ObjectFromString(response)
            
            Log.Debug("response...")
            if response.get('result_code') == 1:
                Log.Debug(response.get('data'))
            else:
                Log.Debug("bad....")
        except Exception, arg:
            Log.Error("####Sorry, an error occured when logging in:")
            Log.Error(repr(Exception) + " "  + repr(arg))
        
        return
    
    
        
    
    @staticmethod
    def getSortTitle(dictList):
        """
        get the 'title' key and return the sortable title as string
        """
        title = dictList['title'].lower().strip()
        firstword = title.split(" ",1)[0]
        if firstword in ['a', 'an', 'the']:
            title = title.split(firstword, 1)[-1]
        return title.strip()
    
    
    
    
    """
                    "title": title,
                    "upNextMediaId": episodeMediaId,
                    "seriesId": seriesId#,
    """
    """
    schema inside Dict{}
        all items (even movies) can be referenced by a the series dict.
        series are known by seriesID (a unique number), provided by crunchyroll.com
        Dict['series'] =
        { seriesId: {
            "title": title,
            "seriesId": seriesId,
            "tvdbId": tvdbId,
            "description": seriesDescription,
            "thumb": thumb,
            "art": art,
            "rating": rating,
            "simpleRating": simpleRating,
            "dateUpdated": dateUpdated,
            "seasonList": []
            }
        }
    """
    """
        Dict['seasons'] =
        { seasonId: {
            "title": title,
            "seasonId": seasonId,
            "seriesId": seriesId,
            "thumb": thumb,
            "art": art,
            "epsRetreived": None,
            "epList": [],
            "dateUpdated": dateUpdated,
            "seasonNumber": seasonNumber,
            "description": description
            }
        }
    """
    """ 
        episodesList contains playable media (it's actually a dict, but let's not get finicky).
        episodes are known by mediaId (a unique number), provided at crunchyroll.com
        This is an episode entry in the list:
        Dict['episodes'] =
        { mediaId: {
            "title": episodeTitle,
            "description": episodeDescription,
            "mediaId": mediaId,
            "episodeNumber": episodeNumber,
            "freePubDate": freePubDate,
            "freePubDateEnd": freePubDateEnd,
            "premiumPubDate": premiumPubDate,
            "premiumPubDateEnd": premiumPubDateEnd,
            "publisher": publisher,
            "duration": duration,
            "subtitleLanguages": subtitleLanguages,
            "rating": rating,
            "simpleRating": simpleRating,
            "countries": countries,
            "dateUpdated": dateUpdated,
            "season": season,
            "seasonId": seasonId,
            "mediaLink": mediaLink,
            "category": category,
            "thumb": thumb,
            "art": art,
            "seriesTitle": seriesTitle,
            "availableResolutions": availableResolutions
            }
        }
    """
    
    
    
    
    @staticmethod
    def cacheFullSeriesList():
        #startTime = Datetime.Now()
        feedHtml = XML.ElementFromURL(SERIES_FEED_URL,cacheTime=SERIES_FEED_CACHE_TIME)
    #    Log.Debug(str(feedHtml))
        items = feedHtml.xpath("//item")
        if Dict['series'] is None:
            Dict['series'] = {}
        
        if Dict['seasons'] is None:
            Dict['seasons'] = {}
        
        dateUpdated = datetime.utcnow()
        
        for item in items:
    #        debugFeedItem(item.xpath("."))
            seasonId = int(item.xpath("./guid")[0].text.split(".com/")[1].split("-")[1])
            try:
                seasonNumber = int(item.xpath("./crunchyroll:season", namespaces=PLUGIN_NAMESPACE)[0].text)
            except:
                seasonNumber = None
            thumb = str(item.xpath("./media:thumbnail", namespaces=PLUGIN_NAMESPACE)[0].get('url')).split("_")[0]+"_full.jpg"
            art = thumb
            seasonTitle = item.xpath("./title")[0].text
            seriesId = int(item.xpath("./crunchyroll:series-guid", namespaces=PLUGIN_NAMESPACE)[0].text.split(".com/series-")[1])
            simpleRating = item.xpath("./media:rating", namespaces=PLUGIN_NAMESPACE)[0].text
            tvdbId = None
            description = item.xpath("./description")[0].text
            seriesDescription = None
            
            if not str(seriesId) in Dict['series'] or Dict['series'][str(seriesId)] is None:
                series = {
                    "title": seasonTitle,
                    "seriesId": seriesId,
                    "tvdbId": tvdbId,
                    "description": seriesDescription,
                    "thumb": thumb,
                    "art": art,
                    "rating": None,
                    "simpleRating": simpleRating,
                    "dateUpdated": dateUpdated,
                    "seasonList": []
                }
                Dict['series'][str(seriesId)] = series
            
            if not seasonId in Dict['series'][str(seriesId)]['seasonList']:
                Dict['series'][str(seriesId)]['seasonList'].append(seasonId)
            
            Dict['series'][str(seriesId)]['dateUpdated'] = dateUpdated
            
            if not str(seasonId) in Dict['seasons'] or Dict['seasons'][str(seasonId)] is None:
                season = {
                    "title": seasonTitle,
                    "seasonId": seasonId,
                    "seriesId": seriesId,
                    "thumb": thumb,
                    "art": art,
                    "epsRetreived": None,
                    "epList": [],
                    "dateUpdated": dateUpdated,
                    "seasonNumber": seasonNumber,
                    "description": description
                }
                Dict['seasons'][str(seasonId)] = season
            
        
        #make sure that the season list for each series is in order
        for seriesid in Dict['series'].keys():
            series = Dict['series'][seriesid]
    #        Log.Debug(series['seasonList'])
            newSeasonList = sorted(series['seasonList'], key=lambda k: Dict['seasons'][str(k)]['seasonNumber'])
            Dict['series'][seriesid]['seasonList'] = newSeasonList
        
    @staticmethod
    def cacheEpisodeListForSeason(seasonId):
#        from datetime import datetime, timedelta
    #    from collections import OrderedDict
        
        if str(seasonId) in BAD_SEASON_IDS:
            return
        
        Log.Debug("running _cacheEpisodeListForSeason")
    
        #startTime = Datetime.Now()
        feed =  "%s%s" % (SEASON_FEED_BASE_URL, str(seasonId))
        feedHtml = XML.ElementFromURL(feed,cacheTime=SERIES_FEED_CACHE_TIME)
        items = feedHtml.xpath("//item")
        if len(items) == 0:
            return
        if Dict['episodes'] is None:
            Dict['episodes'] = {}
        
        dateUpdated = datetime.utcnow()
        
        try:
            rating = feedHtml.xpath("//rating")[0].text
    #        Log.Debug(rating)
            
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
        
        seriesTitle = feedHtml.xpath("//crunchyroll:seriesTitle", namespaces=PLUGIN_NAMESPACE)[0].text
        seriesId = Dict['seasons'][str(seasonId)]["seriesId"]
        if not Dict['series'][str(seriesId)]["title"] == seriesTitle:
            Log.Debug("Series (%s) title (%s) does not match the one on the season (%s) feed (%s)." % (str(seriesId), Dict['series'][str(seriesId)]["title"], str(seasonId), seriesTitle))
            Dict['series'][str(seriesId)]["title"] = seriesTitle
        episodeList = Dict['seasons'][str(seasonId)]["epList"]
        for item in items:
            mediaId = int(item.xpath("./crunchyroll:mediaId", namespaces=PLUGIN_NAMESPACE)[0].text)
    #        Log.Debug("mediaId: %s"%str(mediaId))
            modifiedDate = item.xpath("./crunchyroll:modifiedDate", namespaces=PLUGIN_NAMESPACE)[0].text
    #        Log.Debug(modifiedDate)
#            feedEntryModified = datetime.strptime(modifiedDate, "%a, %d %b %Y %H:%M:%S %Z")
            
            if not str(mediaId) in Dict['episodes']:# or Dict['episodes'][str(mediaId)]["dateUpdated"] <= feedEntryModified:
                #TODO: should use <title> or <crunchyroll:episodeTitle> for the title?
    #            episodeTitle = " "
    #            Log.Debug(episodeTitle)
                try: episodeTitle = item.xpath("./crunchyroll:episodeTitle", namespaces=PLUGIN_NAMESPACE)[0].text
                except: episodeTitle = item.xpath("./title")[0].text
                if episodeTitle is None:
                    episodeTitle = item.xpath("./title")[0].text
    #            Log.Debug(episodeTitle)
                if episodeTitle.startswith("%s - " % seriesTitle):
                    episodeTitle = episodeTitle.replace("%s - " % seriesTitle, "")
                elif episodeTitle.startswith("%s Season " % seriesTitle):
                    episodeTitle = episodeTitle.replace("%s Season " % seriesTitle, "")
                    episodeTitle = episodeTitle.split(" ", 1)[1].lstrip("- ")
    
                episodeDescription = item.xpath("./description")[0].text
                if "/><br />" in episodeDescription:
                    episodeDescription = episodeDescription.split("/><br />")[1]
                
                try: episodeNumber = int(item.xpath("./crunchyroll:episodeNumber", namespaces=PLUGIN_NAMESPACE)[0].text)
                except: episodeNumber = 0
                freePubDateStr = str(item.xpath("./crunchyroll:freePubDate", namespaces=PLUGIN_NAMESPACE)[0].text)
#                datetime.strptime()
                freePubDate = datetime.strptime(freePubDateStr, "%a, %d %b %Y %H:%M:%S %Z")
                freePubDateEnd = datetime.strptime(item.xpath("./crunchyroll:freeEndPubDate", namespaces=PLUGIN_NAMESPACE)[0].text, FEED_DATE_FORMAT)
                premiumPubDate = datetime.strptime(item.xpath("./crunchyroll:premiumPubDate", namespaces=PLUGIN_NAMESPACE)[0].text, FEED_DATE_FORMAT)
                premiumPubDateEnd = datetime.strptime(item.xpath("./crunchyroll:premiumEndPubDate", namespaces=PLUGIN_NAMESPACE)[0].text, FEED_DATE_FORMAT)
                try: publisher = item.xpath("./crunchyroll:publisher", namespaces=PLUGIN_NAMESPACE)[0].text
                except: publisher = ""
                try: duration = int(item.xpath("./crunchyroll:duration", namespaces=PLUGIN_NAMESPACE)[0].text) * 1000
                except: duration = 0
                try: subtitleLanguages = item.xpath("./crunchyroll:subtitleLanguages", namespaces=PLUGIN_NAMESPACE)[0].text.split(",")
                except: subtitleLanguages = ""
                simpleRating = item.xpath("./media:rating", namespaces=PLUGIN_NAMESPACE)[0].text
                countries = item.xpath("./media:restriction", namespaces=PLUGIN_NAMESPACE)[0].text.strip().split(" ")
                try: season = int(item.xpath("./crunchyroll:season", namespaces=PLUGIN_NAMESPACE)[0].text)
                except: season = 0
                mediaLink = item.xpath(EPISODE_MEDIA_LINK_XPATH)[0].text.strip()
                category = item.xpath("./category")[0].text
                try: thumb = str(item.xpath("./enclosure")[0].get('url')).split("_")[0]+"_full.jpg"
                except: thumb = None
                art = thumb
                
                #FIXME: figure out how to deal with video resolutions
                availableResolutions = None
                
                episode = {
                    "title": episodeTitle,
                    "description": episodeDescription,
                    "mediaId": mediaId,
                    "episodeNumber": episodeNumber,
                    "freePubDate": freePubDate,
                    "freePubDateEnd": freePubDateEnd,
                    "premiumPubDate": premiumPubDate,
                    "premiumPubDateEnd": premiumPubDateEnd,
                    "publisher": publisher,
                    "duration": duration,
                    "subtitleLanguages": subtitleLanguages,
                    "rating": rating,
                    "simpleRating": simpleRating,
                    "countries": countries,
                    "dateUpdated": dateUpdated,
                    "season": season,
                    "seasonId": seasonId,
                    "mediaLink": mediaLink,
                    "category": category,
                    "thumb": thumb,
                    "art": art,
                    "seriesTitle": seriesTitle,
                    "availableResolutions": availableResolutions
                }
                
                Dict['episodes'][str(mediaId)] = episode
                if not str(mediaId) in episodeList:
                    episodeList.append(mediaId)
            
    #    list(OrderedDict.fromkeys('abracadabra'))
    #    episodeList = list(set(episodeList))
        Dict['seasons'][str(seasonId)]["epList"] = episodeList
        Dict['seasons'][str(seasonId)]["epsRetreived"] = dateUpdated
        Dict['seasons'][str(seasonId)]["epList"] = sorted(Dict['seasons'][str(seasonId)]["epList"], key=lambda k: Dict['episodes'][str(k)]["episodeNumber"])
    
    @staticmethod
    def getEpisodeListFromFeed(feed, sort=True):
    #    import datetime
        try:
            #TODO: find a way to get season/series ids for the episodes....
            episodeList = []
            dateUpdated = datetime.utcnow()
            
            # timeout errors driving me nuts, so
            req = HTTP.Request(feed, timeout=100)
            feedHtml = XML.ElementFromString(req.content)
    #        feedHtml = XML.ElementFromURL(feed)
            items = feedHtml.xpath("//item")
    #        seriesTitle = feedHtml.xpath("//channel/title")[0].text.replace(" Episodes", "")
            @parallelize
            def parseEpisodeItems():
                for item in items:
                    mediaId = int(item.xpath("./guid")[0].text.split("-")[-1])
                    feedEntryModified = datetime.strptime(item.xpath("./crunchyroll:modifiedDate", namespaces=PLUGIN_NAMESPACE)[0].text, FEED_DATE_FORMAT)
                    @task
                    def parseEpisodeItem(item=item,mediaId=mediaId,feedEntryModified=feedEntryModified):
                        if not str(mediaId) in Dict['episodes'] or Dict['episodes'][str(mediaId)]["dateUpdated"] <= feedEntryModified:
                            seriesTitle = item.xpath("./crunchyroll:seriesTitle", namespaces=PLUGIN_NAMESPACE)[0].text
                            #TODO: should use <title> or <crunchyroll:episodeTitle> for the title?
                            title = item.xpath("./crunchyroll:episodeTitle", namespaces=PLUGIN_NAMESPACE)[0].text
    #                        if title.startswith("%s - " % seriesTitle):
    #                            title = title.replace("%s - " % seriesTitle, "")
    #                        elif title.startswith("%s Season " % seriesTitle):
    #                            title = title.replace("%s Season " % seriesTitle, "")
    #                            title = title.split(" ", 1)[1].lstrip("- ")
                            
                            episodeDescription = item.xpath("./description")[0].text
                            if "/><br />" in episodeDescription:
                                episodeDescription = episodeDescription.split("/><br />")[1]
                            episodeDescription = API.stripHtml(episodeDescription)
                            
                            try:
                                episodeNumber = int(item.xpath("./crunchyroll:episodeNumber", namespaces=PLUGIN_NAMESPACE)[0].text)
                            except:
                                episodeNumber = None
                            
                            freePubDate = datetime.strptime(item.xpath("./crunchyroll:freePubDate", namespaces=PLUGIN_NAMESPACE)[0].text, FEED_DATE_FORMAT)
                            freePubDateEnd = datetime.strptime(item.xpath("./crunchyroll:freeEndPubDate", namespaces=PLUGIN_NAMESPACE)[0].text, FEED_DATE_FORMAT)
                            premiumPubDate = datetime.strptime(item.xpath("./crunchyroll:premiumPubDate", namespaces=PLUGIN_NAMESPACE)[0].text, FEED_DATE_FORMAT)
                            premiumPubDateEnd = datetime.strptime(item.xpath("./crunchyroll:premiumEndPubDate", namespaces=PLUGIN_NAMESPACE)[0].text, FEED_DATE_FORMAT)
                            try: publisher = item.xpath("./crunchyroll:publisher", namespaces=PLUGIN_NAMESPACE)[0].text
                            except: publisher = ""
                            duration = int(item.xpath("./crunchyroll:duration", namespaces=PLUGIN_NAMESPACE)[0].text) * 1000
                            subtitleLanguages = item.xpath("./crunchyroll:subtitleLanguages", namespaces=PLUGIN_NAMESPACE)[0].text.split(",")
                            simpleRating = item.xpath("./media:rating", namespaces=PLUGIN_NAMESPACE)[0].text
                            countries = item.xpath("./media:restriction", namespaces=PLUGIN_NAMESPACE)[0].text.strip().split(" ")
                            try: season = int(item.xpath("./crunchyroll:season", namespaces=PLUGIN_NAMESPACE)[0].text)
                            except: season = None
                            mediaLink = item.xpath(EPISODE_MEDIA_LINK_XPATH)[0].text.strip()
                            category = item.xpath("./category")[0].text
                            try: thumb = str(item.xpath("./media:thumbnail", namespaces=PLUGIN_NAMESPACE)[0].get('url')).split("_")[0]+THUMB_QUALITY[Prefs['thumb_quality']]+".jpg"
                            except IndexError:
                                if "http://static.ak.crunchyroll.com/i/coming_soon_new_thumb.jpg" in description:
                                    thumb = "http://static.ak.crunchyroll.com/i/coming_soon_new_thumb.jpg"
                                else:
                                    thumb = "" # FIXME happens on newbie content, could be a bad idea b/c of cache.
                            art = thumb
                            
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
    
                            if Dict['episodes'][str(mediaId)]["dateUpdated"] <= feedEntryModified:
                                seasonId = Dict['episodes'][str(mediaId)]["seasonId"]
                            #FIXME: figure out how to deal with getting resolutions.
                            availableResolutions = None
                            
                            episode = {
                                "title": title,
                                "description": episodeDescription,
                                "mediaId": mediaId,
                                "episodeNumber": episodeNumber,
                                "freePubDate": freePubDate,
                                "freePubDateEnd": freePubDateEnd,
                                "premiumPubDate": premiumPubDate,
                                "premiumPubDateEnd": premiumPubDateEnd,
                                "publisher": publisher,
                                "duration": duration,
                                "subtitleLanguages": subtitleLanguages,
                                "rating": rating,
                                "simpleRating": simpleRating,
                                "countries": countries,
                                "dateUpdated": dateUpdated,
                                "season": season,
                                "seasonId": seasonId,
                                "mediaLink": mediaLink,
                                "category": category,
                                "thumb": thumb,
                                "art": art,
                                "seriesTitle": seriesTitle,
                                "availableResolutions": availableResolutions
                            }
                            
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
    
    @staticmethod
    def getSeriesListFromFeed(feed, sort=True, sortBy="title"):
        #TODO: implement a check to eliminate need for call if series were cached recently
        API.cacheFullSeriesList()
        
        feedHtml = HTML.ElementFromURL(feed,cacheTime=SERIES_FEED_CACHE_TIME)
        seriesList = []
        items = feedHtml.xpath("//item")
        for item in items:
            seriesGUID = item.xpath("./guid")[0].text.replace("http://www.crunchyroll.com/", "")
            if not seriesGUID in Dict['series']:
                #TODO: figure out what to do if the series can't be found in Dict['series']
                Log.Debug("Could not find series with seriesGUID %s in Dict['series'].")
            else:
                seriesList.append(Dict['series'][str(seriesGUID)])
            
        if sort:
    #        if sortBy == title:
    #            return sorted(seriesList, key=lambda k: getSortTitle(k))
    #        else:
                return sorted(seriesList, key=lambda k: k[sortBy])
        else:
            return seriesList
    
    
    
    @staticmethod
    def GetEpisodeListFromQuery(queryString):
        "return a list of relevant episode dicts matching queryString"
        return API.getEpisodeListFromFeed(SEARCH_URL+queryString.strip().replace(' ', '%20'), sort=False)
    
    
    @staticmethod
    def GetQueueList():
        API.login()
        queueHtml = HTML.ElementFromURL(QUEUE_URL,cacheTime=QUEUE_LIST_CACHE_TIME)
        queueList = []
        items = queueHtml.xpath("//div[@id='main_content']/ul[@id='sortable']/li[@class='queue-item']")
        for item in items:
            title = item.xpath(".//span[@class='series-title ellipsis']")[0].text
            seriesId = int(item.xpath("@series_id")[0].replace("queue_item_",""))
    #        epToPlay = BASE_URL+item.xpath(".//a[@itemprop='url']/@href")[0].split("?t=")[0]
            
    #        episodeTitle= item.xpath(".//a[@itemprop='url']/@title")[0]
    #        episodeDescription = item.xpath(".//p[@itemprop='description']")
    
    #        if episodeDescription:
    #            episodeDescription = episodeDescription[0].text.strip('\n').strip()
    #        else:
    #            episodeDescription = ""
            """
            make sure item has an ID and does not error out from an empty string.
            This happens for series that were on cruncyroll but cruchyroll nolonger has rights to show.
            """
            episodeMediaIDStr = item.xpath("@media_id")[0]
            if not (episodeMediaIDStr == ""):
                episodeMediaID = int(episodeMediaIDStr)
                
                nextUpText = item.xpath(".//span[@class='series-data ellipsis']")[0].text
                fixit = ""
                for line in nextUpText.split('\n'):
                    fixit = fixit + line.strip('\n').strip() +'\n'
    
                nextUpText = fixit
    
    
                queueItem = {
                    "title": title,
                    "upNextMediaId": episodeMediaID,
                    "seriesId": seriesId#,
                }
                queueList.append(queueItem)
            
        return queueList
    
    
    @staticmethod
    def recoverEpisodeDict(mediaId):
        """
        try everything possible to recover the episode info for
        mediaId and save it in Dict{}. If it fails, return none.
        """
        Log.Debug("#######recovering episode dictionary for mediaID %s" % str(mediaId))
        # make sure the series list is up to date
        API.cacheFullSeriesList()
        
        #FIXME: needs work ASAP!!!!
        # figure out method of getting the seriesId that the episode is in...
        # get all the seasons that are in that series
        #    seasonList = GetListOfSeasonsInSeries(seriesId)
        #    hackish meathod...
        for seasonId in Dict['seasons'].keys():
            API.cacheEpisodeListForSeason(seasonId)
        
        
    #    # get a link with title in it.
    #    #import urllib2
    #    req = urllib2.urlopen(BASE_URL+"/media-" + str(mediaId) + "?pskip_wall=1")
    #    redirectedUrl = req.geturl()
    #    req.close
    #    #FIXME: update for new system
    #    redirectedUrl = redirectedUrl.replace("?pskip_wall=1", "")    
    #    seriesName = redirectedUrl.split(".com/")[1].split("/")[0]
    #    seriesUrl = seriesTitleToUrl(seriesName)
    #    _getEpisodeListFromFeed(seriesUrl) # for side-effect of caching episode
        
        if str(mediaId) in Dict['episodes']:
            return Dict['episodes'][str(mediaId)]
        
        # FIXME: blah
        # not good so far, we need a feed that provides full episodes. Yikes.
        # try grabbing from boxee_feeds
        # need seriesID as in boxee_feeds/showseries/384855
        # which can be retrieved from the seriesUrl contents, whew...
        # alternatively, use http://www.crunchyroll.com/series-name/episodes
        # which gives full episodes, but, well, is HTML and has less media info
        return None
    
    
    @staticmethod
    def GetPopularAnimeEpisodes():
        "return a list of anime episode dicts that are currently popular"
        return API.getEpisodeListFromFeed(POPULAR_ANIME_FEED, sort=False)
    
    @staticmethod
    def GetPopularDramaEpisodes():
        "return a list of drama episode dicts that are currenly popular"
        return API.getEpisodeListFromFeed(POPULAR_DRAMA_FEED, sort=False)
    
    @staticmethod
    def GetPopularVideos():
        "return the most popular videos."
        return API.getEpisodeListFromFeed(POPULAR_FEED, sort=False)
    
    @staticmethod
    def GetRecentVideos():
        "return a list of episode dicts of recent videos of all types"
        return API.getEpisodeListFromFeed(RECENT_VIDEOS_FEED, sort=False)
    
    @staticmethod
    def GetRecentAnimeEpisodes():
        "return a list of episode dicts of recently added anime episodes"
        return API.getEpisodeListFromFeed(RECENT_ANIME_FEED, sort=False)
    
    @staticmethod
    def GetRecentDramaEpisodes():
        "return a list of recently added drama videos"
        return API.getEpisodeListFromFeed(RECENT_DRAMA_FEED, sort=False)
    
    @staticmethod
    def GetAnimeSeriesList():
        "return a list of all available series in anime"
        return API.getSeriesListFromFeed(SERIES_FEED_BASE_URL + "genre_anime_all", sort=True)
    
    @staticmethod
    def GetDramaSeriesList():
        "return a list of all available series in Drama"
        return API.getSeriesListFromFeed(SERIES_FEED_BASE_URL + "drama", sort=True)
    
    @staticmethod
    def GetAllSeries():
        "return a list of series dicts that represent all available series"
        list = []
        anime = API.GetAnimeSeriesList()
        drama = API.GetDramaSeriesList()
        # FIXME: if there's overlap, we'll have dupes...
        list = anime + drama
    #    list = sorted(list, key=lambda k: getSortTitle(k))
        return list
    
    @staticmethod
    def GetPopularDramaSeries():
        "return a list of series dicts of most popular drama"
        return API.getSeriesListFromFeed(SERIES_FEED_BASE_URL + "drama_popular", sort=False)
    
    @staticmethod
    def GetPopularAnimeSeries():
        "return a list of series dicts of most popular anime"
        return API.getSeriesListFromFeed(SERIES_FEED_BASE_URL + "anime_popular", sort=False)
    
    @staticmethod
    def GetAnimeSeriesByGenre(genre):
        queryStr = ANIME_GENRE_LIST[genre].replace(' ', '%20')
        feed = SERIES_FEED_BASE_URL + "anime_withtag/" + queryStr
        return API.getSeriesListFromFeed(feed)
    
    @staticmethod
    def GetDramaSeriesByGenre(genre):
        queryStr = DRAMA_GENRE_LIST[genre].replace(' ', '%20')
        feed = SERIES_FEED_BASE_URL + "genre_drama_" + queryStr
        return API.getSeriesListFromFeed(feed)
    
    @staticmethod
    def GetSeriesByGenre(genre):
        list = []
        drama, anime = [],[]
        try:
            drama = API.GetDramaSeriesByGenre(genre)
        except KeyError: # may not have that genre
            drama = []
        try:
            anime = API.GetAnimeSeriesByGenre(genre)
        except KeyError:
            anime = []
    
        # FIXME: if there's overlap, we'll have dupes...    
        return anime + drama
    
    
    @staticmethod
    def GetSeriesDict(seriesId):
        """
        return an series dict object identified by seriesId.
        If you know the seriesId, it SHOULD be in the cache already.
        If not, you could get None if recovery doesn't work. This might 
        happen with seriesId's that come from the great beyond 
        (queue items on server, e.g.)
        Sry bout that.
        """
        if Dict['series'] is None or str(seriesId) not in Dict['series']:
            # get brutal
            Log.Debug("#######recovering series dictionary for seriesID %s" % str(seriesId))
            API.cacheFullSeriesList()
    #        # get a link with title in it.
    #        #import urllib2
    #        req = urllib2.urlopen(BASE_URL+"/media-" + str(mediaId) + "?pskip_wall=1")
    #        redirectedUrl = req.geturl()
    #        req.close
    #        #FIXME: update for new system
    #        redirectedUrl = redirectedUrl.replace("?pskip_wall=1", "")    
    #        seriesName = redirectedUrl.split(".com/")[1].split("/")[0]
    #        seriesUrl = seriesTitleToUrl(seriesName)
    #        _getEpisodeListFromFeed(seriesUrl) # for side-effect of caching episode
            
            if str(mediaId) in Dict['episodes']:
                return Dict['episodes'][str(mediaId)]
            
            # FIXME: blah
            # not good so far, we need a feed that provides full episodes. Yikes.
            # try grabbing from boxee_feeds
            # need seriesID as in boxee_feeds/showseries/384855
            # which can be retrieved from the seriesUrl contents, whew...
            # alternatively, use http://www.crunchyroll.com/series-name/episodes
            # which gives full episodes, but, well, is HTML and has less media info
            
        return Dict['series'].get(str(seriesId))
    
    @staticmethod
    def GetListOfSeasonsInSeries(seriesId):
        # make sure the seriesId is in the cache
        if not str(seriesId) in Dict['series']:
            Log.Debug("Did not find seriesID %s in the cache. refreshing the cache now"%str(seriesId))
            API.cacheFullSeriesList()
            # check again since the cache was just updated
            if not str(seriesId) in Dict['series']:
                Log.Warning("Unable to locate seriesID %s on crunchyroll.com"%str(seriesId))
                return []
        
        # the seriesId is in the cache so return the list of seasonIds
        return Dict['series'][str(seriesId)]['seasonList']
    
    @staticmethod
    def GetSeasonDict(seasonId):
        # make sure the seasonId is in the cache
        if not str(seasonId) in Dict['seasons']:
            Log.Debug("Did not find seasonsID %s in the cache. refreshing the cache now"%str(seasonId))
            API.cacheFullSeriesList()
            # check again since the cache was just updated
            if not str(seasonId) in Dict['seasons']:
                Log.Warning("Unable to locate seasonID %s on crunchyroll.com"%str(seasonId))
                return []
        
        # the seriesId is in the cache so return the list of seasonIds
        return Dict['seasons'][str(seasonId)]
    
    @staticmethod
    def GetListOfEpisodesInSeason(seasonId):
        # make sure the seasonId is in the cache
        Log.Debug("running GetListOfEpisodesInSeason %s"%str(seasonId))
        if not str(seasonId) in Dict['seasons']:
            Log.Debug("Did not find seasonID %s in the cache. refreshing the cache now"%str(seasonId))
            API.cacheFullSeriesList()
            # check again since the cache was just updated
            if not str(seasonId) in Dict['seasons']:
                Log.Debug("Unable to locate seasonID %s on crunchyroll.com"%str(seasonId))
                return []
        
        # the seriesId is in the cache so return the list of seasonIds
        #TODO: should probably add some code to make sure that the list is up to date.
    #    if Dict['seasons'][str(seasonId)]['epsRetreived'] is None or (datetime.utcnow() - Dict['seasons'][str(seasonId)]['epsRetreived']) >= timedelta(hours=5):
    #        _cacheEpisodeListForSeason(seasonId)
    #        Dict['seasons'][str(seasonId)]['epsRetreived'] = datetime.utcnow()
    
        Log.Debug("running GetListOfEpisodesInSeason %s  part 2"%str(seasonId))
        API.cacheEpisodeListForSeason(seasonId)
        Dict['seasons'][str(seasonId)]['epsRetreived'] = datetime.utcnow()
            
        return Dict['seasons'][str(seasonId)]['epList']
    
    @staticmethod
    def GetEpisodeDict(mediaId):
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
            API.recoverEpisodeDict(mediaId)
            
        return Dict['episodes'].get(str(mediaId))
    
    
    @staticmethod
    def SeriesTitleToUrl(title):
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
    
    @staticmethod
    def GetVideoInfo(mediaId, availRes):
        if not mediaId:
            #occasionally this happens, so make sure it's noisy
            raise Exception("#####getVideoInfo(): NO MEDIA ID, SORRY!")
            
        url = "http://www.crunchyroll.com/xml/?req=RpcApiVideoPlayer_GetStandardConfig&media_id=%s&video_format=102&video_quality=10&auto_play=1&show_pop_out_controls=1&pop_out_disable_message=Only+All-Access+Members+and+Anime+Members+can+pop+out+this" % mediaId
        html = HTML.ElementFromURL(url)
        episodeInfo = {}
        episodeInfo['baseUrl'] = MEDIA_URL + str(mediaId)
        episodeInfo['availRes'] = availRes
            
        d = html.xpath("//stream_info/metadata/duration")
        if len(d):
            try: episodeInfo['duration'] = int(float(d[0].text)*1000)
            except Exception, arg:
                Log.Debug(repr(arg) + "\nsetting duration to 0")
                episodeInfo['duration'] = 0
        else:
            Log.Debug("#########Couldnt find duration")
            episodeInfo['duration'] = 0
        
        # I don't think the episode number is ever used from this function....
    #    n = html.xpath("//media_metadata/episode_number")
    #    if len(n):
    #        try: episodeInfo['episodeNum'] = int(html.xpath("//media_metadata/episode_number")[0].text)
    #        except (ValueError, TypeError): episodeInfo['episodeNum'] = 0
    #    else: episodeInfo['duration'] = 0
        
        # width and height may not exist or may be bogus (Bleach eps 358)
    #    try:
    #        width = float(html.xpath("//stream_info/metadata/width")[0].text)
    #        height = float(html.xpath("//stream_info/metadata/height")[0].text)
    #        ratio = width/height
    #    except (IndexError, ValueError, TypeError):
    #        ratio = 1
    #    episodeInfo['wide'] = (ratio > 1.5)
    
        return episodeInfo
    
    @staticmethod
    def GetAvailResForMediaId(mediaId):
        """
        given an mediaId, return a list of integers
        of available heights.
        
        If user is a guest, just return 360, which
        is all they get ;-)
        """
        
        if not Prefs['username'] or not Prefs['password']:
            return [360]
    
        API.login()
    
        availRes = [360]
        url = "%s/media-%s"%(BASE_URL,str(mediaId))
        link = url.replace(BASE_URL, "")
        req = HTTP.Request(url=url, immediate=True, cacheTime=3600*24)
        html = HTML.ElementFromString(req)
        
        try: 
            small = not API.isPremium()
    
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
    
    @staticmethod
    def GetVideoMediaIdFromLink(link):
        mtmp = link.split(".com/")[1].split("/")[1].split("-")
        mediaId = int(mtmp[len(mtmp)-1])
        return mediaId
    
    @staticmethod
    def GetEpInfoFromLink(link):
        #FIXME: currently this works fine for Queue items, which include
        # the title in the link, but should fail horribly
        # with "www.crunchyroll.com/media-45768" style links
        # which are given by feedburner, et. al.
        # furthermore, rss feeds that we use to populate the Dict{} may not contain all episodes.
        mediaId = API.GetVideoMediaIdFromLink(link)
        if not str(mediaId) in Dict['episodes']:
            seriesname = link.split(".com/")[1].split("/")[0]
            url = API.SeriesTitleToUrl(seriesname)
            API.getEpisodeListFromFeed(url) #TODO: investigate reason for calling this...
        episode = API.GetEpisodeDict(mediaId)
        return episode
    
    @staticmethod
    def GetMetadataFromUrl(url):
        episodeId = url.split(".com/")[1].split("/")[1].split("-")
        episodeId = episodeId[len(episodeId)-1]
        if not str(episodeId) in Dict['episodes']:
            seriesName=url.split(".com/")[1].split("/")[0]
            API.getEpisodeListFromFeed(BASE_URL+"/%s.rss"%seriesName)
        episodeData = API.GetEpisodeDict(mediaId)
        metadata = {
            "title": episodeData['title']
        }
        return metadata
    
    @staticmethod
    def GetPrefRes(availRes):
    
        if not Prefs['username'] or not Prefs['password']:
            return 360 # that's all you get
        API.login()
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
    
    @staticmethod
    def GetVideoUrl(videoInfo, resolution):
        """
        construct a URL to display at resolution based on videoInfo
        without checking for coherence to what the site's got
        or if the resolution is valid
        """
        url = videoInfo['baseUrl']+"?p" + str(resolution) + "=1"
        url = url + "&skip_wall=1"
        url = url + ("&t=0" if Prefs['restart'] == 'Restart' else "")
    #    url = url + "&small="+("1" if videoInfo['small'] is True else "0")
    #    url = url + "&wide="+("1" if videoInfo['wide'] is True or JUST_USE_WIDE is True else "0")
        return url
    
    
    
    @staticmethod
    def SetPreferredResolution(sender, query):
        try:
            q = int(query)
        except:
            q = 0
        
        if q not in [360, 480, 720, 1080]:
            return MessageContainer("Bad input", "You need to input one of 360, 480, 720, or 1080")
        
        if API.setPrefResolution(q):
            return MessageContainer("Success", "Resolution changed to %i" % q)
        else:
            return MessageContainer("Failure", "Failed to change resolution, sorry!")
        
    
    @staticmethod
    def jsonRequest(valuesDict, referer=None):
        """
        convenience function. Return API request result as dict.
        """
        response = API.makeAPIRequest(valuesDict, referer)
        response = JSON.ObjectFromString(response)
        return response
    
    @staticmethod
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
    
    @staticmethod
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
    
    @staticmethod
    def loginViaApi(authInfo):
        loginSuccess = False
        try:
            response = API.jsonRequest(
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
    
        
    @staticmethod
    def loggedIn():
        """
        Immediately check if user is logged in, and change global values to reflect status. 
        DO NOT USE THIS A LOT. It requires a web fetch.
        """
        #FIXME: a better way would be to use API, but I don't know how to request status
        # alternatively, might as well just login anyway if you're going to touch the network.
        if not Dict['Authentication']:
            API.resetAuthInfo()
            
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
            Log.Debug(HTTP.CookiesForURL('https://www.crunchyroll.com/'))
            if "Anime Member!" in req.content:
                authInfo['AnimePremium'] = True
            if "Drama Member!" in req.content: #FIXME: untested!
                authInfo['DramaPremium'] = True
            
            Dict['Authentication'] = authInfo #FIXME: needed?
            
            #Log.Debug("#####You are authorized for premium content, have a nice day.")
            #Log.Debug("#####AnimePremium member: %s" % ("yes" if authInfo['AnimePremium'] else "no"))
            #Log.Debug("#####DramaPremium member: %s" % ("yes" if authInfo['DramaPremium'] else "no"))
            if not authInfo['AnimePremium'] and not authInfo['DramaPremium']: #possible if user is just registered
                Log.Error("####Programmer does not know what to do with freebie registered users. Apologies.")
                #Log.Debug(req.content)
                
        return authorized
    
    @staticmethod
    def resetAuthInfo():
        """
        put a default authentication status structure into
        the global Dict{}. Every datum is least permissions on default.
        """
        Dict['Authentication'] =  {'loggedInSince':0.0, 'failedLoginCount':0, 'AnimePremium': False, 'DramaPremium': False}
    
    @staticmethod
    def login(force=False):
        """
        Log the user in if needed. Returns False on authentication failure,
        otherwise True. Feel free to call this anytime you think logging in
        would be useful -- it assumes you will do so.
    
        Guest users don't log in, therefore this will always return true for them.
        See IsPremium() if you want to check permissions. or LoggedIn() if you 
        want to fetch a web page NOW (use conservatively!)
        """
    
        loginSuccess = False
        if not Dict['Authentication'] : API.resetAuthInfo()
        
        authInfo = Dict['Authentication'] #dicts are mutable, so authInfo is a reference & will change Dict presumably
        if Prefs['username'] and Prefs['password']:
    
            # fifteen minutes is reasonable.
            # this also prevents spamming server
            if (force == False) and (time.time() - authInfo['loggedInSince']) < LOGIN_GRACE:
                Log.Debug("loggedin cookies:")
                Log.Debug(HTTP.CookiesForURL('https://www.crunchyroll.com/'))
                return True
    
            if force: 
                HTTP.ClearCookies()
                authInfo['loggedInSince'] = 0
                authInfo['failedLoginCount'] = 0
                #Dict['Authentication'] = authInfo
    
            if not force and authInfo['failedLoginCount'] > 2:
                return False # Don't bash the server, just inform caller
            
            if API.loggedIn():
                authInfo['failedLoginCount'] = 0
                authInfo['loggedInSince'] = time.time()
                #Dict['Authentication'] = authInfo
                Log.Debug("loggedin cookies:")
                Log.Debug(HTTP.CookiesForURL('https://www.crunchyroll.com/'))
                return True
            else:
                Log.Debug("#####WEB LOGIN CHECK FAILED, MUST LOG IN MANUALLY")
    
            # if we reach here, we must manually log in.
            if not force:
                #save about 2 seconds
                HTTP.ClearCookies()
    
            loginSuccess = API.loginViaApi(authInfo)
                
            #check it
            if loginSuccess or API.loggedIn():
                authInfo['loggedInSince'] = time.time()
                authInfo['failedLoginCount'] = 0
                #Dict['Authentication'] = authInfo
                Log.Debug("loggedin cookies:")
                Log.Debug(HTTP.CookiesForURL('https://www.crunchyroll.com/'))
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
    
    @staticmethod
    def isRegistered():
        """
        is the user a registered user?
        Registered users get to use their queue.
        """
        if not API.login():
            return False
    
        if API.loginNotBlank():
            return True
    
    @staticmethod
    def hasPaid():
        """
        does the user own a paid account of any type?
        """
        login()
        if not Dict['Authentication']: API.resetAuthInfo()
        
        authInfo = Dict['Authentication']
        
        if (time.time() - authInfo['loggedInSince']) < LOGIN_GRACE:
            if authInfo['AnimePremium'] is True or authInfo['DramaPremium'] is True:
                return True
    
        return False
        
    @staticmethod
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
    
        API.login()
        if not Dict['Authentication']: API.resetAuthInfo()
        
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
    
    @staticmethod
    def logout():
        """
        Immediately log the user out and clear all authentication info.
        """
        response = API.jsonRequest({'req':"RpcApiUser_Logout"}, referer="https://www.crunchyroll.com")
        HTTP.ClearCookies()
        API.resetAuthInfo()
    
    @staticmethod
    def loginNotBlank():
        if Prefs['username'] and Prefs['password']: return True
        return False
    
    @staticmethod
    def setPrefResolution(res):
        """
        change the preferred resolution serverside to integer res
        """
        if API.hasPaid():
            res2enum = {360:'12', 480:'20', 720:'21', 1080:'23'}
            
            response = API.jsonRequest(
                { 'req': "RpcApiUser_UpdateDefaultVideoQuality",
                  'value': res2enum[res]
                }
                )
        
            if response.get('result_code') == 1:
                return True
            else:
                return False
    
        return False
    
    @staticmethod
    def removeFromQueue(seriesId):
        """
        remove seriesID from queue
        """
        API.login()
        if not API.isRegistered():
            return False
        
        response = API.makeAPIRequest2("req=RpcApiUserQueue_Delete&group_id=%s"%seriesId)
        #FIXME response should have meaning; do something here?
        Log.Debug("remove response: %s"%response)
        return True
    
    @staticmethod
    def addToQueue(seriesId):
        """
        Add seriesId to the queue.
        """
        API.login()
        if not API.isRegistered():
            return False
            
        Log.Debug("add mediaid: %s"%seriesId)
        response = API.makeAPIRequest2("req=RpcApiUserQueue_Add&group_id=%s"%seriesId)
        Log.Debug("add response: %s"%response)
        return True
    
    
    @staticmethod
    def deleteFlashJunk(folder=None):
        """
        remove flash player storage from crunchyroll.com.
        We need to remove everything, as just removing
        'PersistentSettingsProxy.sol' (playhead resume info) leads 
        to buggy player behavior.
        """
        #FIXME: does this also need to be implemented for windows? is it even needed to begin with?
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
                    API.deleteFlashJunk(file_path)
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
    
    @staticmethod
    def stripHtml(html):
        """
        return a string stripped of html tags
        """
        # kinda works
        res = html.replace("&lt;", "<")
        res = res.replace("&gt;", ">")
        res = re.sub(r'<[^>]+>', '', res)
        return res
