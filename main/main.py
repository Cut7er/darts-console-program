import sqlite3
import re
import datetime
from pandas import read_excel
from colorama import init
from playsound import playsound

# autoreset of coloring after every printout
init(autoreset=True)

#ANSI Color Code CONSTANTS
YELLOW = "\x1b[1;33;40m"
GREEN = "\x1b[1;32;40m"
RED = "\x1b[1;31;40m"
CLEAR = "\x1b[0m"
WHITE_BG = "\u001b[47m"
BOLD = "\u001b[1m"

DB_PATH = "data/database.db"

CHECKOUT_VARIANTS = set(read_excel('data/checkout.xlsx')["value"].tolist()) #Daten aus DB holen

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
				,(player, avg_limit,))
		return re.sub("[()',]", "", str(self.cursor.fetchone()))
	
	def get_top_hit(self, player, nb_games):
		self.cursor.execute(
				"SELECT * FROM (SELECT top_score FROM player_stats WHERE name == ? ORDER BY game_id DESC LIMIT ?) ORDER BY top_score DESC LIMIT 1"
				,(player, nb_games,))
		return re.sub("[()',]", "", str(self.cursor.fetchone()))

	def get_max_checkout(self, nb_games, player):
		self.cursor.execute(
			"SELECT MAX(CAST(checkout AS INT)) FROM (SELECT * FROM game_overview ORDER BY game_id DESC LIMIT ?) WHERE winner == ?"
			,(nb_games, player,))
		return re.sub("[()',]", "", str(self.cursor.fetchone()))

	def get_checkout(self, score):
		self.cursor.execute(
			"SELECT checkout FROM checkout_table WHERE value == ?", (score,))
		return re.sub("[()',]", "", str(self.cursor.fetchone()))

	def get_all_direct_games(self, player):
		self.cursor.execute(
			"""SELECT COUNT(winner) FROM (SELECT * FROM game_overview WHERE player1 == ? AND player2 == ?
			UNION SELECT * FROM game_overview WHERE player1 == ? AND player2 == ?) """
			,(players[0].name, players[1].name, players[1].name, players[0].name,))
		return re.sub("[()',]", "", str(self.cursor.fetchone()))
	
	def get_all_direct_wins(self, player):
		self.cursor.execute(
			"""SELECT COUNT(winner) FROM (SELECT * FROM game_overview WHERE player1 == ? AND player2 == ?
			UNION SELECT * FROM game_overview WHERE player1 == ? AND player2 == ?) WHERE winner == ?"""
			,(players[0].name, players[1].name, players[1].name, players[0].name, players[0].name,))
		return re.sub("[()',]", "", str(self.cursor.fetchone()))
	
	def get_trend_direct_games(self, player, nb_trend_games):
		self.cursor.execute(
			"""SELECT COUNT(winner) FROM (SELECT * FROM (SELECT * FROM game_overview WHERE player1 == ? AND player2 == ?
			UNION SELECT * FROM game_overview WHERE player1 == ? AND player2 == ?) ORDER BY game_id DESC LIMIT ?)"""
			,(players[0].name, players[1].name, players[1].name, players[0].name, nb_trend_games,))
		return re.sub("[()',]", "", str(self.cursor.fetchone()))

	def get_trend_direct_wins(self, player, nb_trend_games):
		self.cursor.execute(
			"""SELECT COUNT(winner) FROM (SELECT * FROM (SELECT * FROM game_overview WHERE player1 == ? AND player2 == ?
			UNION SELECT * FROM game_overview WHERE player1 == ? AND player2 == ?) ORDER BY game_id DESC LIMIT ?) WHERE winner == ?"""
			,(players[0].name, players[1].name, players[1].name, players[0].name, nb_trend_games, players[0].name,))
		return re.sub("[()',]", "", str(self.cursor.fetchone()))

	def record_game(self, player_1, player_2, winner, points_default, checkout, player_1_score_history, player_2_score_history): 
		date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		self.cursor.execute("INSERT INTO game_overview(game_id, player1, player2, winner, gamemode, checkout) VALUES (?, ?, ?, ?, ?, ?)",
							(date, player_1, player_2, winner, points_default, checkout))
		for player in players:
			self.cursor.execute("INSERT INTO player_stats(game_id, name, points, turns, top_score, score_hist) VALUES (?, ?, ?, ?, ?, ?)",
						   (date, player.name, sum(player.score_history), len(player.score_history), 
						   	sorted(player.score_history)[-1], str(player.score_history))) #crashes when one player has no history
		self.db.commit()     
	
class Player:
	"""Holds all relevant information about the two players."""
	def __init__(self, name, score, score_history):
		self.name = name
		self.score = score
		self.score_history = score_history
		self.wins = 0
		self.legs = 0
		self.sets = 0

	def __str__(self):
		"""'print(player)' just prints the name of the player."""
		return self.name


"""GAME-RELEVANT FUNCTIONS"""
def get_player_hit():
	"""Ask the user until he supplies a valid hit."""
	while True:
		try:
			hit = int(input("Punkte geworfen: "))
		except ValueError:
			print(f"{RED}Bitte eine ganze ZAHL zwischen 0 und 180 eingeben!")
		else:
			if 0 <= hit <= 180:
				if hit >= 100:
					playsound('sounds/Applaus.mp3', True)
				if hit == 0:
					playsound('sounds/Meep.mp3', True)
				return hit
			else:
				print(f"{RED}Bitte eine ganze Zahl ZWISCHEN 0 UND 180 eingeben!")

def check_for_valid_int(input_text):
	"""checks if the user input is an integer - the parameter is the text the user gets to see"""
	while True:
		try:
			the_verified_integer = int(input(input_text))
			return the_verified_integer
		except ValueError:
			print(f"{RED}Bitte eine ganze Zahl eingeben!")

def players_initial_setup():
	players = [Player(input("\nSpieler 1: "), points_default, []),
			   Player(input("Spieler 2: "), points_default, [])]
	return players


"""STATISTICS FUNCTIONS"""
def player_statistics(players):
	"""query & show historic stats for each player before the game starts"""
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
		print(f"Höchster Wurf:     {GREEN}{db.get_top_hit(player.name, 1000)}") #average score for all games of player  --> platzhalter für "all" finden
		print(f"Höchster Checkout: {GREEN}{db.get_max_checkout(1000,player.name)}") #same

def players_direct_comparison(players):
	"""the two players are compared against each other, 1. for all games and 2. for the last n games""" 
	nb_trend_games = 5
	player1_direct_games = db.get_all_direct_games(players) 
	player1_direct_wins = db.get_all_direct_wins(players)
	player1_direct_losses = str(int(player1_direct_games) - int(player1_direct_wins))
	player1_trend_games = db.get_trend_direct_games(players, nb_trend_games)
	player1_trend_wins = db.get_trend_direct_wins(players, nb_trend_games)
	player1_trend_losses = str(int(player1_trend_games) - int(player1_trend_wins))

	print(f"\n{WHITE_BG}{64*'-'}") #als String einspeisen?!
	print(f"\n{BOLD}Direktvergleich{CLEAR}{9*' '}{RED}{players[0].name}{4*' '}{GREEN}vs.{4*' '}{RED}{players[1].name}{CLEAR}\n")
	print(f"""{15*'~'}{' '}{YELLOW}Gesamt{CLEAR}:{' '}{players[0].name}{' '}{GREEN}{int(player1_direct_wins)}{(int(4-len(player1_direct_wins)))*' '}-{(int(4-len(player1_direct_losses)))*' '}{int(player1_direct_losses)}{CLEAR}{' '}{players[1].name}{' '}{(28-len(players[0].name)-len(players[1].name))*'~'}\n""")
	print(f"""{15*'~'}{' '}{YELLOW}Trend{CLEAR}:{'  '}{players[0].name}{' '}{GREEN}{int(player1_trend_wins)}{(int(4-len(player1_trend_wins)))*' '}-{(int(4-len(player1_trend_losses)))*' '}{int(player1_trend_losses)}{CLEAR}{' '}{players[1].name}{' '}{(28-len(players[0].name)-len(players[1].name))*'~'}""")   	
	print(f"\n{WHITE_BG}{64*'-'}")

def tournament_statistics():
	"""shows tournament-specific stats for the two players in the tournament"""
	print(f"Turnier-Statistik von {RED}{player.name}{CLEAR}")
	print(f"gewonnene Sätze:   {GREEN}{player.sets}/{nb_sets}{CLEAR} ----- Anzahl Siege im aktuellen Satz: {GREEN}{player.legs}/3")
	print(f"Punkteschnitt:     {GREEN}{db.get_average_score(player.name, players[0].wins + players[1].wins)}")
	print(f"Höchster Wurf:     {GREEN}{db.get_top_hit(player.name, players[0].wins + players[1].wins)}") 
	print(f"Höchster Checkout: {GREEN}{db.get_max_checkout(players[0].wins + players[1].wins, player.name)}\n") 


if __name__ == "__main__":
	# initial game setup - decide to play normal or tournament mode, and if tournament should be standard or custom
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
			nb_legs = check_for_valid_int("\nSpiel-Anzahl für Satzsieg: ") 
			nb_sets = check_for_valid_int("Satz-Anzahl für Turniersieg: ")
				
	points_default = check_for_valid_int("\nStartpunktzahl bitte eingeben: ")	
	
	players = players_initial_setup()

	with DBConnection(DB_PATH) as db:
		
		while True:
			
			# switch players after every match so that they alternate
			if (players[0].wins + players[1].wins) != 0:
				players[0], players[1] = players[1], players[0]

			player_statistics(players) #custom function for statistics of opposing players
			players_direct_comparison(players) # custom function for trend statistics of opposing players

			print(f"\nWir spielen von {GREEN}{points_default}{CLEAR} runter. {RED}{players[0]}{CLEAR} beginnt!")

			# game loop
			play = True
			while play:
				for player in players:
					print(f"\nPunkte von {RED}{player}{CLEAR} vor dem Wurf:  {GREEN}{player.score}")
					if player.score in CHECKOUT_VARIANTS:
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
						# ensures that tournamen statistics are not printed twice / or forgotten
						tournament_statistics()
			else:
				for player in players:
					print(f"{GREEN}Gesamtsiege von {RED}{player}{CLEAR}: {GREEN}{player.wins}\n")

			another_round = input(
				"Neue Spieler? [N] - Abbruch? [Q] - Weiterspielen? [andere Taste].\n")
			if another_round.upper() == 'Q':
				break
			elif another_round.upper() == 'N':
				players = players_initial_setup()
			else:
				continue

