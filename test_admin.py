"""
Admin API 테스트 스크립트
"""
import requests
import json

API_URL = "http://localhost:5000"

def test_login():
    """로그인 테스트"""
    print("\n=== 1. 로그인 테스트 ===")
    response = requests.post(
        f"{API_URL}/api/admin/login",
        json={"password": "admin123"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    if response.status_code == 200:
        return response.json().get('token')
    return None

def test_member_team_assign(token):
    """팀 배정 테스트"""
    print("\n=== 2. 팀 배정 테스트 ===")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    data = {
        "room": "test_room",
        "member": "test_member",
        "member_id": "MEM_TEST1234",
        "team": "test_team"
    }

    print(f"URL: {API_URL}/api/commands/member_team")
    print(f"Headers: {headers}")
    print(f"Data: {data}")

    try:
        response = requests.post(
            f"{API_URL}/api/commands/member_team",
            headers=headers,
            json=data,
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

def test_cors_preflight(token):
    """CORS preflight 테스트"""
    print("\n=== 3. CORS Preflight 테스트 ===")

    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type"
    }

    try:
        response = requests.options(
            f"{API_URL}/api/commands/member_team",
            headers=headers,
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Admin API 테스트 시작...")

    # 1. 로그인
    token = test_login()

    if not token:
        print("\n로그인 실패! 서버가 실행 중인지 확인하세요.")
        exit(1)

    print(f"\n토큰: {token[:50]}...")

    # 2. CORS preflight
    test_cors_preflight(token)

    # 3. 팀 배정
    test_member_team_assign(token)

    print("\n테스트 완료!")
