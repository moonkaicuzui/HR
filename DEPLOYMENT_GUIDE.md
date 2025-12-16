# HR Dashboard 배포 가이드
# HR Dashboard Deployment Guide

**버전**: Production Release v1.0
**날짜**: 2025-10-14
**상태**: ✅ Production Ready

---

## 🎯 Quick Start

### 최소 요구사항
- Python 3.8 이상
- 4GB RAM
- 100MB 디스크 공간

### 3분 시작 가이드

```bash
# 1. 프로젝트 클론 또는 다운로드
cd /path/to/HR

# 2. 대시보드 생성 (한국어)
python src/generate_dashboard.py --month 10 --year 2025 --language ko

# 3. 브라우저에서 열기
open output_files/HR_Dashboard_Complete_2025_10.html
```

완료! 대시보드가 브라우저에 표시됩니다.

---

## 📚 상세 사용 가이드

### 커맨드라인 옵션

```bash
python src/generate_dashboard.py [OPTIONS]

Options:
  --month, -m   : 월 (1-12, 기본값: 현재 월)
  --year, -y    : 년도 (기본값: 현재 년도)
  --language, -l: 언어 (ko/en/vi, 기본값: ko)
```

### 사용 예시

```bash
# 한국어 9월 대시보드
python src/generate_dashboard.py --month 9 --year 2025 --language ko

# 영어 10월 대시보드
python src/generate_dashboard.py --month 10 --year 2025 --language en

# 베트남어 현재 월 대시보드
python src/generate_dashboard.py --language vi
```

---

## 🌐 다국어 지원

### 지원 언어

| 언어 | 코드 | 날짜 형식 | 통화 |
|------|------|-----------|------|
| 한국어 | ko | YYYY년 MM월 DD일 | ₩ |
| English | en | MM/DD/YYYY | $ |
| Tiếng Việt | vi | DD/MM/YYYY | ₫ |

### 런타임 언어 전환

대시보드 우측 상단의 국기 아이콘 클릭:
- 🇰🇷 한국어
- 🇺🇸 English
- 🇻🇳 Tiếng Việt

페이지 리로드 없이 즉시 전환됩니다.

---

## 📊 데이터 준비

### 필수 데이터 파일

```
input_files/
├── basic manpower data {month}.csv
├── 5prs data {month}.csv
└── attendance/
    └── converted/
        └── attendance data {month}_converted.csv
```

### 파일 명명 규칙

월 이름은 영어 소문자로 사용:
- january, february, march, april
- may, june, july, august
- september, october, november, december

예시:
- `basic manpower data october.csv` ✅
- `basic manpower data October.csv` ❌
- `basic manpower data 10.csv` ❌

### 데이터 인코딩

모든 CSV 파일은 **UTF-8 인코딩**이어야 합니다.

Windows Excel에서 UTF-8로 저장:
1. 파일 → 다른 이름으로 저장
2. 인코딩: UTF-8 선택
3. 저장

---

## 🚀 프로덕션 배포

### 웹 서버 배포

#### Option 1: 정적 호스팅 (권장)

생성된 HTML 파일을 정적 호스팅 서비스에 업로드:

```bash
# AWS S3
aws s3 cp output_files/HR_Dashboard_Complete_2025_10.html \
  s3://your-bucket/dashboard.html --acl public-read

# GitHub Pages
cp output_files/HR_Dashboard_Complete_2025_10.html docs/index.html
git add docs/index.html
git commit -m "Update dashboard"
git push
```

#### Option 2: Python HTTP 서버

```bash
# 간단한 로컬 서버
cd output_files
python -m http.server 8000

# 브라우저에서 접속
open http://localhost:8000/HR_Dashboard_Complete_2025_10.html
```

#### Option 3: Nginx

```nginx
server {
    listen 80;
    server_name hr-dashboard.example.com;

    root /var/www/hr-dashboard;
    index HR_Dashboard_Complete_2025_10.html;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

### 자동 업데이트 스크립트

```bash
#!/bin/bash
# update_dashboard.sh

# 대시보드 생성
python src/generate_dashboard.py --month $(date +%m) --year $(date +%Y)

# 웹 서버에 배포
scp output_files/HR_Dashboard_Complete_*.html \
  user@server:/var/www/hr-dashboard/

echo "Dashboard updated successfully!"
```

### Cron 자동화

```cron
# 매일 오전 6시 자동 업데이트
0 6 * * * /path/to/update_dashboard.sh

# 매주 월요일 오전 7시
0 7 * * 1 /path/to/update_dashboard.sh
```

---

## 🔒 보안 고려사항

### 접근 제어

대시보드에는 민감한 인사 정보가 포함되어 있습니다.

#### 웹 서버 인증 설정

**Nginx Basic Auth**:
```nginx
location / {
    auth_basic "HR Dashboard";
    auth_basic_user_file /etc/nginx/.htpasswd;
}
```

**Apache .htaccess**:
```apache
AuthType Basic
AuthName "HR Dashboard"
AuthUserFile /path/to/.htpasswd
Require valid-user
```

### 데이터 보호

1. **PII 마스킹**: 대시보드는 개인 식별 정보를 마스킹 처리합니다
2. **HTTPS 필수**: 프로덕션 환경에서는 HTTPS 사용 필수
3. **로그 관리**: 접근 로그를 정기적으로 검토

---

## 📈 성능 최적화

### 파일 크기 최적화

대시보드 HTML 파일 크기: 약 1.5MB

**압축 활성화**:
```nginx
gzip on;
gzip_types text/html text/css application/javascript;
gzip_min_length 1000;
```

압축 후 크기: 약 300KB (80% 감소)

### 캐싱 설정

```nginx
location ~* \.html$ {
    expires 1h;
    add_header Cache-Control "public, must-revalidate";
}
```

---

## 🐛 문제 해결

### 일반적인 문제

#### 1. "No module named 'src'" 에러

**해결**:
```bash
# 프로젝트 루트에서 실행
cd /path/to/HR
python src/generate_dashboard.py
```

#### 2. "FileNotFoundError: basic manpower data" 에러

**원인**: 데이터 파일이 없거나 파일명이 잘못됨

**해결**:
```bash
# 파일 존재 확인
ls input_files/basic\ manpower\ data\ october.csv

# 파일명 확인 (소문자 확인)
ls input_files/ | grep -i manpower
```

#### 3. 한글 깨짐 현상

**원인**: 파일 인코딩이 UTF-8이 아님

**해결**:
```bash
# 현재 인코딩 확인
file -I input_files/basic\ manpower\ data\ october.csv

# UTF-8로 변환
iconv -f CP949 -t UTF-8 input_file.csv > output_file.csv
```

#### 4. 차트가 표시되지 않음

**원인**: 브라우저 JavaScript 비활성화 또는 인터넷 연결 필요 (CDN)

**해결**:
- JavaScript 활성화 확인
- 인터넷 연결 확인 (Chart.js CDN 사용)
- 최신 브라우저 사용 (IE11 제외)

---

## 🌐 브라우저 지원

### 지원 브라우저

| 브라우저 | 버전 | 상태 |
|---------|------|------|
| Chrome | 80+ | ✅ 완전 지원 |
| Firefox | 75+ | ✅ 완전 지원 |
| Safari | 13+ | ✅ 완전 지원 |
| Edge | 80+ | ✅ 완전 지원 |
| IE11 | - | ❌ 미지원 |

### 모바일 지원

- ✅ iOS Safari 13+
- ✅ Android Chrome 80+
- ✅ 반응형 디자인
- ✅ 터치 인터페이스

---

## 📞 지원 및 문의

### 기술 지원

문제 발생 시:
1. 이 가이드의 문제 해결 섹션 확인
2. 로그 파일 확인 (`logs/` 디렉토리)
3. 이슈 보고: [프로젝트 저장소]

### 문서

- **사용자 매뉴얼**: `USER_MANUAL.md`
- **개발자 문서**: `DEVELOPER_GUIDE.md`
- **API 문서**: `API_REFERENCE.md`

---

## 📜 라이선스

이 프로젝트는 회사 내부용으로 제작되었습니다.
외부 배포 시 법무팀 승인 필요.

---

## 🎉 성공적인 배포!

대시보드 배포가 완료되었습니다.

**다음 단계**:
1. 사용자 교육 실시
2. 피드백 수집
3. 정기적인 데이터 업데이트
4. 모니터링 및 최적화

**지원**: 문제 발생 시 IT 부서에 문의하세요.

---

**마지막 업데이트**: 2025-10-14
**버전**: 1.0 Production Release
**상태**: ✅ Production Ready
