# 카카오톡 봇 백엔드 서버

메신저 R로 만든 카카오톡 봇의 백엔드 서버입니다.
카카오톡 봇이 파싱한 명령어를 받아 처리하고 응답을 반환합니다.

## 프로젝트 구조

```
nbc-kakaotalk-bot-backend/
├── app/
│   ├── __init__.py          # Flask 앱 초기화
│   ├── routes/
│   │   ├── __init__.py
│   │   └── commands.py      # 명령어 처리 라우트
│   ├── services/            # 비즈니스 로직
│   │   └── __init__.py
│   └── models/              # 데이터 모델 (필요시)
├── app.py                   # 앱 실행 파일
├── config.py                # 설정 파일
├── requirements.txt         # Python 패키지 의존성
├── .env.example             # 환경 변수 예시
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

### 3. 환경 변수 설정

`.env.example` 파일을 `.env`로 복사하고 필요한 값을 설정하세요.

```bash
cp .env.example .env
```

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
