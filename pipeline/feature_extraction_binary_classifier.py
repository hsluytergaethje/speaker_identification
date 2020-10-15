#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Extraction of features for the binary-classifier-sieve.
Here also string features are used. 
"""

from Text import VERB_POS

ACCUSATIVE_DEPENDENCY_LABEL = "obja"
DATIV_DEPENDENCY_LABEL = "objd"


"""
1) Distance:
- distance to quote (sentences, words, entities)
- distance rank (relative to other mentions)
- punctuation inbetween quote and mention
"""

# create array with distance ranks
def get_ranks(distances):
	sorted_distances = sorted(distances)
	ranks = []
	for entry in distances:
		ranks.append(sorted_distances.index(entry))
	return ranks 

#def check_slices_for_punctuation(annot)

def check_tokens_inbetween_for_punctuation(text, annotation, candidate):
	tok_inbetween = []
	if candidate.id < annotation.start_id:
		tok_inbetween = text.get_token_between_tokens(candidate, annotation.start_token)
	elif candidate.id > annotation.end_id:
		tok_inbetween = text.get_token_between_tokens(candidate, annotation.end_token)
	elif candidate.id > annotation.start_id and candidate.id < annotation.end_id:
		if annotation.is_split():
			tokens_inbetween_slices = text.get_token_lists_between_annotation_slices(annotation)
			for token_list in tokens_inbetween_slices:
				if candidate in token_list.tokens:
					tok_inbetween = token_list.tokens

	if len(tok_inbetween) > 0:
		if any(token.is_punctuation() for token in tok_inbetween):
			return True
	return False


# candidate is a token object
# context is a TokenList
# need predefined split of text into paragraphs - not quote dependent 
def get_distance_features(text, annotation, candidates, context):
	distance_features = []
	distances = [text.get_distance_tok_anno(candidate, annotation) for candidate in candidates]
	distance_ranks = get_ranks(distances)
	punctuation_inbetween = [check_tokens_inbetween_for_punctuation(text, annotation, candidate) \
	for candidate in candidates]

	"""
	distance_to_left_paragraph = [text.get_distance_tok_tok(candidate, context.start_token) for candidate \
	in candidates]

	distance_to_right_paragraph = [text.get_distance_tok_tok(candidate, context.end_token) for candidate \
	in candidates]
	"""

	for i in range(len(candidates)):
		features = {}
		features["dist_to_quote"] = distances[i]
		features["distance_rank_to_quote"] = distance_ranks[i]
		features["punc_inbetween_context_to_quote"] = punctuation_inbetween[i]
		"""
		features["distance_left_paragraph"] = distance_to_left_paragraph[i]
		features["distance_right_paragraph"] = distance_to_right_paragraph[i]
		"""
		distance_features.append(features)

	return distance_features

"""
2) Mention
	- number of quotes in the paragraph
	- number of words in the paragraph
	- order of the mention (e.g. second)
	- mention is within conversation (no non-quote text in the same paragraph)
	- mention is within quote
	- PoS of mention (did not bring improvement)
	- mention is pronoun (did not bring improvement)
	- PoS of previous word
	- PoS of next word
	- if next/previous words is punctuation -> lemma of that word
	- is implicit speaker: if quote spans the whole paragraph

	- mention is subject
	- mention is accusative
	- mention is dativ
	- lemma of verb, mention is dependent on 

	- mention is in same sentence as quote 
	- previous word is in quote
	- next wprd is in quote 
"""
def recursive_verb_head_search(token):
	if token.parent_token.pos in VERB_POS:
		return token.parent_token
	else:
		if token.parent_token.id == token.id:
			return None
		return recursive_verb_head_search(token.parent_token)

def get_annotations_in_context(text, context):
	annotations_in_context = []
	for annotation in text.annotations:
		if annotation.start_token in context.tokens and \
		annotation.end_token in context.tokens:
			annotations_in_context.append(annotation)
	return annotations_in_context


def get_number_of_annotations_in_context(text, context):
	anno_in_context = len(get_annotations_in_context(text, context))
	return anno_in_context

# no non-quote text in context
# will probably be false 
def check_if_in_conversation(context):
	return all(token.is_annotated for token in context.tokens)

def get_tokens_before(text, candidates):
	ids_before = [candidate.id - 1 for candidate in candidates]
	tokens_before = []
	for tok_id in ids_before:
		if tok_id > 0 and tok_id < text.token_number:
			tokens_before.append(text.tokens[tok_id])
		else:
			tokens_before.append("-")

	if len(tokens_before) == len(candidates):
		return tokens_before
	else:
		print("Not every token has a previous token. Lengths don't match.")
		print("Aborting ... ")
		return False

def get_tokens_after(text, candidates):
	ids_after = [candidate.id + 1 for candidate in candidates]
	tokens_after = []
	for tok_id in ids_after:
		if tok_id > 0 and tok_id < text.token_number:
			tokens_after.append(text.tokens[tok_id])
		else:
			tokens_after.append("-")

	if len(tokens_after) == len(candidates):
		return tokens_after
	else:
		print("Not every token has a previous token. Lengths don't match.")
		print("Aborting ... ")
		return False

def check_same_sentence_as_quote(annotation, candidate):
	anno_sen_ids = [i for i in range(annotation.sentence_start_id, annotation.sentence_end_id +1)]
	return candidate.sentence_id in anno_sen_ids

def get_candidate_features(text, annotation, candidates, context):
	candidate_features = []

	number_of_anno_in_context = get_number_of_annotations_in_context(text, context)
	#number_of_words_in_context = context.length

	candidate_ids = [candidate.id for candidate in candidates]
	candidate_orders = get_ranks(candidate_ids)
	candidate_in_conversation = check_if_in_conversation(context)
	candidate_in_quote = [candidate in annotation.tokens for candidate in candidates]
	candidate_pos = [candidate.pos for candidate in candidates]
	candidate_is_pronoun = [candidate.is_pronoun() for candidate in candidates]
	
	previous_tokens = get_tokens_before(text, candidates)
	next_tokens = get_tokens_after(text, candidates)

	pos_of_previous = [token.pos if token != "-" else token for token in previous_tokens]
	pos_of_next = [token.pos if token != "-" else token for token in next_tokens]

	previous_is_punc = [token.is_punctuation() if token != "-" else token for token in previous_tokens]
	next_is_punc = [token.is_punctuation() if token != "-" else token for token in next_tokens]

	previous_in_quote = [token in annotation.tokens for token in previous_tokens]
	next_in_quote = [token in annotation.tokens for token in next_tokens]

	candidate_subjects = [candidate.is_subject() for candidate in candidates]
	candidate_accs = [candidate.dependency == ACCUSATIVE_DEPENDENCY_LABEL for candidate in candidates]
	candidate_dativs = [candidate.dependency == DATIV_DEPENDENCY_LABEL for candidate in candidates]

	candidate_parent_verb_lemma = [recursive_verb_head_search(candidate).lemma  if recursive_verb_head_search(candidate) \
	 is not None else "-" for candidate in candidates]

	candidate_in_quote_sentence = [check_same_sentence_as_quote(annotation,candidate) for candidate in candidates]

	for i in range(len(candidates)):
		features = {}
		# static over all candidates --- useful at all? 
		features["number_of_anno_in_context"] = number_of_anno_in_context
		#features["number_of_words_in_context"] = number_of_words_in_context
		features["in_conversation"] = candidate_in_conversation

		features["candidate_order"] = candidate_orders[i]
		features["candidate_in_quote"] = candidate_in_quote[i]
		features["candidate_in_quote_sentence"] = candidate_in_quote_sentence[i]
		
		# mention features
		features["pos"] = candidate_pos[i]
		features["is_pronoun"] = candidate_is_pronoun[i]
		features["is_subject"] = candidate_subjects[i]
		features["is_acc"] = candidate_accs[i]
		features["is_dativ"] = candidate_dativs[i]
		features["lemma_of_verb_parent"] = candidate_parent_verb_lemma[i]
		
		# features of surrounnding token
		features["pos_previous"] = pos_of_previous[i]
		features["pos_next"] = pos_of_next[i]
		features["previous_is_punc"] = previous_is_punc[i]
		features["next_is_punc"] = next_is_punc[i]
		features["previous_in_quote"] = previous_in_quote[i]
		features["next_in_quote"] = next_in_quote[i]

		candidate_features.append(features)

	return candidate_features


"""
3) Quote
    - length
    - order
    - number of words in the paragraph
    - number of names in the paragraph
    - quotes contains name of the candidate, if candidate is name
    - contains text? -- is split?
    - name is in none-quote text of previous paragraph -- where does this come from? 
    - first word is lower cased
"""

def check_quote_has_candidate_name(annotation, candidate):
	if candidate.is_person_name():
		return any(token.lemma == candidate.lemma for token in annotation.tokens)
	return False


def get_quote_features(text, annotation, candidates, context):
	quote_features = []

	annos_in_context = get_annotations_in_context(text, annotation)
	sorted_anno_ids = sorted([anno.id for anno in annos_in_context])
	anno_rank  = sorted_anno_ids.index(annotation.id)

	number_of_names_in_context = len([token for token in context.tokens if token.is_person_name()])
	candidate_name_in_quote = [check_quote_has_candidate_name(annotation, candidate) for 
	candidate in candidates]

	first_word_is_lower = annotation.start_token.lemma.islower()

	for i in range(len(candidates)):
		features = {}
		features["quote_length"] = len(annotation.tokens)
		features["context_length"] = context.length
		features["number_names_in_context"] = number_of_names_in_context

		features["quote_rank"] = anno_rank
		features["candidate_name_in_quote"] = candidate_name_in_quote[i]
		features["annotation_is_split"] = annotation.is_split()
		features["first_word_in_quote_is_lower"] = first_word_is_lower

		quote_features.append(features)

	return quote_features



def get_all_features(text, annotation, candidates, context):
	distance_features = get_distance_features(text, annotation, candidates, context)
	candidate_features = get_candidate_features(text, annotation, candidates, context)
	quote_features = get_quote_features(text, annotation, candidates, context)

	all_lengths = [len(distance_features), len(candidate_features), len(quote_features)]

	if len(set(all_lengths)) != 1:
		print("Error! Cannot merge feature lists, don't have same lenghts")
		print("lenght distance: {}".format(len(distance_features)))
		print("lenght candidate: {}".format(len(candidate_features)))
		print("lenght quote: {}".format(len(quote_features)))
		return False
	else:
		all_features = []
		for i in range(len(candidates)):
			merged_features = {}
			merged_features.update(distance_features[i])
			merged_features.update(candidate_features[i])
			merged_features.update(quote_features[i])
			all_features.append(merged_features)
	return all_features

