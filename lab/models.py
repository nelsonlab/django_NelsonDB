from django.db import models
from django.contrib.auth.models import User

"""User Model

class User:
	username
	first_name
	last_name
	email
	password
	is_staff
	is_active
	is_superuser
	last_login
	date_joined
"""

class UserProfile(models.Model):
	user = models.OneToOneField(User)
	website = models.CharField(max_length=250, blank=True)
	picture = models.ImageField(upload_to='profile_images', blank=True)
	phone = models.CharField(max_length=30, blank=True)
	organization = models.CharField(max_length=200, blank=True)
	notes = models.CharField(max_length=1000, blank=True)
	job_title = models.CharField(max_length=200, blank=True)

	def __unicode__(self):
		return self.user.username

class Locality(models.Model):
  city = models.CharField(max_length=200, blank=True)
  state = models.CharField(max_length=200, blank=True)
  country = models.CharField(max_length=200, blank=True)
  zipcode = models.CharField(max_length=30, blank=True)

  def __unicode__(self):
    return self.city

class Field(models.Model):
  locality = models.ForeignKey(Locality)
  field_name = models.CharField(max_length=200, unique=True)
  field_num = models.CharField(max_length=200, blank=True)
  comments = models.CharField(max_length=1000, blank=True)

  def __unicode__(self):
    return self.field_name

class Experiment(models.Model):
  user = models.ForeignKey(User)
  field = models.ForeignKey(Field)
  name = models.CharField(max_length=200, unique=True)
  start_date = models.CharField(max_length=200, blank=True)
  purpose = models.CharField(max_length=1000, blank=True)
  comments = models.CharField(max_length=1000, blank=True)

  def __unicode__(self):
    return self.name

class Publication(models.Model):
  user = models.ForeignKey(User)
  publisher = models.CharField(max_length=200, blank=True)
  name_of_paper = models.CharField(max_length=200, unique=True)
  publish_date = models.DateField()
  publication_info = models.CharField(max_length=200, blank=True)

  def __unicode__(self):
    return self.name_of_paper

class Taxonomy(models.Model):
	genus = models.CharField(max_length=200, blank=True)
	species = models.CharField(max_length=200, blank=True)
	population = models.CharField(max_length=200, blank=True)
	common_name = models.CharField(max_length=200, blank=True)
	alias = models.CharField(max_length=200, blank=True)
	race = models.CharField(max_length=200, blank=True)
	subtaxa = models.CharField(max_length=200, blank=True)

	def __unicode__(self):
		return self.genus

class People(models.Model):
	first_name = models.CharField(max_length=200, blank=True)
	last_name = models.CharField(max_length=200, blank=True)
	organization = models.CharField(max_length=200, blank=True)
	phone = models.CharField(max_length=30, blank=True)
	email = models.CharField(max_length=200, blank=True)
	comments = models.CharField(max_length=1000, blank=True)

	def __unicode__(self):
		return self.organization

class Citation(models.Model):
	citation_type = models.CharField(max_length=200, blank=True)
	title = models.CharField(max_length=200, unique=True)
	url = models.CharField(max_length=300, blank=True)
	pubmed_id = models.CharField(max_length=300, blank=True)
	comments = models.CharField(max_length=1000, blank=True)

	def __unicode__(self):
		return self.title

class Medium(models.Model):
	citation = models.ForeignKey(Citation)
	media_name = models.CharField(max_length=200, unique=True)
	media_type = models.CharField(max_length=200, blank=True)
	media_description = models.CharField(max_length=200, blank=True)
	media_preparation = models.CharField(max_length=200, blank=True)
	comments = models.CharField(max_length=1000, blank=True)

	def __unicode__(self):
		return self.media_name

class ObsRow(models.Model):
  row_id = models.CharField(max_length=200, unique=True)
  row_name = models.CharField(max_length=200, blank=True)
  range_num = models.CharField(max_length=200, blank=True)
  plot = models.CharField(max_length=200, blank=True)
  block = models.CharField(max_length=200, blank=True)
  rep = models.CharField(max_length=200, blank=True)
  kernel_num = models.CharField(max_length=200, blank=True)
  planting_date = models.CharField(max_length=200, blank=True)
  harvest_date = models.CharField(max_length=200, blank=True)
  comments = models.CharField(max_length=3000, blank=True)

  def __unicode__(self):
    return self.row_id

class ObsPlant(models.Model):
  plant_id = models.CharField(max_length=200, unique=True)
  plant_num = models.CharField(max_length=200, blank=True)
  comments = models.CharField(max_length=3000, blank=True)

  def __unicode__(self):
    return self.plant_id

class ObsSample(models.Model):
	sample_id = models.CharField(max_length=200, unique=True)
	sample_type = models.CharField(max_length=200, blank=True)
	weight = models.CharField(max_length=200, blank=True)
	kernel_num = models.CharField(max_length=200, blank=True)
	photo = models.CharField(max_length=200, blank=True)
	comments = models.CharField(max_length=3000, blank=True)

	def __unicode__(self):
		return self.sample_id

class Separation(models.Model):
	obs_sample = models.ForeignKey(ObsSample)
	separation_type = models.CharField(max_length=200, blank=True)
	apparatus = models.CharField(max_length=200, blank=True)
	SG = models.CharField(max_length=200, blank=True)
	light_weight = models.CharField(max_length=200, blank=True)
	intermediate_weight = models.CharField(max_length=200, blank=True)
	heavy_weight = models.CharField(max_length=200, blank=True)
	light_percent = models.CharField(max_length=200, blank=True)
	intermediate_percent = models.CharField(max_length=200, blank=True)
	heavy_percent = models.CharField(max_length=200, blank=True)
	operating_factor = models.CharField(max_length=200, blank=True)
	comments = models.CharField(max_length=1000, blank=True)

	def __unicode__(self):
		return self.separation_type

class ObsExtract(models.Model):
	extract_id = models.CharField(max_length=200, unique=True)
	weight = models.CharField(max_length=200, blank=True)
	rep = models.CharField(max_length=200, blank=True)
	grind_method = models.CharField(max_length=200, blank=True)
	solvent = models.CharField(max_length=200, blank=True)
	comments = models.CharField(max_length=3000, blank=True)

	def __unicode__(self):
		return self.extract_id

class ObsEnv(models.Model):
	environment_id = models.CharField(max_length=200, unique=True)
	longitude = models.CharField(max_length=200, blank=True)
	latitude = models.CharField(max_length=200, blank=True)
	comments = models.CharField(max_length=3000, blank=True)

	def __unicode__(self):
		return self.environment_id

class ObsDNA(models.Model):
	dna_id = models.CharField(max_length=200, unique=True)
	extraction_method = models.CharField(max_length=500, blank=True)
	date = models.CharField(max_length=200, blank=True)
	tube_id = models.CharField(max_length=200, blank=True)
	tube_type = models.CharField(max_length=200, blank=True)
	comments = models.CharField(max_length=3000, blank=True)

	def __unicode__(self):
		return self.dna_id

class ObsTissue(models.Model):
	tissue_id = models.CharField(max_length=200, unique=True)
	tissue_type = models.CharField(max_length=200, blank=True)
	tissue_name = models.CharField(max_length=200, blank=True)
	date_ground = models.CharField(max_length=200, blank=True)
	comments = models.CharField(max_length=3000, blank=True)

	def __unicode__(self):
		return self.tissue_id

class ObsPlate(models.Model):
	plate_id = models.CharField(max_length=200, unique=True)
	plate_name = models.CharField(max_length=200, blank=True)
	date = models.CharField(max_length=200, blank=True)
	contents = models.CharField(max_length=200, blank=True)
	rep = models.CharField(max_length=200, blank=True)
	plate_type = models.CharField(max_length=200, blank=True)
	plate_status = models.CharField(max_length=200, blank=True)
	comments = models.CharField(max_length=3000, blank=True)

	def __unicode__(self):
		return self.plate_id

class ObsWell(models.Model):
	well_id = models.CharField(max_length=200, unique=True)
	well = models.CharField(max_length=200, blank=True)
	well_inventory = models.CharField(max_length=200, blank=True)
	tube_label = models.CharField(max_length=200, blank=True)
	comments = models.CharField(max_length=3000, blank=True)

	def __unicode__(self):
		return self.well_id

class ObsCulture(models.Model):
	medium = models.ForeignKey(Medium)
	culture_id = models.CharField(max_length=200, unique=True)
	culture_name = models.CharField(max_length=200, blank=True)
	microbe_type = models.CharField(max_length=200, blank=True)
	plating_cycle = models.CharField(max_length=200, blank=True)
	dilution = models.CharField(max_length=200, blank=True)
	image_filename = models.CharField(max_length=200, blank=True)
	comments = models.CharField(max_length=3000, blank=True)
	num_colonies = models.CharField(max_length=200, blank=True)
	num_microbes = models.CharField(max_length=200, blank=True)

	def __unicode__(self):
		return self.culture_id

class ObsMicrobe(models.Model):
	microbe_id = models.CharField(max_length=200, unique=True)
	microbe_type = models.CharField(max_length=200, blank=True)
	comments = models.CharField(max_length=3000, blank=True)

	def __unicode__(self):
		return self.microbe_id

class Location(models.Model):
  locality = models.ForeignKey(Locality)
  building_name = models.CharField(max_length=200, blank=True)
  location_name = models.CharField(max_length=200, unique=True)
  room = models.CharField(max_length=200, blank=True)
  shelf = models.CharField(max_length=200, blank=True)
  column = models.CharField(max_length=200, blank=True)
  box_name = models.CharField(max_length=200, blank=True)
  comments = models.CharField(max_length=1000, blank=True)

  def __unicode__(self):
    return self.building_name

class Collecting(models.Model):
  user = models.ForeignKey(User)
  collection_date = models.CharField(max_length=200, blank=True)
  collection_method = models.CharField(max_length=1000, blank=True)
  comments = models.CharField(max_length=1000, blank=True)

  def __unicode__(self):
    return self.collection_date

class Passport(models.Model):
	collecting = models.ForeignKey(Collecting)
	people = models.ForeignKey(People)
	taxonomy = models.ForeignKey(Taxonomy)

	def __unicode__(self):
		return self.taxonomy.genus

class Stock(models.Model):
  passport = models.ForeignKey(Passport)
  seed_id = models.CharField(max_length=200, unique=True)
  seed_name = models.CharField(max_length=200, blank=True)
  cross_type = models.CharField(max_length=200, blank=True)
  pedigree = models.CharField(max_length=200, blank=True)
  stock_status = models.CharField(max_length=200, blank=True)
  stock_date = models.CharField(max_length=200, blank=True)
  inoculated = models.BooleanField(default=False)
  comments = models.CharField(max_length=1000, blank=True)

  def __unicode__(self):
      return self.seed_id

class MaizeSample(models.Model):
  locality = models.ForeignKey(Locality)
  maize_id = models.CharField(max_length=200, unique=True)
  type_of_source = models.CharField(max_length=200, blank=True)
  sample_source = models.CharField(max_length=200, blank=True)
  weight = models.CharField(max_length=200, blank=True)
  description = models.CharField(max_length=200, blank=True)
  photo = models.CharField(max_length=200, blank=True)
  comments = models.CharField(max_length=1000, blank=True)

  def __unicode__(self):
      return self.maize_id

class GlycerolStock(models.Model):
  glycerol_stock_id = models.CharField(max_length=200, unique=True)
  stock_date = models.CharField(max_length=200, blank=True)
  extract_color = models.CharField(max_length=200, blank=True)
  organism = models.CharField(max_length=200, blank=True)
  comments = models.CharField(max_length=1000, blank=True)

  def __unicode__(self):
      return self.glycerol_stock_id

class DiseaseInfo(models.Model):
  common_name = models.CharField(max_length=200, unique=True)
  abbrev = models.CharField(max_length=200, blank=True)
  comments = models.CharField(max_length=1000, blank=True)

  def __unicode__(self):
      return self.common_name

class Isolate(models.Model):
  passport = models.ForeignKey(Passport)
  location = models.ForeignKey(Location)
  disease_info = models.ForeignKey(DiseaseInfo)
  isolate_id = models.CharField(max_length=200, unique=True)
  isolate_name = models.CharField(max_length=200, blank=True)
  plant_organ = models.CharField(max_length=200, blank=True)
  comments = models.CharField(max_length=1000, blank=True)

  def __unicode__(self):
      return self.isolate_id

class StockPacket(models.Model):
  stock = models.ForeignKey(Stock)
  location = models.ForeignKey(Location)
  weight = models.CharField(max_length=200, blank=True)
  num_seeds = models.CharField(max_length=200, blank=True)
  comments = models.CharField(max_length=1000, blank=True)

  def __unicode__(self):
    return self.stock.seed_id

class Treatment(models.Model):
	experiment = models.ForeignKey(Experiment)
	treatment_id = models.CharField(max_length=200, unique=True)
	treatment_type = models.CharField(max_length=200, blank=True)
	date = models.CharField(max_length=200, blank=True)
	comments = models.CharField(max_length=1000, blank=True)

	def __unicode__(self):
		return self.treatment_id

class UploadQueue(models.Model):
	experiment = models.ForeignKey(Experiment)
	user = models.ForeignKey(User)
	file_name = models.FileField(upload_to='upload_queue')
	upload_type = models.CharField(max_length=200, blank=True)
	date = models.DateField(auto_now_add=True)
	completed = models.BooleanField(default=False)
	comments = models.CharField(max_length=1000, blank=True)

	def __unicode__(self):
		return self.file_name

class ObsTracker(models.Model):
	obs_entity_type = models.CharField(max_length=200)
	user = models.ForeignKey(User)
	location = models.ForeignKey(Location, default='1')
	experiment = models.ForeignKey(Experiment, default='1')
	field = models.ForeignKey(Field, default='1')
	isolate = models.ForeignKey(Isolate, default='1')
	stock = models.ForeignKey(Stock, default='1')
	maize_sample = models.ForeignKey(MaizeSample, default='1')
	glycerol_stock = models.ForeignKey(GlycerolStock, default='1')
	obs_culture = models.ForeignKey(ObsCulture, default='1')
	obs_dna = models.ForeignKey(ObsDNA, default='1')
	obs_microbe = models.ForeignKey(ObsMicrobe, default='1')
	obs_plant = models.ForeignKey(ObsPlant, default='1')
	obs_plate = models.ForeignKey(ObsPlate, default='1')
	obs_row = models.ForeignKey(ObsRow, default='1')
	obs_sample = models.ForeignKey(ObsSample, default='1')
	obs_tissue = models.ForeignKey(ObsTissue, default='1')
	obs_well = models.ForeignKey(ObsWell, default='1')
	obs_env = models.ForeignKey(ObsEnv, default='1')
	obs_extract = models.ForeignKey(ObsExtract, default='1')

	def __unicode__(self):
		return self.entity_type

class ObsTrackerSource(models.Model):
	target_obs = models.ForeignKey(ObsTracker, related_name='target_obs_tracker')
	source_obs = models.ForeignKey(ObsTracker, related_name='source_obs_tracker')

	def __unicode__(self):
		return self.target_obs

class MeasurementParameter(models.Model):
	parameter = models.CharField(max_length=200, unique=True)
	parameter_type = models.CharField(max_length=200, blank=True)
	unit_of_measure = models.CharField(max_length=200, blank=True)
	protocol = models.CharField(max_length=1000, blank=True)
	trait_id_buckler = models.CharField(max_length=200, blank=True)

	def __unicode__(self):
		return self.parameter

class Measurement(models.Model):
	obs_tracker = models.ForeignKey(ObsTracker)
	user = models.ForeignKey(User)
	measurement_parameter = models.ForeignKey(MeasurementParameter)
	time_of_measurement = models.CharField(max_length=200, blank=True)
	value = models.CharField(max_length=200, blank=True)
	comments = models.CharField(max_length=1000, blank=True)

	def __unicode__(self):
		return self.value
