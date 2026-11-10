# 데이터 빌드 파이프라인

`en/`과 `de/`의 데이터를 처음부터 다시 만드는 스크립트와, 단계별로 Claude 작업자(서브에이전트)에게 준 지침입니다. 평소 단어를 고치거나 추가할 때는 이 파이프라인이 필요 없습니다. 챕터 파일을 직접 고치고 `npm run validate`만 실행하면 됩니다(`en/README.md`, `de/README.md` 참고).

- `*.py`: 결정적인 단계(목록 병합, 사전 수집, 조립, 검사)
- `*.md`: 사람의 판단이 필요한 단계(뜻 고르기, 한글 뜻, 예문, 어근, 유래)를 맡긴 작업자 지침. 묶음 하나(`NN`)마다 작업자 하나에게 "작업 폴더 W에서 X.md를 따르라"고 맡깁니다. 작업자는 검사 스크립트가 오류 0을 낼 때까지 고칩니다.

모든 스크립트는 첫 인자로 작업 폴더 `W`를 받습니다. 내려받은 캐시와 중간 결과는 `W`에만 쓰고, 마지막 조립 단계만 저장소의 `en/`, `de/`에 씁니다.

## 준비

```bash
W=~/lexicon-work
```

```bash
mkdir -p $W/scripts $W/lists $W/oewn $W/de_lists && cp build/en/*.py build/de/*.py $W/scripts/ && cp build/en/*.md build/de/*.md $W/
```

```bash
python3 -m venv $W/venv && $W/venv/bin/pip install wordfreq
```

```bash
curl -L -o $W/oewn/oewn2025.xml.gz https://github.com/globalwordnet/english-wordnet/releases/download/2025-edition/english-wordnet-2025.xml.gz
```

`kaikki.org` 요청은 `curl`로 보내고 요청 사이에 쉬므로, 수집 단계는 단어 수에 따라 수 분이 걸립니다.

## GRE 영어 (`en/`)

1. 단어장 5종 내려받기 ([Xatta-Trone/gre-words-collection](https://github.com/Xatta-Trone/gre-words-collection), 표제어만 사용)

   ```bash
   R=repos/Xatta-Trone/gre-words-collection/contents/word-list; for p in "001 GregMat960:GregMat" "005 PowerscoreRepeatOffenders-699:PowerScore" "008 Magoosh-1000:Magoosh" "012 The Vocabulary.com Top 1000%EF%BB%BF:VocabCom" "013 Manhattan-Prep-1000-GRE-Words-Definitions:Manhattan"; do f=${p%%:*}; gh api "$R/$(python3 -c 'import sys,urllib.parse as u;print(u.quote(sys.argv[1],safe="%"))' "$f").csv" -H 'Accept: application/vnd.github.raw' > "$W/lists/${p##*:}.csv"; done
   ```

2. 병합·정규화·빈도·중요도 → `W/merged.json`: `$W/venv/bin/python $W/scripts/merge.py $W`
3. Wiktionary 수집 → `W/wikt/`: `python3 $W/scripts/fetch_wikt.py $W`
4. 조립(아직 큐레이션 전) + 후보 파일 `W/cand/`: `python3 $W/scripts/build.py $W en`
5. 뜻 큐레이션
   - `python3 $W/scripts/make_batches.py $W` → `W/batches/NN.jsonl`
   - 묶음마다 작업자: `CURATE.md` → `W/curated/<챕터>.json`
   - 전체 검사: `python3 -I $W/scripts/check_curated.py $W`
6. DB 밖 동의어의 뜻
   - `python3 $W/scripts/make_syn.py $W` → `W/sbatches/`
   - 묶음마다 작업자: `SYN.md` → `W/syn/NN.json`
   - `python3 $W/scripts/merge_syn.py $W en` → `en/synonyms.json`
7. 어근·유래
   - `python3 $W/scripts/fetch_etym.py $W`, `python3 $W/scripts/make_ebatches.py $W` → `W/ebatches/`
   - 묶음마다 작업자: `ETYM.md` → `W/parts/NN.json`
   - `python3 $W/scripts/make_roots_raw.py $W`, 작업자 하나: `NORM.md` → `W/roots_norm.json`
   - `python3 $W/scripts/norm.py $W en` → `W/roots_map.json`, `en/roots.json`
8. 최종 조립: `python3 $W/scripts/build.py $W en`, 그다음 `npm run validate`

`build/en/fixes.json`은 사람이 직접 고친 뜻풀이로, 조립할 때 큐레이션 결과 위에 덮어씁니다.

## 독일어 (`de/`)

1. Goethe A1·A2·B1 목록의 표제어 열만 내려받기 ([ilkermeliksitki/goethe-institute-wordlist](https://github.com/ilkermeliksitki/goethe-institute-wordlist). 목록의 예문 열은 쓰지 않습니다)

   ```bash
   for p in $(gh api 'repos/ilkermeliksitki/goethe-institute-wordlist/git/trees/HEAD?recursive=1' --jq '.tree[]|select(.type=="blob")|.path' | grep -E '^(a1|a2|b1)/[a-z]\.tsv$'); do gh api "repos/ilkermeliksitki/goethe-institute-wordlist/contents/$p" -H 'Accept: application/vnd.github.raw' | cut -f1 >> "$W/de_lists/${p%%/*}.txt"; done
   ```

2. 표제어 정규화 → `W/de_merged.json`: `python3 $W/scripts/de_merge.py $W`
3. Wiktionary 수집 → `W/de_wikt/`: `python3 $W/scripts/fetch_de.py $W`
4. 큐레이션
   - `python3 $W/scripts/de_batches.py $W` → `W/dbatches/NN.jsonl`
   - 묶음마다 작업자: `DE.md` → `W/dcurated/NN.json`
   - 전체 검사: `python3 -I $W/scripts/check_de.py $W`
5. 조립: `$W/venv/bin/python $W/scripts/de_build.py $W de`, 그다음 `npm run validate`

`de_build.py`는 활용형 항목과 고유명사를 건너뛰고, Goethe 관사와 성별이 맞는 명사를 고르는 등 `de_batches.py`보다 엄격하게 사전 항목을 고릅니다. 두 단계에서 고른 항목이 다른 단어는 작업자가 엉뚱한 뜻을 받았을 수 있습니다. 이번 빌드에서는 그런 단어 105개를 모아 다시 맡겼습니다(`dbatches/16.jsonl`, 묶음 번호가 클수록 나중에 덮어씀). 지역어 제외 목록(`REGIONAL`)과 활용형 제외 목록(`JUNK`)은 `de_build.py`에 있습니다.

## 일본어 (`ja/`)

준비: `mkdir -p $W/lists/yomi $W/dict && cp build/ja/*.py $W/scripts/ && cp build/ja/*.md $W/`, venv에는 `$W/venv/bin/pip install 'wordfreq[cjk]'`.

1. JLPT 목록(JMdict 번호 포함) 내려받기 ([stephenmk/yomitan-jlpt-vocab](https://github.com/stephenmk/yomitan-jlpt-vocab), Waller 목록 기반)

   ```bash
   for n in 1 2 3 4 5; do gh api repos/stephenmk/yomitan-jlpt-vocab/contents/original_data/n$n.csv -H 'Accept: application/vnd.github.raw' > $W/lists/yomi/n$n.csv; done
   ```

2. JMdict·KANJIDIC2 내려받기: [jmdict-simplified 릴리스](https://github.com/scriptin/jmdict-simplified/releases/latest)의 `jmdict-eng-*.json.tgz`, `kanjidic2-en-*.json.tgz`를 `W/dict/`에 풀기
3. 병합 → `W/ja_merged.json`, `W/jbatches/`, `W/kbatches/`: `$W/venv/bin/python $W/scripts/ja_merge.py $W` (둘째 인자로 레벨 지정, 기본 `5,4,3`. N2·N1까지는 `5,4,3,2,1`)
4. 큐레이션
   - 단어 묶음마다 작업자: `JA.md` → `W/jcurated/NN.json`
   - 한자 묶음마다 작업자: `KANJI.md` → `W/kcurated/NN.json`
   - 전체 검사: `python3 -I $W/scripts/check_ja.py $W words`, `python3 -I $W/scripts/check_ja.py $W kanji`
5. 조립: `python3 $W/scripts/ja_build.py $W ja`, 그다음 `npm run validate`

품사·동사 그룹·자타동사는 JMdict 첫 뜻의 품사 태그로 정하고(`ja_merge.py`의 `grammar`), 단어의 한자 분해도 표기에서 기계적으로 뽑습니다. 작업자는 뜻 고르기, 한글 뜻, 예문, 한자 훈만 씁니다.
