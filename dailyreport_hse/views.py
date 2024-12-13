from django.shortcuts import render, redirect
from .forms import (
    DailyReportForm,
    BlastingDetailFormset,
    DrillingDetailFormset,
    DumpDetailFormset,
    LoadingDetailFormset,
    InspectionDetailForm,
    StoppageDetailForm,
    FollowupDetailForm,
)
from .models import DailyReport


def create_daily_report(request):
    """
    Manage daily report steps.
    """
    # Determine current step
    step = int(request.GET.get("step", 1))

    if request.method == "POST":
        # Update step based on form submission
        step = int(request.POST.get("step", step))

        if step == 1:
            blasting_formset = BlastingDetailFormset(request.POST, queryset=None, prefix="blasting")
            if blasting_formset.is_valid():
                # Save blasting details
                blasting_formset.save()
                return redirect(f"{request.path}?step=2")

        elif step == 2:
            drilling_formset = DrillingDetailFormset(request.POST, queryset=None, prefix="drilling")
            if drilling_formset.is_valid():
                drilling_formset.save()
                return redirect(f"{request.path}?step=3")

        elif step == 3:
            dump_formset = DumpDetailFormset(request.POST, queryset=None, prefix="dump")
            if dump_formset.is_valid():
                dump_formset.save()
                return redirect(f"{request.path}?step=4")

        elif step == 4:
            loading_formset = LoadingDetailFormset(request.POST, queryset=None, prefix="loading")
            if loading_formset.is_valid():
                loading_formset.save()
                return redirect(f"{request.path}?step=5")

        elif step == 5:
            inspection_form = InspectionDetailForm(request.POST, prefix="inspection")
            if inspection_form.is_valid():
                inspection_form.save()
                return redirect(f"{request.path}?step=6")

        elif step == 6:
            stoppage_form = StoppageDetailForm(request.POST, prefix="stoppage")
            if stoppage_form.is_valid():
                stoppage_form.save()
                return redirect(f"{request.path}?step=7")

        elif step == 7:
            followup_form = FollowupDetailForm(request.POST, request.FILES, prefix="followup")
            if followup_form.is_valid():
                followup_form.save()
                return redirect("hsec:report_success")

    # Render the appropriate step
    if step == 1:
        blasting_formset = BlastingDetailFormset(queryset=None, prefix="blasting")
        return render(request, 'dailyreport_hse/new-report.html', {
            'step': step,
            'blasting_formset': blasting_formset,
        })

    elif step == 2:
        drilling_formset = DrillingDetailFormset(queryset=None, prefix="drilling")
        return render(request, 'dailyreport_hse/new-report.html', {
            'step': step,
            'drilling_formset': drilling_formset,
        })

    elif step == 3:
        dump_formset = DumpDetailFormset(queryset=None, prefix="dump")
        return render(request, 'dailyreport_hse/new-report.html', {
            'step': step,
            'dump_formset': dump_formset,
        })

    elif step == 4:
        loading_formset = LoadingDetailFormset(queryset=None, prefix="loading")
        return render(request, 'dailyreport_hse/new-report.html', {
            'step': step,
            'loading_formset': loading_formset,
        })

    elif step == 5:
        inspection_form = InspectionDetailForm(prefix="inspection")
        return render(request, 'dailyreport_hse/new-report.html', {
            'step': step,
            'inspection_form': inspection_form,
        })

    elif step == 6:
        stoppage_form = StoppageDetailForm(prefix="stoppage")
        return render(request, 'dailyreport_hse/new-report.html', {
            'step': step,
            'stoppage_form': stoppage_form,
        })

    elif step == 7:
        followup_form = FollowupDetailForm(prefix="followup")
        return render(request, 'dailyreport_hse/new-report.html', {
            'step': step,
            'followup_form': followup_form,
        })

    return redirect(f"{request.path}?step=1")


def report_success(request):
    """
    Success page
    """
    return render(request, 'report_success.html', {
        'message': 'گزارش با موفقیت ثبت شد.',
    })
