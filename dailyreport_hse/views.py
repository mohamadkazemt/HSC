from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.http import JsonResponse
from .models import DailyReport, BlastingDetail, DrillingDetail, DumpDetail, LoadingDetail
from .forms import DailyReportForm, BlastingDetailForm, DrillingDetailForm, DumpDetailForm, LoadingDetailForm
from BaseInfo.models import MiningBlock, MiningMachine, Dump
from django.utils import timezone
from accounts.models import UserProfile


@login_required
def create_daily_report(request):
    blocks = MiningBlock.objects.all()
    drilling_machines = MiningMachine.objects.all()
    loading_machines = MiningMachine.objects.all()
    dumps = Dump.objects.all()

    if request.method == 'POST':
        print("Received POST data:", request.POST)

        report_form = DailyReportForm(request.POST)
        BlastingFormSet = modelformset_factory(BlastingDetail, form=BlastingDetailForm, extra=0)
        DrillingFormSet = modelformset_factory(DrillingDetail, form=DrillingDetailForm, extra=0)
        DumpFormSet = modelformset_factory(DumpDetail, form=DumpDetailForm, extra=0)
        LoadingFormSet = modelformset_factory(LoadingDetail, form=LoadingDetailForm, extra=0)

        blasting_formset = BlastingFormSet(request.POST, queryset=BlastingDetail.objects.none())
        drilling_formset = DrillingFormSet(request.POST, queryset=DrillingDetail.objects.none())
        dump_formset = DumpFormSet(request.POST, queryset=DumpDetail.objects.none())
        loading_formset = LoadingFormSet(request.POST, queryset=LoadingDetail.objects.none())

        print("Validating forms...")
        print("Report form is valid:", report_form.is_valid())
        print("Blasting formset is valid:", blasting_formset.is_valid())
        print("Drilling formset is valid:", drilling_formset.is_valid())
        print("Dump formset is valid:", dump_formset.is_valid())
        print("Loading formset is valid:", loading_formset.is_valid())

        if (report_form.is_valid() and
            blasting_formset.is_valid() and
            drilling_formset.is_valid() and
            dump_formset.is_valid() and
            loading_formset.is_valid()):

            print("Forms are valid. Saving data...")
            report = report_form.save(commit=False)
            report.user = request.user
            user_profile = request.user.userprofile
            report.user_group = user_profile.group
            report.created_at = timezone.now()
            print("Report details before save:", report)
            report.save()

            for form in blasting_formset:
                if form.cleaned_data:
                    blasting_detail = form.save(commit=False)
                    blasting_detail.daily_report = report
                    print("Saving blasting detail:", blasting_detail)
                    blasting_detail.save()

            for form in drilling_formset:
                if form.cleaned_data:
                    drilling_detail = form.save(commit=False)
                    drilling_detail.daily_report = report
                    print("Saving drilling detail:", drilling_detail)
                    drilling_detail.save()

            for form in dump_formset:
                if form.cleaned_data:
                    dump_detail = form.save(commit=False)
                    dump_detail.daily_report = report
                    print("Saving dump detail:", dump_detail)
                    dump_detail.save()

            for form in loading_formset:
                if form.cleaned_data:
                    loading_detail = form.save(commit=False)
                    loading_detail.daily_report = report
                    print("Saving loading detail:", loading_detail)
                    loading_detail.save()

            print("All data saved successfully.")
            return redirect('report_list')
        else:
            print("Form validation errors:")
            print("Report form errors:", report_form.errors.as_json())
            print("Blasting formset errors:", blasting_formset.errors)
            print("Drilling formset errors:", drilling_formset.errors)
            print("Dump formset errors:", dump_formset.errors)
            print("Loading formset errors:", loading_formset.errors)

            errors = {
                'report_form_errors': report_form.errors,
                'blasting_formset_errors': blasting_formset.errors,
                'drilling_formset_errors': drilling_formset.errors,
                'dump_formset_errors': dump_formset.errors,
                'loading_formset_errors': loading_formset.errors,
            }
            return render(
                request,
                'dailyreport_hse/new-report.html',
                {
                    'report_form': report_form,
                    'blasting_formset': blasting_formset,
                    'drilling_formset': drilling_formset,
                    'dump_formset': dump_formset,
                    'loading_formset': loading_formset,
                    'blocks': blocks,
                    'drilling_machines': drilling_machines,
                    'loading_machines': loading_machines,
                    'dumps': dumps,
                    'errors': errors,
                }
            )
    else:
        print("GET request received. Initializing empty forms.")
        report_form = DailyReportForm()
        BlastingFormSet = modelformset_factory(BlastingDetail, form=BlastingDetailForm, extra=1)
        DrillingFormSet = modelformset_factory(DrillingDetail, form=DrillingDetailForm, extra=1)
        DumpFormSet = modelformset_factory(DumpDetail, form=DumpDetailForm, extra=1)
        LoadingFormSet = modelformset_factory(LoadingDetail, form=LoadingDetailForm, extra=1)

        blasting_formset = BlastingFormSet(queryset=BlastingDetail.objects.none())
        drilling_formset = DrillingFormSet(queryset=DrillingDetail.objects.none())
        dump_formset = DumpFormSet(queryset=DumpDetail.objects.none())
        loading_formset = LoadingFormSet(queryset=LoadingDetail.objects.none())

        return render(
            request,
            'dailyreport_hse/new-report.html',
            {
                'report_form': report_form,
                'blasting_formset': blasting_formset,
                'drilling_formset': drilling_formset,
                'dump_formset': dump_formset,
                'loading_formset': loading_formset,
                'blocks': blocks,
                'drilling_machines': drilling_machines,
                'loading_machines': loading_machines,
                'dumps': dumps,
            }
        )

@login_required
def report_list(request):
    reports = DailyReport.objects.filter(user=request.user)
    print("Retrieved reports for user:", request.user, reports)
    return render(request, 'daily_report/report_list.html', {'reports': reports})

@login_required
def report_detail(request, pk):
    report = get_object_or_404(DailyReport, pk=pk, user=request.user)
    print("Report details for pk:", pk, report)
    return render(
        request,
        'daily_report/report_detail.html',
        {
            'report': report,
            'blasting_details': report.blasting_details.all(),
            'drilling_details': report.drilling_details.all(),
            'dump_details': report.dump_details.all(),
            'loading_details': report.loading_details.all(),
        }
    )
