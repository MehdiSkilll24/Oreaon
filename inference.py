import torch
import torchaudio
import numpy as np
from model import CNN
from cfg import MEL_PARAMS, TARGET_LENGTH, SAMPLE_RATE

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
TARGET_LENGTH = 44100
THRESHOLD = 0.7  # tune this after evaluating on your data

class ClapDetector:
    def __init__(self, model_path="best_model.pt"):
        self.model = CNN().to(DEVICE)
        self.model.load_state_dict(torch.load(model_path, map_location=DEVICE))
        self.model.eval()
        self.transform = torchaudio.transforms.MelSpectrogram(**MEL_PARAMS).to(DEVICE)

    def predict(self, audio_np: np.ndarray, sr: int) -> bool:
        """
        audio_np: numpy array of raw audio samples (float32)
        sr: sample rate of the incoming audio
        returns: True if clap detected
        """
        waveform = torch.tensor(audio_np, dtype=torch.float32).unsqueeze(0)  # [1, samples]

        # resample if needed
        if sr != 44100:
            waveform = torchaudio.functional.resample(waveform, sr, 44100)
        # pad or trim
        if waveform.shape[1] > TARGET_LENGTH:
            waveform = waveform[:, :TARGET_LENGTH]
        elif waveform.shape[1] < TARGET_LENGTH:
            pad = TARGET_LENGTH - waveform.shape[1]
            waveform = torch.nn.functional.pad(waveform, (0, pad))

        waveform = waveform.to(DEVICE)
        spec = self.transform(waveform).clamp(min=1e-9).log()
        spec = (spec - spec.mean()) / (spec.std() + 1e-8)
        spec = spec.unsqueeze(0)  # add batch dim → [1, 1, n_mels, time]

        with torch.no_grad():
            logit = self.model(spec)
            prob = torch.sigmoid(logit).item()

        return prob > THRESHOLD