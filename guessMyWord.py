from random import randint
words = ["DICE", "FOUR", "WHAT", "COKE", "LIKE", "BIKE", "TIKE", "SIKE", "LOVE", "OURS", "BUTT", "CURL", "FLAT", "DIPS", "PUSH", "WORK", "HARD", "NICE", "WARS", "STAR", "HERO"]

wordToGuess = words[(randint(0, len(words) - 1))]

guesses = 5
won = False
while guesses > 0:
	print "\nThe word can be any of these. Make your guess. You have %d guesses.\n" % guesses

	print words

	next = raw_input("\n> ")

	if len(next) != 4:
		print "That isn't four characters long!"
		guesses = guesses - 1
		continue
	
	incommon = 0
	y = 0
	for c in wordToGuess:
		if next[y] == c:
			incommon = incommon + 1
		y = y + 1

	if incommon < 4:
		print "\nThat had %d characters in common." % incommon
		guesses = guesses - 1
	elif incommon == 4:
		print "\nYou got the word! It was %s!" % wordToGuess
		guesses = 0
		won = True
		
if won == False:
	print "\NThe word was %s" % wordToGuess
	