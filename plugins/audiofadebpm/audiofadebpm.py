import os
import json
import random
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QTextEdit, QProgressBar, QInputDialog, QFileDialog,
    QVBoxLayout, QSpinBox, QLineEdit
)
from core.settings import SettingsManager
from core.ffmpegworker import FFmpegWorkerManager

class AudioFadeBPMWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = SettingsManager.instance()
        self.worker_manager = FFmpegWorkerManager()
        self._init_ui()
        self._connect_signals()
        self.input_folder = ""
        self.output_path = ""
        self.audio_files = []
        self._fade_sec = 2

    def _init_ui(self):
        self.select_btn = QPushButton("Selecteer map met video's")
        self.folder_label = QLabel("Geen map geselecteerd")
        self.output_btn = QPushButton("Kies exportlocatie")
        self.output_label = QLabel("Geen export-bestand gekozen")
        self.bpm_label = QLabel("BPM (optioneel):")
        self.bpm_input = QLineEdit()
        self.bpm_input.setPlaceholderText("Bijv. 128")
        self.crossfade_spin = QSpinBox()
        self.crossfade_spin.setRange(0, 10)
        self.crossfade_spin.setValue(2)
        self.crossfade_label = QLabel("Crossfade (seconden):")
        self.start_btn = QPushButton("Start Audio Fade+Concat")
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.progress = QProgressBar()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout = QVBoxLayout(self)
        for w in (
            self.select_btn, self.folder_label, self.output_btn, self.output_label,
            self.bpm_label, self.bpm_input, self.crossfade_label, self.crossfade_spin,
            self.start_btn, self.cancel_btn,
            QLabel("Voortgang:"), self.progress,
            QLabel("Log:"), self.log_output
        ):
            layout.addWidget(w)

    def _connect_signals(self):
        self.select_btn.clicked.connect(self.select_folder)
        self.output_btn.clicked.connect(self.select_output)
        self.start_btn.clicked.connect(self.start_audio_fade_batch)
        self.cancel_btn.clicked.connect(self._on_cancel)

    def log(self, msg):
        self.log_output.append(msg)

    def select_folder(self):
        fld = QFileDialog.getExistingDirectory(self, "Selecteer videomap")
        if fld:
            self.input_folder = fld
            self.folder_label.setText(fld)
            self.log(f"📁 Geselecteerd: {fld}")

    def select_output(self):
        out_path, _ = QFileDialog.getSaveFileName(self, "Kies output-bestand", "", "MP3 (*.mp3);;WAV (*.wav);;AAC (*.aac)")
        if out_path:
            self.output_path = out_path
            self.output_label.setText(f"{out_path}")
            self.log(f"💾 Export-bestand gekozen: {out_path}")

    def start_audio_fade_batch(self):
        if not self.input_folder:
            self.log("❌ Geen map geselecteerd.")
            return
        if not self.output_path:
            self.log("❌ Geen export-bestand gekozen.")
            return
        files = [f for f in os.listdir(self.input_folder)
                 if f.lower().endswith(('.mp4', '.avi', '.mkv', '.mov', '.webm', '.wmv', '.mpg', '.mpeg', '.flv'))]
        if not files:
            self.log("❌ Geen videobestanden gevonden.")
            return

        self._fade_sec = self.crossfade_spin.value()
        self.audio_files = []
        self.progress.setMaximum(len(files) + 1)
        self.progress.setValue(0)
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.log("▶️ Start audio-extractie en fades...")
        self._extract_index = 0
        self._files = files
        self._extract_next_audio()

    def _extract_next_audio(self):
        if self._extract_index >= len(self._files):
            self.log("🎬 Alle audio geëxtraheerd. Start concat...")
            self._concat_audios()
            return

        vid = self._files[self._extract_index]
        in_path = os.path.join(self.input_folder, vid)
        out_audio = os.path.join(self.input_folder, f"_audtmp_{self._extract_index}.wav")
        self.audio_files.append(out_audio)

        # Eerst de duur bepalen via ffprobe
        from subprocess import check_output, CalledProcessError
        try:
            cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{in_path}"'
            out = check_output(cmd, shell=True).decode().strip()
            d = float(out)
        except Exception as e:
            d = 2.0
            self.log(f"⚠️ Kan duur niet bepalen ({vid}), fallback 2.0s: {e}")

        fade_cmd = f'ffmpeg -y -i "{in_path}" -vn -af "afade=t=in:ss=0:d={self._fade_sec},afade=t=out:st={max(0, d-self._fade_sec)}:d={self._fade_sec}" -ac 2 -ar 44100 "{out_audio}"'
        self.log(f"🎧 Extract/fade {vid} ({self._extract_index+1}/{len(self._files)})")
        self.worker_manager.start_worker(
            [fade_cmd],
            lambda v: self.progress.setValue(self._extract_index+1),
            self.log,
            self._extract_callback
        )

    def _extract_callback(self, success, _):
        if not success:
            self.log("❌ Fout tijdens audio-extractie, ga verder met volgende.")
        self._extract_index += 1
        self._extract_next_audio()

    def _concat_audios(self):
        concat_list_path = os.path.join(self.input_folder, "_concat_audio.txt")
        with open(concat_list_path, "w") as f:
            for af in self.audio_files:
                f.write(f"file '{af}'\n")

        ext = os.path.splitext(self.output_path)[1].lower()
        if ext == ".mp3":
            concat_cmd = f'ffmpeg -y -f concat -safe 0 -i "{concat_list_path}" -c:a libmp3lame -b:a 192k "{self.output_path}"'
        elif ext in [".wav", ".pcm"]:
            concat_cmd = f'ffmpeg -y -f concat -safe 0 -i "{concat_list_path}" -c:a pcm_s16le "{self.output_path}"'
        elif ext in [".aac", ".m4a"]:
            concat_cmd = f'ffmpeg -y -f concat -safe 0 -i "{concat_list_path}" -c:a aac -b:a 192k "{self.output_path}"'
        else:
            concat_cmd = f'ffmpeg -y -f concat -safe 0 -i "{concat_list_path}" -c:a aac -b:a 192k "{self.output_path}"'

        self.log(f"▶️ Concat audio-bestanden...\n{concat_cmd}")
        self.worker_manager.start_worker(
            [concat_cmd],
            lambda v: self.progress.setValue(self.progress.maximum()),
            self.log,
            self._on_finished
        )

    def _on_cancel(self):
        self.worker_manager.cancel()

    def _on_finished(self, success, _):
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        if success:
            self.log("✅ Audio concat+fade voltooid!")
        else:
            self.log("❌ Audio gefaald/geannuleerd.")
