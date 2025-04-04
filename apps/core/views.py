from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Region, WildfireEvent


def home(request):
    regions = Region.objects.all()
    recent_events = WildfireEvent.objects.order_by("-start_date")[:5]
    return render(
        request, "core/home.html", {"regions": regions, "recent_events": recent_events}
    )


@login_required
def region_list(request):
    regions = Region.objects.all()
    return render(request, "core/region_list.html", {"regions": regions})


@login_required
def region_detail(request, pk):
    region = get_object_or_404(Region, pk=pk)
    events = WildfireEvent.objects.filter(region=region).order_by("-start_date")
    return render(
        request, "core/region_detail.html", {"region": region, "events": events}
    )
