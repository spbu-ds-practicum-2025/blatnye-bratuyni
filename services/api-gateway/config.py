import os

USER_SERVICE_URL = os.environ.get("USER_SERVICE_URL", "http://user-service:8001")
BOOKING_SERVICE_URL = os.environ.get("BOOKING_SERVICE_URL", "http://booking-service:8002")
NOTIFICATION_SERVICE_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://notification-service:8003")
SECRET_KEY = os.environ.get("JWT_SECRET", "a-string-secret-at-least-256-bits-long")