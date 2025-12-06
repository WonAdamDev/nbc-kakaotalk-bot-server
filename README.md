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

### 4. 팀 데이터 Seed (선택사항)

팀/멤버 데이터를 Excel 파일에서 읽어 초기 DB를 세팅할 수 있습니다.

#### 4.1. team.xlsx 파일 준비

Excel 파일 형식:
| room | member | team |
|------|--------|------|
| NBC  | 홍길동 | 1팀  |
| NBC  | 김철수 | 1팀  |
| NBC  | 이영희 | 2팀  |
| NBC  | 박민수 |      |

자세한 형식은 `TEAM_XLSX_FORMAT.md` 참고

#### 4.2. Seed 활성화

`.env` 파일에서 설정:
```bash
ENABLE_SEED=True
SEED_FILE_PATH=team.xlsx
```

또는 환경 변수로 직접 설정:
```bash
# Windows (PowerShell)
$env:ENABLE_SEED="True"

# Linux/Mac
export ENABLE_SEED=True
```

### 5. 서버 실행

```bash
# 서버 실행 (ENABLE_SEED 환경 변수에 따라 자동으로 seed 실행)
python app.py
```

서버는 기본적으로 `http://localhost:5000`에서 실행됩니다.

## Railway 배포

Railway에 배포할 때 팀 데이터를 안전하게 업로드하는 방법은 `RAILWAY_DEPLOYMENT.md` 문서를 참고하세요.

주요 방법:
- **Railway Volume**: 파일을 Volume에 저장 (추천)
- **환경 변수**: Base64 인코딩하여 환경 변수로 설정 (작은 파일)

자세한 내용: [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md)

## 파일 구조

```
nbc-kakaotalk-bot-server/
├── app/
│   ├── __init__.py              # Flask 앱 초기화
│   ├── cache_manager.py         # Redis/MongoDB 캐시 관리
│   ├── seed.py                  # DB Seeding 로직
│   └── routes/
│       ├── commands.py          # 기본 명령어 라우트
│       ├── member/              # 멤버 관련 라우트
│       ├── team/                # 팀 관련 라우트
│       └── member_team/         # 멤버-팀 연결 라우트
├── app.py                       # 서버 실행 파일
├── config.py                    # 환경 설정
├── seed_script.py               # Railway용 seed 스크립트
├── decode_team_data.py          # Base64 디코딩 스크립트
├── requirements.txt             # Python 의존성
├── Procfile                     # Railway 배포 설정
├── .env.example                 # 환경 변수 예시
├── TEAM_XLSX_FORMAT.md          # team.xlsx 형식 가이드
└── RAILWAY_DEPLOYMENT.md        # Railway 배포 가이드
```

## 보안 주의사항

- `team.xlsx` 파일은 개인정보를 포함하므로 `.gitignore`에 등록되어 있습니다
- Git에 절대 커밋하지 마세요
- Railway 배포 시 Volume 또는 환경 변수를 사용하세요

