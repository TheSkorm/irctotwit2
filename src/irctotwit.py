#!/usr/bin/python
#
# irctotwit.py
# Copyright (C) Michael Wheeler 2008 <twitirc@theskorm.net>
# 
# main.py is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# main.py is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
import sys
import socket
import string
import twitter
import time
fail = False
if len(sys.argv) == 7:
    HOST=sys.argv[1]
    PORT=int(sys.argv[2])
    NICK=sys.argv[3]
    IDENT=sys.argv[4]
    REALNAME=sys.argv[5]
    CHAN="#" + sys.argv[6]
    print "Host - " + HOST
    print "Port - " + str(PORT)
    print "Nick - " + NICK
    print "Ident - " + IDENT
    print "Realname - " + REALNAME
    print "Chan - " + CHAN
else:
    print "Usage irctotwit.py server port nick ident realname channel"
    fail = True

sockettimeout=10
twitterfetch=120
timeout=500
users={}
last={}
cache={}


while fail == False:
  try:
    readbuffer=""
    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.send("NICK %s\r\n" % NICK)
    s.send("USER %s %s bla :%s\r\n" % (IDENT, HOST, REALNAME))
    lasttime = time.time()
    lasttime2 = time.time()
    s.settimeout(sockettimeout)
    who=[]
    while 1:
        try:
           readbuffer=readbuffer+s.recv(1024)
        except socket.timeout:
           pass
        temp=string.split(readbuffer, "\n")
        readbuffer=temp.pop( )
        for line in temp:
            line=string.rstrip(line)
            line=string.split(line)
            if (line):
               lasttime2 = time.time()
            if(line[1]=="352"):
                 who.append(line[7] +"!"+line[4] +"@"+ line[5])
            if(line[1]=="315"):
                 todel=[]
                 for user in users:
                     if user not in who:
                         print "Dropping user " + user
                         todel.append(user)
                 for user in todel:
                     users.pop(user)
            if(line[1]=="266"):
                 s.send("JOIN %s\r\n" % CHAN)
            if(line[1]=="NICK"): 
                 print "Nick change, " + line[0][1:] + " to " + line[2][1:] +"!"+  line[0][1:].split("!")[1]
                 if line[0][1:] in users:
                     temp = users[line[0][1:]]
                     users[line[2][1:] + "!" +line[0][1:].split("!")[1]] = temp
                     users.pop(line[0][1:])
            if(line[0]=="PING"):
                s.send("PONG %s\r\n" % line[1])
                lasttime2 = time.time()
            if(line[1]=="PRIVMSG" and line[2].lower()==NICK.lower() and line[3].lower()==":login"):
                if len(line) > 5:
                  try:
                    users[line[0][1:]] = twitter.Api(username=line[4], password=line[5])
                    user = line[0][1:]
                    statuses = users[user].GetUserTimeline(users[user]._username)
                    statuses += users[user].GetFriendsTimeline()
                    cache[user]=[]
                    try:
                      for status in statuses:
                        if status.GetId() not in cache[user]:
                            cache[user].append(status.GetId()) 
                    except :
                        print "Error checking %s :S" % user
                  except :
                     print "Error updating %s" % user
                elif len(line) > 4:
                  try:  
                    users[line[0][1:]] = twitter.Api(username=line[4])
                    user = line[0][1:]
                    statuses = users[user].GetUserTimeline(users[user]._username)
		    cache[user]=[]
                  except :
                    print "Error updating %s" % user
                  try:
                      for status in statuses:
                        if status.GetId() not in cache[user]:
                            cache[user].append(status.GetId()) 
                  except :
                        print "Error checking %s :S" % user
                s.send("PRIVMSG %s :Logged in\r\n" % line[0].split("!")[0][1:])
            if(line[1]=="PRIVMSG" and line[2].lower()==NICK.lower() and line[3] == ':!t') and line[0][1:] in users:
                try:
                   finline=""
                   for word in line[4:]:
                       finline += " " + word
                   twit = finline[1:]
                   users[line[0][1:]].PostUpdate(twit)
                   print "twitting for %s" % line[0]
                except :
                   pass
        if lasttime  + twitterfetch <= time.time():
            print "Checking for updates..."
            s.send("WHO %s\r\n" % CHAN)
            who=[]
            for user in users:
                try:
                    statuses = users[user].GetUserTimeline(users[user]._username)
                except :
                    print "Error updating %s" % user
                if users[user]._password:
                   try:
		      statuses += users[user].GetFriendsTimeline()
                   except :
                      print "Error grabing status"
                try:
                      for status in statuses:
                        if status.GetId() not in cache[user]:
			    nick = user.split("!")[0]
                            s.send("PRIVMSG %s : %s - %s \r\n" % (nick,status.GetUser().GetScreenName(),status.GetText().replace("&gt;",">").replace("&lt;","<")))
                            cache[user].append(status.GetId()) 
                except :
                        print "Error checking %s :S" % user
            lasttime = time.time()
        if lasttime2 + timeout <= time.time():
            print "Ping time out"
            break
    print "Reconnecting" 
  except :
    time.sleep(0.5)
    print "error"
