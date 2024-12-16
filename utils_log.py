import os
import json
from datetime import datetime
from typing import Any, List, Optional


def write_log(rid: str, step: str, input_data: Any, log_dir: str = "/root/musicai/.log"):
    """
    범용적인 로그 데이터를 JSON 파일에 저장합니다.

    Parameters:
        rid (str): 요청 ID (로그 파일을 구분하는 키).
        input_data (Any): 저장할 로그 데이터 (문자열, 딕셔너리, 리스트 등).
        log_dir (str): 로그 파일 디렉토리 (기본값: "/root/musicai/.log").
    """
    # 로그 파일 경로
    log_file_path = f"{log_dir}/rid_{rid}.json"

    # 디렉토리 존재 여부 확인 및 생성
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 현재 시간 가져오기
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 새로운 로그 항목 생성
    log_entry = {
        f"{step}":{
            "timestamp": current_time,
            "data": input_data
        }
    }

    # 기존 로그 파일 읽기 (없으면 새로 생성)
    logs = []
    if os.path.exists(log_file_path):
        try:
            with open(log_file_path, "r") as log_file:
                logs = json.load(log_file)
        except json.JSONDecodeError:
            print(f"Corrupted log file for rid {rid}. Starting fresh.")

    # 새로운 로그 추가
    logs.append(log_entry)

    # 로그 파일 저장
    try:
        with open(log_file_path, "w") as log_file:
            json.dump(logs, log_file, indent=4)
        print(f"Log written to {log_file_path} for rid {rid}.")
    except Exception as e:
        print(f"Failed to write log for rid {rid}: {e}")

def read_log(rid: str, step:str, log_dir: str = "/root/musicai/.log") -> Optional[List[dict]]:
    """
    요청 ID(rid)별로 저장된 JSON 로그 파일을 읽어옵니다.

    Parameters:
        rid (str): 요청 ID (로그 파일 이름에 사용).
        log_dir (str): 로그 파일 디렉토리 (기본값: "/root/musicai/.log").

    Returns:
        Optional[List[dict]]: 로그 데이터 리스트. 파일이 없거나 오류가 발생하면 None.
    """
    # 로그 파일 경로
    log_file_path = f"{log_dir}/rid_{rid}.json"

    # 파일 존재 여부 확인
    if not os.path.exists(log_file_path):
        print(f"Log file for rid {rid} does not exist in {log_dir}.")
        return None

    # 파일 읽기
    try:
        with open(log_file_path, "r") as log_file:
            logs = json.load(log_file)
            print(f"Log file for rid {rid} successfully read.")
            
            # 모든 `data` 필드를 리스트로 추출
            data_list = [log["data"] for log in logs[step] if "data" in log]
            return data_list
    except json.JSONDecodeError:
        print(f"Failed to decode JSON in log file for rid {rid}.")
        return None
    except Exception as e:
        print(f"Error reading log file for rid {rid}: {e}")
        return None