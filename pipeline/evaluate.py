#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This script includes functions to score
stw unit and speaker annotations.
"""

from dataclasses import dataclass, asdict
from typing import Union

STW_INDEX_KEY = "stwr_indice"

TRUE = "true"
PARTIAL = "partial"
NOT_FOUND = "not found"

SPEAKER = "speaker_indice"
SPEAKER_BACKUP = "speaker_backup_indice"


@dataclass
class stw_eval_info:
    true: int = 0
    partial: int = 0
    not_found: int = 0
    total: int = 0

@dataclass
class stw_metric:
    precision: float = 0.0
    recall: float = 0.0
    precision_loose: float = 0.0
    recall_loose: float = 0.0
    f1: float = 0.0
    f1_loose: float = 0.0

@dataclass
class speaker_eval_info:
    correct: int = 0
    partially_correct: int = 0
    coref_correct: int = 0
    coref_partially_correct: int = 0
    not_found: int = 0
    total: int = 0
    accuracy: float = 0.0
    accuracy_loose : float = 0.0

@dataclass
class speaker_eval_info_gold:
    correct: int = 0
    partially_correct: int = 0
    coref_correct: int = 0
    coref_partially_correct: int = 0
    not_found: int = 0
    total: int = 0
    with_speaker_gold: int = 0
    with_speaker_predicted: int = 0
    accuracy: float = 0.0
    accuracy_loose : float = 0.0


@dataclass
class stw_speaker_summary:
    pred_to_true: stw_eval_info
    true_to_pred: stw_eval_info
    speaker_eval: Union[speaker_eval_info, speaker_eval_info_gold]

def get_char_indice_per_annotation_and_speaker(text, predicted=False):
    annotations = text.annotations
    all_anno_infos = []
    for annotation in annotations:
        anno_char_info = {}
        anno_indice = []
        speaker_indice = []
        speaker_backup = []
        for token in annotation.tokens:
            char_indice = [i for i in range(token.start, token.end +1)]
            anno_indice.extend(char_indice)

        if predicted:
            if annotation.has_speaker_prediction():
                speaker_tokens = text.get_tokens_by_id(annotation.predicted_speaker)
            else:
                speaker_tokens = []
        else:
            if annotation.has_speaker():
                speaker_tokens = text.get_tokens_by_id(annotation.true_speaker_ids)
            else:
                speaker_tokens = []

        for token in speaker_tokens:
            char_indice = [i for i in range(token.start, token.end +1)]
            speaker_indice.extend(char_indice)
            if token.has_coreferents():
                coreferent_tokens = text.get_tokens_by_id(token.coreferent_ids)
                for coref_token in coreferent_tokens:
                    coref_char_indice = [i for i in range(coref_token.start, coref_token.end +1)]
                    speaker_backup.append(coref_char_indice)

        anno_char_info[STW_INDEX_KEY] = anno_indice
        anno_char_info[SPEAKER] = speaker_indice
        anno_char_info[SPEAKER_BACKUP] = speaker_backup
        all_anno_infos.append(anno_char_info)
    return all_anno_infos

def get_true_partial(idx_list_a: list[int], idx_list_b: list[int]):
    len_intersect = len(set(idx_list_a).intersection(set(idx_list_b)))
    if len_intersect == len(idx_list_a):
        return TRUE
    elif len_intersect > 0:
        return PARTIAL
    return NOT_FOUND


def compare(a: list[dict], b: list[dict], idx_key):
    evaluation = stw_eval_info()

    for a_unit in a:
        found = False
        found_true = False
        for b_unit in b:
            match_info = get_true_partial(a_unit[idx_key], b_unit[idx_key])
            if match_info == TRUE:
                evaluation.true += 1
                found_true = True
                break
            elif match_info == PARTIAL:
                found = True
        if found:
            evaluation.partial += 1
        elif not found_true:
            evaluation.not_found += 1
    evaluation.total = len(a)
    return evaluation

def f1(precision, recall):
    return 2 * ((precision * recall) / (precision + recall))

def get_metrics_stw(true_to_pred: stw_eval_info, pred_to_true:stw_eval_info):
    evaluation = stw_metric()
    if pred_to_true.total > 0:
        evaluation.precision = round((pred_to_true.true / pred_to_true.total) * 100, 2)
        evaluation.precision_loose = round(((pred_to_true.true + pred_to_true.partial) / pred_to_true.total) * 100, 2)
    if true_to_pred.total > 0:
        evaluation.recall = round((true_to_pred.true / true_to_pred.total) * 100, 2)
        evaluation.recall_loose = round(((true_to_pred.true + true_to_pred.partial) / true_to_pred.total) * 100, 2)
    if not (evaluation.recall == 0 and evaluation.precision == 0):
        evaluation.f1 = round(f1(evaluation.precision, evaluation.recall), 2)
    if not (evaluation.recall_loose == 0 and evaluation.precision_loose == 9):
        evaluation.f1_loose = round(f1(evaluation.precision_loose, evaluation.recall_loose))
    return evaluation

def add_dataclasses(list_of_dataclasses, speaker=False, speaker_gold=False):
    final = {key: 0 for key in asdict(list_of_dataclasses[0]).keys()}
    for eval_dict in list_of_dataclasses:
        for key, val in asdict(eval_dict).items():
            final[key] += val
    if speaker:
        summed = speaker_eval_info(**final)
    elif speaker_gold:
        summed = speaker_eval_info_gold(**final)
    else:
        summed = stw_eval_info(**final)
    return summed

# SPEAKER 
def map_annotations(a, b):
    mapping = []
    for a_unit in a:
        matching_annos = []
        for b_unit in b:
            len_intersect = len(set(a_unit[STW_INDEX_KEY]).intersection(set(b_unit[STW_INDEX_KEY])))
            if len_intersect > 0: # take all stw unit that have some overlap as possible stw units for speaker eval
                matching_annos.append(b_unit)
        mapping.append((a_unit, matching_annos))
    return mapping

def compare_speaker(a: dict, b: list[dict], eval_info:speaker_eval_info):
    pred_speaker = a[SPEAKER]

    found = False
    found_coref = False
    found_coref_partial = False

    for entry in b:
        # without coref info
        match_info = get_true_partial(pred_speaker, entry[SPEAKER])

        if match_info == TRUE:
            eval_info.correct += 1
            return
        elif match_info == PARTIAL:
            found = True
            continue

        # with coref info
        for pred_entry in a[SPEAKER_BACKUP]:
            for true_entry in entry[SPEAKER]:
                match_info_coref = get_true_partial(pred_entry, true_entry)
                if match_info_coref == TRUE:
                    found_coref = True
                elif match_info_coref == PARTIAL:
                    found_coref_partial = True
    if found_coref:
        eval_info.coref_correct += 1
        return
    if found:
        eval_info.partially_correct += 1
        return
    if found_coref_partial:
        eval_info.coref_partially_correct += 1
        return
    eval_info.not_found += 1
    return


def get_speaker_eval(annotation_mapping):
    eval_info = speaker_eval_info()

    for (predicted, true_annotations) in annotation_mapping:
        if len(true_annotations) > 0:
            eval_info. total += 1
            compare_speaker(predicted, true_annotations, eval_info)
    return eval_info

def get_accuracy_speaker(eval_count: Union[speaker_eval_info, speaker_eval_info_gold]):
    sum_true = eval_count.correct + eval_count.coref_correct
    sum_partial = eval_count.partially_correct + eval_count.coref_partially_correct
    if eval_count.total > 0:
        eval_count.accuracy = round((sum_true / eval_count.total) * 100, 2)
        eval_count.accuracy_loose = round(((sum_true + sum_partial) / eval_count.total) * 100, 2)
    return


def evaluate(predicted_object, true_object, eval_pred_speaker=True):
    if eval_pred_speaker:
        predicted_text = get_char_indice_per_annotation_and_speaker(predicted_object, predicted=True)
    else:
        predicted_text = get_char_indice_per_annotation_and_speaker(predicted_object) 
    true_text = get_char_indice_per_annotation_and_speaker(true_object)


    # evaluate stw
    pred_to_true = compare(predicted_text, true_text, STW_INDEX_KEY)
    true_to_pred = compare(true_text, predicted_text, STW_INDEX_KEY)


    # speaker
    mapping = map_annotations(predicted_text, true_text)
    eval_count = get_speaker_eval(mapping)

    eval_summary = stw_speaker_summary(
            pred_to_true = pred_to_true,
            true_to_pred = true_to_pred,
            speaker_eval = eval_count)

    return eval_summary




def get_eval_per_class(stw_text_per_type_pred, stw_text_per_type_true, write=True, eval_pred_speaker=True):
    eval_per_type = {}
    for stw_type, true_text in stw_text_per_type_true.items():
        eval_per_type[stw_type] = evaluate(stw_text_per_type_pred[stw_type], true_text, eval_pred_speaker=eval_pred_speaker)

    if write:
        print("Evaluation")
        print("===========")
        for stw_type, evaluation in eval_per_type.items():
            print(stw_type)
            print("STW")
            # could print the count numbers too
            stw_metrics = get_metrics_stw(evaluation.true_to_pred, evaluation.pred_to_true)
            pretty_print(asdict(stw_metrics))
            print("\nSPEAKER")
            get_accuracy_speaker(evaluation.speaker_eval)
            pretty_print(asdict(evaluation.speaker_eval))
            print("_"*70)

    return eval_per_type

def get_performance(text, coref=True):
    eval_info = speaker_eval_info_gold()

    eval_info.total += text.annotation_number
    if text.annotation_number > 0:
        for anno in text.annotations:
            true_speaker = anno.true_speaker_ids
            predicted_speaker = anno.predicted_speaker

            if true_speaker is not None:
                eval_info.with_speaker_gold += 1

            if len(predicted_speaker) > 0:
                eval_info.with_speaker_predicted += 1

                if true_speaker is not None:
                    if set(true_speaker) == set(predicted_speaker):
                        eval_info.correct += 1
                    elif len(set(predicted_speaker).intersection(set(true_speaker))) > 0:
                        eval_info.partially_correct += 1

                    elif is_coref_correct(text, predicted_speaker, true_speaker):
                        if coref:
                            eval_info.coref_correct += 1
                    elif is_coref_partly_correct(text, predicted_speaker, true_speaker):
                        if coref:
                            eval_info.coref_partially_correct += 1
                    else:
                        eval_info.not_found += 1
                else:
                    eval_info.not_found += 1
            else:
                if anno.true_speaker_ids is None:
                    eval_info.coref_correct += 1
                else:
                    eval_info.not_found += 1
        get_accuracy_speaker(eval_info)
    return eval_info


def join_stw_speaker(eval_info: list):
    stw_types = list(eval_info[0].keys())
    sorted_by_type = {key: [] for key in stw_types}
    for entry in eval_info:
        for stw_type in stw_types:
            sorted_by_type[stw_type].append(entry[stw_type])

    for stw_type, eval_info_list in sorted_by_type.items():
        true_to_preds = [entry.true_to_pred for entry in eval_info_list]
        pred_to_trues = [entry.pred_to_true for entry in eval_info_list]
        speaker_evals = [entry.speaker_eval for entry in eval_info_list]
        joined_true_to_preds = add_dataclasses(true_to_preds)
        joined_pred_to_trues = add_dataclasses(pred_to_trues)
        joined_speaker_evals = add_dataclasses(speaker_evals, speaker=True)
        print(stw_type)
        get_accuracy_speaker(joined_speaker_evals)
        stw_metric = get_metrics_stw(joined_true_to_preds, joined_pred_to_trues)
        print("STW")
        pretty_print(asdict(stw_metric))
        print("SPEAKER")
        pretty_print(asdict(joined_speaker_evals))
        print("="*70)
    return

def join_speaker(eval_info: dict):
    stw_types = list(eval_info[0].keys())
    sorted_by_type = {key: [] for key in stw_types}
    for entry in eval_info:
        for stw_type in stw_types:
            sorted_by_type[stw_type].append(entry[stw_type])

    for stw_type, eval_info_list in sorted_by_type.items():
        print(stw_type)
        #speaker_evals = [entry.speaker_eval for entry in eval_info_list]
        joined_speaker_evals = add_dataclasses(eval_info_list, speaker_gold=True)
        get_accuracy_speaker(joined_speaker_evals)
        pretty_print(asdict(joined_speaker_evals))
        print("="*70)
    return


def pretty_print(eval_dict):
    for key, val in eval_dict.items():
        print("{}\t{}".format(key, val))


def is_coref_correct(text, pred_ids, true_ids):
    if true_ids is not None:
        if pred_ids is None or len(pred_ids) == 0:
            return False
        all_corefs = []
        true_tokens = text.get_tokens_by_id(true_ids)

        for tok in true_tokens:
            if tok.has_coreferents():
                all_corefs.extend(tok.coreferent_ids)

        return all(speak_id in all_corefs for speak_id in pred_ids)
    else:
        if pred_ids is None or len(pred_ids) == 0:
            return True
    return False

def is_coref_partly_correct(text, pred_ids, true_ids):
    if true_ids is not None:
        if pred_ids is None or len(pred_ids) == 0:
            return False
        all_corefs = []
        true_tokens = text.get_tokens_by_id(true_ids)

        for tok in true_tokens:
            if tok.has_coreferents():
                all_corefs.extend(tok.coreferent_ids)

        return any(speak_id in all_corefs for speak_id in pred_ids)
    else:
        if pred_ids is None or len(pred_ids) == 0:
            return True
    return False



# CALLED IN STW ANNO
def evaluate_stwr_gold_annotations(stwr_anno_per_type, write=True):
    eval_per_type = {}
    for stw_type, true_text in stwr_anno_per_type.items():
        eval_per_type[stw_type] = get_performance(true_text)

    if write:
        print("Evaluation")
        print("===========")
        for stw_type, evaluation in eval_per_type.items():
            print(stw_type)
            pretty_print(asdict(evaluation))
            print("_"*70)

    return eval_per_type


def write_evalutation(outputfilename, eval_per_type):
    with open(outputfilename, 'w') as out:
        header = list(eval_per_type["direct"].keys())
        out.write("STW type/Description\t")
        out.write("{}\n".format("\t".join(header)))

        for stw_type, evaluation in eval_per_type.items():
            vals = [evaluation[key] for key in header]
            out.write("{}\t{}\n".format(stw_type, "\t".join(vals)))


