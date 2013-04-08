from Screens.Screen import Screen
from Components.Label import Label
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Screens.MessageBox import MessageBox
from Plugins.Plugin import PluginDescriptor
from Screens.Console import Console

import urllib2
import sys
import getopt
import zipfile
import os
import urllib

###########################################################################
#remote location
CONST_URL = "http://settings.rubyrolls.com"
#remote settings directory
CONST_SETTINGS_DIR = "/settings/enigma"

#download the list of available settings
def getList(inUrl):
  response = urllib2.urlopen(inUrl)
  html = response.read()
  return html

#download enigma setting  
def dowloadFile(inFile, inEnigmaVersion):
  url = CONST_URL + CONST_SETTINGS_DIR + inEnigmaVersion + "/" + urllib.quote(inFile) #quote to avoid issue with special chars
  #print url
  
  file_name = url.split('/')[-1]
  u = urllib2.urlopen(url)
  f = open(file_name, 'wb')
  meta = u.info()
  file_size = int(meta.getheaders("Content-Length")[0])
  
  print "Downloading: %s Bytes: %s" % (file_name, file_size)

  file_size_dl = 0
  block_sz = 8192
  while True:
    buffer = u.read(block_sz)
    if not buffer:
        break

    file_size_dl += len(buffer)
    f.write(buffer)
    status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
    status = status + chr(8)*(len(status)+1)
    print status,

  f.close()
###########################################################################

#first screen
class FirstMenu(Screen):
	
	skin = """
		<screen position="100,150" size="460,400" title="Download new setting from the server" >
			<widget name="title" position="10,10" size="400,40" font="Regular;22"/>
			<widget name="menu" position="10,50" size="400,200" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, args = 0):
		self.session = session
		list = []
		list.append((_("Enigma 1 settings"), "one"))
		list.append((_("Enigma 2 settings"), "two"))
		list.append((_("Reload Enigma Settins"), "three"))
		list.append((_("Exit"), "exit"))
		
		Screen.__init__(self, session)
		self["menu"] = MenuList(list)

		self["title"] = Label()		
		self["title"].setText("Choose the settings you want to install\n")

		self["myActionMap"] = ActionMap(["SetupActions"],
		{
			"ok": self.go,
			"cancel": self.cancel
		}, -1)

	#go method is called after the selection of a menu 
	def go(self):
		returnValue = self["menu"].l.getCurrentSelection()[1]
		#print "\n[FirstMenu] returnValue: " + returnValue + "\n"
		try:
			if returnValue is not None:
				if returnValue is "one":
					#get the list of settings present in the directory
					result = getList(CONST_URL+"?e=1")			
					self.session.openWithCallback(self.back, SelectionMenu, "1", result)
				elif returnValue is "two":
					result = getList(CONST_URL+"?e=2")
					self.session.openWithCallback(self.back, SelectionMenu, "2", result)
				elif returnValue is "three":
					#TODO implement refresh of settings
					self.session.open(MessageBox,_("HERE COMES THE REFRESH OF THE SETTINGS!"), MessageBox.TYPE_INFO)	
				else:
					self.close(None)
		#exception section
		except Exception as inst:
			self.session.open(MessageBox,_("Download error %s!") % (inst), MessageBox.TYPE_INFO)
			print "\n---------------ERROR---------------------------------"	
			print type(inst)     # the exception instance
			print inst
			print "-----------------------------------------------------\n"	
	
	def myMsg(self, entry):
		self.session.open(MessageBox,_("You selected entry no. %s!") % (entry), MessageBox.TYPE_INFO)
		
	# Restart the GUI if requested by the user.
	def restartGUI(self, answer):
		if answer is True:
			self.session.open(TryQuitMainloop, 3)
		else:
			self.close()	

	def cancel(self, result):
		print "\n[FirstMenu] cancel\n"
		print result
		self.close(None)

	#callback from the top menu	
	def back(self, result):
		print "\n[FirstMenu] back\n"
		print result

#second screen
class SelectionMenu(Screen):
	skin = """
		<screen position="100,150" size="460,400" title="Selection screen for Enigma Settings" >
			<widget name="title" position="10,10" size="400,40" font="Regular;22"/>
			<widget name="menu" position="10,50" size="400,400" scrollbarMode="showOnDemand" />
		</screen>"""
	
	def __init__(self, session, enigma, result):
		self.skin = SelectionMenu.skin
		self.session = session
	
		self["title"] = Label()		
		self["title"].setText("Enigma "+ enigma +" settings")
		self.version = enigma
		
		elements = []
		lines = result.split('\n')
							
		for line in lines:
		#loop over the lines array
			if line.strip(): #check line is not empty
				element = line.split('-') # split over the date - element separator
				elements.append(element[1].strip('\n'))
				#print element[1]+'\n'	
		#debug content		
		#for el in elements:
		#	print el
		
		list = []
		for el in elements:
			list.append((_(el), el))
		list.append((_("Exit"), "exit"))
		
		Screen.__init__(self, session)		

		self["menu"] = MenuList(list)
		self["myActionMap"] = ActionMap(["SetupActions"],
		{
			"ok": self.go,
			"cancel": self.cancel
		}, -1)

	def go(self):
		returnValue = self["menu"].l.getCurrentSelection()[1]
		#print "\n[FirstMenu2] returnValue: " + returnValue + "\n"
		#print " VERSION: "+self.version +"\n"
				
		if returnValue is not None:
			if returnValue is "exit":
				#print "\n[FirstMenu2] cancel\n"
				self.close(None)
			else:
			  #download the selected setting
			  dowloadFile(returnValue, self.version)
			  #installation of the channels
			  installChannels(self, returnValue)
			  
			  #success message
			  self.session.open(MessageBox,_("Installation successfully completed!"), MessageBox.TYPE_INFO)
			  
			  #if self.version is "2":
				#self.session.open(MessageBox,_("You selected entry %s for enigma2!") % (returnValue), MessageBox.TYPE_INFO)	
			  #else:
			  	#self.session.open(MessageBox,_("You selected entry %s for enigma1!") % (returnValue), MessageBox.TYPE_INFO)	
	
	def cancel(self):
		#print "\n[FirstMenu] cancel\n"
		self.close(None)
		
	def updateFinishedCB(self,retval = None):
		self.close(True)
		
###########################################################################

def main(session, **kwargs):
	#print "\n[CallMyMsg] start\n"	
	session.open(FirstMenu)

###########################################################################

def installChannels(self, channelZipFile):
	self.session.openWithCallback(self.cancel, Console, title = _("Restore is running..."), cmdlist = ["tar -xzvf " + channelZipFile + " -C /"], finishedCallback = self.updateFinishedCB, closeOnSuccess = True)

def Plugins(**kwargs):
	return PluginDescriptor(
		name="Download Settings",
		description="Plugin to download the setting from a website",
		where = PluginDescriptor.WHERE_PLUGINMENU,
		icon="ihad_tut.png",
		fnc=main)
