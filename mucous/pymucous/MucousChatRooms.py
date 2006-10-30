# This is part of the Mucous Museek Client, and distributed under the GPLv2
# Copyright (c) 2006 daelstorm. 
import threading
import os
import curses.wrapper
import time
## Chat Rooms
#			
class ChatRooms:
	## Constructor
	# @param self ChatRooms (class)
	# @param mucous Mucous (class)
	def __init__(self, mucous):
		## @var mucous 
		# Mucous (Class)
		self.mucous = mucous
		## @var shape
		# Layout of windows
		self.shape = self.mucous.Config["mucous"]["roombox"]
		## @var dimensions
		# Window placement
		self.dimensions = {}
		## @var windows
		# Curses Window instances
		self.windows = {"text": {}, "border": {} }
		## @var scrolling
		# dict containing vertical scroll position for chatroom, roombox and roomstatus
		self.scrolling = {"chatroom": -1, "roombox": 0, "roomstatus": -1 }
		## @var current
		# current room
		self.current = None
		## @var selected
		# selected window
		self.selected = "chatroom"
		## @var logs
		# dict containing logs for chatroom, roombox and roomstatus 
		self.logs = {"rooms": {},"roombox": {} , "roomstatus": {} }
		## @var rooms
		# dict of users in rooms
		self.rooms = {}
		## @var numticker
		# position of ticker
		self.numticker = 0
		## @var tickers
		# dict of rooms containing lists of tickers 
		self.tickers = {}
		if self.mucous.Config["tickers"]["ticker_cycle"] == "yes":
			time = float(self.mucous.Config["tickers"]["cycletime"])
		elif self.mucous.Config["tickers"]["ticker_scroll"] == "yes":
			time = float(self.mucous.Config["tickers"]["scrolltime"])
		## @var ticker_timer
		# Timer instance for displaying tickers
		self.ticker_timer = threading.Timer(time, self.DrawTicker)
		
	## Create and draw current chat room's window and contents 
	# Cleanup stale windows first
	# Calls: set_room
	def Mode(self):
		try:
			self.mucous.mode = "chat"
			self.mucous.PopupMenu.show = False
			
			# Arrangements: 
			cs = None
			if "roomstatus" in self.windows["text"]:
				del self.windows["text"]["roomstatus"]
			if "roomstatus" in self.windows["border"]:
				del self.windows["border"]["roomstatus"]
			
			if "chat" in self.windows["text"]:
				del self.windows["text"]["chat"]
			if "chat" in self.windows["border"]:
				del self.windows["border"]["chat"]
				
			if self.shape == "big":
				w = self.dimensions["chat"] = {"height": self.mucous.h-13, "width": self.mucous.w-15, "top": 8, "left": 16}
				cs = self.dimensions["roomstatus"] = {"height": 4, "width": w["width"]-2, "top": 2, "left": w["left"]}
			elif self.shape == "widelist":
				w = self.dimensions["chat"] = {"height": self.mucous.h-13, "width": self.mucous.w-25, "top": 8, "left": 26}
				cs = self.dimensions["roomstatus"] ={"height": 4, "width": w["width"]-2, "top": 2, "left": w["left"]}
			elif self.shape in ("noroombox", "small"):
				w = self.dimensions["chat"] = {"height": self.mucous.h-13, "width": self.mucous.w, "top": 8, "left": 1}
				if self.shape in ("noroombox"):
					cs = self.dimensions["roomstatus"] = {"height": 4, "width": w["width"]-2, "top": 2, "left": 1}
					#cs["height"]-2, cs["width"]-1, cs["top"]+1,cs["left"]+1
				elif self.shape in ("small"):
					cs = self.dimensions["roomstatus"] = {"height": 4, "width": w["width"]-15-2, "top": 2, "left": 16}
			elif self.shape == "rightlist":
				w = self.dimensions["chat"] = {"height": self.mucous.h-13, "width": self.mucous.w-15, "top": 8, "left": 1}
				cs = self.dimensions["roomstatus"] = {"height": 4, "width": w["width"]-2, "top": 2, "left": 1}
			elif self.shape == "nostatuslog":
				w = self.dimensions["chat"] = {"height": self.mucous.h-7, "width": self.mucous.w-15, "top": 2, "left": 16}
			elif self.shape == "chat-only":
				w = self.dimensions["chat"] = {"height": self.mucous.h-7, "width": self.mucous.w, "top": 2, "left": 1}
			
			if cs != None:
				brw = self.windows["border"]["roomstatus"] = curses.newwin(cs["height"]+2, cs["width"]+2, cs["top"]-1, cs["left"]-1)
				btw= self.windows["text"]["roomstatus"] = brw.subwin(cs["height"], cs["width"], cs["top"],cs["left"])
				btw.scrollok(0)
					
			self.dimensions["chat"]["start"] = 0
			try:
				mw = self.windows["border"]["chat"] = curses.newwin(w["height"]+2, w["width"], w["top"]-1, w["left"]-1)
				if self.mucous.username == None:
					#mw.border()
					mw.noutrefresh()
					
				tw =self.windows["text"]["chat"] = self.windows["border"]["chat"].subwin(w["height"], w["width"], w["top"], w["left"]-1)
			except Exception, e:
				self.mucous.Help.Log("debug", "Chat Mode: " + str(e))

			tw.scrollok(0)
			tw.idlok(1)

			if self.mucous.Alerts.log in ( "New Chat", "Nick Mention"):
				self.mucous.Alerts.setStatus("")	

			self.set_room(self.current)

			
			curses.doupdate()
		except Exception, e:
			self.mucous.Help.Log("debug", "ChatRooms.Mode: " + str(e))
			
	## Joined a room
	# 
	def Joined(self, name, users, tickers=None):
		try:
			if name not in self.logs["rooms"]:
				self.logs["rooms"][name] = []
				self.logs["roomstatus"][name] = []
				self.OldLogs(name)
						
				
				for user in users:
					self.mucous.user["status"][user] = users[user][0]
					self.mucous.user["statistics"][user] = users[user][1], users[user][2 ], users[user][3], users[user][4]
					
				self.rooms[name] = users.keys()
					#avgspeed, numdownloads, numfiles, numdirs
	
				# tickers == (rooms, [(user1: message1), (user2: message2),] )
				# a string and then a dictionary

				if tickers:
					self.tickers[name] = tickers
				
		except Exception, e:
			self.mucous.Help.Log("debug", "ChatRooms.Joined: " + str(e))
			
	## Leave a room or current room
	# @param self ChatRooms (class)
	# @param room Chat room to be left
	def Leave(self, room=None):
		if room:
			if room in self.rooms:
				self.D.LeaveRoom(room)
			return
		if self.current:
			self.D.LeaveRoom(self.ChatRooms.current)
			
	## Left a room
	# @param self ChatRooms (class)
	# @param room room that was left
	def Left(self, room):
		
		del self.rooms[room]
		joined = self.rooms.keys()
		joined.sort(key=str.lower)
		
		if room == self.current:
			if len(joined) == 1:
				self.Change(None)
			else:
				ix = joined.index(room)
				if ix > 0:
					ix -= 1
				elif ix == 0:
					ix = -1
				self.Change(joined[ix])
				self.AppendChat("Status", joined[ix], '!!!!', "Left room %s" % room)
		joined.remove(room)
		del self.rooms[room]
		del self.tickers[room]
		del self.logs["roomstatus"][room]
		if joined == []:
			self.Change(None)
			self.DrawChatWin()
			self.windows["text"]["chat"].noutrefresh()
		else:
			joined.sort(key=str.lower)
		if room in self.Alerts.alert["CHAT"]:
			del self.Alerts.alert["CHAT"][room]
		curses.doupdate()
		if self.Alerts.log == "%s" % room[:14]:
			self.Alerts.setStatus("")
			
	## Say message In Chat room or current room
	# :: Split \n (newlines) into seperate messages
	# @param self ChatRooms (class)
	# @param room Chat room
	# @param message test
	def SayInChat(self, room, message):
		try:
			
			message = self.mucous.dencode_language(message)
			if room == None or message == None:
				return
			if '\\n' in message:
				
				splited =  message.split('\\n')
				
				if len(splited) > 5:
					
					for i in range(5):
						self.mucous.D.SayRoom(room, splited[i])
					self.mucous.Help.Log("debug", "Your chat message was really long, so it was cut to keep you from getting muted.")
				else:
					for i in range(len(splited)):
						self.mucous.D.SayRoom(room, splited[i])
				
			else:
				self.mucous.D.SayRoom(room, message)
					
		except Exception, e:
			self.mucous.Help.Log("debug", "SayInChat: " + str(e))

				

	## Append status change to log
	# @param self ChatRooms (Class)
	# @param user Username
	# @param room Chat room
	# @param did Is one of [ticker, join, part, change]
	# @param what contains (the ticker if did is ticker) or (away, offline, online if change)
	def AppendStatus(self, user, room, did, what):
		try:

			yes = 0
			if room not in self.logs["roomstatus"]:
				self.logs["roomstatus"][room] = []
			oldlen = len(self.logs["roomstatus"][room])
			if did == "ticker" and what != '':
				if user in self.rooms[room]:
					if room == self.current:
						yes =1
						
			elif did == "join":
				self.logs["roomstatus"][room].append("%s %s joined" % (time.strftime("%H:%M:%S"), user))
				if room == self.current:
					yes =1
					
			elif did == "left":
				self.logs["roomstatus"][room].append("%s %s left" % (time.strftime("%H:%M:%S"), user))
				if room == self.current:
					yes =1
			elif did == "change":
				for rooms11 in self.rooms.keys():
					if user in self.rooms[rooms11]:
						string = "%s %s is %s" % (time.strftime("%H:%M:%S"), user, what)
						if self.logs["roomstatus"][rooms11] == []:
							self.logs["roomstatus"][rooms11].append(string)
							if rooms11 == self.current:
								yes =1
						elif string[10:] != self.logs["roomstatus"][rooms11][-1][10:]:
							self.logs["roomstatus"][rooms11].append(string)
							if rooms11 == self.current:
								yes = 1
								
			if "roomstatus" not in self.windows["text"]:
				return			
			tw = self.windows["text"]["roomstatus"]
			if self.mucous.mode == "chat" and yes == 1:
				if self.scrolling["roomstatus"] >= oldlen -1:
					if len(self.logs["roomstatus"][room]) > 305:
						del self.logs["roomstatus"][room][0]
					self.scrolling["roomstatus"] = -1
					self.DrawStatusText()

		except Exception, e:
			self.mucous.Help.Log("debug", "AppendStatus: " + str(e))
	## Join a room
	# @param self is ChatRooms (Class)
	# @param room is a text string
	def JoinRoom(self, room):
		try:
			self.mucous.D.JoinRoom( self.mucous.dlang( room ) )
		except Exception,e:
			self.mucous.Help.Log("debug", "JoinRoom: " + str(e))
			
	## Loop and Draw the tickers in one of two ways (scrolling, cycling)
	# :: Scrolling shows the entire ticker, while Cycling shows only the part that fits in the viewable area
	# @param self is ChatRooms (Class)
	def DrawTicker(self):
		try:
			if self.mucous.mode != "chat" or self.current not in self.tickers or self.mucous.Config["tickers"]["tickers_enabled"] != 'yes':
				return
			ticks = self.tickers[self.current]
			ttickers = ticks.keys()
			if ttickers == []:
				self.ticker_timer.cancel()
				try:
					self.DrawStatusWin()
					self.DrawStatusText()
					curses.doupdate()
				except:
					pass
			else:
				ttickers.sort(key=str.lower)
				if self.mucous.Config["tickers"]["ticker_scroll"] == "yes":
					if self.mucous.PopupMenu.show == True:
						self.ticker_timer.cancel()
						self.ticker_timer = threading.Timer(float(self.mucous.Config["tickers"]["scrolltime"]), self.DrawTicker)
						self.ticker_timer.start()
						return
					longstring = ""
					for user in ttickers:
						longstring += "[%s] %s " % (user, self.mucous.dlang(ticks[user]))
					if self.shape in ("nostatuslog", "chat-only"):
						bw = self.windows["border"]["chat"]
						s = self.dimensions["chat"]
						padd = -3; posy = 0; posx = 2
					else:
						 
						bw = self.windows["border"]["roomstatus"]
						s = self.dimensions["roomstatus"]
						padd = 0; posy = 5; posx = 1
					
					if self.numticker >= len(longstring):
						self.numticker = 0
					part = longstring[self.numticker:self.numticker+s["width"]-2+padd]
					while len(part) < s["width"]-2 +padd:
						part += longstring[:(s["width"]-2+padd - len(part))] 
					fill = (s["width"]-2 - len(part) +padd) * " "
					
					message = ""
					for m in part:
						message += curses.unctrl(m)
					bw.addstr(posy, posx, "<%s%s>" %(message, fill))
					bw.refresh()
					self.numticker += 1
					#if self.numticker >= len(ttickers):
						#self.numticker = 0
					self.ticker_timer.cancel()
					self.ticker_timer = threading.Timer(float(self.mucous.Config["tickers"]["scrolltime"]), self.DrawTicker)
					self.ticker_timer.start()
					return
			
				
				if self.numticker >= len(ttickers):
					self.numticker = 0
				names = ttickers[self.numticker]
				n = len(names)
				try:
					if self.mucous.PopupMenu.show == True: raise Exception,  "Noticker"
					if self.shape not in ("nostatuslog", "chat-only"):
						if "roomstatus" not in self.windows["border"]:
							return
						bw = self.windows["border"]["roomstatus"]
						s = self.dimensions["roomstatus"]
						tick = str(ticks[names][:s["width"]-7-n])
						fill = (s["width"]-6-len(tick)-len(names)) * " "
						string = "< [%s] %s%s>" % (names, tick, fill)
						bw.addstr(5, 1, self.mucous.dlang( string ))
						bw.refresh()
						
					elif self.shape in ("nostatuslog", "chat-only"):
						mw = self.windows["border"]["chat"]
						s = self.dimensions["chat"]
						tick = str(ticks[names][:s["width"]-25-n])
						fill = (s["width"]-25-len(tick)-len(names)) * " "
						string = "< [%s] %s%s>" %(names, tick, fill)
						mw.addstr(0, 18, self.mucous.dlang( string ))
						mw.refresh()
				except:
					pass
				

				self.numticker += 1

				self.ticker_timer.cancel()
				self.ticker_timer = threading.Timer(float(self.mucous.Config["tickers"]["cycletime"]), self.DrawTicker)
				self.ticker_timer.start()
				
				
		except Exception,e:
			self.mucous.Help.Log("debug", "ChatRooms.DrawTicker: " + str(e))
			
	## Draw the chat window's border
	# @param self is ChatRooms (Class)
	def DrawChatWin(self):
		try:
			s = self.dimensions["chat"]
			mw = self.windows["border"]["chat"]
			if self.selected == "chatroom":
				mw.attron(self.mucous.colors["green"])
				mw.hline(0, 0, curses.ACS_HLINE, s["width"]-1)
				mw.hline(s["height"]+1, 0, curses.ACS_HLINE, s["width"]-1)
				mw.addstr(0, 0, "Oo",  self.mucous.colors["green"] | curses.A_BOLD)
				mw.addstr(0, 3, "< Chat Rooms >",  self.mucous.colors["green"] | curses.A_BOLD)
				mw.addstr(0, s["width"]-1, "^",  self.mucous.colors["green"] | curses.A_BOLD)
				try:
					mw.addstr(s["height"]+1, s["width"]-1, "v",  self.mucous.colors["green"] | curses.A_BOLD)
				except: pass
				mw.addstr(s["height"]+1, 2, "< "+str(abs(self.scrolling["chatroom"]))+" >", self.mucous.colors["green"] | curses.A_BOLD)
				if self.current != None:
					if len(self.logs["rooms"][self.current]) -1 <= abs(self.scrolling["chatroom"]):
						mw.addstr(s["height"]+1, 10, "< AutoScrolling >", self.mucous.colors["green"] | curses.A_BOLD)
				
			else:
				mw.hline(0, 0, curses.ACS_HLINE, s["width"]-1)
				mw.hline(s["height"]+1, 0, curses.ACS_HLINE, s["width"]-1)
				mw.addstr(0, 0, "Oo", curses.A_BOLD)
				mw.addstr(0, 3, "< Chat Rooms >",   curses.A_BOLD)
				mw.addstr(0, s["width"]-1, "^",  curses.A_BOLD)
				try:
					mw.addstr(s["height"]+1, s["width"]-1, "v",  curses.A_BOLD)
				except: pass
# 				mw.addstr(s["height"]+1, 2, "< "+str(abs(self.scrolling["chatroom"]))+" >", curses.A_BOLD)
			mw.noutrefresh()
			
		except Exception,e :
			self.mucous.Help.Log("debug", "ChatRooms.DrawChatWin: " + str(e))

	## Mouse Coordinates in the Chat Rooms Mode
	# @param self is ChatRooms (class)
	# @param x is the horizontal position from the left
	# @param y is the vertical postion from the top
	# @param z is unimportant
	# @param event is the mouse event (button, doubleclick, etc) represented by a number
	def MouseChat(self, x, y, z, event):
		try:
			w = self.dimensions["chat"]
			if y == w["top"]-1 and x >= w["left"]-1 and x < w["left"]+3:
				self.ChatLayout()
				return
			# Clickable room switch
			
			if "roombox" in self.dimensions and self.shape not in ( "noroombox", "chat-only"):
				roombox = self.dimensions["roombox"]
				if y >= roombox["top"]-1 and y < roombox["top"] + roombox["height"] and x < roombox["width"] + roombox["left"] and x > roombox["left"]:
					if self.selected != "roombox":
						self.selected = "roombox"
						self.Mode()
					y -= roombox["top"]
					if "start" not in roombox:
						return
					if y  + roombox["start"] in range(len(self.logs["roombox"][self.current])):
						
						sup = y  + roombox["start"]
						if event in ( 4096, 16384):
							if sup != self.scrolling["roombox"]:
								self.scrolling["roombox"] = sup
							self.DrawBox()
							
							self.mucous.PopupMenu.Create("roombox", 0, True)
							curses.doupdate()
						else:
							if sup != self.scrolling["roombox"]:
								self.scrolling["roombox"] = sup
								self.DrawBox()
								curses.doupdate()
					return
				elif y == roombox["top"] + roombox["height"] and x < roombox["width"] + roombox["left"] and x > roombox["left"]:
					self.ModifyConfig("autojoin", self.current, '')
						
			if y == self.mucous.h-3 or y == self.mucous.h-4:
				if x>= self.mucous.w-27 and x < self.mucous.w-18:
					self.mucous.PopupMenu.Create("encoding", 0, True)
				
				elif x >= self.mucous.w-17 and x < self.mucous.w-1:
					joined = self.rooms.keys()
					joined.sort(key=str.lower)
					if not self.current in joined:
						ix = 0
					else:
						ix = joined.index(self.current)
						
						if x >= self.mucous.w-9 and x < self.mucous.w-1:
							# Next Button
							ix += 1
						elif x <= self.mucous.w-10 and x >= self.mucous.w-17:
							# Prev Button
							ix -= 1
						else:
							return
						if ix < 0:
							ix = -1
						elif ix >= len(joined):
							ix = 0
					self.Change(joined[ix])
					
			elif y  in (w["top"] + w["height"], w["top"] + w["height"]-1) and x >= w["left"] + w["width"]-5 and x <= w["left"] + w["width"]:
				self.mucous.key = "KEY_NPAGE"
				self.mucous.ScrollText("KEY_NPAGE")
				
			elif y in ( w["top"], w["top"]+1)  and x >= w["left"] + w["width"]-5 and x <= w["left"] + w["width"]:
				self.mucous.key = "KEY_PPAGE"
				self.mucous.ScrollText("KEY_PPAGE")
			else:
				if y >= w["top"]-1 and y < w["top"] + w["height"] +1 and x >= w["left"] -1 and x < w["left"] +w["width"]+1:
					if self.selected != "chatroom":
						self.selected = "chatroom"
						self.Mode()
				if "roomstatus" in self.dimensions and self.shape not in ( "nostatuslog", "chat-only") and self.selected != "roomstatus":
					w =  self.dimensions["roomstatus"]
					if y >= w["top"]-1 and y < w["top"] + w["height"] +1 and x >= w["left"] -1 and x < w["left"] +w["width"]+1:
						self.selected = "roomstatus"
						self.Mode()
		except Exception, e:
			self.mucous.Help.Log("debug", "MouseChat: " +str(e) )
			
	## Read Old Chat Room Logs from Disk
	# @param self is ChatRooms (class)
	# @param room room's name used to get log file
	def OldLogs(self, room):
		try:
			# Read from Chat Room Logs
			if "\\" in room: room = room.replace("/", "\\")
			if os.path.exists(os.path.expanduser(self.mucous.Config["mucous"]["log_dir"])+"/rooms/"+room):
				path = os.path.expanduser(self.mucous.Config["mucous"]["log_dir"])+"/rooms/"+room
				f = open(path, "r")
				a = f.read()
				f.close()
				lines = a.split("\n" )
				numlines = -30
				if len(lines) <= abs(numlines):
					numlines = 0
				for line in lines[numlines:]:
					if line == "":
						continue
					timex = line[12:20]
					if line[21] == "[":
						user = line[22:]
						if line.find("\t") == -1:
						# old format
							user = user[:user.find("]")]
							message = line[21+len(user)+3:]
						else:
							# new format with Tab
							user = user[:user.find("\t")-1]
							message = line[line.find("\t")+1:]
					else:
						user = line[21:]
						user = user[:user.find(" ")]
						message = line[21+len(user)+1:]
						
					
					if message[:4] == "/me ": 
						full_message = ["Me", timex, user, message[4:]]
					else:
						full_message = ["Normal", timex, user, message]
					self.logs["rooms"][room].append(full_message)
				self.logs["rooms"][room].append(["Status", "--------", "!!!!", "Connected to Museek"])
			
		except Exception,e:
			self.mucous.Help.Log("debug", "OldLogs: " +str( e) )
			
	## Draw Status Window Text
	# @param self is ChatRooms (class)
	def DrawStatusText(self):
		try:
			if self.shape in ("nostatuslog", "chat-only"):
				return
			if self.mucous.PopupMenu.show == True:
				return
			if self.mucous.mode != "chat":
				return
			s = self.dimensions["chat"]
			tw = self.windows["text"]["roomstatus"]
			w = self.dimensions["roomstatus"]
			
			tw.erase()
			tw.idlok(1)
	
			if self.current == None or self.logs["roomstatus"][self.current] == []:
				tw.noutrefresh()
				return
				
		
			if self.scrolling["roomstatus"] == -1:
				self.scrolling["roomstatus"] = len(self.logs["roomstatus"][self.current])

			clipped_list, self.scrolling["roomstatus"], self.dimensions["roomstatus"]["start"] = self.mucous.FormatData.scrollbox(self.logs["roomstatus"][self.current], self.scrolling["roomstatus"], self.dimensions["roomstatus"]["height"])
			count = 0
			try:
				for line in clipped_list:
					#self.mucous.Help.Log("debug", line +str(self.scrolling["roomstatus"]))
					if len(line) > w["width"]:
						line = line [:w["width"] -len(line) ]
					else:
						line += " " * (w["width"] -len(line))
					if count + self.dimensions["roomstatus"]["start"] == self.scrolling["roomstatus"]:
						tw.addstr(self.mucous.dlang( line) , curses.A_BOLD)
					else:
						tw.addstr(self.mucous.dlang( line ))
					count += 1

			except Exception, e:
				pass

			
			tw.noutrefresh()
		except Exception, e:
			self.mucous.Help.Log("debug", "DrawStatusText: " + str(e))
					
	## Draw the contents of the user-box
	# A status asterix (*) followed by a username
	# @param self is ChatRooms (class)
	# @param user User's name
	# @param start Position to indicate highlight status
	def DrawBoxUsers(self, user, start):
		# RoomBox List Display
		try:
			w = self.dimensions["roombox"]
			mw = self.windows["border"]["roombox"]
			tw = self.windows["text"]["roombox"]
			if self.current == None or self.logs["roombox"][self.current] == []:
				tw.addstr("No one")
				return
			try:
				if user in self.mucous.user["status"]:
					if self.mucous.user["status"][user] == 1:
						tw.addstr('* ', self.mucous.colors["yellow"]|curses.A_BOLD)
					elif  self.mucous.user["status"][user] == 2:
						tw.addstr('* ', self.mucous.colors["green"]|curses.A_BOLD)
					elif self.mucous.user["status"][user] == 0:
						tw.addstr('* ', self.mucous.colors["red"]|curses.A_BOLD)
				else:
					tw.addstr('* ', curses.A_BOLD)
				if self.mucous.config.has_key("banned"):
					if user in self.mucous.config["banned"].keys():
						if self.scrolling["roombox"] == self.logs["roombox"][self.current].index(user):
							attrib = curses.A_BOLD | curses.A_REVERSE | self.mucous.colors["red"]
						else: attrib = self.mucous.colors["red"]| curses.A_BOLD 
						
					elif user in self.mucous.config["ignored"].keys():
						if self.scrolling["roombox"] == self.logs["roombox"][self.current].index(user):
							attrib = curses.A_BOLD | curses.A_REVERSE | self.mucous.colors["yellow"]
						else: attrib = self.mucous.colors["yellow"]| curses.A_BOLD 
						
					elif user in self.mucous.config["trusted"].keys():
						if self.scrolling["roombox"] == self.logs["roombox"][self.current].index(user):
							attrib = curses.A_BOLD | curses.A_REVERSE | self.mucous.colors["cyan"]
						else:
							attrib = self.mucous.colors["cyan"] | curses.A_BOLD 
								
					elif user in self.mucous.config["buddies"].keys():
						if self.scrolling["roombox"] == self.logs["roombox"][self.current].index(user):
							attrib = curses.A_BOLD | curses.A_REVERSE | self.mucous.colors["green"]
						else:
							attrib = self.mucous.colors["green"]| curses.A_BOLD 
					else:
						if self.scrolling["roombox"] == self.logs["roombox"][self.current].index(user):
							attrib = curses.A_BOLD | curses.A_REVERSE 
						else:
							attrib = curses.A_NORMAL	
				else:
					if self.scrolling["roombox"] == self.logs["roombox"][self.current].index(user):
						attrib = curses.A_BOLD | curses.A_REVERSE 
					else:
						attrib = curses.A_NORMAL
				if len(user[:w["twidth"]-2]) < w["twidth"]-2:
					space = " " * ( w["twidth"]-2 - len(user[:w["twidth"]-2]))
				else: space =''
				tw.addstr(self.mucous.dlang(user[:w["twidth"]-2])+space, attrib)	
				
			except:
				pass
		except Exception, e:
			self.mucous.Help.Log("debug", "DrawBoxUsers " +str(e))	
			
	## Create the window and border of the user-box
	# @param self is ChatRooms (class)
	def DrawBox(self):
		# RoomBox Shape Display
		try:
			
			if self.mucous.mode != 'chat' or self.shape == "noroombox":
				return
			# Cleanup stale windows
			if "roombox" in self.windows["text"]:
				del self.windows["text"]["roombox"]
			if "roombox" in self.windows["border"]:
				del self.windows["border"]["roombox"]
			
			if self.shape in ("big", "nostatuslog", "widelist", "rightlist"):
				w = self.dimensions["chat"]
				if self.shape == "rightlist":
					s = self.dimensions["roombox"] = {"height": self.mucous.h-7, "top": 2, "left": (w["width"]), "width": self.mucous.w-w["width"], "start": -1 }
				else:
					s = self.dimensions["roombox"] = {"height": self.mucous.h-7, "top": 2, "left": 0, "width": self.mucous.w-w["width"], "start": -1 }
				# Create wi
				mw = self.windows["border"]["roombox"]  = curses.newwin(s["height"]+2, s["width"], s["top"]-1, s["left"])
				if self.selected == "roombox":
					mw.attron(self.mucous.colors["green"])

				mw.attroff(self.mucous.colors["green"])
				if self.shape == "rightlist":
					self.dimensions["roombox"]["twidth"] = s["width"]-1
					self.dimensions["roombox"]["tleft"] = s["left"]+1
				else:
					self.dimensions["roombox"]["twidth"] = s["width"]-1
					self.dimensions["roombox"]["tleft"] = s["left"]
				tw = self.windows["text"]["roombox"] = mw.subwin(s["height"], s["twidth"], s["top"], s["tleft"])
				
			elif self.shape == "small":
				s = self.dimensions["roombox"] = {"height": 4, "top": 2, "left": 0,  "width": 15}
				
				mw = self.windows["border"]["roombox"] = curses.newwin(s["height"]+2, s["width"], s["top"]-1, s["left"])
				if self.selected == "roombox":
					mw.attron(self.mucous.colors["green"])

				mw.attroff(self.mucous.colors["green"])
				self.dimensions["roombox"]["twidth"] = s["width"] -1
				tw = self.windows["text"]["roombox"] = mw.subwin(s["height"], s["twidth"], s["top"], s["left"])
				
			if self.shape in ("big", "small", "nostatuslog", "widelist", "rightlist"):
				tw.scrollok(0)
				tw.idlok(1)
			

				if self.current != None:
					try:
						if self.selected == "roombox":
							mw.addstr(0, 0, "Users: "+str(len(self.rooms[self.current])), self.mucous.colors["green"]|curses.A_BOLD)
						else:

							mw.addstr(0, 0, "Users: "+str(len(self.rooms[self.current])),  curses.A_BOLD)
						
					except:
						pass
					if "autojoin" in self.mucous.config:
						try:
							if self.selected == "roombox":
								cs  = self.mucous.colors["green"] |curses.A_BOLD
							else:
								cs  = curses.A_BOLD
							if self.current in self.mucous.config["autojoin"].keys():
								
								mw.addstr(self.dimensions["roombox"]["height"]+1, 0, "[x] AutoJoined",  cs)
							else:
								mw.addstr(self.dimensions["roombox"]["height"]+1, 0, "[ ] AutoJoined",  cs)
						except Exception, e:
							self.mucous.Help.Log("debug", "AutoJoined: " + str(e))
							
				mw.noutrefresh()
			
				if self.current != None:
					self.logs["roombox"][self.current] = []
					if len( self.rooms[self.current] ) > 0:
						self.logs["roombox"][self.current] = self.rooms[self.current]
						self.logs["roombox"][self.current].sort(key=str.lower)
				
					try:
						if self.logs["roombox"][self.current] != []:
							clipped_list, self.scrolling["roombox"], self.dimensions["roombox"]["start"] = self.mucous.FormatData.scrollbox(self.logs["roombox"][self.current], self.scrolling["roombox"], self.dimensions["roombox"]["height"])
							# Draw users
							self.FormatBox()
						else:
							tw.addstr("* Empty")
							tw.noutrefresh()
					except Exception, e:
						self.mucous.Help.Log("debug", "RSB: " + str(e))
			#curses.doupdate()
		except Exception, e:
			self.mucous.Help.Log("debug", "DrawBox " +str(e))
			
			
	## Start displaying tickets in one second
	# @param self is ChatRooms (class)
	def TickersStartTimer(self):
		try:
			if self.mucous.mode == "chat":

				if self.rooms.keys() != []:
					self.numticker = 0
					self.ticker_timer.cancel()
					self.ticker_timer = threading.Timer(1.0, self.DrawTicker)
					self.ticker_timer.start()
		except Exception, e:
			self.mucous.Help.Log("debug", "TickersStartTimer: " + str(e))
	## Toggle whether tickers are displayed or not 
	# @param self is ChatRooms (class)
	def ToggleTickersDisplay(self):
		try:
			if str(self.mucous.Config["tickers"]["tickers_enabled"]) == 'no':
				self.mucous.Config["tickers"]["tickers_enabled"] = 'yes'
				
			elif str(self.mucous.Config["tickers"]["tickers_enabled"]) == 'yes':
				self.mucous.Config["tickers"]["tickers_enabled"] = 'no'
			if self.mucous.mode=="setup":
				self.mucous.Setup.Mode()
		except Exception, e:
			self.mucous.Help.Log("debug", "ToggleTickersDisplay: "+str(e))
			
	## Toggle the way Tickers are displayed (Scrolling, Cycling) 
	# @param self is ChatRooms (class)
	def ToggleTickers(self):
		try:
			if self.mucous.Config["tickers"]["ticker_cycle"] == 'no':
				self.mucous.Config["tickers"]["ticker_cycle"] = 'yes'
				if str(self.mucous.Config["tickers"]["ticker_scroll"]) == 'yes':
					self.mucous.Config["tickers"]["ticker_scroll"] = 'no'
				
			elif self.mucous.Config["tickers"]["ticker_cycle"] == 'yes':
				self.mucous.Config["tickers"]["ticker_cycle"] = 'no'
				if str(self.mucous.Config["tickers"]["ticker_scroll"]) == 'no':
					self.mucous.Config["tickers"]["ticker_scroll"] = 'yes'
				
				
			#self.ticker_timer.cancel()
			if self.mucous.mode=="chat":
				self.DrawStatusWin()
				self.DrawStatusText()
				curses.doupdate()
			elif self.mucous.mode=="setup":
				self.mucous.Setup.Mode()
		except Exception, e:
			self.mucous.Help.Log("debug", "ToggleTickers: "+str(e))
			
	## Interator for Chat Room User List
	# Clears, and starts drawing from the scroll position
	def FormatBox(self):
		try:
			w = self.dimensions["roombox"]
			lol = self.logs["roombox"][self.current]
			mw = self.windows["border"]["roombox"]
			tw = self.windows["text"]["roombox"]
			tw.erase()
			clipped_list, self.scrolling["roombox"], self.dimensions["roombox"]["start"] = self.mucous.FormatData.scrollbox(lol, self.scrolling["roombox"], w["height"])
			for lines in clipped_list:
				self.DrawBoxUsers(lines, w["start"])
			tw.noutrefresh()
		except Exception, e:
			self.mucous.Help.Log("debug", "FormatBox: " + str(e))
			
	## Format Current Chat Room
	# @param self is ChatRooms (class)
	def FormatChatText(self):
		try:
			if self.current != None:
				w = self.dimensions["chat"]
				selected_log = self.logs["rooms"][self.current]
				lol = self.LineWrap(selected_log, w)
				
				if self.scrolling["chatroom"] == -1:
					self.scrolling["chatroom"] = len(lol)
	
				clipped_list, self.scrolling["chatroom"], self.dimensions["chat"]["start"] = self.mucous.FormatData.scrollbox(lol, self.scrolling["chatroom"], w["height"])
				
				self.windows["text"]["chat"].erase()
				for lines in clipped_list:
					self.DrawChatText(lines)
	
			self.DrawChatWin()
			self.windows["text"]["chat"].noutrefresh()
		except Exception, e:
			self.mucous.Help.Log("debug", "FormatChatText: " + str(e))
			
	## Insanely complex line wraping for chat messages
	# Needed for proper scrolling
	# @param self is ChatRooms (class)
	# @param the_list self.logs["rooms"][self.current]
	# @param w self.dimensions["chat"]
	# @return cut_list
	def LineWrap(self, the_list, w):
		# we wrap text here so that scrolling works properly... 
		try:
			pos = 0
			cut_list = []
			for mtype, timestamp, username, message in the_list:
				length = 0
				message = self.mucous.dlang(message)
				#mtype, timestamp, username, message = line[0], line[1], line[2], line[3]
				if mtype == "Me":
					#username = self.mucous.dlang(username)
					pre = " * %s " % username
					s = "%s" % message
					length += len(timestamp) + len(pre)
# 				elif mtype == "List":
# 					room = self.current
# 					pre = "Users in %s: "% room
# 					length +=  len(pre)
# 					for user, color in message:
# 						length += len(self.dlang(user))
				elif mtype in ("Mentioned", "Normal", "Status"):
					if username != "": # Universal Timestamp
						if mtype == "Status": # Mucous debugging message
							length += len(timestamp) + 2
						else: # Normal user chat
							length += len(timestamp) + 4
						
						#length += len(self.dlang(username))
						length += len(username)
		
				if "\n" in message:
					
					messagez = message.split('\n')
					# Wrap first line
					firstmsg = messagez[0]
					wit =  len(timestamp) + 4 + len(username)
					lm = len(firstmsg)
					mess = lm - ( (wit + lm ) - w["width"])
					cut_list.append( [ mtype, timestamp, username, firstmsg[:mess] ] )
					restmess = firstmsg[mess:]
					div = ( len(restmess)/w["width"] ) + 1
					spaces= (w["width"] * div) -  len(restmess)
					for seq in range(div):
						if mtype == "Me":
							cut_list.append(['cutme', '', '', restmess[:w["width"]] ])
						else:
							cut_list.append(['cut', '', '', restmess[:w["width"]] ])
						restmess = restmess[w["width"]:]

					# Prepend -- to all following lines
					m = []
					for messages in messagez[1:]:
						m.append("--"+messages)
					# Wrap each of the following lines
					for messages in m:
						lm = len(messages)
						restmess = messages
						div = ( len(restmess)/w["width"] ) + 1
						spaces= (w["width"] * div) -  len(restmess)
						for seq in range(div):
							if mtype == "Me":
								cut_list.append(['cutme', '', '', restmess[:w["width"]] ])
							else:
								cut_list.append(['cut', '', '', restmess[:w["width"]] ])
							restmess = restmess[w["width"]:]
					pos += 1
					continue	
							
					# Short message
				if length +len(message) <= w["width"]:
					cut_list.append([mtype, timestamp, username, message])
					
					# long message
				elif length +len(message) > w["width"]:
					lm = len(message)
					mess = lm - ( (length + lm ) - w["width"])
					cut_list.append( [ mtype, timestamp, username, message[:mess] ] )
					restmess = message[mess:]
					div = ( len(restmess)/w["width"] ) + 1
					spaces= (w["width"] * div) -  len(restmess)
					for seq in range(div):
						#self.mucous.Help.Log("debug", str(div)+"--" + restmess[:w["width"]] )
						if mtype == "Me":
							cut_list.append(['cutme', '', '', restmess[:w["width"]] ])
						else:
							cut_list.append(['cut', '', '', restmess[:w["width"]] ])
						restmess = restmess[w["width"]:]
 						
				pos += 1
			return cut_list
		except Exception, e:
			# Exceptions are Inevitable
			self.mucous.Help.Log("debug", "LineWrap: " + str(e))
			
	## Draw Chat Log Window Text
	# @param self is ChatRooms (class)
	# @param roomlinenumber number of line in chat room log
	def DrawChatText(self, roomlinenumber):
		try:
			room = self.current
			mtype, timestamp, username, message2 = roomlinenumber
			lang = self.mucous.Config["mucous"]["language"]
			w = self.dimensions["chat"]
			room = self.mucous.dlang(room)
			length = 0
			tw = self.windows["text"]["chat"]
			message = ""
			for m in message2:
				message += curses.unctrl(m)
			try:
				if mtype == "Me":
					# /me message
					
					tw.addstr(timestamp)
					username = self.mucous.dlang(username)
					pre = " * %s " % username
					tw.addstr(pre, self.mucous.colors["green"] | curses.A_BOLD)
					s = "%s" % self.mucous.dlang(message)
					tw.addstr(s, self.mucous.colors["green"] | curses.A_BOLD)
					length += len(timestamp) + len(pre)+ len(s)
				elif mtype == "List":
					# List of users in Room
					
					pre = "Users in %s: "% room
					#self.textwin.addstr(pre)
					length +=  len(pre)
					for username, color in message:
						username = self.mucous.dlang(username)
						length += len(username)
						if color == "Me":
							tw.addstr(username, curses.A_BOLD)
						elif color == "Left":
							tw.addstr(username, self.mucous.colors["yellow"])
						elif color == "Banned":
							tw.addstr(username, self.mucous.colors["red"])
						elif color == "Buddies":
							tw.addstr(username, self.mucous.colors["green"])
						elif color == "NotLast":
							tw.addstr(username)
						elif color == "Normal":
							tw.addstr(username)
							
				elif mtype == "cut":
					s = self.mucous.dlang(message) 
					tw.addstr(s)
					length += len(s)
				elif mtype == "cutme":
					s = self.mucous.dlang(message) 
					tw.addstr(s, self.mucous.colors["green"] | curses.A_BOLD)
					length += len(s)
				else:
					if username != "":
						# Universal Timestamp
						tw.addstr(timestamp)
						if mtype == "Status":
							# Mucous debugging message
							pre = " "
							tw.addstr(pre)
							
						else:
							# Normal user chat
							pre = " ["
							tw.addstr(pre, curses.A_BOLD | self.mucous.colors["black"])
					length += len(timestamp) + len(pre)
					
					name = self.mucous.dlang(username)
					if self.mucous.config.has_key("banned"):
						if username == self.mucous.username:
							tw.addstr(username ,  curses.A_BOLD )
						elif username not in self.rooms[room]:
							tw.addstr(name, self.mucous.colors["yellow"])
						elif username in self.mucous.config["banned"].keys():
							tw.addstr(name, self.mucous.colors["red"])
						elif username in self.mucous.config["buddies"].keys():
							tw.addstr(name, self.mucous.colors["green"])
						else:
							tw.addstr(name)
					else:
						tw.addstr(name)
					length += len(name)
					
					if username != "":
						if mtype == "Status":
							suf = " "
							tw.addstr(" ")
						else:
							suf = "] "
							tw.addstr(suf, curses.A_BOLD | self.mucous.colors["black"])
					length += len(suf)
					if mtype == "Mentioned":
						x = message.split(" ")
						for e in x:
							e = self.mucous.dlang(e)
							
							if self.mucous.username not in e:
								tw.addstr(e)
								length += len(e)
							elif self.mucous.username in e:
								tw.addstr(e, self.mucous.colors["cyan"] | curses.A_BOLD)
								length += len(e)
							if e is not  x[-1]:
								if length < w["width"]:
									tw.addstr(" ")
									length +=  1
					elif mtype == "Normal":
						
						s = self.mucous.dlang(message) 
						tw.addstr(s)
						length += len(s)
					elif mtype == "Status":
						s = self.mucous.dlang(message) 
						tw.addstr(s)
						length += len(s)
				
	
			except Exception, e:
				pass
				# Exceptions are Inevitable
			try:
				if length < w["width"]:
					tw.addstr(" " * (w["width"] - length))
			except Exception, e:
				pass
		except Exception, e:
			self.mucous.Help.Log("debug", "DrawChatText: " + str(e))
			
	## Append message to Chat Log
	# @param self is ChatRooms (class)
	# @param mtype type of message
	# @param room room
	# @param user username
	# @param message text
	def AppendChat(self, mtype, room, user, message):
		try:
			if room == None:
				room = self.current
			full_message = [mtype, time.strftime("%H:%M:%S"), user, message]
			if len( self.logs["rooms"][room] ) >= 700:
				del self.logs["rooms"][room][0]
			oldlen = len(self.logs["rooms"][room])
			self.logs["rooms"][room].append(full_message)
				
			if self.mucous.mode == "chat":
				if room == self.current and self.selected == "chatroom":
					if self.scrolling["chatroom"] >= oldlen -1:
						self.scrolling["chatroom"] = -1
						self.FormatChatText()
				elif room == self.current and self.selected == "roombox":
					temp = self.scrolling["chatroom"]
					self.scrolling["chatroom"] = -1
					self.FormatChatText()
					self.scrolling["chatroom"] = temp
		except Exception,e :
			self.mucous.Help.Log("debug", "AppendChat: " + str(e))

	## Draw Chat Room Status Window Border 
	# @param self is ChatRooms (class)
	def DrawStatusWin(self):
		try:
			if self.shape in ("nostatuslog", "chat-only"):
				return
			w = self.dimensions["chat"]
			bw = self.windows["border"]["roomstatus"]
			
			if self.mucous.PopupMenu.show == True: raise  Exception,  "popup"
			
			if self.shape in ("noroombox", "big", "small", "rightlist", "widelist"):
				if self.selected == "roomstatus":
					bw.attron(self.mucous.colors["green"])
				else:
					bw.attroff(self.mucous.colors["green"])
				bw.border()
				bw.addstr(0, 3, "<")
				bw.addstr(0, 4, " Status Log ", self.mucous.colors["blue"] | curses.A_BOLD)
				bw.addstr(0, 16, ">")
				bw.noutrefresh()
		except:
			pass
				
	## Switch to another Chat Window Layout
	# @param self is ChatRooms (class)
	def ChatLayout(self):
		try:
# 			[ "small","big","widelist","rightlist","nostatuslog","chat-only","noroombox"]

			if self.shape == "noroombox":
				self.shape = "small"
				self.selected  = "roombox"
			elif self.shape == "small":
				self.shape = "big"
				self.selected  = "roombox"
			elif self.shape == "big":
				self.shape = "widelist"
				self.selected  = "roombox"
			elif self.shape == "widelist":
				self.shape = "rightlist"
				self.selected  = "roombox"
			elif self.shape == "rightlist":
				self.shape = "nostatuslog"
				self.selected  = "chatroom"
			elif self.shape == "nostatuslog":	
				self.shape = "chat-only"
				self.selected  = "chatroom"
			elif self.shape == "chat-only":
				self.shape = "noroombox"
				self.selected  = "chatroom"
				
			self.mucous.Config["mucous"]["roombox"] = self.shape
			self.Mode()
		except Exception, e:
			self.mucous.Help.Log("debug", "ChatLayout: " + str(e))
			
	
	## Change Room (Reset scrolling)
	# @param self is ChatRooms (class)
	# @param r room name
	def Change(self, r):
		self.scrolling["chatroom"] = self.scrolling["roomstatus"] = -1
		self.scrolling["roombox"] = 0
		self.set_room(r)
		
	## Change Room
	# @param self is ChatRooms (class)
	# @param r room name
	def set_room(self, r):
		try:
			
			self.current = r
			self.mucous.Spl["title"]= r
			
			if self.mucous.mode != "chat":
				return
			
			# Change title in edit window
			if self.shape not in ("chat-only", "nostatuslog"):
				self.DrawStatusWin()
				self.DrawStatusText()
			self.mucous.set_edit_title(self.current)
			# Display Next-room hotspot's text
			try:
				# Encoding
				if self.current != None:
					if self.current in self.mucous.config["encoding.rooms"]:
						blah = self.mucous.config["encoding.rooms"][self.current]
					else:
						blah = self.mucous.config["encoding"]["network"]
					
					self.mucous.windows["inputborder"].addstr(0, self.mucous.w-17-len(blah)-4, "<" + (" " *( len(blah) +2) )+  ">")
					self.mucous.windows["inputborder"].addstr(0, self.mucous.w-17-len(blah)-2, blah, self.mucous.colors["cyan"] | curses.A_BOLD)
					# Previous, Next Buttons
					self.mucous.windows["inputborder"].addstr(0, self.mucous.w-17, "<      >")
					self.mucous.windows["inputborder"].addstr(0, self.mucous.w-15, "Prev", self.mucous.colors["cyan"] | curses.A_BOLD)
					self.mucous.windows["inputborder"].addstr(0, self.mucous.w-9, "<      >")
					self.mucous.windows["inputborder"].addstr(0, self.mucous.w-7,"Next", self.mucous.colors["cyan"] | curses.A_BOLD)
	
					# Clean screen
					self.mucous.windows["inputborder"].noutrefresh()
			except Exception, e:
				pass
			
			try:
				self.windows["input"].noutrefresh()
			except:
				pass
			self.DrawBox()
			
			# Display chat log
			if self.selected == "chatroom":
				self.windows["border"]["chat"].attron(self.mucous.colors["green"])
			else:
				self.windows["border"]["chat"].attroff(self.mucous.colors["green"])
			
			self.FormatChatText()
			
			# Clear Alert log
			if "%s" % self.current == self.mucous.Alerts.log:
				self.mucous.Alerts.setStatus("")
			
			self.TickersStartTimer()
			try:
				self.windows["text"]["chat"].noutrefresh()
			except:
				pass
			
			self.mucous.Alerts.Check()
		except Exception, e:
			self.mucous.Help.Log("debug", "set_room: " + str(e))
		
		