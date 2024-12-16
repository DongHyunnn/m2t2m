import torchaudio
import torch
from audiocraft.models import MusicGen 
import sounddevice as sd
import argparse
import json
import os
    
def save_audio(waveform, sample_rate, output_path="output.wav"):
    """
    PyTorch 텐서를 WAV 파일로 저장합니다.
    
    Parameters:
    - waveform (torch.Tensor): 오디오 데이터 (Tensor 형식, shape: [1, num_samples] 또는 [channels, num_samples]).
    - sample_rate (int): 샘플링 레이트 (Hz).
    - output_path (str): 저장할 WAV 파일 경로.
    """
    try:
        # 텐서가 CUDA에 있으면 CPU로 복사
        if waveform.is_cuda:
            waveform = waveform.cpu()
        
        # 텐서를 NumPy로 변환하지 않고 바로 저장
        torchaudio.save(output_path, waveform, sample_rate)
        print(f"Audio saved to: {output_path}")
    except Exception as e:
        print(f"Error saving audio: {e}")
        
def music_generation(input_audio_path, captions, output_path, file_name="generated.wav",max_time=30):
    """
    MusicGen을 사용하여 입력 오디오와 캡션 기반 음악을 생성합니다.
    
    Parameters:
    - input_audio_path (str): 입력 WAV 파일 경로.
    - captions (dict): {<time>: <text>} 형태의 캡션 딕셔너리.
    - output_path (str): 생성된 WAV 파일의 저장 경로.
    
    Returns:
    - str: 생성된 WAV 파일 경로.
    """ 
    try:
        # 1. Melody 기반 생성 (첫 블록)
        print("Loading musicgen-melody model...")
        melody_model = MusicGen.get_pretrained("facebook/musicgen-melody")
        melody_model.set_generation_params(duration=10)  # 첫 클립 길이 설정 (초)

        print(f"Loading input audio from: {input_audio_path}")
        melody_waveform, sr = torchaudio.load(input_audio_path)
        melody_waveform = melody_waveform.unsqueeze(0).repeat(1, 1, 1)  # 멜로디 복제

        # 첫 번째 캡션 사용
        first_caption = list(captions.values())[0]
        print(f"Generating first block with caption: {first_caption}")

        melody_output = melody_model.generate_with_chroma(
            descriptions=[first_caption],
            melody_wavs=melody_waveform,
            melody_sample_rate=sr,
            progress=True,
        )
        combined_waveform = melody_output[0]  # 첫 번째 생성 결과
        block_1 = os.path.join(output_path,"block1.wav")
        save_audio(combined_waveform, sample_rate=32000,output_path=block_1)

        # 2. Continuation 생성 (후속 블록)
        print("Loading musicgen-small model...")
        continuation_model = MusicGen.get_pretrained("facebook/musicgen-small")
        continuation_model.set_generation_params(duration=10)  # 클립 길이 설정 (초)
        
        last_n_samples = int(5 * sr)
        curr_time = 10
        n=1
        while curr_time < max_time:
            if n < len(list(captions.values())):
                caption = list(captions.values())[n]
            else:
                caption = ""
            curr_time = curr_time + 10
            n=n+1
            # 이전 블록 기반으로 연속 생성
            continuation_output = continuation_model.generate_continuation(
                prompt=combined_waveform[..., -last_n_samples:],
                prompt_sample_rate=sr,
                descriptions=[caption],
                progress=True,
            )

            # 결과를 이어 붙이기
            combined_waveform = torch.cat((combined_waveform, continuation_output[0]), dim=-1)
            block_n = os.path.join(output_path,f"block{n}.wav")
            save_audio(continuation_output[0], sample_rate=32000,output_path=block_n)
            
            if n > 20: break # 무한 루프 방지

        # 3. 결과 WAV 파일 저장 
        output_file = os.path.join(output_path,file_name)
        save_audio(combined_waveform, sample_rate=32000,output_path=output_file)

        print("Music generation completed successfully.")
        return output_file

    except Exception as e:
        print(f"An error occurred during music generation: {e}")
        return None


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Music generation script.")
    
    # 명령줄 인자 정의
    parser.add_argument("--input_audio_path", type=str, required=True, help="Path to the input audio file (WAV format).")
    parser.add_argument("--captions", type=str, required=True, help="JSON-formatted string containing captions.")
    parser.add_argument("--output_path", type=str, required=True, help="Directory where the output audio file will be saved.")
    parser.add_argument("--file_name", type=str, required=True, help="Name of the generated audio file.")
    parser.add_argument("--max_time", type=int, default=30, help="Maximum generation time in seconds.")
    args = parser.parse_args()
    
    captions_dict = json.loads(args.captions) 
    
    
    result_path = music_generation(
        args.input_audio_path, 
        captions_dict, 
        args.output_path,
        args.file_name,
        args.max_time
    )
    print(result_path)
