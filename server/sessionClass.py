# Allows clientHandlers to interact with Sudoku instance
# Keeps track of game status and notifies clients about
# changes. sessionClass objects are created by clientHandlers
import logging
FORMAT='%(asctime)s (%(threadName)-2s) %(message)s'
logging.basicConfig(level=logging.DEBUG,format=FORMAT)
LOG = logging.getLogger()

import os,sys,inspect
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from messageProtocol import *
from clientHandler import *
from serverMain import *
from threading import Thread, Lock, currentThread
from sudoku_new import *


class sessionClass():
    def __init__(self, sessName, maxClients, Server):
        # Server object and session name
        self.Server = Server
        self.sessName = sessName
        # Initiates a sudoku instance
        self.sudoku = Sudoku(LEVEL)
        self.tableLock = Lock()
        # Holds game session clients
        self.clients = []
        self.maxClients = maxClients
        self.gameRunning = False
        self.clientsLock = Lock()

    def notify_update(self,msg):
        # can be used to send a message with notify header
        joined = filter(lambda x: x.session!=None, self.clients)
        map(lambda x: x.send_notification(msg), joined)

    def send_specific_update(self,header,msg):
        # can be used to send a message with specific header
        joined = filter(lambda x: x.session!=None, self.clients)
        print joined
        map(lambda x: x.send_specific(header, msg), joined)

    def getSessInfo(self):
        # Returs a string of session name + player count
        return self.sessName+' ('\
               +str(self.maxClients - len(self.clients))+'/'\
               +str(self.maxClients) + ' spots available)'

    def addMe(self, c):
        # Adds a player to the session and removes them from server lobby
        # Notifies others about the added player and if the session gets
        # full, starts the game.
        with self.clientsLock:
            if len(self.clients) < self.maxClients:
                self.clients.append(c)
                c.session = self
                self.notify_update('\n'+c.nickname+' joined the lobby.')
                self.notify_update('Lobby status: %d/%d players joined.\n' \
                                    % (len(self.clients), self.maxClients))
                self.Server.removeFromLobby(c)
                if len(self.clients) == self.maxClients:
                    self.gameRunning = True
                    self.send_specific_update(
                        REP_TABLE,self.sudoku.sudoku_to_string())
                self.Server.notify_to_lobby_sessions()
                return True
            return False

    def removeMe(self):
        # Removes the player from the session. Notifies others
        # If the session becomes empty or only one player left
        # sends notification about winner and closes session
        caller = currentThread()
        caller.session = None
        if caller in self.clients:
            self.clients.remove(caller)
            self.notify_update(caller.nickname+' joined the game')
            logging.info('%s left game' % caller.getNickname())
        self.Server.notify_to_lobby_sessions()

        if (len(self.clients)<2 and self.gameRunning) or len(self.clients)==0:
            self.send_specific_update(REP_SCORES_GAME_OVER,\
				'Winner(s): %s' %self.findHighScore())
            self.Server.removeSession(self)
            self.Server.addToLobby(self.clients)
            self.clients = []
            logging.info('Session %s closing, not enough players.' %self.sessName)


    def getScoresNicknames(self):
        # Returns a string of players+scores
        msg = ", ".join(map(lambda x: x.getScoreNickname(), self.clients))
        return msg

    def findHighScore(self):
        score = -99999
        for c in self.clients:
            if c.score > score:
                best = c.nickname
                score = c.score
        winners = filter(lambda x: x.score == score, self.clients)
        return ','.join(map(lambda x: x.nickname, winners))+': ' + str(score) + ' points'

    def putNumber(self, x, y, number, client):
        # Takes prechecked x,y,number values (in range 1...9)
        # puts them into Sudoku. Prepares the response if the number was
        # correct/frong/cell full. Correspondingly updates scores
        # Also notifies the players if sudoku board changed        with self.tableLock:
        logging.info('%s wants to put %d at (x=%d y=%d)' % (client.nickname,number,x,y))

        put_table_result = self.sudoku.set_nr(x-1,y-1,number)

        msg = ''
        if put_table_result == NUMBER_EXISTS: # if position occupied
            msg = 'Cannot put %d at (x=%d, y=%d), space already filled.' % (number,x,y)

        else:
            if put_table_result == WRONG_ANSWER: # if wrong
                client.decScore()
                self.notify_update('\n%s incorrectly put %d at (x=%d, y=%d). -1 point :(' \
                                    % (client.nickname,number,x,y))

            elif put_table_result == RIGHT_ANSWER:  # if correct
                client.incScore()
                self.notify_update('\n%s correctly put %d at (x=%d, y=%d). +1 point!' \
                                    % (client.nickname,number,x,y))

            self.notify_update('Scoreboard: ' + self.getScoresNicknames() + '\n')
            self.notify_update(self.sudoku.sudoku_to_string())

            if self.sudoku.is_game_over(): # game over
                self.send_specific_update(REP_SCORES_GAME_OVER,
                    'Winner(s): %s' %self.findHighScore())
                self.Server.removeSession(self)
                self.Server.addToLobby(self.clients)
                self.clients = []

        return REP_PUT_NR, msg
