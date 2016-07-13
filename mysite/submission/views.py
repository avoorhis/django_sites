from django.http import HttpResponse
from django.shortcuts import render, render_to_response
from django.template import RequestContext, loader, Context

from .models_l_env454 import Run
from .forms import RunForm, CsvRunInfoUploadForm, FileUploadForm
from .utils import get_run, get_csv_data

from .csv_tools import CsvMetadata
import csv
import codecs

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
    return render(request, 'submission/upload_metadata.html')

def upload_metadata_file(request):
    error_message = ""
    if request.method == 'POST' and request.FILES:
        # file
        # request.POST: 
        # <QueryDict: {u'csrfmiddlewaretoken': [u'7p7t28ZZm9bg4uTlbFYcx4GGVeSWvLqh']}>
        # request.FILES: 
        # <MultiValueDict: {u'upload_this_file': [<InMemoryUploadedFile: metadata_upload_good_csv.html (text/html)>]}>
        # [13/Jul/2016 16:29:26] "POST /submission/upload_metadata_file/ HTTP/1.1" 200 6815

        # info
        # request.POST: 
        # <QueryDict: {u'find_seq_operator': [u'33'], u'find_insert_size': [u'44'], u'find_rundate': [u'11'], u'find_read_length': [u'55'], u'find_path_to_raw_data': [u'22'], u'find_dna_region': [u'v4v5'], u'find_overlap': [u'hs'], u'csrfmiddlewaretoken': [u'7p7t28ZZm9bg4uTlbFYcx4GGVeSWvLqh'], u'find_has_ns': [u'no']}>
        # https://gist.github.com/imkevinxu/3365661
        # csvfile = request.FILES['csv_file']
        # dialect = csv.Sniffer().sniff(codecs.EncodedFile(csvfile, "utf-8").read(1024))
        # csvfile.open()
        # reader = csv.reader(codecs.EncodedFile(csvfile, "utf-8"), delimiter=',', dialect=dialect)
        # print "printing from views"
        # for row in reader:
        #     print row
        
        csv_file = request.FILES['csv_file']
        csv_handler = CsvMetadata()
        csv_handler.import_from_file(csv_file)
    
        print "csv_handler.csv_by_header_uniqued from views"
        print csv_handler.csv_by_header_uniqued
        # {'domain': ['archaea', 'bacteria'], 'dna_region': ['v6'], 'submit_code': ['ashipunova354276'], 'date_updated': ['2013-03-27'], 'rundate': ['20151111'], 'dataset_description': ['Sample Dataset Description temp', 'Sample Dataset Description temp 2'], 'tube_number': ['1', '2'], 'op_amp': ['JV'], 'concentration': ['1'], 'id': ['7308', '7309'], 'insert_size': ['100'], 'on_vamps': [''], 'trim_distal': [''], 'read_length': ['100'], 'env_sample_source_id': ['120'], 'enzyme': [''], 'overlap': ['complete'], 'platform': [''], 'duplicate': ['no'], 'tube_label': ['Tube_Label_2_temp', 'Tube_Label_1_temp'], 'op_seq': ['JV'], 'barcode_index': [''], 'direction': [''], 'project_name': ['AS_AS_Bv6', 'AS_AS_Av6'], 'sample_received': [''], 'adaptor': [''], 'barcode': [''], 'runkey': [''], 'op_empcr': [''], 'quant_method': ['3'], 'date_initial': ['2013-03-27'], 'user': ['ashipunova'], 'pool': [''], 'lane': ['1', '2'], 'primer_suite': ['Archaeal V6 Suite', 'Bacterial V6 Suite'], 'dataset_name': ['dat_test1']}
        
        # file_upload_form = FileUploadForm(request.POST, request.FILES)
        # form = MyForm(initial={'charfield1': 'foo', 'charfield2': 'bar'})
        
        csv_rundate = "".join(csv_handler.csv_by_header_uniqued['rundate'])
        csv_dna_region = "".join(csv_handler.csv_by_header_uniqued['dna_region'])
        # 'csv_rundate': csv_rundate, 
        # 'csv_path_to_raw_data': "/xraid2-2/sequencing/Illumina/%s" % csv_rundate, 
        # 'csv_dna_region': csv_dna_region, 
        # 'csv_overlap': "".join(csv_handler.csv_by_header_uniqued['rundate']), 
        # 'csv_has_ns': "".join(csv_handler.csv_by_header_uniqued['rundate']), 
        # 'csv_seq_operator': "".join(csv_handler.csv_by_header_uniqued['rundate']), 
        # 'csv_insert_size': "".join(csv_handler.csv_by_header_uniqued['rundate']), 
        # 'csv_read_length': "".join(csv_handler.csv_by_header_uniqued['rundate']), 
        
        metadata_run_info_form = CsvRunInfoUploadForm({'csv_rundate': csv_rundate, 
                    'csv_path_to_raw_data': "/xraid2-2/sequencing/Illumina/%s" % csv_rundate,
                    'csv_dna_region': csv_dna_region, 
                    
                    })
                    
        # metadata_run_info_form = CsvRunInfoUploadForm(request.POST)
        # if file_upload_form.is_valid():
        #     print "file_upload_form.cleaned_data: "
        #     print file_upload_form.cleaned_data
            
            # csv_handler = CsvMetadata()
            # csv_handler.import_from_file(request.FILES['upload_this_file'])
            # return HttpResponseRedirect('submission/upload_metadata_run_info_form.html')
            
        return render(request, 'submission/upload_metadata_run_info_form.html', {'CsvRunInfoUploadForm': metadata_run_info_form, 'header': 'upload_metadata_run_info_form', 'csv_by_header_uniqued': csv_handler.csv_by_header_uniqued, 'error_message': error_message })
    else:
        print "EEE"
        
        file_upload_form = FileUploadForm()
        context = {'file_upload_form':file_upload_form}
        
    # return render(request, 'submission/upload_metadata_file.html', {'file_upload_form': file_upload_form})
        return render_to_response('submission/upload_metadata_file.html', context, context_instance=RequestContext(request))  

    #     return render(request, 'submission/upload_metadata.html', {'form': form, 'header': 'upload_metadata',  'error_message': error_message })
    # 
    # else:
    #     print "IN views.upload_metadata else"
    #     form = FileUploadForm()
    #     context = {'form':form}
    #     return render_to_response('submission/upload_metadata.html', context, context_instance=RequestContext(request))  
    
    # return render(request, 'submission/upload_metadata_file.html')
    
def run_info_csv(request):
    print "request.GET = "
    print request.GET

    print "request.POST = "
    print request.POST

    print "request.FILES = "
    print request.FILES



    my_file = request.GET['csv_file']
    message = 'request.GET[csv_file]: %s' % request.GET['csv_file']
    csv_handler = CsvMetadata()
    csv_handler.import_from_file(my_file)
    
    print "HHHH"
    
    # message = "Filename = "
    # return HttpResponse(message)
    return render(request, 'submission/upload_metadata_run_info_form.html', { 'message': message })
    

# =======

def file_upload_post(request):
    print "file_upload_post method"
    form = CsvRunInfoUploadForm(request.POST, request.FILES)
    return form

def csv_run_info_post(request):
    print "csv_run_info_post method"
    print "2) request.method == 'POST', request.POST:"
    print request.POST
    
    form = CsvRunInfoUploadForm(request.POST, request.FILES)
    print request.FILES
    
    if form.is_valid():
        print "FFF form.cleaned_data"
        print form.cleaned_data
    
    my_file = request.FILES
    m = CsvMetadata()
    m.import_from_file(my_file)
    return form
    
    
    # my_file = request.POST['upload_this_file']
    # print my_file
    # m = CsvMetadata()
    # m.import_from_file(my_file)
    

def first_call():
    print "first_call"
    error_message = ""
    print "IN views.upload_metadata first_call"
    form = FileUploadForm()
    # FileUploadForm(prefix='file_upload')
    return form

def upload_metadata_all(request):
    error_message = ""
    if request.method == 'POST':
        print "1) request.method == 'POST', request.POST:"
        print request.POST
        
        if 'file_upload' in request.POST:
            form = file_upload_post(request)
        elif 'csv_run_info' in request.POST:
            form = csv_run_info_post(request)
    else:
        form = first_call()

    context = {'form':form}
    print "context 1"
    print context
        
    return render(request, 'submission/upload_metadata.html', {'form': form, 'header': 'upload_metadata', 'context': context, 'error_message': error_message })

    # error_message = ""
    # if request.method == 'POST':
    #     print "IN views.upload_metadata if request.method == 'POST'"
    #     form = CsvRunInfoUploadForm(request.POST, request.FILES)
    #     print request.FILES
    #     
    #     print "request.POST = "
    #     print request.POST
    #     if form.is_valid():
    #         print "FFF form.cleaned_data"
    #         print form.cleaned_data
    #     
    #     my_file = request.FILES
    #     # ['file']
    #     m = CsvMetadata()
    #     m.import_from_file(my_file)
    #     # return render_to_response('submission/upload_metadata.html', context_instance=RequestContext(request))
    #     return render(request, 'submission/upload_metadata.html', {'form': form, 'header': 'upload_metadata',  'error_message': error_message })
    # 
    # else:
    #     print "IN views.upload_metadata else"
    #     form = FileUploadForm()
    #     context = {'form':form}
    #     return render_to_response('submission/upload_metadata.html', context, context_instance=RequestContext(request))  
# =======

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