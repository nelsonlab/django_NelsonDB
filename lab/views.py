
import os, tempfile, zipfile
import csv
from lab import loader_scripts
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response, render
from django.conf import settings
from lab.models import UserProfile, Experiment, Passport, Stock, StockPacket, Taxonomy, People, Collecting, Field, Locality, Location, ObsRow, ObsPlant, ObsSample, ObsEnv, ObsWell, ObsCulture, ObsTissue, ObsDNA, ObsPlate, ObsMicrobe, ObsExtract, ObsTracker, ObsTrackerSource, Isolate, DiseaseInfo, Measurement, MeasurementParameter, Treatment, UploadQueue, Medium, Citation, Publication, MaizeSample, Separation, GlycerolStock, FileDump, Marker, GenotypeResults, Primer, MapFeature, MapFeatureInterval
from lab.forms import UserForm, UserProfileForm, ChangePasswordForm, EditUserForm, EditUserProfileForm, NewExperimentForm, LogSeedDataOnlineForm, LogStockPacketOnlineForm, LogPlantsOnlineForm, LogRowsOnlineForm, LogEnvironmentsOnlineForm, LogSamplesOnlineForm, LogMeasurementsOnlineForm, NewTreatmentForm, UploadQueueForm, LogSeedDataOnlineForm, LogStockPacketOnlineForm, NewFieldForm, NewLocalityForm, NewMeasurementParameterForm, NewLocationForm, NewDiseaseInfoForm, NewTaxonomyForm, NewMediumForm, NewCitationForm, UpdateSeedDataOnlineForm, LogTissuesOnlineForm, LogCulturesOnlineForm, LogMicrobesOnlineForm, LogDNAOnlineForm, LogPlatesOnlineForm, LogWellOnlineForm, LogIsolatesOnlineForm, LogSeparationsOnlineForm, LogMaizeSurveyOnlineForm, LogGlycerolStocksOnlineForm, FileDumpForm, SequenceZipfileForm, NewPrimerForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.contrib.auth.models import User
from django.shortcuts import redirect
from itertools import chain
from django.forms.models import inlineformset_factory
from django.forms.formsets import formset_factory
from django.conf import settings
from django.db.models import F
from django import template
from django.template.defaulttags import register
from operator import itemgetter
from django.db import transaction
from django.core.files import File
from django.http import JsonResponse
from django.utils.encoding import smart_str
from wsgiref.util import FileWrapper
from django.conf import settings
import mimetypes
import json
import zipfile

def encode_url(str):
	return str.replace(' ', '_')

def decode_url(str):
	return str.replace('_', ' ')

def check_user_permissions(request):
	permissions = {}
	permissions['is_superuser'] = request.user.is_superuser
	permissions['is_staff'] = request.user.is_staff
	permissions['is_active'] = request.user.is_active
	return permissions

def get_experiment_list(max_results=0, starts_with=''):
	exp_list = []
	if starts_with:
		exp_list = Experiment.objects.filter(name__like='%{}%'.format(starts_with))
	else:
		exp_list = Experiment.objects.all()
	if max_results > 0:
		if len(exp_list) > max_results:
			exp_list = exp_list[:max_results]
	for exp in exp_list:
		exp.url = encode_url(exp.name)
	return exp_list

def index(request):
	context_dict = {}
	if request.session.get('last_visit'):
		last_visit = request.session.get('last_visit')
		visits = request.session.get('visits', 0)
		if(datetime.now() - datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")).days > 0:
			request.session['visits'] = visits + 1
			request.session['last_visit'] = str(datetime.now())
	else:
		request.session['last_visit'] = str(datetime.now())
		request.session['visits'] = 1
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/index.html', context=context_dict)

def error_prelim(request, error_message):
	context = RequestContext(request)
	context_dict = {'errormessage': error_message}
	return render_to_response('lab/error_prelim.html', context_dict, context)

@login_required
def register(request):
	registered = False
	if request.method == 'POST':
		user_form = UserForm(data=request.POST)
		profile_form = UserProfileForm(data=request.POST)
		if user_form.is_valid() and profile_form.is_valid():
			user = user_form.save()
			user.set_password(user.password)
			user.save()

			profile = profile_form.save(commit=False)
			profile.user = user
			if 'picture' in request.FILES:
				profile.picture = request.FILES['picture']
			else:
				profile.picture = 'profile_images/underwater.jpg'
			profile.save()
			registered = True
		else:
			print(user_form.errors, profile_form.errors)
	else:
		user_form = UserForm()
		profile_form = UserProfileForm()
	return render(request, 'lab/register.html', context={'user_form': user_form, 'profile_form': profile_form, 'registered': registered})

def upload_sequence_zipfile(request):
	context_dict = {}
	if request.method == 'POST':
		fileform = SequenceZipfileForm(request.POST, request.FILES)
		if fileform.is_valid():
			user = fileform.cleaned_data['user']
			experiment = fileform.cleaned_data['experiment']
			file_name = fileform.cleaned_data['file_name']
			primer_f = fileform.cleaned_data['primer_f']
			primer_r = fileform.cleaned_data['primer_r']
			gene_name = fileform.cleaned_data['gene_name']
			start_physical_position = fileform.cleaned_data['start_physical_position']
			stop_physical_position = fileform.cleaned_data['stop_physical_position']
			chromosome = fileform.cleaned_data['chromosome']
			comments = fileform.cleaned_data['comments']
			zip_file = fileform.cleaned_data['file']
			parameter = fileform.cleaned_data['measurement_parameter']

			if zipfile.is_zipfile(zip_file):
				zf = zipfile.ZipFile(zip_file, 'r')
				namelist = zf.namelist();

				check_filecontent_ext = True
				for filename in namelist:
					if filename.lower().endswith('.ab1') or filename.lower().endswith('.seq'):
						print(filename)
					else:
						print(filename)
						check_filecontent_ext = False

				if check_filecontent_ext == True:

					unique_names = []
					for filename in namelist:
						filename = filename.replace(".ab1", "")
						filename = filename.replace(".seq", "")
						if filename not in unique_names:
							unique_names.append(filename)

					start_position, created = MapFeature.objects.get_or_create(chromosome=chromosome, physical_position=start_physical_position)
					stop_position, created = MapFeature.objects.get_or_create(chromosome=chromosome, physical_position=stop_physical_position)
					map_feature_interval, created = MapFeatureInterval.objects.get_or_create(map_feature_start=start_position, map_feature_end=stop_position, interval_type='gene', interval_name=gene_name)
					marker_map_feature = MapFeature.objects.get(id=1)
					marker, created = Marker.objects.get_or_create(map_feature_interval=map_feature_interval, marker_map_feature=marker_map_feature, primer_f=primer_f, primer_r=primer_r, marker_id=gene_name, marker_name=gene_name)

					#print(unique_names)
					for name in unique_names:
						#print(name)
						obs_sample = ObsSample.objects.get(sample_id=name)
						sample = ObsTracker.objects.get(obs_entity_type='sample', obs_sample=obs_sample)

						fasta_file = "%s.seq" % name
						chromatogram_file = "%s.ab1" % name

						sequence = zf.read(fasta_file)
						#print(sequence)

						extracted_seqfile = zf.extract(fasta_file, 'media/fasta_files')
						extracted_chromfile = zf.extract(chromatogram_file, 'media/chromatogram_files')

						GenotypeResults.objects.create(obs_tracker=sample, marker=marker, parameter=parameter, sequence=sequence, comments=comments, fasta_file=extracted_seqfile, chromatogram_file=extracted_chromfile)

					FileDump.objects.create(user=user, experiment=experiment, file_name=file_name, file=zip_file, comments=comments)

					complete = True
				else :
					complete = False


		else:
			print(fileform.errors)
			complete = False
		context_dict['complete'] = complete
	else:
		fileform = SequenceZipfileForm()
	context_dict['fileform'] = fileform
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/upload_sequence_zipfile.html', context_dict)

@login_required
def file_storage(request):
	saved = False
	if request.method == 'POST':
		file_form = FileDumpForm(request.POST, request.FILES)
		if file_form.is_valid():
			file = file_form.save(commit=False)
			if 'file' in request.FILES:
				file.file = request.FILES['file']
			file.save()
			saved = True
		else:
			print(file_form.errors)
	else:
		file_form = FileDumpForm()

	all_files = FileDump.objects.all()
	return render(request, 'lab/file_storage.html', context={'file_form': file_form, 'saved': saved, 'all_files': all_files})

@login_required
def download_file_dump(request, file_id):
	file = FileDump.objects.get(id=file_id)

	filename     = '%s/%s' % (settings.MEDIA_ROOT,file.file)
	download_name = file.file
	wrapper      = FileWrapper(open(filename))
	content_type = mimetypes.guess_type(filename)[0]
	response     = HttpResponse(wrapper,content_type=content_type)
	response['Content-Length']      = os.path.getsize(filename)
	response['Content-Disposition'] = "attachment; filename=%s"%download_name
	return response

@login_required
def download_geno_result_file(request, result_id, file_type):
	result = GenotypeResults.objects.get(id=result_id)
	if (file_type == 'fasta'):
		filename     = '%s' % (result.fasta_file)
		download_name = result.fasta_file
	elif (file_type == 'chromatogram'):
		filename     = '%s' % (result.chromatogram_file)
		download_name = result.chromatogram_file
	wrapper      = FileWrapper(open(filename))
	content_type = mimetypes.guess_type(filename)[0]
	response     = HttpResponse(wrapper,content_type=content_type)
	response['Content-Length']      = os.path.getsize(filename)
	response['Content-Disposition'] = "attachment; filename=%s"%download_name
	return response

def user_login(request):
	next_url = request.GET.get('next', '/lab/')
	if request.method == 'POST':
		username = request.POST['username']
		password = request.POST['password']
		user = authenticate(username = username, password = password)
		if user:
			if user.is_active:
				login(request, user)
				return HttpResponseRedirect(next_url)
			else:
				return render(request, 'lab/login.html', context={'next_url':next_url, 'disabled_account': 'disabled'})
		else:
			return render(request, 'lab/login.html', context={'next_url':next_url, 'bad_details': 'bad_details'})
	else:
		return render(request, 'lab/login.html', context={'next_url':next_url})

@login_required
def user_logout(request):
	logout(request)
	return HttpResponseRedirect('/lab/')

def profile(request, profile_name):
	context_dict = {}
	u = User.objects.get(username=profile_name)
	try:
		up = UserProfile.objects.get(user=u)
	except:
		up = None
	context_dict['user'] = u
	context_dict['userprofile'] = up
	if User.is_authenticated and profile_name == request.user.username:
		context_dict['checked_user'] = True
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/profile.html', context=context_dict)

@login_required
def profile_change_password(request):
  context_dict = {}
  if request.method == 'POST':
    change_password_form = ChangePasswordForm(data=request.POST)
    if change_password_form.is_valid():
      if change_password_form.cleaned_data['new_password'] == change_password_form.cleaned_data['new_password_repeat']:
        user = authenticate(username=request.user.username, password=change_password_form.cleaned_data['old_password'])
        if user is not None:
          user.set_password(change_password_form.cleaned_data['new_password'])
          user.save()
          logout(request)
          return HttpResponseRedirect('/lab/login/')
        else:
          context_dict['wrong_password'] = 'wrong_password'
      else:
        context_dict['wrong_repeat'] = 'wrong_repeat'
    else:
      print(change_password_form.errors)
  else:
    change_password_form = ChangePasswordForm()
  context_dict['change_password_form'] = change_password_form
  context_dict['logged_in_user'] = request.user.username
  return render(request, 'lab/profile_change_password.html', context=context_dict)

@login_required
def edit_profile(request):
	context_dict = {}
	user_instance = request.user
	profile_instance = UserProfile.objects.get(user=user_instance)
	user_form = EditUserForm(request.POST or None, instance=user_instance)
	profile_form = EditUserProfileForm(request.POST or None, instance=profile_instance)
	if user_form.is_valid() and profile_form.is_valid():
		user = authenticate(username=request.user.username, password=user_form.cleaned_data['password'])
		if user is not None:
			user_form.save()
			profile = profile_form.save(commit=False)
			profile.user = user
			if 'picture' in request.FILES:
				profile.picture = request.FILES['picture']
			profile.save()
			context_dict['edit_complete'] = 'edit_complete'
		else:
			context_dict['wrong_password'] = 'wrong_password'
	else:
		print(user_form.errors, profile_form.errors)
	context_dict['user_form'] = user_form
	context_dict['profile_form'] = profile_form
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/edit_profile.html', context=context_dict)

def track_url(request):
	context = RequestContext(request)
	page_id = None
	url = '/lab/'
	if request.method == 'GET':
		if 'page_id' in request.GET:
			page_id = request.GET['page_id']
			try:
				page = Page.objects.get(id=page_id)
				page.views = page.views + 1
				page.save()
				url = page.url
			except:
				pass
	return redirect(url)

@login_required
def experiment(request, experiment_name_url):
	experiment_name = decode_url(experiment_name_url)
	context_dict = {'experiment_name': experiment_name}
	if experiment_name is not 'search':
		try:
			experiment = Experiment.objects.get(name=experiment_name)
			context_dict['experiment'] = experiment
			u = User.objects.get(username=experiment.user.username)
			context_dict['user'] = u
			try:
				treatment_data = Treatment.objects.filter(experiment__name=experiment_name)
			except Treatment.DoesNotExist:
				treatment_data = None
			context_dict['treatment_data'] = treatment_data

			obs_type_list = ['stock', 'isolate', 'glycerol_stock', 'maize', 'row', 'plant', 'sample', 'environment', 'dna', 'tissue', 'plate', 'well', 'microbe', 'culture', 'extract']
			for obs_type in obs_type_list:
				obs_data = "%s_data" % (obs_type)

				if obs_type == 'row':
					obs_type_data = find_relationship_for_experiment(experiment_name, 'row', 'row_used_in_experiment')

				if obs_type == 'plant':
					obs_type_data = find_relationship_for_experiment(experiment_name, 'plant', 'plant_used_in_experiment')

				if obs_type == 'environment':
					obs_type_data = find_relationship_for_experiment(experiment_name, 'environment', 'env_used_in_experiment')

				if obs_type == 'dna':
					obs_type_data = find_relationship_for_experiment(experiment_name, 'dna', 'dna_used_in_experiment')

				if obs_type == 'tissue':
					obs_type_data = find_relationship_for_experiment(experiment_name, 'tissue', 'tissue_used_in_experiment')

				if obs_type == 'plate':
					obs_type_data = find_relationship_for_experiment(experiment_name, 'plate', 'plate_used_in_experiment')

				if obs_type == 'well':
					obs_type_data = find_relationship_for_experiment(experiment_name, 'well', 'well_used_in_experiment')

				if obs_type == 'microbe':
					obs_type_data = find_relationship_for_experiment(experiment_name, 'microbe', 'microbe_used_in_experiment')

				if obs_type == 'culture':
					obs_type_data = find_relationship_for_experiment(experiment_name, 'culture', 'culture_used_in_experiment')

				if obs_type == 'extract':
					obs_type_data = find_relationship_for_experiment(experiment_name, 'extract', 'extract_used_in_experiment')

				if obs_type == 'isolate':
					obs_type_data = find_relationship_for_experiment(experiment_name, 'isolate', 'isolate_used_in_experiment')

				if obs_type == 'glycerol_stock':
					obs_type_data = find_relationship_for_experiment(experiment_name, 'glycerol_stock', 'isolate_stock_from_experiment')

				if obs_type == 'maize':
					obs_type_data = find_relationship_for_experiment(experiment_name, 'maize', 'maize_used_in_experiment')

				if obs_type == 'sample':
					obs_type_data = find_relationship_for_experiment(experiment_name, 'sample', 'sample_used_in_experiment')

				if obs_type == 'stock':
					obs_type_data = find_relationship_for_experiment(experiment_name, 'stock', 'stock_used_in_experiment')

					stockpackets_used = find_seedpackets_from_obstracker_stock(obs_type_data)
					context_dict['stockpackets_used'] = stockpackets_used


				context_dict[obs_data] = obs_type_data


			collected_stock_data = find_stock_collected_from_experiment(experiment_name)
			context_dict['collected_stock_data'] = collected_stock_data

			if collected_stock_data is not None:
				stockpackets_collected = find_seedpackets_from_obstrackersource_stock(collected_stock_data)
			else:
				stockpackets_collected = None
			context_dict['stockpackets_collected'] = stockpackets_collected

			try:
				measurement_data = Measurement.objects.filter(obs_tracker__experiment__name=experiment_name)
			except Measurement.DoesNotExist:
				measurement_data = None
			context_dict['measurement_data'] = measurement_data

			genotype_data = None
			context_dict['genotype_data'] = genotype_data

		except Experiment.DoesNotExist:
			pass
	if experiment_name == 'search':
		exp_list = get_experiment_list()
		context_dict['exp_list'] = exp_list
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/experiment.html', context=context_dict)


@login_required
def experiment_delete(request):
	permissions = check_user_permissions(request)
	if (permissions['is_superuser'] == True):
		experiment_id = request.POST.get('experiment_id', False)
		try:
			obs_trackers = ObsTracker.objects.filter(experiment_id=experiment_id)
			for o in obs_trackers:
				if (o.obs_row_id != 1):
					ObsRow.objects.get(id=o.obs_row_id).delete()
				if (o.obs_plant_id != 1):
					ObsPlant.objects.get(id=o.obs_plant_id).delete()
				if (o.obs_tissue_id != 1):
					ObsTissue.objects.get(id=o.obs_tissue_id).delete()
				if (o.obs_culture_id != 1):
					ObsCulture.objects.get(id=o.obs_culture_id).delete()
				if (o.obs_microbe_id != 1):
					ObsMicrobe.objects.get(id=o.obs_microbe_id).delete()
				if (o.obs_plate_id != 1):
					ObsPlate.objects.get(id=o.obs_plate_id).delete()
				if (o.obs_dna_id != 1):
					ObsDNA.objects.get(id=o.obs_dna_id).delete()
				if (o.obs_well_id != 1):
					ObsWell.objects.get(id=o.obs_well_id).delete()
				if (o.obs_sample_id != 1):
					ObsSample.objects.get(id=o.obs_sample_id).delete()
				if (o.obs_extract_id != 1):
					ObsExtract.objects.get(id=o.obs_extract_id).delete()
				if (o.obs_env_id != 1):
					ObsEnv.objects.get(id=o.obs_env_id).delete()
				try:
					Measurement.objects.get(obs_tracker_id=o.id).delete()
				except Measurement.DoesNotExist:
					pass
			obs_trackers.delete()
		except ObsTracker.DoesNotExist:
			pass
		Experiment.objects.get(id=experiment_id).delete()
		message = "Experiment and related data successfully deleted."
	else:
		message = "You do not have the correct permissions to do this."
	return JsonResponse({'message':message}, safe=True)

@login_required
def experiment_edit(request, experiment_id):
	context_dict = {}
	experiment = Experiment.objects.get(id=experiment_id)
	experiment_name = experiment.name
	if request.method == 'POST':
		new_experiment_form = NewExperimentForm(data=request.POST)
		if new_experiment_form.is_valid():
			experiment_name = new_experiment_form.cleaned_data['name']
			if experiment.name != experiment_name:
				try:
					name_check = Experiment.objects.get(name=experiment_name)
					name_check_fail = True
					experiment_added = False
				except (Experiment.DoesNotExist, IndexError):
					name_check_fail = False
					experiment.name = experiment_name
					experiment.user = new_experiment_form.cleaned_data['user']
					experiment.field = new_experiment_form.cleaned_data['field']
					experiment.start_date = new_experiment_form.cleaned_data['start_date']
					experiment.purpose = new_experiment_form.cleaned_data['purpose']
					experiment.comments = new_experiment_form.cleaned_data['comments']
					experiment.save()
					experiment_added = True
			else:
				name_check_fail = False
				experiment.name = experiment_name
				experiment.user = new_experiment_form.cleaned_data['user']
				experiment.field = new_experiment_form.cleaned_data['field']
				experiment.start_date = new_experiment_form.cleaned_data['start_date']
				experiment.purpose = new_experiment_form.cleaned_data['purpose']
				experiment.comments = new_experiment_form.cleaned_data['comments']
				experiment.save()
				experiment_added = True
		else:
			print(new_experiment_form.errors)
			name_check_fail = False
			experiment_added = False
	else:
		experiment_info = Experiment.objects.filter(id=experiment_id).values('name', 'field', 'user', 'start_date', 'purpose', 'comments')
		new_experiment_form = NewExperimentForm(initial=experiment_info[0])
		name_check_fail = False
		experiment_added = False
	context_dict['new_experiment_form'] = new_experiment_form
	context_dict['name_check_fail'] = name_check_fail
	context_dict['experiment_added'] = experiment_added
	context_dict['logged_in_user'] = request.user.username
	context_dict['experiment_id'] = experiment_id
	context_dict['experiment_name'] = experiment_name
	return render(request, 'lab/experiment_edit.html', context=context_dict)

def find_stock_collected_from_experiment(experiment_name):
	try:
		collected_stock_data = ObsTrackerSource.objects.filter(source_obs__experiment__name=experiment_name, source_obs__obs_entity_type='experiment', target_obs__obs_entity_type='stock', relationship='stock_from_experiment')
	except ObsTracker.DoesNotExist:
		try:
			collected_stock_data = ObsTrackerSource.objects.filter(source_obs__experiment__name=experiment_name, target_obs__obs_entity_type='stock')
		except ObsTracker.DoesNotExist:
			collected_stock_data = None
	return collected_stock_data

def datatable_seed_inventory(request):
	selected_stocks = []
	(selected_stocks, return_type) = checkbox_seed_inventory_sort(request)
	count = 0
	arr = []
	for data in selected_stocks:
		if return_type == 'stock':
			arr.append({
				'input': '<input type="checkbox" name="checkbox_stock" value="%s">'%(data.id),
	        	'id': data.id,
	        	'seed_id': data.seed_id,
	        	'cross_type': data.cross_type,
	        	'pedigree': data.pedigree,
	        	'population': data.passport.taxonomy.population,
	        	'status': data.stock_status,
	        	'collector': data.passport.collecting.user.username,
	        	'comments': data.comments,
	    	})
		if return_type == 'measurement':
			arr.append({
				'input': '<input type="checkbox" name="checkbox_stock" value="%s">'%(data['id']),
	        	'id': data['id'],
	        	'seed_id': data['seed_id'],
	        	'cross_type': data['cross_type'],
	        	'pedigree': data['pedigree'],
	        	'population': data['population'],
	        	'status': data['stock_status'],
	        	'collector': data['collector'],
	        	'comments': data['comments'],
	    	})
	return JsonResponse({'data':arr, 'count':count}, safe=True)

def unique_selected_stocks(selected_stocks):
	unique_seed_id = []
	unique_stock_list = []
	for s in selected_stocks:
		if s.obs_tracker.stock.seed_id not in unique_seed_id:
			unique_seed_id.append(s.obs_tracker.stock.seed_id)
			unique_stock_list.append({'id':s.obs_tracker.stock_id, 'seed_id':s.obs_tracker.stock.seed_id, 'cross_type':s.obs_tracker.stock.cross_type, 'pedigree':s.obs_tracker.stock.pedigree, 'population':s.obs_tracker.stock.passport.taxonomy.population, 'stock_status':s.obs_tracker.stock.stock_status, 'collector':s.obs_tracker.stock.passport.collecting.user.username, 'comments':s.obs_tracker.stock.comments})
	return unique_stock_list

def checkbox_seed_inventory_sort(request):
	selected_stocks = {}
	checkbox_taxonomy_list = []
	checkbox_pedigree_list = []
	if request.session.get('checkbox_taxonomy', None):
		checkbox_taxonomy_list = request.session.get('checkbox_taxonomy')
		if request.session.get('checkbox_pedigree', None):
			checkbox_pedigree_list = request.session.get('checkbox_pedigree')
			if request.session.get('checkbox_seedinv_parameters', None):
				checkbox_parameters_list = request.session.get('checkbox_seedinv_parameters')
				for parameter in checkbox_parameters_list:
					for pedigree in checkbox_pedigree_list:
						for taxonomy in checkbox_taxonomy_list:
							stocks = Measurement.objects.filter(obs_tracker__stock__pedigree=pedigree, obs_tracker__stock__passport__taxonomy__population=taxonomy, measurement_parameter__parameter=parameter)
							selected_stocks = list(chain(selected_stocks, stocks))
				selected_stocks=unique_selected_stocks(selected_stocks)
				return_type='measurement'
			else:
				for pedigree in checkbox_pedigree_list:
					for taxonomy in checkbox_taxonomy_list:
						stocks = Stock.objects.filter(pedigree=pedigree, passport__taxonomy__population=taxonomy)
						selected_stocks = list(chain(selected_stocks, stocks))
				return_type='stock'
		else:
			if request.session.get('checkbox_seedinv_parameters', None):
				checkbox_parameters_list = request.session.get('checkbox_seedinv_parameters')
				for parameter in checkbox_parameters_list:
					for taxonomy in checkbox_taxonomy_list:
						stocks = Measurement.objects.filter(obs_tracker__stock__passport__taxonomy__population=taxonomy, measurement_parameter__parameter=parameter)
						selected_stocks = list(chain(selected_stocks, stocks))
				selected_stocks=unique_selected_stocks(selected_stocks)
				return_type='measurement'
			else:
				for taxonomy in checkbox_taxonomy_list:
					stocks = Stock.objects.filter(passport__taxonomy__population=taxonomy)
					selected_stocks = list(chain(selected_stocks, stocks))
				return_type='stock'
	else:
		if request.session.get('checkbox_pedigree', None):
			checkbox_pedigree_list = request.session.get('checkbox_pedigree')
			if request.session.get('checkbox_seedinv_parameters', None):
				checkbox_parameters_list = request.session.get('checkbox_seedinv_parameters')
				for parameter in checkbox_parameters_list:
					for pedigree in checkbox_pedigree_list:
						stocks = Measurement.objects.filter(obs_tracker__stock__pedigree=pedigree, measurement_parameter__parameter=parameter)
						selected_stocks = list(chain(selected_stocks, stocks))
				selected_stocks=unique_selected_stocks(selected_stocks)
				return_type='measurement'
			else:
				for pedigree in checkbox_pedigree_list:
					stocks = Stock.objects.filter(pedigree=pedigree)
					selected_stocks = list(chain(selected_stocks, stocks))
				return_type='stock'
		else:
			if request.session.get('checkbox_seedinv_parameters', None):
				checkbox_parameters_list = request.session.get('checkbox_seedinv_parameters')
				for parameter in checkbox_parameters_list:
					stocks = Measurement.objects.filter(measurement_parameter__parameter=parameter)
					selected_stocks = list(chain(selected_stocks, stocks))
				selected_stocks=unique_selected_stocks(selected_stocks)
				return_type='measurement'
			else:
				selected_stocks = list(Stock.objects.all().exclude(seed_id='0').exclude(passport_id='2').exclude(id=1))[:1000]
				return_type='stock'
	return (selected_stocks, return_type)

def checkbox_session_variable_check(request):
	context_dict = {}
	if request.session.get('checkbox_pedigree', None):
		context_dict['checkbox_pedigree'] = request.session.get('checkbox_pedigree')
	if request.session.get('checkbox_taxonomy', None):
		context_dict['checkbox_taxonomy'] = request.session.get('checkbox_taxonomy')
	if request.session.get('checkbox_isolate_disease', None):
		context_dict['checkbox_isolate_disease'] = request.session.get('checkbox_isolate_disease')
	if request.session.get('checkbox_isolate_taxonomy', None):
		context_dict['checkbox_isolate_taxonomy'] = request.session.get('checkbox_isolate_taxonomy')
	if request.session.get('checkbox_row_experiment', None):
		context_dict['checkbox_row_experiment'] = request.session.get('checkbox_row_experiment')
	if request.session.get('checkbox_plant_experiment', None):
		context_dict['checkbox_plant_experiment'] = request.session.get('checkbox_plant_experiment')
	if request.session.get('checkbox_tissue_experiment', None):
		context_dict['checkbox_tissue_experiment'] = request.session.get('checkbox_tissue_experiment')
	if request.session.get('checkbox_plate_experiment', None):
		context_dict['checkbox_plate_experiment'] = request.session.get('checkbox_plate_experiment')
	if request.session.get('checkbox_well_experiment', None):
		context_dict['checkbox_well_experiment'] = request.session.get('checkbox_well_experiment')
	if request.session.get('checkbox_dna_experiment', None):
		context_dict['checkbox_dna_experiment'] = request.session.get('checkbox_dna_experiment')
	if request.session.get('checkbox_culture_experiment', None):
		context_dict['checkbox_culture_experiment'] = request.session.get('checkbox_culture_experiment')
	if request.session.get('checkbox_maize_experiment', None):
		context_dict['checkbox_maize_experiment'] = request.session.get('checkbox_maize_experiment')
	if request.session.get('checkbox_sample_experiment', None):
		context_dict['checkbox_sample_experiment'] = request.session.get('checkbox_sample_experiment')
	if request.session.get('checkbox_microbe_experiment', None):
		context_dict['checkbox_microbe_experiment'] = request.session.get('checkbox_microbe_experiment')
	if request.session.get('checkbox_env_experiment', None):
		context_dict['checkbox_env_experiment'] = request.session.get('checkbox_env_experiment')
	if request.session.get('checkbox_measurement_experiment', None):
		context_dict['checkbox_measurement_experiment'] = request.session.get('checkbox_measurement_experiment')
	if request.session.get('checkbox_measurement_parameter', None):
		context_dict['checkbox_measurement_parameter'] = request.session.get('checkbox_measurement_parameter')
	if request.session.get('checkbox_seedinv_parameters', None):
		context_dict['checkbox_seedinv_parameters'] = request.session.get('checkbox_seedinv_parameters')
	if request.session.get('checkbox_isolate_disease_names', None):
		context_dict['checkbox_isolate_disease_names'] = request.session.get('checkbox_isolate_disease_names')
	if request.session.get('checkbox_isolate_taxonomy_names', None):
		context_dict['checkbox_isolate_taxonomy_names'] = request.session.get('checkbox_isolate_taxonomy_names')
	return context_dict

@login_required
def seed_inventory(request):
	context_dict = {}
	context_dict = checkbox_session_variable_check(request)
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/seed_inventory.html', context=context_dict)

def show_all_seedinv_taxonomy(request):
	taxonomy_list = []
	if request.session.get('checkbox_pedigree', None):
		checkbox_pedigree_list = request.session.get('checkbox_pedigree')
		for pedigree in checkbox_pedigree_list:
			taxonomy = Stock.objects.filter(pedigree=pedigree).values('pedigree', 'passport__taxonomy__population', 'passport__taxonomy__species').distinct()
			taxonomy_list = list(chain(taxonomy, taxonomy_list))
		for t in taxonomy_list:
			t['input'] = '<input type="checkbox" name="checkbox_taxonomy" value="%s">' % (t['passport__taxonomy__population'])
	else:
		taxonomy_list = list(Taxonomy.objects.filter(common_name='Maize').values('population', 'species').distinct())
		for t in taxonomy_list:
			t['input'] = '<input type="checkbox" name="checkbox_taxonomy" value="%s">' % (t['population'])
			t['passport__taxonomy__population'] = t['population']
			t['passport__taxonomy__species'] = t['species']
			t['pedigree'] = ''
	return JsonResponse({'data':taxonomy_list})

def show_all_seedinv_pedigree(request):
	pedigree_list = []
	if request.session.get('checkbox_taxonomy', None):
		checkbox_taxonomy_list = request.session.get('checkbox_taxonomy')
		for taxonomy in checkbox_taxonomy_list:
			pedigree = Stock.objects.filter(passport__taxonomy__population=taxonomy).values('pedigree', 'passport__taxonomy__population').distinct()
			pedigree_list = list(chain(pedigree, pedigree_list))
		for p in pedigree_list:
			p['input'] = '<input type="checkbox" name="checkbox_pedigree" value="%s">' % (p['pedigree'])
	else:
		pedigree_list = list(Stock.objects.all().values('pedigree', 'passport__taxonomy__population').distinct())
		for p in pedigree_list:
			p['input'] = '<input type="checkbox" name="checkbox_pedigree" value="%s">' % (p['pedigree'])
	return JsonResponse({'data':pedigree_list})

def show_all_seedinv_parameters(request):
	parameter_list = []
	if request.session.get('checkbox_taxonomy', None):
		checkbox_taxonomy_list = request.session.get('checkbox_taxonomy')

		if request.session.get('checkbox_pedigree', None):
			checkbox_pedigree_list = request.session.get('checkbox_pedigree')
			parameter_list_unique = []
			parameter_names_unique = []
			for taxonomy in checkbox_taxonomy_list:
				for pedigree in checkbox_pedigree_list:
					parameters = Measurement.objects.filter(obs_tracker__stock__passport__taxonomy__population=taxonomy, obs_tracker__stock__pedigree=pedigree).values('measurement_parameter__parameter', 'measurement_parameter__protocol', 'measurement_parameter__unit_of_measure').distinct()
					parameter_list = list(chain(parameters, parameter_list))
			for p in parameter_list:
				if p['measurement_parameter__parameter'] not in parameter_names_unique:
					parameter_names_unique.append(p['measurement_parameter__parameter'])
					parameter_list_unique.append({'measurement_parameter__parameter':p['measurement_parameter__parameter'], 'measurement_parameter__protocol':p['measurement_parameter__protocol'], 'measurement_parameter__unit_of_measure':p['measurement_parameter__unit_of_measure'], 'input':'<input type="checkbox" name="checkbox_seedinv_parameters" value="%s">' % (p['measurement_parameter__parameter'])})
			parameter_list = parameter_list_unique
		else:
			for taxonomy in checkbox_taxonomy_list:
				parameters = Measurement.objects.filter(obs_tracker__stock__passport__taxonomy__population=taxonomy).values('measurement_parameter__parameter', 'measurement_parameter__protocol', 'measurement_parameter__unit_of_measure').distinct()
				parameter_list = list(chain(parameters, parameter_list))
			for p in parameter_list:
				p['input'] = '<input type="checkbox" name="checkbox_seedinv_parameters" value="%s">' % (p['measurement_parameter__parameter'])
	elif request.session.get('checkbox_pedigree', None):
		checkbox_pedigree_list = request.session.get('checkbox_pedigree')
		for pedigree in checkbox_pedigree_list:
			parameters = Measurement.objects.filter(obs_tracker__stock__pedigree=pedigree).values('measurement_parameter__parameter', 'measurement_parameter__protocol', 'measurement_parameter__unit_of_measure').distinct()
			parameter_list = list(chain(parameters, parameter_list))
		for p in parameter_list:
			p['input'] = '<input type="checkbox" name="checkbox_seedinv_parameters" value="%s">' % (p['measurement_parameter__parameter'])
	else:
		parameter_list = list(Measurement.objects.all().values('measurement_parameter__parameter', 'measurement_parameter__protocol', 'measurement_parameter__unit_of_measure').distinct())
		for p in parameter_list:
			p['input'] = '<input type="checkbox" name="checkbox_seedinv_parameters" value="%s">' % (p['measurement_parameter__parameter'])
	return JsonResponse({'data':parameter_list})

def seedinv_suggest_parameters(request):
	parameter_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET.get('suggestion', False)
	else:
		starts_with = request.POST.get('suggestion', False)
	if starts_with:
		if request.session.get('checkbox_taxonomy', None):
			checkbox_taxonomy_list = request.session.get('checkbox_taxonomy')
			if request.session.get('checkbox_pedigree', None):
				checkbox_pedigree_list = request.session.get('checkbox_pedigree')
				parameter_list_unique = []
				parameter_names_unique = []
				for taxonomy in checkbox_taxonomy_list:
					for pedigree in checkbox_pedigree_list:
						parameters = Measurement.objects.filter(measurement_parameter__parameter__contains=starts_with, obs_tracker__stock__passport__taxonomy__population=taxonomy, obs_tracker__stock__pedigree=pedigree).values('measurement_parameter__parameter', 'measurement_parameter__protocol', 'measurement_parameter__unit_of_measure').distinct()
						parameter_list = list(chain(parameters, parameter_list))
				for p in parameter_list:
					if p['measurement_parameter__parameter'] not in parameter_names_unique:
						parameter_names_unique.append(p['measurement_parameter__parameter'])
						parameter_list_unique.append({'measurement_parameter__parameter':p['measurement_parameter__parameter'], 'measurement_parameter__protocol':p['measurement_parameter__protocol'], 'measurement_parameter__unit_of_measure':p['measurement_parameter__unit_of_measure'], 'input':'<input type="checkbox" name="checkbox_seedinv_parameters" value="%s">' % (p['measurement_parameter__parameter'])})
				parameter_list = parameter_list_unique
			else:
				for taxonomy in checkbox_taxonomy_list:
					parameters = Measurement.objects.filter(measurement_parameter__parameter__contains=starts_with, obs_tracker__stock__passport__taxonomy__population=taxonomy).values('measurement_parameter__parameter', 'measurement_parameter__protocol', 'measurement_parameter__unit_of_measure').distinct()
					parameter_list = list(chain(parameters, parameter_list))
				for p in parameter_list:
					p['input'] = '<input type="checkbox" name="checkbox_seedinv_parameters" value="%s">' % (p['measurement_parameter__parameter'])
		elif request.session.get('checkbox_pedigree', None):
			checkbox_pedigree_list = request.session.get('checkbox_pedigree')
			for pedigree in checkbox_pedigree_list:
				parameters = Measurement.objects.filter(measurement_parameter__parameter__contains=starts_with, obs_tracker__stock__pedigree=pedigree).values('measurement_parameter__parameter', 'measurement_parameter__protocol', 'measurement_parameter__unit_of_measure').distinct()
				parameter_list = list(chain(parameters, parameter_list))
			for p in parameter_list:
				p['input'] = '<input type="checkbox" name="checkbox_seedinv_parameters" value="%s">' % (p['measurement_parameter__parameter'])
		else:
			parameter_list = list(Measurement.objects.filter(measurement_parameter__parameter__contains=starts_with).values('measurement_parameter__parameter', 'measurement_parameter__protocol', 'measurement_parameter__unit_of_measure').distinct())
			for p in parameter_list:
				p['input'] = '<input type="checkbox" name="checkbox_seedinv_parameters" value="%s">' % (p['measurement_parameter__parameter'])
	return JsonResponse({'data':parameter_list})

def suggest_pedigree(request):
	pedigree_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET.get('suggestion', False)
	else:
		starts_with = request.POST.get('suggestion', False)
	if starts_with:
		if request.session.get('checkbox_taxonomy', None):
			checkbox_taxonomy_list = request.session.get('checkbox_taxonomy')
			for taxonomy in checkbox_taxonomy_list:
				pedigree = Stock.objects.filter(pedigree__contains=starts_with, passport__taxonomy__population=taxonomy).values('pedigree', 'passport__taxonomy__population').distinct()
				pedigree_list = list(chain(pedigree, pedigree_list))
			for p in pedigree_list:
				p['input'] = '<input type="checkbox" name="checkbox_pedigree" value="%s">' % (p['pedigree'])
		else:
			pedigree_list = list(Stock.objects.filter(pedigree__contains=starts_with).values('pedigree', 'passport__taxonomy__population').distinct())
			for p in pedigree_list:
				p['input'] = '<input type="checkbox" name="checkbox_pedigree" value="%s">' % (p['pedigree'])
	return JsonResponse({'data':pedigree_list})

def suggest_taxonomy(request):
	taxonomy_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET['suggestion']
	else:
		starts_with = request.POST['suggestion']
	if starts_with:
		if request.session.get('checkbox_pedigree', None):
			checkbox_pedigree_list = request.session.get('checkbox_pedigree')
			for pedigree in checkbox_pedigree_list:
				taxonomy = Stock.objects.filter(pedigree=pedigree, passport__taxonomy__population__contains=starts_with).values('pedigree', 'passport__taxonomy__population', 'passport__taxonomy__species').distinct()
				taxonomy_list = list(chain(taxonomy, taxonomy_list))
			for t in taxonomy_list:
				t['input'] = '<input type="checkbox" name="checkbox_taxonomy" value="%s">' % (t['passport__taxonomy__population'])
		else:
			taxonomy_list = list(Taxonomy.objects.filter(population__contains=starts_with, common_name='Maize').values('population', 'species').distinct())
			for t in taxonomy_list:
				t['input'] = '<input type="checkbox" name="checkbox_taxonomy" value="%s">' % (t['population'])
				t['passport__taxonomy__population'] = t['population']
				t['passport__taxonomy__species'] = t['species']
				t['pedigree'] = ''
	return JsonResponse({'data':taxonomy_list})

def select_pedigree(request):
	pedigrees = request.POST['pedigrees']
	pedigree_list = json.loads(pedigrees)
	request.session['checkbox_pedigree'] = pedigree_list
	return JsonResponse({'success':True})

def select_taxonomy(request):
	taxonomy = request.POST['taxonomy']
	taxonomy_list = json.loads(taxonomy)
	request.session['checkbox_taxonomy'] = taxonomy_list
	return JsonResponse({'success':True})

def select_seedinv_parameters(request):
	parameters = request.POST['parameters']
	parameters_list = json.loads(parameters)
	request.session['checkbox_seedinv_parameters'] = parameters_list
	return JsonResponse({'success':True})

def checkbox_clear(request, clear_selected):
	del request.session[clear_selected]
	return JsonResponse({'success':True})

def sort_seed_set(set_type):
	packet_data = []
	if set_type == '282':
		seed_set = ['811','3316','3811','4226','4722','A188','A214N','A239','A4415','A554','A556','A6','A619','A632','A634','A635','A641','A654','A659','A661','A679','A680','A682','AB28A','B10','B103','B104','B105','B109','B115','B14A','B164','B2','B37','B46','B52','B57','B64','B68','B73','B73HTRHM','B75','B76','B77','B79','B84','B96','B97','C103','C123','C49A','CH70130','CH9','CI1872','CI21E','CI28A','CI31A','CI3A','CI44','CI64','CI66','CI7','CI90C','CI91B','CM105','CM174','CM37','CM7','CML10','CML103','CML108','CML11','CML14','CML154Q','CML157Q','CML158Q','CML16','CML218','CML220','CML228','CML238','CML247','CML254','CML258','CML261','CML264','CML277','CML281','CML287','CML311','CML314','CML321','CML322','CML323','CML328','CML329','CML331','CML332','CML333','CML341','CML367','CML38','CML40','CML45','CML48','CML5','CML52','CML56','CML61','CML69','CML9','CML91','CML92','CMV3','CO106','CO109','CO125','CO255','D940Y','DE1','DE2','DE3','DE811','E2558W','EP1','F2','F2834T','F44','F6','F7','FR1064','GA209','GE440','GT112','H100','H105W','H49','H84','H91','H95','H99','HI27','HP301','HY','I137TN','I205','I29','IA2132','IA5125B','IDS28','IDS69','IDS91','IL101T','IL14H','IL677A','K148','K4','K55','K64','KI11','KI14','KI2007','KI2021','KI21','KI3','KI43','KI44','KUI2007','KY21','KY226','KY228','L317','L578','M14','M162W','M37W','MO16W','MO17','MO18W','MO1W','MO24W','MO44','MO45','MO46','MO47','MOG','MP313E','MP339','MP717','MS1334','MS153','MS71','MT42','N192','N28HT','N6','N7A','NC222','NC230','NC232','NC236','NC238','NC250','NC250A','NC258','NC260','NC262','NC264','NC268','NC290A','NC292','NC294','NC296','NC296A','NC298','NC300','NC302','NC304','NC306','NC308','NC310','NC312','NC314','NC316','NC318','NC320','NC322','NC324','NC326','NC328','NC33','NC330','NC332','NC334','NC336','NC338','NC340','NC342','NC344','NC346','NC348','NC350','NC352','NC354','NC356','NC358','NC360','NC362','NC364','NC366','NC368','NC370','NC372','ND246','OH40B','OH43','OH43E','OH603','OH7B','OS420','P39','PA762','PA875','PA880','PA91','R109B','R168','R177','R229','R4','SA24','SC213R','SC357','SC55','SD40','SD44','SG1533','SG18','T232','T234','T8','TX303','TX601','TZI10','TZI11','TZI16','TZI18','TZI25','TZI8','TZI9','U267Y','VA102','VA14','VA17','VA22','VA26','VA35','VA59','VA85','VA99','VAW6','W117HT','W153R','W182B','W22','W401','W64A','WF9','YU796NS']
	if set_type == '282_jenny_subset':
		seed_set = ['B105','B115','B75','M14','VA35','B97','IL677A','VA99','NC330','B109','MO44','MO46','B104','NC260','W22','A680','B14A','HY','NC310','PA91','N7A','H100','NC308','MO1W','VA102','H49','NC250','A659','IDS69','B2','I205','N28HT','NC364','B73','PA762','PA880','VAW6','IDS28','K55','NC372','VA85','C103','HP301','NC290A','NC342','NC326','NC328','B77','B79','H95','NC362','B84','SG18','B46','B73HTRHM','GE440','MO45','NC314','H91','K148','NC264','R4','NC316','DE1','VA22','3316','NC294','DE811','NC306']
	seed_data = Stock.objects.filter(pedigree__in=seed_set)
	for seed in seed_data:
		seed_packets = StockPacket.objects.filter(stock_id=seed.id)
		packet_data = list(chain(seed_packets, packet_data))
	return packet_data

@login_required
def seed_set_download(request, set_type):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="seed_inventory_set.csv"'
	packet_data = sort_seed_set(set_type)
	writer = csv.writer(response)
	writer.writerow(['Seed ID', 'Seed Name', 'Pedigree', 'Cross Type', 'Stock Status', 'Stock Date', 'Inoculated', 'Stock Comments', 'Weight(g)', 'Num Seeds', 'Packet Comments', 'Location Name', 'Building Name', 'Room', 'Shelf', 'Column', 'BoxName', 'Location Comments'])
	for row in packet_data:
		writer.writerow([row.stock.seed_id, row.stock.seed_name, row.stock.pedigree, row.stock.cross_type, row.stock.stock_status, row.stock.stock_date, row.stock.inoculated, row.stock.comments, row.weight, row.num_seeds, row.comments, row.location.location_name, row.location.building_name, row.location.room, row.location.shelf, row.location.column, row.location.box_name, row.location.comments])
	return response

@login_required
def update_seed_info(request, stock_id):
	context_dict = {}
	if request.method == 'POST':
		obs_tracker_stock_form = UpdateSeedDataOnlineForm(data=request.POST)
		if obs_tracker_stock_form.is_valid():
			with transaction.atomic():
				try:
					obs_tracker = ObsTracker.objects.get(obs_entity_type='stock', stock_id=stock_id, experiment=obs_tracker_stock_form.cleaned_data['experiment'])
					obs_tracker.glycerol_stock_id = 1
					obs_tracker.maize_sample_id = 1
					obs_tracker.obs_extract_id = 1
					if obs_tracker_stock_form.cleaned_data['obs_row__row_id'] != '':
						obs_tracker.obs_row = ObsRow.objects.get(row_id=obs_tracker_stock_form.cleaned_data['obs_row__row_id'])
					else:
						obs_tracker.obs_row = ObsRow.objects.get(id=1)
					if obs_tracker_stock_form.cleaned_data['obs_plant__plant_id']:
						obs_tracker.obs_plant = ObsPlant.objects.get(plant_id=obs_tracker_stock_form.cleaned_data['obs_plant__plant_id'])
					else:
						obs_tracker.obs_plant = ObsPlant.objects.get(id=1)
					obs_tracker.field = obs_tracker_stock_form.cleaned_data['field']

					stock = Stock.objects.get(id=stock_id)
					stock.seed_id = obs_tracker_stock_form.cleaned_data['stock__seed_id']
					stock.seed_name = obs_tracker_stock_form.cleaned_data['stock__seed_name']
					stock.cross_type = obs_tracker_stock_form.cleaned_data['stock__cross_type']
					stock.pedigree = obs_tracker_stock_form.cleaned_data['stock__pedigree']
					stock.stock_status = obs_tracker_stock_form.cleaned_data['stock__stock_status']
					stock.stock_date = obs_tracker_stock_form.cleaned_data['stock__stock_date']
					stock.inoculated = obs_tracker_stock_form.cleaned_data['stock__inoculated']
					stock.comments = obs_tracker_stock_form.cleaned_data['stock__comments']
					updated_collecting, created = Collecting.objects.get_or_create(collection_date=obs_tracker_stock_form.cleaned_data['stock__passport__collecting__collection_date'], collection_method=obs_tracker_stock_form.cleaned_data['stock__passport__collecting__collection_method'], comments=obs_tracker_stock_form.cleaned_data['stock__passport__collecting__comments'], user=obs_tracker_stock_form.cleaned_data['stock__passport__collecting__user'])
					updated_people, created = People.objects.get_or_create(first_name=obs_tracker_stock_form.cleaned_data['stock__passport__people__first_name'], last_name=obs_tracker_stock_form.cleaned_data['stock__passport__people__last_name'], organization=obs_tracker_stock_form.cleaned_data['stock__passport__people__organization'], phone=obs_tracker_stock_form.cleaned_data['stock__passport__people__phone'], email=obs_tracker_stock_form.cleaned_data['stock__passport__people__email'], comments=obs_tracker_stock_form.cleaned_data['stock__passport__people__comments'])
					updated_taxonomy, created = Taxonomy.objects.get_or_create(genus=obs_tracker_stock_form.cleaned_data['stock__passport__taxonomy__genus'], species=obs_tracker_stock_form.cleaned_data['stock__passport__taxonomy__species'], population=obs_tracker_stock_form.cleaned_data['stock__passport__taxonomy__population'], common_name='Maize', alias='', race='', subtaxa='')
					updated_passport, created = Passport.objects.get_or_create(collecting=updated_collecting, people=updated_people, taxonomy=updated_taxonomy)
					stock.passport = updated_passport
					stock.save()
					obs_tracker.save()
					context_dict['updated'] = True
				except Exception:
					context_dict['failed'] = True
		else:
			print(obs_tracker_stock_form.errors)
	else:
		stock_data = ObsTracker.objects.filter(obs_entity_type='stock', stock_id=stock_id).values('experiment', 'stock__seed_id', 'stock__seed_name', 'stock__cross_type', 'stock__pedigree', 'stock__stock_status', 'stock__stock_date', 'stock__inoculated', 'stock__comments', 'stock__passport__collecting__user', 'stock__passport__collecting__collection_date', 'stock__passport__collecting__collection_method', 'stock__passport__collecting__comments', 'stock__passport__people__first_name', 'stock__passport__people__last_name', 'stock__passport__people__organization', 'stock__passport__people__phone', 'stock__passport__people__email', 'stock__passport__people__comments', 'stock__passport__taxonomy__genus', 'stock__passport__taxonomy__species', 'stock__passport__taxonomy__population', 'obs_row__row_id', 'obs_plant__plant_id', 'field')
		obs_tracker_stock_form = UpdateSeedDataOnlineForm(initial=stock_data[0])
	context_dict['stock_id'] = stock_id
	context_dict['obs_tracker_stock_form'] = obs_tracker_stock_form
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/stock_info_update.html', context=context_dict)

@login_required
def update_seed_packet_info(request, stock_id):
	context_dict = {}
	num_packets = StockPacket.objects.filter(stock_id=stock_id).count()
	EditStockPacketFormSet = formset_factory(LogStockPacketOnlineForm, extra=0)
	if request.method == 'POST':
		edit_packet_form_set = EditStockPacketFormSet(request.POST)
		if edit_packet_form_set.is_valid():
			failed = None
			with transaction.atomic():
				for form in edit_packet_form_set:
					step = 0
					while step < num_packets:
						try:
							update_packet = StockPacket.objects.filter(stock_id=stock_id)[step]
							update_packet.weight = form.cleaned_data['weight']
							update_packet.num_seeds = form.cleaned_data['num_seeds']
							update_packet.comments = form.cleaned_data['comments']
							update_packet.location, created = Location.objects.get_or_create(locality=form.cleaned_data['location__locality'], building_name=form.cleaned_data['location__building_name'], location_name=form.cleaned_data['location__location_name'], room=form.cleaned_data['location__room'], shelf=form.cleaned_data['location__shelf'], column=form.cleaned_data['location__column'], box_name=form.cleaned_data['location__box_name'], comments=form.cleaned_data['location__comments'])
							update_packet.save()
						except Exception as e:
							print("Error: %s %s" % (e.message, e.args))
							failed = True
						step = step + 1
			if failed is not None:
				context_dict['failed'] = True
			else:
				context_dict['saved'] = True
		else:
			print(edit_packet_form_set.errors)
	else:
		packets = StockPacket.objects.filter(stock_id=stock_id).values('stock__seed_id', 'weight', 'num_seeds', 'comments', 'location__building_name', 'location__location_name', 'location__room', 'location__shelf', 'location__column', 'location__box_name', 'location__comments', 'location__locality')
		edit_packet_form_set = EditStockPacketFormSet(initial=packets)
	context_dict['edit_packet_form_set'] = edit_packet_form_set
	context_dict['stock_id'] = stock_id
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/stockpacket_info_update.html', context=context_dict)


def stock_page_measurement_plot(request):
	data = []
	stock_id = request.POST.get('stock_id', False)
	parameter_id = request.POST.get('parameter_of_interest', False)
	#all stocks used in experiment
	#stocks with measurements
	#parameter, stock, value
	experiments = ObsTracker.objects.filter(stock_id=stock_id)
	measurements = []
	for exp in experiments:
		m = Measurement.objects.filter(obs_tracker__experiment_id=exp.experiment_id, measurement_parameter_id=parameter_id)
		measurements = list(chain(measurements, m))
	for ms in measurements:
		ms.obs_tracker = make_obs_tracker_info(ms.obs_tracker, '')
		try:
			value = int(ms.value)
		except ValueError:
			try:
				value = float(ms.value)
			except ValueError:
				value = ms.value
		data.append({'parameter':"%s: %s"% (ms.obs_tracker.experiment.name, ms.measurement_parameter.parameter), 'id':"%s: %s"% (ms.obs_tracker.obs_id, ms.id), 'value':value})

	measurements = Measurement.objects.filter(obs_tracker__stock_id=stock_id, measurement_parameter_id=parameter_id)
	for ms in measurements:
		ms.obs_tracker = make_obs_tracker_info(ms.obs_tracker, '')
		try:
			value = int(ms.value)
		except ValueError:
			try:
				value = float(ms.value)
			except ValueError:
				value = ms.value
		data.append({'parameter':"%s: %s"% (ms.obs_tracker.stock.seed_id, ms.measurement_parameter.parameter), 'id':"%s: %s"% (ms.obs_tracker.obs_id, ms.id), 'value':value})

	return JsonResponse({'data':data}, safe=True)

@login_required
def stock_delete(request):
	permissions = check_user_permissions(request)
	if (permissions['is_superuser'] == True):
		stock_id = request.POST.get('stock_id', False)
		Stock.objects.get(id=stock_id).delete()
		message = "Stock successfully deleted."
	else:
		message = "You do not have the correct permissions."

	return JsonResponse({'message':message}, safe=True)

@login_required
def update_isolate_info(request, isolate_id):
	context_dict = {}
	if request.method == 'POST':
		obs_tracker_isolate_form = LogIsolatesOnlineForm(data=request.POST)
		if obs_tracker_isolate_form.is_valid():
			with transaction.atomic():
				try:
					obs_tracker = ObsTracker.objects.get(obs_entity_type='isolate', isolate_id=isolate_id, experiment=obs_tracker_isolate_form.cleaned_data['experiment'])
					obs_tracker.glycerol_stock_id = 1
					obs_tracker.maize_sample_id = 1
					obs_tracker.obs_extract_id = 1
					obs_tracker.location = obs_tracker_isolate_form.cleaned_data['location']
					obs_tracker.field = obs_tracker_isolate_form.cleaned_data['field']
					if obs_tracker_isolate_form.cleaned_data['obs_dna__dna_id'] != '':
						obs_tracker.obs_dna = ObsDNA.objects.get(dna_id=obs_tracker_isolate_form.cleaned_data['obs_dna__dna_id'])
					else:
						obs_tracker.obs_dna = ObsDNA.objects.get(dna_id='No DNA')
					if obs_tracker_isolate_form.cleaned_data['obs_microbe__microbe_id'] != '':
						obs_tracker.obs_microbe = ObsMicrobe.objects.get(microbe_id=obs_tracker_isolate_form.cleaned_data['obs_microbe__microbe_id'])
					else:
						obs_tracker.obs_microbe = ObsMicrobe.objects.get(microbe_id='No Microbe')
					if obs_tracker_isolate_form.cleaned_data['obs_row__row_id'] != '':
						obs_tracker.obs_row = ObsRow.objects.get(row_id=obs_tracker_isolate_form.cleaned_data['obs_row__row_id'])
					else:
						obs_tracker.obs_row = ObsRow.objects.get(row_id='No Row')
					if obs_tracker_isolate_form.cleaned_data['stock__seed_id'] != '':
						obs_tracker.stock = Stock.objects.get(seed_id=obs_tracker_isolate_form.cleaned_data['stock__seed_id'])
					else:
						obs_tracker.stock = Stock.objects.get(seed_id='No Stock')
					if obs_tracker_isolate_form.cleaned_data['obs_plant__plant_id'] != '':
						obs_tracker.obs_plant = ObsPlant.objects.get(plant_id=obs_tracker_isolate_form.cleaned_data['obs_plant__plant_id'])
					else:
						obs_tracker.obs_plant = ObsPlant.objects.get(plant_id='No Plant')
					if obs_tracker_isolate_form.cleaned_data['obs_tissue__tissue_id'] != '':
						obs_tracker.obs_tissue = ObsTissue.objects.get(tissue_id=obs_tracker_isolate_form.cleaned_data['obs_tissue__tissue_id'])
					else:
						obs_tracker.obs_tissue = ObsTissue.objects.get(tissue_id='No Tissue')
					if obs_tracker_isolate_form.cleaned_data['obs_culture__culture_id'] != '':
						obs_tracker.obs_culture = ObsCulture.objects.get(culture_id=obs_tracker_isolate_form.cleaned_data['obs_culture__culture_id'])
					else:
						obs_tracker.obs_culture = ObsCulture.objects.get(culture_id='No Culture')
					if obs_tracker_isolate_form.cleaned_data['obs_plate__plate_id'] != '':
						obs_tracker.obs_plate = ObsPlate.objects.get(plate_id=obs_tracker_isolate_form.cleaned_data['obs_plate__plate_id'])
					else:
						obs_tracker.obs_plate = ObsPlate.objects.get(plate_id='No Plate')
					if obs_tracker_isolate_form.cleaned_data['obs_well__well_id'] != '':
						obs_tracker.obs_well = ObsWell.objects.get(well_id=obs_tracker_isolate_form.cleaned_data['obs_well__well_id'])
					else:
						obs_tracker.obs_well = ObsWell.objects.get(well_id='No Well')

					isolate = Isolate.objects.get(id=isolate_id)
					isolate.isolate_id = obs_tracker_isolate_form.cleaned_data['isolate__isolate_id']
					isolate.isolate_name = obs_tracker_isolate_form.cleaned_data['isolate__isolate_name']
					isolate.disease_info = obs_tracker_isolate_form.cleaned_data['isolate__disease_info']
					isolate.plant_organ = obs_tracker_isolate_form.cleaned_data['isolate__plant_organ']
					isolate.comments = obs_tracker_isolate_form.cleaned_data['isolate__comments']
					isolate.location = obs_tracker_isolate_form.cleaned_data['location']
					updated_taxonomy, created = Taxonomy.objects.get_or_create(genus=obs_tracker_isolate_form.cleaned_data['isolate__passport__taxonomy__genus'], species='', population='', common_name='Isolate', alias=obs_tracker_isolate_form.cleaned_data['isolate__passport__taxonomy__alias'], race=obs_tracker_isolate_form.cleaned_data['isolate__passport__taxonomy__race'], subtaxa=obs_tracker_isolate_form.cleaned_data['isolate__passport__taxonomy__subtaxa'])
					updated_passport, created = Passport.objects.get_or_create(collecting=isolate.passport.collecting, people=isolate.passport.people, taxonomy=updated_taxonomy)
					isolate.passport = updated_passport
					isolate.save()
					obs_tracker.save()
					context_dict['updated'] = True
				except Exception:
					context_dict['failed'] = True
		else:
			print(obs_tracker_isolate_form.errors)
	else:
		isolate_data = ObsTracker.objects.filter(obs_entity_type='isolate', isolate_id=isolate_id).values('experiment', 'isolate__isolate_id', 'location', 'field', 'obs_dna__dna_id', 'obs_microbe__microbe_id', 'obs_row__row_id', 'stock__seed_id', 'obs_plant__plant_id', 'obs_tissue__tissue_id', 'obs_culture__culture_id', 'obs_plate__plate_id', 'obs_well__well_id', 'isolate__isolate_name', 'isolate__disease_info', 'isolate__plant_organ', 'isolate__passport__taxonomy__genus', 'isolate__passport__taxonomy__alias', 'isolate__passport__taxonomy__race', 'isolate__passport__taxonomy__subtaxa', 'isolate__comments')
		obs_tracker_isolate_form = LogIsolatesOnlineForm(initial=isolate_data[0])
	context_dict['isolate_id'] = isolate_id
	context_dict['obs_tracker_isolate_form'] = obs_tracker_isolate_form
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/isolate_info_update.html', context=context_dict)

@login_required
def update_glycerol_stock_info(request, glycerol_stock_id):
	context_dict = {}
	if request.method == 'POST':
		obs_tracker_glycerol_stock_form = LogGlycerolStocksOnlineForm(data=request.POST)
		if obs_tracker_glycerol_stock_form.is_valid():
			with transaction.atomic():
				try:
					obs_tracker = ObsTracker.objects.get(obs_entity_type='glycerol_stock', glycerol_stock_id=glycerol_stock_id, experiment=obs_tracker_glycerol_stock_form.cleaned_data['experiment'])
					obs_tracker.maize_sample_id = 1
					obs_tracker.obs_extract_id = 1
					obs_tracker.location = obs_tracker_glycerol_stock_form.cleaned_data['location']
					obs_tracker.field = obs_tracker_glycerol_stock_form.cleaned_data['field']
					if obs_tracker_glycerol_stock_form.cleaned_data['obs_dna__dna_id'] != '':
						obs_tracker.obs_dna = ObsDNA.objects.get(dna_id=obs_tracker_glycerol_stock_form.cleaned_data['obs_dna__dna_id'])
					else:
						obs_tracker.obs_dna = ObsDNA.objects.get(dna_id='No DNA')
					if obs_tracker_glycerol_stock_form.cleaned_data['obs_microbe__microbe_id'] != '':
						obs_tracker.obs_microbe = ObsMicrobe.objects.get(microbe_id=obs_tracker_glycerol_stock_form.cleaned_data['obs_microbe__microbe_id'])
					else:
						obs_tracker.obs_microbe = ObsMicrobe.objects.get(microbe_id='No Microbe')
					if obs_tracker_glycerol_stock_form.cleaned_data['obs_row__row_id'] != '':
						obs_tracker.obs_row = ObsRow.objects.get(row_id=obs_tracker_glycerol_stock_form.cleaned_data['obs_row__row_id'])
					else:
						obs_tracker.obs_row = ObsRow.objects.get(row_id='No Row')
					if obs_tracker_glycerol_stock_form.cleaned_data['stock__seed_id'] != '':
						obs_tracker.stock = Stock.objects.get(seed_id=obs_tracker_glycerol_stock_form.cleaned_data['stock__seed_id'])
					else:
						obs_tracker.stock = Stock.objects.get(seed_id='No Stock')
					if obs_tracker_glycerol_stock_form.cleaned_data['obs_plant__plant_id'] != '':
						obs_tracker.obs_plant = ObsPlant.objects.get(plant_id=obs_tracker_glycerol_stock_form.cleaned_data['obs_plant__plant_id'])
					else:
						obs_tracker.obs_plant = ObsPlant.objects.get(plant_id='No Plant')
					if obs_tracker_glycerol_stock_form.cleaned_data['obs_tissue__tissue_id'] != '':
						obs_tracker.obs_tissue = ObsTissue.objects.get(tissue_id=obs_tracker_glycerol_stock_form.cleaned_data['obs_tissue__tissue_id'])
					else:
						obs_tracker.obs_tissue = ObsTissue.objects.get(tissue_id='No Tissue')
					if obs_tracker_glycerol_stock_form.cleaned_data['obs_culture__culture_id'] != '':
						obs_tracker.obs_culture = ObsCulture.objects.get(culture_id=obs_tracker_glycerol_stock_form.cleaned_data['obs_culture__culture_id'])
					else:
						obs_tracker.obs_culture = ObsCulture.objects.get(culture_id='No Culture')
					if obs_tracker_glycerol_stock_form.cleaned_data['obs_plate__plate_id'] != '':
						obs_tracker.obs_plate = ObsPlate.objects.get(plate_id=obs_tracker_glycerol_stock_form.cleaned_data['obs_plate__plate_id'])
					else:
						obs_tracker.obs_plate = ObsPlate.objects.get(plate_id='No Plate')
					if obs_tracker_glycerol_stock_form.cleaned_data['obs_well__well_id'] != '':
						obs_tracker.obs_well = ObsWell.objects.get(well_id=obs_tracker_glycerol_stock_form.cleaned_data['obs_well__well_id'])
					else:
						obs_tracker.obs_well = ObsWell.objects.get(well_id='No Well')
					if obs_tracker_glycerol_stock_form.cleaned_data['obs_sample__sample_id'] != '':
						obs_tracker.obs_sample = ObsSample.objects.get(sample_id=obs_tracker_glycerol_stock_form.cleaned_data['obs_sample__sample_id'])
					else:
						obs_tracker.obs_sample = ObsSample.objects.get(sample_id='No Sample')
					if obs_tracker_glycerol_stock_form.cleaned_data['isolate__isolate_id'] != '':
						obs_tracker.isolate = Isolate.objects.get(isolate_id=obs_tracker_glycerol_stock_form.cleaned_data['isolate__isolate_id'])
					else:
						obs_tracker.isolate = Isolate.objects.get(isolate_id='No Isolate')

					gstock = GlycerolStock.objects.get(id=glycerol_stock_id)
					gstock.glycerol_stock_id = obs_tracker_glycerol_stock_form.cleaned_data['glycerol_stock__glycerol_stock_id']
					gstock.stock_date = obs_tracker_glycerol_stock_form.cleaned_data['glycerol_stock__stock_date']
					gstock.extract_color = obs_tracker_glycerol_stock_form.cleaned_data['glycerol_stock__extract_color']
					gstock.organism = obs_tracker_glycerol_stock_form.cleaned_data['glycerol_stock__organism']
					gstock.comments = obs_tracker_glycerol_stock_form.cleaned_data['glycerol_stock__comments']
					gstock.save()
					obs_tracker.save()
					context_dict['updated'] = True
				except Exception:
					context_dict['failed'] = True
		else:
			print(obs_tracker_glycerol_stock_form.errors)
	else:
		glycerol_stock_data = ObsTracker.objects.filter(obs_entity_type='glycerol_stock', glycerol_stock_id=glycerol_stock_id).values('experiment', 'glycerol_stock__glycerol_stock_id', 'location', 'glycerol_stock__stock_date', 'glycerol_stock__extract_color', 'glycerol_stock__organism', 'glycerol_stock__comments', 'field', 'obs_dna__dna_id', 'obs_microbe__microbe_id', 'obs_row__row_id', 'stock__seed_id', 'obs_plant__plant_id', 'obs_tissue__tissue_id', 'obs_culture__culture_id', 'obs_plate__plate_id', 'obs_well__well_id', 'obs_sample__sample_id', 'isolate__isolate_id')
		obs_tracker_glycerol_stock_form = LogGlycerolStocksOnlineForm(initial=glycerol_stock_data[0])
	context_dict['glycerol_stock_id'] = glycerol_stock_id
	context_dict['obs_tracker_glycerol_stock_form'] = obs_tracker_glycerol_stock_form
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/glycerol_stock_info_update.html', context=context_dict)

@login_required
def edit_info(request, obj_type, obj_id):
	context_dict = {}
	if obj_type == 'measurement_parameter':
		if request.method == 'POST':
			measurement_parameter_form = NewMeasurementParameterForm(data=request.POST)
			if measurement_parameter_form.is_valid():
				with transaction.atomic():
					try:
						parameter = MeasurementParameter.objects.get(id=obj_id)
						parameter.parameter = measurement_parameter_form.cleaned_data['parameter']
						parameter.parameter_type = measurement_parameter_form.cleaned_data['parameter_type']
						parameter.protocol = measurement_parameter_form.cleaned_data['protocol']
						parameter.trait_id_buckler = measurement_parameter_form.cleaned_data['trait_id_buckler']
						parameter.unit_of_measure = measurement_parameter_form.cleaned_data['unit_of_measure']
						parameter.save()
						context_dict['updated'] = True
					except Exception:
						context_dict['failed'] = True
			else:
				print(measurement_parameter_form.errors)
		else:
			parameter_data = MeasurementParameter.objects.filter(id=obj_id).values('parameter', 'parameter_type', 'protocol', 'trait_id_buckler', 'unit_of_measure')
			measurement_parameter_form = NewMeasurementParameterForm(initial=parameter_data[0])
		context_dict['measurement_parameter_id'] = obj_id
		context_dict['measurement_parameter_form'] = measurement_parameter_form
		context_dict['logged_in_user'] = request.user.username
		return render(request, 'lab/edit_measurement_parameter.html', context=context_dict)

	elif obj_type == 'medium':
		if request.method == 'POST':
			medium_form = NewMediumForm(data=request.POST)
			if medium_form.is_valid():
				with transaction.atomic():
					try:
						medium = Medium.objects.get(id=obj_id)
						medium.citation = medium_form.cleaned_data['citation']
						medium.media_name = medium_form.cleaned_data['media_name']
						medium.media_type = medium_form.cleaned_data['media_type']
						medium.media_description = medium_form.cleaned_data['media_description']
						medium.media_preparation = medium_form.cleaned_data['media_preparation']
						medium.comments = medium_form.cleaned_data['comments']
						medium.save()
						context_dict['updated'] = True
					except Exception:
						context_dict['failed'] = True
			else:
				print(medium_form.errors)
		else:
			medium_data = Medium.objects.filter(id=obj_id).values('citation', 'media_name', 'media_type', 'media_description', 'media_preparation', 'comments')
			medium_form = NewMediumForm(initial=medium_data[0])
		context_dict['medium_id'] = obj_id
		context_dict['medium_form'] = medium_form
		context_dict['logged_in_user'] = request.user.username
		return render(request, 'lab/edit_medium.html', context=context_dict)

	elif obj_type == 'field':
		if request.method == 'POST':
			field_form = NewFieldForm(data=request.POST)
			if field_form.is_valid():
				with transaction.atomic():
					try:
						field = Field.objects.get(id=obj_id)
						field.locality = field_form.cleaned_data['locality']
						field.field_name = field_form.cleaned_data['field_name']
						field.field_num = field_form.cleaned_data['field_num']
						field.comments = field_form.cleaned_data['comments']
						field.save()
						context_dict['updated'] = True
					except Exception:
						context_dict['failed'] = True
			else:
				print(field_form.errors)
		else:
			field_data = Field.objects.filter(id=obj_id).values('locality', 'field_name', 'field_num', 'comments')
			field_form = NewFieldForm(initial=field_data[0])
		context_dict['field_id'] = obj_id
		context_dict['field_form'] = field_form
		context_dict['logged_in_user'] = request.user.username
		return render(request, 'lab/edit_field.html', context=context_dict)

	elif obj_type == 'locality':
		if request.method == 'POST':
			locality_form = NewLocalityForm(data=request.POST)
			if locality_form.is_valid():
				with transaction.atomic():
					try:
						locality = Locality.objects.get(id=obj_id)
						locality.city = locality_form.cleaned_data['city']
						locality.state = locality_form.cleaned_data['state']
						locality.country = locality_form.cleaned_data['country']
						locality.zipcode = locality_form.cleaned_data['zipcode']
						locality.save()
						context_dict['updated'] = True
					except Exception:
						context_dict['failed'] = True
			else:
				print(locality_form.errors)
		else:
			locality_data = Locality.objects.filter(id=obj_id).values('city', 'state', 'country', 'zipcode')
			locality_form = NewLocalityForm(initial=locality_data[0])
		context_dict['locality_id'] = obj_id
		context_dict['locality_form'] = locality_form
		context_dict['logged_in_user'] = request.user.username
		return render(request, 'lab/edit_locality.html', context=context_dict)

	elif obj_type == 'location':
		if request.method == 'POST':
			location_form = NewLocationForm(data=request.POST)
			if location_form.is_valid():
				with transaction.atomic():
					try:
						location = Location.objects.get(id=obj_id)
						location.locality = location_form.cleaned_data['locality']
						location.location_name = location_form.cleaned_data['location_name']
						location.building_name = location_form.cleaned_data['building_name']
						location.room = location_form.cleaned_data['room']
						location.shelf = location_form.cleaned_data['shelf']
						location.column = location_form.cleaned_data['column']
						location.box_name = location_form.cleaned_data['box_name']
						location.comments = location_form.cleaned_data['comments']
						location.save()
						context_dict['updated'] = True
					except Exception:
						context_dict['failed'] = True
			else:
				print(location_form.errors)
		else:
			location_data = Location.objects.filter(id=obj_id).values('locality', 'location_name', 'building_name', 'room', 'shelf', 'column', 'box_name', 'comments')
			location_form = NewLocationForm(initial=location_data[0])
		context_dict['location_id'] = obj_id
		context_dict['location_form'] = location_form
		context_dict['logged_in_user'] = request.user.username
		return render(request, 'lab/edit_location.html', context=context_dict)

	elif obj_type == 'disease':
		if request.method == 'POST':
			disease_form = NewDiseaseInfoForm(data=request.POST)
			if disease_form.is_valid():
				with transaction.atomic():
					try:
						disease = DiseaseInfo.objects.get(id=obj_id)
						disease.common_name = disease_form.cleaned_data['common_name']
						disease.abbrev = disease_form.cleaned_data['abbrev']
						disease.comments = disease_form.cleaned_data['comments']
						disease.save()
						context_dict['updated'] = True
					except Exception:
						context_dict['failed'] = True
			else:
				print(disease_form.errors)
		else:
			disease_data = DiseaseInfo.objects.filter(id=obj_id).values('common_name', 'abbrev', 'comments')
			disease_form = NewDiseaseInfoForm(initial=disease_data[0])
		context_dict['disease_info_id'] = obj_id
		context_dict['disease_form'] = disease_form
		context_dict['logged_in_user'] = request.user.username
		return render(request, 'lab/edit_disease.html', context=context_dict)

	elif obj_type == 'taxonomy':
		if request.method == 'POST':
			taxonomy_form = NewTaxonomyForm(data=request.POST)
			if taxonomy_form.is_valid():
				with transaction.atomic():
					try:
						taxonomy = Taxonomy.objects.get(id=obj_id)
						taxonomy.genus = taxonomy_form.cleaned_data['genus']
						taxonomy.species = taxonomy_form.cleaned_data['species']
						taxonomy.population = taxonomy_form.cleaned_data['population']
						taxonomy.alias = taxonomy_form.cleaned_data['alias']
						taxonomy.race = taxonomy_form.cleaned_data['race']
						taxonomy.subtaxa = taxonomy_form.cleaned_data['subtaxa']
						taxonomy.save()
						context_dict['updated'] = True
					except Exception:
						context_dict['failed'] = True
			else:
				print(taxonomy_form.errors)
		else:
			taxonomy_data = Taxonomy.objects.filter(id=obj_id).values('genus', 'species', 'population', 'alias', 'race', 'subtaxa')
			taxonomy_form = NewTaxonomyForm(initial=taxonomy_data[0])
		context_dict['taxonomy_id'] = obj_id
		context_dict['taxonomy_form'] = taxonomy_form
		context_dict['logged_in_user'] = request.user.username
		return render(request, 'lab/edit_taxonomy.html', context=context_dict)

	elif obj_type == 'primer':
		if request.method == 'POST':
			primer_form = NewPrimerForm(data=request.POST)
			if primer_form.is_valid():
				with transaction.atomic():
					try:
						primer = Primer.objects.get(id=obj_id)
						primer.primer_id = primer_form.cleaned_data['primer_id']
						primer.primer_name = primer_form.cleaned_data['primer_name']
						primer.primer_tail = primer_form.cleaned_data['primer_tail']
						primer.size_range = primer_form.cleaned_data['size_range']
						primer.temp_min = primer_form.cleaned_data['temp_min']
						primer.temp_max = primer_form.cleaned_data['temp_max']
						primer.order_date = primer_form.cleaned_data['order_date']
						primer.comments = primer_form.cleaned_data['comments']
						primer.save()
						context_dict['updated'] = True
					except Exception:
						context_dict['failed'] = True
			else:
				print(primer_form.errors)
		else:
			primer_data = Primer.objects.filter(id=obj_id).values('primer_id', 'primer_name', 'primer_tail', 'size_range', 'temp_min', 'temp_max', 'order_date', 'comments')
			primer_form = NewPrimerForm(initial=primer_data[0])
		context_dict['primer_id'] = obj_id
		context_dict['primer_form'] = primer_form
		context_dict['logged_in_user'] = request.user.username
		return render(request, 'lab/edit_primer.html', context=context_dict)

def select_stockpacket_from_stock(request):
	context_dict = {}
	selected_packets = []
	checkbox_stock_list = request.POST.getlist('checkbox_stock')
	request.session['checkbox_stock'] = checkbox_stock_list
	for stock in checkbox_stock_list:
		packet = StockPacket.objects.filter(stock__id=stock)
		selected_packets = list(chain(packet, selected_packets))
	context_dict = checkbox_session_variable_check(request)
	context_dict['selected_packets'] = selected_packets
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/stock.html', context=context_dict)

@login_required
def download_stock_used_experiment(request, experiment_name):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="%s_seed_used.csv"' % (experiment_name)
	stock_for_experiment = find_relationship_for_experiment(experiment_name, 'stock', 'stock_used_in_experiment')
	writer = csv.writer(response)
	writer.writerow(['Seed ID', 'Seed Name', 'Cross Type', 'Pedigree', 'Population', 'Status', 'Inoculated', 'Collector', 'Comments'])
	for data in stock_for_experiment:
		writer.writerow([data.stock.seed_id, data.stock.seed_name, data.stock.cross_type, data.stock.pedigree, data.stock.passport.taxonomy.population, data.stock.stock_status, data.stock.inoculated, data.stock.passport.collecting.user, data.stock.comments])
	return response

@login_required
def download_stock_collected_experiment(request, experiment_name):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="%s_seed_collected.csv"' % (experiment_name)
	collected_stock_data = find_stock_collected_from_experiment(experiment_name)
	writer = csv.writer(response)
	writer.writerow(['Seed ID', 'Seed Name', 'Cross Type', 'Pedigree', 'Population', 'Status', 'Inoculated', 'Collector', 'Comments'])
	for data in collected_stock_data:
		writer.writerow([data.target_obs.stock.seed_id, data.target_obs.stock.seed_name, data.target_obs.stock.cross_type, data.target_obs.stock.pedigree, data.target_obs.stock.passport.taxonomy.population, data.target_obs.stock.stock_status, data.target_obs.stock.inoculated, data.target_obs.stock.passport.collecting.user, data.target_obs.stock.comments])
	return response

@login_required
def row_data_from_experiment(request, experiment_name):
	context_dict = {}
	context_dict = checkbox_session_variable_check(request)
	row_data = find_relationship_for_experiment(experiment_name, 'row', 'row_used_in_experiment')
	context_dict['row_data'] = row_data
	context_dict['experiment_name'] = experiment_name
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/row_experiment_data.html', context=context_dict)

@login_required
def download_row_experiment(request, experiment_name):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="%s_rows.csv"' % (experiment_name)
	row_data = find_relationship_for_experiment(experiment_name, 'row', 'row_used_in_experiment')
	writer = csv.writer(response)
	writer.writerow(['Row ID', 'Row Name', 'Field', 'Source Stock', 'Range', 'Plot', 'Block', 'Rep', 'Kernel Num', 'Planting Date', 'Harvest Date', 'Comments'])
	for row in row_data:
		writer.writerow([row.obs_row.row_id, row.obs_row.row_name, row.field.field_name, row.stock.seed_id, row.obs_row.range_num, row.obs_row.plot, row.obs_row.block, row.obs_row.rep, row.obs_row.kernel_num, row.obs_row.planting_date, row.obs_row.harvest_date, row.obs_row.comments])
	return response

@login_required
def passport(request, passport_id):
	context_dict = {}
	passport = Passport.objects.get(id=passport_id)
	stocks = Stock.objects.filter(passport=passport)
	isolates = Isolate.objects.filter(passport=passport)

	if passport.people.organization != 'No Source' and passport.people.organization != '' and passport.people.organization != 'NULL':
		collecting_source = True
	else:
		collecting_source = None
	context_dict['passport'] = passport
	context_dict['stocks'] = stocks
	context_dict['isolates'] = isolates
	context_dict['collecting_source'] = collecting_source
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/passport.html', context=context_dict)

def datatable_glycerol_inventory(request):
	glycerol_stocks = ObsTracker.objects.filter(obs_entity_type='glycerol_stock')
	count = glycerol_stocks.count()
	arr = []
	check = []
	for data in glycerol_stocks:
		if data.glycerol_stock_id in check:
			pass
		else:
			check.append(data.glycerol_stock_id)
			try:
				arr.append({
		    	'id': data.glycerol_stock_id,
		    	'glycerol_stock_id': data.glycerol_stock.glycerol_stock_id,
		    	'experiment_name': data.experiment.name,
		    	'field_id': data.field_id,
		    	'field_name': data.field.field_name,
		    	'isolate_table_id': data.isolate_id,
		    	'isolate_id': data.isolate.isolate_id,
		    	'obs_dna_id': data.obs_dna_id,
		    	'dna_id': data.obs_dna.dna_id,
		    	'location_id': data.location_id,
		    	'location_name': data.location.location_name,
		    	'stock_date': data.glycerol_stock.stock_date,
		    	'extract_color': data.glycerol_stock.extract_color,
		    	'organism': data.glycerol_stock.organism,
		    	'username': data.user.username,
		    	'comments': data.glycerol_stock.comments,
				})
			except GlycerolStock.DoesNotExist:
				pass
	return JsonResponse({'data':arr, 'recordsTotal':count}, safe=True)

@login_required
def glycerol_stock_inventory(request):
	context_dict = {}
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/glycerol_stock_inventory.html', context=context_dict)

def datatable_isolate_inventory(request):
	selected_isolates = checkbox_isolate_sort(request)
	#count = selected_isolates.count()
	arr = []
	for data in selected_isolates:
		arr.append({
			'input': '<input type="checkbox" name="checkbox_isolates" value="%s">'%(data.id),
        	'id': data.id,
        	'isolate_id': data.isolate_id,
        	'isolate_name': data.isolate_name,
        	'disease_name': data.disease_info.common_name,
        	'disease_id': data.disease_info.id,
        	'plant_organ': data.plant_organ,
        	'genus': data.passport.taxonomy.genus,
        	'alias': data.passport.taxonomy.alias,
        	'race': data.passport.taxonomy.race,
        	'subtaxa': data.passport.taxonomy.subtaxa,
        	'comments': data.comments,
    	})
	return JsonResponse({'data':arr}, safe=True)

@login_required
def isolate_inventory(request):
	context_dict = {}
	context_dict = checkbox_session_variable_check(request)
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/isolate_inventory.html', context=context_dict)

def checkbox_isolate_sort(request):
	selected_isolates = {}
	checkbox_taxonomy_list = []
	checkbox_disease_list = []
	if request.session.get('checkbox_isolate_taxonomy', None):
		checkbox_taxonomy_list = request.session.get('checkbox_isolate_taxonomy')
		if request.session.get('checkbox_isolate_disease', None):
			checkbox_disease_list = request.session.get('checkbox_isolate_disease')
			for disease_id in checkbox_disease_list:
				for taxonomy_id in checkbox_taxonomy_list:
					isolates = Isolate.objects.filter(disease_info__id=disease_id, passport__taxonomy__id=taxonomy_id)
					selected_isolates = list(chain(selected_isolates, isolates))
		else:
			for taxonomy_id in checkbox_taxonomy_list:
				isolates = Isolate.objects.filter(passport__taxonomy__id=taxonomy_id)
				selected_isolates = list(chain(selected_isolates, isolates))
	else:
		if request.session.get('checkbox_isolate_disease', None):
			checkbox_disease_list = request.session.get('checkbox_isolate_disease')
			for disease_id in checkbox_disease_list:
				isolates = Isolate.objects.filter(disease_info__id=disease_id)
				selected_isolates = list(chain(selected_isolates, isolates))
		else:
			selected_isolates = list(Isolate.objects.all().exclude(id=1))[:2000]
	return selected_isolates

def show_all_isolate_taxonomy(request):
	isolate_taxonomy_list = []
	if request.session.get('checkbox_isolate_disease', None):
		checkbox_isolate_disease = request.session.get('checkbox_isolate_disease')
		for disease_id in checkbox_isolate_disease:
			taxonomy = Isolate.objects.filter(disease_info__id=disease_id).values('passport__taxonomy__id', 'disease_info__common_name', 'passport__taxonomy__genus', 'passport__taxonomy__alias', 'passport__taxonomy__race', 'passport__taxonomy__subtaxa', 'passport__taxonomy__species').distinct()
			isolate_taxonomy_list = list(chain(taxonomy, isolate_taxonomy_list))
		for p in isolate_taxonomy_list:
			p['input'] = '<input type="checkbox" name="checkbox_isolate_taxonomy_id" value="%s">' % (p['passport__taxonomy__id'])
	else:
		isolate_taxonomy_list = list(Taxonomy.objects.filter(common_name='Isolate').values('id', 'genus', 'alias', 'race', 'subtaxa', 'species').distinct())
		for t in isolate_taxonomy_list:
			t['input'] = '<input type="checkbox" name="checkbox_isolate_taxonomy_id" value="%s">' % (t['id'])
			t['disease_info__common_name'] = ''
			t['passport__taxonomy__genus'] = t['genus']
			t['passport__taxonomy__alias'] = t['alias']
			t['passport__taxonomy__race'] = t['race']
			t['passport__taxonomy__subtaxa'] = t['subtaxa']
			t['passport__taxonomy__species'] = t['species']
	return JsonResponse({'data':isolate_taxonomy_list})

def show_all_isolate_disease(request):
	isolate_disease_list = []
	if request.session.get('checkbox_isolate_taxonomy', None):
		checkbox_isolate_taxonomy = request.session.get('checkbox_isolate_taxonomy')
		for taxonomy_id in checkbox_isolate_taxonomy:
			disease = Isolate.objects.filter(passport__taxonomy__id=taxonomy_id).values('disease_info__id', 'disease_info__common_name', 'passport__taxonomy__genus').distinct()
			isolate_disease_list = list(chain(disease, isolate_disease_list))
		for p in isolate_disease_list:
			p['input'] = '<input type="checkbox" name="checkbox_isolate_disease_id" value="%s">' % (p['disease_info__id'])
	else:
		isolate_disease_list = list(DiseaseInfo.objects.filter().values('id', 'common_name').distinct())
		for t in isolate_disease_list:
			t['input'] = '<input type="checkbox" name="checkbox_isolate_disease_id" value="%s">' % (t['id'])
			t['disease_info__common_name'] = t['common_name']
			t['passport__taxonomy__genus'] = ''
	return JsonResponse({'data':isolate_disease_list})

def suggest_isolate_taxonomy(request):
	isolate_taxonomy_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET['suggestion']
	else:
		starts_with = request.POST['suggestion']
	if starts_with:
		if request.session.get('checkbox_isolate_disease', None):
			checkbox_isolate_disease = request.session.get('checkbox_isolate_disease')
			for disease_id in checkbox_isolate_disease:
				taxonomy = Isolate.objects.filter(disease_info__id=disease_id, passport__taxonomy__genus__contains=starts_with).values('passport__taxonomy__id', 'disease_info__common_name', 'passport__taxonomy__genus', 'passport__taxonomy__alias', 'passport__taxonomy__race', 'passport__taxonomy__subtaxa', 'passport__taxonomy__species').distinct()
				isolate_taxonomy_list = list(chain(taxonomy, isolate_taxonomy_list))
			for t in isolate_taxonomy_list:
				t['input'] = '<input type="checkbox" name="checkbox_isolate_taxonomy_id" value="%s">' % (t['passport__taxonomy__id'])
		else:
			isolate_taxonomy_list = list(Taxonomy.objects.filter(genus__contains=starts_with, common_name='Isolate').values('id', 'genus', 'alias', 'race', 'subtaxa', 'species').distinct())
			for t in isolate_taxonomy_list:
				t['input'] = '<input type="checkbox" name="checkbox_isolate_taxonomy_id" value="%s">' % (t['id'])
				t['disease_info__common_name'] = ''
				t['passport__taxonomy__genus'] = t['genus']
				t['passport__taxonomy__alias'] = t['alias']
				t['passport__taxonomy__race'] = t['race']
				t['passport__taxonomy__subtaxa'] = t['subtaxa']
				t['passport__taxonomy__species'] = t['species']
	return JsonResponse({'data':isolate_taxonomy_list})

def suggest_isolate_disease(request):
	isolate_disease_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET['suggestion']
	else:
		starts_with = request.POST['suggestion']
	if starts_with:
		if request.session.get('checkbox_isolate_taxonomy', None):
			checkbox_isolate_taxonomy = request.session.get('checkbox_isolate_taxonomy')
			for taxonomy_id in checkbox_isolate_taxonomy:
				disease = Isolate.objects.filter(disease_info__common_name__contains=starts_with, passport__taxonomy__id=taxonomy_id).values('disease_info__id', 'disease_info__common_name', 'passport__taxonomy__genus').distinct()
				isolate_disease_list = list(chain(disease, isolate_disease_list))
			for t in isolate_disease_list:
				t['input'] = '<input type="checkbox" name="checkbox_isolate_disease_id" value="%s">' % (t['disease_info__id'])
		else:
			isolate_disease_list = list(DiseaseInfo.objects.filter(common_name__contains=starts_with).values('id', 'common_name').distinct())
			for t in isolate_disease_list:
				t['input'] = '<input type="checkbox" name="checkbox_isolate_disease_id" value="%s">' % (t['id'])
				t['disease_info__common_name'] = t['common_name']
				t['passport__taxonomy__genus'] = ''
	return JsonResponse({'data':isolate_disease_list})

def select_isolate_taxonomy(request):
	taxonomies = request.POST['taxonomies']
	checkbox_isolate_taxonomy_ids = json.loads(taxonomies)
	checkbox_isolate_taxonomy_names = []
	for taxonomy_id in checkbox_isolate_taxonomy_ids:
		taxonomy_name = Taxonomy.objects.filter(id=taxonomy_id).values('genus')
		checkbox_isolate_taxonomy_names = list(chain(taxonomy_name, checkbox_isolate_taxonomy_names))
	request.session['checkbox_isolate_taxonomy'] = checkbox_isolate_taxonomy_ids
	request.session['checkbox_isolate_taxonomy_names'] = checkbox_isolate_taxonomy_names
	return JsonResponse({'success':True})

def select_isolate_disease(request):
	diseases = request.POST['diseases']
	disease_list = json.loads(diseases)
	checkbox_isolate_disease_names = []
	for disease_id in disease_list:
		disease_name = DiseaseInfo.objects.filter(id=disease_id).values('common_name')
		checkbox_isolate_disease_names = list(chain(disease_name, checkbox_isolate_disease_names))
	request.session['checkbox_isolate_disease'] = disease_list
	request.session['checkbox_isolate_disease_names'] = checkbox_isolate_disease_names
	return JsonResponse({'success':True})

def select_isolates(request):
	context_dict = {}
	selected_isolates = []
	checkbox_isolates_list = request.POST.getlist('checkbox_isolates')
	request.session['checkbox_isolates'] = checkbox_isolates_list
	for isolate in checkbox_isolates_list:
		isolate = Isolate.objects.filter(id=isolate)
		selected_isolates = list(chain(isolate, selected_isolates))
	context_dict = checkbox_session_variable_check(request)
	context_dict['selected_isolates'] = selected_isolates
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/isolate.html', context=context_dict)

@login_required
def single_disease_info(request, disease_id):
	context_dict = {}
	try:
		disease_info = DiseaseInfo.objects.get(id=disease_id)
	except DiseaseInfo.DoesNotExist:
		disease_info = None
	context_dict['disease_info'] = disease_info
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/disease_info.html', context=context_dict)

@login_required
def single_field_info(request, field_id):
	context_dict = {}
	try:
		field_info = Field.objects.get(id=field_id)
	except DiseaseInfo.DoesNotExist:
		field_info = None
	context_dict['field_info'] = field_info
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/field.html', context=context_dict)

@login_required
def single_parameter_info(request, parameter_id):
	context_dict = {}
	try:
		parameter_info = MeasurementParameter.objects.get(id=parameter_id)
	except MeasurementParameter.DoesNotExist:
		parameter_info = None
	context_dict['parameter_info'] = parameter_info
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/measurement_parameter.html', context=context_dict)

@login_required
def single_medium_info(request, medium_id):
	context_dict = {}
	try:
		medium_info = Medium.objects.get(id=medium_id)
	except Medium.DoesNotExist:
		medium_info = None
	context_dict['medium_info'] = medium_info
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/medium.html', context=context_dict)

@login_required
def single_location_info(request, location_id):
	context_dict = {}
	try:
		location_info = Location.objects.get(id=location_id)
	except Location.DoesNotExist:
		location_info = None
	context_dict['location_info'] = location_info
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/location.html', context=context_dict)

@login_required
def single_locality_info(request, locality_id):
	context_dict = {}
	try:
		locality_info = Locality.objects.get(id=locality_id)
	except Locality.DoesNotExist:
		locality_info = None
	context_dict['locality_info'] = locality_info
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/locality.html', context=context_dict)

@login_required
def single_taxonomy_info(request, taxonomy_id):
	context_dict = {}
	try:
		taxonomy_info = Taxonomy.objects.get(id=taxonomy_id)
	except Taxonomy.DoesNotExist:
		taxonomy_info = None
	context_dict['taxonomy_info'] = taxonomy_info
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/taxonomy.html', context=context_dict)

@login_required
def single_primer_info(request, id):
	context_dict = {}
	try:
		primer_info = Primer.objects.get(id=id)
	except Primer.DoesNotExist:
		primer_info = None
	context_dict['primer_info'] = primer_info
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/primer.html', context=context_dict)

@login_required
def browse_medium_data(request):
	context_dict = {}
	medium_data = Medium.objects.all()
	context_dict['medium_data'] = medium_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/medium_data.html', context=context_dict)

@login_required
def browse_parameter_data(request):
	context_dict = {}
	parameter_data = MeasurementParameter.objects.all()
	context_dict['parameter_data'] = parameter_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/parameter_data.html', context=context_dict)

@login_required
def browse_location_data(request):
	context_dict = {}
	location_data = Location.objects.all().exclude(location_name='')
	context_dict['location_data'] = location_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/location_data.html', context=context_dict)

@login_required
def browse_locality_data(request):
	context_dict = {}
	locality_data = Locality.objects.all()
	context_dict['locality_data'] = locality_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/locality_data.html', context=context_dict)

@login_required
def browse_field_data(request):
	context_dict = {}
	field_data = Field.objects.all()
	field_map_file = FileDump.objects.filter(file_name="Musgrave Research Farm Field Map")
	context_dict['field_data'] = field_data
	context_dict['field_map_file'] = field_map_file
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/field_data.html', context=context_dict)

@login_required
def browse_disease_info_data(request):
	context_dict = {}
	disease_data = DiseaseInfo.objects.all()
	context_dict['disease_data'] = disease_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/disease_data.html', context=context_dict)

@login_required
def browse_taxonomy_data(request):
	context_dict = {}
	taxonomy_data = Taxonomy.objects.filter().exclude(genus='').exclude(genus=0)
	context_dict['taxonomy_data'] = taxonomy_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/taxonomy_data.html', context=context_dict)

@login_required
def browse_primer_data(request):
	context_dict = {}
	primer_data = Primer.objects.filter().exclude(primer_id='No Primer')
	context_dict['primer_data'] = primer_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/primer_data.html', context=context_dict)

@login_required
def browse_publication_data(request):
	context_dict = {}
	publication_data = Publication.objects.filter()
	context_dict['publication_data'] = publication_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/publication_data.html', context=context_dict)

@login_required
def browse_downloads(request):
	context_dict = {}
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/downloads.html', context=context_dict)

@login_required
def new_experiment(request):
	context_dict = {}
	if request.method == 'POST':
		new_experiment_form = NewExperimentForm(data=request.POST)
		if new_experiment_form.is_valid():
			new_experiment_name = new_experiment_form.cleaned_data['name']
			try:
				name_check = Experiment.objects.get(name=new_experiment_name)
				name_check_fail = True
				experiment_added = False
			except (Experiment.DoesNotExist, IndexError):
				name_check_fail = False
				new_experiment_user = new_experiment_form.cleaned_data['user']
				new_experiment_field = new_experiment_form.cleaned_data['field']
				new_experiment_start_date = new_experiment_form.cleaned_data['start_date']
				new_experiment_purpose = new_experiment_form.cleaned_data['purpose']
				new_experiment_comments = new_experiment_form.cleaned_data['comments']
				experiment = Experiment.objects.create(user=new_experiment_user, field=new_experiment_field, name=new_experiment_name,  start_date=new_experiment_start_date, purpose=new_experiment_purpose, comments=new_experiment_comments)
				experiment_added = True
		else:
			print(new_experiment_form.errors)
			name_check_fail = False
			experiment_added = False
	else:
		new_experiment_form = NewExperimentForm()
		name_check_fail = False
		experiment_added = False
	context_dict['new_experiment_form'] = new_experiment_form
	context_dict['name_check_fail'] = name_check_fail
	context_dict['experiment_added'] = experiment_added
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/new_experiment.html', context=context_dict)

@login_required
def log_data_select_obs(request):
	context_dict = {}
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/log_data.html', context_dict)

@login_required
def serve_data_template_file(request, filename):
	path = '%s/%s.csv' % (settings.MEDIA_ROOT,filename)
	with open(path, "rb") as excel:
		data = excel.read()
		response = HttpResponse(data,content_type='application/vnd.ms-excel')
		response['Content-Disposition'] = 'attachment; filename=%s.csv' % (filename)
		return response

@login_required
def maize_data_browse(request):
	context_dict = {}
	maize_data = sort_maize_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['maize_data'] = maize_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/maize_data.html', context=context_dict)

def sort_maize_data(request):
	maize_data = {}
	if request.session.get('checkbox_maize_experiment_id_list', None):
		checkbox_maize_experiment_id_list = request.session.get('checkbox_maize_experiment_id_list')
		for maize_experiment in checkbox_maize_experiment_id_list:
			rows = ObsTracker.objects.filter(obs_entity_type='maize', experiment__id=maize_experiment)
			maize_data = list(chain(rows, maize_data))
	else:
		maize_data = ObsTracker.objects.filter(obs_entity_type='maize')[:2000]
	return maize_data

def suggest_maize_experiment(request):
	context_dict = {}
	tissue_experiment_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET['suggestion']
	else:
		starts_with = request.POST['suggestion']
	if starts_with:
		maize_experiment_list = ObsTracker.objects.filter(obs_entity_type='maize', experiment__name__contains=starts_with).values('experiment__name', 'experiment__field__field_name', 'experiment__field__id', 'experiment__id').distinct()[:2000]
	else:
		maize_experiment_list = None
	context_dict = checkbox_session_variable_check(request)
	context_dict['maize_experiment_list'] = maize_experiment_list
	return render(request, 'lab/maize_experiment_list.html', context=context_dict)

def select_maize_experiment(request):
	context_dict = {}
	plant_data = []
	checkbox_maize_experiment_name_list = []
	checkbox_maize_experiment_list = request.POST.getlist('checkbox_maize_experiment')
	for experiment_id in checkbox_maize_experiment_list:
		experiment_name = Experiment.objects.filter(id=experiment_id).values('name')
		checkbox_maize_experiment_name_list = list(chain(experiment_name, checkbox_maize_experiment_name_list))
	request.session['checkbox_maize_experiment'] = checkbox_maize_experiment_name_list
	request.session['checkbox_maize_experiment_id_list'] = checkbox_maize_experiment_list
	maize_data = sort_maize_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['maize_data'] = maize_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/maize_data.html', context=context_dict)

def checkbox_maize_data_clear(request):
	context_dict = {}
	del request.session['checkbox_maize_experiment']
	del request.session['checkbox_maize_experiment_id_list']
	maize_data = sort_maize_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['maize_data'] = maize_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/maize_data.html', context=context_dict)

def show_all_maize_experiment(request):
	context_dict = {}
	maize_experiment_list = ObsTracker.objects.filter(obs_entity_type='maize').values('experiment__name', 'experiment__field__field_name', 'experiment__field__id', 'experiment__id').distinct()[:2000]
	context_dict = checkbox_session_variable_check(request)
	context_dict['maize_experiment_list'] = maize_experiment_list
	return render(request, 'lab/maize_experiment_list.html', context=context_dict)


@login_required
def maize_data_from_experiment(request, experiment_name):
	context_dict = {}
	maize_data = find_relationship_for_experiment(experiment_name, 'maize', 'maize_used_in_experiment')
	context_dict['maize_data'] = maize_data
	context_dict['experiment_name'] = experiment_name
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/maize_experiment_data.html', context=context_dict)

@login_required
def download_maize_experiment(request, experiment_name):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="%s_maize_survey.csv"' % (experiment_name)
	maize_data = find_relationship_for_experiment(experiment_name, 'maize', 'maize_used_in_experiment')
	writer = csv.writer(response)
	writer.writerow(['Maize ID', 'County', 'Sub Location', 'Village', 'Weight', 'Harvest Date', 'Storage Months', 'Storage Conditions', 'Maize Variety', 'Seed Source', 'Moisture Content', 'Source Type', 'Appearance', 'GPS Latitude', 'GPS Longitude', 'GPS Altitude', 'GPS Accuracy', 'Photo Filename'])
	for row in maize_data:
		writer.writerow([row.maize_sample.maize_id, row.maize_sample.county, row.maize_sample.sub_location, row.maize_sample.village, row.maize_sample.weight, row.maize_sample.harvest_date, row.maize_sample.storage_months, row.maize_sample.storage_conditions, row.maize_sample.maize_variety, row.maize_sample.seed_source, row.maize_sample.moisture_content, row.maize_sample.source_type, row.maize_sample.appearance, row.maize_sample.gps_latitude, row.maize_sample.gps_longitude, row.maize_sample.gps_altitude, row.maize_sample.gps_accuracy, row.maize_sample.photo])
	return response

@login_required
def download_maize_data(request):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="selected_experiment_maize_survey.csv"'
	maize_data = sort_maize_data(request)
	writer = csv.writer(response)
	writer.writerow(['Exp Name', 'Maize ID', 'County', 'Sub Location', 'Village', 'Weight', 'Harvest Date', 'Storage Months', 'Storage Conditions', 'Maize Variety', 'Seed Source', 'Moisture Content', 'Source Type', 'Appearance', 'GPS Latitude', 'GPS Longitude', 'GPS Altitude', 'GPS Accuracy', 'Photo Filename'])
	for row in maize_data:
		writer.writerow([row.experiment.name, row.maize_sample.maize_id, row.maize_sample.county, row.maize_sample.sub_location, row.maize_sample.village, row.maize_sample.weight, row.maize_sample.harvest_date, row.maize_sample.storage_months, row.maize_sample.storage_conditions, row.maize_sample.maize_variety, row.maize_sample.seed_source, row.maize_sample.moisture_content, row.maize_sample.source_type, row.maize_sample.appearance, row.maize_sample.gps_latitude, row.maize_sample.gps_longitude, row.maize_sample.gps_altitude, row.maize_sample.gps_accuracy, row.maize_sample.photo])
	return response

def find_glycerol_stock_from_experiment(experiment_name):
	try:
		glycerol_stock_data = ObsTracker.objects.filter(obs_entity_type='glycerol_stock', experiment__name=experiment_name)
	except ObsTracker.DoesNotExist:
		glycerol_stock_data = None
	return glycerol_stock_data

@login_required
def glycerol_stock_data_from_experiment(request, experiment_name):
	context_dict = {}
	glycerol_stock_data = find_glycerol_stock_from_experiment(experiment_name)
	context_dict['glycerol_stock_data'] = glycerol_stock_data
	context_dict['experiment_name'] = experiment_name
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/glycerol_stock_experiment_data.html', context=context_dict)

@login_required
def download_glycerol_stocks_experiment(request, experiment_name):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="%s_glycerol_stocks.csv"' % (experiment_name)
	glycerol_stock_data = find_glycerol_stock_from_experiment(experiment_name)
	writer = csv.writer(response)
	writer.writerow(['Glycerol Stock ID', 'Stock Date', 'Extract Color', 'Organism', 'Location Name', 'Source Seed ID', 'Source Row ID', 'Source Culture ID', 'Source Isolate ID', 'Comments'])
	for row in glycerol_stock_data:
		writer.writerow([row.glycerol_stock.glycerol_stock_id, row.glycerol_stock.stock_date, row.glycerol_stock.extract_color, row.glycerol_stock.organism, row.location, row.stock.seed_id, row.obs_row.row_id, row.obs_culture.culture_id, row.isolate.isolate_id, row.glycerol_stock.comments])
	return response

@login_required
def microbe_data_browse(request):
	context_dict = {}
	microbe_data = sort_microbe_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['microbe_data'] = microbe_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/microbe_data.html', context=context_dict)

def sort_microbe_data(request):
	microbe_data = {}
	if request.session.get('checkbox_microbe_experiment_id_list', None):
		checkbox_microbe_experiment_id_list = request.session.get('checkbox_microbe_experiment_id_list')
		for m in checkbox_microbe_experiment_id_list:
			microbes = ObsTracker.objects.filter(obs_entity_type='microbe', experiment__id=m)
			microbe_data = list(chain(microbes, microbe_data))
	else:
		microbe_data = ObsTracker.objects.filter(obs_entity_type='microbe')[:2000]
	return microbe_data

@login_required
def download_microbe_data(request):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="selected_experiment_microbes.csv"'
	microbe_data = sort_microbe_data(request)
	writer = csv.writer(response)
	writer.writerow(['Exp ID', 'Microbe ID', 'Microbe Type', 'Comments', 'Source Row ID', 'Source Seed ID', 'Source Plant ID', 'Source Tissue ID', 'Source Culture ID'])
	for row in microbe_data:
		writer.writerow([row.experiment.name, row.obs_microbe.microbe_id, row.obs_microbe.microbe_type, row.obs_microbe.comments, row.obs_row.row_id, row.stock.seed_id, row.obs_plant.plant_id, row.obs_tissue.tissue_id, row.obs_culture.culture_id])
	return response

def suggest_microbe_experiment(request):
	context_dict = {}
	microbe_experiment_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET['suggestion']
	else:
		starts_with = request.POST['suggestion']
	if starts_with:
		microbe_experiment_list = ObsTracker.objects.filter(obs_entity_type='microbe', experiment__name__contains=starts_with).values('experiment__name', 'experiment__field__field_name', 'experiment__field__id', 'experiment__id').distinct()[:2000]
	else:
		microbe_experiment_list = None
	context_dict = checkbox_session_variable_check(request)
	context_dict['microbe_experiment_list'] = microbe_experiment_list
	return render(request, 'lab/microbe_experiment_list.html', context=context_dict)

def select_microbe_experiment(request):
	context_dict = {}
	microbe_data = []
	checkbox_microbe_experiment_name_list = []
	checkbox_microbe_experiment_list = request.POST.getlist('checkbox_microbe_experiment')
	for microbe_experiment in checkbox_microbe_experiment_list:
		microbes = ObsTracker.objects.filter(obs_entity_type='microbe', experiment__id=microbe_experiment)
		microbe_data = list(chain(microbes, microbe_data))
	for experiment_id in checkbox_microbe_experiment_list:
		experiment_name = Experiment.objects.filter(id=experiment_id).values('name')
		checkbox_microbe_experiment_name_list = list(chain(experiment_name, checkbox_microbe_experiment_name_list))
	request.session['checkbox_microbe_experiment'] = checkbox_microbe_experiment_name_list
	request.session['checkbox_microbe_experiment_id_list'] = checkbox_microbe_experiment_list
	context_dict = checkbox_session_variable_check(request)
	context_dict['microbe_data'] = microbe_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/microbe_data.html', context=context_dict)

def checkbox_microbe_data_clear(request):
	context_dict = {}
	del request.session['checkbox_microbe_experiment']
	del request.session['checkbox_microbe_experiment_id_list']
	microbe_data = sort_microbe_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['microbe_data'] = microbe_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/microbe_data.html', context=context_dict)

def show_all_microbe_experiment(request):
	context_dict = {}
	microbe_experiment_list = ObsTracker.objects.filter(obs_entity_type='microbe').values('experiment__name', 'experiment__field__field_name', 'experiment__field__id', 'experiment__id').distinct()[:2000]
	context_dict = checkbox_session_variable_check(request)
	context_dict['microbe_experiment_list'] = microbe_experiment_list
	return render(request, 'lab/microbe_experiment_list.html', context=context_dict)

@login_required
def microbe_data_from_experiment(request, experiment_name):
	context_dict = {}
	microbe_data = find_relationship_for_experiment(experiment_name, 'microbe', 'microbe_used_in_experiment')
	context_dict['microbe_data'] = microbe_data
	context_dict['experiment_name'] = experiment_name
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/microbe_experiment_data.html', context=context_dict)

@login_required
def download_microbe_experiment(request, experiment_name):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="%s_microbes.csv"' % (experiment_name)
	microbe_data = find_relationship_for_experiment(experiment_name, 'microbe', 'microbe_used_in_experiment')
	writer = csv.writer(response)
	writer.writerow(['Microbe ID', 'Microbe Type', 'Comments', 'Source Row ID', 'Source Seed ID', 'Source Plant ID', 'Source Tissue ID', 'Source Culture ID'])
	for row in microbe_data:
		writer.writerow([row.obs_microbe.microbe_id, row.obs_microbe.microbe_type, row.obs_microbe.comments, row.obs_row.row_id, row.stock.seed_id, row.obs_plant.plant_id, row.obs_tissue.tissue_id, row.obs_culture.culture_id])
	return response

@login_required
def env_data_browse(request):
	context_dict = {}
	env_data = sort_env_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['env_data'] = env_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/env_data.html', context=context_dict)

def sort_env_data(request):
	env_data = {}
	if request.session.get('checkbox_env_experiment_id_list', None):
		checkbox_env_experiment_id_list = request.session.get('checkbox_env_experiment_id_list')
		for e in checkbox_env_experiment_id_list:
			envs = ObsTracker.objects.filter(obs_entity_type='environment', experiment__id=e)
			env_data = list(chain(envs, env_data))
	else:
		env_data = ObsTracker.objects.filter(obs_entity_type='environment')[:2000]
	return env_data

@login_required
def download_env_data(request):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="selected_experiment_environments.csv"'
	env_data = sort_env_data(request)
	writer = csv.writer(response)
	writer.writerow(['Exp ID', 'Environment ID', 'Field Name', 'Longitude', 'Latitude', 'Comments'])
	for row in env_data:
		writer.writerow([row.experiment.name, row.obs_env.environment_id, row.field.field_name, row.obs_env.longitude, row.obs_env.latitude, row.obs_env.comments])
	return response

def suggest_env_experiment(request):
	context_dict = {}
	env_experiment_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET['suggestion']
	else:
		starts_with = request.POST['suggestion']
	if starts_with:
		env_experiment_list = ObsTracker.objects.filter(obs_entity_type='environment', experiment__name__contains=starts_with).values('experiment__name', 'experiment__field__field_name', 'experiment__field__id', 'experiment__id').distinct()[:2000]
	else:
		env_experiment_list = None
	context_dict = checkbox_session_variable_check(request)
	context_dict['env_experiment_list'] = env_experiment_list
	return render(request, 'lab/env_experiment_list.html', context=context_dict)

def select_env_experiment(request):
	context_dict = {}
	env_data = []
	checkbox_env_experiment_name_list = []
	checkbox_env_experiment_list = request.POST.getlist('checkbox_env_experiment')
	for env_experiment in checkbox_env_experiment_list:
		env = ObsTracker.objects.filter(obs_entity_type='environment', experiment__id=env_experiment)
		env_data = list(chain(env, env_data))
	for experiment_id in checkbox_env_experiment_list:
		experiment_name = Experiment.objects.filter(id=experiment_id).values('name')
		checkbox_env_experiment_name_list = list(chain(experiment_name, checkbox_env_experiment_name_list))
	request.session['checkbox_env_experiment'] = checkbox_env_experiment_name_list
	request.session['checkbox_env_experiment_id_list'] = checkbox_env_experiment_list
	context_dict = checkbox_session_variable_check(request)
	context_dict['env_data'] = env_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/env_data.html', context=context_dict)

def checkbox_env_data_clear(request):
	context_dict = {}
	del request.session['checkbox_env_experiment']
	del request.session['checkbox_env_experiment_id_list']
	env_data = sort_env_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['env_data'] = env_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/env_data.html', context=context_dict)

def show_all_env_experiment(request):
	context_dict = {}
	env_experiment_list = ObsTracker.objects.filter(obs_entity_type='environment').values('experiment__name', 'experiment__field__field_name', 'experiment__field__id', 'experiment__id').distinct()[:2000]
	context_dict = checkbox_session_variable_check(request)
	context_dict['env_experiment_list'] = env_experiment_list
	return render(request, 'lab/env_experiment_list.html', context=context_dict)

@login_required
def env_data_from_experiment(request, experiment_name):
	context_dict = {}
	env_data = find_relationship_for_experiment(experiment_name, 'environment', 'env_used_in_experiment')
	context_dict['env_data'] = env_data
	context_dict['experiment_name'] = experiment_name
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/env_experiment_data.html', context=context_dict)

@login_required
def download_env_experiment(request, experiment_name):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="%s_environments.csv"' % (experiment_name)
	env_data = find_relationship_for_experiment(experiment_name, 'environment', 'env_used_in_experiment')
	writer = csv.writer(response)
	writer.writerow(['Environment ID', 'Field Name', 'Longitude', 'Latitude', 'Comments'])
	for row in env_data:
		writer.writerow([row.obs_env.environment_id, row.field.field_name, row.obs_env.longitude, row.obs_env.latitude, row.obs_env.comments])
	return response

@login_required
def mapfeature_data_browse(request):
	context_dict = {}
	mapfeature_data = sort_mapfeature_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['mapfeature_data'] = mapfeature_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/mapfeature_data.html', context=context_dict)

def sort_mapfeature_data(request):
	data = {}
	data = MapFeatureInterval.objects.all().exclude(id=1)
	return data

@login_required
def row_data_browse(request):
	context_dict = {}
	row_data = sort_row_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['row_data'] = row_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/row_data.html', context=context_dict)

def sort_row_data(request):
	row_data = {}
	if request.session.get('checkbox_row_experiment_id_list', None):
		checkbox_row_experiment_id_list = request.session.get('checkbox_row_experiment_id_list')
		for row_experiment in checkbox_row_experiment_id_list:
			rows = ObsTracker.objects.filter(obs_entity_type='row', experiment__id=row_experiment)
			row_data = list(chain(rows, row_data))
	else:
		row_data = ObsTracker.objects.filter(obs_entity_type='row').exclude(stock__seed_id=0).exclude(stock__seed_id='YW').exclude(stock__seed_id='135sib').exclude(stock__seed_id='R. Wisser').exclude(stock__seed_id='R_Wisser')[:2000]
	return row_data

@login_required
def download_row_data(request):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="selected_experiment_rows.csv"'
	row_data = sort_row_data(request)
	writer = csv.writer(response)
	writer.writerow(['Exp ID', 'Row ID', 'Row Name', 'Field', 'Source Stock', 'Range', 'Plot', 'Block', 'Rep', 'Kernel Num', 'Planting Date', 'Harvest Date', 'Comments'])
	for row in row_data:
		writer.writerow([row.experiment.name, row.obs_row.row_id, row.obs_row.row_name, row.field.field_name, row.stock.seed_id, row.obs_row.range_num, row.obs_row.plot, row.obs_row.block, row.obs_row.rep, row.obs_row.kernel_num, row.obs_row.planting_date, row.obs_row.harvest_date, row.obs_row.comments])
	return response

def suggest_row_experiment(request):
	context_dict = {}
	row_experiment_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET['suggestion']
	else:
		starts_with = request.POST['suggestion']
	if starts_with:
		row_experiment_list = ObsTracker.objects.filter(obs_entity_type='row', experiment__name__contains=starts_with).values('experiment__name', 'experiment__field__field_name', 'experiment__field__id', 'experiment__id').distinct()[:2000]
	else:
		row_experiment_list = None
	context_dict = checkbox_session_variable_check(request)
	context_dict['row_experiment_list'] = row_experiment_list
	return render(request, 'lab/row_experiment_list.html', context=context_dict)

def select_row_experiment(request):
	context_dict = {}
	row_data = []
	checkbox_row_experiment_name_list = []
	checkbox_row_experiment_list = request.POST.getlist('checkbox_row_experiment')
	for row_experiment in checkbox_row_experiment_list:
		rows = ObsTracker.objects.filter(obs_entity_type='row', experiment__id=row_experiment)
		row_data = list(chain(rows, row_data))
	for experiment_id in checkbox_row_experiment_list:
		experiment_name = Experiment.objects.filter(id=experiment_id).values('name')
		checkbox_row_experiment_name_list = list(chain(experiment_name, checkbox_row_experiment_name_list))
	request.session['checkbox_row_experiment'] = checkbox_row_experiment_name_list
	request.session['checkbox_row_experiment_id_list'] = checkbox_row_experiment_list
	context_dict = checkbox_session_variable_check(request)
	context_dict['row_data'] = row_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/row_data.html', context=context_dict)

def checkbox_row_data_clear(request):
	context_dict = {}
	del request.session['checkbox_row_experiment']
	del request.session['checkbox_row_experiment_id_list']
	row_data = sort_row_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['row_data'] = row_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/row_data.html', context=context_dict)

def show_all_row_experiment(request):
	context_dict = {}
	row_experiment_list = ObsTracker.objects.filter(obs_entity_type='row').values('experiment__name', 'experiment__field__field_name', 'experiment__field__id', 'experiment__id').distinct()[:2000]
	context_dict = checkbox_session_variable_check(request)
	context_dict['row_experiment_list'] = row_experiment_list
	return render(request, 'lab/row_experiment_list.html', context=context_dict)

@login_required
def marker_data_browse(request):
	context_dict = {}
	marker_data = Marker.objects.all().exclude(id=1)
	context_dict['marker_data'] = marker_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/marker_data.html', context=context_dict)

@login_required
def sequence_data_browse(request):
	context_dict = {}
	seq_data = GenotypeResults.objects.all()
	context_dict['seq_data'] = seq_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/genotype_result_data.html', context=context_dict)

@login_required
def sequence_alignment_browse(request):
	context_dict = {}
	seq_data = GenotypeResults.objects.all()
	context_dict['seq_data'] = seq_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/genotype_result_data.html', context=context_dict)

@login_required
def sample_data_browse(request):
	context_dict = {}
	sample_data = sort_sample_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['sample_data'] = sample_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/sample_data.html', context=context_dict)

def sort_sample_data(request):
	sample_data = {}
	if request.session.get('checkbox_sample_experiment_id_list', None):
		checkbox_sample_experiment_id_list = request.session.get('checkbox_sample_experiment_id_list')
		for sample_experiment in checkbox_sample_experiment_id_list:
			samples = ObsTracker.objects.filter(obs_entity_type='sample', experiment__id=sample_experiment)
			sample_data = list(chain(samples, sample_data))
	else:
		sample_data = ObsTracker.objects.filter(obs_entity_type='sample')[:2000]
	return sample_data

@login_required
def download_sample_data(request):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="selected_experiment_samples.csv"'
	sample_data = sort_sample_data(request)
	writer = csv.writer(response)
	writer.writerow(['Exp ID', 'Sample ID', 'Sample Type', 'Sample Name', 'Source Seed ID', 'Source Row ID', 'Source Plant ID', 'Weight', 'Volume', 'Density', 'Num Kernels', 'Photo', 'Comments'])
	for row in sample_data:
		writer.writerow([row.experiment, row.obs_sample.sample_id, row.obs_sample.sample_type, row.obs_sample.sample_name, row.stock.seed_id, row.obs_row.row_id, row.obs_plant.plant_id, row.obs_sample.weight, row.obs_sample.volume, row.obs_sample.density, row.obs_sample.kernel_num, row.obs_sample.photo, row.obs_sample.comments])
	return response

def suggest_sample_experiment(request):
	context_dict = {}
	sample_experiment_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET['suggestion']
	else:
		starts_with = request.POST['suggestion']
	if starts_with:
		sample_experiment_list = ObsTracker.objects.filter(obs_entity_type='sample', experiment__name__contains=starts_with).values('experiment__name', 'experiment__field__field_name', 'experiment__field__id', 'experiment__id').distinct()[:2000]
	else:
		sample_experiment_list = None
	context_dict = checkbox_session_variable_check(request)
	context_dict['sample_experiment_list'] = sample_experiment_list
	return render(request, 'lab/sample_experiment_list.html', context=context_dict)

def select_sample_experiment(request):
	context_dict = {}
	sample_data = []
	checkbox_sample_experiment_name_list = []
	checkbox_sample_experiment_list = request.POST.getlist('checkbox_sample_experiment')
	for experiment_id in checkbox_sample_experiment_list:
		experiment_name = Experiment.objects.filter(id=experiment_id).values('name')
		checkbox_sample_experiment_name_list = list(chain(experiment_name, checkbox_sample_experiment_name_list))
	request.session['checkbox_sample_experiment'] = checkbox_sample_experiment_name_list
	request.session['checkbox_sample_experiment_id_list'] = checkbox_sample_experiment_list
	sample_data = sort_sample_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['sample_data'] = sample_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/sample_data.html', context=context_dict)

def checkbox_sample_data_clear(request):
	context_dict = {}
	del request.session['checkbox_sample_experiment']
	del request.session['checkbox_sample_experiment_id_list']
	sample_data = sort_sample_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['sample_data'] = sample_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/sample_data.html', context=context_dict)

def show_all_sample_experiment(request):
	context_dict = {}
	sample_experiment_list = ObsTracker.objects.filter(obs_entity_type='sample').values('experiment__name', 'experiment__field__field_name', 'experiment__field__id', 'experiment__id').distinct()[:2000]
	context_dict = checkbox_session_variable_check(request)
	context_dict['sample_experiment_list'] = sample_experiment_list
	return render(request, 'lab/sample_experiment_list.html', context=context_dict)

def find_sample_from_experiment(experiment_name):
	try:
		sample_data = ObsTracker.objects.filter(obs_entity_type='sample', experiment__name=experiment_name)
	except ObsTracker.DoesNotExist:
		sample_data = None
	return sample_data

@login_required
def sample_data_from_experiment(request, experiment_name):
	context_dict = {}
	sample_data = find_sample_from_experiment(experiment_name)
	context_dict['sample_data'] = sample_data
	context_dict['experiment_name'] = experiment_name
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/sample_experiment_data.html', context=context_dict)

@login_required
def download_sample_experiment(request, experiment_name):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="%s_samples.csv"' % (experiment_name)
	sample_data = find_sample_from_experiment(experiment_name)
	writer = csv.writer(response)
	writer.writerow(['Sample ID', 'Sample Type', 'Sample Name', 'Source Seed ID', 'Source Row ID', 'Source Plant ID', 'Weight', 'Volume', 'Density', 'Num Kernels', 'Photo', 'Comments'])
	for row in sample_data:
		writer.writerow([row.obs_sample.sample_id, row.obs_sample.sample_type, row.obs_sample.sample_name, row.stock.seed_id, row.obs_row.row_id, row.obs_plant.plant_id, row.obs_sample.weight, row.obs_sample.volume, row.obs_sample.density, row.obs_sample.kernel_num, row.obs_sample.photo, row.obs_sample.comments])
	return response

@login_required
def update_sample_info(request, obs_sample_id):
	context_dict = {}
	if request.method == 'POST':
		obs_tracker_samples_form = LogSamplesOnlineForm(data=request.POST)
		if obs_tracker_samples_form.is_valid():
			with transaction.atomic():
				try:
					obs_tracker = ObsTracker.objects.get(obs_entity_type='sample', obs_sample_id=obs_sample_id, experiment=obs_tracker_samples_form.cleaned_data['experiment'])
					obs_tracker.glycerol_stock_id = 1
					obs_tracker.maize_sample_id = 1
					obs_tracker.obs_extract_id = 1
					if obs_tracker_samples_form.cleaned_data['stock__seed_id'] != '':
						obs_tracker.stock = Stock.objects.get(seed_id=obs_tracker_samples_form.cleaned_data['stock__seed_id'])
						try:
							obs_tracker_source_stock = ObsTrackerSource.objects.get(target_obs=obs_tracker, source_obs__obs_entity_type='stock', relationship='sample_from_stock')
							obs_tracker_source_stock.source_obs = ObsTracker.objects.get(obs_entity_type='stock', stock__seed_id=obs_tracker_samples_form.cleaned_data['stock__seed_id'])
							obs_tracker_source_stock.save()
						except ObsTrackerSource.DoesNotExist:
							new_source_stock = ObsTrackerSource.objects.create(source_obs = ObsTracker.objects.get(obs_entity_type='stock', stock__seed_id=obs_tracker_samples_form.cleaned_data['stock__seed_id']), target_obs=obs_tracker, relationship="sample_from_stock")
					else:
						obs_tracker.stock = Stock.objects.get(id=1)
					if obs_tracker_samples_form.cleaned_data['obs_row__row_id'] != '':
						obs_tracker.obs_row = ObsRow.objects.get(row_id=obs_tracker_samples_form.cleaned_data['obs_row__row_id'])
						try:
							obs_tracker_source_row = ObsTrackerSource.objects.get(target_obs=obs_tracker, source_obs__obs_entity_type='row', relationship='sample_from_row')
							obs_tracker_source_row.source_obs = ObsTracker.objects.get(obs_entity_type='row', obs_row__row_id=obs_tracker_samples_form.cleaned_data['obs_row__row_id'])
							obs_tracker_source_row.save()
						except ObsTrackerSource.DoesNotExist:
							new_source_row = ObsTrackerSource.objects.create(source_obs = ObsTracker.objects.get(obs_entity_type='row', obs_row__row_id=obs_tracker_samples_form.cleaned_data['obs_row__row_id']), target_obs=obs_tracker, relationship="sample_from_row")
					else:
						obs_tracker.obs_row = ObsRow.objects.get(id=1)
					if obs_tracker_samples_form.cleaned_data['obs_plant__plant_id'] != '':
						obs_tracker.obs_plant = ObsPlant.objects.get(plant_id=obs_tracker_samples_form.cleaned_data['obs_plant__plant_id'])
						try:
							obs_tracker_source_plant = ObsTrackerSource.objects.get(target_obs=obs_tracker, source_obs__obs_entity_type='plant', relationship='sample_from_plant')
							obs_tracker_source_plant.source_obs = ObsTracker.objects.get(obs_entity_type='plant', obs_plant__plant_id=obs_tracker_samples_form.cleaned_data['obs_plant__plant_id'])
							obs_tracker_source_plant.save()
						except ObsTrackerSource.DoesNotExist:
							new_source_plant = ObsTrackerSource.objects.create(source_obs = ObsTracker.objects.get(obs_entity_type='plant', obs_plant__plant_id=obs_tracker_samples_form.cleaned_data['obs_plant__plant_id']), target_obs=obs_tracker, relationship="sample_from_plant")
					else:
						obs_tracker.obs_plant = ObsPlant.objects.get(id=1)

					obs_sample = ObsSample.objects.get(id=obs_sample_id)
					obs_sample.sample_id = obs_tracker_samples_form.cleaned_data['obs_sample__sample_id']
					obs_sample.sample_name = obs_tracker_samples_form.cleaned_data['obs_sample__sample_name']
					obs_sample.sample_type = obs_tracker_samples_form.cleaned_data['obs_sample__sample_type']
					obs_sample.weight = obs_tracker_samples_form.cleaned_data['obs_sample__weight']
					obs_sample.volume = obs_tracker_samples_form.cleaned_data['obs_sample__volume']
					obs_sample.density = obs_tracker_samples_form.cleaned_data['obs_sample__density']
					obs_sample.kernel_num = obs_tracker_samples_form.cleaned_data['obs_sample__kernel_num']
					obs_sample.photo = obs_tracker_samples_form.cleaned_data['obs_sample__photo']
					obs_sample.comments = obs_tracker_samples_form.cleaned_data['obs_sample__comments']

					if obs_tracker_samples_form.cleaned_data['source_sample_id'] != '':
						try:
							obs_tracker_source_sample = ObsTrackerSource.objects.get(target_obs=obs_tracker, source_obs__obs_entity_type='sample')
							obs_tracker_source_sample.source_obs = ObsTracker.objects.get(obs_entity_type='sample', obs_sample__sample_id=obs_tracker_samples_form.cleaned_data['source_sample_id'])
							obs_tracker_source_sample.save()
						except ObsTrackerSource.DoesNotExist:
							new_source_sample = ObsTrackerSource.objects.create(source_obs = ObsTracker.objects.get(obs_entity_type='sample', obs_sample__sample_id=obs_tracker_samples_form.cleaned_data['source_sample_id']), target_obs=obs_tracker, relationship="sample_from_sample")
					else:
						try:
							obs_tracker_source_sample = ObsTrackerSource.objects.get(target_obs=obs_tracker, source_obs__obs_entity_type='sample', relationship="sample_from_sample")
							obs_tracker_source_sample.delete()
						except ObsTrackerSource.DoesNotExist:
							pass

					obs_sample.save()
					obs_tracker.save()
					context_dict['updated'] = True
				except Exception:
					context_dict['failed'] = True
		else:
			print(obs_tracker_samples_form.errors)
	else:
		samples_data = ObsTracker.objects.filter(obs_entity_type='sample', obs_sample_id=obs_sample_id).values('experiment', 'obs_sample__sample_id', 'obs_sample__sample_type', 'obs_sample__sample_name', 'stock__seed_id', 'obs_row__row_id', 'obs_plant__plant_id', 'obs_sample__weight', 'obs_sample__volume', 'obs_sample__density', 'obs_sample__kernel_num', 'obs_sample__photo', 'obs_sample__comments')
		obs_tracker_samples_form = LogSamplesOnlineForm(initial=samples_data[0])
	context_dict['obs_sample_id'] = obs_sample_id
	context_dict['obs_tracker_samples_form'] = obs_tracker_samples_form
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/samples_info_update.html', context=context_dict)

@login_required
def tissue_data_browse(request):
	context_dict = {}
	tissue_data = sort_tissue_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['tissue_data'] = tissue_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/tissue_data.html', context=context_dict)

def sort_tissue_data(request):
	tissue_data = {}
	if request.session.get('checkbox_tissue_experiment_id_list', None):
		checkbox_tissue_experiment_id_list = request.session.get('checkbox_tissue_experiment_id_list')
		for tissue_experiment in checkbox_tissue_experiment_id_list:
			tissues = ObsTracker.objects.filter(obs_entity_type='tissue', experiment__id=tissue_experiment)
			tissue_data = list(chain(tissues, tissue_data))
	else:
		tissue_data = ObsTracker.objects.filter(obs_entity_type='tissue')[:2000]
	return tissue_data

@login_required
def download_tissue_data(request):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="selected_experiment_tissues.csv"'
	tissue_data = sort_tissue_data(request)
	writer = csv.writer(response)
	writer.writerow(['Exp ID', 'Tissue ID', 'Tissue Type', 'Tissue Name', 'Date Ground', 'Comments', 'Row ID', 'Plant ID', 'Plate ID', 'Seed ID'])
	for row in tissue_data:
		writer.writerow([row.experiment, row.obs_tissue.tissue_id, row.obs_tissue.tissue_type, row.obs_tissue.tissue_name, row.obs_tissue.date_ground, row.obs_tissue.comments, row.obs_row.row_id, row.obs_plant.plant_id, row.obs_plate.plate_id, row.stock.seed_id])
	return response

def suggest_tissue_experiment(request):
	context_dict = {}
	tissue_experiment_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET['suggestion']
	else:
		starts_with = request.POST['suggestion']
	if starts_with:
		tissue_experiment_list = ObsTracker.objects.filter(obs_entity_type='tissue', experiment__name__contains=starts_with).values('experiment__name', 'experiment__field__field_name', 'experiment__field__id', 'experiment__id').distinct()[:2000]
	else:
		tissue_experiment_list = None
	context_dict = checkbox_session_variable_check(request)
	context_dict['tissue_experiment_list'] = tissue_experiment_list
	return render(request, 'lab/tissue_experiment_list.html', context= context_dict)

def select_tissue_experiment(request):
	context_dict = {}
	plant_data = []
	checkbox_tissue_experiment_name_list = []
	checkbox_tissue_experiment_list = request.POST.getlist('checkbox_tissue_experiment')
	for experiment_id in checkbox_tissue_experiment_list:
		experiment_name = Experiment.objects.filter(id=experiment_id).values('name')
		checkbox_tissue_experiment_name_list = list(chain(experiment_name, checkbox_tissue_experiment_name_list))
	request.session['checkbox_tissue_experiment'] = checkbox_tissue_experiment_name_list
	request.session['checkbox_tissue_experiment_id_list'] = checkbox_tissue_experiment_list
	tissue_data = sort_tissue_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['tissue_data'] = tissue_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/tissue_data.html', context=context_dict)

def checkbox_tissue_data_clear(request):
	context_dict = {}
	del request.session['checkbox_tissue_experiment']
	del request.session['checkbox_tissue_experiment_id_list']
	tissue_data = sort_tissue_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['tissue_data'] = tissue_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/tissue_data.html', context=context_dict)

def show_all_tissue_experiment(request):
	context_dict = {}
	tissue_experiment_list = ObsTracker.objects.filter(obs_entity_type='tissue').values('experiment__name', 'experiment__field__field_name', 'experiment__field__id', 'experiment__id').distinct()[:2000]
	context_dict = checkbox_session_variable_check(request)
	context_dict['tissue_experiment_list'] = tissue_experiment_list
	return render(request, 'lab/tissue_experiment_list.html', context=context_dict)

@login_required
def tissue_data_from_experiment(request, experiment_name):
	context_dict = {}
	tissue_data = find_relationship_for_experiment(experiment_name, 'tissue', 'tissue_used_in_experiment')
	context_dict['tissue_data'] = tissue_data
	context_dict['experiment_name'] = experiment_name
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/tissue_experiment_data.html', context=context_dict)

@login_required
def download_tissue_experiment(request, experiment_name):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="%s_tissues.csv"' % (experiment_name)
	tissue_data = find_relationship_for_experiment(experiment_name, 'tissue', 'tissue_used_in_experiment')
	writer = csv.writer(response)
	writer.writerow(['Tissue ID', 'Tissue Type', 'Tissue Name', 'Date Ground', 'Comments', 'Row ID', 'Plant ID', 'Plate ID', 'Seed ID'])
	for row in tissue_data:
		writer.writerow([row.obs_tissue.tissue_id, row.obs_tissue.tissue_type, row.obs_tissue.tissue_name, row.obs_tissue.date_ground, row.obs_tissue.comments, row.obs_row.row_id, row.obs_plant.plant_id, row.obs_plate.plate_id, row.stock.seed_id])
	return response

@login_required
def separation_data_browse(request):
	context_dict = {}
	separation_data = sort_separation_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['separation_data'] = separation_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/separation_data.html', context=context_dict)

def sort_separation_data(request):
	separation_data = []
	sample_data = []
	if request.session.get('checkbox_separation_experiment_id_list', None):
		checkbox_separation_experiment_id_list = request.session.get('checkbox_separation_experiment_id_list')
		for separation_experiment in checkbox_separation_experiment_id_list:
			try:
				samples = ObsTracker.objects.filter(obs_entity_type='samples', experiment__id=separation_experiment)
			except ObsTracker.DoesNotExist:
				samples = None
			sample_data = list(chain(samples, sample_data))
		for sample in sample_data:
			try:
				separation = Separation.objects.filter(obs_sample_id=sample.obs_sample_id)
			except Separation.DoesNotExist:
				separation = None
			separation_data = list(chain(separation, separation_data))
	else:
		separation_data = Separation.objects.all()[:2000]
	return separation_data

def find_separation_from_experiment(experiment_name):
	try:
		sample_data = ObsTracker.objects.filter(obs_entity_type='sample', experiment__name=experiment_name)
	except ObsTracker.DoesNotExist:
		sample_data = None
	if sample_data is not None:
		separations = []
		for sample in sample_data:
			try:
				separation = Separation.objects.filter(obs_sample_id=sample.obs_sample_id)
			except Separation.DoesNotExist:
				separation = None
			separations = list(chain(separation, separations))
	return separations

@login_required
def separation_data_from_experiment(request, experiment_name):
	context_dict = {}
	separation_data = find_separation_from_experiment(experiment_name)
	context_dict['separation_data'] = separation_data
	context_dict['experiment_name'] = experiment_name
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/separation_experiment_data.html', context=context_dict)

@login_required
def download_separation_experiment(request, experiment_name):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="%s_separations.csv"' % (experiment_name)
	separation_data = find_separation_from_experiment(experiment_name)
	writer = csv.writer(response)
	writer.writerow(['Sample ID', 'Sample Name', 'Separation Type', 'Apparatus', 'SG', 'Light Weight (g)', 'Medium Weight (g)', 'Heavy Weight (g)', 'Light Percent', 'Medium Percent', 'Heavy Percent', 'Operating Factor', 'Comments'])
	for row in separation_data:
		writer.writerow([row.obs_sample.sample_id, row.obs_sample.sample_name, row.separation_type, row.apparatus, row.SG, row.light_weight, row.intermediate_weight, row.heavy_weight, row.light_percent, row.intermediate_percent, row.heavy_percent, row.operating_factor, row.comments])
	return response

@login_required
def download_separation_data(request):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="all_separations.csv"'
	separation_data = sort_separation_data(request)
	writer = csv.writer(response)
	writer.writerow(['Sample ID', 'Sample Name', 'Separation Type', 'Apparatus', 'SG', 'Light Weight (g)', 'Medium Weight (g)', 'Heavy Weight (g)', 'Light Percent', 'Medium Percent', 'Heavy Percent', 'Operating Factor', 'Comments'])
	for row in separation_data:
		writer.writerow([row.obs_sample.sample_id, row.obs_sample.sample_name, row.separation_type, row.apparatus, row.SG, row.light_weight, row.intermediate_weight, row.heavy_weight, row.light_percent, row.intermediate_percent, row.heavy_percent, row.operating_factor, row.comments])
	return response

@login_required
def plate_data_browse(request):
	context_dict = {}
	plate_data = sort_plate_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['plate_data'] = plate_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/plate_data.html', context=context_dict)

def sort_plate_data(request):
	plate_data = {}
	if request.session.get('checkbox_plate_experiment_id_list', None):
		checkbox_plate_experiment_id_list = request.session.get('checkbox_plate_experiment_id_list')
		for plate_experiment in checkbox_plate_experiment_id_list:
			plates = ObsTracker.objects.filter(obs_entity_type='plate', experiment__id=plate_experiment)
			plate_data = list(chain(plates, plate_data))
	else:
		plate_data = ObsTracker.objects.filter(obs_entity_type='plate')[:2000]
	return plate_data

@login_required
def download_plate_data(request):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="selected_experiment_tissues.csv"'
	plate_data = sort_plate_data(request)
	writer = csv.writer(response)
	writer.writerow(['Exp ID', 'Plate ID', 'Plate Name', 'Location', 'Date Plated', 'Contents', 'Rep', 'Plate Type', 'Plate Status', 'Comments'])
	for row in plate_data:
		writer.writerow([row.experiment, row.obs_plate.plate_id, row.obs_plate.plate_name, row.location, row.obs_plate.date, row.obs_plate.contents, row.obs_plate.rep, row.obs_plate.plate_type, row.obs_plate.plate_status, row.obs_plate.comments])
	return response

def suggest_plate_experiment(request):
	context_dict = {}
	plate_experiment_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET['suggestion']
	else:
		starts_with = request.POST['suggestion']
	if starts_with:
		plate_experiment_list = ObsTracker.objects.filter(obs_entity_type='plate', experiment__name__contains=starts_with).values('experiment__name', 'experiment__field__field_name', 'experiment__field__id', 'experiment__id').distinct()[:2000]
	else:
		plate_experiment_list = None
	context_dict = checkbox_session_variable_check(request)
	context_dict['plate_experiment_list'] = plate_experiment_list
	return render(request, 'lab/plate_experiment_list.html', context=context_dict)

def select_plate_experiment(request):
	context_dict = {}
	plant_data = []
	checkbox_plate_experiment_name_list = []
	checkbox_plate_experiment_list = request.POST.getlist('checkbox_plate_experiment')
	for experiment_id in checkbox_plate_experiment_list:
		experiment_name = Experiment.objects.filter(id=experiment_id).values('name')
		checkbox_plate_experiment_name_list = list(chain(experiment_name, checkbox_plate_experiment_name_list))
	request.session['checkbox_plate_experiment'] = checkbox_plate_experiment_name_list
	request.session['checkbox_plate_experiment_id_list'] = checkbox_plate_experiment_list
	plate_data = sort_plate_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['plate_data'] = plate_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/plate_data.html', context=context_dict)

def checkbox_plate_data_clear(request):
	context_dict = {}
	del request.session['checkbox_plate_experiment']
	del request.session['checkbox_plate_experiment_id_list']
	plate_data = sort_plate_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['plate_data'] = plate_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/plate_data.html', context=context_dict)

def show_all_plate_experiment(request):
	context_dict = {}
	plate_experiment_list = ObsTracker.objects.filter(obs_entity_type='plate').values('experiment__name', 'experiment__field__field_name', 'experiment__field__id', 'experiment__id').distinct()[:2000]
	context_dict = checkbox_session_variable_check(request)
	context_dict['plate_experiment_list'] = plate_experiment_list
	return render(request, 'lab/plate_experiment_list.html', context= context_dict)


@login_required
def plate_data_from_experiment(request, experiment_name):
	context_dict = {}
	plate_data = find_relationship_for_experiment(experiment_name, 'plate', 'plate_used_in_experiment')
	context_dict['plate_data'] = plate_data
	context_dict['experiment_name'] = experiment_name
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/plate_experiment_data.html', context=context_dict)

@login_required
def download_plate_experiment(request, experiment_name):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="%s_plates.csv"' % (experiment_name)
	plate_data = find_relationship_for_experiment(experiment_name, 'plate', 'plate_used_in_experiment')
	writer = csv.writer(response)
	writer.writerow(['Plate ID', 'Plate Name', 'Date Plate', 'Contents', 'Rep', 'Plate Type', 'Plate Status', 'Plate Comments'])
	for row in plate_data:
		writer.writerow([row.obs_plate.plate_id, row.obs_plate.plate_name, row.obs_plate.date, row.obs_plate.contents, row.obs_plate.rep, row.obs_plate.plate_type, row.obs_plate.plate_status, row.obs_plate.comments])
	return response

@login_required
def well_data_browse(request):
	context_dict = {}
	well_data = sort_well_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['well_data'] = well_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/well_data.html', context=context_dict)

def sort_well_data(request):
	well_data = {}
	if request.session.get('checkbox_well_experiment_id_list', None):
		checkbox_well_experiment_id_list = request.session.get('checkbox_well_experiment_id_list')
		for well_experiment in checkbox_well_experiment_id_list:
			wells = ObsTracker.objects.filter(obs_entity_type='well', experiment__id=well_experiment)
			well_data = list(chain(wells, well_data))
	else:
		well_data = ObsTracker.objects.filter(obs_entity_type='well')[:2000]
	return well_data

@login_required
def download_well_data(request):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="selected_experiment_wells.csv"'
	well_data = sort_well_data(request)
	writer = csv.writer(response)
	writer.writerow(['Exp ID', 'Well ID', 'Well', 'Well Inventory', 'Tube Label', 'Comments', 'Plate ID', 'Row ID', 'Plant ID', 'Tissue ID', 'Seed ID'])
	for row in well_data:
		writer.writerow([row.experiment, row.obs_well.well_id, row.obs_well.well, row.obs_well.well_inventory, row.obs_well.tube_label, row.obs_well.comments, row.obs_plate.plate_id, row.obs_row.row_id, row.obs_plant.plant_id, row.obs_tissue.tissue_id, row.stock.seed_id])
	return response

def suggest_well_experiment(request):
	context_dict = {}
	well_experiment_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET['suggestion']
	else:
		starts_with = request.POST['suggestion']
	if starts_with:
		well_experiment_list = ObsTracker.objects.filter(obs_entity_type='well', experiment__name__contains=starts_with).values('experiment__name', 'experiment__field__field_name', 'experiment__field__id', 'experiment__id').distinct()[:2000]
	else:
		well_experiment_list = None
	context_dict = checkbox_session_variable_check(request)
	context_dict['well_experiment_list'] = well_experiment_list
	return render(request, 'lab/well_experiment_list.html', context=context_dict)

def select_well_experiment(request):
	context_dict = {}
	well_data = []
	checkbox_well_experiment_name_list = []
	checkbox_well_experiment_list = request.POST.getlist('checkbox_well_experiment')
	for experiment_id in checkbox_well_experiment_list:
		experiment_name = Experiment.objects.filter(id=experiment_id).values('name')
		checkbox_well_experiment_name_list = list(chain(experiment_name, checkbox_well_experiment_name_list))
	request.session['checkbox_well_experiment'] = checkbox_well_experiment_name_list
	request.session['checkbox_well_experiment_id_list'] = checkbox_well_experiment_list
	well_data = sort_well_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['well_data'] = well_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/well_data.html', context=context_dict)

def checkbox_well_data_clear(request):
	context_dict = {}
	del request.session['checkbox_well_experiment']
	del request.session['checkbox_well_experiment_id_list']
	well_data = sort_well_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['well_data'] = well_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/well_data.html', context=context_dict)

def show_all_well_experiment(request):
	context_dict = {}
	well_experiment_list = ObsTracker.objects.filter(obs_entity_type='well').values('experiment__name', 'experiment__field__field_name', 'experiment__field__id', 'experiment__id').distinct()[:2000]
	context_dict = checkbox_session_variable_check(request)
	context_dict['well_experiment_list'] = well_experiment_list
	return render(request, 'lab/well_experiment_list.html', context=context_dict)

@login_required
def well_data_from_experiment(request, experiment_name):
	context_dict = {}
	well_data = find_relationship_for_experiment(experiment_name, 'well', 'well_used_in_experiment')
	context_dict['well_data'] = well_data
	context_dict['experiment_name'] = experiment_name
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/well_experiment_data.html', context=context_dict)

@login_required
def download_well_experiment(request, experiment_name):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="%s_wells.csv"' % (experiment_name)
	well_data = find_relationship_for_experiment(experiment_name, 'well', 'well_used_in_experiment')
	writer = csv.writer(response)
	writer.writerow(['Well ID', 'Well', 'Well Inventory', 'Tube Label', 'Comments', 'Plate ID', 'Row ID', 'Plant ID', 'Tissue ID', 'Seed ID'])
	for row in well_data:
		writer.writerow([row.obs_well.well_id, row.obs_well.well, row.obs_well.well_inventory, row.obs_well.tube_label, row.obs_well.comments, row.obs_plate.plate_id, row.obs_row.row_id, row.obs_plant.plant_id, row.obs_tissue.tissue_id, row.stock.seed_id])
	return response

@login_required
def plant_data_browse(request):
	context_dict = {}
	plant_data = sort_plant_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['plant_data'] = plant_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/plant_data.html', context=context_dict)

def sort_plant_data(request):
	plant_data = {}
	if request.session.get('checkbox_plant_experiment_id_list', None):
		checkbox_plant_experiment_id_list = request.session.get('checkbox_plant_experiment_id_list')
		for plant_experiment in checkbox_plant_experiment_id_list:
			plants = ObsTracker.objects.filter(obs_entity_type='plant', experiment__id=plant_experiment)
			plant_data = list(chain(plants, plant_data))
	else:
		plant_data = ObsTracker.objects.filter(obs_entity_type='plant')[:2000]
	return plant_data

@login_required
def download_plant_data(request):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="selected_experiment_plants.csv"'
	plant_data = sort_plant_data(request)
	writer = csv.writer(response)
	writer.writerow(['Exp ID', 'Row ID', 'Seed ID', 'Plant ID', 'Plant Num', 'Comments'])
	for row in plant_data:
		writer.writerow([row.experiment, row.obs_row, row.stock.seed_id, row.obs_plant.plant_id, row.obs_plant.plant_num, row.obs_plant.comments])
	return response

def suggest_plant_experiment(request):
	context_dict = {}
	plant_experiment_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET['suggestion']
	else:
		starts_with = request.POST['suggestion']
	if starts_with:
		plant_experiment_list = ObsTracker.objects.filter(obs_entity_type='plant', experiment__name__contains=starts_with).values('experiment__name', 'experiment__field__field_name', 'experiment__field__id', 'experiment__id').distinct()[:2000]
	else:
		plant_experiment_list = None
	context_dict = checkbox_session_variable_check(request)
	context_dict['plant_experiment_list'] = plant_experiment_list
	return render(request, 'lab/plant_experiment_list.html', context=context_dict)

def select_plant_experiment(request):
	context_dict = {}
	plant_data = []
	checkbox_plant_experiment_name_list = []
	checkbox_plant_experiment_list = request.POST.getlist('checkbox_plant_experiment')
	for experiment_id in checkbox_plant_experiment_list:
		experiment_name = Experiment.objects.filter(id=experiment_id).values('name')
		checkbox_plant_experiment_name_list = list(chain(experiment_name, checkbox_plant_experiment_name_list))
	request.session['checkbox_plant_experiment'] = checkbox_plant_experiment_name_list
	request.session['checkbox_plant_experiment_id_list'] = checkbox_plant_experiment_list
	plant_data = sort_plant_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['plant_data'] = plant_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/plant_data.html', context=context_dict)

def checkbox_plant_data_clear(request):
	context_dict = {}
	del request.session['checkbox_plant_experiment']
	del request.session['checkbox_plant_experiment_id_list']
	plant_data = sort_plant_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['plant_data'] = plant_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/plant_data.html', context=context_dict)

def show_all_plant_experiment(request):
	context_dict = {}
	plant_experiment_list = ObsTracker.objects.filter(obs_entity_type='plant').values('experiment__name', 'experiment__field__field_name', 'experiment__field__id', 'experiment__id').distinct()[:2000]
	context_dict = checkbox_session_variable_check(request)
	context_dict['plant_experiment_list'] = plant_experiment_list
	return render(request, 'lab/plant_experiment_list.html', context=context_dict)

@login_required
def plant_data_from_experiment(request, experiment_name):
	context_dict = {}
	plant_data = find_relationship_for_experiment(experiment_name, 'plant', 'plant_used_in_experiment')
	context_dict['plant_data'] = plant_data
	context_dict['experiment_name'] = experiment_name
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/plant_experiment_data.html', context=context_dict)

@login_required
def download_plant_experiment(request, experiment_name):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="%s_plants.csv"' % (experiment_name)
	plant_data = find_relationship_for_experiment(experiment_name, 'plant', 'plant_used_in_experiment')
	writer = csv.writer(response)
	writer.writerow(['Plant ID', 'Plant Num', 'Row ID', 'Stock ID', 'Comments'])
	for row in plant_data:
		writer.writerow([row.obs_plant.plant_id, row.obs_plant.plant_num, row.obs_row.row_id, row.stock.seed_id, row.obs_plant.comments])
	return response

@login_required
def culture_data_browse(request):
	context_dict = {}
	culture_data = sort_culture_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['culture_data'] = culture_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/culture_data.html', context=context_dict)

def sort_culture_data(request):
	culture_data = {}
	if request.session.get('checkbox_culture_experiment_id_list', None):
		checkbox_culture_experiment_id_list = request.session.get('checkbox_culture_experiment_id_list')
		for culture_experiment in checkbox_culture_experiment_id_list:
			cultures = ObsTracker.objects.filter(obs_entity_type='culture', experiment__id=culture_experiment)
			culture_data = list(chain(cultures, culture_data))
	else:
		culture_data = ObsTracker.objects.filter(obs_entity_type='culture')[:2000]
	return culture_data

@login_required
def download_culture_data(request):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="selected_experiment_cultures.csv"'
	culture_data = sort_culture_data(request)
	writer = csv.writer(response)
	writer.writerow(['Exp ID', 'Culture ID', 'Culture Name', 'Microbe Type', 'Plating Cycle', 'Dilution', 'Image', 'Comments', 'Medium ID', 'Tissue ID', 'Plant ID', 'Row ID', 'Seed ID', 'Username'])
	for row in culture_data:
		writer.writerow([row.experiment, row.obs_culture.culture_id, row.obs_culture.culture_name, row.obs_culture.microbe_type, row.obs_culture.plating_cycle, row.obs_culture.dilution, row.obs_culture.image_filename, row.obs_culture.comments, row.medium.medium_id, row.obs_tissue.tissue_id, row.obs_row.row_id, row.stock.seed_id, row.user])
	return response

def suggest_culture_experiment(request):
	context_dict = {}
	culture_experiment_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET['suggestion']
	else:
		starts_with = request.POST['suggestion']
	if starts_with:
		culture_experiment_list = ObsTracker.objects.filter(obs_entity_type='culture', experiment__name__contains=starts_with).values('experiment__name', 'experiment__field__field_name', 'experiment__field__id', 'experiment__id').distinct()[:2000]
	else:
		culture_experiment_list = None
	context_dict = checkbox_session_variable_check(request)
	context_dict['culture_experiment_list'] = culture_experiment_list
	return render(request, 'lab/culture_experiment_list.html', context=context_dict)

def select_culture_experiment(request):
	context_dict = {}
	culture_data = []
	checkbox_culture_experiment_name_list = []
	checkbox_culture_experiment_list = request.POST.getlist('checkbox_culture_experiment')
	for experiment_id in checkbox_culture_experiment_list:
		experiment_name = Experiment.objects.filter(id=experiment_id).values('name')
		checkbox_culture_experiment_name_list = list(chain(experiment_name, checkbox_culture_experiment_name_list))
	request.session['checkbox_culture_experiment'] = checkbox_culture_experiment_name_list
	request.session['checkbox_culture_experiment_id_list'] = checkbox_culture_experiment_list
	culture_data = sort_culture_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['culture_data'] = culture_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/culture_data.html', context=context_dict)

def checkbox_culture_data_clear(request):
	context_dict = {}
	del request.session['checkbox_culture_experiment']
	del request.session['checkbox_culture_experiment_id_list']
	culture_data = sort_culture_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['culture_data'] = culture_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/culture_data.html', context=context_dict)

def show_all_culture_experiment(request):
	context_dict = {}
	culture_experiment_list = ObsTracker.objects.filter(obs_entity_type='culture').values('experiment__name', 'experiment__field__field_name', 'experiment__field__id', 'experiment__id').distinct()[:2000]
	context_dict = checkbox_session_variable_check(request)
	context_dict['culture_experiment_list'] = culture_experiment_list
	return render(request, 'lab/culture_experiment_list.html', context=context_dict)


@login_required
def culture_data_from_experiment(request, experiment_name):
	context_dict = {}
	culture_data = find_relationship_for_experiment(experiment_name, 'culture', 'culture_used_in_experiment')
	context_dict['culture_data'] = culture_data
	context_dict['experiment_name'] = experiment_name
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/culture_experiment_data.html', context=context_dict)

@login_required
def download_culture_experiment(request, experiment_name):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="%s_cultures.csv"' % (experiment_name)
	culture_data = find_relationship_for_experiment(experiment_name, 'culture', 'culture_used_in_experiment')
	writer = csv.writer(response)
	writer.writerow(['Culture ID', 'Culture Name', 'Microbe Type', 'Plating Cycle', 'Dilution', 'Image', 'Comments', 'Medium ID', 'Tissue ID', 'Plant ID', 'Row ID', 'Seed ID', 'Username'])
	for row in culture_data:
		writer.writerow([row.obs_culture.culture_id, row.obs_culture.culture_name, row.obs_culture.microbe_type, row.obs_culture.plating_cycle, row.obs_culture.dilution, row.obs_culture.image_filename, row.obs_culture.comments, row.obs_culture.medium.media_name, row.obs_tissue.tissue_id, row.obs_plant.plant_id, row.obs_row.row_id, row.stock.seed_id, row.user])
	return response

@login_required
def dna_data_browse(request):
	context_dict = {}
	dna_data = sort_dna_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['dna_data'] = dna_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/dna_data.html', context=context_dict)

def sort_dna_data(request):
	dna_data = {}
	if request.session.get('checkbox_dna_experiment_id_list', None):
		checkbox_dna_experiment_id_list = request.session.get('checkbox_dna_experiment_id_list')
		for dna_experiment in checkbox_dna_experiment_id_list:
			dna = ObsTracker.objects.filter(obs_entity_type='dna', experiment__id=dna_experiment)
			dna_data = list(chain(dna, dna_data))
	else:
		dna_data = ObsTracker.objects.filter(obs_entity_type='dna')[:2000]
	return dna_data

@login_required
def download_dna_data(request):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="selected_experiment_wells.csv"'
	dna_data = sort_dna_data(request)
	writer = csv.writer(response)
	writer.writerow(['Exp ID', 'DNA ID', 'Extraction Method', 'Date', 'Tube ID', 'Tube Type', 'Comments', 'Well ID', 'Plate ID', 'Plant ID', 'Tissue ID', 'Row ID', 'Seed ID', 'Username'])
	for row in dna_data:
		writer.writerow([row.experiment, row.obs_dna.dna_id, row.obs_dna.extraction_method, row.obs_dna.date, row.obs_dna.tube_id, row.obs_dna.tube_type, row.obs_dna.comments, row.obs_well.well_id, row.obs_plate.plate_id, row.obs_plant.plant_id, row.obs_tissue.tissue_id, row.obs_row.row_id, row.stock.seed_id, row.user])
	return response

def suggest_dna_experiment(request):
	context_dict = {}
	dna_experiment_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET['suggestion']
	else:
		starts_with = request.POST['suggestion']
	if starts_with:
		dna_experiment_list = ObsTracker.objects.filter(obs_entity_type='dna', experiment__name__contains=starts_with).values('experiment__name', 'experiment__field__field_name', 'experiment__field__id', 'experiment__id').distinct()[:2000]
	else:
		dna_experiment_list = None
	context_dict = checkbox_session_variable_check(request)
	context_dict['dna_experiment_list'] = dna_experiment_list
	return render(request, 'lab/dna_experiment_list.html', context=context_dict)

def select_dna_experiment(request):
	context_dict = {}
	dna_data = []
	checkbox_dna_experiment_name_list = []
	checkbox_dna_experiment_list = request.POST.getlist('checkbox_dna_experiment')
	for experiment_id in checkbox_dna_experiment_list:
		experiment_name = Experiment.objects.filter(id=experiment_id).values('name')
		checkbox_dna_experiment_name_list = list(chain(experiment_name, checkbox_dna_experiment_name_list))
	request.session['checkbox_dna_experiment'] = checkbox_dna_experiment_name_list
	request.session['checkbox_dna_experiment_id_list'] = checkbox_dna_experiment_list
	dna_data = sort_dna_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['dna_data'] = dna_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/dna_data.html', context=context_dict)

def checkbox_dna_data_clear(request):
	context_dict = {}
	del request.session['checkbox_dna_experiment']
	del request.session['checkbox_dna_experiment_id_list']
	dna_data = sort_dna_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['dna_data'] = dna_data
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/dna_data.html', context=context_dict)

def show_all_dna_experiment(request):
	context_dict = {}
	dna_experiment_list = ObsTracker.objects.filter(obs_entity_type='dna').values('experiment__name', 'experiment__field__field_name', 'experiment__field__id', 'experiment__id').distinct()[:2000]
	context_dict = checkbox_session_variable_check(request)
	context_dict['dna_experiment_list'] = dna_experiment_list
	return render(request, 'lab/dna_experiment_list.html', context=context_dict)

@login_required
def dna_data_from_experiment(request, experiment_name):
	context_dict = {}
	dna_data = find_relationship_for_experiment(experiment_name, 'dna', 'dna_used_in_experiment')
	context_dict['dna_data'] = dna_data
	context_dict['experiment_name'] = experiment_name
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/dna_experiment_data.html', context=context_dict)

@login_required
def download_dna_experiment(request, experiment_name):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="%s_dna.csv"' % (experiment_name)
	dna_data = find_relationship_for_experiment(experiment_name, 'dna', 'dna_used_in_experiment')
	writer = csv.writer(response)
	writer.writerow(['DNA ID', 'Extraction Method', 'Date', 'Tube ID', 'Tube Type', 'Comments', 'Well ID', 'Plate ID', 'Plant ID', 'Tissue ID', 'Row ID', 'Seed ID', 'Username'])
	for row in dna_data:
		writer.writerow([row.obs_dna.dna_id, row.obs_dna.extraction_method, row.obs_dna.date, row.obs_dna.tube_id, row.obs_dna.tube_type, row.obs_dna.comments, row.obs_well.well_id, row.obs_plate.plate_id, row.obs_plant.plant_id, row.obs_tissue.tissue_id, row.obs_row.row_id, row.stock.seed_id, row.user])
	return response

def datatable_measurement_data(request):
	measurement_data = sort_measurement_data(request)
	count = 0
	arr = []
	for data in measurement_data:
		arr.append({
        	'experiment_name': data.obs_tracker.experiment.name,
        	'obs_id': data.obs_tracker.obs_id,
        	'obs_url': data.obs_tracker.obs_id_url,
        	'username': data.user.username,
        	'time_of_measurement': data.time_of_measurement,
        	'parameter_type': data.measurement_parameter.parameter_type,
        	'parameter_name': data.measurement_parameter.parameter,
        	'parameter_id': data.measurement_parameter_id,
        	'value': data.value,
        	'unit_of_measure': data.measurement_parameter.unit_of_measure,
        	'trait_id_buckler': data.measurement_parameter.trait_id_buckler,
        	'comments': data.comments,
    	})
	return JsonResponse({'data':arr, 'recordsTotal':count}, safe=True)

@login_required
def measurement_data_browse(request):
	context_dict = {}
	context_dict = checkbox_session_variable_check(request)
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/measurement_data.html', context=context_dict)

def sort_measurement_data(request):
	measurement_data = {}
	checkbox_taxonomy_list = []
	checkbox_pedigree_list = []
	if request.session.get('checkbox_measurement_experiment', None):
		checkbox_measurement_experiment = request.session.get('checkbox_measurement_experiment')
		if request.session.get('checkbox_measurement_parameter', None):
			checkbox_measurement_parameter = request.session.get('checkbox_measurement_parameter')
			for e in checkbox_measurement_experiment:
				for p in checkbox_measurement_parameter:
					m = Measurement.objects.filter(measurement_parameter__parameter=p, obs_tracker__experiment__name=e['name'])
					measurement_data = list(chain(measurement_data, m))
		else:
			for e in checkbox_measurement_experiment:
				m = Measurement.objects.filter(obs_tracker__experiment__name=e['name'])
				measurement_data = list(chain(measurement_data, m))
	else:
		if request.session.get('checkbox_measurement_parameter', None):
			checkbox_measurement_parameter = request.session.get('checkbox_measurement_parameter')
			for p in checkbox_measurement_parameter:
				m = Measurement.objects.filter(measurement_parameter__parameter=p)
				measurement_data = list(chain(measurement_data, m))
		else:
			measurement_data = list(Measurement.objects.all())[:1000]

	for data in measurement_data:
		data = make_obs_tracker_info(data.obs_tracker, '')
	return measurement_data

@login_required
def download_measurement_data(request):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="selected_experiment_measurements.csv"'
	measurement_data = sort_measurement_data(request)
	writer = csv.writer(response)
	writer.writerow(['Exp ID', 'Obs ID', 'User', 'Time', 'Parameter Type', 'Parameter', 'Value', 'Units', 'Trait ID Buckler', 'Comments'])
	for row in measurement_data:
		writer.writerow([row.obs_tracker.experiment, row.obs_tracker.obs_id, row.user, row.time_of_measurement, row.measurement_parameter.parameter_type, row.measurement_parameter, row.value, row.measurement_parameter.unit_of_measure, row.measurement_parameter.trait_id_buckler, row.comments])
	return response

def suggest_measurement_experiment(request):
	measurement_experiment_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET.get('suggestion', False)
	else:
		starts_with = request.POST.get('suggestion', False)
	if starts_with:
		if request.session.get('checkbox_measurement_parameter', None):
			checkbox_parameter_list = request.session.get('checkbox_measurement_parameter')
			for parameter in checkbox_parameter_list:
				e = Measurement.objects.filter(obs_tracker__experiment__name__contains=starts_with, measurement_parameter__parameter=parameter).values('obs_tracker__experiment_id', 'obs_tracker__experiment__name', 'obs_tracker__experiment__field__field_name', 'measurement_parameter__parameter').distinct()
				measurement_experiment_list = list(chain(e, measurement_experiment_list))
			for m in measurement_experiment_list:
				m['input'] = '<input type="checkbox" name="checkbox_measurement_experiment" value="%s">' % (m['obs_tracker__experiment_id'])
		else:
			measurement_experiment_list = list(Measurement.objects.filter(obs_tracker__experiment__name__contains=starts_with).values('obs_tracker__experiment_id', 'obs_tracker__experiment__name', 'obs_tracker__experiment__field__field_name').distinct())
			for m in measurement_experiment_list:
				m['input'] = '<input type="checkbox" name="checkbox_measurement_experiment" value="%s">' % (m['obs_tracker__experiment_id'])
				m['measurement_parameter__parameter'] = ''
	return JsonResponse({'data':measurement_experiment_list})

def select_measurement_experiment(request):
	experiments = request.POST['experiments']
	checkbox_measurement_experiment_name_list = []
	checkbox_measurement_experiment_list = json.loads(experiments)
	for experiment_id in checkbox_measurement_experiment_list:
		experiment_name = Experiment.objects.filter(id=experiment_id).values('name')
		checkbox_measurement_experiment_name_list = list(chain(experiment_name, checkbox_measurement_experiment_name_list))
	request.session['checkbox_measurement_experiment'] = checkbox_measurement_experiment_name_list
	request.session['checkbox_measurement_experiment_id_list'] = checkbox_measurement_experiment_list
	return JsonResponse({'success':True})

def show_all_measurement_experiment(request):
	measurement_experiment_list = []
	if request.session.get('checkbox_measurement_parameter', None):
		checkbox_parameter_list = request.session.get('checkbox_measurement_parameter')
		for parameter in checkbox_parameter_list:
			e = Measurement.objects.filter(measurement_parameter__parameter=parameter).values('obs_tracker__experiment_id', 'obs_tracker__experiment__name', 'obs_tracker__experiment__field__field_name', 'measurement_parameter__parameter').distinct()
			measurement_experiment_list = list(chain(e, measurement_experiment_list))
		for m in measurement_experiment_list:
			m['input'] = '<input type="checkbox" name="checkbox_measurement_experiment" value="%s">' % (m['obs_tracker__experiment_id'])
	else:
		measurement_experiment_list = list(Measurement.objects.all().values('obs_tracker__experiment_id', 'obs_tracker__experiment__name', 'obs_tracker__experiment__field__field_name').distinct())
		for m in measurement_experiment_list:
			m['input'] = '<input type="checkbox" name="checkbox_measurement_experiment" value="%s">' % (m['obs_tracker__experiment_id'])
			m['measurement_parameter__parameter'] = ''
	return JsonResponse({'data':measurement_experiment_list})

def suggest_measurement_parameter(request):
	measurement_parameter_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET.get('suggestion', False)
	else:
		starts_with = request.POST.get('suggestion', False)
	if starts_with:
		if request.session.get('checkbox_measurement_experiment', None):
			checkbox_experiment_list = request.session.get('checkbox_measurement_experiment')
			for experiment in checkbox_experiment_list:
				p = Measurement.objects.filter(obs_tracker__experiment__name=experiment['name'], measurement_parameter__parameter__contains=starts_with).values('obs_tracker__experiment__name', 'measurement_parameter__parameter_type', 'measurement_parameter__parameter').distinct()
				measurement_parameter_list = list(chain(p, measurement_parameter_list))
			for m in measurement_parameter_list:
				m['input'] = '<input type="checkbox" name="checkbox_measurement_parameter" value="%s">' % (m['measurement_parameter__parameter'])
		else:
			measurement_parameter_list = list(Measurement.objects.filter(measurement_parameter__parameter__contains=starts_with).values('measurement_parameter__parameter_type', 'measurement_parameter__parameter').distinct())
			for m in measurement_parameter_list:
				m['input'] = '<input type="checkbox" name="checkbox_measurement_parameter" value="%s">' % (m['measurement_parameter__parameter'])
				m['obs_tracker__experiment__name'] = ''
	return JsonResponse({'data':measurement_parameter_list})

def select_measurement_parameter(request):
	parameters = request.POST['parameters']
	checkbox_measurement_parameter_list = json.loads(parameters)
	print(checkbox_measurement_parameter_list)
	request.session['checkbox_measurement_parameter'] = checkbox_measurement_parameter_list
	return JsonResponse({'success':True})

def show_all_measurement_parameter(request):
	measurement_parameter_list = []
	if request.session.get('checkbox_measurement_experiment', None):
		checkbox_experiment_list = request.session.get('checkbox_measurement_experiment')
		for experiment in checkbox_experiment_list:
			p = Measurement.objects.filter(obs_tracker__experiment__name=experiment['name']).values('obs_tracker__experiment__name', 'measurement_parameter__parameter_type', 'measurement_parameter__parameter').distinct()
			measurement_parameter_list = list(chain(p, measurement_parameter_list))
		for m in measurement_parameter_list:
			m['input'] = '<input type="checkbox" name="checkbox_measurement_parameter" value="%s">' % (m['measurement_parameter__parameter'])
	else:
		measurement_parameter_list = list(Measurement.objects.all().values('measurement_parameter__parameter_type', 'measurement_parameter__parameter').distinct())
		for m in measurement_parameter_list:
			m['input'] = '<input type="checkbox" name="checkbox_measurement_parameter" value="%s">' % (m['measurement_parameter__parameter'])
			m['obs_tracker__experiment__name'] = ''
	return JsonResponse({'data':measurement_parameter_list})

def find_measurement_from_experiment(experiment_name):
	try:
		measurement_data = Measurement.objects.filter(obs_tracker__experiment__name=experiment_name)
	except Measurement.DoesNotExist:
		measurement_data = None
	return measurement_data

@login_required
def measurement_data_from_experiment(request, experiment_name):
	context_dict = {}
	measurement_data = find_measurement_from_experiment(experiment_name)
	for m in measurement_data:
		m = make_obs_tracker_info(m.obs_tracker, '')

	context_dict['measurement_data'] = measurement_data
	context_dict['experiment_name'] = experiment_name
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/measurement_experiment_data.html', context=context_dict)

def separations_measurement_data_from_experiment(request, experiment_name):
	context = RequestContext(request)
	context_dict = {}
	measurement_data = find_measurement_from_experiment(experiment_name)
	measurement_data = measurement_data.filter(obs_tracker__obs_entity_type='sample', measurement_parameter__parameter='AF').exclude(obs_tracker__obs_sample__sample_type='Control')

	data = []
	unique_types = {}
	inc = 1
	for q in measurement_data:
		if q.obs_tracker.obs_sample.sample_type not in unique_types:
			unique_types[q.obs_tracker.obs_sample.sample_type] = inc
			inc = inc + 1

	for q in measurement_data:
		print(q.obs_tracker.obs_sample.sample_type)
		data.append({'sample_type_number':unique_types[q.obs_tracker.obs_sample.sample_type], 'sample_type':q.obs_tracker.obs_sample.sample_type, 'm_value':q.value, 'sample_id':q.obs_tracker.obs_sample.sample_id, 'parameter_type':q.measurement_parameter.parameter})

	return JsonResponse({'data':data}, safe=True)

@login_required
def download_measurement_experiment(request, experiment_name):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="%s_measurements.csv"' % (experiment_name)
	measurement_data = find_measurement_from_experiment(experiment_name)
	for m in measurement_data:
		m = make_obs_tracker_info(m.obs_tracker, '')
	writer = csv.writer(response)
	writer.writerow(['Obs', 'User', 'Time', 'Parameter Type', 'Parameter', 'Value', 'Units', 'TraitID Buckler', 'Comments'])
	for row in measurement_data:
		writer.writerow([row.obs_tracker.obs_id, row.user, row.time_of_measurement, row.measurement_parameter.parameter_type, row.measurement_parameter.parameter, row.value, row.measurement_parameter.unit_of_measure, row.measurement_parameter.trait_id_buckler, row.comments])
	return response

@login_required
def stock_for_experiment(request, experiment_name):
	context_dict = {}
	context_dict['stock_for_experiment'] = find_relationship_for_experiment(experiment_name, 'stock', 'stock_used_in_experiment')
	context_dict['experiment_name'] = experiment_name
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/seed_for_experiment.html', context=context_dict)

@login_required
def stock_collected_from_experiment(request, experiment_name):
	context_dict = {}
	collected_stock_data = find_stock_collected_from_experiment(experiment_name)
	context_dict['collected_stock_data'] = collected_stock_data
	context_dict['experiment_name'] = experiment_name
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/seed_collected_from_experiment.html', context=context_dict)

def find_seedpackets_from_obstracker_stock(stock_query):
	seed_packet_list = []
	for packet in stock_query:
		try:
			seed_packet = StockPacket.objects.filter(stock=packet.stock)
		except StockPacket.DoesNotExist:
			seed_packet = None
		seed_packet_list = list(chain(seed_packet, seed_packet_list))
	return seed_packet_list

def find_seedpackets_from_obstrackersource_stock(stock_query):
	seed_packet_list = []
	for packet in stock_query:
		try:
			seed_packet = StockPacket.objects.filter(stock=packet.target_obs.stock)
		except StockPacket.DoesNotExist:
			seed_packet = None
		seed_packet_list = list(chain(seed_packet, seed_packet_list))
	return seed_packet_list

def find_relationship_for_experiment(experiment_name, obs_entity_type, relationship):
	try:
		used_data = ObsTrackerSource.objects.filter(source_obs__experiment__name=experiment_name, source_obs__obs_entity_type='experiment', target_obs__obs_entity_type=obs_entity_type, relationship=relationship)
	except ObsTrackerSource.DoesNotExist:
		used_data = None
	data_for_experiment = []
	if used_data:
		for s in used_data:
			data_for_experiment.append(s.target_obs)
	else:
		try:
			data_for_experiment = ObsTracker.objects.filter(experiment__name=experiment_name, obs_entity_type=obs_entity_type)
		except ObsTracker.DoesNotExist:
			data_for_experiment = None
	return data_for_experiment

@login_required
def stockpackets_for_experiment(request, experiment_name):
	context_dict = {}
	stock_data = find_relationship_for_experiment(experiment_name, 'stock', 'stock_used_in_experiment')
	if stock_data is not None:
		stockpackets_used = find_seedpackets_from_obstracker_stock(stock_data)
	else:
		stockpackets_used = None
	context_dict['stockpackets'] = stockpackets_used
	context_dict['packet_type'] = 'Used'
	context_dict['experiment_name'] = experiment_name
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/seedpackets_for_experiment.html', context=context_dict)

def download_stockpackets_for_experiment(request, experiment_name):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="%s_measurements.csv"' % (experiment_name)
	stock_data = find_relationship_for_experiment(experiment_name, 'stock', 'stock_used_in_experiment')
	if stock_data is not None:
		stockpackets_used = find_seedpackets_from_obstracker_stock(stock_data)
	else:
		stockpackets_used = None
	writer = csv.writer(response)
	writer.writerow(['Seed ID', 'Seed Name', 'Cross Type', 'Pedigree', 'Population', 'Status', 'Inoculated', 'Seed Comments', 'Weight (g)', 'Num Seeds', 'Location', 'Packet Comments'])
	for row in stockpackets_used:
		writer.writerow([row.stock.seed_id, row.stock.seed_name, row.stock.cross_type, row.stock.pedigree, row.stock.passport.taxonomy.population, row.stock.stock_status, row.stock.inoculated, row.stock.comments, row.weight, row.num_seeds, row.location.location_name, row.comments])
	return response

@login_required
def stockpackets_collected_from_experiment(request, experiment_name):
	context_dict = {}
	collected_stock_data = find_stock_collected_from_experiment(experiment_name)
	if collected_stock_data is not None:
		stockpackets_collected = find_seedpackets_from_obstrackersource_stock(collected_stock_data)
	else:
		stockpackets_collected = None
	context_dict['stockpackets'] = stockpackets_collected
	context_dict['packet_type'] = 'Collected'
	context_dict['experiment_name'] = experiment_name
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/seedpackets_for_experiment.html', context=context_dict)

def download_stockpackets_collected_experiment(request, experiment_name):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="%s_measurements.csv"' % (experiment_name)
	stock_data = find_stock_collected_from_experiment(experiment_name)
	if stock_data is not None:
		stockpackets_collected = find_seedpackets_from_obstrackersource_stock(stock_data)
	else:
		stockpackets_collected = None
	writer = csv.writer(response)
	writer.writerow(['Seed ID', 'Seed Name', 'Cross Type', 'Pedigree', 'Population', 'Status', 'Inoculated', 'Seed Comments', 'Weight (g)', 'Num Seeds', 'Location', 'Packet Comments'])
	for row in stockpackets_collected:
		writer.writerow([row.stock.seed_id, row.stock.seed_name, row.stock.cross_type, row.stock.pedigree, row.stock.passport.taxonomy.population, row.stock.stock_status, row.stock.inoculated, row.stock.comments, row.weight, row.num_seeds, row.location.location_name, row.comments])
	return response


def isolate_data_from_experiment(request, experiment_name):
	context_dict = {}
	isolate_data = find_relationship_for_experiment(experiment_name, 'isolate', 'isolate_used_in_experiment')
	context_dict['isolate_data'] = isolate_data
	context_dict['experiment_name'] = experiment_name
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/isolate_from_experiment.html', context=context_dict)

def download_isolates_experiment(request, experiment_name):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="%s_measurements.csv"' % (experiment_name)
	isolate_data = find_relationship_for_experiment(experiment_name, 'isolate', 'isolate_used_in_experiment')
	writer = csv.writer(response)
	writer.writerow(['Isolate ID', 'Isolate Name', 'Plant Organ', 'Isolate Comments', 'Genus', 'Species', 'Alias', 'Race', 'Subtaxa', 'Disease Name', 'Location Name', 'Box Name'])
	for i in isolate_data:
		writer.writerow([i.isolate_id, i.isolate.isolate_name, i.isolate.plant_organ, i.isolate.comments, i.isolate.passport.taxonomy.genus, i.isolate.passport.taxonomy.species, i.isolate.passport.taxonomy.alias, i.isolate.passport.taxonomy.race, i.isolate.passport.taxonomy.subtaxa, i.isolate.disease_info, i.isolate.location.location_name, i.isolate.location.box_name])
	return response

def make_obs_tracker_info(tracker, relationship):
	obs_entity_type = tracker.obs_entity_type
	if obs_entity_type == 'stock':
		try:
			obs_tracker_id_info = [tracker.stock.seed_id, obs_entity_type, tracker.stock_id]
		except Stock.DoesNotExist:
			obs_tracker_id_info = ['No Stock', obs_entity_type, 1]
	elif obs_entity_type == 'isolate':
		try:
			obs_tracker_id_info = [tracker.isolate.isolate_id, obs_entity_type, tracker.isolate_id]
		except Isolate.DoesNotExist:
			obs_tracker_id_info = ['No Isolate', obs_entity_type, 1]
	elif obs_entity_type == 'glycerol_stock':
		try:
			obs_tracker_id_info = [tracker.glycerol_stock.glycerol_stock_id, obs_entity_type, tracker.glycerol_stock_id]
		except GlycerolStock.DoesNotExist:
			obs_tracker_id_info = ['No Glycerol Stock', obs_entity_type, 1]
	elif obs_entity_type == 'maize':
		try:
			obs_tracker_id_info = [tracker.maize_sample.maize_sample_id, obs_entity_type, tracker.maize_sample_id]
		except MaizeSample.DoesNotExist:
			obs_tracker_id_info = ['No Maize Sample', obs_entity_type, 1]
	elif obs_entity_type == 'row':
		try:
			obs_tracker_id_info = [tracker.obs_row.row_id, obs_entity_type, tracker.obs_row_id]
		except ObsRow.DoesNotExist:
			obs_tracker_id_info = ['No Row', obs_entity_type, 1]
	elif obs_entity_type == 'plant':
		try:
			obs_tracker_id_info = [tracker.obs_plant.plant_id, obs_entity_type, tracker.obs_plant_id]
		except ObsPlant.DoesNotExist:
			obs_tracker_id_info = ['No Plant', obs_entity_type, 1]
	elif obs_entity_type == 'culture':
		try:
			obs_tracker_id_info = [tracker.obs_culture.culture_id, obs_entity_type, tracker.obs_culture_id]
		except ObsCulture.DoesNotExist:
			obs_tracker_id_info = ['No Culture', obs_entity_type, 1]
	elif obs_entity_type == 'dna':
		try:
			obs_tracker_id_info = [tracker.obs_dna.dna_id, obs_entity_type, tracker.obs_dna_id]
		except ObsDNA.DoesNotExist:
			obs_tracker_id_info = ['No DNA', obs_entity_type, 1]
	elif obs_entity_type == 'microbe':
		try:
			obs_tracker_id_info = [tracker.obs_microbe.microbe_id, obs_entity_type, tracker.obs_microbe_id]
		except ObsMicrobe.DoesNotExist:
			obs_tracker_id_info = ['No Microbe', obs_entity_type, 1]
	elif obs_entity_type == 'plate':
		try:
			obs_tracker_id_info = [tracker.obs_plate.plate_id, obs_entity_type, tracker.obs_plate_id]
		except ObsPlate.DoesNotExist:
			obs_tracker_id_info = ['No Plate', obs_entity_type, 1]
	elif obs_entity_type == 'well':
		try:
			obs_tracker_id_info = [tracker.obs_well.well_id, obs_entity_type, tracker.obs_well_id]
		except ObsWell.DoesNotExist:
			obs_tracker_id_info = ['No Well', obs_entity_type, 1]
	elif obs_entity_type == 'tissue':
		try:
			obs_tracker_id_info = [tracker.obs_tissue.tissue_id, obs_entity_type, tracker.obs_tissue_id]
		except ObsTissue.DoesNotExist:
			obs_tracker_id_info = ['No Tissue', obs_entity_type, 1]
	elif obs_entity_type == 'culture':
		try:
			obs_tracker_id_info = [tracker.obs_culture.culture_id, obs_entity_type, tracker.obs_culture_id]
		except ObsCulture.DoesNotExist:
			obs_tracker_id_info = ['No Culture', obs_entity_type, 1]
	elif obs_entity_type == 'sample':
		try:
			obs_tracker_id_info = [tracker.obs_sample.sample_id, obs_entity_type, tracker.obs_sample_id]
		except ObsSample.DoesNotExist:
			obs_tracker_id_info = ['No Stock', obs_entity_type, 1]
	elif obs_entity_type == 'extract':
		try:
			obs_tracker_id_info = [tracker.obs_extract.extract_id, obs_entity_type, tracker.obs_extract_id]
		except ObsExtract.DoesNotExist:
			obs_tracker_id_info = ['No Extract', obs_entity_type, 1]
	elif obs_entity_type == 'maize':
		try:
			obs_tracker_id_info = [tracker.maize_sample.maize_id, obs_entity_type, tracker.maize_sample_id]
		except MaizeSample.DoesNotExist:
			obs_tracker_id_info = ['No Maize Sample', obs_entity_type, 1]
	elif obs_entity_type == 'experiment':
		try:
			obs_tracker_id_info = [tracker.experiment.name, obs_entity_type, tracker.experiment.name]
		except Experiment.DoesNotExist:
			obs_tracker_id_info = ['No Experiment', obs_entity_type, 1]
	else:
		obs_tracker_id_info = ['None', 'No Type', 1]

	tracker.relationship = relationship
	tracker.obs_id = obs_tracker_id_info[0]
	tracker.obs_id_url = '/lab/%s/%s/' % (obs_tracker_id_info[1], obs_tracker_id_info[2])
	return tracker

def get_obs_relationships(obs_type, obs_id, relationships):
	search = 'target_obs__%s' % (obs_type)
	print(search)
	obs_trackers = []
	for r in relationships:
		kwargs = {search:obs_id, 'relationship':r}
		try:
			obs_tracker_source = ObsTrackerSource.objects.filter(**kwargs)
		except ObsTrackerSource.DoesNotExist:
			obs_tracker_source = None
		if obs_tracker_source is not None:
			for s in obs_tracker_source:
				s = make_obs_tracker_info(s.source_obs, s.relationship)
				obs_trackers.append(s)
	return obs_trackers

def get_obs_tracker(obs_type, obs_id):
	kwargs = {obs_type:obs_id}
	try:
		obs_tracker = ObsTracker.objects.filter(**kwargs)
	except ObsTracker.DoesNotExist:
		obs_tracker = None
	if obs_tracker is not None:
		for tracker in obs_tracker:
			tracker = make_obs_tracker_info(tracker, '')
	return obs_tracker

def get_obs_source(obs_type, obs_id, relationship):
	obs_tracker_type = 'target_obs__%s'%(obs_type)
	if (relationship != ''):
		kwargs = {obs_tracker_type:obs_id, 'relationship':relationship}
	else:
		kwargs = {obs_tracker_type:obs_id}
	try:
		obs_source = ObsTrackerSource.objects.filter(**kwargs)
	except ObsTrackerSource.DoesNotExist:
		obs_source = None
	if obs_source is not None:
		for tracker in obs_source:
			tracker = make_obs_tracker_info(tracker.source_obs, tracker.relationship)
	return obs_source

def get_obs_target(obs_type, obs_id):
	obs_tracker_type = 'source_obs__%s'%(obs_type)
	kwargs = {obs_tracker_type:obs_id}
	try:
		obs_target = ObsTrackerSource.objects.filter(**kwargs)
	except ObsTrackerSource.DoesNotExist:
		obs_target = None
	if obs_target is not None:
		for tracker in obs_target:
			tracker = make_obs_tracker_info(tracker.target_obs, tracker.relationship)
	return obs_target

def get_seed_collected_from_row(obs_type, obs_id):
	obs_tracker_type = 'source_obs__%s'%(obs_type)
	kwargs = {obs_tracker_type:obs_id, 'target_obs__obs_entity_type':'stock'}
	try:
		obs_source = ObsTrackerSource.objects.filter(**kwargs)
	except ObsTrackerSource.DoesNotExist:
		obs_source = None
	if obs_source is not None:
		for tracker in obs_source:
			tracker = make_obs_tracker_info(tracker.target_obs, tracker.relationship)
	return obs_source

@login_required
def single_stock_info(request, stock_id):
	context_dict = {}
	obs_tracker_seed = []
	obs_source = []
	obs_targets = []
	try:
		stock_info = Stock.objects.get(id=stock_id)
	except Stock.DoesNotExist:
		stock_info = None
	if stock_info is not None:
		obs_tracker = get_obs_tracker('stock_id', stock_id)
		for t in obs_tracker:
			if t.obs_id != stock_info.seed_id:
				obs_tracker_seed.append(t)
				obs_targets.append(t)
		obs_source_row = get_obs_source('stock_id', stock_id, 'stock_from_row')
		obs_source_plant = get_obs_source('stock_id', stock_id, 'stock_from_plant')
		obs_source_introgression = get_obs_source('stock_id', stock_id, 'stock_from_introgression_parent')
		obs_source_backcross = get_obs_source('stock_id', stock_id, 'stock_from_backcross_parent')
		for t in obs_source_row:
			obs_source.append(t)
		for t in obs_source_plant:
			obs_source.append(t)
		for t in obs_source_introgression:
			obs_source.append(t)
		for t in obs_source_backcross:
			obs_source.append(t)
		obs_source_targets = get_obs_target('stock_id', stock_id)
		for t in obs_source_targets:
			obs_targets.append(t.target_obs)
		obs_measurements = get_obs_measurements('stock_id', stock_id)
		measured_parameters = {}
		for mp in obs_measurements:
			if mp.measurement_parameter_id not in measured_parameters:
				measured_parameters[mp.measurement_parameter_id] = mp.measurement_parameter.parameter
	else:
		obs_tracker = None
		obs_source = None
		obs_measurements = None
		measured_parameters = None
	try:
		stock_packets = StockPacket.objects.filter(stock_id=stock_id)
	except StockPacket.DoesNotExist:
		stock_packets = None
	context_dict['stock_info'] = stock_info
	context_dict['obs_tracker'] = obs_tracker_seed
	context_dict['obs_source'] = obs_source
	context_dict['obs_targets'] = obs_targets
	context_dict['obs_measurements'] = obs_measurements
	context_dict['stock_packets'] = stock_packets
	context_dict['measured_parameters'] = measured_parameters
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/stock_info.html', context=context_dict)

def get_obs_measurements(obs_type, obs_id):
	obs_tracker_type = 'obs_tracker__%s'%(obs_type)
	kwargs = {obs_tracker_type:obs_id}
	try:
		obs_measurements = Measurement.objects.filter(**kwargs)
	except ObsTracker.DoesNotExist:
		obs_measurements = None
	if obs_measurements is not None:
		for measurement in obs_measurements:
			measurement = make_obs_tracker_info(measurement.obs_tracker, '')
	return obs_measurements

@login_required
def single_row_info(request, obs_row_id):
	context_dict = {}
	obs_tracker_row = []
	try:
		row_info = ObsRow.objects.get(id=obs_row_id)
	except ObsRow.DoesNotExist:
		row_info = None
	if row_info is not None:
		obs_tracker = get_obs_tracker('obs_row_id', obs_row_id)
		for t in obs_tracker:
			if t.obs_id != row_info.row_id:
				obs_tracker_row.append(t)
		obs_source = get_seed_collected_from_row('obs_row_id', obs_row_id)
		obs_measurements = get_obs_measurements('obs_row_id', obs_row_id)
	else:
		obs_tracker_row = None
		obs_source = None
	context_dict['row_info'] = row_info
	context_dict['obs_tracker'] = obs_tracker_row
	context_dict['obs_source'] = obs_source
	context_dict['obs_measurements'] = obs_measurements
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/row_info.html', context=context_dict)

@login_required
def single_isolate_info(request, isolate_table_id):
	context_dict = {}
	try:
		isolate_info = Isolate.objects.get(id=isolate_table_id)
	except Isolate.DoesNotExist:
		isolate_info = None
	if isolate_info is not None:
		relationships = ['isolate_from_stock', 'isolate_from_row', 'isolate_from_plant', 'isolate_from_tissue', 'isolate_from_culture', 'isolate_from_microbe', 'isolate_from_plate', 'isolate_from_well', 'isolate_from_dna', 'isolate_used_in_experiment']
		obs_tracker = get_obs_relationships('isolate_id', isolate_table_id, relationships)
		print(obs_tracker)
		#obs_tracker = get_obs_tracker('isolate_id', isolate_table_id)
	context_dict['isolate_info'] = isolate_info
	context_dict['obs_tracker'] = obs_tracker
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/isolate_info.html', context=context_dict)

@login_required
def single_glycerol_stock_info(request, glycerol_stock_table_id):
	context_dict = {}
	try:
		glycerol_stock_info = GlycerolStock.objects.get(id=glycerol_stock_table_id)
	except GlycerolStock.DoesNotExist:
		glycerol_stock_info = None
	if glycerol_stock_info is not None:
		obs_tracker = get_obs_tracker('glycerol_stock_id', glycerol_stock_table_id)
	context_dict['glycerol_stock_info'] = glycerol_stock_info
	context_dict['obs_tracker'] = obs_tracker
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/glycerol_stock_info.html', context=context_dict)

@login_required
def single_plant_info(request, obs_plant_id):
	context_dict = {}
	try:
		plant_info = ObsPlant.objects.get(id=obs_plant_id)
	except ObsPlant.DoesNotExist:
		plant_info = None
	if plant_info is not None:
		obs_tracker = get_obs_tracker('obs_plant_id', obs_plant_id)
	context_dict['plant_info'] = plant_info
	context_dict['obs_tracker'] = obs_tracker
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/plant_info.html', context=context_dict)

@login_required
def single_maize_info(request, maize_id):
	context_dict = {}
	try:
		maize_info = MaizeSample.objects.get(id=maize_id)
	except MaizeSample.DoesNotExist:
		maize_info = None
	if maize_info is not None:
		obs_tracker = get_obs_tracker('maize_sample_id', maize_id)
	context_dict['maize_info'] = maize_info
	context_dict['obs_tracker'] = obs_tracker
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/maize_info.html', context=context_dict)

@login_required
def single_sample_info(request, obs_sample_id):
	context_dict = {}
	try:
		sample_info = ObsSample.objects.get(id=obs_sample_id)
	except ObsSample.DoesNotExist:
		sample_info = None
	if sample_info is not None:
		obs_tracker = get_obs_tracker('obs_sample_id', obs_sample_id)
		obs_tracker_source_obs = get_obs_source('obs_sample_id', obs_sample_id, '')
		obs_tracker_target_obs = get_obs_target('obs_sample_id', obs_sample_id)
	context_dict['sample_info'] = sample_info
	context_dict['obs_tracker'] = obs_tracker
	context_dict['obs_tracker_source_obs'] = obs_tracker_source_obs
	context_dict['obs_tracker_target_obs'] = obs_tracker_target_obs
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/sample_info.html', context=context_dict)

@login_required
def single_extract_info(request, obs_extract_id):
	context_dict = {}
	try:
		extract_info = ObsExtract.objects.get(id=obs_extract_id)
	except ObsExtract.DoesNotExist:
		extract_info = None
	if extract_info is not None:
		obs_tracker = get_obs_tracker('obs_extract_id', obs_extract_id)
	context_dict['extract_info'] = extract_info
	context_dict['obs_tracker'] = obs_tracker
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/extract_info.html', context=context_dict)

@login_required
def single_plate_info(request, obs_plate_id):
	context_dict = {}
	try:
		plate_info = ObsPlate.objects.get(id=obs_plate_id)
	except ObsPlate.DoesNotExist:
		plate_info = None
	if plate_info is not None:
		obs_tracker = get_obs_tracker('obs_plate_id', obs_plate_id)
	context_dict['plate_info'] = plate_info
	context_dict['obs_tracker'] = obs_tracker
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/plate_info.html', context=context_dict)

@login_required
def single_well_info(request, obs_well_id):
	context_dict = {}
	try:
		well_info = ObsWell.objects.get(id=obs_well_id)
	except ObsWell.DoesNotExist:
		well_info = None
	if well_info is not None:
		obs_tracker = get_obs_tracker('obs_well_id', obs_well_id)
	context_dict['well_info'] = well_info
	context_dict['obs_tracker'] = obs_tracker
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/well_info.html', context=context_dict)

@login_required
def single_tissue_info(request, obs_tissue_id):
	context_dict = {}
	try:
		tissue_info = ObsTissue.objects.get(id=obs_tissue_id)
	except ObsTissue.DoesNotExist:
		tissue_info = None
	if tissue_info is not None:
		obs_tracker = get_obs_tracker('obs_tissue_id', obs_tissue_id)
	context_dict['tissue_info'] = tissue_info
	context_dict['obs_tracker'] = obs_tracker
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/tissue_info.html', context=context_dict)

@login_required
def single_culture_info(request, obs_culture_id):
	context_dict = {}
	try:
		culture_info = ObsCulture.objects.get(id=obs_culture_id)
	except ObsCulture.DoesNotExist:
		culture_info = None
	if culture_info is not None:
		obs_tracker = get_obs_tracker('obs_culture_id', obs_culture_id)
	context_dict['culture_info'] = culture_info
	context_dict['obs_tracker'] = obs_tracker
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/culture_info.html', context=context_dict)

@login_required
def single_dna_info(request, obs_dna_id):
	context_dict = {}
	try:
		dna_info = ObsDNA.objects.get(id=obs_dna_id)
	except ObsDNA.DoesNotExist:
		dna_info = None
	if dna_info is not None:
		obs_tracker = get_obs_tracker('obs_dna_id', obs_dna_id)
	context_dict['dna_info'] = dna_info
	context_dict['obs_tracker'] = obs_tracker
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/dna_info.html', context=context_dict)


@login_required
def log_data_online(request, data_type):
	context_dict = {}
	failed = False
	if data_type == 'seed_inventory':
		data_type_title = 'Load Seed Info'
		LogDataOnlineFormSet = formset_factory(LogSeedDataOnlineForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				sent = True
				for form in log_data_online_form_set:
					try:
						form.cleaned_data['stock__seed_id']

						with transaction.atomic():
							try:
								experiment_used = form.cleaned_data['experiment_used']
								experiment_collected = form.cleaned_data['experiment_collected']
								experiment = form.cleaned_data['experiment']
								user = request.user
								seed_id = form.cleaned_data['stock__seed_id']
								seed_name = form.cleaned_data['stock__seed_name']
								cross_type = form.cleaned_data['stock__cross_type']
								pedigree = form.cleaned_data['stock__pedigree']
								stock_status = form.cleaned_data['stock__stock_status']
								stock_date = form.cleaned_data['stock__stock_date']
								inoculated = form.cleaned_data['stock__inoculated']
								stock_comments = form.cleaned_data['stock__comments']
								genus = form.cleaned_data['stock__passport__taxonomy__genus']
								species = form.cleaned_data['stock__passport__taxonomy__species']
								population = form.cleaned_data['stock__passport__taxonomy__population']
								row_id = form.cleaned_data['obs_row__row_id']
								plant_id = form.cleaned_data['obs_plant__plant_id']
								field = form.cleaned_data['field']
								collection_user = form.cleaned_data['stock__passport__collecting__user']
								collection_date = form.cleaned_data['stock__passport__collecting__collection_date']
								collection_method = form.cleaned_data['stock__passport__collecting__collection_method']
								collection_comments = form.cleaned_data['stock__passport__collecting__comments']
								source_fname = form.cleaned_data['stock__passport__people__first_name']
								source_lname = form.cleaned_data['stock__passport__people__last_name']
								source_organization = form.cleaned_data['stock__passport__people__organization']
								source_phone = form.cleaned_data['stock__passport__people__phone']
								source_email = form.cleaned_data['stock__passport__people__email']
								source_comments = form.cleaned_data['stock__passport__people__comments']

								new_taxonomy, created = Taxonomy.objects.get_or_create(genus=genus, species=species, population=population, common_name='Maize', alias='NULL', race='NULL', subtaxa='NULL')
								new_people, created = People.objects.get_or_create(first_name=source_fname, last_name=source_lname, organization=source_organization, phone=source_phone, email=source_email, comments=source_comments)
								new_collecting, created = Collecting.objects.get_or_create(user=collection_user, collection_date=collection_date, collection_method=collection_method, comments=collection_comments)
								new_passport, created = Passport.objects.get_or_create(collecting=new_collecting, taxonomy=new_taxonomy, people=new_people)
								new_stock, created = Stock.objects.get_or_create(seed_id=seed_id, defaults={'passport':new_passport, 'seed_name':seed_name, 'cross_type':cross_type, 'pedigree':pedigree, 'stock_status':stock_status, 'stock_date':stock_date, 'inoculated':inoculated, 'comments':stock_comments})
								if experiment_used == True:
									new_stock.stock_status = stock_status
									new_stock.save()

								if row_id != '':
									obs_row = ObsRow.objects.get(row_id=row_id)
								else:
									obs_row = ObsRow.objects.get(id=1)
								if plant_id != '':
									obs_plant = ObsPlant.objects.get(plant_id=plant_id)
								else:
									obs_plant = ObsPlant.objects.get(id=1)

								new_obs_tracker, created = ObsTracker.objects.get_or_create(obs_entity_type='stock', stock=new_stock, experiment_id=1, user=user, field=field, glycerol_stock_id=1, isolate_id=1, location_id=1, maize_sample_id=1, obs_culture_id=1, obs_dna_id=1, obs_env_id=1, obs_extract_id=1, obs_microbe_id=1, obs_plant=obs_plant, obs_plate_id=1, obs_row=obs_row, obs_sample_id=1, obs_tissue_id=1, obs_well_id=1)
								new_obs_tracker_exp, created = ObsTracker.objects.get_or_create(obs_entity_type='experiment', stock_id=1, experiment=experiment, user=user, field_id=1, glycerol_stock_id=1, isolate_id=1, location_id=1, maize_sample_id=1, obs_culture_id=1, obs_dna_id=1, obs_env_id=1, obs_extract_id=1, obs_microbe_id=1, obs_plant_id=1, obs_plate_id=1, obs_row_id=1, obs_sample_id=1, obs_tissue_id=1, obs_well_id=1)

								if experiment_used == True:
									new_obs_tracker_source, created = ObsTrackerSource.objects.get_or_create(source_obs=new_obs_tracker_exp, target_obs=new_obs_tracker, relationship='stock_used_in_experiment')
								if experiment_collected == True:
									new_obs_tracker_source, created = ObsTrackerSource.objects.get_or_create(source_obs=new_obs_tracker_exp, target_obs=new_obs_tracker, relationship='stock_from_experiment')
									if row_id != '':
										source_row, created = ObsTracker.objects.get_or_create(obs_entity_type='row', obs_row=obs_row)
										new_obs_tracker_source_row, created = ObsTrackerSource.objects.get_or_create(source_obs=source_row, target_obs=new_obs_tracker, relationship='stock_from_row')
									if plant_id != '':
										source_plant, created = ObsTracker.objects.get_or_create(obs_entity_type='plant', obs_plant=obs_plant)
										new_obs_tracker_source_plant, created = ObsTrackerSource.objects.get_or_create(source_obs=source_plant, target_obs=new_obs_tracker, relationship='stock_from_plant')
							except Exception as e:
								print("Error: %s %s" % (e.message, e.args))
								failed = True
					except KeyError:
						pass
			else:
				sent = False
				print(log_data_online_form_set.errors)
		else:
			sent = False
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'seed_packet':
		data_type_title = 'Inventory Seed Packets'
		LogDataOnlineFormSet = formset_factory(LogStockPacketOnlineForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				sent = True
				for form in log_data_online_form_set:
					try:
						form.cleaned_data['stock__seed_id']

						with transaction.atomic():
							try:
								seed_id = form.cleaned_data['stock__seed_id']
								weight = form.cleaned_data['weight']
								num_seeds = form.cleaned_data['num_seeds']
								packet_comments = form.cleaned_data['comments']
								locality = form.cleaned_data['location__locality']
								building_name = form.cleaned_data['location__building_name']
								location_name = form.cleaned_data['location__location_name']
								room = form.cleaned_data['location__room']
								shelf = form.cleaned_data['location__shelf']
								column = form.cleaned_data['location__column']
								box_name = form.cleaned_data['location__box_name']
								location_comments = form.cleaned_data['location__comments']

								new_location, created = Location.objects.get_or_create(locality=locality, building_name=building_name, location_name=location_name, room=room, shelf=shelf, column=column, box_name=box_name, comments=location_comments)
								new_stock_packet = StockPacket.objects.get_or_create(stock=Stock.objects.get(seed_id=seed_id), location=new_location, weight=weight, num_seeds=num_seeds, comments=packet_comments)
							except Exception as e:
								print("Error: %s %s" % (e.message, e.args))
								failed = True
					except KeyError:
						pass
			else:
				sent = False
				print(log_data_online_form_set.errors)
		else:
			sent = False
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'field':
		data_type_title = 'Add Field Info'
		LogDataOnlineFormSet = formset_factory(NewFieldForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				sent = True
				for form in log_data_online_form_set:
					try:
						locality = form.cleaned_data['locality']
						field_name = form.cleaned_data['field_name']
						field_num = form.cleaned_data['field_num']
						comments = form.cleaned_data['comments']

						try:
							new_field = Field.objects.get_or_create(locality=locality, field_name=field_name, field_num=field_num, comments=comments)
						except Exception as e:
							print("Error: %s %s" % (e.message, e.args))
							failed = True
					except KeyError:
						pass
			else:
				sent = False
				print(log_data_online_form_set.errors)
		else:
			sent = False
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'locality':
		data_type_title = 'Add Locality Info'
		LogDataOnlineFormSet = formset_factory(NewLocalityForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				sent = True
				for form in log_data_online_form_set:
					try:
						city = form.cleaned_data['city']
						state = form.cleaned_data['state']
						country = form.cleaned_data['country']
						zipcode = form.cleaned_data['zipcode']

						try:
							new_locality, created = Locality.objects.get_or_create(city=city, state=state, country=country, zipcode=zipcode)
						except Exception as e:
							print("Error: %s %s" % (e.message, e.args))
							failed = True
					except KeyError:
						pass
			else:
				sent = False
				print(log_data_online_form_set.errors)
		else:
			sent = False
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'primer':
		data_type_title = 'Add Primer Info'
		LogDataOnlineFormSet = formset_factory(NewPrimerForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				sent = True
				for form in log_data_online_form_set:
					try:
						primer_id = form.cleaned_data['primer_id']
						primer_name = form.cleaned_data['primer_name']
						primer_tail = form.cleaned_data['primer_tail']
						size_range = form.cleaned_data['size_range']
						temp_min = form.cleaned_data['temp_min']
						temp_max = form.cleaned_data['temp_max']
						order_date = form.cleaned_data['order_date']
						comments = form.cleaned_data['comments']

						try:
							new_primer, created = Primer.objects.get_or_create(primer_id=primer_id, primer_name=primer_name, primer_tail=primer_tail, size_range=size_range, temp_min=temp_min, temp_max=temp_max, order_date=order_date, comments=comments)
						except Exception as e:
							print("Error: %s %s" % (e.message, e.args))
							failed = True
					except KeyError:
						pass
			else:
				sent = False
				print(log_data_online_form_set.errors)
		else:
			sent = False
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'parameter':
		data_type_title = 'Add Measurement Parameter Info'
		LogDataOnlineFormSet = formset_factory(NewMeasurementParameterForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				sent = True
				for form in log_data_online_form_set:
					try:
						parameter = form.cleaned_data['parameter']
						parameter_type = form.cleaned_data['parameter_type']
						protocol = form.cleaned_data['protocol']
						trait_id_buckler = form.cleaned_data['trait_id_buckler']
						unit_of_measure = form.cleaned_data['unit_of_measure']

						try:
							new_parameter = MeasurementParameter.objects.get_or_create(parameter=parameter, parameter_type=parameter_type, protocol=protocol, trait_id_buckler=trait_id_buckler, unit_of_measure=unit_of_measure)
						except Exception as e:
							print("Error: %s %s" % (e.message, e.args))
							failed = True
					except KeyError:
						pass
			else:
				sent = False
				print(log_data_online_form_set.errors)
		else:
			sent = False
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'location':
		data_type_title = 'Add Location Info'
		LogDataOnlineFormSet = formset_factory(NewLocationForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				sent = True
				for form in log_data_online_form_set:
					try:
						locality = form.cleaned_data['locality']
						building_name = form.cleaned_data['building_name']
						location_name = form.cleaned_data['location_name']
						room = form.cleaned_data['room']
						shelf = form.cleaned_data['shelf']
						column = form.cleaned_data['column']
						box_name = form.cleaned_data['box_name']
						comments = form.cleaned_data['comments']

						try:
							new_location = Location.objects.get_or_create(locality=locality, building_name=building_name, location_name=location_name, room=room, shelf=shelf, column=column, box_name=box_name, comments=comments)
						except Exception as e:
							print("Error: %s %s" % (e.message, e.args))
							failed = True
					except KeyError:
						pass
			else:
				sent = False
				print(log_data_online_form_set.errors)
		else:
			sent = False
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'disease':
		data_type_title = 'Add Disease Info'
		LogDataOnlineFormSet = formset_factory(NewDiseaseInfoForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				sent = True
				for form in log_data_online_form_set:
					try:
						common_name = form.cleaned_data['common_name']
						abbrev = form.cleaned_data['abbrev']
						comments = form.cleaned_data['comments']

						try:
							new_disease = DiseaseInfo.objects.get_or_create(common_name=common_name, abbrev=abbrev, comments=comments)
						except Exception as e:
							print("Error: %s %s" % (e.message, e.args))
							failed = True
					except KeyError:
						pass
			else:
				sent = False
				print(log_data_online_form_set.errors)
		else:
			sent = False
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'medium':
		data_type_title = 'Add Medium Info'
		LogDataOnlineFormSet = formset_factory(NewMediumForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				sent = True
				for form in log_data_online_form_set:
					try:
						citation = form.cleaned_data['citation']
						media_name = form.cleaned_data['media_name']
						media_type = form.cleaned_data['media_type']
						media_description = form.cleaned_data['media_description']
						media_preparation = form.cleaned_data['media_preparation']
						comments = form.cleaned_data['comments']

						try:
							new_medium = Medium.objects.get_or_create(citation=citation, media_name=media_name, media_type=media_type, media_description=media_description, media_preparation=media_preparation, comments=comments)
						except Exception as e:
							print("Error: %s %s" % (e.message, e.args))
							failed = True
					except KeyError:
						pass
			else:
				sent = False
				print(log_data_online_form_set.errors)
		else:
			sent = False
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'citation':
		data_type_title = 'Add Citation Info'
		LogDataOnlineFormSet = formset_factory(NewCitationForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				sent = True
				for form in log_data_online_form_set:
					try:
						citation_type = form.cleaned_data['citation']
						title = form.cleaned_data['media_name']
						url = form.cleaned_data['media_type']
						pubmed_id = form.cleaned_data['media_description']
						comments = form.cleaned_data['comments']

						try:
							new_citation = Citation.objects.get_or_create(citation_type=citation_type, title=title, url=url, pubmed_id=pubmed_id, comments=comments)
						except Exception as e:
							print("Error: %s %s" % (e.message, e.args))
							failed = True
					except KeyError:
						pass
			else:
				sent = False
				print(log_data_online_form_set.errors)
		else:
			sent = False
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'plant':
		data_type_title = 'Load Plant Info'
		LogDataOnlineFormSet = formset_factory(LogPlantsOnlineForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				sent = True
				for form in log_data_online_form_set:
					try:
						experiment = form.cleaned_data['experiment']
						plant_id = form.cleaned_data['plant_id']
						plant_num = form.cleaned_data['plant_num']
						seed_id = form.cleaned_data['seed_id']
						row_id = form.cleaned_data['row_id']
						plant_comments = form.cleaned_data['plant_comments']
						user = request.user

						if row_id != '':
							try:
								obs_tracker = ObsTracker.objects.get(obs_entity_type='row', obs_row=ObsRow.objects.get(row_id=row_id))
								field_id = obs_tracker.field_id
								obs_row_id = obs_tracker.obs_row_id

							except Exception as e:
								obs_tracker = None
								field_id = 1
								obs_row_id = 1
								print("Error: %s %s" % (e.message, e.args))
								failed = True
						else:
							field_id = 1
							obs_row_id = 1
						try:
							new_obsplant, created = ObsPlant.objects.get_or_create(plant_id=plant_id, plant_num=plant_num, comments=plant_comments)
							new_obs_tracker, created = ObsTracker.objects.get_or_create(obs_entity_type='plant', stock=Stock.objects.get(seed_id=seed_id), experiment=1, user=user, field_id=field_id, glycerol_stock_id=1, isolate_id=1, location_id=1, maize_sample_id=1, obs_culture_id=1, obs_dna_id=1, obs_env_id=1, obs_extract_id=1, obs_microbe_id=1, obs_plant=new_obsplant, obs_plate_id=1, obs_row_id=obs_row_id, obs_sample_id=1, obs_tissue_id=1, obs_well_id=1)
							if row_id !='':
								new_source_row, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='row', obs_row__row_id=row_id), target_obs=new_obs_tracker, relationship="plant_from_row")
							if seed_id !='':
								new_source_stock, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='stock', stock__seed_id=seed_id), target_obs=new_obs_tracker, relationship="plant_from_stock")
							new_obs_tracker_exp, created = ObsTracker.objects.get_or_create(obs_entity_type='experiment', stock_id=1, experiment=experiment, user=user, field_id=1, glycerol_stock_id=1, isolate_id=1, location_id=1, maize_sample_id=1, obs_culture_id=1, obs_dna_id=1, obs_env_id=1, obs_extract_id=1, obs_microbe_id=1, obs_plant_id=1, obs_plate_id=1, obs_row_id=1, obs_sample_id=1, obs_tissue_id=1, obs_well_id=1)
							new_obs_tracker_source, created = ObsTrackerSource.objects.get_or_create(source_obs=new_obs_tracker_exp, target_obs=new_obs_tracker, relationship='plant_used_in_experiment')
						except Exception as e:
							print("Error: %s %s" % (e.message, e.args))
							failed = True
					except KeyError:
						pass
			else:
				sent = False
				print(log_data_online_form_set.errors)
		else:
			sent = False
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'row':
		data_type_title = 'Load Row Info'
		LogDataOnlineFormSet = formset_factory(LogRowsOnlineForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				sent = True
				for form in log_data_online_form_set:
					try:
						experiment = form.cleaned_data['experiment']
						row_id = form.cleaned_data['row_id']
						row_name = form.cleaned_data['row_name']
						seed_id = form.cleaned_data['seed_id']
						field = form.cleaned_data['field']
						range_num = form.cleaned_data['range_num']
						plot = form.cleaned_data['plot']
						block = form.cleaned_data['block']
						rep = form.cleaned_data['rep']
						kernel_num = form.cleaned_data['kernel_num']
						planting_date = form.cleaned_data['planting_date']
						harvest_date = form.cleaned_data['harvest_date']
						row_comments = form.cleaned_data['row_comments']
						user = request.user

						if seed_id == '':
							seed_id = 'No Stock'

						try:
							new_obsrow, created = ObsRow.objects.get_or_create(row_id=row_id, row_name=row_name, range_num=range_num, plot=plot, block=block, rep=rep, kernel_num=kernel_num, planting_date=planting_date, harvest_date=harvest_date, comments=row_comments)
							new_obs_tracker, created = ObsTracker.objects.get_or_create(obs_entity_type='row', stock=Stock.objects.get(seed_id=seed_id), experiment=1, user=user, field=field, glycerol_stock_id=1, isolate_id=1, location_id=1, maize_sample_id=1, obs_culture_id=1, obs_dna_id=1, obs_env_id=1, obs_extract_id=1, obs_microbe_id=1, obs_plant_id=1, obs_plate_id=1, obs_row=new_obsrow, obs_sample_id=1, obs_tissue_id=1, obs_well_id=1)
							if seed_id !='' and seed_id !='No Stock':
								new_source_stock, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='stock', stock__seed_id=seed_id), target_obs=new_obs_tracker, relationship="row_from_stock")
							new_obs_tracker_exp, created = ObsTracker.objects.get_or_create(obs_entity_type='experiment', stock_id=1, experiment=experiment, user=user, field_id=1, glycerol_stock_id=1, isolate_id=1, location_id=1, maize_sample_id=1, obs_culture_id=1, obs_dna_id=1, obs_env_id=1, obs_extract_id=1, obs_microbe_id=1, obs_plant_id=1, obs_plate_id=1, obs_row_id=1, obs_sample_id=1, obs_tissue_id=1, obs_well_id=1)
							new_obs_tracker_source, created = ObsTrackerSource.objects.get_or_create(source_obs=new_obs_tracker_exp, target_obs=new_obs_tracker, relationship='row_used_in_experiment')
						except Exception as e:
							print("Error: %s %s" % (e.message, e.args))
							failed = True
					except KeyError:
						pass
			else:
				sent = False
				print(log_data_online_form_set.errors)
		else:
			sent = False
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'environment':
		data_type_title = 'Load Environment Info'
		LogDataOnlineFormSet = formset_factory(LogEnvironmentsOnlineForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				sent = True
				for form in log_data_online_form_set:
					try:
						experiment = form.cleaned_data['experiment']
						environment_id = form.cleaned_data['environment_id']
						field = form.cleaned_data['field']
						longitude = form.cleaned_data['longitude']
						latitude = form.cleaned_data['latitude']
						environment_comments = form.cleaned_data['environment_comments']
						user = request.user

						try:
							new_obsenv, created = ObsEnv.objects.get_or_create(environment_id=environment_id, longitude=longitude, latitude=latitude, comments=environment_comments)
							new_obs_tracker, created = ObsTracker.objects.get_or_create(obs_entity_type='environment', stock_id=1, experiment=1, user=user, field=field, glycerol_stock_id=1, isolate_id=1, location_id=1, maize_sample_id=1, obs_culture_id=1, obs_dna_id=1, obs_env=new_obsenv, obs_extract_id=1, obs_microbe_id=1, obs_plant_id=1, obs_plate_id=1, obs_row_id=1, obs_sample_id=1, obs_tissue_id=1, obs_well_id=1)
							new_obs_tracker_exp, created = ObsTracker.objects.get_or_create(obs_entity_type='experiment', stock_id=1, experiment=experiment, user=user, field_id=1, glycerol_stock_id=1, isolate_id=1, location_id=1, maize_sample_id=1, obs_culture_id=1, obs_dna_id=1, obs_env_id=1, obs_extract_id=1, obs_microbe_id=1, obs_plant_id=1, obs_plate_id=1, obs_row_id=1, obs_sample_id=1, obs_tissue_id=1, obs_well_id=1)
							new_obs_tracker_source, created = ObsTrackerSource.objects.get_or_create(source_obs=new_obs_tracker_exp, target_obs=new_obs_tracker, relationship='env_used_in_experiment')
						except Exception as e:
							print("Error: %s %s" % (e.message, e.args))
							failed = True
					except KeyError:
						pass
			else:
				sent = False
				print(log_data_online_form_set.errors)
		else:
			sent = False
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'sample':
		data_type_title = 'Load Samples Info'
		LogDataOnlineFormSet = formset_factory(LogSamplesOnlineForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				sent = True
				for form in log_data_online_form_set:
					try:
						experiment = form.cleaned_data['experiment']
						sample_id = form.cleaned_data['obs_sample__sample_id']
						sample_type = form.cleaned_data['obs_sample__sample_type']
						sample_name = form.cleaned_data['obs_sample__sample_name']
						source_seed_id = form.cleaned_data['stock__seed_id']
						source_row_id = form.cleaned_data['obs_row__row_id']
						source_plant_id = form.cleaned_data['obs_plant__plant_id']
						source_sample_id = form.cleaned_data['source_sample_id']
						weight = form.cleaned_data['obs_sample__weight']
						volume = form.cleaned_data['obs_sample__volume']
						density = form.cleaned_data['obs_sample__density']
						kernel_num = form.cleaned_data['obs_sample__kernel_num']
						photo = form.cleaned_data['obs_sample__photo']
						sample_comments = form.cleaned_data['obs_sample__comments']
						user = request.user

						if source_row_id == '':
							source_row_id = 'No Row'
						if source_plant_id == '':
							source_plant_id = 'No Plant'
						if source_seed_id == '':
							source_seed_id = 'No Stock'
						if source_sample_id == '':
							source_sample_id = 'No Sample'

						try:
							new_obssample, created = ObsSample.objects.get_or_create(sample_id=sample_id, sample_type=sample_type, sample_name=sample_name, weight=weight, volume=volume, density=density, kernel_num=kernel_num, photo=photo, comments=sample_comments)
							new_obs_tracker, new_obs_tracker_created = ObsTracker.objects.get_or_create(obs_entity_type='sample', stock=Stock.objects.get(seed_id=source_seed_id), experiment=1, user=user, field_id=1, glycerol_stock_id=1, isolate_id=1, location_id=1, maize_sample_id=1, obs_culture_id=1, obs_dna_id=1, obs_env_id=1, obs_extract_id=1, obs_microbe_id=1, obs_plant=ObsPlant.objects.get(plant_id=source_plant_id), obs_plate_id=1, obs_row=ObsRow.objects.get(row_id=source_row_id), obs_sample=new_obssample, obs_tissue_id=1, obs_well_id=1)
							if source_sample_id !='' and source_sample_id !='No Sample':
								new_source_sample, created = ObsTrackerSource.objects.get_or_create(source_obs=ObsTracker.objects.get(obs_entity_type='sample', obs_sample__sample_id=source_sample_id), target_obs=new_obs_tracker, relationship='sample_from_sample')
							if source_row_id !='' and source_row_id != 'No Row':
								new_source_row, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='row', obs_row__row_id=source_row_id), target_obs=new_obs_tracker, relationship="sample_from_row")
							if source_plant_id !='' and source_plant_id != 'No Plant':
								new_source_plant, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='plant', obs_plant__plant_id=source_plant_id), target_obs=new_obs_tracker, relationship="sample_from_plant")
							if source_seed_id !='' and source_seed_id != 'No Stock':
								new_source_stock, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='stock', stock__seed_id=source_seed_id), target_obs=new_obs_tracker, relationship="sample_from_stock")
							new_obs_tracker_exp, created = ObsTracker.objects.get_or_create(obs_entity_type='experiment', stock_id=1, experiment=experiment, user=user, field_id=1, glycerol_stock_id=1, isolate_id=1, location_id=1, maize_sample_id=1, obs_culture_id=1, obs_dna_id=1, obs_env_id=1, obs_extract_id=1, obs_microbe_id=1, obs_plant_id=1, obs_plate_id=1, obs_row_id=1, obs_sample_id=1, obs_tissue_id=1, obs_well_id=1)
							new_obs_tracker_source, created = ObsTrackerSource.objects.get_or_create(source_obs=new_obs_tracker_exp, target_obs=new_obs_tracker, relationship='sample_used_in_experiment')
						except Exception as e:
							print("Error: %s %s" % (e.message, e.args))
							failed = True
					except KeyError:
						pass
			else:
				sent = False
				print(log_data_online_form_set.errors)
		else:
			sent = False
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'tissue':
		data_type_title = 'Load Tissue Info'
		LogDataOnlineFormSet = formset_factory(LogTissuesOnlineForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				sent = True
				for form in log_data_online_form_set:
					try:
						experiment = form.cleaned_data['experiment']
						tissue_id = form.cleaned_data['tissue_id']
						row_id = form.cleaned_data['row_id']
						seed_id = form.cleaned_data['seed_id']
						plant_id = form.cleaned_data['plant_id']
						culture_id = form.cleaned_data['culture_id']
						tissue_name = form.cleaned_data['tissue_name']
						tissue_type = form.cleaned_data['tissue_type']
						date_ground = form.cleaned_data['date_ground']
						tissue_comments = form.cleaned_data['tissue_comments']
						user = request.user

						if row_id == '':
							row_id = 'No Row'
						if plant_id == '':
							plant_id = 'No Plant'
						if seed_id == '':
							seed_id = 'No Stock'
						if culture_id == '':
							culture_id = 'No Culture'

						try:
							new_obstissue, created = ObsTissue.objects.get_or_create(tissue_id=tissue_id, tissue_name=tissue_name, tissue_type=tissue_type, date_ground=date_ground, comments=tissue_comments)
							new_obs_tracker, created = ObsTracker.objects.get_or_create(obs_entity_type='tissue', stock=Stock.objects.get(seed_id=seed_id), experiment=1, user=user, field_id=1, glycerol_stock_id=1, isolate_id=1, location_id=1, maize_sample_id=1, obs_culture=ObsCulture.objects.get(culture_id=culture_id), obs_dna_id=1, obs_env_id=1, obs_extract_id=1, obs_microbe_id=1, obs_plant=ObsPlant.objects.get(plant_id=plant_id), obs_plate_id=1, obs_row=ObsRow.objects.get(row_id=row_id), obs_sample_id=1, obs_tissue=new_obstissue, obs_well_id=1)
							if row_id !='' and row_id !='No Row':
								new_source_row, created = ObsTrackerSource.objects.get_or_create(source_obs=ObsTracker.objects.get(obs_entity_type='row', obs_row__row_id=row_id), target_obs=new_obs_tracker, relationship='tissue_from_row')
							if culture_id !='' and culture_id !='No Culture':
								new_source_culture, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='culture', obs_culture__culture_id=culture_id), target_obs=new_obs_tracker, relationship="tissue_from_culture")
							if plant_id !='' and plant_id != 'No Plant':
								new_source_plant, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='plant', obs_plant__plant_id=plant_id), target_obs=new_obs_tracker, relationship="tissue_from_plant")
							if seed_id !='' and seed_id != 'No Stock':
								new_source_stock, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='stock', stock__seed_id=seed_id), target_obs=new_obs_tracker, relationship="tissue_from_stock")
							new_obs_tracker_exp, created = ObsTracker.objects.get_or_create(obs_entity_type='experiment', stock_id=1, experiment=experiment, user=user, field_id=1, glycerol_stock_id=1, isolate_id=1, location_id=1, maize_sample_id=1, obs_culture_id=1, obs_dna_id=1, obs_env_id=1, obs_extract_id=1, obs_microbe_id=1, obs_plant_id=1, obs_plate_id=1, obs_row_id=1, obs_sample_id=1, obs_tissue_id=1, obs_well_id=1)
							new_obs_tracker_source, created = ObsTrackerSource.objects.get_or_create(source_obs=new_obs_tracker_exp, target_obs=new_obs_tracker, relationship='tissue_used_in_experiment')
						except Exception as e:
							print("Error: %s %s" % (e.message, e.args))
							failed = True
					except KeyError:
						pass
			else:
				sent = False
				print(log_data_online_form_set.errors)
		else:
			sent = False
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'culture':
		data_type_title = 'Load Culture Info'
		LogDataOnlineFormSet = formset_factory(LogCulturesOnlineForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				sent = True
				for form in log_data_online_form_set:
					try:
						experiment = form.cleaned_data['experiment']
						culture_id = form.cleaned_data['culture_id']
						medium = form.cleaned_data['medium']
						row_id = form.cleaned_data['row_id']
						plant_id = form.cleaned_data['plant_id']
						seed_id = form.cleaned_data['seed_id']
						tissue_id = form.cleaned_data['tissue_id']
						microbe_id = form.cleaned_data['microbe_id']
						culture_name = form.cleaned_data['culture_name']
						microbe_type = form.cleaned_data['microbe_type']
						plating_cycle = form.cleaned_data['plating_cycle']
						dilution = form.cleaned_data['dilution']
						num_colonies = form.cleaned_data['num_colonies']
						num_microbes = form.cleaned_data['num_microbes']
						image = form.cleaned_data['image']
						culture_comments = form.cleaned_data['culture_comments']
						user = request.user

						if row_id == '':
							row_id = 'No Row'
						if plant_id == '':
							plant_id = 'No Plant'
						if seed_id == '':
							seed_id = 'No Stock'
						if tissue_id == '':
							tissue_id = 'No Tissue'
						if microbe_id == '':
							microbe_id = 'No Microbe'

						try:
							new_obsculture, created = ObsCulture.objects.get_or_create(medium=medium, culture_id=culture_id, culture_name=culture_name, microbe_type=microbe_type, plating_cycle=plating_cycle, dilution=dilution, image_filename=image, num_colonies=num_colonies, num_microbes=num_microbes, comments=tissue_comments)
							new_obs_tracker, created = ObsTracker.objects.get_or_create(obs_entity_type='culture', stock=Stock.objects.get(seed_id=seed_id), experiment=1, user=user, field_id=1, glycerol_stock_id=1, isolate_id=1, location_id=1, maize_sample_id=1, obs_culture=new_obsculture, obs_dna_id=1, obs_env_id=1, obs_extract_id=1, obs_microbe=ObsMicrobe.objects.get(microbe_id=microbe_id), obs_plant=ObsPlant.objects.get(plant_id=plant_id), obs_plate_id=1, obs_row=ObsRow.objects.get(row_id=row_id), obs_sample=new_obssample, obs_tissue=ObsTissue.objects.get(tissue_id=tissue_id), obs_well_id=1)
							if row_id !='' and row_id !='No Row':
								new_source_row, created = ObsTrackerSource.objects.get_or_create(source_obs=ObsTracker.objects.get(obs_entity_type='row', obs_row__row_id=row_id), target_obs=new_obs_tracker, relationship='culture_from_row')
							if tissue_id !='' and tissue_id !='No Tissue':
								new_source_tissue, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='tissue', obs_tissue__tissue_id=tissue_id), target_obs=new_obs_tracker, relationship="culture_from_tissue")
							if plant_id !='' and plant_id !='No Plant':
								new_source_plant, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='plant', obs_plant__plant_id=plant_id), target_obs=new_obs_tracker, relationship="culture_from_plant")
							if seed_id !='' and seed_id !='No Stock':
								new_source_stock, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='stock', stock__seed_id=seed_id), target_obs=new_obs_tracker, relationship="culture_from_stock")
							if microbe_id !='' and microbe_id !='No Microbe':
								new_source_microbe, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='microbe', obs_microbe__microbe_id=microbe_id), target_obs=new_obs_tracker, relationship="culture_from_microbe")
							new_obs_tracker_exp, created = ObsTracker.objects.get_or_create(obs_entity_type='experiment', stock_id=1, experiment=experiment, user=user, field_id=1, glycerol_stock_id=1, isolate_id=1, location_id=1, maize_sample_id=1, obs_culture_id=1, obs_dna_id=1, obs_env_id=1, obs_extract_id=1, obs_microbe_id=1, obs_plant_id=1, obs_plate_id=1, obs_row_id=1, obs_sample_id=1, obs_tissue_id=1, obs_well_id=1)
							new_obs_tracker_source, created = ObsTrackerSource.objects.get_or_create(source_obs=new_obs_tracker_exp, target_obs=new_obs_tracker, relationship='culture_used_in_experiment')
						except Exception as e:
							print("Error: %s %s" % (e.message, e.args))
							failed = True
					except KeyError:
						pass
			else:
				sent = False
				print(log_data_online_form_set.errors)
		else:
			sent = False
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'microbe':
		data_type_title = 'Load Microbe Info'
		LogDataOnlineFormSet = formset_factory(LogMicrobesOnlineForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				sent = True
				for form in log_data_online_form_set:
					try:
						experiment = form.cleaned_data['experiment']
						microbe_id = form.cleaned_data['microbe_id']
						row_id = form.cleaned_data['row_id']
						plant_id = form.cleaned_data['plant_id']
						seed_id = form.cleaned_data['seed_id']
						tissue_id = form.cleaned_data['tissue_id']
						culture_id = form.cleaned_data['culture_id']
						microbe_type = form.cleaned_data['microbe_type']
						microbe_comments = form.cleaned_data['microbe_comments']
						user = request.user

						if row_id == '':
							row_id = 'No Row'
						if plant_id == '':
							plant_id = 'No Plant'
						if seed_id == '':
							seed_id = 'No Stock'
						if tissue_id == '':
							tissue_id = 'No Tissue'
						if culture_id == '':
							culture_id = 'No Culture'

						try:
							new_obsmicrobe, created = ObsMicrobe.objects.get_or_create(microbe_id=microbe_id, microbe_type=microbe_type, comments=microbe_comments)
							new_obs_tracker, created = ObsTracker.objects.get_or_create(obs_entity_type='microbe', stock=Stock.objects.get(seed_id=seed_id), experiment=1, user=user, field_id=1, glycerol_stock_id=1, isolate_id=1, location_id=1, maize_sample_id=1, obs_culture=ObsCulture.objects.get(culture_id=culture_id), obs_dna_id=1, obs_env_id=1, obs_extract_id=1, obs_microbe=new_obsmicrobe, obs_plant=ObsPlant.objects.get(plant_id=plant_id), obs_plate_id=1, obs_row=ObsRow.objects.get(row_id=row_id), obs_sample=new_obssample, obs_tissue=ObsTissue.objects.get(tissue_id=tissue_id), obs_well_id=1)
							if row_id !='' and row_id !='No Row':
								new_source_row, created = ObsTrackerSource.objects.get_or_create(source_obs=ObsTracker.objects.get(obs_entity_type='row', obs_row__row_id=row_id), target_obs=new_obs_tracker, relationship='microbe_from_row')
							if tissue_id !='' and tissue_id !='No Tissue':
								new_source_tissue, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='tissue', obs_tissue__tissue_id=tissue_id), target_obs=new_obs_tracker, relationship="microbe_from_tissue")
							if plant_id !='' and plant_id !='No Plant':
								new_source_plant, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='plant', obs_plant__plant_id=plant_id), target_obs=new_obs_tracker, relationship="microbe_from_plant")
							if seed_id !='' and seed_id !='No Stock':
								new_source_stock, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='stock', stock__seed_id=seed_id), target_obs=new_obs_tracker, relationship="microbe_from_stock")
							if culture_id !='' and culture_id !='No Culture':
								new_source_culture, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='culture', obs_culture__culture_id=culture_id), target_obs=new_obs_tracker, relationship="microbe_from_culture")
							new_obs_tracker_exp, created = ObsTracker.objects.get_or_create(obs_entity_type='experiment', stock_id=1, experiment=experiment, user=user, field_id=1, glycerol_stock_id=1, isolate_id=1, location_id=1, maize_sample_id=1, obs_culture_id=1, obs_dna_id=1, obs_env_id=1, obs_extract_id=1, obs_microbe_id=1, obs_plant_id=1, obs_plate_id=1, obs_row_id=1, obs_sample_id=1, obs_tissue_id=1, obs_well_id=1)
							new_obs_tracker_source, created = ObsTrackerSource.objects.get_or_create(source_obs=new_obs_tracker_exp, target_obs=new_obs_tracker, relationship='microbe_used_in_experiment')
						except Exception as e:
							print("Error: %s %s" % (e.message, e.args))
							failed = True
					except KeyError:
						pass
			else:
				sent = False
				print(log_data_online_form_set.errors)
		else:
			sent = False
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'dna':
		data_type_title = 'Load DNA Info'
		LogDataOnlineFormSet = formset_factory(LogDNAOnlineForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				sent = True
				for form in log_data_online_form_set:
					try:
						experiment = form.cleaned_data['experiment']
						dna_id = form.cleaned_data['dna_id']
						microbe_id = form.cleaned_data['microbe_id']
						row_id = form.cleaned_data['row_id']
						plant_id = form.cleaned_data['plant_id']
						seed_id = form.cleaned_data['seed_id']
						tissue_id = form.cleaned_data['tissue_id']
						culture_id = form.cleaned_data['culture_id']
						plate_id = form.cleaned_data['plate_id']
						well_id = form.cleaned_data['well_id']
						sample_id = form.cleaned_data['sample_id']
						extraction = form.cleaned_data['extraction']
						date = form.cleaned_data['date']
						tube_id = form.cleaned_data['tube_id']
						tube_type = form.cleaned_data['tube_type']
						dna_comments = form.cleaned_data['dna_comments']
						user = request.user

						if row_id == '':
							row_id = 'No Row'
						if plant_id == '':
							plant_id = 'No Plant'
						if seed_id == '':
							seed_id = 'No Stock'
						if tissue_id == '':
							tissue_id = 'No Tissue'
						if culture_id == '':
							culture_id = 'No Culture'
						if microbe_id == '':
							microbe_id = 'No Microbe'
						if plate_id == '':
							plate_id = 'No Plate'
						if well_id == '':
							well_id = 'No Well'
						if sample_id == '':
							sample_id = 'No Sample'

						try:
							new_obsdna, created = ObsDNA.objects.get_or_create(dna_id=dna_id, extraction_method=extraction, date=date, tube_id=tube_id, tube_type=tube_type, comments=dna_comments)
							new_obs_tracker, created = ObsTracker.objects.get_or_create(obs_entity_type='dna', stock=Stock.objects.get(seed_id=seed_id), experiment=1, user=user, field_id=1, glycerol_stock_id=1, isolate_id=1, location_id=1, maize_sample_id=1, obs_culture=ObsCulture.objects.get(culture_id=culture_id), obs_dna=new_obsdna, obs_env_id=1, obs_extract_id=1, obs_microbe=ObsMicrobe.objects.get(microbe_id=microbe_id), obs_plant=ObsPlant.objects.get(plant_id=plant_id), obs_plate=ObsPlate.objects.get(plate_id=plate_id), obs_row=ObsRow.objects.get(row_id=row_id), obs_sample=ObsSample.objects.get(sample_id=sample_id), obs_tissue=ObsTissue.objects.get(tissue_id=tissue_id), obs_well=ObsWell.objects.get(well_id=well_id))
							if row_id !='' and row_id != 'No Row':
								new_source_row, created = ObsTrackerSource.objects.get_or_create(source_obs=ObsTracker.objects.get(obs_entity_type='row', obs_row__row_id=row_id), target_obs=new_obs_tracker, relationship='dna_from_row')
							if tissue_id !='' and tissue_id != 'No Tissue':
								new_source_tissue, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='tissue', obs_tissue__tissue_id=tissue_id), target_obs=new_obs_tracker, relationship="dna_from_tissue")
							if plant_id !='' and plant_id != 'No Plant':
								new_source_plant, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='plant', obs_plant__plant_id=plant_id), target_obs=new_obs_tracker, relationship="dna_from_plant")
							if seed_id !='' and seed_id != 'No Stock':
								new_source_stock, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='stock', stock__seed_id=seed_id), target_obs=new_obs_tracker, relationship="dna_from_stock")
							if culture_id !='' and culture_id != 'No Culture':
								new_source_culture, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='culture', obs_culture__culture_id=culture_id), target_obs=new_obs_tracker, relationship="dna_from_culture")
							if microbe_id !='' and microbe_id !='No Microbe':
								new_source_microbe, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='microbe', obs_microbe__microbe_id=microbe_id), target_obs=new_obs_tracker, relationship="dna_from_microbe")
							if plate_id !='' and plate_id != 'No Plate':
								new_source_plate, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='plate', obs_plate__plate_id=plate_id), target_obs=new_obs_tracker, relationship="dna_in_plate")
							if well_id !='' and well_id !='No Well':
								new_source_well, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='well', obs_well__well_id=well_id), target_obs=new_obs_tracker, relationship="dna_in_well")
							if sample_id !='' and sample_id != 'No Sample':
								new_source_sample, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='sample', obs_sample__sample_id=sample_id), target_obs=new_obs_tracker, relationship="dna_from_sample")
							new_obs_tracker_exp, created = ObsTracker.objects.get_or_create(obs_entity_type='experiment', stock_id=1, experiment=experiment, user=user, field_id=1, glycerol_stock_id=1, isolate_id=1, location_id=1, maize_sample_id=1, obs_culture_id=1, obs_dna_id=1, obs_env_id=1, obs_extract_id=1, obs_microbe_id=1, obs_plant_id=1, obs_plate_id=1, obs_row_id=1, obs_sample_id=1, obs_tissue_id=1, obs_well_id=1)
							new_obs_tracker_source, created = ObsTrackerSource.objects.get_or_create(source_obs=new_obs_tracker_exp, target_obs=new_obs_tracker, relationship='dna_used_in_experiment')
						except Exception as e:
							print("Error: %s %s" % (e.message, e.args))
							failed = True
					except KeyError:
						pass
			else:
				sent = False
				print(log_data_online_form_set.errors)
		else:
			sent = False
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'plate':
		data_type_title = 'Load Plate Info'
		LogDataOnlineFormSet = formset_factory(LogPlatesOnlineForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				sent = True
				for form in log_data_online_form_set:
					try:
						experiment = form.cleaned_data['experiment']
						plate_id = form.cleaned_data['plate_id']
						location = form.cleaned_data['location']
						plate_name = form.cleaned_data['plate_name']
						date = form.cleaned_data['date']
						contents = form.cleaned_data['contents']
						rep = form.cleaned_data['rep']
						plate_type = form.cleaned_data['plate_type']
						plate_status = form.cleaned_data['plate_status']
						plate_comments = form.cleaned_data['plate_comments']
						user = request.user

						try:
							new_obsplate, created = ObsPlate.objects.get_or_create(plate_id=plate_id, plate_name=plate_name, date=date, contents=contents, rep=rep, plate_type=plate_type, plate_status=plate_status, comments=plate_comments)
							new_obs_tracker, created = ObsTracker.objects.get_or_create(obs_entity_type='plate', stock_id=1, experiment=1, user=user, field_id=1, glycerol_stock_id=1, isolate_id=1, location_id=1, maize_sample_id=1, obs_culture_id=1, obs_dna_id=1, obs_env_id=1, obs_extract_id=1, obs_microbe_id=1, obs_plant_id=1, obs_plate=new_obsplate, obs_row_id=1, obs_sample_id=1, obs_tissue_id=1, obs_well_id=1)
							new_obs_tracker_exp, created = ObsTracker.objects.get_or_create(obs_entity_type='experiment', stock_id=1, experiment=experiment, user=user, field_id=1, glycerol_stock_id=1, isolate_id=1, location_id=1, maize_sample_id=1, obs_culture_id=1, obs_dna_id=1, obs_env_id=1, obs_extract_id=1, obs_microbe_id=1, obs_plant_id=1, obs_plate_id=1, obs_row_id=1, obs_sample_id=1, obs_tissue_id=1, obs_well_id=1)
							new_obs_tracker_source, created = ObsTrackerSource.objects.get_or_create(source_obs=new_obs_tracker_exp, target_obs=new_obs_tracker, relationship='plate_used_in_experiment')
						except Exception as e:
							print("Error: %s %s" % (e.message, e.args))
							failed = True
					except KeyError:
						pass
			else:
				sent = False
				print(log_data_online_form_set.errors)
		else:
			sent = False
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'well':
		data_type_title = 'Load Well Info'
		LogDataOnlineFormSet = formset_factory(LogWellOnlineForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				sent = True
				for form in log_data_online_form_set:
					try:
						experiment = form.cleaned_data['experiment']
						well_id = form.cleaned_data['well_id']
						microbe_id = form.cleaned_data['microbe_id']
						row_id = form.cleaned_data['row_id']
						plant_id = form.cleaned_data['plant_id']
						seed_id = form.cleaned_data['seed_id']
						tissue_id = form.cleaned_data['tissue_id']
						culture_id = form.cleaned_data['culture_id']
						plate_id = form.cleaned_data['plate_id']
						well = form.cleaned_data['well']
						inventory = form.cleaned_data['extraction']
						tube_label = form.cleaned_data['date']
						well_comments = form.cleaned_data['dna_comments']
						user = request.user

						if row_id == '':
							row_id = 'No Row'
						if plant_id == '':
							plant_id = 'No Plant'
						if seed_id == '':
							seed_id = 'No Stock'
						if tissue_id == '':
							tissue_id = 'No Tissue'
						if culture_id == '':
							culture_id = 'No Culture'
						if microbe_id == '':
							microbe_id = 'No Microbe'
						if plate_id == '':
							plate_id = 'No Plate'

						try:
							new_obswell, created = ObsWell.objects.get_or_create(well_id=well_id, well=well, date=date, well_inventory=inventory, tube_label=tube_label, comments=well_comments)
							new_obs_tracker, created = ObsTracker.objects.get_or_create(obs_entity_type='well', stock=Stock.objects.get(seed_id=seed_id), experiment=1, user=user, field_id=1, glycerol_stock_id=1, isolate_id=1, location_id=1, maize_sample_id=1, obs_culture=ObsCulture.objects.get(culture_id=culture_id), obs_dna=new_obsdna, obs_env_id=1, obs_extract_id=1, obs_microbe=ObsMicrobe.objects.get(microbe_id=microbe_id), obs_plant=ObsPlant.objects.get(plant_id=plant_id), obs_plate=ObsPlate.objects.get(plate_id=plate_id), obs_row=ObsRow.objects.get(row_id=row_id), obs_sample_id=1, obs_tissue=ObsTissue.objects.get(tissue_id=tissue_id), obs_well=new_obswell)
							if row_id !='' and row_id != 'No Row':
								new_source_row, created = ObsTrackerSource.objects.get_or_create(source_obs= ObsTracker.objects.get(obs_entity_type='row', obs_row__row_id=row_id), target_obs=new_obs_tracker, relationship='row_in_well')
							if tissue_id !='' and tissue_id != 'No Tissue':
								new_source_tissue, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='tissue', obs_tissue__tissue_id=tissue_id), target_obs=new_obs_tracker, relationship="tissue_in_well")
							if plant_id !='' and plant_id != 'No Plant':
								new_source_plant, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='plant', obs_plant__plant_id=plant_id), target_obs=new_obs_tracker, relationship="plant_in_well")
							if seed_id !='' and seed_id != 'No Stock':
								new_source_stock, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='stock', stock__seed_id=seed_id), target_obs=new_obs_tracker, relationship="stock_in_well")
							if culture_id !='' and culture_id != 'No Culture':
								new_source_culture, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='culture', obs_culture__culture_id=culture_id), target_obs=new_obs_tracker, relationship="culture_in_well")
							if microbe_id !='' and microbe_id != 'No Microbe':
								new_source_microbe, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='microbe', obs_microbe__microbe_id=microbe_id), target_obs=new_obs_tracker, relationship="microbe_in_well")
							if plate_id !='' and plate_id != 'No Plate':
								new_source_plate, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='plate', obs_plate__plate_id=plate_id), target_obs=new_obs_tracker, relationship="well_in_plate")
							new_obs_tracker_exp, created = ObsTracker.objects.get_or_create(obs_entity_type='experiment', stock_id=1, experiment=experiment, user=user, field_id=1, glycerol_stock_id=1, isolate_id=1, location_id=1, maize_sample_id=1, obs_culture_id=1, obs_dna_id=1, obs_env_id=1, obs_extract_id=1, obs_microbe_id=1, obs_plant_id=1, obs_plate_id=1, obs_row_id=1, obs_sample_id=1, obs_tissue_id=1, obs_well_id=1)
							new_obs_tracker_source, created = ObsTrackerSource.objects.get_or_create(source_obs=new_obs_tracker_exp, target_obs=new_obs_tracker, relationship='well_used_in_experiment')

						except Exception as e:
							print("Error: %s %s" % (e.message, e.args))
							failed = True
					except KeyError:
						pass
			else:
				sent = False
				print(log_data_online_form_set.errors)
		else:
			sent = False
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'separation':
		data_type_title = 'Load Separation Info'
		LogDataOnlineFormSet = formset_factory(LogSeparationsOnlineForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				sent = True
				for form in log_data_online_form_set:
					try:
						sample_id = form.cleaned_data['sample_id']
						sample_name = form.cleaned_data['sample_name']
						separation_type = form.cleaned_data['separation_type']
						apparatus = form.cleaned_data['apparatus']
						sg = form.cleaned_data['sg']
						light_weight = form.cleaned_data['light_weight']
						medium_weight = form.cleaned_data['medium_weight']
						heavy_weight = form.cleaned_data['heavy_weight']
						light_percent = form.cleaned_data['light_percent']
						medium_percent = form.cleaned_data['medium_percent']
						heavy_percent = form.cleaned_data['heavy_percent']
						operating_factor = form.cleaned_data['operating_factor']
						separation_comments = form.cleaned_data['separation_comments']

						try:
							new_separation, created = Separation.objects.get_or_create(obs_sample=ObsSample.objects.get(sample_id=sample_id), separation_type=separation_type, apparatus=apparatus, SG=sg, light_weight=light_weight, intermediate_weight=medium_weight, heavy_weight=heavy_weight, light_percent=light_percent, intermediate_percent=medium_percent, heavy_percent=heavy_percent, operating_factor=operating_factor, comments=separation_comments)
						except Exception as e:
							print("Error: %s %s" % (e.message, e.args))
							failed = True
					except KeyError:
						pass
			else:
				sent = False
				print(log_data_online_form_set.errors)
		else:
			sent = False
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'maize':
		data_type_title = 'Load Maize Survey Data'
		LogDataOnlineFormSet = formset_factory(LogMaizeSurveyOnlineForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				sent = True
				for form in log_data_online_form_set:
					try:
						experiment = form.cleaned_data['experiment']
						maize_id = form.cleaned_data['maize_id']
						county = form.cleaned_data['county']
						sub_location = form.cleaned_data['sub_location']
						village = form.cleaned_data['village']
						weight = form.cleaned_data['weight']
						harvest_date = form.cleaned_data['harvest_date']
						storage_months = form.cleaned_data['storage_months']
						storage_conditions = form.cleaned_data['storage_conditions']
						maize_variety = form.cleaned_data['maize_variety']
						seed_source = form.cleaned_data['seed_source']
						moisture_content = form.cleaned_data['moisture_content']
						source_type = form.cleaned_data['source_type']
						appearance = form.cleaned_data['appearance']
						gps_latitude = form.cleaned_data['gps_latitude']
						gps_longitude = form.cleaned_data['gps_longitude']
						gps_altitude = form.cleaned_data['gps_altitude']
						gps_accuracy = form.cleaned_data['gps_accuracy']
						photo = form.cleaned_data['photo']
						user = request.user

						try:
							new_maize_sample, created = MaizeSample.objects.get_or_create(maize_id=maize_id, county=county, sub_location=sub_location, village=village, weight=weight, harvest_date=harvest_date, storage_months=storage_months, storage_conditions=storage_conditions, maize_variety=maize_variety, seed_source=seed_source, moisture_content=moisture_content, source_type=source_type, appearance=appearance, gps_latitude=gps_latitude, gps_longitude=gps_longitude, gps_altitude=gps_altitude, gps_accuracy=gps_accuracy, photo=photo)
							new_obs_tracker, created = ObsTracker.objects.get_or_create(obs_entity_type='maize', stock_id=1, experiment=1, user=user, field_id=1, glycerol_stock_id=1, isolate_id=1, location_id=1, maize_sample=new_maize_sample, obs_culture_id=1, obs_dna_id=1, obs_env_id=1, obs_extract_id=1, obs_microbe_id=1, obs_plant_id=1, obs_plate_id=1, obs_row_id=1, obs_sample_id=1, obs_tissue_id=1, obs_well_id=1)
							new_obs_tracker_exp, created = ObsTracker.objects.get_or_create(obs_entity_type='experiment', stock_id=1, experiment=experiment, user=user, field_id=1, glycerol_stock_id=1, isolate_id=1, location_id=1, maize_sample_id=1, obs_culture_id=1, obs_dna_id=1, obs_env_id=1, obs_extract_id=1, obs_microbe_id=1, obs_plant_id=1, obs_plate_id=1, obs_row_id=1, obs_sample_id=1, obs_tissue_id=1, obs_well_id=1)
							new_obs_tracker_source, created = ObsTrackerSource.objects.get_or_create(source_obs=new_obs_tracker_exp, target_obs=new_obs_tracker, relationship='maize_used_in_experiment')
						except Exception as e:
							print("Error: %s %s" % (e.message, e.args))
							failed = True
					except KeyError:
						pass
			else:
				sent = False
				print(log_data_online_form_set.errors)
		else:
			sent = False
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'isolate':
		data_type_title = 'Load Isolate Info'
		LogDataOnlineFormSet = formset_factory(LogIsolatesOnlineForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				sent = True
				for form in log_data_online_form_set:
					try:
						experiment = form.cleaned_data['experiment']
						isolate_id = form.cleaned_data['isolate__isolate_id']
						location = form.cleaned_data['location']
						field = form.cleaned_data['field']
						dna_id = form.cleaned_data['obs_dna__dna_id']
						microbe_id = form.cleaned_data['obs_microbe__microbe_id']
						row_id = form.cleaned_data['obs_row__row_id']
						plant_id = form.cleaned_data['obs_plant__plant_id']
						seed_id = form.cleaned_data['stock__seed_id']
						tissue_id = form.cleaned_data['obs_tissue__tissue_id']
						culture_id = form.cleaned_data['obs_culture__culture_id']
						plate_id = form.cleaned_data['obs_plate__plate_id']
						well_id = form.cleaned_data['obs_well__well_id']
						isolate_name = form.cleaned_data['isolate__isolate_name']
						disease = form.cleaned_data['isolate__disease_info']
						plant_organ = form.cleaned_data['isolate__plant_organ']
						genus = form.cleaned_data['isolate__passport__taxonomy__genus']
						alias = form.cleaned_data['isolate__passport__taxonomy__alias']
						race = form.cleaned_data['isolate__passport__taxonomy__race']
						subtaxa = form.cleaned_data['isolate__passport__taxonomy__subtaxa']
						isolate_comments = form.cleaned_data['isolate__comments']
						user = request.user

						if row_id == '':
							row_id = 'No Row'
						if dna_id == '':
							dna_id = 'No DNA'
						if plant_id == '':
							plant_id = 'No Plant'
						if seed_id == '':
							seed_id = 'No Stock'
						if tissue_id == '':
							tissue_id = 'No Tissue'
						if culture_id == '':
							culture_id = 'No Culture'
						if microbe_id == '':
							microbe_id = 'No Microbe'
						if plate_id == '':
							plate_id = 'No Plate'
						if well_id == '':
							well_id = 'No Well'

						try:
							new_taxonomy, created = Taxonomy.objects.get_or_create(genus=genus, common_name='Isolate', alias=alias, race=race, subtaxa=subtaxa)
							new_passport, created = Passport.objects.get_or_create(taxonomy=new_taxonomy, people_id=1, collecting_id=1)
							new_isolate, created = Isolate.objects.get_or_create(passport=new_passport, location=location, disease_info=disease, isolate_id=isolate_id, isolate_name=isolate_name, plant_organ=plant_organ, comments=isolate_comments)
							new_obs_tracker, created = ObsTracker.objects.get_or_create(obs_entity_type='isolate', stock=Stock.objects.get(seed_id=seed_id), experiment=experiment, user=user, field=field, glycerol_stock_id=1, isolate=new_isolate, location=location, maize_sample_id=1, obs_culture=ObsCulture.objects.get(culture_id=culture_id), obs_dna=ObsDNA.objects.get(dna_id=dna_id), obs_env_id=1, obs_extract_id=1, obs_microbe=ObsMicrobe.objects.get(microbe_id=microbe_id), obs_plant=ObsPlant.objects.get(plant_id=plant_id), obs_plate=ObsPlate.objects.get(plate_id=plate_id), obs_row=ObsRow.objects.get(row_id=row_id), obs_sample_id=1, obs_tissue=ObsTissue.objects.get(tissue_id=tissue_id), obs_well=ObsWell.objects.get(well_id=well_id))
							if row_id !='' and row_id !='No Row':
								new_source_row, created = ObsTrackerSource.objects.get_or_create(source_obs=ObsTracker.objects.get(obs_entity_type='row', obs_row__row_id=row_id), target_obs=new_obs_tracker, relationship='isolate_from_row')
							if tissue_id !='' and tissue_id != 'No Tissue':
								new_source_tissue, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='tissue', obs_tissue__tissue_id=tissue_id), target_obs=new_obs_tracker, relationship="isolate_from_tissue")
							if plant_id !='' and plant_id != 'No Plant':
								new_source_plant, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='plant', obs_plant__plant_id=plant_id), target_obs=new_obs_tracker, relationship="isolate_from_plant")
							if seed_id !='' and seed_id != 'No Stock':
								new_source_stock, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='stock', stock__seed_id=seed_id), target_obs=new_obs_tracker, relationship="isolate_from_stock")
							if culture_id !='' and culture_id != 'No Culture':
								new_source_culture, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='culture', obs_culture__culture_id=culture_id), target_obs=new_obs_tracker, relationship="isolate_from_culture")
							if microbe_id !='' and microbe_id != 'No Microbe':
								new_source_microbe, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='microbe', obs_microbe__microbe_id=microbe_id), target_obs=new_obs_tracker, relationship="isolate_from_microbe")
							if plate_id !='' and plate_id != 'No Plate':
								new_source_plate, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='plate', obs_plate__plate_id=plate_id), target_obs=new_obs_tracker, relationship="isolate_from_plate")
							if well_id !='' and well_id != 'No Well':
								new_source_well, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='well', obs_well__well_id=well_id), target_obs=new_obs_tracker, relationship="isolate_from_well")
							if dna_id !='' and dna_id !='No DNA':
								new_source_dna, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='dna', obs_dna__dna_id=dna_id), target_obs=new_obs_tracker, relationship="isolate_from_dna")
							new_obs_tracker_exp, created = ObsTracker.objects.get_or_create(obs_entity_type='experiment', stock_id=1, experiment=experiment, user=user, field_id=1, glycerol_stock_id=1, isolate_id=1, location_id=1, maize_sample_id=1, obs_culture_id=1, obs_dna_id=1, obs_env_id=1, obs_extract_id=1, obs_microbe_id=1, obs_plant_id=1, obs_plate_id=1, obs_row_id=1, obs_sample_id=1, obs_tissue_id=1, obs_well_id=1)
							new_obs_tracker_source, created = ObsTrackerSource.objects.get_or_create(source_obs=new_obs_tracker_exp, target_obs=new_obs_tracker, relationship='isolate_used_in_experiment')
						except Exception as e:
							print("Error: %s %s" % (e.message, e.args))
							failed = True
					except KeyError:
						pass
			else:
				sent = False
				print(log_data_online_form_set.errors)
		else:
			sent = False
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'glycerol_stock':
		data_type_title = 'Load Isolate Stock Info'
		LogDataOnlineFormSet = formset_factory(LogGlycerolStocksOnlineForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				sent = True
				for form in log_data_online_form_set:
					try:
						experiment = form.cleaned_data['experiment']
						glycerol_stock_id = form.cleaned_data['glycerol_stock__glycerol_stock_id']
						location = form.cleaned_data['location']
						stock_date = form.cleaned_data['glycerol_stock__date']
						extract_color = form.cleaned_data['glycerol_stock__extract_color']
						organism = form.cleaned_data['glycerol_stock__organism']
						glycerol_stock_comments = form.cleaned_data['glycerol_stock__comments']
						field = form.cleaned_data['field']
						culture_id = form.cleaned_data['obs_culture__culture_id']
						dna_id = form.cleaned_data['obs_dna__dna_id']
						plate_id = form.cleaned_data['obs_plate__plate_id']
						row_id = form.cleaned_data['obs_row__row_id']
						plant_id = form.cleaned_data['obs_plant__plant_id']
						tissue_id = form.cleaned_data['obs_tissue__tissue_id']
						seed_id = form.cleaned_data['stock__seed_id']
						sample_id = form.cleaned_data['obs_sample__sample_id']
						well_id = form.cleaned_data['obs_well__well_id']
						microbe_id = form.cleaned_data['obs_microbe__microbe_id']
						isolate_id = form.cleaned_data['isolate__isolate_id']
						user = request.user

						if row_id == '':
							row_id = 'No Row'
						if dna_id == '':
							dna_id = 'No DNA'
						if plant_id == '':
							plant_id = 'No Plant'
						if seed_id == '':
							seed_id = 'No Stock'
						if tissue_id == '':
							tissue_id = 'No Tissue'
						if culture_id == '':
							culture_id = 'No Culture'
						if microbe_id == '':
							microbe_id = 'No Microbe'
						if plate_id == '':
							plate_id = 'No Plate'
						if well_id == '':
							well_id = 'No Well'
						if sample_id == '':
							sample_id = 'No Sample'
						if isolate_id == '':
							isolate_id = 'No Isolate'

						try:
							new_glycerol_stock, created = GlycerolStock.objects.get_or_create(glycerol_stock_id=glycerol_stock_id, stock_date=stock_date, extract_color=extract_color, organism=organism, comments=glycerol_stock_comments)
							new_obs_tracker, created = ObsTracker.objects.get_or_create(obs_entity_type='glycerol_stock', stock=Stock.objects.get(seed_id=seed_id), experiment=1, user=user, field=field, glycerol_stock=new_glycerol_stock, isolate=Isolate.objects.get(isolate_id=isolate_id), location=location, maize_sample_id=1, obs_culture=ObsCulture.objects.get(culture_id=culture_id), obs_dna=ObsDNA.objects.get(dna_id=dna_id), obs_env_id=1, obs_extract_id=1, obs_microbe=ObsMicrobe.objects.get(microbe_id=microbe_id), obs_plant=ObsPlant.objects.get(plant_id=plant_id), obs_plate=ObsPlate.objects.get(plate_id=plate_id), obs_row=ObsRow.objects.get(row_id=row_id), obs_sample=ObsSample.objects.get(sample_id=sample_id), obs_tissue=ObsTissue.objects.get(tissue_id=tissue_id), obs_well=ObsWell.objects.get(well_id=well_id))
							if row_id !='' and row_id != 'No Row':
								new_source_row, created = ObsTrackerSource.objects.get_or_create(source_obs=ObsTracker.objects.get(obs_entity_type='row', obs_row__row_id=row_id), target_obs=new_obs_tracker, relationship='isolate_stock_from_row')
							if tissue_id !='' and tissue_id !='No Tissue':
								new_source_tissue, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='tissue', obs_tissue__tissue_id=tissue_id), target_obs=new_obs_tracker, relationship="isolate_stock_from_tissue")
							if plant_id !='' and plant_id !='No Plant':
								new_source_plant, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='plant', obs_plant__plant_id=plant_id), target_obs=new_obs_tracker, relationship="isolate_stock_from_plant")
							if seed_id !='' and seed_id != 'No Stock':
								new_source_stock, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='stock', stock__seed_id=seed_id), target_obs=new_obs_tracker, relationship="isolate_stock_from_stock")
							if culture_id !='' and culture_id !='No Culture':
								new_source_culture, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='culture', obs_culture__culture_id=culture_id), target_obs=new_obs_tracker, relationship="isolate_stock_from_culture")
							if microbe_id !='' and microbe_id != 'No Microbe':
								new_source_microbe, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='microbe', obs_microbe__microbe_id=microbe_id), target_obs=new_obs_tracker, relationship="isolate_stock_from_microbe")
							if plate_id !='' and plate_id !='No Plate':
								new_source_plate, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='plate', obs_plate__plate_id=plate_id), target_obs=new_obs_tracker, relationship="isolate_stock_from_plate")
							if well_id !='' and well_id != 'No Well':
								new_source_well, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='well', obs_well__well_id=well_id), target_obs=new_obs_tracker, relationship="isolate_stock_from_well")
							if dna_id !='' and dna_id !='No DNA':
								new_source_dna, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='dna', obs_dna__dna_id=dna_id), target_obs=new_obs_tracker, relationship="isolate_stock_from_dna")
							if sample_id !='' and sample_id !='No Sample':
								new_source_sample, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='sample', obs_sample__sample_id=sample_id), target_obs=new_obs_tracker, relationship="isolate_stock_from_sample")
							if isolate_id !='' and isolate_id !='No Isolate':
								new_source_isolate, created = ObsTrackerSource.objects.get_or_create(source_obs = ObsTracker.objects.get(obs_entity_type='isolate', isolate__isolate_id=isolate_id), target_obs=new_obs_tracker, relationship="isolate_stock_from_isolate")
							new_obs_tracker_exp, created = ObsTracker.objects.get_or_create(obs_entity_type='experiment', stock_id=1, experiment=experiment, user=user, field_id=1, glycerol_stock_id=1, isolate_id=1, location_id=1, maize_sample_id=1, obs_culture_id=1, obs_dna_id=1, obs_env_id=1, obs_extract_id=1, obs_microbe_id=1, obs_plant_id=1, obs_plate_id=1, obs_row_id=1, obs_sample_id=1, obs_tissue_id=1, obs_well_id=1)
							new_obs_tracker_source, created = ObsTrackerSource.objects.get_or_create(source_obs=new_obs_tracker_exp, target_obs=new_obs_tracker, relationship='isolate_stock_from_experiment')
						except Exception as e:
							print("Error: %s %s" % (e.message, e.args))
							failed = True
					except KeyError:
						pass
			else:
				sent = False
				print(log_data_online_form_set.errors)
		else:
			sent = False
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'measurement':
		data_type_title = 'Load Measurements'
		LogDataOnlineFormSet = formset_factory(LogMeasurementsOnlineForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				sent = True
				for form in log_data_online_form_set:
					try:
						observation_id = form.cleaned_data['observation_id']
						measurement_parameter = form.cleaned_data['measurement_parameter']
						user = form.cleaned_data['user']
						time_of_measurement = form.cleaned_data['time_of_measurement']
						value = form.cleaned_data['value']
						measurement_comments = form.cleaned_data['measurement_comments']
						try:
							obs_unit = ObsRow.objects.get(row_id=observation_id)
							obs_tracker = ObsTracker.objects.get(obs_entity_type='row', obs_row=obs_unit)
							obs_tracker_found = True
						except (ObsRow.DoesNotExist, ObsTracker.DoesNotExist):
							pass
						try:
							obs_unit = ObsPlant.objects.get(plant_id=observation_id)
							obs_tracker = ObsTracker.objects.get(obs_entity_type='plant', obs_plant=obs_unit)
							obs_tracker_found = True
						except (ObsPlant.DoesNotExist, ObsTracker.DoesNotExist):
							pass
						try:
							obs_unit = ObsSample.objects.get(sample_id=observation_id)
							obs_tracker = ObsTracker.objects.get(obs_entity_type='sample', obs_sample=obs_unit)
							obs_tracker_found = True
						except (ObsSample.DoesNotExist, ObsTracker.DoesNotExist):
							pass
						try:
							obs_unit = ObsCulture.objects.get(culture_id=observation_id)
							obs_tracker = ObsTracker.objects.get(obs_entity_type='culture', obs_culture=obs_unit)
							obs_tracker_found = True
						except (ObsCulture.DoesNotExist, ObsTracker.DoesNotExist):
							pass
						try:
							obs_unit = ObsDNA.objects.get(dna_id=observation_id)
							obs_tracker = ObsTracker.objects.get(obs_entity_type='dna', obs_dna=obs_unit)
							obs_tracker_found = True
						except (ObsDNA.DoesNotExist, ObsTracker.DoesNotExist):
							pass
						try:
							obs_unit = ObsEnv.objects.get(environment_id=observation_id)
							obs_tracker = ObsTracker.objects.get(obs_entity_type='environment', obs_env=obs_unit)
							obs_tracker_found = True
						except (ObsEnv.DoesNotExist, ObsTracker.DoesNotExist):
							pass
						try:
							obs_unit = ObsExtract.objects.get(extract_id=observation_id)
							obs_tracker = ObsTracker.objects.get(obs_entity_type='extract', obs_extract=obs_unit)
							obs_tracker_found = True
						except (ObsExtract.DoesNotExist, ObsTracker.DoesNotExist):
							pass
						try:
							obs_unit = ObsMicrobe.objects.get(microbe_id=observation_id)
							obs_tracker = ObsTracker.objects.get(obs_entity_type='microbe', obs_microbe=obs_unit)
							obs_tracker_found = True
						except (ObsMicrobe.DoesNotExist, ObsTracker.DoesNotExist):
							pass
						try:
							obs_unit = ObsPlate.objects.get(plate_id=observation_id)
							obs_tracker = ObsTracker.objects.get(obs_entity_type='plate', obs_plate=obs_unit)
							obs_tracker_found = True
						except (ObsPlate.DoesNotExist, ObsTracker.DoesNotExist):
							pass
						try:
							obs_unit = ObsTissue.objects.get(tissue_id=observation_id)
							obs_tracker = ObsTracker.objects.get(obs_entity_type='tissue', obs_tissue=obs_unit)
							obs_tracker_found = True
						except (ObsTissue.DoesNotExist, ObsTracker.DoesNotExist):
							pass
						try:
							obs_unit = ObsWell.objects.get(well_id=observation_id)
							obs_tracker = ObsTracker.objects.get(obs_entity_type='well', obs_well=obs_unit)
							obs_tracker_found = True
						except (ObsWell.DoesNotExist, ObsTracker.DoesNotExist):
							pass
						try:
							obs_unit = GlycerolStock.objects.get(glycerol_stock_id=observation_id)
							obs_tracker = ObsTracker.objects.get(obs_entity_type='glycerol_stock', glycerol_stock=obs_unit)
							obs_tracker_found = True
						except (GlycerolStock.DoesNotExist, ObsTracker.DoesNotExist):
							pass
						try:
							obs_unit = Stock.objects.get(seed_id=observation_id)
							obs_tracker = ObsTracker.objects.get(obs_entity_type='stock', stock=obs_unit)
							obs_tracker_found = True
						except (Stock.DoesNotExist, ObsTracker.DoesNotExist):
							pass

						if obs_tracker_found == True:
							try:
								new_measurement, created = Measurement.objects.get_or_create(obs_tracker=obs_tracker, measurement_parameter=measurement_parameter, user=user, time_of_measurement=time_of_measurement, value=value, comments=measurement_comments)
							except Exception as e:
								print("Error: %s %s" % (e.message, e.args))
								failed = True
						else:
							failed = True
					except KeyError:
						pass
			else:
				sent = False
				print(log_data_online_form_set.errors)
		else:
			sent = False
			log_data_online_form_set = LogDataOnlineFormSet

	context_dict['log_data_online_form_set'] = log_data_online_form_set
	context_dict['data_type'] = data_type
	context_dict['failed'] = failed
	context_dict['sent'] = sent
	context_dict['data_type_title'] = data_type_title
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/log_data_online.html', context=context_dict)

@login_required
def new_treatment(request):
	context_dict = {}
	if request.method == 'POST':
		new_treatment_form = NewTreatmentForm(data=request.POST)
		if new_treatment_form.is_valid():
			new_treatment_exp = new_treatment_form.cleaned_data['experiment']
			new_treatment_id = new_treatment_form.cleaned_data['treatment_id']
			new_treatment_type = new_treatment_form.cleaned_data['treatment_type']
			new_treatment_date = new_treatment_form.cleaned_data['date']
			new_treatment_comments = new_treatment_form.cleaned_data['comments']
			new_treatment = Treatment.objects.get_or_create(experiment=new_treatment_exp, treatment_id=new_treatment_id, treatment_type=new_treatment_type, date=new_treatment_date, comments=new_treatment_comments)

			treatment_added = True
		else:
			print(new_treatment_form.errors)
			treatment_added = False
	else:
		new_treatment_form = NewTreatmentForm()
		treatment_added = False
	context_dict['new_treatment_form'] = new_treatment_form
	context_dict['treatment_added'] = treatment_added
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/new_treatment.html', context=context_dict)

def site_map(request):
	context_dict = {}

	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/site_map.html', context=context_dict)

@login_required
def queue_upload_file(request, data_type):
	context_dict = {}
	if request.method == 'POST':
		upload_form = UploadQueueForm(request.POST, request.FILES)
		if upload_form.is_valid():
			new_upload_exp = upload_form.cleaned_data['experiment']
			new_upload_user = upload_form.cleaned_data['user']
			new_upload_filename = upload_form.cleaned_data['file_name']
			new_upload_comments = upload_form.cleaned_data['comments']

			new_upload = UploadQueue.objects.get_or_create(experiment=new_upload_exp, user=new_upload_user, file_name=new_upload_filename, upload_type=data_type, comments=new_upload_comments)

			upload_added = True
		else:
			print(upload_form.errors)
			upload_added = False
	else:
		upload_form = UploadQueueForm()
		upload_added = False
	context_dict['upload_form'] = upload_form
	context_dict['upload_added'] = upload_added
	context_dict['data_type'] = data_type
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/new_upload.html', context=context_dict)

@login_required
def seed_id_search(request):
	context_dict = {}
	seed_id_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET['suggestion']
	else:
		starts_with = request.POST['suggestion']
	if starts_with:
		seed_id_list = Stock.objects.filter(seed_id__contains=starts_with)[:2000]
	else:
		seed_id_list = None
	context_dict = checkbox_session_variable_check(request)
	context_dict['seed_id_list'] = seed_id_list
	return render(request, 'lab/seed_id_search_list.html', context=context_dict)

def sidebar_search_page(request):
	starts_with = request.POST.get("sidebarsearch", "")
	context_dict = {}
	experiment_results = []
	row_results = []
	isolate_results = []
	glycerol_results = []
	plant_results = []
	plate_results = []
	culture_results = []
	microbe_results = []
	extract_results = []
	dna_results = []
	sample_results = []
	tissue_results = []
	env_results = []
	well_results = []
	maize_results = []
	field_results = []
	user_results = []
	locality_results = []
	people_results = []
	stock_results = []
	try:
		experiment_results = Experiment.objects.filter(name__icontains=starts_with).exclude(name='No Experiment')
	except Experiment.DoesNotExist:
		experiment_results = None
	for result in experiment_results:
		result.url = "/lab/experiment/%s/" % (result.name)
	try:
		row_results = ObsRow.objects.filter(row_id__icontains=starts_with).exclude(row_id='No Row')
	except ObsRow.DoesNotExist:
		row_results = None
	for result in row_results:
		result.url = "/lab/row/%d/" % (result.id)
	try:
		isolate_results = Isolate.objects.filter(isolate_id__icontains=starts_with).exclude(isolate_id='No Isolate')
	except Isolate.DoesNotExist:
		isolate_results = None
	for result in isolate_results:
		result.url = "/lab/isolate/%d/" % (result.id)
	try:
		glycerol_results = GlycerolStock.objects.filter(glycerol_stock_id__icontains=starts_with)
	except GlycerolStock.DoesNotExist:
		glycerol_results = None
	for result in glycerol_results:
		result.url = "/lab/glycerol_stock/%d/" % (result.id)
	try:
		plant_results = ObsPlant.objects.filter(plant_id__icontains=starts_with).exclude(plant_id='No Plant')
	except ObsPlant.DoesNotExist:
		plant_results = None
	for result in plant_results:
		result.url = "/lab/plant/%d/" % (result.id)
	try:
		plate_results = ObsPlate.objects.filter(plate_id__icontains=starts_with).exclude(plate_id='No Plate')
	except ObsPlate.DoesNotExist:
		plate_results = None
	for result in plate_results:
		result.url = "/lab/plate/%d/" % (result.id)
	try:
		culture_results = ObsCulture.objects.filter(culture_id__icontains=starts_with).exclude(culture_id='No Culture')
	except ObsCulture.DoesNotExist:
		culture_results = None
	for result in culture_results:
		result.url = "/lab/culture/%d/" % (result.id)
	try:
		microbe_results = ObsMicrobe.objects.filter(microbe_id__icontains=starts_with).exclude(microbe_id='No Microbe')
	except ObsMicrobe.DoesNotExist:
		microbe_results = None
	for result in microbe_results:
		result.url = "/lab/microbe/%d/" % (result.id)
	try:
		extract_results = ObsExtract.objects.filter(extract_id__icontains=starts_with).exclude(extract_id='No Extract')
	except ObsExtract.DoesNotExist:
		extract_results = None
	for result in extract_results:
		result.url = "/lab/extract/%d/" % (result.id)
	try:
		dna_results = ObsDNA.objects.filter(dna_id__icontains=starts_with).exclude(dna_id='No DNA')
	except ObsDNA.DoesNotExist:
		dna_results = None
	for result in dna_results:
		result.url = "/lab/dna/%d/" % (result.id)
	try:
		sample_results = ObsSample.objects.filter(sample_id__icontains=starts_with).exclude(sample_id='No Sample')
	except ObsSample.DoesNotExist:
		sample_results = None
	for result in sample_results:
		result.url = "/lab/sample/%d/" % (result.id)
	try:
		tissue_results = ObsTissue.objects.filter(tissue_id__icontains=starts_with).exclude(tissue_id='No Tissue')
	except ObsTissue.DoesNotExist:
		tissue_results = None
	for result in tissue_results:
		result.url = "/lab/tissue/%d/" % (result.id)
	try:
		env_results = ObsEnv.objects.filter(environment_id__icontains=starts_with).exclude(environment_id='No Environment')
	except ObsEnv.DoesNotExist:
		env_results = None
	for result in env_results:
		result.url = "/lab/env/%d/" % (result.id)
	try:
		well_results = ObsWell.objects.filter(well_id__icontains=starts_with).exclude(well_id='No Well')
	except ObsWell.DoesNotExist:
		well_results = None
	for result in well_results:
		result.url = "/lab/well/%d/" % (result.id)
	try:
		maize_results = MaizeSample.objects.filter(maize_id__icontains=starts_with).exclude(maize_id='No Maize ID')
	except MaizeSample.DoesNotExist:
		maize_results = None
	for result in maize_results:
		result.url = "/lab/maize/%d/" % (result.id)
	try:
		field_results = Field.objects.filter(field_name__icontains=starts_with).exclude(field_name='No Field')
	except Field.DoesNotExist:
		field_results = None
	for result in field_results:
		result.url = "/lab/field/%d/" % (result.id)
	try:
		user_results = User.objects.filter(username__icontains=starts_with)
	except User.DoesNotExist:
		user_results = None
	for result in user_results:
		result.url = "/lab/profile/%s/" % (result.username)
	try:
		locality_results = Locality.objects.filter(city__icontains=starts_with)
	except Locality.DoesNotExist:
		locality_results = None
	for result in locality_results:
		result.url = "/lab/locality/%d/" % (result.id)
	try:
		people_results = People.objects.filter(first_name__icontains=starts_with)
	except People.DoesNotExist:
		people_results = None
	for result in people_results:
		result.url = "/lab/people/%d/" % (result.id)
	try:
		stock_results = Stock.objects.filter(seed_id__icontains=starts_with).exclude(seed_id='No Stock')
	except Stock.DoesNotExist:
		stock_results = None
	for result in stock_results:
		result.url = "/lab/stock/%d/" % (result.id)

	context_dict['starts_with'] = starts_with
	context_dict['experiment_results'] = experiment_results
	context_dict['row_results'] = row_results
	context_dict['isolate_results'] = isolate_results
	context_dict['glycerol_results'] = glycerol_results
	context_dict['plant_results'] = plant_results
	context_dict['plate_results'] = plate_results
	context_dict['culture_results'] = culture_results
	context_dict['microbe_results'] = microbe_results
	context_dict['extract_results'] = extract_results
	context_dict['dna_results'] = dna_results
	context_dict['sample_results'] = sample_results
	context_dict['tissue_results'] = tissue_results
	context_dict['env_results'] = env_results
	context_dict['well_results'] = well_results
	context_dict['maize_results'] = maize_results
	context_dict['field_results'] = field_results
	context_dict['user_results'] = user_results
	context_dict['locality_results'] = locality_results
	context_dict['people_results'] = people_results
	context_dict['stock_results'] = stock_results
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/sidebar_search_page.html', context=context_dict)

def sidebar_search(request):
	context_dict = {}
	results_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET['suggestion']
	else:
		starts_with = request.POST['suggestion']
	if starts_with:
		try:
			experiment_results = Experiment.objects.filter(name__contains=starts_with).exclude(name='No Experiment')[:10]
		except Experiment.DoesNotExist:
			experiment_results = None
		for result in experiment_results:
			result.url = "/lab/experiment/%s/" % (result.name)
		try:
			row_results = ObsRow.objects.filter(row_id__contains=starts_with).exclude(row_id='No Row')[:10]
		except ObsRow.DoesNotExist:
			row_results = None
		for result in row_results:
			result.url = "/lab/row/%d/" % (result.id)
		try:
			isolate_results = Isolate.objects.filter(isolate_id__contains=starts_with).exclude(isolate_id='No Isolate')[:10]
		except Isolate.DoesNotExist:
			isolate_results = None
		for result in isolate_results:
			result.url = "/lab/isolate/%d/" % (result.id)
		try:
			glycerol_results = GlycerolStock.objects.filter(glycerol_stock_id__contains=starts_with)[:10]
		except GlycerolStock.DoesNotExist:
			glycerol_results = None
		for result in glycerol_results:
			result.url = "/lab/glycerol_stock/%d/" % (result.id)
		try:
			plant_results = ObsPlant.objects.filter(plant_id__contains=starts_with).exclude(plant_id='No Plant')[:10]
		except ObsPlant.DoesNotExist:
			plant_results = None
		for result in plant_results:
			result.url = "/lab/plant/%d/" % (result.id)
		try:
			plate_results = ObsPlate.objects.filter(plate_id__contains=starts_with).exclude(plate_id='No Plate')[:10]
		except ObsPlate.DoesNotExist:
			plate_results = None
		for result in plate_results:
			result.url = "/lab/plate/%d/" % (result.id)
		try:
			culture_results = ObsCulture.objects.filter(culture_id__contains=starts_with).exclude(culture_id='No Culture')[:10]
		except ObsCulture.DoesNotExist:
			culture_results = None
		for result in culture_results:
			result.url = "/lab/culture/%d/" % (result.id)
		try:
			microbe_results = ObsMicrobe.objects.filter(microbe_id__contains=starts_with).exclude(microbe_id='No Microbe')[:10]
		except ObsMicrobe.DoesNotExist:
			microbe_results = None
		for result in microbe_results:
			result.url = "/lab/microbe/%d/" % (result.id)
		try:
			extract_results = ObsExtract.objects.filter(extract_id__contains=starts_with).exclude(extract_id='No Extract')[:10]
		except ObsExtract.DoesNotExist:
			extract_results = None
		for result in extract_results:
			result.url = "/lab/extract/%d/" % (result.id)
		try:
			dna_results = ObsDNA.objects.filter(dna_id__contains=starts_with).exclude(dna_id='No DNA')[:10]
		except ObsDNA.DoesNotExist:
			dna_results = None
		for result in dna_results:
			result.url = "/lab/dna/%d/" % (result.id)
		try:
			sample_results = ObsSample.objects.filter(sample_id__contains=starts_with).exclude(sample_id='No Sample')[:10]
		except ObsSample.DoesNotExist:
			sample_results = None
		for result in sample_results:
			result.url = "/lab/sample/%d/" % (result.id)
		try:
			tissue_results = ObsTissue.objects.filter(tissue_id__contains=starts_with).exclude(tissue_id='No Tissue')[:10]
		except ObsTissue.DoesNotExist:
			tissue_results = None
		for result in tissue_results:
			result.url = "/lab/tissue/%d/" % (result.id)
		try:
			env_results = ObsEnv.objects.filter(environment_id__contains=starts_with).exclude(environment_id='No Environment')[:10]
		except ObsEnv.DoesNotExist:
			env_results = None
		for result in env_results:
			result.url = "/lab/env/%d/" % (result.id)
		try:
			well_results = ObsWell.objects.filter(well_id__contains=starts_with).exclude(well_id='No Well')[:10]
		except ObsWell.DoesNotExist:
			well_results = None
		for result in well_results:
			result.url = "/lab/well/%d/" % (result.id)
		try:
			maize_results = MaizeSample.objects.filter(maize_id__contains=starts_with).exclude(maize_id='No Maize ID')[:10]
		except MaizeSample.DoesNotExist:
			maize_results = None
		for result in maize_results:
			result.url = "/lab/maize/%d/" % (result.id)
		try:
			field_results = Field.objects.filter(field_name__contains=starts_with).exclude(field_name='No Field')[:10]
		except Field.DoesNotExist:
			field_results = None
		for result in field_results:
			result.url = "/lab/field/%d/" % (result.id)
		try:
			user_results = User.objects.filter(username__contains=starts_with)[:10]
		except User.DoesNotExist:
			user_results = None
		for result in user_results:
			result.url = "/lab/profile/%s/" % (result.username)
		try:
			locality_results = Locality.objects.filter(city__contains=starts_with)[:10]
		except Locality.DoesNotExist:
			locality_results = None
		for result in locality_results:
			result.url = "/lab/locality/%d/" % (result.id)
		try:
			people_results = People.objects.filter(first_name__contains=starts_with)[:10]
		except People.DoesNotExist:
			people_results = None
		for result in people_results:
			result.url = "/lab/people/%d/" % (result.id)
		try:
			stock_results = Stock.objects.filter(seed_id__contains=starts_with).exclude(seed_id='No Stock')[:10]
		except Stock.DoesNotExist:
			stock_results = None
		for result in stock_results:
			result.url = "/lab/stock/%d/" % (result.id)

		results_list = list(chain(experiment_results, user_results, row_results, stock_results, isolate_results, glycerol_results, plant_results, plate_results, culture_results, microbe_results, extract_results, dna_results, sample_results, tissue_results, env_results, well_results, maize_results, field_results, locality_results, people_results))[:10]

	else:
		results_list = None
	context_dict = checkbox_session_variable_check(request)
	context_dict['results_list'] = results_list
	return render(request, 'lab/sidebar_search_results_list.html', context=context_dict)

@login_required
def mycotoxin_templates(request):
	context_dict = {}

	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/mycotoxin_templates.html', context=context_dict)

@login_required
def query_builder(request):
	context_dict = {}

	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/query_builder.html', context=context_dict)

@login_required
def query_builder_options(request):
	context_dict = {}
	query_builder_fields_list = {}
	selected_options = []
	if request.POST.getlist('checkbox_qbo', False):
		selected_options = request.POST.getlist('checkbox_qbo')
	else:
		selected_options = None

	obs_entity_type = request.POST['obs_entity_type']

	if 'Measurement' in selected_options:
		measurement_fields_list = [('measurement_time', "<select name='qb_measurement_time_choice'><option value='' >None</option><option value='time_of_measurement'>Ascending</option><option value='-time_of_measurement'>Descending</option></select>", '<input class="search-query" type="text" name="qb_measurement_time" placeholder="Type a Date"/>', 'checkbox_qb_measurement'),('measurement_value', "<select name='qb_measurement_value_choice'><option value='' >None</option><option value='value'>Ascending</option><option value='-value'>Descending</option></select>", '<input class="search-query" type="text" name="qb_measurement_value" placeholder="Type a Value"/>', 'checkbox_qb_measurement'),('measurement_comments', "<select name='qb_measurement_comments_choice'><option value='' >None</option><option value='comments'>A to Z</option><option value='-comments'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_measurement_comments" placeholder="Type a Comment"/>', 'checkbox_qb_measurement'),('measurement_parameter', "<select name='qb_measurement_parameter_choice'><option value='' >None</option><option value='measurement_parameter__parameter'>A to Z</option><option value='-measurement_parameter__parameter'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_measurement_parameter" placeholder="Type a Parameter"/>', 'checkbox_qb_measurement'),('measurement_parameter_type', "<select name='qb_measurement_type_choice'><option value='' >None</option><option value='measurement_parameter__parameter_type'>A to Z</option><option value='-measurement_parameter__parameter_type'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_measurement_type" placeholder="Type a Parameter Type"/>', 'checkbox_qb_measurement'),('measurement_protocol', "<select name='qb_measurement_protocol_choice'><option value='' >None</option><option value='measurement_parameter__protocol'>A to Z</option><option value='-measurement_parameter__protocol'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_measurement_protocol" placeholder="Type a Protocol"/>', 'checkbox_qb_measurement'),('measurement_unit_of_measure', "<select name='qb_measurement_unit_choice'><option value='' >None</option><option value='measurement_parameter__unit_of_measure'>A to Z</option><option value='-measurement_parameter__unit_of_measure'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_measurement_unit" placeholder="Type a Unit"/>', 'checkbox_qb_measurement'), ('measurement_trait_id_buckler', "<select name='qb_measurement_buckler_choice'><option value='' >None</option><option value='measurement_parameter__trait_id_buckler'>A to Z</option><option value='-measurement_parameter__trait_id_buckler'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_measurement_buckler" placeholder="Type a Buckler TraitID"/>', 'checkbox_qb_measurement')]
		query_builder_fields_list = list(chain(measurement_fields_list, query_builder_fields_list))
	if 'Stock' in selected_options:
		stock_fields_list = [('stock_seed_id', "<select name='qb_stock_seed_id_choice'><option value='' >None</option><option value='stock__seed_id'>Ascending</option><option value='-stock__seed_id'>Descending</option></select>", '<input class="search-query" type="text" name="qb_stock_seed_id" placeholder="Type a Seed ID"/>', 'checkbox_qb_stock'), ('stock_seed_name', "<select name='qb_stock_seed_name_choice'><option value='' >None</option><option value='stock__seed_name'>A to Z</option><option value='-stock__seed_name'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_stock_seed_name" placeholder="Type a Seed Name"/>', 'checkbox_qb_stock'), ('stock_cross_type', "<select name='qb_stock_cross_choice'><option value='' >None</option><option value='stock__cross_type'>A to Z</option><option value='-stock__cross_type'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_stock_cross" placeholder="Type a Cross Type"/>', 'checkbox_qb_stock'), ('stock_pedigree', "<select name='qb_stock_pedigree_choice'><option value='' >None</option><option value='stock__pedigree'>A to Z</option><option value='-stock__pedigree'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_stock_pedigree" placeholder="Type a Pedigree"/>', 'checkbox_qb_stock'), ('stock_status', "<select name='qb_stock_status_choice'><option value='' >None</option><option value='stock__stock_status'>A to Z</option><option value='-stock__stock_status'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_stock_status" placeholder="Type a Stock Status"/>', 'checkbox_qb_stock'),('stock_date', "<select name='qb_stock_date_choice'><option value='' >None</option><option value='stock__stock_date'>Ascending</option><option value='-stock__stock_date'>Descending</option></select>", '<input class="search-query" type="text" name="qb_stock_date" placeholder="Type a Stock Date"/>', 'checkbox_qb_stock'),('stock_inoculated', '', '<input type="checkbox" name="qb_stock_inoculated" value="1"/>', 'checkbox_qb_stock'),('stock_comments', "<select name='qb_stock_comments_choice'><option value='' >None</option><option value='stock__comments'>A to Z</option><option value='-stock__comments'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_stock_comments" placeholder="Type Stock Comments"/>', 'checkbox_qb_stock'),('stock_genus', "<select name='qb_stock_genus_choice'><option value='' >None</option><option value='stock__passport__taxonomy__genus'>A to Z</option><option value='-stock__passport__taxonomy__genus'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_stock_genus" placeholder="Type a Genus"/>', 'checkbox_qb_stock'),('stock_species', "<select name='qb_stock_species_choice'><option value='' >None</option><option value='stock__passport__taxonomy__species'>A to Z</option><option value='-stock__passport__taxonomy__species'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_stock_species" placeholder="Type a Species"/>', 'checkbox_qb_stock'),('stock_population', "<select name='qb_stock_population_choice'><option value='' >None</option><option value='stock__passport__taxonomy__population'>A to Z</option><option value='-stock__passport__taxonomy__population'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_stock_population" placeholder="Type a Population"/>', 'checkbox_qb_stock'),('stock_collection_date', "<select name='qb_stock_collecting_date_choice'><option value='' >None</option><option value='stock__passport__collecting__collection_date'>Ascending</option><option value='-stock__passport__collecting__collection_date'>Descending</option></select>", '<input class="search-query" type="text" name="qb_stock_collecting_date" placeholder="Type a Collection Date"/>', 'checkbox_qb_stock'),('stock_collection_method', "<select name='qb_stock_collecting_method_choice'><option value='' >None</option><option value='stock__passport__collecting__collection_method'>A to Z</option><option value='-stock__passport__collecting__collection_method'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_stock_collecting_method" placeholder="Type a Collection Method"/>', 'checkbox_qb_stock'),('stock_collection_comments', "<select name='qb_stock_collecting_comments_choice'><option value='' >None</option><option value='stock__passport__collecting__comments'>A to Z</option><option value='-stock__passport__collecting__comments'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_stock_collecting_comments" placeholder="Type Collecting Comments"/>', 'checkbox_qb_stock'),('stock_source_organization', "<select name='qb_stock_people_org_choice'><option value='' >None</option><option value='stock__passport__people__organization'>A to Z</option><option value='-stock__passport__people__organization'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_stock_people_org" placeholder="Type a Source"/>', 'checkbox_qb_stock')]
		query_builder_fields_list = list(chain(stock_fields_list, query_builder_fields_list))
	if 'Experiment' in selected_options:
		experiment_fields_list = [('experiment_name', "<select name='qb_experiment_name_choice'><option value='' >None</option><option value='experiment__name'>Ascending</option><option value='-experiment__name'>Descending</option></select>", '<input class="search-query" type="text" name="qb_experiment_name" placeholder="Type Experiment Name"/>', 'checkbox_qb_experiment'), ('experiment_field_name', "<select name='qb_experiment_field_name_choice'><option value='' >None</option><option value='experiment__field__field_name'>A to Z</option><option value='-experiment__field__field_name'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_experiment_field_name" placeholder="Type a Field Name"/>', 'checkbox_qb_experiment'), ('experiment_field_locality_city', "<select name='qb_experiment_field_locality_city_choice'><option value='' >None</option><option value='experiment__field__locality__city'>A to Z</option><option value='-experiment__field__locality__city'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_experiment_field_locality_city" placeholder="Type a Locality City"/>', 'checkbox_qb_experiment'), ('experiment_start_date', "<select name='qb_experiment_date_choice'><option value='' >None</option><option value='experiment__start_date'>Ascending</option><option value='-experiment__start_date'>Descending</option></select>", '<input class="search-query" type="text" name="qb_experiment_date" placeholder="Type an Experiment Date"/>', 'checkbox_qb_experiment'), ('experiment_purpose', "<select name='qb_experiment_purpose_choice'><option value='' >None</option><option value='experiment__purpose'>A to Z</option><option value='-experiment__purpose'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_experiment_purpose" placeholder="Type Experiment Purpose"/>', 'checkbox_qb_experiment'), ('experiment_comments', "<select name='qb_experiment_comments_choice'><option value='' >None</option><option value='experiment__comments'>A to Z</option><option value='-experiment__comments'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_experiment_comments" placeholder="Type Experiment Comments"/>', 'checkbox_qb_experiment')]
		query_builder_fields_list = list(chain(experiment_fields_list, query_builder_fields_list))
	if 'Treatment' in selected_options:
		treatments_fields_list = [('treatment_id', "<select name='qb_treatment_id_choice'><option value='' >None</option><option value='ascending'>Ascending</option><option value='descending'>Descending</option></select>", '<input class="search-query" type="text" name="qb_treatment_id" placeholder="Type a Treatment ID"/>', 'checkbox_qb_treatment'), ('treatment_type', "<select name='qb_treatment_type_choice'><option value='' >None</option><option value='alphabetical'>A to Z</option><option value='revalphabetical'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_treatment_type" placeholder="Type a Treatment Type"/>', 'checkbox_qb_treatment'), ('treatment_date', "<select name='qb_treatment_date_choice'><option value='' >None</option><option value='ascending'>Ascending</option><option value='descending'>Descending</option></select>", '<input class="search-query" type="text" name="qb_treatment_date" placeholder="Type Treatment Date"/>', 'checkbox_qb_treatment'), ('treatment_comments', "<select name='qb_treatment_comments_choice'><option value='' >None</option><option value='alphabetical'>A to Z</option><option value='revalphabetical'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_treatment_comments" placeholder="Type Treatment Comments"/>', 'checkbox_qb_treatment')]
		query_builder_fields_list = list(chain(treatments_fields_list, query_builder_fields_list))
	if 'ObsRow' in selected_options:
		row_fields_list = [('row_id', "<select name='qb_row_id_choice'><option value='' >None</option><option value='obs_row__row_id'>Ascending</option><option value='-obs_row__row_id'>Descending</option></select>", '<input class="search-query" type="text" name="qb_row_id" placeholder="Type a Row ID"/>', 'checkbox_qb_row'), ('row_name', "<select name='qb_row_name_choice'><option value='' >None</option><option value='obs_row__row_name'>A to Z</option><option value='-obs_row__row_name'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_row_name" placeholder="Type a Row Name"/>', 'checkbox_qb_row'), ('row_field_name', "<select name='qb_row_field_name_choice'><option value='' >None</option><option value='field__field_name'>A to Z</option><option value='-field__field_name'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_row_field_name" placeholder="Type a Field Name"/>', 'checkbox_qb_row'), ('row_field_locality_city', "<select name='qb_row_field_locality_city_choice'><option value='' >None</option><option value='field__locality__city'>A to Z</option><option value='-field__locality__city'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_row_field_locality_city" placeholder="Type a Locality City"/>', 'checkbox_qb_row'), ('row_range_num', "<select name='qb_row_range_choice'><option value='' >None</option><option value='obs_row__range_num'>Ascending</option><option value='-obs_row__range_num'>Descending</option></select>", '<input class="search-query" type="text" name="qb_row_range" placeholder="Type a Range Num"/>', 'checkbox_qb_row'), ('row_plot', "<select name='qb_row_plot_choice'><option value='' >None</option><option value='obs_row__plot'>A to Z</option><option value='-obs_row__plot'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_row_plot" placeholder="Type a Plot"/>', 'checkbox_qb_row'), ('row_block', "<select name='qb_row_block_choice'><option value='' >None</option><option value='obs_row__block'>A to Z</option><option value='-obs_row__block'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_row_block" placeholder="Type a Block"/>', 'checkbox_qb_row'), ('row_rep', "<select name='qb_row_rep_choice'><option value='' >None</option><option value='obs_row__rep'>A to Z</option><option value='-obs_row__rep'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_row_rep" placeholder="Type a Rep"/>', 'checkbox_qb_row'), ('row_kernel_num', "<select name='qb_row_kernel_num_choice'><option value='' >None</option><option value='obs_row__kernel_num'>Ascending</option><option value='-obs_row__kernel_num'>Descending</option></select>", '<input class="search-query" type="text" name="qb_row_kernel_num" placeholder="Type Kernel Num"/>', 'checkbox_qb_row'), ('row_planting_date', "<select name='qb_row_planting_date_choice'><option value='' >None</option><option value='obs_row__planting_date'>Ascending</option><option value='-obs_row__planting_date'>Descending</option></select>", '<input class="search-query" type="text" name="qb_row_planting_date" placeholder="Type a Planting Date"/>', 'checkbox_qb_row'), ('row_harvest_date', "<select name='qb_row_harvest_date_choice'><option value='' >None</option><option value='obs_row__harvest_date'>Ascending</option><option value='-obs_row__harvest_date'>Descending</option></select>", '<input class="search-query" type="text" name="qb_row_harvest_date" placeholder="Type a Harvest Date"/>', 'checkbox_qb_row'), ('row_comments', "<select name='qb_row_comments_choice'><option value='' >None</option><option value='obs_row__comments'>A to Z</option><option value='-obs_row__comments'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_row_comments" placeholder="Type a Row Comment"/>', 'checkbox_qb_row')]
		query_builder_fields_list = list(chain(row_fields_list, query_builder_fields_list))
	if 'ObsPlant' in selected_options:
		plant_fields_list = [('plant_id', "<select name='qb_plant_id_choice'><option value='' >None</option><option value='obs_plant__plant_id'>Ascending</option><option value='-obs_plant__plant_id'>Descending</option></select>", '<input class="search-query" type="text" name="qb_plant_id" placeholder="Type a Plant ID"/>', 'checkbox_qb_plant'), ('plant_num', "<select name='qb_plant_num_choice'><option value=''>None</option><option value='obs_plant__plant_num'>Ascending</option><option value='-obs_plant__plant_num'>Descending</option></select>", '<input class="search-query" type="text" name="qb_plant_num" placeholder="Type a Plant Num"/>', 'checkbox_qb_plant'), ('plant_comments', "<select name='qb_plant_comments_choice'><option value='' >None</option><option value='obs_plant__comments'>A to Z</option><option value='-obs_plant__comments'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_plant_comments" placeholder="Type a Plant Comment"/>', 'checkbox_qb_plant')]
		query_builder_fields_list = list(chain(plant_fields_list, query_builder_fields_list))
	if 'ObsSample' in selected_options:
		sample_fields_list = [('sample_id', "<select name='qb_sample_id_choice'><option value='' >None</option><option value='obs_sample__sample_id'>Ascending</option><option value='-obs_sample__sample_id'>Descending</option></select>", '<input class="search-query" type="text" name="qb_sample_id" placeholder="Type a Sample ID"/>', 'checkbox_qb_sample'), ('sample_type', "<select name='qb_sample_type_choice'><option value=''>None</option><option value='obs_sample__sample_type'>A to Z</option><option value='-obs_sample__sample_type'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_sample_type" placeholder="Type a Sample Type"/>', 'checkbox_qb_sample'), ('weight', "<select name='qb_sample_weight_choice'><option value='' >None</option><option value='obs_sample__weight'>Ascending</option><option value='-obs_sample__weight'>Descending</option></select>", '<input class="search-query" type="text" name="qb_sample_weight" placeholder="Type a Weight"/>', 'checkbox_qb_sample'), ('kernel_num', "<select name='qb_sample_kernel_num_choice'><option value='' >None</option><option value='obs_sample__kernel_num'>Ascending</option><option value='-obs_sample__kernel_num'>Descending</option></select>", '<input class="search-query" type="text" name="qb_sample_kernel_num" placeholder="Type Kernel Num"/>', 'checkbox_qb_sample'), ('sample_comments', "<select name='qb_sample_comments_choice'><option value='' >None</option><option value='obs_sample__comments'>A to Z</option><option value='-obs_sample__comments'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_sample_comments" placeholder="Type a Sample Comment"/>', 'checkbox_qb_sample')]
		query_builder_fields_list = list(chain(sample_fields_list, query_builder_fields_list))
	if 'ObsEnv' in selected_options:
		env_fields_list = [('environment_id', "<select name='qb_env_id_choice'><option value='' >None</option><option value='obs_env__environment_id'>Ascending</option><option value='-obs_env__environment_id'>Descending</option></select>", '<input class="search-query" type="text" name="qb_env_id" placeholder="Type an Environment ID"/>', 'checkbox_qb_env'), ('longitude', "<select name='qb_env_longitude_choice'><option value=''>None</option><option value='obs_env__longitude'>Ascending</option><option value='-obs_env__longitude'>Descending</option></select>", '<input class="search-query" type="text" name="qb_env_longitude" placeholder="Type a Longitude"/>', 'checkbox_qb_env'), ('latitude', "<select name='qb_env_latitude_choice'><option value='' >None</option><option value='obs_env__latitude'>Ascending</option><option value='-obs_env__latitude'>Descending</option></select>", '<input class="search-query" type="text" name="qb_env_latitude" placeholder="Type a Latitude"/>', 'checkbox_qb_env'), ('environment_comments', "<select name='qb_env_comments_choice'><option value='' >None</option><option value='obs_env__comments'>A to Z</option><option value='-obs_env__comments'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_env_comments" placeholder="Type Environment Comments"/>', 'checkbox_qb_env')]
		query_builder_fields_list = list(chain(env_fields_list, query_builder_fields_list))
	if 'ObsTissue' in selected_options:
		tissue_fields_list = [('tissue_id', "<select name='qb_tissue_id_choice'><option value='' >None</option><option value='obs_tissue__tissue_id'>Ascending</option><option value='-obs_tissue__tissue_id'>Descending</option></select>", '<input class="search-query" type="text" name="qb_tissue_id" placeholder="Type a Tissue ID"/>', 'checkbox_qb_tissue'), ('tissue_type', "<select name='qb_tissue_type_choice'><option value=''>None</option><option value='obs_tissue__tissue_type'>A to Z</option><option value='-obs_tissue__tissue_type'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_tissue_type" placeholder="Type a Tissue Type"/>', 'checkbox_qb_tissue'), ('tissue_name', "<select name='qb_tissue_name_choice'><option value='' >None</option><option value='obs_tissue__tissue_name'>A to Z</option><option value='-obs_tissue__tissue_name'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_tissue_name" placeholder="Type a Tissue Name"/>', 'checkbox_qb_tissue'), ('tissue_date_ground', "<select name='qb_tissue_date_ground_choice'><option value='' >None</option><option value='obs_tissue__date_ground'>Ascending</option><option value='-obs_tissue__date_ground'>Descending</option></select>", '<input class="search-query" type="text" name="qb_tissue_date_ground" placeholder="Type Date Ground"/>', 'checkbox_qb_tissue'), ('tissue_comments', "<select name='qb_tissue_comments_choice'><option value='' >None</option><option value='obs_tissue__comments'>A to Z</option><option value='-obs_tissue__comments'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_tissue_comments" placeholder="Type a Tissue Comment"/>', 'checkbox_qb_tissue')]
		query_builder_fields_list = list(chain(tissue_fields_list, query_builder_fields_list))
	if 'ObsPlate' in selected_options:
		plate_fields_list = [('plate_id', "<select name='qb_plate_id_choice'><option value='' >None</option><option value='obs_plate__plate_id'>Ascending</option><option value='-obs_plate__plate_id'>Descending</option></select>", '<input class="search-query" type="text" name="qb_plate_id" placeholder="Type a Plate ID"/>', 'checkbox_qb_plate'), ('plate_name', "<select name='qb_plate_name_choice'><option value=''>None</option><option value='obs_plate__plate_name'>A to Z</option><option value='-obs_plate__plate_name'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_plate_name" placeholder="Type a Plate Name"/>', 'checkbox_qb_plate'), ('plate_date', "<select name='qb_plate_date_choice'><option value='' >None</option><option value='obs_plate__date'>Ascending</option><option value='-obs_plate__date'>Descending</option></select>", '<input class="search-query" type="text" name="qb_plate_date" placeholder="Type a Plate Date"/>', 'checkbox_qb_plate'), ('plate_contents', "<select name='qb_plate_contents_choice'><option value='' >None</option><option value='obs_plate__contents'>Ascending</option><option value='-obs_plate__contents'>Descending</option></select>", '<input class="search-query" type="text" name="qb_plate_contents" placeholder="Type Plate Contents"/>', 'checkbox_qb_plate'), ('plate_rep', "<select name='qb_plate_rep_choice'><option value='' >None</option><option value='obs_plate__rep'>Ascending</option><option value='-obs_plate__rep'>Descending</option></select>", '<input class="search-query" type="text" name="qb_plate_rep" placeholder="Type Plate Rep"/>', 'checkbox_qb_plate'), ('plate_type', "<select name='qb_plate_type_choice'><option value='' >None</option><option value='obs_plate__plate_type'>A to Z</option><option value='-obs_plate__plate_type'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_plate_type" placeholder="Type a Plate Type"/>', 'checkbox_qb_plate'), ('plate_status', "<select name='qb_plate_status_choice'><option value='' >None</option><option value='obs_plate__plate_status'>A to Z</option><option value='-obs_plate__plate_status'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_plate_status" placeholder="Type a Plate Status"/>', 'checkbox_qb_plate'), ('plate_comments', "<select name='qb_plate_comments_choice'><option value='' >None</option><option value='obs_plate__comments'>A to Z</option><option value='-obs_plate__comments'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_plate_comments" placeholder="Type a Plate Comment"/>', 'checkbox_qb_plate')]
		query_builder_fields_list = list(chain(plate_fields_list, query_builder_fields_list))
	if 'ObsWell' in selected_options:
		well_fields_list = [('well_id', "<select name='qb_well_id_choice'><option value='' >None</option><option value='obs_well__well_id'>Ascending</option><option value='-obs_well__well_id'>Descending</option></select>", '<input class="search-query" type="text" name="qb_well_id" placeholder="Type a Well ID"/>', 'checkbox_qb_well'), ('well_well', "<select name='qb_well_well_choice'><option value=''>None</option><option value='obs_well__well'>A to Z</option><option value='-obs_well__well'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_well_well" placeholder="Type a Well"/>', 'checkbox_qb_well'), ('well_inventory', "<select name='qb_well_inventory_choice'><option value='' >None</option><option value='obs_well__well_inventory'>A to Z</option><option value='-obs_well__well_inventory'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_well_inventory" placeholder="Type a Well Inventory"/>', 'checkbox_qb_well'), ('well_tube_label', "<select name='qb_well_tube_label_choice'><option value='' >None</option><option value='obs_well__tube_label'>Ascending</option><option value='-obs_well__tube_label'>Descending</option></select>", '<input class="search-query" type="text" name="qb_well_tube_label" placeholder="Type Tube Label"/>', 'checkbox_qb_well'), ('well_comments', "<select name='qb_well_comments_choice'><option value='' >None</option><option value='obs_well__comments'>A to Z</option><option value='-obs_well__comments'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_well_comments" placeholder="Type a Well Comment"/>', 'checkbox_qb_well')]
		query_builder_fields_list = list(chain(well_fields_list, query_builder_fields_list))
	if 'ObsDNA' in selected_options:
		dna_fields_list = [('dna_id', "<select name='qb_dna_id_choice'><option value='' >None</option><option value='obs_dna__dna_id'>Ascending</option><option value='-obs_dna__dna_id'>Descending</option></select>", '<input class="search-query" type="text" name="qb_dna_id" placeholder="Type a DNA ID"/>', 'checkbox_qb_dna'), ('dna_extraction_method', "<select name='qb_dna_extraction_method_choice'><option value=''>None</option><option value='obs_dna__extraction_method'>A to Z</option><option value='-obs_dna__extraction_method'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_dna_extraction_method" placeholder="Type a DNA Extraction"/>', 'checkbox_qb_dna'), ('dna_date', "<select name='qb_dna_date_choice'><option value='' >None</option><option value='obs_dna__date'>A to Z</option><option value='-obs_dna__date'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_dna_date" placeholder="Type a DNA Date"/>', 'checkbox_qb_dna'), ('dna_tube_id', "<select name='qb_dna_tube_id_choice'><option value='' >None</option><option value='obs_dna__tube_id'>Ascending</option><option value='-obs_dna__tube_id'>Descending</option></select>", '<input class="search-query" type="text" name="qb_dna_tube_id" placeholder="Type DNA Tube ID"/>', 'checkbox_qb_dna'), ('dna_tube_type', "<select name='qb_dna_tube_type_choice'><option value='' >None</option><option value='obs_dna__tube_type'>Ascending</option><option value='-obs_dna__tube_type'>Descending</option></select>", '<input class="search-query" type="text" name="qb_dna_tube_type" placeholder="Type DNA Tube Type"/>', 'checkbox_qb_dna'), ('dna_comments', "<select name='qb_dna_comments_choice'><option value='' >None</option><option value='obs_dna__comments'>A to Z</option><option value='-obs_dna__comments'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_dna_comments" placeholder="Type a DNA Comment"/>', 'checkbox_qb_dna')]
		query_builder_fields_list = list(chain(dna_fields_list, query_builder_fields_list))
	if 'ObsCulture' in selected_options:
		culture_fields_list = [('culture_id', "<select name='qb_culture_id_choice'><option value='' >None</option><option value='obs_culture__culture_id'>Ascending</option><option value='-obs_culture__culture_id'>Descending</option></select>", '<input class="search-query" type="text" name="qb_culture_id" placeholder="Type a Culture ID"/>', 'checkbox_qb_culture'), ('culture_name', "<select name='qb_culture_name_choice'><option value=''>None</option><option value='obs_culture__culture_name'>A to Z</option><option value='-obs_culture__culture_name'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_culture_name" placeholder="Type a Culture Name"/>', 'checkbox_qb_culture'), ('culture_microbe_type', "<select name='qb_culture_microbe_type_choice'><option value='' >None</option><option value='obs_culture__microbe_type'>A to Z</option><option value='-obs_culture__microbe_type'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_culture_microbe_type" placeholder="Type a Culture Microbe Type"/>', 'checkbox_qb_culture'), ('culture_plating_cycle', "<select name='qb_culture_plating_cycle_choice'><option value='' >None</option><option value='obs_culture__plating_cycle'>Ascending</option><option value='-obs_culture__plating_cycle'>Descending</option></select>", '<input class="search-query" type="text" name="qb_culture_plating_cycle" placeholder="Type Culture Plating Cycle"/>', 'checkbox_qb_culture'), ('culture_dilution', "<select name='qb_culture_dilution_choice'><option value='' >None</option><option value='obs_culture__dilution'>Ascending</option><option value='-obs_culture__dilution'>Descending</option></select>", '<input class="search-query" type="text" name="qb_culture_dilution" placeholder="Type a Culture Dilution"/>', 'checkbox_qb_culture'), ('culture_image_filename', "<select name='qb_culture_image_filename_choice'><option value='' >None</option><option value='obs_culture__image_filename'>Ascending</option><option value='-obs_culture__image_filename'>Descending</option></select>", '<input class="search-query" type="text" name="qb_culture_image_filename" placeholder="Type a Culture Image File"/>', 'checkbox_qb_culture'), ('culture_comments', "<select name='qb_culture_comments_choice'><option value='' >None</option><option value='obs_culture__comments'>Ascending</option><option value='-obs_culture__comments'>Descending</option></select>", '<input class="search-query" type="text" name="qb_culture_comments" placeholder="Type a Culture Comment"/>', 'checkbox_qb_culture'), ('culture_medium_name', "<select name='qb_culture_medium_name_choice'><option value='' >None</option><option value='obs_culture__medium__media_name'>Ascending</option><option value='-obs_culture__medium__media_name'>Descending</option></select>", '<input class="search-query" type="text" name="qb_culture_medium_name" placeholder="Type a Culture Medium Name"/>', 'checkbox_qb_culture'), ('culture_medium_type', "<select name='qb_culture_medium_type_choice'><option value='' >None</option><option value='obs_culture__medium__media_type'>Ascending</option><option value='-obs_culture__medium__media_type'>Descending</option></select>", '<input class="search-query" type="text" name="qb_culture_medium_type" placeholder="Type a Culture Medium Type"/>', 'checkbox_qb_culture'), ('culture_medium_description', "<select name='qb_culture_medium_description_choice'><option value='' >None</option><option value='obs_culture__medium__media_description'>Ascending</option><option value='-obs_culture__medium__media_description'>Descending</option></select>", '<input class="search-query" type="text" name="qb_culture_medium_description" placeholder="Type a Culture Medium Description"/>', 'checkbox_qb_culture'), ('culture_medium_preparation', "<select name='qb_culture_medium_preparation_choice'><option value='' >None</option><option value='obs_culture__medium__media_preparation'>Ascending</option><option value='-obs_culture__medium__media_preparation'>Descending</option></select>", '<input class="search-query" type="text" name="qb_culture_medium_preparation" placeholder="Type a Culture Media Prep"/>', 'checkbox_qb_culture'), ('culture_medium_comments', "<select name='qb_culture_medium_comments_choice'><option value='' >None</option><option value='obs_culture__medium__comments'>Ascending</option><option value='-obs_culture__medium__comments'>Descending</option></select>", '<input class="search-query" type="text" name="qb_culture_medium_comments" placeholder="Type a Culture Medium Comment"/>', 'checkbox_qb_culture'), ('culture_medium_citation_type', "<select name='qb_culture_medium_citation_type_choice'><option value='' >None</option><option value='obs_culture__medium__citation__citation_type'>Ascending</option><option value='-obs_culture__medium__citation__citation_type'>Descending</option></select>", '<input class="search-query" type="text" name="qb_culture_medium_citation_type" placeholder="Type a Culture Medium Citation Type"/>', 'checkbox_qb_culture'), ('culture_medium_citation_title', "<select name='qb_culture_medium_citation_title_choice'><option value='' >None</option><option value='obs_culture__medium__citation__title'>A to Z</option><option value='-obs_culture__medium__citation__title'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_culture_medium_citation_title" placeholder="Type a Culture Medium Citation Title"/>', 'checkbox_qb_culture'), ('culture_medium_citation_url', "<select name='qb_culture_medium_citation_url_choice'><option value='' >None</option><option value='obs_culture__medium__citation__url'>A to Z</option><option value='-obs_culture__medium__citation__url'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_culture_medium_citation_url" placeholder="Type a Culture Medium Citation URL"/>', 'checkbox_qb_culture'), ('culture_medium_citation_pubmed', "<select name='qb_culture_medium_citation_pubmed_choice'><option value='' >None</option><option value='obs_culture__medium__citation__pubmed_id'>A to Z</option><option value='-obs_culture__medium__citation__pubmed_id>Z to A</option></select>", '<input class="search-query" type="text" name="qb_culture_medium_citation_pubmed" placeholder="Type a Culture Medium Citation Pubmed"/>', 'checkbox_qb_culture'), ('culture_medium_citation_comments', "<select name='qb_culture_medium_citation_comments_choice'><option value='' >None</option><option value='obs_culture__medium__citation__comments'>A to Z</option><option value='-obs_culture__medium__citation__comments'>Z to A</option></select>", '<input class="search-query" type="text" name="qb_culture_medium_citation_comments" placeholder="Type a Culture Medium Citation Comment"/>', 'checkbox_qb_culture')]
		query_builder_fields_list = list(chain(culture_fields_list, query_builder_fields_list))

	context_dict['selected_options'] = selected_options
	context_dict['obs_entity_type'] = obs_entity_type
	context_dict['query_builder_fields_list'] = query_builder_fields_list
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/query_builder_fields_list.html', context=context_dict)

@login_required
def query_builder_fields(request):
	context = RequestContext(request)
	context_dict = {}
	obs_tracker_ordered_results = []
	measurement_ordered_results = []
	obs_tracker_kwargs = {}
	obs_tracker_order = []
	measurement_kwargs = {}
	measurement_order = []
	measurement_fields = []
	obs_tracker_fields = []
	display_fields = []
	obs_tracker_args = []

	if request.POST.getlist('checkbox_qb_options', False):
		qb_options = request.POST.getlist('checkbox_qb_options')
	else:
		qb_options = None

	obs_entity_type = request.POST['obs_entity_type']

	if request.POST.getlist('checkbox_qb_measurement', False):
		measurement_fields = request.POST.getlist('checkbox_qb_measurement')
		display_fields = list(chain(display_fields, request.POST.getlist('checkbox_qb_measurement')))
		measurement_args = [('measurement_time', 'qb_measurement_time', 'qb_measurement_time_choice', 'time_of_measurement__contains'), ('measurement_value', 'qb_measurement_value', 'qb_measurement_value_choice', 'value__contains'), ('measurement_comments', 'qb_measurement_comments', 'qb_measurement_comments_choice', 'comments__contains'), ('measurement_parameter', 'qb_measurement_parameter', 'qb_measurement_parameter_choice', 'measurement_parameter__parameter__contains'), ('measurement_parameter_type', 'qb_measurement_type', 'qb_measurement_type_choice', 'measurement_parameter__parameter_type__contains'), ('measurement_protocol', 'qb_measurement_protocol', 'qb_measurement_protocol_choice', 'measurement_parameter__protocol__contains'), ('measurement_unit_of_measure', 'qb_measurement_unit', 'qb_measurement_unit_choice', 'measurement_parameter__unit_of_measure__contains'), ('measurement_trait_id_buckler', 'qb_measurement_buckler', 'qb_measurement_buckler_choice', 'measurement_parameter__trait_id_buckler__contains')]

	if request.POST.getlist('checkbox_qb_experiment', False):
		obs_tracker_fields =list(chain(obs_tracker_fields, request.POST.getlist('checkbox_qb_experiment')))
		display_fields = list(chain(display_fields, request.POST.getlist('checkbox_qb_experiment')))
		experiment_args = [('experiment_name', 'qb_experiment_name', 'qb_experiment_name_choice', 'experiment__name__contains'), ('experiment_field_name', 'qb_experiment_field_name', 'qb_experiment_field_name_choice', 'experiment__field__field_name__contains'), ('experiment_field_locality_city', 'qb_experiment_field_locality_city', 'qb_experiment_field_locality_city_choice', 'experiment__field__locality__city__contains'), ('experiment_start_date', 'qb_experiment_date', 'qb_experiment_date_choice', 'experiment__start_date__contains'), ('experiment_purpose', 'qb_experiment_purpose', 'qb_experiment_purpose_choice', 'experiment__purpose__contains'), ('experiment_comments', 'qb_experiment_comments', 'qb_experiment_comments_choice', 'experiment__comments__contains')]
		obs_tracker_args.extend(experiment_args)

	if request.POST.getlist('checkbox_qb_treatment', False):
		display_fields = list(chain(display_fields, request.POST.getlist('checkbox_qb_treatment')))
		experiment_args = [()]

	if request.POST.getlist('checkbox_qb_row', False):
		obs_tracker_fields = list(chain(obs_tracker_fields, request.POST.getlist('checkbox_qb_row')))
		display_fields = list(chain(display_fields, request.POST.getlist('checkbox_qb_row')))
		row_args = [('row_id', 'qb_row_id', 'qb_row_id_choice', 'obs_row__row_id__contains'), ('row_name', 'qb_row_name', 'qb_row_name_choice', 'obs_row__row_name__contains'), ('row_field_name', 'qb_row_field_name', 'qb_row_field_name_choice', 'field__field_name__contains'), ('row_field_locality_city', 'qb_row_field_locality_city', 'qb_row_field_locality_city_choice', 'field__locality__city__contains'), ('row_range_num', 'qb_row_range', 'qb_row_range_choice', 'obs_row__range_num__contains'), ('row_plot', 'qb_row_plot', 'qb_row_plot_choice', 'obs_row__plot__contains'), ('row_block', 'qb_row_block', 'qb_row_block_choice', 'obs_row__block__contains'), ('row_rep', 'qb_row_rep', 'qb_row_rep_choice', 'obs_row__rep__contains'), ('row_kernel_num', 'qb_row_kernel_num', 'qb_row_kernel_num_choice', 'obs_row__kernel_num__contains'), ('row_planting_date', 'qb_row_planting_date', 'qb_row_planting_date_choice', 'obs_row__planting_date__contains'), ('row_harvest_date', 'qb_row_harvest_date', 'qb_row_harvest_date_choice', 'obs_row__harvest_date__contains'), ('row_comments', 'qb_row_comments', 'qb_row_comments_choice', 'obs_row__comments__contains')]
		obs_tracker_args.extend(row_args)

	if request.POST.getlist('checkbox_qb_plant', False):
		obs_tracker_fields = list(chain(obs_tracker_fields, request.POST.getlist('checkbox_qb_plant')))
		display_fields = list(chain(display_fields, request.POST.getlist('checkbox_qb_plant')))
		plant_args = [('plant_id', 'qb_plant_id', 'qb_plant_id_choice', 'obs_plant__plant_id__contains'), ('plant_num', 'qb_plant_num', 'qb_plant_num_choice', 'obs_plant__plant_num__contains'), ('plant_comments', 'qb_plant_comments', 'qb_plant_comments_choice', 'obs_plant__comments__contains')]
		obs_tracker_args.extend(plant_args)

	if request.POST.getlist('checkbox_qb_tissue', False):
		obs_tracker_fields = list(chain(obs_tracker_fields, request.POST.getlist('checkbox_qb_tissue')))
		display_fields = list(chain(display_fields, request.POST.getlist('checkbox_qb_tissue')))
		tissue_args = [('tissue_id', 'qb_tissue_id', 'qb_tissue_id_choice', 'obs_tissue__tissue_id__contains'), ('tissue_type', 'qb_tissue_type', 'qb_tissue_type_choice', 'obs_tissue__tissue_type__contains'), ('tissue_name', 'qb_tissue_name', 'qb_tissue_name_choice', 'obs_tissue__tissue_name__contains'), ('tissue_date_ground', 'qb_tissue_date_ground', 'qb_tissue_date_ground_choice', 'obs_tissue__date_ground__contains'), ('tissue_comments', 'qb_tissue_comments', 'qb_tissue_comments_choice', 'obs_tissue__comments__contains')]
		obs_tracker_args.extend(tissue_args)

	if request.POST.getlist('checkbox_qb_plate', False):
		obs_tracker_fields = list(chain(obs_tracker_fields, request.POST.getlist('checkbox_qb_plate')))
		display_fields = list(chain(display_fields, request.POST.getlist('checkbox_qb_plate')))
		plate_args = [('plate_id', 'qb_plate_id', 'qb_plate_id_choice', 'obs_plate__plate_id__contains'), ('plate_name', 'qb_plate_name', 'qb_plate_name_choice', 'obs_plate__plate_name__contains'), ('plate_date', 'qb_plate_date', 'qb_plate_date_choice', 'obs_plate__date__contains'), ('plate_contents', 'qb_plate_contents', 'qb_plate_contents_choice', 'obs_plate__contents__contains'), ('plate_rep', 'qb_plate_rep', 'qb_plate_rep_choice', 'obs_plate__rep__contains'), ('plate_type', 'qb_plate_type', 'qb_plate_type_choice', 'obs_plate__plate_type__contains'), ('plate_status', 'qb_plate_status', 'qb_plate_status_choice', 'obs_plate__plate_status__contains'), ('plate_comments', 'qb_plate_comments', 'qb_plate_comments_choice', 'obs_plate__comments__contains')]
		obs_tracker_args.extend(plate_args)

	if request.POST.getlist('checkbox_qb_well', False):
		obs_tracker_fields = list(chain(obs_tracker_fields, request.POST.getlist('checkbox_qb_well')))
		display_fields = list(chain(display_fields, request.POST.getlist('checkbox_qb_well')))
		well_args = [('well_id', 'qb_well_id', 'qb_well_id_choice', 'obs_well__well_id__contains'), ('well_well', 'qb_well_well', 'qb_well_well_choice', 'obs_well__well__contains'), ('well_inventory', 'qb_well_inventory', 'qb_well_inventory_choice', 'obs_well__well_inventory__contains'), ('well_tube_label', 'qb_well_tube_label', 'qb_well_tube_label_choice', 'obs_well__tube_label__contains'), ('well_comments', 'qb_well_comments', 'qb_well_comments_choice', 'obs_well__comments__contains')]
		obs_tracker_args.extend(well_args)

	if request.POST.getlist('checkbox_qb_culture', False):
		obs_tracker_fields = list(chain(obs_tracker_fields, request.POST.getlist('checkbox_qb_culture')))
		display_fields = list(chain(display_fields, request.POST.getlist('checkbox_qb_culture')))
		culture_args = [('culture_id', 'qb_culture_id', 'qb_culture_id_choice', 'obs_culture__culture_id__contains'), ('culture_name', 'qb_culture_name', 'qb_culture_name_choice', 'obs_culture__culture_name__contains'), ('culture_microbe_type', 'qb_culture_microbe_type', 'qb_culture_microbe_type_choice', 'obs_culture__microbe_type__contains'), ('culture_plating_cycle', 'qb_culture_plating_cycle', 'qb_culture_plating_cycle_choice', 'obs_well__plating_cycle__contains'), ('culture_dilution', 'qb_culture_dilution', 'qb_culture_dilution_choice', 'obs_culture__dilution__contains'), ('culture_image_filename', 'qb_culture_image_filename', 'qb_culture_image_filename_choice', 'obs_culture__image_filename__contains'), ('culture_comments', 'qb_culture_comments', 'qb_culture_comments_choice', 'obs_culture__comments__contains'), ('culture_medium_name', 'qb_culture_medium_name', 'qb_culture_medium_name_choice', 'obs_culture__medium__media_name__contains'), ('culture_medium_type', 'qb_culture_medium_type', 'qb_culture_medium_type_choice', 'obs_culture__medium__media_type__contains'), ('culture_medium_description', 'qb_culture_medium_description', 'qb_culture_medium_description_choice', 'obs_culture__medium__media_description__contains'), ('culture_medium_preparation', 'qb_culture_medium_preparation', 'qb_culture_medium_preparation_choice', 'obs_culture__medium__media_preparation__contains'), ('culture_medium_comments', 'qb_culture_medium_comments', 'qb_culture_medium_comments_choice', 'obs_culture__medium__comments__contains'), ('culture_medium_citation_type', 'qb_culture_medium_citation_type', 'qb_culture_medium_citation_type_choice', 'obs_culture__medium__citation__citation_type__contains'), ('culture_medium_citation_title', 'qb_culture_medium_citation_title', 'qb_culture_medium_citation_title', 'obs_culture__medium__citation__title__contains'), ('culture_medium_citation_url', 'qb_culture_medium_citation_url', 'qb_culture_medium_citation_url_choice', 'obs_culture__medium__citation__title__contains'), ('culture_medium_citation_url', 'qb_culture_medium_citation_url', 'qb_culture_medium_citation_url_choice', 'obs_culture__medium__citation__url__contains'), ('culture_medium_citation_pubmed', 'qb_culture_medium_citation_pubmed', 'qb_culture_medium_citation_pubmed_choice', 'obs_culture__medium__citation__pubmed_id__contains'), ('culture_medium_citation_comments', 'qb_culture_medium_citation_comments', 'qb_culture_medium_citation_comments_choice', 'obs_culture__medium__citation__comments__contains')]
		obs_tracker_args.extend(culture_args)

	if request.POST.getlist('checkbox_qb_dna', False):
		obs_tracker_fields = list(chain(obs_tracker_fields, request.POST.getlist('checkbox_qb_dna')))
		display_fields = list(chain(display_fields, request.POST.getlist('checkbox_qb_dna')))
		dna_args = [('dna_id', 'qb_dna_id', 'qb_dna_id_choice', 'obs_dna__dna_id__contains'), ('dna_extraction_method', 'qb_dna_extraction_method', 'qb_dna_extraction_method_choice', 'obs_dna__extraction_method__contains'), ('dna_date', 'qb_dna_date', 'qb_dna_date_choice', 'obs_dna__date__contains'), ('dna_tube_id', 'qb_dna_tube_id', 'qb_dna_tube_id_choice', 'obs_dna__tube_id__contains'), ('dna_tube_type', 'qb_dna_tube_type', 'qb_dna_tube_type_choice', 'obs_dna__tube_type__contains'), ('dna_comments', 'qb_dna_comments_type', 'qb_dna_comments_choice', 'obs_dna__comments__contains')]
		obs_tracker_args.extend(dna_args)

	if request.POST.getlist('checkbox_qb_sample', False):
		display_fields = list(chain(display_fields, request.POST.getlist('checkbox_qb_sample')))

	if request.POST.getlist('checkbox_qb_env', False):
		display_fields = list(chain(display_fields, request.POST.getlist('checkbox_qb_env')))

	if request.POST.getlist('checkbox_qb_stock', False):
		obs_tracker_fields = list(chain(obs_tracker_fields, request.POST.getlist('checkbox_qb_stock')))
		display_fields = list(chain(display_fields, request.POST.getlist('checkbox_qb_stock')))
		stock_args = [('stock_seed_id', 'qb_stock_seed_id', 'qb_stock_seed_id_choice', 'stock__seed_id__contains'), ('stock_seed_name', 'qb_stock_seed_name', 'qb_stock_seed_name_choice', 'stock__seed_name__contains'), ('stock_cross_type', 'qb_stock_cross', 'qb_stock_cross_choice', 'stock__cross_type__contains'), ('stock_pedigree', 'qb_stock_pedigree', 'qb_stock_pedigree_choice', 'stock__pedigree__contains'), ('stock_status', 'qb_stock_status', 'qb_stock_status_choice', 'stock__stock_status__contains'), ('stock_date', 'qb_stock_date', 'qb_stock_date_choice', 'stock__stock_date__contains'), ('stock_inoculated', 'qb_stock_inoculated', '', 'stock__inoculated'), ('stock_comments', 'qb_stock_comments', 'qb_stock_comments_choice', 'stock__comments__contains'), ('stock_genus', 'qb_stock_genus', 'qb_stock_genus_choice', 'stock__passport__taxonomy__genus__contains'), ('stock_species', 'qb_stock_species', 'qb_stock_species_choice', 'stock__passport__taxonomy__species__contains'), ('stock_population', 'qb_stock_population', 'qb_stock_population_choice', 'stock__passport__taxonomy__population__contains'), ('stock_collection_date', 'qb_stock_collecting_date', 'qb_stock_collecting_date_choice', 'stock__passport__collecting__collection_date__contains'), ('stock_collection_method', 'qb_collecting_method', 'qb_collecting_method_choice', 'stock__passport__collecting__collection_method__contains'), ('stock_collection_comments', 'qb_stock_collecting_comments', 'qb_stock_collecting_comments_choice', 'stock__passport__collecting__comments__contains'), ('stock_source_organization', 'qb_stock_people_org', 'qb_stock_people_org_choice', 'stock__passport__people__organization__contains')]
		obs_tracker_args.extend(stock_args)

	model_field_mapper = {'measurement_time':'time_of_measurement', 'measurement_value': 'value', 'measurement_comments': 'comments', 'measurement_parameter': 'measurement_parameter__parameter', 'measurement_parameter_type': 'measurement_parameter__parameter_type', 'measurement_protocol': 'measurement_parameter__protocol', 'measurement_unit_of_measure': 'measurement_parameter__unit_of_measure', 'measurement_trait_id_buckler': 'measurement_parameter__trait_id_buckler', 'experiment_name': 'experiment__name', 'experiment_field_name': 'experiment__field__field_name', 'experiment_field_locality_city': 'experiment__field__locality__city', 'experiment_start_date': 'experiment__start_date', 'experiment_purpose': 'experiment__purpose', 'experiment_comments': 'experiment__comments', 'row_id': 'obs_row__row_id', 'row_name': 'obs_row__row_name', 'row_field_name': 'field__field_name', 'row_field_locality_city': 'field__locality__city', 'row_range_num': 'obs_row__range_num', 'row_plot': 'obs_row__plot', 'row_block': 'obs_row__block', 'row_rep': 'obs_row__rep', 'row_kernel_num': 'obs_row__kernel_num', 'row_planting_date': 'obs_row__planting_date', 'row_harvest_date': 'obs_row__harvest_date', 'row_comments': 'obs_row__comments', 'plant_id': 'obs_plant__plant_id', 'plant_num': 'obs_plant__plant_num', 'plant_comments': 'obs_plant__comments', 'stock_seed_id': 'stock__seed_id', 'stock_seed_name': 'stock__seed_name', 'stock_cross_type': 'stock__cross_type', 'stock_pedigree': 'stock__pedigree', 'stock_status': 'stock__stock_status', 'stock_date': 'stock__stock_date', 'stock_inoculated': 'stock__inoculated', 'stock_comments': 'stock__comments', 'stock_genus': 'stock__passport__taxonomy__genus', 'stock_species': 'stock__passport__taxonomy__species', 'stock_population': 'stock__passport__taxonomy__population', 'stock_collection_date': 'stock__passport__collecting__collection_date', 'stock_collection_method': 'stock__passport__collecting__collection_method', 'stock_collection_comments': 'stock__passport__collecting__comments', 'stock_source_organization': 'stock__passport__people__organization', 'tissue_id': 'obs_tissue__tissue_id', 'tissue_type': 'obs_tissue__tissue_type', 'tissue_name': 'obs_tissue__tissue_name', 'tissue_date_ground': 'obs_tissue__date_ground', 'tissue_comments': 'obs_tissue__comments', 'plate_id': 'obs_plate__plate_id', 'plate_name': 'obs_plate__plate_name', 'plate_date': 'obs_plate__date', 'plate_contents': 'obs_plate__contents', 'plate_rep': 'obs_plate__rep', 'plate_type': 'obs_plate__plate_type', 'plate_status': 'obs_plate__plate_status', 'plate_comments': 'obs_plate__comments', 'well_id': 'obs_well__well_id', 'well_well': 'obs_well__well', 'well_inventory': 'obs_well__well_inventory', 'well_tube_label': 'obs_well__tube_label', 'well_comments': 'obs_well__comments', 'culture_id': 'obs_culture__culture_id', 'culture_name': 'obs_culture__culture_name', 'culture_microbe_type': 'obs_culture__microbe_type', 'culture_plating_cycle': 'obs_culture__plating_cycle', 'culture_dilution': 'obs_culture__dilution', 'culture_image_filename': 'obs_culture__image_filename', 'culture_comments': 'obs_culture__comments', 'culture_medium_type': 'obs_culture__medium__media_type', 'culture_medium_name': 'obs_culture__medium__media_name', 'culture_medium_description': 'obs_culture__medium__media_description', 'culture_medium_preparation': 'obs_culture__medium__media_preparation', 'culture_medium_comments': 'obs_culture__medium__comments', 'culture_medium_citation_type': 'obs_culture__medium__citation__citation_type', 'culture_medium_citation_title': 'obs_culture__medium__citation__title', 'culture_medium_citation_url': 'obs_culture__medium__citation__url', 'culture_medium_citation_pubmed': 'obs_culture__medium__citation__pubmed_id', 'culture_medium_citation_comments': 'obs_culture__medium__citation__comments', 'dna_id': 'obs_dna__dna_id', 'dna_extraction_method': 'obs_dna__extraction_method', 'dna_date': 'obs_dna__date', 'dna_tube_id': 'obs_dna__tube_id', 'dna_tube_type': 'obs_dna__tube_type', 'dna_comments': 'obs_dna__comments'}

	obs_tracker_model_fields = ['id']
	for w,x,y,z in obs_tracker_args:
		if w in obs_tracker_fields:
			obs_tracker_model_fields.append(model_field_mapper[w])
			obs_tracker_kwargs[z] = request.POST[x]
			if request.POST[y] != '':
				obs_tracker_order.append(request.POST[y])
	obs_tracker_kwargs['obs_entity_type'] = obs_entity_type
	try:
		obs_tracker_ordered_results = ObsTracker.objects.filter(**obs_tracker_kwargs).values(*obs_tracker_model_fields).order_by(*obs_tracker_order)
	except ObsTracker.DoesNotExist:
		obs_tracker_ordered_results = None

	if 'Measurement' in qb_options:
		measurement_results = []
		measurement_model_fields = []
		for w,x,y,z in measurement_args:
			if w in measurement_fields:
				measurement_model_fields.append(model_field_mapper[w])
				measurement_kwargs[z] = request.POST[x]
				if request.POST[y] != '':
					measurement_order.append(request.POST[y])
		for result in obs_tracker_ordered_results:
			measurement_kwargs['obs_tracker_id'] = result['id']
			try:
				measurement_results = Measurement.objects.filter(**measurement_kwargs).values(*measurement_model_fields)
			except Measurement.DoesNotExist:
				measurement_results = None
			for m in measurement_results:
				for f in obs_tracker_fields:
					m[f] = result[model_field_mapper[f]]
				for f in measurement_fields:
					m[f] = m[model_field_mapper[f]]
			measurement_ordered_results = list(chain(measurement_ordered_results, measurement_results))
		for order in measurement_order:
			measurement_ordered_results = sorted(measurement_ordered_results, key=itemgetter(order))
		display_results = measurement_ordered_results
	else:
		for result in obs_tracker_ordered_results:
			for f in obs_tracker_fields:
				result[f] = result[model_field_mapper[f]]
		display_results = obs_tracker_ordered_results

	if 'qb_results_view' in request.POST:
		context_dict['qb_options'] = qb_options
		context_dict['display_fields'] = display_fields
		context_dict['display_results'] = display_results
		context_dict['logged_in_user'] = request.user.username
		return render_to_response('lab/query_builder_results.html', context_dict, context)

	if 'qb_results_download' in request.POST:
		response = HttpResponse(content_type='text/csv')
		response['Content-Disposition'] = 'attachment; filename="query_builder_results.csv"'
		writer = csv.writer(response)
		writer.writerow(display_fields)
		for value in display_results:
			value_write = []
			for field in display_fields:
				try:
					value_write.append(value[field])
				except KeyError:
					value_write.append('N/A')
			writer.writerow(value_write)
		return response

@login_required
def maize_data_keyword_browse(request, keyword):
	context = RequestContext(request)
	context_dict = {}
	if keyword == 'mycotoxin':
		maize_data = ObsTracker.objects.filter(obs_entity_type='maize', experiment__name='15RK')
	context_dict['maize_data'] = maize_data
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/maize_data.html', context_dict, context)

@login_required
def sample_data_keyword_browse(request, keyword):
	context = RequestContext(request)
	context_dict = {}
	if keyword == 'mycotoxin':
		samples_data = ObsTracker.objects.filter(obs_entity_type='sample', experiment__name='15RK')
	context_dict['samples_data'] = samples_data
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/samples_data.html', context_dict, context)

@login_required
def separation_data_keyword_browse(request, keyword):
	context = RequestContext(request)
	context_dict = {}
	if keyword == 'mycotoxin':
		separation_data = Separation.objects.all()
	context_dict['separation_data'] = separation_data
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/separation_data.html', context_dict, context)

@login_required
def extract_data_keyword_browse(request, keyword):
	context = RequestContext(request)
	context_dict = {}
	if keyword == 'mycotoxin':
		extract_data = ObsTracker.objects.filter(obs_entity_type='extract', experiment__name='15RK')
	context_dict['extract_data'] = extract_data
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/extract_data.html', context_dict, context)

@login_required
def measurement_data_keyword_browse(request, keyword):
	context = RequestContext(request)
	context_dict = {}
	measurement_data = Measurement.objects.filter(obs_tracker__experiment__name='15RK')
	for m in measurement_data:
		m = make_obs_tracker_info(m.obs_tracker, '')
	context_dict['measurement_data'] = measurement_data
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/measurement_data.html', context_dict, context)

@login_required
def upload_online(request, template_type):
	context_dict = {}
	if request.method == 'POST':
		sent = True
		upload_form = UploadQueueForm(request.POST, request.FILES)
		if upload_form.is_valid():
			new_upload_exp = upload_form.cleaned_data['experiment']
			new_upload_user = upload_form.cleaned_data['user']
			new_upload_filename = upload_form.cleaned_data['file_name']
			new_upload_comments = upload_form.cleaned_data['comments']
			new_upload_verified = upload_form.cleaned_data['verified']
			upload_added = True

			if template_type == 'seed_stock':
				results_dict = loader_scripts.seed_stock_loader_prep(request.FILES['file_name'], new_upload_user)
			elif template_type == 'seed_packet':
				results_dict = loader_scripts.seed_packet_loader_prep(request.FILES['file_name'], new_upload_user)
			elif template_type == 'row_data':
				results_dict = loader_scripts.row_loader_prep(request.FILES['file_name'], new_upload_user)
			elif template_type == 'measurement_data':
				results_dict = loader_scripts.measurement_loader_prep(request.FILES['file_name'], new_upload_user)
			elif template_type == 'plant_data':
				results_dict = loader_scripts.plant_loader_prep(request.FILES['file_name'], new_upload_user)
			elif template_type == 'tissue_data':
				results_dict = loader_scripts.tissue_loader_prep(request.FILES['file_name'], new_upload_user)
			elif template_type == 'culture_data':
				results_dict = loader_scripts.culture_loader_prep(request.FILES['file_name'], new_upload_user)
			elif template_type == 'microbe_data':
				results_dict = loader_scripts.microbe_loader_prep(request.FILES['file_name'], new_upload_user)
			elif template_type == 'dna_data':
				results_dict = loader_scripts.dna_loader_prep(request.FILES['file_name'], new_upload_user)
			elif template_type == 'plate_data':
				results_dict = loader_scripts.plate_loader_prep(request.FILES['file_name'], new_upload_user)
			elif template_type == 'well_data':
				results_dict = loader_scripts.well_loader_prep(request.FILES['file_name'], new_upload_user)
			elif template_type == 'env_data':
				results_dict = loader_scripts.env_loader_prep(request.FILES['file_name'], new_upload_user)
			elif template_type == 'isolate_data':
				results_dict = loader_scripts.isolate_loader_prep(request.FILES['file_name'], new_upload_user)
			elif template_type == 'samples_data':
				results_dict = loader_scripts.samples_loader_prep(request.FILES['file_name'], new_upload_user)
			elif template_type == 'separation_data':
				results_dict = loader_scripts.separation_loader_prep(request.FILES['file_name'], new_upload_user)
			elif template_type == 'maize_data':
				results_dict = loader_scripts.maize_loader_prep(request.FILES['file_name'], new_upload_user)
			elif template_type == 'glycerol_stock_data':
				results_dict = loader_scripts.glycerol_stock_loader_prep(request.FILES['file_name'], new_upload_user)
			elif template_type == 'primer_data':
				results_dict = loader_scripts.primer_loader_prep(request.FILES['file_name'], new_upload_user)
			elif template_type == 'marker_data':
				results_dict = loader_scripts.marker_loader_prep(request.FILES['file_name'], new_upload_user)
			elif template_type == 'map_feature_interval_data':
				results_dict = loader_scripts.map_feature_interval_loader_prep(request.FILES['file_name'], new_upload_user)
			elif template_type == 'nils_data':
				results_dict = loader_scripts.nils_loader_prep(request.FILES['file_name'], new_upload_user)
			else:
				results_dict = None
			if results_dict is not None:
				if new_upload_verified == False:
					upload_complete = False

					if template_type == 'seed_stock':
						output = loader_scripts.seed_stock_loader_prep_output(results_dict, new_upload_exp, template_type)
					elif template_type == 'seed_packet':
						output = loader_scripts.seed_packet_loader_prep_output(results_dict, new_upload_exp, template_type)
					elif template_type == 'row_data':
						output = loader_scripts.row_loader_prep_output(results_dict, new_upload_exp, template_type)
					elif template_type == 'measurement_data':
						output = loader_scripts.measurement_loader_prep_output(results_dict, new_upload_exp, template_type)
					elif template_type == 'plant_data':
						output = loader_scripts.plant_loader_prep_output(results_dict, new_upload_exp, template_type)
					elif template_type == 'tissue_data':
						output = loader_scripts.tissue_loader_prep_output(results_dict, new_upload_exp, template_type)
					elif template_type == 'culture_data':
						output = loader_scripts.culture_loader_prep_output(results_dict, new_upload_exp, template_type)
					elif template_type == 'microbe_data':
						output = loader_scripts.microbe_loader_prep_output(results_dict, new_upload_exp, template_type)
					elif template_type == 'dna_data':
						output = loader_scripts.dna_loader_prep_output(results_dict, new_upload_exp, template_type)
					elif template_type == 'plate_data':
						output = loader_scripts.plate_loader_prep_output(results_dict, new_upload_exp, template_type)
					elif template_type == 'well_data':
						output = loader_scripts.well_loader_prep_output(results_dict, new_upload_exp, template_type)
					elif template_type == 'env_data':
						output = loader_scripts.env_loader_prep_output(results_dict, new_upload_exp, template_type)
					elif template_type == 'isolate_data':
						output = loader_scripts.isolate_loader_prep_output(results_dict, new_upload_exp, template_type)
					elif template_type == 'samples_data':
						output = loader_scripts.samples_loader_prep_output(results_dict, new_upload_exp, template_type)
					elif template_type == 'separation_data':
						output = loader_scripts.separation_loader_prep_output(results_dict, new_upload_exp, template_type)
					elif template_type == 'maize_data':
						output = loader_scripts.maize_loader_prep_output(results_dict, new_upload_exp, template_type)
					elif template_type == 'glycerol_stock_data':
						output = loader_scripts.glycerol_stock_loader_prep_output(results_dict, new_upload_exp, template_type)
					elif template_type == 'primer_data':
						output = loader_scripts.primer_loader_prep_output(results_dict, new_upload_exp, template_type)
					elif template_type == 'marker_data':
						output = loader_scripts.marker_loader_prep_output(results_dict, new_upload_exp, template_type)
					elif template_type == 'map_feature_interval_data':
						output = loader_scripts.map_feature_interval_loader_prep_output(results_dict, new_upload_exp, template_type)
					elif template_type == 'nils_data':
						output = loader_scripts.nils_loader_prep_output(results_dict, new_upload_exp, template_type)
					else:
						output = None
					return output

				elif new_upload_verified == True:
					if template_type == 'seed_stock':
						uploaded = loader_scripts.seed_stock_loader(results_dict)
					elif template_type == 'seed_packet':
						uploaded = loader_scripts.seed_packet_loader(results_dict)
					elif template_type == 'row_data':
						uploaded = loader_scripts.row_loader(results_dict)
					elif template_type == 'measurement_data':
						uploaded = loader_scripts.measurement_loader(results_dict)
					elif template_type == 'plant_data':
						uploaded = loader_scripts.plant_loader(results_dict)
					elif template_type == 'tissue_data':
						uploaded = loader_scripts.tissue_loader(results_dict)
					elif template_type == 'culture_data':
						uploaded = loader_scripts.culture_loader(results_dict)
					elif template_type == 'microbe_data':
						uploaded = loader_scripts.microbe_loader(results_dict)
					elif template_type == 'dna_data':
						uploaded = loader_scripts.dna_loader(results_dict)
					elif template_type == 'plate_data':
						uploaded = loader_scripts.plate_loader(results_dict)
					elif template_type == 'well_data':
						uploaded = loader_scripts.well_loader(results_dict)
					elif template_type == 'env_data':
						uploaded = loader_scripts.env_loader(results_dict)
					elif template_type == 'isolate_data':
						uploaded = loader_scripts.isolate_loader(results_dict)
					elif template_type == 'samples_data':
						uploaded = loader_scripts.samples_loader(results_dict)
					elif template_type == 'separation_data':
						uploaded = loader_scripts.separation_loader(results_dict)
					elif template_type == 'maize_data':
						uploaded = loader_scripts.maize_loader(results_dict)
					elif template_type == 'glycerol_stock_data':
						uploaded = loader_scripts.glycerol_stock_loader(results_dict)
					elif template_type == 'primer_data':
						uploaded = loader_scripts.primer_loader(results_dict)
					elif template_type == 'marker_data':
						uploaded = loader_scripts.marker_loader(results_dict)
					elif template_type == 'map_feature_interval_data':
						uploaded = loader_scripts.map_feature_interval_loader(results_dict)
					elif template_type == 'nils_data':
						uploaded = loader_scripts.nils_loader(results_dict)
					else:
						uploaded = False

					if uploaded == True:
						new_upload, created = UploadQueue.objects.get_or_create(experiment=new_upload_exp, user=new_upload_user, file_name=new_upload_filename, upload_type=template_type)
						new_upload.comments = new_upload_comments
						new_upload.verified = new_upload_verified
						new_upload.completed = True
						new_upload.save()
						upload_complete = True
					else:
						upload_complete = False
				else:
					upload_complete = False
			else:
				upload_complete = False
		else:
			print(upload_form.errors)
			upload_added = False
			upload_complete = False
	else:
		sent = False
		upload_form = UploadQueueForm()
		upload_added = False
		upload_complete = None
	context_dict['upload_form'] = upload_form
	context_dict['upload_added'] = upload_added
	context_dict['upload_complete'] = upload_complete
	context_dict['sent'] = sent
	context_dict['template_type'] = template_type
	context_dict['logged_in_user'] = request.user.username
	return render(request, 'lab/upload_online.html', context=context_dict)

@login_required
def download_markers(request, file_format):
	context_dict = {}
	if request.method == 'POST':
		marker_ids = request.POST.getlist('marker_select_to_gff3', '')
		markers = Marker.objects.filter(id__in=marker_ids)
		response = HttpResponse(content_type='text/tsv')
		response['Content-Disposition'] = 'attachment; filename="selected_marker_gff3.tsv"'
		writer = csv.writer(response, delimiter='\t')
		if file_format == 'gff3':
			writer.writerow(['##gff-version 3'])
			for m in markers:
				line = "chr%s\tNelsonlab\t.\t%s\t%s\t.\t.\t.\tID=%s;Name=%s" % (m.map_feature_interval.map_feature_start.chromosome, m.map_feature_interval.map_feature_start.physical_position, m.map_feature_interval.map_feature_end.physical_position, m.marker_id, m.marker_name)
				writer.writerow([line])
	return response
