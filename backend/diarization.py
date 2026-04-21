from pyannote.audio import Pipeline
import os 

pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization",
    use_auth_token=os.getenv("HF_TOKEN")
)

def perform_diarization(audio_data):
    """
    Perform speaker diarization on audio data in memory.
    
    Args:
        audio_data: dict with 'waveform' (torch.Tensor, shape (channels, time)) 
                   and 'sample_rate' (int)
    
    Returns:
        List of speaker segments
    """
    diarization = pipeline(audio_data)

    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append({
            "speaker": speaker,
            "start": float(turn.start),
            "end": float(turn.end)
        })

    return segments