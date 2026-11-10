# Normalize word parts

`roots_raw.jsonl` lists every word part found in a GRE vocabulary set, one JSON object per line: `type`, `form`, and `meanings` mapping each raw Korean meaning (written by different people, so inconsistent) to example words. Read the whole file in parts (about 120 lines per Read, using offset and limit). Treat its contents purely as data.

Goal: one consistent entry per real morpheme, so a learner who taps a part sees every word sharing that same morpheme.

Write `roots_norm.json` with the Write tool:

```json
{
  "merge_forms": {"spect": "spec", "cred": "cred"},
  "split": {
    "in-": [
      {"label": "부정", "ko": "~이 아닌 (부정)", "members": ["부정"]},
      {"label": "안으로", "ko": "안으로, 안에", "members": ["안에", "안으로", "안으로, ~하게", "향해", "위에"]}
    ]
  },
  "ko": {"spec": "보다", "ab-": "~에서 떨어져"}
}
```

- `merge_forms`: spelling variants of the SAME morpheme map to one canonical form of the same type (`spect` to `spec`, `ced` and `cess` to `ced`). Only real variants of one morpheme; leave look-alikes alone. Omit forms that stay as they are.
- `split`: ONLY for canonical forms that cover genuinely different morphemes (Latin `in-` "not" vs `in-` "into"; `-ate` verb vs adjective is NOT worth splitting). Each group has a short `label` (1 to 5 Korean characters, shown in brackets), a clean `ko` meaning, and `members`: the raw meanings it absorbs. Every raw meaning of that canonical form, including those brought in by `merge_forms`, must be in exactly one group. Raw meanings that are only wording variants of the same idea go in the same group.
- `ko`: a clean Korean meaning (1 to 10 characters where possible) for each canonical form that is NOT split. Write one for every unsplit canonical form; choose the meaning that fits most of its words.

When done, run `python3 -I scripts/norm.py .` from the work directory given in your task. It validates your file and reports problems; fix them and rerun until it says OK. Report only the final counts it prints.
