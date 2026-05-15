## Summary
This PR adds a user authentication module with JWT-based login, registration, and token refresh endpoints. It includes password hashing with bcrypt and middleware for route protection.

## Risks
- JWT secret is read from env but no rotation mechanism is documented
- Password reset endpoint lacks rate limiting — vulnerable to abuse
- Token refresh doesn't invalidate old tokens (token replay possible)

## Suggestions
- Add rate limiting to /auth/login and /auth/register endpoints
- Implement token blacklisting for logout functionality
- Add input validation with a schema library (zod/joi) for all auth payloads
- Consider adding a password strength requirement

## Confidence: Medium
