from typing import List
from typing import Optional
from sqlalchemy import ForeignKey, String, Boolean, Integer, select, create_engine, or_, delete
from sqlalchemy import text as db_text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
import time
import random 
import string

class Base(DeclarativeBase):
    pass

class Message(Base):
    __tablename__ = "message"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id = mapped_column(Integer, nullable=False)
    message_id = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(String(30))
    date = mapped_column(Integer, nullable=False)
    def __repr__(self) -> str:
        return f"Message(id={self.id!r}, user_id={self.user_id!r}, text={self.text!r}, message_id={self.message_id!r}, date={self.date!r})"

class BotMessage(Base):
    __tablename__ = "botmessage"
    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id = mapped_column(Integer, nullable=False)
    message_id = mapped_column(Integer, nullable=False)
    def __repr__(self) -> str:
        return f"BotMessage(id={self.id!r}, chat_id={self.chat_id!r}, message_id={self.message_id!r})"

class Game(Base):
    __tablename__ = "game"
    id: Mapped[int] = mapped_column(primary_key=True)
    player_1 = mapped_column(Integer, nullable=False)
    player_2 = mapped_column(Integer, nullable=False)
    def __repr__(self) -> str:
        return f"Game(id={self.id!r}, player_1={self.player_1!r}, player_2={self.player_2!r})"

class Lobby(Base):
    __tablename__ = "lobby"
    id: Mapped[int] = mapped_column(primary_key=True)
    name = mapped_column(String(5), nullable=False)
    creator_id = mapped_column(Integer, nullable=False)
    def __repr__(self) -> str:
        return f"Lobby(id={self.id!r})"

def db_init_session():
    engine = create_engine("sqlite:///data.db", echo=False)
    session = Session(engine)
    return session

def db_create_database():
    print("creating database...")
    engine = create_engine("sqlite:///data.db", echo=True)
    Base.metadata.create_all(engine)
    session = Session(engine)

def db_get_last_message(session, user_id):
    q = select(Message).where(Message.user_id.in_([user_id])).order_by(Message.id.desc())
    result = session.execute(q).first()
    print("result")
    print(result)
    if result:
        #m = session.get(Message result[0].id)
        return result[0].message_id
    else:
        return None 

def db_raw_sql(session, sql_str):
    #sql = db_text('ALTER TABLE `reply` RENAME TO `message`')
	#sql = db_text('DROP TABLE `message`')
    sql = db_text(sql_str)
    session.execute(sql)

def db_get_player_game(session, player_id):
    q = select(Game).where(or_(Game.player_1 == player_id, Game.player_2 == player_id))
    result = session.execute(q).first()
    if result is not None:
        return result[0]
    else:
        return None

def db_add_game(session, player_1, player_2):
    # prima controllo che entrambi i giocatori non sono in altre partite in corso
    if db_get_player_game(session, player_1) == None and (db_get_player_game(session, player_2) == None or player_2 == 0):
        game = Game(player_1 = player_1, player_2 = player_2)
        session.add(game)
        session.commit()
        return game
    else:
        return None

def db_add_BotMessage(session, chat_id, message_id):
    #print(f'db add bot message {message_id}')
    message = BotMessage(chat_id = chat_id, message_id = message_id)
    session.add(message)
    session.commit()

def db_get_botmessages(session, chat_id):
    q = select(BotMessage).where(BotMessage.chat_id == chat_id)
    result = session.execute(q)
    return result.all()

def db_delete_botmessage(session, message_id):
    q = delete(BotMessage).where(message_id == message_id)
    session.execute(q)

def db_add_lobby(session, creator_id):
    # il giocatore 1 non deve già giocare ad una partita o aver creato un'altra lobby
    game = db_get_player_game(session, creator_id)
    lobby = db_get_player_lobby(session, creator_id)
    if game == None and lobby == None:
        name = db_random_name(session) 
        lobby = Lobby(name=name, creator_id=creator_id)
        session.add(lobby)
        session.commit()
        return f"Succesfully created lobby named {lobby.name}, your opponent may now accept to play with you writing /playgame {lobby.name}"
    else:
        if game != None:
            return "you are already playing a game"
        if lobby != None:
            return f"you have already created a lobby, {lobby.name}, you have to delete that lobby to create a new one ( /rmlobby )"

def db_get_player_lobby(session, player_id):
    q = select(Lobby).where(Lobby.creator_id == player_id)
    result = session.execute(q).first()
    if result is not None:
        return result[0]
    else:
        return None

# comando /playgame nomepartita, il giocatore 2 (p2) accetta di giocare;
def db_play_game(session, player_2, name):
    # il giocatore 2 non deve già giocare ad altre partite
    if db_get_player_game(session, player_2) == None:
        # seleziona la lobby tramite name,
        q = select(Lobby).where(Lobby.name == name)
        r = session.execute(q).first()
        if r is not None:
            if r[0].creator_id != player_2: # se il creatore della lobby e il giocatore 2 non sono la solita persona
                # elimina la lobby
                db_delete_lobby(session, r[0].id)
                # ritorno p1 (creator_id) e p2 che accetta tramite /playgame nomepartita (name) per creare la nuova partita effettiva fra i due giocatori
                return {"p1": r[0].creator_id, "p2": player_2}
            else:
                return "you can't play versus yourself!"
        else:
            return f"game named {name} not found"
    else:
        return "you are already playing a game"

def db_delete_lobby(session, lobby_id):
    l = session.get(Lobby, lobby_id)
    if l is not None:
        session.delete(l)
        session.commit()        

def db_delete_game(session, game_id):
    game = session.get(Game, game_id)
    if game is not None:
        session.delete(game)
        session.commit()

def db_print_messages(session):
    q = select(Message)
    for m in session.scalars(q):
        print(m)

def db_print_botmessages(session):
    q = select(BotMessage)
    for m in session.scalars(q):
        print(m)        

def db_print_games(session):
    q = select(Game)
    for g in session.scalars(q):
        print(g)

def db_print_lobbies(session):
    q = select(Lobby)
    for l in session.scalars(q):
        print(l) 

def db_random_name(session):
    characters = string.ascii_lowercase + string.digits
    random_string = ''.join(random.choices(characters, k=6))
    q = select(Lobby).where(Lobby.name == random_string)
    result = session.execute(q).first()
    if result == None:
        return random_string
    else:
        return db_random_name(session)

def test_db_save_message(session):
    message = Message(user_id=1234, message_id=1, text="hello world", date=time.time())
    session.add_all([message])
    session.commit()

def test_db_get_message(session, id):
    q = select(Message).where(Message.user_id.in_([id]))
    for message in session.scalars(q):
        print(message)
        if message.replied == False:
            print("replied is false")
        message.replied = True
        session.commit()
        print(message)