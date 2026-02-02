# app/core/password_validation.py
"""
Password strength validation utilities.
Implements NIST/OWASP guidelines for secure passwords.
"""
import re
from typing import List, Dict, Optional
from pydantic import BaseModel


class PasswordValidationError(BaseModel):
    """Password validation error details"""
    code: str
    message: str


class PasswordValidationResult(BaseModel):
    """Result of password validation"""
    is_valid: bool
    errors: List[PasswordValidationError]
    strength_score: int  # 0-100
    suggestions: List[str]


def validate_password_strength(password: str) -> PasswordValidationResult:
    """
    Validate password strength according to security best practices.

    Requirements:
    - Minimum 12 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 number
    - At least 1 special character
    - No common weak patterns

    Args:
        password: Password to validate

    Returns:
        PasswordValidationResult with validation details
    """
    errors = []
    suggestions = []
    score = 0

    # Basic length check (minimum 12 characters)
    if len(password) < 12:
        errors.append(PasswordValidationError(
            code="min_length",
            message="Password must be at least 12 characters long"
        ))
    else:
        score += 20

    # Length bonus scoring
    if len(password) >= 16:
        score += 10
    if len(password) >= 20:
        score += 10

    # Uppercase letter requirement
    if not re.search(r'[A-Z]', password):
        errors.append(PasswordValidationError(
            code="missing_uppercase",
            message="Password must contain at least one uppercase letter (A-Z)"
        ))
        suggestions.append("Add at least one uppercase letter")
    else:
        score += 15

    # Lowercase letter requirement
    if not re.search(r'[a-z]', password):
        errors.append(PasswordValidationError(
            code="missing_lowercase",
            message="Password must contain at least one lowercase letter (a-z)"
        ))
        suggestions.append("Add at least one lowercase letter")
    else:
        score += 15

    # Number requirement
    if not re.search(r'\d', password):
        errors.append(PasswordValidationError(
            code="missing_number",
            message="Password must contain at least one number (0-9)"
        ))
        suggestions.append("Add at least one number")
    else:
        score += 15

    # Special character requirement
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append(PasswordValidationError(
            code="missing_special",
            message="Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)"
        ))
        suggestions.append("Add at least one special character")
    else:
        score += 15

    # Check for common weak patterns
    weak_patterns = [
        (r'(.)\1{2,}', "repeated_characters", "Avoid repeating the same character multiple times"),
        (r'(012|123|234|345|456|567|678|789|890)', "sequential_numbers", "Avoid sequential numbers"),
        (r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', "sequential_letters", "Avoid sequential letters"),
        (r'(qwer|asdf|zxcv|qwerty|asdfgh|zxcvbn)', "keyboard_patterns", "Avoid keyboard patterns"),
    ]

    for pattern, code, message in weak_patterns:
        if re.search(pattern, password.lower()):
            errors.append(PasswordValidationError(
                code=code,
                message=f"Password contains weak pattern: {message}"
            ))
            score = max(0, score - 10)  # Penalty for weak patterns

    # Check for common passwords (basic list)
    common_passwords = {
        'password', 'password123', '123456789', 'qwerty123', 'admin123',
        'welcome123', 'letmein123', 'password1', 'abc123456', 'qwerty1234'
    }

    if password.lower() in common_passwords:
        errors.append(PasswordValidationError(
            code="common_password",
            message="Password is too common and easily guessable"
        ))
        suggestions.append("Use a unique password not found in common password lists")
        score = max(0, score - 20)

    # Character variety bonus
    char_types = 0
    if re.search(r'[A-Z]', password):
        char_types += 1
    if re.search(r'[a-z]', password):
        char_types += 1
    if re.search(r'\d', password):
        char_types += 1
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        char_types += 1

    if char_types >= 4:
        score += 10

    # Cap the score at 100
    score = min(score, 100)

    # Add general suggestions if password is weak
    if score < 60:
        suggestions.extend([
            "Consider using a passphrase with multiple words",
            "Mix uppercase and lowercase letters throughout",
            "Use numbers and symbols in meaningful ways"
        ])

    is_valid = len(errors) == 0

    return PasswordValidationResult(
        is_valid=is_valid,
        errors=errors,
        strength_score=score,
        suggestions=suggestions
    )


def get_password_requirements_text() -> str:
    """
    Get a user-friendly description of password requirements.

    Returns:
        String describing password requirements
    """
    return (
        "Password must be at least 12 characters long and contain:\n"
        "• At least one uppercase letter (A-Z)\n"
        "• At least one lowercase letter (a-z)\n"
        "• At least one number (0-9)\n"
        "• At least one special character (!@#$%^&*(),.?\":{}|<>)\n"
        "• No common patterns or dictionary words"
    )