# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals
#from django.utils.encoding import python_2_unicode_compatible
from six import python_2_unicode_compatible

from django.db import models

class ModelChoiceIterator(object):
    def __iter__(self):
        if self.field.empty_label is not None:
            yield ("", self.field.empty_label)
        if self.field.cache_choices:
            if self.field.choice_cache is None:
                self.field.choice_cache = [
                    self.choice(obj) for obj in self.queryset.all()
                ]
            for choice in self.field.choice_cache:
                yield choice
        else:
            try:
                for obj in self.queryset:
                    yield self.choice(obj)
            except TypeError:
                for obj in self.queryset.all():
                    yield self.choice(obj)

class AllMethodCachingQueryset(models.query.QuerySet):
    def all(self, get_from_cache=True):
        if get_from_cache:
            return self
        else:
            return self._clone()

class AllMethodCachingManager(models.Manager):
    def get_query_set(self):
        return AllMethodCachingQueryset(self.model, using=self._db)

models.options.DEFAULT_NAMES = models.options.DEFAULT_NAMES + ('env454_db',)

@python_2_unicode_compatible  # only if you need to support Python 2
class Contact(models.Model):
    objects = models.Manager()
    cache_all_method = AllMethodCachingManager()

    contact_id  = models.SmallIntegerField(primary_key=True)
    contact	    = models.CharField(max_length=32)
    email	    = models.CharField(max_length=64)
    institution = models.CharField(max_length=128)
    vamps_name  = models.CharField(max_length=20)
    first_name  = models.CharField(max_length=20, blank=True, null=True)
    last_name   = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'contact'
        unique_together = (('contact', 'email', 'institution'),)

    def __str__(self):
        return self.contact
        # return "%s, %s, %s, %s, %s, %s, %s" % (self.contact_id, self.contact, self.email, self.institution, self.vamps_name, self.first_name, self.last_name)

class Dataset(models.Model):
    dataset_id = models.SmallIntegerField(primary_key=True)
    dataset = models.CharField(unique=True, max_length=64)
    dataset_description = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'dataset'

    def __str__(self):
        return self.dataset

class DnaRegion(models.Model):
    dna_region_id = models.AutoField(primary_key=True, editable=False)
    dna_region    = models.CharField(unique=True, max_length=32, editable=False)

    class Meta:
        managed = False
        db_table = 'dna_region'

    def __str__(self):
        return self.dna_region

class EnvSampleSource(models.Model):
    objects = models.Manager()
    cache_all_method = AllMethodCachingManager()

    env_sample_source_id = models.IntegerField(primary_key=True)
    env_source_name = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'env_sample_source'

    def __str__(self):
        return "%s: %s" % (self.env_sample_source_id, self.env_source_name)

class IlluminaAdaptor(models.Model):
    objects = models.Manager()
    cache_all_method = AllMethodCachingManager()

    illumina_adaptor_id = models.SmallIntegerField(primary_key=True, editable=False)
    illumina_adaptor = models.CharField(unique=True, max_length=3, editable=False)

    class Meta:
        managed = False
        db_table = 'illumina_adaptor'

    def __str__(self):
        return "%s" % (self.illumina_adaptor)

class IlluminaAdaptorRef(models.Model):
    objects = models.Manager()
    cache_all_method = AllMethodCachingManager()

    illumina_adaptor    = models.ForeignKey('IlluminaAdaptor', models.DO_NOTHING, primary_key=True, editable=False)
    illumina_index      = models.ForeignKey('IlluminaIndex', models.DO_NOTHING, editable=False)
    illumina_run_key    = models.ForeignKey('IlluminaRunKey', models.DO_NOTHING, editable=False)
    dna_region          = models.ForeignKey('DnaRegion', models.DO_NOTHING, editable=False)
    domain              = models.CharField(max_length=9, blank=True, null=True, editable=False)

    class Meta:
        managed = False
        db_table = 'illumina_adaptor_ref'
        unique_together = (('illumina_adaptor', 'dna_region', 'domain'),)

    def __str__(self):
        return "%s, %s, %s, %s, %s" % (self.illumina_adaptor, self.illumina_index, self.illumina_run_key, self.dna_region, self.domain)

class IlluminaIndex(models.Model):
    illumina_index_id = models.AutoField(primary_key=True, editable=False)
    illumina_index = models.CharField(unique=True, max_length=6, editable=False)

    class Meta:
        managed = False
        db_table = 'illumina_index'

    def __str__(self):
        return self.illumina_index

class IlluminaRunKey(models.Model):
    illumina_run_key_id = models.AutoField(primary_key=True, editable=False)
    illumina_run_key = models.CharField(unique=True, max_length=5, editable=False)

    class Meta:
        managed = False
        db_table = 'illumina_run_key'

    def __str__(self):
        return self.illumina_run_key

class Primer(models.Model):
    primer_id = models.SmallIntegerField(primary_key=True)
    primer = models.CharField(unique=True, max_length=16)
    direction = models.CharField(max_length=1)
    sequence = models.CharField(max_length=64)
    region = models.CharField(max_length=16)
    original_seq = models.CharField(max_length=64)
    domain = models.CharField(max_length=9, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'primer'

class PrimerSuite(models.Model):
    primer_suite_id = models.SmallIntegerField(primary_key=True)
    primer_suite = models.CharField(unique=True, max_length=25)

    class Meta:
        managed = False
        db_table = 'primer_suite'

    def __str__(self):
        return self.primer_suite

class Project(models.Model):
    objects = models.Manager()
    cache_all_method = AllMethodCachingManager()

    # form_class.base_fields['foo'].queryset = YourModel.cache_all_method.all()

    project_id = models.SmallIntegerField(primary_key=True)
    project = models.CharField(unique=True, max_length=32)
    title = models.CharField(max_length=64)
    project_description = models.CharField(max_length=255)
    rev_project_name = models.CharField(unique=True, max_length=32)
    funding = models.CharField(max_length=64)
    env_sample_source = models.ForeignKey(EnvSampleSource, models.DO_NOTHING)
    contact = models.ForeignKey(Contact, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'project'

    def __str__(self):
        return "%s" % (self.project)

class RefPrimerSuitePrimer(models.Model):
    primer_suite = models.ForeignKey(PrimerSuite, models.DO_NOTHING)
    primer = models.ForeignKey(Primer, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'ref_primer_suite_primer'

class Run(models.Model):
    objects = models.Manager()
    cache_all_method = AllMethodCachingManager()

    run_id = models.SmallIntegerField(primary_key=True)
    run = models.CharField(max_length=16)
    run_prefix = models.CharField(max_length=7)
    date_trimmed = models.DateTimeField()
    platform = models.CharField(max_length=7, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'run'
        unique_together = (('run', 'platform'),)

    def __str__(self):
        return self.run

class RunInfoIll(models.Model):
    objects = models.Manager()
    cache_all_method = AllMethodCachingManager()

    run_info_ill_id = models.AutoField(primary_key=True)
    run_key = models.ForeignKey('RunKey', models.DO_NOTHING)
    run = models.ForeignKey('Run', models.DO_NOTHING)
    lane = models.IntegerField()
    dataset = models.ForeignKey('Dataset', models.DO_NOTHING)
    project = models.ForeignKey('Project', models.DO_NOTHING)
    tubelabel = models.CharField(max_length=32)
    barcode = models.CharField(max_length=4)
    adaptor = models.CharField(max_length=3)
    dna_region = models.ForeignKey('DnaRegion', models.DO_NOTHING)
    amp_operator = models.CharField(max_length=5)
    seq_operator = models.CharField(max_length=5)
    # barcode_index = models.CharField(max_length=12)
    overlap = models.CharField(max_length=8)
    insert_size = models.SmallIntegerField()
    file_prefix = models.CharField(max_length=45)
    read_length = models.SmallIntegerField()
    primer_suite = models.ForeignKey('PrimerSuite', models.DO_NOTHING)
    updated = models.DateTimeField()
    platform = models.CharField(max_length=7, blank=True, null=True)
    illumina_index = models.ForeignKey('IlluminaIndex', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'run_info_ill'
        unique_together = (('run', 'run_key', 'illumina_index', 'lane'),)

    def __str__(self):
        return """run_info_ill_id: %s;
run_key: %s;
run: %s;
lane: %s;
dataset: %s;
project: %s;
tubelabel: %s;
barcode: %s;
adaptor: %s;
dna_region: %s;
amp_operator: %s;
seq_operator: %s;
illumina_index: %s;
overlap: %s;
insert_size: %s;
file_prefix: %s;
read_length: %s;
primer_suite: %s; """ %  (self.run_info_ill_id, self.run_key, self.run, self.lane, self.dataset, self.project, self.tubelabel, self.barcode, self.adaptor, self.dna_region, self.amp_operator, self.seq_operator, self.illumina_index, self.overlap, self.insert_size, self.file_prefix, self.read_length, self.primer_suite)

class RunKey(models.Model):
    run_key_id = models.SmallIntegerField(primary_key=True)
    run_key = models.CharField(unique=True, max_length=25)

    class Meta:
        managed = False
        db_table = 'run_key'
