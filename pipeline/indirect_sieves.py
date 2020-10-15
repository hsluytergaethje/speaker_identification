#!/usr/bin/python
# -*- coding: utf-8 -*-

from prepare_text_binary_classifier import get_features_representation_per_annotation
from read_write_helper import load_pickled_data
from Text import read_word_list

INT_FEATURES = True

def read_word_tuples(input_file):
    word_pairs = {}
    with open(input_file, 'r') as in_file:
        for line in in_file.readlines():
            line = line.strip().split(" ")
            noun = line[0]
            verb = line[1]
            if verb not in word_pairs:
                word_pairs[verb] = [noun]
            else:
                word_pairs[verb].append(noun)
    return word_pairs

CANDIDATE_POS_EXTENDED = ["NN", "NE", "PPER", "PIS", "PRELS"]
VERB_POS = ["VVFIN", "VVPP", "VVINF", "VAINF", "VVIZU", "VAFIN", "VMFIN"]
TO_EXCLUDE = ["es"]
FUNCTIONAL_NOUN_TAG = ["pn", "obja"]

# load classifier model
def set_up_classifier(classifier_path):
    global BINARY_CLASSIFIER
    BINARY_CLASSIFIER = load_pickled_data(classifier_path)
    
# load functional verb cue list
def set_up_func_verbs(functional_verb_path):
    global FUNCTIONAL_VERB_CONSTRUCSTIONS
    FUNCTIONAL_VERB_CONSTRUCSTIONS = read_word_tuples(functional_verb_path)

# get sentence of stw unit
def get_base_context(annotation, text, after=False):
    contexts_to_check = []
    if annotation.is_split():
        tokens_between_anno = text.get_token_lists_between_annotation_slices(annotation)
        contexts_to_check.extend([token_list.tokens for token_list in tokens_between_anno])
    # expect sentences to have length 1 -> annotation guidelines
    sentences = text.get_sentences_including_annotation(annotation)
    
    token_ids_before = [i for i in range(sentences[0].start, annotation.start_id)]
    tokens_before_quote = text.get_tokens_by_id(token_ids_before)
    contexts_to_check.append(tokens_before_quote)
   
    if after:
        token_ids_after = [i for i in range(annotation.end_id, sentences[-1].end)]
        tokens_after_quote = text.get_tokens_by_id(token_ids_after)
        contexts_to_check.append(tokens_after_quote)

    return contexts_to_check

def get_context_before(annotation, text, sen_number_before):
    contexts_to_check = get_base_context(annotation, text)
    
    sentences = text.get_sentences_including_annotation(annotation)
    sentences_before = text.get_sentences_before(sentences[0], sen_number_before)
    for sentence in sentences_before:
        contexts_to_check.append(sentence.tokens)
    return contexts_to_check

def get_context_after(annotation, text, sen_number_after):
    contexts_to_check = get_base_context(annotation, text, after=True)
    
    sentences = text.get_sentences_including_annotation(annotation)
    sentences_after = text.get_sentences_after(sentences[-1], sen_number_after)
    for sentence in sentences_after:
        contexts_to_check.append(sentence.tokens)
    return contexts_to_check


def match_token_list_pattern(token_list, ignore_tok_is_annotated=False):
    if any(token.is_speech_verb() for token in token_list) and any(token.is_candidate() for token in token_list):
        for token in token_list:
            if ignore_tok_is_annotated:
                if token.is_candidate():
                    return token
            else:
                if token.is_candidate() and not token.is_annotated:
                    return token
    return None

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

# checks if a verb is part of a functional noun-verb construction
def is_functional_verb_cue(text, actual_verb, function_verb):
    all_children = get_all_children_recursive(text, actual_verb, [])
    for child in all_children:
        if child.dependency in FUNCTIONAL_NOUN_TAG:
            if child.lemma in FUNCTIONAL_VERB_CONSTRUCSTIONS[function_verb.lemma]:
                return True
    return False

# extract functional noun-verb constructions from context
def get_functional_verb_cues(text, contexts):
    verb_cues= []
    verbs = get_verbs(contexts, correct=False)
    if any(verb.lemma in FUNCTIONAL_VERB_CONSTRUCSTIONS for verb in verbs):
        for verb in verbs:
            if verb.lemma in FUNCTIONAL_VERB_CONSTRUCSTIONS:
                actual_verb = get_actual_verb(verb)
                if actual_verb is not None:
                    if is_functional_verb_cue(text, actual_verb, verb):
                        verb_cues.append(actual_verb)
    return verb_cues

# extract verb cues from context
def get_speech_verbs(contexts, correct=True):
    speech_verb_candidates = []
    
    for context in contexts:
        if any(token.is_speech_verb() for token in context):
            speech_verb_candidates.extend([token for token in context if token.is_speech_verb()])
    if correct:
        actual_verbs = [get_actual_verb(verb) for verb in speech_verb_candidates]
        speech_verbs = [verb for verb in actual_verbs if verb is not None]
    else:
        speech_verbs = speech_verb_candidates
    return speech_verbs

# extract closest verb to stw unit
def get_closest_verb(verbs, text, annotation):
    if len(verbs) > 1:
        distances = [text.get_distance_tok_anno(verb_cue, annotation) for verb_cue in verbs]
        index_closest = distances.index(min(distances))
        closest_verb = verbs[index_closest]
    elif len(verbs) == 1:
        closest_verb = verbs[0]
    else:
        closest_verb = None
    return closest_verb

"""
Trigram sieve -- looser version
Attribute speaker subject within short context before and after the stw unit
"""
def trigram_sieve_indirect(text, annotation, context=None):
    contexts_to_check = []
    if annotation.is_split():
        tokens_between_anno = text.get_token_lists_between_annotation_slices(annotation)
        contexts_to_check.extend([token_list.tokens for token_list in tokens_between_anno])
    contexts_to_check.append(text.get_previous_tokens(annotation.start_token, 4))
    
    speakers = []
    for context in contexts_to_check:
        speaker = match_token_list_pattern(context, ignore_tok_is_annotated = True)
        if speaker is not None:
            speakers.append(speaker.id)
    return speakers

"""
Search children of verbs recusively to get subject
"""
def recursive_subj_search(text, token):
    children = text.get_direct_children(token)
    if any(child.is_subject() for child in children):
        return [child for child in children if child.is_subject()]
    else:
        if token.parent_token.id == token.id:
            return []
        else:
            return recursive_subj_search(text, token.parent_token)

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
            if child.is_candidate() and (not text.is_predicted_speaker_of_annotation_before(child, annotation)) \
            and (not text.is_predicted_speaker_of_annotation_after(child, annotation)) and child.is_subject():
                candidates.append(child.id)
        elif check_candidate:
            if child.is_candidate() and child.is_subject():
                candidates.append(child.id)
        elif check_predicted:
            if not text.is_predicted_speaker_of_annotation_before(child, annotation) \
            and (not text.is_predicted_speaker_of_annotation_after(child, annotation)) and child.is_subject():
                if child.pos in CANDIDATE_POS_EXTENDED and child.lemma not in TO_EXCLUDE:
                    candidates.append(child.id)
        else:
            if child.is_subject():
                #if child.pos in CANDIDATE_POS_EXTENDED and child.lemma not in TO_EXCLUDE:
                candidates.append(child.id)

    return candidates

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
        return get_candidate_from_verb(text, closest_verb, annotation, check_candidate, check_predicted)


"""
Dependency Sieve
Attribute speaker to the subject of the closest verb cue, 
if the subject is a candidate
"""
def dependency_sieve_indirect(text, annotation, contexts):
    return retrieve_speaker_from(contexts, text, annotation)


"""
Loose Dependency Sieve
Attribute speaker to the subject of the closest verb cue
"""
def depencency_sieve_loose_indirect(text, annotation, contexts):
    return retrieve_speaker_from(contexts, text, annotation, check_candidate=False)

def get_actual_verb(verb):
    if verb.dependency == "aux":
        if verb.parent_token.pos in VERB_POS:
            return verb.parent_token
        return None
    else:
        return verb

def get_verbs(contexts, correct=True):
    verbs = []
    for context in contexts:
        verbs.extend([token for token in context if token.pos in VERB_POS])
    if correct:
        actual_verbs = [get_actual_verb(verb) for verb in verbs]
        corrected_verbs = [verb for verb in actual_verbs if verb is not None]
    else:
        corrected_verbs = verbs
    return corrected_verbs

"""
Single verb sieve
if only one verb in predefined context, attribute
speaker to subject of the verb

"""
def single_verb_sieve(text, annotation, contexts):
    verbs = get_verbs(contexts)
    if len(verbs) == 1:
        return get_candidate_from_verb(text, verbs[0], annotation, check_candidate=False)
    return []


def get_candidates(contexts, check_subj=False, check_annotated=False):
    candidates = []
    for context in contexts:
        if check_subj and check_annotated:
            candidates.extend([token for token in context if token.is_candidate() and token.is_subject() and (not token.is_annotated)])
        elif check_subj:
            candidates.extend([token for token in context if token.is_candidate() and token.is_subject()])
        elif check_annotated:
            candidates.extend([token for token in context if token.is_candidate() and (not token.is_annotated)])
        else:
            candidates.extend([token for token in context if token.is_candidate()])
    return candidates


"""
Single Candidate sieve
If context only includes one candidate, attribute the stw unit 
to the candidate
"""
def single_candidate_sieve_indirect(text, annotation, contexts):
    candidates = get_candidates(contexts)
    if len(candidates) == 1:
        return [candidates[0].id]
    return []

"""
Closest Verb sieve
Attribute speaker to the subject of the closest verb to the 
stw unit. 
"""
def closest_verb_sieve(text, annotation, contexts):
    verbs = get_verbs(contexts)
    closest_verb = get_closest_verb(verbs, text, annotation)
    if closest_verb is None:
        return []
    else:
        return get_candidate_from_verb(text, closest_verb, annotation, check_candidate=False)


def get_subjs(contexts):
    subj = []
    for context in contexts:
        subj.extend([token for token in context if token.is_subject()])
    return subj


def get_possessive_subj(text, subj_token):
    if not subj_token.is_candidate(pis=True):
        children = text.get_direct_children(subj_token)
        if any(child.dependency == "det" for child in children):
            for child in children:
                if child.dependency == "det" and child.pos == "PPOSAT":
                    return child
    return subj_token

"""
Single Subject sieve
Attribute speaker to the subject, if it is the only
one in a given context. If the subject is a speech noun, 
attribute to possessive pronoun if any. 
"""
def single_subj_sieve_indirect(text, annotation, contexts):
    subjs = get_subjs(contexts)
    if len(subjs) == 1:
        checked_subj = get_possessive_subj(text, subjs[0])
        if not checked_subj.lemma in SPEECH_NOUNS:
            return [checked_subj.id]
    return []

def get_candidate_from_verb_non_subj(text, verb, annotation):
    children = text.get_direct_children(verb)
    candidates = []
    for child in children:
        if child.is_candidate():
            candidates.append(child)
    return candidates

"""
Closest Verb sieve
Attribute speaker to the child of the closest verb to the 
stw unit if the child is a candidate. 
"""
def closest_verb_candidate_sieve(text, annotation, contexts):
    verbs = get_verbs(contexts)
    closest_verb = get_closest_verb(verbs, text, annotation)
    if closest_verb is None:
        return []
    else:
        return get_candidate_from_verb_non_subj(text, closest_verb, annotation)


def get_closest_token(token_list, token, text):
    if len(token_list) > 1:
        distances = [text.get_distance_tok_tok(tok, token) for tok in token_list]
        index_closest = distances.index(min(distances))
        closest = token_list[index_closest]
    elif len(token_list) == 1:
        closest = token_list[0]
    else:
        closest = None 
    return closest

"""
If strict search for speaker with dependency sieve was unsuccessful, 
this sieve identifies the speaker as the closest mention to the speech verb 
"""
def speech_verb_fall_back_sieve(text, annotation, contexts, check_candidate_strict=True):
    speech_verbs = get_speech_verbs(contexts)
    functional_verbs = get_functional_verb_cues(text, contexts)
    verb_cues = speech_verbs + functional_verbs 

    closest_verb = get_closest_verb(verb_cues, text, annotation)
    if closest_verb is None:
        return []
    else:
        speakers = get_candidate_from_verb(text, closest_verb, annotation)
        if len(speakers) == 0:
            if check_candidate_strict:
                candidates = get_candidates(contexts)
            else:
                candidates = [tok for context in contexts for tok in context if tok.pos in CANDIDATE_POS_EXTENDED]
            closest = get_closest_token(candidates, closest_verb, text)
            if closest is None:
                return []
            else:
                return [closest.id]

"""
Binary classifier sieve 
Apply binary classifier to predict the speaker
"""
def binary_classifier_sieve(text, annotation, contexts=None):
    speakers = []
    candidate_features, candidate_tokens = get_features_representation_per_annotation(text, annotation, use_int=INT_FEATURES)
    for candidate_feat,candidate_tok in zip(candidate_features, candidate_tokens):
        result = BINARY_CLASSIFIER.classify(candidate_feat)
        if result == 1:
            speakers.append(candidate_tok.id)
    return speakers 

"""
Complete speaker if speaker is common noun or proper noun
If neighbouring token is apposition and dependent of speaker 
token, also attribute as speaker
"""
def complete_speaker(predicted_speaker_ids, text):
    possible_pos = ["NE", "NN"]
    predicted_speaker = text.get_tokens_by_id(predicted_speaker_ids)
    if len(predicted_speaker) == 1:
        predicted_speaker = predicted_speaker[0]
        if predicted_speaker.pos in possible_pos:
            children = text.get_direct_children(predicted_speaker)
            possible_speaker_additions = [predicted_speaker.id]
            for child in children:
                if child.dependency == "app" and child.pos in possible_pos:
                    if abs(child.id - predicted_speaker.id) == 1:
                        possible_speaker_additions.append(child.id)
            return possible_speaker_additions
        return [predicted_speaker.id]
    return predicted_speaker_ids 

"""
APPLY SIEVES
"""
def apply_sieves_indirect(text, sieves, functional_verb_path, speech_noun_file, classifier_path=None):
    set_up_func_verbs(functional_verb_path)

    if classifier_path is not None:
        set_up_classifier(classifier_path)

    global SPEECH_NOUNS
    SPEECH_NOUNS = read_word_list(speech_noun_file)

    if text.annotation_number > 0:
        for annotation in text.annotations:
            all_contexts = []
            all_contexts.append(get_base_context(annotation, text))
            all_contexts.append(get_context_before(annotation, text, 1))
            all_contexts.append(get_context_after(annotation, text, 1))

            for contexts in all_contexts:
                if not annotation.has_speaker_prediction():
                    for sieve in sieves:
                        if not annotation.has_speaker_prediction():
                            speakers = sieve(text, annotation, contexts)
                            annotation.predicted_speaker = complete_speaker(speakers, text)	
                            if annotation.has_speaker_prediction():
                                annotation.predicted_by = str(sieve)
            


def apply_sieves_to_corpus_indirect(corpus, sieves):
    for text in corpus:
        apply_sieves_indirect(text, sieves)

