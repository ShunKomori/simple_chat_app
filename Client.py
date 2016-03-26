import sys
import socket
import signal
import thread

BUF = 4096
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
flag = 1

def signal_handler(signal, frame):
    print('Exit the program.')
    s.close()
    sys.exit(0)

def username():
	while True:
		username = raw_input('Username: ')
		if username != '':
			break
	s.send(username)

def password():
	while True:
		password = raw_input('Password: ')
		if password != '':
			break	
	s.send(password)

def command():
	global flag
	while flag:
		command = raw_input('Command: ')
		if command != '':
			s.send(command)
			if command == 'logout':
				print 'Terminate this client program.'
				sys.exit(0)

			flag = 0
			break

def who(msg):
	index = msg.find(' ')
	msg = msg[index+1:]
	print 'Current connected users:'
	print msg

def last(msg):
	index = msg.find(' ')
	msg = msg[index+1:]
	print 'Users recently connected:'
	print msg

def receive_message():
	#s.setblocking(0)

	global flag
	while True:
		try:
			data = s.recv(BUF)
		except:
			print 'recv() failed. Press enter to exit the program.'
			break
		else:
			if len(data) == 0:
				print 'recv() failed. Press enter to exit the program.'
				break

			if data.find('who') == 0:
				who(data)
			elif data.find('last') == 0:
				last(data)
			elif data == 'broadcastDone':
				print 'Sent a message to everyone!\n'
			elif data == 'invalidCommand':
				print 'Invalid command.\n'

			else:
				print '\nYou\'ve got a message!'
				print '---------------------------------'
				print data
				print '---------------------------------'
				print 'Command:'
			flag = 1

	thread.interrupt_main()

def main(argv):
	signal.signal(signal.SIGINT, signal_handler)

	host = argv[0]
	port = int(argv[1])

	s.connect((host,port))

	login = False
	while not login:

		try:
			data = s.recv(BUF)
		except:
			print 'recv() failed'
			break
		if len(data) == 0:
			print 'recv() failed'
			break
		
		if data == 'username':
			username()
		elif data == 'password':
			password()
		elif data == 'wronguser':
			print 'Invalid username.\n'
		elif data == 'alreadyin':
			print 'This user is already logged in.\n'
		elif data == 'wrongpass':
			print 'Invalid password.\n'
		elif data == 'blocked':
			print 'This username is blocked for a while since the last attempt.\n'
			break
		elif data == 'welcome':
			print '\nWelcome to the simple chat server!\n'
			login = True

	if login:
		thread.start_new_thread(receive_message, ())
		while True:
			command()

	s.close()

if __name__ == '__main__':
	main(sys.argv[1:])
