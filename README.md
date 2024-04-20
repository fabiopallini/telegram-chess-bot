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
