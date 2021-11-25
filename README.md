# Speaker Identification for Speech, Thought and Writing in the Literary Domain

This repository contains a pipeline to annotate German raw text with speech, thought and writing instances (STW units) and their respective speakers. Four representations of STW units are annotated: direct, indirect, reported and free indirect. For the annotation of the STW units, the [STW recognition tool](https://github.com/redewiedergabe/tagger) developed by [Brunner et al. (2020a)](http://ceur-ws.org/Vol-2624/paper5.pdf) [^1] is used.

For the identification of the speakers, four sieve systems are used (based on [Krug et al. (2016)](https://dhd2016.de/abstracts/vortr%C3%A4ge-040.html) [^2] and [Muzny et al. (2017)](https://aclanthology.org/E17-1044.pdf) [^3]), one system for each type of representation. The sieve systems are provided in this repository. 

The systems were developed with the help of a subset of the [Corpus Redewiedergabe](https://github.com/redewiedergabe/corpus) ([Brunner et al. 2020b](https://aclanthology.org/2020.lrec-1.100.pdf) [^4]). Preprocessed files can be found in `corpus/annotated/`. Tokenized texts can be found in corpus/sentences.
A subset of the corpus which was used as a held-out testset to evaluate the speaker identification systems can be found in `corpus/test_set`. 
The sieve systems rely on precompiled lists, stored in `resources/`. In three of the four systems, binary classifiers are applied, the models are stored in `models/`.  

The pipeline includes the following preprocessing steps: sentence splitting, tokenization,  lemmatization, PoS-tagging, Dependency Parsing and Named Entity Recognition. It is depicted in `documents/images`. 


### Additional Tool
For the preprocessing of raw text [ParZu](https://github.com/rsennrich/ParZu) ([Sennrich et al. 2013](https://aclanthology.org/R13-1079.pdf) [^5]) needs to be installed. The STW recognition tool and the Named Entity Recognizer are available in the [flair](https://github.com/flairNLP/flair) ([Akbik et al. 2018](http://aclanthology.lst.uni-saarland.de/C18-1139.pdf) [^6]) library. 


### Pipeline
The pipeline has four different modes:
1. __annotate__: Input is raw text, prepocessing is applied, STW units are predicted and speaker are identified on the basis of the predicted STW units.  
2. __speaker annotate__: Input is annotated text (examples in `corpus/annotated/`), the speaker identificatino is performed on the basis of gold STW annotations. 
3. __evaluate__: Input is annotated text. Speakers are identified on the basis of predicted STW units. The annotation of STW units and speakers is evaluated. The evaluation is printed to the console. 
4. __evaluate gold__: Input is annotated text. Speakers are identified on the basis of gold STW units. The speaker annotations are evaluated. The evaluation is printed to the console.

In all modes, the annotations are written to a tsv-file. The default mode is __annotate__. 
For the options __speaker annotate__ and __evaluate gold__ no preprocessing is performed, therefore the additional tools do not need to be installed. 

To be able to use all available modes, the packages indicated in the file `requirements_preprocessing.txt` need to be installed and the paths in the config file need to be changed to absolute paths. If speakers should only be identified for already annotated files, it is enough to install the packages indicated in the file `requirements_annotated.txt`. 

In the config file in `pipeline/`, the sieves that should be applied can be selected and the paths to the additional tools, the resources files and the binary classifiers can be set. 

### Example usages:

1. Annotation of raw text - no evaluation
```
python stwr_speaker_annotation.py -c config.ini ../corpus/sentences/rwk_mkhz_6360-1.xmi.sentences.txt
```
Since no output directory is specified, the output file will be written to the directory `corpus/sentence`. It will not overwrite the input file, the suffix of the output file is `_annotated.tsv`.

2. Speaker annotation of annotated text with evaluation
```
python stwr_speaker_annotation.py -c config.ini -m evaluate_gold ../corpus/annotated/* -o ../speaker_annotations/
```
For all files in the directory `corpus/annotated/` the speakers are predicted. The output files are written to the folder `speaker_annotations` in the root directory of this repository (needs to be created first). The overall evaluation is printed to the console. If the evaluation should be printed per file, the option `-p` (or `--print_eval`) can be added. 

### References 

[^1]: Annelen Brunner, Ngoc Duyen Tanja Tu, Lukas Weimer and Fotis Jannidis. To bert or not to bert–comparing contextual embeddings in a deep learning architecture for the automatic recognition of four types of speech, thought and writing representation. In Proceedings of the 16th Conference on Natural Language Processing (KONVENS 2020), Zurich, Switzerland, June 2020a.
 
[^2]: Markus Krug, Fotis Jannidis, Isabella Reger, Luisa Macharowsky, Lukas Weimer and Frank Puppe. Attribuierung direkter Reden in deutschen Romanen des 18.-20. Jahrhunderts. Methoden zur Bestimmung des Sprechers und des Angesprochenen. In DHd 2016, Modellierung - Vernetzung - Visualisierung, Die Digital Humanities als fächerübergreifendes Forschungsparadigma, Konferenzabstracts, pages 124–130, Leipzig, Germany, March 2016.
 
[^3]: Grace Muzny, Michael Fang, Angel Chang, and Dan Jurafsky. A two-stage sieve approach for quote attribution. In Proceedings of the 15th Conference of the European Chapter of the Association for Computational Linguistics: Volume 1, Long Papers, pages 460–470, Valencia, Spain, April 2017. Association for Computational Linguistics.

[^4]: Annelen Brunner, Stefan Engelberg, Fotis Jannidis, Ngoc Duyen Tanja Tu and Lukas Weimer. Corpus REDEWIEDERGABE. In Proceedings of the 12th International Conference on Language Resources and Evaluation (LREC’20), pages 803–812, Marseille, France, May 2020a. European Language Resources Association. 

[^5]: Rico Sennrich, Martin Volk, and Gerold Schneider. Exploiting synergies between open resources for german dependency parsing, pos-tagging, and morphological analysis. In Proceedings of the International Conference Recent Advances in Natural Language Processing RANLP 2013, pages 601–609, Hissar, Bulgaria, September 2013. INCOMA Ltd. Shoumen, Bulgaria. 

[^6]: Alan Akbik, Duncan Blythe, and Roland Vollgraf. Contextual string embeddings for sequence labeling. In COLING 2018, 27th International Conference on Computational Linguistics, pages 1638–1649, Santa Fe, New Mexico, USA, August 2018. Association for Computational Linguistics.
