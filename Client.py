#!/usr/bin/env python

"""
An echo client that allows the user to send multiple lines to the server.
Entering a blank line will exit the client.
"""

import socket
import sys

BUF = 4096

def username(s):

	username = raw_input('Username: ')
	s.send(username)

def password(s):

	password = raw_input('Password: ')
	s.send(password)

def command(s):

	command = raw_input('Command: ')
	s.send(command)

def main(argv):

	host = argv[0]
	port = int(argv[1])

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((host,port))
	#sys.stdout.write('%')

	while 1:
		'''
	    # read from keyboard
	    line = sys.stdin.readline()
	    if line == '\n':
	        break
	    s.send(line)
	    '''

		data = s.recv(BUF)
		#print data
		if data == 'username':
			username(s)
		if data == 'password':
			password(s)
		if data == 'wronguser':
			print 'Invalid username'
		if data == 'alreadyin':
			print 'This user is already logged in.'
		if data == 'wrongpass':
			print 'Invalid password'
		if data == 'blocked':
			print 'This username is blocked for a while since the last attempt'
			s.close()
			break

		if data == 'welcome':
			print 'Welcome to the simple chat server!'
			command(s)

		'''
	    sys.stdout.write(data)
	    sys.stdout.write('%')
	    '''
	s.close()

if __name__ == '__main__':
	main(sys.argv[1:])


'''

import sys
from socket import *

BUF = 4096

def main(argv):

	servIP = argv[0]
	servPort = int(argv[1])
	clntSock = socket(AF_INET, SOCK_STREAM)
	clntSock.connect((servIP, servPort))

	sentence = raw_input('Input: ')

	clntSock.send(sentence)

	clntSock.close()

if __name__ == '__main__':
	main(sys.argv[1:])

import sys
from socket import *

BUF = 4096

def main(argv):

	ip = argv[0]
	port = int(argv[1])
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect((ip, port))

    try:
    	message = raw_input('Input: ')
        sock.sendall(message)
        response = sock.recv(1024)
        print "Received: {}".format(response)
    finally:
        sock.close()

if __name__ == '__main__':
	main(sys.argv[1:])
'''