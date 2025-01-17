# installation guide

### virtualenv (optional)
```
python3 -m venv venv
source venv/bin/activate
```

### install dependencies
```
pip install -r requirements.txt
```

***

### install stockfish

MAC
```
brew install stockfish
```

Ubuntu Linux
```
sudo apt-get install stockfish

```

Fedora Linux 
```
sudo dnf install stockfish
```

launch the command to find the path where stockfish is installed
```
which stockfish 
```

***

### migrate database
launch with --migrate parameter only when you change the database model in db.py
```
python3 main.py --migrate
```

### create a config file
```
touch config
```

config file content:
```
TELEGRAM_TOKEN=<your bot's token>
STOCKFISH=/path/to/bin/stockfish
```

### run
```
python3 main.py
```

***

### how to play && available commands
once you have created your bot with BotFather, start the bot with `/start` command

```
/newgame_computer
```
creates a new game against stockfish

```
/newgame
```
creates a new game with a secret code to give to your opponent   

```
/newgame <secret code>
```
the opponent may accept the game with this command

```
/stopgame
```
stop the current game, and giveup!

```
/rmlobby
```
Once you have created a new game with a secret code using the /newgame command, and you are waiting for your opponent to accept the game, you may need to cancel this game and make the secret code no longer usable with this command.

***

### move examples
write in the message box the move you want to do

- Move the king from e1 to e2: Ke2
- Move the queen from d1 to f3: Qf3
- Move the rook from a1 to d1: Rd1
- Move the bishop from f1 to g2: Bg2
- Move the knight from b1 to c3: Nc3
- Move the pawn from e2 to e4: e4

***

![chess](https://github.com/fabiopallini/telegram-chess-bot/assets/8449266/ce931cb4-7428-4338-9c24-dabbe6003d5b)
