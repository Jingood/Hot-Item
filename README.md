# 🔥 Hot Item — 한정판 선착순 구매 시스템

> 수량이 한정된 상품을 동시에 수백 명이 구매하려 할 때 발생하는 **Race Condition**을 직접 만들고,  
> 4단계에 걸쳐 아키텍처를 개선하며 각 단계의 성능 변화를 **Locust 부하 테스트로 수치화**한 프로젝트입니다.

<br>

## 📌 프로젝트 개요

| 항목 | 내용 |
|---|---|
| 개발 기간 | 2025.03 — 2025.04 |
| 개발 인원 | 1명 (개인 프로젝트) |
| 테스트 환경 | 동시 접속 유저 500명 · Spawn rate 100/s · 재고 100개 |
| 블로그 시리즈 | [devjingood.tistory.com](https://devjingood.tistory.com) |

<br>

## 🛠 기술 스택

| 분류 | 기술 |
|---|---|
| Backend | Python 3.12, Django 5.0, Django REST Framework |
| Database | PostgreSQL 16 |
| Cache / Queue | Redis 7.2 |
| 인증 | SimpleJWT (커스텀 인증 클래스) |
| API 문서 | drf-spectacular (Swagger UI) |
| 부하 테스트 | Locust |
| 인프라 | Docker, Docker Compose, Dev Container |

<br>

## 🏗 시스템 아키텍처

```
┌─────────────────────────────────────────┐
│              Client (500 users)          │
└──────────────────┬──────────────────────┘
                   │ HTTP
┌──────────────────▼──────────────────────┐
│           Django REST Framework          │
│  ┌───────────────────────────────────┐  │
│  │  StatelessJWTAuthentication       │  │  ← v4: DB 조회 없이 토큰만 검증
│  │  OrderSerializer (IntegerField)   │  │  ← v5 목표: Serializer DB 조회 제거
│  │  OrderCreateView                  │  │
│  └───────────────┬───────────────────┘  │
└──────────────────┼──────────────────────┘
           ┌───────┴────────┐
           │                │
┌──────────▼──────┐ ┌───────▼────────────┐
│   Redis 7.2     │ │  PostgreSQL 16      │
│                 │ │                     │
│ • 재고 원자 연산 │ │ • 주문 최종 저장    │
│ • 대기열 관리   │ │ • 사용자 인증       │
└─────────────────┘ └─────────────────────┘
```

<br>

## 📁 프로젝트 구조

```
hot-item/
├── config/                  # Django 프로젝트 설정
│   ├── settings.py
│   └── urls.py
├── accounts/                # 회원 앱
│   ├── models.py            # AbstractUser 상속 커스텀 User
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── authentication.py   # v4: StatelessJWTAuthentication
├── shop/                    # 상품 / 주문 앱
│   ├── models.py            # Item, Order 모델
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── locustfile.py            # 부하 테스트 시나리오
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

<br>

## ⚙️ 로컬 실행 방법

### 1. 저장소 클론

```bash
git clone https://github.com/Jingood/hot-item.git
cd hot-item
```

### 2. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일을 열어 값을 설정합니다
```

```env
# .env
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True

POSTGRES_DB=hot_item_db
POSTGRES_USER=hot_item_user
POSTGRES_PASSWORD=your_password_here

REDIS_URL=redis://redis:6379/0
```

### 3. 컨테이너 실행

```bash
docker-compose up -d
```

### 4. Django 프로젝트 초기화

```bash
# DB 마이그레이션
docker-compose exec web python manage.py migrate

# 슈퍼유저 생성 (Admin 접속용)
docker-compose exec web python manage.py createsuperuser
```

### 5. 접속

| 서비스 | URL |
|---|---|
| Swagger UI | http://localhost:8001/api/docs/ |
| Django Admin | http://localhost:8001/admin/ |

<br>

## 🔑 API 엔드포인트

### 계정

| Method | URL | 설명 | 인증 |
|---|---|---|---|
| `POST` | `/api/accounts/signup/` | 회원가입 | ✗ |
| `POST` | `/api/accounts/login/` | 로그인 (JWT 발급) | ✗ |
| `POST` | `/api/accounts/refresh/` | Access Token 재발급 | ✗ |
| `POST` | `/api/accounts/logout/` | 로그아웃 (토큰 블랙리스트) | ✓ |

### 상품 / 주문

| Method | URL | 설명 | 인증 |
|---|---|---|---|
| `GET` | `/api/shop/items/` | 상품 목록 조회 | ✗ |
| `POST` | `/api/shop/orders/` | 주문 생성 (선착순 구매) | ✓ |

<br>

## 🧪 부하 테스트

### 테스트 전 준비 — 더미 유저 & 토큰 생성

```bash
# 1. Django shell 진입
docker-compose exec web python manage.py shell

# 2. 더미 유저 500명 생성
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
User = get_user_model()
hashed_pw = make_password('testpass123!')
users = [User(username=f'dummy{i}', password=hashed_pw) for i in range(1, 501)]
User.objects.bulk_create(users, ignore_conflicts=True)
print("완료!")

# 3. 토큰 사전 발급 (로그인 병목 방지)
from rest_framework_simplejwt.tokens import RefreshToken
with open('access_tokens.txt', 'w') as f:
    for i in range(1, 501):
        user = User.objects.get(username=f'dummy{i}')
        f.write(f"{str(RefreshToken.for_user(user).access_token)}\n")
print("토큰 저장 완료!")
exit()
```

### 테스트 실행

```bash
# Locust 웹 UI로 실행
locust -f locustfile.py --host=http://localhost:8001

# 설정: Users 500 / Spawn rate 100
# 접속: http://localhost:8089
```

<br>

## 📊 단계별 성능 비교 결과

> 테스트 환경: 동시 접속 500명 · Spawn rate 100/s · 재고 100개

| 버전 | 핵심 변경 | 초과 판매 | 최대 RPS | 95%ile 응답 | 실패율 | 병목 위치 |
|---|---|:---:|---:|---:|---:|---|
| **v1** | 순수 RDBMS | ❌ 발생 | ~165 | 68 ms | ~1% | Race Condition |
| **v2** | Pessimistic Lock | ✅ 없음 | ~95 | ~30,000 ms | 61.87% | Lock Contention |
| **v3** | Redis 대기열 | ✅ 없음 | **~180** | ~19,000 ms | 70.92% | JWT 인증 DB 조회 |
| **v4** | 커스텀 JWT 인증 | ✅ 없음 | ~155 | ~32,000 ms | 66.5% | Serializer DB 조회 |

<br>

## 🔍 단계별 개선 과정

### v1 — Race Condition 재현 (의도된 실패)

```
① SELECT: stock 읽기
② 판단:   stock > 0 → 구매 가능  ← 수백 명이 동시에 같은 값을 읽음
③ UPDATE: stock -= 1 저장        ← 동시에 실행 → 음수 도달 → 500 에러
```

재고 100개임에도 100건 이상의 주문이 생성되는 **초과 판매** 발생.  
`PositiveIntegerField` 제약으로 음수 저장 시도 시 500 에러.

---

### v2 — Pessimistic Locking

```python
# select_for_update()로 row에 배타적 락 설정
item = Item.objects.select_for_update().get(id=item_id)
```

초과 판매 **완전 차단**, 정확히 100건만 처리. 그러나 락을 기다리는 트랜잭션들이  
DB 커넥션을 점유한 채 대기 → PostgreSQL 연결 한도(100개) 초과 →  
`FATAL: sorry, too many clients already` → **Lock Contention으로 서버 마비**.

---

### v3 — Redis 인메모리 대기열

```
DB 락 제거 → Redis Sorted Set 원자적 연산으로 재고 제어
→ 최대 RPS v2 대비 약 90% 향상 (~95 → ~180)
→ 2차 병목 노출: SimpleJWT가 매 요청마다 User.objects.get() 실행
```

주문 로직 병목 해소 후, 인증 단계의 DB 조회가 커넥션 풀을 고갈시킴.

---

### v4 — 커스텀 JWT 인증 클래스

```python
class StatelessJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        # DB 조회 없이 토큰에서 user_id만 추출
        user = User()
        user.id = validated_token.get("user_id")
        return user
```

인증 DB 조회 제거 후, **3차 병목 노출**: DRF `PrimaryKeyRelatedField`가  
`is_valid()` 시 `Item.objects.get()`을 내부적으로 실행.  
프레임워크가 숨기고 있던 DB I/O가 고부하 환경에서 수면 위로 드러남.

---

### 핵심 인사이트

> **트래픽은 물처럼 항상 가장 좁은 곳을 찾아낸다.**
>
> 가장 큰 병목을 제거하면 그 뒤에 숨어있던 다음 병목이 드러난다.  
> 이 프로젝트에서 발견한 병목 3곳 중 2곳은 직접 작성한 코드가 아니라  
> **프레임워크 내부에서 조용히 실행되는 DB 쿼리**였다.

<br>

## 🚀 v5 계획 — Message Queue 도입

현재 구조의 근본 문제는 유저 요청이 DB에 **동기적으로** 도달한다는 점.  
DB 커넥션은 유한한 자원이기 때문에 동시 요청이 한도를 넘으면 시스템이 무너진다.

```
# 현재 (동기)
요청 → 인증 → Serializer 검증 → Redis → DB 저장 → 응답

# 목표 (비동기)
요청 → Redis 대기열 등록 → 즉시 응답 ✓
                ↓ (Celery Worker)
         Serializer 검증 → DB 저장
```

DB 쓰기를 Celery Worker로 분리하면 커넥션은 워커 수만큼만 소비,  
500명이 동시에 접근해도 에러율 **0%** 를 목표로 한다.

<br>

## 📝 관련 블로그 시리즈

전체 개발 과정과 트러블슈팅을 12개 포스트로 기록했습니다.

| 번호 | 제목 |
|---|---|
| #1 | 프로젝트 소개 & Docker 환경 구성 |
| #2 | requirements.txt, Dockerfile, docker-compose.yml 작성 |
| #3 | Dev Container로 VS Code 개발 환경 컨테이너 안으로 옮기기 |
| #4 | settings.py 환경 변수 연동, PostgreSQL 마이그레이션, Redis 연결 확인 |
| #5 | DRF + Swagger 문서 자동화, 커스텀 User 모델, JWT 인증 설정 |
| TS#1 | 트러블슈팅: AUTH_USER_MODEL 변경 후 migrate 실패 |
| #6 | 회원가입 / 로그인 / 로그아웃 API 구현 및 Swagger UI 테스트 |
| #7 | shop 앱 — Item / Order 모델 설계 및 Django Admin 등록 |
| #8 | 선착순 구매 API v1 — 순수 RDBMS, 의도된 실패 |
| #9 | v1 부하 테스트 — Race Condition을 눈으로 확인하다 |
| #10 | v2 부하 테스트 — 정합성은 지켰지만, 서버가 뻗었다 |
| #11 | v3 부하 테스트 — Redis가 락을 없앴지만, 새로운 병목이 나타났다 |
| #12 | 프로젝트 최종 회고 — v1부터 v4까지, 우리가 증명한 것들 |

👉 [블로그 바로가기](https://devjingood.tistory.com)

<br>

---

<div align="center">
  <sub>Made with 🔥 by <a href="https://github.com/Jingood">JinGood</a></sub>
</div>
