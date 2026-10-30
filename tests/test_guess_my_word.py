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


def runScript(stdin):
	"""Run src/guessMyWord.py as a script with the given stdin, returning its output."""
	result = subprocess.run(
		[sys.executable, "-B", os.path.join(SRC_DIR, "guessMyWord.py")],
		input=stdin.encode(),
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE,
		timeout=30,
	)
	if result.returncode != 0 or result.stderr:
		raise AssertionError("script failed: " + result.stderr.decode())
	return result.stdout.decode()


def revealedWord(output):
	"""Return the word named by the closing 'The word was' line."""
	lastLine = output.rstrip().rpartition("\n")[2]
	if not lastLine.startswith("The word was "):
		raise AssertionError("no closing 'The word was' line: " + repr(lastLine))
	return lastLine[len("The word was "):]


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

	def test_script_plays_to_completion_from_piped_input(self):
		"""Running src/guessMyWord.py as a script, the entry point the README, the VS
		Code launch config and the browser bundle all use, plays a whole game through
		the real input(): five wrong-length guesses end it with the word revealed."""
		output = runScript("AB\n" * 5)
		self.assertEqual(output.count("That isn't four characters long!"), 5)
		self.assertIn(revealedWord(output), guessMyWord.GuessMyWord().words)

	def test_script_ends_cleanly_on_empty_input(self):
		"""With no input at all, the real input() hits end-of-file on the first prompt
		and the script exits normally with the word revealed, without a traceback."""
		output = runScript("")
		self.assertNotIn("That isn't four characters long!", output)
		self.assertIn(revealedWord(output), guessMyWord.GuessMyWord().words)

	def test_constructor_sets_five_guesses(self):
		self.assertEqual(guessMyWord.GuessMyWord().guesses, 5)

	def test_every_word_is_four_uppercase_characters(self):
		"""len(guess) != 4 and the character comparison both depend on this invariant."""
		for word in guessMyWord.GuessMyWord().words:
			self.assertEqual(len(word), 4, word)
			self.assertEqual(word, word.upper(), word)

	def test_word_list_is_not_empty(self):
		self.assertGreater(len(guessMyWord.GuessMyWord().words), 0)

	def test_word_list_has_no_duplicates(self):
		"""The word is drawn by index, so a repeated entry would be drawn twice as often as
		the others and would be shown twice in the list printed before every guess."""
		words = guessMyWord.GuessMyWord().words
		repeated = sorted({word for word in words if words.count(word) > 1})
		self.assertEqual(repeated, [])

	def test_word_draw_reaches_first_and_last_word(self):
		"""The word is drawn with randint, whose bounds are both inclusive: its lowest
		and highest values pick the first and last words rather than indexing past the
		end of the list."""
		words = guessMyWord.GuessMyWord().words
		for bound, expected in ((min, words[0]), (max, words[-1])):
			with self.subTest(expected=expected):
				buffer = io.StringIO()
				with patch("guessMyWord.randint", side_effect=bound):
					with patch("builtins.input", side_effect=[EOFError()]):
						with contextlib.redirect_stdout(buffer):
							guessMyWord.GuessMyWord().run()
				self.assertEqual(revealedWord(buffer.getvalue()), expected)

	def test_word_list_is_shown_before_every_guess(self):
		"""'The word can be any of these.' is followed by the candidate words on every
		turn, so the list the player picks from is printed once per prompt, after the
		turn header and before the guess is scored."""
		words = guessMyWord.GuessMyWord().words
		output = playGame(["FOUR", "LIKE", "DOOR", "WHAT", "COKE"])
		self.assertEqual(output.count(str(words)), 5)
		for turn in output.split("The word can be any of these.")[1:]:
			self.assertIn(str(words), turn.partition("in common.")[0])

	def test_off_list_guess_is_scored_and_costs_one_guess(self):
		"""A four-character guess that is not in the word list is still accepted: 'DUCK'
		is scored positionally against 'DICE' (the 'D' and 'C') and costs one guess."""
		self.assertNotIn("DUCK", guessMyWord.GuessMyWord().words)
		output = playGame(["DUCK", "DICE"])
		self.assertIn("That had 2 characters in common.", output)
		self.assertIn("You have 4 guesses.", output)
		self.assertIn("You got the word! It was DICE", output)

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

	def test_anagram_scores_zero_because_scoring_is_positional(self):
		"""Regression guard for issue #17: 'ECID' holds every letter of 'DICE' but none in
		its position, so it scores 0 rather than the 4 a letter-overlap count would give."""
		output = playGame(["ECID"] * 5)
		self.assertIn("That had 0 characters in common.", output)
		self.assertNotIn("You got the word!", output)

	def test_repeated_letter_counts_only_positional_match(self):
		"""'EEEE' matches 'DICE' only at the last position, so it scores 1 rather than
		counting the 'E' once per repetition."""
		output = playGame(["EEEE"] * 5)
		self.assertIn("That had 1 character in common.", output)

	def test_single_match_uses_singular_noun(self):
		"""Regression guard for issue #27: 'DOOR' shares only the positional 'D' with
		'DICE', so the count reads '1 character' rather than '1 characters'."""
		output = playGame(["DOOR"] * 5)
		self.assertIn("That had 1 character in common.", output)
		self.assertNotIn("1 characters", output)

	def test_last_guess_uses_singular_noun(self):
		"""Regression guard for issue #27: the final turn reads '1 guess' rather than
		'1 guesses', while earlier turns keep the plural."""
		output = playGame(["FOUR"] * 5)
		self.assertIn("You have 1 guess.", output)
		self.assertIn("You have 2 guesses.", output)
		self.assertNotIn("1 guesses", output)

	def test_turn_header_counts_down_from_five(self):
		"""The README promises five guesses in total: the first turn header shows 5, and
		each scored miss lowers the next header by exactly one, down to 1."""
		output = playGame(["FOUR", "LIKE", "DOOR", "WHAT", "COKE"])
		headers = [line for line in output.splitlines() if line.startswith("The word can be any of these.")]
		self.assertEqual(headers, [
			"The word can be any of these. Make your guess. You have 5 guesses.",
			"The word can be any of these. Make your guess. You have 4 guesses.",
			"The word can be any of these. Make your guess. You have 3 guesses.",
			"The word can be any of these. Make your guess. You have 2 guesses.",
			"The word can be any of these. Make your guess. You have 1 guess.",
		])

	def test_wrong_length_guess_costs_one_guess(self):
		"""Regression guard for issue #7: a short guess costs exactly one guess rather
		than ending the run, so the remaining turns stay playable."""
		output = playGame(["AB", "DICE"])
		self.assertIn("That isn't four characters long!", output)
		self.assertIn("You have 4 guesses.", output)
		self.assertIn("You got the word! It was DICE", output)
		self.assertNotIn("The word was DICE", output)

	def test_over_long_guess_costs_one_guess(self):
		"""A guess longer than four characters is the wrong length too: 'DICES' begins with
		'DICE' but costs one guess rather than being scored on its first four characters
		and winning, and the next prompt still accepts the word."""
		output = playGame(["DICES", "DICE"])
		self.assertIn("That isn't four characters long!", output)
		self.assertIn("You have 4 guesses.", output)
		self.assertEqual(output.count("Make your guess."), 2)
		self.assertNotIn("in common", output)
		self.assertIn("You got the word! It was DICE", output)

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

	def test_whitespace_padded_guess_wins(self):
		"""Regression guard for issue #22: surrounding whitespace is stripped before the
		length check, so a padded exact guess wins rather than costing a guess."""
		output = playGame([" dice "] * 5)
		self.assertIn("You got the word! It was DICE", output)
		self.assertNotIn("That isn't four characters long!", output)

	def test_inner_space_is_kept_and_scored(self):
		"""Only surrounding whitespace is stripped: the space in 'D CE' stays, so the guess is
		four characters long and is scored against 'DICE' with the space as a miss, giving
		three matches rather than being rejected or collapsed to 'DCE'."""
		output = playGame(["D CE"] * 5)
		self.assertNotIn("That isn't four characters long!", output)
		self.assertIn("That had 3 characters in common.", output)
		self.assertNotIn("You got the word!", output)

	def test_length_is_checked_before_case_mapping(self):
		"""Regression guard for issue #37: 'ß' upper-cases to 'SS', so the length is checked
		on the guess as typed. The three-character 'ßce' costs a guess as the wrong length
		instead of being scored as 'SSCE'."""
		output = playGame(["ßce", "DICE"])
		self.assertIn("That isn't four characters long!", output)
		self.assertIn("You have 4 guesses.", output)
		self.assertNotIn("in common", output)

	def test_case_mapping_keeps_characters_in_position(self):
		"""Regression guard for issue #37: the four-character 'ßICE' is scored rather than
		rejected as 'SSICE', and its 'I', 'C' and 'E' stay in the positions they were typed
		in, so three matches are reported."""
		output = playGame(["ßICE"] * 5)
		self.assertNotIn("That isn't four characters long!", output)
		self.assertIn("That had 3 characters in common.", output)

	def test_five_misses_end_game_revealing_word(self):
		"""Five scored misses spend every guess: the word is revealed and a sixth input,
		the exact word, is never read (it would otherwise win)."""
		output = playGame(["FOUR", "LIKE", "DOOR", "WHAT", "COKE", "DICE"])
		self.assertIn("You have 1 guess.", output)
		self.assertIn("The word was DICE", output)
		self.assertNotIn("You got the word!", output)
		self.assertEqual(output.count("Make your guess."), 5)

	def test_wrong_length_guesses_alone_exhaust_game(self):
		"""Each wrong-length guess costs one guess, so five of them end the game with the
		word revealed before the sixth input, the exact word, is read."""
		output = playGame(["AB"] * 5 + ["DICE"])
		self.assertEqual(output.count("That isn't four characters long!"), 5)
		self.assertIn("The word was DICE", output)
		self.assertNotIn("You got the word!", output)

	def test_win_on_final_guess_is_a_win(self):
		"""The exact word on the fifth and last guess wins: the loop scores it before the
		guesses run out, so the word is not revealed as a loss."""
		output = playGame(["FOUR", "LIKE", "DOOR", "WHAT", "DICE"])
		self.assertIn("You have 1 guess.", output)
		self.assertIn("You got the word! It was DICE", output)
		self.assertNotIn("The word was DICE", output)

	def test_win_stops_prompting(self):
		"""A win on the second guess ends the game: no further prompt is shown and the
		losing message is not printed."""
		output = playGame(["FOUR", "DICE", "FOUR"])
		self.assertIn("You got the word! It was DICE", output)
		self.assertEqual(output.count("Make your guess."), 2)
		self.assertNotIn("The word was DICE", output)

	def test_empty_guess_costs_one_guess(self):
		"""Pressing Enter without a guess is a wrong-length guess: it costs one guess and
		the next prompt still accepts a winning guess."""
		output = playGame(["", "DICE"])
		self.assertIn("That isn't four characters long!", output)
		self.assertIn("You have 4 guesses.", output)
		self.assertIn("You got the word! It was DICE", output)

	def test_end_of_input_ends_game_cleanly(self):
		"""Regression guard for issue #9: running out of input after one guess ends the
		game with the closing message rather than raising EOFError."""
		output = playGame(["LIKE", EOFError()])
		self.assertIn("That had 2 characters in common.", output)
		self.assertIn("The word was DICE", output)

	def test_interrupt_ends_game_cleanly(self):
		"""Regression guard for issue #21: pressing Ctrl-C at the prompt ends the game
		with the closing message rather than raising KeyboardInterrupt."""
		output = playGame(["LIKE", KeyboardInterrupt()])
		self.assertIn("That had 2 characters in common.", output)
		self.assertIn("The word was DICE", output)


if __name__ == "__main__":
	unittest.main()
