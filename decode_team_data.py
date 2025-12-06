"""
환경 변수에서 Base64로 인코딩된 team.xlsx 파일을 디코딩하는 스크립트

사용법:
1. 로컬에서 team.xlsx를 Base64로 인코딩
2. Railway 환경 변수에 TEAM_DATA_BASE64로 설정
3. 서버 시작 시 이 스크립트가 자동으로 디코딩
"""

import os
import base64
import sys

def decode_team_data():
    """환경 변수에서 Base64 데이터를 디코딩하여 team.xlsx 파일로 저장"""

    team_data_base64 = os.environ.get('TEAM_DATA_BASE64')

    if not team_data_base64:
        print("[DECODE] TEAM_DATA_BASE64 environment variable not found")
        print("[DECODE] Skipping decode process")
        return 0

    output_path = os.environ.get('SEED_FILE_PATH', 'team.xlsx')

    try:
        print(f"[DECODE] Decoding Base64 data to: {output_path}")

        # Base64 디코딩
        decoded_data = base64.b64decode(team_data_base64)

        # 파일로 저장
        with open(output_path, 'wb') as f:
            f.write(decoded_data)

        file_size = len(decoded_data)
        print(f"[DECODE SUCCESS] File created: {output_path} ({file_size} bytes)")
        return 0

    except Exception as e:
        print(f"[DECODE ERROR] Failed to decode: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(decode_team_data())
