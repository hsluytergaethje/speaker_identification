#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Annotation of raw texts with speech, thought, writing annotations and 
their respective speakers.
Four modes: annotate, speaker annotate,  evaluate, evaluate gold
    - annotate: input is raw text
    - speaker_annotate: input is text annotated with stw units
    - evaluate: input is text annotated with stw units and speakers, 
    stw unit and speaker annotations are evaluated 
    - evaluate_gold: input is text annotated with stw units and speakers,
    the speakers are predicted on the basis of the gold stw units, 
    speaker annotations are evaluated
Config file:
    - options for stwr recognition
    - options for sieves
    - path to parzu 
    - paths to additional resources
    - paths to binary classifiers
Command line input: 
    input directory, output directory, config file, mode
"""

import os
import sys
import argparse
import configparser
from pathlib import Path

from read_write_helper import read_tsv_df, read_txt, write_annotations_to_tsv
from preprocess import preprocess_text, initialize_flair, initialize_stw_tagger, initialize_parzu
from Text import create_text_class, get_sentences
from evaluate import get_eval_per_class, evaluate_stwr_gold_annotations, join_stw_speaker, join_speaker

# import functions for speaker annotation
from direct_sieves import *
from indirect_sieves import *
from reported_sieves import *
from free_indirect_sieves import *

CWD = os.getcwd()

# match sieves from config file to sieve functions
SIEVE_TRANSLATION = {
    "trigram_matching_sieve": trigram_matching_sieve,
    "loose_trigram_matching_sieve": loose_trigram_matching_sieve, 
    "colon_sieve": colon_sieve,
    "dependency_sieve": dependency_sieve,
    "loose_dependency_sieve": loose_dependency_sieve,
    "single_candidate_sieve": single_candidate_sieve,
    "vocative_detection_sieve": vocative_detection_sieve, 
    "binary_classifier_sieve":  binary_classifier_sieve,
    "conversational_sieve": conversational_sieve,
    "loose_conversational_sieve": loose_conversational_pattern,
    "adjacent_quote_sieve": adjacent_quote_sieve,

    "dependency_sieve_indirect": dependency_sieve_indirect,
    "loose_depencency_sieve_indirect": depencency_sieve_loose_indirect,
    "single_candidate_sieve_indirect": single_candidate_sieve_indirect,
    "closest_verb_sieve": closest_verb_sieve,
    "closest_candidate_sieve": closest_candidate_sieve,
    "speech_verb_fall_back_sieve": speech_verb_fall_back_sieve,
    "trigram_sieve_indirect": trigram_sieve_indirect,
    "single_verb_sieve": single_verb_sieve,

    "passive_sieve": passive_sieve,
    "stw_dependency_sieve": stw_dependency_sieve,
    "single_speech_noun_sieve": single_speech_noun_sieve,
    "single_candidate_sieve_reported": single_candidate_sieve_reported,
    "single_subject_sieve_strict": single_subj_sieve_strict,
    "stw_i_sieve": stw_i_sieve,
    "loose_stw_dependency_sieve": stw_dependency_sieve_loose,
    "single_subject_sieve": single_subj_sieve,
    "single_subject_sieve_indirect": single_subj_sieve_indirect,
    "loose_depencency_sieve_reported": depencency_sieve_loose_reported,
    "closest_subject_sieve": closest_subj_sieve,
    "speech_noun_genitive_object_sieve": speech_noun_genitive_object_sieve,
    "dependency_sieve_reported": dependency_sieve_reported,

    "loose_closest_candidate_sieve": loose_closest_candidate_sieve,
    "question_sieve": question_sieve,
    "neighbouring_instance_sieve": neighbouring_instance_sieve,
    "closest_speaking_candidate_strict": closest_speaking_candidate_strict,
    "closest_candidate_sieve_before_strict": closest_candidate_sieve_before_strict,
    "closest_candidate_sieve_before": closest_candidate_sieve_before    
}

# optimal sieves 
OPTIMAL_DIRECT_SIEVES = [trigram_matching_sieve, colon_sieve, dependency_sieve, loose_trigram_matching_sieve, \
loose_dependency_sieve, single_candidate_sieve, vocative_detection_sieve, \
conversational_sieve, binary_classifier_sieve, loose_conversational_pattern]

OPTIMAL_INDIRECT_SIEVES = [dependency_sieve_indirect, single_speech_noun_sieve, depencency_sieve_loose_indirect, single_candidate_sieve_indirect,
single_subj_sieve_indirect, closest_verb_sieve, binary_classifier_sieve, closest_candidate_sieve]

OPTIMAL_REPORTED_SIEVES_IN =  [passive_sieve, stw_dependency_sieve, single_speech_noun_sieve, single_subj_sieve_strict, 
single_candidate_sieve_reported, stw_i_sieve, binary_classifier_sieve, stw_dependency_sieve_loose, single_subj_sieve] 

OPTIMAL_REPORTED_SIEVES_OUT = [single_subj_sieve_strict, dependency_sieve_reported,single_candidate_sieve_reported, closest_verb_sieve]

OPTIMAL_FREEINDIRECT_SIEVES = [closest_speaking_candidate_strict, closest_candidate_sieve_before_strict, closest_candidate_sieve_before]

OPTIMAL_SIEVES_BY_TYPE = {
    "direct": OPTIMAL_DIRECT_SIEVES,
    "indirect": OPTIMAL_INDIRECT_SIEVES,
    "reported_in": OPTIMAL_REPORTED_SIEVES_IN,
    "reported_out": OPTIMAL_REPORTED_SIEVES_OUT,
    "freeindirect": OPTIMAL_FREEINDIRECT_SIEVES
}

ALL_SPEECH_TYPES = [["direct"], ["indirect"], ["reported"], ["freeIndirect", "freeIndirect indirect"]]

# preprocess text and create text object

def get_text_objects(text, parzu_path, verb_path, mensch_path, vocative_path):
    parzu_text = " ".join(text)
    all_text_objects = preprocess_text(parzu_text, parzu_path, verb_path, mensch_path, vocative_path)
    return all_text_objects

# preprocess text and annotations, create text objects 
def get_text_eval_object_from_annotated_text(filepath, parzu_path,
    verb_path, mensch_path, vocative_path, coreference=True, character_index=True):
    textdf = read_tsv_df(filepath)
    sentences_df = get_sentences(textdf)
    text = [" ".join(sentence["tok"]) for sentence in sentences_df]
    text_objects_stwr_predicted = get_text_objects(text, parzu_path, \
        verb_path, mensch_path, vocative_path)

    print("\n[6] Creating text objects from annotated text")
    text_objects_stwr_true = {}
    for speech_type in ALL_SPEECH_TYPES:
        text_object = create_text_class(textdf, speech_type, verb_path, mensch_path, vocative_path, \
            coreference=coreference, character_index=character_index)
        if speech_type[0] == "freeIndirect":
            actual_type = "freeindirect"
        else:
            actual_type = speech_type[0]
        text_objects_stwr_true[actual_type] = text_object
    return text_objects_stwr_predicted, text_objects_stwr_true

# preprocess text with gold annotations and create text objects
def get_txt_object_from_gold_annotations(filepath, verb_path, mensch_path, vocative_path, \
    coreference=True, character_index=True, speaker_present=True):
    textdf = read_tsv_df(filepath)
    text_objects_stwr_true = {}
    print("[1] Creating text objects")
    for speech_type in ALL_SPEECH_TYPES:
        text_object = create_text_class(textdf, speech_type, verb_path, mensch_path, vocative_path, \
            coreference=coreference, character_index=character_index, speaker_present=speaker_present)
        if speech_type[0] == "freeIndirect":
            actual_type = "freeindirect"
        else:
            actual_type = speech_type[0]
        text_objects_stwr_true[actual_type] = text_object
    return text_objects_stwr_true

# predict speaker with selected sieves 
def speaker_prediction(sieve_information, stw_text_per_type, speech_noun_path, functional_verb_path, classifier_paths):
    predicted_per_type = {}
    for stw_type, text_object in stw_text_per_type.items():
        if stw_type == "direct":
            print("\t-direct ")
            apply_sieves(text_object, sieve_information[stw_type], functional_verb_path, classifier_paths[stw_type])
        elif stw_type == "indirect":
            print("\t-indirect")
            apply_sieves_indirect(text_object, sieve_information[stw_type], functional_verb_path, speech_noun_path, \
                classifier_paths[stw_type])
        elif stw_type == "reported":
            print("\t-reported")
            apply_sieves_reported(text_object, sieve_information[stw_type][0], \
                sieve_information[stw_type][1], functional_verb_path, speech_noun_path, classifier_paths[stw_type])
        elif stw_type == "freeindirect":
            print("\t-free indirect")
            apply_sieves_freeIndirect(text_object, sieve_information[stw_type])
        predicted_per_type[stw_type] = text_object
    return predicted_per_type


def check_file_path(filepath, extension=".pkl"):
    if not os.path.exists(filepath) or not filepath.endswith(extension):
        print(f"The filepath {filepath} does not exist. Please check the filpath and the config file.")
        print("Aborting.")
        sys.exit(-1)


def parse_sieve_selection(sieve_selection, classifier_paths):
    parsed_sieves = {}
    parsed_classifier_paths = {}

    for sieve_name, sieves in sieve_selection.items():
        if sieves == "optimal":
            parsed_sieves[sieve_name] = OPTIMAL_SIEVES_BY_TYPE[sieve_name]
            if binary_classifier_sieve in OPTIMAL_SIEVES_BY_TYPE[sieve_name]:
                check_file_path(classifier_paths[sieve_name])
                parsed_classifier_paths[sieve_name] = classifier_paths[sieve_name]
            else:
                parsed_classifier_paths[sieve_name] = None
        else:
            sieve_list = []
            sieves = sieves.split("\n")
            for sieve in sieves:
                if sieve != '':
                    if sieve in SIEVE_TRANSLATION:
                        sieve_list.append(SIEVE_TRANSLATION[sieve])
                    else:
                        print("The sieve name you selected is not in the list.")
                        print(f"Sieve name: {sieve}")
                        print("Aborting.")
                        sys.exit(-1)
            if "binary_classifier_sieve" in sieves:
                check_file_path(classifier_paths[sieve_name])
                parsed_classifier_paths[sieve_name] = classifier_paths[sieve_name]
            else:
                parsed_classifier_paths[sieve_name] = None

            parsed_sieves[sieve_name] = sieve_list

    parsed_sieves["reported"] = [parsed_sieves["reported_in"], parsed_sieves["reported_out"]]
    del parsed_sieves["reported_in"]
    del parsed_sieves["reported_out"]
    parsed_classifier_paths["reported"] = parsed_classifier_paths["reported_out"]
    del parsed_classifier_paths["reported_out"]
    return parsed_sieves, parsed_classifier_paths

def process_text(path_to_input, outputfile, mode, parsed_sieves, parsed_classifier_paths, parzu_path,
    verb_path, mensch_path, vocative_path, speech_noun_path, functional_verb_path, print_eval):
    print(f"Annotation of file {os.path.basename(path_to_input)}")
    if mode == "annotate":
        text = read_txt(path_to_input)
        stw_type_to_object = get_text_objects(text, parzu_path, verb_path, mensch_path, vocative_path)
        if stw_type_to_object == 0:
            return 0
        print("Speaker Annotation")
        print("[6] Finding speakers")
        predicted_per_type = speaker_prediction(parsed_sieves, stw_type_to_object, speech_noun_path, functional_verb_path, \
            parsed_classifier_paths)
        print(f"[7] Writing outputfile to {outputfile}\n")
        write_annotations_to_tsv(predicted_per_type, outputfile)
        return None

    elif mode == "speaker_annotate":
        stw_type_to_object = get_txt_object_from_gold_annotations(path_to_input, verb_path, mensch_path, vocative_path, \
            coreference=True, character_index=True, speaker_present=False)
        print("[2] Finding speakers")
        predicted_per_type = speaker_prediction(parsed_sieves, stw_type_to_object, speech_noun_path, functional_verb_path, \
            parsed_classifier_paths)
        print(f"[3] Writing outputfile to {outputfile}")
        write_annotations_to_tsv(predicted_per_type, outputfile)


    elif mode == "evaluate":
        stw_type_to_object, true_objects = get_text_eval_object_from_annotated_text(path_to_input, parzu_path, \
                verb_path, mensch_path, vocative_path)
        if stw_type_to_object == 0:
            return 0
        print("Speaker Annotation")
        print("[7] Finding speakers")
        predicted_per_type = speaker_prediction(parsed_sieves, stw_type_to_object, speech_noun_path, functional_verb_path, \
            parsed_classifier_paths)
        print("[8] Evaluating")
        evaluation = get_eval_per_class(predicted_per_type, true_objects, write=print_eval)
        print(f"[9] Writing outputfile to {outputfile}")
        write_annotations_to_tsv(predicted_per_type, outputfile)
        return evaluation

    else:
        stw_type_to_object = get_txt_object_from_gold_annotations(path_to_input, verb_path, mensch_path, vocative_path)
        print("[2] Finding speakers")
        predicted_per_type = speaker_prediction(parsed_sieves, stw_type_to_object, speech_noun_path, functional_verb_path, \
            parsed_classifier_paths)
        print("[3] Evaluating")
        evaluation = evaluate_stwr_gold_annotations(predicted_per_type, write=print_eval)
        print(f"[4] Writing outputfile to {outputfile}")
        write_annotations_to_tsv(predicted_per_type, outputfile)
        return evaluation


def _parse_arguments():
    task_description = "Annotate Speech, Thought and Writing instance and speakers in a text."
    parser = argparse.ArgumentParser(description=task_description)

    parser.add_argument("-c", "--config", help="Set path/to/config.ini", required=True)
    parser.add_argument("input", nargs='+', help="Set (multiple) path/to/inputfile/")
    parser.add_argument("-o", "--output_dir", help="Set path/to/output/directory")

    extension_help = """Set file extension for the annotated outputfile. File extension is added
    to the basename of the inputfile"""
    parser.add_argument("-ext", "--output_file_extension", help=extension_help)

    mode_help = """If set to \"annotate\", raw text is being annotated.
     If set to \"evaluate\", annotated text in tsv format serve as input. An evaluation
     is performed. If set to \"evaluate_gold\", annotated text serves as input. Speaker prediction
     is performed on the basis of the gold speech, thought and writing annotations in the annotated 
     text. If set to \"speaker_annotate\", it is assumed that speech thought and writing 
     information are avalailable in the same format as in the RWK tsv files. Predicted annotations are 
     always written to the outputfile."""

    parser.add_argument("-m", "--mode", help=mode_help, choices=["annotate", "evaluate", "evaluate_gold", "speaker_annotate"], \
        required=False, default="annotate")
    parser.add_argument("-p", "--print_eval", help="Set, if evaluation shall be printed for every single file", \
        action="store_true", default=False)

    args = parser.parse_args()
    return args


def main():
    args = _parse_arguments()

    # Get arguments from the config file
    config = configparser.ConfigParser()
    config.read(args.config)

    parzu_path = config["ParZu"]["ParZuPath"]
    if args.mode in ["annotate", "evaluate"]:
        print("[0] Initialize flair")
        initialize_flair()

        print("[0] Initialize STW taggers")
        initialize_stw_tagger()

        # parzu
        print("[0] Initialize ParZu")
        initialize_parzu(parzu_path)

    classifier_paths = {}
    for type_name, classifier_path in config.items("Classifier"):
        classifier_paths[type_name] = classifier_path 

    sieve_preselection = {}
    for sieve_name, selection in config.items("Sieve_Selection"):
        sieve_preselection[sieve_name] = selection

    parsed_sieves, parsed_classifier_paths = parse_sieve_selection(sieve_preselection, classifier_paths)

    # additional ressources
    verb_path = config["Ressources"]["VerbList"]
    mensch_path = config["Ressources"]["MenschList"]
    vocative_path = config["Ressources"]["VocativeList"]
    speech_noun_path = config["Ressources"]["SpeechNounList"]
    functional_verb_path = config["Ressources"]["FunctionalVerbList"]

    # print eval
    print_eval = args.print_eval

    if args.output_file_extension:
        extension = args.output_file_extension
    else:
        extension = "_annotated.tsv"

    # process texts
    collected_evaluations = []
    for filename in args.input:
        if args.output_dir:
            output_directory = Path(args.output_dir)
        else:
            output_directory = Path(os.path.dirname(filename))

        base_name = os.path.splitext(os.path.basename(filename))[0]
        outputfilename = output_directory / (base_name + extension)
        try:
            evaluation = process_text(filename, outputfilename, args.mode, parsed_sieves, parsed_classifier_paths, parzu_path, \
                verb_path, mensch_path, vocative_path, speech_noun_path, functional_verb_path, print_eval)
            if evaluation == 0:
                continue
            elif evaluation is not None:
                collected_evaluations.append(evaluation)
        except Exception as e:
            print("An error has occured: ")
            print(e)
            print("Skipping ...")
            continue

    # summarize evaluations
    if len(collected_evaluations) >= 1:
        print("="*70)
        if args.mode == "evaluate":
            join_stw_speaker(collected_evaluations)
        else:
            join_speaker(collected_evaluations)

    return 0


if __name__ == '__main__':
    exit(main())
