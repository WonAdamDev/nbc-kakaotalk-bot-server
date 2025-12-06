# Railway 배포 가이드 - team.xlsx 파일 업로드

## 개요
Railway에 배포할 때 `team.xlsx` 파일을 안전하게 업로드하는 방법을 설명합니다.

## 방법 비교

| 방법 | 난이도 | 보안성 | 파일 크기 제한 | 추천 |
|------|--------|--------|----------------|------|
| Railway Volume | 중 | 높음 | 없음 | ⭐⭐⭐ 가장 추천 |
| 환경 변수 (Base64) | 하 | 높음 | ~100KB | 작은 파일만 |
| Private Repository | 하 | 중 | 없음 | 비추천 |

## 방법 1: Railway Volume 사용 (추천)

### 장점
- 파일 크기 제한 없음
- Git에 커밋하지 않아도 됨
- 파일 수정이 쉬움
- 가장 안전한 방법

### 단계

#### 1. Railway에서 Volume 생성

1. Railway 대시보드 접속: https://railway.app/dashboard
2. 프로젝트 선택
3. 서비스 선택 (Flask 서버)
4. "Variables" 탭 → "Volumes" 섹션
5. "New Volume" 클릭
6. Volume 설정:
   - Mount Path: `/data`
   - 생성 클릭

#### 2. Volume에 파일 업로드

현재 Railway는 대시보드에서 직접 파일 업로드를 지원하지 않습니다.
대신 다음 방법들을 사용할 수 있습니다:

**방법 A: 임시 배포 스크립트 사용**

1. 프로젝트에 임시 업로드 스크립트 추가:

```python
# upload_to_volume.py
import os
import shutil

if __name__ == '__main__':
    # 로컬 team.xlsx를 Volume으로 복사
    source = 'team.xlsx'
    dest = '/data/team.xlsx'

    if os.path.exists(source):
        os.makedirs('/data', exist_ok=True)
        shutil.copy2(source, dest)
        print(f"[SUCCESS] {source} → {dest}")
    else:
        print(f"[ERROR] {source} not found")
```

2. Procfile 임시 수정:
```
web: python upload_to_volume.py && gunicorn -w 4 -b 0.0.0.0:$PORT "app:create_app()"
```

3. team.xlsx를 Git에 임시로 커밋 (주의: 배포 후 즉시 제거)
4. Railway에 배포
5. 배포 완료 후 team.xlsx를 Git에서 제거하고 Procfile 원복

**방법 B: SSH 접속 후 수동 업로드 (Railway Pro 필요)**

Railway Pro 플랜에서는 SSH 접속이 가능합니다.

#### 3. Seed 실행 설정

**옵션 A: 서버 시작 시 자동 Seed**

환경 변수 설정:
```
SEED_ON_START=true
SEED_FILE_PATH=/data/team.xlsx
```

`app.py` 수정:
```python
import os

if __name__ == '__main__':
    # ... 기존 코드 ...

    # 환경 변수로 자동 seed 설정
    if os.environ.get('SEED_ON_START') == 'true':
        args.seed = True
        seed_file = os.environ.get('SEED_FILE_PATH', 'team.xlsx')
        args.seed_file = seed_file
```

Procfile:
```
web: python app.py && gunicorn -w 4 -b 0.0.0.0:$PORT "app:create_app()"
```

**옵션 B: 별도 Seed 스크립트**

`seed_script.py` 생성:
```python
from app import create_app, cache_manager
from app.seed import seed_from_excel
import os

app = create_app()

with app.app_context():
    excel_path = os.environ.get('SEED_FILE_PATH', '/data/team.xlsx')
    print(f"[SEED] Starting seed with: {excel_path}")
    result = seed_from_excel(cache_manager, excel_path)

    if result['success']:
        print(f"[SEED SUCCESS] {result['message']}")
    else:
        print(f"[SEED FAILED] {result['message']}")
        exit(1)
```

Procfile:
```
web: python seed_script.py; gunicorn -w 4 -b 0.0.0.0:$PORT "app:create_app()"
```

## 방법 2: 환경 변수로 Base64 인코딩 (작은 파일만)

### 장점
- 설정이 간단
- Railway 대시보드에서 바로 설정 가능

### 단점
- 파일 크기 제한 (~100KB)
- Base64 인코딩으로 크기가 약 33% 증가
- 환경 변수 크기 제한

### 단계

#### 1. 로컬에서 파일 인코딩

**Windows (PowerShell):**
```powershell
$bytes = [System.IO.File]::ReadAllBytes("team.xlsx")
$base64 = [System.Convert]::ToBase64String($bytes)
$base64 | Out-File -FilePath team_base64.txt
```

**Windows (Git Bash):**
```bash
base64 team.xlsx > team_base64.txt
```

**Linux/Mac:**
```bash
base64 team.xlsx > team_base64.txt
```

#### 2. Railway 환경 변수 설정

1. Railway 대시보드 → 프로젝트 → "Variables"
2. "New Variable" 클릭
3. 변수 추가:
   - Key: `TEAM_DATA_BASE64`
   - Value: `team_base64.txt` 파일 내용 복사/붙여넣기

#### 3. 서버 시작 시 디코딩

`app.py` 수정:
```python
import base64
import os

# Flask 앱 생성 전에 실행
if os.environ.get('TEAM_DATA_BASE64'):
    print("[SEED] Decoding team.xlsx from environment variable...")
    try:
        with open('team.xlsx', 'wb') as f:
            f.write(base64.b64decode(os.environ.get('TEAM_DATA_BASE64')))
        print("[SEED] team.xlsx decoded successfully")
    except Exception as e:
        print(f"[SEED ERROR] Failed to decode: {e}")

app = create_app()

# Seed 실행
if os.path.exists('team.xlsx') and args.seed:
    run_seed('team.xlsx')
```

## 방법 3: Private Git Repository (비추천)

### 경고
- 개인정보가 Git 히스토리에 영구히 남습니다
- 실수로 Public으로 전환 시 정보 유출 위험
- **절대 추천하지 않습니다**

만약 정말 사용해야 한다면:
1. Repository를 Private으로 설정
2. `.gitignore`에서 `team.xlsx` 제거
3. 커밋 및 푸시
4. Railway에 배포
5. **배포 후 즉시 파일 제거 및 Git 히스토리 정리**

```bash
# Git 히스토리에서 파일 완전 제거
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch team.xlsx" \
  --prune-empty --tag-name-filter cat -- --all

git push origin --force --all
```

## 권장 워크플로우

### 초기 배포
1. Railway에서 Volume 생성 (`/data`)
2. 임시로 `team.xlsx`를 포함하여 배포 (업로드 스크립트 사용)
3. 파일이 Volume에 복사되면 Git에서 제거
4. Procfile을 seed 스크립트로 업데이트
5. 재배포

### 데이터 업데이트
1. 로컬에서 `team.xlsx` 수정
2. Base64 인코딩 또는 Volume 재업로드
3. Railway에서 서비스 재시작

## 문제 해결

### "파일을 찾을 수 없습니다" 오류
```bash
# Railway 로그에서 확인
railway logs

# Volume 마운트 확인
ls -la /data/
```

### Seed가 실행되지 않음
```bash
# 환경 변수 확인
echo $SEED_ON_START
echo $SEED_FILE_PATH

# Procfile 확인
cat Procfile
```

### Volume이 비어있음
- Volume은 서비스 재시작 후에도 유지됩니다
- 하지만 새 배포 시 초기화될 수 있습니다
- Seed 스크립트를 Procfile에 포함하여 매번 실행하도록 설정

## 보안 체크리스트

- [ ] `team.xlsx`가 `.gitignore`에 포함되어 있음
- [ ] Git 히스토리에 `team.xlsx`가 없음
- [ ] Private repository 사용 (또는 Volume 사용)
- [ ] Railway 환경 변수가 암호화됨
- [ ] 배포 후 로컬 개발자에게 파일 공유 방법 안내

## 추가 자료

- Railway Volume 문서: https://docs.railway.app/reference/volumes
- Railway CLI: https://docs.railway.app/develop/cli
- Flask 배포 가이드: https://flask.palletsprojects.com/en/3.0.x/deploying/
