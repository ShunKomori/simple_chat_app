import socket
import sys
import signal
import fcntl, os
import errno
import select

BUF = 4096
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def signal_handler(signal, frame):
    print('Exit the program.')
    s.close()
    sys.exit(0)

def username(s):
	while True:
		username = raw_input('Username: ')
		if username != '':
			break
	s.send(username)

def password(s):
	while True:
		password = raw_input('Password: ')
		if password != '':
			break	
	s.send(password)

def command(s):
	while True:
		command = raw_input('\nCommand: ')
		receive_message(s)
		if command != '':
			s.send(command)
			break

def who(s):
	users = s.recv(BUF)
	print 'Current connected users:'
	print users

def last(s):
	users = s.recv(BUF)
	print 'Users recently connected:'
	print users

def receive_message(s):
	s.setblocking(0)
	try:
		msg = s.recv(BUF)
	except:
		pass
	else:
		if len(msg) == 0:
			print 'recv() failed.'
			sys.exit(0)
		print 'You\'ve got a message!'
		print '---------------------------------'
		print msg
		print '---------------------------------'
	s.setblocking(1)

def main(argv):
	signal.signal(signal.SIGINT, signal_handler)

	host = argv[0]
	port = int(argv[1])

	s.connect((host,port))

	login = False
	while True:

		if login:
			command(s)

		data = s.recv(BUF)
		if data == 'username':
			username(s)
		elif data == 'password':
			password(s)
		elif data == 'wronguser':
			print '\nInvalid username.'
		elif data == 'alreadyin':
			print '\nThis user is already logged in.'
		elif data == 'wrongpass':
			print '\nInvalid password.'
		elif data == 'blocked':
			print '\nThis username is blocked for a while since the last attempt.'
			s.close()
			break

		elif data == 'welcome':
			print '\nWelcome to the simple chat server!'
			login = True
		elif data == 'who':
			who(s)
		elif data == 'last':
			last(s)
		elif data == 'broadcastDone':
			print 'Sent message to everyone!'
		#elif data == 'broadcast':
		#	broadcast(s)
		elif data == 'logout':
			print '\nSuccessfully logged out.'
			break
		elif data == 'invalidCommand':
			print 'Invalid command.'
		#else:
		#	print 'Error.'
		#	break

	s.close()

if __name__ == '__main__':
	main(sys.argv[1:])
