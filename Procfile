# 기본 설정 (Seed 없이 서버만 실행)
# web: gunicorn -w 4 -b 0.0.0.0:$PORT "app:create_app()"

# Seed 포함 설정 (team.xlsx 파일이 있을 때)
# web: python seed_script.py && gunicorn -w 4 -b 0.0.0.0:$PORT "app:create_app()"

# Base64 디코딩 + Seed 포함 설정 (환경 변수 TEAM_DATA_BASE64 사용)
# web: python decode_team_data.py && python seed_script.py && gunicorn -w 4 -b 0.0.0.0:$PORT "app:create_app()"

# 현재 사용 중인 설정 (기본)
web: gunicorn -w 4 -b 0.0.0.0:$PORT "app:create_app()"
