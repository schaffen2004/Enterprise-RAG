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
cp .env.local .env

# 1. Khởi động Postgres
docker compose -f infra/docker-compose.yml up -d

# 2. Cài đặt dependencies
uv venv .venv
uv pip install -r requirements-dev.txt

# 3. Chạy API (tự tạo bảng khi khởi động)
.venv/bin/python main.py
```

API chạy tại `http://localhost:8000`, docs tại `/docs`.

## Cấu hình S3

Tài liệu được lưu trên Amazon S3. Thêm các biến sau vào `.env`:

```env
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=ap-southeast-1
S3_BUCKET=...
MAX_UPLOAD_SIZE_MB=20
```

## Auth API

| Method | Endpoint                 | Mô tả                        |
| ------ | ------------------------ | ---------------------------- |
| POST   | `/api/v1/auth/register`  | Đăng ký tài khoản            |
| POST   | `/api/v1/auth/login`     | Đăng nhập, trả về JWT        |
| GET    | `/api/v1/auth/me`        | Thông tin user hiện tại      |
| GET    | `/health`                | Health check                 |

## Documents API

| Method | Endpoint                     | Mô tả                                        |
| ------ | ---------------------------- | -------------------------------------------- |
| POST   | `/api/v1/documents/upload`   | Upload tài liệu lên S3 (yêu cầu Bearer JWT)  |

Ví dụ:

```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@data/test.pdf"
```

Định dạng hỗ trợ: `.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.txt`.
File được lưu với key `documents/<user_id>/<uuid><extension>`.

## Test

```bash
.venv/bin/python -m pytest
```
