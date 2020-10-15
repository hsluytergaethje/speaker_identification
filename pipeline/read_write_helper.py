#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This files contains methods to read tsv- and txt-files. 
Additionally methods with which object of the type "Text"
can be written to a tsv-file. 
"""

import pickle
import pandas as pd
import csv

# read tsv-file to pandas dataframe
def read_tsv_df(full_filename):
    return pd.read_csv(full_filename, encoding="utf-8", delimiter="\t",\
                quoting=csv.QUOTE_NONE, na_filter=False)

# read txt file linewise
def read_txt(filename):
    text = []
    with open(filename, 'r', encoding="utf-8") as input_file:
        for line in input_file:
            text.append(line.strip())
    return text

# read txt file as one string
def read_raw(filename):
    with open(filename, 'r', encoding="utf-8") as input_file:
        text = input_file.read()
    return text


def read_files_from_directory(corpus_dir, ending=".txt", read_method=read_txt):
	corpus_dir = Path(corpus_dir)
	corpus = []
	filenames = []
	for filename in os.listdir(corpus_dir):
		full_filename = corpus_dir / filename
		text = read_method(full_filename)
		corpus.append(text)
		filenames.append(filename)
	return corpus, filenames

def load_pickled_data(filename):
    with open(filename, "rb") as pickled_data:
        dataset = pickle.load(pickled_data)
        return dataset

# process stw and speaker annotations from the rwk tsv files
def process_annotations(text, annotations, anno_type, offset=0):

	token_annos = [[] for i in range(text.token_number)]
	token_speakers = [[] for i in range(text.token_number)]

	for anno in annotations:
		anno_id = str(anno.id + offset)
		medium = anno.medium

		for token in anno.tokens:
			anno_tag = anno_type + "." + medium + "." + anno_id
			token_annos[token.id].append(anno_tag)

		if anno.has_speaker_prediction():
			for tok_id in anno.predicted_speaker:
				token_speakers[tok_id].append(str(anno_id))

	# generate tags from entries
	anno_column = []
	speaker_column = []

	for entry in token_annos:
		if len(entry) > 0:
			anno_column.append("|".join(entry))
		else:
			anno_column.append("-")

	for i, entry in enumerate(token_speakers):
		if len(entry) > 0:
			speaker_column.append("_".join(entry))
		else:
			speaker_column.append("-")

	return anno_column, speaker_column

# process 
def get_base_df(text):
	text_info = {"start":[], "end": [], "tok":[], "pos":[], "lemma":[], \
	"dependency":[], "parentID":[], "senID":[], "NER":[], "coreference":[]}

	for token in text.tokens:
		text_info["start"].append(token.start)
		text_info["end"].append(token.end)
		text_info["tok"].append(token.text)
		text_info["pos"].append(token.pos)
		text_info["lemma"].append(token.lemma)
		text_info["dependency"].append(token.dependency)
		text_info["parentID"].append(token.parent_token.id)
		text_info["senID"].append(token.sentence_id)
		text_info["NER"].append(token.ner)
		if token.has_coreferents():
			text_info["coreference"].append("|".join([str(coref_id) for coref_id in token.coreferent_ids]))
		else:
			text_info["coreference"].append("-")


	textdf = pd.DataFrame.from_dict(text_info)
	return textdf


def get_annotation_speaker_column(stw_type_to_text):
	current_offset = 0 
	anno_columns = []
	speaker_columns = []

	for stw_type, text in stw_type_to_text.items():
		anno, speaker = process_annotations(text, text.annotations, stw_type, current_offset)
		anno_columns.append(anno)
		speaker_columns.append(speaker)
		current_offset += text.annotation_number

	final_anno = []
	final_speaker = []

	for i in range(text.token_number):
		current_speakers = [speaker_col[i] for speaker_col in speaker_columns]
		current_annos = [anno_col[i] for anno_col in anno_columns]
		if all(anno == "-" for anno in current_annos):
			final_anno.append("-")
		else:
			filtered_anno = [anno for anno in current_annos if anno != "-"]
			final_anno.append("|".join(filtered_anno))

		if all(anno == "-" for anno in current_speakers):
			final_speaker.append("-")
		else:
			filtered_anno = [anno for anno in current_speakers if anno != "-"]
			final_indice = "_".join(filtered_anno)
			final_speaker.append("speaker." + final_indice)

	return final_anno, final_speaker

def write_annotations_to_tsv(stw_type_to_text_obj, outputfile):
	text_df = get_base_df(stw_type_to_text_obj["direct"])
	stwr_col, speaker_col = get_annotation_speaker_column(stw_type_to_text_obj)
	text_df.insert(6, "stwr", stwr_col)
	text_df.insert(7, "speaker", speaker_col)

	text_df.to_csv(outputfile, sep="\t", index=False, quoting=csv.QUOTE_NONE)