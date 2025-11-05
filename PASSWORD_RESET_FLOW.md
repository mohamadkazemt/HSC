# Emergency Portal Password Reset Flow

## Visual Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Emergency Login Page                        │
│                  /emergency/login/                              │
│                                                                 │
│  [Username Field]                                              │
│  [Password Field]                                              │
│  [Forgot Password Link] ────────┐                             │
│  [Login Button]                  │                             │
└──────────────────────────────────┼──────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│              Password Reset Request Page                        │
│            /emergency/password-reset/                          │
│                                                                 │
│  📧 Enter Your Email Address                                   │
│  [Email Input Field]                                           │
│  [Send Reset Link Button]                                      │
│  [Back to Login Link]                                          │
└──────────────────────────────────┬──────────────────────────────┘
                                   │
                                   │ POST (email)
                                   │
                                   ▼
                      ┌────────────────────────┐
                      │    Backend Validation   │
                      │  - Check if email exists│
                      │  - Verify emergency role│
                      │  - Generate reset token │
                      │  - Send email with link │
                      └────────────┬────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│              Email Sent Confirmation Page                       │
│          /emergency/password-reset/done/                       │
│                                                                 │
│  ✅ Email Sent!                                                │
│  Check your inbox for the reset link                           │
│  [Back to Login Link]                                          │
└─────────────────────────────────────────────────────────────────┘

                           ║
                           ║ User receives email
                           ║
                           ▼
                    ┌─────────────┐
                    │  📧 Email    │
                    │  With Link   │
                    │  (24h valid) │
                    └──────┬───────┘
                           │ Click link
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│           Password Reset Confirm Page                           │
│    /emergency/password-reset-confirm/<uidb64>/<token>/        │
│                                                                 │
│  IF TOKEN VALID:                                               │
│    🔒 Set New Password                                         │
│    [New Password Field]                                        │
│    [Confirm Password Field]                                    │
│    [Set Password Button]                                       │
│                                                                 │
│  IF TOKEN INVALID:                                             │
│    ⚠️  Link Expired/Invalid                                    │
│    [Request New Link Button]                                   │
└──────────────────────────────────┬──────────────────────────────┘
                                   │
                                   │ POST (new password)
                                   │
                                   ▼
                      ┌────────────────────────┐
                      │  Backend Processing     │
                      │  - Validate password    │
                      │  - Hash new password    │
                      │  - Update user record   │
                      │  - Invalidate token     │
                      └────────────┬────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│              Password Reset Complete Page                       │
│          /emergency/password-reset-complete/                   │
│                                                                 │
│  ✅ Success!                                                    │
│  Your password has been reset                                  │
│  [Login Now Button]                                            │
│                                                                 │
│  Auto-redirect to login in 5 seconds...                        │
└──────────────────────────────────┬──────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Emergency Login Page                        │
│                  /emergency/login/                              │
│                                                                 │
│  Login with new password                                       │
└─────────────────────────────────────────────────────────────────┘
```

## URL Routes

| Route | View | Template | Purpose |
|-------|------|----------|---------|
| `/emergency/password-reset/` | `emergency_password_reset_view` | `emergency_password_reset.html` | Request reset |
| `/emergency/password-reset/done/` | `emergency_password_reset_done_view` | `emergency_password_reset_done.html` | Confirm email sent |
| `/emergency/password-reset-confirm/<uidb64>/<token>/` | `PasswordResetConfirmView` | `emergency_password_reset_confirm.html` | Set new password |
| `/emergency/password-reset-complete/` | `PasswordResetCompleteView` | `emergency_password_reset_complete.html` | Success message |

## Security Measures

1. **Token-Based**: Uses Django's secure token generator
2. **Time-Limited**: Tokens expire after 24 hours
3. **Role-Based**: Only emergency personnel can reset
4. **Email Verification**: Requires valid email address
5. **CSRF Protected**: All forms include CSRF tokens
6. **Password Validation**: Enforces Django's password validators
7. **One-Time Use**: Tokens invalidated after use

## Error Handling

### User Not Found
- Shows generic message (security best practice)
- Prevents user enumeration attacks
- "If this email exists, a reset link will be sent"

### Invalid/Expired Token
- Clear error message
- Option to request new link
- Redirects to password reset page

### Email Send Failure
- Catches exceptions
- Shows error message to user
- Logs error for admin review

## Email Template

The system sends a plain-text email containing:
```
Subject: بازیابی رمز عبور - پورتال اورژانس

سلام {user_name},

درخواست بازیابی رمز عبور برای حساب کاربری شما در پورتال اورژانس دریافت شد.

برای تنظیم رمز عبور جدید، لطفاً روی لینک زیر کلیک کنید:

{reset_url}

این لینک فقط برای ۲۴ ساعت معتبر است.

اگر این درخواست را نداده‌اید، لطفاً این ایمیل را نادیده بگیرید.

با تشکر،
تیم پورتال اورژانس
```

## Database Changes

No database migrations required! The feature uses:
- Existing User model
- Existing Group model (EmergencyManager, EmergencyDoctor, EmergencyNurse)
- No new tables needed

## Dependencies

- `django.contrib.auth` - Authentication framework
- `django.contrib.auth.tokens` - Token generation
- `django.core.mail` - Email sending
- `django.utils.http` - URL encoding
- `django.utils.encoding` - Secure encoding
