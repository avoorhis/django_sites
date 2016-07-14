from datetime import datetime
from .models import *
import csv
import codecs
import time
from .utils import Utils

from django.conf import settings
from django.core.exceptions import ValidationError

from collections import defaultdict

class CsvMetadata():
  
    def __init__(self):
        
        self.RUN_INFO_FORM_FIELD_HEADERS = ["dna_region", "insert_size", "op_seq", "overlap", "read_length", "rundate"]
        self.csv_headers = []
        self.csv_content = []
        self.run_info_from_csv = {}
        self.errors = []
        self.csv_by_header_uniqued = defaultdict( list )
        self.csvfile = ""
        
        # error = True
        
        self.HEADERS = {'id': {'field':'id', 'required':True},
          'submit_code': {'field':'submit_code', 'required':True},
        	'user': {'field':'user', 'required':True},
        	'tube_number': {'field':'tube_number', 'required':True},
        	'tube_label': {'field':'tube_label', 'required':True},
        	'dataset_description': {'field':'dataset_description', 'required':True},
        	'duplicate': {'field':'duplicate', 'required':True},
        	'domain': {'field':'domain', 'required':True},
        	'primer_suite': {'field':'primer_suite', 'required':True},
        	'dna_region': {'field':'dna_region', 'required':True},
        	'project_name': {'field':'project_name', 'required':True},
        	'dataset_name': {'field':'dataset_name', 'required':True},
        	'runkey': {'field':'runkey', 'required':True},
        	'barcode': {'field':'barcode', 'required':True},
        	'pool': {'field':'pool', 'required':True},
        	'lane': {'field':'lane', 'required':True},
        	'direction': {'field':'direction', 'required':True},
        	'platform': {'field':'platform', 'required':True},
        	'op_amp': {'field':'op_amp', 'required':True},
        	'op_seq': {'field':'op_seq', 'required':True},
        	'op_empcr': {'field':'op_empcr', 'required':True},
        	'enzyme': {'field':'enzyme', 'required':True},
        	'rundate': {'field':'rundate', 'required':True},
        	'adaptor': {'field':'adaptor', 'required':True},
        	'date_initial': {'field':'date_initial', 'required':True},
        	'date_updated': {'field':'date_updated', 'required':True},
        	'on_vamps': {'field':'on_vamps', 'required':True},
        	'sample_received': {'field':'sample_received', 'required':True},
        	'concentration': {'field':'concentration', 'required':True},
        	'quant_method': {'field':'quant_method', 'required':True},
        	'overlap': {'field':'overlap', 'required':True},
        	'insert_size': {'field':'insert_size', 'required':True},
        	'barcode_index': {'field':'barcode_index', 'required':True},
        	'read_length': {'field':'read_length', 'required':True},
        	'trim_distal': {'field':'trim_distal', 'required':True},
        	'env_sample_source_id': {'field':'env_sample_source_id', 'required':True},}


        # codeid = models.SmallIntegerField(primary_key=True)
        # remotecode = models.CharField(max_length=32)
        # active = models.BooleanField()
        # created = models.DateField()
        # modified = models.DateField()
        # incentiveid = models.CharField(max_length=32)
        #     


        
    # class Meta:
        # delimiter = ";"
        # dbModel = Code
        
    def get_dialect(self):
        try:
            
            dialect = csv.Sniffer().sniff(codecs.EncodedFile(self.csvfile, "utf-8").read(1024))
            print "dialect = "
            print dialect
            return dialect
            
        except csv.Error as e:
            self.errors.append('%s is not a valid CSV file' % (self.csvfile))
            print "self.errors 1"
            print self.errors
            print "except csv.Error as e:"
            print e
        except:
            raise


    def import_from_file(self, csvfile):
        # print "csvfile from CodeCSvModel.import_from_file"
        self.csvfile = csvfile
        # print self.csvfile
        dialect = self.get_dialect()
        # try:
        #
        #     dialect = csv.Sniffer().sniff(codecs.EncodedFile(self.csvfile, "utf-8").read(1024))
        #     print "dialect = "
        #     print dialect
        #
        # except csv.Error as e:
        #     self.errors.append('%s is not a valid CSV file' % (self.csvfile))
        #     print "self.errors 1"
        #     print self.errors
        #     print "except csv.Error as e:"
        #     print e
            # sys.exit('file %s, line %d: %s' % (filename, reader.line_num, e))
            
        # except csv.Error:
        #     self.errors.append('E Not a valid CSV file')
        #     print "self.errors 1"
        #     print self.errors
            # raise ValidationError(u'Not a valid CSV file')
        # except:
        #     raise
    
        try:
            self.csvfile.open()
            reader = csv.reader(codecs.EncodedFile(self.csvfile, "utf-8"), delimiter=',', dialect=dialect)
        except csv.Error as e:
            self.errors.append('%s is not a valid CSV file' % (self.csvfile))
            print "self.errors 1"
            print self.errors
            print "except csv.Error as e:"
            print e
        except:
            raise
            

        # reader = csv.reader(doc.read().splitlines(), dialect)
        print "from csv_tools reader = "
        print reader
        self.csv_headers = []
        required_headers = [header_name for header_name, values in
                            self.HEADERS.items() if values['required']]
    
        self.csv_headers, self.csv_content = self.parce_csv(reader)
        
        self.csv_by_header = defaultdict( list )
        
        utils = Utils()
        t0 = utils.benchmark_w_return_1()
        for row in zip(*self.csv_content):
            self.csv_by_header[row[0]] = row[1:]
        utils.benchmark_w_return_2(t0)
        
        t0 = utils.benchmark_w_return_1()
        self.csv_by_header_uniqued = dict((x[0], list(set(x[1:]))) for x in zip(*self.csv_content))
        utils.benchmark_w_return_2(t0)
        
        """TODO: time benchmark
        
        import time
        return time.time()
        t1 = time.time()
        print 'time: %.2f m' % total
        
        """
        print "self.csv_by_header_uniqued"
        print self.csv_by_header_uniqued
        print "*" * 8
        # print self.csv_by_header
        # print set(self.csv_by_header['rundate'])
        # print "*" * 8

        # a = self.check_headers_presence(reader, required_headers)
        self.check_headers_presence(reader, required_headers)        
        
        # print "self.check_headers_presence(reader)"
        # print a
    
      
        # writer = csv.DictWriter(doc, 
        #                         ["dna_region", "rundate"])
        #                         
        # for row in self.csv_content:
        #     writer.writerow({'dna_region': row.dna_region, 'rundate': row.rundate})
        #     print writer
            
    def get_initial_run_info_data_dict(self):
        try:
            csv_rundate = "".join(self.csv_by_header_uniqued['rundate'])

            self.run_info_from_csv = {'csv_rundate': csv_rundate, 
            'csv_path_to_raw_data': "/xraid2-2/sequencing/Illumina/%s" % csv_rundate, 
            'csv_dna_region': "".join(self.csv_by_header_uniqued['dna_region']), 
            'csv_overlap': "".join(self.csv_by_header_uniqued['overlap']), 
            'csv_has_ns': "".join(self.csv_by_header_uniqued['rundate']), 
            'csv_seq_operator': "".join(self.csv_by_header_uniqued['op_seq']), 
            'csv_insert_size': "".join(self.csv_by_header_uniqued['insert_size']), 
            'csv_read_length': "".join(self.csv_by_header_uniqued['read_length'])}
        except KeyError as e:
            cause = e.args[0]
            self.errors.append('There is no data for %s in the file %s' % (cause, self.csvfile))
        except:
            raise

    def parce_csv(self, reader):
      for y_index, row in enumerate(reader):
          self.csv_content.append(row)
          # print "self.csv_content 1 = "
          # print self.csv_content
          if y_index == 0:
              self.csv_headers = [header_name.lower() for header_name in row if header_name]
              # print "self.csv_headers 1 = "
              # print self.csv_headers
              continue
      return self.csv_headers, self.csv_content

    def check_headers_presence(self, reader, required_headers):
      missing_headers = set(required_headers) - set([r.lower() for r in self.csv_headers])
      print "missing_headers: "
      print missing_headers
      if missing_headers:
          missing_headers_str = ', '.join(missing_headers)
          # todo: return error_message instead
          self.errors.append('Missing headers: %s' % (missing_headers_str))
          print "self.errors 3"
          print self.errors
          # raise ValidationError(u'Missing headers: %s' % (missing_headers_str))
          
          return False
      return True

    def required_cell_values_validation(reader):
      # sanity check required cell values
      for y_index, row in enumerate(reader):
        # ignore blank rows
        # if not ''.join(str(x) for x in row):
        #     continue

        for x_index, cell_value in enumerate(row):
            # if indexerror, probably an empty cell past the headers col count
            try:
                self.csv_headers[x_index]
            except IndexError:
                continue
            if self.csv_headers[x_index] in required_headers:
                if not cell_value:
                    self.errors.append('Missing required value %s for row %s' %
                                            (self.csv_headers[x_index], y_index + 1))
                    print "self.errors 4"
                    print self.errors

                    
                    # raise ValidationError(u'Missing required value %s for row %s' %
                                            # (self.csv_headers[x_index], y_index + 1))
    