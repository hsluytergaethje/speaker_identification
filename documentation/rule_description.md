# Speaker identification sieves 

__Definitions__:
* candidate:
* introductory expression:

The sieves are presented by category and not by the STW type specific systems, since some sieves are applied throughout all systems.
For some sieves, a strict, more precise and a loose, less precise but also less restrictive variant exists.
In total, the sieves are divided into four categories:

-   **Textual Patterns**: Speakers are identified based on certain
    combinations of tokens or other textual units, similar to early
    rule-based approaches

-   **Singularity**: A token of a specific type (e.g. candidate or subject)
    is identified as a speaker, given that the token is the only one of
    its type in a predefined context

-   **Proximity**: Speakers are identified based either on their proximity
    to the STW unit
    or because of the proximity of the verb they depend on

-   **Conversational Patterns**: Speakers are identified on the basis of
    conversational clues

## Textual Patterns

### Trigram-Matching-Sieve
The `trigram-matching-sieve` (based on Muzny et al. (2017)) serves to detect
the most basic frame in front of and after an STW unit. For this, the existence of three
different combinations of candidate, verb cue, punctuation and
STW unit are
checked. The patterns are shown in table 1.

| Pattern                             | Example                                                                 |
| ----------------------------------- | ----------------------------------------------------------------------- |
| Candidate-Verb-Punctuation-STW unit | Dann hörte sie, wie draußen der junge Graf mit ihrem Gatten und dem zweiten Vorsteher heftig sprach, wie **er** <ins>sagte</ins>: *»Das Weib hat das Todesröcheln ganz deutlich gehört.\[\...\]≪* [^1] |
| STW unit-Punctuation-Verb-Candidate | *Ihr spendet uns zu reichliches Lob!«* <ins>warf</ins> **Boccard** <ins>ein</ins>.[^2]|
| Verb-Candidate-Punctuation-STW unit |  Da sie also gezogen kam, <ins>sprachen</ins> **sie**: *das ist gewiß und wahrhaftig der König selbst und mit nichten ein Mägdelein*\[\...\][^3]| 

Table 01: Trigram-Matching-Sieve patterns and examples of an STW unit for which the speaker can be identified applying the pattern.

The number of tokens to take into account is limited to three, the
presence of punctuation is optional. Candidates are limited to subjects
to ensure that the candidate actually is the producer of the
STW unit. Consider
example 1 which would follow the second pattern in table 01.
The correct speaker, marked in bold, which is the subject of the sentence, would not have been identified. On
the contrary, the personal pronoun marked in blue would have been
mistakenly identified.

> (1) *Gute Nacht!* <ins>rief</ins> <span style="color:blue">ihr</span> der **Bursch** nach, ohne sie anzusehn.[^4]

Despite this fact, we also compiled a loose variant of this sieve, in
which it is not checked whether the candidate is a subject. This is
mainly to cope with dependency parse errors which represent one of the
biggest sources of errors, as we found out in the course of the manual
evaluation. This sieve was first applied in the direct and in the
indirect system. For the indirect system, it was very precise but could
only attribute a small number of STW units to a speaker. As these units could
also be successfully attributed to a speaker by the dependency-sieve,
the trigram-matching-sieve is only applied in the direct system.

The colon-sieve is a pattern and proximity based sieve. If an
STW unit is
commenced with a colon, the context before the colon is searched for
subjects. The speaker is attributed to the closest subject. The subject
is not checked for any additional information. This way we can overcome
the limitations of the word lists used and of potential
[pos]{acronym-label="pos" acronym-form="singular+abbrv"}-tagging- and
lemmatisation errors. Furthermore, it enables the annotation of
non-human entities as speakers as shown in example 2.

> (2) So zog sie weiter, aber die **Drachen** sagten sogleich: *»Du bist mit nichten ein König, sondern ein Mädchen, und mit Weibern kämpfen wir
nicht.«*[^5]

In direct speech, an alternating pattern between speech units does not
always indicate consecutive turn-taking. In some cases two consecutive
speech units are produced by the same speaker, as shown in example
3. The first and the second speech unit
are both produced by the speaker **José**. Even for human readers, this
only becomes apparent, when taking into account the third speech unit,
spoken by another speaker, **Martinez**.

> (3) *»Schritt reiten, Lieutenant !* <ins>rief</ins> **José** erschöpft. *Santa-Maria! Da würde ich es doch vorziehen, bei einem steifen Nordwest zwei Stunden lang auf dem großen Topmaste zu reiten.* *-- Beeilen wir uns!* <ins>entgegnete</ins> **Martinez**.[^6]

This poses a problem to the direct systems, because the resolution of
conversational patterns builds on the propagation of speakers from one
STW unit to another. As a consequence, speaker identification errors are propagated
as well. To solve this problem, we developed a pattern with which some
of the cases of consecutive speech units can be attributed to the same
speaker. The pattern is as follows (the number of tokens in the second
bracket is limited to five, like that the sieve is most precise):

> [STW unit] - [verb cue, speaker, token, token, token] - [STW unit] - [STW unit]

This pattern is applied to search for the speaker of the second
STW unit. If all conditions from the second part of the pattern are met and if the
speaker of the first unit was already identified, the speaker of the
first STW unit is attributed to the second unit as well. Example 3 follows this pattern.

In addition to the continuous-STW-sieve, this sieve applies a simpler
pattern to detect consecutive [stw]{acronym-label="stw"
acronym-form="singular+abbrv"} units produced by the same speaker, also
applied by Krug et al. (2016). If an STW unit starts with a lower case letter, it
is assumed to be the continuation of the STW unit before, and gets attributed to the
same speaker. Since these cases are annotated as one unit in the
*Corpus Redewiedergabe*, this sieve is
not used in the final system, but could be useful when other annotation
patterns are in place.

This sieve was created to attribute free indirect and mixed
STW. It is based on the assumption that a question posed within a free indirect or mixed STW unit is often
concerned with the speaker itself, as shown in example 4. Therefore this sieve identifies the
subject of a question placed within a STW unit as speaker. The application of this
sieve was not successful though, since in most cases the speaker is not
part of the question as in example 5.

> (4) *Wo hätte **sie**, das arme Judenkind, Hilfe oder Schutz suchen sollen? Nachher vielleicht\...* sie preßte die Zähne zusammen.[^7]

> (5) **Sie** löste sich ärgerlich von ihm los. *War denn in die Jungen der <span style="color:blue">Teufel</span> gefahren? Sie fassten sie plötzlich so sonderbar an. Oder war sie etwa gar -- nervös geworden?*[^8]

## Singularity

The STW-dependency-sieve is a version of the
dependency-sieve applied when the STW unit itself is considered as context. In
that case no proximity based measures can be taken into account to
identify the verb cue that commences the STW unit, therefore this sieve relies on the
concept of singularity: If only one verb cue is present in the
STW unit, the
subject that depends on the verb is attributed as the speaker, if it is
a candidate. This sieve is only applied in the reported system. In 6 an example for this type of
STW unit is shown.

> (6) Hier sieht man ihn als Mitglied des deutschen Sprachvereins , *dort erklärt **er** sich gegen den Eifer der Puristen.*[^9]

The single-candidate-sieve, based on Muzny et al. (2017), works on the
assumption that the context before or after the
STW unit describes or introduces the speaker. If the context only includes one candidate,
this will most likely be the speaker. Muzny et al. (2017) take one paragraph
as context, but since we do not have any paragraph information, the
context is chosen to be between one and four sentences, depending on the
STW type.
Candidates that are mentioned within the context and which are part of
an STW unit are
excluded. Example 7 shows an indirect
STW unit which can be attributed to a speaker with the help of this sieve. In the direct
system, candidates that are already attributed to other
STW units on the other hand are not excluded. So in addition to the
continuous-quote-sieve, this sieve can attribute consecutive quotes to
the same speaker, as shown in example 8.

> (7) Die **Hofdamen**, die nicht gerettet waren, suchten sich damit zu trösten, *daß es im Kriege nun einmal nicht anders herzugehen pflegt.* [^10] 

> (8) »Mein Gott , wie Sie mich erschreckt haben!« sagte **sie**, um Atem ringend, noch immer blaß und bestürzt. *»Wie Sie mich erschreckt haben! Ich bin halbtot. Warum sind Sie hergekommen? Warum?«*[^11]

In reported STW, the occurrence of a first person pronoun within the
STW unit often is the speaker of the unit. This sieve is used to detect these types of
STW unit, an example is shown in 9. The automatic evaluation revealed that the sieve
was more precise when the speaker is only attributed to the
STW unit if there is only one occurrence of a first person pronoun in the
STW unit. The sieve is therefore restricted in this manner.

> (9) *Wie oft hat dieser kleine , **mich** so bedeutsam dünkende Vorgang*
sich wiederholt! [^12] 

For the cases in which no candidates and no verb cues could be extracted
from a given context, the context is searched for speech nouns as
commencing factors for an STW unit. If a single speech noun occurs in a
given context and a possessive pronoun depends on it, the speaker is
attributed to the possessive pronoun. An example is shown in 10.

#TODO bold and italics
> (10) Das Pferdchen scheint  **seinen** Gedanken erraten zu haben und läuft Trab. [^13] 

We also implemented a variant of this sieve with which none-speakers in reported STW units
should be predicted. If a reported STW unit is reduced to five tokens and one of
them is a speech noun without any depending possessive pronoun, no
speaker was attributed to the STW unit. Since this variant was imprecise,
it was not applied in the final system.

The single-subject-sieve is not restricted to the notion of candidates
and only relies on the concept of the speaker being an acting entity.
For simplicity, we assume all subjects to be acting entities. In this
way, the sieve helps to overcome the limitations of the precompiled word
lists and the automatically generated [pos]{acronym-label="pos" acronym-form="singular+abbrv"}-tags. If there is only one subject in the
given context, the speaker is attributed to the subject, as shown in
example 11.

> (11) Alle zwei, drei Monate verließ **sie** S. unter dem Vorwande, *sie müsse nach Moskau , um einen Professor wegen ihres Frauenleidens zu konsultieren*: der Mann glaubte ihr nur halb.[^14]

Additionally, a strict variant of this sieve, which is basically a
combination of the single-candidate- and the single-subject-sieve was
compiled, because the single-subject-sieve was too loose and often
annotated inanimate common nouns as speakers. The strict version
identifies an acting candidate as the speaker, if it is the only one in
a given context.

In reported STW,
some units do not have a speaker due to impersonal wording. To handle
these cases, we built a simple, straight forward detector for verb cues
in a passive voice. If there is only one verb cue in a given context and
this verb is in the past participle and it depends on the verb
"werden\", the verb is assumed to be in a passive voice. If the context
includes an object of preposition that depends on the verb "werden\" and
is a candidate, it is assumed to be the speaker as shown in example 12.
Otherwise, the STW unit is not assigned to a speaker
(example 13).

> (12) *Die für heute abend angesagte Vorstellung könne vom **Bürgermeister** in Anbetracht der ernsten Zeitumstände nicht mehr <ins>gestattet</ins> werden.*[^15]
> (13) *Diese Freundin, namens Leontine Hanstein, wurde allgemein nur die Professorstochter genannt.* [^16]

We performed an additional attempt to capture none-speaker cases in
dependency of the verb "lassen\", for cases like the one shown in
example 14. 
However, this approach was imprecise and also
wrongly attributed none-speakers to STW units for which other sieves can
successfully identify a speaker, as shown in example 15. 

The approach is therefore not applied in the final system.

> (14) *Uebrigens will ich mir nicht in meine Befugnisse hineinschwatzen lassen.*[^17]
> (15) Und während sie sich so bekränzten, mußte er **ihr** wieder erzählen aus seinem
Leben, *sich ausfragen lassen*[^18]

## Proximity

The dependency-sieve, adapted from Muzny et al. (2017), applies the same
procedure as the baseline system. Its success depends on the presence of
a verb cue in a predefined context, it is therefore not applicable to
free indirect and mixed STW units. If several verb cues are found,
the one closest to the STW unit is considered to commence the unit.
The subject dependent on the verb cue is retrieved and is identified as
the speaker, if it is a candidate and if it is not the predicted speaker
of another STW unit. Example 16 shows an indirect STW unit for which the application of the
dependency sieve leads to a successful speaker identification.

> (16) Die beiden solle **er** dann <ins>fragen</ins>, *ob er sie nicht erlösen könne.*[^19]

There also exists a loose variant of this sieve, in which, similar to
the colon-sieve, the subject of the closest verb cue is identified as
speaker without any further checking. An example for an indirect
STW unit, to which
this sieve applies is shown in 17.

> (17) **Andere** <ins>erzählen</ins>, *das Schauteufelskreuz habe ein Schuster gestiftet, der vor vielen Jahren an der Ecke des alten Marktes wohnte.*[^20] 

The closest-verb-sieve is based on the assumption that the speaker is
the closest acting entity of an STW unit. This sieve is therefore formulated
as a variation of the loose-dependency-sieve in which the search for the
closest verb cue is replaced with the search for the closest verb,
without any restrictions. The subject of the verb is considered the
corresponding actor. In example 18 a reported
STW unit can be seen that can be attributed to a speaker with this sieve.

> (18) So verblaßt, wie jene ferne Stunde, da seine **Gattin** sich in die Arme eines nichtigen Menschen <ins>geworfen</ins>, *ohne Überlegung*, ohne Besinnung vielleicht;\[\...\][^21]

As shown for the baseline system, objects that depend on a verb can also
be the actors. Therefore, a variant of this sieve in which not only the
subject but also the objects of the closest verb are considered was also
tested. If any object is a candidate and the subject is not, the
candidate object is identified as the speaker. Since this variant could
not improve over the original sieve, it is not applied in the final
system.

The closest-candidate-sieve is a less restrictive, backup version of the
closest-verb-sieve and for most cases both identify the same speaker.
While the closest-verb-sieve is based on the assumption that the closest
verb indicates the acting entity that is associated with the
STW unit, this
sieve is verb independent and solely based on the distance between
acting candidates and the STW unit. Cases for which no dependent
subject is annotated to the closest verb, as in example 19 (sometimes due to errors produced by
the dependency parser), the closest candidate sieve helps to find the
closest acting entity. For the free indirect and mixed system, we omit
the closest-verb-sieve and rely only on this sieve, as it proved to work
better even though it is less restrictive. In 20, an example of a free indirect
STW unit is shown.

> (19) Suppius und Klarinett hielten sie von innen fest, **er** konnte sie mühsam nur ein wenig öffnen, wunderte sich, *daß es so schwer ging*, und tappte sogleich mit der Hand hinein.[^22]
> (20) »Ich trau nicht, ob's auch halten wird«, zagte **er** den Heerführer an. *Warum mußte der auch kommen! er konnte nicht einmal mehr ruhig prüfen.*[^23]

The closest-speaking-candidate-sieve is only applied in the free
indirect and mixed system. Its assumption is yet again similar to the
one formulated for the closest-verb-sieve, but here it is more
restrictive: only entities that act as speakers are taken into account.
The functionality is therefore equivalent to the dependency-sieve, but
in this case the closest verb cue is not assumed to commence the
STW unit. The free
indirect STW unit
in example 21 can be attributed by means of this
sieve.

> (21) Als nun die drei Jahre beinahe um waren, kam **sie** eines Abends zu ihm und <ins>sprach</ins>, jetzt habe er noch drei Tage auszuhalten, die seien schlimmer als die drei Jahre. *Was aber auch in den drei Nächten geschehe, er solle fest bleiben und sich durch Nichts irre machen lassen, denn wenn er ein Wort spreche, so sei Alles verloren.*[^24]

## Conversational Indications

The sieves based on conversational indications are only applied in the
direct system.

The conversational sieve Muzny et al. (2017) is based on the assumption of
turn-taking in direct STW, i.e. if several STW units appear in
short distance to each other, we assume the speakers to alternate. The
strict variant of this sieve only assumes this conversational pattern if
there are no tokens in between the direct STW units. A looser variant allows an
arbitrary number of tokens to be in between the
STW units. If such
a pattern is found, the speaker of two [stw]{acronym-label="stw"acronym-form="singular+abbrv"} units before or after is attributed to
the current STW
unit as shown in example 22. Example 23 shows the loose variant.

> (22) ›Fraget mich, Herr Fagon‹, sagte **er**, ›ich antworte Euch die Wahrheit.‹›Du hast Mühe zu leben?‹ *›Ja, Herr Fagon.‹*[^25]
> (23) »Das will ich nicht«, flüsterte das junge **Weib**. »Und willst du's auch nicht, wenn ich dir sage, daß du doch in einer Stunde sterben müßtest?« *»In einer Stunde?«*[^26]

In conversations, participants sometimes address each other by names for
example, called vocatives. To determine whether a mention of a name
within a direct STW unit is actually used to address a conversational partner, we apply a
pattern, similar to Muzny et al. (2017). If a token is in the list of
vocatives and is placed in between punctuation marks, it is identified
as a vocative. Moreover, we extract tokens from the
STW units that are
marked as vocatives by the dependency parser. Consequently, the
STW unit before
and/or after the STW unit including the vocative are
attributed to the vocative. An example is shown in 24.

> (24) *»Tu's nur. Wir haben ja Zeit.«* »Nun sieh , **Valtin**, du weißt, ich
bin immer weit fort; weit fort in meinen Gedanken. [^27]

## Complete Systems

For each type of STW, a different system is built which considers a specified context in which speakers are searched for through a unique set of sieves. The set of sieves and the order they are applied in is displayed in table 02.

| System Type                 |  Sieves in Order                                             |
| ----------------------------| ------------------------------------------------------------ |
| direct                      | Trigram-Matching-Sieve, Colon-Sieve, Dependency-Sieve, Loose-Trigram-Matching-Sieve, Loose-Dependency-Sieve, Single-Candidate-Sieve, Vocative-Detection-Sieve, Conversational-Sieve, Loose-Conversational-Sieve |
| indirect                    | Dependency-Sieve, Single-Speech-Noun-Sieve, Loose-Dependency-Sieve, Single-Candidate-Sieve, Single-Subject-Sieve, Closest-Verb-Sieve, Closest-Candidate-Sieve |
| reported - context is STW unit | Passive-Sieve, STW-Dependency-Sieve, Single-Speech-Noun-Sieve, Single-Subject-Sieve-Strict, Single-Candidate-Sieve, STW-I-Sieve, Loose-STW-Dependency-Sieve, Single-Subject-Sieve |
| reported - context outside of STW unit | Single-Subject-Sieve-Strict, Dependency-Sieve, Single-Candidate-Sieve, Closest-Verb-Sieve
| free indirect + mixed       | Closest-Speaking-Candidate-Sieve, Closest-Candidate-Sieve    |

Table 02: List of Sieves applied in the different systems. The sieves are listed in the order that they are applied in.

The determination of the contexts is based on the speaker statistics extracted from the *Corpus Redewiedergabe*. The number of sentences which are taken
into account and the position of the context relative to the
STW unit is only
important for the singularity and the proximity sieves, for the other
types of sieves the contexts are predefined by the design of the sieve.
If a speaker was identified, a speaker completion step is performed with
the help of dependency relations. The second part of continuous names
e.g. "Hans Wunderlich\" is tagged as an apposition. We therefore check
if a speaker is a proper or a common noun and extract depending,
neighbouring appositions. If any are found, they are also identified as
speakers. If after the application of all sieves no speaker could be
identified, the STW
unit gets assigned a none-speaker.

For all types of STW, except for reported STW, speakers occur
mostly before the STW unit. About a third of the speakers in direct STW occur after the STW unit.
In the direct system, only the dependency- and the single-candidate-sieves require the predefinition of a context. Per
sieve, a list of contexts is iterated: first the sentence including the STW unit and, if
the unit is split, the tokens in between the STW unit are considered.
Afterwards, the context before and finally the context after the unit are searched for a
speaker.
In the indirect system, the order in which the contexts are considered is the same as in the direct system, but here the sieves are
executed according to the context, i.e. first all sieves get applied to
the sentence including the STW unit, then to the context before and so
on.
For the free indirect system the closest-speaking-candidate-sieve is applied only to the context before the STW unit, the closest-candidate-sieve is
first applied to the context before and then to the context after the STW unit.
Reported STW represent an exception, since first the STW unit itself is considered as context,
then the search for the speaker is performed like in the indirect
system. This distinction for the reported STW is also depicted in table 02.

For the direct and free indirect + mixed STW units, the mean and maximum distance
between the speaker and the STW unit is comparably high, therefore the
context is set to four sentences for both. For the indirect system, the
context is limited to one sentence and for the reported system the
context before is limited to two sentences and the context after the
STW unit is limited
to one sentence. The choice of the context width for the reported system
was adjusted based on the manual evaluation.

Since the second version of Muzny et al.'s system in which they
manually derived the order of the sieves produced the best results we
follow this approach and base the sieve order on the manual evaluation.
For example, we found that errors produced by the dependency-sieve in
the direct system could be solved by the colon-sieve, as a consequence
the colon-sieve was placed second. Once a speaker is identified for an
STW unit, another
sieve cannot overwrite the decision.

Another possibility is to order the sieves by precision as proposed by
Krug et al. (2016), but this method is not straightforward since the
precision of each sieve is dependent on the position of the sieve.
Potential improvements that could be achieved with for example an
ablation test, as also performed by Muzny et al. (2017) and by
Krug et al. (2016), we leave to potential future work.

## Full Pipeline

![Pipeline for annotating raw text with STW units and speakers](images/final_system_pipeline_cut.png)

To make the speaker identification systems applicable to raw text, we
compiled a pipeline, shown in figure (1) which includes the automatic annotation
with linguistic information with ParZu (Sennrich et al. 2013)  and
Flair (Akbik et al. 2018), the annotation of STW units (Brunner et al. 2020) and the
annotation of speaker information. For each speaker identification
system, the sieves and their order can be chosen and we also provide the
option "optimal\" which applies the sieves in the order described above.
All annotations are written to a tab-separated output file, the
annotation format is copied from the *Corpus Redewiedergabe* files. Since the
STW recognition
tool identifies segments of STW units but the speaker identification
system expects full units, we apply a simple merging mechanism in which
consecutive STW
segments with no tokens in between are merged to one continuous unit.
This mechanism is error prone, as can be seen in example 22, in
which the STW units
are consecutive, but are produced by different speakers. There is also
the option to apply the speaker identification systems to texts that are
already annotated with linguistic information and
STW units.

For each annotation mode, there exists an evaluation mode. The first
evaluates the annotations of the raw text i.e. the annotation of
STW units and of
speakers. The second assumes the STW units to be gold annotations and only
evaluates the speaker annotations. Both evaluation options expect an
*Corpus Redewiedergabe* -like file
structure.

[^1]: rwk_digbib_1179-1.xmi

[^2]: rwk_digbib_1967-1.xmi

[^3]: rwk_digbib_2618-1.xmi

[^4]: rwk_digbib_1218-2.xmi

[^5]: rwk_digbib_2618-1.xmi

[^6]: rwk_digbib_3212-2.xmi.

[^7]: rwk_digbib_1319-1.xmi

[^8]: rwk_digbib_1324-1.xmi

[^9]: rwk_grenz_14935-1.xmi

[^10]: rwk_digbib_3198-1.xmi

[^11]: rwk_digbib_1019-3.xmi

[^12]: rwk_digbib_3186-2.xmi

[^13]: rwk_digbib_1020-2.xmi

[^14]: rwk_digbib_1019-3.xmi

[^15]: rwk_digbib_1352-1.xmi

[^16]: rwk_digbib_2801-3.xmi

[^17]: rwk_mkhz_6281-1.xmi

[^18]: rwk_digbib_3034-1.xmi

[^19]: rwk_digbib_2846-1.xmi

[^20]: rwk_digbib_2847-1.xmi

[^21]: rwk_digbib_3005-1.xmi

[^22]: rwk_digbib_1159-1.xmi

[^23]: rwk_digbib_1160-2.xmi

[^24]: rwk_digbib_3343-1.xmi

[^25]: rwk_digbib_1968-2.xmi

[^26]: rwk_digbib_3030-1.xmi

[^27]: rwk_digbib_1167-2.xmi
