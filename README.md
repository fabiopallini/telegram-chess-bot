## installation guide

create a config file
> touch config

config file content:
```
TELEGRAM_TOKEN=<your bot's token>
STOCKFISH=/path/to/stockfish/bin/stockfish
```

virtualenv (optional)
> python3 -m venv venv
> source venv/bin/activate

dependencies
> pip install -r requirements.txt

run
> python3 main.py


## install stockfish

### MAC ###
brew install stockfish

### Ubuntu Linux ###
apt-get install stockfish

## migrate database
launch with --migrate parameter only when you change the database model in db.py
> python3 main.py --migrate
