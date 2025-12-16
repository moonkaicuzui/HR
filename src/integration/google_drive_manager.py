"""
Google Drive Integration Manager for QIP Incentive Dashboard System
This module handles automatic synchronization of data files from Google Drive
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import pickle
import hashlib

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
import io

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/drive_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Google Drive API scope
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


@dataclass
class SyncResult:
    """Result of a synchronization operation"""
    success: bool
    files_synced: int
    files_failed: int
    error_message: str = ""
    details: Dict[str, Any] = None


class GoogleDriveManager:
    """
    Main class for managing Google Drive synchronization
    """
    
    def __init__(self, config_path: str = 'config_files/drive_config.json'):
        """
        Initialize the Google Drive Manager
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.service = None
        self.cache_dir = Path(self.config['local_paths']['cache_dir'])
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Create necessary directories
        self._setup_directories()
        
    def _load_config(self) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Return default configuration"""
        return {
            "google_drive": {
                "root_folder_id": "",
                "folder_structure": {
                    "monthly_data": {"id": "", "naming_pattern": "{year}_{month:02d}"},
                    "aql_history": {"id": "", "file_pattern": "AQL_REPORT_{month}_{year}.csv"},
                    "configs": {"id": ""}
                }
            },
            "sync_settings": {
                "auto_sync_enabled": True,
                "sync_interval_minutes": 60,
                "retry_attempts": 3,
                "cache_duration_hours": 24
            },
            "local_paths": {
                "data_root": "./input_files",
                "cache_dir": "./.cache/drive_sync",
                "logs_dir": "./logs/drive_sync"
            }
        }
    
    def _setup_directories(self):
        """Create necessary local directories"""
        paths = [
            self.config['local_paths']['data_root'],
            self.config['local_paths']['cache_dir'],
            self.config['local_paths']['logs_dir'],
            'input_files/AQL history',
            'input_files/attendance/original',
            'input_files/attendance/converted'
        ]
        
        for path in paths:
            Path(path).mkdir(parents=True, exist_ok=True)
    
    def initialize(self, auth_type: str = 'service_account', 
                  credentials_path: str = None) -> bool:
        """
        Initialize Google Drive API connection
        
        Args:
            auth_type: Type of authentication ('service_account' or 'oauth2')
            credentials_path: Path to credentials file
            
        Returns:
            bool: True if initialization successful
        """
        try:
            if auth_type == 'service_account':
                self.service = self._authenticate_service_account(credentials_path)
            else:
                self.service = self._authenticate_oauth2(credentials_path)
            
            # Test connection
            self._test_connection()
            logger.info("Google Drive connection initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive connection: {e}")
            return False
    
    def _authenticate_service_account(self, key_file: str = None) -> Any:
        """
        Authenticate using service account
        
        Args:
            key_file: Path to service account key file
            
        Returns:
            Google Drive service object
        """
        if not key_file:
            key_file = os.environ.get('GOOGLE_SERVICE_ACCOUNT_KEY', 
                                     'credentials/service-account-key.json')
        
        if not os.path.exists(key_file):
            raise FileNotFoundError(f"Service account key file not found: {key_file}")
        
        credentials = ServiceAccountCredentials.from_service_account_file(
            key_file, scopes=SCOPES
        )
        
        return build('drive', 'v3', credentials=credentials)
    
    def _authenticate_oauth2(self, credentials_path: str = None) -> Any:
        """
        Authenticate using OAuth2 flow
        
        Args:
            credentials_path: Path to OAuth2 credentials file
            
        Returns:
            Google Drive service object
        """
        creds = None
        token_file = 'token.pickle'
        
        # Load existing token
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not credentials_path:
                    credentials_path = 'credentials/client_secrets.json'
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        return build('drive', 'v3', credentials=creds)
    
    def _test_connection(self):
        """Test Google Drive connection by listing root folder"""
        try:
            # Try to get information about the root folder
            root_id = self.config['google_drive'].get('root_folder_id', 'root')
            self.service.files().get(fileId=root_id).execute()
        except HttpError as e:
            raise ConnectionError(f"Failed to connect to Google Drive: {e}")
    
    def sync_monthly_data(self, year: int, month: str) -> SyncResult:
        """
        Sync all data files for a specific month
        
        Args:
            year: Year (e.g., 2025)
            month: Month name (e.g., 'july')
            
        Returns:
            SyncResult object
        """
        logger.info(f"Starting sync for {month} {year}")
        
        files_synced = 0
        files_failed = 0
        sync_details = {}
        
        try:
            # Get month number
            month_num = self._get_month_number(month)
            
            # Sync current month data
            current_month_folder = f"{year}_{month_num:02d}"
            monthly_files = [
                ('basic_manpower_data.csv', f'basic manpower data {month}.csv'),
                ('attendance_data.csv', f'attendance/original/attendance data {month}.csv'),
                ('5prs_data.csv', f'5prs data {month}.csv')
            ]
            
            for drive_name, local_name in monthly_files:
                success = self._sync_file_from_path(
                    f"monthly_data/{current_month_folder}/{drive_name}",
                    f"input_files/{local_name}"
                )
                if success:
                    files_synced += 1
                    sync_details[drive_name] = "Success"
                else:
                    files_failed += 1
                    sync_details[drive_name] = "Failed"
            
            # Sync AQL history for current and previous months
            months_to_sync = self._get_months_for_aql(month_num, year)
            for m_name, m_year in months_to_sync:
                aql_file = f"AQL_REPORT_{m_name.upper()}_{m_year}.csv"
                local_path = f"input_files/AQL history/1.HSRG AQL REPORT-{m_name.upper()}.{m_year}.csv"
                
                success = self._sync_file_from_path(
                    f"aql_history/{aql_file}",
                    local_path
                )
                if success:
                    files_synced += 1
                    sync_details[aql_file] = "Success"
                else:
                    files_failed += 1
                    sync_details[aql_file] = "Failed"
            
            # Sync configuration files
            config_files = [
                ('auditor_trainer_area_mapping.json', 'auditor_trainer_area_mapping.json'),
                ('type2_position_mapping.json', 'type2_position_mapping.json')
            ]
            
            for drive_name, local_name in config_files:
                success = self._sync_file_from_path(
                    f"configs/{drive_name}",
                    local_name
                )
                if success:
                    files_synced += 1
                    sync_details[drive_name] = "Success"
                else:
                    files_failed += 1
                    sync_details[drive_name] = "Failed"
            
            # Generate sync result
            success = files_failed == 0
            result = SyncResult(
                success=success,
                files_synced=files_synced,
                files_failed=files_failed,
                error_message="" if success else f"{files_failed} files failed to sync",
                details=sync_details
            )
            
            logger.info(f"Sync completed: {files_synced} succeeded, {files_failed} failed")
            return result
            
        except Exception as e:
            logger.error(f"Error during sync: {e}")
            return SyncResult(
                success=False,
                files_synced=files_synced,
                files_failed=files_failed,
                error_message=str(e),
                details=sync_details
            )
    
    def _get_month_number(self, month: str) -> int:
        """Convert month name to number"""
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        return months.get(month.lower(), 0)
    
    def _get_months_for_aql(self, current_month: int, year: int) -> List[Tuple[str, int]]:
        """Get list of months needed for AQL history (current + 2 previous)"""
        months = [
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december'
        ]
        
        result = []
        for i in range(3):
            month_idx = current_month - 1 - i
            year_offset = 0
            
            if month_idx < 0:
                month_idx += 12
                year_offset = -1
            
            result.append((months[month_idx], year + year_offset))
        
        return result
    
    def _sync_file_from_path(self, drive_path: str, local_path: str) -> bool:
        """
        Sync a file from Drive path to local path
        
        Args:
            drive_path: Path in Google Drive (relative to root folder)
            local_path: Local destination path
            
        Returns:
            bool: True if sync successful
        """
        try:
            # Find file in Drive
            file_id = self._find_file_by_path(drive_path)
            if not file_id:
                logger.warning(f"File not found in Drive: {drive_path}")
                return False
            
            # Check if update needed
            if self._is_cache_valid(file_id, local_path):
                logger.info(f"Using cached version of {drive_path}")
                return True
            
            # Download file
            success = self._download_file(file_id, local_path)
            if success:
                self._update_cache_metadata(file_id, local_path)
                logger.info(f"Successfully synced {drive_path} to {local_path}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error syncing {drive_path}: {e}")
            return False
    
    def _find_file_by_path(self, path: str) -> Optional[str]:
        """
        Find file ID by path in Google Drive
        
        Args:
            path: Path relative to root folder
            
        Returns:
            File ID if found, None otherwise
        """
        try:
            parts = path.split('/')
            parent_id = self.config['google_drive']['root_folder_id']
            
            # Navigate through folders
            for i, part in enumerate(parts[:-1]):
                # Search for folder
                query = f"name='{part}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder'"
                results = self.service.files().list(
                    q=query,
                    fields='files(id, name)'
                ).execute()
                
                items = results.get('files', [])
                if not items:
                    logger.warning(f"Folder not found: {part}")
                    return None
                
                parent_id = items[0]['id']
            
            # Search for file
            file_name = parts[-1]
            query = f"name='{file_name}' and '{parent_id}' in parents"
            results = self.service.files().list(
                q=query,
                fields='files(id, name, modifiedTime)'
            ).execute()
            
            items = results.get('files', [])
            if items:
                return items[0]['id']
            
            return None
            
        except HttpError as e:
            logger.error(f"Error finding file {path}: {e}")
            return None
    
    def _download_file(self, file_id: str, destination: str) -> bool:
        """
        Download a file from Google Drive
        
        Args:
            file_id: Google Drive file ID
            destination: Local destination path
            
        Returns:
            bool: True if download successful
        """
        try:
            # Create destination directory if needed
            Path(destination).parent.mkdir(parents=True, exist_ok=True)
            
            # Download file
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.debug(f"Download {int(status.progress() * 100)}%")
            
            # Write to file
            fh.seek(0)
            with open(destination, 'wb') as f:
                f.write(fh.read())
            
            return True
            
        except HttpError as e:
            logger.error(f"Error downloading file {file_id}: {e}")
            return False
    
    def _is_cache_valid(self, file_id: str, local_path: str) -> bool:
        """
        Check if cached file is still valid
        
        Args:
            file_id: Google Drive file ID
            local_path: Local file path
            
        Returns:
            bool: True if cache is valid
        """
        cache_file = self.cache_dir / f"{file_id}.meta"
        
        if not cache_file.exists() or not Path(local_path).exists():
            return False
        
        try:
            with open(cache_file, 'r') as f:
                metadata = json.load(f)
            
            # Check cache age
            cache_time = datetime.fromisoformat(metadata['cached_at'])
            cache_duration = timedelta(hours=self.config['sync_settings']['cache_duration_hours'])
            
            if datetime.now() - cache_time > cache_duration:
                return False
            
            # Check file modification time
            file_meta = self.service.files().get(
                fileId=file_id,
                fields='modifiedTime'
            ).execute()
            
            drive_modified = datetime.fromisoformat(file_meta['modifiedTime'].replace('Z', '+00:00'))
            cached_modified = datetime.fromisoformat(metadata['drive_modified'])
            
            return drive_modified <= cached_modified
            
        except Exception as e:
            logger.debug(f"Cache validation error: {e}")
            return False
    
    def _update_cache_metadata(self, file_id: str, local_path: str):
        """Update cache metadata for a file"""
        try:
            file_meta = self.service.files().get(
                fileId=file_id,
                fields='modifiedTime,name,size'
            ).execute()
            
            metadata = {
                'file_id': file_id,
                'local_path': local_path,
                'cached_at': datetime.now().isoformat(),
                'drive_modified': file_meta['modifiedTime'].replace('Z', '+00:00'),
                'file_name': file_meta['name'],
                'file_size': file_meta.get('size', 0)
            }
            
            cache_file = self.cache_dir / f"{file_id}.meta"
            with open(cache_file, 'w') as f:
                json.dump(metadata, f)
                
        except Exception as e:
            logger.warning(f"Failed to update cache metadata: {e}")
    
    def validate_synced_data(self, month: str) -> Dict[str, bool]:
        """
        Validate that all required files are present and valid
        
        Args:
            month: Month name
            
        Returns:
            Dictionary of file validation results
        """
        validation_results = {}
        
        # Define required files (only critical data files)
        required_files = [
            f'input_files/basic manpower data {month}.csv',
            f'input_files/attendance/original/attendance data {month}.csv',
            f'input_files/5prs data {month}.csv'
        ]
        
        # Optional config files (already exist locally in config_files folder)
        optional_files = [
            'config_files/auditor_trainer_area_mapping.json',
            'config_files/type2_position_mapping.json'
        ]
        
        # Check required files
        for file_path in required_files:
            if Path(file_path).exists():
                # Additional validation (file size, format, etc.)
                validation_results[file_path] = self._validate_file(file_path)
            else:
                validation_results[file_path] = False
        
        # Check optional files (don't fail if missing)
        for file_path in optional_files:
            if Path(file_path).exists():
                validation_results[file_path] = self._validate_file(file_path)
            # Don't add to results if missing (to avoid warnings)
        
        return validation_results
    
    def download_specific_file(self, drive_path: str, local_path: str) -> bool:
        """
        특정 파일을 Google Drive에서 다운로드
        
        Args:
            drive_path: Google Drive 파일 경로 (예: "monthly_data/2025_07/파일명.csv")
            local_path: 로컬 저장 경로
            
        Returns:
            bool: 다운로드 성공 여부
        """
        try:
            # Google Drive 서비스 초기화 확인
            if not self.service:
                logger.info("Google Drive 연결 초기화 중...")
                if not self.initialize():
                    logger.error("Google Drive 연결 실패")
                    return False
            
            logger.info(f"🔍 Google Drive에서 파일 검색: {drive_path}")
            
            # 파일 검색
            file_id = self._find_file_by_path(drive_path)
            if not file_id:
                logger.warning(f"❌ 파일을 찾을 수 없습니다: {drive_path}")
                return False
            
            # 다운로드 실행
            logger.info(f"📥 파일 다운로드 중: {drive_path}")
            success = self._download_file(file_id, local_path)
            
            if success:
                logger.info(f"✅ 파일 다운로드 성공: {local_path}")
            else:
                logger.error(f"❌ 파일 다운로드 실패: {drive_path}")
                
            return success
            
        except Exception as e:
            logger.error(f"파일 다운로드 중 오류: {e}")
            return False
    
    def _validate_file(self, file_path: str) -> bool:
        """
        Validate individual file
        
        Args:
            file_path: Path to file
            
        Returns:
            bool: True if file is valid
        """
        try:
            path = Path(file_path)
            
            # Check file size
            if path.stat().st_size == 0:
                return False
            
            # Check file format
            if path.suffix == '.csv':
                # Try to read CSV
                import pandas as pd
                pd.read_csv(file_path, nrows=1)
            elif path.suffix == '.json':
                # Try to parse JSON
                with open(file_path, 'r') as f:
                    json.load(f)
            
            return True
            
        except Exception as e:
            logger.warning(f"File validation failed for {file_path}: {e}")
            return False
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status"""
        status = {
            'connected': self.service is not None,
            'last_sync': None,
            'cache_size': 0,
            'cached_files': []
        }
        
        try:
            # Get last sync time from most recent cache file
            cache_files = list(self.cache_dir.glob('*.meta'))
            if cache_files:
                latest = max(cache_files, key=lambda p: p.stat().st_mtime)
                with open(latest, 'r') as f:
                    metadata = json.load(f)
                    status['last_sync'] = metadata['cached_at']
            
            # Calculate cache size
            for cache_file in cache_files:
                status['cache_size'] += cache_file.stat().st_size
                with open(cache_file, 'r') as f:
                    metadata = json.load(f)
                    status['cached_files'].append(metadata['file_name'])
            
        except Exception as e:
            logger.warning(f"Error getting sync status: {e}")
        
        return status


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Google Drive Sync Manager for QIP System')
    parser.add_argument('--month', type=str, required=True, help='Month to sync (e.g., july)')
    parser.add_argument('--year', type=int, default=2025, help='Year (default: 2025)')
    parser.add_argument('--config', type=str, default='config_files/drive_config.json', 
                       help='Path to configuration file')
    parser.add_argument('--auth', type=str, choices=['service_account', 'oauth2'],
                       default='service_account', help='Authentication type')
    parser.add_argument('--credentials', type=str, help='Path to credentials file')
    
    args = parser.parse_args()
    
    # Initialize manager
    manager = GoogleDriveManager(args.config)
    
    # Connect to Google Drive
    if manager.initialize(args.auth, args.credentials):
        # Sync data
        result = manager.sync_monthly_data(args.year, args.month)
        
        if result.success:
            print(f"✅ Successfully synced {result.files_synced} files")
            print("\nValidating synced data...")
            
            # Validate data
            validation = manager.validate_synced_data(args.month)
            
            all_valid = all(validation.values())
            if all_valid:
                print("✅ All files validated successfully")
            else:
                print("⚠️ Some files failed validation:")
                for file, valid in validation.items():
                    if not valid:
                        print(f"  ❌ {file}")
        else:
            print(f"❌ Sync failed: {result.error_message}")
            if result.details:
                print("\nDetails:")
                for file, status in result.details.items():
                    symbol = "✅" if status == "Success" else "❌"
                    print(f"  {symbol} {file}: {status}")
    else:
        print("❌ Failed to initialize Google Drive connection")