import select 
import socket 
import sys 
import threading
import hashlib
import signal
from datetime import datetime, timedelta
import pytz

BUF = 4096
BLOCK_TIME = 60
TIME_OUT = 60*30

user_block_list = {}
users = {}
current_users = {}
logout_history = {}
client_socks = {}
messages = {}

# Signal handler for SIGINT(Ctrl+C).
def signal_handler(signal, frame):
    print('Exit the program.')
    sys.exit(0)

# Main Server.
class Server: 
    def __init__(self, port): 
        self.host = '' 
        self.port = int(port) 
        self.size = BUF 
        self.server = None 
        self.threads = [] 

    # Open server socket.
    def open_socket(self): 
        try: 
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
            self.server.bind((self.host,self.port)) 
            self.server.listen(5) 
        except socket.error, (value, message): 
            if self.server: 
                self.server.close() 
            print "Could not open socket: " + message 
            sys.exit(1) 

    def run(self):
        # Set signal handler.
        signal.signal(signal.SIGINT, signal_handler)

        # Read 'user_pass.txt' and store its data in user_pass_list([username, password, username, password, ...]).
        fo = open('user_pass.txt', 'r')
        info = fo.read()
        user_pass_list = info.split()

        # Extract usernames from user_pass_list and store them in users.
        for i in range (len(user_pass_list)):
            if i % 2 == 0:
                users[user_pass_list[i]] = True

        # Open socket
        self.open_socket() 
        input = [self.server] 
        while True:
            # Keep accepting connection from a client and create a server thread for that user.
            c = Client(self.server.accept(), user_pass_list)
            c.setDaemon(True)
            c.start()
            self.threads.append(c)
            print 'one thread created.'

        # Close all threads.
        self.server.close()
        for c in self.threads: 
            c.join()

        print 'server terminated'

# Server thread for each client.
class Client(threading.Thread): 
    def __init__(self,(client,address),user_pass_list): 
        threading.Thread.__init__(self)
        self.client = client
        self.address = address 
        self.size = BUF
        self.user_pass_list = user_pass_list
        self.user = ''
        self.client.settimeout(TIME_OUT) # Set timeout.
        self.timeout_flag = 0
    
    def run(self):       
        running = 1
        while running:
            # If this is the first loop, execute login process.
            if running == 1:
                login_success = self.login()
                # If login is succeeded, keep running.
                if login_success:
                    running = running + 1
                # Else, get out of the loop (and terminate the thread).
                else:
                    break

            # If this is not the first loop, take commands from the client.
            else:
                command = self.receive()
                # If a client is inactive for a while, get out of the loop (and terminate the thread).
                if self.timeout_flag:
                    break
                if len(command) == 0:
                    print 'receive() from ' + self.user + ' failed.'
                    break

                # Manage commands from the client
                print 'command from ' + self.user + ': ' + command
                if command == 'who':
                    self.who()
                elif command.find('last') == 0:
                    self.last(command)
                elif command == 'logout':
                    break
                elif command.find('broadcast') == 0:
                    self.broadcast(command)
                elif command.find('send (') == 0:
                    self.multi_send(command)
                elif command.find('send') == 0:
                    self.single_send(command)
                else:
                    self.send('invalidCommand', self.client)
        
        # Close the client socket and terminate.
        self.logout()
        if self.user != '':
            print self.user + ' terminated.'
        else:
            print 'one client terminated.'

    # Send a message from the designated socket.
    def send(self, message, socket):
        try:
            socket.send(message)
        except:
            # If its own socket is failed, log out itself.
            if socket == self.client:
                self.logout()
            # Else, close the failed socket.
            else:
                socket.close()

    # Receive a message from the designated socket.
    def receive(self):
        try:
            msg = self.client.recv(self.size)
        # In case of timeout, log out itself and set the timeout flag 1.
        except socket.timeout:
            self.logout()
            self.timeout_flag = 1
        except:
            self.logout()     
        else:
            return msg

    def login(self):
        success = False
        count = 1
        # If there are three consecutive failures with a valid user name, the server blocks the user
        # of the IP address. But wrong usernames don't count as a failure, because this
        # doesn't cause denial-of-service attacks.
        while count < 4:
            self.send('username', self.client)
            username = self.receive()
            if len(username) == 0:
                print 'receive() from ' + self.user + ' failed.'
                break

            # Check if this user from this ip address has been blocked or not.
            check = username + ' ' + self.address[0]
            if check in user_block_list:
                dt = datetime.now(pytz.timezone('US/Eastern'))
                present = dt.replace(tzinfo=None)
                # If it hasn't been 60 seconds since this user got blocked,
                # let the user know it and break the while loop (return False).
                if present - user_block_list[check] < timedelta(seconds=BLOCK_TIME):
                    self.send('blocked', self.client)
                    break

            self.send('password', self.client)
            password = self.receive()
            if len(password) == 0:
                print 'receive() from ' + self.user + ' failed.'
                break
            password = hashlib.sha1(password.encode()).hexdigest()

            # If wrong username, let the user know it and continue the while loop.
            if username not in users:
                self.send('wronguser', self.client)
                count = 1
                continue

            found = False
            # Check if the username and the password are valid or not.
            for i in range (len(self.user_pass_list)):
                if (self.user_pass_list[i] == username) and (self.user_pass_list[i+1] == password):
                    found = True
                    break

            if found:
                # If this username is already logged in, let the user know it.
                # This doesn't count as a failure. Continue the while loop.
                if username in current_users:
                    self.send('alreadyin', self.client)
                    count = 1
                    continue
                # Else, the login is succeeded.
                else:
                    success = True

            # If the login is succeeded, add the user to the list of the current users,
            # and break the while loop.
            if success:
                self.user = username
                current_users[username] = True
                client_socks[username] = self.client
                print username + ' logged in'

                self.send('welcome', self.client)

                # EXTRA FEATURE 1: Notify the users currently logged in that
                # this user has logged in.
                message = 'loginInfo ' + username + ' logged in.'
                for user in current_users:
                    if user != self.user:
                        self.send(message, client_socks[user])

                # EXTRA FEATURE 2: Send the stored messages to the user
                if username in messages:
                    stored_msgs = 'stored ' + messages[username]
                    self.send(stored_msgs, self.client)
                    # Remove the stored message.
                    messages.pop(username, None)

                break

            # Else, let the user know that the password is wrong,
            # and increment the count variable by 1.
            else:
                self.send('wrongpass', self.client)
                count = count + 1

        # If there are three failures with a valid user name,
        # add this user to the block list and save the present time.
        # Then, let the user know it.
        if count == 4:
            print username + ' blocked.'
            self.send('blocked', self.client)
            dt = datetime.now(pytz.timezone('US/Eastern'))
            present = dt.replace(tzinfo=None)
            user_block_list[check] = present

        return success

    def who(self):
        # Get the users currently logged in.
        users = current_users.keys()

        # Convert the list into a string
        response = 'who '
        for user in users:
            response = response + str(user) + ' '
        response = response[:-1]
        response = response + '\n'

        self.send(response, self.client)

    def last(self, command):
        # command -> [command, minutes]
        last_and_minutes = command.split()

        # If the length of the list is not 2, it's invalid.
        if len(last_and_minutes) != 2:
            self.send('invalidCommand', self.client)
        else:
            mins = int(last_and_minutes[1])

            # Get the present time.
            dt = datetime.now(pytz.timezone('US/Eastern'))
            present = dt.replace(tzinfo=None)

            # Create a response.
            response = 'last '
            # Get all the users currently logged in.
            for user in current_users:
                response = response + str(user) + ' '
            # Get the users who logged out within 'mins' ago.
            for user in logout_history.keys():
                # The users currently logged in are already in the response.
                if user not in current_users:
                     if present - logout_history[user] < timedelta(minutes=mins):
                        response = response + str(user) + ' '
            response = response[:-1]
            response = response + '\n'

            self.send(response, self.client)

    def broadcast(self, command):
        broadcast_and_message = command.split()
        # If command is composed of only 'command', it's invalid.
        if len(broadcast_and_message) < 2:
            self.send('invalidCommand', self.client)
        else:
            # command = command('broadcast') + ' ' + 'message'
            message = command[command.find(' ') + 1:]
            message = '<from ' + self.user + '>\n' + message + '\n'

            # Send a message to everyone.
            for user in users:
                # If the receiver is currently logged in, send it to them.
                if user in current_users:
                    if user != self.user:
                        self.send(message, client_socks[user])
                '''
                # EXTRA FEATURE 2: If not, store the message in 'messages'.
                else:
                    if user in messages:
                        messages[user] = messages[user] + message
                    else:
                        messages[user] = message
                '''
            self.send('Sent a message to everyone!\n', self.client)

    def multi_send(self, command):
        # command = command('send') + ' ' + '(receivers)' + ' ' + 'message'
        receivers_string = command[command.find('(')+1:command.find(')')]

        # Invalid send command.
        if command.rfind(')') < 0:
            self.send('invalidCommand', self.client)

        else:
            message = command[command.rfind(')')+2:]
            # Invalid send command.
            if message == '' or message == None or len(message) == 0:
                self.send('invalidCommand', self.client)
            else:
                message = '<from ' + self.user + '>\n' + message + '\n'

                # receivers_string = 'receiver' + ' ' + 'receiver' + ' ' + ...
                receivers = receivers_string.split()

                sent = False
                response = '' # Response to the client.
                # Send a message to the receivers.
                for user in receivers:
                        # If the receiver is currently logged in, send it to them.
                        if user in current_users:
                            if user != self.user: # The client itself doesn't receive a message.
                                self.send(message, client_socks[user])
                                sent = True
                        # EXTRA FEATURE 2: If not, store the message in 'messages'.
                        else:
                            if user in messages:
                                messages[user] = messages[user] + message
                                sent = True
                            # If no such user, let the client know it.
                            elif user not in users:
                                response = response + 'No user found called ' + user + '.\n'
                            else:
                                messages[user] = message
                                sent = True
                if sent:
                    response = response + 'Sent a message to the listed users!\n'
                self.send(response, self.client)

    def single_send(self, command):
        # Invalid command.
        if command.find(' ') < 0:
            self.send('invalidCommand', self.client)
        elif command.find(' ', command.find(' ')+1) < 0 :
            self.send('invalidCommand', self.client)
        else:
            # command = command('send') + ' ' + 'receiver' + ' ' + 'message'
            receiver = command[command.find(' ')+1:command.find(' ', command.find(' ')+1)]
            message = command[command.find(' ', command.find(' ')+1)+1:]
            # Invalid command.
            if message == '' or message == None or len(message) == 0:
                self.send('invalidCommand', self.client)
            elif receiver == self.user:
                self.send('invalidCommand', self.client) # You can't send a private message to yourself.
            elif receiver not in users:
                self.send('noSuchUser', self.client)
            else:
                message = '<from ' + self.user + '>\n' + message + '\n'

                # Invalid send command.
                if receiver == self.user:
                    self.send('invalidCommand', self.client)

                else:
                    # If the receiver is currently logged in, send it to them.
                    if receiver in current_users:
                        self.send(message, client_socks[receiver])
                    # EXTRA FEATURE 2: If not, store the message in 'messages'.
                    else:
                        if receiver in messages:
                            messages[receiver] = messages[receiver] + message
                        else:
                            messages[receiver] = message
                    self.send('Sent a private message to the user!\n', self.client)

    def logout(self):
        # If username is known, record the logout time.
        if self.user != '':
                dt = datetime.now(pytz.timezone('US/Eastern'))
                present = dt.replace(tzinfo=None)
                current_users.pop(self.user, None)
                logout_history[self.user] = present
        # Close the client socket.
        self.client.close()

if __name__ == "__main__": 
    s = Server(sys.argv[1]) 
    s.run()