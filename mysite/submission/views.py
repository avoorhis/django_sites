
'''
# from django.shortcuts import render

# Create your views here.
def index(request):
    return HttpResponse("Illumina files processing")
    
# def 
'''
#
# from django.shortcuts import render_to_response
# from django.template import RequestContext
# from django.views.generic import TemplateView
#
# def index(request):
#   return render_to_response('submission/index.html', context_instance=RequestContext(request))
#
#
# class HelpView(TemplateView):
#     template_name = "help.html"
#
# from django.http import HttpResponse
#
# def index(request):
#     return HttpResponse("Illumina files processing")
#
# from django.http import HttpResponse
#
# from .models_l_env454 import Run
#
# def index(request):
#     latest_run_list = Run.objects.order_by('-run')[:10]
#     output = ', '.join([q.run for q in latest_run_list])
#     return HttpResponse(output)

from django.http import HttpResponse
from django.template import loader
from django.http import Http404

from django.shortcuts import get_object_or_404
from django.shortcuts import render
from .models_l_env454 import Run


# def index(request):
#     latest_run_list = Run.objects.order_by('-run')[:15]
#     template = loader.get_template('submission/index.html')
#     context = {
#         'latest_run_list': latest_run_list,
#     }
#     return HttpResponse(template.render(context, request))


def index(request):
    latest_run_list = Run.objects.order_by('-run')[:10]
    context = {'latest_run_list': latest_run_list}
    return render(request, 'submission/index.html', context)
        
# def detail(request, run_id):
#     return HttpResponse("You're looking at run %s." % run_id)
#
# def detail(request, run_id):
#     try:
#         run = Run.objects.get(pk=run_id)
#     except Run.DoesNotExist:
#         raise Http404("Run does not exist")
#     return render(request, 'submission/detail.html', {'run': run})

def detail(request, run_id):
    run = get_object_or_404(Run, pk=run_id)
    return render(request, 'submission/detail.html', {'run': run})
    
def results(request, run_id):
    response = "You're looking at the results of run %s."
    return HttpResponse(response % run_id)

def vote(request, run_id):
    return HttpResponse("You're voting on run %s." % run_id)
    
def help(request):
    return render(request, 'submission/help.html')

def gzip_all(request):
    latest_run_list = Run.objects.order_by('-run')[:10]
    context = {'latest_run_list': latest_run_list}
    return render(request, 'submission/gzip_all.html', context)
        
# ---
from django.http import HttpResponseRedirect

from .forms import NameForm

def get_name(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = NameForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            return HttpResponseRedirect('/submission/name/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = NameForm()

    return render(request, 'submission/name.html', {'form': form})