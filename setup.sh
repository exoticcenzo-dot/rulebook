#!/bin/bash
# Prepares a fresh machine: installs the voice engine and downloads its model.
set -e
pip install --break-system-packages -q kokoro-onnx soundfile opencv-python-headless pillow numpy
(apt-get install -y -q fonts-noto-cjk || true)
mkdir -p /home/claude/tts && cd /home/claude/tts
for f in kokoro-v1.0.onnx voices-v1.0.bin; do
  [ -s "$f" ] || curl -sSL -o "$f" "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/$f"
done
