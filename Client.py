import sys
import socket
import signal
import thread

BUF = 4096
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
flag = 1 # For synchronization 

# Signal handler for SIGINT(Ctrl+C).
def signal_handler(signal, frame):
    print('Exit the program.')
    s.close()
    sys.exit(0)

# Username prompt
def username():
	while True:
		username = raw_input('Username: ')
		if username != '':
			break
	s.send(username)

# Password prompt
def password():
	while True:
		password = raw_input('Password: ')
		if password != '':
			break	
	s.send(password)

# Command prompt
def command():
	global flag
	while flag:
		command = raw_input('Command: ')
		if command != '':
			s.send(command)
			# Log out the program.
			if command == 'logout':
				print 'Terminate this client program.'
				sys.exit(0)

			flag = 0 # Wait the response.
			break

def who(msg):
	index = msg.find(' ') # 'who' + ' ' + result
	msg = msg[index+1:]
	print 'Current connected users:'
	print msg

def last(msg):
	index = msg.find(' ') # 'last' + ' ' + result
	msg = msg[index+1:]
	print 'Users recently connected:'
	print msg

def show_login_info(msg):
	index = msg.find(' ') # 'loginInfo' + ' ' + info
	msg = msg[index+1:]
	print '\n---------------------------------'
	print msg
	print '---------------------------------'
	print 'Command:'

def show_stored_messages(msg):
	index = msg.find(' ') # 'stored' + ' ' + messages
	msg = msg[index+1:]
	print '\nYou have messages!'
	print '---------------------------------'
	print msg
	print '---------------------------------'
	print 'Command:'

def receive_message():
	global flag

	# Keep receiving messages.
	while True:
		try:
			# Receive data from the socket.
			data = s.recv(BUF)
		except:
			print 'recv() failed. Press enter to exit the program.'
			break
		else:
			if len(data) == 0:
				print 'recv() failed. Press enter to exit the program.'
				break

			# Manage the recieved data.
			if data.find('who') == 0:
				who(data)
			elif data.find('last') == 0:
				last(data)
			elif data.find('Sent') == 0:
				print data
			elif data == 'invalidCommand':
				print 'Invalid command.\n'
			elif data == 'noSuchUser':
				print 'No such user found.\n'
			elif data.find('No user found called') == 0:
				print data
			elif data.find('stored') == 0:
				show_stored_messages(data)
			elif data.find('loginInfo') == 0:
				show_login_info(data)
			else:
				print '\nYou\'ve got a message!'
				print '---------------------------------'
				print data
				print '---------------------------------'
				print 'Command:'
			flag = 1 # Show the command prompt.

	thread.interrupt_main()

# Examinme if the given host name is an IP address or not.
def validate_ip(host):
	l = host.split('.')
	if len(l) != 4:
		return False
	for n in l:
		if not n.isdigit():
			return False
		i = int(n)
		if i < 0 or i > 255:
			return False
	return True

def main(argv):
	# Set signal handler.
	signal.signal(signal.SIGINT, signal_handler)

	# Get the host and port number.
	if validate_ip(argv[0]):
		host = argv[0]
	else:
		host = socket.gethostbyname(argv[0])
	port = int(argv[1])

	# Connect the socket to the server.
	try:
		s.connect((host,port))
	except:
		print 'connect() failed.'
		sys.exit(0)

	login = False
	while not login:
		try:
			# Receive data from the socket.
			data = s.recv(BUF)
		except:
			print 'recv() failed'
			break
		if len(data) == 0:
			print 'recv() failed'
			break
		
		# Manage the process before login.
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

	# After login, start the receiver thread.
	if login:
		thread.start_new_thread(receive_message, ())
		# Keep calling command prompt.
		while True:
			command()

	# Close the socket.
	s.close()

if __name__ == '__main__':
	main(sys.argv[1:])
