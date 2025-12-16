#!/usr/bin/env python3
"""
Password Hash Generator for HR Dashboard
HR 대시보드용 비밀번호 해시 생성기

This script generates a SHA-256 hash for a given password.
Use the output to update the PASSWORD_HASH in docs/auth.html.
이 스크립트는 주어진 비밀번호의 SHA-256 해시를 생성합니다.
출력값을 docs/auth.html의 PASSWORD_HASH에 업데이트하세요.

Usage / 사용법:
    python scripts/update_password.py
    python scripts/update_password.py --password "your_new_password"
"""

import hashlib
import getpass
import argparse
import re
from pathlib import Path


def generate_hash(password: str) -> str:
    """
    Generate SHA-256 hash of the password
    비밀번호의 SHA-256 해시 생성

    Args:
        password: Plain text password / 평문 비밀번호

    Returns:
        str: SHA-256 hash in hexadecimal / 16진수 SHA-256 해시
    """
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def update_auth_file(new_hash: str, auth_file_path: str = None) -> bool:
    """
    Update the PASSWORD_HASH in auth.html
    auth.html의 PASSWORD_HASH 업데이트

    Args:
        new_hash: New SHA-256 hash / 새 SHA-256 해시
        auth_file_path: Path to auth.html (optional) / auth.html 경로 (선택)

    Returns:
        bool: True if successful / 성공 시 True
    """
    if auth_file_path is None:
        auth_file_path = Path(__file__).parent.parent / "docs" / "auth.html"
    else:
        auth_file_path = Path(auth_file_path)

    if not auth_file_path.exists():
        print(f"❌ Auth file not found: {auth_file_path}")
        print(f"❌ 인증 파일을 찾을 수 없습니다: {auth_file_path}")
        return False

    try:
        with open(auth_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find and replace the PASSWORD_HASH value
        # PASSWORD_HASH 값을 찾아서 교체
        pattern = r"PASSWORD_HASH:\s*'[a-f0-9]{64}'"
        replacement = f"PASSWORD_HASH: '{new_hash}'"

        if not re.search(pattern, content):
            print("❌ PASSWORD_HASH pattern not found in auth.html")
            print("❌ auth.html에서 PASSWORD_HASH 패턴을 찾을 수 없습니다")
            return False

        new_content = re.sub(pattern, replacement, content)

        with open(auth_file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"✅ Password hash updated in: {auth_file_path}")
        print(f"✅ 비밀번호 해시가 업데이트됨: {auth_file_path}")
        return True

    except Exception as e:
        print(f"❌ Error updating auth file: {e}")
        print(f"❌ 인증 파일 업데이트 에러: {e}")
        return False


def main():
    """
    Main entry point
    메인 진입점
    """
    parser = argparse.ArgumentParser(
        description="Generate SHA-256 password hash for HR Dashboard / HR 대시보드용 SHA-256 비밀번호 해시 생성"
    )
    parser.add_argument(
        '--password', '-p',
        type=str,
        help='Password to hash (if not provided, will prompt) / 해시할 비밀번호 (미지정시 프롬프트)'
    )
    parser.add_argument(
        '--update', '-u',
        action='store_true',
        help='Update auth.html with the new hash / auth.html을 새 해시로 업데이트'
    )
    parser.add_argument(
        '--auth-file',
        type=str,
        help='Path to auth.html file / auth.html 파일 경로'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("HR Dashboard Password Hash Generator")
    print("HR 대시보드 비밀번호 해시 생성기")
    print("=" * 60)
    print()

    # Get password
    # 비밀번호 가져오기
    if args.password:
        password = args.password
    else:
        password = getpass.getpass("Enter new password / 새 비밀번호 입력: ")
        confirm = getpass.getpass("Confirm password / 비밀번호 확인: ")

        if password != confirm:
            print()
            print("❌ Passwords do not match!")
            print("❌ 비밀번호가 일치하지 않습니다!")
            return 1

    if len(password) < 6:
        print()
        print("⚠️  Warning: Password is less than 6 characters")
        print("⚠️  경고: 비밀번호가 6자 미만입니다")
        print()

    # Generate hash
    # 해시 생성
    password_hash = generate_hash(password)

    print()
    print("Generated SHA-256 Hash / 생성된 SHA-256 해시:")
    print("-" * 60)
    print(password_hash)
    print("-" * 60)
    print()

    # Update auth.html if requested
    # 요청 시 auth.html 업데이트
    if args.update:
        success = update_auth_file(password_hash, args.auth_file)
        if not success:
            return 1
    else:
        print("💡 To update auth.html automatically, run with --update flag")
        print("💡 auth.html을 자동으로 업데이트하려면 --update 플래그로 실행하세요")
        print()
        print("   python scripts/update_password.py --update")
        print()
        print("Or manually update PASSWORD_HASH in docs/auth.html:")
        print("또는 docs/auth.html의 PASSWORD_HASH를 수동으로 업데이트하세요:")
        print()
        print(f"   PASSWORD_HASH: '{password_hash}'")

    print()
    print("=" * 60)
    return 0


if __name__ == '__main__':
    exit(main())
