#import filebrowser
#from filebrowser.fields import FileBrowseField
from django import forms
from lab.models import UserProfile, Experiment, Field, ObsRow, ObsPlant, Locality, Stock, ObsRow, ObsPlant, ObsSample, ObsEnv, MeasurementParameter, Citation, Medium, Location, DiseaseInfo, FileDump, Primer
from django.contrib.auth.models import User
from django.core.validators import EmailValidator
import re

class UserForm(forms.ModelForm):
	username = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Username'}), help_text="Choose a username:")
	email = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Email'}), validators=[EmailValidator], help_text="Enter your email:")
	password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password'}), help_text="Select a password:")
	first_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'First Name'}), help_text="First name:")
	last_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Last Name'}), help_text="Last name:")

	class Meta:
		model = User
		fields = ['username', 'password', 'email', 'first_name', 'last_name']

class FileDumpForm(forms.ModelForm):
	user = forms.ModelChoiceField(queryset=User.objects.all(), empty_label="--- Username ---", help_text="Select the primary user:", required=True)
	experiment = forms.ModelChoiceField(queryset=Experiment.objects.all(), empty_label="--- Experiment ---", help_text="Select the experiment if relevant:", required=True)
	file_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'File Name'}), help_text="Give an informative name to the file:")
	file = forms.FileField(help_text="Select your file:")
	comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Comments:'}), help_text="Any additional comments:", required=False)

	class Meta:
		model = FileDump
		fields = ['user', 'experiment', 'file_name', 'file', 'comments']

class SequenceZipfileForm(forms.Form):
	user = forms.ModelChoiceField(queryset=User.objects.all(), empty_label="--- Username ---", help_text="Select the primary user:", required=True)
	experiment = forms.ModelChoiceField(queryset=Experiment.objects.all(), empty_label="--- Experiment ---", help_text="Select the experiment:", required=True)
	measurement_parameter = forms.ModelChoiceField(queryset=MeasurementParameter.objects.all(), empty_label="--- Parameter ---", help_text="Select the sequencing method parameter", required=True)
	primer_f = forms.ModelChoiceField(queryset=Primer.objects.all(), empty_label="--- Forward Primer ---", help_text="Select the primer used:", required=True)
	primer_r = forms.ModelChoiceField(queryset=Primer.objects.all(), empty_label="--- Reverse Primer ---", help_text="Select the primer used:", required=True)
	gene_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Gene Name'}), help_text="Give the gene name:")
	start_physical_position = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Start Position'}), help_text="Give the gene start physical position if known:")
	stop_physical_position = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Stop Position'}), help_text="Give the gene stop physical position if known:")
	chromosome = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Chromosome'}), help_text="Give the gene chromosome:")
	file_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'File Name'}), help_text="Give an informative name to the file:")
	file = forms.FileField(help_text="Select your zip file. Zipped file should contain .seq and .ab1 files that are named according to their sample name:")
	comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Comments:'}), help_text="Any additional comments:", required=False)

class UserProfileForm(forms.ModelForm):
	phone = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Phone Number'}), help_text="Add your phone number:")
	organization = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Organization'}), help_text="Your affiliated organization:")
	job_title = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Job Title'}), help_text="(Optional) Type your job title:", required=False)
	notes = forms.CharField(widget=forms.Textarea(attrs={'placeholder':'Notes','rows': '5', 'cols': '20'}), help_text="(Optional) Add any notes about yourself:", required=False)
	website = forms.URLField(widget=forms.TextInput(attrs={'placeholder':'Website'}), help_text="(Optional) Your website: ", required=False)
	picture = forms.ImageField(widget=forms.ClearableFileInput(), help_text="(Optional) Select a profile image:", initial='profile_images/underwater.jpg', required=False)

	class Meta:
		model = UserProfile
		fields = ['phone','organization','job_title','notes','website', 'picture']

class ChangePasswordForm(forms.ModelForm):
	old_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Old Password'}), help_text="Type your old password:")
	new_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'New Password'}), help_text="Select a new password:")
	new_password_repeat = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Retype New Password'}), help_text="Retype your new password:")

	class Meta:
		model = User
		fields = []

class EditUserForm(forms.ModelForm):
	password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password'}), help_text="Type your password:")
	email = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Email'}), validators=[EmailValidator], help_text="Edit your email:", required=False)
	first_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'First Name'}), help_text="Change you first name:", required=False)
	last_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Last Name'}), help_text="Change your last name:", required=False)

	class Meta:
		model = User
		fields = ['email', 'first_name', 'last_name']

class EditUserProfileForm(forms.ModelForm):
	phone = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Phone Number'}), help_text="Edit your phone number:", required=False)
	organization = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Organization'}), help_text="Edit your affiliated organization:", required=False)
	job_title = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Job Title'}), help_text="Change your job title:", required=False)
	notes = forms.CharField(widget=forms.Textarea(attrs={'placeholder':'Notes','rows': '5', 'cols': '20'}), help_text="Modify any notes about yourself:", required=False)
	website = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Website'}), help_text="Change your website: ", required=False)
	picture = forms.ImageField(help_text="Change your profile image:", required=False)

	class Meta:
		model = UserProfile
		fields = ['phone', 'organization', 'job_title', 'notes', 'website', 'picture']

class NewExperimentForm(forms.Form):
	user = forms.ModelChoiceField(queryset=User.objects.all(), empty_label="--- Username ---", help_text="Select the primary user:", required=True)
	field = forms.ModelChoiceField(queryset=Field.objects.all(), empty_label="--- Field Name ---", help_text="Select a field or select 'No Field':", required=True)
	name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Experiment Name'}), help_text="Assign an experiment name (e.g. 15XY with NO SPACES, UNDERLINES, or SPECIAL CHARACTERS):", required=True)
	start_date = forms.DateField(widget=forms.DateInput(attrs={'placeholder':'Start Date'}), help_text="Give a start date in format MM/DD/YYYY:", required=True)
	purpose = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Purpose'}), help_text="Description of purpose:", required=True)
	comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Comments', 'rows': '5', 'cols': '20'}), help_text="Any additional comments:", required=False)

	def clean_name(self):
		data = self.cleaned_data['name']
		if re.match("^[a-zA-Z0-9]*$", data):
			return data
		else:
			raise forms.ValidationError("Name should contain no special characters, spaces, or underlines!")
		return data

class NewTreatmentForm(forms.Form):
	experiment = forms.ModelChoiceField(queryset=Experiment.objects.all(), empty_label="--- Experiment ---", help_text="Select the experiment:", required=True)
	treatment_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Treatment ID'}), help_text="Assign a unique ID for this treatment:", required=True)
	treatment_type = forms.CharField(widget=forms.DateInput(attrs={'placeholder':'Treatment Type'}), help_text="What kind of treatment (e.g. inoculation, fertilizer):", required=True)
	date = forms.DateField(widget=forms.DateInput(attrs={'placeholder':'Treatment Date'}), help_text="On what date was treatment (01-30-2015):", required=True)
	comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Comments', 'rows': '5', 'cols': '20'}), help_text="Any additional comments:" , required=False)

class NewFieldForm(forms.Form):
	locality = forms.ModelChoiceField(queryset=Locality.objects.all(), empty_label="--- Locality ---", help_text="Select the correct locality:", required=True)
	field_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Field Name'}), help_text="Give a field name:", required=True)
	field_num = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Field Num'}), help_text="What is the field number:", required=False)
	comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Comments'}), help_text="Any additional comments:", required=False)

class NewLocalityForm(forms.Form):
	city = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'City'}), help_text="Type a city name:", required=True)
	state = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'State'}), help_text="What state is the city in:", required=False)
	country = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Country'}), help_text="What country is the state in:", required=False)
	zipcode = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Zipcode'}), help_text="Type the zipcode:", required=False)

class NewPrimerForm(forms.Form):
	primer_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Primer ID'}), help_text="Type a unique primer ID:", required=True)
	primer_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Primer Name'}), help_text="Type an easily identifiable primer name:", required=False)
	primer_tail = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Primer Tail'}), help_text="What is the primer's tail:", required=False)
	size_range = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Size Range'}), help_text="The primer's size range:", required=False)
	temp_min = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Temp Min'}), help_text="The primer's minimum temperature:", required=False)
	temp_max = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Temp Max'}), help_text="The primer's maximum temperature:", required=False)
	order_date = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Order Date'}), help_text="The date the primer was ordered:", required=False)
	comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Comments'}), help_text="Any additional comments:", required=False)

class NewMeasurementParameterForm(forms.Form):
	parameter = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Parameter'}), help_text="Type a new parameter:", required=True)
	parameter_type = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Parameter Type'}), help_text="What type of parameter is this:", required=True)
	protocol = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Protocol'}), help_text="Give a description of the protocol:", required=False)
	trait_id_buckler = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Buckler Trait ID'}), help_text="Give Buckler trait ID if exists:", required=False)
	unit_of_measure = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Unit of Measure'}), help_text="What is the unit of measure:", required=False)

class NewLocationForm(forms.Form):
	locality = forms.ModelChoiceField(queryset=Locality.objects.all(), empty_label="--- Locality ---", help_text="Select the correct locality:", required=True)
	building_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Building Name'}), help_text="Type the building name:", required=True)
	location_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Location Name'}), help_text="Type the location name:", required=True)
	room = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Room'}), help_text="Type the room name or number:", required=False)
	shelf = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Shelf'}), help_text="Give the shelf name or number:", required=False)
	column = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Column'}), help_text="Give the column name or number:", required=False)
	box_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Box Name'}), help_text="Give the box name:", required=False)
	comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Comments'}), help_text="Any additional comments:", required=False)

class NewDiseaseInfoForm(forms.Form):
	common_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Common Name'}), help_text="Type the disease common name:", required=True)
	abbrev = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Abbreviation'}), help_text="Type the abbreviation:", required=False)
	comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Comments'}), help_text="Any additional comments:", required=False)

class NewCitationForm(forms.Form):
	citation_type = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Citation Type'}), help_text="Type the disease common name:", required=True)
	title = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Title'}), help_text="Type the citation:", required=False)
	url = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'URL'}), help_text="A URL linking to the article:", required=False)
	pubmed_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Pubmed ID'}), help_text="The Pubmed ID:", required=False)
	comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Comments'}), help_text="Any additional comments:", required=False)

class NewMediumForm(forms.Form):
	citation = forms.ModelChoiceField(queryset=Citation.objects.all(), empty_label="--- Citation ---", help_text="Select the relevant citation:", required=True)
	media_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Media Name'}), help_text="A unique name for the media:", required=True)
	media_type = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Media Type'}), help_text="The type of media:", required=False)
	media_description = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Description'}), help_text="A brief description of the media and its uses:", required=False)
	media_preparation = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Preparation'}), help_text="How the media is prepared:", required=False)
	comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Comments'}), help_text="Any additional comments:", required=False)

class NewTaxonomyForm(forms.Form):
	genus = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Genus'}), help_text="Type the genus:", required=False)
	species = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Species'}), help_text="Type the species:", required=False)
	population = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Population'}), help_text="Type the population:", required=False)
	alias = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Alias'}), help_text="Type the alias (historically for isolates):", required=False)
	race = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Race'}), help_text="Type the race (historically for isolates):", required=False)
	subtaxa = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Sub-taxa'}), help_text="Type the sub-taxa (historically for isolates):", required=False)

class UpdateSeedDataOnlineForm(forms.Form):
	experiment = forms.ModelChoiceField(queryset=Experiment.objects.all(), empty_label="--- Experiment ---", help_text="Experiment", required=True)
	stock__seed_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Seed ID'}), help_text="Seed ID:", required=True)
	stock__seed_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Seed Name'}), help_text="Seed Name:", required=False)
	stock__cross_type = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Cross Type'}), help_text="Cross Type:", required=False)
	stock__pedigree = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Pedigree'}), help_text="Pedigree", required=True)
	stock__stock_status = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Stock Status'}), help_text="Stock Status", required=False)
	stock__stock_date = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Stock Date'}), help_text="Stock Date", required=False)
	stock__inoculated = forms.BooleanField(help_text="Inoculated", required=False)
	stock__comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Comments'}), help_text="Stock Comments", required=False)
	stock__passport__taxonomy__genus = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Genus'}), help_text="Genus", required=False)
	stock__passport__taxonomy__species = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Species'}), help_text="Species", required=False)
	stock__passport__taxonomy__population = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Population'}), help_text="Population", required=False)
	obs_row__row_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Row ID'}), help_text="Row ID", required=False)
	obs_plant__plant_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Plant ID'}), help_text="Plant ID", required=False)
	field = forms.ModelChoiceField(queryset=Field.objects.all(), empty_label="--- Field Source ---", help_text="Field Source", required=True)
	stock__passport__collecting__user = forms.ModelChoiceField(queryset=User.objects.all(), empty_label="--- Collected By ---", help_text="Collector", required=True)
	stock__passport__collecting__collection_date = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Collection Date'}), help_text="Date Collected", required=False)
	stock__passport__collecting__collection_method = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Collection Method'}), help_text="Collection Method", required=False)
	stock__passport__collecting__comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Collection Comments'}), help_text="Collection Comments", required=False)
	stock__passport__people__first_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source First Name'}), help_text="Source First Name", required=False)
	stock__passport__people__last_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Last Name'}), help_text="Source Last Name", required=False)
	stock__passport__people__organization = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Organization'}), help_text="Source Organization", required=False)
	stock__passport__people__phone = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Phone'}), help_text="Source Phone", required=False)
	stock__passport__people__email = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Email'}), help_text="Source Email", required=False)
	stock__passport__people__comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Comments'}), help_text="Source Comments", required=False)

class LogSeedDataOnlineForm(forms.Form):
	experiment_used = forms.BooleanField(help_text="Used", required=False)
	experiment_collected = forms.BooleanField(help_text="Collected", required=False, initial=True)
	experiment = forms.ModelChoiceField(queryset=Experiment.objects.all(), empty_label="--- Experiment ---", help_text="Experiment", required=True)
	stock__seed_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Seed ID'}), help_text="Seed ID:", required=True)
	stock__seed_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Seed Name'}), help_text="Seed Name:", required=False)
	stock__cross_type = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Cross Type'}), help_text="Cross Type:", required=False)
	stock__pedigree = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Pedigree'}), help_text="Pedigree", required=True)
	stock__stock_status = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Stock Status'}), help_text="Stock Status", required=False)
	stock__stock_date = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Stock Date'}), help_text="Stock Date", required=False)
	stock__inoculated = forms.BooleanField(help_text="Inoculated", required=False)
	stock__comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Comments'}), help_text="Stock Comments", required=False)
	stock__passport__taxonomy__genus = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Genus'}), help_text="Genus", required=False)
	stock__passport__taxonomy__species = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Species'}), help_text="Species", required=False)
	stock__passport__taxonomy__population = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Population'}), help_text="Population", required=False)
	obs_row__row_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Row ID'}), help_text="Row ID", required=False)
	obs_plant__plant_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Plant ID'}), help_text="Plant ID", required=False)
	field = forms.ModelChoiceField(queryset=Field.objects.all(), empty_label="--- Field Source ---", help_text="Field Source", required=True)
	stock__passport__collecting__user = forms.ModelChoiceField(queryset=User.objects.all(), empty_label="--- Collected By ---", help_text="Collector", required=True)
	stock__passport__collecting__collection_date = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Collection Date'}), help_text="Date Collected", required=False)
	stock__passport__collecting__collection_method = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Collection Method'}), help_text="Collection Method", required=False)
	stock__passport__collecting__comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Collection Comments'}), help_text="Collection Comments", required=False)
	stock__passport__people__first_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source First Name'}), help_text="Source First Name", required=False)
	stock__passport__people__last_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Last Name'}), help_text="Source Last Name", required=False)
	stock__passport__people__organization = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Organization'}), help_text="Source Organization", required=False)
	stock__passport__people__phone = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Phone'}), help_text="Source Phone", required=False)
	stock__passport__people__email = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Email'}), help_text="Source Email", required=False)
	stock__passport__people__comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Comments'}), help_text="Source Comments", required=False)

class LogStockPacketOnlineForm(forms.Form):
	stock__seed_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Seed ID'}), required=True)
	weight = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Weight'}), required=False)
	num_seeds = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Num Seeds'}), required=False)
	comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Packet Comments'}), required=False)
	location__locality = forms.ModelChoiceField(queryset=Locality.objects.all(), empty_label="--- Locality ---", required=True)
	location__building_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Building Name'}), required=False)
	location__location_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Location Name'}), required=True)
	location__room = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Room'}), required=False)
	location__shelf = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Shelf'}), required=False)
	location__column = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Column'}), required=False)
	location__box_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Box Name'}), required=False)
	location__comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Location Comments'}), required=False)

class LogRowsOnlineForm(forms.Form):
	experiment = forms.ModelChoiceField(queryset=Experiment.objects.all(), empty_label="--- Experiment ---", required=True)
	row_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Row ID'}), required=True)
	row_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Row Name'}), required=True)
	seed_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Seed ID'}), required=True)
	field = forms.ModelChoiceField(queryset=Field.objects.all(), empty_label="--- Field Name ---", required=True)
	range_num = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Range'}), required=False)
	plot = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Plot'}), required=False)
	block = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Block'}), required=False)
	rep = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Rep'}), required=False)
	kernel_num = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Kernel Num'}), required=False)
	planting_date = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Planting Date'}), required=False)
	harvest_date = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Harvest Date'}), required=False)
	row_comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Comments'}), required=False)

class LogPlantsOnlineForm(forms.Form):
	experiment = forms.ModelChoiceField(queryset=Experiment.objects.all(), empty_label="--- Experiment ---", required=True)
	plant_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Plant ID'}), required=True)
	plant_num = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Plant Num'}), required=True)
	seed_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Seed ID'}), required=True)
	row_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Row ID'}), required=False)
	plant_comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Comments'}), required=False)

class LogSamplesOnlineForm(forms.Form):
	experiment = forms.ModelChoiceField(queryset=Experiment.objects.all(), empty_label="--- Experiment ---", help_text="Experiment: ", required=True)
	obs_sample__sample_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Sample ID'}), help_text="Sample ID (Unique):", required=True)
	obs_sample__sample_type = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Sample Type'}), help_text="Sample Type:", required=False)
	obs_sample__sample_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Sample Name'}), help_text="Sample Name:", required=False)
	stock__seed_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Seed ID'}), help_text="Source Seed ID:", required=False)
	obs_row__row_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Row ID'}), help_text="Source Row ID:", required=False)
	obs_plant__plant_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Plant ID'}), help_text="Source Plant ID:", required=False)
	source_sample_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Sample ID'}), help_text="Source Sample ID:", required=False)
	obs_sample__weight = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Weight'}), help_text="Weight (g):", required=False)
	obs_sample__volume = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Volume'}), help_text="Volume (mL):", required=False)
	obs_sample__density = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Density'}), help_text="Density (g/mL):", required=False)
	obs_sample__kernel_num = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Num Kernels'}), help_text="Number of Kernels:", required=False)
	obs_sample__photo = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Photo'}), help_text="Photo Filename:", required=False)
	obs_sample__comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Comments'}), help_text="Additional comments:", required=False)

class LogEnvironmentsOnlineForm(forms.Form):
	experiment = forms.ModelChoiceField(queryset=Experiment.objects.all(), empty_label="--- Experiment ---", required=True)
	environment_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Environment ID'}), required=True)
	field = forms.ModelChoiceField(queryset=Field.objects.all(), empty_label="--- Field Name ---", required=True)
	longitude = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Longitude'}), required=False)
	latitude = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Latitude'}), required=False)
	environment_comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Comments'}), required=False)

class LogTissuesOnlineForm(forms.Form):
	experiment = forms.ModelChoiceField(queryset=Experiment.objects.all(), empty_label="--- Experiment ---", required=True)
	tissue_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Tissue ID'}), required=True)
	row_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Row ID'}), required=False)
	seed_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Seed ID'}), required=False)
	plant_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Plant ID'}), required=False)
	culture_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Culture ID'}), required=False)
	tissue_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Tissue Name'}), required=False)
	tissue_type = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Tissue Type'}), required=False)
	date_ground = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Date Ground'}), required=False)
	tissue_comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Comments'}), required=False)

class LogCulturesOnlineForm(forms.Form):
	experiment = forms.ModelChoiceField(queryset=Experiment.objects.all(), empty_label="--- Experiment ---", required=True)
	culture_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Culture ID'}), required=True)
	medium = forms.ModelChoiceField(queryset=Medium.objects.all(), empty_label="--- Medium ---", required=True)
	location = forms.ModelChoiceField(queryset=Location.objects.all(), empty_label="--- Location ---", required=True)
	row_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Row ID'}), required=False)
	seed_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Seed ID'}), required=False)
	plant_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Plant ID'}), required=False)
	tissue_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Tissue ID'}), required=False)
	microbe_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Microbe ID'}), required=False)
	culture_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Culture Name'}), required=False)
	microbe_type = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Microbe Type'}), required=False)
	plating_cycle = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Plating Cycle'}), required=False)
	dilution = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Dilution'}), required=False)
	num_colonies = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Num Colonies'}), required=False)
	num_microbes = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Num Microbes'}), required=False)
	image = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Image'}), required=False)
	culture_comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Comments'}), required=False)

class LogMicrobesOnlineForm(forms.Form):
	experiment = forms.ModelChoiceField(queryset=Experiment.objects.all(), empty_label="--- Experiment ---", required=True)
	microbe_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Microbe ID'}), required=True)
	row_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Row ID'}), required=False)
	seed_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Seed ID'}), required=False)
	plant_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Plant ID'}), required=False)
	tissue_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Tissue ID'}), required=False)
	culture_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Culture ID'}), required=False)
	microbe_type = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Microbe Type'}), required=False)
	microbe_comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Comments'}), required=False)

class LogDNAOnlineForm(forms.Form):
	experiment = forms.ModelChoiceField(queryset=Experiment.objects.all(), empty_label="--- Experiment ---", required=True)
	dna_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'DNA ID'}), required=True)
	microbe_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Microbe ID'}), required=False)
	row_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Row ID'}), required=False)
	seed_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Seed ID'}), required=False)
	plant_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Plant ID'}), required=False)
	tissue_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Tissue ID'}), required=False)
	culture_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Culture ID'}), required=False)
	plate_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Plate ID'}), required=False)
	well_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Well ID'}), required=False)
	sample_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Sample ID'}), required=False)
	extraction = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Extraction'}), required=False)
	date = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Date'}), required=False)
	tube_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Tube ID'}), required=False)
	tube_type = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Tube Type'}), required=False)
	dna_comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Comments'}), required=False)

class LogWellOnlineForm(forms.Form):
	experiment = forms.ModelChoiceField(queryset=Experiment.objects.all(), empty_label="--- Experiment ---", required=True)
	well_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Well ID'}), required=True)
	microbe_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Microbe ID'}), required=False)
	row_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Row ID'}), required=False)
	seed_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Seed ID'}), required=False)
	plant_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Plant ID'}), required=False)
	tissue_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Tissue ID'}), required=False)
	culture_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Culture ID'}), required=False)
	plate_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Plate ID'}), required=False)
	well = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Well'}), required=False)
	inventory = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Inventory'}), required=False)
	tube_label = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Tube Label'}), required=False)
	well_comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Comments'}), required=False)

class LogMaizeSurveyOnlineForm(forms.Form):
	experiment = forms.ModelChoiceField(queryset=Experiment.objects.all(), empty_label="--- Experiment ---", required=True)
	maize_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Maize ID'}), required=True)
	county = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'County'}), required=False)
	sub_location = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Sub Location'}), required=False)
	village = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Village'}), required=False)
	weight = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Weight'}), required=False)
	harvest_date = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Harvest Date'}), required=False)
	storage_months = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Storage Months'}), required=False)
	storage_conditions = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Storage Conditions'}), required=False)
	maize_variety = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Maize Variety'}), required=False)
	seed_source = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Seed Source'}), required=False)
	moisture_content = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Moisture Content'}), required=False)
	source_type = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Type'}), required=False)
	appearance = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Appearance'}), required=False)
	gps_latitude = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'GPS Latitude'}), required=False)
	gps_longitude = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'GPS Longitude'}), required=False)
	gps_altitude = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'GPS Altitude'}), required=False)
	gps_accuracy = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'GPS Accuracy'}), required=False)
	photo = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Photo Filename'}), required=False)

class LogPlatesOnlineForm(forms.Form):
	experiment = forms.ModelChoiceField(queryset=Experiment.objects.all(), empty_label="--- Experiment ---", required=True)
	plate_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Plate ID'}), required=True)
	location_id = forms.ModelChoiceField(queryset=Location.objects.all(), empty_label="--- Location Name ---", required=True)
	plate_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Plate Name'}), required=False)
	date = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Date'}), required=False)
	contents = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Contents'}), required=False)
	rep = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Rep'}), required=False)
	plate_type = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Plate Type'}), required=False)
	plate_status = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Plate Status'}), required=False)
	plate_comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Comments'}), required=False)

class LogSeparationsOnlineForm(forms.Form):
	sample_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Sample ID'}), required=True)
	sample_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Sample Name'}), required=False)
	separation_type = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Separation Type'}), required=False)
	apparatus = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Apparatus'}), required=False)
	sg = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Specific Gravity'}), required=False)
	light_weight = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Light Weight'}), required=False)
	medium_weight = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Medium Weight'}), required=False)
	heavy_weight = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Heavy Weight'}), required=False)
	light_percent = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Light Percent'}), required=False)
	medium_percent = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Medium Percent'}), required=False)
	heavy_percent = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Heavy Percent'}), required=False)
	operating_factor = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Operating Factor'}), required=False)
	separation_comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Comments'}), required=False)

class LogIsolatesOnlineForm(forms.Form):
	experiment = forms.ModelChoiceField(queryset=Experiment.objects.all(), empty_label="--- Experiment ---", help_text="Experiment:", required=True)
	isolate__isolate_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Isolate ID'}), help_text="Isolate ID:", required=True)
	location = forms.ModelChoiceField(queryset=Location.objects.all(), empty_label="--- Location Name ---", help_text="Location:", required=True)
	field = forms.ModelChoiceField(queryset=Field.objects.all(), empty_label="--- Source Field Name ---", help_text="Source Field Name:", required=True)
	obs_dna__dna_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source DNA ID'}), help_text="Source DNA ID:", required=False)
	obs_microbe__microbe_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Microbe ID'}), help_text="Source Microbe ID:", required=False)
	obs_row__row_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Row ID'}), help_text="Source Row ID:", required=False)
	stock__seed_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Seed ID'}), help_text="Source Seed ID:", required=False)
	obs_plant__plant_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Plant ID'}), help_text="Source Plant ID:", required=False)
	obs_tissue__tissue_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Tissue ID'}), help_text="Source Tissue ID:", required=False)
	obs_culture__culture_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Culture ID'}), help_text="Source Culture ID:", required=False)
	obs_plate__plate_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Plate ID'}), help_text="Source Plate ID:", required=False)
	obs_well__well_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Well ID'}), help_text="Source Well ID:", required=False)
	isolate__isolate_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Isolate Name'}), help_text="Isolate Name:", required=False)
	isolate__disease_info = forms.ModelChoiceField(queryset=DiseaseInfo.objects.all(), empty_label="--- Disease ---", help_text="Disease Name:", required=True)
	isolate__plant_organ = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Plant Organ'}), help_text="Plant Organ:", required=False)
	isolate__passport__taxonomy__genus = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Genus'}), help_text="Genus:", required=False)
	isolate__passport__taxonomy__alias = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Alias'}), help_text="Alias:", required=False)
	isolate__passport__taxonomy__race = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Race'}), help_text="Race:", required=False)
	isolate__passport__taxonomy__subtaxa = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Subtaxa'}), help_text="Subtaxa:", required=False)
	isolate__comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Comments'}), help_text="Additional Comments:", required=False)

class LogGlycerolStocksOnlineForm(forms.Form):
	experiment = forms.ModelChoiceField(queryset=Experiment.objects.all(), empty_label="--- Experiment ---", help_text="Experiment:", required=True)
	glycerol_stock__glycerol_stock_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Glycerol Stock ID'}), help_text="Glycerol Stock ID:", required=True)
	location = forms.ModelChoiceField(queryset=Location.objects.all(), empty_label="--- Location Name ---", help_text="Location:", required=True)
	glycerol_stock__stock_date = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Stock Date'}), help_text="Stock Date:", required=False)
	glycerol_stock__extract_color = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Extract Color'}), help_text="Extract Color:", required=False)
	glycerol_stock__organism = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Organism'}), help_text="Organism:", required=False)
	glycerol_stock__comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Comments'}), help_text="Comments:", required=False)
	field = forms.ModelChoiceField(queryset=Field.objects.all(), empty_label="--- Source Field Name ---", help_text="Source Field Name:", required=True)
	obs_culture__culture_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Culture ID'}), help_text="Source Culture ID:", required=False)
	obs_dna__dna_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source DNA ID'}), help_text="Source DNA ID:", required=False)
	obs_plate__plate_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Plate ID'}), help_text="Source Plate ID:", required=False)
	obs_row__row_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Row ID'}), help_text="Source Row ID:", required=False)
	obs_plant__plant_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Plant ID'}), help_text="Source Plant ID:", required=False)
	obs_tissue__tissue_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Tissue ID'}), help_text="Source Tissue ID:", required=False)
	stock__seed_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Seed ID'}), help_text="Source Seed ID:", required=False)
	obs_sample__sample_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Sample ID'}), help_text="Source Sample ID:", required=False)
	obs_well__well_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Well ID'}), help_text="Source Well ID:", required=False)
	obs_microbe__microbe_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Microbe ID'}), help_text="Source Microbe ID:", required=False)
	isolate__isolate_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Source Isolate ID'}), help_text="Source Isolate ID:", required=False)

class LogMeasurementsOnlineForm(forms.Form):
	observation_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Observation Unit'}), required=True)
	measurement_parameter = forms.ModelChoiceField(queryset=MeasurementParameter.objects.all(), empty_label="--- Parameter ---", required=True)
	user = forms.ModelChoiceField(queryset=User.objects.all(), empty_label="--- Username ---", required=True)
	time_of_measurement = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Time of Measurement'}), required=False)
	value = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Value'}), required=True)
	measurement_comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Comments'}), required=False)

class UploadQueueForm(forms.Form):
	experiment = forms.ModelChoiceField(queryset=Experiment.objects.all(), empty_label="--- Experiment ---", help_text="Choose the experiment that data is related to:", required=True)
	user = forms.ModelChoiceField(queryset=User.objects.all(), empty_label="--- Username ---", help_text="Select the user who produced data:", required=True)
	file_name = forms.FileField(help_text="Select your file:")
	comments = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Comments'}), help_text="Any additional comments:", required=False)
	verified = forms.BooleanField(help_text="Verified:", required=False)
