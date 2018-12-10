# #sudoku-multiplayer
A simple distributed multiplayer sudoku game in the terminal, implemented in Python using RPC.
- - - -
## Running the server
From the root directory, run `python2.7 server/serverMain.py`.

An optional `-a` flag followed by the server IP address can be specified. By default, the server listens to `127.0.0.1`.

## Starting up a client
From the root directory, run `python2.7 client/clientMain.py`.
- - - -
## Playing the game
### Setup
Clients guide players through the setup process of the game. Players go through the setup to:
1. Pick asked for a (unique) nickname.
2. Enter the IP address of the server they want to play on.
3. Choose an option based on the server:
    * _Create a new session_, specify the number of players in the game, and wait for others to join the session.
    * _Join an existing session_ by specifying the name of the session.

### Difficulty
When all the players in a given session connect, the game starts by displaying an identical sudoku grid to all players.  The number of unfilled spaces is predetermined statically in code via the `LEVEL` variable in `sudoku_new_py`.

### Mechanics
Players try to fill in the spaces on the grid by solving the sudoku. Players will gain a point for a correct guess, lost one for an incorrect guess, and be prompted to try again if they’ve tried to place a number in a filled spot.

### End game
There are several ways the server decides to end the game:
* The default and the natural way for the game to end is when **all the grid spaces are filled**.
* Since there is a minimum number of players required per session, the game ends when **less than two players are left** in the game due to, say, a disconnect.

When the game ends, all the players remaining are notified of the winner and are retuned to the lobby.
- - - -
## Brief descriptions of the files
### Client
#### `clientMain.py`
* Responsible for asking players for input during setup and gameplay.
* Communicates with the server.
#### `clientIO.py`
* Provices I/O capabilities for the player from the terminal.
* Facilitated by classes such as `SyncConsoleAppenderRawInputReader` and `AbstractSyncIO`.

### Server
#### `serverMain.py`
* Responsible for creating a listener socket.
* Keeps track of connected clients and game sessions.
* Creates `clientHandler` objects  to process client requests.
#### `clientHandler.py`
* Processes client requests, and sends notifications to clients.
#### `sessionClass.py`
* Allows `clientHander` objects to interact with sudoku instances.
* Keeps track of and notifies clients of changes to the game status.
#### `sudoku_new.py`
* Creates, validates, and makes changes to sudoku grids.
* Numbers are added spots via instances of the member class.
* Helps determine if a given grid arrangement ends the game.
