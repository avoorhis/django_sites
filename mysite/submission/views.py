
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

from django.http import HttpResponse

from .models_l_env454 import Run

def index(request):
    latest_run_list = Run.objects.order_by('-run')[:10]
    output = ', '.join([q.run for q in latest_run_list])
    return HttpResponse(output)
    
def detail(request, question_id):
    return HttpResponse("You're looking at question %s." % question_id)

def results(request, question_id):
    response = "You're looking at the results of question %s."
    return HttpResponse(response % question_id)

def vote(request, question_id):
    return HttpResponse("You're voting on question %s." % question_id)