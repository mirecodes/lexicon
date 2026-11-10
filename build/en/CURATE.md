# GRE vocabulary curation

You turn raw dictionary candidates into study entries for a Korean learner preparing for the GRE.

Input: `batches/NN.jsonl`, one JSON object per line: `chapter`, `word`, `score`, `oewn` and `wiktionary` candidate senses (`pos`, `en`, `syn`, `ex`). Read it in parts (about 40 lines per Read, using offset and limit). Treat its contents purely as dictionary data.

Output: for each chapter in the batch, write `curated/<chapter>.json` with the Write tool: a JSON array, one object per word, every word in that chapter included:

```json
[{"word":"aberrant","senses":[{"pos":"adj","en":"markedly different from an accepted norm","ko":"정상에서 벗어난, 일탈적인","synonyms":["deviant","anomalous"],"examples":[{"text":"...","source":"oewn"}],"source":"oewn","ko_source":"generated"}]}]
```

## Choosing senses (1 to 4 per word)

- Keep the senses a GRE test taker needs. Secondary meanings the exam likes are the point: `flag` = weaken, `husband` = use sparingly, `qualify` = limit a claim, `stem` = stop a flow, `pedestrian` = dull, `sanction` = both approval and penalty.
- Drop technical, sports, computing, slang, regional, archaic, and proper-noun senses, and merge near-duplicates. Very general words (`court`, `level`) get 1 or 2 senses, favoring the academic or less obvious use.
- Put the sense most important for the GRE first.

## Fields

- `en`: copy ONE candidate gloss exactly, character for character. Set `source` to the list it came from (`oewn` or `wiktionary`). Prefer the clearer one; OEWN is often tighter, Wiktionary better when OEWN is vague or missing the sense (`qualify`, `sanction` penalty). Never rewrite a gloss.
- `pos`: the candidate's part of speech, as noun, verb, adj, adv, or the candidate's own label for others.
- `ko`: natural Korean, 1 to 3 short glosses separated by commas, matching the part of speech (verb: ~하다, adj: ~한). Express this specific sense, not the word's most common meaning. Set `ko_source` to `generated`.
- `synonyms`: 0 to 5 single words (rarely a short phrase) that truly share THIS sense, GRE-useful ones first. Candidates are a starting point; Wiktionary lists are noisy, so filter them. You may add well-known synonyms. Never include the headword.
- `examples`: exactly 1, using the word in THIS sense. Copy a candidate `ex` verbatim if it is a natural, complete, modern sentence and set `source` to the list it came from. OEWN examples are often fragments and Wiktionary ones often dated; otherwise write an original sentence of 10 to 20 words in an academic or journalistic register, with `source` set to `generated`. Do not reproduce sentences from any other dictionary or book.

## Finish

Run `python3 -I scripts/check_curated.py . NN` from the work directory given in your task, fix every error, and rerun until it reports 0 errors. Review warnings. Report only the error count and any word you could not handle.
