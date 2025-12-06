"""
team.xlsx를 Base64로 인코딩하여 Railway 환경 변수에 설정할 수 있게 합니다.
"""

import base64
import os

def encode_file():
    """team.xlsx를 Base64로 인코딩"""
    input_file = 'team.xlsx'
    output_file = 'team_base64.txt'

    if not os.path.exists(input_file):
        print(f"[ERROR] {input_file} not found")
        print("Please make sure team.xlsx is in the current directory")
        return

    try:
        # 파일 읽기
        with open(input_file, 'rb') as f:
            file_data = f.read()

        file_size = len(file_data)
        print(f"\n{'='*60}")
        print("Encode team.xlsx to Base64")
        print(f"{'='*60}")
        print(f"Input file: {input_file}")
        print(f"File size: {file_size:,} bytes ({file_size/1024:.2f} KB)")

        # Base64 인코딩
        encoded_data = base64.b64encode(file_data).decode('utf-8')
        encoded_size = len(encoded_data)

        print(f"\nEncoded size: {encoded_size:,} characters ({encoded_size/1024:.2f} KB)")
        print(f"Size increase: {(encoded_size/file_size - 1)*100:.1f}%")

        # 환경 변수 크기 제한 경고
        if encoded_size > 100000:  # 100KB
            print(f"\n⚠️  WARNING: Encoded size is large ({encoded_size/1024:.2f} KB)")
            print("   Some platforms have environment variable size limits")
            print("   Consider using Railway Volume upload method instead")

        # 파일로 저장
        with open(output_file, 'w') as f:
            f.write(encoded_data)

        print(f"\n[SUCCESS] ✓ Base64 encoded data saved to: {output_file}")
        print(f"\nNext steps:")
        print(f"1. Copy the contents of {output_file}")
        print(f"2. Go to Railway Dashboard → Your Project → Variables")
        print(f"3. Add new variable:")
        print(f"   Key: TEAM_DATA_BASE64")
        print(f"   Value: <paste the Base64 string>")
        print(f"4. Deploy your service")
        print(f"\nThe service will automatically decode and save to /data/team.xlsx")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"[ERROR] Encoding failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    encode_file()
