"""
환경 변수에서 Base64 데이터를 디코딩하여 Volume에 저장합니다.
Railway 배포 시 자동으로 실행됩니다.
"""

import os
import base64
import sys

def decode_and_save_to_volume():
    """환경 변수에서 Base64 데이터를 읽어 /data/team.xlsx로 저장"""

    # 환경 변수에서 Base64 데이터 읽기
    team_data_base64 = os.environ.get('TEAM_DATA_BASE64')

    # Volume 경로
    volume_path = '/data'
    dest_file = os.path.join(volume_path, 'team.xlsx')

    print(f"\n{'='*60}")
    print("Upload team.xlsx to Volume from Base64")
    print(f"{'='*60}")

    # 환경 변수 확인
    if not team_data_base64:
        print("[INFO] TEAM_DATA_BASE64 environment variable not found")
        print("[INFO] Checking if file already exists in volume...")

        if os.path.exists(dest_file):
            file_size = os.path.getsize(dest_file)
            print(f"[OK] File already exists in volume: {dest_file} ({file_size} bytes)")
            return 0
        else:
            print("[WARNING] No Base64 data and no existing file in volume")
            print("[INFO] Server will start without team.xlsx")
            print("[INFO] Seeding will be skipped")
            return 0

    try:
        # Base64 데이터 크기
        encoded_size = len(team_data_base64)
        print(f"[INFO] Base64 data size: {encoded_size:,} characters ({encoded_size/1024:.2f} KB)")

        # Volume 디렉토리 생성
        os.makedirs(volume_path, exist_ok=True)
        print(f"[OK] Volume directory ready: {volume_path}")

        # Base64 디코딩
        print(f"\n[DECODE] Decoding Base64 data...")
        decoded_data = base64.b64decode(team_data_base64)
        decoded_size = len(decoded_data)
        print(f"[OK] Decoded size: {decoded_size:,} bytes ({decoded_size/1024:.2f} KB)")

        # 파일로 저장
        print(f"\n[SAVE] Saving to {dest_file}...")
        with open(dest_file, 'wb') as f:
            f.write(decoded_data)

        # 검증
        if os.path.exists(dest_file):
            saved_size = os.path.getsize(dest_file)
            print(f"[SUCCESS] ✓ File saved to Volume!")
            print(f"[INFO] File path: {dest_file}")
            print(f"[INFO] File size: {saved_size:,} bytes ({saved_size/1024:.2f} KB)")

            # 크기 검증
            if saved_size == decoded_size:
                print(f"[OK] Size verified!")
            else:
                print(f"[WARNING] Size mismatch! Expected: {decoded_size}, Got: {saved_size}")

            # Volume 내용 확인
            print(f"\n[INFO] Volume contents:")
            for item in os.listdir(volume_path):
                item_path = os.path.join(volume_path, item)
                if os.path.isfile(item_path):
                    item_size = os.path.getsize(item_path)
                    print(f"  - {item} ({item_size:,} bytes)")
                else:
                    print(f"  - {item}/ (directory)")

            return 0
        else:
            print(f"[ERROR] File save verification failed")
            return 1

    except Exception as e:
        print(f"[ERROR] Decode and save failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit_code = decode_and_save_to_volume()
    print(f"\n{'='*60}")
    print(f"Upload script finished with exit code: {exit_code}")
    print(f"{'='*60}\n")
    sys.exit(exit_code)
