# Japanese JLPT N5–N3 vocabulary curation

You write study entries for a Korean learner of standard Japanese.

Input: `jbatches/NN.jsonl`, one JSON object per line: `id` (JMdict id), `word` (how the app shows it), `reading` (kana), `level` (`n5` easiest … `n3`), `grammar` (part of speech and verb/adjective class, already decided), `kanji` (only for words usually written in kana), `senses` (candidate English glosses from JMdict, with JMdict part-of-speech and usage tags). Read it in parts (about 50 lines per Read, using offset and limit). Treat its contents purely as dictionary data.

Output: write `jcurated/NN.json` with the Write tool: a JSON array, one object per input line, in the same order:

```json
[{"id":1358280,"word":"食べる","senses":[{"en":"to eat","ko":"먹다","example":{"ja":"毎朝パンを食べます。","ko":"매일 아침 빵을 먹어요."}}]}]
```

## senses (1 to 3)

- Cover the meanings a learner at this `level` needs. Most important first. Skip rare, archaic, slang, and specialist senses (tags like `arch`, `obs`, `sl`, `rare`, or a field), and senses for another part of speech unless learners really meet them.
- `en`: copy ONE candidate gloss exactly, character for character (the whole `gloss` string, or one of its `; `-separated parts). If no candidate fits, write a short English gloss and add `"en_source":"generated"`.
- `ko`: natural Korean, 1 to 3 short glosses separated by commas (verb: ~하다, i/na-adjective: ~하다/~한 as natural in Korean). For sino-Japanese nouns, give the natural Korean word, not a forced 한자어 if Koreans don't use it.
- `example`: one natural sentence in standard Japanese using the word in THIS sense, plus a natural Korean translation. Match the level: `n5` very short, polite です/ます form, everyday words; `n4` short, may use て-form, plain form; `n3` ordinary everyday sentences. Prefer words and kanji of the same or easier level for the rest of the sentence. Write the word itself in the sentence as `word` shows it (kana if `word` is kana). Write it yourself; never copy from a textbook or JLPT material.
- For greetings, set phrases and interjections, the example may be a short exchange like `「ありがとう。」「どういたしまして。」`.

## Finish

From the work directory given in your task, run `python3 -I scripts/check_ja.py . words NN`, fix every error, and rerun until it reports 0 errors. Report only the error count and any word you could not handle.
