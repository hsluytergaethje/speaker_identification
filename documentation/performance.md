# Performance of the speaker identification system

The highest accuracy for each sieve system could be performed with the sieves selection and order shown in the table below. In the file `pipeline/config.ini` this option can be chosen by selecting 'optimal'. 

| System Type                 |  Sieves in Order                                             |
| ----------------------------| ------------------------------------------------------------ |
| direct                      | Trigram-Matching-Sieve, Colon-Sieve, Dependency-Sieve, Loose-Trigram-Matching-Sieve, Loose-Dependency-Sieve, Single-Candidate-Sieve, Vocative-Detection-Sieve, Conversational-Sieve, Loose-Conversational-Sieve |
| indirect                    | Dependency-Sieve, Single-Speech-Noun-Sieve, Loose-Dependency-Sieve, Single-Candidate-Sieve, Single-Subject-Sieve, Closest-Verb-Sieve, Closest-Candidate-Sieve |
| reported - context is STW unit | Passive-Sieve, STW-Dependency-Sieve, Single-Speech-Noun-Sieve, Single-Subject-Sieve-Strict, Single-Candidate-Sieve, STW-I-Sieve, Loose-STW-Dependency-Sieve, Single-Subject-Sieve |
| reported - context outside of STW unit | Single-Subject-Sieve-Strict, Dependency-Sieve, Single-Candidate-Sieve, Closest-Verb-Sieve
| free indirect + mixed       | Closest-Speaking-Candidate-Sieve, Closest-Candidate-Sieve    |

## Performance of the full pipeline
In the table below the performance of the STW recognition tool and of the speaker identification system is shown. 
For each type of STW the performance was calculated on a different test set which can be found in `corpus/test_set/sentences/`.
The accuracy of the speaker identification systems could only be calculated for correctly classified STW units.

<table border="1">
  <tr>
    <th scope="col">STW type</th>
    <<th scope="col" colspan="2">STW Recognition F1 Score</th>
    <th scope="col" colspan="2">Speaker Identification Accuracy</th>
  </tr>
  <tr>
  <th scope="row">&nbsp;</th>
    <td>Strict</td>
    <td>Loose</td>
    <td>Strict</td>
    <td>Loose</td>
  </tr>
   <tr>
  <tr>
  <td>Direct</td>
    <td>69.1</td>
    <td>93.31</td>
    <td>59.88</td>
    <td>61.34</td>
  </tr>
   <tr>
  <td>Indirect</td>
    <td>79.0</td>
    <td>84.32</td>
    <td>80.61</td>
    <td>82.62</td>
  </tr>
   <tr>
  <td>Reported</td>
    <td>61.77</td>
    <td>71.65</td>
    <td>76.19</td>
    <td>77.78</td>
  </tr>
   <tr>
  <td>Free Indirect</td>
    <td>53.32</td>
    <td>69.78</td>
    <td>40.0</td>
    <td>40.0</td>
  </tr>
</table>



## Comparison to related work 

In the table below the performance of similar speaker identification system is compared to this work. The performance differs from the one presented above as the speaker identification systems were applied to gold labeled STW. Like this it is assured that complicated STW unit which could not be correctly identified by the STW recognition tool are also attributed. 

| Author               | STW type    | Performance Range | STW Medium    | Domain     | Language    |
| -------------------  | ------------| ----------------- | ------------- | ---------- | ----------- |
| Pareti et al. (2013) | Direct<br>Indirect<br>Mixed | 85 -91<br>74-79<br>65-81 | Speech | News | English |
| Krug et al. (2016)   | Direct      | 78.4              | Speech        | Literature | German      |
| Muzny et al. (2017)  | Direct      | 76 - 85           | Speech        | Literature | English     |
| This work            | Direct<br>Indirect<br>Reported<br>Free indirect | 63.91<br>82.2<br>71.38<br>50.0 | Speech<br>Thought<br>Writing | Literature | German | 



