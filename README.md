# 카카오톡 봇 백엔드 서버

메신저 R로 만든 카카오톡 봇의 백엔드 서버입니다.
카카오톡 봇이 파싱한 명령어를 받아 처리하고 응답을 반환합니다.

## 설치 및 실행

### 1. 가상환경 생성 및 활성화

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정 (선택)

로컬 개발은 기본값으로 동작합니다. 설정을 변경하려면 `.env` 파일을 생성하세요:

```bash
cp .env.example .env
```

**참고**: `.env` 파일이 없어도 기본값으로 정상 동작합니다.

### 4. 서버 실행

```bash
python app.py
```

서버는 기본적으로 `http://localhost:5000`에서 실행됩니다.

