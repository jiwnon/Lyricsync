# LyricSync

**노래 커버 영상 제작자를 위한 자막 자동 생성 + 렌더링 도구**

가사 txt 파일을 힌트로 WhisperX의 forced alignment를 활용해  
정확한 타임스탬프의 SRT를 뽑고, 스타일을 설정해 영상에 바로 입힙니다.

---

## 왜 만들었나

기존 Whisper 기반 자막 도구는 **일반 발화** 기준으로 받아쓰기를 시도합니다.  
노래 커버 영상은 가사가 이미 알려져 있음에도 처음부터 인식하기 때문에 정확도가 낮습니다.

LyricSync는 **가사 txt를 힌트로** 제공해 발화 타임스탬프와 가사를 강제 정렬합니다.  
받아쓰기가 아닌 **정렬 문제**로 접근합니다.

---

## 주요 기능

| 기능 | 설명 |
|---|---|
| **SRT 자동 생성** | 영상 + 가사 txt → 타임스탬프 정렬된 SRT |
| **보정 테이블** | 생성된 자막의 시간/텍스트를 UI에서 직접 수정 |
| **자막 렌더링** | SRT + 스타일 설정 → 자막 입힌 영상 출력 |
| **미리보기** | 렌더링 전 첫 자막 구간 프레임 이미지로 확인 |
| **스타일 커스터마이징** | 폰트 / 크기 / 글자색 / 외곽선색 / 두께 / 위치 |

---

## 파이프라인

```
영상 파일 + 가사 txt
        ↓
  오디오 추출 (FFmpeg)
        ↓
  WhisperX 음성인식 + 단어 단위 타임스탬프
        ↓
  가사 라인 ↔ 타임스탬프 forced alignment
        ↓
  SRT 생성 + 보정 UI
        ↓
  (선택) 자막 스타일 설정 → FFmpeg 렌더링 → 영상 출력
```

---

## 설치

**Python 3.10+ 및 FFmpeg 필요**

```bash
# FFmpeg 설치 (없는 경우)
# Windows: https://ffmpeg.org/download.html
# Mac: brew install ffmpeg

# 레포 클론
git clone https://github.com/jiwnon/Lyricsync.git
cd Lyricsync

# 의존성 설치
pip install -r requirements.txt
```

---

## 실행

```bash
python app.py
```

브라우저에서 `http://localhost:7860` 접속

---

## 사용법

### Tab 1 — 자막 생성

1. 영상 파일 업로드 (mp4, mkv, avi, mov, webm)
2. 가사 txt 파일 업로드 (한 줄 = 자막 1개)
3. 언어 선택 (ko / en / ja / zh)
4. **자막 생성** 클릭
5. 보정 테이블에서 시간/텍스트 직접 수정 가능
6. SRT 다운로드 또는 **수정 내용으로 SRT 내보내기**

### Tab 2 — 자막 렌더링

1. 영상 파일 + SRT 파일 업로드
2. 스타일 설정
   - 폰트: NanumGothic / NanumSquare / Malgun Gothic / Arial
   - 크기: 16 ~ 72px
   - 글자색 / 외곽선색 (컬러피커)
   - 외곽선 두께: 0 ~ 5
   - 위치: 하단 중앙 / 상단 중앙 / 중앙
3. **미리보기** — 첫 자막 구간 프레임 확인
4. **영상 렌더링** — 자막 입힌 mp4 출력

---

## 출력 예시

```srt
1
00:00:03,240 --> 00:00:05,810
어떤 말도 위로가 되지 않아

2
00:00:05,810 --> 00:00:08,430
그냥 옆에 있어줘

3
00:00:08,430 --> 00:00:11,120
말없이 손만 잡아줘도 돼
```

---

## 기술 스택

- **WhisperX** — 단어 단위 forced alignment
- **FFmpeg** — 오디오 추출, 자막 렌더링
- **Gradio** — 로컬 UI
- **Python 3.10+**

---

## 호환

생성된 SRT 파일은 **Vrew**, **Adobe Premiere Pro**, **DaVinci Resolve**, **YouTube** 자막 업로드에 바로 사용 가능합니다.
