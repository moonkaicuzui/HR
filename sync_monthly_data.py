#!/usr/bin/env python3
"""
Standalone Google Drive synchronization script
독립 실행형 구글 드라이브 동기화 스크립트
"""
import sys
import json
from pathlib import Path
from datetime import datetime
from src.integration.google_drive_manager import GoogleDriveManager


def update_sync_manifest(month: int, year: int, month_name: str, project_root: Path):
    """
    Update sync manifest with year info from Google Drive folder
    Google Drive 폴더 정보로 동기화 매니페스트 업데이트

    Args:
        month: Month number (1-12) / 월 번호 (1-12)
        year: Year from Google Drive folder / Google Drive 폴더의 연도
        month_name: Month name (e.g., 'september') / 월 이름 (예: 'september')
        project_root: Project root path / 프로젝트 루트 경로
    """
    manifest_path = project_root / "input_files" / "sync_manifest.json"

    # Load existing manifest or create new
    # 기존 매니페스트 로드 또는 새로 생성
    if manifest_path.exists():
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
    else:
        manifest = {
            "description": "Sync manifest tracking Google Drive folder sources",
            "description_ko": "Google Drive 폴더 소스를 추적하는 동기화 매니페스트",
            "months": {}
        }

    # Update month entry with year from Google Drive folder name
    # Google Drive 폴더명의 연도로 월 항목 업데이트
    manifest["months"][month_name] = {
        "year": year,
        "month": month,
        "folder": f"{year}_{month:02d}",
        "synced_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    manifest["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Save manifest
    # 매니페스트 저장
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"📋 Updated sync manifest: {manifest_path}")
    print(f"   {month_name} → {year}_{month:02d} (from Google Drive folder)")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Sync monthly data from Google Drive')
    parser.add_argument('--month', type=int, required=True, help='Month (1-12)')
    parser.add_argument('--year', type=int, required=True, help='Year (e.g., 2025)')
    args = parser.parse_args()
    
    # Month name mapping
    months = ['', 'january', 'february', 'march', 'april', 'may', 'june',
              'july', 'august', 'september', 'october', 'november', 'december']
    month_name = months[args.month].lower()
    
    print(f"Syncing {month_name} {args.year} data from Google Drive...")
    
    try:
        manager = GoogleDriveManager()
        if not manager.initialize('service_account', 'credentials/service-account-key.json'):
            print("❌ Failed to authenticate")
            return 1
        
        # Download files directly
        from google.api_core import retry
        import io
        from googleapiclient.http import MediaIoBaseDownload
        
        # Find folder
        results = manager.service.files().list(
            q=f"mimeType='application/vnd.google-apps.folder' and name='{args.year}_{args.month:02d}'",
            fields='files(id, name)'
        ).execute()
        
        folders = results.get('files', [])
        if not folders:
            print(f"❌ Folder {args.year}_{args.month:02d} not found in Google Drive")
            return 1
        
        folder_id = folders[0]['id']
        print(f"✅ Found folder: {args.year}_{args.month:02d}")
        
        # List files in folder
        file_results = manager.service.files().list(
            q=f"'{folder_id}' in parents",
            fields='files(id, name, size)'
        ).execute()
        
        files = file_results.get('files', [])
        
        # Download mapping
        download_map = {
            'basic_manpower_data.csv': f'input_files/basic manpower data {month_name}.csv',
            'attendance_data.csv': f'input_files/attendance/original/attendance data {month_name}.csv',
            '5prs_data.csv': f'input_files/5prs data {month_name}.csv'
        }
        
        print("\nDownloading files:")
        for file in files:
            if file['name'] in download_map:
                local_path = download_map[file['name']]
                
                # Create directory
                Path(local_path).parent.mkdir(parents=True, exist_ok=True)
                
                # Download
                request = manager.service.files().get_media(fileId=file['id'])
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                
                while not done:
                    status, done = downloader.next_chunk()
                
                # Save
                with open(local_path, 'wb') as f:
                    f.write(fh.getvalue())
                
                size_kb = int(file.get('size', 0)) / 1024
                print(f"  ✅ {file['name']:40s} → {local_path}  ({size_kb:.1f} KB)")
        
        # Download AQL file
        print("\nDownloading AQL history:")
        aql_results = manager.service.files().list(
            q=f"name='AQL_REPORT_{month_name.upper()}_{args.year}.csv'",
            fields='files(id, name, size)'
        ).execute()
        
        aql_files = aql_results.get('files', [])
        if aql_files:
            file = aql_files[0]
            local_path = f'input_files/AQL history/1.HSRG AQL REPORT-{month_name.upper()}.{args.year}.csv'
            
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            
            request = manager.service.files().get_media(fileId=file['id'])
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            
            while not done:
                status, done = downloader.next_chunk()
            
            with open(local_path, 'wb') as f:
                f.write(fh.getvalue())
            
            size_kb = int(file.get('size', 0)) / 1024
            print(f"  ✅ {file['name']:40s} → {local_path}  ({size_kb:.1f} KB)")
        
        # Convert attendance with column standardization
        # 출석 데이터 변환 및 컬럼 표준화
        import pandas as pd
        orig = f'input_files/attendance/original/attendance data {month_name}.csv'
        conv = f'input_files/attendance/converted/attendance data {month_name}_converted.csv'
        if Path(orig).exists():
            df = pd.read_csv(orig)

            # Column name mapping for standardization
            # 컬럼명 표준화 매핑
            column_mapping = {
                'Sequence': 'No.',
                'Company Code': 'CoCode',
                'Combination Department Code': 'Department',
                'Personnel Number': 'ID No',
                'Attendance Name': 'compAdd',
                'Work Time Code': 'WTime'
            }

            # Apply mapping only for columns that exist
            # 존재하는 컬럼만 매핑 적용
            df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
            df.to_csv(conv, index=False)
            print(f"\n✅ Created converted attendance file: {conv}")
            print(f"   Columns standardized: {list(df.columns)}")

        # Update sync manifest with year info from Google Drive folder
        # Google Drive 폴더 정보로 동기화 매니페스트 업데이트
        project_root = Path(__file__).parent
        update_sync_manifest(args.month, args.year, month_name, project_root)

        print(f"\n✅ All {month_name} {args.year} data synced successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
