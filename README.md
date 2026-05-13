# auto-caption

오디오 파일을 넣으면 자동으로 SRT 자막을 생성해주는 도구.

**faster-whisper**로 단어별 타임스탬프를 추출하고, **Claude Code**가 문맥을 파악해서 자연스러운 위치에서 줄을 나눕니다.

---

## 동작 방식

1. faster-whisper가 오디오에서 단어별 타임스탬프를 추출합니다.
2. 단어들을 10글자 단위로 묶어 청크를 만듭니다.
3. Claude가 문맥을 보고 청크들을 자연스러운 자막 세그먼트로 병합/분리합니다.
4. 문장 부호(`.` `!` `?`) 기준으로 한 번 더 다듬은 뒤 SRT 파일로 저장합니다.

---

## 요구사항

- Python 3.12+
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [Claude Code CLI](https://claude.ai/code) (로그인 상태여야 함)

### 설치

```powershell
pip install faster-whisper
```

Claude Code CLI는 위 링크에서 설치 후 `claude login`으로 로그인하세요.

---

## 사용법

### 기본 — 현재 폴더의 mp3 파일 전부 처리

오디오 파일이 있는 폴더에서 PowerShell을 열고 실행합니다.
(폴더 빈 곳에서 Shift+우클릭 → "PowerShell 창 열기")

```powershell
.\caption.ps1
```

현재 폴더에 있는 `.mp3` 파일을 전부 찾아서 순서대로 처리합니다.

### 특정 파일만 처리

```powershell
.\caption.ps1 강의01.mp3 강의02.mp3
```

### 결과

오디오 파일과 같은 폴더에 `.srt` 파일이 생성됩니다.

```
강의01.mp3  →  강의01.srt
강의02.mp3  →  강의02.srt
```

---

## 지원 포맷

faster-whisper가 지원하는 모든 오디오/영상 포맷

`mp3` `mp4` `wav` `m4a` `mkv` `webm` 등

---

## 주의사항

- 처음 실행 시 Whisper 모델(`medium`)을 자동으로 다운로드합니다. (약 1.5GB)
- Claude Code CLI가 설치되어 있고 로그인된 상태여야 합니다.
- 오디오 길이에 따라 처리 시간이 달라집니다.
