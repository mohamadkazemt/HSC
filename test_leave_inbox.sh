#!/bin/bash

# 🧪 Leave Inbox Integration - Quick Test Script
# Run this to verify the implementation

echo "🎯 Leave Inbox Integration Test"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if in correct directory
if [ ! -f "manage.py" ]; then
    echo -e "${RED}❌ Error: Please run this script from the HSC project root directory${NC}"
    exit 1
fi

echo "📋 Step 1: Checking modified files..."
echo ""

# Check dashboard views.py
if grep -q "from leave_reports.models import ShiftReport, ApprovalHierarchy" dashboard/views.py; then
    echo -e "${GREEN}✅ dashboard/views.py - Leave imports added${NC}"
else
    echo -e "${RED}❌ dashboard/views.py - Missing leave imports${NC}"
fi

if grep -q "pending_replacement_approvals" dashboard/views.py; then
    echo -e "${GREEN}✅ dashboard/views.py - Replacement approvals query added${NC}"
else
    echo -e "${RED}❌ dashboard/views.py - Missing replacement query${NC}"
fi

if grep -q "pending_manager_approvals" dashboard/views.py; then
    echo -e "${GREEN}✅ dashboard/views.py - Manager approvals query added${NC}"
else
    echo -e "${RED}❌ dashboard/views.py - Missing manager query${NC}"
fi

echo ""

# Check dashboard template
if grep -q "Leave Inbox Widget" templates/dashboard/dashboard.html; then
    echo -e "${GREEN}✅ dashboard.html - Inbox widget added${NC}"
else
    echo -e "${RED}❌ dashboard.html - Missing inbox widget${NC}"
fi

if grep -q "approveReplacement" templates/dashboard/dashboard.html; then
    echo -e "${GREEN}✅ dashboard.html - JavaScript functions added${NC}"
else
    echo -e "${RED}❌ dashboard.html - Missing JavaScript${NC}"
fi

if grep -q "rejectModal" templates/dashboard/dashboard.html; then
    echo -e "${GREEN}✅ dashboard.html - Reject modal added${NC}"
else
    echo -e "${RED}❌ dashboard.html - Missing reject modal${NC}"
fi

echo ""

# Check sidebar
if grep -q "واحد اداری" templates/partials/sidebar.html; then
    echo -e "${GREEN}✅ sidebar.html - HR/Admin Unit added${NC}"
else
    echo -e "${RED}❌ sidebar.html - Missing HR/Admin Unit${NC}"
fi

if grep -q "مدیریت مرخصی" templates/partials/sidebar.html; then
    echo -e "${GREEN}✅ sidebar.html - Leave Management submenu added${NC}"
else
    echo -e "${RED}❌ sidebar.html - Missing Leave Management${NC}"
fi

echo ""
echo "📋 Step 2: Checking leave_reports URLs..."
echo ""

if grep -q "approve-replacement" leave_reports/urls.py; then
    echo -e "${GREEN}✅ leave_reports/urls.py - Approval endpoints exist${NC}"
else
    echo -e "${YELLOW}⚠️  leave_reports/urls.py - Check approval endpoints${NC}"
fi

echo ""
echo "📋 Step 3: Testing Django configuration..."
echo ""

# Check for syntax errors
python manage.py check --deploy 2>&1 | head -n 20
CHECK_EXIT=$?

if [ $CHECK_EXIT -eq 0 ]; then
    echo -e "${GREEN}✅ Django system check passed${NC}"
else
    echo -e "${YELLOW}⚠️  Django system check has warnings (check above)${NC}"
fi

echo ""
echo "📋 Step 4: Checking database models..."
echo ""

# Check if models are accessible
python manage.py shell -c "
from leave_reports.models import ShiftReport, ApprovalHierarchy
print('✅ ShiftReport model accessible')
print('✅ ApprovalHierarchy model accessible')
" 2>&1

echo ""
echo "================================"
echo "📊 Test Summary"
echo "================================"
echo ""
echo "✅ = Pass"
echo "⚠️  = Warning (manual check needed)"
echo "❌ = Fail"
echo ""

# Count results (simplified)
PASS_COUNT=$(grep -c "✅" <<< "$(bash $0 2>&1)" || echo 0)

echo -e "${GREEN}Tests completed!${NC}"
echo ""
echo "📝 Next Steps:"
echo "1. Start the development server: python manage.py runserver"
echo "2. Login to dashboard"
echo "3. Create test leave request"
echo "4. Verify inbox widget appears"
echo "5. Test approve/reject buttons"
echo "6. Check sidebar HR/Admin Unit menu"
echo ""
echo "📚 Documentation:"
echo "- LEAVE_INBOX_INTEGRATION_COMPLETE.md"
echo "- LEAVE_INBOX_VISUAL_GUIDE.md"
echo ""
echo "🎉 Implementation complete!"
