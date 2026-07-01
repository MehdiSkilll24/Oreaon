SAMPLE_RATE = 44100
TARGET_LENGTH = 44100
N_MELS = 64
N_FFT = 1024
HOP_LENGTH = 512
F_MAX = 8000

MEL_PARAMS = dict(
    sample_rate=SAMPLE_RATE,
    n_mels=N_MELS,
    n_fft=N_FFT,
    hop_length=HOP_LENGTH,
    f_max=F_MAX
)