CSEE4119 Homework 3
Name: Shunsuke Komori
UNI: sk3961

<Description of the Code>
Server.py is a program for the server of this chat application.
Its main thread keeps accepting new connections from clients and
create a new thread for each client to respond their request.
Client.py is a program for the client of this chat application.
Its main thread manages the login process, and after login, it creates a new
thread for accepting data from the server so that the new message can
pop up in cosole immediately after it arrives. The main thread keeps
sending commands to the server, and the new thread keeps accepting data from
the server.
All the funcitons of this code work exactly as specified in the instruction.
I set 'invalid command' notification for wrong syntax of commands.
If the client tries to 'send' a message to a username that is not in the valid
users list, the server will notifiy the client that there's no such user
in its users.

<Development Environment>
Python 2.7.10
Sublime Text 2

<Instructions on How to Run the Code>
python Server.py <port number>
python Client.py <server> <port number>

<Sample Commands>
python Server.py 4444
python Client.py 127.0.0.1 4444
python Client.py localhost 4444

<Additional Features>
1. Login information
As soon as one user logs in, this login information pops up in
cosole of the other users logged in at the time. You can test this
function by checking if one user's terminal shows 'username logged in' message
when the other user logs in.

2. Offline messaging
If the receiving user of a private message is offline, the server stores the message
and deliver it to the receiver when the user logs in. I didn't implement this function
for broadcast in consideration of its characteristics. You can test this function by
sending a 'send' message to an offline user and checking if that message shows up
when you log in as that offline user.
