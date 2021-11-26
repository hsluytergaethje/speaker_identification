#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Extract candidate-stw-unit pairs from context
and featurize. Serves as input for the binary classifier. 
"""

import sys
from tqdm import tqdm

from feature_extraction_binary_classifier import get_all_features
from feature_extraction_binary_classifier_int import get_all_int_features
from read_write_helper import read_files_from_directory
from Text import create_corpus_classes, TokenList


def get_all_candidates(text):
	candidates = [token for token in text.tokens if token.is_candidate()]
	return candidates


def get_closest_coreferent(text, annotation, coreferent_tokens):
	distances = [text.get_distance_tok_anno(token, annotation) for token in coreferent_tokens]
	min_dist = min(distances)
	closest_coreferent = coreferent_tokens[distances.index(min_dist)]
	return closest_coreferent

def get_labels(text, annotation, candidates):
	labels = [0]*len(candidates)
	if annotation.true_speaker_ids is None:
		return labels
	else:
		speaker_tokens = text.get_tokens_by_id(annotation.true_speaker_ids)
		if any(token.is_candidate() for token in speaker_tokens):
			coreferent_tok_ids = []
			for token in speaker_tokens:
				if token.has_coreferents():
					coreferent_tok_ids.extend(token.coreferent_ids)
			coreferent_tokens = text.get_tokens_by_id(coreferent_tok_ids)
			candidate_coreferents = [token for token in coreferent_tokens if token.is_candidate()]
			if len(candidate_coreferents) > 0:
				closest = get_closest_coreferent(text, annotation, coreferent_tokens)
				speaker_tokens = [closest]
			else:
				return labels
		
		for i, candidate in enumerate(candidates):
			if candidate.id in annotation.true_speaker_ids:
				labels[i] = 1
	return labels


def get_narrow_context(text, annotation, window=4):
	start_sen_id = annotation.start_token.sentence_id
	end_sen_id = annotation.end_token.sentence_id

	if start_sen_id - window >= 0:
		context_start_id = start_sen_id - window
	else:
		context_start_id = 0 

	if end_sen_id + window < text.sentence_number:
		context_end_id = end_sen_id + window
	else:
		context_end_id = text.sentence_number 

	if annotation.has_speaker():
		speaker_tokens = text.get_tokens_by_id(annotation.true_speaker_ids)
		speaker_sen_ids = sorted([tok.sentence_id for tok in speaker_tokens])

		if speaker_sen_ids[0] < context_start_id:
			context_start_id = speaker_sen_ids[0]
		if speaker_sen_ids[-1] > context_end_id:
			context_end_id  = speaker_sen_ids[-1]

	anno_sentences_ids = [i for i in range(context_start_id, context_end_id)]
	context_sentences = text.get_sentences_by_ids(anno_sentences_ids)

	all_tokens = []
	for sentence in context_sentences:
		all_tokens.extend(sentence.tokens)

	context = TokenList(all_tokens)

	return context

def get_features_representation_per_annotation(text, annotation, use_int=True):
	context = get_narrow_context(text, annotation)
	candidates = get_all_candidates(context)
	if use_int:
			candidate_features = get_all_int_features(text, annotation, candidates, context)
	else:
		candidate_features = get_all_features(text, annotation, candidates, context)
	return candidate_features, candidates


def get_feature_representations(text, use_int=False):
	dataset = []
	for annotation in text.annotations:
		context = get_narrow_context(text, annotation)
		candidates = get_all_candidates(context)
		candidate_features = get_all_features(text, annotation, candidates, context)
		if use_int:
			candidate_features = get_all_int_features(text, annotation, candidates, context)
		else:
			candidate_features = get_all_features(text, annotation, candidates, context)
		labels = get_labels(text, annotation, candidates)
		if len(candidate_features) != len(labels):
			print("Error! Different number of candidates and labels!")
			print("Number of labels: {}".format(len(labels)))
			print("Number of candidates: {}".format(len(candidate_features)))
			return False
		else:
			for i in range(len(labels)):
				dataset.append((candidate_features[i], labels[i]))
	return dataset


def create_dataset(corpus):
	dataset = []
	for text in tqdm(corpus):
		dataset.extend(get_feature_representations(text))
	return dataset

def get_features_labels_from_corpus_dir(corpus_dir):
	corpus, filenames = read_files_from_directory(corpus_dir, ending=".tsv", read_method=read_tsv_df)
	print("Creating text objects...")
	corpus_classes = create_corpus_classes(corpus, ["direct"])
	print("Done.")
	print("Starting feature extration...")
	dataset = create_dataset(corpus_classes)
	print("Done.")
	return dataset


def main(args):
	if len(args) != 2:
		print("usage: {} path/to/corpus/directory".format(args[0]))
		return 0

	dataset = get_features_labels_from_corpus_dir(args[1])
	print(len(dataset))
	print(dataset[0])

	return 1

if __name__ == '__main__':
	exit(main(sys.argv))

