#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This sccript is used to match untokenized text to tokenized text,
or to match with different tokenizations. It assumes that the two
texts have the same number of characters (excluding spaces) and
start with the same character. 
"""

def character_to_token_mapping(text, tokens):
	char_indice_no_spaces = [i for i, char in enumerate(text) if char != " "]
	text_no_spaces = [text[i] for i in char_indice_no_spaces]

	if len(text_no_spaces) != len("".join(tokens)):
		print("Mapping cannot be produced, tokens and text don't have same length")
		print("Length of string text no spaces: {}".format(len(text_no_spaces)))
		print("Length of tokens joined: {}".format(len("".join(tokens))))
		print("Skipping ...")
		return 0

	char_counter = -1
	char_to_token_id = {}
	for token_index, token in enumerate(tokens):
		for char in token:
			char_counter += 1
			original_char_id = char_indice_no_spaces[char_counter]
			char_to_token_id[original_char_id] = token_index
	return char_to_token_id

# mapped according to first mapping (a)
def token_to_token_from_char_mapping(char_to_tok_a, char_to_tok_b):
	current_tok_id = 0
	tok_to_tok_mapping = {}
	tok_to_tok_mapping[current_tok_id] = []

	for char_id, tok_id in char_to_tok_a.items():
		if tok_id not in tok_to_tok_mapping:
			tok_to_tok_mapping[tok_id] = []

		if char_id in char_to_tok_b:
			if char_to_tok_b[char_id] not in tok_to_tok_mapping[tok_id]:
				tok_to_tok_mapping[tok_id].append(char_to_tok_b[char_id])
		else:
			print("Error, the ID is not in the second mapping.")
	return tok_to_tok_mapping


def reverse_mapping(char_to_tok):
	tok_to_char = {}
	for char_id, tok_id in char_to_tok.items():
		if tok_id not in tok_to_char:
			tok_to_char[tok_id] = []
		tok_to_char[tok_id].append(char_id)
	return tok_to_char
