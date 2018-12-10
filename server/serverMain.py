# The main server file. Creates a listener socket,
# keeps tract of connected clients and game sessions
# creates clientHandler object for each client

import logging
FORMAT='%(asctime)s (%(threadName)-2s) %(message)s'
logging.basicConfig(level=logging.DEBUG,format=FORMAT)
LOG = logging.getLogger()

import os,sys,inspect
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from messageProtocol import *
from sessionClass import *
from clientHandler import *
from threading import Thread, Lock, currentThread

from socket import AF_INET, SOCK_STREAM, socket
from socket import error as soc_err

from argparse import ArgumentParser

class serverClass(object):
    def __init__(self):
        # stores clients not in game session
        self.lobbyList = []
        self.lobbyListLock = Lock()

        # stores all the clients connected
        self.clientListLock = Lock()
        self.clientList = []

        # stores list of sessions
        self.sessionListLock = Lock()
        self.sessionList = []

    def removeMe(self):
        # Remove the client from server (and from lobby)
        caller = currentThread()
        if caller.session != None:
            caller.session.removeMe()
        if caller in self.clientList:
            self.clientList.remove(caller)
            logging.info('%s left game' % caller.getNickname())
        if caller in self.lobbyList:
            self.lobbyList.remove(caller)
            logging.info('%s left lobby' % caller.getNickname())

    def removeFromLobby(self,c):
        # remove the client from lobby
        with self.lobbyListLock:
            if c in self.lobbyList:
                self.lobbyList.remove(c)

    def addToLobby(self,c_list):
        # adds the client to lobby. Sends a list of available
        # sessions on the server
        for c in c_list:
            c.session=None
            if c.nickname != None:
                c.send_notification(self.sessionList2string())
        with self.lobbyListLock:
            self.lobbyList += c_list

    def notify_to_lobby_sessions(self):
        # sends session list to players in the lobby
        for c in self.lobbyList:
            c.session=None
            if c.nickname != None:
                c.send_notification(self.sessionList2string())

    def getSessions(self):
        # return list of sessions on server
        with self.sessionListLock:
            return self.sessionList

    def getSessNames(self):
        # returns a list of session name strings
        lst = list()
        for s in self.sessionList:
            lst.append(s.sessName)
        return lst

    def getUsedNicknames(self):
        # returns a list of connected clients name strings
        return map(lambda x: x.nickname, self.clientList)

    def addSession(self,session):
        # adds a session to server's session list if session name
        # not in use. Returns True / False based on succeeding
        with self.sessionListLock:
            if session not in self.sessionList:
                self.sessionList.append(session)
                return True
            return False

    def sessionList2string(self):
        # returns a string of sessions on server + player count
        if len(self.getSessions())==0:
            return 'No sessions available. Create one!'
        return 'Available sessions: %s' %''.join(map(lambda x: '\n    ' +
                        x.getSessInfo(),self.getSessions()))

    def removeSession(self,sess):
        # remove a session from server
        with self.sessionListLock:
            if sess in self.sessionList:
                self.sessionList.remove(sess)

    def addClient(self,client):
        # adds a client to the server's client list
        with self.clientListLock:
            if client not in self.clientList:
                self.clientList.append(client)
                return True
            return False

    def listen(self,sock_addr):
        # Creates a listener socket
        self.sock_addr = sock_addr
        self.s = socket(AF_INET, SOCK_STREAM)
        self.s.bind(self.sock_addr)
        self.s.listen(1)
        LOG.debug( 'Socket %s:%d is in listening state'\
                       '' % self.s.getsockname() )
    def loop(self):
        # server's main loop. Creates clientHandler's for each connecter
        LOG.info( 'Falling to serving loop, press Ctrl+C to terminate ...' )
        clients = []

        try:
            while 1:
                client_socket = None
                LOG.info( 'Awaiting new clients ...' )
                client_socket,client_addr = self.s.accept()
                c = clientHandler(client_socket, self)
                self.clientList.append(c)
                self.addToLobby([c])
                c.start()
        except KeyboardInterrupt:
            LOG.warn( 'Ctrl+C issued closing server ...' )
        finally:
            if client_socket != None:
                client_socket.close()
            self.s.close()
        map(lambda x: x.join(), clients)

if __name__ == '__main__':
    parser = ArgumentParser(description="Tic tac toe game server")
    parser.add_argument('-a', '--server-addr',
                        help="Listening address. Default localhost.",
                        default='127.0.0.1')
    args = parser.parse_args()
    server = serverClass()
    server.listen((args.server_addr,7777))
    server.loop()
    LOG.info('Terminating ...')
