"""
api holds functions that interface with crunchyroll.com,
plus some useful utilities that aren't interface items
"""

from constants import *
import time, os, re

#for cookie wrangling:
from Cookie import BaseCookie
import plistlib
from datetime import datetime, timedelta

def makeAPIRequest(valuesDict,referrer=None):
	"""
	make a crunchyroll.com API request with the passed
	dictionary. Optionally, specify referrer to prevent request
	from choking.
	"""
	h = API_HEADERS
	if not referrer is None:
		h['Referrer'] = referrer
	h['Cookie']=HTTP.GetCookiesForURL(BASE_URL)
	req = HTTP.Request("https"+API_URL,values=valuesDict,cacheTime=0,immediate=True, headers=h)
	response = re.sub(r'\n\*/$', '', re.sub(r'^/\*-secure-\n', '', req.content))
	return response


def makeAPIRequest2(data,referrer=None):
	"""
	using raw data string, make an API request. Return the result
	"""
	h = API_HEADERS
	if not referrer is None:
		h['Referrer'] = referrer
	h['Cookie']=HTTP.GetCookiesForURL(BASE_URL)
	req = HTTP.Request("http"+API_URL,data=data,cacheTime=0,immediate=True, headers=h)
	response = re.sub(r'\n\*/$', '', re.sub(r'^/\*-secure-\n', '', req.content))
	return response

def loggedIn():
	"""
	Immediately check if user is logged in, and change global values to reflect status. 
	DO NOT USE THIS A LOT. It requires a web fetch.
	"""
	if not Dict['Authentication']:
		resetAuthInfo()
		
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
		if "Anime Member!" in req.content:
			authInfo['AnimePremium'] = True
		if "Drama Member!" in req.content: #FIXME untested!
			authInfo['DramaPremium'] = True
		
		Dict['Authentication'] = authInfo #FIXME: needed?
		
		Log.Debug("#####You are authorized for premium content, have a nice day.")
		Log.Debug("#####AnimePremium member: %s" % ("yes" if authInfo['AnimePremium'] else "no"))
		Log.Debug("#####DramaPremium member: %s" % ("yes" if authInfo['DramaPremium'] else "no"))
		if not authInfo['AnimePremium'] and not authInfo['DramaPremium']: #WTF?
			Log.Error("####Programmer does not know what he's doing withe Anime/Drama accounts. Apologies.")
			Log.Debug(req.content)
			
	return authorized

def resetAuthInfo():
	"""
	put a default authentication status structure into
	the global Dict{}. Every datum is least permissions on default.
	"""
	Dict['Authentication'] =  {'loggedInSince':0.0, 'failedLoginCount':0, 'AnimePremium': False, 'DramaPremium': False}

def login(force=False):
	"""
	Log the user in if needed. Returns False on authentication failure,
	otherwise True. Feel free to call this anytime you think logging in
	would be useful -- it assumes you will do so.

	Guest users don't log in, therefore this will always return true for them.
	See IsPremium() if you want to check permissions. or LoggedIn() if you 
	want to fetch a web page NOW (use conservatively!)
	"""

	# this modifies Safari's cookies to be regular
	
	if not Dict['Authentication'] : resetAuthInfo()
	
	authInfo = Dict['Authentication'] #dicts are mutable, so authInfo is a reference & will change Dict presumably
	if Prefs['username'] and Prefs['password']:

		# fifteen minutes is reasonable.
		# this also prevents spamming server
		if (force == False) and (time.time() - authInfo['loggedInSince']) < LOGIN_GRACE:
			return True

		Log.Debug("#########Well\n forced is %s and loggedInTime is %f" % (repr(force), time.time() - authInfo['loggedInSince']) )
		if force: 
			HTTP.ClearCookies()
			killSafariCookies()
			authInfo['loggedInSince'] = 0
			authInfo['failedLoginCount'] = 0
			#Dict['Authentication'] = authInfo

		if not force and authInfo['failedLoginCount'] > 2:
			return False # Don't bash the server, just inform caller
		
		Log.Debug("#########checking log in")
		if loggedIn():
			authInfo['failedLoginCount'] = 0
			authInfo['loggedInSince'] = time.time()
			#Dict['Authentication'] = authInfo
			return True
		else:
			Log.Debug("########WEB LOGIN CHECK FAILED, MUST LOG IN AGAIN")

		# if we reach here, we must manually log in.
		if not force:
			#save about 2 seconds
			killSafariCookies()
			HTTP.ClearCookies()
		try:
			data = {'formname':'RpcApiUser_Login','fail_url':'http://www.crunchyroll.com/login','name':Prefs['username'],'password':Prefs['password']}
			req = HTTP.Request(url='https://www.crunchyroll.com/?a=formhandler', values=data, immediate=True, cacheTime=10, headers={'Referrer':'https://www.crunchyroll.com'})
			HTTP.Headers['Cookie'] = HTTP.GetCookiesForURL('https://www.crunchyroll.com/')
		except Exception, arg:
			Log.Error("####Sorry, an error occured when logging in:")
			Log.Error(repr(Exception) + " "  + repr(arg))
			return False
			
		#check it
		if loggedIn():
			authInfo['loggedInSince'] = time.time()
			authInfo['failedLoginCount'] = 0
			#Dict['Authentication'] = authInfo
			transferCookiesToSafari()
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

def isPremium(epType=None):
	"""
	return True if the user is logged in and has permissions to view extended content.
	You can pass ANIME_TYPE or DRAMA_TYPE to check specifically.
	
	Passing type=None will return True if the user is logged in. Any other type
	returns false.
	"""
	if not Dict['Authentication']: resetAuthInfo()
	
	authInfo = Dict['Authentication']
	
	login()
	if (time.time() - authInfo['loggedInSince']) < LOGIN_GRACE:
		Log.Debug("#####we're in the login window")
		if epType is None: return True

		if epType == ANIME_TYPE and authInfo['AnimePremium'] is True:
			return True
		elif epType == DRAMA_TYPE and authInfo['DramaPremium'] is True:
			return True
		Log.Debug("#####BUT neither Anime nor Drama Premium is set!")

		return False #FIXME actually this should be an exception

	Log.Debug("####you're not in the login grace period, too bad. t = %f" % (time.time()-authInfo['loggedInSince']))
	return False

def logout():
	"""
	Immediately log the user out and clear all authentication info.
	"""
	req = HTTP.Request(url='https://www.crunchyroll.com/logout', immediate=True, cacheTime=10, headers={'Referrer':'https://www.crunchyroll.com'})
	
	# tell plex who's boss
	HTTP.ClearCookies()
	killSafariCookies()
	
	#this turns every permission off:
	resetAuthInfo()

def loginNotBlank():
	if Prefs['username'] and Prefs['password']: return True
	return False

def setPrefResolution(res):
	"""
	change the preferred resolution serverside to integer res
	"""
	res2enum = {360:'12', 480:'20', 720:'21', 1080:'23'}
	
	response = makeAPIRequest(
		{ 'req': "RpcApiUser_UpdateDefaultVideoQuality",
		  'value': res2enum[res]
		}
		)
	Log.Debug("####setPrefResolution() response: \n" + repr(response))
	response = JSON.ObjectFromString(response)
	if response.has_key("result_code") and response["result_code"] == '1':
		return True
	else:
		return False
	
def removeFromQueue(seriesId):
	"""
	remove seriesID from queue
	"""
	login()
	if not isPremium():
		return False
	
	response = makeAPIRequest2("req=RpcApiUserQueue_Delete&group_id=%s"%seriesId)
	#FIXME response should have meaning; do something here?
	Log.Debug("remove response: %s"%response)
	return True

def addToQueue(seriesId):
	"""
	Add seriesId to the queue.
	"""
	login()
	if not isPremium():
		return False
		
	Log.Debug("add mediaid: %s"%seriesId)
	response = makeAPIRequest2("req=RpcApiUserQueue_Add&group_id=%s"%seriesId)
	Log.Debug("add response: %s"%response)
	return True

def transferCookiesToSafari():
	"""
	Copy all crunchyroll cookies from Plex's cookie storage
	into Safari's Plist
	"""

	cookieString = HTTP.GetCookiesForURL(BASE_URL)
	if not cookieString: return True

	try:
		theCookies = BaseCookie(cookieString)
		appendThis = []
		tomorrow = datetime.now() + timedelta((1))
		for k, v in theCookies.items():
			#Plex doesn't supply these, so:
			cookieDict = {'Domain':".crunchyroll.com", 
				'Path':"/", 
				'Expires': tomorrow, 
				'Created': time.time(),
				'Name': k,
				'Value': v.value
			}
			appendThis.append(cookieDict)
		Log.Debug("#######Transferring these cookies:")
		Log.Debug(appendThis)
		
		filename = os.path.expanduser("~/Library/Cookies/Cookies.plist")
		theList = plistlib.readPlist(filename)
		finalCookies = appendThis
		
		# brute force replace
		for item in theList:
			if not "crunchyroll.com" in item['Domain']:
				finalCookies.append(item)

		plistlib.writePlist(finalCookies, filename)
		return True
	except Exception, arg:
		Log.Error("#########transferCookiesToSafari() Exception occured:")
		Log.Error(repr(Exception) + " " + repr(arg))
		return False

def killSafariCookies():
	"""
	remove all cookies from ~/Library/Cookies/Cookies.plist matching the domain of .*crunchyroll.com
	and save the result.
	"""
	import os.path, plistlib
	filename = os.path.expanduser("~/Library/Cookies/Cookies.plist")
	try:
		theList = plistlib.readPlist(filename)
	except IOError:
		#hm, okay, whatev, no file or gimpiness, let's bail
		return
		
	theSavedList = []
	for item in theList:
		if not "crunchyroll.com" in item['Domain']:
			theSavedList.append(item)
		else:
			Log.Debug("######removing cookie:")
			Log.Debug(item)
		
	plistlib.writePlist(theSavedList, filename)
	
	
def transferCookiesToPlex():
	"""
	grab all crunchyroll.com cookies from Safari
	and transfer them to Plex. You shouldn't do this
	because Plex needs to be the master to
	keep the cookie situation <= fubar.
	"""
	# This function does nothing ATM
	import os.path, plistlib
	filename = os.path.expanduser("~/Library/Cookies/Cookies.plist")
	try:
		theList = plistlib.readPlist(filename)
	except IOError:
		#hm, okay, whatev, no file or gimpiness, let's bail
		return
		
	cookieList = []
	for item in theList:
		if "crunchyroll.com" in item['Domain']:
			cookieList.append(item)
	
	s = SimpleCookie()
	for cookie in cookieList:
		#FIXME: should I bother?
		pass


########## OLD STUFF FOR REFERENCE OR REVERT ####
def loginAtStart_old():
	global GlobalWasLoggedIn
	global AnimePremium
	global DramaPremium
	#HTTP.ClearCookies() # FIXME put this back in after debugging
	if loginNotBlank():
		data = { "name": Prefs['username'], "password": Prefs['password'], "req": "RpcApiUser_Login" }
		response = makeAPIRequest(data)
		Log.Debug("loginResponse:%s"%response)
		response = JSON.ObjectFromString(response)
		GlobalWasLoggedIn = (response.get('result_code') == 1)
		if GlobalWasLoggedIn:
			AnimePremium = (response.get('data').get('premium').get(PREMIUM_TYPE_ANIME) == 1)
			DramaPremium = (response.get('data').get('premium').get(PREMIUM_TYPE_DRAMA) == 1)
	return GlobalWasLoggedIn


def loggedIn_old():
	return GlobalWasLoggedIn


def login_old():
	if LoginNotBlank():
		data = { "name": Prefs['username'], "password": Prefs['password'], "req": "RpcApiUser_Login" }
		response = makeAPIRequest(data)
