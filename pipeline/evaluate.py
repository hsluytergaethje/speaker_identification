#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This script includes functions to score 
stw unit and speaker annotations. 
"""

from collections import Counter
import pandas as pd


def score_matching_indice(predicted, true):
	predicted = set(predicted)
	true = set(true)
	coinciding = len(true.intersection(predicted))
	percentage_pred = int((coinciding / len(predicted)) * 100)
	percentage_true = int((coinciding / len(true)) * 100)
	return coinciding, percentage_pred, percentage_true


def several_max(max_ids):
	return len(max_ids) > 1


def get_max_id(scores):
	max_ids = []
	max_score = max(scores)
	for i, score in enumerate(scores):
		if score == max_score:
			max_ids.append(i)
	return max_ids

# extract matching annotations
def get_matching_rwk_annos(kalli_annos, rwk_annos):
	matching_annos = []
	percentages_trues = []
	percentages_preds = []
	for i, anno in enumerate(kalli_annos):
		
		indice = anno["stwr_indice"]
		perc_preds = []
		perc_trues = []
		
		for rwk_anno in rwk_annos:
			rwk_indice = rwk_anno["stwr_indice"]
			coinc, percentage_pred, percentage_true = score_matching_indice(indice, rwk_indice)
			perc_preds.append(percentage_pred)
			perc_trues.append(percentage_true)            
		
		pred_ids_max = get_max_id(perc_preds)
		true_ids_max = get_max_id(perc_trues)
		
			
		if several_max(pred_ids_max):
			if several_max(true_ids_max):
				uniques = list(set(perc_preds))
				if len(uniques) == 1:
					if uniques[0] == 0:
						corresponding_annos = None
						percentages_preds.append(-1)
						percentages_trues.append(-1)
					else:
						print("all same values but not 0")
						print(perc_preds)
				else:
					if pred_ids_max == true_ids_max:
						corresponding_annos = pred_ids_max
						percentages_preds.append([perc_preds[j] for j in pred_ids_max])
						percentages_trues.append([perc_trues[j] for j in pred_ids_max])
					else:
						# TODO: find better solution - other way ot match these annotations? 
						corresponding_annos = None
						percentages_preds.append(-1)
						percentages_trues.append(-1)
						print("several maxima .. ")
						print(perc_preds)
						print(i)
						print(perc_trues)
			else:
				true_id_max = true_ids_max[0]
				if true_id_max in pred_ids_max:
					corresponding_annos = true_ids_max
					percentages_preds.append([perc_preds[true_id_max]])
					percentages_trues.append([perc_trues[true_id_max]])
				else:
					corresponding_annos = None
					percentages_preds.append(-1)
					percentages_trues.append(-1)
					print("best true not in pred")
					print(perc_preds)
					print(i)
					print(perc_trues)
		else:
			corresponding_annos = pred_ids_max
			percentages_preds.append([perc_preds[pred_ids_max[0]]])
			percentages_trues.append([perc_trues[pred_ids_max[0]]])
		
		matching_annos.append(corresponding_annos)
				

	return matching_annos, percentages_preds, percentages_trues


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

		anno_char_info["stwr_indice"] = anno_indice
		anno_char_info["speaker_indice"] = speaker_indice
		anno_char_info["speaker_backup_indice"] = speaker_backup
		all_anno_infos.append(anno_char_info)
	return all_anno_infos

def evaluate_speakers(kalli_anno, rwk_annos):
	kalli_speaker = set(kalli_anno["speaker_indice"])
	kalli_backups = []
	if "speaker_backup_indice" in kalli_anno:
		for speaker_backup in kalli_anno["speaker_backup_indice"]:
			kalli_backups.append(set(speaker_backup))

	rwk_speakers = [rwk_anno["speaker_indice"] for rwk_anno in rwk_annos]
	
	correct = 0
	partial = 0
	
	for speaker in rwk_speakers:
		speaker = set(speaker)
		if len(speaker.intersection(kalli_speaker)) == len(speaker) or \
		any(len(speaker.intersection(kalli_backup)) == len(speaker) for kalli_backup in kalli_backups):
			correct += 1
		elif len(speaker.intersection(kalli_speaker)) > 0 or \
		any(len(speaker.intersection(kalli_backup)) > 0 for kalli_backup in kalli_backups):
			partial += 1
	
	if correct == len(rwk_speakers):
		return "correct"
	elif partial > 0:
		return "partial"
	else:
		return "wrong"


def get_rwk_matches(mappings):
	all_numbers = []
	for mapping in mappings:
		if mapping is not None:
			for element in mapping:
				if element is not None:
					all_numbers.append(element)
	return all_numbers

def rwk_double_annotated(rwk_matches):
	return len(rwk_matches) != len(set(rwk_matches))


def get_double_values(rwk_matches):
	counted = Counter(rwk_matches)
	doubles = []
	for val, count in counted.most_common():
		if count > 1:
			doubles.append(val)
	return doubles

def get_anno_id_by_value(mappings, rwk_values):
	kalli_ids = {}
	for rwk_val in rwk_values:
		kalli_ids[rwk_val] = []
	
	for i, rwk_id_list in enumerate(mappings):
		if rwk_id_list is not None:
			for rwk_value in rwk_values:
				if rwk_value in rwk_id_list:
					kalli_ids[rwk_value].append(i)
	return kalli_ids


def handle_double_annotation(preds, trues):
	true_100 = []
	to_keep = []
	for i, perc_true in enumerate(trues):
		if 100 in perc_true:
			true_100.append(i)
	if len(true_100) < 1:
		for i, perc_pred in enumerate(preds):
			if perc_pred == 100 or 100 in perc_pred: # changed to "100 in" for pipeline eval 
				to_keep.append(i)
	else:
		to_keep.extend(true_100)
	return to_keep


# evaluate per file 
def evaluate_stwrs(kalli_annos, rwk_annos, mappings, perc_pred, perc_true):
	eval_values = {"not_found":0, "invented":0, "stwr_correct":0, "stwr_partial": 0, "contracted":0, \
				  "speaker_correct":0, "speaker_partial":0, "speaker_wrong":0}
	
	rwk_instances = len(rwk_annos)
	rwk_matches = get_rwk_matches(mappings)
	number_rwk_matched = len(set(rwk_matches))
	
	eval_values["not_found"] = rwk_instances - number_rwk_matched
	
	try:
		if rwk_double_annotated(rwk_matches):
			double_rwk_ids = get_double_values(rwk_matches)
			rwk_to_kalli_ids = get_anno_id_by_value(mappings, double_rwk_ids)
			for rwk_id, kalli_values in rwk_to_kalli_ids.items():
				preds = [perc_pred[i] for i in kalli_values]
				trues = [perc_true[i] for i in kalli_values]

				to_keep = handle_double_annotation(preds, trues)

				for i in range(len(kalli_values)):
					if i not in to_keep:
						mappings[kalli_values[i]] = None
				rwk_matches = get_rwk_matches(mappings)
	except:
		print(rwk_matches)
		print(rwk_to_kalli_ids)
		print(perc_pred)
		print(perc_true)
		return None
	
	for i, (mapping, pred, true) in enumerate(zip(mappings, perc_pred, perc_true)):
		if mapping is None:
			eval_values["invented"] += 1
		else:
			if len(mapping) > 1:
				eval_values["contracted"] += 1
			for mapping_index in range(len(mapping)):
				if true[mapping_index] == 100 and pred[mapping_index] == 100:
					eval_values["stwr_correct"] += 1
				else:
					# we can assume this, since the annotations coincided 
					eval_values["stwr_partial"] += 1
	
	speaker_correct = 0
	speaker_partial = 0
	speaker_wrong = 0
	for i in range(len(mappings)):
		if mappings[i] is not None:
			current_kalli = kalli_annos[i]
			current_rwks = [rwk_annos[rwk_index] for rwk_index in mappings[i]]
			speaker_eval = evaluate_speakers(current_kalli, current_rwks)
			if speaker_eval == "correct":
				eval_values["speaker_correct"] += 1
			elif speaker_eval == "partial":
				eval_values["speaker_partial"] += 1
			else:
				eval_values["speaker_wrong"] += 1

	accuracies = calculate_metrics(eval_values, rwk_annos)
	eval_values.update(accuracies)
	
	return eval_values

def calculate_metrics(evaluation, true_text):
	accuracies = {"stwr_accuracy_loose":0, "stwr_accuracy_strict":0, "speaker_accuracy_loose":0, \
				   "speaker_accuracy_strict":0}
	
	all_rwk_instances = len(true_text)
	
	rwk_predicted_total = evaluation['stwr_correct'] + evaluation['stwr_partial']
	

	if all_rwk_instances > 0 and rwk_predicted_total > 0:
		accuracies["stwr_accuracy_loose"] = round(((evaluation['stwr_correct'] + evaluation['stwr_partial']) / all_rwk_instances) *100, 2)
		accuracies["stwr_accuracy_strict"] = round((evaluation['stwr_correct'] / all_rwk_instances)*100, 2)
		
		accuracies["speaker_accuracy_loose"] = round(((evaluation["speaker_correct"] + evaluation["speaker_partial"]) / rwk_predicted_total) *100, 2)
		accuracies["speaker_accuracy_strict"] = round((evaluation["speaker_correct"] / rwk_predicted_total)*100, 2)
	
	return accuracies
	

def evaluate(predicted_object, true_object, eval_pred_speaker=True):
	if eval_pred_speaker:
		predicted_text = get_char_indice_per_annotation_and_speaker(predicted_object, predicted=True)
	else:
		predicted_text = get_char_indice_per_annotation_and_speaker(predicted_object) 
	true_text = get_char_indice_per_annotation_and_speaker(true_object)

	if len(true_text) > 1:
		matching_annos, perc_pred, perc_true = get_matching_rwk_annos(predicted_text, true_text)
	else:
		matching_annos = [None]* len(predicted_text)
		perc_pred = [None]* len(predicted_text)
		perc_true = [None]* len(predicted_text)
	return evaluate_stwrs(predicted_text, true_text, matching_annos, perc_pred, perc_true)


def pretty_print(eval_dict):
	for key, val in eval_dict.items():
		print("{}\t{}".format(key, val))


# evaluate and print evaluation 
def get_eval_per_class(stw_text_per_type_pred, stw_text_per_type_true, write=True, eval_pred_speaker=True):
	eval_per_type = {}
	for stw_type, true_text in stw_text_per_type_true.items():
		eval_per_type[stw_type] = evaluate(stw_text_per_type_pred[stw_type], true_text, eval_pred_speaker=eval_pred_speaker)

	if write:
		print("Evaluation")
		print("===========")
		for stw_type, evaluation in eval_per_type.items():
			print(stw_type)
			pretty_print(evaluation)
			print("_"*70)

	return eval_per_type


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


def get_performance(text, coref=False):
	meta = {"annotation_number": 0, "annotation_number_with_speaker":0, "predicted_num_speaker": 0, "speaker_correct":0, \
	 "speaker_part_corr": 0, "speaker_coref_correct": 0, "speaker_coref_partly_correct": 0, "speaker_accuracy_strict": 0, \
	 "speaker_accuracy_loose": 0}

	meta["annotation_number"] += text.annotation_number
	if text.annotation_number > 0:
		for anno in text.annotations:
			if anno.true_speaker_ids is not None:
				meta["annotation_number_with_speaker"] += 1
				
			if len(anno.predicted_speaker) > 0:
				meta["predicted_num_speaker"] += 1
				if anno.true_speaker_ids is not None:
					if all(speak_id in anno.true_speaker_ids for speak_id in anno.predicted_speaker):
						if all(speak_id in anno.predicted_speaker for speak_id in anno.true_speaker_ids):
							meta["speaker_correct"] += 1
						else:
							meta["speaker_part_corr"] += 1
					elif any(speak_id in anno.true_speaker_ids for speak_id in anno.predicted_speaker):
						meta["speaker_part_corr"] += 1

					elif is_coref_correct(text, anno.predicted_speaker, anno.true_speaker_ids):
						if coref:
							meta["speaker_coref_correct"] += 1
					elif is_coref_partly_correct(text, anno.predicted_speaker, anno.true_speaker_ids):
						if coref:
							meta["speaker_coref_partly_correct"] += 1
			else:
				if anno.true_speaker_ids is None:
					meta["speaker_correct"] += 1

		acc_strict = round((meta["speaker_correct"] + meta["speaker_coref_correct"]) / meta["annotation_number"] * 100, 2)
		acc_loose = round((meta["speaker_correct"] + meta["speaker_part_corr"] + meta["speaker_coref_correct"] \
			+ meta["speaker_coref_partly_correct"]) / meta["annotation_number"] * 100, 2)   
		meta["speaker_accuracy_strict"] = acc_strict
		meta["speaker_accuracy_loose"] = acc_loose
	return meta

def evaluate_stwr_gold_annotations(stwr_anno_per_type, write=True):
	eval_per_type = {}
	for stw_type, true_text in stwr_anno_per_type.items():
		eval_per_type[stw_type] = get_performance(true_text)

	if write:
		print("Evaluation")
		print("===========")
		for stw_type, evaluation in eval_per_type.items():
			print(stw_type)
			pretty_print(evaluation)
			print("_"*70)

	return eval_per_type

def join_evaluations(eval_list):
	joined_evals = {}
	stw_types = list(eval_list[0].keys())
	eval_components = list(eval_list[0][stw_types[0]].keys())

	for stw_type in stw_types:
		joined_evals[stw_type] = {key:0 for key in eval_components}

	for eval_dict in eval_list:
		for stw_type, evaluation in eval_dict.items():
			for eval_comp, val in evaluation.items():
				joined_evals[stw_type][eval_comp] += val

	for stw_type, evaluation in joined_evals.items():
		actual_acc = evaluation["speaker_accuracy_strict"] / len(eval_list)
		actual_acc_loose = evaluation["speaker_accuracy_loose"] / len(eval_list)
		joined_evals[stw_type]["speaker_accuracy_strict"] = actual_acc
		joined_evals[stw_type]["speaker_accuracy_loose"] = actual_acc_loose

	print("Overall Evaluation")
	print("===================")
	for stw_type, evaluation in joined_evals.items():
		print(stw_type)
		pretty_print(evaluation)
		print("_"*70)
	return joined_evals

def write_evalutation(outputfilename, eval_per_type):
	with open(outputfilename, 'w') as out:
		header = list(eval_per_type["direct"].keys())
		out.write("STW type/Description\t")
		out.write("{}\n".format("\t".join(header)))

		for stw_type, evaluation in eval_per_type.items():
			vals = [evaluation[key] for key in header]
			out.write("{}\t{}\n".format(stw_type, "\t".join(vals)))


