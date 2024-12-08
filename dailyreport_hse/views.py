from formtools.wizard.views import SessionWizardView
from django.shortcuts import render
from .forms import (
    WorkFrontStatusForm, DumpStatusForm, DrillingSiteStatusForm,
    IncidentForm, HSEParticipationForm, SafetyStopForm, HSEReportForm
)
from .models import HSEReport

FORMS = [
    ("workfront", WorkFrontStatusForm),
    ("dump", DumpStatusForm),
    ("drilling_site", DrillingSiteStatusForm),
    ("incident", IncidentForm),
    ("participation", HSEParticipationForm),
    ("safety_stop", SafetyStopForm),
    ("final", HSEReportForm),
]

TEMPLATES = {
    "workfront": "dailyreport_hse/workfront.html",
    "dump": "steps/dump.html",
    "drilling_site": "steps/drilling_site.html",
    "incident": "steps/incident.html",
    "participation": "steps/participation.html",
    "safety_stop": "steps/safety_stop.html",
    "final": "steps/final.html",
}

class HSEWizard(SessionWizardView):
    form_list = FORMS

    def get_template_names(self):
        return [TEMPLATES[self.steps.current]]

    def done(self, form_list, **kwargs):
        report = HSEReport()
        report.shift_date = form_list[-1].cleaned_data['shift_date']
        report.supervisor = form_list[-1].cleaned_data['supervisor']
        report.next_shift_tasks = form_list[-1].cleaned_data['next_shift_tasks']
        report.save()
        return render(self.request, 'steps/complete.html', {'report': report})
