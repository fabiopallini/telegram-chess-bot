### installation guide

## virtualenv (optional)
```
python3 -m venv venv
source venv/bin/activate
```

## install dependencies
```
pip install -r requirements.txt
```

### install stockfish

## MAC ###
```
brew install stockfish
```

## Ubuntu Linux
```
sudo apt-get install stockfish

```

## Fedora Linux 
```
sudo dnf install stockfish
```

launch the command 
```
which stockfish 
```
to find the path where stockfish is installed

### migrate database
launch with --migrate parameter only when you change the database model in db.py
```
python3 main.py --migrate
```

### create a config file
```
touch config
```

### config file content:
```
TELEGRAM_TOKEN=<your bot's token>
STOCKFISH=/path/to/bin/stockfish
```

### run
```
python3 main.py
```

### how to play
once you have created your bot with BotFather, start the bot with `/start` command
 
### available commands

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
