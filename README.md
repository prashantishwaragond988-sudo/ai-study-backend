# AI Study App Backend

Flask backend for the AI Study App.

Milestone 4 adds login with JWT access/refresh tokens. Password reset, SMS,
WhatsApp, OCR, AI, Cloudinary uploads, Google login, and Flutter integration are
intentionally not implemented yet.

## What Is Included

- Production-friendly Flask app factory structure.
- Environment-based configuration using `.env`.
- CORS support for future Flutter/web clients.
- JSON response helpers.
- Central JSON error handling.
- Basic structured logging.
- Firebase Admin SDK initialization from `serviceAccountKey.json` locally or
  `FIREBASE_SERVICE_ACCOUNT_BASE64` in production.
- Firestore service layer.
- `/health` endpoint.
- `/firestore-test` endpoint.
- `POST /api/auth/register`.
- `POST /api/auth/verify-email-otp`.
- `POST /api/auth/login`.
- `POST /api/auth/refresh-token`.
- `POST /api/auth/logout`.
- Bcrypt password hashing.
- Gmail SMTP email delivery for registration OTP.
- One-time OTP records with 5-minute expiry.
- PyJWT access and refresh tokens.
- Firestore `user_sessions` records with hashed refresh tokens.
- Placeholder service for future Cloudinary integration.

## Folder Structure

```text
backend/
  app/
    __init__.py
    config.py
    auth/
      routes.py
      services.py
      validators.py
    common/
      errors.py
      responses.py
    firestore/
      routes.py
    health/
      routes.py
    integrations/
      __init__.py
    services/
      firebase_admin_service.py
      firestore_service.py
      email_service.py
      jwt_service.py
      cloudinary_service.py
  .env
  .env.example
  .gitignore
  requirements.txt
  run.py
  serviceAccountKey.json
  README.md
```

## Key Files

- `app/auth/routes.py`: Registration and email OTP verification endpoints.
- `app/auth/services.py`: Registration, duplicate checks, password hashing, OTP storage, OTP verification, login, refresh-token session checks, and logout.
- `app/auth/validators.py`: Request validation for registration, OTP verification, login, refresh-token, and logout.
- `app/services/email_service.py`: Gmail SMTP email delivery.
- `app/services/jwt_service.py`: JWT creation and refresh-token verification.
- `app/services/firebase_admin_service.py`: Firebase Admin SDK initialization.
- `app/services/firestore_service.py`: Firestore test service.
- `app/common/errors.py`: Central JSON error handling.
- `app/config.py`: Environment-backed configuration.

## Setup

1. Create and activate a Python virtual environment:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables:

```bash
copy .env.example .env
```

Required Firebase values:

```text
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_CREDENTIALS_PATH=serviceAccountKey.json
# Optional for cloud deployment:
FIREBASE_SERVICE_ACCOUNT_BASE64=
```

Required Gmail SMTP values:

```text
EMAIL_PROVIDER=gmail
EMAIL_FROM=your-gmail-address@gmail.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-gmail-address@gmail.com
SMTP_PASSWORD=your-gmail-app-password
```

Use a Gmail App Password, not your normal Gmail password.

Required JWT value:

```text
JWT_SECRET_KEY=use-a-long-random-secret
JWT_ACCESS_TOKEN_EXPIRES_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRES_DAYS=30
```

4. Add Firebase Admin credentials:

Place the Firebase Admin service account file here:

```text
backend/serviceAccountKey.json
```

This file is intentionally ignored by git.

5. Run the backend:

```bash
python run.py
```

By default the server runs at:

```text
http://127.0.0.1:5000
```

## Render Deployment

Firebase Admin credentials work in two modes:

- Local development: set `FIREBASE_CREDENTIALS_PATH=serviceAccountKey.json`.
- Render/production: set `FIREBASE_SERVICE_ACCOUNT_BASE64` to a Base64-encoded
  copy of `serviceAccountKey.json`.

When `FIREBASE_SERVICE_ACCOUNT_BASE64` exists, the backend initializes Firebase
Admin directly from that decoded JSON. If it is empty, the backend falls back to
`FIREBASE_CREDENTIALS_PATH`, preserving local development behavior.

### Generate Firebase Base64 Value

From the `backend` directory on Windows PowerShell:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("serviceAccountKey.json"))
```

From the `backend` directory on macOS/Linux:

```bash
base64 -w 0 serviceAccountKey.json
```

If your macOS `base64` command does not support `-w`, use:

```bash
base64 serviceAccountKey.json | tr -d '\n'
```

Copy the full output and add it to Render as the
`FIREBASE_SERVICE_ACCOUNT_BASE64` environment variable. Do not commit the JSON
file or the Base64 value to git.

### Render Environment Variables

Set these in the Render service environment:

```text
FLASK_ENV=production
FLASK_DEBUG=false
FLASK_HOST=0.0.0.0
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_SERVICE_ACCOUNT_BASE64=your-base64-service-account-json
JWT_SECRET_KEY=use-a-long-random-production-secret
JWT_ACCESS_TOKEN_EXPIRES_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRES_DAYS=30
EMAIL_PROVIDER=gmail
EMAIL_FROM=your-gmail-address@gmail.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-gmail-address@gmail.com
SMTP_PASSWORD=your-gmail-app-password
```

Use a production-safe start command such as:

```bash
gunicorn run:app
```

## Verify Existing Backend

```bash
curl http://127.0.0.1:5000/health
curl http://127.0.0.1:5000/firestore-test
```

## Postman Examples

### 1. Register

Method:

```text
POST
```

URL:

```text
http://127.0.0.1:5000/api/auth/register
```

Headers:

```text
Content-Type: application/json
```

Body:

```json
{
  "name": "Alex Johnson",
  "email": "alex@example.com",
  "mobileNumber": "+919876543210",
  "password": "StrongPass123"
}
```

Success response:

```json
{
  "ok": true,
  "message": "Registration created. Verification OTP sent to email.",
  "user": {
    "userId": "...",
    "email": "alex@example.com",
    "emailVerified": false
  }
}
```

Firestore writes:

- `users/{userId}`
- `otp_codes/{otpId}`

### 2. Verify Email OTP

Method:

```text
POST
```

URL:

```text
http://127.0.0.1:5000/api/auth/verify-email-otp
```

Headers:

```text
Content-Type: application/json
```

Body:

```json
{
  "email": "alex@example.com",
  "otp": "123456"
}
```

Success response:

```json
{
  "ok": true,
  "message": "Email verified successfully.",
  "user": {
    "userId": "...",
    "email": "alex@example.com",
    "emailVerified": true
  }
}
```

Verification behavior:

- Checks that the OTP exists.
- Checks that `purpose` is `register`.
- Checks that the OTP has not expired.
- Marks `users/{userId}.emailVerified` as `true`.
- Deletes the OTP document so it cannot be reused.

### 3. Login

Method:

```text
POST
```

URL:

```text
http://127.0.0.1:5000/api/auth/login
```

Headers:

```text
Content-Type: application/json
```

Body:

```json
{
  "email": "alex@example.com",
  "password": "StrongPass123"
}
```

Success response:

```json
{
  "ok": true,
  "message": "Login successful.",
  "user": {
    "userId": "...",
    "name": "Alex Johnson",
    "email": "alex@example.com",
    "mobileNumber": "+919876543210",
    "emailVerified": true
  },
  "tokens": {
    "accessToken": "...",
    "refreshToken": "...",
    "expiresIn": 3600
  }
}
```

If the user exists but has not verified email:

```json
{
  "ok": false,
  "error": "Email is not verified."
}
```

### 4. Refresh Token

Method:

```text
POST
```

URL:

```text
http://127.0.0.1:5000/api/auth/refresh-token
```

Headers:

```text
Content-Type: application/json
```

Body:

```json
{
  "refreshToken": "..."
}
```

Success response:

```json
{
  "ok": true,
  "accessToken": "..."
}
```

### 5. Logout

Method:

```text
POST
```

URL:

```text
http://127.0.0.1:5000/api/auth/logout
```

Headers:

```text
Content-Type: application/json
```

Body:

```json
{
  "refreshToken": "..."
}
```

Success response:

```json
{
  "ok": true,
  "message": "Logged out successfully."
}
```

Logout marks the matching `user_sessions/{sessionId}` document as inactive.

## Error Responses

Duplicate email:

```json
{
  "ok": false,
  "error": "Email already exists."
}
```

Duplicate mobile:

```json
{
  "ok": false,
  "error": "Mobile number already exists."
}
```

Validation error:

```json
{
  "ok": false,
  "error": "Validation failed.",
  "details": {
    "email": "Enter a valid email address."
  }
}
```

Invalid OTP:

```json
{
  "ok": false,
  "error": "Invalid OTP."
}
```

Expired OTP:

```json
{
  "ok": false,
  "error": "OTP expired."
}
```

## Not Implemented Yet

The following are intentionally deferred to later milestones:

- Forgot password
- SMS OTP
- WhatsApp
- Cloudinary uploads
- OCR
- AI
- Flutter integration
