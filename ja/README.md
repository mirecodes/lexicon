# 일본어 JLPT N5–N3 단어 데이터베이스

JLPT N5·N4·N3 단어입니다. JLPT는 2010년 이후 공식 단어 목록을 내지 않아서, 사실상 표준으로 쓰이는 Jonathan Waller의 레벨별 목록(jisho.org도 사용)을 기준으로 했습니다. 단어가 여러 레벨에 실려 있으면 가장 낮은 레벨에 넣었습니다.

N2·N1은 넣지 않았습니다. 목록을 정리한 쪽도 N2와 N1의 경계가 불분명하다고 밝히고 있어서, 독일어에서 공식 목록이 없는 B2를 뺀 것과 같은 기준을 적용했습니다. 같은 파이프라인으로 추가할 수 있습니다(`build/README.md`).

## 구조

```
ja/
  n5/a.json … n5/wa.json   레벨별, 읽기 첫 글자의 행(あ·か·さ·た·な·は·ま·や·ら·わ)별 챕터. 파일 안은 읽기 순
  n4/…  n3/…
  parts.json               한자 사전 {"食|kanji": {type, form, ko, on, kun}}
```

## 항목 형식

```json
{
  "id": 1358280,
  "word": "食べる",
  "reading": "たべる",
  "level": "n5",
  "zipf": 4.92,
  "pos": "verb",
  "grammar": {"type": "verb", "class": "ichidan", "transitive": true},
  "parts": ["食|kanji"],
  "senses": [{
    "en": "to eat",
    "ko": "먹다",
    "examples": [{"text": "毎朝パンを食べます。", "ko": "매일 아침 빵을 먹어요.", "source": "generated"}],
    "source": "jmdict",
    "ko_source": "generated"
  }]
}
```

- `id`: JMdict 항목 번호
- `word`: 앱에 보이는 표기. 보통 가나로만 쓰는 단어(JMdict `uk` 표시: ある, いる, できる)는 가나로 쓰고, 한자 표기는 `kanji`에 둡니다.
- `reading`: 가나 읽기. 가타카나 단어는 `word`와 같습니다.
- `grammar.class`: 동사는 `godan`(1그룹, 5단), `ichidan`(2그룹, 1단), `suru`·`kuru`(3그룹). 형용사는 `i`(い형용사), `na`(な형용사). `transitive`: 타동사 `true`, 자동사 `false`(둘 다 되면 없음). `suru: true`: する를 붙여 동사로 쓰는 명사(勉強する)
- `parts`: 표기에 들어간 한자. `parts.json`에 한국어 훈음(`먹을 식`)과 음독·훈독이 있습니다.

## 출처

- 단어와 레벨: Jonathan Waller의 [JLPT 목록](http://www.tanos.co.uk/jlpt/) (CC BY). JMdict 번호와 표기 정리는 [stephenmk/yomitan-jlpt-vocab](https://github.com/stephenmk/yomitan-jlpt-vocab) (CC BY-SA 4.0)
- 읽기, 품사, 영어 뜻: [JMdict](https://www.edrdg.org/jmdict/j_jmdict.html) ([jmdict-simplified](https://github.com/scriptin/jmdict-simplified) JSON, EDRDG 라이선스, CC BY-SA 4.0). `source: generated`인 뜻은 JMdict에 맞는 풀이가 없어 Claude가 썼습니다.
- 한자 음독·훈독과 한국 한자음: [KANJIDIC2](https://www.edrdg.org/wiki/index.php/KANJIDIC_Project) (CC BY-SA 4.0)
- 한글 뜻, 예문과 번역, 한자 훈: Claude가 작성했으며 사람의 검수를 거치지 않았습니다.
- 빈도: [wordfreq](https://github.com/rspeer/wordfreq)

## 추가·수정·삭제

해당 레벨·행 파일에서 읽기 순서를 지켜 고친 뒤 검사합니다.

```bash
npm run validate
```
