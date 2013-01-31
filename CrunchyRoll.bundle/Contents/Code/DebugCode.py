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
#        dir.Append(Function(DirectoryItem(KillSafariCookiesItem, "Kill Safari Cookies", summary="This will remove all crunchyroll.com cookies from Safari's cookie file. Useful if login status is not synced.")) )
#        dir.Append(Function(DirectoryItem(TransferCookiesItem, "Transfer cookies to Safari", summary="This transfers Plex's crunchyroll cookies into safari's plist.")) )
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
    Dict = {}
#    Dict.Reset() #OMG this doesn't work. Just delete the file at Plug-in support/com.plexapp.plugins.CrunchyRoll
    Dict.Save()
    Log.Debug(Prefs)
#    Prefs = {}
#    CreatePrefs()
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
    
def ConstructTestVideo(episode)    :
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
