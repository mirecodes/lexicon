# Lexicon

GRE 영단어와 독일어 A1–B1 단어를 하루 50단어씩 카드로 넘겨 보는 학습 앱입니다.

- 앱: https://mirecodes.github.io/lexicon/
- 데이터와 형식 설명: [en/README.md](en/README.md), [de/README.md](de/README.md)

## 기능

- 오늘의 20단어: 날마다 바뀌는 단어 20개 (영어는 중요도 상위 절반, 독일어는 전체 레벨에서)
- Day별 단어장: 중요도순 50단어씩, 진행 상황 저장
- 전체 단어: 검색, A–Z·중요도순 정렬
- 카드 뒷면: 한글·영어 뜻, 뜻별 동의어, 예문, 어근·접두사·접미사, 유래
- 동의어나 어근을 누르면 그 뜻과 같은 어근을 가진 단어를 팝업으로 보여 줍니다.
- 독일어: 명사는 관사와 성별 색, 복수형. 동사는 변화 유형과 현재·과거·완료형, 분리동사는 `an · rufen`처럼 나눠 표시하고 전철·어간을 누르면 뜻과 같은 요소를 가진 단어를 보여 줍니다.

## 개발

React + TypeScript + Vite 앱입니다(`src/`). 단어 데이터의 원본은 `en/`, `de/`의 챕터 파일이고, `scripts/data.ts`가 이를 검사한 뒤 앱이 읽는 `public/data/`로 묶습니다(커밋하지 않음). Node 24 이상이 필요합니다.

```bash
npm install
```

```bash
npm run dev
```

- `npm run validate`: 챕터 파일 검사만
- `npm run build`: 검사·묶기·타입 검사·빌드 (`dist/`)

`main`에 푸시하면 GitHub Actions(`.github/workflows/deploy.yml`)가 빌드해 GitHub Pages에 배포합니다. 풀 리퀘스트에서는 빌드와 검사만 합니다.

## 출처와 라이선스

- 단어 선정: GregMat, Magoosh, Manhattan Prep, PowerScore, Vocabulary.com 단어장에 실렸는지를 기준으로 했습니다. 각 단어장의 내용(뜻, 예문)은 사용하지 않았습니다.
- 영어 뜻·예문·동의어: [Open English WordNet](https://en-word.net) (CC BY 4.0), [Wiktionary](https://en.wiktionary.org) ([kaikki.org](https://kaikki.org) 추출본, CC BY-SA 4.0)
- 사용 빈도: [wordfreq](https://github.com/rspeer/wordfreq)
- Day별 카드의 별자리 선: [d3-celestial](https://github.com/ofrohn/d3-celestial) (BSD-3-Clause) 데이터를 투영해 `src/constellations.ts`로 만들었습니다.
- 한글 뜻, 유래 요약, 일부 예문: Claude가 작성했으며 사람의 검수를 거치지 않았습니다.

- 독일어 표제어와 레벨: Goethe-Institut 시험 단어 목록 (목록의 예문은 사용하지 않음)

Wiktionary 자료를 포함하므로 `en/`, `de/` 폴더와 거기서 만든 앱 데이터는 [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)을 따릅니다.
