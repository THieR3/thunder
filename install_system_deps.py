import subprocess
import sys

subprocess.run(["apt-get", "update"], check=True)
subprocess.run(["apt-get", "install", "-y", "tesseract-ocr", "tesseract-ocr-fra"], check=True)