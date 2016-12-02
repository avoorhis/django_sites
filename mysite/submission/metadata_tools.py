from .forms import RunForm, FileUploadForm, CsvRunInfoUploadForm, MetadataOutCsvForm, AddProjectForm
from .utils import Utils, Dirs
from collections import defaultdict
from datetime import datetime
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.db.models import Q
from django.forms import formset_factory
from django.forms.models import model_to_dict
from django.shortcuts import render
from django.utils.datastructures import MultiValueDictKeyError
import codecs
import csv
import models
import models_l_env454
import os
import time

# Assuming that in each csv one rundate and one platform!
class CsvMetadata():
    """
    IN
    Unique per upload (run_info):
        Run date:
        Path to raw data:
        Platform:
        DNA Region:
        Overlap:
        Has Ns:
        Seq Operator:
        Insert Size:
        Read Length:

    Can be changed in the table:
        HEADERS_TO_EDIT_METADATA

    Taken from csv: HEADERS_FROM_CSV
    Taken from vamps_submission tables on vamps:
        'vamps_auth_id'
        'first_name'
        'project_description'
        'funding'
        'institution'
        'title'
        'num_of_tubes'
        'date_initial'
        'submit_code'
        'email'
        'date_updated'
        'last_name'
        'temp_project'
        'user'
        'passwd'
        'security_level'
        'active'
        'locked'
        'date_added'
        'id'
    Taken from user table on env454:
        see models

    OUT:
    ini:
        "rundate"
        "lane_domain"
        "dna_region"
        "path_to_raw_data"
        "overlap"
        "machine"
    csv: HEADERS_TO_CSV
    """

    def __init__(self):

        self.RUN_INFO_FORM_FIELD_HEADERS = ["dna_region", "insert_size", "op_seq", "overlap", "read_length", "rundate"]
        self.csv_headers = []
        self.csv_content = []
        self.run_info_from_csv = {}
        self.errors = []
        self.csv_by_header_uniqued = defaultdict(list)
        self.csv_by_header = defaultdict(list)
        self.csvfile = ""
        self.cause = ""
        self.path_to_csv = ""
        self.selected_lane = ""
        self.domain_letter = ""
        self.selected_machine_short = ""
        self.ini_names = {}
        self.metadata_csv_file_names = {}
        self.dirs = Dirs()
        self.lanes_domains = []
        # self.out_metadata = defaultdict(lambda: defaultdict(int))
        self.out_metadata = defaultdict(defaultdict)
        self.out_metadata_table = defaultdict(list)
        self.vamps_submissions = {}
        self.user_info_arr = {}
        self.adaptors_full = {}
        self.domain_choices = dict(models.Domain.LETTER_BY_DOMAIN_CHOICES)
        self.machine_shortcuts_choices = dict(models.Machine.MACHINE_SHORTCUTS_CHOICES)
        self.utils = Utils()
        self.files_created = []
        self.empty_cells = []
        self.new_project = ""
        self.new_project_created = False
        self.adaptor_ref = self.get_all_adaptors()

        # error = True

        self.HEADERS_FROM_CSV = {
            'id': {'field': 'id', 'required': True},
            'submit_code': {'field': 'submit_code', 'required': True},
            'user': {'field': 'user', 'required': True},
            'tube_number': {'field': 'tube_number', 'required': True},
            'tube_label': {'field': 'tube_label', 'required': False},
            'dataset_description': {'field': 'dataset_description', 'required': False},
            'duplicate': {'field': 'duplicate', 'required': False},
            'domain': {'field': 'domain', 'required': True},
            'primer_suite': {'field': 'primer_suite', 'required': True},
            'dna_region': {'field': 'dna_region', 'required': True},
            'project_name': {'field': 'project_name', 'required': True},
            'dataset_name': {'field': 'dataset_name', 'required': True},
            'runkey': {'field': 'runkey', 'required': False},
            'barcode': {'field': 'barcode', 'required': False},
            'pool': {'field': 'pool', 'required': False},
            'lane': {'field': 'lane', 'required': True},
            'direction': {'field': 'direction', 'required': False},
            'platform': {'field': 'platform', 'required': True},
            'op_amp': {'field': 'op_amp', 'required': True},
            'op_seq': {'field': 'op_seq', 'required': True},
            'op_empcr': {'field': 'op_empcr', 'required': False},
            'enzyme': {'field': 'enzyme', 'required': False},
            'rundate': {'field': 'rundate', 'required': True},
            'adaptor': {'field': 'adaptor', 'required': True},
            'date_initial': {'field': 'date_initial', 'required': True},
            'date_updated': {'field': 'date_updated', 'required': True},
            'on_vamps': {'field': 'on_vamps', 'required': False},
            'sample_received': {'field': 'sample_received', 'required': False},
            'concentration': {'field': 'concentration', 'required': True},
            'quant_method': {'field': 'quant_method', 'required': True},
            'overlap': {'field': 'overlap', 'required': True},
            'insert_size': {'field': 'insert_size', 'required': True},
            'barcode_index': {'field': 'barcode_index', 'required': False},
            'read_length': {'field': 'read_length', 'required': True},
            'trim_distal': {'field': 'trim_distal', 'required': False},
            'env_sample_source_id': {'field': 'env_sample_source_id', 'required': True},
        }

        self.HEADERS_TO_CSV = ['adaptor', 'amp_operator', 'barcode', 'barcode_index', 'data_owner', 'dataset', 'dataset_description', 'dna_region', 'email', 'env_sample_source_id', 'first_name', 'funding', 'insert_size', 'institution', 'lane', 'last_name', 'overlap', 'platform', 'primer_suite', 'project', 'project_description', 'project_title', 'read_length', 'run', 'run_key', 'seq_operator', 'tubelabel']

        self.HEADERS_TO_EDIT_METADATA = ['domain', 'lane', 'contact_name', 'run_key', 'barcode_index', 'adaptor', 'project', 'dataset', 'dataset_description', 'env_source_name', 'tubelabel', 'barcode', 'amp_operator']

        self.required_headers = [header_name for header_name, values in
                                 self.HEADERS_FROM_CSV.items() if values['required']]
        # print "self.required_headers = %s" % self.required_headers

    def no_data_message(self):
        return 'There is no data for <span class="emph_it">%s</span> in the file <span class="emph_it">%s</span>' % (self.cause, self.csvfile)

    def import_from_file(self, csvfile):
        print "import_from_file"
        
        self.csvfile = csvfile
        dialect = self.get_dialect()

        self.get_reader(dialect)
        self.csv_headers, self.csv_content = self.parce_csv()

        self.csvfile.seek(0)
        next(self.reader)

        self.check_headers_presence()
        self.check_req_info_presence()

        if len(self.empty_cells) > 0:
            return len(self.empty_cells)
        else:
            self.get_csv_by_header_uniqued()
            return 0

    def get_dialect(self):
        try:
            dialect = csv.Sniffer().sniff(codecs.EncodedFile(self.csvfile, "utf-8").read(1024), delimiters=',')
        except csv.Error as e:
            self.errors.append('Warning for %s: %s' % (self.csvfile, e))
        except:
            raise
        else:
            if dialect:
              self.csvfile.seek(0)
              print "dialect.delimiter"
              print dialect.delimiter
              # print dir(dialect)
              # ['__doc__', '__init__', '__module__', '_name', '_valid', '_validate', 'delimiter', 'doublequote', 'escapechar', 'lineterminator', 'quotechar', 'quoting', 'skipinitialspace']

              # print "----"
              return dialect
            else:
              print("WARNING, file %s is empty (size = %s), check it's path" % (self.csvfile.name, self.csvfile.size))

    def get_reader(self, dialect):
        try:
            self.csvfile.open()
            self.reader = csv.reader(codecs.EncodedFile(self.csvfile, "utf-8"), delimiter=',', dialect=dialect)
        except csv.Error as e:
            self.errors.append('%s is not a valid CSV file: %s' % (self.csvfile, e))
        except:
            raise

    def get_csv_by_header(self):
        for row in zip(*self.csv_content):
            self.csv_by_header[row[0]] = row[1:]

    def get_csv_by_header_uniqued(self):
        self.csv_by_header_uniqued = ""
        self.csv_by_header_uniqued = dict((x[0], list(set(x[1:]))) for x in zip(*self.csv_content))

    def get_initial_run_info_data_dict(self):
        print "get_initial_run_info_data_dict"
        
        try:
            csv_rundate = "".join(self.csv_by_header_uniqued['rundate'])

            self.run_info_from_csv = {
                'csv_rundate':          csv_rundate,
                'csv_path_to_raw_data': "/xraid2-2/sequencing/Illumina/%s%s" % (csv_rundate, self.selected_machine_short),
                'csv_platform':	        "".join(self.csv_by_header_uniqued['platform']),
                'csv_dna_region':	    "".join(self.csv_by_header_uniqued['dna_region']),
                'csv_overlap':		    "".join(self.csv_by_header_uniqued['overlap']),
                'csv_has_ns':		    "".join(self.csv_by_header_uniqued['rundate']),
                'csv_seq_operator':	    "".join(self.csv_by_header_uniqued['op_seq']),
                'csv_insert_size':	    "".join(self.csv_by_header_uniqued['insert_size']),
                'csv_read_length':	    "".join(self.csv_by_header_uniqued['read_length'])
            }

            # print "RRR self.run_info_from_csv"
            # print self.run_info_from_csv
        except KeyError as e:
            self.cause = e.args[0]
            self.errors.append(self.no_data_message())
        except:
            raise

    def parce_csv(self):
      for y_index, row in enumerate(self.reader):
          # print "parce_csv row"
          # print row

          self.csv_content.append(row)
          if y_index == 0:
              self.csv_headers = [header_name.lower() for header_name in row if header_name]
              continue
      return self.csv_headers, self.csv_content

    def check_headers_presence(self):
      missing_headers = set(self.required_headers) - set([r.lower() for r in self.csv_headers])
      # print "self.csv_headers = " 
      # print self.csv_headers
      if missing_headers:
          missing_headers_str = ', '.join(missing_headers)
          self.errors.append('Missing headers: %s' % (missing_headers_str))
          # print "self.errors 3"
          # print self.errors
          # raise ValidationError(u'Missing headers: %s' % (missing_headers_str))
          return False
      return True

    def check_req_info_presence(self):
        empty_cells_interim = []
        for row in self.reader:
            for header in self.csv_headers:
                if header in self.required_headers:
                    ind = self.csv_headers.index(header)
                    # print "header = %s; row[ind] = %s" % (header, row[ind])
                    if not row[ind]:
                        empty_cells_interim.append(header)
                        # print "NOOOO"
        self.empty_cells = list(set(empty_cells_interim))

    def run_query_to_dict(self, query):
        res_dict = {}
        cursor = connection.cursor()
        cursor.execute(query)

        column_names = [d[0] for d in cursor.description]

        for row in cursor:
          res_dict = dict(zip(column_names, row))

        return res_dict
      # dump it to a json string
      # self.vamps_submissions = json.dumps(info)

    def get_vamps_submission_info(self, db_name = "test_vamps"):
        # todo: get db_name depending on local/not
        out_file_name = "temp_subm_info"
        try:
            for submit_code in self.csv_by_header_uniqued['submit_code']:
                # print "submit_code = %s" % submit_code
                query_subm = """SELECT subm.*, auth.user, auth.passwd, auth.first_name, auth.last_name, auth.active, auth.security_level, auth.email, auth.institution, auth.date_added
                    FROM %s.vamps_submissions AS subm
                    JOIN %s.vamps_auth AS auth
                      ON (auth.id = subm.vamps_auth_id)
                    WHERE submit_code = \"%s\"""" % (db_name, db_name, submit_code)
                self.vamps_submissions[submit_code] = self.run_query_to_dict(query_subm)
            # print "self.vamps_submissions = %s" % self.vamps_submissions
        except KeyError as e:
            self.cause = e.args[0]
            self.errors.append(self.no_data_message())
        except:
            raise

    # def benchmark_w_return_1(self):
    #   print  "\n"
    #   print "-" * 10
    #   return time.time()
    #
    # def benchmark_w_return_2(self, t0):
    #   t1 = time.time()
    #   total = float(t1-t0) / 60
    #   print 'time: %.2f m' % total

    def get_adaptor_from_csv_content(self):
        for i in xrange(len(self.csv_content)-1):
            # print "+" * 9
            adaptor    = self.csv_by_header['adaptor'][i]
            dna_region = self.csv_by_header['dna_region'][i]
            domain     = self.csv_by_header['domain'][i]

            self.get_adaptors_full(adaptor, dna_region, domain)

    def get_all_adaptors(self, db_name = "test_env454"):
        return models_l_env454.IlluminaAdaptorRef.cache_all_method.select_related('illumina_adaptor', 'illumina_index', 'illumina_run_key', 'dna_region')

    def get_adaptors_full(self, adaptor, dna_region, domain, db_name = "test_env454"):
        # self.adaptor_ref
        # links = models_l_env454.IlluminaAdaptorRef.cache_all_method.select_related('illumina_adaptor', 'illumina_index', 'illumina_run_key', 'dna_region')
        # print links.filter(Q(illumina_adaptor_id__illumina_adaptor = "A04") | Q(illumina_adaptor_id__illumina_adaptor = "A08"))

        key = "_".join([adaptor, dna_region, domain])
        mm = self.adaptor_ref.filter(illumina_adaptor_id__illumina_adaptor = adaptor).filter(dna_region_id__dna_region = dna_region).filter(domain = domain)

        # print "self.adaptors_full timing 2"
        # t0 = self.utils.benchmark_w_return_1()
        self.adaptors_full = {key: (row.illumina_index, row.illumina_run_key) for row in mm}
        # self.utils.benchmark_w_return_2(t0)

    def get_user_info(self, db_name = "test_env454"):
        print "HERE1"
        # todo: get db_name depending on local/not
        try:
            print "HERE2"
            # TODO: collect submit_code and vamps_user_id into a dict, run one query with "OR"
            for submit_code in self.csv_by_header_uniqued['submit_code']:
                print "submit_code = %s, self.vamps_submissions[submit_code]['user'] = %s" % (submit_code, self.vamps_submissions[submit_code]['user'])
                vamps_user_id = self.vamps_submissions[submit_code]['user']
                print "CCC1 vamps_user_id = %s" % vamps_user_id

                contacts = models_l_env454.Contact.cache_all_method.get(vamps_name = vamps_user_id)
                # .filter(vamps_name = vamps_user_id)

                # print "CCC contacts = %s" % contacts

                # for row in contacts:
                self.user_info_arr[submit_code] = model_to_dict(contacts)

                # self.user_info_arr.append({submit_code: (model_to_dict(row)) for row in contacts})

            # print "self.user_info_arr = %s" % self.user_info_arr
        except KeyError as e:
            print "HERE3"
            self.cause = e.args[0]
            print "self.cause"
            print self.cause
            self.errors.append(self.no_data_message())
            self.errors.append(" Or the vamps_submission has no such submit_code.")
            print "self.no_data_message()"
            print self.no_data_message()
        except:
            print "HERE4"
            
            raise

    def get_selected_variables(self, request_post):
        # change from form if needed
        # machine_shortcuts_choices = dict(models.Machine.MACHINE_SHORTCUTS_CHOICES)

        if 'submit_run_info' in request_post:
            self.selected_machine       = request_post.get('csv_platform', False)
            # print "self.selected_machine in request_post= %s" % (self.selected_machine)
            self.selected_machine_short = self.machine_shortcuts_choices[self.selected_machine]
            self.selected_rundate       = request_post.get('csv_rundate', False)
            self.selected_dna_region    = request_post.get('csv_dna_region', False)
            self.selected_overlap       = request_post.get('csv_overlap', False)
        else:
            # print "self.csv_by_header_uniqued['platform']"
            # print self.csv_by_header_uniqued['platform']
            self.selected_machine = " ".join(self.csv_by_header_uniqued['platform']).lower()
            # print "self.selected_machine 2 = %s" % self.selected_machine
            # print "MMM self.machine_shortcuts_choices"
            # print self.machine_shortcuts_choices
            self.selected_machine_short = self.machine_shortcuts_choices[self.selected_machine]
            # print "self.selected_machine_short 2 = %s" % self.selected_machine_short

            self.selected_rundate = " ".join(self.csv_by_header_uniqued['rundate']).lower()

    def create_path_to_csv(self):
        # /xraid2-2/g454/run_new_pipeline/illumina/miseq_info/20160711
        # print "self.selected_machine from create_path_to_csv = %s" % (self.selected_machine)

        self.path_to_csv = os.path.join(settings.ILLUMINA_RES_DIR, self.selected_machine + "_info", self.selected_rundate)
        print "self.path_to_csv"
        print self.path_to_csv
        new_dir = self.dirs.check_and_make_dir(self.path_to_csv)

    def get_lanes_domains(self):
        for idx, val in self.out_metadata.items():
            domain_letter = self.domain_choices[val['domain']]
            self.lanes_domains.append("%s_%s" % (val['lane'], domain_letter))
        # print "self.lanes_domains = %s" % self.lanes_domains
        return self.lanes_domains

    def create_out_file_names(self, pattern):
        return {lane_domain: pattern % (self.selected_rundate, self.selected_machine_short, lane_domain) for lane_domain in self.lanes_domains}

    def create_ini_names(self):
        self.ini_names = self.create_out_file_names("%s_%s_%s_run_info.ini")

    def make_out_metadata_csv_file_names(self):
        # OLD: metadata_20160803_1_B.csv
        # NEW: metadata_20151111_hs_1_A.csv
        self.metadata_csv_file_names = self.create_out_file_names("metadata_%s_%s_%s.csv")

    def write_ini(self):
        path_to_raw_data = "/xraid2-2/sequencing/Illumina/%s%s/" % (self.selected_rundate, self.selected_machine_short)
        overlap_choices = dict(models.Overlap.OVERLAP_CHOICES)

        for lane_domain, ini_name in self.ini_names.items():
            ini_text = '''{"rundate":"%s","lane_domain":"%s","dna_region":"%s","path_to_raw_data":"%s","overlap":"%s","machine":"%s"}
                        ''' % (self.selected_rundate, lane_domain, self.selected_dna_region, path_to_raw_data, overlap_choices[self.selected_overlap], self.selected_machine)
            ini_file = open(os.path.join(self.path_to_csv, ini_name), 'w')
            ini_file.write(ini_text)
            ini_file.close()

    def write_out_metadata_to_csv(self, my_post_dict, request):
        print "write_out_metadata_to_csv"
        writers = {}
        for lane_domain in self.metadata_csv_file_names.keys():
            writers[lane_domain] = csv.DictWriter(open(os.path.join(self.path_to_csv, self.metadata_csv_file_names[lane_domain]), 'ab'), self.HEADERS_TO_CSV)
            writers[lane_domain].writeheader()

        for idx, val in self.out_metadata.items():
            # todo: DRY
            domain_letter = self.domain_choices[val['domain']]
            lane_domain = "%s_%s" % (val['lane'], domain_letter)

            to_write = {h: val[h] for h in self.HEADERS_TO_CSV}

            writers[lane_domain].writerow(to_write)

    def check_out_csv_files(self):
        for lane_domain, file_name in self.metadata_csv_file_names.items():
            if os.path.isfile(os.path.join(self.path_to_csv, file_name)):
                self.files_created.append(os.path.join(self.path_to_csv, file_name))

    def update_out_metadata(self, my_post_dict, request):
        print "update_out_metadata"
        # ???
        for header in self.HEADERS_TO_CSV:
            for i in self.out_metadata.keys():
                try:
                    self.out_metadata[i][header] = my_post_dict['form-' + str(i) + '-' + header]
                except MultiValueDictKeyError, e:
                    pass
                except:
                    raise

    def edit_out_metadata(self, request):
        print "edit_out_metadata"

        # print "FROM edit_out_metadata: request.session['out_metadata']"
        # print request.session['out_metadata']

        self.out_metadata = request.session['out_metadata']

        for i, v in self.out_metadata.items():
            # print "i = %s" % i
            self.out_metadata[i]['dna_region']		    = request.POST.get('csv_dna_region', False)
            self.out_metadata[i]['has_ns']			    = request.POST.get('csv_has_ns', False)
            self.out_metadata[i]['insert_size']		    = request.POST.get('csv_insert_size', False)
            self.out_metadata[i]['overlap']			    = request.POST.get('csv_overlap', False)
            self.out_metadata[i]['path_to_raw_data']	= request.POST.get('csv_path_to_raw_data', False)
            self.out_metadata[i]['platform']			= request.POST.get('csv_platform', False)
            self.out_metadata[i]['read_length']			= request.POST.get('csv_read_length', False)
            self.out_metadata[i]['run']				    = request.POST.get('csv_rundate', False)
            self.out_metadata[i]['seq_operator']		= request.POST.get('csv_seq_operator', False)

            # TODO:
            # ? 'overlap': 'hs_complete' now!

        # print "self.out_metadata = %s" % self.out_metadata

    def edit_out_metadata_table(self, request):
        print "edit_out_metadata_table"
        
        self.out_metadata_table = request.session['out_metadata_table']

        print "OOO request.session['run_info_form_post']['csv_has_ns']"
        print request.session['run_info_form_post']['csv_has_ns']

        for x in range(0, len(self.out_metadata_table['rows'])):
            adaptor    = request.POST['form-'+str(x)+'-adaptor']
            dna_region = request.session['run_info_form_post']['csv_dna_region']
            domain     = request.POST['form-'+str(x)+'-domain']

            key = "_".join([adaptor, dna_region, domain])

            self.get_adaptors_full(adaptor, dna_region, domain)
            # nnnn = ""
            
            try:
                self.out_metadata_table['rows'][x]['barcode_index'] = self.adaptors_full[key][0].illumina_index
                # if (request.session['run_info_form_post']['csv_has_ns'] == 'yes'):
                #     nnnn = "NNNN"
                # self.out_metadata_table['rows'][x]['run_key']       = nnnn + self.adaptors_full[key][1].illumina_run_key
                self.out_metadata_table['rows'][x]['run_key']       = self.adaptors_full[key][1].illumina_run_key
            except KeyError:
                self.out_metadata_table['rows'][x]['barcode_index'] = ""
                self.out_metadata_table['rows'][x]['run_key']       = ""
            except:
                raise

    def add_out_metadata_table_to_out_metadata(self, request):
        print "add_out_metadata_table_to_out_metadata"
        
        nnnn = ""
        # TODO: benchmark
        for x in range(0, len(request.session['out_metadata_table']['rows'])):
            print "SSS1 self.out_metadata_table['rows'][x]['run_key']"
            print self.out_metadata_table['rows'][x]['run_key']
            for header in self.HEADERS_TO_EDIT_METADATA:
                if (self.out_metadata_table['rows'][x][header] != request.POST['form-'+str(x)+'-' + header]):
                    self.out_metadata_table['rows'][x][header] = request.POST['form-'+str(x)+'-' + header]
                    
            if (request.session['run_info_form_post']['csv_has_ns'] == 'yes') and not self.out_metadata_table['rows'][x]['run_key'].startswith("NNNN"):
                nnnn = "NNNN"
            self.out_metadata_table['rows'][x]['run_key'] = nnnn + request.POST['form-'+str(x)+'-' + 'run_key']

            print "SSS2 self.out_metadata_table['rows'][x]['run_key']"
            print self.out_metadata_table['rows'][x]['run_key']
                    

    def edit_post_metadata_table(self, request):
        print "edit_post_metadata_table"
        
        my_post_dict = request.POST.copy()
        my_post_dict['form-TOTAL_FORMS']   = len(request.session['out_metadata'].keys())
        my_post_dict['form-INITIAL_FORMS'] = len(request.session['out_metadata'].keys())
        my_post_dict['form-MAX_NUM_FORMS'] = len(request.session['out_metadata_table'].keys())
        
        
        nnnn = ""
        for x in range(0, len(request.session['out_metadata_table']['rows'])):
            print "SSS3 self.out_metadata_table['rows'][x]['run_key']"
            print self.out_metadata_table['rows'][x]['run_key']
            my_post_dict['form-'+str(x)+'-barcode_index'] = self.out_metadata_table['rows'][x]['barcode_index']
            if (request.session['run_info_form_post']['csv_has_ns'] == 'yes') and not self.out_metadata_table['rows'][x]['run_key'].startswith("NNNN"):
                nnnn = "NNNN"
            my_post_dict['form-'+str(x)+'-run_key']       = nnnn + self.out_metadata_table['rows'][x]['run_key']
            
            print "SSS4 self.out_metadata_table['rows'][x]['run_key']"
            print self.out_metadata_table['rows'][x]['run_key']
                                
        return my_post_dict

    def make_new_out_metadata(self):
        print "make_new_out_metadata"
        idx = 0
        # print "self.csv_content = %s, len(self.csv_content) = %s" % (self.csv_content, len(self.csv_content))
        # print "self.csv_content[0] =  head = %s" % (self.csv_content[0])

        # print " &&&&&&& list(set(self.csv_content[0]) & set(self.HEADERS_TO_CSV))"
        # a = list(set(self.csv_content[0]) & set(self.HEADERS_TO_CSV))
        # print a
        # ['barcode_index', 'lane', 'dna_region', 'read_length', 'env_sample_source_id', 'barcode', 'overlap', 'dataset_description', 'adaptor', 'primer_suite', 'insert_size']

        # print "self.csv_by_header = %s" % self.csv_by_header

        # print "UUU self.adaptors_full = %s" % self.adaptors_full
        # {'A08_v4v5_bacteria': (<IlluminaIndex: ACTTGA>, <IlluminaRunKey: TACGC>)}
        # print self.adaptors_full['A08_v4v5_bacteria'][0].illumina_index

        self.get_user_info()
        if self.errors:
            return
            
        for i in xrange(len(self.csv_content)-1):

            curr_submit_code = self.csv_by_header['submit_code'][i]
            print "self.user_info_arr[curr_submit_code] = "
            print self.user_info_arr[curr_submit_code]

            adaptor    = self.csv_by_header['adaptor'][i]
            dna_region = self.csv_by_header['dna_region'][i]
            domain     = self.csv_by_header['domain'][i]

            self.get_adaptors_full(adaptor, dna_region, domain)

            key = "_".join([adaptor, dna_region, domain])

            # print i
            self.out_metadata[i]['adaptor']				 = self.csv_by_header['adaptor'][i]
            self.out_metadata[i]['amp_operator']		 = self.csv_by_header['op_amp'][i]
            self.out_metadata[i]['barcode']				 = self.csv_by_header['barcode'][i]
            self.out_metadata[i]['barcode_index']		 = self.csv_by_header['barcode_index'][i]
            try:
                if (self.out_metadata[i]['barcode_index'] == ""):
                    self.out_metadata[i]['barcode_index'] = self.adaptors_full[key][0].illumina_index
            except KeyError:
                self.out_metadata[i]['barcode_index'] = ""
            except:
                raise

            # self.out_metadata[i]['contact_name']         = self.user_info_arr[curr_submit_code]['last_name'] + ', ' + self.user_info_arr[curr_submit_code]['first_name']
            # <option value="36">Nicole Webster</option>
            # self.out_metadata[i]['contact_name']         = self.user_info_arr[curr_submit_code]['contact_id']
            self.out_metadata[i]['contact_name']         = self.user_info_arr[curr_submit_code]['first_name'] + ' ' + self.user_info_arr[curr_submit_code]['last_name']
            self.out_metadata[i]['data_owner']           = self.out_metadata[i]['contact_name']

            self.out_metadata[i]['dataset']				 = self.csv_by_header['dataset_name'][i]
            self.out_metadata[i]['dataset_description']	 = self.csv_by_header['dataset_description'][i]
            # TODO:
            # $combined_metadata[$num]["dataset_id"]         = get_id($combined_metadata[$num], "dataset", $db_name, $connection);
            # TODO:
            # $combined_metadata[$num]["date_initial"]       = $session["vamps_submissions_arr"][$csv_metadata_row["submit_code"]]["date_initial"];
            # TODO:
            # $combined_metadata[$num]["date_updated"]       = date("Y-m-d");

            self.out_metadata[i]['dna_region']			 = self.csv_by_header['dna_region'][i]
            # TODO:
            # $combined_metadata[$num]["dna_region_id"]      = get_id($session["run_info"], "dna_region_0", $db_name, $connection);

            # TODO: make dropdown menu, camelize, choose
            self.out_metadata[i]['domain']			     = self.csv_by_header['domain'][i]
            self.out_metadata[i]['email']                = self.user_info_arr[curr_submit_code]['email']
            self.out_metadata[i]["env_sample_source_id"] = self.csv_by_header['env_sample_source_id'][i];
            self.out_metadata[i]['env_source_name']      = self.csv_by_header['env_sample_source_id'][i]
            self.out_metadata[i]['first_name']           = self.user_info_arr[curr_submit_code]['first_name']
            self.out_metadata[i]['funding']                = self.vamps_submissions[curr_submit_code]['funding']

            # print "self.csv_by_header['submit_code'][i] = %s" % self.csv_by_header['submit_code'][i]
            # print "self.vamps_submissions[curr_submit_code]['institution'] = %s" % self.vamps_submissions[curr_submit_code]['institution']

            self.out_metadata[i]['insert_size']			 = self.csv_by_header['insert_size'][i]
            self.out_metadata[i]['institution']			 = self.vamps_submissions[curr_submit_code]['institution']
            self.out_metadata[i]['lane']				 = self.csv_by_header['lane'][i]
            self.out_metadata[i]['last_name']            = self.user_info_arr[curr_submit_code]['last_name']
            # TODO:
            # $combined_metadata[$num]["locked"]             = $session["vamps_submissions_arr"][$csv_metadata_row["submit_code"]]["locked"];
            # $combined_metadata[$num]["num_of_tubes"]       = $session["vamps_submissions_arr"][$csv_metadata_row["submit_code"]]["num_of_tubes"];
            # self.out_metadata[i]['nnnn']                 = self.csv_by_header['lane'][i]
            # $combined_metadata[$num]["op_empcr"]           = $csv_metadata_row["op_empcr"];

            self.out_metadata[i]['overlap']				 = self.csv_by_header['overlap'][i]
            self.out_metadata[i]['primer_suite']		 = self.csv_by_header['primer_suite'][i]
            # TODO:
            # $combined_metadata[$num]["primer_suite_id"]    = get_primer_suite_id($combined_metadata[$num]["dna_region"], $combined_metadata[$num]["domain"], $db_name, $connection);

            self.out_metadata[i]['project']				 = self.csv_by_header['project_name'][i]
            self.out_metadata[i]['project_description']	 = self.vamps_submissions[curr_submit_code]['project_description']
            try:
                self.out_metadata[i]['project_title']		= self.vamps_submissions[curr_submit_code]['title']
            except KeyError:
                try:
                    self.out_metadata[i]['project_title']       = self.vamps_submissions[curr_submit_code]['project_title']
                except KeyError:
                    self.out_metadata[i]['project_title']       = ""
            except:
                raise

            self.out_metadata[i]['read_length']			 = self.csv_by_header['read_length'][i]

            # TODO: get from session["run_info"]["seq_operator"] (run_info upload)
            try:
                self.out_metadata[i]['run_key'] = self.adaptors_full[key][1].illumina_run_key
            except KeyError:
                self.out_metadata[i]['run_key']                = ""
            except:
                raise

            # if (self.csv_by_header['run_key'][i] == ""):
            #     self.out_metadata[i]['run_key'] = self.adaptors_full[key][1].illumina_run_key

            # TODO: get from session["run_info"]["seq_operator"] (run_info upload)
            # self.out_metadata[i]['seq_operator']       = self.csv_by_header['seq_operator'][i]
            self.out_metadata[i]['tubelabel']			 = self.csv_by_header['tube_label'][i]

        # print "self.out_metadata = %s" % self.out_metadata

    def make_metadata_table(self):
        print "make_metadata_table"
        
        self.out_metadata_table['headers'] = self.HEADERS_TO_EDIT_METADATA

        for i in xrange(len(self.out_metadata.keys())):
            self.out_metadata_table['rows'].append({})

        # print "OOO self.out_metadata_table = %s" % self.out_metadata_table

        for r_num, v in self.out_metadata.items():
            for header in self.HEADERS_TO_EDIT_METADATA:
                try:
                    self.out_metadata_table['rows'][int(r_num)][header] = (self.out_metadata[r_num][header])
                except KeyError, e:
                    print "KeyError, e = %s" % e
                    self.out_metadata_table['rows'][int(r_num)][header] = ""
                except:
                    raise

        # print "self.out_metadata_table BBB = %s" % self.out_metadata_table

    def add_new_project(self, request_post):
        project_name = request_post['project_0'] + "_" + request_post['project_1'] + "_" + request_post['project_2'] + request_post['project_3']

        owner = models_l_env454.Contact.cache_all_method.get(contact = request_post['contact'])

        # print "NNN project_name = %s, project_title = %s, funding = %s, env_sample_source_id = %s, contact_id = %d" % (project_name, request_post['project_title'], request_post['funding'], request_post['env_source_name'], owner.contact_id)

        return models_l_env454.Project.objects.get_or_create(project=project_name, title=request_post['project_title'], project_description=request_post['project_description'], rev_project_name=project_name[::-1], funding=request_post['funding'], env_sample_source_id=request_post['env_source_name'], contact_id=owner.contact_id)

        # return created

    def csv_file_upload(self, request):

        csv_file = request.FILES['csv_file']
        if csv_file.size == 0:
            self.errors.append("The file %s is empty or does not exist." % csv_file)
            return ("", 'no_file')

            # render(request, 'submission/upload_metadata.html', {'errors': self.errors, 'errors_size': len(self.errors) })

        has_empty_cells = self.import_from_file(csv_file)

        if has_empty_cells:                
            self.errors.append("The following csv fields should not be empty: %s" % ", ".join(self.empty_cells))
            return ("", 'has_empty_cells')

        # TODO:
        # validate size and type of the file
        # tmp_path = 'tmp/%s' % csv_file
        # default_storage.save(tmp_path, ContentFile(csv_file.file.read()))
        # full_tmp_path = os.path.join(settings.BASE_DIR, tmp_path)
        # - See more at: http://blog.hayleyanderson.us/2015/07/18/validating-file-types-in-django/#sthash.Ux4hWNaD.dpuf
        # csv_validation = Validation()
        # csv_validation.required_cell_values_validation()

        self.get_initial_run_info_data_dict()
        self.get_selected_variables(request.POST)
        request.session['run_info_from_csv'] = self.run_info_from_csv
        metadata_run_info_form = CsvRunInfoUploadForm(initial=request.session['run_info_from_csv'])

        # # TODO: move to one method in metadata_tools, call from here as create info and create csv
        # request.session['lanes_domains'] = self.get_lanes_domains()
        # del request.session['lanes_domains']

        self.get_vamps_submission_info()

        self.get_csv_by_header()

        self.get_adaptor_from_csv_content()

        self.make_new_out_metadata()
        if self.errors:
            return (metadata_run_info_form, has_empty_cells)
            
        request.session['out_metadata'] = self.out_metadata

        # TODO: use to get db_names
        print "self.utils.is_local(request) = %s" % self.utils.is_local(request)
        # utils.is_local(request) = True

        # utils.is_local(request)
        # HOSTNAME = request.get_host()
        # if HOSTNAME.startswith("localhost"):
        #     print "local"

        return (metadata_run_info_form, has_empty_cells)

    def submit_new_project(self, request):
        # print "EEE: request.POST = %s" % request.POST

        # request.session['run_info_from_csv'] = self.run_info_from_csv
        # print "request.session['run_info_from_csv'] 111 = "
        # print request.session['run_info_from_csv']

        metadata_run_info_form = CsvRunInfoUploadForm(initial=request.session['run_info_from_csv'])

        metadata_new_project_form = AddProjectForm(request.POST)

        if metadata_new_project_form.is_valid():        
            # print "!!!metadata_new_project_form.cleaned_data"
            # print metadata_new_project_form.cleaned_data
            """
            !!!metadata_new_project_form.cleaned_data
            {'env_source_name': <EnvSampleSource: 0: >, 'project_description': u'www', 'funding': u'rrr', 'project_title': u'sss', 'project': u'dfsdfs_dsfsdfs_B_v6', 'contact': <Contact: Eric Boyd>}

            """

            self.new_project, self.new_project_created = self.add_new_project(request.POST)

        return metadata_new_project_form

    def submit_run_info(self, request):
        self.get_selected_variables(request.POST)
        request.session['run_info'] = {}
        request.session['run_info']['selected_rundate']         = self.selected_rundate
        request.session['run_info']['selected_machine_short']   = self.selected_machine_short
        request.session['run_info']['selected_machine']         = self.selected_machine
        request.session['run_info']['selected_dna_region']      = self.selected_dna_region
        request.session['run_info']['selected_overlap']         = self.selected_overlap

        print "RRR request.POST from submit_run_info"
        print request.POST

            # self.out_metadata[i]['nnnn']                 = self.csv_by_header['lane'][i]

        #*) metadata table to show and edit
        self.edit_out_metadata(request)
        request.session['out_metadata'] = self.out_metadata

        self.make_metadata_table()

        # metadata_run_info_form = CsvRunInfoUploadForm(initial=request.session['run_info_from_csv'])
        metadata_run_info_form = CsvRunInfoUploadForm(request.POST)
        request.session['run_info_form_post'] = request.POST

        MetadataOutCsvFormSet = formset_factory(MetadataOutCsvForm, max_num = len(self.out_metadata_table['rows']))
        formset = MetadataOutCsvFormSet(initial=self.out_metadata_table['rows'])

        request.session['out_metadata_table'] = self.out_metadata_table

        return (request, metadata_run_info_form, formset)

    def create_submission_metadata_file(self, request):
        # print "EEE: request.POST = %s" % request.POST

        """
        *) metadata table to show and edit
        *) metadata out edit
        *) ini and csv machine_info/run dir
        *) ini files
        *) metadata csv files
        """

        #*) metadata table to show and edit
        self.edit_out_metadata_table(request)
        metadata_run_info_form = CsvRunInfoUploadForm(request.session['run_info_form_post'])

        MetadataOutCsvFormSet = formset_factory(MetadataOutCsvForm)

        my_post_dict = self.edit_post_metadata_table(request)

        self.add_out_metadata_table_to_out_metadata(request)

        #*) metadata out edit
        self.out_metadata = request.session['out_metadata']
        self.update_out_metadata(my_post_dict, request)

        # adaptor    = self.csv_by_header['adaptor'][i]
        # dna_region = self.csv_by_header['dna_region'][i]
        # domain     = self.csv_by_header['domain'][i]
        #
        # self.get_adaptors_full(adaptor, dna_region, domain)

        # ----
        self.selected_rundate       = request.session['run_info']['selected_rundate']
        self.selected_machine_short = request.session['run_info']['selected_machine_short']
        self.selected_machine       = request.session['run_info']['selected_machine']
        self.selected_dna_region    = request.session['run_info']['selected_dna_region']
        self.selected_overlap       = request.session['run_info']['selected_overlap']

        #*) ini and csv machine_info/run dir
        self.get_lanes_domains()
        self.create_path_to_csv()

        # *) validation
        formset = MetadataOutCsvFormSet(my_post_dict)

        if len(metadata_run_info_form.errors) == 0 and formset.total_error_count() == 0:

            #*) ini files
            self.create_ini_names()
            self.write_ini()

            #*) metadata csv files
            self.make_out_metadata_csv_file_names()
            self.write_out_metadata_to_csv(my_post_dict, request)

            # *) check if csv was created
            self.check_out_csv_files()

        return (request, metadata_run_info_form, formset)