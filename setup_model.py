"""
setup_model.py — Download the MediaPipe selfie segmentation model.

Run this ONCE before running the game:
    python setup_model.py

It downloads 'selfie_segmenter_landscape.tflite' (~250KB) from Google's
public model storage into the 'assets/' directory.
"""

import os
import urllib.request
import sys

# The landscape model is smaller and faster (144×256 input vs 256×256).
# It's the same model that powers Google Meet background blur.
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "image_segmenter/selfie_segmenter_landscape/float32/latest/"
    "selfie_segmenter_landscape.tflite"
)
MODEL_DIR = "assets"
MODEL_FILENAME = "selfie_segmenter_landscape.tflite"


def download_model():
    os.makedirs(MODEL_DIR, exist_ok=True)
    model_path = os.path.join(MODEL_DIR, MODEL_FILENAME)

    if os.path.exists(model_path):
        size = os.path.getsize(model_path)
        print(f"[OK] Model already exists at '{model_path}' ({size:,} bytes)")
        return model_path

    print(f"Downloading selfie segmentation model...")
    print(f"  URL: {MODEL_URL}")
    print(f"  Destination: {model_path}")

    try:
        urllib.request.urlretrieve(MODEL_URL, model_path, _progress_hook)
        size = os.path.getsize(model_path)
        print(f"\n[OK] Download complete! ({size:,} bytes)")
        return model_path
    except Exception as e:
        print(f"\n[ERROR] Download failed: {e}")
        print()
        print("Please download the model manually:")
        print(f"  1. Open this URL in your browser:")
        print(f"     {MODEL_URL}")
        print(f"  2. Save the file as: {model_path}")
        sys.exit(1)


def _progress_hook(block_num, block_size, total_size):
    downloaded = block_num * block_size
    if total_size > 0:
        percent = min(100, downloaded * 100 // total_size)
        bar = "#" * (percent // 2) + "-" * (50 - percent // 2)
        print(f"\r  [{bar}] {percent}%", end="", flush=True)


if __name__ == "__main__":
    download_model()
    print("\nYou're ready to play! Run: python main.py")
