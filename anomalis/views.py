from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Location, Anomalytype
from .forms import LocationForm, AnomalytypeForm, AnomalyForm
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




@login_required
def location(request):
    locations = Location.objects.all()
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('anomalis:location')
    else:
        form = LocationForm()
    return render(request, 'anomalis/information.html', {'form': form, 'locations': locations})

@login_required
def anomalytype(request):
    if request.method == 'POST':
        form = AnomalytypeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('anomalis:anomalytype')
    else:
        form = AnomalytypeForm()
    return render(request, 'anomalis/information.html', {'form': form})


@login_required
def delete_location(request, pk):
    location = Location.objects.get(id=pk)
    if request.method == 'POST':
        location.delete()
        return redirect('anomalis:location')
    return render(request, 'anomalis/delete.html', {'location': location})


@login_required
def delete_anomalytype(request, pk):
    anomalytype = Anomalytype.objects.get(id=pk)
    if request.method == 'POST':
        anomalytype.delete()
        return redirect('anomalis:anomalytype')
    return render(request, 'anomalis/delete.html', {'anomalytype': anomalytype})


@login_required
def location_edit(request, pk):
    location = Location.objects.get(id=pk)
    if request.method == 'POST':
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            return redirect('anomalis:location')
    else:
        form = LocationForm(instance=location)
    return render(request, 'anomalis/delete.html', {'form': form, 'location': location})


