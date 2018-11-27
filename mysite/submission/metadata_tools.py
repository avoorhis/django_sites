from __future__ import unicode_literals
from .forms import RunForm, FileUploadForm, CsvRunInfoUploadForm, MetadataOutCsvForm, AddProjectForm
from .utils import Utils, Dirs
from collections import defaultdict
from datetime import datetime
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.db import connections
from django.db.models import Q
from django.forms import formset_factory
from django.forms.models import model_to_dict
from django.shortcuts import render
from django.utils.datastructures import MultiValueDictKeyError
import codecs
import csv
from .model_choices import Overlap, Machine, Domain
from .models_l_env454 import *
from .models_l_vamps import VampsSubmissionsTubes
import io
import os, sys
import stat
import time
import logging

class CsvFile():
    """ in files, parse
    can be
    1) new (from vamp2)
    2) old (from vamps)
    3) manual
    """
    def __init__(self, metadata_obj, out_files_obj, selected_vals_obj):
        self.utils = Utils()
        self.metadata = metadata_obj
        self.out_files = out_files_obj
        self.selected_vals = selected_vals_obj

        self.csv_by_header = defaultdict(list)
        self.csv_by_header_uniqued = defaultdict(list) # public
        self.csv_content = []
        self.csv_headers = []
        self.vamps2_csv = False
        self.csv_file_in = ""
        self.run_info_from_csv = {}
        self.errors = set() # public

        self.HEADERS_FROM_CSV = {
            'id': {'field': 'id', 'required': True},
            'submit_code': {'field': 'submit_code', 'required': True},
            'user': {'field': 'user', 'required': True},
            'tube_number': {'field': 'tube_number', 'required': True},
            'tubelabel': {'field': 'tubelabel', 'required': False},
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

        self.HEADERS_FROM_vamps2_CSV = {
            'adaptor'            : {'field': 'adaptor', 'required': True},
            'amp_operator'       : {'field': 'amp_operator', 'required': True},
            'barcode'            : {'field': 'barcode', 'required': False},
            'barcode_index'      : {'field': 'barcode_index', 'required': False},
            'data_owner'         : {'field': 'data_owner', 'required': True},
            'dataset'            : {'field': 'dataset', 'required': True},
            'dataset_description': {'field': 'dataset_description', 'required': False},
            'dna_region'         : {'field': 'dna_region', 'required': True},
            'email'              : {'field': 'email', 'required': True},
            'env_source_name'    : {'field': 'env_source_name', 'required': True},
            'first_name'         : {'field': 'first_name', 'required': True},
            'funding'            : {'field': 'funding', 'required': True},
            'insert_size'        : {'field': 'insert_size', 'required': True},
            'institution'        : {'field': 'institution', 'required': True},
            'lane'               : {'field': 'lane', 'required': True},
            'last_name'          : {'field': 'last_name', 'required': True},
            'overlap'            : {'field': 'overlap', 'required': True},
            'platform'           : {'field': 'platform', 'required': True},
            'primer_suite'       : {'field': 'primer_suite', 'required': True},
            'project'            : {'field': 'project', 'required': True},
            'project_description': {'field': 'project_description', 'required': True},
            'project_title'      : {'field': 'project_title', 'required': True},
            'read_length'        : {'field': 'read_length', 'required': True},
            'run'                : {'field': 'run', 'required': True},
            'run_key'            : {'field': 'run_key', 'required': False},
            'seq_operator'       : {'field': 'seq_operator', 'required': True},
            'tubelabel'          : {'field': 'tubelabel', 'required': False},
        }


        self.all_headers = set(self.out_files.HEADERS_TO_CSV + self.metadata.HEADERS_TO_EDIT_METADATA + list(self.HEADERS_FROM_vamps2_CSV.keys()) + list(self.HEADERS_FROM_CSV.keys()))
        # {'platform', 'barcode', 'tubelabel', 'project_description', 'project', 'domain', 'id', 'tube_number', 'runkey', 'dataset', 'project_name', 'op_empcr', 'adaptor', 'run_key', 'date_initial', 'insert_size', 'on_vamps', 'pool', 'concentration', 'data_owner', 'seq_operator', 'institution', 'sample_received', 'enzyme', 'project_title', 'email', 'env_source_name', 'duplicate', 'barcode_index', 'read_length', 'primer_suite', 'quant_method', 'trim_distal', 'env_sample_source_id', 'user', 'first_name', 'run', 'submit_code', 'dataset_name', 'direction', 'tubelabel', 'rundate', 'date_updated', 'last_name', 'amp_operator', 'dna_region', 'op_seq', 'op_amp', 'funding', 'lane', 'overlap', 'dataset_description', 'contact_name'}

        self.required_headers = [header_name for header_name, values in
                                 self.HEADERS_FROM_CSV.items() if values['required']]

        self.required_headers_vamps2 = [header_name for header_name, values in
                                 self.HEADERS_FROM_vamps2_CSV.items() if values['required']]

    def import_from_file(self, csv_file_in):
        logging.info("import_from_file")

        self.csv_file_in = csv_file_in
        dialect = self.get_dialect()

        self.get_dict_reader()
        self.get_reader(dialect)
        # self.csv_headers, self.csv_content =
        self.parce_csv()

        self.check_headers_presence()
        self.check_req_info_presence()

        if len(self.empty_cells) > 0:
            return len(self.empty_cells)
        else:
            self.get_csv_by_header_uniqued()
            return 0

    def get_dialect(self):
        try:
            open_file = codecs.EncodedFile(self.csv_file_in, "utf-8")
            open_file_part = open_file.read(1024).decode("utf-8")
            # dialect = csv.Sniffer().sniff(codecs.EncodedFile(self.csv_file_in, "utf-8").read(1024), delimiters=',')
            dialect = csv.Sniffer().sniff(open_file_part)  # , delimiters=','
        except csv.Error as e:
            logging.warning("Warning for %s: %s' % (self.csv_file_in, e)")
            pass
            # self.errors.append('Warning for %s: %s' % (self.csv_file_in, e))
        except:
            raise
        else:
            if dialect:
                self.csv_file_in.seek(0)
                logging.info("dialect.delimiter")
                logging.info(dialect.delimiter)
                # logging.info(dir(dialect))
                # ['__doc__', '__init__', '__module__', '_name', '_valid', '_validate', 'delimiter', 'doublequote', 'escapechar', 'lineterminator', 'quotechar', 'quoting', 'skipinitialspace']

                # logging.info("----")
                return dialect
            else:
                logging.warning("WARNING, file %s is empty (size = %s), check it's path" % (
                self.csv_file_in.name, self.csv_file_in.size))

    def get_dict_reader(self):
        try:
            self.csv_file_in.seek(0)
            self.dict_reader = list(csv.DictReader(io.StringIO(self.csv_file_in.read().decode('utf-8'))))
        except csv.Error as e:
            self.errors.add('%s is not a valid CSV file: %s' % (self.csv_file_in, e))
        except:
            raise

    def get_reader(self, dialect):
        # import io
        try:
            self.csv_file_in.seek(0)
            self.reader = csv.reader(io.StringIO(self.csv_file_in.read().decode('utf-8')))

        except csv.Error as e:
            self.errors.add('%s is not a valid CSV file: %s' % (self.csv_file_in, e))
        except:
            raise

    def get_csv_by_header(self):
        temp_d_from_csv = {}
        for row in zip(*self.csv_content):
            temp_d_from_csv[row[0]] = row[1:]
        self.csv_by_header = self.utils.make_an_empty_dict_from_set(self.all_headers)
        self.csv_by_header.update(temp_d_from_csv)

    def get_csv_by_header_uniqued(self):
        self.csv_by_header_uniqued = self.utils.make_an_empty_dict_from_set(self.all_headers)
        temp_d_from_csv = dict((x[0], list(set(x[1:]))) for x in zip(*self.csv_content))
        self.csv_by_header_uniqued.update(temp_d_from_csv)

    def parce_csv(self):
        self.csv_content = [row for row in self.reader]
        self.csv_headers = [header_name.lower() for header_name in self.csv_content[0]]

    def check_headers_presence(self):
        missing_headers = set()
        if 'submit_code' in self.csv_headers:
            missing_headers = set(self.required_headers) - set([r.lower() for r in self.csv_headers])
        else:
            missing_headers = set(self.required_headers_vamps2) - set([r.lower() for r in self.csv_headers])
            self.vamps2_csv = True

        if missing_headers:
            missing_headers_str = ', '.join(missing_headers)
            self.errors.add('Missing headers: %s' % (missing_headers_str))
            return False
        return True

    def check_req_info_presence(self):
        empty_cells_interim = []
        for row in self.reader:
            for header in self.csv_headers:
                if header in self.required_headers:
                    ind = self.csv_headers.index(header)
                    # logging.debug("header = %s; row[ind] = %s" % (header, row[ind])
                    if not row[ind]:
                        empty_cells_interim.append(header)
                        # logging.debug("NOOOO")
        self.empty_cells = list(set(empty_cells_interim))

    def get_initial_run_info_data_dict(self):
        logging.info("get_initial_run_info_data_dict")

        if self.vamps2_csv:
            csv_rundate = "".join(self.csv_by_header_uniqued['run'])
            self.run_info_from_csv['csv_seq_operator'] = ""
        else:
            csv_rundate = "".join(self.csv_by_header_uniqued['rundate'])
            self.run_info_from_csv['csv_seq_operator'] = "".join(self.csv_by_header_uniqued['op_seq'])

        try:
            platform = "".join(self.csv_by_header_uniqued['platform']).lower()
            selected_machine_short = self.selected_vals.get_selected_machine_short(platform)

            self.run_info_from_csv = {
                'csv_rundate'         : csv_rundate,
                'csv_path_to_raw_data': "/xraid2-2/sequencing/Illumina/%s%s" % (
                csv_rundate, selected_machine_short),
                'csv_platform'        : platform,
                'csv_dna_region'      : "".join(self.csv_by_header_uniqued['dna_region']),
                'csv_overlap'         : "".join(self.csv_by_header_uniqued['overlap']),
                # 'csv_has_ns':		    "".join(self.csv_by_header_uniqued['rundate']),
                'csv_insert_size'     : "".join(self.csv_by_header_uniqued['insert_size']),
                'csv_read_length'     : "".join(self.csv_by_header_uniqued['read_length'])
            }

            # logging.debug("RRR self.run_info_from_csv"
            # logging.debug(self.run_info_from_csv)
        except KeyError as e:
            self.cause = e.args[0]
            self.errors.add(self.no_data_message())
        except:
            raise

    def get_adaptor_from_csv_content(self):
        for i in range(len(self.csv_content)-1):
            # logging.debug("+" * 9)
            adaptor    = self.csv_by_header['adaptor'][i]
            dna_region = self.csv_by_header['dna_region'][i]
            try:
                domain     = self.csv_by_header['domain'][i]
            except IndexError:
                domain = self.metadata.domains_per_row[i]
            except:
                raise

            self.metadata.get_adaptors_full(adaptor, dna_region, domain)

    def csv_file_upload(self, request):
        csv_file_in = request.FILES['csv_file']
        if csv_file_in.size == 0:
            self.errors.add("The file %s is empty or does not exist." % csv_file_in)
            return ('no_file')

        has_empty_cells = self.import_from_file(csv_file_in)

        if has_empty_cells: # should create errors not here
            self.errors.add("The following csv fields should not be empty: %s" % ", ".join(self.empty_cells))
            return ('has_empty_cells')

    def get_csv_projects(self):
        csv_projects = set()
        for i in range(len(self.csv_content)-1):
            if self.csv_by_header['project_name']:
                csv_projects.add(self.csv_by_header['project_name'][i])
            elif self.csv_by_header['project']:
                csv_projects.add(self.csv_by_header['project'][i])
        return csv_projects

class SelectedVals():
    def __init__(self, request, METADATA_NAMES):
        self.machine_shortcuts_choices = dict(Machine.MACHINE_SHORTCUTS_CHOICES)
        self.METADATA_NAMES = METADATA_NAMES
        self.current_selected_data = {
            "selected_dna_region"   : "",
            "selected_machine"      : "",
            "selected_machine_short": "",
            "selected_overlap"      : "",
            "selected_rundate"      : ""
        }

    def get_selected_machine_short(self, platform):
        selected_machine_short = self.machine_shortcuts_choices[platform]
        self.current_selected_data["selected_machine_short"] = selected_machine_short
        return selected_machine_short

    def fill_out_request_session_run_info(self, selected_data):
        if selected_data:
            self.current_selected_data = selected_data

        current_run_info = {}
        current_run_info['selected_rundate'] = self.current_selected_data["selected_rundate"]
        current_run_info['selected_machine_short'] = self.current_selected_data["selected_machine_short"]
        current_run_info['selected_machine'] = self.current_selected_data["selected_machine"]
        current_run_info['selected_dna_region'] = self.current_selected_data["selected_dna_region"]
        current_run_info['selected_overlap'] = self.current_selected_data["selected_overlap"]

        return current_run_info

    def get_selected_variables(self, request):
        # change from form if needed
        current_selected_data = self.current_selected_data
        selected_machine_short = self.current_selected_data["selected_machine_short"]

        for selected_name, metadata_names_arr in self.METADATA_NAMES.items():
            current_selected_data[selected_name] = self.get_selected_val(request, metadata_names_arr)

        try:
            current_selected_data["selected_machine_short"] = selected_machine_short or self.machine_shortcuts_choices[current_selected_data["selected_machine"]] #            platform = "".join(self.csv_by_header_uniqued['platform']).lower()    # selected_machine_short = self.selected_vals.get_selected_machine_short(platform)
        except KeyError:
            pass
        except:
            raise

        if current_selected_data:
            self.current_selected_data = current_selected_data

        return self.current_selected_data

    def get_selected_val(self, request, metadata_names_arr):
        for metadata_name in metadata_names_arr:
            # if metadata_name == 'csv_plarform':
            #     print(metadata_name)
            selected_val = request.POST.get(metadata_name, False)
                # self.get_selected_val(run_info_dict, metadata_name)
            if (not selected_val):
                selected_val = request.session.get(metadata_name, False)
            else:
                return selected_val.lower()


    # def get_selected_variables(self, request_post, csv_by_header_uniqued):
    #     # change from form if needed
    #     # if 'submit_run_info' in request_post:
    #     try:
    #         self.current_selected_data["selected_machine"]       = request_post.get('csv_platform', False) or  " ".join(csv_by_header_uniqued['platform']).lower()
    #         self.current_selected_data["selected_machine_short"] = self.current_selected_data["selected_machine_short"] or self.machine_shortcuts_choices[self.current_selected_data["selected_machine"]]
    #         self.current_selected_data["selected_rundate"]       = request_post.get('csv_rundate', False) or " ".join(csv_by_header_uniqued['run']).lower()
    #         self.current_selected_data["selected_dna_region"]    = request_post.get('csv_dna_region', False) or " ".join(csv_by_header_uniqued['dna_region']).lower()
    #         self.current_selected_data["selected_overlap"]       = request_post.get('csv_overlap', False) or " ".join(csv_by_header_uniqued['overlap']).lower()
    #     except KeyError:
    #         logging.debug("csv_by_header_uniqued")
    #         logging.debug(csv_by_header_uniqued)
    #         pass
    #     except:
    #         raise

class OutFiles():
    # out files
    def __init__(self, request, metadata_obj, out_files_obj):
        self.request = request
        self.metadata_obj = metadata_obj
        self.out_files_obj = out_files_obj
        try:
            self.current_selected_data = self.request.session['run_info']
        except KeyError:
            self.current_selected_data = self.out_files_obj.current_selected_data
        except:
            raise

        self.metadata_csv_file_names = {}
        self.files_created = []  # public
        self.dirs = Dirs()
        self.lanes_domains = []
        self.HEADERS_TO_CSV = ['adaptor', 'amp_operator', 'barcode', 'barcode_index', 'data_owner', 'dataset', 'dataset_description', 'dna_region', 'email', 'env_sample_source_id', 'first_name', 'funding', 'insert_size', 'institution', 'lane', 'last_name', 'overlap', 'platform', 'primer_suite', 'project', 'project_description', 'project_title', 'read_length', 'run', 'run_key', 'seq_operator', 'tubelabel']

    def create_ini_names(self, out_metadata):
        self.ini_names = self.create_out_file_names("%s_%s_%s_run_info.ini", out_metadata)

    def create_out_file_names(self, pattern, out_metadata):
        self.lanes_domains = self.metadata_obj.get_lanes_domains(out_metadata)

        return {lane_domain: pattern % (self.current_selected_data["selected_rundate"], self.current_selected_data["selected_machine_short"], lane_domain) for lane_domain in self.lanes_domains} #create in Metadata

    def create_out_metadata_csv_file_names(self, out_metadata):
        # OLD: metadata_20160803_1_B.csv
        # NEW: metadata_20151111_hs_1_A.csv
        self.metadata_csv_file_names = self.create_out_file_names("metadata_%s_%s_%s.csv", out_metadata)

    def write_out_metadata_to_csv(self, path_to_csv, out_metadata):
        logging.info("write_out_metadata_to_csv")

        writers = {}
        self.create_out_metadata_csv_file_names(out_metadata)
        for lane_domain in self.metadata_csv_file_names.keys():
            writers[lane_domain] = csv.DictWriter(open(os.path.join(path_to_csv, self.metadata_csv_file_names[lane_domain]), 'w'), self.HEADERS_TO_CSV)
            writers[lane_domain].writeheader()

        i = 0
        for idx, val in out_metadata.items():
            lane_domain = self.metadata_obj.get_lane_domain(val)
            i = i+1
            # for h in self.HEADERS_TO_CSV:
            #     logging.debug("TTT idx = %s, val = %s, h = %s, val[h] = %s" % (idx, val, h, val[h]))

            to_write = {h: val[h] for h in self.HEADERS_TO_CSV} #primer_suite err

            writers[lane_domain].writerow(to_write)

    def check_out_csv_files(self, path_to_csv = None):
        for lane_domain, file_name in self.metadata_csv_file_names.items():
            if os.path.isfile(os.path.join(path_to_csv, file_name)):
                curr_file = os.path.join(path_to_csv, file_name)
                self.files_created.append(curr_file)
                self.dirs.chmod_wg(curr_file)

    def create_path_to_csv(self, selected_data): #change to use self.current_selected_data
        # /xraid2-2/g454/run_new_pipeline/illumina/miseq_info/20160711

        path_to_csv = os.path.join(settings.ILLUMINA_RES_DIR, selected_data["selected_machine"] + "_info", selected_data["selected_rundate"])
        logging.debug("path_to_csv")
        logging.debug(path_to_csv)
        new_dir = self.dirs.check_and_make_dir(path_to_csv)
        return path_to_csv

    def write_ini(self, path_to_csv):
        path_to_raw_data = "/xraid2-2/sequencing/Illumina/%s%s/" % (self.current_selected_data["selected_rundate"], self.current_selected_data["selected_machine_short"])
        overlap_choices = dict(Overlap.OVERLAP_CHOICES)

        for lane_domain, ini_name in self.ini_names.items():
            ini_text = '''{"rundate":"%s","lane_domain":"%s","dna_region":"%s","path_to_raw_data":"%s","overlap":"%s","machine":"%s"}
                        ''' % (self.current_selected_data["selected_rundate"], lane_domain, self.current_selected_data["selected_dna_region"], path_to_raw_data, overlap_choices[self.current_selected_data["selected_overlap"]], self.current_selected_data["selected_machine"])
            full_ini_name = os.path.join(path_to_csv, ini_name)
            ini_file = open(full_ini_name, 'w')
            ini_file.write(ini_text)
            ini_file.close()
            self.dirs.chmod_wg(full_ini_name)


class Metadata():
    """
    data independent of if it comes from a file, db or a form
    """
    def __init__(self, request):
        self.utils = Utils()
        self.mysql_util = MysqlUtil()
        self.vamps_submissions = {}
        # self.selected_machine_short = ""
        # self.selected_machine = ""
        # self.selected_rundate = ""
        self.domains_per_row = []
        self.errors = set() # public
        self.user_info_arr = {}
        # self.machine_shortcuts_choices = dict(Machine.MACHINE_SHORTCUTS_CHOICES)
        self.domain_choices = dict(Domain.LETTER_BY_DOMAIN_CHOICES)
        self.adaptor_ref = self.get_all_adaptors()
        self.adaptors_full = {}

        # To MysqlUtil?
        self.db_prefix = ""
        if (self.utils.is_local(request)):
            self.db_prefix = "test_"

        self.HEADERS_TO_EDIT_METADATA = ['domain', 'lane', 'contact_name', 'run_key', 'barcode_index', 'adaptor', 'project', 'dataset', 'dataset_description', 'env_source_name', 'tubelabel', 'barcode', 'amp_operator']

        self.METADATA_NAMES = {}
        self.METADATA_NAMES['selected_machine'] = ['csv_platform', 'platform']
        self.METADATA_NAMES['selected_machine_short'] = ['selected_machine_short', '']
        self.METADATA_NAMES['selected_rundate'] = ['csv_rundate', 'run']
        self.METADATA_NAMES['selected_dna_region'] = ['csv_dna_region', 'dna_region']
        self.METADATA_NAMES['selected_overlap'] = ['csv_overlap', 'overlap']


    def get_lanes_domains(self, out_metadata):
        domain_choices = dict(Domain.LETTER_BY_DOMAIN_CHOICES)
        lanes_domains = []

        for idx, val in out_metadata.items():
            domain_letter = domain_choices[val['domain']]
            lanes_domains.append("%s_%s" % (val['lane'], domain_letter))
        # logging.debug("self.lanes_domains = %s" % self.lanes_domains)
        return lanes_domains

    # TODO combine with previous
    def get_lane_domain(self, out_metadata_entry):
        domain_choices = dict(Domain.LETTER_BY_DOMAIN_CHOICES)
        domain_letter = domain_choices[out_metadata_entry['domain']]
        return "%s_%s" % (out_metadata_entry['lane'], domain_letter)

    # def get_selected_variables(self, request_post, csv_by_header_uniqued):
    #     # change from form if needed
    #     # if 'submit_run_info' in request_post:
    #     try:
    #         self.selected_machine       = request_post.get('csv_platform', False) or  " ".join(csv_by_header_uniqued['platform']).lower()
    #         self.selected_machine_short = self.selected_machine_short or self.machine_shortcuts_choices[self.selected_machine]
    #         self.selected_rundate       = request_post.get('csv_rundate', False) or " ".join(csv_by_header_uniqued['run']).lower()
    #         self.selected_dna_region    = request_post.get('csv_dna_region', False) or " ".join(csv_by_header_uniqued['dna_region']).lower()
    #         self.selected_overlap       = request_post.get('csv_overlap', False) or " ".join(csv_by_header_uniqued['overlap']).lower()
    #     except KeyError:
    #         logging.debug("csv_by_header_uniqued")
    #         logging.debug(csv_by_header_uniqued)
    #         pass
    #         # self.selected_machine = " ".join(csv_by_header_uniqued['platform']).lower()
    #         # self.selected_machine_short = self.machine_shortcuts_choices[self.selected_machine]
    #         # self.selected_rundate = " ".join(csv_by_header_uniqued['rundate']).lower()
    #     except:
    #         raise

    # old vamps
    def get_vamps_submission_info(self, csv_by_header_uniqued):
        db_name = self.db_prefix + "vamps"

        try:
            for submit_code in csv_by_header_uniqued['submit_code']:
                query_subm = """
                SELECT subm.*, auth.username, auth.encrypted_password, auth.first_name, auth.last_name, auth.active, auth.security_level, auth.email, auth.institution, auth.current_sign_in_at, auth.last_sign_in_at
                    FROM %s.vamps_submissions AS subm
                    JOIN vamps2.user AS auth
                      USING(user_id)
                    WHERE submit_code = \"%s\"""" % (db_name, submit_code)

                self.vamps_submissions[submit_code] = self.mysql_util.run_query_to_dict(query_subm, 'vamps')
        except KeyError as e:
            self.cause = e.args[0]
            self.errors.add(self.no_data_message())
        except:
            raise

    def get_vamps2_submission_info(self, project_id = ""):
        db_name = "vamps2"
        try:
            query_subm = """SELECT username AS data_owner, dataset, dataset_description, email, first_name, funding, institution, last_name, project, project_description, title AS project_title, tubelabel
            FROM dataset JOIN project USING(project_id) JOIN user ON(owner_user_id = user_id)
            WHERE project_id = %s""" % (project_id)

            self.vamps2_project_results = self.mysql_util.run_query_to_dict(query_subm, db_name)

            # TODO: check all return self
            return self.vamps2_project_results
        except KeyError as e:
            self.cause = e.args[0]
            self.errors.add(self.no_data_message())
        except:
            raise

    def get_domain_dna_regions(self, data_dict):
        # print("PPP5 data_dict: %s" % data_dict)

        try:
            self.domain_dna_regions = [k.split("_")[-1] for k in [x['project'] for x in data_dict]]
        except KeyError:
            self.domain_dna_regions = [k.split("_")[-1] for k in [x['project_name'] for x in data_dict]]
        except:
            raise

    def get_domain_per_row(self, info_list_len):
        for r in self.domain_dna_regions:
            domain_letter = r[0]
            domain = ""
            # dna_region = r[1:]
            for d, letter in self.domain_choices.items():
                if letter == domain_letter:
                    domain = d
                    break
            self.domains_per_row.append(domain)

    def make_metadata_out_from_project_data(self, vamps2_dict):
        # TODO: test with csv if changes still work from
        primer_suites = self.get_primer_suites()
        info_list_len = len(vamps2_dict)
        self.get_domain_per_row(info_list_len)

        for i in range(info_list_len):
            self.out_metadata[i] = self.utils.make_an_empty_dict_from_set(self.all_headers)
            self.out_metadata[i].update(vamps2_dict[i])

            try: # dump the whole vamps2_dict to out_metadata, then add if key is different
                self.out_metadata[i]['contact_name']         = vamps2_dict[i]['first_name'] + ' ' + vamps2_dict[i]['last_name']
                self.out_metadata[i]['dna_region']			 = self.dna_region
                self.out_metadata[i]['domain']			     = self.domains_per_row[i]
                self.out_metadata[i]['lane']				 = '1' # default
                self.out_metadata[i]['primer_suite']		 = primer_suites[i]
                # TODO: get from session["run_info"]["seq_operator"] (run_info upload)
            except IndexError:
                pass
            except:
                raise

    def get_primer_suites(self):
        primer_suites = []
        print("PPP0 self.domain_dna_regions: %s" % self.domain_dna_regions)

        for r in self.domain_dna_regions:
            domain_letter = r[0]
            dna_region = r[1:]
            print("PPP1 domain_letter: %s" % domain_letter)
            print("PPP2 dna_region: %s" % dna_region)
            print("PPP3 self.suite_domain_choices: %s" % self.suite_domain_choices)
            try:
                primer_suite = self.suite_domain_choices[domain_letter] + ' ' + dna_region.upper() + ' Suite'
            except KeyError:
                primer_suite = ""
            except:
                raise

            primer_suites.append(primer_suite)
        return primer_suites

    def get_all_adaptors(self):
        # db_name = self.db_prefix + "env454"
        return IlluminaAdaptorRef.cache_all_method.select_related('illumina_adaptor', 'illumina_index', 'illumina_run_key', 'dna_region')

    def get_adaptors_full(self, adaptor, dna_region, domain):
        # db_name = self.db_prefix + "env454"
        key = "_".join([adaptor, dna_region, domain])
        mm = self.adaptor_ref.filter(illumina_adaptor_id__illumina_adaptor = adaptor).filter(dna_region_id__dna_region = dna_region).filter(domain = domain)

        # TODO: make once self.adaptors_full.update({})

        # logging.debug("self.adaptors_full timing 2")
        # t0 = self.utils.benchmark_w_return_1()
        self.adaptors_full = {key: (row.illumina_index, row.illumina_run_key) for row in mm}
        # self.utils.benchmark_w_return_2(t0)

    def check_user(self, csv_by_header_uniqued):
        try:
            data_owner = "".join(csv_by_header_uniqued['data_owner'])
            contacts = Contact.cache_all_method.get(vamps_name = data_owner)
        except Contact.DoesNotExist as e:
            self.errors.add("Please add contact information for %s to env454." % data_owner)
        except:
            raise

    def get_user_info(self, csv_by_header_uniqued):
        # db_name = self.db_prefix + "env454"

        try:
            # TODO: collect submit_code and vamps_user_id into a dict, run one query with "OR"
            for submit_code in csv_by_header_uniqued['submit_code']:
                # logging.debug("submit_code = %s, self.vamps_submissions[submit_code]['user'] = %s" % (submit_code, self.vamps_submissions[submit_code]['user']))
                try:
                  vamps_user_id = self.vamps_submissions[submit_code]['username']
                except KeyError as e:
                  user_name_by_submit_code = self.get_user_name_by_submit_code(submit_code)
                  self.errors.add("Please check if contact information for %s exists in VAMPS." % submit_code)
                  return
                except:
                  raise

                try:
                    contacts = Contact.cache_all_method.get(vamps_name = vamps_user_id)
                    self.user_info_arr[submit_code] = model_to_dict(contacts)

                except Contact.DoesNotExist as e:
                    # self.cause = e.args[0]
                    self.errors.add("Please add contact information for %s to env454." % vamps_user_id)
                except:
                    raise
        except:
            raise

    def check_projects(self, csv_projects):
        missing_projects = []
        # for i in range(len(csv_content)-1):
        #     if csv_by_header['project_name']:
        #         csv_project = csv_by_header['project_name'][i]
        #     elif csv_by_header['project']:
        #         csv_project = csv_by_header['project'][i]

        for csv_project in csv_projects:
            try:
                Project.objects.get(project = csv_project)
            except Project.DoesNotExist as e:
                missing_projects.append(csv_project)
            except:
                raise

        missing_projects_list = ", ".join(list(set(missing_projects)))
        if len(missing_projects_list) > 0:
            self.errors.add("Please add project information for %s to env454." % missing_projects_list)


class OutData():
    def __init__(self, request):
        self.metadata = Metadata(request)
        self.selected_vals = SelectedVals(request, self.metadata.METADATA_NAMES)
        self.out_files = OutFiles(request, self.metadata, self.selected_vals)
        self.csv_file = CsvFile(self.metadata, self.out_files, self.selected_vals)
        self.utils = Utils()

        self.out_metadata = defaultdict(lambda: defaultdict(lambda: 0)) # TODO: Why create from scratch each time?
        self.out_metadata_table = defaultdict(list) # public
        self.current_selected_data = defaultdict()
        self.errors = set() # public
        self.request = request

    # TODO: what's a difference with make_metadata_run_info_form?
    def work_with_request(self): #TODO: rename and/or split. Upload and parse file, get_initial run info, get current selected data, fill out request.session run info, makes metadata_run_info_form, get_vamps_submission_info, makes csv_by_header, get_domain_dna_regions, get_domain_per_row, get_adaptor_from_csv_content, check_user or get_user_info, get_csv_projects, check_projects, make_new_out_metadata, collect errors, populate request.session['csv_by_header_uniqued'], populate request.session['out_metadata']

        has_empty_cells = self.csv_file.csv_file_upload(self.request)
        self.csv_file.get_initial_run_info_data_dict()
        self.current_selected_data = self.selected_vals.get_selected_variables(self.request)

        # self.current_selected_data = self.selected_vals.get_selected_variables(self.request.POST, self.csv_file.csv_by_header_uniqued)
        self.request.session['run_info_from_csv'] = self.csv_file.run_info_from_csv
        metadata_run_info_form = CsvRunInfoUploadForm(initial = self.request.session['run_info_from_csv'])

        if not self.csv_file.vamps2_csv:
            self.metadata.get_vamps_submission_info(self.csv_file.csv_by_header_uniqued)

        self.csv_file.get_csv_by_header()

        info_list_len = len(self.csv_file.csv_by_header['dataset'])
        self.metadata.get_domain_dna_regions(self.csv_file.dict_reader)
        self.metadata.get_domain_per_row(info_list_len)
        self.csv_file.get_adaptor_from_csv_content()

        # TODO: DRY
        if self.csv_file.vamps2_csv:
            self.metadata.check_user(self.csv_file.csv_by_header_uniqued)
            self.csv_file.errors.update(self.metadata.errors)  # public

        else:
            self.metadata.get_user_info(self.csv_file.csv_by_header_uniqued)
            self.csv_file.errors.update(self.metadata.errors)  # public

        csv_projects = self.csv_file.get_csv_projects()
        self.metadata.check_projects(csv_projects)

        self.make_new_out_metadata()
        self.errors.update(self.csv_file.errors)

        # self.request.session['csv_by_header_uniqued'] = self.csv_file.csv_by_header_uniqued
        # TODO DRY
        if ( not self.errors ):
            self.request.session['out_metadata'] = self.out_metadata

        return (metadata_run_info_form, has_empty_cells)

    # TODO: rename or join
    def make_metadata_run_info_form(self):

        # selected_data = self.selected_vals.get_selected_variables(self.request.POST, self.request.session['csv_by_header_uniqued'])
        selected_data = self.selected_vals.get_selected_variables(self.request)
        self.request.session['run_info'] = self.selected_vals.fill_out_request_session_run_info(selected_data)

        if (
                'create_vamps2_submission_csv' in self.request.session.keys() and
                self.request.session['create_vamps2_submission_csv']
        ):
            self.create_vamps2_submission_csv(self.request)

        self.edit_out_metadata()
        self.request.session['out_metadata'] = self.out_metadata
        # try:
        #     path_to_csv
        # except NameError:
        #     path_to_csv = self.out_files.create_path_to_csv(selected_data)
        # except:
        #     raise
        #
        path_to_csv = self.out_files.create_path_to_csv(selected_data)
        self.out_files.check_out_csv_files(path_to_csv)
        self.request.session['files_created'] = self.out_files.files_created #doesn't belong here
        self.request.session['run_info_form_post'] = self.request.POST
        self.request.session['out_metadata_table'] = self.out_metadata_table #doesn't belong here

        self.make_metadata_table() #doesn't belong here

        metadata_run_info_form = CsvRunInfoUploadForm(self.request.POST)
        MetadataOutCsvFormSet = formset_factory(MetadataOutCsvForm, max_num = len(self.out_metadata_table['rows']))
        formset = MetadataOutCsvFormSet(initial=self.out_metadata_table['rows'])

        return (self.request, metadata_run_info_form, formset)

    # TODO: 2) how to simplify it (case?)?
    def make_new_out_metadata(self):
        logging.info("make_new_out_metadata")

        if self.request.FILES:
            if (not self.csv_file.vamps2_csv):
                self.make_metadata_out_from_csv()
            else:
                self.make_metadata_out_from_project_data(self.csv_file.dict_reader)
        else:
            if self.vamps2_project_results:
              self.make_metadata_out_from_project_data(self.vamps2_project_results)

    def make_metadata_out_from_csv(self):
        for i in range(len(self.csv_file.csv_content)-1):

            curr_submit_code = self.csv_file.csv_by_header['submit_code'][i]
            adaptor    = self.csv_file.csv_by_header['adaptor'][i]
            dna_region = self.csv_file.csv_by_header['dna_region'][i]
            domain     = self.csv_file.csv_by_header['domain'][i]

            self.metadata.get_adaptors_full(adaptor, dna_region, domain)
            key = "_".join([adaptor, dna_region, domain])

            self.out_metadata[i]['adaptor']				 = self.csv_file.csv_by_header['adaptor'][i]
            self.out_metadata[i]['amp_operator']		 = self.csv_file.csv_by_header['op_amp'][i]
            self.out_metadata[i]['barcode']				 = self.csv_file.csv_by_header['barcode'][i]
            self.out_metadata[i]['barcode_index']		 = self.csv_file.csv_by_header['barcode_index'][i]
            try:
                if (self.out_metadata[i]['barcode_index'] == ""):
                    self.out_metadata[i]['barcode_index'] = self.metadata.adaptors_full[key][0].illumina_index
            except KeyError:
                self.out_metadata[i]['barcode_index'] = ""
            except:
                raise
            try:
                # TODO: change as get_selected
                self.out_metadata[i]['contact_name']         = self.metadata.user_info_arr[curr_submit_code]['first_name'] + ' ' + self.metadata.user_info_arr[curr_submit_code]['last_name']
                self.out_metadata[i]['email'] = self.metadata.user_info_arr[curr_submit_code]['email']
                self.out_metadata[i]['data_owner']           = self.metadata.user_info_arr[curr_submit_code]['vamps_name']
                self.out_metadata[i]['first_name']           = self.metadata.user_info_arr[curr_submit_code]['first_name']
                self.out_metadata[i]['funding']              = self.metadata.vamps_submissions[curr_submit_code]['funding']
                self.out_metadata[i]['institution']			 = self.metadata.vamps_submissions[curr_submit_code]['institution']
                self.out_metadata[i]['last_name']            = self.metadata.user_info_arr[curr_submit_code]['last_name']
                self.out_metadata[i]['project_description']	 = self.metadata.vamps_submissions[curr_submit_code]['project_description']

            except KeyError:
                if not curr_submit_code:
                    logging.error("There is no such submit code in the database: %s" % curr_submit_code)
                    self.csv_file.errors.add("There is no such submit code in the database: %s" % curr_submit_code)

                # else there is no such user info
            except:
                raise

            # TODO: change as get_selected
            self.out_metadata[i]['dataset']				 = self.csv_file.csv_by_header['dataset_name'][i]
            self.out_metadata[i]['dataset_description']	 = self.csv_file.csv_by_header['dataset_description'][i]
            self.out_metadata[i]['dna_region']			 = self.csv_file.csv_by_header['dna_region'][i]
            self.out_metadata[i]['domain']			     = self.csv_file.csv_by_header['domain'][i]
            self.out_metadata[i]["env_sample_source_id"] = self.csv_file.csv_by_header['env_sample_source_id'][i]
            self.out_metadata[i]['env_source_name']      = self.csv_file.csv_by_header['env_sample_source_id'][i]
            self.out_metadata[i]['insert_size']			 = self.csv_file.csv_by_header['insert_size'][i]
            self.out_metadata[i]['lane']				 = self.csv_file.csv_by_header['lane'][i]
            self.out_metadata[i]['overlap']				 = self.csv_file.csv_by_header['overlap'][i]
            self.out_metadata[i]['primer_suite']		 = self.csv_file.csv_by_header['primer_suite'][i]
            self.out_metadata[i]['project']				 = self.csv_file.csv_by_header['project_name'][i]
            try:
                self.out_metadata[i]['project_title']		= self.metadata.vamps_submissions[curr_submit_code]['title']
            except KeyError:
                try:
                    self.out_metadata[i]['project_title']       = self.metadata.vamps_submissions[curr_submit_code]['project_title']
                except KeyError:
                    self.out_metadata[i]['project_title']       = ""
            except:
                raise

            self.out_metadata[i]['read_length']			 = self.csv_file.csv_by_header['read_length'][i]

            try:
                self.out_metadata[i]['run_key'] = self.metadata.adaptors_full[key][1].illumina_run_key
            except KeyError:
                self.out_metadata[i]['run_key']                = ""
            except:
                raise

            try:
                self.out_metadata[i]['tubelabel']			 = self.csv_file.csv_by_header['tubelabel'][i]
                self.out_metadata[i]['tube_label']			 = self.csv_file.csv_by_header['tubelabel'][i]
            except IndexError:
                self.out_metadata[i]['tubelabel'] = self.csv_file.csv_by_header['tube_label'][i]
                self.out_metadata[i]['tube_label'] = self.csv_file.csv_by_header['tube_label'][i]
            except:
                raise
            """
            for VampsSubmissions and VampsSubmissionsTubes:
            """
            #MIMINUM VampsSubmissionsTubes:
            self.out_metadata[i]['direction']   = self.csv_file.csv_by_header['direction'][i]
            self.out_metadata[i]['id']          = self.csv_file.csv_by_header['id'][i]
            self.out_metadata[i]['op_empcr']    = self.csv_file.csv_by_header['op_empcr'][i]
            self.out_metadata[i]['pool']        = self.csv_file.csv_by_header['pool'][i]
            self.out_metadata[i]['submit_code'] = self.csv_file.csv_by_header['submit_code'][i]

    def edit_out_metadata(self):
        logging.info("edit_out_metadata")

        try:
            self.out_metadata = self.request.session['out_metadata']
        except KeyError:
            self.request.session['out_metadata'] = self.out_metadata
        except:
            raise

        for i, v in self.out_metadata.items():
            self.out_metadata[i]['dna_region']		    = self.request.POST.get('csv_dna_region', False)
            self.out_metadata[i]['has_ns']			    = self.request.POST.get('csv_has_ns', False)
            self.out_metadata[i]['insert_size']		    = self.request.POST.get('csv_insert_size', False)
            self.out_metadata[i]['overlap']			    = self.request.POST.get('csv_overlap', False)
            self.out_metadata[i]['path_to_raw_data']	= self.request.POST.get('csv_path_to_raw_data', False)
            self.out_metadata[i]['platform']			= self.request.POST.get('csv_platform', False)
            self.out_metadata[i]['read_length']			= self.request.POST.get('csv_read_length', False)
            self.out_metadata[i]['run']				    = self.request.POST.get('csv_rundate', False)
            self.out_metadata[i]['seq_operator']		= self.request.POST.get('csv_seq_operator', False)

    def update_out_metadata(self, my_post_dict):
        logging.info("update_out_metadata")

        # Check for 'form-2-env_source_name' vs. 'env_sample_source_id'
        for header in self.out_files.HEADERS_TO_CSV:
            for i in self.out_metadata.keys():
                try:
                    self.out_metadata[i][header] = my_post_dict['form-' + str(i) + '-' + header]
                except MultiValueDictKeyError as e:
                    pass
                except:
                    raise

    def make_metadata_table(self):
        logging.info("make_metadata_table")

        self.out_metadata_table['headers'] = self.metadata.HEADERS_TO_EDIT_METADATA

        for i in range(len(self.out_metadata.keys())):
            self.out_metadata_table['rows'].append({})

        # logging.debug("OOO self.out_metadata_table = %s" % self.out_metadata_table)

        for r_num, v in self.out_metadata.items(): #create with all possible headers instead? What fields to show?
            for header in self.metadata.HEADERS_TO_EDIT_METADATA:
                try:
                    self.out_metadata_table['rows'][int(r_num)][header] = (self.out_metadata[r_num][header])
                except KeyError as e:
                    logging.warning("KeyError, e = %s" % e)
                    self.out_metadata_table['rows'][int(r_num)][header] = ""
                except:
                    raise

    def edit_out_metadata_table(self):
        logging.info("edit_out_metadata_table")

        self.out_metadata_table = self.request.session['out_metadata_table']

        # logging.debug("OOO self.request.session['run_info_form_post']['csv_has_ns']")
        # logging.debug(self.request.session['run_info_form_post']['csv_has_ns'])

        for x in range(0, len(self.out_metadata_table['rows'])):
            adaptor    = self.request.POST['form-'+str(x)+'-adaptor']
            dna_region = self.request.session['run_info_form_post']['csv_dna_region']
            domain     = self.request.POST['form-'+str(x)+'-domain']
            env_source_name = self.request.POST['form-' + str(x) + '-env_source_name']

            key = "_".join([adaptor, dna_region, domain])

            self.metadata.get_adaptors_full(adaptor, dna_region, domain)

            try:
                self.out_metadata_table['rows'][x]['barcode_index'] = self.metadata.adaptors_full[key][0].illumina_index
                # if (self.request.session['run_info_form_post']['csv_has_ns'] == 'yes'):
                #     nnnn = "NNNN"
                self.out_metadata_table['rows'][x]['run_key']       = self.metadata.adaptors_full[key][1].illumina_run_key
                self.out_metadata_table['rows'][x]['env_source_name'] = env_source_name
                self.out_metadata_table['rows'][x]['env_sample_source_id'] = env_source_name

            except KeyError:
                self.out_metadata_table['rows'][x]['barcode_index'] = ""
                self.out_metadata_table['rows'][x]['run_key']       = ""
                self.out_metadata_table['rows'][x]['env_source_name'] = 0
                self.out_metadata_table['rows'][x]['env_sample_source_id'] = 0
            except:
                raise

    def add_out_metadata_table_to_out_metadata(self):
        logging.info("add_out_metadata_table_to_out_metadata")

        nnnn = ""
        # TODO: benchmark
        for x in range(0, len(self.request.session['out_metadata_table']['rows'])):
            # logging.debug("SSS1 self.out_metadata_table['rows'][x]['run_key']")
            # logging.debug(self.out_metadata_table['rows'][x]['run_key'])
            for header in self.metadata.HEADERS_TO_EDIT_METADATA:
                if (self.out_metadata_table['rows'][x][header] != self.request.POST['form-'+str(x)+'-' + header]):
                    self.out_metadata_table['rows'][x][header] = self.request.POST['form-'+str(x)+'-' + header]

            # TODO: DRY
            if (self.request.session['run_info_form_post']['csv_has_ns'] == 'yes') and not self.out_metadata_table['rows'][x]['run_key'].startswith("NNNN"):
                nnnn = "NNNN"
            self.out_metadata_table['rows'][x]['run_key'] = nnnn + self.request.POST['form-'+str(x)+'-' + 'run_key']

            # logging.debug("SSS2 self.out_metadata_table['rows'][x]['run_key']")
            # logging.debug(self.out_metadata_table['rows'][x]['run_key'])

    def edit_post_metadata_table(self):
        logging.info("edit_post_metadata_table")

        my_post_dict = self.request.POST.copy()
        my_post_dict['form-TOTAL_FORMS']   = len(self.request.session['out_metadata'].keys())
        my_post_dict['form-INITIAL_FORMS'] = len(self.request.session['out_metadata'].keys())
        my_post_dict['form-MAX_NUM_FORMS'] = len(self.request.session['out_metadata_table'].keys())

        # TODO: move out
        nnnn = ""
        for x in range(0, len(self.request.session['out_metadata_table']['rows'])):
            my_post_dict['form-'+str(x)+'-barcode_index'] = self.out_metadata_table['rows'][x]['barcode_index']
            if (self.request.session['run_info_form_post']['csv_has_ns'] == 'yes') \
                    and not self.out_metadata_table['rows'][x]['run_key'].startswith("NNNN"):
                nnnn = "NNNN"
            my_post_dict['form-'+str(x)+'-run_key']       = nnnn + self.out_metadata_table['rows'][x]['run_key']
        return my_post_dict

    def create_submission_metadata_file(self):  # public
        # logging.debug("EEE: self.request.POST = %s" % self.request.POST)

        """
        *) metadata table to show and edit
        *) metadata out edit
        *) ini and csv machine_info/run dir
        *) ini files
        *) metadata csv files
        """

        # *) metadata table to show and edit
        self.edit_out_metadata_table()
        metadata_run_info_form = CsvRunInfoUploadForm(self.request.session['run_info_form_post'])

        MetadataOutCsvFormSet = formset_factory(MetadataOutCsvForm)

        my_post_dict = self.edit_post_metadata_table()

        self.add_out_metadata_table_to_out_metadata()

        # *) metadata out edit
        self.out_metadata = self.request.session['out_metadata']
        self.update_out_metadata(my_post_dict)

        # adaptor    = self.csv_by_header['adaptor'][i]
        # dna_region = self.csv_by_header['dna_region'][i]
        # domain     = self.csv_by_header['domain'][i]
        #
        # self.get_adaptors_full(adaptor, dna_region, domain)

        #TODO: change as get_selected (for name get...)
        self.current_selected_data = {
            "selected_rundate"      : self.request.session['run_info']['selected_rundate'],
            "selected_machine_short": self.request.session['run_info']['selected_machine_short'],
            "selected_machine"      : self.request.session['run_info']['selected_machine'],
            "selected_dna_region"   : self.request.session['run_info']['selected_dna_region'],
            "selected_overlap"      : self.request.session['run_info']['selected_overlap']
        }

        # *) ini and csv machine_info/run dir
        self.metadata.lanes_domains = self.metadata.get_lanes_domains(self.out_metadata) #move to Metadata?
        # TODO: from here move to OutFiles
        path_to_csv = self.out_files.create_path_to_csv(self.current_selected_data)

        # *) validation
        formset = MetadataOutCsvFormSet(my_post_dict)

        if (len(metadata_run_info_form.errors) == 0 and formset.total_error_count() == 0):

            # *) ini files
            self.out_files.create_ini_names(self.out_metadata, self.metadata)
            self.out_files.write_ini(path_to_csv)

            # *) metadata csv files
            self.out_files.create_out_metadata_csv_file_names(self.out_metadata, self.metadata)
            self.out_files.write_out_metadata_to_csv(path_to_csv, self.out_metadata, self.metadata)

            # *) check if csv was created
            self.out_files.check_out_csv_files(path_to_csv)

            if len(self.vamps_submissions) > 0:
                self.update_submission_tubes(self.request)

        self.new_rundate, self.new_rundate_created = self.insert_run(self.request)
        logging.info(
            "self.new_rundate = %s, self.new_rundate_created = %s" % (self.new_rundate, self.new_rundate_created))

        return (self.request, metadata_run_info_form, formset)


class MysqlUtil():
    def __init__(self):
        pass

    def run_query_to_dict(self, query, connection_name):
        import pprint
        pp = pprint.PrettyPrinter(indent = 4)

        res_dict = {}
        cursor = connections[connection_name].cursor()
        # cursor = connection.cursor()
        cursor.execute(query)

        column_names = [d[0] for d in cursor.description]

        for row in cursor:
            res_dict = dict(zip(column_names, row))

        return res_dict

