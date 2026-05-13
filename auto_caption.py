import sys
import io
import json
import subprocess
from pathlib import Path
from faster_whisper import WhisperModel

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def transcribe(audio_path: str) -> list[dict]:
    model = WhisperModel("medium", device="auto", compute_type="default")
    segments, _ = model.transcribe(audio_path, word_timestamps=True)

    words = []
    for segment in segments:
        if segment.words:
            for word in segment.words:
                words.append({
                    "word": word.word,
                    "start": round(word.start, 3),
                    "end": round(word.end, 3),
                })
    return words


def chunk_words(words: list[dict], max_chars: int = 10) -> list[dict]:
    chunks = []
    current_words = []
    current_len = 0

    for w in words:
        word_len = len(w["word"].strip())
        if current_words and current_len + word_len > max_chars:
            chunks.append({
                "start": current_words[0]["start"],
                "end": current_words[-1]["end"],
                "text": "".join(w["word"] for w in current_words).strip(),
            })
            current_words = []
            current_len = 0
        current_words.append(w)
        current_len += word_len

    if current_words:
        chunks.append({
            "start": current_words[0]["start"],
            "end": current_words[-1]["end"],
            "text": "".join(w["word"] for w in current_words).strip(),
        })

    return chunks


def ask_claude_for_segments(words: list[dict]) -> list[dict]:
    chunks = chunk_words(words, max_chars=10)
    chunks_json = json.dumps(chunks, ensure_ascii=False, indent=2)

    prompt = f"""아래는 오디오 자막을 10글자 단위로 미리 묶은 청크 데이터입니다.
문맥을 파악해서 자연스러운 자막 세그먼트로 병합하거나 분리해 주세요.

규칙:
- 한 세그먼트는 최대 20자 이내, 반드시 한 문장만
- 문장이 끊기는 자연스러운 위치(마침표, 쉼표, 접속사 앞 등)에서 분리
- 각 세그먼트의 start/end는 포함된 청크들의 타임스탬프 기준
- 문맥상 말이 되지 않는 단어는 Whisper 오인식으로 판단하고 자연스럽게 교정
- 앞뒤 문맥을 보고 잘린 어절은 이어붙여서 완성된 문장으로 만들기
- 말줄임표, 불필요한 추임새(어, 음, 그)는 문맥에 방해되면 생략 가능
- 반드시 아래 JSON 배열 형식으로만 응답 (다른 텍스트 없이)

[
  {{"start": 0.0, "end": 2.5, "text": "세그먼트 텍스트"}},
  ...
]

청크 데이터:
{chunks_json}"""

    result = subprocess.run(
        ["claude", "--print", prompt],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    if result.returncode != 0:
        raise RuntimeError(f"Claude 호출 실패: {result.stderr}")

    output = result.stdout.strip()

    # JSON 블록 추출
    if "```" in output:
        start = output.find("```")
        end = output.rfind("```")
        output = output[start:end].strip()
        output = output.lstrip("`json").lstrip("`").strip()

    return json.loads(output)


def format_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def split_by_sentence(segments: list[dict]) -> list[dict]:
    import re
    result = []
    for seg in segments:
        # 문장 끝 기호 뒤에서 분리 (기호는 앞 문장에 포함)
        parts = re.split(r'(?<=[.!?])\s+', seg["text"].strip())
        parts = [p.strip() for p in parts if p.strip()]
        if len(parts) <= 1:
            result.append(seg)
            continue
        total_chars = sum(len(p) for p in parts)
        duration = seg["end"] - seg["start"]
        current_start = seg["start"]
        for p in parts:
            ratio = len(p) / total_chars
            current_end = round(current_start + duration * ratio, 3)
            result.append({"start": current_start, "end": current_end, "text": p})
            current_start = current_end
    return result


def to_srt(segments: list[dict]) -> str:
    lines = []
    for i, seg in enumerate(segments, 1):
        lines.append(str(i))
        lines.append(f"{format_time(seg['start'])} --> {format_time(seg['end'])}")
        lines.append(seg["text"].strip())
        lines.append("")
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("사용법: python auto_caption.py <오디오파일>")
        sys.exit(1)

    audio_path = sys.argv[1]
    output_path = Path(audio_path).with_suffix(".srt")

    print(f"[1/3] Whisper로 타임스탬프 추출 중... ({audio_path})")
    words = transcribe(audio_path)
    print(f"      → {len(words)}개 단어 추출 완료")

    print("[2/3] Claude에게 문맥 기반 줄바꿈 요청 중...")
    segments = ask_claude_for_segments(words)
    segments = split_by_sentence(segments)
    print(f"      → {len(segments)}개 세그먼트 생성 완료")

    print(f"[3/3] SRT 파일 저장 중... ({output_path})")
    srt_content = to_srt(segments)
    output_path.write_text(srt_content, encoding="utf-8")

    print(f"\n완료! → {output_path}")


if __name__ == "__main__":
    main()
