# Speaker Identification for Speech, Thought and Writing in the Literary Domain

This repository contains a pipeline to annotate raw text with speech, thought and writing instances (STW units) and their respective speakers. Four representations of stw units are annotated: direct, indirect, reported and free indirect. For the annotation of the stw units, the STW recognition tool developed by Schricker et al., 2019 [1] is used. For the identification of the speakers, four sieve systems are used (based on Muzny et al, 2017 [2]), one system for each type of representation. The sieve systems are provided in this repository. 

The systems were developed with the help of a subset of the corpus Redewiedergabe (https://github.com/redewiedergabe/corpus). Preprocessed files can be found in corpus/annotated. Tokenized texts can be found in corpus/sentences.
The sieve systems rely on precompiled lists, stored in resources/. In three of the four systems, binary classifiers are applied, the models are stored in models/.  

The pipeline includes the following preprocessing steps: sentence splitting, tokenization,  lemmatization, PoS-tagging, Dependency Parsing and Named Entity Recognition.  


### Additional Tools
For the preprocessing of raw text two external tools need to be installed:
* STW recognition tool (https://github.com/LuiseHenriette/STW_recognition_tool)
* ParZu (https://github.com/rsennrich/ParZu)


### Pipeline
The pipeline has four different modes:
1. __annotate__: Input is raw text, prepocessing is applied, stw units are predicted and speaker are identified on the basis of the predicted stw units.  
2. __speaker annotate__: Input is annotated text (examples in corpus/annotated), the speaker identificatino is performed on the basis of gold stw annotations. 
3. __evaluate__: Input is annotated text. Speakers are identified on the basis of predicted stw units. The annotation of stw units and speakers is evaluated. The evaluation is printed to the console. 
4. __evaluate gold__: Input is annotated text. Speakers are identified on the basis of gold stw units. The speaker annotations are evaluated. The evaluation is printed to the console.

In all modes, the annotations are written to a tsv-file. The default mode is __annotate__. 
For the options __speaker annotate__ and __evaluate gold__ no preprocessing is performed, therefore the additional tools do not need to be installed. 

In the config file in pipeline/, the sieves that should be applied can be selected, parameters for the stw recognition tool can be set and the paths to the additional tools, the resources files and the binary classifiers can be set. 

### Example usages:

1. Annotation of raw text - no evaluation
```
python stwr_speaker_annotation.py -c config.ini ../corpus/sentences/rwk_mkhz_6360-1.xmi.sentences.txt
```
Since no output directory is specified, the output file will be written to the directory corpus/sentence. It will not overwrite the input file, the extension of the output file is "_annotated.tsv".

2. Speaker annotation of annotated text with evaluation
```
python stwr_speaker_annotation.py -c config.ini -m evaluate_gold ../corpus/annotated/* -o ../speaker_annotations/
```
For all files in the directory corpus/annotated the speakers are predicted. The outputfiles are written to the folder speaker_annotations in the root directory of this repository (needs to be created first). The overall evaluation is printed to the console. If the evaluation should be printed per file, the option "-p" (or --print_eval) can be added. 


[1] Luise Schricker, Manfred Stede, and Peer Trilcke. Extraction and classification of speech, thought, and writing in german narrative texts. In Proceedings of the 15th Conference on Natural Language Processing (KONVENS 2019), pages 183–192, Erlangen, Germany, October 2019.

[2] Grace Muzny, Michael Fang, Angel Chang, and Dan Jurafsky. A two-stage sieve approach for quote attribution. In Proceedings of the 15th Conference of the European Chapter of the Association for Computational Linguistics: Volume 1, Long Papers, pages 460–470, Valencia, Spain, April 2017. Association for Computational Linguistics.
