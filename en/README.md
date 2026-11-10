# GRE 영단어 데이터베이스

GRE 단어장 5종(GregMat, Magoosh 1000, Manhattan Prep 1000, PowerScore Repeat Offenders, Vocabulary.com Top 1000)의 합집합 2,713단어입니다.

## 구조

```
en/
  a/ab.json … z/ze.json   단어 챕터: 표제어 앞 두 글자 기준, 파일 안은 알파벳순
  roots.json              어근·접두사·접미사 사전 {id: {type, ko}}
  synonyms.json           DB에 없는 동의어의 뜻 {word: [sense]}
```

검사와 앱용 묶음(중요도순)은 저장소 루트의 `scripts/data.ts`가 맡습니다. 항목의 TypeScript 형식은 `src/types.ts`의 `EnEntry`입니다.

## 항목 형식

```json
{
  "word": "abate",
  "score": 50,
  "zipf": 2.71,
  "lists": ["GregMat", "Magoosh"],
  "curated": true,
  "parts": ["ab-", "bat"],
  "origin": {"ko": "…", "source": "wiktionary", "ko_source": "generated"},
  "senses": [{
    "pos": "verb",
    "en": "become less in amount or intensity",
    "ko": "약해지다, 누그러지다",
    "synonyms": ["subside", "wane"],
    "examples": [{"text": "The storm abated", "source": "oewn"}],
    "source": "oewn",
    "ko_source": "generated"
  }]
}
```

- `lists`: 이 단어가 실린 단어장
- `zipf`: 영어 사용 빈도 ([wordfreq](https://github.com/rspeer/wordfreq), 0~8, 높을수록 흔함)
- `score`: 중요도 0~100 = 80 × (단어장 수 / 5) + 20 × (빈도가 GRE 핵심 단어 중앙값 Zipf 2.5에 가까운 정도). 공식은 `scripts/data.ts`의 `score()`
- `source`: 영어 뜻과 예문의 출처. `oewn`은 [Open English WordNet](https://en-word.net) (CC BY 4.0), `wiktionary`는 [Wiktionary](https://en.wiktionary.org) (CC BY-SA, [kaikki.org](https://kaikki.org) 추출본), `generated`는 Claude가 작성
- `ko_source: generated`: 한글 뜻은 모두 Claude가 작성했습니다. 사람의 검수를 거치지 않았습니다.
- `parts`: `roots.json`의 id. 같은 철자라도 뜻이 다른 형태소는 `in-(부정)`, `in-(안으로)`처럼 구분합니다.
- `origin`: Wiktionary 어원을 바탕으로 Claude가 한국어로 요약한 유래. 근거가 부족한 단어는 비워 두었습니다.

## 추가·수정·삭제

1. 해당 챕터 파일(`b/ba.json` 등)에서 알파벳 순서를 지켜 항목을 추가하거나 고치거나 지웁니다. 새 챕터가 필요하면 `<첫 글자>/<앞 두 글자>.json` 파일을 만듭니다.
2. `score`는 `lists`와 `zipf`로 계산한 값이어야 합니다. 검사기가 틀린 값을 알려 줍니다.
3. 저장소 루트에서 검사합니다. 앱 데이터는 `npm run dev`·`npm run build`가 다시 만들고, 배포 때는 GitHub Actions가 검사와 빌드를 함께 합니다.

```bash
npm run validate
```
