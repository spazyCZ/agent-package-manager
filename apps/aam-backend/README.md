# AAM Backend

FastAPI backend server for the Agent Package Manager registry.

## Installation

```bash
# From the monorepo root
npm run backend:install

# Or directly
cd apps/aam-backend
pip install -e '.[dev]'
```

## Running

```bash
# Development mode with auto-reload
npm run backend

# Or directly
uvicorn aam_backend.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, access the API documentation at:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- OpenAPI JSON: http://localhost:8000/api/openapi.json

## Configuration

Configuration is done via environment variables or a `.env` file:

```env
# Application
APP_ENV=development
DEBUG=true
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql+asyncpg://aam:aam@localhost:5432/aam

# Redis
REDIS_URL=redis://localhost:6379/0

# Storage
STORAGE_BACKEND=local
STORAGE_LOCAL_PATH=/data/packages

# JWT
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Database Migrations

```bash
# Run migrations
nx run aam-backend:migrate

# Create a new migration
nx run aam-backend:migrate-create -- "migration name"
```

## Development

```bash
# Run tests
pytest

# Run linting
ruff check src/ tests/
mypy src/

# Format code
ruff format src/ tests/
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/register` - Register
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/logout` - Logout

### Users
- `GET /api/v1/users/me` - Get current user
- `PATCH /api/v1/users/me` - Update current user
- `GET /api/v1/users/{username}` - Get user by username

### Packages
- `GET /api/v1/packages` - List packages
- `GET /api/v1/packages/search` - Search packages
- `GET /api/v1/packages/{name}` - Get package
- `GET /api/v1/packages/{name}/{version}` - Get package version
- `POST /api/v1/packages` - Publish package
- `DELETE /api/v1/packages/{name}` - Unpublish package
