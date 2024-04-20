import os
import sys
import time
import requests
import json
import chess, chess.svg, chess.pgn, chess.engine
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF, renderPM
#import cairosvg
import random
from db import *

TOKEN = None 
BOT_URL = None
STOCKFISH = None
offset = 0
session = None
DEBUG_PGN = None
TIMEOUT = 3 

def main():
	global session

	if read_config() == False:
		return

	if os.path.exists("data.db") == False or (len(sys.argv) > 1 and sys.argv[1] == "--migrate"):
		db_create_database()

	session = db_init_session()

	while True:
		updates = get_updates()['result']
		for i in range(len(updates)):
			if 'message' in updates[i]:
				message = updates[i]['message']
				user_id = message['from']['id']
				message_id = message['message_id']
				text = message['text']
				date = message['date']
				q = select(Message).where(Message.message_id == message_id)
				result = session.execute(q).first()
				# se nel DB non è presente un messaggio con id uguale a message_id, non ho ancora risposto a questo messaggio
				if result == None:

					if text.startswith("/"):

						# on bot first launch
						if text == "/start":
							base_url = f'https://api.telegram.org/bot{TOKEN}/setMyCommands'
							params = {
								'commands': json.dumps(get_menu_buttons())
							}
							while True:
								try:
									response = requests.get(base_url, params=params, timeout=TIMEOUT)
									break
								except Exception as e:
									print(e)
									time.sleep(3)
							send_message(user_id, "bot started")

						if text == "/newgame_computer":
							lobby = db_get_player_lobby(session, user_id)
							if lobby == None:
								game_add(session, user_id, 0)
							else:
								send_message(user_id, f"you can't create a game now, you are in a lobby ({lobby.name}), waiting to play with an opponent, to play a game right now with the computer you need to quit from the lobby ( /rmlobby )")

						if text == "/newgame":
							result = db_add_lobby(session, user_id)
							send_message(user_id, result)

						if text.startswith("/playgame"):
							params = read_command_params(text)
							if len(params) >= 1:
								result = db_play_game(session, user_id, params[0])
								if "p1" in result:
									game_add(session, result['p1'], result['p2'])
								else:
									send_message(user_id, result)
							else:
								send_message(user_id, "missing game name: /playgame gamename")

						if text.startswith("/rmlobby"):
							lobby = db_get_player_lobby(session, user_id)
							if lobby:
								name = lobby.name
								db_delete_lobby(session, lobby.id)
								send_message(user_id, f'removed from {name} lobby')
							else:
								send_message(user_id, 'no lobby to remove')

						if text == "/stopgame":
							game = db_get_player_game(session, user_id)
							if game:
								board = load_game_pgn(game.id)
								game_stop(session, user_id, game, board)
							else:
								send_message(user_id, "you are not playing any game")
                    
					else:
						game = db_get_player_game(session, user_id)
						# controllo se l'utente che ha inviato il messaggio sta partecipando a un game
						if game is not None:
							board = load_game_pgn(game.id)
							if (user_id == game.player_1 and board.turn == chess.WHITE) or (user_id == game.player_2 and board.turn == chess.BLACK):
								if validate_str_move(text):
									move_result = chess_move(board, game, user_id, text)								
									status = check_game_status(board)
									if status != "ok": # partita terminata
										send_message(game.player_1, status)
										if game.player_2 != 0:
											send_message(game.player_2, status)
										game_stop(session, user_id, game, board)
											
									# se la mossa è valida e user_id sta giocando con il computer (player_2 id == 0)
									if move_result == True and status == "ok" and game.player_2 == 0:
										computer_move(board, game, user_id)
								else:
									send_message(user_id, "not valid command")
							else:
								send_message(user_id, "it's not your turn, wait for your opponent's move")	
						else:
							send_message(user_id, "not playing in any game")

					# salvo il messaggio nel DB per segnarlo come risposta avvenuta
					session.add(Message(user_id=user_id, message_id=message_id, text=text, date=date))
					session.commit()
					print("replied to " + str(message_id))
				else:
					print("already replied at " + str(message_id))

				# cancello il messaggio (comando) che ho appena inviato
				delete_message(user_id, message_id)
		time.sleep(5)

def send_photo(user_id, photo_url, local_file):
	if user_id != None:
		while True:
			if local_file == False:
				url = f"{BOT_URL}/sendPhoto?chat_id={user_id}&photo={photo_url}"
				try:
					r = requests.get(url, timeout=TIMEOUT)
					#print('send_photo response')
					#print(r.json())
					break
				except Exception as e:
					print(e)
					time.sleep(3)
			else:
				url = f"{BOT_URL}/sendPhoto?chat_id={user_id}"
				files = {'photo': open(photo_url, 'rb')}
				try:
					r = requests.get(url, files=files, timeout=TIMEOUT)
					json = r.json()
					#print('send_photo response')
					#print(json)
					if len(json['result']) > 0:
						result = json['result']
						db_add_BotMessage(session, result['chat']['id'], result['message_id'])
					break
				except Exception as e:
					print(e)
					time.sleep(3)

def send_message(user_id, text):
	if user_id != None:
		params = {
			"chat_id": user_id,
			"text": text,
			"parse_mode": "HTML"
		}
		url = f"{BOT_URL}/sendMessage"
		while True:
			try:
				r = requests.get(url, params=params, timeout=TIMEOUT)
				json = r.json()
				#print('send_message response')
				#print(json)
				if len(json['result']) > 0:
					result = json['result']
					db_add_BotMessage(session, result['chat']['id'], result['message_id'])
				break
			except Exception as e:
				print(e)
				time.sleep(3)

def delete_message(chat_id, message_id):
	delete_url = f"{BOT_URL}/deleteMessage"
	params = {
		'chat_id': chat_id,
		'message_id': message_id
	}
	while True:
		try:
			response = requests.get(delete_url, params=params, timeout=TIMEOUT)
			break
		except Exception as e:
			print(e)
			time.sleep(3)

def send_reply(user_id, reply_id, text):
	url = f"{BOT_URL}/sendMessage?chat_id={user_id}&reply_to_message_id={reply_id}&text={text}"
	while True:
		try:
			r = requests.get(url, timeout=TIMEOUT)
			print(r.json())	
			break
		except Exception as e:
			print(e)
			time.sleep(3)
	
def get_updates():
	global offset
	if offset == 0:
		url = f"{BOT_URL}/getUpdates"
	else:
		url = f"{BOT_URL}/getUpdates?offset={offset}"
	while True:
		try:
			r = requests.get(url, timeout=TIMEOUT)
			content = r.json()
			# se ci sono nuovi messaggi prendo l'ultimo update_id e aumento l'offset di 1, per riuscire sempre a prendere gli ultimi 100 messaggi.
			# telegram non restituisce più di 100 messaggi per volta, bisogna passargli un offset 
			if len(content['result']) > 0:
				update_id = content['result'][-1]['update_id']
				offset = update_id + 1
				print(content)
			return content		
		except Exception as e:
			print(f"get update error: {e}")
			time.sleep(3)

def clear_bot_messages(session, user_id):
	botmessages = db_get_botmessages(session, user_id)
	#print('bot messages')	
	for i in range(0, len(botmessages)):
		m = botmessages[i][0]
		#print(m)
		delete_message(m.chat_id, m.message_id)
		db_delete_botmessage(session, m.message_id)	

def game_add(session, p1, p2):
	game = db_add_game(session, p1, p2)
	if game:
		save_game_pgn(chess.Board(), game.id)
		send_photo(p1, "new_game.pdf", True)
		send_message(p1, "new game started, you own WHITE pieces")
		if game.player_2 != 0:
			send_photo(game.player_2, "new_game.pdf", True)
			send_message(game.player_2, "new game started, you own BLACK pieces")
	else:
		send_message(p1, "you or your opponent is already playing a game")

def game_stop(session, user_id, game, board):
	game_moves = ""

	if game != None:
		game_moves = f"\ngame moves:\n{get_game_moves(game.id)}"
		db_delete_game(session, game.id)
		delete_game_pgn(game.id)
	
	if board and board.is_game_over():
		result = board.result()
		if result == "0-1":
			result = "BLACK"
		if result == "1-0":
			result = "WHITE"
		if result == "BLACK" or result == "WHITE":
			response = f"Congratulations! {result} has won the game! {game_moves}"
		else:
			response = f"Game ended in a draw! {game_moves}"
		send_message(game.player_1, response)
		if game.player_2 != 0: # se il giocatore 2 non è il computer
			send_message(game.player_2, response)

	else:
		response_p1 = f"your opponent left the game, you win! {game_moves}"
		if user_id == game.player_1:
			response_p1 = f"you left the game, you lost! {game_moves}"
		
		response_p2 = f"your opponent left the game, you win! {game_moves}"
		if user_id == game.player_2:
			response_p2 = f"you left the game, you lost! {game_moves}"

		send_message(game.player_1, response_p1)
		if game.player_2 != 0: # se il giocatore 2 non è il computer
			send_message(game.player_2, response_p2)


def computer_move(board, game, user_id):
	global STOCKFISH
	if STOCKFISH == None:
		print("STOCKFISH not found!")
		return
	engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH)
	engine.configure({"Skill Level": 5}) # 0-20
	result = engine.play(board, chess.engine.Limit(time=4.0))
	best_move = result.move
	pos = best_move.uci()
	engine.quit()
	'''
	moves = []
	for move in board.legal_moves:
		moves.append(move.uci())
	r = random.randint(0, len(moves)-1)
	pos = moves[r]
	'''
	chess_move(board, game, user_id, pos)

def chess_move(board, game, user_id, san_move):
	result = False
	try:
		move = board.parse_san(san_move) # controlla se la mossa è legale
		board.push(move)
		file_name = str(game.id) + "_" + str(san_move)
		save_image(board, file_name, move)
		clear_bot_messages(session, user_id)
		send_photo(game.player_1, "data/"+file_name+".pdf", True)
		if game.player_2 != 0: # player_2 non è il computer
			send_photo(game.player_2, "data/"+file_name+".pdf", True)			
		os.remove("data/"+file_name+".pdf")
		save_game_pgn(board, game.id)
		result = True
	except ValueError:
		send_message(user_id, "illegal move " + san_move)
	return result

def validate_str_move(text):
	if len(text) >= 2 and len(text) <= 4:
		return True
	return False

def save_image(board, name, last_move):
	svg_path = "data/"+name+".svg"
	f = open(svg_path, "w")
	svg = chess.svg.board(board, lastmove=last_move)
	f.write(svg)
	f.close()
	# converting svg to pdf or png
	drawing = svg2rlg(svg_path)
	renderPDF.drawToFile(drawing, "data/"+name+".pdf")
	#cairosvg.svg2png(url=svg_path, write_to="data/"+name+".png")
	os.remove(svg_path)

def print_game_pgn(name):
	pgn = open("data/pgn/"+name+".pgn")
	game = chess.pgn.read_game(pgn)
	print("printing images..."+game.headers["Event"])
	# Iterate through all moves and play them on a board.
	board = game.board()
	n = 0
	for move in game.mainline_moves():
		board.push(move)
		save_image(board, "m" + str(n), move)
		n+=1
	print("done")

def get_game_moves(name):
	if DEBUG_PGN:
		name = DEBUG_PGN
	pgn = open("data/pgn/"+str(name)+".pgn")
	game = chess.pgn.read_game(pgn)
	pgn.close()
	board = game.board()
	result = ""
	for m in game.mainline_moves():
		try:
			san = board.san(m)
			result += san + " "
		except:
			pass
	return result

def load_game_pgn(name):
	if DEBUG_PGN:
		name = DEBUG_PGN
	pgn = open("data/pgn/"+str(name)+".pgn")
	game = chess.pgn.read_game(pgn)
	pgn.close()
	board = game.board()
	for move in game.mainline_moves():
		board.push(move)
	return board

def save_game_pgn(board, name):
	game = chess.pgn.Game()
	node = game
	for move in board.move_stack:
		node = node.add_variation(move)
	f = open("data/pgn/"+str(name)+".pgn", "w")
	f.write(str(game))
	f.close()

def delete_game_pgn(name):
	path = "data/pgn/"+str(name)+".pgn"
	if os.path.exists(path):
		os.remove(path)

def check_game_status(board):
	#if board.outcome():
		#print("outcome: " + board.outcome())
	if board.is_checkmate():
		return "checkmate"
	if board.is_stalemate():
		return "stalemate"
	if board.is_insufficient_material():
		return "insufficient_material"
	return "ok"

def read_command_params(text):
	params = text.split(" ")
	a = []
	for i in range(len(params)):
		if i > 0:
			a.append(params[i])
	return a	

def read_config():
	if os.path.exists("data") == False:
		os.mkdir("data")
	if os.path.exists("data/pgn") == False:
		os.mkdir("data/pgn")

	global TOKEN
	global BOT_URL 
	global STOCKFISH 
	if os.path.exists("config") == False:
		print("missing config file")
		return False
	f = open("config", "r")
	for line in f:
		if line.startswith("TELEGRAM_TOKEN="):
			a = line.split("=")
			if len(a) > 1:
				TOKEN = a[1].strip()
				BOT_URL = f"https://api.telegram.org/bot{TOKEN}"
		if line.startswith("STOCKFISH="):
			a = line.split("=")
			if len(a) > 1:
				STOCKFISH = a[1].strip()

	f.close()
	if TOKEN != None and BOT_URL != None:
		return True
	else:
		print("TOKEN error in config file")
		return False

def get_menu_buttons():
	commands = [
		{
			'command': 'start',
			'description': 'Start the bot'
		},
		{
			'command': 'newgame_computer',
			'description': 'Start a new game against the computer'
		},
		{
			'command': 'newgame',
			'description': 'Start a new multiplayer game'
		},	
		{
			'command': 'stopgame',
			'description': 'Stop the game, you will lose the game'
		},	
		{
			'command': 'rmlobby',
			'description': 'Remove the lobby you have created'
		}
	]
	return commands

if __name__ == "__main__":
	main()
