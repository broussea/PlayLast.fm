import urllib2
from   xml.dom import minidom
import time

class lastfm_handle:
	
	CHARTLIST_URL = "http://ws.audioscrobbler.com/1.0/user/USERNAME/weeklychartlist.xml"
	CHART_URL     = "http://ws.audioscrobbler.com/1.0/user/USERNAME/weeklytrackchart.xml?from=START_TIMESTAMP&to=END_TIMESTAMP"
	
	def __init__(self):
		self.user = None
	
	def set_user(self,user):
		self.user = user
	def get_user(self):
		return self.user
	
	def get_weekly_timestamps(self, week_nb = 4):
		
		# Adapt URL to user
		chartlist_url = self.CHARTLIST_URL.replace("USERNAME", self.user)
		
		# Fetch weekly charts list
#		print "Fetching chart list at %s: " % chartlist_url,
		
		url_ok	= False
		err_count = 0
		
		while url_ok == False and err_count < 10:
			req = urllib2.Request(chartlist_url)
			try:
				chartlist = urllib2.urlopen(req).read()
			except IOError:
				url_ok	 = False
				err_count += 1
			else:
				url_ok = True
		
		if err_count >= 10:
			print "Could not fecth chart list"
#			sys.exit(-1)
		
#		print "done"
		
		xmldata	   = minidom.parseString(chartlist)
		chart_data	= xmldata.getElementsByTagName('chart')
		chart_data.reverse()

		# Store timestamps
		week_ts = []
		for i in range(min(len(chart_data),week_nb)):
			week_ts.append( {"start":int(chart_data[i].getAttribute("from")), "end":int(chart_data[i].getAttribute("to"))} )
		
		return week_ts
	
	def get_chart_songs(self, week_nb):

		charts = []

		# Adapt URL to user
		CHART_URL = self.CHART_URL.replace("USERNAME", self.user)
		
		# Retrieve weekly chart list
		weeks = self.get_weekly_timestamps(week_nb)
		
		# Build list of charts
		for i in range(week_nb):
			
#			print "Fetching week %i of %i:" % (i+1, week_nb),
			
			my_url = CHART_URL.replace("START_TIMESTAMP", str(weeks[i]["start"]) )
			my_url = my_url.replace("END_TIMESTAMP", str(weeks[i]["end"]) )

#			print my_url,

			url_ok	= False
			err_count = 0
			
			while url_ok == False and err_count < 10:
				req = urllib2.Request(my_url)
				try:
					charts.append( urllib2.urlopen(req).read() )
				except IOError:
					url_ok	 = False
					err_count += 1
				else:
					url_ok = True
			
			if err_count >= 10:
				print "Could not fecth chart list"
#				sys.exit(-1)
			
#			print "- done"
			
			# Wait: last.fm servers reject consecutive requests occuring in less than 1 sec
			time.sleep(1)
		    
		# Build list of songs
		songs = {}
		for c in charts:
			xmldata = minidom.parseString(c)
			for t in xmldata.getElementsByTagName('track'):
				my_song = {}
				my_song["artist"] = t.getElementsByTagName('artist')[0].firstChild.nodeValue
		        	my_song["name"]   = t.getElementsByTagName('name')[0].firstChild.nodeValue
		        	my_song["score"]  = int(t.getElementsByTagName('playcount')[0].firstChild.nodeValue)
				key = my_song["artist"] + " - " + my_song["name"]
				if key in songs:
					songs[key]["score"] += my_song["score"]
				else:
					songs[key] = my_song
		
		# Sort list
		s = songs.values()
		s.sort(lambda x,y: cmp(x["score"], y["score"]))
		s.reverse()
		
		return s
