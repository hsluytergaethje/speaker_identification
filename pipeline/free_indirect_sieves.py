#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This siebes include the sieves for the free indirect system
"""
from indirect_sieves import get_context_before, get_context_after, dependency_sieve_indirect, get_candidates, complete_speaker

"""
Closest speaking candidate sieve
Attribute the speaker to the closest speaking candidate
to the stw unit. 
"""
def closest_speaking_candidate(text, annotation, distance=4):
	contexts = get_context_before(annotation, text, distance)
	return dependency_sieve_indirect(text, annotation, contexts)

"""
Strict version of the closest speaking candidate sieve, only 
consider one sentence. 
"""
def closest_speaking_candidate_strict(text, annotation):
	return closest_speaking_candidate(text, annotation, distance=1)

"""
Closest candidate before stw unit
Attributes the speaker to the closest candidate in front of stw unit
that is also a subject 
"""

def closest_candidate_sieve_before(text, annotation, distance=4):
    contexts = get_context_before(annotation, text, distance)

    candidates = get_candidates(contexts, check_subj=True)
    if len(candidates) > 0:
        distances = [text.get_distance_tok_anno(candidate, annotation) for candidate in candidates]
        index_closest = distances.index(min(distances))
        return [candidates[index_closest].id]
    return []

def closest_candidate_sieve_before_strict(text, annotation):
	return closest_candidate_sieve_before(text, annotation, distance=1)


"""
Closest candidate after stw unit
Attributes the speaker to the closest candidate after stw unit
that is also a subject 
"""
def closest_candidate_sieve_after(text, annotation):
    contexts = get_context_after(annotation, text, 1)
    candidates = get_candidates(contexts, check_subj=True)
    if len(candidates) > 0:
        distances = [text.get_distance_tok_anno(candidate, annotation) for candidate in candidates]
        index_closest = distances.index(min(distances))
        return [candidates[index_closest].id]
    return []

"""
Loose closest candidate
Attrubute speaker to closest candidate, don't need to be subject
"""
def loose_closest_candidate_sieve(text, annotation):
    contexts = get_context_before(annotation, text, 1)
    candidates = get_candidates(contexts)
    if len(candidates) > 0:
        distances = [text.get_distance_tok_anno(candidate, annotation) for candidate in candidates]
        index_closest = distances.index(min(distances))
        return [candidates[index_closest].id]
    return []


"""
Question Sieve
Attribute speaker to subject of the question 
within the stw unit. 
"""
question_words = ["wie", "wo", "was", "wann", "wieso", "warum", "weshalb"]
def is_question(sentence):
    return sentence[-1].text == "?"


def get_candidates_per_context(contexts, check_subj=False):
    candidates = []
    for context in contexts:
        if not check_subj:
            candidates.append([token for token in context if token.is_candidate()])
        else:
            candidates.append([token for token in context if token.is_candidate() and token.is_subject()])
    return candidates


def question_sieve(text, annotation):
    sentences = text.get_sentences_including_annotation(annotation)
    question_sentences = [sentence.tokens for sentence in sentences if is_question(sentence.tokens)]
    if len(question_sentences) > 0:
        candidates = get_candidates_per_context(question_sentences, check_subj=True)
        # if several sentence within quote are question
        # if several question have candidates, take candidates from first question
        if len(candidates) > 0:
            speakers = [token.id for token in candidates[0]]
            return speakers
    return []


"""
Neighboring Sieve
Attribute speaker to speaker of neighbouring stw unit.  
"""
def get_sentence_distance(anno_1, anno_2):
    if anno_1.end_id < anno_2.start_id:
        return anno_2.start_token.sentence_id - anno_1.end_token.sentence_id
    elif anno_2.end_id < anno_1.start_id:
        return anno_1.start_token.sentence_id - anno_2.end_token.sentence_id
    else:
        return 0

# could adjust distance here 
def get_speaker_from_neighboring_instance(annotation, neighbor, max_dist=5):
    if neighbor.has_speaker_prediction():
        distance = get_sentence_distance(annotation, neighbor)
        if distance < max_dist:
            return neighbor.predicted_speaker
    return []

def neighbouring_instance_sieve(text, annotation):
    neighbors = []
    neighbors.append(text.get_previous_anno_by_distance(annotation, 1))
    neighbors.append(text.get_next_anno_by_distance(annotation, 1))
    if len(neighbors) > 0: 
        # prefer context of annotation before 
        for neighbor in neighbors:
            if neighbor is not None:
                speakers = get_speaker_from_neighboring_instance(annotation, neighbor)
                if len(speakers) > 0:
                    return speakers
    return []


"""
APPLY SIEVES
"""
def apply_sieves_freeIndirect(text, sieves):
    if text.annotation_number > 0:
        for sieve in sieves:
            for annotation in text.annotations:
                if not annotation.has_speaker_prediction():
                    speakers = sieve(text, annotation)
                    annotation.predicted_speaker = complete_speaker(speakers, text)
                    if annotation.has_speaker_prediction():
                        annotation.predicted_by = str(sieve).split(" ")[1]


def apply_sieves_to_corpus_freeIndirect(corpus, sieves):
    for text in corpus:
        apply_sieves_freeIndirect(text, sieves)
