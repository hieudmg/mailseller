import httpx
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class RecaptchaService:
    """Service for verifying Google reCAPTCHA v2 tokens"""

    def __init__(self):
        self.secret_key = settings.RECAPTCHA_SECRET_KEY
        self.verify_url = settings.RECAPTCHA_VERIFY_URL
        self.enabled = settings.RECAPTCHA_ENABLED

    async def verify_token(
        self, token: str, remote_ip: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Verify a reCAPTCHA token with Google's API

        Args:
            token: The reCAPTCHA response token from the client
            remote_ip: Optional IP address of the user

        Returns:
            tuple: (is_valid: bool, error_message: Optional[str])
        """
        # If reCAPTCHA is disabled, always return success
        if not self.enabled:
            logger.info("reCAPTCHA verification skipped (disabled)")
            return True, None

        # Check if secret key is configured
        if not self.secret_key:
            logger.error("reCAPTCHA secret key not configured")
            return False, "reCAPTCHA not configured"

        # Validate token is provided
        if not token:
            logger.warning("reCAPTCHA token not provided")
            return False, "reCAPTCHA token required"

        try:
            # Prepare request data
            data = {
                "secret": self.secret_key,
                "response": token,
            }

            # Add remote IP if provided
            if remote_ip:
                data["remoteip"] = remote_ip

            # Make verification request to Google
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.verify_url,
                    data=data,
                    timeout=10.0,
                )

                # Check if request was successful
                if response.status_code != 200:
                    logger.error(
                        f"reCAPTCHA API returned status {response.status_code}"
                    )
                    return False, "reCAPTCHA verification failed"

                # Parse response
                result = response.json()

                # Check if verification was successful
                if result.get("success"):
                    logger.info("reCAPTCHA verification successful")
                    return True, None
                else:
                    # Log error codes
                    error_codes = result.get("error-codes", [])
                    logger.warning(f"reCAPTCHA verification failed: {error_codes}")

                    # Return user-friendly error message
                    error_message = self._get_error_message(error_codes)
                    return False, error_message

        except httpx.TimeoutException:
            logger.error("reCAPTCHA verification timeout")
            return False, "reCAPTCHA verification timeout"
        except httpx.RequestError as e:
            logger.error(f"reCAPTCHA verification request error: {str(e)}")
            return False, "reCAPTCHA verification failed"
        except Exception as e:
            logger.error(f"Unexpected error during reCAPTCHA verification: {str(e)}")
            return False, "reCAPTCHA verification failed"

    def _get_error_message(self, error_codes: list[str]) -> str:
        """
        Convert reCAPTCHA error codes to user-friendly messages

        Error codes documentation:
        https://developers.google.com/recaptcha/docs/verify#error_code_reference
        """
        error_messages = {
            "missing-input-secret": "reCAPTCHA configuration error",
            "invalid-input-secret": "reCAPTCHA configuration error",
            "missing-input-response": "Please complete the reCAPTCHA verification",
            "invalid-input-response": "Invalid reCAPTCHA response, please try again",
            "bad-request": "reCAPTCHA verification failed",
            "timeout-or-duplicate": "reCAPTCHA expired or already used, please try again",
        }

        # Return first matching error message
        for code in error_codes:
            if code in error_messages:
                return error_messages[code]

        # Default error message
        return "reCAPTCHA verification failed, please try again"


# Singleton instance
recaptcha_service = RecaptchaService()
