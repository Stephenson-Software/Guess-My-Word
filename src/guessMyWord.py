import io
import sys
from random import randint


# @author Daniel McCoy Stephenson
# @since December 2016
class GuessMyWord:
	def __init__(self):
		self.words = ["DICE", "FOUR", "WHAT", "COKE", "LIKE", "BIKE", "TIKE", "SIKE", "LOVE", "OURS", "BUTT", "CURL", "FLAT", "DIPS", "PUSH", "WORK", "HARD", "NICE", "WARS", "STAR", "HERO"]
		self.guesses = 5

	def run(self):
		wordToGuess = self.words[(randint(0, len(self.words) - 1))]
		won = False
		while self.guesses > 0:
			guessNoun = "guess" if self.guesses == 1 else "guesses"
			print("\nThe word can be any of these. Make your guess. You have", self.guesses, guessNoun + ".\n")

			print(self.words)

			try:
				guess = input("\n> ").strip()
				guess.encode()  # raises on a surrogate standing for an undecodable byte
			except UnicodeError:
				guess = ""
			except (EOFError, KeyboardInterrupt, RuntimeError):  # RuntimeError: input() found a standard stream closed
				print()
				break

			if len(guess) != 4:
				print("That isn't four characters long!")
				self.guesses -= 1
				continue
			
			incommon = 0
			y = 0
			for c in wordToGuess:
				if guess[y].upper() == c:
					incommon += 1
				y = y + 1

			if incommon < 4:
				characterNoun = "character" if incommon == 1 else "characters"
				print("\nThat had", incommon, characterNoun, "in common.")
				self.guesses = self.guesses - 1
			elif incommon == 4:
				print("\nYou got the word! It was", wordToGuess) 
				self.guesses = 0
				won = True
				
		if won == False:
			print("\nThe word was", wordToGuess)

if __name__ == "__main__":
	# A strict decoder would lose every line buffered alongside an undecodable byte.
	if isinstance(sys.stdin, io.TextIOWrapper):
		sys.stdin.reconfigure(errors="surrogateescape")
	guessMyWord = GuessMyWord()
	guessMyWord.run()