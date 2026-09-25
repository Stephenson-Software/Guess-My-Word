import contextlib
import io
import os
import subprocess
import sys
import unittest
from unittest.mock import patch

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC_DIR)

import guessMyWord


def playGame(guesses, wordIndex=0):
	"""Run one game with scripted input and a fixed word, returning printed output."""
	game = guessMyWord.GuessMyWord()
	buffer = io.StringIO()
	with patch("guessMyWord.randint", return_value=wordIndex):
		with patch("builtins.input", side_effect=guesses):
			with contextlib.redirect_stdout(buffer):
				game.run()
	return buffer.getvalue()


# @author Daniel McCoy Stephenson
# @since August 2026
class TestGuessMyWord(unittest.TestCase):
	def test_import_does_not_start_game(self):
		"""Importing the module defines the class without entering run() (issue #10)."""
		environment = dict(os.environ)
		environment["PYTHONPATH"] = SRC_DIR
		result = subprocess.run(
			[sys.executable, "-c", "import guessMyWord"],
			stdin=subprocess.DEVNULL,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			env=environment,
			timeout=30,
		)
		self.assertEqual(result.returncode, 0, result.stderr.decode())
		self.assertEqual(result.stdout.decode(), "")

	def test_constructor_sets_five_guesses(self):
		self.assertEqual(guessMyWord.GuessMyWord().guesses, 5)

	def test_every_word_is_four_uppercase_characters(self):
		"""len(guess) != 4 and the character comparison both depend on this invariant."""
		for word in guessMyWord.GuessMyWord().words:
			self.assertEqual(len(word), 4, word)
			self.assertEqual(word, word.upper(), word)

	def test_word_list_is_not_empty(self):
		self.assertGreater(len(guessMyWord.GuessMyWord().words), 0)

	def test_no_matching_characters_reports_zero(self):
		output = playGame(["FOUR"] * 5)
		self.assertIn("That had 0 characters in common.", output)

	def test_exact_guess_wins(self):
		"""Regression guard for issue #6: the accumulated count reaches 4 on the exact
		word, which takes the win branch."""
		output = playGame(["DICE"] * 5)
		self.assertIn("You got the word! It was DICE", output)
		self.assertNotIn("The word was DICE", output)

	def test_partial_match_accumulates_beyond_one(self):
		"""Regression guard for issue #6: 'LIKE' shares the positional 'I' and 'E' with
		'DICE', so two matches must be reported rather than the overwritten one."""
		output = playGame(["LIKE"] * 5)
		self.assertIn("That had 2 characters in common.", output)

	def test_wrong_length_guess_costs_one_guess(self):
		"""Regression guard for issue #7: a short guess costs exactly one guess rather
		than ending the run, so the remaining turns stay playable."""
		output = playGame(["AB", "DICE"])
		self.assertIn("That isn't four characters long!", output)
		self.assertIn("You have 4 guesses.", output)
		self.assertIn("You got the word! It was DICE", output)
		self.assertNotIn("The word was DICE", output)

	def test_lowercase_guess_wins(self):
		"""Regression guard for issue #8: the guess is upper-cased before comparison, so
		a lowercase spelling of the word wins rather than scoring zero."""
		output = playGame(["dice"] * 5)
		self.assertIn("You got the word! It was DICE", output)
		self.assertNotIn("That had 0 characters in common.", output)

	def test_mixed_case_partial_match_is_scored(self):
		"""Regression guard for issue #8: 'LiKe' shares the positional 'i' and 'e' with
		'DICE' only once normalized, so two matches are reported rather than zero."""
		output = playGame(["LiKe"] * 5)
		self.assertIn("That had 2 characters in common.", output)

	def test_end_of_input_ends_game_cleanly(self):
		"""Regression guard for issue #9: running out of input after one guess ends the
		game with the closing message rather than raising EOFError."""
		output = playGame(["LIKE", EOFError()])
		self.assertIn("That had 2 characters in common.", output)
		self.assertIn("The word was DICE", output)


if __name__ == "__main__":
	unittest.main()
