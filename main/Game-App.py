import sqlite3
import re
import datetime
from pandas import read_excel
from colorama import init
import playsound

# autoreset of coloring after every printout
init(autoreset=True)

#ANSI Color Code CONSTANTS
YELLOW = "\x1b[1;33;40m"
GREEN = "\x1b[1;32;40m"
RED = "\x1b[1;31;40m"
CLEAR = "\x1b[0m"
WHITE_BG = "\u001b[47m"

# get checkout value list
VALUES = set(read_excel('data/checkout.xlsx')["value"].tolist()) #Daten aus DB holen

class DBConnection:
	"""Manages a db connection and defines the needed queries.
	   Needs to be used as a contextmanager."""

	def __init__(self, file_name):
		self.file_name = file_name
		self.db = None
		self.cursor = None

	def __enter__(self):
		self.db = sqlite3.connect(self.file_name)
		self.cursor = self.db.cursor()
		return self

	def __exit__(self, *args):
		self.cursor.close()
		self.db.close()

	def get_wins(self, player):
		self.cursor.execute(
			"SELECT COUNT(winner) FROM game_overview WHERE winner == ?", (player,))
		return re.sub("[()',]", "", str(self.cursor.fetchone()))
	
	def get_total_games(self, player):
		self.cursor.execute(
			"SELECT COUNT(winner) FROM game_overview WHERE player1 == ? OR player2 == ?", (player, player,))
		return re.sub("[()',]", "", str(self.cursor.fetchone()))
		
	def get_average_score(self, player, avg_limit):
		self.cursor.execute(
				"SELECT SUM(points)/SUM(turns) FROM (SELECT * FROM player_stats WHERE name == ? ORDER BY game_id DESC LIMIT ?)"
				,(player,avg_limit,))
		return re.sub("[()',]", "", str(self.cursor.fetchone()))
	
	def get_top_hit(self, player, nb_games):
		self.cursor.execute(
				"SELECT * FROM (SELECT top_score FROM player_stats WHERE name == ? ORDER BY game_id DESC LIMIT ?) ORDER BY top_score DESC LIMIT 1"
				,(player, nb_games,))
		return re.sub("[()',]", "", str(self.cursor.fetchone()))

	def get_max_checkout(self, nb_games, player):
		self.cursor.execute(
			"SELECT MAX(CAST(checkout AS INT)) FROM (SELECT * FROM game_overview ORDER BY game_id DESC LIMIT ?) WHERE winner == ?"
			,(nb_games,player,))
		return re.sub("[()',]", "", str(self.cursor.fetchone()))

	def get_checkout(self, score):
		self.cursor.execute(
			"SELECT checkout FROM checkout_table WHERE value == ?", (score,))
		return re.sub("[()',]", "", str(self.cursor.fetchone()))

	def get_games_direct(self, player):
		self.cursor.execute(
			"""SELECT COUNT(winner) FROM (SELECT * FROM game_overview WHERE player1 == ? AND player2 == ?
			UNION SELECT * FROM game_overview WHERE player1 == ? AND player2 == ?) """
			,(players[0].name, players[1].name, players[1].name, players[0].name,))
		return re.sub("[()',]", "", str(self.cursor.fetchone()))
	
	def get_wins_direct(self, player):
		self.cursor.execute(
			"""SELECT COUNT(winner) FROM (SELECT * FROM game_overview WHERE player1 == ? AND player2 == ?
			UNION SELECT * FROM game_overview WHERE player1 == ? AND player2 == ?) WHERE winner == ?"""
			,(players[0].name, players[1].name, players[1].name, players[0].name, players[0].name,))
		return re.sub("[()',]", "", str(self.cursor.fetchone()))
	
	def get_games_trend(self, player):
		self.cursor.execute(
			"""SELECT COUNT(winner) FROM (SELECT * FROM (SELECT * FROM game_overview WHERE player1 == ? AND player2 == ?
			UNION SELECT * FROM game_overview WHERE player1 == ? AND player2 == ?) ORDER BY game_id DESC LIMIT 5)"""
			,(players[0].name, players[1].name, players[1].name, players[0].name,))
		return re.sub("[()',]", "", str(self.cursor.fetchone()))

	def get_wins_trend(self, player):
		self.cursor.execute(
			"""SELECT COUNT(winner) FROM (SELECT * FROM (SELECT * FROM game_overview WHERE player1 == ? AND player2 == ?
			UNION SELECT * FROM game_overview WHERE player1 == ? AND player2 == ?) ORDER BY game_id DESC LIMIT 5) WHERE winner == ?"""
			,(players[0].name, players[1].name, players[1].name, players[0].name, players[0].name,))
		return re.sub("[()',]", "", str(self.cursor.fetchone()))

	def record_game(self, player_1, player_2, winner, points_default, checkout, player_1_score_history, player_2_score_history): 
		date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  #gesamte score-history als liste appenden --> neue Zeile "string" nötig
		self.cursor.execute("INSERT INTO game_overview(game_id, player1, player2, winner, gamemode, checkout) VALUES (?, ?, ?, ?, ?, ?)",
							(date, player_1, player_2, winner, points_default, checkout))
		for player in players:
			self.cursor.execute("INSERT INTO player_stats(game_id, name, points, turns, top_score) VALUES (?, ?, ?, ?, ?)",
						   (date, player.name, sum(player.score_history), len(player.score_history), sorted(player.score_history)[-1]))
		self.db.commit()     
	
class Player:

	def __init__(self, name, score, score_history):
		self.name = name
		self.score = score
		self.score_history = score_history
		self.wins = 0
		self.legs = 0
		self.sets = 0

	def __str__(self): #nötig?
		"""`print(player)` just prints the name of the player."""
		return self.name

def get_player_hit():
	"""Ask the user until he supplies a valid hit."""
	while True:
		try:
			hit = int(input("Punkte geworfen: "))
		except ValueError:
			print(f"{RED}Bitte eine Zahl zwischen 0 und 180 eingeben!")
		else:
			if 0 <= hit <= 180:
				if hit >= 100:
					playsound.playsound('sounds/Applaus.mp3', True)
				if hit == 0:
					playsound.playsound('sounds/Meep.mp3', True)
				return hit
			else:
				print(f"{RED}Bitte eine Zahl zwischen 0 und 180 eingeben!")

def player_statistics(players):
	# query & show stats for each player before the game starts
	for player in players:
		player.score = points_default
		player.score_history = []
		player_wins = int(db.get_wins(player.name))
		player_total_games = int(db.get_total_games(player.name))
		if player_total_games != 0:
			player_win_ratio = player_wins / player_total_games
		else:
			player_win_ratio = 0			
		print(f"\nGesamt-Statistik von {RED}{player.name}{CLEAR}")
		print(f"Siege: {GREEN}{player_wins}{CLEAR} ----- Niederlagen: {GREEN}{player_total_games-player_wins}{CLEAR} ----- Siegquote: {GREEN}{player_win_ratio:.2f}")
		print(f"Punkteschnitt:     {GREEN}{db.get_average_score(player.name, 10)}") #2nd parameter: gleitender durchschnitt über n spiele
		print(f"Höchster Wurf:     {GREEN}{db.get_top_hit(player.name, 1000) }") #average score for all games of player  --> platzhalter für "all" finden
		print(f"Höchster Checkout: {GREEN}{db.get_max_checkout(1000,player.name)}") #same

def player_versus(players): #verschönern, mit dynamischer Zeilenlänge
	games_direct = db.get_games_direct(players) #abschaffen!
	wins_direct = db.get_wins_direct(players)
	games_trend = db.get_games_trend(players)
	wins_trend = db.get_wins_trend(players)    
	print(f"\n{WHITE_BG}----------------------------------------------------------------")
	print(f"\nDirektvergleich         {RED}{players[0].name}   {GREEN}vs.   {RED}{players[1].name}{CLEAR}\n")
	print(f"""~~~~~~~~~~~~~~~ {YELLOW}Gesamt{CLEAR}: {players[0].name} {GREEN}{int(wins_direct)}  -  {int(games_direct)
	- int(wins_direct)}{CLEAR} {players[1].name} ~~~~~~~~~~~~~~~~~\n""")    
	if int(wins_direct) >= 10 and (int(games_direct) - int(wins_direct)) >= 10:
		print(f"""~~~~~~~~~~~~~~~ {YELLOW}Trend{CLEAR}:  {players[0].name} {GREEN}{int(wins_trend)}   -   {int(games_trend)
		- int(wins_trend)}{CLEAR} {players[1].name} ~~~~~~~~~~~~~~~~~""")
	elif int(wins_direct) >= 10 and (int(games_direct) - int(wins_direct)) < 10:
		print(f"""~~~~~~~~~~~~~~~ {YELLOW}Trend{CLEAR}:  {players[0].name} {GREEN}{int(wins_trend)}   -  {int(games_trend)
		- int(wins_trend)}{CLEAR} {players[1].name} ~~~~~~~~~~~~~~~~~""")
	elif int(wins_direct) < 10 and (int(games_direct) - int(wins_direct)) >= 10:
		print(f"""~~~~~~~~~~~~~~~ {YELLOW}Trend{CLEAR}:  {players[0].name} {GREEN}{int(wins_trend)}  -   {int(games_trend)
		- int(wins_trend)}{CLEAR} {players[1].name} ~~~~~~~~~~~~~~~~~""")
	else:
		print(f"""~~~~~~~~~~~~~~~ {YELLOW}Trend{CLEAR}:  {players[0].name} {GREEN}{int(wins_trend)}  -  {int(games_trend)
		- int(wins_trend)}{CLEAR} {players[1].name} ~~~~~~~~~~~~~~~~~""")    
	print(f"\n{WHITE_BG}----------------------------------------------------------------")    

def tournament_statistics():
	print(f"Turnier-Statistik von {RED}{player.name}{CLEAR}")
	print(f"gewonnene Sätze:   {GREEN}{player.sets}/{nb_sets}{CLEAR} ----- Anzahl Siege im aktuellen Satz: {GREEN}{player.legs}/3")
	print(f"Punkteschnitt:     {GREEN}{db.get_average_score(player.name, players[0].wins + players[1].wins)}")
	print(f"Höchster Wurf:     {GREEN}{db.get_top_hit(player.name, players[0].wins + players[1].wins)}") 
	print(f"Höchster Checkout: {GREEN}{db.get_max_checkout(players[0].wins + players[1].wins, player.name)}\n") 

def players_initial_setup():
	players = [Player(input("\nSpieler 1: "), points_default, []),
			   Player(input("Spieler 2: "), points_default, [])]
	return players

if __name__ == "__main__":
	# game setup
	tournament_mode = False
	tournament = input("\nTurnier spielen? [T]: ") 
	if tournament.upper() == "T":
		tournament_mode = True
		tournament_end = False
		print(f"{RED}Turniermodus\n")
		
		customize_tournament = input("Standardeinstellungen? (3 Siege pro Satz, 3 Sätze für Turniersieg) [S]: ")
		if customize_tournament.upper() == "S": 
			nb_legs = 3
			nb_sets = 3
			print(f"{RED}Standardeinstellungen!{CLEAR} Es werden {GREEN}{nb_sets} Sätze mit je {nb_legs} Siegen{CLEAR} zum Gesamtsieg benötigt!")	

		else:
			while True: #check for valid number in Funktion überführen
				try:
					nb_legs = int(input("\nSpiel-Anzahl für Satzsieg: "))
					break
				except ValueError:
					print(f"{RED}Bitte eine Zahl eingeben!")

			while True:
				try:
					nb_sets = int(input("Satz-Anzahl für Turniersieg: "))
					break
				except ValueError:
					print(f"{RED}Bitte eine Zahl eingeben!")
	
	while True:
		try:
			points_default = int(input("\nStartpunktzahl bitte eingeben: "))
			break
		except ValueError:
			print(f"{RED}Bitte eine Zahl eingeben!")

	players = players_initial_setup()

	# setup database connection
	with DBConnection('data/darts_db.db') as db:
		while True:
			
			player_statistics(players) #custom function for statistics of opposing players
			player_versus(players) # custom function for trend statistics of opposing players
			
			# switch players after every match so that they alternate
			if (players[0].wins + players[1].wins) != 0:
				players[0], players[1] = players[1], players[0]
				
			print(f"\nWir spielen von {GREEN}{points_default}{CLEAR} runter. {RED}{players[0]}{CLEAR} beginnt!")

			# game loop
			play = True
			while play:
				for player in players:
					print(f"\nPunkte von {RED}{player}{CLEAR} vor dem Wurf:  {GREEN}{player.score}")
					if player.score in VALUES:
						print("Checkout:", db.get_checkout(player.score))

					hit = get_player_hit()
					player.score -= hit
					player.score_history.append(hit)
					if player.score == 0:
						print(f"Punkte von {RED}{player}{CLEAR} nach dem Wurf: {GREEN}{player.score}\n")
						print(f"{YELLOW}=====================***SIEG! SIEG! SIEG!***====================\n")
						player.wins += 1
						if tournament_mode:
							player.legs += 1
							if player.legs == nb_legs:
								player.sets += 1
								player.legs = 0
								print(f"{RED}{player.name}{CLEAR} hat seinen {GREEN}{player.sets}. Satz{CLEAR} gewonnen!\n")
								if player.sets == nb_sets:
									print(f"{YELLOW}{player.name} hat das Turnier gewonnen!\n")
									tournament_end = True
									for player in players:
										tournament_statistics()
										player.legs = 0
										player.sets = 0
								else: 
									for player in players:
										player.legs = 0

						db.record_game(players[0].name, players[1].name, player.name, points_default,
									   hit, players[0].score_history, players[1].score_history)
						play = False
						break
					elif player.score >= 2:
						print(f"Punkte von {RED}{player}{CLEAR} nach dem Wurf: {GREEN}{player.score}")
						print(f"\n----------------------------------------------------------------")
					elif player.score <= 1:
						print(f"{RED}Zu viel geworfen! Lusche.")
						print(f"\n----------------------------------------------------------------")
						player.score += hit

			if tournament_mode:
				for player in players:
					if tournament_end == False:
						# so that tournament stats are not printed twice!
						tournament_statistics()
			else:
				for player in players:
					print(f"Gesamtsiege von {RED}{player}{CLEAR}: {GREEN}{player.wins}\n")

			another_round = input(
				"Neue Spieler? [N] - Abbruch? [Q] - Weiterspielen? [andere Taste].\n")
			if another_round.upper() == 'Q':
				break
			elif another_round.upper() == 'N':
				players = players_initial_setup()
			else:
				continue

