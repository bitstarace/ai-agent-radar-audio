"""Gemini APIでポッドキャスト風の対話台本を生成し、Gemini TTSで音声化する。"""
from __future__ import annotations

import io
import os
import time
import wave

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

SCRIPT_MODEL = os.environ.get("GEMINI_SCRIPT_MODEL", "gemini-2.5-flash")
TTS_MODEL = os.environ.get("GEMINI_TTS_MODEL", "gemini-3.8-flash-tts")

SPEAKER_A = "ホストA"
SPEAKER_B = "ホストB"
VOICE_A = "Kore"
VOICE_B = "Puck"

SCRIPT_PROMPT_TEMPLATE = """\
あなたはポッドキャストの構成作家です。以下は「AI Agent Radar」という、\
Claude Code/AIエージェント関連の動向をまとめた日次レポートです。

このレポートの内容を、{speaker_a}と{speaker_b}という2人のホストが\
テンポよく会話しながら解説するポッドキャスト台本を作成してください。

要件:
- 日本語の自然な話し言葉で書くこと（Markdown記号や見出し記号は使わない）
- レポートの主要トピック(ニュース・トレンド、AIコードレビュー関連、\
注目GitHubリポジトリ、Redditの反応)を満遍なく取り上げること
- 聞いて楽しい、掘り下げのある掛け合いにすること(単なる読み上げにしない)
- 全体で5〜8分程度で読み上げられる分量(日本語で1500〜2500文字程度)
- 各発言は必ず "{speaker_a}: " または "{speaker_b}: " で始める形式のみで出力する
  (それ以外の説明文やタイトルは一切出力しない)
- 冒頭の挨拶と締めの一言を入れること

レポート本文:
---
{report}
---
"""


def _call_with_retry(fn, attempts: int = 5, base_wait: int = 30):
    """一時的なサーバー側エラー(429/500/503)のときだけ、待ってから再試行する。"""
    for i in range(attempts):
        try:
            return fn()
        except genai_errors.APIError as exc:
            retryable = getattr(exc, "code", None) in (429, 500, 503)
            if not retryable or i == attempts - 1:
                raise
            wait = base_wait * (2**i)  # 30, 60, 120, 240 秒
            print(f"一時エラー({exc.code})。{wait}秒後に再試行 ({i + 1}/{attempts - 1})")
            time.sleep(wait)


def generate_dialogue_script(client: genai.Client, report_markdown: str) -> str:
    prompt = SCRIPT_PROMPT_TEMPLATE.format(
        speaker_a=SPEAKER_A, speaker_b=SPEAKER_B, report=report_markdown
    )
    response = _call_with_retry(
        lambda: client.models.generate_content(model=SCRIPT_MODEL, contents=prompt)
    )
    text = (response.text or "").strip()
    if not text:
        raise RuntimeError("Geminiから台本テキストが返されませんでした")
    return text


def synthesize_audio(client: genai.Client, dialogue_script: str) -> bytes:
    """dialogue_script を読み上げ、PCM(16bit/24kHz/mono)のバイト列を返す。"""
    response = _call_with_retry(
        lambda: client.models.generate_content(
            model=TTS_MODEL,
            contents=dialogue_script,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                        speaker_voice_configs=[
                            types.SpeakerVoiceConfig(
                                speaker=SPEAKER_A,
                                voice_config=types.VoiceConfig(
                                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                        voice_name=VOICE_A
                                    )
                                ),
                            ),
                            types.SpeakerVoiceConfig(
                                speaker=SPEAKER_B,
                                voice_config=types.VoiceConfig(
                                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                        voice_name=VOICE_B
                                    )
                                ),
                            ),
                        ]
                    )
                ),
            ),
        )
    )
    part = response.candidates[0].content.parts[0]
    pcm_bytes = part.inline_data.data
    if not pcm_bytes:
        raise RuntimeError("Gemini TTSから音声データが返されませんでした")
    return pcm_bytes


def pcm_to_wav_bytes(
    pcm_bytes: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2
) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()
