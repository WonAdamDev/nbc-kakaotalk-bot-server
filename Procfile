# 기본 설정 (Seed 없이 서버만 실행)
# web: gunicorn -w 4 -b 0.0.0.0:$PORT "app:create_app()"

# Base64 → Volume 업로드 + Seed + 서버 실행 (현재 사용 중)
# 1. upload_to_volume.py: 환경 변수에서 Base64 디코딩하여 /data/team.xlsx 저장
# 2. seed_script.py: /data/team.xlsx로 DB seed
# 3. gunicorn: 서버 시작
web: python upload_to_volume.py && python seed_script.py && gunicorn -w 4 -b 0.0.0.0:$PORT "app:create_app()"
