import select 
import socket 
import sys 
import threading
import hashlib

from datetime import datetime, timedelta
import pytz


BUF = 4096
BLOCK_TIME = 60

user_block_list = {}
users = {}
current_users = {}

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

            '''
            data = self.client.recv(self.size)
            if data:
                data = data.upper()
                self.client.send(data) 
            else: 
                self.client.close() 
                running = 0
                print 'one client terminated'
            '''
        
        self.client.close()
        print 'one client terminated'

    def login(self):

        success = False
        count = 1
        # If there are three consecutive failures with a valid user name, the server blocks the user
        # of the IP address. But wrong usernames don't count as a failure, because this
        # doesn't cause denial-of-service attacks.
        while count < 4:
            self.client.send('username')
            username = self.client.recv(self.size)

            # Check if this user from this ip address has been blocked or not.
            check = username + ' ' + self.address[0]
            if check in user_block_list:
                dt = datetime.now(pytz.timezone('US/Eastern'))
                present = dt.replace(tzinfo=None)
                # If it hasn't been 60 seconds since this user got blocked,
                # let the user know it and break the while loop (return False).
                if present - user_block_list[check] < timedelta(seconds=BLOCK_TIME):
                    self.client.send('blocked')
                    break

            self.client.send('password')
            password = self.client.recv(self.size)
            password = hashlib.sha1(password.encode()).hexdigest()

            # If wrong username, let the user know it and continue the while loop.
            if username not in users:
                self.client.send('wronguser')
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
                    self.client.send('alreadyin')
                    count = 1
                    continue
                # Else, the login is succeeded.
                else:
                    success = True

            # If the login is succeeded, add the user to the list of the current users,
            # and break the while loop.
            if success:
                current_users[username] = True
                print username + ' logged in'
                self.client.send('welcome')
                break
            # Else, let the user know that the password is wrong,
            # and increment the count variable by 1.
            else:
                self.client.send('wrongpass')
                count = count + 1

        # If there are three failures with a valid user name,
        # add this user to the block list and save the present time.
        # Then, let the user know it.
        if count == 4:
            self.client.send('blocked')
            dt = datetime.now(pytz.timezone('US/Eastern'))
            present = dt.replace(tzinfo=None)
            user_block_list[check] = present

        return success


if __name__ == "__main__": 
    s = Server(sys.argv[1]) 
    s.run()