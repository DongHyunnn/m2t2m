from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import argparse
import re

parser = argparse.ArgumentParser()
parser.add_argument("--system", default="Reflect the instruction to caption. Answer only with the modified caption.", type=str)
parser.add_argument("--caption", default="This is a symphonic orchestra playing a piece that's riveting, thrilling and exciting. The peace would be suitable in a movie when something grand and impressive happens. There are clarinets, tubas, trumpets and french horns being played. The brass instruments help create that sense of a momentous occasion.', 'time': '0:00-10:00'} {'text': 'This is a classical music piece from a movie soundtrack. There is a clarinet playing the main melody while a brass section and a flute are playing the melody. The rhythmic background is provided by the acoustic drums. The atmosphere is epic and victorious. This piece could be used in the soundtrack of a historical drama movie during the scenes of an army marching towards the end.', 'time': '10:00-20:00'} {'text': 'This is a live performance of a classical music piece. There is a harp playing the melody while a horn is playing the bass line in the background. The atmosphere is epic. This piece could be used in the soundtrack of a historical drama movie during the scenes of an adventure video game.", type=str)
parser.add_argument("--instruction", default="happy", type=str)
args = parser.parse_args()


def load_model_and_tokenizer(model_name="meta-llama/Llama-2-3b", dtype=torch.float16):
    """
    LLaMA 모델과 토크나이저를 로드합니다.
    """
    try:
        # 토크나이저 로드
        tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)

        # 패딩 토큰 설정
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token  # eos_token을 pad_token으로 설정

        # 모델 로드
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=dtype,
            device_map="auto",
            trust_remote_code=True
        )
        return model, tokenizer
    except Exception as e:
        raise RuntimeError(f"Error loading model or tokenizer: {e}")
    
def generate_text(model, tokenizer, prompt, gen_len=100, temperature=0.5, top_p=0.9):
    """
    입력 프롬프트를 제외하고 생성된 텍스트만 반환합니다.

    Parameters:
    - model: LLaMA 모델 객체.
    - tokenizer: LLaMA 토크나이저 객체.
    - prompt (str): 입력 프롬프트.
    - gen_len (int): 생성할 최대 텍스트 길이.
    - temperature (float): 출력의 다양성을 조절하는 파라미터.
    - top_p (float): 상위 확률 누적 샘플링.

    Returns:
    - str: 생성된 텍스트(입력 프롬프트 제외).
    """
    # 입력 텍스트를 텐서로 변환
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    max_length = len(prompt) + gen_len
    # 텍스트 생성
    with torch.inference_mode():
        outputs = model.generate(
            inputs.input_ids,
            max_length=max_length,
            temperature=temperature,
            top_p=top_p,
            do_sample=True,         
            pad_token_id=tokenizer.pad_token_id  # 패딩 토큰 설정
        )

    # 전체 시퀀스 디코딩
    full_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
     
    generated_text = full_output.split("Output: \n", 1)
    if len(generated_text) > 1:
        generated_text = generated_text[1].strip() 
    else :
        raise ValueError("Wrong format")
        
    json_output = extract_json(generated_text)
    

    return str(json_output)

def extract_json(output):
    match = re.search(r"\{.*?\}", output, re.DOTALL)  # JSON 패턴만 추출
    return match.group(0) if match else None

if __name__ == "__main__":
    # 모델 이름 (Hugging Face 허브에서 제공되는 이름 사용)
    model_name = "meta-llama/Llama-3.2-3B-Instruct"

    # 모델과 토크나이저 로드
    # print("Loading model and tokenizer...")
    model, tokenizer = load_model_and_tokenizer(model_name)

    # 입력 프롬프트 설정
    prompt = args.system + "\nprevious caption :" + args.caption + "\nmusical expression :" + args.instruction + "\nOutput: \n"

    # 텍스트 생성
    # print("Generating text...")
    generated_text = generate_text(model, tokenizer, prompt, gen_len=100)

    # 결과 출력
    print(generated_text)
