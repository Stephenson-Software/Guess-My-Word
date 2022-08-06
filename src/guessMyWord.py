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
			print("\nThe word can be any of these. Make your guess. You have", self.guesses,"guesses.\n")

			print(self.words)

			next = input("\n> ")

			if len(next) != 4:
				print("That isn't four characters long!")
				self.guesses =- 1
				continue
			
			incommon = 0
			y = 0
			for c in wordToGuess:
				if next[y] == c:
					incommon =+ 1
				y = y + 1

			if incommon < 4:
				print("\nThat had", incommon, "characters in common.")
				self.guesses = self.guesses - 1
			elif incommon == 4:
				print("\nYou got the word! It was", wordToGuess) 
				self.guesses = 0
				won = True
				
		if won == False:
			print("\nThe word was", wordToGuess)

guessMyWord = GuessMyWord()
guessMyWord.run()