# Emergency Portal Password Reset Feature

## Overview
Comprehensive password reset functionality has been implemented for the Emergency Portal, allowing emergency personnel to securely reset their passwords via email.

## Components

### 1. Views (emergency_services/views.py)
- `emergency_password_reset_view()` - Initial password reset request form
- `emergency_password_reset_done_view()` - Confirmation that email was sent
- Django's built-in `PasswordResetConfirmView` - Password reset confirmation
- Django's built-in `PasswordResetCompleteView` - Success page

### 2. URLs (emergency_services/urls.py)
```
/emergency/password-reset/                    - Request password reset
/emergency/password-reset/done/               - Confirmation page
/emergency/password-reset-confirm/<uidb64>/<token>/ - Set new password
/emergency/password-reset-complete/           - Success page
```

### 3. Templates
All templates use consistent emergency portal styling with Tailwind CSS:

- **emergency_password_reset.html** - Email input form
- **emergency_password_reset_done.html** - Email sent confirmation
- **emergency_password_reset_confirm.html** - New password form with validation
- **emergency_password_reset_complete.html** - Success page with auto-redirect

### 4. Security Features
- Email verification required
- Only emergency personnel (EmergencyManager, EmergencyDoctor, EmergencyNurse) can reset passwords
- Tokens expire after 24 hours
- Password strength validation
- Secure token generation using Django's built-in system

## User Flow

1. **Forgot Password**: User clicks "فراموشی رمز عبور؟" on login page
2. **Enter Email**: User enters their registered email address
3. **Email Sent**: System sends password reset link to email
4. **Click Link**: User clicks the link in email
5. **Set Password**: User enters and confirms new password
6. **Success**: Password reset complete, auto-redirect to login after 5 seconds

## Email Configuration

The system uses Django's email backend. Ensure these settings are configured in `settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.your-provider.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-password'
DEFAULT_FROM_EMAIL = 'noreply@your-domain.com'
```

For development, you can use console backend:
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

## Testing

### Manual Testing
1. Navigate to http://localhost:8000/emergency/login/
2. Click "فراموشی رمز عبور؟"
3. Enter a valid emergency personnel email
4. Check console (development) or email inbox (production) for reset link
5. Click link and set new password
6. Login with new password

### Required Data
- Emergency personnel user with valid email address
- User must be in one of these groups:
  - EmergencyManager
  - EmergencyDoctor
  - EmergencyNurse

## Design Features

### Consistent Branding
- Red emergency gradient color scheme
- Ambulance/medical icons
- Persian (Farsi) language support
- RTL layout
- Vazirmatn font family

### User Experience
- Clear step-by-step flow
- Animated success indicators
- Auto-redirect after success
- Helpful error messages
- Password match validation
- Responsive design

## Integration

The password reset feature is fully integrated with:
- Emergency login page (link provided)
- Emergency portal styling
- Role-based authentication system
- Existing permission system

## Future Enhancements

Potential improvements:
- SMS-based password reset option
- Two-factor authentication
- Password reset history logging
- Admin notification on password resets
- Custom email templates with HTML
- Rate limiting for reset requests
