# team.xlsx 파일 형식

## 개요
`team.xlsx` 파일은 서버 시작 시 팀/멤버 데이터를 초기화(seed)하는 데 사용됩니다.

## 필수 컬럼

| 컬럼명 | 타입 | 필수 여부 | 설명 |
|--------|------|-----------|------|
| room   | 문자열 | 필수 | 카카오톡 방 이름 |
| member | 문자열 | 필수 | 멤버 이름 |
| team   | 문자열 | 선택 | 팀 이름 (비어있으면 팀 없는 멤버) |

## 예시

### Excel 형식

| room | member | team |
|------|--------|------|
| NBC  | 홍길동 | 1팀  |
| NBC  | 김철수 | 1팀  |
| NBC  | 이영희 | 2팀  |
| NBC  | 박민수 |      |

### CSV 형식
```csv
room,member,team
NBC,홍길동,1팀
NBC,김철수,1팀
NBC,이영희,2팀
NBC,박민수,
```

## 사용 방법

### 1. 로컬 개발 환경

```bash
# .env 파일 생성 또는 수정
# ENABLE_SEED=True
# SEED_FILE_PATH=team.xlsx

# 또는 환경 변수로 직접 설정
export ENABLE_SEED=True
export SEED_FILE_PATH=team.xlsx

# 서버 실행 (자동으로 seed 실행됨)
python app.py
```

### 2. Railway 배포 환경

#### 방법 1: Railway CLI 사용 (추천)

```bash
# Railway CLI 설치
npm install -g @railway/cli

# Railway 로그인
railway login

# 프로젝트 연결
railway link

# team.xlsx 파일 업로드 (Volume에 저장)
railway run upload team.xlsx

# 또는 환경 변수 설정
railway variables set SEED_ON_START=true
```

#### 방법 2: Railway Volume 사용

1. Railway 대시보드 → 프로젝트 선택
2. "Settings" → "Volumes" → "New Volume" 클릭
3. Volume 마운트 경로 설정: `/app/data`
4. Volume에 team.xlsx 파일 업로드
5. Procfile 수정:
   ```
   web: python app.py --seed --seed-file /app/data/team.xlsx
   ```

#### 방법 3: Base64 인코딩 (작은 파일의 경우)

```bash
# 로컬에서 파일을 Base64로 인코딩
base64 team.xlsx > team_base64.txt

# Railway 환경 변수에 추가
TEAM_DATA_BASE64="<base64 인코딩된 내용>"
```

그 후 서버 시작 시 디코딩:
```python
# app.py에 추가
import base64
import os

if os.environ.get('TEAM_DATA_BASE64'):
    with open('team.xlsx', 'wb') as f:
        f.write(base64.b64decode(os.environ.get('TEAM_DATA_BASE64')))
```

## 주의사항

1. **개인정보 보호**
   - `team.xlsx` 파일은 `.gitignore`에 등록되어 있습니다
   - Git에 절대 커밋하지 마세요

2. **컬럼명 정확히 입력**
   - 컬럼명은 대소문자를 구분하지 않습니다
   - 하지만 `room`, `member`, `team`으로 정확히 입력하는 것을 권장합니다

3. **빈 값 처리**
   - `room`, `member`는 비어있으면 해당 행을 무시합니다
   - `team`은 비어있어도 됩니다 (팀 없는 멤버로 등록됨)

4. **중복 데이터**
   - 같은 멤버가 여러 번 나오면 마지막 값으로 덮어씌워집니다
   - 한 멤버는 하나의 팀에만 속할 수 있습니다

## 문제 해결

### "파일을 찾을 수 없습니다" 오류
- `team.xlsx` 파일이 `app.py`와 같은 디렉토리에 있는지 확인
- 또는 `--seed-file` 옵션으로 절대 경로 지정

### "필수 컬럼이 없습니다" 오류
- Excel 파일의 첫 번째 행에 `room`, `member`, `team` 컬럼이 있는지 확인
- 컬럼명의 공백이나 오타 확인

### "CacheManager가 초기화되지 않았습니다" 오류
- Redis와 MongoDB가 실행 중인지 확인
- 환경 변수 `REDIS_URL`, `MONGO_URI` 확인
