import tempfile
from pathlib import Path

import gradio as gr

from pipeline import run
from src.srt_writer import write_srt, segments_to_srt_text


def generate(video_file, lyrics_file, language, progress=gr.Progress()):
    if video_file is None or lyrics_file is None:
        return "영상과 가사 파일을 모두 업로드해주세요.", None, None

    steps = [
        "오디오 추출 중...",
        "WhisperX 모델 로드 중...",
        "음성 인식 + 타임스탬프 추출 중...",
        "가사 파싱 중...",
        "가사-타임스탬프 정렬 중...",
        "SRT 저장 중...",
        "완료!",
    ]
    step_iter = iter(range(len(steps)))

    def on_progress(msg: str):
        idx = next(step_iter, len(steps) - 1)
        progress(idx / len(steps), desc=msg)

    try:
        segments, srt_path = run(
            video_path=video_file,
            lyrics_path=lyrics_file,
            model_size="medium",
            language=language,
            progress_callback=on_progress,
        )
    except Exception as e:
        return f"오류 발생: {e}", None, None

    # [index, start(float), end(float), text] — float so Gradio stores as number
    table = [
        [i + 1, s["start"], s["end"], s["text"]]
        for i, s in enumerate(segments)
    ]

    srt_preview = segments_to_srt_text(segments)
    return srt_preview, table, srt_path


def export_edited(table_data):
    """Re-export SRT after user edits the table.
    Gradio passes gr.Dataframe contents as a pandas DataFrame.
    """
    if table_data is None or len(table_data) == 0:
        return None

    segments = []
    for _, row in table_data.iterrows():
        segments.append({
            "text": str(row.iloc[3]),
            "start": float(row.iloc[1]),
            "end": float(row.iloc[2]),
        })

    out_path = str(Path(tempfile.gettempdir()) / "lyricsync_edited.srt")
    write_srt(segments, out_path)
    return out_path


with gr.Blocks(title="LyricSync") as demo:
    gr.Markdown("# LyricSync — 커버 영상 자막 자동 생성")
    gr.Markdown("영상과 가사 txt를 업로드하면 타임스탬프가 맞춰진 SRT 파일을 생성합니다.")

    with gr.Row():
        with gr.Column(scale=1):
            video_input = gr.File(label="영상 파일", file_types=[".mp4", ".mkv", ".avi", ".mov", ".webm"])
            lyrics_input = gr.File(label="가사 txt 파일", file_types=[".txt"])
            language = gr.Dropdown(
                choices=["ko", "en", "ja", "zh"],
                value="ko",
                label="언어",
            )
            run_btn = gr.Button("자막 생성", variant="primary")

        with gr.Column(scale=2):
            srt_preview = gr.Textbox(
                label="SRT 미리보기",
                lines=20,
                interactive=False,
            )

    gr.Markdown("### 보정 테이블 (시간/텍스트 직접 수정 가능)")
    segment_table = gr.Dataframe(
        headers=["#", "시작(초)", "종료(초)", "가사"],
        datatype=["number", "number", "number", "str"],
        interactive=True,
        wrap=True,
    )

    with gr.Row():
        download_btn = gr.File(label="SRT 다운로드", interactive=False)
        export_btn = gr.Button("수정 내용으로 SRT 내보내기")

    run_btn.click(
        fn=generate,
        inputs=[video_input, lyrics_input, language],
        outputs=[srt_preview, segment_table, download_btn],
    )

    export_btn.click(
        fn=export_edited,
        inputs=[segment_table],
        outputs=[download_btn],
    )

if __name__ == "__main__":
    demo.launch(inbrowser=True)
