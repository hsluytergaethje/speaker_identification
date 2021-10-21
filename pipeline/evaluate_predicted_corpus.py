#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Evaluate stwr predictions and speaker annotations independent from the 
the prediction process. 
"""
import os
import argparse
import configparser

from read_write_helper import read_tsv_df
from Text import create_text_class
from stwr_speaker_annotation import get_txt_object_from_gold_annotations
from evaluate import get_eval_per_class, write_evalutation, join_evaluations

def read_corpus(filenames,  verb_path, mensch_path, vocative_path, extension=".tsv", \
	coreference=True, character_index=True):
	filename_texts = {}
	for filename in filenames:
		pure_filename = os.path.basename(filename).split(extension)[0]
		filename_texts[pure_filename] = get_txt_object_from_gold_annotations(filename, verb_path, 
			mensch_path, vocative_path, coreference=coreference, character_index=character_index)
	return filename_texts

def evaluate_corpus(filename_text_true, filename_text_predicted):
	filename_evaluation = {}
	for filename, text_predicted in filename_text_predicted.items():
		if filename in filename_text_true:
			evaluation = get_eval_per_class(text_predicted, filename_text_true[filename], write=False, eval_pred_speaker=False)
			filename_evaluation[filename] = evaluation
		else:
			print(f"The filename {filename} is not in the list of gold annotations.")
			print("Skipping...")

	join_evaluations(list(filename_evaluation.values()))
	return filename_evaluation


def _parse_arguments():
	task_description = "Compare Speech, Thought, Writing and Speaker annotations with gold annotations."
	parser = argparse.ArgumentParser(description=task_description)

	parser.add_argument("-c", "--config", help="Set path/to/config.ini", required=True)
	parser.add_argument("-p", "--predicted", nargs='+', help="Set (multiple) path/to/predicted/inputfile/", 
		required=True)
	parser.add_argument("-g", "--gold", nargs='+', help="Set (multiple) path/to/gold/inputfile/", required=True)

	ep_help = """Set to the extension of the predicted file, e.g. \"annotated.tsv\". The basename (removing the 
	extension of the file) should be equivalent to the basename of the gold file."""
	parser.add_argument("-ep", "--extension_predicted", help=ep_help, default="_annotated.tsv")

	eg_help = """Set to the extension of the gold file, e.g. \".tsv\". The basename (removing the 
	extension of the file) should be equivalent to the basename of the predicted file."""
	parser.add_argument("-eg", "--extension_gold", help=eg_help, default=".tsv")


	write_eval_help = "Write evaluation per file to an outputfile. The evaluation file will be named: inputfile_eval.tsv"
	parser.add_argument("-w", "--write_eval", help=write_eval_help, action="store_true", default=False)

	parser.add_argument("-o", "--output_dir", help="Set path/to/output/directory for evaluation files.", \
		default="evaluations")

	args = parser.parse_args()
	return args


def main():
	args = _parse_arguments()

	# Get arguments from the config file
	config = configparser.ConfigParser()
	config.read(args.config)

	# additional ressources
	verb_path = config["Ressources"]["VerbList"]
	mensch_path = config["Ressources"]["MenschList"]
	vocative_path = config["Ressources"]["VocativeList"]

	# extensions
	true_ext = args.extension_gold
	pred_ext = args.extension_predicted
	eval_ext = "_eval.tsv"

	# read in corpus
	predicted_corpus = read_corpus(args.predicted, verb_path, mensch_path, vocative_path, pred_ext, \
		coreference=False)
	true_corpus = read_corpus(args.gold, verb_path, mensch_path, vocative_path, true_ext)

	print(predicted_corpus.keys())
	print(true_corpus.keys())

	# evaluate
	evaluated = evaluate_corpus(true_corpus, predicted_corpus)

	if args.write_eval:
		output_directory = Path(args.output_dir)
		if not output_directory.exists():
			os.mkdir(output_directory)
	
		for filename, evaluation in evaluated.items():
			base_name = os.path.basename(filename)
			outputfilename = output_directory / (base_name + eval_ext)
			write_eval(outputfilename, evaluation)

	return 0

if __name__ == '__main__':
	exit(main())

