
import csv
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from lab.models import UserProfile, Experiment, Passport, Stock, StockPacket, Taxonomy, People, Collecting, Field, Locality, Location, ObsRow, ObsPlant, ObsSample, ObsEnv, ObsSelector, Isolate, DiseaseInfo, Measurement, MeasurementParameter, Treatment
from lab.forms import UserForm, UserProfileForm, ChangePasswordForm, EditUserForm, EditUserProfileForm, NewExperimentForm, LogSeedDataOnlineForm, LogStockPacketOnlineForm, LogPlantsOnlineForm, LogRowsOnlineForm, LogEnvironmentsOnlineForm, LogSamplesOnlineForm, LogMeasurementsOnlineForm, NewTreatmentForm
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

"""Used to handle data from URL, to ensure blank spaces don't mess things up"""
def encode_url(str):
	return str.replace(' ', '_')

def decode_url(str):
	return str.replace('_', ' ')


"""This is used to process AJAX requests when something is typed in the "find an experiment" input. It is used to display the experiments on the left side of the templates."""
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
	context = RequestContext(request)
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
	return render_to_response('lab/index.html', context_dict, context)

def about_people(request, people_selection):
	context = RequestContext(request)
	context_dict = {}
	if people_selection == 'all':
		people_all_button = True
		people_staff_button = None
		people_active_button = None
		users = User.objects.all().exclude(username='NULL').exclude(username='unknown_person').exclude(username='unknown')
		for user in users:
			user_profile = UserProfile.objects.get(user=user)
			user.job_title = user_profile.job_title
			user.picture = user_profile.picture
	elif people_selection == 'staff':
		people_all_button = None
		people_staff_button = True
		people_active_button = None
		users = User.objects.filter(is_staff='1').exclude(username='NULL').exclude(username='unknown_person').exclude(username='unknown')
		for user in users:
			user_profile = UserProfile.objects.get(user=user)
			user.job_title = user_profile.job_title
			user.picture = user_profile.picture
	elif people_selection == 'active':
		people_all_button = None
		people_staff_button = None
		people_active_button = True
		users = User.objects.filter(is_active='1').exclude(username='NULL').exclude(username='unknown_person').exclude(username='unknown')
		for user in users:
			user_profile = UserProfile.objects.get(user=user)
			user.job_title = user_profile.job_title
			user.picture = user_profile.picture
	else:
		people_all_button = None
		people_staff_button = None
		people_active_button = None
		users = None
	context_dict['people_all_button'] = people_all_button
	context_dict['people_staff_button'] = people_staff_button
	context_dict['people_active_button'] = people_active_button
	context_dict['users'] = users
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/people.html', context_dict, context)

def about_literature(request):
	context = RequestContext(request)
	context_dict = {}
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/literature.html', context_dict, context)

def about_goals(request):
	context = RequestContext(request)
	context_dict = {}
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/goals.html', context_dict, context)

def about_collaborators(request):
	context = RequestContext(request)
	context_dict = {}
	collaborators = People.objects.all()
	context_dict['collaborators'] = collaborators
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/collaborators.html', context_dict, context)


"""Was from tango_with_django project. Not used anymore.

def add_page(request, category_name_url):
	context = RequestContext(request)
	category_name = decode_url(category_name_url)
	context_dict = {'category_name': category_name}
	if request.method == 'POST':
		form = PageForm(request.POST)
		if form.is_valid():
			page = form.save(commit=False)
			try:
				cat = Category.objects.get(name=category_name)
				page.category = cat
			except Category.DoesNotExist:
				return render_to_response('lab/add_category.html', {}, context)
			page.views = 0
			page.save()
			return category(request, category_name_url)
		else:
			print(form.errors)
	else:
		form = PageForm()
	return render_to_response('lab/add_page.html', {'category_name_url': category_name_url, 'category_name': category_name, 'form': form}, context)
"""

def error_prelim(request, error_message):
	context = RequestContext(request)
	context_dict = {'errormessage': error_message}
	return render_to_response('lab/error_prelim.html', context_dict, context)

def register(request):
	context = RequestContext(request)
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
			profile.save()
			registered = True
		else:
			print(user_form.errors, profile_form.errors)
	else:
		user_form = UserForm()
		profile_form = UserProfileForm()
	return render_to_response('lab/register.html', {'user_form': user_form, 'profile_form': profile_form, 'registered': registered}, context)

def user_login(request):
	context = RequestContext(request)
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
				return render_to_response('lab/login.html', {'next_url':next_url, 'disabled_account': 'disabled'}, context)
		else:
			return render_to_response('lab/login.html', {'next_url':next_url, 'bad_details': 'bad_details'}, context)
	else:
		return render_to_response('lab/login.html', {'next_url':next_url}, context)

@login_required
def user_logout(request):
	logout(request)
	return HttpResponseRedirect('/lab/')

def profile(request, profile_name):
	context = RequestContext(request)
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
	return render_to_response('lab/profile.html', context_dict, context)

@login_required
def profile_change_password(request):
  context = RequestContext(request)
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
  return render_to_response('lab/profile_change_password.html', context_dict, context)

@login_required
def edit_profile(request):
	context = RequestContext(request)
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
	return render_to_response('lab/edit_profile.html', context_dict, context)

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
	context = RequestContext(request)
	experiment_name = decode_url(experiment_name_url)
	context_dict = {'experiment_name': experiment_name}
	if experiment_name is not 'search':
		try:
			experiment = Experiment.objects.get(name=experiment_name)
			context_dict['experiment'] = experiment
			u = User.objects.get(username=experiment.user.username)
			context_dict['user'] = u
			try:
				treatment_data = Treatment.objects.filter(experiment=experiment)
			except Treatment.DoesNotExist:
				treatment_data = None
			try:
				row_data = ObsRow.objects.filter(obs_selector__experiment__name=experiment_name)
			except ObsRow.DoesNotExist:
				row_data = None
			try:
				plant_data = ObsPlant.objects.filter(obs_selector__experiment__name=experiment_name)
			except ObsPlant.DoesNotExist:
				plant_data = None
			try:
				samples_data = ObsSample.objects.filter(obs_selector__experiment__name=experiment_name)
			except ObsSample.DoesNotExist:
				samples_data = None
			try:
				stock_row_data = ObsRow.objects.filter(obs_selector__experiment__name=experiment_name)
			except ObsRow.DoesNotExist:
				stock_row_data = None
			try:
				stock_seed_data = Stock.objects.filter(passport__collecting__obs_selector__experiment__name=experiment_name)
			except:
				stock_seed_data = None
			try:
				measurement_data = Measurement.objects.filter(obs_selector__experiment__name=experiment_name)
			except Measurement.DoesNotExist:
				measurement_data = None
			context_dict['treatment_data'] = treatment_data
			context_dict['row_data'] = row_data
			context_dict['plant_data'] = plant_data
			context_dict['samples_data'] = samples_data
			context_dict['stock_row_data'] = stock_row_data
			context_dict['stock_seed_data'] = stock_seed_data
			context_dict['measurement_data'] = measurement_data
		except Experiment.DoesNotExist:
			pass
	if experiment_name == 'search':
		exp_list = get_experiment_list()
		context_dict['exp_list'] = exp_list
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/experiment.html', context_dict, context)

def checkbox_seed_inventory_sort(request):
	selected_stocks = {}
	checkbox_taxonomy_list = []
	checkbox_pedigree_list = []
	if request.session.get('checkbox_taxonomy', None):
		checkbox_taxonomy_list = request.session.get('checkbox_taxonomy')
		if request.session.get('checkbox_pedigree', None):
			checkbox_pedigree_list = request.session.get('checkbox_pedigree')
			for pedigree in checkbox_pedigree_list:
				for taxonomy in checkbox_taxonomy_list:
					stocks = Stock.objects.filter(pedigree=pedigree, passport__taxonomy__population=taxonomy)
					selected_stocks = list(chain(selected_stocks, stocks))[:1000]
		else:
			for taxonomy in checkbox_taxonomy_list:
				stocks = Stock.objects.filter(passport__taxonomy__population=taxonomy)
				selected_stocks = list(chain(selected_stocks, stocks))[:1000]
	else:
		if request.session.get('checkbox_pedigree', None):
			checkbox_pedigree_list = request.session.get('checkbox_pedigree')
			for pedigree in checkbox_pedigree_list:
				stocks = Stock.objects.filter(pedigree=pedigree)
				selected_stocks = list(chain(selected_stocks, stocks))[:1000]
		else:
			selected_stocks = Stock.objects.exclude(seed_id='0')[:1000]
	return selected_stocks

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
	if request.session.get('checkbox_measurement_experiment', None):
		context_dict['checkbox_measurement_experiment'] = request.session.get('checkbox_measurement_experiment')
	return context_dict

@login_required
def seed_inventory(request):
	context = RequestContext(request)
	context_dict = {}
	selected_stocks = checkbox_seed_inventory_sort(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['selected_stocks'] = selected_stocks
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/seed_inventory.html', context_dict, context)

def show_all_seedinv_taxonomy(request):
	context = RequestContext(request)
	context_dict = {}
	taxonomy_list = []
	if request.session.get('checkbox_pedigree', None):
		checkbox_pedigree_list = request.session.get('checkbox_pedigree')
		for pedigree in checkbox_pedigree_list:
			taxonomy = Stock.objects.filter(pedigree=pedigree).values('pedigree', 'passport__taxonomy__population', 'passport__taxonomy__species').distinct()[:1000]
			taxonomy_list = list(chain(taxonomy, taxonomy_list))
	else:
		taxonomy_list = Taxonomy.objects.filter(common_name='Maize')[:1000]
	context_dict = checkbox_session_variable_check(request)
	context_dict['taxonomy_list'] = taxonomy_list
	return render_to_response('lab/seed_taxonomy_list.html', context_dict, context)

def show_all_seedinv_pedigree(request):
	context = RequestContext(request)
	context_dict = {}
	pedigree_list = []
	if request.session.get('checkbox_taxonomy', None):
		checkbox_taxonomy_list = request.session.get('checkbox_taxonomy')
		for taxonomy in checkbox_taxonomy_list:
			pedigree = Stock.objects.filter(passport__taxonomy__population=taxonomy).values('pedigree', 'passport__taxonomy__population').distinct()[:1000]
			pedigree_list = list(chain(pedigree, pedigree_list))
	else:
		pedigree_list = Stock.objects.all().values('pedigree').distinct()[:1000]
	context_dict = checkbox_session_variable_check(request)
	context_dict['pedigree_list'] = pedigree_list
	return render_to_response('lab/seed_pedigree_list.html', context_dict, context)

def suggest_pedigree(request):
	context = RequestContext(request)
	context_dict = {}
	pedigree_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET['suggestion']
	else:
		starts_with = request.POST['suggestion']
	if starts_with:
		if request.session.get('checkbox_taxonomy', None):
			checkbox_taxonomy_list = request.session.get('checkbox_taxonomy')
			for taxonomy in checkbox_taxonomy_list:
				pedigree = Stock.objects.filter(pedigree__contains=starts_with, passport__taxonomy__population=taxonomy).values('pedigree', 'passport__taxonomy__population').distinct()[:1000]
				pedigree_list = list(chain(pedigree, pedigree_list))
		else:
			pedigree_list = Stock.objects.filter(pedigree__contains=starts_with).values('pedigree').distinct()[:1000]
	else:
		if request.session.get('checkbox_taxonomy', None):
			checkbox_taxonomy_list = request.session.get('checkbox_taxonomy')
			for taxonomy in checkbox_taxonomy_list:
				pedigree = Stock.objects.filter(passport__taxonomy__population=taxonomy).values('pedigree', 'passport__taxonomy__population').distinct()[:1000]
				pedigree_list = list(chain(pedigree, pedigree_list))
		else:
			pedigree_list = Stock.objects.all().values('pedigree').distinct()[:1000]
	context_dict = checkbox_session_variable_check(request)
	context_dict['pedigree_list'] = pedigree_list
	return render_to_response('lab/seed_pedigree_list.html', context_dict, context)

def suggest_taxonomy(request):
	context = RequestContext(request)
	context_dict = {}
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
				taxonomy = Stock.objects.filter(pedigree=pedigree, passport__taxonomy__population__contains=starts_with).values('pedigree', 'passport__taxonomy__population', 'passport__taxonomy__species').distinct()[:1000]
				taxonomy_list = list(chain(taxonomy, taxonomy_list))
		else:
			taxonomy_list = Taxonomy.objects.filter(population__contains=starts_with, common_name='Maize')[:1000]
	else:
		if request.session.get('checkbox_pedigree', None):
			checkbox_pedigree_list = request.session.get('checkbox_pedigree')
			for pedigree in checkbox_pedigree_list:
				taxonomy = Stock.objects.filter(pedigree=pedigree).values('pedigree', 'passport__taxonomy__population', 'passport__taxonomy__species').distinct()[:1000]
				taxonomy_list = list(chain(taxonomy, taxonomy_list))
		else:
			taxonomy_list = Taxonomy.objects.filter(common_name='Maize')[:1000]
	context_dict = checkbox_session_variable_check(request)
	context_dict['taxonomy_list'] = taxonomy_list
	return render_to_response('lab/seed_taxonomy_list.html', context_dict, context)

def select_pedigree(request):
	context = RequestContext(request)
	context_dict = {}
	checkbox_pedigree_list = request.POST.getlist('checkbox_pedigree')
	request.session['checkbox_pedigree'] = checkbox_pedigree_list
	selected_stocks = checkbox_seed_inventory_sort(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['selected_stocks'] = selected_stocks
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/seed_inventory.html', context_dict, context)

def select_taxonomy(request):
	context = RequestContext(request)
	context_dict = {}
	checkbox_taxonomy_list = request.POST.getlist('checkbox_taxonomy')
	request.session['checkbox_taxonomy'] = checkbox_taxonomy_list
	selected_stocks = checkbox_seed_inventory_sort(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['selected_stocks'] = selected_stocks
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/seed_inventory.html', context_dict, context)

def checkbox_seed_inventory_clear(request, clear_selected):
	context = RequestContext(request)
	context_dict = {}
	del request.session[clear_selected]
	selected_stocks = checkbox_seed_inventory_sort(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['selected_stocks'] = selected_stocks
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/seed_inventory.html', context_dict, context)

def select_stockpacket_from_stock(request):
	context = RequestContext(request)
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
	return render_to_response('lab/stock.html', context_dict, context)

@login_required
def row_data_from_experiment(request, experiment_name):
	context = RequestContext(request)
	context_dict = {}
	context_dict = checkbox_session_variable_check(request)
	row_data = ObsRow.objects.filter(obs_selector__experiment__name=experiment_name)
	context_dict['row_data'] = row_data
	context_dict['experiment_name'] = experiment_name
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/row_experiment_data.html', context_dict, context)

@login_required
def download_row_experiment(request, experiment_name):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="%s_rows.csv"' % (experiment_name)
	row_data = ObsRow.objects.filter(obs_selector__experiment__name=experiment_name)
	writer = csv.writer(response)
	writer.writerow(['Row ID', 'Row Name', 'Field', 'Source Stock', 'Range', 'Plot', 'Block', 'Rep', 'Kernel Num', 'Planting Date', 'Harvest Date', 'Comments'])
	for row in row_data:
		writer.writerow([row.row_id, row.row_name, row.field.field_name, row.stock.seed_id, row.range_num, row.plot, row.block, row.rep, row.kernel_num, row.planting_date, row.harvest_date, row.comments])
	return response

@login_required
def passport(request, passport_id):
	context = RequestContext(request)
	context_dict = {}
	passport = Passport.objects.get(id=passport_id)
	try:
		collecting_row = ObsRow.objects.get(obs_selector=passport.collecting.obs_selector)
	except ObsRow.DoesNotExist:
		collecting_row = None
	if passport.collecting.field.field_name != 'No Field':
		collecting_field = True
	else:
		collecting_field = None
	if passport.people.organization != 'No Source' and passport.people.organization != '' and passport.people.organization != 'NULL':
		collecting_source = True
	else:
		collecting_source = None
	context_dict['passport'] = passport
	context_dict['collecting_row'] = collecting_row
	context_dict['collecting_field'] = collecting_field
	context_dict['collecting_source'] = collecting_source
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/passport.html', context_dict, context)

@login_required
def isolate_inventory(request):
	context = RequestContext(request)
	context_dict = {}
	context_dict = checkbox_session_variable_check(request)
	selected_isolates = checkbox_isolate_sort(request)
	context_dict['selected_isolates'] = selected_isolates
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/isolate_inventory.html', context_dict, context)

def checkbox_isolate_sort(request):
	selected_isolates = {}
	checkbox_taxonomy_list = []
	checkbox_disease_list = []
	if request.session.get('checkbox_isolate_taxonomy', None):
		checkbox_taxonomy_list = request.session.get('checkbox_isolate_taxonomy_id')
		if request.session.get('checkbox_isolate_disease', None):
			checkbox_disease_list = request.session.get('checkbox_isolate_disease_id')
			for disease_id in checkbox_disease_list:
				for taxonomy_id in checkbox_taxonomy_list:
					isolates = Isolate.objects.filter(disease_info__id=disease_id, passport__taxonomy__id=taxonomy_id)
					selected_isolates = list(chain(selected_isolates, isolates))[:1000]
		else:
			for taxonomy_id in checkbox_taxonomy_list:
				isolates = Isolate.objects.filter(passport__taxonomy__id=taxonomy_id)
				selected_isolates = list(chain(selected_isolates, isolates))[:1000]
	else:
		if request.session.get('checkbox_isolate_disease', None):
			checkbox_disease_list = request.session.get('checkbox_isolate_disease_id')
			for disease_id in checkbox_disease_list:
				isolates = Isolate.objects.filter(disease_info__id=disease_id)
				selected_isolates = list(chain(selected_isolates, isolates))[:1000]
		else:
			selected_isolates = Isolate.objects.all()[:1000]
	return selected_isolates

def show_all_isolate_taxonomy(request):
	context = RequestContext(request)
	context_dict = {}
	isolate_taxonomy_list = []
	if request.session.get('checkbox_isolate_disease', None):
		checkbox_isolate_disease = request.session.get('checkbox_isolate_disease_id')
		for disease_id in checkbox_isolate_disease:
			taxonomy = Isolate.objects.filter(disease_info__id=disease_id).values('passport__taxonomy__id', 'disease_info__common_name', 'passport__taxonomy__genus', 'passport__taxonomy__alias', 'passport__taxonomy__race', 'passport__taxonomy__subtaxa', 'passport__taxonomy__species').distinct()[:1000]
			isolate_taxonomy_list = list(chain(taxonomy, isolate_taxonomy_list))
	else:
		isolate_taxonomy_list = Taxonomy.objects.filter(common_name='Isolate')[:1000]
	context_dict = checkbox_session_variable_check(request)
	context_dict['isolate_taxonomy_list'] = isolate_taxonomy_list
	return render_to_response('lab/isolate_taxonomy_list.html', context_dict, context)

def show_all_isolate_disease(request):
	context = RequestContext(request)
	context_dict = {}
	isolate_disease_list = []
	if request.session.get('checkbox_isolate_taxonomy', None):
		checkbox_isolate_taxonomy = request.session.get('checkbox_isolate_taxonomy_id')
		for taxonomy_id in checkbox_isolate_taxonomy:
			disease = Isolate.objects.filter(passport__taxonomy__id=taxonomy_id).values('disease_info__id', 'disease_info__common_name', 'passport__taxonomy__genus').distinct()[:1000]
			isolate_disease_list = list(chain(disease, isolate_disease_list))
	else:
		isolate_disease_list = DiseaseInfo.objects.all()[:1000]
	context_dict = checkbox_session_variable_check(request)
	context_dict['isolate_disease_list'] = isolate_disease_list
	return render_to_response('lab/isolate_disease_list.html', context_dict, context)

def suggest_isolate_taxonomy(request):
	context = RequestContext(request)
	context_dict = {}
	isolate_taxonomy_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET['suggestion']
	else:
		starts_with = request.POST['suggestion']
	if starts_with:
		if request.session.get('checkbox_isolate_disease', None):
			checkbox_isolate_disease = request.session.get('checkbox_isolate_disease_id')
			for disease_id in checkbox_isolate_disease:
				taxonomy = Isolate.objects.filter(disease_info__id=disease_id, passport__taxonomy__genus__contains=starts_with).values('passport__taxonomy__id', 'disease_info__common_name', 'passport__taxonomy__genus', 'passport__taxonomy__alias', 'passport__taxonomy__race', 'passport__taxonomy__subtaxa', 'passport__taxonomy__species').distinct()[:1000]
				isolate_taxonomy_list = list(chain(taxonomy, isolate_taxonomy_list))
		else:
			isolate_taxonomy_list = Taxonomy.objects.filter(genus__contains=starts_with, common_name='Isolate')[:1000]
	else:
		if request.session.get('checkbox_isolate_disease', None):
			checkbox_isolate_disease = request.session.get('checkbox_isolate_disease_id')
			for disease_id in checkbox_isolate_disease:
				taxonomy = Isolate.objects.filter(disease_info__id=disease_id).values('passport__taxonomy__id', 'disease_info__common_name', 'passport__taxonomy__genus', 'passport__taxonomy__alias', 'passport__taxonomy__race', 'passport__taxonomy__subtaxa', 'passport__taxonomy__species').distinct()[:1000]
				isolate_taxonomy_list = list(chain(taxonomy, isolate_taxonomy_list))
		else:
			isolate_taxonomy_list = Taxonomy.objects.filter(common_name='Isolate')[:1000]
	context_dict = checkbox_session_variable_check(request)
	context_dict['isolate_taxonomy_list'] = isolate_taxonomy_list
	return render_to_response('lab/isolate_taxonomy_list.html', context_dict, context)

def suggest_isolate_disease(request):
	context = RequestContext(request)
	context_dict = {}
	isolate_disease_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET['suggestion']
	else:
		starts_with = request.POST['suggestion']
	if starts_with:
		if request.session.get('checkbox_isolate_taxonomy', None):
			checkbox_isolate_taxonomy = request.session.get('checkbox_isolate_taxonomy_id')
			for taxonomy_id in checkbox_isolate_taxonomy:
				disease = Isolate.objects.filter(disease_info__common_name__contains=starts_with, passport__taxonomy__id=taxonomy_id).values('disease_info__id', 'disease_info__common_name', 'passport__taxonomy__genus').distinct()[:1000]
				isolate_disease_list = list(chain(disease, isolate_disease_list))
		else:
			isolate_disease_list = DiseaseInfo.objects.filter(common_name__contains=starts_with)[:1000]
	else:
		if request.session.get('checkbox_isolate_taxonomy', None):
			checkbox_isolate_taxonomy = request.session.get('checkbox_isolate_taxonomy_id')
			for taxonomy_id in checkbox_isolate_taxonomy:
				disease = Isolate.objects.filter(passport__taxonomy__id=taxonomy_id).values('disease_info__id', 'disease_info__common_name', 'passport__taxonomy__genus').distinct()[:1000]
				isolate_disease_list = list(chain(disease, isolate_disease_list))
		else:
			isolate_disease_list = DiseaseInfo.objects.all()[:1000]
	context_dict = checkbox_session_variable_check(request)
	context_dict['isolate_disease_list'] = isolate_disease_list
	return render_to_response('lab/isolate_disease_list.html', context_dict, context)

def select_isolate_taxonomy(request):
	context = RequestContext(request)
	context_dict = {}
	checkbox_isolate_taxonomy_id = []
	checkbox_isolate_taxonomy = []
	checkbox_isolate_taxonomy_id = request.POST.getlist('checkbox_isolate_taxonomy_id')
	for taxonomy_id in checkbox_isolate_taxonomy_id:
		taxonomy_name = Taxonomy.objects.filter(id=taxonomy_id).values('genus')
		checkbox_isolate_taxonomy = list(chain(taxonomy_name, checkbox_isolate_taxonomy))
	request.session['checkbox_isolate_taxonomy_id'] = checkbox_isolate_taxonomy_id
	request.session['checkbox_isolate_taxonomy'] = checkbox_isolate_taxonomy
	selected_isolates = checkbox_isolate_sort(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['selected_isolates'] = selected_isolates
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/isolate_inventory.html', context_dict, context)

def select_isolate_disease(request):
	context = RequestContext(request)
	context_dict = {}
	checkbox_isolate_disease_id = []
	checkbox_isolate_disease = []
	checkbox_isolate_disease_id = request.POST.getlist('checkbox_isolate_disease_id')
	for disease_id in checkbox_isolate_disease_id:
		disease_name = DiseaseInfo.objects.filter(id=disease_id).values('common_name')
		checkbox_isolate_disease = list(chain(disease_name, checkbox_isolate_disease))
	request.session['checkbox_isolate_disease_id'] = checkbox_isolate_disease_id
	request.session['checkbox_isolate_disease'] = checkbox_isolate_disease
	selected_isolates = checkbox_isolate_sort(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['selected_isolates'] = selected_isolates
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/isolate_inventory.html', context_dict, context)

def checkbox_isolate_inventory_clear(request, clear_selected):
	context = RequestContext(request)
	context_dict = {}
	del request.session[clear_selected]
	selected_isolates = checkbox_isolate_sort(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['selected_isolates'] = selected_isolates
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/isolate_inventory.html', context_dict, context)

def select_isolates(request):
	context = RequestContext(request)
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
	return render_to_response('lab/isolate.html', context_dict, context)

@login_required
def disease_info(request, disease_id):
	context = RequestContext(request)
	context_dict = {}
	try:
		disease_info = DiseaseInfo.objects.get(id=disease_id)
	except DiseaseInfo.DoesNotExist:
		disease_info = None
	context_dict['disease_info'] = disease_info
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/disease_info.html', context_dict, context)

@login_required
def field_info(request, field_id):
	context = RequestContext(request)
	context_dict = {}
	try:
		field_info = Field.objects.get(id=field_id)
	except DiseaseInfo.DoesNotExist:
		field_info = None
	context_dict['field_info'] = field_info
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/field.html', context_dict, context)

@login_required
def measurement_parameter(request, parameter_id):
	context = RequestContext(request)
	context_dict = {}
	try:
		parameter_info = MeasurementParameter.objects.get(id=parameter_id)
	except MeasurementParameter.DoesNotExist:
		parameter_info = None
	context_dict['parameter_info'] = parameter_info
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/measurement_parameter.html', context_dict, context)

@login_required
def new_experiment(request):
	context = RequestContext(request)
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
	return render_to_response('lab/new_experiment.html', context_dict, context)

@login_required
def log_data_select_obs(request):
	context = RequestContext(request)
	context_dict = {}

	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/log_data.html', context_dict, context)

@login_required
def serve_data_template_file(request, filename):
	path = '%s/%s.xlsx' % (settings.MEDIA_ROOT,filename)
	with open(path, "rb") as excel:
		data = excel.read()
		response = HttpResponse(data,content_type='application/vnd.ms-excel')
		response['Content-Disposition'] = 'attachment; filename=%s' % (filename)
		return response

@login_required
def row_data_browse(request):
	context = RequestContext(request)
	context_dict = {}
	row_data = sort_row_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['row_data'] = row_data
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/row_data.html', context_dict, context)

def sort_row_data(request):
	row_data = {}
	if request.session.get('checkbox_row_experiment_id_list', None):
		checkbox_row_experiment_id_list = request.session.get('checkbox_row_experiment_id_list')
		for row_experiment in checkbox_row_experiment_id_list:
			rows = ObsRow.objects.filter(obs_selector__experiment__id=row_experiment)
			row_data = list(chain(rows, row_data))[:2000]
	else:
		row_data = ObsRow.objects.all()[:2000]
	return row_data

@login_required
def download_row_data(request):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="selected_experiment_rows.csv"'
	row_data = sort_row_data(request)
	writer = csv.writer(response)
	writer.writerow(['Exp ID', 'Row ID', 'Row Name', 'Field', 'Source Stock', 'Range', 'Plot', 'Block', 'Rep', 'Kernel Num', 'Planting Date', 'Harvest Date', 'Comments'])
	for row in row_data:
		writer.writerow([row.obs_selector.experiment, row.row_id, row.row_name, row.field.field_name, row.stock.seed_id, row.range_num, row.plot, row.block, row.rep, row.kernel_num, row.planting_date, row.harvest_date, row.comments])
	return response

def suggest_row_experiment(request):
	context = RequestContext(request)
	context_dict = {}
	row_experiment_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET['suggestion']
	else:
		starts_with = request.POST['suggestion']
	if starts_with:
		row_experiment_list = ObsRow.objects.filter(obs_selector__experiment__name__contains=starts_with).values('obs_selector__experiment__name', 'obs_selector__experiment__field__field_name', 'obs_selector__experiment__field__id', 'obs_selector__experiment__id').distinct()[:1000]
	else:
		row_experiment_list = ObsRow.objects.all().values('obs_selector__experiment__name', 'obs_selector__experiment__field__field_name', 'obs_selector__experiment__field__id', 'obs_selector__experiment__id').distinct()[:1000]
	context_dict = checkbox_session_variable_check(request)
	context_dict['row_experiment_list'] = row_experiment_list
	return render_to_response('lab/row_experiment_list.html', context_dict, context)

def select_row_experiment(request):
	context = RequestContext(request)
	context_dict = {}
	row_data = []
	checkbox_row_experiment_name_list = []
	checkbox_row_experiment_list = request.POST.getlist('checkbox_row_experiment')
	for row_experiment in checkbox_row_experiment_list:
		rows = ObsRow.objects.filter(obs_selector__experiment__id=row_experiment)
		row_data = list(chain(rows, row_data))
	for experiment_id in checkbox_row_experiment_list:
		experiment_name = Experiment.objects.filter(id=experiment_id).values('name')
		checkbox_row_experiment_name_list = list(chain(experiment_name, checkbox_row_experiment_name_list))
	request.session['checkbox_row_experiment'] = checkbox_row_experiment_name_list
	request.session['checkbox_row_experiment_id_list'] = checkbox_row_experiment_list
	context_dict = checkbox_session_variable_check(request)
	context_dict['row_data'] = row_data
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/row_data.html', context_dict, context)

def checkbox_row_data_clear(request):
	context = RequestContext(request)
	context_dict = {}
	del request.session['checkbox_row_experiment']
	del request.session['checkbox_row_experiment_id_list']
	row_data = sort_row_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['row_data'] = row_data
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/row_data.html', context_dict, context)

def show_all_row_experiment(request):
	context = RequestContext(request)
	context_dict = {}
	row_experiment_list = ObsRow.objects.all().values('obs_selector__experiment__name', 'obs_selector__experiment__field__field_name', 'obs_selector__experiment__field__id', 'obs_selector__experiment__id').distinct()[:1000]
	context_dict = checkbox_session_variable_check(request)
	context_dict['row_experiment_list'] = row_experiment_list
	return render_to_response('lab/row_experiment_list.html', context_dict, context)

@login_required
def samples_data_browse(request):
	context = RequestContext(request)
	context_dict = {}
	samples_data = sort_samples_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['samples_data'] = samples_data
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/samples_data.html', context_dict, context)

def sort_samples_data(request):
	samples_data = {}
	if request.session.get('checkbox_samples_experiment_id_list', None):
		checkbox_samples_experiment_id_list = request.session.get('checkbox_samples_experiment_id_list')
		for samples_experiment in checkbox_samples_experiment_id_list:
			samples = ObsSample.objects.filter(obs_selector__experiment__id=samples_experiment)
			samples_data = list(chain(samples, samples_data))[:2000]
	else:
		samples_data = ObsSample.objects.all()[:2000]
	return samples_data


@login_required
def plant_data_browse(request):
	context = RequestContext(request)
	context_dict = {}
	plant_data = sort_plant_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['plant_data'] = plant_data
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/plant_data.html', context_dict, context)

def sort_plant_data(request):
	plant_data = {}
	if request.session.get('checkbox_plant_experiment_id_list', None):
		checkbox_plant_experiment_id_list = request.session.get('checkbox_plant_experiment_id_list')
		for plant_experiment in checkbox_plant_experiment_id_list:
			plants = ObsPlant.objects.filter(obs_selector__experiment__id=plant_experiment)
			plant_data = list(chain(plants, plant_data))[:2000]
	else:
		plant_data = ObsPlant.objects.all()[:2000]
	return plant_data

@login_required
def download_plant_data(request):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="selected_experiment_plants.csv"'
	plant_data = sort_plant_data(request)
	writer = csv.writer(response)
	writer.writerow(['Exp ID', 'Row ID', 'Plant ID', 'Plant Num', 'Comments'])
	for row in plant_data:
		writer.writerow([row.obs_selector.experiment, row.obs_row, row.plant_id, row.plant_num, row.comments])
	return response

def suggest_plant_experiment(request):
	context = RequestContext(request)
	context_dict = {}
	plant_experiment_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET['suggestion']
	else:
		starts_with = request.POST['suggestion']
	if starts_with:
		plant_experiment_list = ObsPlant.objects.filter(obs_selector__experiment__name__contains=starts_with).values('obs_selector__experiment__name', 'obs_selector__experiment__field__field_name', 'obs_selector__experiment__field__id', 'obs_selector__experiment__id').distinct()[:1000]
	else:
		plant_experiment_list = ObsPlant.objects.all().values('obs_selector__experiment__name', 'obs_selector__experiment__field__field_name', 'obs_selector__experiment__field__id', 'obs_selector__experiment__id').distinct()[:1000]
	context_dict = checkbox_session_variable_check(request)
	context_dict['plant_experiment_list'] = plant_experiment_list
	return render_to_response('lab/plant_experiment_list.html', context_dict, context)

def select_plant_experiment(request):
	context = RequestContext(request)
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
	return render_to_response('lab/plant_data.html', context_dict, context)

def checkbox_plant_data_clear(request):
	context = RequestContext(request)
	context_dict = {}
	del request.session['checkbox_plant_experiment']
	del request.session['checkbox_plant_experiment_id_list']
	plant_data = sort_plant_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['plant_data'] = plant_data
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/plant_data.html', context_dict, context)

def show_all_plant_experiment(request):
	context = RequestContext(request)
	context_dict = {}
	plant_experiment_list = ObsPlant.objects.all().values('obs_selector__experiment__name', 'obs_selector__experiment__field__field_name', 'obs_selector__experiment__field__id', 'obs_selector__experiment__id').distinct()[:1000]
	context_dict = checkbox_session_variable_check(request)
	context_dict['plant_experiment_list'] = plant_experiment_list
	return render_to_response('lab/plant_experiment_list.html', context_dict, context)

@login_required
def plant_data_from_experiment(request, experiment_name):
	context = RequestContext(request)
	context_dict = {}
	plant_data = ObsPlant.objects.filter(obs_selector__experiment__name=experiment_name)
	context_dict['plant_data'] = plant_data
	context_dict['experiment_name'] = experiment_name
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/plant_experiment_data.html', context_dict, context)

@login_required
def download_plant_experiment(request, experiment_name):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="%s_plants.csv"' % (experiment_name)
	plant_data = ObsPlant.objects.filter(obs_selector__experiment__name=experiment_name)
	writer = csv.writer(response)
	writer.writerow(['Plant ID', 'Plant Num', 'Row ID', 'Stock ID', 'Comments'])
	for row in plant_data:
		writer.writerow([row.plant_id, row.plant_num, row.obs_row.row_id, row.stock.seed_id, row.comments])
	return response

@login_required
def measurement_data_browse(request):
	context = RequestContext(request)
	context_dict = {}
	measurement_data = sort_measurement_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['measurement_data'] = measurement_data
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/measurement_data.html', context_dict, context)

def sort_measurement_data(request):
	measurement_data = {}
	if request.session.get('checkbox_measurement_experiment_id_list', None):
		checkbox_measurement_experiment_id_list = request.session.get('checkbox_measurement_experiment_id_list')
		for measurement_experiment in checkbox_measurement_experiment_id_list:
			measurements = Measurement.objects.filter(obs_selector__experiment__id=measurement_experiment)
			measurement_data = list(chain(measurements, measurement_data))[:2000]
	else:
		measurement_data = Measurement.objects.all()[:2000]

	obs_types = [ObsRow, ObsPlant, ObsSample, ObsEnv]
	for data in measurement_data:
		for obs_type in obs_types:
			try:
				obs = obs_type.objects.get(obs_selector=data.obs_selector.id)
				obs_exists = True
			except obs_type.DoesNotExist:
				obs_exists = False
			if obs_exists == True:
				if obs_type == ObsRow:
					data.obs_display = obs.row_id
					data.obs_url = '/lab/row/%s/' % (obs.id)
				if obs_type == ObsPlant:
					data.obs_display = obs.plant_id
					data.obs_url = '/lab/plant/%s/' % (obs.id)
				if obs_type == ObsSample:
					data.obs_display = obs.sample_id
					data.obs_url = '/lab/sample/%s/' % (obs.id)
				if obs_type == ObsEnv:
					data.obs_display = obs.environment_id
					data.obs_url = '/lab/environment/%s/' % (obs.id)
	return measurement_data

@login_required
def download_measurement_data(request):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="selected_experiment_measurements.csv"'
	measurement_data = sort_measurement_data(request)
	writer = csv.writer(response)
	writer.writerow(['Exp ID', 'Obs ID', 'User', 'Time', 'Parameter Type', 'Parameter', 'Value', 'Units', 'Trait ID Buckler', 'Comments'])
	for row in measurement_data:
		writer.writerow([row.obs_selector.experiment, row.obs_display, row.user, row.time_of_measurement, row.measurement_parameter.parameter_type, row.measurement_parameter, row. value, row.measurement_parameter.unit_of_measure, row.measurement_parameter.trait_id_buckler, row.comments])
	return response

def suggest_measurement_experiment(request):
	context = RequestContext(request)
	context_dict = {}
	measurement_experiment_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET['suggestion']
	else:
		starts_with = request.POST['suggestion']
	if starts_with:
		measurement_experiment_list = Measurement.objects.filter(obs_selector__experiment__name__contains=starts_with).values('obs_selector__experiment__name', 'obs_selector__experiment__field__field_name', 'obs_selector__experiment__field__id', 'obs_selector__experiment__id').distinct()[:1000]
	else:
		measurement_experiment_list = Measurement.objects.all().values('obs_selector__experiment__name', 'obs_selector__experiment__field__field_name', 'obs_selector__experiment__field__id', 'obs_selector__experiment__id').distinct()[:1000]
	context_dict = checkbox_session_variable_check(request)
	context_dict['measurement_experiment_list'] = measurement_experiment_list
	return render_to_response('lab/measurement_experiment_list.html', context_dict, context)

def select_measurement_experiment(request):
	context = RequestContext(request)
	context_dict = {}
	measurement_data = []
	checkbox_measurement_experiment_name_list = []
	checkbox_measurement_experiment_list = request.POST.getlist('checkbox_measurement_experiment')
	for experiment_id in checkbox_measurement_experiment_list:
		experiment_name = Experiment.objects.filter(id=experiment_id).values('name')
		checkbox_measurement_experiment_name_list = list(chain(experiment_name, checkbox_measurement_experiment_name_list))
	request.session['checkbox_measurement_experiment'] = checkbox_measurement_experiment_name_list
	request.session['checkbox_measurement_experiment_id_list'] = checkbox_measurement_experiment_list
	measurement_data = sort_measurement_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['measurement_data'] = measurement_data
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/measurement_data.html', context_dict, context)

def checkbox_measurement_data_clear(request):
	context = RequestContext(request)
	context_dict = {}
	del request.session['checkbox_measurement_experiment']
	del request.session['checkbox_measurement_experiment_id_list']
	measurement_data = sort_measurement_data(request)
	context_dict = checkbox_session_variable_check(request)
	context_dict['measurement_data'] = measurement_data
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/measurement_data.html', context_dict, context)

def show_all_measurement_experiment(request):
	context = RequestContext(request)
	context_dict = {}
	measurement_experiment_list = Measurement.objects.all().values('obs_selector__experiment__name', 'obs_selector__experiment__field__field_name', 'obs_selector__experiment__field__id', 'obs_selector__experiment__id').distinct()[:1000]
	context_dict = checkbox_session_variable_check(request)
	context_dict['measurement_experiment_list'] = measurement_experiment_list
	return render_to_response('lab/measurement_experiment_list.html', context_dict, context)

@login_required
def measurement_data_from_experiment(request, experiment_name):
	context = RequestContext(request)
	context_dict = {}
	phenotype_data = Measurement.objects.filter(obs_selector__experiment__name=experiment_name)
	obs_types = [ObsRow, ObsPlant, ObsSample, ObsEnv]
	for data in phenotype_data:
		for obs_type in obs_types:
			try:
				obs = obs_type.objects.get(obs_selector=data.obs_selector.id)
				obs_exists = True
			except obs_type.DoesNotExist:
				obs_exists = False
			if obs_exists == True:
				if obs_type == ObsRow:
					data.obs_display = obs.row_id
					data.obs_url = '/lab/row/%s/' % (obs.id)
				if obs_type == ObsPlant:
					data.obs_display = obs.plant_id
					data.obs_url = '/lab/plant/%s/' % (obs.id)
				if obs_type == ObsSample:
					data.obs_display = obs.sample_id
					data.obs_url = '/lab/sample/%s/' % (obs.id)
				if obs_type == ObsEnv:
					data.obs_display = obs.environment_id
					data.obs_url = '/lab/environment/%s/' % (obs.id)
	context_dict['phenotype_data'] = phenotype_data
	context_dict['experiment_name'] = experiment_name
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/measurement_experiment_data.html', context_dict, context)

@login_required
def download_measurement_experiment(request, experiment_name):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="%s_measurements.csv"' % (experiment_name)
	phenotype_data = Measurement.objects.filter(obs_selector__experiment__name=experiment_name)
	obs_types = [ObsRow, ObsPlant, ObsSample, ObsEnv]
	for data in phenotype_data:
		for obs_type in obs_types:
			try:
				obs = obs_type.objects.get(obs_selector=data.obs_selector.id)
				obs_exists = True
			except obs_type.DoesNotExist:
				obs_exists = False
			if obs_exists == True:
				if obs_type == ObsRow:
					data.obs_display = obs.row_id
					data.obs_url = '/lab/row/%s/' % (obs.id)
				if obs_type == ObsPlant:
					data.obs_display = obs.plant_id
					data.obs_url = '/lab/plant/%s/' % (obs.id)
				if obs_type == ObsSample:
					data.obs_display = obs.sample_id
					data.obs_url = '/lab/sample/%s/' % (obs.id)
				if obs_type == ObsEnv:
					data.obs_display = obs.environment_id
					data.obs_url = '/lab/environment/%s/' % (obs.id)
	writer = csv.writer(response)
	writer.writerow(['Obs', 'User', 'Time', 'Parameter Type', 'Parameter', 'Value', 'Units', 'TraitID Buckler', 'Comments'])
	for row in phenotype_data:
		writer.writerow([row.obs_display, row.user, row.time_of_measurement, row.measurement_parameter.parameter_type, row.measurement_parameter.parameter, row.value, row.measurement_parameter.unit_of_measure, row.measurement_parameter.trait_id_buckler, row.comments])
	return response

@login_required
def genotype_data_browse(request):
	context = RequestContext(request)
	context_dict = {}

	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/index.html', context_dict, context)

@login_required
def seedinv_from_experiment(request, experiment_name):
	context = RequestContext(request)
	context_dict = {}
	try:
		seedinv_from_row_experiment = ObsRow.objects.filter(obs_selector__experiment__name=experiment_name)
	except ObsRow.DoesNotExist:
		seedinv_from_row_experiment = None
	try:
		seedinv_from_sample_experiment = ObsSample.objects.filter(obs_selector__experiment__name=experiment_name)
	except ObsSample.DoesNotExist:
		seedinv_from_sample_experiment = None
	context_dict['seedinv_from_row_experiment'] = seedinv_from_row_experiment
	context_dict['seedinv_from_sample_experiment'] = seedinv_from_sample_experiment
	context_dict['experiment_name'] = experiment_name
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/seed_from_experiment.html', context_dict, context)

@login_required
def seedinv_collected_from_experiment(request, experiment_name):
	context = RequestContext(request)
	context_dict = {}
	try:
		seedinv_stock = Stock.objects.filter(passport__collecting__obs_selector__experiment__name=experiment_name)
	except:
		seedinv_stock = None
	context_dict['seedinv_stock'] = seedinv_stock
	context_dict['experiment_name'] = experiment_name
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/seed_collected_from_experiment.html', context_dict, context)

@login_required
def single_stock_info(request, stock_id):
	context = RequestContext(request)
	context_dict = {}
	try:
		stock_info = Stock.objects.get(id=stock_id)
	except Stock.DoesNotExist:
		stock_info = None

	if stock_info is not None:
		try:
			obs_row = ObsRow.objects.get(obs_selector_id=stock_info.passport.collecting.obs_selector_id)
			stock_info.obs_row_id = obs_row.id
			stock_info.row_id = obs_row.row_id
		except ObsRow.DoesNotExist:
			obs_row = None
		context_dict['stock_info'] = stock_info

	obs_row_stock_0 = ObsRow.objects.filter(stock_id=stock_id)
	context_dict['obs_row_stock_0'] = obs_row_stock_0

	"""step = 1
	iterate = True
	while iterate == True:
		obs_row_stock_prev = 'obs_row_stock_%d' % (step-1)
		for row_stock in context_dict[obs_row_stock_prev]:
			obs_row_stock_index = 'obs_row_stock_%d' % (step)
			try:
				obs_row_stock_info = ObsRow.objects.get(obs_selector=row_stock.stock.passport.collecting.obs_selector_id)
				if obs_row_stock_info:
					context_dict[obs_row_stock_index] = obs_row_stock_info
					step = step + 1
				else:
					iterate = False
			except ObsRow.DoesNotExist:
				iterate = False"""

	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/stock_info.html', context_dict, context)

@login_required
def single_row_info(request, obs_row_id):
	context = RequestContext(request)
	context_dict = {}
	row_info = ObsRow.objects.get(id=obs_row_id)

	context_dict['row_info'] = row_info
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/row_info.html', context_dict, context)

@login_required
def log_data_online(request, data_type):
	context = RequestContext(request)
	context_dict = {}

	if data_type == 'seed_inventory':
		data_type_title = 'Log Seed Info'
		LogDataOnlineFormSet = formset_factory(LogSeedDataOnlineForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				for form in log_data_online_form_set:
					try:
						seed_id = form.cleaned_data['seed_id']
						seed_name = form.cleaned_data['seed_name']
						cross_type = form.cleaned_data['cross_type']
						pedigree = form.cleaned_data['pedigree']
						stock_status = form.cleaned_data['stock_status']
						stock_date = form.cleaned_data['stock_date']
						inoculated = form.cleaned_data['inoculated']
						stock_comments = form.cleaned_data['stock_comments']
						genus = form.cleaned_data['genus']
						species = form.cleaned_data['species']
						population = form.cleaned_data['population']
						population = form.cleaned_data['population']
						collection_field = form.cleaned_data['collection_field']
						collection_row = form.cleaned_data['collection_row']
						collection_plant = form.cleaned_data['collection_plant']
						collection_user = form.cleaned_data['collection_user']
						collection_date = form.cleaned_data['collection_date']
						collection_method = form.cleaned_data['collection_method']
						collection_comments = form.cleaned_data['collection_comments']
						source_fname = form.cleaned_data['source_fname']
						source_lname = form.cleaned_data['source_lname']
						source_organization = form.cleaned_data['source_organization']
						source_phone = form.cleaned_data['source_phone']
						source_email = form.cleaned_data['source_email']
						source_comments = form.cleaned_data['source_comments']

						new_taxonomy = Taxonomy.objects.get_or_create(genus=genus, species=species, population=population, common_name='Maize', alias='NULL', race='NULL', subtaxa='NULL')
						new_people = People.objects.get_or_create(first_name=source_fname, last_name=source_lname, organization=source_organization, phone=source_phone, email=source_email, comments=source_comments)
						if collection_row:
							source = ObsRow.objects.get(row_id=collection_row)
							new_collecting = Collecting.objects.get_or_create(field=collection_field, user=collection_user, obs_selector=source.obs_selector, collection_date=collection_date, collection_method=collection_method, comments=collection_comments)
							new_passport = Passport.objects.get_or_create(collecting=Collecting.objects.get(field=collection_field, user=collection_user, obs_selector=source.obs_selector, collection_date=collection_date, collection_method=collection_method, comments=collection_comments), taxonomy=Taxonomy.objects.get(genus=genus, species=species, population=population, common_name='Maize', alias='NULL', race='NULL', subtaxa='NULL'), people=People.objects.get(first_name=source_fname, last_name=source_lname, organization=source_organization, phone=source_phone, email=source_email, comments=source_comments))
							new_stock = Stock.objects.get_or_create(passport=Passport.objects.get(collecting=Collecting.objects.get(field=collection_field, user=collection_user, obs_selector=source.obs_selector, collection_date=collection_date, collection_method=collection_method, comments=collection_comments), taxonomy=Taxonomy.objects.get(genus=genus, species=species, population=population, common_name='Maize', alias='NULL', race='NULL', subtaxa='NULL'), people=People.objects.get(first_name=source_fname, last_name=source_lname, organization=source_organization, phone=source_phone, email=source_email, comments=source_comments)), seed_id=seed_id, seed_name=seed_name, cross_type=cross_type, pedigree=pedigree, stock_status=stock_status, stock_date=stock_date, inoculated=inoculated, comments=stock_comments)
						elif collection_plant:
							source = ObsRow.objects.get(row_id=collection_row)
							new_collecting = Collecting.objects.get_or_create(field=collection_field, user=collection_user, obs_selector=source.obs_selector, collection_date=collection_date, collection_method=collection_method, comments=collection_comments)
							new_passport = Passport.objects.get_or_create(collecting=Collecting.objects.get(field=collection_field, user=collection_user, obs_selector=source.obs_selector, collection_date=collection_date, collection_method=collection_method, comments=collection_comments), taxonomy=Taxonomy.objects.get(genus=genus, species=species, population=population, common_name='Maize', alias='NULL', race='NULL', subtaxa='NULL'), people=People.objects.get(first_name=source_fname, last_name=source_lname, organization=source_organization, phone=source_phone, email=source_email, comments=source_comments))
							new_stock = Stock.objects.get_or_create(passport=Passport.objects.get(collecting=Collecting.objects.get(field=collection_field, user=collection_user, obs_selector=source.obs_selector, collection_date=collection_date, collection_method=collection_method, comments=collection_comments), taxonomy=Taxonomy.objects.get(genus=genus, species=species, population=population, common_name='Maize', alias='NULL', race='NULL', subtaxa='NULL'), people=People.objects.get(first_name=source_fname, last_name=source_lname, organization=source_organization, phone=source_phone, email=source_email, comments=source_comments)), seed_id=seed_id, seed_name=seed_name, cross_type=cross_type, pedigree=pedigree, stock_status=stock_status, stock_date=stock_date, inoculated=inoculated, comments=stock_comments)
						else:
							new_collecting = Collecting.objects.get_or_create(field=collection_field, user=collection_user, obs_selector_id=1, collection_date=collection_date, collection_method=collection_method, comments=collection_comments)
							new_passport = Passport.objects.get_or_create(collecting=Collecting.objects.get(field=collection_field, user=collection_user, obs_selector_id=1, collection_date=collection_date, collection_method=collection_method, comments=collection_comments), taxonomy=Taxonomy.objects.get(genus=genus, species=species, population=population, common_name='Maize', alias='NULL', race='NULL', subtaxa='NULL'), people=People.objects.get(first_name=source_fname, last_name=source_lname, organization=source_organization, phone=source_phone, email=source_email, comments=source_comments))
							new_stock = Stock.objects.get_or_create(passport=Passport.objects.get(collecting=Collecting.objects.get(field=collection_field, user=collection_user, obs_selector_id=1, collection_date=collection_date, collection_method=collection_method, comments=collection_comments), taxonomy=Taxonomy.objects.get(genus=genus, species=species, population=population, common_name='Maize', alias='NULL', race='NULL', subtaxa='NULL'), people=People.objects.get(first_name=source_fname, last_name=source_lname, organization=source_organization, phone=source_phone, email=source_email, comments=source_comments)), seed_id=seed_id, seed_name=seed_name, cross_type=cross_type, pedigree=pedigree, stock_status=stock_status, stock_date=stock_date, inoculated=inoculated, comments=stock_comments)
					except KeyError:
						pass
			else:
				print(log_data_online_form_set.errors)
		else:
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'seed_packet':
		data_type_title = 'Inventory Seed Packets'
		LogDataOnlineFormSet = formset_factory(LogStockPacketOnlineForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				for form in log_data_online_form_set:
					try:
						seed_id = form.cleaned_data['seed_id']
						weight = form.cleaned_data['weight']
						num_seeds = form.cleaned_data['num_seeds']
						packet_comments = form.cleaned_data['packet_comments']
						locality = form.cleaned_data['locality']
						building_name = form.cleaned_data['building_name']
						location_name = form.cleaned_data['location_name']
						room = form.cleaned_data['room']
						shelf = form.cleaned_data['shelf']
						column = form.cleaned_data['column']
						box_name = form.cleaned_data['box_name']
						location_comments = form.cleaned_data['location_comments']

						new_location = Location.objects.get_or_create(locality=locality, building_name=building_name, location_name=location_name, room=room, shelf=shelf, column=column, box_name=box_name, comments=location_comments)
						new_stock_packet = StockPacket.objects.get_or_create(stock=Stock.objects.get(seed_id=seed_id), location=Location.objects.get(locality=locality, building_name=building_name, location_name=location_name, room=room, shelf=shelf, column=column, box_name=box_name, comments=location_comments), weight=weight, num_seeds=num_seeds, comments=packet_comments)

					except KeyError:
						pass
			else:
				print(log_data_online_form_set.errors)
		else:
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'plant':
		data_type_title = 'Log Plant Info'
		LogDataOnlineFormSet = formset_factory(LogPlantsOnlineForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				for form in log_data_online_form_set:
					try:
						experiment = form.cleaned_data['experiment']
						plant_id = form.cleaned_data['plant_id']
						plant_num = form.cleaned_data['plant_num']
						seed_id = form.cleaned_data['seed_id']
						row_id = form.cleaned_data['row_id']
						plant_comments = form.cleaned_data['plant_comments']

						new_obs_selector = ObsSelector.objects.create(experiment=experiment)
						new_plant = ObsPlant.objects.get_or_create(obs_selector=ObsSelector.objects.order_by('-pk')[0], obs_row=ObsRow.objects.get(row_id=row_id), plant_id=plant_id, plant_num=plant_num, comments=plant_comments)

					except KeyError:
						pass
			else:
				print(log_data_online_form_set.errors)
		else:
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'row':
		data_type_title = 'Log Row Info'
		LogDataOnlineFormSet = formset_factory(LogRowsOnlineForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
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

						new_obs_selector = ObsSelector.objects.create(experiment=experiment)
						new_row = ObsRow.objects.get_or_create(obs_selector=ObsSelector.objects.order_by('-pk')[0], field=field, stock=Stock.objects.get(seed_id=seed_id), row_id=row_id, row_name=row_name, range_num=range_num, plot=plot, block=block, rep=rep, kernel_num=kernel_num, planting_date=planting_date, harvest_date=harvest_date, comments=row_comments)

					except KeyError:
						pass
			else:
				print(log_data_online_form_set.errors)
		else:
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'environment':
		data_type_title = 'Log Environment Info'
		LogDataOnlineFormSet = formset_factory(LogEnvironmentsOnlineForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				for form in log_data_online_form_set:
					try:
						experiment = form.cleaned_data['experiment']
						environment_id = form.cleaned_data['environment_id']
						field = form.cleaned_data['field']
						longitude = form.cleaned_data['longitude']
						latitude = form.cleaned_data['latitude']
						environment_comments = form.cleaned_data['environment_comments']

						new_obs_selector = ObsSelector.objects.create(experiment=experiment)
						new_environment = ObsEnv.objects.get_or_create(obs_selector=ObsSelector.objects.order_by('-pk')[0], field=field, environment_id=environment_id, longitude=longitude, latitude=latitude, comments=environment_comments)

					except KeyError:
						pass
			else:
				print(log_data_online_form_set.errors)
		else:
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'samples':
		data_type_title = 'Log Samples Info'
		LogDataOnlineFormSet = formset_factory(LogSamplesOnlineForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				for form in log_data_online_form_set:
					try:
						experiment = form.cleaned_data['experiment']
						sample_id = form.cleaned_data['sample_id']
						sample_type = form.cleaned_data['sample_type']
						source_seed_id = form.cleaned_data['source_seed_id']
						source_row_id = form.cleaned_data['source_row_id']
						source_plant_id = form.cleaned_data['source_plant_id']
						source_sample_id = form.cleaned_data['source_sample_id']
						weight = form.cleaned_data['weight']
						kernel_num = form.cleaned_data['kernel_num']
						sample_comments = form.cleaned_data['sample_comments']

						new_obs_selector = ObsSelector.objects.create(experiment=experiment)
						new_sample = ObsSample.objects.get_or_create(obs_selector=ObsSelector.objects.order_by('-pk')[0], obs_plant=ObsPlant.objects.get(plant_id=source_plant_id), obs_row=ObsRow.objects.get(row_id=source_row_id), stock=Stock.objects.get(seed_id=source_seed_id), source_sample=ObsSample.objects.get(sample_id=source_sample_id), sample_id=sample_id, sample_type=sample_type, weight=weight, kernel_num=kernel_num, comments=sample_comments)

					except KeyError:
						pass
			else:
				print(log_data_online_form_set.errors)
		else:
			log_data_online_form_set = LogDataOnlineFormSet

	if data_type == 'measurement':
		data_type_title = 'Log Measurements'
		LogDataOnlineFormSet = formset_factory(LogMeasurementsOnlineForm, extra=10)
		if request.method == 'POST':
			log_data_online_form_set = LogDataOnlineFormSet(request.POST)
			if log_data_online_form_set.is_valid():
				for form in log_data_online_form_set:
					try:
						row_id = form.cleaned_data['row_id']
						plant_id = form.cleaned_data['plant_id']
						sample_id = form.cleaned_data['sample_id']
						environment_id = form.cleaned_data['environment_id']
						measurement_parameter = form.cleaned_data['measurement_parameter']
						user = form.cleaned_data['user']
						time_of_measurement = form.cleaned_data['time_of_measurement']
						value = form.cleaned_data['value']
						measurement_comments = form.cleaned_data['measurement_comments']

						if row_id != '':
							obs_row = ObsRow.objects.get(row_id=row_id)
							new_measurement = Measurement.objects.get_or_create(obs_selector_id=obs_row.obs_selector_id, measurement_parameter=measurement_parameter, user=user, time_of_measurement=time_of_measurement, value=value, comments=measurement_comments)
						elif plant_id != '':
							obs_plant = ObsPlant.objects.get(plant_id=plant_id)
							new_measurement = Measurement.objects.get_or_create(obs_selector_id=obs_plant.obs_selector_id, measurement_parameter=measurement_parameter, user=user, time_of_measurement=time_of_measurement, value=value, comments=measurement_comments)
						elif sample_id != '':
							obs_sample = ObsPlant.objects.get(sample_id=sample_id)
							new_measurement = Measurement.objects.get_or_create(obs_selector_id=obs_sample.obs_selector_id, measurement_parameter=measurement_parameter, user=user, time_of_measurement=time_of_measurement, value=value, comments=measurement_comments)
						elif environment_id != '':
							obs_env = ObsPlant.objects.get(environment_id=environment_id)
							new_measurement = Measurement.objects.get_or_create(obs_selector_id=obs_env.obs_selector_id, measurement_parameter=measurement_parameter, user=user, time_of_measurement=time_of_measurement, value=value, comments=measurement_comments)

					except KeyError:
						pass
			else:
				print(log_data_online_form_set.errors)
		else:
			log_data_online_form_set = LogDataOnlineFormSet

	context_dict['log_data_online_form_set'] = log_data_online_form_set
	context_dict['data_type'] = data_type
	context_dict['data_type_title'] = data_type_title
	context_dict['logged_in_user'] = request.user.username
	return render_to_response('lab/log_data_online.html', context_dict, context)

@login_required
def new_treatment(request):
	context = RequestContext(request)
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
	return render_to_response('lab/new_treatment.html', context_dict, context)
