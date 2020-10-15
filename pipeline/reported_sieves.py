#!/usr/bin/python
# -*- coding: utf-8 -*-

""" 
This scripts includes the sieves used in the reported system.
"""

import sys
from Text import read_word_list
from indirect_sieves import get_speech_verbs, get_base_context, get_context_before, get_context_after, recursive_subj_search
from indirect_sieves import get_closest_verb, get_verbs, get_actual_verb, get_functional_verb_cues, binary_classifier_sieve, \
set_up_classifier, set_up_func_verbs, complete_speaker


INT_FEATURES = True
GENITIVE_TAG = "gmod"


"""
Retrieve speaker candidates in dependency relation of a verb.
"""
def get_candidate_from_verb(text, verb, annotation, check_candidate=True, check_predicted=False):
	candidates = []
	children = text.get_direct_children(verb)

	if not any(child.is_subject() for child in children):
		children = recursive_subj_search(text, verb)


	for child in children: 
		if check_candidate and check_predicted:
			if child.is_candidate(pis=True) and (not text.is_predicted_speaker_of_annotation_before(child, annotation)) \
			and (not text.is_predicted_speaker_of_annotation_after(child, annotation)) and child.is_subject():
				candidates.append(child.id)
		elif check_candidate:
			if child.is_candidate(pis=True) and child.is_subject():
				candidates.append(child.id)
		elif check_predicted:
			if not text.is_predicted_speaker_of_annotation_before(child, annotation) \
			and (not text.is_predicted_speaker_of_annotation_after(child, annotation)) and child.is_subject():
				if child.pos in CANDIDATE_POS_EXTENDED and child.lemma not in TO_EXCLUDE:
					candidates.append(child.id)
		else:
			if child.is_subject():
				candidates.append(child.id)

	return candidates

"""
Returns the children of a given token with the help 
of dependency relations.
"""
def get_all_children_recursive(text, token, visited):
	if token not in visited:
		visited.append(token)
		children = text.get_direct_children(token)
		for child in children:
			get_all_children_recursive(text,child, visited)
	return visited


"""
Extracts a list of candidates from a given context.
"""
def get_candidates(contexts, check_subj=False, check_annotated=False):
	candidates = []
	for context in contexts:
		if check_subj and check_annotated:
			candidates.extend([token for token in context if token.is_candidate(pis=True) and token.is_subject() and (not token.is_annotated)])
		elif check_subj:
			candidates.extend([token for token in context if token.is_candidate(pis=True) and token.is_subject()])
		elif check_annotated:
			candidates.extend([token for token in context if token.is_candidate(pis=True) and (not token.is_annotated)])
		else:
			candidates.extend([token for token in context if token.is_candidate(pis=True)])
	return candidates

"""
Sort verbs by distance to stw unit. 
"""
def sort_verbs_by_distance(verb_list, annotation, text):
	distances_indice = [(text.get_distance_tok_anno(verb_cue, annotation), i) for i,verb_cue in enumerate(verb_list)]
	sorted_distances = sorted(distances_indice)
	sorted_verbs = [verb_list[i] for dist, i in sorted_distances]
	return sorted_verbs

"""
Retrieves the speaker in dependence of the verb cue 
closest to a given stw unit
"""
def retrieve_speaker_from(contexts, text, annotation, check_candidate=True, check_predicted=False):
	speakers = []
	speech_verbs = get_speech_verbs(contexts)
	functional_verbs = get_functional_verb_cues(text, contexts)
	verb_cues = speech_verbs + functional_verbs 

	closest_verb = get_closest_verb(verb_cues, text, annotation)
	if closest_verb is None:
		return []
	else:
		return get_candidate_from_verb(text, closest_verb, annotation, check_candidate)


"""
Single Candidate sieve
If context only includes one candidate, attribute the stw unit 
to the candidate
"""
def single_candidate_sieve_reported(text, annotation, contexts):
	candidates = get_candidates(contexts)
	if len(candidates) == 1:
		return [candidates[0].id]
	return []


"""
Single Speech Noun sieve
If context only includes one speech noun, attribute the stw unit 
to the possessive pronoun depending on the speech noun. If no
possessive pronoun present, attribute to "none-speaker"
"""

def get_speech_nouns(contexts):
	speech_nouns = [token for context in contexts for token in context if token.lemma in SPEECH_NOUNS]
	return speech_nouns


def single_speech_noun_sieve(text, annotation, contexts):
	candidates = get_candidates(contexts)
	if len(candidates) == 0:
		speech_nouns = get_speech_nouns(contexts)
		if len(speech_nouns) == 1:
			possessive = get_possessive_subj(text, speech_nouns[0])
			if possessive != speech_nouns[0]:
				return [possessive.id]
			else:
				return [-1]
	return []  


def speech_noun_genitive_object_sieve(text, annotation, contexts):
	speech_nouns = get_speech_nouns(contexts)
	speakers = []
	if len(speech_nouns) == 1:
		children = text.get_direct_children(speech_nouns[0])
		for child in children:
			if child.dependency == GENITIVE_TAG:
				if child.is_candidate():
					speakers.append(child.id)
	return speakers

"""
Passive Sieve
If retrieved speech verb is in a passive voice, attrbute 
speaker to prepositional object, else attribute to none-speaker
"""
def passive_sieve(text, annotation, contexts):
	speech_verbs = get_speech_verbs(contexts, correct=False)
	functional_verbs = get_functional_verb_cues(text, contexts)
	verb_cues = speech_verbs + functional_verbs

	if len(verb_cues) == 1:
		speech_verb = verb_cues[0]
		actual_verb = get_actual_verb(speech_verb)
		if actual_verb is not None:
	
			if actual_verb.lemma == "werden" and speech_verb.pos == "VVPP":
				all_children = get_all_children_recursive(text, speech_verb, [])

				# get prepositional object 
				pns = [tok for tok in all_children if tok.dependency == "pn"]
				filtered = [tok for tok in pns if tok.parent_token.dependency == "pp"]

				candidates = []
				if len(filtered) > 0:
					for token in filtered:
						if token.is_candidate():
							candidates.append(token)
				else:
					return [-1]
				
				if len(candidates) == 1:
					return [candidates[0].id]
				else:
					return [-1]
	return []


"""
STW dependency sieve
If single verb cue exists in stw unit, attribute speaker 
to the subject of the verb, if subject is a candidate. 
"""
def stw_depedency_sieve(text, annotation, contexts):
	speech_verbs = get_speech_verbs(contexts)
	functional_verbs = get_functional_verb_cues(text, contexts)

	verb_cues = speech_verbs + functional_verbs 

	if len(verb_cues) == 1:
		predicted_speaker_ids = get_candidate_from_verb(text, verb_cues[0], annotation)
		additions = complete_speaker(predicted_speaker_ids, text)
		return additions
	else:
		candidates_list = [tuple(get_candidate_from_verb(text, verb, annotation)) for verb in verb_cues]
		# if all candidate lists in the candidate_list are the same we continue 
		if len(set(candidates_list)) == 1:
			#assert(type(candidates_list[0]) == tuple)
			additions = complete_speaker(list(candidates_list[0]), text)
			return additions    
	return [] 


"""
Loose STW Depedency Sieve for annotation as context.
Same as stw depedency sieve, only that children don't have to be candidates
"""
def stw_dependency_sieve_loose(text, annotation, contexts):
	speech_verbs = get_speech_verbs(contexts)
	functional_verbs = get_functional_verb_cues(text, contexts)

	verb_cues = speech_verbs + functional_verbs 

	if len(verb_cues) == 1:
		predicted_speaker_ids = get_candidate_from_verb(text, verb_cues[0], annotation, check_candidate=False)
		additions = complete_speaker(predicted_speaker_ids, text)
		return additions
	else:
		# check if both point to same tok
		candidates_list = [tuple(get_candidate_from_verb(text, verb, annotation, check_candidate=False)) for verb in verb_cues]
		if len(set(candidates_list)) == 1:
			additions = complete_speaker(list(candidates_list[0]), text)
			return additions  
	return [] # speaker cannot be determined


"""
Dependency Sieve
Attribute speaker to the subject of the closest verb cue, 
if the subject is a candidate
"""
def dependency_sieve_reported(text, annotation, contexts):
	return retrieve_speaker_from(contexts, text, annotation)

def depencency_sieve_loose_reported(text, annotation, contexts):
	return retrieve_speaker_from(contexts, text, annotation, check_candidate=False)


"""
Single subj sieve
Attribute speaker to subject if it is the single subject
in a given context
"""
def get_subjs(contexts):
	subj = []
	for context in contexts:
		subj.extend([token for token in context if token.is_subject()])
	return subj

# check if direct child is "det"
# and has PoS PPOSAT
def get_possessive_subj(text, subj_token):
	if not subj_token.is_candidate(pis=True):
		children = text.get_direct_children(subj_token)
		if any(child.dependency == "det" for child in children):
			for child in children:
				if child.dependency == "det" and child.pos == "PPOSAT":
					return child
	return subj_token


def single_subj_sieve(text, annotation, contexts):
	subjs = get_subjs(contexts)
	if len(subjs) == 1:
		checked_subj = get_possessive_subj(text, subjs[0])
		if not checked_subj.lemma in SPEECH_NOUNS:
			return [checked_subj.id]
	return []

def single_subj_sieve_strict(text, annotation, contexts):
	subjs = get_subjs(contexts)
	if len(subjs) == 1:
		subj = subjs[0]
		if subj.is_candidate():
			additions = complete_speaker([subj.id], text)
			return additions
	return []

def get_i_token(contexts):
	i_token = ["ich", "mich"]
	i_token_in_context = [token  for context in contexts for token in context \
	if token.lemma in i_token]
	return i_token_in_context

"""
STW I sieve
Attribute speaker to "I" in the stw unit, if there is only a single mention in the
stw unit. 
"""
def stw_i_sieve(text, annotation, contexts):
	i_token = get_i_token(contexts)
	if len(i_token) == 1:
		return [i_token[0].id]
	return []

"""
Closest Subject Sieve
Attribute speaker to the closest subject, if 
it is a candidate 
"""
def closest_subj_sieve(text, annotation, contexts, check_candidate=True):
	subjs = get_subjs(contexts)
	if len(subjs) > 0:
		distances = [text.get_distance_tok_anno(subj, annotation) for subj in subjs]
		index_closest = distances.index(min(distances))
		closest_subj = subjs[index_closest]
		if check_candidate:
			if closest_subj.is_candidate():
				return [closest_subj.id]
		else:
			return [closest_subj.id]
	return []


"""
APPLY SIEVES
"""
def apply_sieves_reported(text, anno_sieves, sieves, functional_verb_path, speech_noun_file, classifier_path):
	global SPEECH_NOUNS
	SPEECH_NOUNS = read_word_list(speech_noun_file)

	set_up_func_verbs(functional_verb_path)

	if classifier_path is not None:
		set_up_classifier(classifier_path)

	if text.annotation_number > 0:
		for annotation in text.annotations:
			# first search speaker in annotation
			for anno_sieve in anno_sieves:
				if not annotation.has_speaker_prediction():
					speakers = anno_sieve(text, annotation, [annotation.tokens])
					annotation.predicted_speaker = complete_speaker(speakers, text)
					if annotation.has_speaker_prediction():
						annotation.predicted_by = str(anno_sieve).split(" ")[1]

			
			if not annotation.has_speaker_prediction():
				all_contexts = []
				all_contexts.append(get_base_context(annotation, text))
				all_contexts.append(get_context_before(annotation, text, 2)) # how many? 
				all_contexts.append(get_context_after(annotation, text, 1))
				for contexts in all_contexts:
					if not annotation.has_speaker_prediction():
						for sieve in sieves:
							if not annotation.has_speaker_prediction():
								speakers = sieve(text, annotation, contexts)
								annotation.predicted_speaker = complete_speaker(speakers, text)
								if annotation.has_speaker_prediction():
									annotation.predicted_by = str(sieve).split(" ")[1]

			if annotation.has_speaker_prediction() and annotation.predicted_speaker[0] == -1:
				annotation.predicted_speaker = []


def apply_sieves_to_corpus_reported(corpus, anno_sieves, sieves):
	for text in corpus:
		apply_sieves_reported(text, anno_sieves, sieves)


