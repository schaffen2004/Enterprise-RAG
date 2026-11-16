# Enterprise-RAG

## Cấu trúc

```
.
├── infra/              # Docker Compose (Postgres, Adminer)
├── src/
│   ├── api/            # FastAPI routers & dependencies
│   ├── model/          # SQLAlchemy models
│   ├── schemas/        # Pydantic request/response schemas
│   ├── services/       # Business logic (UserService)
│   ├── utils/          # Shared helpers: config, security, DB session
│   └── main.py         # FastAPI application
├── tests/              # API integration tests
├── main.py             # Runnable entry point
└── requirements.txt
```

## Chạy dịch vụ

```bash
# 0. Tạo file cấu hình
cp .env.example .env

# 1. Khởi động Postgres
docker compose -f infra/docker-compose.yml up -d

# 2. Cài đặt dependencies
uv venv .venv
uv pip install -r requirements-dev.txt

# 3. Chạy API (tự tạo bảng khi khởi động)
.venv/bin/python main.py
```

API chạy tại `http://localhost:8000`, docs tại `/docs`.

## Auth API

| Method | Endpoint                 | Mô tả                        |
| ------ | ------------------------ | ---------------------------- |
| POST   | `/api/v1/auth/register`  | Đăng ký tài khoản            |
| POST   | `/api/v1/auth/login`     | Đăng nhập, trả về JWT        |
| GET    | `/api/v1/auth/me`        | Thông tin user hiện tại      |
| GET    | `/health`                | Health check                 |

## Test

```bash
.venv/bin/python -m pytest
```
