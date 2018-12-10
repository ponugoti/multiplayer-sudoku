# A clientHandler object is created for each client in serverMain
# who connects to the server's listener socket. The clientHandler
# will take action based on clients actions and also allows to notify
# the changes in game session.
import logging

FORMAT = '%(asctime)s (%(threadName)-2s) %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
LOG = logging.getLogger()

from sessionClass import *
import sessionClass as sc
from serverMain import *
from threading import Thread, Lock, currentThread

from socket import AF_INET, SOCK_STREAM, socket
from socket import error as soc_err

import os, sys, inspect

sys.path.insert(1, os.path.join(sys.path[0], '..'))
from messageProtocol import *


class clientHandler(Thread):
    def __init__(self, soc, Server):
        LOG.info('Created client %s:%d' % soc.getsockname())
        Thread.__init__(self)
        self.soc = soc  # tuple (IP, port)
        self.score = 0
        self.nickname = None
        self.session = None
        self.Server = Server
        self.send_lock = Lock()

    def getNickname(self):
        return self.nickname # returns string: client name

    def getScoreNickname(self):
        # Returns string of players name and score
        return self.nickname + ' ' + str(self.score)

    def incScore(self):
        self.score += 1 # increases client score

    def decScore(self):
        self.score -= 1 # decreases client score

    def requestPutNumber(self, unparsedInts):
        # Parses client input - expects three integers 1...9
        # If parsing succeeded, interacts with session's Sudoku
        LOG.debug('Client %s:%d wants to write to sudoku: %s' \
                  '' % (self.soc.getsockname() + (unparsedInts,)))
        try:
            if len(unparsedInts) != 3:
                return REP_NOT_OK, 'The input must contain 3 numbers\n' + \
                                   'For example, \'213\' puts \'3\' at (x=2, y=1).'
            ints = list(unparsedInts)
            x, y, number = int(ints[0]), int(ints[1]), int(ints[2])
            for n in [x,y,number]:
                if n not in range(1,10):
                    REP, MSG = REP_NOT_OK, "The number must be in [1..9]."
            REP, MSG = self.session.putNumber(x, y, number, self)
        except ValueError:
            REP, MSG = REP_NOT_OK, "Unexpected error: Parsing int failed!"
        return REP, MSG

    def rcvMessage(self):
        # Handles reading commands from TCP socket reads until
        # message terminating char. Handles socket errors and client
        # premature disconnection
        m, b = '', ''
        try:
            b = self.soc.recv(1)
            m += b
            while len(b) > 0 and not (b.endswith(MSG_TERMCHR)):
                b = self.soc.recv(1)
                m += b

            if len(b) <= 0:
                LOG.info('Client %s:%d disconnected' % \
                         self.soc.getsockname())
                self.soc.close()
                m = ''
            m = m[:-1]
        except KeyboardInterrupt:
            self.soc.close()
            LOG.info('Ctrl+C issued, disconnecting client %s:%d' \
                     % self.soc.getsockname())
            m = ''
        except soc_err as e:
            if e.errno == 107:
                LOG.warn('Client %s:%d left before server could handle it'
                         % self.soc.getsockname())
            else:
                LOG.error('Error: %s' % str(e))
            self.soc.close()
            LOG.info('Client %s:%d disconnected' % self.soc.getsockname())
            m = ''
        return m

    def joinSession(self, sessName):
        # Tries to join a session by invoking session method.
        # Dependent on outcome returns a string. Upon the string
        # rcvProtocolMessage will take action
        for sess in self.Server.sessionList:
            if sessName == sess.sessName:
                if sess.addMe(self):
                    self.session = sess
                    if self.session.gameRunning:
                        return "Start"
                    return 'Wait'
                return "session full"
        return "No such session"

    def createSession(self, sessName, maxPlayerCount):
        # Creates a session and tries to join it.
        # Dependent on outcome returns a string. Upon the string
        # rcvProtocolMessage will take action
        if sessName in self.Server.getSessNames():
            return REP_NOT_OK, "Session name in use"
        if maxPlayerCount < 2:
            return REP_NOT_OK, "Too few max players specified %d" % maxPlayerCount
        sess = sc.sessionClass(sessName, maxPlayerCount, self.Server)
        self.Server.sessionList.append(sess)
        self.session = sess
        if sess.addMe(self):
            self.session = sess
            return "OK", ""
        return REP_NOT_OK, "session full"

    def rcvProtocolMessage(self, message):
        # Takes action based on client actions. Checks if such actions
        # are available according to the client's state
        REP, MSG = 'OK', ''
        LOG.debug('Received request [%d bytes] in total' % len(message))
        # Check if the received message is faulty
        if len(message) < 2:
            LOG.debug('Not enough data received from %s ' % message)
            return REP_NOT_OK, 'received too short message'
        elif message.count(HEADER_SEP, 2) > 0 or message.count(FIELD_SEP) > 1:
            LOG.debug('Faulty message received from %s ' % message)
            return REP_NOT_OK, 'received too faulty message'
        payload = message[2:]
        # Client requests nickname - check if available and assemble reply
        if message.startswith(REQ_NICKNAME + HEADER_SEP):
            if payload not in self.Server.getUsedNicknames():
                self.nickname = payload
                LOG.debug('Client %s:%d will use name ' \
                          '%s' % (self.soc.getsockname() + (self.nickname,)))
                REP = REP_CURRENT_SESSIONS
                MSG = ''
                self.send_notification(self.Server.sessionList2string())
            else:
                REP, MSG = REP_NOT_OK, "Name in use"
        # Client wants to join a session - return if full/ok/game starts
        elif message.startswith(REQ_JOIN_EXIST_SESS + HEADER_SEP):
            if (self.name == None):
                LOG.debug('Name unknown at session join: %s ' % message)
                REP, MSG = REP_NOT_OK, "Specify name"
            elif (self.session != None):
                LOG.debug('Join session while in session: %s ' % message)
                REP, MSG = REP_NOT_OK, "Leave current session"
            else:
                msg = self.joinSession(payload)
            if msg == "Wait":
                LOG.debug('Client %s:%d joined session ' \
                          '%s' % (self.soc.getsockname() + (payload,)))
                REP, MSG = REP_WAITING_PLAYERS, ''
            elif msg == "Start":
                LOG.debug('Client %s:%d joined session ' \
                          '%s' % (self.soc.getsockname() + (payload,)))
                REP, MSG = None, ''
            else:
                LOG.debug('Client %s:%d failed to join session: ' \
                          '%s' % (self.soc.getsockname() + (msg,)))
                REP, MSG = REP_NOT_OK, msg
        # Client wants to create a new session - return if full/ok/game starts
        elif message.startswith(REQ_JOIN_NEW_SESS + HEADER_SEP):
            try:
                if self.name == None:
                    LOG.debug('Name unknown at session create: %s ' % message)
                    REP, MSG = REP_NOT_OK, "Specify name"
                elif self.session != None:
                    LOG.debug('Join session while in session: %s ' % message)
                    REP, MSG = REP_NOT_OK, "Leave current session"
                else:
                    sessname, playercount = payload.split(FIELD_SEP)
                    playercount = int(playercount)
                    REP, MSG = self.createSession(sessname, playercount)
                    if REP == "OK":
                        LOG.debug('Client %s:%d created session %s' \
                                  % (self.soc.getsockname() + (sessname,)))
                        REP, MSG = REP_WAITING_PLAYERS, ''
                    else:
                        LOG.debug('Client %s:%d failed to create and join session: ' \
                                  '%s' % (self.soc.getsockname() + (MSG,)))
            except:
                REP, MSG = REP_NOT_OK, "Unable to parse integer"
        # Client wants to interact with sudoku
        elif message.startswith(REQ_PUT_NR + HEADER_SEP):
            if self.session == None:
                LOG.debug('Not in session: %s ' % message)
                REP, MSG = REP_NOT_OK, "Not in session"
            else:
                REP, MSG = self.requestPutNumber(payload)

        else:
            LOG.debug('Unknown control message received: %s ' % message)
            REP, MSG = REP_NOT_OK, "Unknown control message"

        return REP, MSG


    def session_send(self, msg):
        # add message terminating char to the end and send it out\
        m = msg + MSG_TERMCHR
        LOG.info('Send to %s : %s' % (self.nickname, m))
        with self.send_lock:
            r = False
            try:
                self.soc.sendall(m)
                r = True
            except KeyboardInterrupt:
                self.soc.close()
                LOG.info('Ctrl+C issued, disconnecting client %s:%d' \
                         '' % self.soc.getsockname())
            except soc_err as e:
                if e.errno == 107:
                    LOG.warn('Client %s left before server could handle it' \
                             '' % self.soc.nickname)
                else:
                    LOG.error('Error: %s' % str(e))
                self.soc.close()
                LOG.info('Client %s:%d disconnected' % self.soc.getsockname())
            return r

    def send_notification(self, message):
        # sends nofify message
        return self.session_send(REP_NOTIFY + HEADER_SEP + message)

    def send_specific(self, header, message):
        # allows to send message with any header
        return self.session_send(header + HEADER_SEP + message)

    def run(self):
        # Main client loop
        while True:
            m = self.rcvMessage()
            LOG.debug('Raw msg: %s' % m)
            if len(m) <= 0:
                break
            rsp, msg = self.rcvProtocolMessage(m)
            if not rsp:
                continue
            if not self.send_specific(rsp, msg):
                break

        # Client handler closing - remove it from the server and session
        self.exists = False
        if self.session != None:
            self.session.removeMe()
        self.Server.removeMe()
