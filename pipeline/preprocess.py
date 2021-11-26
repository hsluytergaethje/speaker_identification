#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Pipeline:
1) tokenization & sentence splitting, PoS, Lemma, Dependency with Parzu
3) NER with flair
4) verb fixing (on corpus classes)
5) Parc annotation to annotations with IDs
"""


from io import StringIO
import csv
import sys

import pandas as pd
from flair.models import SequenceTagger
from flair.data import Sentence

from Text import Text, Annotation, TokenList, Token, create_token_sentences, create_text_class, get_sentences, populate_word_lists
from read_write_helper import read_tsv_df, read_txt
from character_token_mapping import character_to_token_mapping, token_to_token_from_char_mapping, reverse_mapping

PARZU_FIELD_NAMES = ['ID','tok','lemma','rfpos','pos','morph','parentID','dependency','na','naa']

FINITE_VERB = "VVFIN"
PREFIX = "PTKVZ"

MEDIUM_PLACEHOLDER = "stw"
NOT_ANNOTATED = "x"

tagger = None
stw_taggers = {}
ParZu = None

def initialize_flair():
    global tagger
    tagger = SequenceTagger.load('de-ner-germeval')


def initialize_stw_tagger():
    global stw_taggers
    stw_taggers = {
            "direct" : SequenceTagger.load('de-historic-direct'),
            "indirect": SequenceTagger.load('de-historic-indirect'),
            "reported": SequenceTagger.load('de-historic-reported'),
            "freeindirect": SequenceTagger.load('de-historic-free-indirect')

            }

def initialize_parzu(parzu_path):
    global ParZu
    if parzu_path not in sys.path:
        sys.path.insert(1, parzu_path)
    import parzu_class as parzu

    options = parzu.process_arguments(commandline=False)
    ParZu = parzu.Parser(options, timeout=10000)

def stw_annoate_text(text: pd.DataFrame, tagger: SequenceTagger) \
        -> list[Sentence]:
    sentence_frames = get_sentences(text)
    sentence_list = [" ".join(sentence["tok"]) for sentence in sentence_frames]
    annotations = []
    for sentence in sentence_list:
        flair_sen = Sentence(sentence, use_tokenizer=False)
        tagger.predict(flair_sen)
        annotations.append(flair_sen)
    return annotations

def get_continuous_annotations(annotated_sentences: list[Sentence])\
        -> dict:
    annotations = {}
    token_id = -1
    current_anno_id = -1
    before_annotated = False
    for sentence in annotated_sentences:
        for token in sentence:
            token_id += 1
            label = token.labels[0].value
            if label != NOT_ANNOTATED:
                if not before_annotated:
                    current_anno_id += 1
                    annotations[current_anno_id] = {"token_ids":[token_id],
                        "medium":MEDIUM_PLACEHOLDER}
                    before_annotated = True
                else:
                    annotations[current_anno_id]["token_ids"].append(token_id)
            else:
                before_annotated = False
    return annotations

# Annnotation with ParZu
def annotate_with_parzu(text):
    text_anno = ParZu.main(text)
    return text_anno

def postprocess_parzu(text_anno):
    text = {"tok":[], "lemma":[], "pos":[], "dependency":[], "parentID":[], "senID":[]}

    anno_reader = csv.DictReader(StringIO("".join(text_anno)), fieldnames=PARZU_FIELD_NAMES, \
        delimiter="\t", quoting=csv.QUOTE_NONE)

    token_ids = []
    sentence_id = -1
    for row in anno_reader:
        token_ids.append(row["ID"])
        if row["ID"] == "1":
            sentence_id += 1
        for key in text:
            if key == "senID":
                text[key].append(sentence_id)
            else:
                text[key].append(row[key])

    corrected_parent_ids = []
    relative_parent_ids = []
    for t,p in zip(token_ids, text["parentID"]):
        if int(p) == 0:
            relative_parent_ids.append(0)
        else:
            relative_parent_ids.append(int(p) - int(t))

    # match to overall token IDs
    for i, rel_id in enumerate(relative_parent_ids):
        corrected_parent_ids.append(i + rel_id)

    text["parentID"] = corrected_parent_ids
    df = pd.DataFrame.from_dict(text)
    return df

# Annotation with Flair
def get_sentence_text(text):
    sentence_frames = get_sentences(text)
    sentences = [sentence["tok"] for sentence in sentence_frames]
    sen_texts = [Sentence(" ".join(sentence)) for sentence in sentences]
    return sen_texts

# extract overall token id for PERSON NER
def get_overall_annotation_ids_for_PER(annotated_sentences):
    overall_id = 0
    sentence_anno_ids = []

    for sentence in annotated_sentences:
        last =  overall_id + len(sentence)

        # need overall id for the dataframe annotation
        overall_ids = [i for i in range(overall_id, last)]
        overall_id = overall_ids[-1] + 1

        anno_ids = []
        for entry in sentence.get_spans('ner'):
            if entry.tag == "PER":
                ids = [tok.idx for tok in entry.tokens]
                anno_ids.extend(ids)

        if len(anno_ids) > 0:
            sentence_anno_ids.extend([overall_ids[i-1] for i in anno_ids])

    return sentence_anno_ids

def annotate_text_with_NER(text, insert_id=7):
    if "NER" not in text.columns:
        sentences = get_sentence_text(text)
        tagger.predict(sentences)
        ids = get_overall_annotation_ids_for_PER(sentences)
        tags = ["-" if i not in ids else "yes" for i in range(len(text["tok"]))]
        text.insert(insert_id, "NER", tags)
    return text


# Fix lemmata
def fix_lemma_per_sentence(text, sentences):
    id_to_new_lemma = {}
    for sentence in sentences:
        for token in sentence.tokens:
            if token.pos == FINITE_VERB:
                children = text.get_direct_children(token)
                if any(child.pos == PREFIX for child in children):
                    for child in children:
                        if child.pos == PREFIX:
                            new_lemma = child.lemma + token.lemma
                            id_to_new_lemma[token.id] = new_lemma
    return id_to_new_lemma

def correct_lemmata_in_textdf(text, ids_to_lemmata):
    for token_id, new_lemma in ids_to_lemmata.items():
        text.iloc[token_id, text.columns.get_loc("lemma")] = new_lemma

def fix_text(text, text_df):
    ids_to_lemmata = fix_lemma_per_sentence(text, text.sentences)
    correct_lemmata_in_textdf(text_df, ids_to_lemmata)
    return text_df

# Token text, lemma, pos, ner, dependency, parent_id, token_id, sentence_id, coreferent_ids=[]
# Tokenlist: list of token object
# Annotation: Anno id, token list, true speaker Ids (None)
# Text: Annotation list, token_list, sentence list
# Sentence: Tokenlist 

def create_text_object(textdf, anno_dict):
    token_list, all_sentences = create_token_sentences(textdf, coreference=False, character_index=True)
    annotation_objects = []

    for anno_id, anno_info in anno_dict.items():
        token_id_list = anno_info["token_ids"]
        medium = anno_info["medium"]
        anno_tokens = [token_list.tokens[i] for i in token_id_list]
        anno = Annotation(anno_id, anno_tokens, None, medium)
        annotation_objects.append(anno)

    text_object = Text(annotation_objects, token_list, all_sentences)
    return text_object


def get_character_start_end_columns(tok_to_char):
    start_column = []
    end_column = []

    for tok, char_list in tok_to_char.items():
        char_list = sorted(char_list)
        start_column.append(char_list[0])
        end_column.append(char_list[-1])

    return start_column, end_column

# replace filename with actual text, since we have to read it for the stwr anno anyway
#def process_text(filename, stwr_anno_filename)
def preprocess_text(text, parzu_path, verb_path, mensch_path, vocative_path):
    print("Prepocessing")
    print("[1] Sentence splitting, Tokenization, Lemmatization, PoS-Tagging, Dependency Parsing (ParZu)")
    text_parzu = annotate_with_parzu(text)
    textdf = postprocess_parzu(text_parzu)

    tokens = list(textdf["tok"])
    char_to_tok = character_to_token_mapping(text, tokens)
    if char_to_tok == 0:
        return 0
    tok_to_char = reverse_mapping(char_to_tok)
    start_col, end_col = get_character_start_end_columns(tok_to_char)

    print("[2] Named Entity Recognition (Flair)")
    textdf = annotate_text_with_NER(textdf, insert_id=6)
    textdf.insert(0, "start", start_col)
    textdf.insert(1, "end", end_col)


    print("[3] Processing of Speech Thought Writing Annotations")
    #initialize_stw_tagger()
    anno_type_to_tokenlists = {}
    for type_name, stw_tagger in stw_taggers.items():
        annotated_flair_sentences = stw_annoate_text(textdf, stw_tagger)
        annotations = get_continuous_annotations(annotated_flair_sentences)
        anno_type_to_tokenlists[type_name] = annotations

    print("[4] Fixing Lemmatization for split Verbs")
    text_object_tmp = create_text_object(textdf, anno_type_to_tokenlists["direct"])

    textdf = fix_text(text_object_tmp, textdf)

    print("[5] Creating text objects")
    populate_word_lists(verb_path, mensch_path, vocative_path)
    all_text_object = {}
    for key, annotations in anno_type_to_tokenlists.items():
        text_object = create_text_object(textdf, anno_type_to_tokenlists[key])
        all_text_object[key] = text_object

    print("Prepocessing done\n")
    return all_text_object

if __name__ == '__main__':
    test_file = "/Users/milchats/Hennys/Uni/thesis/speaker_identification_stw/corpus/sentences/rwk_digbib_930-1.xmi.sentences.txt"
    stwr_file = "/Users/milchats/Hennys/Uni/thesis/STW_recognition_tool/text_annotated.tsv"
    text = " ".join(read_txt(test_file))
    all_text_objects = preprocess_text(text, stwr_file)


