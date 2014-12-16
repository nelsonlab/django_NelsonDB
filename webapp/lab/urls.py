from django.conf.urls import patterns, url
from lab import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^about/goals/$', views.about_goals, name='about_goals'),
    url(r'^about/collaborators/$', views.about_collaborators, name='about_collaborators'),
    url(r'^about/people/(?P<people_selection>\w+)/$', views.about_people, name='about_people'),
    url(r'^about/literature/$', views.about_literature, name='about_literature'),
	url(r'^error_prelim/$', views.error_prelim, name='error_prelim'),
	url(r'^experiment/(?P<experiment_name_url>\w+)/$', views.experiment, name='experiment'),
	url(r'^register/$', views.register, name='register'),
	url(r'^login/$', views.user_login, name='login'),
	url(r'^logout/$', views.user_logout, name='logout'),
    url(r'^change_password/$', views.profile_change_password, name ='profile_change_password'),
    url(r'^edit_profile/$', views.edit_profile, name ='edit_profile'),
	url(r'^profile/(?P<profile_name>\w+)/$', views.profile, name ='profile'),
	url(r'^goto/$', views.track_url, name='track_url'),
    url(r'^seed_inventory/$', views.seed_inventory, name='seed_inventory'),
    url(r'^seed_inventory/select_pedigree/$', views.select_pedigree, name='select_pedigree'),
    url(r'^seed_inventory/select_taxonomy/$', views.select_taxonomy, name='select_taxonomy'),
    url(r'^seed_inventory/select_stocks/$', views.select_stockpacket_from_stock, name='select_stockpacket_from_stock'),
    url(r'^seed_inventory/suggest_pedigree/$', views.suggest_pedigree, name='suggest_pedigree'),
    url(r'^seed_inventory/suggest_taxonomy/$', views.suggest_taxonomy, name='suggest_taxonomy'),
    url(r'^seed_inventory/show_all_taxonomy/$', views.show_all_seedinv_taxonomy, name='show_all_seedinv_taxonomy'),
    url(r'^seed_inventory/show_all_pedigree/$', views.show_all_seedinv_pedigree, name='show_all_seedinv_pedigree'),
    url(r'^seed_inventory/checkbox_clear/(?P<clear_selected>\w+)/$', views.checkbox_seed_inventory_clear, name='checkbox_seed_inventory_clear'),
    url(r'^seed_inventory/experiment/(?P<experiment_name>\w+)/$', views.seedinv_from_experiment, name='seedinv_from_experiment'),
    url(r'^inventory/passport/(?P<passport_id>\d+)/$', views.passport, name='passport'),
    url(r'^isolate_inventory/$', views.isolate_inventory, name='isolate_inventory'),
    url(r'^isolate_inventory/suggest_isolate_taxonomy/$', views.suggest_isolate_taxonomy, name='suggest_isolate_taxonomy'),
    url(r'^isolate_inventory/suggest_isolate_disease/$', views.suggest_isolate_disease, name='suggest_isolate_disease'),
    url(r'^isolate_inventory/select_isolate_disease/$', views.select_isolate_disease, name='select_isolate_disease'),
    url(r'^isolate_inventory/select_isolate_taxonomy/$', views.select_isolate_taxonomy, name='select_isolate_taxonomy'),
    url(r'^isolate_inventory/show_all_disease/$', views.show_all_isolate_disease, name='show_all_isolate_disease'),
    url(r'^isolate_inventory/show_all_taxonomy/$', views.show_all_isolate_taxonomy, name='show_all_isolate_taxonomy'),
    url(r'^isolate_inventory/checkbox_clear/(?P<clear_selected>\w+)/$', views.checkbox_isolate_inventory_clear, name='checkbox_isolate_inventory_clear'),
    url(r'^isolate_inventory/select_isolates/$', views.select_isolates, name='select_isolates'),
    url(r'^data/phenotype/$', views.phenotype_data_browse, name='phenotype_data_browse'),
    url(r'^data/phenotype/experiment/(?P<experiment_name>\w+)/$', views.phenotype_data_from_experiment, name='phenotype_data_from_experiment'),
    url(r'^data/genotype/$', views.genotype_data_browse, name='genotype_data_browse'),
    url(r'^data/plant/$', views.plant_data_browse, name='plant_data_browse'),
    url(r'^data/samples/$', views.samples_data_browse, name='samples_data_browse'),
    url(r'^data/row/$', views.row_data_browse, name='row_data_browse'),
    url(r'^data/row/suggest_row_experiment/$', views.suggest_row_experiment, name='suggest_row_experiment'),
    url(r'^data/row/select_row_experiment/$', views.select_row_experiment, name='select_row_experiment'),
    url(r'^data/row/experiment/(?P<experiment_name>\w+)/$', views.row_data_from_experiment, name='row_data_from_experiment'),
    url(r'^data/row/checkbox_clear/$', views.checkbox_row_data_clear, name='checkbox_row_data_clear'),
    url(r'^disease_info/(?P<disease_id>\d+)/$', views.disease_info, name='disease_info'),
    url(r'^field/(?P<field_id>\d+)/$', views.field_info, name='field_info'),
    url(r'^stock/(?P<stock_id>\d+)/$', views.single_stock_info, name='single_stock_info'),
    url(r'^row/(?P<obs_row_id>\d+)/$', views.single_row_info, name='single_row_info'),
    url(r'^measurement_parameter/(?P<parameter_id>\d+)/$', views.measurement_parameter, name='measurement_parameter'),
    url(r'^new_experiment/$', views.new_experiment, name='new_experiment'),
    url(r'^log_data/select_obs/$', views.log_data_select_obs, name='log_data_select_obs'),
    url(r'^download/template/(?P<filename>\w+)', views.serve_data_template_file, name='serve_data_template_file'),
    )
