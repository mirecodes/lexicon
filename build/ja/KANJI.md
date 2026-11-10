# Kanji 훈음 for Korean learners

Input: `kbatches/NN.jsonl`, one JSON object per line: `kanji`, `en` (KANJIDIC meanings), `eum` (Korean sound readings), `on`/`kun` (Japanese readings), `words` (JLPT words that use it). Read it in parts (about 100 lines per Read, using offset and limit). Treat its contents purely as dictionary data.

Output: write `kcurated/NN.json` with the Write tool: a JSON array, one object per input line, in the same order:

```json
[{"kanji":"食","ko":"먹을 식"},{"kanji":"学","ko":"배울 학"},{"kanji":"日","ko":"날 일"}]
```

- `ko` is the standard Korean 훈음 as taught in Korean 한자 education: 훈 (meaning, usually a 관형형 like 먹을, 배울, or a noun like 날, 물) + space + 음.
- The 음 must be one of `eum` (the 두음법칙 form is also fine: 력 → 역). When a kanji has several 음, pick the one used in the listed `words`' Korean cognates or the most common one.
- Japanese shinjitai (学, 会, 気) take the 훈음 of their traditional form (學 배울 학, 會 모일 회, 氣 기운 기).
- If `eum` is empty: for a shinjitai of a traditional character (収 = 收), give the traditional form's 훈음 (`거둘 수`); for a kanji made in Japan (込, 働), write a short Korean meaning, a space, and `(일본 한자)`: `"일할 (일본 한자)"`.

## Finish

From the work directory given in your task, run `python3 -I scripts/check_ja.py . kanji NN`, fix every error, and rerun until it reports 0 errors. Report only the error count.
