import torchaudio
import torch

def load_and_resample(wav_path: str, target_sr: int = 16000):
    """
    Load an audio file and return a single-channel normalized waveform at target sample rate.
    """
    waveform, sr = torchaudio.load(wav_path)

    # If stereo → convert to mono
    if waveform.size(0) > 1:
        waveform = torch.mean(waveform, dim=0, keepdim=True)

    # Resample if needed
    if sr != target_sr:
        waveform = torchaudio.functional.resample(waveform, sr, target_sr)

    # Normalize
    waveform = waveform / (torch.max(torch.abs(waveform)) + 1e-9)

    return waveform, target_sr


def bytes_to_tempfile(wav_bytes: bytes, suffix=".wav"):
    """
    Writes bytes to a secure temporary file and returns its path.
    """
    import tempfile, os
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    with open(path, "wb") as f:
        f.write(wav_bytes)
    return path
