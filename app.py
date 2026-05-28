import subprocess
import tempfile
from pathlib import Path

import gradio as gr

from pipeline import run
from src.burn import preview_frame, render_video
from src.srt_writer import write_srt, segments_to_srt_text


# ── Tab 1: 자막 생성 ──────────────────────────────────────────────────────────

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

    table = [
        [i + 1, s["start"], s["end"], s["text"]]
        for i, s in enumerate(segments)
    ]

    srt_preview = segments_to_srt_text(segments)
    return srt_preview, table, srt_path


def export_edited(table_data):
    """Re-export SRT after user edits the table."""
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


# ── Tab 2: 자막 입히기 ────────────────────────────────────────────────────────

def do_preview(video_file, srt_file, font, font_size, primary_color, outline_color, outline_width, position):
    if video_file is None or srt_file is None:
        return None, "영상과 SRT 파일을 모두 업로드해주세요."
    try:
        img_path = preview_frame(
            video_path=video_file,
            srt_path=srt_file,
            font=font,
            font_size=int(font_size),
            primary_color=primary_color,
            outline_color=outline_color,
            outline=int(outline_width),
            position=position,
        )
        return img_path, "미리보기 완료"
    except FileNotFoundError:
        return None, "ffmpeg를 찾을 수 없습니다. ffmpeg가 설치되어 있는지 확인해주세요."
    except subprocess.CalledProcessError as e:
        return None, f"ffmpeg 오류: {e.stderr.decode(errors='replace')}"


def do_render(video_file, srt_file, font, font_size, primary_color, outline_color, outline_width, position, progress=gr.Progress()):
    if video_file is None or srt_file is None:
        return None, "영상과 SRT 파일을 모두 업로드해주세요."
    try:
        progress(0.1, desc="렌더링 중... (영상 길이에 따라 수 분 소요될 수 있습니다)")
        out_path = render_video(
            video_path=video_file,
            srt_path=srt_file,
            font=font,
            font_size=int(font_size),
            primary_color=primary_color,
            outline_color=outline_color,
            outline=int(outline_width),
            position=position,
        )
        progress(1.0, desc="완료!")
        return out_path, "렌더링 완료!"
    except FileNotFoundError:
        return None, "ffmpeg를 찾을 수 없습니다. ffmpeg가 설치되어 있는지 확인해주세요."
    except subprocess.CalledProcessError as e:
        return None, f"ffmpeg 오류: {e.stderr.decode(errors='replace')}"


# ── UI ────────────────────────────────────────────────────────────────────────

with gr.Blocks(title="LyricSync") as demo:
    gr.Markdown("# LyricSync — 커버 영상 자막 자동 생성")

    with gr.Tabs():

        # ── Tab 1 ──
        with gr.Tab("자막 생성"):
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

        # ── Tab 2 ──
        with gr.Tab("자막 입히기"):
            gr.Markdown("SRT 파일과 영상을 업로드하면 자막이 입혀진 영상을 생성합니다.")

            with gr.Row():
                with gr.Column(scale=1):
                    burn_video_input = gr.File(
                        label="영상 파일",
                        file_types=[".mp4", ".mkv", ".avi", ".mov", ".webm"],
                    )
                    burn_srt_input = gr.File(label="SRT 파일", file_types=[".srt"])

                    gr.Markdown("### 스타일 설정")
                    font_choice = gr.Dropdown(
                        choices=["NanumGothic", "NanumSquare", "Malgun Gothic", "Arial"],
                        value="Malgun Gothic",
                        label="폰트",
                    )
                    font_size = gr.Slider(minimum=16, maximum=72, value=24, step=1, label="폰트 크기")
                    primary_color = gr.ColorPicker(value="#FFFFFF", label="글자 색상")
                    outline_color = gr.ColorPicker(value="#000000", label="외곽선 색상")
                    outline_width = gr.Slider(minimum=0, maximum=5, value=2, step=1, label="외곽선 두께")
                    position = gr.Dropdown(
                        choices=["하단 중앙", "상단 중앙", "중앙"],
                        value="하단 중앙",
                        label="자막 위치",
                    )

                    with gr.Row():
                        preview_btn = gr.Button("미리보기")
                        render_btn = gr.Button("영상 렌더링", variant="primary")

                with gr.Column(scale=2):
                    preview_image = gr.Image(label="미리보기 프레임", type="filepath")
                    burn_status = gr.Textbox(label="상태", interactive=False)

            render_output = gr.File(label="렌더링된 영상 다운로드", interactive=False)

            preview_btn.click(
                fn=do_preview,
                inputs=[
                    burn_video_input, burn_srt_input,
                    font_choice, font_size, primary_color, outline_color, outline_width, position,
                ],
                outputs=[preview_image, burn_status],
            )
            render_btn.click(
                fn=do_render,
                inputs=[
                    burn_video_input, burn_srt_input,
                    font_choice, font_size, primary_color, outline_color, outline_width, position,
                ],
                outputs=[render_output, burn_status],
            )


if __name__ == "__main__":
    demo.launch(inbrowser=True, server_port=7860)
