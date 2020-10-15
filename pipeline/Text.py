#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Creation of Text, Annotation and Token object. 
"""

from collections import OrderedDict
import copy
from tqdm import tqdm 


VERB_POS = ["VVFIN", "VVPP", "VVINF", "VAINF", "VVIZU"]
MENSCH_POS = "NN"
NER_POS = "NE"
PRONOUN_POS = "PPER"
CANDIDATE_POS = ["PPER", "NN", "NE"]
PUNCTUATION = ["$.", "$,", "$("]
TO_EXCLUDE = ["es"]
SUBJECT_TAG = "subj"
#SUBJECT_TAG = "SB"

def read_word_list(filename):
    word_list = []
    with open(filename, 'r') as file_in:
        for line in file_in:
            word_list.append(line.strip())
    return word_list

def populate_word_lists(verb_path, mensch_path, vocative_path):
    global SPEECH_VERBS, MENSCH_WORDS, VOCATIVE_WORDS
    SPEECH_VERBS = read_word_list(verb_path)
    VOCATIVE_WORDS = read_word_list(vocative_path)
    MENSCH_WORDS = read_word_list(mensch_path)

class Token():
    def __init__(self, text, lemma, pos, ner, dependency, parent_id, token_id, sentence_id, \
        coreferent_ids=[], start=None, end=None):
        self.text = text
        self.lemma = lemma
        self.pos = pos
        self.ner = ner
        self.id = token_id
        self.dependency = dependency
        self.parent_id = parent_id
        self.sentence_id = sentence_id
        self.parent_token = None
        self.is_annotated = False
        self.coreferent_ids = coreferent_ids
        
        # character indice in original text 
        self.start = start
        self.end = end 
    
    def __repr__(self):
        return repr(self.__dict__)

    def has_coreferents(self):
        return len(self.coreferent_ids) > 0 
    
    def is_speech_verb(self):
        return self.pos in VERB_POS and self.lemma in SPEECH_VERBS
    
    def is_subject(self):
        return self.dependency == SUBJECT_TAG
    def is_mensch(self):
        return self.pos == MENSCH_POS and self.lemma in MENSCH_WORDS
        
    def is_person_name(self):
        return self.ner == "yes"

    def is_punctuation(self):
        return self.pos in PUNCTUATION

    def is_pronoun(self):
        return self.pos == PRONOUN_POS and self.lemma not in TO_EXCLUDE
    
    def is_candidate(self, pis=False):
        if self.pos in CANDIDATE_POS:
            if self.is_pronoun():
                return True
            elif self.is_mensch():
                return True
            elif self.is_person_name():
                return True
        if pis:
            if self.pos == "PIS":
                return True
        return False


# consecutive Token List
class TokenList():
    def __init__(self, token_list):
        self.tokens = token_list
        self.text = [token.text for token in self.tokens]
        self.start = token_list[0].id
        self.end = token_list[-1].id
        self.start_token = token_list[0]
        self.end_token = token_list[-1]
        self.length = len(self.tokens)
    
    def __repr__(self):
        return " ".join(self.text)
    
    # we don't use these methods in text, since we're iterating all tokens
    # in Text we just retrieve an entry from a dict
    def get_token_by_index(self, index):
        for tok in self.tokens:
            if tok.id == index:
                return tok
    def get_token_by_indices(self, indices):
        tokens = []
        for tok in self.tokens:
            if tok.id in indices:
                tokens.append(tok)
        return tokens
    
    def token_in_list(self, tok):
        return tok in self.tokens



# anno id should start with 0 and should be consectuive (to be able to get an order of the annotations)
# token_list is an array of token objects

class Annotation():
    def __init__(self, anno_id, token_list, true_spaker_ids, medium=None):
        self.id = anno_id
        self.tokens = token_list # array of token object
        self.text = [token.text for token in self.tokens]
        
        self.token_ids = sorted([token.id for token in self.tokens])
        self.start_id  = min(self.token_ids)
        self.end_id = max(self.token_ids)        
        
        self.start_token = self.tokens[0]
        self.end_token = self.tokens[-1]

        self.sentence_start_id = self.start_token.sentence_id
        self.sentence_end_id = self.end_token.sentence_id
        
        self.slices = self.extract_slices()
        
        self.true_speaker_ids = true_spaker_ids
        self.predicted_speaker = None
        self.predicted_by = None

        self.medium = medium
        
        self.parent_id = None
    
    def __repr__(self):
        return repr(self.__dict__)
        
    def get_tokens_by_id(self, token_ids):
        selected_tokens = []
        for token in self.tokens:
            if token.id in token_ids:
                selected_tokens.append(token)
        return selected_tokens
    
    def has_speaker(self):
        return self.true_speaker_ids is not None

    def has_speaker_prediction(self):
        return self.predicted_speaker is not None and len(self.predicted_speaker) > 0 
                
        
    def is_split(self):
        current_id = self.token_ids[0] - 1 
        for token_id in self.token_ids:
            if token_id != current_id + 1:
                return True
            else:
                current_id += 1
        return False

    def extract_slices(self):
        if self.is_split():
            slices_ids = []
            one_slice = []
            current = self.start_id - 1
            for tok_id in self.token_ids:
                if tok_id == current + 1:
                    one_slice.append(tok_id)
                    current += 1
                else:
                    slices_ids.append(one_slice)
                    one_slice = [tok_id]
                    current = tok_id
            slices_ids.append(one_slice)
            slices_token = [TokenList(self.get_tokens_by_id(slice_ids)) for slice_ids in slices_ids]
            return slices_token
        else:
            return TokenList(self.tokens)
    
    # =====================================VOCATIVES=====================================================
    def has_vocative(self):
        return len(self.get_vocatives()) > 0
    
    def is_vocative(self, vocative_candidate_id):
        context = [vocative_candidate_id -1, vocative_candidate_id +1]
        context_token = self.get_tokens_by_id(context)
        return all(tok.pos in PUNCTUATION for tok in context_token)
            
        
    def get_vocatives(self):
        vocative_tokens = []
        for token in self.tokens:
            if token.is_person_name():
                if self.is_vocative(token.id):
                    vocative_tokens.append(token)
            elif token.text in VOCATIVE_WORDS :
                if self.is_vocative(token.id):
                    vocative_tokens.append(token)
            elif token.dependency == "vok":
                vocative_tokens.append(token)
        return vocative_tokens


# text consists of annotations (one type) and all tokens
# need to know start and end(length) of text
# get previous/next n tokens -> need to be sorted
# get previous / next anno -> need to be sorted 
# token_list is an object of class TokenList

class Text():
    def __init__(self, annotation_list, token_list, sentence_list):
        self.annotations = annotation_list
        self.tokens = token_list.tokens # should be sorted 
        self.text = token_list.text
        
        self.sentences = sentence_list
        self.sentence_number = len(self.sentences)
        
        self.token_number = token_list.length # should equal text length 
        self.annotation_number = len(self.annotations)
        
        self.token_ids = sorted([token.id for token in self.tokens])
        self.annotation_ids = sorted([anno.id for anno in self.annotations])
                
        self.id_to_token_mapping = self.get_id_token_mapping()
        self.id_to_anno_mapping = self.get_id_anno_mapping()
        
        self.start = token_list.start
        self.end = token_list.end
        
        self.set_parent_tokens()
    
    # ========================= Complete token info ================================================
    def set_parent_tokens(self):
        for token in self.tokens:
            parent = self.get_tokens_by_id([token.parent_id])[0]
            token.parent_token = parent

    # ==================== Annotate overlaps =======================================================
    def set_parent_id(self):
        for anno in self.annotations:
            for anno_cmp in self.annotations:
                if not anno_cmp.id == anno.id:
                    if anno.start_id >= anno_cmp.start_id and anno.end_id <= anno_cmp.end_id:
                        if anno.parent_id is None:
                            anno.parent_id = anno_cmp.id
                        else:
                            # since is not possible in direct speech? 
                            # in other types, quotes don't really have relation 
                            anno.parent_id = None
                            

    # check if annotation is "Binnenannotation"
    def check_annotation_is_surrounded(self, anno):
        return anno.parent_id is None

    def check_if_annotations_overlap(self, anno_a, anno_b):
        if anno_a.parent_id is anno_b.id:
            return True
        elif anno_b.parent_id is anno_a.id:
            return True
        return False 
            
        
    # ================================ Get token, annotation to ID mappings===================
    def get_id_token_mapping(self):
        id_to_token = {}
        for token in self.tokens:
            if token.id in id_to_token:
                print("Token already exists. Skipping...")
            id_to_token[token.id] = token
        return id_to_token
    
    def get_id_anno_mapping(self):
        id_to_anno = {}
        for anno in self.annotations:
            if anno.id in id_to_anno:
                print("Annotation already exists. Skipping...") 
            id_to_anno[anno.id] = anno
        return id_to_anno
    
    
    # ================================== Get/Check tokens, annotations by ID =======================
    def get_tokens_by_id(self, token_ids):
        selected_tokens = []
        for token_id in token_ids:
            if token_id in self.id_to_token_mapping:
                selected_tokens.append(self.id_to_token_mapping[token_id])
            #else:
                #print(f"Error! The ID {token_id} is not in the token list")
        return selected_tokens

    def get_distance_tok_tok(self, token_a, token_b):
        return abs(token_a.id - token_b.id)
    
    def get_annotations_by_id(self, anno_ids):
        selected_annos = []
        for anno_id in anno_ids:
            if anno_id in self.id_to_anno_mapping:
                selected_annos.append(self.id_to_anno_mapping[anno_id])
            #else:
                #print(f"Error! The ID {anno_id} is not in the annotation list")
                selected_annos.append(None)
        return selected_annos
    
    
    def check_id_in_list_of_token(self, index, list_of_token):
        return any(tok.id == index for tok in list_of_token)
    
    
    def check_if_anno_is_last(self, anno):
        return self.check_id_in_list_of_token(self.end, anno.tokens)
    
    
    
    # =============================== Check if start and end of text is annotated==============
    def starts_with_annotation(self):
        return self.check_id_in_list_of_token(0, self.annotations[0].tokens)
    
    
    # last annotation in list is not always last in file (in case of nested anno)
    def ends_with_annotation(self):
        return any(self.check_if_anno_is_last(anno) for anno in self.annotations)
            

    # =============================== Get previous, next tokens====================================
    # extract the n token before the passed token
    def get_previous_tokens(self, token, n):
        if token.id - n >= self.start:
            first = token.id - n
        else:
            first = self.start
            
        wanted_token_ids = [i for i in range(first, token.id)]
        return self.get_tokens_by_id(wanted_token_ids)

    def get_next_tokens(self, token, n):
        if token.id + n <= self.end:
            last = token.id + n + 1
        else:
            last = self.end + 1
        wanted_token_ids = [i for i in range(token.id + 1, last)]
        return self.get_tokens_by_id(wanted_token_ids)
    
    # ============================ Check token dependencies=========================================
    
    def is_direct_child(self, token_to_check, possible_parent_token):
        return token_to_check.parent_token == possible_parent_token
    
    def get_direct_children(self, token):
        children = []
        sentence = self.sentences[token.sentence_id]
        for candidate in sentence.tokens:
            if self.is_direct_child(candidate, token):
                children.append(candidate)
        return children
    
    # =============================== Get sentences with annotation=================================
    def get_sentences_by_ids(self, ids):
        selected_sentences = [self.sentences[i] for i in ids]
        return selected_sentences

            
    def get_sentences_including_annotation(self, anno):
        sen_ids = [i for i in range(anno.start_token.sentence_id, anno.end_token.sentence_id + 1)]
        return self.get_sentences_by_ids(sen_ids)
    
    def get_sentence_id(self, sentence):
        return sentence.tokens[0].sentence_id
    
    def get_sentences_before(self, sentence, n):
        sen_id = self.get_sentence_id(sentence)
        if sen_id - n >= 0:
            start = sen_id - n
        else:
            start = 0
        ids_to_retrieve = [i for i in range(start, sen_id)]
        return self.get_sentences_by_ids(ids_to_retrieve)
    
    def get_sentences_after(self, sentence, n):
        sen_id = self.get_sentence_id(sentence)
        if sen_id + n < self.sentence_number:
            end = sen_id + n + 1
        else:
            end = self.sentence_number
            
        ids_to_retrieve = [i for i in range(sen_id + 1, end)]
        return self.get_sentences_by_ids(ids_to_retrieve)
        
    
    # ======================== Get tokens in between annotation slices==============================
    def get_token_lists_between_annotation_slices(self, anno):
        token_lists_between = []
        if anno.is_split():
            i = 0
            while i < len(anno.slices) - 1:
                token_ids_to_obtain = [j for j in range(anno.slices[i].end + 1, anno.slices[i+1].start + 1)]
                obtained_tokens = TokenList(self.get_tokens_by_id(token_ids_to_obtain))
                token_lists_between.append(obtained_tokens)
                i += 1
        return token_lists_between
    
    # is this useful? 
    def check_token_between_annotation(self, anno, token):
        token_lists_between = self.get_token_lists_between_annotation_slices(anno)
        return any(token_list.token_in_list(token) for token_list in token_lists_between)


    #============================= Get tokens between two tokens======================================

    def get_token_between_tokens(self, token_a, token_b):
        if token_a.id < token_b.id:
            ids_inbetween = [i for i in range(token_a.id, token_b.id + 1)]
        elif token_b.id < token_a.id:
            ids_inbetween = [i for i in range(token_b.id, token_a.id + 1)]
        else:
            ids_inbetween = []

        return self.get_tokens_by_id(ids_inbetween)            
        
    # ============================ Get tokens between two annos =========================================
    def get_tokens_between_current_and_before(self, annotation):
        anno_before = self.get_previous_anno_by_distance(annotation, 1)
        if anno_before is not None:
            tokens_ids_inbetween = [tok_id for tok_id in range(anno_before.end_id +1, annotation.start_id)]
            return self.get_tokens_by_id(tokens_ids_inbetween)
        return []
    
    def get_tokens_between_current_and_after(self, annotation):
        anno_after = self.get_next_anno_by_distance(annotation, 1)
        if anno_after is not None:
            tokens_ids_inbetween = [tok_id for tok_id in range(annotation.end_id +1, anno_after.start_id)]
            return self.get_tokens_by_id(tokens_ids_inbetween)
        return []
    
    
    def get_tokens_between_two_annos(self, anno_a, anno_b):
        if not self.check_if_annotations_overlap(anno_a, anno_b):
            if anno_a.id < anno_b.id:
                tok_ids = [i for i in range(anno_a.end_id +1, anno_b.start_id)]
            else:
                tok_ids = [i for i in range(anno_b.end_id +1, anno_a.start_id)]
            return self.get_tokens_by_id(tok_ids)
        
        else:
            return []
    # ============================ Get previous, next anno ===========================================
    def get_previous_anno_by_distance(self, anno, n):
        counter = 0
        if anno.id - n >= 0:
            for i in range(anno.id -1, -1, -1):
                if self.id_to_anno_mapping[i].parent_id is anno.parent_id:
                    counter += 1
                    if counter == n:
                        return self.id_to_anno_mapping[i]
        return None
            

    def get_next_anno_by_distance(self, anno, n):
        counter = 0
        if anno.id + n < self.annotation_number:
            for i in range(anno.id + 1, self.annotation_number):
                if self.id_to_anno_mapping[i].parent_id is anno.parent_id:
                    counter += 1
                    if counter == n:
                        return self.id_to_anno_mapping[i]
        return None
        
    # get distances
    def get_distance_tok_anno(self, token, anno):
        if token.id < anno.start_id:
            return anno.start_id - token.id
        elif  token.id > anno.end_id:
            return token.id - anno.end_id
        else:
            if anno.is_split():
                starts = [anno_slice.start for anno_slice in anno.slices]
                ends = [anno_slice.end for anno_slice in anno.slices]
                starts_ends = starts + ends

                distances = [abs(start_end_id - token.id) for start_end_id in starts_ends]
                return min(distances)
            return 0
    
    
    def get_distance_between_annotations(self, anno_a, anno_b):
        if not self.check_if_annotations_overlap(anno_a, anno_b):
            
            if anno_a.id < anno_b.id:
                return anno_b.start_id - anno_a.end_id
            else:
                return anno_a.start_id - anno_b.end_id
        return -1
    
    def check_if_in_conversation(self, anno_a, anno_b):
        tokens_between = self.get_tokens_between_two_annos(anno_a, anno_b)
            
        tok_not_annotated = 0
        for tok in tokens_between:
            if not tok.is_annotated:
                tok_not_annotated += 1
        if tok_not_annotated <= 1:
            return True
        return False

    # --------------------------- Check token already predicted as speaker ------------------------------
    def is_predicted_speaker_of_annotation_before(self, token, annotation):
        anno_before = self.get_previous_anno_by_distance(annotation, 1)
        if anno_before is not None and anno_before.predicted_speaker is not None:
            return token.id in anno_before.predicted_speaker
        return False

    def is_predicted_speaker_of_annotation_after(self, token, annotation):
        anno_after = self.get_next_anno_by_distance(annotation, 1)
        if anno_after is not None and anno_after.predicted_speaker is not None:
            return token.id in anno_after.predicted_speaker
        return False


def get_sentences(text):
    sentence_dict = dict(tuple(text.groupby("senID", axis=0)))
    sentence_frames = list(sentence_dict.values())
    return sentence_frames

# extract the speaker information for the stwr units
# splits speaker 
# returns dictionary with annotation IDs as keys and indice as values 
def get_speaker_ids_and_values(text):

    # extract speaker same way as stwr unit
    speakers = set(text[text["speaker"] != "-"]["speaker"])

    speaker_ids = {}
    for tag in speakers:
        speaker_ids[tag] = list(text.index[text["speaker"] == tag])

    # seperate tags and join the ids 
    seperated_tags_speaker = {}
    for tag_keys, indice in speaker_ids.items():

        for key in tag_keys.split("_"):
            if "." in key:
                tag_id = key.split(".")[1]
            else:
                tag_id = key

            if tag_id in seperated_tags_speaker:
                seperated_tags_speaker[tag_id].extend(indice)
            else:
                seperated_tags_speaker[tag_id] = copy.deepcopy(indice)
                
    return seperated_tags_speaker


def process_coreferent_ids(coreferent_ids):
    if coreferent_ids == "-":
        return []
    else:
        coreferent_ids = coreferent_ids.split("|")
        if not len(coreferent_ids) == 1 and not coreferent_ids[0] == '':
            coref_ints = [int(coref_id) for coref_id in coreferent_ids]
        elif len(coreferent_ids) == 1 and not coreferent_ids[0] == '':
            coref_ints = [int(coreferent_ids[0])]
        else:
            coref_ints = []
        return coref_ints


def create_token_sentences(text_df, coreference=True, character_index=False):
    sentence_frames = get_sentences(text_df)
    token_list = []
    all_sentences = []
    for sentence_id, sentence in enumerate(sentence_frames):
        sentence_tokens = []
        for row_id, row in sentence.iterrows():
            if coreference:
                coreferent_ids_raw = row["coreference"]
                coreferent_ids = process_coreferent_ids(coreferent_ids_raw)
            else:
                coreferent_ids = []

            if character_index:
                start = row["start"]
                end = row["end"]
            else:
                start = None
                end = None

            tok = Token(row["tok"],row["lemma"], row["pos"],row["NER"], row["dependency"],row["parentID"],
                        row_id, sentence_id, coreferent_ids, start, end)

            token_list.append(tok)
            sentence_tokens.append(tok)
        all_sentences.append(TokenList(sentence_tokens))
    return TokenList(token_list), all_sentences

def create_annotation_objects(text, tokens, anno_types, speaker_ids):
    tags = text[text["stwr"] != "-"]["stwr"]
    ordered_tags_unique = []
    for tag in tags:
        if tag not in ordered_tags_unique:
            ordered_tags_unique.append(tag)

    # collect the ids of the tokens, the stwr unit is annotated to
    # tags are not seperated yet (to easily collect ids)
    tags_to_indice = OrderedDict()
    for tag in ordered_tags_unique:
        tags_to_indice[tag] = list(text.index[text["stwr"] == tag])
        
    # seperate tags and join the ids 
    # tag_keys are full annotation: e.g direct.thought.9|indirect.thought.10.nonfact
    seperated_tags = OrderedDict()
    for tag_keys, indice in tags_to_indice.items():
        for key in tag_keys.split("|"):
            key = key.split(".")
            tag_type = key[0]
            tag_medium = key[1]
            tag_id = key[2]
            if tag_type in anno_types:
                if tag_id in seperated_tags:
                    seperated_tags[tag_id][0].extend(indice)
                else:
                    seperated_tags[tag_id] = (copy.deepcopy(indice), tag_medium)
    
    current_id = 0
    annotations = []
    for tag_id, (indice, medium) in seperated_tags.items():
        token_objects = tokens.get_token_by_indices(indice)
        for token in token_objects:
            token.is_annotated = True
        if tag_id in speaker_ids:
            true_speaker = speaker_ids[tag_id]
        else:
            true_speaker = None
        anno = Annotation(current_id, token_objects, true_speaker, medium=medium)
        current_id += 1
        annotations.append(anno)
    return annotations

def create_text_class(text, anno_types, verb_path, mensch_path, vocative_path, coreference=True,
 character_index=True, speaker_present=True):
    populate_word_lists(verb_path, mensch_path, vocative_path)

    tokens, sentence_list = create_token_sentences(text, coreference=coreference, character_index=character_index)
    if speaker_present:
        speakers = get_speaker_ids_and_values(text)
    else:
        speakers = []
    annotations = create_annotation_objects(text, tokens, anno_types, speakers)
    text_object = Text(annotations, tokens, sentence_list)
    return text_object

def create_corpus_classes(corpus, anno_types, verb_path, mensch_path, vocative_path, coreference=True, character_index=True):
    corpus_objects = []
    for text in tqdm(corpus):
        text_object = create_text_class(text, anno_types, verb_path, mensch_path, vocative_path, \
            coreference=coreference, character_index=character_index)
        corpus_objects.append(text_object)
    return corpus_objects
        