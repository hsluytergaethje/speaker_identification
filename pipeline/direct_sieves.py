#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This scripts includes the sieves used in the direct system.
"""
from indirect_sieves import retrieve_speaker_from, get_base_context, get_context_before, get_context_after, get_candidates, \
binary_classifier_sieve, set_up_classifier, set_up_func_verbs, complete_speaker

EXTENDED_CANDIDATE_POS = ["NN", "NE", "PPER", "PIS", "PRELS", "PDS", "PPOSS"]

GENITIVE_TAG = "gmod"
#GENITIVE_TAG = "AG"

INT_FEATURES = True

def apply_sieves(text, sieves, functional_verb_path, classifier_path=None):
	set_up_func_verbs(functional_verb_path)

	if classifier_path is not None:
		set_up_classifier(classifier_path)

	for sieve in sieves:
		for annotation in text.annotations:
			if not annotation.has_speaker_prediction():
				speakers = sieve(text, annotation)
				annotation.predicted_speaker = complete_speaker(speakers, text)
				if annotation.has_speaker_prediction():
					annotation.predicted_by = str(sieve).split(" ")[1]


def apply_sieves_to_corpus(corpus, sieves):
	for text in corpus:
		apply_sieves(text, sieves)

"""
Trigram Matching Sieve: 
- check three different pattern consisting of candidate, verb cue, punctuation
and stw unit to assign the speaker
"""
def candidate_verb_punc_quote(token_list, check_subj=True):
	if len(token_list) == 3:
		# blub sie sagte
		if token_list[1].is_candidate() and token_list[2].is_speech_verb():
			if check_subj:
				if token_list[1].is_subject():
					return [token_list[1].id]
			else:
				return [token_list[1].id] 
		# sie sagte :
		elif token_list[0].is_candidate() and token_list[1].is_speech_verb() and token_list[2].text == ":":
			if check_subj:
				if token_list[0].is_subject():
					return [token_list[0].id]
			else:
				return [token_list[0].id]
	# Sie sagte
	elif len(token_list) == 2:
		if token_list[0].is_candidate() and token_list[1].is_speech_verb():
			if check_subj:
				if token_list[0].is_subject():
					return [token_list[0].id]
			else:
				return [token_list[0].id]
	return []

# token_list after quote
def quote_punc_verb_candidate(token_list, check_subj=True):
	if len(token_list) >= 2:
		# sagte sie
		if token_list[0].is_speech_verb() and token_list[1].is_candidate():
			if check_subj:
				if token_list[1].is_subject():
					return [token_list[1].id]
			else:
				return [token_list[1].id]
	if len(token_list) > 2:
		# , sagte sie
		if token_list[0].is_punctuation() and token_list[1].is_speech_verb() and token_list[2].is_candidate():
			if check_subj:
				if token_list[2].is_subject():
					return [token_list[2].id]
			else:
				return [token_list[2].id]
	return []

# token_list before quote
def verb_candidate_punc_quote(token_list, check_subj=True):
	if len(token_list) == 3:
		# dann sagte sie
		if token_list[1].is_speech_verb() and token_list[2].is_candidate():
			if check_subj:
				if token_list[2].is_subject():
					return [token_list[2].id]
			else:
				return [token_list[2].id]
		# sagte sie :
		elif token_list[0].is_speech_verb() and token_list[1].is_candidate() and token_list[2].text == ":":
			if check_subj:
				if token_list[1].is_subject():
					return [token_list[1].id]
			else:
				return [token_list[1].id]
	elif len(token_list) == 2:
		# sagte sie 
		if token_list[0].is_speech_verb() and token_list[1].is_candidate():
			if check_subj:
				if token_list[1].is_subject():
					return [token_list[1].id]
			else:
				return [token_list[1].id]
	return []


def trigram_matching_sieve(text, annotation, context=None):
	speakers = []

	# check context inbetween quote first
	contexts_inbetween = []
	if annotation.is_split():
		tokens_between_anno = text.get_token_lists_between_annotation_slices(annotation)
		contexts_inbetween.extend([token_list.tokens for token_list in tokens_between_anno])

	if len(contexts_inbetween) > 0:
		for context in contexts_inbetween:
			speakers.extend(quote_punc_verb_candidate(context))
	
	if len(speakers) < 1:
		context_before = text.get_previous_tokens(annotation.start_token, 3)
		context_after = text.get_next_tokens(annotation.end_token, 3)
	
		speaker = candidate_verb_punc_quote(context_before)
		if len(speaker) == 0:
			speaker = quote_punc_verb_candidate(context_after)
			if len(speaker) == 0:
				speaker = verb_candidate_punc_quote(context_before)
		speakers.extend(speaker) 
	return speakers


# Trigram matching sieve without subject checking
def loose_trigram_matching_sieve(text, annotation):
	speakers = []

	# check context inbetween quote first
	contexts_inbetween = []
	if annotation.is_split():
		tokens_between_anno = text.get_token_lists_between_annotation_slices(annotation)
		contexts_inbetween.extend([token_list.tokens for token_list in tokens_between_anno])

	if len(contexts_inbetween) > 0:
		for context in contexts_inbetween:
			speakers.extend(quote_punc_verb_candidate(context, check_subj=False))
	
	if len(speakers) < 1:
		context_before = text.get_previous_tokens(annotation.start_token, 3)
		context_after = text.get_next_tokens(annotation.end_token, 3)
	
		speaker = candidate_verb_punc_quote(context_before, check_subj=False)
		if len(speaker) == 0:
			speaker = quote_punc_verb_candidate(context_after, check_subj=False)
			if len(speaker) == 0:
				verb_candidate_punc_quote(context_before, check_subj=False)
		speakers.extend(speaker) 
	return speakers


"""
Dependency Sieve
- attribute speaker to the subject of the closest verb cue, 
if the subject is a candidate
"""
def search_speech_verb_candidate_in_context(context):
	speakers = []
	for i, token in enumerate(context):
		if token.is_speech_verb():
			for dependent_tok in context[i-3:i+4]:
				if dependent_tok.is_candidate() and not dependent_tok.is_annotated and dependent_tok.is_subject():
					speakers.append(dependent_tok)
	return speakers

# speaker are tokens
def get_closest_speaker(text, speakers, annotation):
	distances = []
	for speaker_list in speakers:
		least_dist = min([text.get_distance_tok_anno(tok, annotation) for tok in speaker_list])
		distances.append(least_dist)
		
	closest_speaker_index = distances.index(min(distances))
	return speakers[closest_speaker_index]

# Do not consider context after stw unit if ends with a colon
def filter_context_after_annotation(text, context_after):
	sentence_after = text.get_sentences_by_ids([context_after[0].id])[0]
	end_token = text.get_tokens_by_id([sentence_after.end])
	if end_token.text == ":":
		new_context = [token for token in context_after if token not in sentence_after.tokens]
		return new_context
	return context_after

# apply dependency pattern
def dependency_sieve(text, annotation, loose=False):
	contexts_to_check = []

	if annotation.is_split():
		tokens_between_anno = text.get_token_lists_between_annotation_slices(annotation)
		contexts_to_check.extend([token_list.tokens for token_list in tokens_between_anno])

	# if annotation is first, we still want tokens before
	if annotation.id == 0:
		contexts_to_check.append(text.get_previous_tokens(annotation.start_token, 40))
	else:
		contexts_to_check.append(text.get_tokens_between_current_and_before(annotation)[-40:])

	if annotation.id == text.annotations[-1].id:
		contexts_to_check.append(text.get_next_tokens(annotation.end_token, 40))
	else:
		contexts_to_check.append(text.get_tokens_between_current_and_after(annotation)[:40])
	
	if not loose: 
		return retrieve_speaker_from(contexts_to_check, text, annotation, check_predicted=True)
	else:
		return retrieve_speaker_from(contexts_to_check, text, annotation, check_candidate=False, check_predicted=True)

# Do not check if the subject of the closest verb is a candidate
def loose_dependency_sieve(text, annotation):
	speaker_ids = dependency_sieve(text, annotation, loose=True)
	
	if len(speaker_ids) == 1:
		actual_speakers = []
		speaker_token = text.get_tokens_by_id(speaker_ids)[0]
		if not speaker_token.is_candidate():
			children = text.get_direct_children(speaker_token)
			for child in children:
				if child.dependency == GENITIVE_TAG:
					if child.is_candidate():
						actual_speakers.append(child.id)
			if len(actual_speakers) > 0:
				return actual_speakers
	return speaker_ids

"""
Colon Sieve
If context before the stw unit ends with a colon, 
identify the subject of the context as speaker
"""
def colon_sieve(text, annotation, check_annotated=False):
	token_id_before_anno = annotation.start_id - 1
	if token_id_before_anno >= 0:
		tokens_before_anno = text.get_tokens_by_id([token_id_before_anno])
		if len(tokens_before_anno) == 1:
			token_before_anno = tokens_before_anno[0]
			if token_before_anno.text == ":":
				colon_sentence = text.get_sentences_by_ids([token_before_anno.sentence_id])[0]
				context = [token for token in colon_sentence.tokens if token.id < token_before_anno.id]
				subjects = [token for token in context if token.is_subject()]
				# checking the pos made it worse    
				#subjects = [token for token in subjects if token.pos in EXTENDED_CANDIDATE_POS and token.text != "es"]
				if check_annotated	:
					subjects = [token for token in subjects if (token.text != "es") and (not token.is_annotated)]
				else:
					subjects = [token for token in subjects if token.text != "es"]
				if len(subjects) > 0:
					distances = [text.get_distance_tok_anno(tok, annotation) for tok in subjects]
					smallest_distance = min(distances)
					closest_subject = subjects[distances.index(smallest_distance)]
					return [closest_subject.id]
	return []


"""
Adjacent-STW-Sieve
If current stw unit starts with a lower cased character, 
attribute speaker of unit before to the current unit 
"""
def adjacent_quote_sieve(text, annotation):
	if annotation.start_token.text.islower():
		anno_before = text.get_previous_anno_by_distance(annotation, 1)
		if text.get_distance_between_annotations(anno_before, annotation) < 7:
			if anno_before.has_speaker_prediction():
				return anno_before.predicted_speaker
	return []



"""
Single Candidate sieve
If context only includes one candidate, attribute the stw unit 
to the candidate
"""
def retrieve_candidates(text, context, annotation):
	candidates = [token for token in context if token.is_candidate()]				
	return candidates

# is too errorprone, since almost always finds speaker (not correct one)
def closest_candidate_sieve(text, annotation, contexts=None):
	if contexts is None:
		contexts = []
		contexts.extend(get_base_context(annotation, text))
		contexts.extend(get_context_before(annotation, text, 1))
		contexts.extend(get_context_after(annotation, text, 1))

	candidates = get_candidates(contexts, check_subj=True, check_annotated=True)
	if len(candidates) > 0:
		distances = [text.get_distance_tok_anno(candidate, annotation) for candidate in candidates]
		index_closest = distances.index(min(distances))
		return [candidates[index_closest].id]
	return []


def single_candidate_sieve(text, annotation, window=40):
	contexts_to_check = []

	if annotation.id == 0:
		contexts_to_check.extend(text.get_previous_tokens(annotation.start_token, window))
	else:
		contexts_to_check.extend(text.get_tokens_between_current_and_before(annotation)[-window:])

	if annotation.id == text.annotations[-1].id:
		contexts_to_check.extend(text.get_next_tokens(annotation.end_token, window))
	else:
		contexts_to_check.extend(text.get_tokens_between_current_and_after(annotation)[:window])
	
	candidates = retrieve_candidates(text, contexts_to_check, annotation)

	if len(candidates) == 1:
		speaker_id = [candidates[0].id]
	else:
		speaker_id = []
	return speaker_id

# is less secure than other single mention sieve, since context is less wide    
# is not restrictive enough, recall is shite
def single_mention_sieve_limited(text, annotation):
	return single_mention_sieve(text, annotation, window=15)

"""
Vocative-Sieve
If stw unit before or after current unit has a vocative, attribute 
current unit to the vocative
""" 
def vocative_detection_sieve(text, annotation):
	anno_before = text.get_previous_anno_by_distance(annotation, 1)
	anno_after = text.get_next_anno_by_distance(annotation, 1)
	
	vocatives = []
	
	if anno_before is not None:
		#distance = text.get_distance_between_annotations(annotation, anno_before)
		#if distance > 0 and distance < 5:

		if anno_before.has_vocative():
			vocatives = anno_before.get_vocatives()
			
	# prefer context before
	if len(vocatives) == 0 and anno_after is not None:
		#distance = text.get_distance_between_annotations(annotation, anno_after)
		#if distance > 0 and distance < 5:  
		if anno_after.has_vocative():
			vocatives = anno_after.get_vocatives()

	if len(vocatives) == 1:
		vocative_tok_ids = [tok.id for tok in vocatives]
		return vocative_tok_ids
	return []


"""
Conversational Sieve
If two stw unit before or after the current unit is in conversation
with the current unit, attribute the speaker to the one of the other 
unit
"""
def conversational_sieve(text, annotation):
	anno_after = text.get_next_anno_by_distance(annotation, 2)
	anno_before = text.get_previous_anno_by_distance(annotation, 2)
	if anno_before is not None:
		if text.check_if_in_conversation(annotation, anno_before) and anno_before.has_speaker_prediction():
			return anno_before.predicted_speaker
	if anno_after is not None:
		if text.check_if_in_conversation(annotation, anno_after) and anno_after.has_speaker_prediction():
			return anno_after.predicted_speaker
	return []


"""
Loose conversational Sieve
Similar to conversational sieve. Looser understanding of "in conversation".
Several tokens can be inbetween stw units. 
"""
def loose_conversational_pattern(text, annotation):
	anno_after = text.get_next_anno_by_distance(annotation, 2)
	anno_before = text.get_previous_anno_by_distance(annotation, 2)
	if anno_before is not None: 
		if anno_before.has_speaker_prediction():
			return anno_before.predicted_speaker
	if anno_after is not None:
		if anno_after.has_speaker_prediction():
			return anno_after.predicted_speaker
	return []


"""
Continuous STW Sieve
Apply pattern matching to check if stw unit before 
has the same speaker as the current unit. If so, attribute to 
speaker before. 
"""
def continuous_quote_sieve(text, annotation, distance=5):
    next_anno = text.get_next_anno_by_distance(annotation, 1)
    if next_anno is not None:
        if text.get_distance_between_annotations(annotation, next_anno) <= 1:
            previous_anno = text.get_previous_anno_by_distance(annotation, 1)
            if previous_anno is not None:
                if text.get_distance_between_annotations(previous_anno, annotation) <= distance:
                    if previous_anno.has_speaker_prediction():
                        tokens_inbetween = text.get_tokens_between_two_annos(previous_anno, annotation)
                        speaker_tokens = text.get_tokens_by_id(previous_anno.predicted_speaker)
                        if all(speaker_token in tokens_inbetween for speaker_token in speaker_tokens):
                            if any(token.is_speech_verb() for token in tokens_inbetween):
                                return previous_anno.predicted_speaker
    return []

