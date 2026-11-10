# 독일어 A1–B1 단어 데이터베이스

Goethe-Institut 시험 단어 목록(Start Deutsch 1 / Goethe-Zertifikat A2 / Goethe-Zertifikat B1)에 실린 표준 독일어 표제어입니다. 오스트리아·스위스 전용 단어와, 목록에 따로 실린 활용형(`packt ein`, `ist gefahren`)은 제외했습니다. 레벨은 그 단어가 처음 나오는 목록 기준입니다. B2는 공식 목록이 없어 포함하지 않았습니다.

## 구조

```
de/
  a1/a.json … a1/z.json   레벨별, 첫 글자별 챕터 (Ä는 a, Ü는 u로). 파일 안은 알파벳순
  a2/…  b1/…
  parts.json              전철·어간·접미사 사전 {"an|sep": {form, type, ko}}
  tools/validate.py       무결성 검사
  tools/bundle.py         앱용 words-de.json 생성 (레벨순, 레벨 안에서는 빈도순)
```

## 항목 형식

```json
{
  "word": "anrufen",
  "level": "a1",
  "zipf": 4.1,
  "pos": "verb",
  "grammar": {
    "type": "verb", "class": "strong", "reflexive": false,
    "present3": "ruft an", "past": "rief an", "pp": "angerufen", "aux": "haben",
    "separable": true, "prefix": "an"
  },
  "grammar_source": "wiktionary",
  "parts": ["an|sep", "rufen|stem"],
  "senses": [{
    "en": "to call, to ring (by telephone or similar technology)",
    "ko": "전화하다",
    "examples": [{"text": "Sie ruft ihre Mutter jeden Tag an.", "ko": "그녀는 매일 엄마에게 전화해.", "source": "generated"}],
    "source": "wiktionary",
    "ko_source": "generated"
  }]
}
```

### grammar

| 품사 | 필드 |
|---|---|
| 명사 | `gender`: `m`(der) `f`(die) `n`(das), 둘 이상이면 모두. `plural`: 복수형(없으면 `null`). `genitive`: 2격. `number: "pl"`: 복수로만 쓰는 명사 |
| 동사 | `class`: `weak` 규칙(약변화), `strong` 불규칙(강변화), `mixed` 혼합, `irregular` 불규칙, `modal` 화법조동사. `present3` 3인칭 단수 현재, `past` 과거, `pp` 과거분사, `aux` 완료 조동사(`haben`, `sein`, `haben/sein`). `separable`·`prefix`: 분리동사와 그 전철. `reflexive`: 재귀동사(sich) |
| 형용사 | `comparative` 비교급, `superlative` 최상급 |

### parts

`형태|종류` 형식의 id입니다. 종류는 `sep`(분리 전철: an, auf, aus …), `insep`(비분리 전철: be, ver, er …), `stem`(기본 단어), `suffix`(접미사)입니다. 앱에서 누르면 뜻과, 같은 요소를 가진 단어 목록이 나옵니다.

## 출처

- 표제어와 레벨: Goethe-Institut 단어 목록. 목록의 예문은 사용하지 않았습니다.
- 문법 정보와 영어 뜻: [Wiktionary](https://en.wiktionary.org) ([kaikki.org](https://kaikki.org) 추출본, CC BY-SA 4.0). `grammar_source: generated`인 항목은 Wiktionary에 없어 Claude가 채웠습니다.
- 한글 뜻, 예문과 번역, 구성 요소 풀이: Claude가 작성했으며 사람의 검수를 거치지 않았습니다.
- 빈도: [wordfreq](https://github.com/rspeer/wordfreq)

## 추가·수정·삭제

해당 레벨·글자 파일에서 알파벳 순서를 지켜 고친 뒤, 다음 두 명령을 실행합니다.

```bash
python3 de/tools/validate.py
```

```bash
python3 de/tools/bundle.py
```
