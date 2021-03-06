from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import *
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView, UpdateView, DeleteView, ModelFormMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from .forms import *
import re

def index(request):
    regiondata = []
    for region in Region_data:
        regiondata.append(region[0])
    context = {
        'industries': Industry.objects.all(),
        'services': ServiceCategory.objects.all(),
        'regions': regiondata
    }
    return render(request, 'index/index.html', context=context)


def list(request):
    if request.method == 'POST':
        regions = request.POST.getlist('region')
        industries = request.POST.getlist('industry')
        services = request.POST.getlist('service')
    # Send empty if nothing selected
        if len(regions) == 0 and len(industries) == 0 and len(services) == 0:
            context = {
            }
            return render(request, 'index/list.html', context=context)

    # chaining the  input data for querying
        if len(regions) == 0:
            for region in Region_data:
                regions.append(region[0])

        if len(industries) == 0:
            allindustries = Industry.objects.all()
            for industry in allindustries:
                industries.append(industry.Name)

        if len(services) == 0:
            allservices = ServiceCategory.objects.all()
            for service in allservices:
                services.append(service.Name)
    # Query Codes here
        query_result = OrgBaseInfo.objects.filter(
            Q(Region__in=regions) & Q(Industry__Name__in=industries) & Q(
                ServiceCategory__Name__in=services)
        ).distinct().order_by('Region')
        context = {
            'query_result': query_result
        }
        return render(request, 'index/list.html', context=context)
    query_result = OrgBaseInfo.objects.all()
    context = {
        'query_result': query_result
    }
    return render(request, 'index/list.html', context=context)


def details(request, id):
    org = get_object_or_404(OrgBaseInfo, pk=id)
    region = org.Region
    services = Service.objects.filter(OrgName=org)
    cases = Case.objects.filter(OrgName=org)
    experiences = Experience.objects.filter(OrgName=org)
    context = {
        'org': org,
        'services': services,
        'cases': cases,
        'experiences': experiences
    }
    return render(request, 'index/details.html', context=context)


def search(request):
    orgInfo = request.POST["orgInfo"]
    p = re.compile('\W')   # Check if the input has any non alphanumeric charaters
    specialChars = p.findall(orgInfo)
    for chars in specialChars:
        if chars != ' ':
            return redirect('index') # Redirect to index if undesirable input
    form = SearchForm({'search': orgInfo})
    if form.is_valid():
        orgs = OrgBaseInfo.objects.filter(
            Name__icontains=orgInfo).order_by('Region')
        return render(request, 'index/list.html', context={'query_result': orgs})
    else:
        return redirect('index')


# Org_Base_Info

class OrgbaseInfoCreate(LoginRequiredMixin, CreateView):
    model = OrgBaseInfo
    form_class = OrgBaseInfoForm


class OrgBaseInfoUpdate(LoginRequiredMixin, UpdateView):
    model = OrgBaseInfo
    form_class = OrgBaseInfoForm
    context_object_name = 'org'
    template = 'orgbaseinfo_form.html'

    def get_success_url(self):
        id = self.kwargs['pk']
        return reverse_lazy('details', kwargs={'id': id})


class OrgDelete(LoginRequiredMixin, DeleteView):
    model = OrgBaseInfo
    success_url = reverse_lazy('index')


@login_required
def OrgDelete(request, pk):
    org = OrgBaseInfo.objects.get(id=pk)
    org.delete()
    return redirect('index')


# Industry Options ------------>
@login_required
def EditIndustryOptions(request):
    industries = Industry.objects.all()
    context = {
        "objects":industries,
        "title": "Industry"
    }
    return render(request, 'index/industry_options.html', context=context)

class AddIndustry(LoginRequiredMixin, CreateView):
    model = Industry
    form_class = IndustryForm
    template = "index/industry_form.html"
    def form_valid(self, form):
        form.save()
        return redirect('options_industry')

class UpdateIndustry(LoginRequiredMixin, UpdateView):
    model = Industry
    form_class = IndustryForm
    context_object_name = 'industry'
    
    def form_valid(self, form):
        form.save()
        return redirect('options_industry')

@login_required
def DeleteIndustry(request, pk):
    industry = Industry.objects.get(id=pk)
    industry.delete()
    return redirect('options_industry')

# Service Options
@login_required
def EditServiceCategoryOptions(request):
    services = ServiceCategory.objects.all()
    context = {
        "objects":services,
        "title": "Service"
    }
    return render(request, 'index/serviceCategory_options.html', context=context)

class AddServiceCategory(LoginRequiredMixin, CreateView):
    model = ServiceCategory
    form_class = addServiceCategoryForm
    template_name = "index/servicecategory_form.html"
    success_url = reverse_lazy('options_serviceCategory')
   
    def form_valid(self, form):
        form.save()
        return redirect('options_serviceCategory')

class UpdateServiceCategory(LoginRequiredMixin, UpdateView):
    model = ServiceCategory
    form_class = addServiceCategoryForm
    context_object_name = 'serviceCategory'
    def form_valid(self, form):
        form.save()
        return redirect('options_serviceCategory')

@login_required
def DeleteServiceCategory(request, pk):
    service = ServiceCategory.objects.get(id=pk)
    service.delete()
    return redirect('options_serviceCategory')


# Service
@method_decorator(login_required, name='dispatch')
class ServiceCreate(CreateView):
    model = Service
    form_class = ServiceForm

    def form_valid(self, form):
        service = form.save(commit=False)
        service.OrgName = OrgBaseInfo.objects.get(id=self.kwargs["pk"])
        service.save()
        form.save_m2m()
        return redirect('details', id=self.kwargs["pk"])


class ServiceUpdate(LoginRequiredMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    context_object_name = 'service'


@login_required
def ServiceDelete(request, pk):
    service = Service.objects.get(id=pk)
    orgid = service.OrgName.id
    service.delete()
    return redirect('details', id=int(orgid))


# Experience
class ExperienceCreate(LoginRequiredMixin, CreateView):
    model = Experience
    form_class = ExperienceForm

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.OrgName = OrgBaseInfo.objects.get(id=self.kwargs["pk"])
        instance.save()
        return redirect('details', id=self.kwargs["pk"])


class ExperienceUpdate(LoginRequiredMixin, UpdateView):
    model = Experience
    form_class = ExperienceForm


class ExperienceDelete(LoginRequiredMixin, DeleteView):
    model = Experience
    success_url = reverse_lazy('index')


# Case
class CaseCreate(LoginRequiredMixin, CreateView):
    model = Case
    form_class = CaseForm

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.OrgName = OrgBaseInfo.objects.get(id=self.kwargs["pk"])
        instance.save()
        form.save_m2m()
        return redirect('details', id=self.kwargs["pk"])


class CaseUpdate(LoginRequiredMixin, UpdateView):
    model = Case
    form_class = CaseForm
    context_object_name = 'case'


@login_required
def CaseDelete(request, pk):
    case = Case.objects.get(id=pk)
    orgid = case.OrgName.id
    case.delete()
    return redirect('details', id=int(orgid))
