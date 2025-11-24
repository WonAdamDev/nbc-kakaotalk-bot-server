# 카카오톡 봇 백엔드 서버

메신저 R로 만든 카카오톡 봇의 백엔드 서버입니다.
카카오톡 봇이 파싱한 명령어를 받아 처리하고 응답을 반환합니다.

## 프로젝트 구조

```
nbc-kakaotalk-bot-backend/
├── app/
│   ├── __init__.py          # Flask 앱 초기화
│   └── routes/
│       ├── __init__.py
│       └── commands.py      # 명령어 처리 라우트
├── app.py                   # 앱 실행 파일
├── config.py                # 설정 파일
├── requirements.txt         # Python 패키지 의존성
├── Procfile                 # Railway 배포 설정
├── .env.example             # 환경 변수 예시
├── .gitignore
└── README.md
```

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

## API 엔드포인트

### Health Check
- **GET** `/health`
- 서버 상태 확인

### 명령어 처리

#### Test 명령어
- **POST** `/api/commands/test`
- Body:
  ```json
  {
    "user": "사용자명",
    "room": "방이름"
  }
  ```

#### Echo 명령어
- **POST** `/api/commands/echo`
- Body:
  ```json
  {
    "message": "반복할 메시지"
  }
  ```

## 카카오톡 봇과 연동

카카오톡 봇(메신저 R)에서 다음과 같이 요청을 보내세요:

1. 사용자가 `!test` 입력
2. 봇이 명령어 파싱
3. `POST http://your-server:5000/api/commands/test`로 요청 전송
4. 백엔드에서 처리 후 응답 반환
5. 봇이 응답을 카카오톡 방에 출력

## 새로운 명령어 추가하기

`app/routes/commands.py`에 새로운 라우트를 추가하세요:

```python
@bp.route('/your-command', methods=['POST'])
def your_command():
    data = request.get_json()
    # 처리 로직
    return jsonify({
        'success': True,
        'response': '응답 메시지'
    }), 200
```

## Railway 프로덕션 배포

### 1. 배포 구성 확인

프로젝트에 이미 Railway 배포에 필요한 파일들이 포함되어 있습니다:

**Procfile** (Railway 시작 명령어):
```
web: gunicorn -w 4 -b 0.0.0.0:$PORT "app:create_app()"
```

**requirements.txt** (Gunicorn 포함):
```txt
Flask==3.0.0
Flask-CORS==4.0.0
python-dotenv==1.0.0
requests==2.31.0
gunicorn==21.2.0
```

### 2. GitHub에 Push

```bash
git add .
git commit -m "Initial commit"
git push origin master
```

### 3. Railway 설정

1. [Railway](https://railway.app/) 로그인
2. "New Project" → "Deploy from GitHub repo"
3. 저장소 선택

### 4. 환경 변수 설정 (Railway 대시보드)

```env
SECRET_KEY=your-random-production-secret-key-here
DEBUG=False
HOST=0.0.0.0
PORT=5000
```

**중요**:
- `SECRET_KEY`는 랜덤한 긴 문자열 사용
- `DEBUG=False` (프로덕션에서는 필수)
- Railway가 자동으로 HTTPS 제공

### 5. 배포 완료

Railway가 자동으로 빌드 및 배포합니다. 배포 후:

```bash
# Health check 테스트
curl https://your-app.railway.app/health
```

### 6. 도메인 연결 (선택)

Railway 대시보드에서 커스텀 도메인 연결 가능:
- Settings → Domains → Add Custom Domain

## 보안 주의사항

- **절대 Git에 커밋하지 마세요** (`.gitignore`에 추가됨):
  - `.env` 파일
  - API 키, 비밀번호 등 민감한 정보

- **프로덕션 환경 (Railway)**:
  - `SECRET_KEY`는 랜덤한 긴 문자열 사용
  - `DEBUG=False` 설정 필수
  - Railway 환경 변수에서 설정 관리
  - Railway가 자동으로 HTTPS 제공
