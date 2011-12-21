import os
import urllib

def makeStrms(seriesId, location):
	seriesTitle = Dict['series'][str(seriesId)]['title']
	
	if not os.path.exists(location):
		os.makedirs(location)
	loc = os.path.join(location, seriesTitle)
	if not os.path.exists(loc):
		os.makedirs(loc)
	
	listEpIds = Dict['series'][str(seriesId)]['epList']
	epList = []
	for eId in listEpIds:
		epList.append(Dict['episodes'][str(eId)])
	sortedEpList = sorted(epList, key=lambda k: k['episodeNum'])
	seasonList = []
	for e in sortedEpList:
		s = e['season']
		if s not in seasonList:
			seasonList.append(s)
	numSeasons = len(seasonList)
	
	hasSpecials = False
	if numSeasons > 1 and None in seasonList:
		hasSpecials = True
		seasonList.remove(None)
	maxSeason = 0
	for s in seasonList:
		if maxSeason < int(s):
			maxSeason = int(s)
	for sn in range(1, (int(maxSeason) + 1)):
		sLoc = os.path.join(loc, "Season %02d"%sn)
		if not os.path.exists(sLoc):
			os.makedirs(sLoc)
	if hasSpecials is True:
		sLoc = os.path.join(loc, "Specials")
		if not os.path.exists(sLoc):
			os.makedirs(sLoc)
	specialCount = 1
	for e in sortedEpList:
		s = e['season']
		if s is not None:
			enum = e['episodeNum']
			sLoc = os.path.join(loc, "Season %02d"%s)
		else:
			enum = specialCount
			specialCount = specialCount + 1
			sLoc = os.path.join(loc, "Specials")
		st = str(re.sub(r'--+', '-', re.sub(r'[!:\'\?\.,()&@#$%^*;~/`]', '', seriesTitle).replace(" ", "-").lower()).rstrip("-"))
		et = str(re.sub(r'--+', '-', re.sub(r'[!:\'\?\.,()&@#$%^*;~/`]', '', e['title']).replace(" ", "-").lower()).rstrip("-"))
		link = "http://www.crunchyroll.com/%s/%s-%s"%(st,et,e['mediaId'])
		isWide = IsWide(e['mediaId'])
		if len(e['availableResolutions']) == 0:
			e['availableResolutions'] = scrapper.getAvailResFromPage(e['link'], ['12'])
			Dict['episodes'][str(e['mediaId'])]['availableResolutions'] = e['availableResolutions']
		r = max(e['availableResolutions'])
		#for r in e['availableResolutions']:
		if s is not None:
			strmLoc = os.path.join(sLoc, "%s - S%02dE%02d.strm"%(seriesTitle, s, enum))
		else:
			strmLoc = os.path.join(sLoc, "%s - S00E%02d - %s.strm"%(seriesTitle, enum, e['title']))
		data = "%s?p%s=1&t=0&small=0&wide=%s"%(link,VIDEO_QUALITY[RES_NAMES[r]],isWide)
		data2 = urllib.quote(data).replace("/","%"+"2F")
		#Log.Debug("blahwriting: %s"%data2)
		data = "plex://localhost/video/:/webkit?url=%s"%data2#urllib.quote(data)#%(data.replace("=","%"+"3D").replace("?","%"+"3F"))
		#Log.Debug("writing: %s"%data)
		strmFile = os.fdopen(os.open(strmLoc, os.O_WRONLY|os.O_CREAT), 'w')
		strmFile.write(data)
		strmFile.close()
	return

def DirMenu(sender, folderPath, seriesId, replace):
	if not os.path.exists(folderPath):
		os.makedirs(folderPath)
	dir = MediaContainer(disabledViewModes=["coverflow"], title1="Store To", title2="%s"%folderPath, replaceParent=replace)
	dir.Append(makeParentDirItem(folderPath, seriesId))
	dir.Append(makeSelectDirItem(folderPath, seriesId))
	dir.Append(makeNewFolderItem(folderPath, seriesId))
	for file in os.listdir(folderPath):
		subPath = os.path.join(folderPath, file)
		if os.path.isdir(subPath):
			dir.Append(makeDirMenuItem(subPath, seriesId))
	dir.replace_parent = replace
	dir.no_history = replace
	dir.replaceParent = replace
	dir.noHistory = replace
	return dir

def makeDirMenuItem(path, seriesId):
	name = os.path.basename(path)
	if name is "":
		name = os.path.basename(os.path.dirname(path))
	return Function(DirectoryItem(DirMenu,"%s/" % name, thumb=R(CRUNCHYROLL_ICON)), folderPath=path, seriesId=seriesId, replace=True)

def makeParentDirItem(path, seriesId):
	path = os.path.dirname(path)
	return Function(DirectoryItem(DirMenu,"../", thumb=R(CRUNCHYROLL_ICON)), folderPath=path, seriesId=seriesId, replace=True)

def makeSelectDirItem(path, seriesId):
	return Function(PopupDirectoryItem(SelectFolderConfirm, "Select This Folder", "Select this folder to save the files to. This operation may take a few minutes"), path=path, seriesId=seriesId)

def makeNewFolderItem(path, seriesId):
	return Function(InputDirectoryItem(NewFolderMenu, "Make New Folder", "Create a new folder"), folderPath=path, seriesId=seriesId)

def NewFolderMenu(sender, query, folderPath, seriesId):
	path = os.path.join(folderPath, query)
	if not os.path.exists(path):
		os.makedirs(path)
	return DirMenu(sender, path, seriesId, True)

def SelectFolderConfirm(sender, path, seriesId):
	dir = MediaContainer(disabledViewModes=["coverflow"], title1="Select This Folder?")
	dir.Append(Function(DirectoryItem(SelectFolder, "Yes"), seriesId=seriesId, path=path))
	return dir

def SelectFolder(sender, path, seriesId):
	makeStrms(seriesId, path)
	return MessageContainer(sender.itemTitle, "Done!")


