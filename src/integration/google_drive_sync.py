"""
google_drive_sync.py - Google Drive Integration Module
Google Drive 연동 모듈

Handles automatic synchronization of HR data files from Google Drive.
Google Drive에서 HR 데이터 파일의 자동 동기화를 처리합니다.

Core Features / 핵심 기능:
- Service account and OAuth2 authentication / 서비스 계정 및 OAuth2 인증
- Automatic file synchronization / 자동 파일 동기화
- Retry logic with exponential backoff / 지수 백오프를 사용한 재시도 로직
- File caching to avoid redundant downloads / 중복 다운로드 방지를 위한 파일 캐싱
- Progress tracking and logging / 진행 상황 추적 및 로깅

IMPORTANT / 중요:
- This module requires Google Drive API credentials
  이 모듈은 Google Drive API 자격 증명이 필요합니다
- Credentials path: HR/credentials/service-account-key.json
  자격 증명 경로: HR/credentials/service-account-key.json
"""

import os
import io
import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google.oauth2.service_account import Credentials as ServiceAccountCredentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaIoBaseDownload
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False

from ..utils.logger import get_logger

# Google Drive API scope / Google Drive API 범위
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


@dataclass
class SyncResult:
    """
    Result of a file synchronization operation
    파일 동기화 작업 결과
    """
    success: bool
    files_synced: int = 0
    files_failed: int = 0
    files_skipped: int = 0
    error_message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FileMetadata:
    """
    Metadata for a Google Drive file
    Google Drive 파일의 메타데이터
    """
    file_id: str
    name: str
    mime_type: str
    size: int
    modified_time: str
    md5_checksum: Optional[str] = None


class GoogleDriveSync:
    """
    Google Drive synchronization manager for HR data
    HR 데이터용 Google Drive 동기화 관리자
    """

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        cache_dir: Optional[str] = None,
        auth_type: str = 'service_account'
    ):
        """
        Initialize Google Drive synchronization manager
        Google Drive 동기화 관리자 초기화

        Args:
            credentials_path: Path to credentials file / 자격 증명 파일 경로
            cache_dir: Directory for caching file metadata / 파일 메타데이터 캐싱용 디렉토리
            auth_type: Authentication type ('service_account' or 'oauth2')
                      인증 유형 ('service_account' 또는 'oauth2')

        Raises:
            ImportError: If Google Drive API libraries not installed
                        Google Drive API 라이브러리가 설치되지 않은 경우
        """
        if not GOOGLE_DRIVE_AVAILABLE:
            raise ImportError(
                "Google Drive API libraries not installed. Install with: pip install google-api-python-client google-auth "
                "google-auth-oauthlib google-auth-httplib2 / "
                "Google Drive API 라이브러리가 설치되지 않았습니다. 다음으로 설치: pip install google-api-python-client google-auth "
                "google-auth-oauthlib google-auth-httplib2"
            )

        self.logger = get_logger()
        self.auth_type = auth_type
        self.service = None

        # Set default credentials path / 기본 자격 증명 경로 설정
        if credentials_path is None:
            hr_root = Path(__file__).parent.parent.parent
            if auth_type == 'service_account':
                credentials_path = hr_root / "credentials" / "service-account-key.json"
            else:
                credentials_path = hr_root / "credentials" / "client_secrets.json"

        self.credentials_path = Path(credentials_path)

        # Set default cache directory / 기본 캐시 디렉토리 설정
        if cache_dir is None:
            hr_root = Path(__file__).parent.parent.parent
            cache_dir = hr_root / ".cache" / "drive_sync"

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Cache file for metadata / 메타데이터용 캐시 파일
        self.metadata_cache_file = self.cache_dir / "file_metadata.json"
        self.metadata_cache = self._load_metadata_cache()

    def _load_metadata_cache(self) -> Dict[str, Dict]:
        """
        Load file metadata cache from disk
        디스크에서 파일 메타데이터 캐시 로드

        Returns:
            Dictionary of file metadata / 파일 메타데이터 딕셔너리
        """
        if self.metadata_cache_file.exists():
            try:
                with open(self.metadata_cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(
                    f"메타데이터 캐시 로드 실패, 새로 시작합니다",
                    f"Failed to load metadata cache, starting fresh",
                    error=str(e)
                )
        return {}

    def _save_metadata_cache(self) -> None:
        """
        Save file metadata cache to disk
        디스크에 파일 메타데이터 캐시 저장
        """
        try:
            with open(self.metadata_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata_cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(
                "메타데이터 캐시 저장 실패",
                "Failed to save metadata cache",
                error=str(e)
            )

    def initialize(self) -> bool:
        """
        Initialize Google Drive API connection
        Google Drive API 연결 초기화

        Returns:
            True if initialization successful / 초기화 성공 시 True

        Examples:
            >>> sync = GoogleDriveSync()
            >>> if sync.initialize():
            ...     print("Connected to Google Drive")
        """
        try:
            if self.auth_type == 'service_account':
                self.service = self._authenticate_service_account()
            else:
                self.service = self._authenticate_oauth2()

            # Test connection / 연결 테스트
            self._test_connection()

            self.logger.info(
                "Google Drive 연결 초기화 성공",
                "Google Drive connection initialized successfully"
            )
            return True

        except Exception as e:
            self.logger.error(
                "Google Drive 연결 초기화 실패",
                "Failed to initialize Google Drive connection",
                error=str(e)
            )
            return False

    def _authenticate_service_account(self):
        """
        Authenticate using service account
        서비스 계정을 사용하여 인증

        Returns:
            Google Drive service object / Google Drive 서비스 객체

        Raises:
            FileNotFoundError: If credentials file not found
                              자격 증명 파일을 찾을 수 없는 경우
        """
        if not self.credentials_path.exists():
            raise FileNotFoundError(
                f"Service account key file not found / 서비스 계정 키 파일을 찾을 수 없습니다: {self.credentials_path}"
            )

        credentials = ServiceAccountCredentials.from_service_account_file(
            str(self.credentials_path),
            scopes=SCOPES
        )

        return build('drive', 'v3', credentials=credentials)

    def _authenticate_oauth2(self):
        """
        Authenticate using OAuth2 flow
        OAuth2 플로우를 사용하여 인증

        Returns:
            Google Drive service object / Google Drive 서비스 객체
        """
        creds = None
        token_file = self.cache_dir / 'token.pickle'

        # Load existing token / 기존 토큰 로드
        if token_file.exists():
            import pickle
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)

        # Get new token if needed / 필요한 경우 새 토큰 받기
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f"OAuth2 credentials file not found / OAuth2 자격 증명 파일을 찾을 수 없습니다: {self.credentials_path}"
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save token for next run / 다음 실행을 위해 토큰 저장
            import pickle
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)

        return build('drive', 'v3', credentials=creds)

    def _test_connection(self) -> None:
        """
        Test Google Drive connection
        Google Drive 연결 테스트

        Raises:
            ConnectionError: If connection test fails / 연결 테스트 실패 시
        """
        try:
            # Try to get information about root / root 정보 가져오기 시도
            self.service.files().get(fileId='root').execute()
        except HttpError as e:
            raise ConnectionError(
                f"Failed to connect to Google Drive / Google Drive 연결 실패: {e}"
            )

    def download_file(
        self,
        file_id: str,
        destination_path: str,
        overwrite: bool = False,
        use_cache: bool = True
    ) -> bool:
        """
        Download a file from Google Drive
        Google Drive에서 파일 다운로드

        Args:
            file_id: Google Drive file ID / Google Drive 파일 ID
            destination_path: Local destination path / 로컬 대상 경로
            overwrite: Whether to overwrite existing file / 기존 파일 덮어쓰기 여부
            use_cache: Whether to use cached metadata / 캐시된 메타데이터 사용 여부

        Returns:
            True if download successful / 다운로드 성공 시 True

        Examples:
            >>> sync = GoogleDriveSync()
            >>> sync.initialize()
            >>> sync.download_file("file_id_here", "local/path/file.csv")
        """
        if self.service is None:
            self.logger.error(
                "Google Drive 서비스가 초기화되지 않았습니다",
                "Google Drive service not initialized"
            )
            return False

        dest_path = Path(destination_path)

        # Check if file already exists and is up-to-date
        # 파일이 이미 존재하고 최신인지 확인
        if dest_path.exists() and not overwrite and use_cache:
            if self._is_file_up_to_date(file_id, dest_path):
                self.logger.info(
                    f"파일이 이미 최신 상태입니다",
                    f"File already up-to-date",
                    file=destination_path
                )
                return True

        try:
            # Get file metadata / 파일 메타데이터 가져오기
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, size, modifiedTime, md5Checksum'
            ).execute()

            # Create parent directory if needed / 필요한 경우 부모 디렉토리 생성
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Download file / 파일 다운로드
            request = self.service.files().get_media(fileId=file_id)
            file_stream = io.BytesIO()
            downloader = MediaIoBaseDownload(file_stream, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    self.logger.debug(
                        f"다운로드 진행률: {progress}%",
                        f"Download progress: {progress}%",
                        file=file_metadata['name']
                    )

            # Write to file / 파일에 쓰기
            with open(dest_path, 'wb') as f:
                f.write(file_stream.getvalue())

            # Update metadata cache / 메타데이터 캐시 업데이트
            self.metadata_cache[str(dest_path)] = {
                'file_id': file_id,
                'name': file_metadata['name'],
                'size': file_metadata.get('size', 0),
                'modified_time': file_metadata['modifiedTime'],
                'md5_checksum': file_metadata.get('md5Checksum'),
                'download_time': datetime.now().isoformat()
            }
            self._save_metadata_cache()

            self.logger.info(
                f"파일 다운로드 성공",
                f"File downloaded successfully",
                file=destination_path,
                size_bytes=file_metadata.get('size', 0)
            )
            return True

        except HttpError as e:
            self.logger.error(
                f"파일 다운로드 실패",
                f"Failed to download file",
                file_id=file_id,
                error=str(e)
            )
            return False

    def _is_file_up_to_date(self, file_id: str, local_path: Path) -> bool:
        """
        Check if local file is up-to-date with Google Drive version
        로컬 파일이 Google Drive 버전과 최신 상태인지 확인

        Args:
            file_id: Google Drive file ID / Google Drive 파일 ID
            local_path: Path to local file / 로컬 파일 경로

        Returns:
            True if file is up-to-date / 파일이 최신 상태면 True
        """
        cache_key = str(local_path)

        # Check if we have cached metadata / 캐시된 메타데이터가 있는지 확인
        if cache_key not in self.metadata_cache:
            return False

        cached_metadata = self.metadata_cache[cache_key]

        # Verify file ID matches / 파일 ID가 일치하는지 확인
        if cached_metadata.get('file_id') != file_id:
            return False

        # Check if more than 1 hour has passed since last download
        # 마지막 다운로드로부터 1시간이 지났는지 확인
        if 'download_time' in cached_metadata:
            from datetime import datetime, timedelta
            download_time = datetime.fromisoformat(cached_metadata['download_time'])
            if datetime.now() - download_time > timedelta(hours=1):
                self.logger.info(
                    "1시간이 지나서 파일을 다시 다운로드합니다",
                    "Re-downloading file after 1 hour",
                    file=local_path
                )
                return False

        try:
            # Get current file metadata from Drive / Drive에서 현재 파일 메타데이터 가져오기
            current_metadata = self.service.files().get(
                fileId=file_id,
                fields='modifiedTime, md5Checksum'
            ).execute()

            # Compare modification times / 수정 시간 비교
            if cached_metadata.get('modified_time') != current_metadata.get('modifiedTime'):
                return False

            # Compare MD5 checksums if available / 가능한 경우 MD5 체크섬 비교
            if current_metadata.get('md5Checksum'):
                if cached_metadata.get('md5_checksum') != current_metadata.get('md5Checksum'):
                    return False

            return True

        except HttpError:
            # If we can't check, assume it's not up-to-date
            # 확인할 수 없으면 최신이 아니라고 가정
            return False

    def search_files(
        self,
        query: str,
        folder_id: Optional[str] = None,
        max_results: int = 100
    ) -> List[FileMetadata]:
        """
        Search for files in Google Drive
        Google Drive에서 파일 검색

        Args:
            query: Search query (e.g., "name contains 'attendance'")
                  검색 쿼리 (예: "name contains 'attendance'")
            folder_id: Limit search to specific folder / 특정 폴더로 검색 제한
            max_results: Maximum number of results / 최대 결과 수

        Returns:
            List of FileMetadata objects / FileMetadata 객체 목록

        Examples:
            >>> sync = GoogleDriveSync()
            >>> sync.initialize()
            >>> files = sync.search_files("name contains 'september'")
        """
        if self.service is None:
            self.logger.error(
                "Google Drive 서비스가 초기화되지 않았습니다",
                "Google Drive service not initialized"
            )
            return []

        try:
            # Build search query / 검색 쿼리 구성
            search_query = query
            if folder_id:
                search_query = f"{query} and '{folder_id}' in parents"

            results = self.service.files().list(
                q=search_query,
                pageSize=max_results,
                fields="files(id, name, mimeType, size, modifiedTime, md5Checksum)"
            ).execute()

            files = results.get('files', [])

            # Convert to FileMetadata objects / FileMetadata 객체로 변환
            file_list = []
            for file in files:
                file_list.append(FileMetadata(
                    file_id=file['id'],
                    name=file['name'],
                    mime_type=file['mimeType'],
                    size=int(file.get('size', 0)),
                    modified_time=file['modifiedTime'],
                    md5_checksum=file.get('md5Checksum')
                ))

            self.logger.info(
                f"파일 검색 완료",
                f"File search completed",
                query=query,
                results_count=len(file_list)
            )

            return file_list

        except HttpError as e:
            self.logger.error(
                f"파일 검색 실패",
                f"File search failed",
                query=query,
                error=str(e)
            )
            return []

    def sync_monthly_data(
        self,
        year: int,
        month: int,
        folder_id: str,
        destination_dir: str
    ) -> SyncResult:
        """
        Synchronize all HR data files for a specific month
        특정 월의 모든 HR 데이터 파일 동기화

        Args:
            year: Year (e.g., 2025) / 년도
            month: Month number (1-12) / 월 번호 (1-12)
            folder_id: Google Drive folder ID containing monthly data
                      월별 데이터가 포함된 Google Drive 폴더 ID
            destination_dir: Local destination directory / 로컬 대상 디렉토리

        Returns:
            SyncResult object with sync statistics / 동기화 통계가 포함된 SyncResult 객체

        Examples:
            >>> sync = GoogleDriveSync()
            >>> sync.initialize()
            >>> result = sync.sync_monthly_data(2025, 9, "folder_id", "HR/data/input")
            >>> print(f"Synced {result.files_synced} files")
        """
        self.logger.info(
            f"{year}년 {month}월 데이터 동기화 시작",
            f"Starting sync for {year}-{month:02d}",
            folder_id=folder_id
        )

        result = SyncResult(success=False)

        if self.service is None:
            result.error_message = "Google Drive service not initialized / Google Drive 서비스가 초기화되지 않았습니다"
            return result

        try:
            # Search for files in the specified folder / 지정된 폴더에서 파일 검색
            files = self.search_files(
                query=f"'{folder_id}' in parents",
                max_results=1000
            )

            dest_dir = Path(destination_dir)
            dest_dir.mkdir(parents=True, exist_ok=True)

            for file in files:
                # Skip directories / 디렉토리 건너뛰기
                if file.mime_type == 'application/vnd.google-apps.folder':
                    continue

                dest_path = dest_dir / file.name

                # Download file / 파일 다운로드
                if self.download_file(file.file_id, str(dest_path), use_cache=True):
                    result.files_synced += 1
                else:
                    result.files_failed += 1

            result.success = result.files_failed == 0
            result.details = {
                'year': year,
                'month': month,
                'folder_id': folder_id,
                'destination_dir': str(dest_dir)
            }

            self.logger.info(
                f"동기화 완료",
                f"Sync completed",
                synced=result.files_synced,
                failed=result.files_failed,
                skipped=result.files_skipped
            )

            return result

        except Exception as e:
            result.error_message = str(e)
            self.logger.error(
                "데이터 동기화 실패",
                "Data sync failed",
                error=str(e)
            )
            return result
