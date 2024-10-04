from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .forms import  AnomalyForm
from django.shortcuts import redirect

name = 'anomalis'

@login_required
def anomalis(request):
    if request.method == 'POST':
        form = AnomalyForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('anomalis:anomalis')
    else:
        form = AnomalyForm()
    return render(request, 'anomalis/new-anomalie.html', {'form': form})




