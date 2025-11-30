# Scheduled Checklist Enforcement System - Implementation Summary

## Overview

This document describes the implementation of a comprehensive "Scheduled Checklist Enforcement" system for the Django project. The system includes monthly scheduling, shift-based assignment, blocking mechanisms, and machine condition logic.

## Features Implemented

### 1. Monthly Scheduling System

**Models:**
- `ChecklistSchedule`: Defines when specific checklists must be filled
  - Supports monthly days (e.g., 1st and 15th of every month)
  - Supports specific dates
  - Supports weekly scheduling
  - Targets specific Machines, Locations, or Checklist Types

- `ScheduledChecklistInstance`: Tracks individual scheduled checklist instances
  - Status: `pending`, `completed`, `skipped`
  - Links to completed Checklist records
  - Prevents double submission with race condition handling

**Location:** `checklist_app/models.py`

### 2. Shift-Based Assignment & "First-to-Claim" Logic

**Helper Functions:**
- `get_users_on_shift(target_date, shift_name)`: Identifies Safety Inspectors on a specific shift
- `get_pending_scheduled_checklists(user, target_date)`: Gets pending tasks for a user
- `claim_scheduled_checklist(instance_id, user)`: Implements first-to-claim logic with race condition protection

**Race Condition Protection:**
- Uses `select_for_update()` with database transactions
- Prevents double submission when two inspectors try to complete the same checklist simultaneously

**Location:** `checklist_app/services.py`

### 3. Blocking End-of-Shift Report

**Integration:**
- `check_pending_tasks(user, target_date)`: Checks if user has pending scheduled checklists
- Integrated into `dailyreport_hse/views.py`:
  - `CreateDailyReportView.post()`: Blocks report submission if pending checklists exist
  - `DailyReportFormView.get_context_data()`: Shows pending checklists in form context

**Error Messages:**
- Provides clear error messages listing which checklists are missing
- Returns structured error response with pending task details

**Location:** `dailyreport_hse/views.py`, `checklist_app/services.py`

### 4. Machine Condition Logic (Breakdown vs. Healthy)

**Model Changes:**
- Added `machine_status` field to `Checklist` model:
  - Choices: `healthy` (سالم), `broken` (خراب/در حال تعمیر)
  - Required for machine checklists only

**View Updates:**
- `get_general_questions()`: Checks machine status before loading questions
  - If `broken`: Returns empty questions list with special flag
  - If `healthy`: Loads all checklist questions normally

- `submit_general_checklist()`: Handles machine status
  - Validates machine_status is provided for machine checklists
  - If broken: Allows immediate submission without questions
  - If healthy: Requires all questions to be answered

**Location:** `checklist_app/models.py`, `checklist_app/views.py`

## Database Schema Changes

### New Models

1. **ChecklistSchedule**
   - `name`: Name of the schedule
   - `checklist_type`: Type of checklist (machine/location/contractor_vehicle)
   - `schedule_type`: monthly_days/specific_dates/weekly
   - `monthly_days`: JSONField for days of month (e.g., [1, 15])
   - `specific_dates`: JSONField for specific dates
   - `target_machine`, `target_location_section`, `target_contractor_vehicle`: Target entities
   - `is_active`: Enable/disable schedule

2. **ScheduledChecklistInstance**
   - `schedule`: ForeignKey to ChecklistSchedule
   - `due_date`: Date when checklist is due
   - `status`: pending/completed/skipped
   - `completed_by`: User who completed it
   - `completed_at`: Timestamp of completion
   - Unique constraint: (schedule, due_date)

### Modified Models

1. **Checklist**
   - Added `machine_status`: CharField (healthy/broken)
   - Added `scheduled_instance`: ForeignKey to ScheduledChecklistInstance

## API Endpoints

### New Endpoints

1. **GET/POST `/checklist_app/api/pending-tasks/`**
   - Returns pending scheduled checklists for current user
   - Used by daily report form to check before submission

2. **GET `/checklist_app/pending-scheduled/`**
   - View page showing pending scheduled checklists
   - For Safety Inspectors to see their tasks

### Modified Endpoints

1. **POST `/checklist_app/get-questions/`**
   - Now accepts `machine_status` parameter
   - Returns empty questions if machine is broken

2. **POST `/checklist_app/submit-checklist/`**
   - Now accepts `machine_status` and `scheduled_instance_id`
   - Handles machine status validation
   - Claims scheduled instance atomically

## Management Commands

### `create_scheduled_instances`

Creates scheduled checklist instances for today and future dates.

**Usage:**
```bash
python manage.py create_scheduled_instances
python manage.py create_scheduled_instances --days-ahead 7
python manage.py create_scheduled_instances --date 2024-12-25
```

**Recommendation:** Run daily via cron job to create instances for upcoming dates.

## How to Use

### 1. Create a Schedule

1. Go to Django Admin → Checklist Schedules
2. Create a new schedule:
   - Set name, checklist type, schedule type
   - For monthly: Set `monthly_days` (e.g., [1, 15])
   - For specific dates: Set `specific_dates` (e.g., ["2024-12-25", "2025-01-01"])
   - Select target machine/location/vehicle
   - Activate the schedule

### 2. Generate Instances

Run the management command daily:
```bash
python manage.py create_scheduled_instances --days-ahead 30
```

### 3. Safety Inspectors See Tasks

- Safety Inspectors on Day Shift will see pending scheduled checklists
- They can access via `/checklist_app/pending-scheduled/`
- When completing a checklist, they select the scheduled instance

### 4. First-to-Claim Logic

- When Inspector A completes a scheduled checklist, it's marked as completed
- Inspector B's task list automatically updates (no longer shows the completed task)
- Race conditions are handled with database-level locking

### 5. Daily Report Blocking

- When a Safety Inspector tries to submit a daily report
- System checks for pending scheduled checklists
- If found, submission is blocked with error message listing missing checklists
- Inspector must complete scheduled checklists first

## Database Migrations

**You must run migrations to create the new models:**

```bash
python manage.py makemigrations checklist_app
python manage.py migrate checklist_app
```

## Thread Safety

The implementation uses:
- `select_for_update()` for row-level locking
- Database transactions (`@transaction.atomic`)
- Unique constraints to prevent duplicates

This ensures thread-safe operation even with concurrent requests.

## Integration with shift_manager

The system integrates with `shift_manager` app:
- Uses `get_shift_for_date()` to determine which groups are on Day Shift
- Uses `get_active_groups_for_current_shift()` for current shift detection
- Identifies Safety Inspectors by position: `position__name='بازرس شیفت ایمنی'`

## Testing Recommendations

1. **Test Schedule Creation:**
   - Create a monthly schedule for days 1 and 15
   - Run `create_scheduled_instances` command
   - Verify instances are created correctly

2. **Test First-to-Claim:**
   - Create two users as Safety Inspectors on same shift
   - Create a pending scheduled checklist
   - Have both users try to complete it simultaneously
   - Verify only one succeeds

3. **Test Daily Report Blocking:**
   - Create a pending scheduled checklist
   - Try to submit daily report
   - Verify blocking with error message
   - Complete the checklist
   - Verify daily report can now be submitted

4. **Test Machine Status:**
   - Create a machine checklist
   - Select "Broken" status
   - Verify no questions are shown
   - Submit checklist
   - Verify it's saved with broken status

## Files Modified/Created

### Created Files:
- `checklist_app/services.py` - Helper functions
- `checklist_app/management/commands/create_scheduled_instances.py` - Management command
- `SCHEDULED_CHECKLIST_IMPLEMENTATION.md` - This document

### Modified Files:
- `checklist_app/models.py` - Added new models and fields
- `checklist_app/views.py` - Updated views for machine status and scheduled checklists
- `checklist_app/urls.py` - Added new URL patterns
- `checklist_app/admin.py` - Registered new models
- `dailyreport_hse/views.py` - Integrated blocking mechanism

## Notes

- The system maintains backward compatibility with ad-hoc checklists
- Scheduled checklists are optional - existing functionality continues to work
- Machine status is only required for machine-type checklists
- The system assumes Safety Inspectors have position name: 'بازرس شیفت ایمنی'

## Future Enhancements (Optional)

1. Email/SMS notifications for pending scheduled checklists
2. Dashboard widget showing pending tasks count
3. Bulk schedule creation interface
4. Schedule templates
5. Recurring schedule patterns (e.g., every 2 weeks)

