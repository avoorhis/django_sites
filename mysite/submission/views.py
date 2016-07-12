from django.http import HttpResponse
from django.shortcuts import render, render_to_response
from django.template import RequestContext, loader, Context

from .models_l_env454 import Run
from .forms import RunForm, CsvUploadForm
from .utils import get_run, get_csv_data

from .csv_tools import CodeCSvModel


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
    current_url = request.META["HTTP_REFERER"]
    
    return render(request, current_url, context)

# def detail(request, run_id):
#     return HttpResponse("You're looking at run %s." % run_id)
#
# def detail(request, run_id):
#     try:
#         run = Run.objects.get(pk=run_id)
#     except Run.DoesNotExist:
#         raise Http404("Run does not exist")
#     return render(request, 'submission/detail.html', {'run': run})



def help(request):
    return render(request, 'submission/help.html', {'header': 'Help and tips'})

def upload_metadata(request):
    # csv_data = {}
    # 
    # try:
    #     form, csv_data, error_message = get_csv_data(request)
    #     print "csv_data from views.upload_metadata"
    #     print csv_data
    # except:
    #     form, error_message = get_csv_data(request)
    #     return render(request, 'submission/upload_metadata.html', {'form': form, 'csv_data': csv_data, 'header': 'Data upload to db', 'is_cluster': 'not', 'pipeline_command': 'env454upload',  'error_message': error_message})
    # return render(request, 'submission/upload_metadata_run_info_form.html', {'form': form, 'csv_data': csv_data, 'header': 'Data upload to db', 'is_cluster': 'not', 'pipeline_command': 'env454upload',  'error_message': error_message})

    # error_message = ""
    #   # If we had a POST then get the request post values.
    #   if request.method == 'POST':
    #       print "IN utils.get_csv_data if request.method == 'POST'"
    #       form = CsvUploadForm(request.POST, request.FILES)
    #       print request.FILES
    #       my_file = request.FILES
    #       # ['file']
    #       m = CodeCSvModel()
    #       m.import_from_file(my_file)
    #       run_info_data = {}
    #       # return render_to_response('submission/upload_metadata_run_info_form.html', context_instance=RequestContext(request))
    #       return (form, run_info_data, error_message)
    # 
    #   else:
    #       print "IN views.upload_metadata else"
    #       form = CsvUploadForm()
    #       context = {'form':form}
    #       # return render_to_response('submission/upload_metadata.html', context, context_instance=RequestContext(request))  
    #       return (form, error_message)


# def upload_metadata(request):

    # If we had a POST then get the request post values.
    if request.method == 'POST':
        print "IN views.upload_metadata if request.method == 'POST'"
        form = CsvUploadForm(request.POST, request.FILES)
        print request.FILES
        my_file = request.FILES
        # ['file']
        m = CodeCSvModel()
        m.import_from_file(my_file)
        return render_to_response('submission/upload_metadata.html', context_instance=RequestContext(request))

    else:
        print "IN views.upload_metadata else"
        form = CsvUploadForm()
        context = {'form':form}
        return render_to_response('submission/upload_metadata.html', context, context_instance=RequestContext(request))  

def data_upload(request):
    run_data = {}
    try:
        form, run_data, error_message = get_run(request)
    except:
        form, error_message = get_run(request)
    return render(request, 'submission/page_w_command_l.html', {'form': form, 'run_data': run_data, 'header': 'Data upload to db', 'is_cluster': 'not', 'pipeline_command': 'env454upload',  'error_message': error_message})

def run_info_upload(request):
    run_data = {}
    try:
        form, run_data, error_message = get_run(request)
    except:
        form, error_message = get_run(request)
    return render(request, 'submission/page_w_command_l.html', {'form': form, 'run_data': run_data, 'header': 'Run info upload to db', 'is_cluster': 'not', 'pipeline_command': 'env454run_info_upload',  'error_message': error_message })

def chimera_checking(request):
    run_data = {}
    try:
        form, run_data, error_message = get_run(request)
    except:
        form, error_message = get_run(request)
    return render(request, 'submission/page_w_command_l.html', {'form': form, 'run_data': run_data, 'header': 'Chimera checking (for v4v5 region only)', 'is_cluster': '', 'pipeline_command': 'illumina_chimera_only', 'what_to_check': 'statistics ', 'check_command': 'chimera/; chimera_stats.py', 'error_message': error_message})

def demultiplex(request):
    run_data = {}
    try:
        form, run_data, error_message = get_run(request)
    except:
        form, error_message = get_run(request)
    return render(request, 'submission/page_w_command_l.html', {'form': form, 'run_data': run_data, 'header': 'Demultiplex Illumina files by index/run_key/lane', 'is_cluster': 'not', 'pipeline_command': 'illumina_files_demultiplex_only',  'error_message': error_message })

def overlap(request):
    run_data = {}
    check_command = ''
    try:
        form, run_data, error_message = get_run(request)
        check_command = 'reads_overlap/; take_%s_stats.py' % run_data['find_machine']
    except:
        form, error_message = get_run(request)
    return render(request, 'submission/page_w_command_l.html', {'form': form, 'run_data': run_data, 'header': 'Overlap, filter and unique reads in already demultiplexed files', 'is_cluster': '', 'pipeline_command': 'illumina_files', 'what_to_check': 'the overlap percentage ', 'check_command': check_command, 'error_message': error_message })

def overlap_only(request):
    run_data = {}
    check_command = ''
    try:
        form, run_data, error_message = get_run(request)
        check_command = 'reads_overlap/; take_%s_stats.py' % run_data['find_machine']
    except:
        form, error_message = get_run(request)
    return render(request, 'submission/page_wo_c_l.html', {'form': form, 'run_data': run_data, 'header': 'Overlap reads in already demultiplexed files', 'is_cluster': '', 'command': '; run_partial_overlap_clust.sh; date', 'what_to_check': 'the overlap percentage ', 'check_command': check_command, 'error_message': error_message })


def filter_mismatch(request):
    run_data = {}
    header = '''Filtering partial (Ev4, v4v5 and ITS1) merged\n
    Maximum number of mismatches allowed in the overlapped region is 3'''
    try:
        form, run_data, error_message = get_run(request)
    except:
        form, error_message = get_run(request)
    return render(request, 'submission/page_wo_c_l.html', {'form': form, 'run_data': run_data, 'header': header, 'is_cluster': '', 'command': 'reads_overlap/; run_mismatch_filter.sh; date',  'error_message': error_message })
    
def gast(request):
    run_data = {}
    try:
        form, run_data, error_message = get_run(request)
        # print "!!!form.cleaned_data"
        # print form.cleaned_data
        # print "555 find_rundate = "
        # print run_data['find_rundate']
    except:
        form, error_message = get_run(request)
    return render(request, 'submission/page_wo_c_l.html', {'form': form, 'run_data': run_data, 'header': 'Gast', 'is_cluster': 'not', 'command': 'reads_overlap/; run_gast_ill_nonchim_sge.sh; date', 'what_to_check': 'the percent of "Unknown" taxa ', 'check_command': 'gast/; percent10_gast_unknowns.sh', 'error_message': error_message})

def gzip_all(request):
    run_data = {}
    try:
        form, run_data, error_message = get_run(request)
    except:
        form, error_message = get_run(request)
    return render(request, 'submission/page_wo_c_l.html', {'form': form, 'run_data': run_data, 'header': 'Gzip all files', 'is_cluster': 'not', 'command': '; time gzip -r *',  'error_message': error_message})

def clear_db(request):
    run_data = {}
    try:
        form, run_data, error_message = get_run(request)
    except:
        form, error_message = get_run(request)
    return render(request, 'submission/clear_db.html', {'form': form, 'run_data': run_data, 'header': 'Remove old data from db',  'error_message': error_message})

def uniqueing(request):
    run_data = {}
    try:
        form, run_data, error_message = get_run(request)
    except:
        form, error_message = get_run(request)
    return render(request, 'submission/page_wo_c_l.html', {'form': form, 'run_data': run_data, 'header': 'Uniqueing fasta files', 'is_cluster': '', 'command': 'reads_overlap/; run_unique_fa.sh; date',  'error_message': error_message })

def check_fa_counts(request):
    run_data = {}
    try:
        form, run_data, error_message = get_run(request)
    except:
        form, error_message = get_run(request)
    return render(request, 'submission/page_wo_c_l.html', {'form': form, 'run_data': run_data, 'header': 'Check counts in fasta files', 'is_cluster': 'not', 'command': 'reads_overlap/; grep '>' *REMOVED.unique | wc -l; date',  'error_message': error_message})

def check_db_counts(request):
    run_data = {}
    try:
        form, run_data, error_message = get_run(request)
    except:
        form, error_message = get_run(request)
    return render(request, 'submission/check_db_counts.html', {'form': form, 'run_data': run_data, 'header': 'Check counts in db', 'error_message': error_message})

def gunzip_all(request):
    run_data = {}
    try:
        form, run_data, error_message = get_run(request)
    except:
        form, error_message = get_run(request)
    return render(request, 'submission/page_wo_c_l.html', {'form': form, 'run_data': run_data, 'header': 'Gunzip all files', 'is_cluster': 'not', 'command': '; time gunzip -r *.gz',  'error_message': error_message})