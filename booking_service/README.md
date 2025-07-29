# 📅 Booking Service

**Handles car reservations.**

---

### Features

- 🗓️ **Booking Creation with Availability Check**  
  Interacts with the Car Service via gRPC to verify availability before confirming reservations.

- 🔍 **User Booking Management**  
  Authenticated users can view and delete their own bookings.

- 🛠️ **Admin CRUD for Bookings**  
  Full access for administrators to create, update, and delete any booking.

- 📜 **Centralized Logging**  
  All booking-related events are sent asynchronously to Kafka for processing.

- 🧪 **Tested with Pytest**  
  Covered by unit tests using `pytest` and mock dependencies for isolation.

---

## 📚 API Documentation

All API endpoints are documented and accessible via **Swagger UI**:

```
http://localhost:<SERVICE_PORT>/docs
```

---
