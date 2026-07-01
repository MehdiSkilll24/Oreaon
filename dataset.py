import torch, torchaudio
import glob
from cfg import MEL_PARAMS, SAMPLE_RATE, TARGET_LENGTH
TARGET_LENGTH = 44100

class Dataset(torch.utils.data.Dataset):
    def __init__(self):
        super().__init__()
        # we loop through each file from both respective wav folders and put them in their respective lists 

        pos_clap = [(f, 1) for f in glob.glob("data/claps/*.wav")]
        false_clap = [(f, 0) for f in glob.glob("data/negatives/*.wav")]

        # Check class balance
        print(f"Claps: {len(pos_clap)} | Negatives: {len(false_clap)}")

        self.all_files = pos_clap + false_clap
        
        # we define the mel spectogram transform object (to project the sound files into a 2d spectogram)
        self.transform = torchaudio.transforms.MelSpectrogram(**MEL_PARAMS)
        self.resample_cache = {}

    def __len__(self):
        return len(self.all_files)

    def __getitem__(self, index):
        file_path, label = self.all_files[index]
        waveform, sr = torchaudio.load(file_path)

        # Fix 1: resample if needed
        if sr != 44100:
            # We cache the transform object to be used for each new sample rate then we cache that sample rate for the transform to apply directly on it
            # alternative way: we transform for each SR != 44k -> slow, instead we save any new sr and transform only once for the first time, then it's cached and can be remembered
            if sr not in self.resample_cache:
                self.resample_cache[sr] = torchaudio.transforms.Resample(sr, 44100)
            waveform = self.resample_cache[sr](waveform)

        # Fix 2: force mono (CNN accepts mono only i.e 1 channel)
        waveform = waveform.mean(dim=0, keepdim=True)

        # Fix 3: pad or trim
        if waveform.shape[1] > TARGET_LENGTH:
            waveform = waveform[:, :TARGET_LENGTH]
        elif waveform.shape[1] < TARGET_LENGTH:
            pad = TARGET_LENGTH - waveform.shape[1]
            waveform = torch.nn.functional.pad(waveform, (0, pad))

        # Fix 4: mel spectrogram projection + log scale
        waveform = self.transform(waveform)
        waveform = waveform.clamp(min=1e-9).log()
        waveform = (waveform - waveform.mean()) / (waveform.std() + 1e-8)


        # Fix 5: correct label dtype
        label = torch.tensor(label, dtype=torch.float32)

        return waveform, label