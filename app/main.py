from flask import Flask, request, jsonify, send_from_directory,render_template
import os
import uuid
import subprocess
from flask_cors import CORS 

import json

import shlex

def music_to_caption(music_file):
    
    command = f"/root/anaconda3/envs/ctp431/bin/python /root/musicai/app/caption.py --audio_path '{music_file}'"
    
    try:
        # subprocess.run을 사용하여 명령 실행 및 출력 캡처
        result = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,  # 표준 출력 캡처
            stderr=subprocess.PIPE,  # 표준 오류 캡처
            text=True,               # 출력을 문자열로 반환 
        ) 
        caption_dict = parse_caption(result.stdout)    
              
        global latest_file_id  
        global stored_captions  
        stored_captions[latest_file_id] = caption_dict   
             
        # 결과 반환
        return str(caption_dict)
    except Exception as e:
        return str(e)
    
    # # 기본값 향후 주석처리
    # caption = "A peaceful melody with soft strings and subtle percussion."
    # return caption

"""TODO: 적절한 sllm을 찾아 적용해야 합니다. 3080ti: 12GB VRAM 
    3B 정도의 모델을 사용해도 성능이 괜찮을지 모르겠네요.          
    우선 현재는 llama 3.2 1B와 3B를 사용할 수 있을듯 합니다.
    생성된 텍스트가 영 이상하다면 gpt 결재를 염두해둡시다.  
"""
def generate_new_caption(input_text):
    # 입력 단순화
    input_text = ", ".join(set(input_text.split(", ")))  # 중복 제거
    # prev_caption = prev_caption[:500]  # 최대 길이 제한
    global latest_file_id  
    global stored_captions  
    
    # 곡 정보 풍성하게
    system_prompt = (
        'Answer with only the new caption content. Follow this example format. \n'
        'Only output the data in JSON format. Do not add explanations or any other text. \n'
        '{\n expression: ~. \n mood: ~. \n dynamics: ~. \n instruments: ~. \n style: ~. \n}\n'
        'Do not include any introductory or closing remarks, only provide JSON formatted output. \n'
        'Now process the following input and provide output in the same format: \n'
        'Input: Add relevant details such as mood, dynamics, instruments and style to make it more vivid and aligned with the input expression. \n'
    )
    command = f'/root/anaconda3/envs/llama32/bin/python /root/musicai/app/text_prompting.py --system {shlex.quote((system_prompt))} --caption {shlex.quote((list(stored_captions[latest_file_id].values())[0]))} --instruction {shlex.quote((input_text))}'
    print(command)
    try:
        # subprocess.run을 사용하여 명령 실행 및 출력 캡처
        result = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,  # 표준 출력 캡처
            stderr=subprocess.PIPE,  # 표준 오류 캡처
            text=True,               # 출력을 문자열로 반환 
        ) 
            
        additional_info = result.stdout   
        # 결과 반환
    except Exception as e:
        return str(e)
    
    system_prompt = (
        "Answer with only the new caption content. Follow this example format.\n"
        "Only output the data in JSON format. Do not add explanations or any other text.\n"
        "{\ncaption: This is a jazz-inspired classical music piece from a movie soundtrack. The main melody is played by...\n}\n"
        "Do not include any introductory or closing remarks, only provide JSON formatted output.\n"
        "Now process the following input and provide output in the same format: \n"
        "Input: Modify the caption to reflect the given musical expression. \n"
        "Add relevant details to make it more vivid and aligned with the input expression. \n"
    )
    
    for time_stamp, prev_caption in stored_captions[latest_file_id].items():
        command = f'/root/anaconda3/envs/llama32/bin/python /root/musicai/app/text_prompting.py --system {shlex.quote(system_prompt)} --caption {shlex.quote(prev_caption)} --instruction {shlex.quote(additional_info)}'
        print(command)
        try:
            # subprocess.run을 사용하여 명령 실행 및 출력 캡처
            result = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,  # 표준 출력 캡처
                stderr=subprocess.PIPE,  # 표준 오류 캡처
                text=True,               # 출력을 문자열로 반환 
            ) 
             
            stored_captions[latest_file_id][time_stamp] = result.stdout   
            # 결과 반환
        except Exception as e:
            return str(e)
    return str(stored_captions[latest_file_id])
import ast

def parse_caption(input_string):
    """
    입력된 문자열을 파싱하여 {time: text} 형태의 딕셔너리를 반환합니다.

    Parameters:
    - input_string (str): 여러 개의 딕셔너리 문자열이 공백으로 연결된 문자열.

    Returns:
    - dict: {time: text} 형태의 딕셔너리.
    """
    # 1. 문자열 분리
    dict_strings = input_string.strip().split('\n')

    # 분리된 문자열에서 딕셔너리 형태를 복원
    dict_strings = [s if s.startswith('{') else '{' + s for s in dict_strings]
    dict_strings = [s if s.endswith('}') else s + '}' for s in dict_strings]

    # 결과를 저장할 딕셔너리
    result = {}

    # 2. 개별 딕셔너리 문자열 파싱
    for dict_str in dict_strings:
        try:
            # 문자열을 딕셔너리로 변환
            caption_dict = ast.literal_eval(dict_str)
            # 'time'과 'text' 추출하여 결과 딕셔너리에 추가
            time = caption_dict.get('time', '').strip()
            text = caption_dict.get('text', '').strip()
            if time and text:
                result[time] = text
        except Exception as e:
            print(f"Error parsing: {dict_str}\nException: {e}")
            continue

    return result

    # 기본값 향후 주석 처리
    # new_caption = f"{prev_caption} and also inspired by {input_text}."
    # return new_caption

"""TODO: music gen을 적용해야 합니다. 받아온 캡션으로 model call해서 wav를 생성"""
def generate_music_based_on_caption():
    """
    캡션을 기반으로 음악을 생성하는 함수.
    실제로는 AI 모델이나 알고리즘을 사용하여 음악을 생성해야 합니다.
    여기에선 간단한 예시로 'generated_music.wav' 파일을 반환합니다.
    """ 
    
    global latest_file_id  
    global stored_captions
    
    filename = f"{latest_file_id}.wav"
    input_file = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    caption = stored_captions[latest_file_id]
    generated_music_file = os.path.join(app.config["OUTPUT_FOLDER"],filename)
    
    json_caption = json.dumps(caption)
    command = (
        f"/root/anaconda3/envs/audiocraft/bin/python /root/musicai/app/music_gen.py "
        f"--input_audio_path {shlex.quote(input_file)} "
        f"--captions {shlex.quote(json_caption)} "
        f"--output_path {shlex.quote(app.config['OUTPUT_FOLDER'])} "
        f"--file_name {shlex.quote(filename)} "
        f"--max_time 30"
    )
    print(command)
    try:
        result = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,  # 표준 출력 캡처
            stderr=subprocess.PIPE,  # 표준 오류 캡처
            text=True,               # 출력을 문자열로 반환 
        ) 
        print(result.stdout)
        print(result.stderr)
        return result.stdout
    except Exception as e:
        return str(e)
    



app = Flask(
    __name__, 
    template_folder=os.path.abspath('templates'), 
    static_folder=os.path.abspath('static')
)
CORS(app)

# 설정
UPLOAD_FOLDER = os.path.abspath("data/input")
OUTPUT_FOLDER = os.path.abspath("data/output")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER

# 업로드 폴더가 존재하지 않으면 생성
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 서버 메모리에 캡션 및 파일 관리
stored_captions = {}  # file_id -> caption
latest_file_id = None  # 가장 최근 업로드된 파일의 file_id

@app.route("/")
def index():
    """메인 페이지"""
    return render_template("index.html")


@app.route("/static/<path:path>")
def serve_static(path):
    """정적 파일 제공"""
    return send_from_directory("static", path)


@app.route("/upload", methods=["POST"])
def upload_file():
    """파일 업로드 처리"""
    if "audio-file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["audio-file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not file.filename.endswith(".wav"):
        return jsonify({"error": "Invalid file type. Only .wav files are allowed."}), 400

    # 파일 ID 생성 (UUID 사용)
    file_id = str(uuid.uuid4())  # 고유한 file_id 생성
    filename = file_id + ".wav"  # file_id를 파일 이름으로 사용
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    file.save(save_path)

    # 최신 file_id 업데이트
    global latest_file_id
    latest_file_id = file_id

    # 파일 경로 저장
    stored_captions[file_id] = "No caption generated yet."  # 초기 캡션 설정

    return jsonify({"file_id": file_id, "file_url": f"/data/input/{filename}"})

@app.route("/analyze-music", methods=["POST"])
def analyze_music():
    """음악 분석 처리"""
    if latest_file_id is None:
        return jsonify({"error": "No file uploaded yet."}), 400

    # 가장 최근 파일 ID 사용
    file_id = latest_file_id
    filename = file_id + ".wav"
    
    # 입력된 음악 파일 경로 받아오기
    music_file = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    
    # 예시 캡션 생성 (여기서는 고정된 결과를 반환)
    caption = music_to_caption(music_file)

    # 캡션 저장
    # stored_captions[file_id] = caption
    print(f"Caption for {file_id} saved: {caption}")

    # 결과 반환
    result = {
        "caption": caption
    }
    return jsonify(result)

@app.route("/generate-music", methods=["POST"])
def generate_music():
    """텍스트 및 이전 캡션을 기반으로 새로운 음악 캡션 생성"""
    if latest_file_id is None:
        return jsonify({"error": "No file uploaded yet."}), 400

    # 가장 최근 파일 ID 사용
    file_id = latest_file_id

    # 입력 데이터 검증
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "Invalid input. 'text' is required."}), 400

    text = data["text"]
    previous_caption = stored_captions[file_id]
    print(f"Previous caption for {file_id}: {previous_caption}")

    # 새로운 캡션 생성
    new_caption = generate_new_caption(text) 

    # 새로운 캡션 저장
    print(f"New caption for {file_id}: {new_caption}")

    # 결과 반환
    result = {
        "new_caption": new_caption
    }
    return jsonify(result)

    
@app.route("/final-music", methods=["POST"])
def final_music():
    """새로운 캡션을 기반으로 음악 생성"""
    if latest_file_id is None:
        return jsonify({"error": "No file uploaded yet."}), 400

    # 가장 최근 파일 ID 사용
    file_id = latest_file_id
    new_caption = stored_captions[file_id]
    
    print(f"Generating music for caption: {new_caption}")

    # 음악 생성 로직 (예시로 생성된 캡션을 바탕으로 음악을 생성하는 로직 추가)
    generate_music_based_on_caption()
    
    generated_music_file = os.path.join("data/output",f"{file_id}.wav") 
    print(generated_music_file)
    # 파일이 없으면 에러 반환
    if not os.path.exists(generated_music_file):
        return jsonify({"error": "Generated music not found."}), 404

    # 성공 응답 반환
    return jsonify({
        "file_url": generated_music_file,
        "used_caption": new_caption
    })

@app.route("/data/input/<filename>")
def serve_input_file(filename):
    """업로드된 입력 파일 제공"""
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/data/output/<filename>")
def serve_output_file(filename):
    """생성된 출력 파일 제공"""
    return send_from_directory(app.config["OUTPUT_FOLDER"], filename)


if __name__ == "__main__":
    app.run(debug=True)
