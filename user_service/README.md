# 🧑‍💼 User Service

**Responsible for user authentication, profile management, and security.**

---

### Features

- ✅ **JWT Authentication**  
  Implements Access and Refresh tokens stored securely in HTTP-only cookies and managed via Redis.

- 🔐 **User Login, Registration, Refresh and Logout**  
  Full lifecycle authentication with secure password hashing and validation.

- 🙍‍♂️ **User Profile Management**  
  View and update user details with validation and authorization checks.

- 🛠️ **User Management for Superadmin**  
   Full CRUD access to manage users, assign roles, and perform administrative actions available only to Superadmin.

- 📬 **Password Reset via Email**  
  Generates time-limited reset tokens stored in Redis, sends emails asynchronously through Kafka → Notification Service.

- ⚠️ **Rate Limiting**  
  Protects critical endpoints using Redis-backed rate limiter to prevent abuse.

- 📜 **Centralized Logging**  
  All user-related events and errors are logged asynchronously to Kafka and consumed by Log Service.

- 🧪 **Comprehensive Testing**  
  Fully covered with unit tests using `pytest` and `unittest.mock` for dependencies and external calls.

---

## 📚 API Documentation

All API endpoints are documented and accessible via **Swagger UI**:

```
http://localhost:<SERVICE_PORT>/docs
```

---
