import select 
import socket 
import sys 
import threading
import hashlib

from datetime import datetime, timedelta
import pytz

import signal

BUF = 4096
BLOCK_TIME = 60

user_block_list = {}
users = {}
current_users = {}
logout_history = {}
client_socks = {}

def signal_handler(signal, frame):
    print('Exit the program.')
    sys.exit(0)

class Server: 
    def __init__(self, port): 
        self.host = '' 
        self.port = int(port) 
        #self.backlog = 5 
        self.size = BUF 
        self.server = None 
        self.threads = [] 

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

        signal.signal(signal.SIGINT, signal_handler)

        fo = open('user_pass.txt', 'r')
        info = fo.read()
        user_pass_list = info.split()

        for i in range (len(user_pass_list)):
            if i % 2 == 0:
                users[user_pass_list[i]] = True

        self.open_socket() 
        input = [self.server,sys.stdin] 
        running = 1 
        while running:
            inputready,outputready,exceptready = select.select(input,[],[]) 

            for s in inputready: 

                if s == self.server: 
                    # handle the server socket 
                    c = Client(self.server.accept(), user_pass_list)
                    c.setDaemon(True)
                    c.start()
                    self.threads.append(c)
                    print 'one thread created'

                elif s == sys.stdin: 
                    # handle standard input 
                    junk = sys.stdin.readline() 
                    running = 0 

        # close all threads 

        self.server.close() 
        for c in self.threads: 
            c.join()

        print 'server terminated'

class Client(threading.Thread): 
    def __init__(self,(client,address),user_pass_list): 
        threading.Thread.__init__(self) 
        self.client = client 
        self.address = address 
        self.size = BUF
        self.user_pass_list = user_pass_list
        self.user = ''

    def run(self):
        running = 1
        while running:
            if running == 1:
                login_success = self.login()
                if login_success:
                    running = running + 1
                    continue
                else:
                    running = 0

            else:
                try:
                    command = self.client.recv(self.size)
                except:
                    current_users.pop(self.user, None)
                    dt = datetime.now(pytz.timezone('US/Eastern'))
                    present = dt.replace(tzinfo=None)
                    logout_history[self.user] = present
                    running = 0

                if command == 'who':
                    self.who()
                elif command.find('last') == 0:
                    self.last(command)
                elif command == 'logout':
                    self.logout()
                    running = 0
                elif command.find('broadcast') == 0:
                    self.broadcast(command)
                else:
                    self.send('invalidCommand')
        
        self.client.close()
        print 'one client terminated'

    def send(self, message):
        try:
            self.client.send(message)
        except:
            dt = datetime.now(pytz.timezone('US/Eastern'))
            present = dt.replace(tzinfo=None)
            current_users.pop(self.user, None)
            logout_history[self.user] = present
            self.client.close()
            print 'one client terminated'
            

    def login(self):
        success = False
        count = 1
        # If there are three consecutive failures with a valid user name, the server blocks the user
        # of the IP address. But wrong usernames don't count as a failure, because this
        # doesn't cause denial-of-service attacks.
        while count < 4:
            self.send('username')
            username = self.client.recv(self.size)

            # Check if this user from this ip address has been blocked or not.
            check = username + ' ' + self.address[0]
            if check in user_block_list:
                dt = datetime.now(pytz.timezone('US/Eastern'))
                present = dt.replace(tzinfo=None)
                # If it hasn't been 60 seconds since this user got blocked,
                # let the user know it and break the while loop (return False).
                if present - user_block_list[check] < timedelta(seconds=BLOCK_TIME):
                    self.send('blocked')
                    break

            self.send('password')
            password = self.client.recv(self.size)
            password = hashlib.sha1(password.encode()).hexdigest()

            # If wrong username, let the user know it and continue the while loop.
            if username not in users:
                self.send('wronguser')
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
                    self.send('alreadyin')
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
                self.send('welcome')
                break
            # Else, let the user know that the password is wrong,
            # and increment the count variable by 1.
            else:
                self.send('wrongpass')
                count = count + 1

        # If there are three failures with a valid user name,
        # add this user to the block list and save the present time.
        # Then, let the user know it.
        if count == 4:
            self.send('blocked')
            dt = datetime.now(pytz.timezone('US/Eastern'))
            present = dt.replace(tzinfo=None)
            user_block_list[check] = present

        return success

    def who(self):
        users = current_users.keys()

        response = ''
        for user in users:
            response = response + str(user) + ' '
        response = response[:-1]

        self.send('who')
        self.send(response)

    def last(self, command):
        last_and_minutes = command.split()

        if len(last_and_minutes) != 2:
            self.send('invalidCommand')
        else:
            mins = int(last_and_minutes[1])

            dt = datetime.now(pytz.timezone('US/Eastern'))
            present = dt.replace(tzinfo=None)

            response = ''
            for user in current_users:
                response = response + str(user) + ' '
            for user in logout_history.keys():
                if user not in current_users:
                     if present - logout_history[user] < timedelta(minutes=mins):
                        response = response + str(user) + ' '
            response = response[:-1]

            self.send('last')
            self.send(response)

    def broadcast(self, command):
        broadcast_and_message = command.split()

        if len(broadcast_and_message) != 2:
            self.send('invalidCommand')
        else:
            message = broadcast_and_message[1]
            message = '-- From ' + self.user + ' --\n' + message
            for user in current_users:
                if user != self.user:
                    client_socks[user].send(message)
            self.send('broadcastDone')

    def logout(self):
        current_users.pop(self.user, None)
        dt = datetime.now(pytz.timezone('US/Eastern'))
        present = dt.replace(tzinfo=None)
        logout_history[self.user] = present
        self.send('logout')

        #print current_users
        #print logout_history

if __name__ == "__main__": 
    s = Server(sys.argv[1]) 
    s.run()