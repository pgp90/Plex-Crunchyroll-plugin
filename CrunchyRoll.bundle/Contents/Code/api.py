# -*- coding: utf-8 -*-
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

PREMIUM_TYPE_ANIME = '2'
PREMIUM_TYPE_DRAMA = '4'

def jsonRequest(valuesDict, referer=None):
	"""
	convenience function. Return API request result as dict.
	"""
	response = makeAPIRequest(valuesDict, referer)
	response = JSON.ObjectFromString(response)
	return response

def makeAPIRequest(valuesDict,referer=None):
	"""
	make a crunchyroll.com API request with the passed
	dictionary. Optionally, specify referer to prevent request
	from choking.
	"""
	h = API_HEADERS
	if not referer is None:
		h['Referer'] = referer
	h['Cookie']=HTTP.GetCookiesForURL(BASE_URL)
	req = HTTP.Request("https"+API_URL,values=valuesDict,cacheTime=0,immediate=True, headers=h)
	response = re.sub(r'\n\*/$', '', re.sub(r'^/\*-secure-\n', '', req.content))
	return response


def makeAPIRequest2(data,referer=None):
	"""
	using raw data string, make an API request. Return the result.
	"""
	h = API_HEADERS
	if not referer is None:
		h['Referer'] = referer
	h['Cookie']=HTTP.GetCookiesForURL(BASE_URL)
	req = HTTP.Request("https"+API_URL,data=data,cacheTime=0,immediate=True, headers=h)
	response = re.sub(r'\n\*/$', '', re.sub(r'^/\*-secure-\n', '', req.content))
	return response

def loginViaWeb():
	# backup plan in case cookies go bonkers, not used.
	data = {'formname':'RpcApiUser_Login','fail_url':'http://www.crunchyroll.com/login','name':Prefs['username'],'password':Prefs['password']}
	req = HTTP.Request(url='https://www.crunchyroll.com/?a=formhandler', values=data, immediate=True, cacheTime=10, headers={'Referer':'https://www.crunchyroll.com'})
	HTTP.Headers['Cookie'] = HTTP.GetCookiesForURL('https://www.crunchyroll.com/')

def loginViaApi(authInfo):
	loginSuccess = False
	try:
		response = jsonRequest(
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
			HTTP.Headers['Cookie'] = HTTP.GetCookiesForURL('https://www.crunchyroll.com/')
	except Exception, arg:
		Log.Error("####Sorry, an error occured when logging in:")
		Log.Error(repr(Exception) + " "  + repr(arg))
		return False
	
	return loginSuccess
	
def loggedIn():
	"""
	Immediately check if user is logged in, and change global values to reflect status. 
	DO NOT USE THIS A LOT. It requires a web fetch.
	"""
	# FIXME a better way would be to use API, but I don't know how to request status
	# alternatively, might as well just login anyway if you're going to touch the network.
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
		
		#Log.Debug("#####You are authorized for premium content, have a nice day.")
		#Log.Debug("#####AnimePremium member: %s" % ("yes" if authInfo['AnimePremium'] else "no"))
		#Log.Debug("#####DramaPremium member: %s" % ("yes" if authInfo['DramaPremium'] else "no"))
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
	
	loginSuccess = False
	if not Dict['Authentication'] : resetAuthInfo()
	
	authInfo = Dict['Authentication'] #dicts are mutable, so authInfo is a reference & will change Dict presumably
	if Prefs['username'] and Prefs['password']:

		# fifteen minutes is reasonable.
		# this also prevents spamming server
		if (force == False) and (time.time() - authInfo['loggedInSince']) < LOGIN_GRACE:
			return True

		if force: 
			HTTP.ClearCookies()
			killSafariCookies()
			authInfo['loggedInSince'] = 0
			authInfo['failedLoginCount'] = 0
			#Dict['Authentication'] = authInfo

		if not force and authInfo['failedLoginCount'] > 2:
			return False # Don't bash the server, just inform caller
		
		if loggedIn():
			authInfo['failedLoginCount'] = 0
			authInfo['loggedInSince'] = time.time()
			#Dict['Authentication'] = authInfo
			return True
		else:
			Log.Debug("#####WEB LOGIN CHECK FAILED, MUST LOG IN MANUALLY")

		# if we reach here, we must manually log in.
		if not force:
			#save about 2 seconds
			killSafariCookies()
			HTTP.ClearCookies()

		loginSuccess = loginViaApi(authInfo)
			
		#check it
		if loginSuccess or loggedIn():
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

def isRegistered():
	"""
	is the user a registered user?
	Registered users get to use their queue.
	"""
	if not login():
		return False

	if loginNotBlank():
		return True

def hasPaid():
	"""
	does the user own a paid account of any type?
	"""
	login()
	if not Dict['Authentication']: resetAuthInfo()
	
	authInfo = Dict['Authentication']
	
	if (time.time() - authInfo['loggedInSince']) < LOGIN_GRACE:
		if authInfo['AnimePremium'] is True or authInfo['DramaPremium'] is True:
			return True

	return False

	
def isPremium(epType=None):
	"""
	return True if the user is logged in and has permissions to view extended content.
	You can pass ANIME_TYPE or DRAMA_TYPE to check specifically.
	
	Passing type=None will return True if the user is logged in. Any other type
	returns false.
	"""
	login()
	if not Dict['Authentication']: resetAuthInfo()
	
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

def logout():
	"""
	Immediately log the user out and clear all authentication info.
	"""
	response = jsonRequest({'req':"RpcApiUser_Logout"}, referer="https://www.crunchyroll.com")
	
	# this doesn't seem to help. Cookies still infect the system somewhere (and it's NOT
	# safari, i checked). So whatever. at best, we can try to be secure and fail. Good
	# faith, you know.
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
	if isPaid():
		res2enum = {360:'12', 480:'20', 720:'21', 1080:'23'}
		
		response = jsonRequest(
			{ 'req': "RpcApiUser_UpdateDefaultVideoQuality",
			  'value': res2enum[res]
			}
			)
	
		if response.get('result_code') == 1:
			return True
		else:
			return False

	return False

def removeFromQueue(seriesId):
	"""
	remove seriesID from queue
	"""
	login()
	if not isRegistered():
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
	if not isRegistered():
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
	import platform
	if "darwin" in platform.system().lower():
		
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
			#Log.Debug("#######Transferring these cookies:")
			#Log.Debug(appendThis)
			
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
	else:
		Log.Error("####Removing webkit cookies from a non-Darwin system is unsupported.")
		return False

def killSafariCookies():
	"""
	remove all cookies from ~/Library/Cookies/Cookies.plist matching the domain of .*crunchyroll.com
	and save the result.
	"""
	import os.path, plistlib, platform
	if "darwin" in platform.system().lower():
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
				#Log.Debug("######removing cookie:")
				#Log.Debug(item)
				pass
		plistlib.writePlist(theSavedList, filename)
	
	
def transferCookiesToPlex():
	"""
	grab all crunchyroll.com cookies from Safari
	and transfer them to Plex. You shouldn't do this
	because Plex needs to be the master to
	keep the cookie situation <= fubar.
	"""
	# This function does nothing ATM
	return
	
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

def deleteFlashJunk(folder=None):
	"""
	remove flash player storage from crunchyroll.com.
	We need to remove everything, as just removing
	'PersistentSettingsProxy.sol' (playhead resume info) leads 
	to buggy player behavior.
	"""
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
				deleteFlashJunk(file_path)
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
