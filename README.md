## gym 프로젝트 소개 및 기능 정의
 - 회원권을 구매하여 크레딧을 생성합니다.
 - 크레딧으로 등록한 레슨을 예약합니다.
 - 나의 예약 및 크레딧 잔고를 확인합니다.

## 기술적 소개
 - django 프레임 워크 테스트
 - docker-compose를 활용한 배포
 - 스웨거를 통한 api 확인
 - 적절한 orm 활용법

## 기본 정보

- 주소 : http://localhost:8000(개발), http://localhost(배포) 
- swagger path : http://localhost:8000/swagger/
- 기본 관리자 정보 : username : admin password: admin
- 개발 서버 실행 순서(개발 서버 sqlite 사용)
- 1. python manage.py migrate
- 2. python manage.py create_default_user
- 3. python manage.py runserver
- 배포 서버 실행 : docker-compose up
- 필자는 Mac amd를 사용해 docker-compose.yml 파일 platform: linux/amd64를 설정 했으나 장비에 따라 해당 문구 삭제 필요



## API 사용 설명
1. 스웨거 접속 : http://localhost:8000/swagger/
2. 우측 상단 Django login : admin/admin
1. 예약을 위한 수업을 생성해 주세요
2. 크레딧 구매를 위한 가격정책(회원권)을 생성해 주세요.
3. 크레딧을 구매합니다.
4. 수업을 예약합니다

