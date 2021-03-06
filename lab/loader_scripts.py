import codecs
import csv
from collections import OrderedDict
import time
from lab import loader_db_mirror
from django.http import HttpResponseRedirect, HttpResponse
from lab.models import UserProfile, Experiment, Passport, Stock, StockPacket, Taxonomy, People, Collecting, Field, Locality, Location, ObsRow, ObsPlant, ObsSample, ObsEnv, ObsWell, ObsCulture, ObsTissue, ObsDNA, ObsPlate, ObsMicrobe, ObsExtract, ObsTracker, ObsTrackerSource, Isolate, DiseaseInfo, Measurement, MeasurementParameter, Treatment, UploadQueue, Medium, Citation, Publication, MaizeSample, Separation, GlycerolStock, ObsTrackerSource, Primer, Marker, MapFeature, MapFeatureInterval
from django.db import IntegrityError, transaction

def seed_stock_loader_prep(upload_file, user):
    start = time.clock()

    #-- These are the tables that will hold the curated data that is then written to csv files --
    stock_new = OrderedDict({})
    #--- Key = (stock_id, passport_id, seed_id, seed_name, cross_type, pedigree, stock_status, stock_date, inoculated, comments)
    #--- Value = (stock_id)
    passport_new = OrderedDict({})
    #--- Key = (passport_id, collecting_id, people_id, taxonomy_id)
    #--- Value = (passport_id)
    collecting_new = OrderedDict({})
    #--- Key = (collecting_id, user_id, collection_date, collection_method, comments)
    #--- Value = (collecting_id)
    people_new = OrderedDict({})
    #--- Key = (people_id, first_name, last_name, organization, phone, email, comments)
    #--- Value = (people_id)
    taxonomy_new = OrderedDict({})
    #--- Key = (taxonomy_id, genus, species, population, common_name, alias, race, subtaxa)
    #--- Value = (taxonomy_id)
    obs_tracker_new = OrderedDict({})
    #--- Key = (obs_tracker_id, obs_entity_type, experiment_id, field_id, glycerol_stock_id, isolate_id, location_id, maize_sample_id, obs_culture_id, obs_dna_id, obs_env_id, obs_extract_id, obs_microbe_id, obs_plant_id, obs_plate_id, obs_row_id, obs_sample_id, obs_tissue_id, obs_well_id, stock_id, user_id)
    #--- Value = (obs_tracker_id)
    obs_tracker_source_new = OrderedDict({})
    #--- Key = (obs_tracker_source_id, source_obs_id, target_obs_id)
    #--- Value = (obs_tracker_source_id)

    user_hash_table = loader_db_mirror.user_hash_mirror()
    stock_hash_table = loader_db_mirror.stock_hash_mirror()
    stock_id = loader_db_mirror.stock_id_mirror()
    row_id_table = loader_db_mirror.row_id_mirror()
    plant_id_table = loader_db_mirror.plant_id_mirror()
    obs_tracker_hash_table = loader_db_mirror.obs_tracker_hash_mirror()
    obs_tracker_id = loader_db_mirror.obs_tracker_id_mirror()
    collecting_hash_table = loader_db_mirror.collecting_hash_mirror()
    collecting_id = loader_db_mirror.collecting_id_mirror()
    people_hash_table = loader_db_mirror.people_hash_mirror()
    people_id = loader_db_mirror.people_id_mirror()
    taxonomy_hash_table = loader_db_mirror.taxonomy_hash_mirror()
    taxonomy_id = loader_db_mirror.taxonomy_id_mirror()
    passport_hash_table = loader_db_mirror.passport_hash_mirror()
    passport_id = loader_db_mirror.passport_id_mirror()
    experiment_name_table = loader_db_mirror.experiment_name_mirror()
    field_name_table = loader_db_mirror.field_name_mirror()
    seed_id_table = loader_db_mirror.seed_id_mirror()
    obs_tracker_source_hash_table = loader_db_mirror.obs_tracker_source_hash_mirror()
    obs_tracker_source_id = loader_db_mirror.obs_tracker_source_id_mirror()
    obs_tracker_obs_row_id_table = loader_db_mirror.obs_tracker_obs_row_id_mirror()
    obs_tracker_obs_plant_id_table = loader_db_mirror.obs_tracker_obs_plant_id_mirror()

    error_count = 0
    row_id_error = OrderedDict({})
    plant_id_error = OrderedDict({})
    field_name_error = OrderedDict({})
    collecting_hash_exists = OrderedDict({})
    people_hash_exists = OrderedDict({})
    taxonomy_hash_exists = OrderedDict({})
    passport_hash_exists = OrderedDict({})
    stock_hash_exists = OrderedDict({})
    obs_tracker_hash_exists = OrderedDict({})
    obs_tracker_source_hash_exists = OrderedDict({})

    stock_file = csv.DictReader(codecs.iterdecode(upload_file, 'utf-8'))
    for row in stock_file:
        seed_id = row["Seed ID"]
        seed_name = row["Seed Name"]
        experiment_used = row["Used"]
        experiment_collected = row["Collected"]
        experiment_name = row["Experiment Name"]
        cross_type = row["Cross Type"]
        pedigree = row["Pedigree"]
        stock_status = row["Stock Status"]
        stock_date = row["Stock Date"]
        inoculated = row["Inoculated"]
        stock_comments = row["Stock Comments"]
        genus = row["Genus"]
        species = row["Species"]
        population = row["Population"]
        row_id = row["Row ID"]
        field_name = row["Field Name"]
        plant_id = row["Plant ID"]
        collection_username = row["Username"]
        collection_date = row["Collection Date"]
        collection_method = row["Method"]
        collection_comments = row["Collection Comments"]
        organization = row["Organization"]
        first_name = row["First Name"]
        last_name = row["Last Name"]
        phone = row["Phone"]
        email = row["Email"]
        source_comments = row["Source Comments"]

        if row_id != '':
            row_id_fix = row_id + '\r'
            if row_id in row_id_table:
                obs_row_id = row_id_table[row_id][0]
            elif row_id_fix in row_id_table:
                obs_row_id = row_id_table[row_id_fix][0]
            else:
                row_id_error[(seed_id, seed_name, cross_type, pedigree, stock_status, stock_date, inoculated, stock_comments, genus, species, population, row_id, field_name, plant_id, collection_username, collection_date, collection_method, collection_comments, organization, first_name, last_name, phone, email, source_comments)] = error_count
                error_count = error_count + 1
                obs_row_id = 1
        else:
            obs_row_id = 1

        if plant_id != '':
            plant_id_fix = plant_id + '\r'
            if plant_id in plant_id_table:
                obs_plant_id = plant_id_table[plant_id][0]
            elif plant_id_fix in plant_id_table:
                obs_plant_id = plant_id_table[plant_id_fix][0]
            else:
                plant_id_error[(seed_id, seed_name, cross_type, pedigree, stock_status, stock_date, inoculated, stock_comments, genus, species, population, row_id, field_name, plant_id, collection_username, collection_date, collection_method, collection_comments, organization, first_name, last_name, phone, email, source_comments)] = error_count
                error_count = error_count + 1
                obs_plant_id = 1
        else:
            obs_plant_id = 1

        if field_name != '':
            field_name_fix = field_name + '\r'
            if field_name in field_name_table:
                field_id = field_name_table[field_name][0]
            elif field_name_fix in field_name_table:
                field_id = field_name_table[field_name_fix][0]
            else:
                field_name_error[(seed_id, seed_name, cross_type, pedigree, stock_status, stock_date, inoculated, stock_comments, genus, species, population, row_id, field_name, plant_id, collection_username, collection_date, collection_method, collection_comments, organization, first_name, last_name, phone, email, source_comments)] = error_count
                error_count = error_count + 1
                field_id = 1
        else:
            field_id = 1

        if collection_username == '':
            collection_username = 'unknown_person'

        collecting_hash = str(user_hash_table[collection_username]) + collection_date + collection_method + collection_comments
        collecting_hash_fix = collecting_hash + '\r'
        if collecting_hash not in collecting_hash_table and collecting_hash_fix not in collecting_hash_table:
            collecting_hash_table[collecting_hash] = collecting_id
            collecting_new[(collecting_id, user_hash_table[collection_username], collection_date, collection_method, collection_comments)] = collecting_id
            collecting_id = collecting_id + 1
        else:
            collecting_hash_exists[(user_hash_table[collection_username], collection_date, collection_method, collection_comments)] = collecting_id

        if collecting_hash in collecting_hash_table:
            temp_collecting_id = collecting_hash_table[collecting_hash]
        elif collecting_hash_fix in collecting_hash_table:
            temp_collecting_id = collecting_hash_table[collecting_hash_fix]
        else:
            temp_collecting_id = 1
            error_count = error_count + 1

        people_hash = first_name + last_name + organization + phone + email + source_comments
        people_hash_fix = people_hash + '\r'
        if people_hash not in people_hash_table and people_hash_fix not in people_hash_table:
            people_hash_table[people_hash] = people_id
            people_new[(people_id, first_name, last_name, organization, phone, email, source_comments)] = people_id
            people_id = people_id + 1
        else:
            people_hash_exists[(first_name, last_name, organization, phone, email, source_comments)] = people_id

        if people_hash in people_hash_table:
            temp_people_id = people_hash_table[people_hash]
        elif people_hash_fix in people_hash_table:
            temp_people_id = people_hash_table[people_hash_fix]
        else:
            temp_people_id = 1
            error_count = error_count + 1

        taxonomy_hash = genus + species + population + 'Maize' + '' + '' + ''
        taxonomy_hash_fix = taxonomy_hash + '\r'
        if taxonomy_hash not in taxonomy_hash_table and taxonomy_hash_fix not in taxonomy_hash_table:
            taxonomy_hash_table[taxonomy_hash] = taxonomy_id
            taxonomy_new[(taxonomy_id, genus, species, population, 'Maize', '', '', '')] = taxonomy_id
            taxonomy_id = taxonomy_id + 1
        else:
            taxonomy_hash_exists[(genus, species, population, 'Maize', '', '', '')] = taxonomy_id

        if taxonomy_hash in taxonomy_hash_table:
            temp_taxonomy_id = taxonomy_hash_table[taxonomy_hash]
        elif taxonomy_hash_fix in taxonomy_hash_table:
            temp_taxonomy_id = taxonomy_hash_table[taxonomy_hash_fix]
        else:
            temp_taxonomy_id = 1
            error_count = error_count + 1

        passport_hash = str(temp_collecting_id) + str(temp_people_id) + str(temp_taxonomy_id)
        passport_hash_fix = passport_hash + '\r'
        if passport_hash not in passport_hash_table and passport_hash_fix not in passport_hash_table:
            passport_hash_table[passport_hash] = passport_id
            passport_new[(passport_id, collecting_hash_table[collecting_hash], people_hash_table[people_hash], taxonomy_hash_table[taxonomy_hash])] = passport_id
            passport_id = passport_id + 1
        else:
            passport_hash_exists[(collecting_hash_table[collecting_hash], people_hash_table[people_hash], taxonomy_hash_table[taxonomy_hash])] = passport_id

        if passport_hash in passport_hash_table:
            temp_passport_id = passport_hash_table[passport_hash]
        elif passport_hash_fix in passport_hash_table:
            temp_passport_id = passport_hash_table[passport_hash_fix]
        else:
            temp_passport_id = 1
            error_count = error_count + 1


        if seed_id not in seed_id_table and seed_id + '\r' not in seed_id_table:
            if inoculated == '':
                inoculated = '0'

            stock_hash = str(temp_passport_id) + seed_id + seed_name + cross_type + pedigree + stock_status + stock_date + inoculated + stock_comments
            stock_hash_fix = stock_hash + '\r'
            if stock_hash not in stock_hash_table and stock_hash_fix not in stock_hash_table:
                stock_hash_table[stock_hash] = stock_id
                stock_new[(stock_id, passport_hash_table[passport_hash], seed_id, seed_name, cross_type, pedigree, stock_status, stock_date, inoculated, stock_comments)] = stock_id
                seed_id_table[seed_id] = (stock_id, passport_hash_table[passport_hash], seed_id, seed_name, cross_type, pedigree, stock_status, stock_date, inoculated, stock_comments)
                stock_id = stock_id + 1
            else:
                stock_hash_exists[(passport_hash_table[passport_hash], seed_id, seed_name, cross_type, pedigree, stock_status, stock_date, inoculated, stock_comments)] = stock_id
        elif experiment_used == '1':
            stock_hash = str(seed_id_table[seed_id][1]) + seed_id + seed_id_table[seed_id][3] + seed_id_table[seed_id][4] + seed_id_table[seed_id][5] + stock_status + seed_id_table[seed_id][6] + seed_id_table[seed_id][7] + str(seed_id_table[seed_id][8]) + seed_id_table[seed_id][9]
            stock_hash_fix = stock_hash + '\r'
            stock_hash_table[stock_hash] = stock_id
            stock_new[(seed_id_table[seed_id][0], seed_id_table[seed_id][1], seed_id, seed_id_table[seed_id][3], seed_id_table[seed_id][4], seed_id_table[seed_id][5], stock_status, seed_id_table[seed_id][6], seed_id_table[seed_id][7], seed_id_table[seed_id][8], seed_id_table[seed_id][9])] = seed_id_table[seed_id][0]
            seed_id_table[seed_id] = (seed_id_table[seed_id][0], seed_id_table[seed_id][1], seed_id, seed_id_table[seed_id][3], seed_id_table[seed_id][4], seed_id_table[seed_id][5], stock_status, seed_id_table[seed_id][6], seed_id_table[seed_id][7], seed_id_table[seed_id][8], seed_id_table[seed_id][9])
        else:
            stock_hash_exists[(passport_hash_table[passport_hash], seed_id, seed_name, cross_type, pedigree, stock_status, stock_date, inoculated, stock_comments)] = stock_id

        if experiment_name == '':
            experiment_name = 'No Experiment'

        if seed_id in seed_id_table:
            temp_stock_id = seed_id_table[seed_id][0]
        elif seed_id + '\r' in seed_id_table:
            temp_stock_id = seed_id_table[seed_id + '\r'][0]
        elif stock_hash in stock_hash_table:
            temp_stock_id = stock_hash_table[stock_hash]
        elif stock_hash_fix in stock_hash_table:
            temp_stock_id = stock_hash_table[stock_hash_fix]
        else:
            temp_stock_id = 1
            error_count = error_count + 1


        obs_tracker_stock_hash = 'stock' + str(1) + str(field_id) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(obs_plant_id) + str(1) + str(obs_row_id) + str(1) + str(1) + str(1) + str(temp_stock_id) + str(user_hash_table[user.username])
        obs_tracker_stock_hash_fix = obs_tracker_stock_hash + '\r'
        if obs_tracker_stock_hash not in obs_tracker_hash_table and obs_tracker_stock_hash_fix not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_stock_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'stock', 1, field_id, 1, 1, 1, 1, 1, 1, 1, 1, 1, obs_plant_id, 1, obs_row_id, 1, 1, 1, temp_stock_id, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1
        else:
            obs_tracker_hash_exists[('stock', 1, field_id, 1, 1, 1, 1, 1, 1, 1, 1, 1, obs_plant_id, 1, obs_row_id, 1, 1, 1, temp_stock_id, user_hash_table[user.username])] = obs_tracker_id

        if obs_tracker_stock_hash in obs_tracker_hash_table:
            temp_targetobs_id = obs_tracker_hash_table[obs_tracker_stock_hash]
        elif obs_tracker_stock_hash_fix in obs_tracker_hash_table:
            temp_targetobs_id = obs_tracker_hash_table[obs_tracker_stock_hash_fix]
        else:
            temp_targetobs_id = 1
            error_count = error_count + 1

        obs_tracker_exp_hash = 'experiment' + str(experiment_name_table[experiment_name][0]) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(user_hash_table[user.username])
        if obs_tracker_exp_hash not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_exp_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'experiment', experiment_name_table[experiment_name][0], 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1

        if experiment_used == '1':

            obs_tracker_source_hash = str(obs_tracker_hash_table[obs_tracker_exp_hash]) + str(temp_targetobs_id) + 'stock_used_in_experiment'
            if obs_tracker_source_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], temp_targetobs_id, 'stock_used_in_experiment')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], temp_targetobs_id, 'stock_used_in_experiment')] = obs_tracker_source_id


        if experiment_collected == '1':

            obs_tracker_source_hash = str(obs_tracker_hash_table[obs_tracker_exp_hash]) + str(temp_targetobs_id) + 'stock_from_experiment'
            if obs_tracker_source_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], temp_targetobs_id, 'stock_from_experiment')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], temp_targetobs_id, 'stock_from_experiment')] = obs_tracker_source_id

            if obs_row_id != 1:
                obs_tracker_source_row_hash = str(obs_tracker_obs_row_id_table[obs_row_id][0]) + str(temp_targetobs_id) + 'stock_from_row'
                if obs_tracker_source_row_hash not in obs_tracker_source_hash_table:
                    obs_tracker_source_hash_table[obs_tracker_source_row_hash] = obs_tracker_source_id
                    obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_row_id_table[obs_row_id][0], temp_targetobs_id, 'stock_from_row')] = obs_tracker_source_id
                    obs_tracker_source_id = obs_tracker_source_id + 1
                else:
                    obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_row_id_table[obs_row_id][0], temp_targetobs_id, 'stock_from_row')] = obs_tracker_source_id

            if obs_plant_id != 1:
                obs_tracker_source_plant_hash = str(obs_tracker_obs_plant_id_table[obs_plant_id][0]) + str(temp_targetobs_id) + 'stock_from_plant'
                if obs_tracker_source_plant_hash not in obs_tracker_source_hash_table:
                    obs_tracker_source_hash_table[obs_tracker_source_plant_hash] = obs_tracker_source_id
                    obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_plant_id_table[obs_plant_id][0], temp_targetobs_id, 'stock_from_plant')] = obs_tracker_source_id
                    obs_tracker_source_id = obs_tracker_source_id + 1
                else:
                    obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_plant_id_table[obs_plant_id][0], temp_targetobs_id, 'stock_from_plant')] = obs_tracker_source_id

    end = time.clock()
    stats = {}
    stats[("Time: %s" % (end-start), "Errors: %s" % (error_count))] = error_count

    results_dict = {}
    results_dict['stock_new'] = stock_new
    results_dict['passport_new'] = passport_new
    results_dict['collecting_new'] = collecting_new
    results_dict['people_new'] = people_new
    results_dict['taxonomy_new'] = taxonomy_new
    results_dict['obs_tracker_new'] = obs_tracker_new
    results_dict['obs_tracker_source_new'] = obs_tracker_source_new
    results_dict['plant_id_error'] = plant_id_error
    results_dict['row_id_error'] = row_id_error
    results_dict['field_name_error'] = field_name_error
    results_dict['collecting_hash_exists'] = collecting_hash_exists
    results_dict['people_hash_exists'] = people_hash_exists
    results_dict['taxonomy_hash_exists'] = taxonomy_hash_exists
    results_dict['passport_hash_exists'] = passport_hash_exists
    results_dict['stock_hash_exists'] = stock_hash_exists
    results_dict['obs_tracker_hash_exists'] = obs_tracker_hash_exists
    results_dict['obs_tracker_source_hash_exists'] = obs_tracker_source_hash_exists
    results_dict['stats'] = stats
    return results_dict

def seed_stock_loader_prep_output(results_dict, new_upload_exp, template_type):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s_%s_prep.csv"' % (new_upload_exp, template_type)
    writer = csv.writer(response)
    writer.writerow(['Stats'])
    writer.writerow([''])
    for key in results_dict['stats'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Stock Table'])
    writer.writerow(['stock_id', 'passport_id', 'seed_id', 'seed_name', 'cross_type', 'pedigree', 'stock_status', 'stock_date', 'inoculated', 'comments'])
    for key in results_dict['stock_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Collecting Table'])
    writer.writerow(['collecting_id', 'user_id', 'collection_date', 'collection_method', 'comments'])
    for key in results_dict['collecting_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New People Table'])
    writer.writerow(['people_id', 'first_name', 'last_name', 'organization', 'phone', 'email', 'comments'])
    for key in results_dict['people_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Taxonomy Table'])
    writer.writerow(['taxonomy_id', 'genus', 'species', 'population', 'common_name', 'alias', 'race', 'subtaxa'])
    for key in results_dict['taxonomy_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Passport Table'])
    writer.writerow(['passport_id', 'collecting_id', 'people_id', 'taxonomy_id'])
    for key in results_dict['passport_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTracker Table'])
    writer.writerow(['obs_tracker_id', 'obs_entity_type', 'experiment_id', 'field_id', 'glycerol_stock_id', 'isolate_id', 'location_id', 'maize_sample_id', 'obs_culture_id', 'obs_dna_id', 'obs_env_id', 'obs_extract_id', 'obs_microbe_id', 'obs_plant_id', 'obs_plate_id', 'obs_row_id', 'obs_sample_id', 'obs_tissue_id', 'obs_well_id', 'stock_id', 'user_id'])
    for key in results_dict['obs_tracker_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTrackerSource Table'])
    writer.writerow(['obs_tracker_source_id', 'source_obs_id', 'targe_obs_id', 'relationship'])
    for key in results_dict['obs_tracker_source_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['---------------------------------------------------------------------------------------------------'])
    writer.writerow([''])
    writer.writerow(['Plant ID Errors'])
    writer.writerow(['seed_id', 'seed_name', 'cross_type', 'pedigree', 'stock_status', 'stock_date', 'inoculated', 'stock_comments', 'genus', 'species', 'population', 'row_id', 'field_name', 'plant_id', 'collection_username', 'collection_date', 'collection_method', 'collection_comments', 'organization', 'first_name', 'last_name', 'phone', 'email', 'source_comments'])
    for key in results_dict['plant_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Field Name Errors'])
    writer.writerow(['seed_id', 'seed_name', 'cross_type', 'pedigree', 'stock_status', 'stock_date', 'inoculated', 'stock_comments', 'genus', 'species', 'population', 'row_id', 'field_name', 'plant_id', 'collection_username', 'collection_date', 'collection_method', 'collection_comments', 'organization', 'first_name', 'last_name', 'phone', 'email', 'source_comments'])
    for key in results_dict['field_name_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Row ID Errors'])
    writer.writerow(['seed_id', 'seed_name', 'cross_type', 'pedigree', 'stock_status', 'stock_date', 'inoculated', 'stock_comments', 'genus', 'species', 'population', 'row_id', 'field_name', 'plant_id', 'collection_username', 'collection_date', 'collection_method', 'collection_comments', 'organization', 'first_name', 'last_name', 'phone', 'email', 'source_comments'])
    for key in results_dict['row_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Collecting Entries Already Exist'])
    for key in results_dict['collecting_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['People Entries Already Exist'])
    for key in results_dict['people_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Taxonomy Entries Already Exist'])
    for key in results_dict['taxonomy_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Passport Entries Already Exist'])
    for key in results_dict['passport_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Stock Entries Already Exist'])
    for key in results_dict['stock_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTracker Entries Already Exist'])
    for key in results_dict['obs_tracker_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTrackerSource Entries Already Exist'])
    for key in results_dict['obs_tracker_source_hash_exists'].keys():
        writer.writerow(key)

    return response

def seed_stock_loader(results_dict):
    try:
        for key in results_dict['collecting_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = Collecting.objects.create(id=key[0], user_id=key[1], collection_date=key[2], collection_method=key[3], comments=key[4])
            except Exception as e:
                print("Collecting Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['people_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = People.objects.create(id=key[0], first_name=key[1], last_name=key[2], organization=key[3], phone=key[4], email=key[5], comments=key[6])
            except Exception as e:
                print("People Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['taxonomy_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = Taxonomy.objects.create(id=key[0], genus=key[1], species=key[2], population=key[3], common_name=key[4], alias=key[5], race=key[6], subtaxa=key[7])
            except Exception as e:
                print("Taxonomy Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['passport_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = Passport.objects.create(id=key[0], collecting_id=key[1], people_id=key[2], taxonomy_id=key[3])
            except Exception as e:
                print("Passport Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['stock_new'].keys():
            try:
                with transaction.atomic():
                    new_stock, create = Stock.objects.update_or_create(id=key[0], seed_id=key[2], defaults= { 'passport_id':key[1], 'seed_name':key[3], 'cross_type':key[4], 'pedigree':key[5], 'stock_status':key[6], 'stock_date':key[7], 'inoculated':key[8], 'comments':key[9] } )
            except Exception as e:
                print("Stock Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = ObsTracker.objects.create(id=key[0], obs_entity_type=key[1], experiment_id=key[2], field_id=key[3], glycerol_stock_id=key[4], isolate_id=key[5], location_id=key[6], maize_sample_id=key[7], obs_culture_id=key[8], obs_dna_id=key[9], obs_env_id=key[10], obs_extract_id=key[11], obs_microbe_id=key[12], obs_plant_id=key[13], obs_plate_id=key[14], obs_row_id=key[15], obs_sample_id=key[16], obs_tissue_id=key[17], obs_well_id=key[18], stock_id=key[19], user_id=key[20])
            except Exception as e:
                print("ObsTracker Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_source_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = ObsTrackerSource.objects.create(id=key[0], source_obs_id=key[1], target_obs_id=key[2], relationship=key[3])
            except Exception as e:
                print("ObsTrackerSource Error: %s %s" % (e.message, e.args))
                return False
    except Exception as e:
        print("Error: %s %s" % (e.message, e.args))
        return False
    return True

def seed_packet_loader_prep(upload_file, user):
    start = time.clock()

    #-- These are the tables that will hold the curated data that is then written to csv files --
    stock_packet_new = OrderedDict({})
    #--- Key = (stock_id, passport_id, seed_id, seed_name, cross_type, pedigree, stock_status, stock_date, inoculated, comments)
    #--- Value = (stock_id)
    location_new = OrderedDict({})
    #--- Key = (location_id, location_name, building_name, room, shelf, column, box_name, comments)
    #--- Value = (location_id)
    locality_new = OrderedDict({})
    #--- Key = (city, state, country, zipcode)
    #--- Value = (locality_id)

    stock_packet_hash_table = loader_db_mirror.stockpacket_hash_mirror()
    stock_packet_id = loader_db_mirror.stockpacket_id_mirror()
    location_hash_table = loader_db_mirror.location_hash_mirror()
    location_id = loader_db_mirror.location_id_mirror()
    locality_hash_table = loader_db_mirror.locality_hash_mirror()
    location_name_table = loader_db_mirror.location_name_mirror()
    locality_id = loader_db_mirror.locality_id_mirror()
    seed_id_table = loader_db_mirror.seed_id_mirror()

    error_count = 0
    seed_id_error = OrderedDict({})
    locality_hash_exists = OrderedDict({})
    location_hash_exists = OrderedDict({})
    stock_packet_hash_exists = OrderedDict({})

    stock_packet_file = csv.DictReader(codecs.iterdecode(upload_file, 'utf-8'))
    for row in stock_packet_file:
        seed_id = row["Seed ID"]
        weight = row["Weight"]
        num_seeds = row["Number of Seeds"]
        packet_comments = row["Seed Packet Comments"]
        location_name = row["Location Name"]
        building_name = row["Building Name"]
        room = row["Room"]
        shelf = row["Shelf"]
        column = row["Column"]
        box_name = row["Box Name"]
        city = row["City"]
        state = row["State"]
        country = row["Country"]
        zipcode = row["Zipcode"]
        location_comments = row["Location Comments"]

        if seed_id != '':
            seed_id_fix = seed_id + '\r'
            if seed_id in seed_id_table:
                stock_id = seed_id_table[seed_id][0]
            elif seed_id_fix in seed_id_table:
                stock_id = seed_id_table[seed_id_fix][0]
            else:
                seed_id_error[(seed_id, weight, num_seeds, packet_comments, location_name, building_name, room, shelf, column, box_name, city, state, country, zipcode, location_comments)] = error_count
                error_count = error_count + 1
                stock_id = 1
        else:
            seed_id_error[(seed_id, seed_name, cross_type, pedigree, stock_status, stock_date, inoculated, stock_comments, genus, species, population, row_id, field_name, plant_id, collection_username, collection_date, collection_method, collection_comments, organization, first_name, last_name, phone, email, source_comments)] = error_count
            error_count = error_count + 1
            stock_id = 1

        locality_hash = city + state + country + zipcode
        locality_hash_fix = locality_hash + '\r'
        if locality_hash not in locality_hash_table and locality_hash_fix not in locality_hash_table:
            locality_hash_table[locality_hash] = locality_id
            locality_new[(locality_id, city, state, country, zipcode)] = locality_id
            locality_id = locality_id + 1
        else:
            locality_hash_exists[(city, state, country, zipcode)] = locality_id

        if locality_hash in locality_hash_table:
            temp_locality_id = locality_hash_table[locality_hash]
        elif locality_hash_fix in locality_hash_table:
            temp_locality_id = locality_hash_table[locality_hash_fix]
        else:
            temp_locality_id = 1
            error_count = error_count + 1

        location_hash = str(temp_locality_id) + building_name + location_name + room + shelf + column + box_name + location_comments
        location_hash_fix = location_hash + '\r'
        if location_name not in location_name_table and location_hash not in location_hash_table and location_hash_fix not in location_hash_table:
            location_hash_table[location_hash] = location_id
            location_new[(location_id, temp_locality_id, location_name, building_name, room, shelf, column, box_name, location_comments)] = location_id
            location_id = location_id + 1
        else:
            location_hash_exists[(temp_locality_id, location_name, building_name, room, shelf, column, box_name, location_comments)] = location_id

        if location_name in location_name_table:
            temp_location_id = location_name_table[location_name][0]
        elif location_hash in location_hash_table:
            temp_location_id = location_hash_table[location_hash]
        elif location_hash_fix in location_hash_table:
            temp_location_id = location_hash_table[location_hash_fix]
        else:
            temp_location_id = 1
            error_count = error_count + 1

        stock_packet_hash = str(stock_id) + str(temp_location_id) + weight + num_seeds + packet_comments
        stock_packet_hash_fix = stock_packet_hash + '\r'
        if stock_packet_hash not in stock_packet_hash_table and stock_packet_hash_fix not in stock_packet_hash_table:
            stock_packet_hash_table[stock_packet_hash] = stock_packet_id
            stock_packet_new[(stock_packet_id, stock_id, temp_location_id, weight, num_seeds, packet_comments)] = stock_packet_id
            stock_packet_id = stock_packet_id + 1
        else:
            stock_packet_hash_exists[(stock_id, location_id, weight, num_seeds, packet_comments)] = stock_packet_id

    end = time.clock()
    stats = {}
    stats[("Time: %s" % (end-start), "Errors: %s" % (error_count))] = error_count

    results_dict = {}
    results_dict['stock_packet_new'] = stock_packet_new
    results_dict['location_new'] = location_new
    results_dict['locality_new'] = locality_new
    results_dict['seed_id_error'] = seed_id_error
    results_dict['location_hash_exists'] = location_hash_exists
    results_dict['locality_hash_exists'] = locality_hash_exists
    results_dict['stock_packet_hash_exists'] = stock_packet_hash_exists
    results_dict['stats'] = stats
    return results_dict

def seed_packet_loader_prep_output(results_dict, new_upload_exp, template_type):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s_%s_prep.csv"' % (new_upload_exp, template_type)
    writer = csv.writer(response)
    writer.writerow(['Stats'])
    writer.writerow([''])
    for key in results_dict['stats'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Stock Packet Table'])
    writer.writerow(['stock_packet_id', 'stock_id', 'location_id', 'weight', 'num_seeds', 'comments'])
    for key in results_dict['stock_packet_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Location Table'])
    writer.writerow(['location_id', 'location_name', 'building_name', 'room', 'shelf', 'column', 'box_name', 'comments'])
    for key in results_dict['location_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Locality Table'])
    writer.writerow(['locality_id', 'city', 'state', 'country', 'zipcode'])
    for key in results_dict['locality_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['---------------------------------------------------------------------------------------------------'])
    writer.writerow([''])
    writer.writerow(['Seed ID Errors'])
    writer.writerow(['seed_id', 'weight', 'num_seeds', 'packet_comments', 'location_name', 'building_name', 'room', 'shelf', 'column', 'box_name', 'city', 'state', 'country', 'zipcode', 'location_comments'])
    for key in results_dict['seed_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Location Entries Already Exist'])
    for key in results_dict['location_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Locality Entries Already Exist'])
    for key in results_dict['locality_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Stock Packet Entries Already Exist'])
    for key in results_dict['stock_packet_hash_exists'].keys():
        writer.writerow(key)

    return response

def seed_packet_loader(results_dict):
    try:
        for key in results_dict['locality_new'].keys():
            try:
                with transaction.atomic():
                    new_locality = Locality.objects.create(id=key[0], city=key[1], state=key[2], country=key[3], zipcode=key[4])
            except Exception as e:
                print("Locality Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['location_new'].keys():
            try:
                with transaction.atomic():
                    new_location = Location.objects.create(id=key[0], locality_id=key[1], location_name=key[2], building_name=key[3], room=key[4], shelf=key[5], column=key[6], box_name=key[7], comments=key[8])
            except Exception as e:
                print("Location Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['stock_packet_new'].keys():
            try:
                with transaction.atomic():
                    new_stock_packet = StockPacket.objects.create(id=key[0], stock_id=key[1], location_id=key[2], weight=key[3], num_seeds=key[4], comments=key[5])
            except Exception as e:
                print("StockPacket Error: %s %s" % (e.message, e.args))
                return False
    except Exception as e:
        print("Error: %s %s" % (e.message, e.args))
        return False
    return True

def row_loader_prep(upload_file, user):
    start = time.clock()

    obs_row_new = OrderedDict({})
    #--- Key = (obs_row_id, row_id, row_name, range_num, plot, block, rep, kernel_num, planting_date, harvest_date, comments)
    #--- Value = (obs_row_id)
    obs_tracker_new = OrderedDict({})
    #--- Key = (obs_tracker_id, obs_entity_type, experiment_id, field_id, glycerol_stock_id, isolate_id, location_id, maize_sample_id, obs_culture_id, obs_dna_id, obs_env_id, obs_extract_id, obs_microbe_id, obs_plant_id, obs_plate_id, obs_row_id, obs_sample_id, obs_tissue_id, obs_well_id, stock_id, user_id)
    #--- Value = (obs_tracker_id)

    obs_tracker_source_new = OrderedDict({})
    #--- Key = (obs_tracker_source_id, source_obs_id, target_obs_id, relationship)
    #--- Value = (obs_tracker_source_id)

    user_hash_table = loader_db_mirror.user_hash_mirror()
    obs_row_hash_table = loader_db_mirror.obs_row_hash_mirror()
    obs_row_id = loader_db_mirror.obs_row_id_mirror()
    row_id_table = loader_db_mirror.row_id_mirror()
    seed_id_table = loader_db_mirror.seed_id_mirror()
    field_name_table = loader_db_mirror.field_name_mirror()
    obs_tracker_hash_table = loader_db_mirror.obs_tracker_hash_mirror()
    obs_tracker_source_hash_table = loader_db_mirror.obs_tracker_source_hash_mirror()
    obs_tracker_stock_id_table = loader_db_mirror.obs_tracker_stock_id_mirror()
    obs_tracker_id = loader_db_mirror.obs_tracker_id_mirror()
    obs_tracker_source_id = loader_db_mirror.obs_tracker_source_id_mirror()
    experiment_name_table = loader_db_mirror.experiment_name_mirror()

    error_count = 0
    source_seed_id_error = OrderedDict({})
    field_name_error = OrderedDict({})
    row_hash_exists = OrderedDict({})
    obs_tracker_hash_exists = OrderedDict({})
    obs_tracker_source_hash_exists = OrderedDict({})

    row_file = csv.DictReader(codecs.iterdecode(upload_file, 'utf-8'))
    for row in row_file:
        row_id = row["Row ID"]
        experiment_name = row["Experiment Name"]
        source_seed_id = row["Source Seed ID"]
        field_name = row["Field Name"]
        row_name = row["Row Name"]
        row_range = row["Range"]
        plot = row["Plot"]
        block = row["Block"]
        rep = row["Rep"]
        kernel_num = row["Kernel Num"]
        planting_date = row["Planting Date"]
        harvest_date = row["Harvest Date"]
        comments = row["Row Comments"]

        if source_seed_id != '':
            source_seed_id_fix = source_seed_id + '\r'
            if source_seed_id in seed_id_table:
                stock_id = seed_id_table[source_seed_id][0]
            elif source_seed_id_fix in seed_id_table:
                stock_id = seed_id_table[source_seed_id_fix][0]
            else:
                source_seed_id_error[(row_id, source_seed_id, field_name, row_name, row_range, plot, block,rep, kernel_num, planting_date, harvest_date, comments)] = error_count
                error_count = error_count + 1
                stock_id = 1
        else:
            stock_id = 1

        if field_name != '':
            field_name_fix = field_name + '\r'
            if field_name in field_name_table:
                field_id = field_name_table[field_name][0]
            elif field_name_fix in field_name_table:
                field_id = field_name_table[field_name_fix][0]
            else:
                field_name_error[(row_id, source_seed_id, field_name, row_name, row_range, plot, block,rep, kernel_num, planting_date, harvest_date, comments)] = error_count
                error_count = error_count + 1
                field_id = 1
        else:
            field_id = 1

        row_hash = row_id + row_name + row_range + plot + block + rep + kernel_num + planting_date + harvest_date + comments
        row_hash_fix = row_hash + '\r'
        if row_id not in row_id_table and row_id + '\r' not in row_id_table:
            if row_hash not in obs_row_hash_table and row_hash_fix not in obs_row_hash_table:
                obs_row_hash_table[row_hash] = obs_row_id
                obs_row_new[(obs_row_id, row_id, row_name, row_range, plot, block, rep, kernel_num, planting_date, harvest_date, comments)] = obs_row_id
                row_id_table[row_id] = (obs_row_id, row_id, row_name, row_range, plot, block, rep, kernel_num, planting_date, harvest_date, comments)
                obs_row_id = obs_row_id + 1
            else:
                row_hash_exists[(row_id, row_name, row_range, plot, block, rep, kernel_num, planting_date, harvest_date, comments)] = obs_row_id
        else:
            row_hash_exists[(row_id, row_name, row_range, plot, block, rep, kernel_num, planting_date, harvest_date, comments)] = obs_row_id

        if row_id in row_id_table:
            temp_obsrow_id = row_id_table[row_id][0]
        elif row_id + '\r' in row_id_table:
            temp_obsrow_id = row_id_table[row_id + '\r'][0]
        elif row_hash in obs_row_hash_table:
            temp_obsrow_id = obs_row_hash_table[row_hash]
        elif row_hash_fix in obs_row_hash_table:
            temp_obsrow_id = obs_row_hash_table[row_hash_fix]
        else:
            temp_obsrow_id = 1
            error_count = error_count + 1

        obs_tracker_row_hash = 'row' + str(1) + str(field_id) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(temp_obsrow_id) + str(1) + str(1) + str(1) + str(stock_id) + str(user_hash_table[user.username])
        obs_tracker_row_hash_fix = obs_tracker_row_hash + '\r'
        if obs_tracker_row_hash not in obs_tracker_hash_table and obs_tracker_row_hash_fix not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_row_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'row', 1, field_id, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, temp_obsrow_id, 1, 1, 1, stock_id, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1
        else:
            obs_tracker_hash_exists[('row', 1, field_id, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, temp_obsrow_id, 1, 1, 1, stock_id, user_hash_table[user.username])] = obs_tracker_id

        if stock_id != 1:
            obs_tracker_source_stock_hash = str(obs_tracker_stock_id_table[stock_id][0]) + str(obs_tracker_hash_table[obs_tracker_row_hash]) + 'row_from_stock'
            if obs_tracker_source_stock_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_stock_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_stock_id_table[stock_id][0], obs_tracker_hash_table[obs_tracker_row_hash], 'row_from_stock')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_stock_id_table[stock_id][0], obs_tracker_hash_table[obs_tracker_row_hash], 'row_from_stock')] = obs_tracker_source_id

        obs_tracker_exp_hash = 'experiment' + str(experiment_name_table[experiment_name][0]) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(user_hash_table[user.username])
        if obs_tracker_exp_hash not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_exp_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'experiment', experiment_name_table[experiment_name][0], 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1

        obs_tracker_source_hash = str(obs_tracker_hash_table[obs_tracker_exp_hash]) + str(obs_tracker_hash_table[obs_tracker_row_hash]) + 'row_used_in_experiment'
        if obs_tracker_source_hash not in obs_tracker_source_hash_table:
            obs_tracker_source_hash_table[obs_tracker_source_hash] = obs_tracker_source_id
            obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], obs_tracker_hash_table[obs_tracker_row_hash], 'row_used_in_experiment')] = obs_tracker_source_id
            obs_tracker_source_id = obs_tracker_source_id + 1
        else:
            obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], obs_tracker_hash_table[obs_tracker_row_hash], 'row_used_in_experiment')] = obs_tracker_source_id

    end = time.clock()
    stats = {}
    stats[("Time: %s" % (end-start), "Errors: %s" % (error_count))] = error_count

    results_dict = {}
    results_dict['obs_row_new'] = obs_row_new
    results_dict['obs_tracker_new'] = obs_tracker_new
    results_dict['source_seed_id_error'] = source_seed_id_error
    results_dict['field_name_error'] = field_name_error
    results_dict['row_hash_exists'] = row_hash_exists
    results_dict['obs_tracker_hash_exists'] = obs_tracker_hash_exists
    results_dict['obs_tracker_source_new'] = obs_tracker_source_new
    results_dict['obs_tracker_source_hash_exists'] = obs_tracker_source_hash_exists
    results_dict['stats'] = stats
    return results_dict

def row_loader_prep_output(results_dict, new_upload_exp, template_type):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s_%s_prep.csv"' % (new_upload_exp, template_type)
    writer = csv.writer(response)
    writer.writerow(['Stats'])
    writer.writerow([''])
    for key in results_dict['stats'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Row Table'])
    writer.writerow(['obs_row_id', 'row_id', 'row_name', 'range_num', 'plot', 'block', 'rep', 'kernel_num', 'planting_date', 'harvest_date', 'comments'])
    for key in results_dict['obs_row_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTracker Table'])
    writer.writerow(['obs_tracker_id', 'obs_entity_type', 'experiment_id', 'field_id', 'glycerol_stock_id', 'isolate_id', 'location_id', 'maize_sample_id', 'obs_culture_id', 'obs_dna_id', 'obs_env_id', 'obs_extract_id', 'obs_microbe_id', 'obs_plant_id', 'obs_plate_id', 'obs_row_id', 'obs_sample_id', 'obs_tissue_id', 'obs_well_id', 'stock_id', 'user_id'])
    for key in results_dict['obs_tracker_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTrackerSource Table'])
    writer.writerow(['obs_tracker_source_id', 'source_obs_id', 'targe_obs_id', 'relationship'])
    for key in results_dict['obs_tracker_source_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['---------------------------------------------------------------------------------------------------'])
    writer.writerow([''])
    writer.writerow(['Source Seed ID Errors'])
    writer.writerow(['row_id', 'source_seed_id', 'field_name', 'row_name', 'range', 'plot', 'block', 'rep', 'kernel_num', 'planting_date', 'harvest_date', 'comments'])
    for key in results_dict['source_seed_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Field Name Errors'])
    writer.writerow(['row_id', 'source_seed_id', 'field_name', 'row_name', 'range', 'plot', 'block', 'rep', 'kernel_num', 'planting_date', 'harvest_date', 'comments'])
    for key in results_dict['field_name_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Row Entry Already Exists'])
    for key in results_dict['row_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTracker Entry Already Exists'])
    for key in results_dict['obs_tracker_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTrackerSource Entries Already Exist'])
    for key in results_dict['obs_tracker_source_hash_exists'].keys():
        writer.writerow(key)
    return response

def row_loader(results_dict):
    try:
        for key in results_dict['obs_row_new'].keys():
            try:
                with transaction.atomic():
                    new_obsrow = ObsRow.objects.create(id=key[0], row_id=key[1], row_name=key[2], range_num=key[3], plot=key[4], block=key[5], rep=key[6], kernel_num=key[7], planting_date=key[8], harvest_date=key[9], comments=key[10])
            except Exception as e:
                print("ObsRow Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = ObsTracker.objects.create(id=key[0], obs_entity_type=key[1], experiment_id=key[2], field_id=key[3], glycerol_stock_id=key[4], isolate_id=key[5], location_id=key[6], maize_sample_id=key[7], obs_culture_id=key[8], obs_dna_id=key[9], obs_env_id=key[10], obs_extract_id=key[11], obs_microbe_id=key[12], obs_plant_id=key[13], obs_plate_id=key[14], obs_row_id=key[15], obs_sample_id=key[16], obs_tissue_id=key[17], obs_well_id=key[18], stock_id=key[19], user_id=key[20])
            except Exception as e:
                print("ObsTracker Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_source_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = ObsTrackerSource.objects.create(id=key[0], source_obs_id=key[1], target_obs_id=key[2], relationship=key[3])
            except Exception as e:
                print("ObsTrackerSource Error: %s %s" % (e.message, e.args))
                return False
    except Exception as e:
        print("Error: %s %s" % (e.message, e.args))
        return False
    return True

def plant_loader_prep(upload_file, user):
    start = time.clock()

    obs_plant_new = OrderedDict({})
    #--- Key = (obs_plant_id, plant_id, plant_num, comments)
    #--- Value = (obs_plant_id)
    obs_tracker_new = OrderedDict({})
    #--- Key = (obs_tracker_id, obs_entity_type, experiment_id, field_id, glycerol_stock_id, isolate_id, location_id, maize_sample_id, obs_culture_id, obs_dna_id, obs_env_id, obs_extract_id, obs_microbe_id, obs_plant_id, obs_plate_id, obs_row_id, obs_sample_id, obs_tissue_id, obs_well_id, stock_id, user_id)
    #--- Value = (obs_tracker_id)

    obs_tracker_source_new = OrderedDict({})
    #--- Key = (obs_tracker_source_id, source_obs_id, target_obs_id, relationship)
    #--- Value = (obs_tracker_source_id)

    user_hash_table = loader_db_mirror.user_hash_mirror()
    obs_plant_hash_table = loader_db_mirror.obs_plant_hash_mirror()
    obs_plant_id = loader_db_mirror.obs_plant_id_mirror()
    row_id_table = loader_db_mirror.row_id_mirror()
    seed_id_table = loader_db_mirror.seed_id_mirror()
    plant_id_table = loader_db_mirror.plant_id_mirror()
    obs_tracker_hash_table = loader_db_mirror.obs_tracker_hash_mirror()
    obs_tracker_stock_id_table = loader_db_mirror.obs_tracker_stock_id_mirror()
    obs_tracker_obs_row_id_table = loader_db_mirror.obs_tracker_obs_row_id_mirror()
    obs_tracker_source_hash_table = loader_db_mirror.obs_tracker_source_hash_mirror()
    obs_tracker_id = loader_db_mirror.obs_tracker_id_mirror()
    obs_tracker_source_id = loader_db_mirror.obs_tracker_source_id_mirror()
    experiment_name_table = loader_db_mirror.experiment_name_mirror()

    error_count = 0
    seed_id_error = OrderedDict({})
    row_id_error = OrderedDict({})
    plant_hash_exists = OrderedDict({})
    obs_tracker_hash_exists = OrderedDict({})
    obs_tracker_source_hash_exists = OrderedDict({})

    plant_file = csv.DictReader(codecs.iterdecode(upload_file, 'utf-8'))
    for row in plant_file:
        plant_id = row["Plant ID"]
        experiment_name = row["Experiment Name"]
        row_id = row["Source Row ID"]
        seed_id = row["Source Seed ID"]
        plant_num = row["Plant Number"]
        comments = row["Plant Comments"]
        user = user

        if seed_id != '':
            seed_id_fix = seed_id + '\r'
            if seed_id in seed_id_table:
                stock_id = seed_id_table[seed_id][0]
            elif seed_id_fix in seed_id_table:
                stock_id = seed_id_table[seed_id_fix][0]
            else:
                seed_id_error[(plant_id, experiment_name, row_id, seed_id, plant_num, comments)] = error_count
                error_count = error_count + 1
                stock_id = 1
        else:
            stock_id = 1

        if row_id != '':
            row_id_fix = row_id + '\r'
            if row_id in row_id_table:
                obs_row_id = row_id_table[row_id][0]
            elif row_id_fix in row_id_table:
                obs_row_id = row_id_table[row_id_fix][0]
            else:
                row_id_error[(plant_id, experiment_name, row_id, seed_id, plant_num, comments)] = error_count
                error_count = error_count + 1
                obs_row_id = 1
        else:
            obs_row_id = 1

        plant_hash = plant_id + plant_num + comments
        plant_hash_fix = plant_hash + '\r'
        if plant_id not in plant_id_table and plant_id + '\r' not in plant_id_table:
            if plant_hash not in obs_plant_hash_table and plant_hash_fix not in obs_plant_hash_table:
                obs_plant_hash_table[plant_hash] = obs_plant_id
                obs_plant_new[(obs_plant_id, plant_id, plant_num, comments)] = obs_plant_id
                plant_id_table[plant_id] = (obs_plant_id, plant_id, plant_num, comments)
                obs_plant_id = obs_plant_id + 1
            else:
                plant_hash_exists[(plant_id, plant_num, comments)] = obs_plant_id
        else:
            plant_hash_exists[(plant_id, plant_num, comments)] = obs_plant_id

        if plant_id in plant_id_table:
            temp_obsplant_id = plant_id_table[plant_id][0]
        elif plant_id + '\r' in plant_id_table:
            temp_obsplant_id = plant_id_table[plant_id + '\r'][0]
        elif plant_hash in obs_plant_hash_table:
            temp_obsplant_id = obs_plant_hash_table[plant_hash]
        elif plant_hash_fix in obs_plant_hash_table:
            temp_obsplant_id = obs_plant_hash_table[plant_hash_fix]
        else:
            temp_obsplant_id = 1
            error_count = error_count + 1

        obs_tracker_plant_hash = 'plant' + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(temp_obsplant_id) + str(1) + str(obs_row_id) + str(1) + str(1) + str(1) + str(stock_id) + str(user_hash_table[user.username])
        obs_tracker_plant_hash_fix = obs_tracker_plant_hash + '\r'
        if obs_tracker_plant_hash not in obs_tracker_hash_table and obs_tracker_plant_hash_fix not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_plant_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'plant', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, temp_obsplant_id, 1, obs_row_id, 1, 1, 1, stock_id, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1
        else:
            obs_tracker_hash_exists[('plant', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, temp_obsplant_id, 1, obs_row_id, 1, 1, 1, stock_id, user_hash_table[user.username])] = obs_tracker_id

        if stock_id != 1:
            obs_tracker_source_stock_hash = str(obs_tracker_stock_id_table[stock_id][0]) + str(obs_tracker_hash_table[obs_tracker_plant_hash]) + 'plant_from_stock'
            if obs_tracker_source_stock_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_stock_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_stock_id_table[stock_id][0], obs_tracker_hash_table[obs_tracker_plant_hash], 'plant_from_stock')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_stock_id_table[stock_id][0], obs_tracker_hash_table[obs_tracker_plant_hash], 'plant_from_stock')] = obs_tracker_source_id

        if obs_row_id != 1:
            obs_tracker_source_row_hash = str(obs_tracker_obs_row_id_table[obs_row_id][0]) + str(obs_tracker_hash_table[obs_tracker_plant_hash]) + 'plant_from_row'
            if obs_tracker_source_row_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_row_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_row_id_table[obs_row_id][0], obs_tracker_hash_table[obs_tracker_plant_hash], 'plant_from_row')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_row_id_table[obs_row_id][0], obs_tracker_hash_table[obs_tracker_plant_hash], 'plant_from_row')] = obs_tracker_source_id

        obs_tracker_exp_hash = 'experiment' + str(experiment_name_table[experiment_name][0]) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(user_hash_table[user.username])
        if obs_tracker_exp_hash not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_exp_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'experiment', experiment_name_table[experiment_name][0], 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1

        obs_tracker_source_hash = str(obs_tracker_hash_table[obs_tracker_exp_hash]) + str(obs_tracker_hash_table[obs_tracker_plant_hash]) + 'plant_used_in_experiment'
        if obs_tracker_source_hash not in obs_tracker_source_hash_table:
            obs_tracker_source_hash_table[obs_tracker_source_hash] = obs_tracker_source_id
            obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], obs_tracker_hash_table[obs_tracker_plant_hash], 'plant_used_in_experiment')] = obs_tracker_source_id
            obs_tracker_source_id = obs_tracker_source_id + 1
        else:
            obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], obs_tracker_hash_table[obs_tracker_plant_hash], 'plant_used_in_experiment')] = obs_tracker_source_id


    end = time.clock()
    stats = {}
    stats[("Time: %s" % (end-start), "Errors: %s" % (error_count))] = error_count

    results_dict = {}
    results_dict['obs_plant_new'] = obs_plant_new
    results_dict['obs_tracker_new'] = obs_tracker_new
    results_dict['obs_tracker_source_new'] = obs_tracker_source_new
    results_dict['seed_id_error'] = seed_id_error
    results_dict['row_id_error'] = row_id_error
    results_dict['plant_hash_exists'] = plant_hash_exists
    results_dict['obs_tracker_hash_exists'] = obs_tracker_hash_exists
    results_dict['obs_tracker_source_hash_exists'] = obs_tracker_source_hash_exists
    results_dict['stats'] = stats
    return results_dict

def plant_loader_prep_output(results_dict, new_upload_exp, template_type):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s_%s_prep.csv"' % (new_upload_exp, template_type)
    writer = csv.writer(response)
    writer.writerow(['Stats'])
    writer.writerow([''])
    for key in results_dict['stats'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Plant Table'])
    writer.writerow(['obs_plant_id', 'plant_id', 'plant_num', 'comments'])
    for key in results_dict['obs_plant_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTracker Table'])
    writer.writerow(['obs_tracker_id', 'obs_entity_type', 'experiment_id', 'field_id', 'glycerol_stock_id', 'isolate_id', 'location_id', 'maize_sample_id', 'obs_culture_id', 'obs_dna_id', 'obs_env_id', 'obs_extract_id', 'obs_microbe_id', 'obs_plant_id', 'obs_plate_id', 'obs_row_id', 'obs_sample_id', 'obs_tissue_id', 'obs_well_id', 'stock_id', 'user_id'])
    for key in results_dict['obs_tracker_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTrackerSource Table'])
    writer.writerow(['obs_tracker_source_id', 'source_obs_id', 'targe_obs_id', 'relationship'])
    for key in results_dict['obs_tracker_source_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['---------------------------------------------------------------------------------------------------'])
    writer.writerow([''])
    writer.writerow(['Seed ID Errors'])
    writer.writerow(['plant_id', 'experiment_name', 'row_id', 'seed_id', 'plant_num', 'comments'])
    for key in results_dict['seed_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Row ID Errors'])
    writer.writerow(['plant_id', 'experiment_name', 'row_id', 'seed_id', 'plant_num', 'comments'])
    for key in results_dict['row_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Plant Entry Already Exists'])
    for key in results_dict['plant_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTracker Entry Already Exists'])
    for key in results_dict['obs_tracker_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTrackerSource Entries Already Exist'])
    for key in results_dict['obs_tracker_source_hash_exists'].keys():
        writer.writerow(key)
    return response

def plant_loader(results_dict):
    try:
        for key in results_dict['obs_plant_new'].keys():
            try:
                with transaction.atomic():
                    new_obsrow = ObsPlant.objects.create(id=key[0], plant_id=key[1], plant_num=key[2], comments=key[3])
            except Exception as e:
                print("ObsPlant Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = ObsTracker.objects.create(id=key[0], obs_entity_type=key[1], experiment_id=key[2], field_id=key[3], glycerol_stock_id=key[4], isolate_id=key[5], location_id=key[6], maize_sample_id=key[7], obs_culture_id=key[8], obs_dna_id=key[9], obs_env_id=key[10], obs_extract_id=key[11], obs_microbe_id=key[12], obs_plant_id=key[13], obs_plate_id=key[14], obs_row_id=key[15], obs_sample_id=key[16], obs_tissue_id=key[17], obs_well_id=key[18], stock_id=key[19], user_id=key[20])
            except Exception as e:
                print("ObsTracker Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_source_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = ObsTrackerSource.objects.create(id=key[0], source_obs_id=key[1], target_obs_id=key[2], relationship=key[3])
            except Exception as e:
                print("ObsTrackerSource Error: %s %s" % (e.message, e.args))
                return False
    except Exception as e:
        print("Error: %s %s" % (e.message, e.args))
        return False
    return True

def tissue_loader_prep(upload_file, user):
    start = time.clock()

    obs_tissue_new = OrderedDict({})
    #--- Key = (obs_tissue_id, tissue_id, tissue_type, tissue_name, date_ground, comments)
    #--- Value = (obs_tissue_id)
    obs_tracker_new = OrderedDict({})
    #--- Key = (obs_tracker_id, obs_entity_type, experiment_id, field_id, glycerol_stock_id, isolate_id, location_id, maize_sample_id, obs_culture_id, obs_dna_id, obs_env_id, obs_extract_id, obs_microbe_id, obs_plant_id, obs_plate_id, obs_row_id, obs_sample_id, obs_tissue_id, obs_well_id, stock_id, user_id)
    #--- Value = (obs_tracker_id)
    obs_tracker_source_new = OrderedDict({})
    #--- Key = (obs_tracker_source_id, source_obs_id, target_obs_id, relationship)
    #--- Value = (obs_tracker_source_id)

    user_hash_table = loader_db_mirror.user_hash_mirror()
    obs_tissue_hash_table = loader_db_mirror.obs_tissue_hash_mirror()
    obs_tissue_id = loader_db_mirror.obs_tissue_id_mirror()
    row_id_table = loader_db_mirror.row_id_mirror()
    seed_id_table = loader_db_mirror.seed_id_mirror()
    plant_id_table = loader_db_mirror.plant_id_mirror()
    culture_id_table = loader_db_mirror.culture_id_mirror()
    tissue_id_table = loader_db_mirror.tissue_id_mirror()
    obs_tracker_hash_table = loader_db_mirror.obs_tracker_hash_mirror()
    obs_tracker_source_hash_table = loader_db_mirror.obs_tracker_source_hash_mirror()
    obs_tracker_stock_id_table = loader_db_mirror.obs_tracker_stock_id_mirror()
    obs_tracker_obs_row_id_table = loader_db_mirror.obs_tracker_obs_row_id_mirror()
    obs_tracker_obs_plant_id_table = loader_db_mirror.obs_tracker_obs_plant_id_mirror()
    obs_tracker_obs_culture_id_table = loader_db_mirror.obs_tracker_obs_culture_id_mirror()
    obs_tracker_id = loader_db_mirror.obs_tracker_id_mirror()
    obs_tracker_source_id = loader_db_mirror.obs_tracker_source_id_mirror()
    experiment_name_table = loader_db_mirror.experiment_name_mirror()

    error_count = 0
    seed_id_error = OrderedDict({})
    row_id_error = OrderedDict({})
    plant_id_error = OrderedDict({})
    culture_id_error = OrderedDict({})
    tissue_hash_exists = OrderedDict({})
    obs_tracker_hash_exists = OrderedDict({})
    obs_tracker_source_hash_exists = OrderedDict({})

    tissue_file = csv.DictReader(codecs.iterdecode(upload_file, 'utf-8'))
    for row in tissue_file:
        tissue_id = row["Tissue ID"]
        experiment_name = row["Experiment Name"]
        tissue_name = row["Tissue Name"]
        tissue_type = row["Tissue Type"]
        date_ground = row["Date Ground"]
        tissue_comments = row["Tissue Comments"]
        row_id = row["Source Row ID"]
        seed_id = row["Source Seed ID"]
        plant_id = row["Source Plant ID"]
        culture_id = row["Source Culture ID"]
        user = user

        if seed_id != '':
            seed_id_fix = seed_id + '\r'
            if seed_id in seed_id_table:
                stock_id = seed_id_table[seed_id][0]
            elif seed_id_fix in seed_id_table:
                stock_id = seed_id_table[seed_id_fix][0]
            else:
                seed_id_error[(tissue_id, experiment_name, tissue_name, tissue_type, date_ground, row_id, seed_id, plant_id, culture_id, tissue_comments)] = error_count
                error_count = error_count + 1
                stock_id = 1
        else:
            stock_id = 1

        if row_id != '':
            row_id_fix = row_id + '\r'
            if row_id in row_id_table:
                obs_row_id = row_id_table[row_id][0]
            elif row_id_fix in row_id_table:
                obs_row_id = row_id_table[row_id_fix][0]
            else:
                row_id_error[(tissue_id, experiment_name, tissue_name, tissue_type, date_ground, row_id, seed_id, plant_id, culture_id, tissue_comments)] = error_count
                error_count = error_count + 1
                obs_row_id = 1
        else:
            obs_row_id = 1

        if plant_id != '':
            plant_id_fix = plant_id + '\r'
            if plant_id in plant_id_table:
                obs_plant_id = plant_id_table[plant_id][0]
            elif plant_id_fix in plant_id_table:
                obs_plant_id = plant_id_table[plant_id_fix][0]
            else:
                plant_id_error[(tissue_id, experiment_name, tissue_name, tissue_type, date_ground, row_id, seed_id, plant_id, culture_id, tissue_comments)] = error_count
                error_count = error_count + 1
                obs_plant_id = 1
        else:
            obs_plant_id = 1

        if culture_id != '':
            culture_id_fix = culture_id + '\r'
            if culture_id in culture_id_table:
                obs_culture_id = culture_id_table[culture_id][0]
            elif culture_id_fix in culture_id_table:
                obs_culture_id = culture_id_table[culture_id_fix][0]
            else:
                culture_id_error[(tissue_id, experiment_name, tissue_name, tissue_type, date_ground, row_id, seed_id, plant_id, culture_id, tissue_comments)] = error_count
                error_count = error_count + 1
                obs_culture_id = 1
        else:
            obs_culture_id = 1

        tissue_hash = tissue_id + tissue_type + tissue_name + date_ground + tissue_comments
        tissue_hash_fix = tissue_hash + '\r'
        if tissue_id not in tissue_id_table and tissue_id + '\r' not in tissue_id_table:
            if tissue_hash not in obs_tissue_hash_table and tissue_hash_fix not in obs_tissue_hash_table:
                obs_tissue_hash_table[tissue_hash] = obs_tissue_id
                obs_tissue_new[(obs_tissue_id, tissue_id, tissue_type, tissue_name, date_ground, tissue_comments)] = obs_tissue_id
                tissue_id_table[tissue_id] = (obs_tissue_id, tissue_id, tissue_type, tissue_name, date_ground, tissue_comments)
                obs_tissue_id = obs_tissue_id + 1
            else:
                tissue_hash_exists[(tissue_id, tissue_type, tissue_name, date_ground, tissue_comments)] = obs_tissue_id
        else:
            tissue_hash_exists[(tissue_id, tissue_type, tissue_name, date_ground, tissue_comments)] = obs_tissue_id

        if tissue_id in tissue_id_table:
            temp_obstissue_id = tissue_id_table[tissue_id][0]
        elif tissue_id + '\r' in tissue_id_table:
            temp_obstissue_id = tissue_id_table[tissue_id + '\r'][0]
        elif tissue_hash in obs_tissue_hash_table:
            temp_obstissue_id = obs_tissue_hash_table[tissue_hash]
        elif tissue_hash_fix in obs_tissue_hash_table:
            temp_obstissue_id = obs_tissue_hash_table[tissue_hash_fix]
        else:
            temp_obstissue_id = 1
            error_count = error_count + 1

        obs_tracker_tissue_hash = 'tissue' + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(obs_culture_id) + str(1) + str(1) + str(1) + str(1) + str(obs_plant_id) + str(1) + str(obs_row_id) + str(1) + str(temp_obstissue_id) + str(1) + str(stock_id) + str(user_hash_table[user.username])
        obs_tracker_tissue_hash_fix = obs_tracker_tissue_hash + '\r'
        if obs_tracker_tissue_hash not in obs_tracker_hash_table and obs_tracker_tissue_hash_fix not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_tissue_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'tissue', 1, 1, 1, 1, 1, 1, obs_culture_id, 1, 1, 1, 1, obs_plant_id, 1, obs_row_id, 1, temp_obstissue_id, 1, stock_id, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1
        else:
            obs_tracker_hash_exists[('tissue', 1, 1, 1, 1, 1, 1, obs_culture_id, 1, 1, 1, 1, obs_plant_id, 1, obs_row_id, 1, temp_obstissue_id, 1, stock_id, user_hash_table[user.username])] = obs_tracker_id

        if stock_id != 1:
            obs_tracker_source_stock_hash = str(obs_tracker_stock_id_table[stock_id][0]) + str(obs_tracker_hash_table[obs_tracker_tissue_hash]) + 'tissue_from_stock'
            if obs_tracker_source_stock_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_stock_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_stock_id_table[stock_id][0], obs_tracker_hash_table[obs_tracker_tissue_hash], 'tissue_from_stock')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_stock_id_table[stock_id][0], obs_tracker_hash_table[obs_tracker_tissue_hash], 'tissue_from_stock')] = obs_tracker_source_id

        if obs_row_id != 1:
            obs_tracker_source_row_hash = str(obs_tracker_obs_row_id_table[obs_row_id][0]) + str(obs_tracker_hash_table[obs_tracker_tissue_hash]) + 'tissue_from_row'
            if obs_tracker_source_row_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_row_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_row_id_table[obs_row_id][0], obs_tracker_hash_table[obs_tracker_tissue_hash], 'tissue_from_row')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_row_id_table[obs_row_id][0], obs_tracker_hash_table[obs_tracker_tissue_hash], 'tissue_from_row')] = obs_tracker_source_id

        if obs_plant_id != 1:
            obs_tracker_source_plant_hash = str(obs_tracker_obs_plant_id_table[obs_plant_id][0]) + str(obs_tracker_hash_table[obs_tracker_tissue_hash]) + 'tissue_from_plant'
            if obs_tracker_source_plant_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_plant_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_plant_id_table[obs_plant_id][0], obs_tracker_hash_table[obs_tracker_tissue_hash], 'tissue_from_plant')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_plant_id_table[obs_plant_id][0], obs_tracker_hash_table[obs_tracker_tissue_hash], 'tissue_from_plant')] = obs_tracker_source_id

        if obs_culture_id != 1:
            obs_tracker_source_culture_hash = str(obs_tracker_obs_culture_id_table[obs_culture_id][0]) + str(obs_tracker_hash_table[obs_tracker_tissue_hash]) + 'tissue_from_culture'
            if obs_tracker_source_culture_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_culture_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_culture_id_table[obs_culture_id][0], obs_tracker_hash_table[obs_tracker_tissue_hash], 'tissue_from_culture')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_culture_id_table[obs_culture_id][0], obs_tracker_hash_table[obs_tracker_tissue_hash], 'tissue_from_culture')] = obs_tracker_source_id

        obs_tracker_exp_hash = 'experiment' + str(experiment_name_table[experiment_name][0]) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(user_hash_table[user.username])
        if obs_tracker_exp_hash not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_exp_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'experiment', experiment_name_table[experiment_name][0], 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1

        obs_tracker_source_hash = str(obs_tracker_hash_table[obs_tracker_exp_hash]) + str(obs_tracker_hash_table[obs_tracker_tissue_hash]) + 'tissue_used_in_experiment'
        if obs_tracker_source_hash not in obs_tracker_source_hash_table:
            obs_tracker_source_hash_table[obs_tracker_source_hash] = obs_tracker_source_id
            obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], obs_tracker_hash_table[obs_tracker_tissue_hash], 'tissue_used_in_experiment')] = obs_tracker_source_id
            obs_tracker_source_id = obs_tracker_source_id + 1
        else:
            obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], obs_tracker_hash_table[obs_tracker_tissue_hash], 'tissue_used_in_experiment')] = obs_tracker_source_id


    end = time.clock()
    stats = {}
    stats[("Time: %s" % (end-start), "Errors: %s" % (error_count))] = error_count

    results_dict = {}
    results_dict['obs_tissue_new'] = obs_tissue_new
    results_dict['obs_tracker_new'] = obs_tracker_new
    results_dict['obs_tracker_source_new'] = obs_tracker_source_new
    results_dict['seed_id_error'] = seed_id_error
    results_dict['row_id_error'] = row_id_error
    results_dict['plant_id_error'] = plant_id_error
    results_dict['culture_id_error'] = culture_id_error
    results_dict['tissue_hash_exists'] = tissue_hash_exists
    results_dict['obs_tracker_hash_exists'] = obs_tracker_hash_exists
    results_dict['obs_tracker_source_hash_exists'] = obs_tracker_source_hash_exists
    results_dict['stats'] = stats
    return results_dict

def tissue_loader_prep_output(results_dict, new_upload_exp, template_type):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s_%s_prep.csv"' % (new_upload_exp, template_type)
    writer = csv.writer(response)
    writer.writerow(['Stats'])
    writer.writerow([''])
    for key in results_dict['stats'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Tissue Table'])
    writer.writerow(['obs_tissue_id', 'tissue_id', 'tissue_type', 'tissue_name', 'date_ground', 'comments'])
    for key in results_dict['obs_tissue_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTracker Table'])
    writer.writerow(['obs_tracker_id', 'obs_entity_type', 'experiment_id', 'field_id', 'glycerol_stock_id', 'isolate_id', 'location_id', 'maize_sample_id', 'obs_culture_id', 'obs_dna_id', 'obs_env_id', 'obs_extract_id', 'obs_microbe_id', 'obs_plant_id', 'obs_plate_id', 'obs_row_id', 'obs_sample_id', 'obs_tissue_id', 'obs_well_id', 'stock_id', 'user_id'])
    for key in results_dict['obs_tracker_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTrackerSource Table'])
    writer.writerow(['obs_tracker_source_id', 'source_obs_id', 'targe_obs_id', 'relationship'])
    for key in results_dict['obs_tracker_source_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['---------------------------------------------------------------------------------------------------'])
    writer.writerow([''])
    writer.writerow(['Seed ID Errors'])
    writer.writerow(['tissue_id', 'experiment_name', 'tissue_name', 'tissue_type', 'date_ground', 'source_row_id', 'source_seed_id', 'source_plant_id', 'source_culture_id', 'tissue_comments'])
    for key in results_dict['seed_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Row ID Errors'])
    writer.writerow(['tissue_id', 'experiment_name', 'tissue_name', 'tissue_type', 'date_ground', 'source_row_id', 'source_seed_id', 'source_plant_id', 'source_culture_id', 'tissue_comments'])
    for key in results_dict['row_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Plant ID Errors'])
    writer.writerow(['tissue_id', 'experiment_name', 'tissue_name', 'tissue_type', 'date_ground', 'source_row_id', 'source_seed_id', 'source_plant_id', 'source_culture_id', 'tissue_comments'])
    for key in results_dict['plant_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Culture ID Errors'])
    writer.writerow(['tissue_id', 'experiment_name', 'tissue_name', 'tissue_type', 'date_ground', 'source_row_id', 'source_seed_id', 'source_plant_id', 'source_culture_id', 'tissue_comments'])
    for key in results_dict['culture_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Tissue Entry Already Exists'])
    for key in results_dict['tissue_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTracker Entry Already Exists'])
    for key in results_dict['obs_tracker_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTrackerSource Entries Already Exist'])
    for key in results_dict['obs_tracker_source_hash_exists'].keys():
        writer.writerow(key)
    return response

def tissue_loader(results_dict):
    try:
        for key in results_dict['obs_tissue_new'].keys():
            try:
                with transaction.atomic():
                    new_obstissue = ObsTissue.objects.create(id=key[0], tissue_id=key[1], tissue_type=key[2], tissue_name=key[3], date_ground=key[4], comments=key[5])
            except Exception as e:
                print("ObsTissue Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = ObsTracker.objects.create(id=key[0], obs_entity_type=key[1], experiment_id=key[2], field_id=key[3], glycerol_stock_id=key[4], isolate_id=key[5], location_id=key[6], maize_sample_id=key[7], obs_culture_id=key[8], obs_dna_id=key[9], obs_env_id=key[10], obs_extract_id=key[11], obs_microbe_id=key[12], obs_plant_id=key[13], obs_plate_id=key[14], obs_row_id=key[15], obs_sample_id=key[16], obs_tissue_id=key[17], obs_well_id=key[18], stock_id=key[19], user_id=key[20])
            except Exception as e:
                print("ObsTracker Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_source_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = ObsTrackerSource.objects.create(id=key[0], source_obs_id=key[1], target_obs_id=key[2], relationship=key[3])
            except Exception as e:
                print("ObsTrackerSource Error: %s %s" % (e.message, e.args))
                return False
    except Exception as e:
        print("Error: %s %s" % (e.message, e.args))
        return False
    return True

def culture_loader_prep(upload_file, user):
    start = time.clock()

    obs_culture_new = OrderedDict({})
    #--- Key = (obs_culture_id, medium_id, culture_id, culture_name, microbe_type, plating_cycle, dilution, image_filename, comments, num_colonies, num_microbes)
    #--- Value = (obs_culture_id)
    obs_tracker_new = OrderedDict({})
    #--- Key = (obs_tracker_id, obs_entity_type, experiment_id, field_id, glycerol_stock_id, isolate_id, location_id, maize_sample_id, obs_culture_id, obs_dna_id, obs_env_id, obs_extract_id, obs_microbe_id, obs_plant_id, obs_plate_id, obs_row_id, obs_sample_id, obs_tissue_id, obs_well_id, stock_id, user_id)
    #--- Value = (obs_tracker_id)
    obs_tracker_source_new = OrderedDict({})
    #--- Key = (obs_tracker_source_id, source_obs_id, target_obs_id, relationship)
    #--- Value = (obs_tracker_source_id)

    user_hash_table = loader_db_mirror.user_hash_mirror()
    obs_culture_hash_table = loader_db_mirror.obs_culture_hash_mirror()
    obs_culture_id = loader_db_mirror.obs_culture_id_mirror()
    row_id_table = loader_db_mirror.row_id_mirror()
    seed_id_table = loader_db_mirror.seed_id_mirror()
    plant_id_table = loader_db_mirror.plant_id_mirror()
    tissue_id_table = loader_db_mirror.tissue_id_mirror()
    microbe_id_table = loader_db_mirror.microbe_id_mirror()
    culture_id_table = loader_db_mirror.culture_id_mirror()
    obs_tracker_hash_table = loader_db_mirror.obs_tracker_hash_mirror()
    obs_tracker_stock_id_table = loader_db_mirror.obs_tracker_stock_id_mirror()
    obs_tracker_obs_row_id_table = loader_db_mirror.obs_tracker_obs_row_id_mirror()
    obs_tracker_obs_plant_id_table = loader_db_mirror.obs_tracker_obs_plant_id_mirror()
    obs_tracker_obs_tissue_id_table = loader_db_mirror.obs_tracker_obs_tissue_id_mirror()
    obs_tracker_obs_microbe_id_table = loader_db_mirror.obs_tracker_obs_microbe_id_mirror()
    obs_tracker_source_hash_table = loader_db_mirror.obs_tracker_source_hash_mirror()
    obs_tracker_id = loader_db_mirror.obs_tracker_id_mirror()
    obs_tracker_source_id = loader_db_mirror.obs_tracker_source_id_mirror()
    experiment_name_table = loader_db_mirror.experiment_name_mirror()
    media_name_table = loader_db_mirror.medium_name_mirror()
    location_name_table = loader_db_mirror.location_name_mirror()

    error_count = 0
    seed_id_error = OrderedDict({})
    row_id_error = OrderedDict({})
    plant_id_error = OrderedDict({})
    tissue_id_error = OrderedDict({})
    microbe_id_error = OrderedDict({})
    media_name_error = OrderedDict({})
    location_name_error = OrderedDict({})
    culture_hash_exists = OrderedDict({})
    obs_tracker_hash_exists = OrderedDict({})
    obs_tracker_source_hash_exists = OrderedDict({})

    culture_file = csv.DictReader(codecs.iterdecode(upload_file, 'utf-8'))
    for row in culture_file:
        culture_id = row["Culture ID"]
        experiment_name = row["Experiment Name"]
        media_name = row["Media Name"]
        location_name = row["Location Name"]
        culture_name = row["Culture Name"]
        microbe_type = row["Microbe Type"]
        plating_cycle = row["Plating Cycle"]
        dilution = row["Dilution"]
        image_filename = row["Image File"]
        culture_comments = row["Culture Comments"]
        num_colonies = row["Num Colonies"]
        num_microbes = row["Num Microbes"]
        row_id = row["Source Row ID"]
        seed_id = row["Source Seed ID"]
        plant_id = row["Source Plant ID"]
        tissue_id = row["Source Tissue ID"]
        microbe_id = row["Source Microbe ID"]
        user = user

        if seed_id != '':
            seed_id_fix = seed_id + '\r'
            if seed_id in seed_id_table:
                stock_id = seed_id_table[seed_id][0]
            elif seed_id_fix in seed_id_table:
                stock_id = seed_id_table[seed_id_fix][0]
            else:
                seed_id_error[(culture_id, experiment_name, media_name, location_name, culture_name, microbe_type, plating_cycle, dilution, image_filename, culture_comments, row_id, seed_id, plant_id, tissue_id, microbe_id)] = error_count
                error_count = error_count + 1
                stock_id = 1
        else:
            stock_id = 1

        if row_id != '':
            row_id_fix = row_id + '\r'
            if row_id in row_id_table:
                obs_row_id = row_id_table[row_id][0]
            elif row_id_fix in row_id_table:
                obs_row_id = row_id_table[row_id_fix][0]
            else:
                row_id_error[(culture_id, experiment_name, media_name, location_name, culture_name, microbe_type, plating_cycle, dilution, image_filename, culture_comments, row_id, seed_id, plant_id, tissue_id, microbe_id)] = error_count
                error_count = error_count + 1
                obs_row_id = 1
        else:
            obs_row_id = 1

        if plant_id != '':
            plant_id_fix = plant_id + '\r'
            if plant_id in plant_id_table:
                obs_plant_id = plant_id_table[plant_id][0]
            elif plant_id_fix in plant_id_table:
                obs_plant_id = plant_id_table[plant_id_fix][0]
            else:
                plant_id_error[(culture_id, experiment_name, media_name, location_name, culture_name, microbe_type, plating_cycle, dilution, image_filename, culture_comments, row_id, seed_id, plant_id, tissue_id, microbe_id)] = error_count
                error_count = error_count + 1
                obs_plant_id = 1
        else:
            obs_plant_id = 1

        if tissue_id != '':
            tissue_id_fix = tissue_id + '\r'
            if tissue_id in tissue_id_table:
                obs_tissue_id = tissue_id_table[tissue_id][0]
            elif tissue_id_fix in tissue_id_table:
                obs_tissue_id = tissue_id_table[tissue_id_fix][0]
            else:
                tissue_id_error[(culture_id, experiment_name, media_name, location_name, culture_name, microbe_type, plating_cycle, dilution, image_filename, culture_comments, row_id, seed_id, plant_id, tissue_id, microbe_id)] = error_count
                error_count = error_count + 1
                obs_tissue_id = 1
        else:
            obs_tissue_id = 1

        if microbe_id != '':
            microbe_id_fix = microbe_id + '\r'
            if microbe_id in microbe_id_table:
                obs_microbe_id = microbe_id_table[microbe_id][0]
            elif microbe_id_fix in microbe_id_table:
                obs_microbe_id = microbe_id_table[microbe_id_fix][0]
            else:
                microbe_id_error[(culture_id, experiment_name, media_name, location_name, culture_name, microbe_type, plating_cycle, dilution, image_filename, culture_comments, row_id, seed_id, plant_id, tissue_id, microbe_id)] = error_count
                error_count = error_count + 1
                obs_microbe_id = 1
        else:
            obs_microbe_id = 1

        if media_name != '':
            media_name_fix = media_name + '\r'
            if media_name in media_name_table:
                medium_id = media_name_table[media_name][0]
            elif media_name_fix in media_name_table:
                medium_id = media_name_table[media_name_fix][0]
            else:
                media_name_error[(culture_id, experiment_name, media_name, location_name, culture_name, microbe_type, plating_cycle, dilution, image_filename, culture_comments, row_id, seed_id, plant_id, tissue_id, microbe_id)] = error_count
                error_count = error_count + 1
                medium_id = 1
        else:
            medium_id = 1

        if location_name != '':
            location_name_fix = location_name + '\r'
            if location_name in location_name_table:
                location_id = location_name_table[location_name][0]
            elif location_name_fix in location_name_table:
                location_id = location_name_table[location_name_fix][0]
            else:
                location_name_error[(culture_id, experiment_name, media_name, location_name, culture_name, microbe_type, plating_cycle, dilution, image_filename, culture_comments, row_id, seed_id, plant_id, tissue_id, microbe_id)] = error_count
                error_count = error_count + 1
                location_id = 1
        else:
            location_id = 1

        culture_hash = str(medium_id) + culture_id + culture_name + microbe_type + plating_cycle + dilution + image_filename + culture_comments + num_colonies + num_microbes
        culture_hash_fix = culture_hash + '\r'
        if culture_id not in culture_id_table and culture_id + '\r' not in culture_id_table:
            if culture_hash not in obs_culture_hash_table and culture_hash_fix not in obs_culture_hash_table:
                obs_culture_hash_table[culture_hash] = obs_culture_id
                obs_culture_new[(obs_culture_id, medium_id, culture_id, culture_name, microbe_type, plating_cycle, dilution, image_filename, culture_comments, num_colonies, num_microbes)] = obs_culture_id
                culture_id_table[culture_id] = (obs_culture_id, medium_id, culture_id, culture_name, microbe_type, plating_cycle, dilution, image_filename, culture_comments, num_colonies, num_microbes)
                obs_culture_id = obs_culture_id + 1
            else:
                culture_hash_exists[(medium_id, culture_id, culture_name, microbe_type, plating_cycle, dilution, image_filename, culture_comments, num_colonies, num_microbes)] = obs_culture_id
        else:
            culture_hash_exists[(medium_id, culture_id, culture_name, microbe_type, plating_cycle, dilution, image_filename, culture_comments, num_colonies, num_microbes)] = obs_culture_id

        if culture_id in culture_id_table:
            temp_obsculture_id = culture_id_table[culture_id][0]
        elif culture_id + '\r' in culture_id_table:
            temp_obsculture_id = culture_id_table[culture_id + '\r'][0]
        elif culture_hash in obs_culture_hash_table:
            temp_obsculture_id = obs_culture_hash_table[culture_hash]
        elif culture_hash_fix in obs_culture_hash_table:
            temp_obsculture_id = obs_culture_hash_table[culture_hash_fix]
        else:
            temp_obsculture_id = 1
            error_count = error_count + 1

        obs_tracker_culture_hash = 'culture' + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(temp_obsculture_id) + str(1) + str(1) + str(1) + str(obs_microbe_id) + str(obs_plant_id) + str(1) + str(obs_row_id) + str(1) + str(obs_tissue_id) + str(1) + str(stock_id) + str(user_hash_table[user.username])
        obs_tracker_culture_hash_fix = obs_tracker_culture_hash + '\r'
        if obs_tracker_culture_hash not in obs_tracker_hash_table and obs_tracker_culture_hash_fix not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_culture_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'culture', 1, 1, 1, 1, 1, 1, temp_obsculture_id, 1, 1, 1, obs_microbe_id, obs_plant_id, 1, obs_row_id, 1, obs_tissue_id, 1, stock_id, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1
        else:
            obs_tracker_hash_exists[('culture', 1, 1, 1, 1, 1, 1, temp_obsculture_id, 1, 1, 1, obs_microbe_id, obs_plant_id, 1, obs_row_id, 1, obs_tissue_id, 1, stock_id, user_hash_table[user.username])] = obs_tracker_id

        if stock_id != 1:
            obs_tracker_source_stock_hash = str(obs_tracker_stock_id_table[stock_id][0]) + str(obs_tracker_hash_table[obs_tracker_culture_hash]) + 'culture_from_stock'
            if obs_tracker_source_stock_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_stock_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_stock_id_table[stock_id][0], obs_tracker_hash_table[obs_tracker_culture_hash], 'culture_from_stock')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_stock_id_table[stock_id][0], obs_tracker_hash_table[obs_tracker_culture_hash], 'culture_from_stock')] = obs_tracker_source_id

        if obs_row_id != 1:
            obs_tracker_source_row_hash = str(obs_tracker_obs_row_id_table[obs_row_id][0]) + str(obs_tracker_hash_table[obs_tracker_culture_hash]) + 'culture_from_row'
            if obs_tracker_source_row_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_row_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_row_id_table[obs_row_id][0], obs_tracker_hash_table[obs_tracker_culture_hash], 'culture_from_row')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_row_id_table[obs_row_id][0], obs_tracker_hash_table[obs_tracker_culture_hash], 'culture_from_row')] = obs_tracker_source_id

        if obs_plant_id != 1:
            obs_tracker_source_plant_hash = str(obs_tracker_obs_plant_id_table[obs_plant_id][0]) + str(obs_tracker_hash_table[obs_tracker_culture_hash]) + 'culture_from_plant'
            if obs_tracker_source_plant_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_plant_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_plant_id_table[obs_plant_id][0], obs_tracker_hash_table[obs_tracker_culture_hash], 'culture_from_plant')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_plant_id_table[obs_plant_id][0], obs_tracker_hash_table[obs_tracker_culture_hash], 'culture_from_plant')] = obs_tracker_source_id

        if obs_tissue_id != 1:
            obs_tracker_source_tissue_hash = str(obs_tracker_obs_tissue_id_table[obs_tissue_id][0]) + str(obs_tracker_hash_table[obs_tracker_culture_hash]) + 'culture_from_tissue'
            if obs_tracker_source_tissue_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_tissue_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_tissue_id_table[obs_tissue_id][0], obs_tracker_hash_table[obs_tracker_culture_hash], 'culture_from_tissue')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_tissue_id_table[obs_tissue_id][0], obs_tracker_hash_table[obs_tracker_culture_hash], 'culture_from_tissue')] = obs_tracker_source_id

        if obs_microbe_id != 1:
            obs_tracker_source_microbe_hash = str(obs_tracker_obs_microbe_id_table[obs_microbe_id][0]) + str(obs_tracker_hash_table[obs_tracker_culture_hash]) + 'culture_from_microbe'
            if obs_tracker_source_microbe_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_microbe_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_microbe_id_table[obs_microbe_id][0], obs_tracker_hash_table[obs_tracker_culture_hash], 'culture_from_microbe')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_microbe_id_table[obs_microbe_id][0], obs_tracker_hash_table[obs_tracker_culture_hash], 'culture_from_microbe')] = obs_tracker_source_id

        obs_tracker_exp_hash = 'experiment' + str(experiment_name_table[experiment_name][0]) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(user_hash_table[user.username])
        if obs_tracker_exp_hash not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_exp_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'experiment', experiment_name_table[experiment_name][0], 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1

        obs_tracker_source_hash = str(obs_tracker_hash_table[obs_tracker_exp_hash]) + str(obs_tracker_hash_table[obs_tracker_culture_hash]) + 'culture_used_in_experiment'
        if obs_tracker_source_hash not in obs_tracker_source_hash_table:
            obs_tracker_source_hash_table[obs_tracker_source_hash] = obs_tracker_source_id
            obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], obs_tracker_hash_table[obs_tracker_culture_hash], 'culture_used_in_experiment')] = obs_tracker_source_id
            obs_tracker_source_id = obs_tracker_source_id + 1
        else:
            obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], obs_tracker_hash_table[obs_tracker_culture_hash], 'culture_used_in_experiment')] = obs_tracker_source_id

    end = time.clock()
    stats = {}
    stats[("Time: %s" % (end-start), "Errors: %s" % (error_count))] = error_count

    results_dict = {}
    results_dict['obs_culture_new'] = obs_culture_new
    results_dict['obs_tracker_new'] = obs_tracker_new
    results_dict['obs_tracker_source_new'] = obs_tracker_source_new
    results_dict['seed_id_error'] = seed_id_error
    results_dict['row_id_error'] = row_id_error
    results_dict['plant_id_error'] = plant_id_error
    results_dict['tissue_id_error'] = tissue_id_error
    results_dict['microbe_id_error'] = microbe_id_error
    results_dict['media_name_error'] = media_name_error
    results_dict['location_name_error'] = location_name_error
    results_dict['culture_hash_exists'] = culture_hash_exists
    results_dict['obs_tracker_hash_exists'] = obs_tracker_hash_exists
    results_dict['obs_tracker_source_hash_exists'] = obs_tracker_source_hash_exists
    results_dict['stats'] = stats
    return results_dict

def culture_loader_prep_output(results_dict, new_upload_exp, template_type):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s_%s_prep.csv"' % (new_upload_exp, template_type)
    writer = csv.writer(response)
    writer.writerow(['Stats'])
    writer.writerow([''])
    for key in results_dict['stats'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Culture Table'])
    writer.writerow(['obs_culture_id', 'medium_id', 'culture_id', 'culture_name', 'microbe_type', 'plating_cycle', 'dilution', 'image_filename', 'tissue_comments', 'num_colonies', 'num_microbes'])
    for key in results_dict['obs_culture_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTracker Table'])
    writer.writerow(['obs_tracker_id', 'obs_entity_type', 'experiment_id', 'field_id', 'glycerol_stock_id', 'isolate_id', 'location_id', 'maize_sample_id', 'obs_culture_id', 'obs_dna_id', 'obs_env_id', 'obs_extract_id', 'obs_microbe_id', 'obs_plant_id', 'obs_plate_id', 'obs_row_id', 'obs_sample_id', 'obs_tissue_id', 'obs_well_id', 'stock_id', 'user_id'])
    for key in results_dict['obs_tracker_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTrackerSource Table'])
    writer.writerow(['obs_tracker_source_id', 'source_obs_id', 'targe_obs_id', 'relationship'])
    for key in results_dict['obs_tracker_source_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['---------------------------------------------------------------------------------------------------'])
    writer.writerow([''])
    writer.writerow(['Seed ID Errors'])
    writer.writerow(['culture_id', 'experiment_name', 'media_name', 'location_name', 'culture_name', 'microbe_type', 'plating_cycle', 'dilution', 'image_filename', 'culture_comments', 'source_row_id', 'source_seed_id', 'source_plant_id', 'source_tissue_id', 'source_microbe_id'])
    for key in results_dict['seed_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Row ID Errors'])
    writer.writerow(['culture_id', 'experiment_name', 'media_name', 'location_name', 'culture_name', 'microbe_type', 'plating_cycle', 'dilution', 'image_filename', 'culture_comments', 'source_row_id', 'source_seed_id', 'source_plant_id', 'source_tissue_id', 'source_microbe_id'])
    for key in results_dict['row_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Plant ID Errors'])
    writer.writerow(['culture_id', 'experiment_name', 'media_name', 'location_name', 'culture_name', 'microbe_type', 'plating_cycle', 'dilution', 'image_filename', 'culture_comments', 'source_row_id', 'source_seed_id', 'source_plant_id', 'source_tissue_id', 'source_microbe_id'])
    for key in results_dict['plant_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Tissue ID Errors'])
    writer.writerow(['culture_id', 'experiment_name', 'media_name', 'location_name', 'culture_name', 'microbe_type', 'plating_cycle', 'dilution', 'image_filename', 'culture_comments', 'source_row_id', 'source_seed_id', 'source_plant_id', 'source_tissue_id', 'source_microbe_id'])
    for key in results_dict['tissue_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Microbe ID Errors'])
    writer.writerow(['culture_id', 'experiment_name', 'media_name', 'location_name', 'culture_name', 'microbe_type', 'plating_cycle', 'dilution', 'image_filename', 'culture_comments', 'source_row_id', 'source_seed_id', 'source_plant_id', 'source_tissue_id', 'source_microbe_id'])
    for key in results_dict['microbe_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Culture Entry Already Exists'])
    for key in results_dict['culture_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTracker Entry Already Exists'])
    for key in results_dict['obs_tracker_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTrackerSource Entries Already Exist'])
    for key in results_dict['obs_tracker_source_hash_exists'].keys():
        writer.writerow(key)
    return response

def culture_loader(results_dict):
    try:
        for key in results_dict['obs_culture_new'].keys():
            try:
                with transaction.atomic():
                    new_obsculture = ObsCulture.objects.create(id=key[0], medium_id=key[1], culture_id=key[2], culture_name=key[3], microbe_type=key[4], plating_cycle=key[5], dilution=key[6], image_filename=key[7], comments=key[8], num_colonies=key[9], num_microbes=key[10])
            except Exception as e:
                print("ObsCulture Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = ObsTracker.objects.create(id=key[0], obs_entity_type=key[1], experiment_id=key[2], field_id=key[3], glycerol_stock_id=key[4], isolate_id=key[5], location_id=key[6], maize_sample_id=key[7], obs_culture_id=key[8], obs_dna_id=key[9], obs_env_id=key[10], obs_extract_id=key[11], obs_microbe_id=key[12], obs_plant_id=key[13], obs_plate_id=key[14], obs_row_id=key[15], obs_sample_id=key[16], obs_tissue_id=key[17], obs_well_id=key[18], stock_id=key[19], user_id=key[20])
            except Exception as e:
                print("ObsTracker Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_source_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = ObsTrackerSource.objects.create(id=key[0], source_obs_id=key[1], target_obs_id=key[2], relationship=key[3])
            except Exception as e:
                print("ObsTrackerSource Error: %s %s" % (e.message, e.args))
                return False
    except Exception as e:
        print("Error: %s %s" % (e.message, e.args))
        return False
    return True

def dna_loader_prep(upload_file, user):
    start = time.clock()

    obs_dna_new = OrderedDict({})
    #--- Key = (obs_dna_id, dna_id, extraction_method, date, tube_id, tube_type, comments)
    #--- Value = (obs_dna_id)
    obs_tracker_new = OrderedDict({})
    #--- Key = (obs_tracker_id, obs_entity_type, experiment_id, field_id, glycerol_stock_id, isolate_id, location_id, maize_sample_id, obs_culture_id, obs_dna_id, obs_env_id, obs_extract_id, obs_microbe_id, obs_plant_id, obs_plate_id, obs_row_id, obs_sample_id, obs_tissue_id, obs_well_id, stock_id, user_id)
    #--- Value = (obs_tracker_id)
    obs_tracker_source_new = OrderedDict({})
    #--- Key = (obs_tracker_source_id, source_obs_id, target_obs_id, relationship)
    #--- Value = (obs_tracker_source_id)

    user_hash_table = loader_db_mirror.user_hash_mirror()
    obs_dna_hash_table = loader_db_mirror.obs_dna_hash_mirror()
    obs_dna_id = loader_db_mirror.obs_dna_id_mirror()
    row_id_table = loader_db_mirror.row_id_mirror()
    seed_id_table = loader_db_mirror.seed_id_mirror()
    plant_id_table = loader_db_mirror.plant_id_mirror()
    tissue_id_table = loader_db_mirror.tissue_id_mirror()
    microbe_id_table = loader_db_mirror.microbe_id_mirror()
    culture_id_table = loader_db_mirror.culture_id_mirror()
    well_id_table = loader_db_mirror.well_id_mirror()
    dna_id_table = loader_db_mirror.dna_id_mirror()
    plate_id_table = loader_db_mirror.plate_id_mirror()
    sample_id_table = loader_db_mirror.sample_id_mirror()
    obs_tracker_hash_table = loader_db_mirror.obs_tracker_hash_mirror()
    obs_tracker_stock_id_table = loader_db_mirror.obs_tracker_stock_id_mirror()
    obs_tracker_obs_sample_id_table = loader_db_mirror.obs_tracker_obs_sample_id_mirror()
    obs_tracker_obs_well_id_table = loader_db_mirror.obs_tracker_obs_well_id_mirror()
    obs_tracker_obs_row_id_table = loader_db_mirror.obs_tracker_obs_row_id_mirror()
    obs_tracker_obs_plant_id_table = loader_db_mirror.obs_tracker_obs_plant_id_mirror()
    obs_tracker_obs_tissue_id_table = loader_db_mirror.obs_tracker_obs_tissue_id_mirror()
    obs_tracker_obs_microbe_id_table = loader_db_mirror.obs_tracker_obs_microbe_id_mirror()
    obs_tracker_obs_culture_id_table = loader_db_mirror.obs_tracker_obs_culture_id_mirror()
    obs_tracker_obs_plate_id_table = loader_db_mirror.obs_tracker_obs_plate_id_mirror()
    obs_tracker_source_hash_table = loader_db_mirror.obs_tracker_source_hash_mirror()
    obs_tracker_id = loader_db_mirror.obs_tracker_id_mirror()
    obs_tracker_source_id = loader_db_mirror.obs_tracker_source_id_mirror()
    experiment_name_table = loader_db_mirror.experiment_name_mirror()

    error_count = 0
    seed_id_error = OrderedDict({})
    row_id_error = OrderedDict({})
    plant_id_error = OrderedDict({})
    tissue_id_error = OrderedDict({})
    microbe_id_error = OrderedDict({})
    culture_id_error = OrderedDict({})
    well_id_error = OrderedDict({})
    plate_id_error = OrderedDict({})
    sample_id_error = OrderedDict({})
    dna_hash_exists = OrderedDict({})
    obs_tracker_hash_exists = OrderedDict({})
    obs_tracker_source_hash_exists = OrderedDict({})

    dna_file = csv.DictReader(codecs.iterdecode(upload_file, 'utf-8'))
    for row in dna_file:
        dna_id = row["DNA ID"]
        experiment_name = row["Experiment Name"]
        extraction = row["Extraction Method"]
        date = row["Date"]
        tube_id = row["Tube ID"]
        tube_type = row["Tube Type"]
        dna_comments = row["DNA Comments"]
        row_id = row["Source Row ID"]
        seed_id = row["Source Seed ID"]
        plant_id = row["Source Plant ID"]
        tissue_id = row["Source Tissue ID"]
        microbe_id = row["Source Microbe ID"]
        well_id = row["Source Well ID"]
        culture_id = row["Source Culture ID"]
        plate_id = row["Source Plate ID"]
        sample_id = row["Source Sample ID"]
        user = user

        if seed_id != '':
            seed_id_fix = seed_id + '\r'
            if seed_id in seed_id_table:
                stock_id = seed_id_table[seed_id][0]
            elif seed_id_fix in seed_id_table:
                stock_id = seed_id_table[seed_id_fix][0]
            else:
                seed_id_error[(dna_id, experiment_name, extraction, date, tube_id, tube_type, dna_comments, row_id, seed_id, plant_id, tissue_id, microbe_id, well_id, culture_id, plate_id)] = error_count
                error_count = error_count + 1
                stock_id = 1
        else:
            stock_id = 1

        if sample_id != '':
            sample_id_fix = sample_id + '\r'
            if sample_id in sample_id_table:
                obs_sample_id = sample_id_table[sample_id][0]
            elif sample_id_fix in sample_id_table:
                obs_sample_id = sample_id_table[sample_id_fix][0]
            else:
                sample_id_error[(dna_id, experiment_name, extraction, date, tube_id, tube_type, dna_comments, row_id, seed_id, plant_id, tissue_id, microbe_id, well_id, culture_id, plate_id)] = error_count
                error_count = error_count + 1
                obs_sample_id = 1
        else:
            obs_sample_id = 1

        if row_id != '':
            row_id_fix = row_id + '\r'
            if row_id in row_id_table:
                obs_row_id = row_id_table[row_id][0]
            elif row_id_fix in row_id_table:
                obs_row_id = row_id_table[row_id_fix][0]
            else:
                row_id_error[(dna_id, experiment_name, extraction, date, tube_id, tube_type, dna_comments, row_id, seed_id, plant_id, tissue_id, microbe_id, well_id, culture_id, plate_id)] = error_count
                error_count = error_count + 1
                obs_row_id = 1
        else:
            obs_row_id = 1

        if plant_id != '':
            plant_id_fix = plant_id + '\r'
            if plant_id in plant_id_table:
                obs_plant_id = plant_id_table[plant_id][0]
            elif plant_id_fix in plant_id_table:
                obs_plant_id = plant_id_table[plant_id_fix][0]
            else:
                plant_id_error[(dna_id, experiment_name, extraction, date, tube_id, tube_type, dna_comments, row_id, seed_id, plant_id, tissue_id, microbe_id, well_id, culture_id, plate_id)] = error_count
                error_count = error_count + 1
                obs_plant_id = 1
        else:
            obs_plant_id = 1

        if tissue_id != '':
            tissue_id_fix = tissue_id + '\r'
            if tissue_id in tissue_id_table:
                obs_tissue_id = tissue_id_table[tissue_id][0]
            elif tissue_id_fix in tissue_id_table:
                obs_tissue_id = tissue_id_table[tissue_id_fix][0]
            else:
                tissue_id_error[(dna_id, experiment_name, extraction, date, tube_id, tube_type, dna_comments, row_id, seed_id, plant_id, tissue_id, microbe_id, well_id, culture_id, plate_id)] = error_count
                error_count = error_count + 1
                obs_tissue_id = 1
        else:
            obs_tissue_id = 1

        if microbe_id != '':
            microbe_id_fix = microbe_id + '\r'
            if microbe_id in microbe_id_table:
                obs_microbe_id = microbe_id_table[microbe_id][0]
            elif microbe_id_fix in microbe_id_table:
                obs_microbe_id = microbe_id_table[microbe_id_fix][0]
            else:
                microbe_id_error[(dna_id, experiment_name, extraction, date, tube_id, tube_type, dna_comments, row_id, seed_id, plant_id, tissue_id, microbe_id, well_id, culture_id, plate_id)] = error_count
                error_count = error_count + 1
                obs_microbe_id = 1
        else:
            obs_microbe_id = 1

        if well_id != '':
            well_id_fix = well_id + '\r'
            if well_id in well_id_table:
                obs_well_id = well_id_table[well_id][0]
            elif well_id_fix in well_id_table:
                obs_well_id = well_id_table[well_id_fix][0]
            else:
                well_id_error[(dna_id, experiment_name, extraction, date, tube_id, tube_type, dna_comments, row_id, seed_id, plant_id, tissue_id, microbe_id, well_id, culture_id, plate_id)] = error_count
                error_count = error_count + 1
                obs_well_id = 1
        else:
            obs_well_id = 1

        if culture_id != '':
            culture_id_fix = culture_id + '\r'
            if culture_id in culture_id_table:
                obs_culture_id = culture_id_table[culture_id][0]
            elif culture_id_fix in culture_id_table:
                obs_culture_id = culture_id_table[culture_id_fix][0]
            else:
                culture_id_error[(dna_id, experiment_name, extraction, date, tube_id, tube_type, dna_comments, row_id, seed_id, plant_id, tissue_id, microbe_id, well_id, culture_id, plate_id)] = error_count
                error_count = error_count + 1
                obs_culture_id = 1
        else:
            obs_culture_id = 1

        if plate_id != '':
            plate_id_fix = plate_id + '\r'
            if plate_id in plate_id_table:
                obs_plate_id = plate_id_table[plate_id][0]
            elif plate_id_fix in plate_id_table:
                obs_plate_id = plate_id_table[plate_id_fix][0]
            else:
                plate_id_error[(dna_id, experiment_name, extraction, date, tube_id, tube_type, dna_comments, row_id, seed_id, plant_id, tissue_id, microbe_id, well_id, culture_id, plate_id)] = error_count
                error_count = error_count + 1
                obs_plate_id = 1
        else:
            obs_plate_id = 1

        dna_hash = dna_id + extraction + date + tube_id + tube_type + dna_comments
        dna_hash_fix = dna_hash + '\r'
        if dna_id not in dna_id_table and dna_id + '\r' not in dna_id_table:
            if dna_hash not in obs_dna_hash_table and dna_hash_fix not in obs_dna_hash_table:
                obs_dna_hash_table[dna_hash] = obs_dna_id
                obs_dna_new[(obs_dna_id, dna_id, extraction, date, tube_id, tube_type, dna_comments)] = obs_dna_id
                dna_id_table[dna_id] = (obs_dna_id, dna_id, extraction, date, tube_id, tube_type, dna_comments)
                obs_dna_id = obs_dna_id + 1
            else:
                dna_hash_exists[(dna_id, extraction, date, tube_id, tube_type, dna_comments)] = obs_dna_id
        else:
            dna_hash_exists[(dna_id, extraction, date, tube_id, tube_type, dna_comments)] = obs_dna_id

        if dna_id in dna_id_table:
            temp_obsdna_id = dna_id_table[dna_id][0]
        elif dna_id + '\r' in dna_id_table:
            temp_obsdna_id = dna_id_table[dna_id + '\r'][0]
        elif dna_hash in obs_dna_hash_table:
            temp_obsdna_id = obs_dna_hash_table[dna_hash]
        elif dna_hash_fix in obs_dna_hash_table:
            temp_obsdna_id = obs_dna_hash_table[dna_hash_fix]
        else:
            temp_obsdna_id = 1
            error_count = error_count + 1

        obs_tracker_dna_hash = 'dna' + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(obs_culture_id) + str(temp_obsdna_id) + str(1) + str(1) + str(obs_microbe_id) + str(obs_plant_id) + str(obs_plate_id) + str(obs_row_id) + str(obs_sample_id) + str(obs_tissue_id) + str(1) + str(stock_id) + str(user_hash_table[user.username])
        obs_tracker_dna_hash_fix = obs_tracker_dna_hash + '\r'
        if obs_tracker_dna_hash not in obs_tracker_hash_table and obs_tracker_dna_hash_fix not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_dna_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'dna', 1, 1, 1, 1, 1, 1, obs_culture_id, temp_obsdna_id, 1, 1, obs_microbe_id, obs_plant_id, obs_plate_id, obs_row_id, obs_sample_id, obs_tissue_id, 1, stock_id, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1
        else:
            obs_tracker_hash_exists[('dna', 1, 1, 1, 1, 1, 1, obs_culture_id, temp_obsdna_id, 1, 1, obs_microbe_id, obs_plant_id, obs_plate_id, obs_row_id, obs_sample_id, obs_tissue_id, 1, stock_id, user_hash_table[user.username])] = obs_tracker_id

        if stock_id != 1:
            obs_tracker_source_stock_hash = str(obs_tracker_stock_id_table[stock_id][0]) + str(obs_tracker_hash_table[obs_tracker_dna_hash]) + 'culture_from_stock'
            if obs_tracker_source_stock_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_stock_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_stock_id_table[stock_id][0], obs_tracker_hash_table[obs_tracker_dna_hash], 'culture_from_stock')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_stock_id_table[stock_id][0], obs_tracker_hash_table[obs_tracker_dna_hash], 'culture_from_stock')] = obs_tracker_source_id

        if obs_row_id != 1:
            obs_tracker_source_row_hash = str(obs_tracker_obs_row_id_table[obs_row_id][0]) + str(obs_tracker_hash_table[obs_tracker_dna_hash]) + 'dna_from_row'
            if obs_tracker_source_row_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_row_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_row_id_table[obs_row_id][0], obs_tracker_hash_table[obs_tracker_dna_hash], 'dna_from_row')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_row_id_table[obs_row_id][0], obs_tracker_hash_table[obs_tracker_dna_hash], 'dna_from_row')] = obs_tracker_source_id

        if obs_plant_id != 1:
            obs_tracker_source_plant_hash = str(obs_tracker_obs_plant_id_table[obs_plant_id][0]) + str(obs_tracker_hash_table[obs_tracker_dna_hash]) + 'dna_from_plant'
            if obs_tracker_source_plant_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_plant_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_plant_id_table[obs_plant_id][0], obs_tracker_hash_table[obs_tracker_dna_hash], 'dna_from_plant')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_plant_id_table[obs_plant_id][0], obs_tracker_hash_table[obs_tracker_dna_hash], 'dna_from_plant')] = obs_tracker_source_id

        if obs_tissue_id != 1:
            obs_tracker_source_tissue_hash = str(obs_tracker_obs_tissue_id_table[obs_tissue_id][0]) + str(obs_tracker_hash_table[obs_tracker_dna_hash]) + 'dna_from_tissue'
            if obs_tracker_source_tissue_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_tissue_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_tissue_id_table[obs_tissue_id][0], obs_tracker_hash_table[obs_tracker_dna_hash], 'dna_from_tissue')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_tissue_id_table[obs_tissue_id][0], obs_tracker_hash_table[obs_tracker_dna_hash], 'dna_from_tissue')] = obs_tracker_source_id

        if obs_microbe_id != 1:
            obs_tracker_source_microbe_hash = str(obs_tracker_obs_microbe_id_table[obs_microbe_id][0]) + str(obs_tracker_hash_table[obs_tracker_dna_hash]) + 'dna_from_microbe'
            if obs_tracker_source_microbe_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_microbe_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_microbe_id_table[obs_microbe_id][0], obs_tracker_hash_table[obs_tracker_dna_hash], 'dna_from_microbe')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_microbe_id_table[obs_microbe_id][0], obs_tracker_hash_table[obs_tracker_dna_hash], 'dna_from_microbe')] = obs_tracker_source_id

        if obs_culture_id != 1:
            obs_tracker_source_culture_hash = str(obs_tracker_obs_culture_id_table[obs_culture_id][0]) + str(obs_tracker_hash_table[obs_tracker_dna_hash]) + 'dna_from_culture'
            if obs_tracker_source_culture_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_culture_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_culture_id_table[obs_culture_id][0], obs_tracker_hash_table[obs_tracker_dna_hash], 'dna_from_culture')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_culture_id_table[obs_culture_id][0], obs_tracker_hash_table[obs_tracker_dna_hash], 'dna_from_culture')] = obs_tracker_source_id

        if obs_sample_id != 1:
            obs_tracker_source_sample_hash = str(obs_tracker_obs_sample_id_table[obs_sample_id][0]) + str(obs_tracker_hash_table[obs_tracker_dna_hash]) + 'dna_from_sample'
            if obs_tracker_source_sample_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_sample_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_sample_id_table[obs_sample_id][0], obs_tracker_hash_table[obs_tracker_dna_hash], 'dna_from_sample')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_sample_id_table[obs_sample_id][0], obs_tracker_hash_table[obs_tracker_dna_hash], 'dna_from_sample')] = obs_tracker_source_id

        if obs_well_id != 1:
            obs_tracker_source_well_hash = str(obs_tracker_obs_well_id_table[obs_well_id][0]) + str(obs_tracker_hash_table[obs_tracker_dna_hash]) + 'dna_in_well'
            if obs_tracker_source_well_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_well_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_well_id_table[obs_well_id][0], obs_tracker_hash_table[obs_tracker_dna_hash], 'dna_in_well')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_well_id_table[obs_well_id][0], obs_tracker_hash_table[obs_tracker_dna_hash], 'dna_in_well')] = obs_tracker_source_id

        if obs_plate_id != 1:
            obs_tracker_source_plate_hash = str(obs_tracker_obs_plate_id_table[obs_plate_id][0]) + str(obs_tracker_hash_table[obs_tracker_dna_hash]) + 'dna_in_plate'
            if obs_tracker_source_plate_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_plate_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_plate_id_table[obs_plate_id][0], obs_tracker_hash_table[obs_tracker_dna_hash], 'dna_in_plate')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_plate_id_table[obs_plate_id][0], obs_tracker_hash_table[obs_tracker_dna_hash], 'dna_in_plate')] = obs_tracker_source_id

        obs_tracker_exp_hash = 'experiment' + str(experiment_name_table[experiment_name][0]) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(user_hash_table[user.username])
        if obs_tracker_exp_hash not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_exp_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'experiment', experiment_name_table[experiment_name][0], 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1

        obs_tracker_source_hash = str(obs_tracker_hash_table[obs_tracker_exp_hash]) + str(obs_tracker_hash_table[obs_tracker_dna_hash]) + 'dna_used_in_experiment'
        if obs_tracker_source_hash not in obs_tracker_source_hash_table:
            obs_tracker_source_hash_table[obs_tracker_source_hash] = obs_tracker_source_id
            obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], obs_tracker_hash_table[obs_tracker_dna_hash], 'dna_used_in_experiment')] = obs_tracker_source_id
            obs_tracker_source_id = obs_tracker_source_id + 1
        else:
            obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], obs_tracker_hash_table[obs_tracker_dna_hash], 'dna_used_in_experiment')] = obs_tracker_source_id

    end = time.clock()
    stats = {}
    stats[("Time: %s" % (end-start), "Errors: %s" % (error_count))] = error_count

    results_dict = {}
    results_dict['obs_dna_new'] = obs_dna_new
    results_dict['obs_tracker_new'] = obs_tracker_new
    results_dict['obs_tracker_source_new'] = obs_tracker_source_new
    results_dict['seed_id_error'] = seed_id_error
    results_dict['row_id_error'] = row_id_error
    results_dict['plant_id_error'] = plant_id_error
    results_dict['tissue_id_error'] = tissue_id_error
    results_dict['microbe_id_error'] = microbe_id_error
    results_dict['culture_id_error'] = culture_id_error
    results_dict['plate_id_error'] = plate_id_error
    results_dict['well_id_error'] = well_id_error
    results_dict['sample_id_error'] = sample_id_error
    results_dict['dna_hash_exists'] = dna_hash_exists
    results_dict['obs_tracker_hash_exists'] = obs_tracker_hash_exists
    results_dict['obs_tracker_source_hash_exists'] = obs_tracker_source_hash_exists
    results_dict['stats'] = stats
    return results_dict

def dna_loader_prep_output(results_dict, new_upload_exp, template_type):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s_%s_prep.csv"' % (new_upload_exp, template_type)
    writer = csv.writer(response)
    writer.writerow(['Stats'])
    writer.writerow([''])
    for key in results_dict['stats'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New DNA Table'])
    writer.writerow(['obs_dna_id', 'dna_id', 'extraction_method', 'date', 'tube_id', 'tube_type', 'comments'])
    for key in results_dict['obs_dna_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTracker Table'])
    writer.writerow(['obs_tracker_id', 'obs_entity_type', 'experiment_id', 'field_id', 'glycerol_stock_id', 'isolate_id', 'location_id', 'maize_sample_id', 'obs_culture_id', 'obs_dna_id', 'obs_env_id', 'obs_extract_id', 'obs_microbe_id', 'obs_plant_id', 'obs_plate_id', 'obs_row_id', 'obs_sample_id', 'obs_tissue_id', 'obs_well_id', 'stock_id', 'user_id'])
    for key in results_dict['obs_tracker_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTrackerSource Table'])
    writer.writerow(['obs_tracker_source_id', 'source_obs_id', 'targe_obs_id', 'relationship'])
    for key in results_dict['obs_tracker_source_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['---------------------------------------------------------------------------------------------------'])
    writer.writerow([''])
    writer.writerow(['Seed ID Errors'])
    writer.writerow(['dna_id', 'experiment_name', 'extraction', 'date', 'tube_id', 'tube_type', 'dna_comments', 'source_row_id', 'source_seed_id', 'source_plant_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_culture_id', 'source_plate_id'])
    for key in results_dict['seed_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Row ID Errors'])
    writer.writerow(['dna_id', 'experiment_name', 'extraction', 'date', 'tube_id', 'tube_type', 'dna_comments', 'source_row_id', 'source_seed_id', 'source_plant_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_culture_id', 'source_plate_id'])
    for key in results_dict['row_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Plant ID Errors'])
    writer.writerow(['dna_id', 'experiment_name', 'extraction', 'date', 'tube_id', 'tube_type', 'dna_comments', 'source_row_id', 'source_seed_id', 'source_plant_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_culture_id', 'source_plate_id'])
    for key in results_dict['plant_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Tissue ID Errors'])
    writer.writerow(['dna_id', 'experiment_name', 'extraction', 'date', 'tube_id', 'tube_type', 'dna_comments', 'source_row_id', 'source_seed_id', 'source_plant_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_culture_id', 'source_plate_id'])
    for key in results_dict['tissue_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Microbe ID Errors'])
    writer.writerow(['dna_id', 'experiment_name', 'extraction', 'date', 'tube_id', 'tube_type', 'dna_comments', 'source_row_id', 'source_seed_id', 'source_plant_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_culture_id', 'source_plate_id'])
    for key in results_dict['microbe_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Culture ID Errors'])
    writer.writerow(['dna_id', 'experiment_name', 'extraction', 'date', 'tube_id', 'tube_type', 'dna_comments', 'source_row_id', 'source_seed_id', 'source_plant_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_culture_id', 'source_plate_id'])
    for key in results_dict['culture_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Plate ID Errors'])
    writer.writerow(['dna_id', 'experiment_name', 'extraction', 'date', 'tube_id', 'tube_type', 'dna_comments', 'source_row_id', 'source_seed_id', 'source_plant_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_culture_id', 'source_plate_id'])
    for key in results_dict['plate_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Well ID Errors'])
    writer.writerow(['dna_id', 'experiment_name', 'extraction', 'date', 'tube_id', 'tube_type', 'dna_comments', 'source_row_id', 'source_seed_id', 'source_plant_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_culture_id', 'source_plate_id'])
    for key in results_dict['well_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Sample ID Errors'])
    writer.writerow(['dna_id', 'experiment_name', 'extraction', 'date', 'tube_id', 'tube_type', 'dna_comments', 'source_row_id', 'source_seed_id', 'source_plant_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_culture_id', 'source_plate_id'])
    for key in results_dict['sample_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['DNA Entry Already Exists'])
    for key in results_dict['dna_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTracker Entry Already Exists'])
    for key in results_dict['obs_tracker_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTrackerSource Entries Already Exist'])
    for key in results_dict['obs_tracker_source_hash_exists'].keys():
        writer.writerow(key)
    return response

def dna_loader(results_dict):
    try:
        for key in results_dict['obs_dna_new'].keys():
            try:
                with transaction.atomic():
                    new_obsdna = ObsDNA.objects.create(id=key[0], dna_id=key[1], extraction_method=key[2], date=key[3], tube_id=key[4], tube_type=key[5], comments=key[6])
            except Exception as e:
                print("ObsDNA Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = ObsTracker.objects.create(id=key[0], obs_entity_type=key[1], experiment_id=key[2], field_id=key[3], glycerol_stock_id=key[4], isolate_id=key[5], location_id=key[6], maize_sample_id=key[7], obs_culture_id=key[8], obs_dna_id=key[9], obs_env_id=key[10], obs_extract_id=key[11], obs_microbe_id=key[12], obs_plant_id=key[13], obs_plate_id=key[14], obs_row_id=key[15], obs_sample_id=key[16], obs_tissue_id=key[17], obs_well_id=key[18], stock_id=key[19], user_id=key[20])
            except Exception as e:
                print("ObsTracker Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_source_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = ObsTrackerSource.objects.create(id=key[0], source_obs_id=key[1], target_obs_id=key[2], relationship=key[3])
            except Exception as e:
                print("ObsTrackerSource Error: %s %s" % (e.message, e.args))
                return False
    except Exception as e:
        print("Error: %s %s" % (e.message, e.args))
        return False
    return True

def microbe_loader_prep(upload_file, user):
    start = time.clock()

    obs_microbe_new = OrderedDict({})
    #--- Key = (obs_microbe_id, microbe_id, microbe_type, comments)
    #--- Value = (obs_microbe_id)
    obs_tracker_new = OrderedDict({})
    #--- Key = (obs_tracker_id, obs_entity_type, experiment_id, field_id, glycerol_stock_id, isolate_id, location_id, maize_sample_id, obs_culture_id, obs_dna_id, obs_env_id, obs_extract_id, obs_microbe_id, obs_plant_id, obs_plate_id, obs_row_id, obs_sample_id, obs_tissue_id, obs_well_id, stock_id, user_id)
    #--- Value = (obs_tracker_id)
    obs_tracker_source_new = OrderedDict({})
    #--- Key = (obs_tracker_source_id, source_obs_id, target_obs_id, relationship)
    #--- Value = (obs_tracker_source_id)

    user_hash_table = loader_db_mirror.user_hash_mirror()
    obs_microbe_hash_table = loader_db_mirror.obs_microbe_hash_mirror()
    obs_microbe_id = loader_db_mirror.obs_microbe_id_mirror()
    row_id_table = loader_db_mirror.row_id_mirror()
    seed_id_table = loader_db_mirror.seed_id_mirror()
    plant_id_table = loader_db_mirror.plant_id_mirror()
    tissue_id_table = loader_db_mirror.tissue_id_mirror()
    microbe_id_table = loader_db_mirror.microbe_id_mirror()
    culture_id_table = loader_db_mirror.culture_id_mirror()
    obs_tracker_hash_table = loader_db_mirror.obs_tracker_hash_mirror()
    obs_tracker_source_hash_table = loader_db_mirror.obs_tracker_source_hash_mirror()
    obs_tracker_id = loader_db_mirror.obs_tracker_id_mirror()
    obs_tracker_source_id = loader_db_mirror.obs_tracker_source_id_mirror()
    obs_tracker_stock_id_table = loader_db_mirror.obs_tracker_stock_id_mirror()
    obs_tracker_obs_row_id_table = loader_db_mirror.obs_tracker_obs_row_id_mirror()
    obs_tracker_obs_plant_id_table = loader_db_mirror.obs_tracker_obs_plant_id_mirror()
    obs_tracker_obs_tissue_id_table = loader_db_mirror.obs_tracker_obs_tissue_id_mirror()
    obs_tracker_obs_culture_id_table = loader_db_mirror.obs_tracker_obs_culture_id_mirror()
    experiment_name_table = loader_db_mirror.experiment_name_mirror()

    error_count = 0
    seed_id_error = OrderedDict({})
    row_id_error = OrderedDict({})
    plant_id_error = OrderedDict({})
    tissue_id_error = OrderedDict({})
    culture_id_error = OrderedDict({})
    microbe_hash_exists = OrderedDict({})
    obs_tracker_hash_exists = OrderedDict({})
    obs_tracker_source_hash_exists = OrderedDict({})

    microbe_file = csv.DictReader(codecs.iterdecode(upload_file, 'utf-8'))
    for row in microbe_file:
        microbe_id = row["Microbe ID"]
        experiment_name = row["Experiment Name"]
        microbe_type = row["Microbe Type"]
        microbe_comments = row["Microbe Comments"]
        row_id = row["Source Row ID"]
        seed_id = row["Source Seed ID"]
        plant_id = row["Source Plant ID"]
        tissue_id = row["Source Tissue ID"]
        culture_id = row["Source Culture ID"]
        user = user

        if seed_id != '':
            seed_id_fix = seed_id + '\r'
            if seed_id in seed_id_table:
                stock_id = seed_id_table[seed_id][0]
            elif seed_id_fix in seed_id_table:
                stock_id = seed_id_table[seed_id_fix][0]
            else:
                seed_id_error[(microbe_id, experiment_name, microbe_type, microbe_comments, row_id, seed_id, plant_id, tissue_id, culture_id)] = error_count
                error_count = error_count + 1
                stock_id = 1
        else:
            stock_id = 1

        if row_id != '':
            row_id_fix = row_id + '\r'
            if row_id in row_id_table:
                obs_row_id = row_id_table[row_id][0]
            elif row_id_fix in row_id_table:
                obs_row_id = row_id_table[row_id_fix][0]
            else:
                row_id_error[(microbe_id, experiment_name, microbe_type, microbe_comments, row_id, seed_id, plant_id, tissue_id, culture_id)] = error_count
                error_count = error_count + 1
                obs_row_id = 1
        else:
            obs_row_id = 1

        if plant_id != '':
            plant_id_fix = plant_id + '\r'
            if plant_id in plant_id_table:
                obs_plant_id = plant_id_table[plant_id][0]
            elif plant_id_fix in plant_id_table:
                obs_plant_id = plant_id_table[plant_id_fix][0]
            else:
                plant_id_error[(microbe_id, experiment_name, microbe_type, microbe_comments, row_id, seed_id, plant_id, tissue_id, culture_id)] = error_count
                error_count = error_count + 1
                obs_plant_id = 1
        else:
            obs_plant_id = 1

        if tissue_id != '':
            tissue_id_fix = tissue_id + '\r'
            if tissue_id in tissue_id_table:
                obs_tissue_id = tissue_id_table[tissue_id][0]
            elif tissue_id_fix in tissue_id_table:
                obs_tissue_id = tissue_id_table[tissue_id_fix][0]
            else:
                tissue_id_error[(microbe_id, experiment_name, microbe_type, microbe_comments, row_id, seed_id, plant_id, tissue_id, culture_id)] = error_count
                error_count = error_count + 1
                obs_tissue_id = 1
        else:
            obs_tissue_id = 1

        if culture_id != '':
            culture_id_fix = culture_id + '\r'
            if culture_id in culture_id_table:
                obs_culture_id = culture_id_table[culture_id][0]
            elif culture_id_fix in culture_id_table:
                obs_culture_id = culture_id_table[culture_id_fix][0]
            else:
                culture_id_error[(microbe_id, experiment_name, microbe_type, microbe_comments, row_id, seed_id, plant_id, tissue_id, culture_id)] = error_count
                error_count = error_count + 1
                obs_culture_id = 1
        else:
            obs_culture_id = 1

        microbe_hash = microbe_id + microbe_type + microbe_comments
        microbe_hash_fix = microbe_hash + '\r'
        if microbe_id not in microbe_id_table and microbe_id + '\r' not in microbe_id_table:
            if microbe_hash not in obs_microbe_hash_table and microbe_hash_fix not in obs_microbe_hash_table:
                obs_microbe_hash_table[microbe_hash] = obs_microbe_id
                obs_microbe_new[(obs_microbe_id, microbe_id, microbe_type, microbe_comments)] = obs_microbe_id
                microbe_id_table[microbe_id] = (obs_microbe_id, microbe_id, microbe_type, microbe_comments)
                obs_microbe_id = obs_microbe_id + 1
            else:
                microbe_hash_exists[(medium_id, culture_id, culture_name, microbe_type, plating_cycle, dilution, image_filename, tissue_comments, num_colonies, num_microbes)] = obs_microbe_id
        else:
            microbe_hash_exists[(medium_id, culture_id, culture_name, microbe_type, plating_cycle, dilution, image_filename, tissue_comments, num_colonies, num_microbes)] = obs_microbe_id

        if microbe_id in microbe_id_table:
            temp_obsmicrobe_id = microbe_id_table[microbe_id][0]
        elif microbe_id + '\r' in microbe_id_table:
            temp_obsmicrobe_id = microbe_id_table[microbe_id + '\r'][0]
        elif microbe_hash in obs_microbe_hash_table:
            temp_obsmicrobe_id = obs_microbe_hash_table[microbe_hash]
        elif microbe_hash_fix in obs_microbe_hash_table:
            temp_obsmicrobe_id = obs_microbe_hash_table[microbe_hash_fix]
        else:
            temp_obsmicrobe_id = 1
            error_count = error_count + 1

        obs_tracker_microbe_hash = 'microbe' + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(obs_culture_id) + str(1) + str(1) + str(1) + str(temp_obsmicrobe_id) + str(obs_plant_id) + str(1) + str(obs_row_id) + str(1) + str(obs_tissue_id) + str(1) + str(stock_id) + str(user_hash_table[user.username])
        obs_tracker_microbe_hash_fix = obs_tracker_microbe_hash + '\r'
        if obs_tracker_microbe_hash not in obs_tracker_hash_table and obs_tracker_microbe_hash_fix not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_microbe_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'microbe', 1, 1, 1, 1, 1, 1, obs_culture_id, 1, 1, 1, temp_obsmicrobe_id, obs_plant_id, 1, obs_row_id, 1, obs_tissue_id, 1, stock_id, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1
        else:
            obs_tracker_hash_exists[('microbe', 1, 1, 1, 1, 1, 1, obs_culture_id, 1, 1, 1, temp_obsmicrobe_id, obs_plant_id, 1, obs_row_id, 1, obs_tissue_id, 1, stock_id, user_hash_table[user.username])] = obs_tracker_id

        if stock_id != 1:
            obs_tracker_source_stock_hash = str(obs_tracker_stock_id_table[stock_id][0]) + str(obs_tracker_hash_table[obs_tracker_microbe_hash]) + 'microbe_from_stock'
            if obs_tracker_source_stock_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_stock_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_stock_id_table[stock_id][0], obs_tracker_hash_table[obs_tracker_microbe_hash], 'microbe_from_stock')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_stock_id_table[stock_id][0], obs_tracker_hash_table[obs_tracker_microbe_hash], 'microbe_from_stock')] = obs_tracker_source_id

        if obs_row_id != 1:
            obs_tracker_source_row_hash = str(obs_tracker_obs_row_id_table[obs_row_id][0]) + str(obs_tracker_hash_table[obs_tracker_microbe_hash]) + 'microbe_from_row'
            if obs_tracker_source_row_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_row_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_row_id_table[obs_row_id][0], obs_tracker_hash_table[obs_tracker_microbe_hash], 'microbe_from_row')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_row_id_table[obs_row_id][0], obs_tracker_hash_table[obs_tracker_microbe_hash], 'microbe_from_row')] = obs_tracker_source_id

        if obs_plant_id != 1:
            obs_tracker_source_plant_hash = str(obs_tracker_obs_plant_id_table[obs_plant_id][0]) + str(obs_tracker_hash_table[obs_tracker_microbe_hash]) + 'microbe_from_plant'
            if obs_tracker_source_plant_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_plant_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_plant_id_table[obs_plant_id][0], obs_tracker_hash_table[obs_tracker_microbe_hash], 'microbe_from_plant')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_plant_id_table[obs_plant_id][0], obs_tracker_hash_table[obs_tracker_microbe_hash], 'microbe_from_plant')] = obs_tracker_source_id

        if obs_tissue_id != 1:
            obs_tracker_source_tissue_hash = str(obs_tracker_obs_tissue_id_table[obs_tissue_id][0]) + str(obs_tracker_hash_table[obs_tracker_microbe_hash]) + 'microbe_from_tissue'
            if obs_tracker_source_tissue_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_tissue_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_tissue_id_table[obs_tissue_id][0], obs_tracker_hash_table[obs_tracker_microbe_hash], 'microbe_from_tissue')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_tissue_id_table[obs_tissue_id][0], obs_tracker_hash_table[obs_tracker_microbe_hash], 'microbe_from_tissue')] = obs_tracker_source_id

        if obs_culture_id != 1:
            obs_tracker_source_culture_hash = str(obs_tracker_obs_culture_id_table[obs_culture_id][0]) + str(obs_tracker_hash_table[obs_tracker_microbe_hash]) + 'microbe_from_culture'
            if obs_tracker_source_culture_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_culture_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_culture_id_table[obs_culture_id][0], obs_tracker_hash_table[obs_tracker_microbe_hash], 'microbe_from_culture')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_culture_id_table[obs_culture_id][0], obs_tracker_hash_table[obs_tracker_microbe_hash], 'microbe_from_culture')] = obs_tracker_source_id

        obs_tracker_exp_hash = 'experiment' + str(experiment_name_table[experiment_name][0]) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(user_hash_table[user.username])
        if obs_tracker_exp_hash not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_exp_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'experiment', experiment_name_table[experiment_name][0], 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1

        obs_tracker_source_hash = str(obs_tracker_hash_table[obs_tracker_exp_hash]) + str(obs_tracker_hash_table[obs_tracker_microbe_hash]) + 'microbe_used_in_experiment'
        if obs_tracker_source_hash not in obs_tracker_source_hash_table:
            obs_tracker_source_hash_table[obs_tracker_source_hash] = obs_tracker_source_id
            obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], obs_tracker_hash_table[obs_tracker_microbe_hash], 'microbe_used_in_experiment')] = obs_tracker_source_id
            obs_tracker_source_id = obs_tracker_source_id + 1
        else:
            obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], obs_tracker_hash_table[obs_tracker_microbe_hash], 'microbe_used_in_experiment')] = obs_tracker_source_id

    end = time.clock()
    stats = {}
    stats[("Time: %s" % (end-start), "Errors: %s" % (error_count))] = error_count

    results_dict = {}
    results_dict['obs_microbe_new'] = obs_microbe_new
    results_dict['obs_tracker_new'] = obs_tracker_new
    results_dict['obs_tracker_source_new'] = obs_tracker_source_new
    results_dict['seed_id_error'] = seed_id_error
    results_dict['row_id_error'] = row_id_error
    results_dict['plant_id_error'] = plant_id_error
    results_dict['tissue_id_error'] = tissue_id_error
    results_dict['culture_id_error'] = culture_id_error
    results_dict['microbe_hash_exists'] = microbe_hash_exists
    results_dict['obs_tracker_hash_exists'] = obs_tracker_hash_exists
    results_dict['obs_tracker_source_hash_exists'] = obs_tracker_source_hash_exists
    results_dict['stats'] = stats
    return results_dict

def microbe_loader_prep_output(results_dict, new_upload_exp, template_type):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s_%s_prep.csv"' % (new_upload_exp, template_type)
    writer = csv.writer(response)
    writer.writerow(['Stats'])
    writer.writerow([''])
    for key in results_dict['stats'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Microbe Table'])
    writer.writerow(['obs_microbe_id', 'microbe_id', 'microbe_type', 'comments'])
    for key in results_dict['obs_microbe_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTracker Table'])
    writer.writerow(['obs_tracker_id', 'obs_entity_type', 'experiment_id', 'field_id', 'glycerol_stock_id', 'isolate_id', 'location_id', 'maize_sample_id', 'obs_culture_id', 'obs_dna_id', 'obs_env_id', 'obs_extract_id', 'obs_microbe_id', 'obs_plant_id', 'obs_plate_id', 'obs_row_id', 'obs_sample_id', 'obs_tissue_id', 'obs_well_id', 'stock_id', 'user_id'])
    for key in results_dict['obs_tracker_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTrackerSource Table'])
    writer.writerow(['obs_tracker_source_id', 'source_obs_id', 'targe_obs_id', 'relationship'])
    for key in results_dict['obs_tracker_source_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['---------------------------------------------------------------------------------------------------'])
    writer.writerow([''])
    writer.writerow(['Seed ID Errors'])
    writer.writerow(['microbe_id', 'experiment_name', 'microbe_type', 'microbe_comments','source_row_id', 'source_seed_id', 'source_plant_id', 'source_tissue_id', 'source_culture_id'])
    for key in results_dict['seed_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Row ID Errors'])
    writer.writerow(['microbe_id', 'experiment_name', 'microbe_type', 'microbe_comments','source_row_id', 'source_seed_id', 'source_plant_id', 'source_tissue_id', 'source_culture_id'])
    for key in results_dict['row_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Plant ID Errors'])
    writer.writerow(['microbe_id', 'experiment_name', 'microbe_type', 'microbe_comments','source_row_id', 'source_seed_id', 'source_plant_id', 'source_tissue_id', 'source_culture_id'])
    for key in results_dict['plant_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Tissue ID Errors'])
    writer.writerow(['microbe_id', 'experiment_name', 'microbe_type', 'microbe_comments','source_row_id', 'source_seed_id', 'source_plant_id', 'source_tissue_id', 'source_culture_id'])
    for key in results_dict['tissue_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Culture ID Errors'])
    writer.writerow(['microbe_id', 'experiment_name', 'microbe_type', 'microbe_comments','source_row_id', 'source_seed_id', 'source_plant_id', 'source_tissue_id', 'source_culture_id'])
    for key in results_dict['culture_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Microbe Entry Already Exists'])
    for key in results_dict['microbe_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTracker Entry Already Exists'])
    for key in results_dict['obs_tracker_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTrackerSource Entries Already Exist'])
    for key in results_dict['obs_tracker_source_hash_exists'].keys():
        writer.writerow(key)
    return response

def microbe_loader(results_dict):
    try:
        for key in results_dict['obs_microbe_new'].keys():
            try:
                with transaction.atomic():
                    new_obsmicrobe = ObsMicrobe.objects.create(id=key[0], microbe_id=key[1], microbe_type=key[2], comments=key[3])
            except Exception as e:
                print("ObsMicrobe Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = ObsTracker.objects.create(id=key[0], obs_entity_type=key[1], experiment_id=key[2], field_id=key[3], glycerol_stock_id=key[4], isolate_id=key[5], location_id=key[6], maize_sample_id=key[7], obs_culture_id=key[8], obs_dna_id=key[9], obs_env_id=key[10], obs_extract_id=key[11], obs_microbe_id=key[12], obs_plant_id=key[13], obs_plate_id=key[14], obs_row_id=key[15], obs_sample_id=key[16], obs_tissue_id=key[17], obs_well_id=key[18], stock_id=key[19], user_id=key[20])
            except Exception as e:
                print("ObsTracker Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_source_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = ObsTrackerSource.objects.create(id=key[0], source_obs_id=key[1], target_obs_id=key[2], relationship=key[3])
            except Exception as e:
                print("ObsTrackerSource Error: %s %s" % (e.message, e.args))
                return False
    except Exception as e:
        print("Error: %s %s" % (e.message, e.args))
        return False
    return True

def plate_loader_prep(upload_file, user):
    start = time.clock()

    obs_plate_new = OrderedDict({})
    #--- Key = (obs_plate_id, plate_id, plate_name, date, contents, rep, plate_type, plate_status, comments)
    #--- Value = (obs_plate_id)
    obs_tracker_new = OrderedDict({})
    #--- Key = (obs_tracker_id, obs_entity_type, experiment_id, field_id, glycerol_stock_id, isolate_id, location_id, maize_sample_id, obs_culture_id, obs_dna_id, obs_env_id, obs_extract_id, obs_microbe_id, obs_plant_id, obs_plate_id, obs_row_id, obs_sample_id, obs_tissue_id, obs_well_id, stock_id, user_id)
    #--- Value = (obs_tracker_id)
    obs_tracker_source_new = OrderedDict({})

    user_hash_table = loader_db_mirror.user_hash_mirror()
    obs_plate_hash_table = loader_db_mirror.obs_plate_hash_mirror()
    obs_plate_id = loader_db_mirror.obs_plate_id_mirror()
    plate_id_table = loader_db_mirror.plate_id_mirror()
    location_name_table = loader_db_mirror.location_name_mirror()
    obs_tracker_hash_table = loader_db_mirror.obs_tracker_hash_mirror()
    obs_tracker_source_hash_table = loader_db_mirror.obs_tracker_source_hash_mirror()
    obs_tracker_id = loader_db_mirror.obs_tracker_id_mirror()
    obs_tracker_source_id = loader_db_mirror.obs_tracker_source_id_mirror()
    experiment_name_table = loader_db_mirror.experiment_name_mirror()

    error_count = 0
    location_name_error = OrderedDict({})
    plate_hash_exists = OrderedDict({})
    obs_tracker_hash_exists = OrderedDict({})
    obs_tracker_source_hash_exists = OrderedDict({})

    plate_file = csv.DictReader(codecs.iterdecode(upload_file, 'utf-8'))
    for row in plate_file:
        plate_id = row["Plate ID"]
        experiment_name = row["Experiment Name"]
        location_name = row["Location Name"]
        plate_name = row["Plate Name"]
        date = row["Date Plated"]
        contents = row["Plate Contents"]
        rep = row["Plate Rep"]
        plate_type = row["Plate Type"]
        plate_status = row["Plate Status"]
        plate_comments = row["Plate Comments"]
        user = user

        if location_name != '':
            location_name_fix = location_name + '\r'
            if location_name in location_name_table:
                location_id = location_name_table[location_name][0]
            elif location_name_fix in location_name_table:
                location_id = location_name_table[location_name_fix][0]
            else:
                location_name_error[(plate_id, experiment_name, location_name, plate_name, date, contents, rep, plate_type, plate_status, plate_comments)] = error_count
                error_count = error_count + 1
                location_id = 1
        else:
            location_id = 1

        plate_hash = plate_id + plate_name + date + contents + rep + plate_type + plate_status + plate_comments
        plate_hash_fix = plate_hash + '\r'
        if plate_id not in plate_id_table and plate_id + '\r' not in plate_id_table:
            if plate_hash not in obs_plate_hash_table and plate_hash_fix not in obs_plate_hash_table:
                obs_plate_hash_table[plate_hash] = obs_plate_id
                obs_plate_new[(obs_plate_id, plate_id, plate_name, date, contents, rep, plate_type, plate_status, plate_comments)] = obs_plate_id
                plate_id_table[plate_id] = (obs_plate_id, plate_id, plate_name, date, contents, rep, plate_type, plate_status, plate_comments)
                obs_plate_id = obs_plate_id + 1
            else:
                plate_hash_exists[(plate_id, plate_name, date, contents, rep, plate_type, plate_status, plate_comments)] = obs_plate_id
        else:
            plate_hash_exists[(plate_id, plate_name, date, contents, rep, plate_type, plate_status, plate_comments)] = obs_plate_id

        if plate_id in plate_id_table:
            temp_obsplate_id = plate_id_table[plate_id][0]
        elif plate_id + '\r' in plate_id_table:
            temp_obsplate_id = plate_id_table[plate_id + '\r'][0]
        elif plate_hash in obs_plate_hash_table:
            temp_obsplate_id = obs_plate_hash_table[plate_hash]
        elif plate_hash_fix in obs_plate_hash_table:
            temp_obsplate_id = obs_plate_hash_table[plate_hash_fix]
        else:
            temp_obsplate_id = 1
            error_count = error_count + 1

        obs_tracker_plate_hash = 'plate' + str(1) + str(1) + str(1) + str(1) + str(location_id) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(temp_obsplate_id) + str(1) + str(1) + str(1) + str(1) + str(1) + str(user_hash_table[user.username])
        obs_tracker_plate_hash_fix = obs_tracker_plate_hash + '\r'
        if obs_tracker_plate_hash not in obs_tracker_hash_table and obs_tracker_plate_hash_fix not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_plate_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'plate', 1, 1, 1, 1, location_id, 1, 1, 1, 1, 1, 1, 1, temp_obsplate_id, 1, 1, 1, 1, 1, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1
        else:
            obs_tracker_hash_exists[('plate', 1, 1, 1, 1, location_id, 1, 1, 1, 1, 1, 1, 1, temp_obsplate_id, 1, 1, 1, 1, 1, user_hash_table[user.username])] = obs_tracker_id

        obs_tracker_exp_hash = 'experiment' + str(experiment_name_table[experiment_name][0]) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(user_hash_table[user.username])
        if obs_tracker_exp_hash not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_exp_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'experiment', experiment_name_table[experiment_name][0], 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1

        obs_tracker_source_hash = str(obs_tracker_hash_table[obs_tracker_exp_hash]) + str(obs_tracker_hash_table[obs_tracker_plate_hash]) + 'plate_used_in_experiment'
        if obs_tracker_source_hash not in obs_tracker_source_hash_table:
            obs_tracker_source_hash_table[obs_tracker_source_hash] = obs_tracker_source_id
            obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], obs_tracker_hash_table[obs_tracker_plate_hash], 'plate_used_in_experiment')] = obs_tracker_source_id
            obs_tracker_source_id = obs_tracker_source_id + 1
        else:
            obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], obs_tracker_hash_table[obs_tracker_plate_hash], 'plate_used_in_experiment')] = obs_tracker_source_id

    end = time.clock()
    stats = {}
    stats[("Time: %s" % (end-start), "Errors: %s" % (error_count))] = error_count

    results_dict = {}
    results_dict['obs_plate_new'] = obs_plate_new
    results_dict['obs_tracker_new'] = obs_tracker_new
    results_dict['obs_tracker_source_new'] = obs_tracker_source_new
    results_dict['location_name_error'] = location_name_error
    results_dict['plate_hash_exists'] = plate_hash_exists
    results_dict['obs_tracker_hash_exists'] = obs_tracker_hash_exists
    results_dict['obs_tracker_source_hash_exists'] = obs_tracker_source_hash_exists
    results_dict['stats'] = stats
    return results_dict

def plate_loader_prep_output(results_dict, new_upload_exp, template_type):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s_%s_prep.csv"' % (new_upload_exp, template_type)
    writer = csv.writer(response)
    writer.writerow(['Stats'])
    writer.writerow([''])
    for key in results_dict['stats'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Plate Table'])
    writer.writerow(['obs_plate_id', 'plate_id', 'plate_name', 'date', 'contents', 'rep', 'plate_type', 'plate_status', 'comments'])
    for key in results_dict['obs_plate_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTracker Table'])
    writer.writerow(['obs_tracker_id', 'obs_entity_type', 'experiment_id', 'field_id', 'glycerol_stock_id', 'isolate_id', 'location_id', 'maize_sample_id', 'obs_culture_id', 'obs_dna_id', 'obs_env_id', 'obs_extract_id', 'obs_microbe_id', 'obs_plant_id', 'obs_plate_id', 'obs_row_id', 'obs_sample_id', 'obs_tissue_id', 'obs_well_id', 'stock_id', 'user_id'])
    for key in results_dict['obs_tracker_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTrackerSource Table'])
    writer.writerow(['obs_tracker_source_id', 'source_obs_id', 'targe_obs_id', 'relationship'])
    for key in results_dict['obs_tracker_source_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['---------------------------------------------------------------------------------------------------'])
    writer.writerow([''])
    writer.writerow(['Location Name Errors'])
    writer.writerow(['plate_id', 'experiment_name', 'location_name', 'plate_name', 'date', 'contents', 'rep', 'plate_type', 'plate_status', 'plate_comments'])
    for key in results_dict['location_name_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Plate Entry Already Exists'])
    for key in results_dict['plate_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTracker Entry Already Exists'])
    for key in results_dict['obs_tracker_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTrackerSource Entry Already Exists'])
    for key in results_dict['obs_tracker_source_hash_exists'].keys():
        writer.writerow(key)
    return response

def plate_loader(results_dict):
    try:
        for key in results_dict['obs_plate_new'].keys():
            try:
                with transaction.atomic():
                    new_obsplate = ObsPlate.objects.create(id=key[0], plate_id=key[1], plate_name=key[2], date=key[3], contents=key[4], rep=key[5], plate_type=key[6], plate_status=key[7], comments=key[8])
            except Exception as e:
                print("ObsPlate Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = ObsTracker.objects.create(id=key[0], obs_entity_type=key[1], experiment_id=key[2], field_id=key[3], glycerol_stock_id=key[4], isolate_id=key[5], location_id=key[6], maize_sample_id=key[7], obs_culture_id=key[8], obs_dna_id=key[9], obs_env_id=key[10], obs_extract_id=key[11], obs_microbe_id=key[12], obs_plant_id=key[13], obs_plate_id=key[14], obs_row_id=key[15], obs_sample_id=key[16], obs_tissue_id=key[17], obs_well_id=key[18], stock_id=key[19], user_id=key[20])
            except Exception as e:
                print("ObsTracker Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_source_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = ObsTrackerSource.objects.create(id=key[0], source_obs_id=key[1], target_obs_id=key[2], relationship=key[3])
            except Exception as e:
                print("ObsTrackerSource Error: %s %s" % (e.message, e.args))
                return False
    except Exception as e:
        print("Error: %s %s" % (e.message, e.args))
        return False
    return True

def env_loader_prep(upload_file, user):
    start = time.clock()

    obs_env_new = OrderedDict({})
    #--- Key = (obs_env_id, environment_id, longitude, latitude, comments)
    #--- Value = (obs_env_id)
    obs_tracker_new = OrderedDict({})
    #--- Key = (obs_tracker_id, obs_entity_type, experiment_id, field_id, glycerol_stock_id, isolate_id, location_id, maize_sample_id, obs_culture_id, obs_dna_id, obs_env_id, obs_extract_id, obs_microbe_id, obs_plant_id, obs_plate_id, obs_row_id, obs_sample_id, obs_tissue_id, obs_well_id, stock_id, user_id)
    #--- Value = (obs_tracker_id)
    obs_tracker_source_new = OrderedDict({})

    user_hash_table = loader_db_mirror.user_hash_mirror()
    obs_env_hash_table = loader_db_mirror.obs_env_hash_mirror()
    obs_env_id = loader_db_mirror.obs_env_id_mirror()
    field_name_table = loader_db_mirror.field_name_mirror()
    env_id_table = loader_db_mirror.env_id_mirror()
    obs_tracker_hash_table = loader_db_mirror.obs_tracker_hash_mirror()
    obs_tracker_source_hash_table = loader_db_mirror.obs_tracker_source_hash_mirror()
    obs_tracker_id = loader_db_mirror.obs_tracker_id_mirror()
    obs_tracker_source_id = loader_db_mirror.obs_tracker_source_id_mirror()
    experiment_name_table = loader_db_mirror.experiment_name_mirror()

    error_count = 0
    field_name_error = OrderedDict({})
    env_hash_exists = OrderedDict({})
    obs_tracker_hash_exists = OrderedDict({})
    obs_tracker_source_hash_exists = OrderedDict({})

    env_file = csv.DictReader(codecs.iterdecode(upload_file, 'utf-8'))
    for row in env_file:
        environment_id = row["Environment ID"]
        experiment_name = row["Experiment Name"]
        field_name = row["Field Name"]
        longitude = row["Longitude"]
        latitude = row["Latitude"]
        env_comments = row["Environment Comments"]
        user = user

        if field_name != '':
            field_name_fix = field_name + '\r'
            if field_name in field_name_table:
                field_id = field_name_table[field_name][0]
            elif field_name_fix in field_name_table:
                field_id = field_name_table[field_name_fix][0]
            else:
                field_name_error[(environment_id, experiment_name, field_name, longitude, latitude, env_comments)] = error_count
                error_count = error_count + 1
                field_id = 1
        else:
            field_id = 1

        env_hash = environment_id + longitude + latitude + env_comments
        env_hash_fix = env_hash + '\r'
        if environment_id not in env_id_table and environment_id + '\r' not in env_id_table:
            if env_hash not in obs_env_hash_table and env_hash_fix not in obs_env_hash_table:
                obs_env_hash_table[env_hash] = obs_env_id
                obs_env_new[(obs_env_id, environment_id, longitude, latitude, env_comments)] = obs_env_id
                env_id_table[environment_id] = (obs_env_id, environment_id, longitude, latitude, env_comments)
                obs_env_id = obs_env_id + 1
            else:
                env_hash_exists[(environment_id, longitude, latitude, env_comments)] = obs_env_id
        else:
            env_hash_exists[(environment_id, longitude, latitude, env_comments)] = obs_env_id

        if environment_id in env_id_table:
            temp_obsenv_id = env_id_table[environment_id][0]
        elif environment_id + '\r' in env_id_table:
            temp_obsenv_id = env_id_table[environment_id + '\r'][0]
        elif env_hash in obs_env_hash_table:
            temp_obsenv_id = obs_env_hash_table[env_hash]
        elif env_hash_fix in obs_env_hash_table:
            temp_obsenv_id = obs_env_hash_table[env_hash_fix]
        else:
            temp_obsenv_id = 1
            error_count = error_count + 1

        obs_tracker_env_hash = 'environment' + str(1) + str(field_id) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(temp_obsenv_id) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(user_hash_table[user.username])
        obs_tracker_env_hash_fix = obs_tracker_env_hash + '\r'
        if obs_tracker_env_hash not in obs_tracker_hash_table and obs_tracker_env_hash_fix not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_env_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'environment', 1, field_id, 1, 1, 1, 1, 1, 1, temp_obsenv_id, 1, 1, 1, 1, 1, 1, 1, 1, 1, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1
        else:
            obs_tracker_hash_exists[('environment', 1, field_id, 1, 1, 1, 1, 1, 1, temp_obsenv_id, 1, 1, 1, 1, 1, 1, 1, 1, 1, user_hash_table[user.username])] = obs_tracker_id

        obs_tracker_exp_hash = 'experiment' + str(experiment_name_table[experiment_name][0]) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(user_hash_table[user.username])
        if obs_tracker_exp_hash not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_exp_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'experiment', experiment_name_table[experiment_name][0], 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1

        obs_tracker_source_hash = str(obs_tracker_hash_table[obs_tracker_exp_hash]) + str(obs_tracker_hash_table[obs_tracker_env_hash]) + 'env_used_in_experiment'
        if obs_tracker_source_hash not in obs_tracker_source_hash_table:
            obs_tracker_source_hash_table[obs_tracker_source_hash] = obs_tracker_source_id
            obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], obs_tracker_hash_table[obs_tracker_env_hash], 'env_used_in_experiment')] = obs_tracker_source_id
            obs_tracker_source_id = obs_tracker_source_id + 1
        else:
            obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], obs_tracker_hash_table[obs_tracker_env_hash], 'env_used_in_experiment')] = obs_tracker_source_id

    end = time.clock()
    stats = {}
    stats[("Time: %s" % (end-start), "Errors: %s" % (error_count))] = error_count

    results_dict = {}
    results_dict['obs_env_new'] = obs_env_new
    results_dict['obs_tracker_new'] = obs_tracker_new
    results_dict['obs_tracker_source_new'] = obs_tracker_source_new
    results_dict['field_name_error'] = field_name_error
    results_dict['env_hash_exists'] = env_hash_exists
    results_dict['obs_tracker_hash_exists'] = obs_tracker_hash_exists
    results_dict['obs_tracker_source_hash_exists'] = obs_tracker_source_hash_exists
    results_dict['stats'] = stats
    return results_dict

def env_loader_prep_output(results_dict, new_upload_exp, template_type):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s_%s_prep.csv"' % (new_upload_exp, template_type)
    writer = csv.writer(response)
    writer.writerow(['Stats'])
    writer.writerow([''])
    for key in results_dict['stats'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Environment Table'])
    writer.writerow(['obs_env_id', 'environment_id', 'longitude', 'latitude', 'comments'])
    for key in results_dict['obs_env_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTracker Table'])
    writer.writerow(['obs_tracker_id', 'obs_entity_type', 'experiment_id', 'field_id', 'glycerol_stock_id', 'isolate_id', 'location_id', 'maize_sample_id', 'obs_culture_id', 'obs_dna_id', 'obs_env_id', 'obs_extract_id', 'obs_microbe_id', 'obs_plant_id', 'obs_plate_id', 'obs_row_id', 'obs_sample_id', 'obs_tissue_id', 'obs_well_id', 'stock_id', 'user_id'])
    for key in results_dict['obs_tracker_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTrackerSource Table'])
    writer.writerow(['obs_tracker_id', 'source_obs_id', 'target_obs_id', 'relationship'])
    for key in results_dict['obs_tracker_source_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['---------------------------------------------------------------------------------------------------'])
    writer.writerow([''])
    writer.writerow(['Field Name Errors'])
    writer.writerow(['environment_id', 'experiment_name', 'field_name', 'longitude', 'latitude', 'env_comments'])
    for key in results_dict['field_name_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Environment Entry Already Exists'])
    for key in results_dict['env_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTracker Entry Already Exists'])
    for key in results_dict['obs_tracker_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTrackerSource Entry Already Exists'])
    for key in results_dict['obs_tracker_source_hash_exists'].keys():
        writer.writerow(key)
    return response

def env_loader(results_dict):
    try:
        for key in results_dict['obs_env_new'].keys():
            try:
                with transaction.atomic():
                    new_obsenv = ObsEnv.objects.create(id=key[0], environment_id=key[1], longitude=key[2], latitude=key[3], comments=key[4])
            except Exception as e:
                print("ObsEnv Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = ObsTracker.objects.create(id=key[0], obs_entity_type=key[1], experiment_id=key[2], field_id=key[3], glycerol_stock_id=key[4], isolate_id=key[5], location_id=key[6], maize_sample_id=key[7], obs_culture_id=key[8], obs_dna_id=key[9], obs_env_id=key[10], obs_extract_id=key[11], obs_microbe_id=key[12], obs_plant_id=key[13], obs_plate_id=key[14], obs_row_id=key[15], obs_sample_id=key[16], obs_tissue_id=key[17], obs_well_id=key[18], stock_id=key[19], user_id=key[20])
            except Exception as e:
                print("ObsTracker Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_source_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = ObsTrackerSource.objects.create(id=key[0], source_obs_id=key[1], target_obs_id=key[2], relationship=key[3])
            except Exception as e:
                print("ObsTrackerSource Error: %s %s" % (e.message, e.args))
                return False
    except Exception as e:
        print("Error: %s %s" % (e.message, e.args))
        return False
    return True

def well_loader_prep(upload_file, user):
    start = time.clock()

    obs_well_new = OrderedDict({})
    #--- Key = (obs_well_id, well_id, well, well_inventory, tube_label, comments)
    #--- Value = (obs_well_id)
    obs_tracker_new = OrderedDict({})
    #--- Key = (obs_tracker_id, obs_entity_type, experiment_id, field_id, glycerol_stock_id, isolate_id, location_id, maize_sample_id, obs_culture_id, obs_dna_id, obs_env_id, obs_extract_id, obs_microbe_id, obs_plant_id, obs_plate_id, obs_row_id, obs_sample_id, obs_tissue_id, obs_well_id, stock_id, user_id)
    #--- Value = (obs_tracker_id)
    obs_tracker_source_new = OrderedDict({})
    #--- Key = (obs_tracker_source_id, source_obs_id, target_obs_id, relationship)
    #--- Value = (obs_tracker_source_id)

    user_hash_table = loader_db_mirror.user_hash_mirror()
    obs_well_hash_table = loader_db_mirror.obs_well_hash_mirror()
    obs_well_id = loader_db_mirror.obs_well_id_mirror()
    row_id_table = loader_db_mirror.row_id_mirror()
    seed_id_table = loader_db_mirror.seed_id_mirror()
    plant_id_table = loader_db_mirror.plant_id_mirror()
    tissue_id_table = loader_db_mirror.tissue_id_mirror()
    microbe_id_table = loader_db_mirror.microbe_id_mirror()
    culture_id_table = loader_db_mirror.culture_id_mirror()
    plate_id_table = loader_db_mirror.plate_id_mirror()
    well_id_table = loader_db_mirror.well_id_mirror()
    obs_tracker_hash_table = loader_db_mirror.obs_tracker_hash_mirror()
    obs_tracker_id = loader_db_mirror.obs_tracker_id_mirror()
    obs_tracker_source_hash_table = loader_db_mirror.obs_tracker_source_hash_mirror()
    obs_tracker_source_id = loader_db_mirror.obs_tracker_source_id_mirror()
    obs_tracker_stock_id_table = loader_db_mirror.obs_tracker_stock_id_mirror()
    obs_tracker_obs_row_id_table = loader_db_mirror.obs_tracker_obs_row_id_mirror()
    obs_tracker_obs_plant_id_table = loader_db_mirror.obs_tracker_obs_plant_id_mirror()
    obs_tracker_obs_tissue_id_table = loader_db_mirror.obs_tracker_obs_tissue_id_mirror()
    obs_tracker_obs_culture_id_table = loader_db_mirror.obs_tracker_obs_culture_id_mirror()
    obs_tracker_obs_plate_id_table = loader_db_mirror.obs_tracker_obs_plate_id_mirror()
    obs_tracker_obs_microbe_id_table = loader_db_mirror.obs_tracker_obs_microbe_id_mirror()
    experiment_name_table = loader_db_mirror.experiment_name_mirror()

    error_count = 0
    seed_id_error = OrderedDict({})
    row_id_error = OrderedDict({})
    plant_id_error = OrderedDict({})
    tissue_id_error = OrderedDict({})
    culture_id_error = OrderedDict({})
    plate_id_error = OrderedDict({})
    microbe_id_error = OrderedDict({})
    well_hash_exists = OrderedDict({})
    obs_tracker_hash_exists = OrderedDict({})
    obs_tracker_source_hash_exists = OrderedDict({})

    well_file = csv.DictReader(codecs.iterdecode(upload_file, 'utf-8'))
    for row in well_file:
        well_id = row["Well ID"]
        experiment_name = row["Experiment Name"]
        well = row["Well"]
        inventory = row["Inventory"]
        tube_label = row["Tube Label"]
        well_comments = row["Well Comments"]
        row_id = row["Source Row ID"]
        seed_id = row["Source Seed ID"]
        plant_id = row["Source Plant ID"]
        tissue_id = row["Source Tissue ID"]
        culture_id = row["Source Culture ID"]
        microbe_id = row["Source Microbe ID"]
        plate_id = row["Source Plate ID"]
        user = user

        if seed_id != '':
            seed_id_fix = seed_id + '\r'
            if seed_id in seed_id_table:
                stock_id = seed_id_table[seed_id][0]
            elif seed_id_fix in seed_id_table:
                stock_id = seed_id_table[seed_id_fix][0]
            else:
                seed_id_error[(well_id, experiment_name, well, inventory, tube_label, well_comments, row_id, seed_id, plant_id, tissue_id, culture_id, microbe_id, plate_id)] = error_count
                error_count = error_count + 1
                stock_id = 1
        else:
            stock_id = 1

        if row_id != '':
            row_id_fix = row_id + '\r'
            if row_id in row_id_table:
                obs_row_id = row_id_table[row_id][0]
            elif row_id_fix in row_id_table:
                obs_row_id = row_id_table[row_id_fix][0]
            else:
                row_id_error[(well_id, experiment_name, well, inventory, tube_label, well_comments, row_id, seed_id, plant_id, tissue_id, culture_id, microbe_id, plate_id)] = error_count
                error_count = error_count + 1
                obs_row_id = 1
        else:
            obs_row_id = 1

        if plant_id != '':
            plant_id_fix = plant_id + '\r'
            if plant_id in plant_id_table:
                obs_plant_id = plant_id_table[plant_id][0]
            elif plant_id_fix in plant_id_table:
                obs_plant_id = plant_id_table[plant_id_fix][0]
            else:
                plant_id_error[(well_id, experiment_name, well, inventory, tube_label, well_comments, row_id, seed_id, plant_id, tissue_id, culture_id, microbe_id, plate_id)] = error_count
                error_count = error_count + 1
                obs_plant_id = 1
        else:
            obs_plant_id = 1

        if tissue_id != '':
            tissue_id_fix = tissue_id + '\r'
            if tissue_id in tissue_id_table:
                obs_tissue_id = tissue_id_table[tissue_id][0]
            elif tissue_id_fix in tissue_id_table:
                obs_tissue_id = tissue_id_table[tissue_id_fix][0]
            else:
                tissue_id_error[(well_id, experiment_name, well, inventory, tube_label, well_comments, row_id, seed_id, plant_id, tissue_id, culture_id, microbe_id, plate_id)] = error_count
                error_count = error_count + 1
                obs_tissue_id = 1
        else:
            obs_tissue_id = 1

        if culture_id != '':
            culture_id_fix = culture_id + '\r'
            if culture_id in culture_id_table:
                obs_culture_id = culture_id_table[culture_id][0]
            elif culture_id_fix in culture_id_table:
                obs_culture_id = culture_id_table[culture_id_fix][0]
            else:
                culture_id_error[(well_id, experiment_name, well, inventory, tube_label, well_comments, row_id, seed_id, plant_id, tissue_id, culture_id, microbe_id, plate_id)] = error_count
                error_count = error_count + 1
                obs_culture_id = 1
        else:
            obs_culture_id = 1

        if plate_id != '':
            plate_id_fix = plate_id + '\r'
            if plate_id in plate_id_table:
                obs_plate_id = plate_id_table[plate_id][0]
            elif plate_id_fix in plate_id_table:
                obs_plate_id = plate_id_table[plate_id_fix][0]
            else:
                plate_id_error[(well_id, experiment_name, well, inventory, tube_label, well_comments, row_id, seed_id, plant_id, tissue_id, culture_id, microbe_id, plate_id)] = error_count
                error_count = error_count + 1
                obs_plate_id = 1
        else:
            obs_plate_id = 1

        if microbe_id != '':
            microbe_id_fix = microbe_id + '\r'
            if microbe_id in microbe_id_table:
                obs_microbe_id = microbe_id_table[microbe_id][0]
            elif microbe_id_fix in microbe_id_table:
                obs_microbe_id = microbe_id_table[microbe_id_fix][0]
            else:
                microbe_id_error[(well_id, experiment_name, well, inventory, tube_label, well_comments, row_id, seed_id, plant_id, tissue_id, culture_id, microbe_id, plate_id)] = error_count
                error_count = error_count + 1
                obs_microbe_id = 1
        else:
            obs_microbe_id = 1

        well_hash = well_id + well + inventory + tube_label + well_comments
        well_hash_fix = well_hash + '\r'
        if well_id not in well_id_table and well_id + '\r' not in well_id_table:
            if well_hash not in obs_well_hash_table and well_hash_fix not in obs_well_hash_table:
                obs_well_hash_table[well_hash] = obs_well_id
                obs_well_new[(obs_well_id, well_id, well, inventory, tube_label, well_comments)] = obs_well_id
                well_id_table[well_id] = (obs_well_id, well_id, well, inventory, tube_label, well_comments)
                obs_well_id = obs_well_id + 1
            else:
                well_hash_exists[(well_id, well, inventory, tube_label, well_comments)] = obs_well_id
        else:
            well_hash_exists[(well_id, well, inventory, tube_label, well_comments)] = obs_well_id

        if well_id in well_id_table:
            temp_obswell_id = well_id_table[well_id][0]
        elif well_id + '\r' in well_id_table:
            temp_obswell_id = well_id_table[well_id + '\r'][0]
        elif well_hash in obs_well_hash_table:
            temp_obswell_id = obs_well_hash_table[well_hash]
        elif well_hash_fix in obs_well_hash_table:
            temp_obswell_id = obs_well_hash_table[well_hash_fix]
        else:
            temp_obswell_id = 1
            error_count = error_count + 1

        obs_tracker_well_hash = 'well' + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(obs_culture_id) + str(1) + str(1) + str(1) + str(obs_microbe_id) + str(obs_plant_id) + str(obs_plate_id) + str(obs_row_id) + str(1) + str(obs_tissue_id) + str(temp_obswell_id) + str(stock_id) + str(user_hash_table[user.username])
        obs_tracker_well_hash_fix = obs_tracker_well_hash + '\r'
        if obs_tracker_well_hash not in obs_tracker_hash_table and obs_tracker_well_hash_fix not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_well_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'well', 1, 1, 1, 1, 1, 1, obs_culture_id, 1, 1, 1, obs_microbe_id, obs_plant_id, obs_plate_id, obs_row_id, 1, obs_tissue_id, temp_obswell_id, stock_id, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1
        else:
            obs_tracker_hash_exists[('well', 1, 1, 1, 1, 1, 1, obs_culture_id, 1, 1, 1, obs_microbe_id, obs_plant_id, obs_plate_id, obs_row_id, 1, obs_tissue_id, temp_obswell_id, stock_id, user_hash_table[user.username])] = obs_tracker_id

        if stock_id != 1:
            obs_tracker_source_stock_hash = str(obs_tracker_hash_table[obs_tracker_well_hash]) + str(obs_tracker_stock_id_table[stock_id][0]) + 'stock_in_well'
            if obs_tracker_source_stock_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_stock_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_well_hash], obs_tracker_stock_id_table[stock_id][0], 'stock_in_well')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_well_hash], obs_tracker_stock_id_table[stock_id][0], 'stock_in_well')] = obs_tracker_source_id

        if obs_row_id != 1:
            obs_tracker_source_row_hash = str(obs_tracker_hash_table[obs_tracker_well_hash]) + str(obs_tracker_obs_row_id_table[obs_row_id][0]) + 'row_in_well'
            if obs_tracker_source_row_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_row_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_well_hash], obs_tracker_obs_row_id_table[obs_row_id][0], 'row_in_well')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_well_hash], obs_tracker_obs_row_id_table[obs_row_id][0], 'row_in_well')] = obs_tracker_source_id

        if obs_plant_id != 1:
            obs_tracker_source_plant_hash = str(obs_tracker_hash_table[obs_tracker_well_hash]) + str(obs_tracker_obs_plant_id_table[obs_plant_id][0]) + 'plant_in_well'
            if obs_tracker_source_plant_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_plant_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_well_hash], obs_tracker_obs_plant_id_table[obs_plant_id][0], 'plant_in_well')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_well_hash], obs_tracker_obs_plant_id_table[obs_plant_id][0], 'plant_in_well')] = obs_tracker_source_id

        if obs_tissue_id != 1:
            obs_tracker_source_tissue_hash = str(obs_tracker_hash_table[obs_tracker_well_hash]) + str(obs_tracker_obs_tissue_id_table[obs_tissue_id][0]) + 'tissue_in_well'
            if obs_tracker_source_tissue_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_tissue_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_well_hash], obs_tracker_obs_tissue_id_table[obs_tissue_id][0], 'tissue_in_well')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_well_hash], obs_tracker_obs_tissue_id_table[obs_tissue_id][0], 'tissue_in_well')] = obs_tracker_source_id

        if obs_culture_id != 1:
            obs_tracker_source_culture_hash = str(obs_tracker_hash_table[obs_tracker_well_hash]) + str(obs_tracker_obs_culture_id_table[obs_culture_id][0]) + 'culture_in_well'
            if obs_tracker_source_culture_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_culture_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_well_hash], obs_tracker_obs_culture_id_table[obs_culture_id][0], 'culture_in_well')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_well_hash], obs_tracker_obs_culture_id_table[obs_culture_id][0], 'culture_in_well')] = obs_tracker_source_id

        if obs_microbe_id != 1:
            obs_tracker_source_microbe_hash = str(obs_tracker_hash_table[obs_tracker_well_hash]) + str(obs_tracker_obs_microbe_id_table[obs_microbe_id][0]) + 'microbe_in_well'
            if obs_tracker_source_microbe_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_microbe_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_well_hash], obs_tracker_obs_microbe_id_table[obs_microbe_id][0], 'microbe_in_well')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_well_hash], obs_tracker_obs_microbe_id_table[obs_microbe_id][0], 'microbe_in_well')] = obs_tracker_source_id

        if obs_plate_id != 1:
            obs_tracker_source_plate_hash = str(obs_tracker_obs_plate_id_table[obs_plate_id][0]) + str(obs_tracker_hash_table[obs_tracker_well_hash]) + 'well_in_plate'
            if obs_tracker_source_plate_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_plate_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_plate_id_table[obs_plate_id][0], obs_tracker_hash_table[obs_tracker_well_hash], 'well_in_plate')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_plate_id_table[obs_plate_id][0], obs_tracker_hash_table[obs_tracker_well_hash], 'well_in_plate')] = obs_tracker_source_id

        obs_tracker_exp_hash = 'experiment' + str(experiment_name_table[experiment_name][0]) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(user_hash_table[user.username])
        if obs_tracker_exp_hash not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_exp_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'experiment', experiment_name_table[experiment_name][0], 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1

        obs_tracker_source_hash = str(obs_tracker_hash_table[obs_tracker_exp_hash]) + str(obs_tracker_hash_table[obs_tracker_well_hash]) + 'well_used_in_experiment'
        if obs_tracker_source_hash not in obs_tracker_source_hash_table:
            obs_tracker_source_hash_table[obs_tracker_source_hash] = obs_tracker_source_id
            obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], obs_tracker_hash_table[obs_tracker_well_hash], 'well_used_in_experiment')] = obs_tracker_source_id
            obs_tracker_source_id = obs_tracker_source_id + 1
        else:
            obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], obs_tracker_hash_table[obs_tracker_well_hash], 'well_used_in_experiment')] = obs_tracker_source_id

    end = time.clock()
    stats = {}
    stats[("Time: %s" % (end-start), "Errors: %s" % (error_count))] = error_count

    results_dict = {}
    results_dict['obs_well_new'] = obs_well_new
    results_dict['obs_tracker_new'] = obs_tracker_new
    results_dict['obs_tracker_source_new'] = obs_tracker_source_new
    results_dict['seed_id_error'] = seed_id_error
    results_dict['row_id_error'] = row_id_error
    results_dict['plant_id_error'] = plant_id_error
    results_dict['tissue_id_error'] = tissue_id_error
    results_dict['culture_id_error'] = culture_id_error
    results_dict['plate_id_error'] = plate_id_error
    results_dict['microbe_id_error'] = microbe_id_error
    results_dict['well_hash_exists'] = well_hash_exists
    results_dict['obs_tracker_hash_exists'] = obs_tracker_hash_exists
    results_dict['obs_tracker_source_hash_exists'] = obs_tracker_source_hash_exists
    results_dict['stats'] = stats
    return results_dict

def well_loader_prep_output(results_dict, new_upload_exp, template_type):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s_%s_prep.csv"' % (new_upload_exp, template_type)
    writer = csv.writer(response)
    writer.writerow(['Stats'])
    writer.writerow([''])
    for key in results_dict['stats'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Well Table'])
    writer.writerow(['obs_well_id', 'well_id', 'well', 'well_inventory', 'tube_label', 'comments'])
    for key in results_dict['obs_well_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTracker Table'])
    writer.writerow(['obs_tracker_id', 'obs_entity_type', 'experiment_id', 'field_id', 'glycerol_stock_id', 'isolate_id', 'location_id', 'maize_sample_id', 'obs_culture_id', 'obs_dna_id', 'obs_env_id', 'obs_extract_id', 'obs_microbe_id', 'obs_plant_id', 'obs_plate_id', 'obs_row_id', 'obs_sample_id', 'obs_tissue_id', 'obs_well_id', 'stock_id', 'user_id'])
    for key in results_dict['obs_tracker_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTrackerSource Table'])
    writer.writerow(['obs_tracker_source_id', 'source_obs_id', 'targe_obs_id', 'relationship'])
    for key in results_dict['obs_tracker_source_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['---------------------------------------------------------------------------------------------------'])
    writer.writerow([''])
    writer.writerow(['Seed ID Errors'])
    writer.writerow(['well_id', 'experiment_name', 'well', 'inventory', 'tube_label', 'well_comments', 'source_row_id', 'source_seed_id', 'source_plant_id', 'source_tissue_id', 'source_culture_id', 'source_microbe_id', 'source_plate_id'])
    for key in results_dict['seed_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Row ID Errors'])
    writer.writerow(['well_id', 'experiment_name', 'well', 'inventory', 'tube_label', 'well_comments', 'source_row_id', 'source_seed_id', 'source_plant_id', 'source_tissue_id', 'source_culture_id', 'source_microbe_id', 'source_plate_id'])
    for key in results_dict['row_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Plant ID Errors'])
    writer.writerow(['well_id', 'experiment_name', 'well', 'inventory', 'tube_label', 'well_comments', 'source_row_id', 'source_seed_id', 'source_plant_id', 'source_tissue_id', 'source_culture_id', 'source_microbe_id', 'source_plate_id'])
    for key in results_dict['plant_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Tissue ID Errors'])
    writer.writerow(['well_id', 'experiment_name', 'well', 'inventory', 'tube_label', 'well_comments', 'source_row_id', 'source_seed_id', 'source_plant_id', 'source_tissue_id', 'source_culture_id', 'source_microbe_id', 'source_plate_id'])
    for key in results_dict['tissue_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Culture ID Errors'])
    writer.writerow(['well_id', 'experiment_name', 'well', 'inventory', 'tube_label', 'well_comments', 'source_row_id', 'source_seed_id', 'source_plant_id', 'source_tissue_id', 'source_culture_id', 'source_microbe_id', 'source_plate_id'])
    for key in results_dict['culture_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Microbe ID Errors'])
    writer.writerow(['well_id', 'experiment_name', 'well', 'inventory', 'tube_label', 'well_comments', 'source_row_id', 'source_seed_id', 'source_plant_id', 'source_tissue_id', 'source_culture_id', 'source_microbe_id', 'source_plate_id'])
    for key in results_dict['microbe_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Plate ID Errors'])
    writer.writerow(['well_id', 'experiment_name', 'well', 'inventory', 'tube_label', 'well_comments', 'source_row_id', 'source_seed_id', 'source_plant_id', 'source_tissue_id', 'source_culture_id', 'source_microbe_id', 'source_plate_id'])
    for key in results_dict['plate_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Well Entry Already Exists'])
    for key in results_dict['well_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTracker Entry Already Exists'])
    for key in results_dict['obs_tracker_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTrackerSource Entries Already Exist'])
    for key in results_dict['obs_tracker_source_hash_exists'].keys():
        writer.writerow(key)
    return response

def well_loader(results_dict):
    try:
        for key in results_dict['obs_well_new'].keys():
            try:
                with transaction.atomic():
                    new_obswell = ObsWell.objects.create(id=key[0], well_id=key[1], well=key[2], well_inventory=key[3], tube_label=key[4], comments=key[5])
            except Exception as e:
                print("ObsWell Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = ObsTracker.objects.create(id=key[0], obs_entity_type=key[1], experiment_id=key[2], field_id=key[3], glycerol_stock_id=key[4], isolate_id=key[5], location_id=key[6], maize_sample_id=key[7], obs_culture_id=key[8], obs_dna_id=key[9], obs_env_id=key[10], obs_extract_id=key[11], obs_microbe_id=key[12], obs_plant_id=key[13], obs_plate_id=key[14], obs_row_id=key[15], obs_sample_id=key[16], obs_tissue_id=key[17], obs_well_id=key[18], stock_id=key[19], user_id=key[20])
            except Exception as e:
                print("ObsTracker Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_source_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = ObsTrackerSource.objects.create(id=key[0], source_obs_id=key[1], target_obs_id=key[2], relationship=key[3])
            except Exception as e:
                print("ObsTrackerSource Error: %s %s" % (e.message, e.args))
                return False
    except Exception as e:
        print("Error: %s %s" % (e.message, e.args))
        return False
    return True

def samples_loader_prep(upload_file, user):
    start = time.clock()

    obs_sample_new = OrderedDict({})
    #--- Key = (obs_sample_id, sample_id, sample_type, sample_name, weight, volume, density, kernel_num, photo, comments)
    #--- Value = (obs_sample_id)
    obs_tracker_new = OrderedDict({})
    #--- Key = (obs_tracker_id, obs_entity_type, experiment_id, field_id, glycerol_stock_id, isolate_id, location_id, maize_sample_id, obs_culture_id, obs_dna_id, obs_env_id, obs_extract_id, obs_microbe_id, obs_plant_id, obs_plate_id, obs_row_id, obs_sample_id, obs_tissue_id, obs_well_id, stock_id, user_id)
    #--- Value = (obs_tracker_id)
    obs_tracker_source_new = OrderedDict({})
    #--- Key = (obs_tracker_source_id, source_obs_id, target_obs_id)
    #--- Value = (obs_tracker_source_id)

    user_hash_table = loader_db_mirror.user_hash_mirror()
    obs_sample_hash_table = loader_db_mirror.obs_sample_hash_mirror()
    obs_sample_id = loader_db_mirror.obs_sample_id_mirror()
    row_id_table = loader_db_mirror.row_id_mirror()
    seed_id_table = loader_db_mirror.seed_id_mirror()
    plant_id_table = loader_db_mirror.plant_id_mirror()
    sample_id_table = loader_db_mirror.sample_id_mirror()
    obs_tracker_hash_table = loader_db_mirror.obs_tracker_hash_mirror()
    obs_tracker_id = loader_db_mirror.obs_tracker_id_mirror()
    experiment_name_table = loader_db_mirror.experiment_name_mirror()
    obs_tracker_sample_id_table = loader_db_mirror.obs_tracker_sample_id_mirror()
    obs_tracker_source_hash_table = loader_db_mirror.obs_tracker_source_hash_mirror()
    obs_tracker_source_id = loader_db_mirror.obs_tracker_source_id_mirror()
    obs_tracker_stock_id_table = loader_db_mirror.obs_tracker_stock_id_mirror()
    obs_tracker_obs_row_id_table = loader_db_mirror.obs_tracker_obs_row_id_mirror()
    obs_tracker_obs_plant_id_table = loader_db_mirror.obs_tracker_obs_plant_id_mirror()

    error_count = 0
    seed_id_error = OrderedDict({})
    row_id_error = OrderedDict({})
    plant_id_error = OrderedDict({})
    source_sample_id_error = OrderedDict({})
    sample_hash_exists = OrderedDict({})
    obs_tracker_hash_exists = OrderedDict({})
    obs_tracker_source_hash_exists = OrderedDict({})

    sample_file = csv.DictReader(codecs.iterdecode(upload_file, 'utf-8'))
    for row in sample_file:
        sample_id = row["Sample ID"]
        experiment_name = row["Experiment Name"]
        sample_type = row["Sample Type"]
        sample_name = row["Sample Name"]
        kernel_num = row["Kernel Number"]
        weight = row["Weight"]
        volume = row["Volume"]
        density = row["Density"]
        photo = row["Photo"]
        sample_comments = row["Sample Comments"]
        row_id = row["Source Row ID"]
        seed_id = row["Source Seed ID"]
        plant_id = row["Source Plant ID"]
        source_sample_id = row["Source Sample ID"]
        user = user

        if seed_id != '':
            seed_id_fix = seed_id + '\r'
            if seed_id in seed_id_table:
                stock_id = seed_id_table[seed_id][0]
            elif seed_id_fix in seed_id_table:
                stock_id = seed_id_table[seed_id_fix][0]
            else:
                seed_id_error[(sample_id, experiment_name, sample_type, sample_name, kernel_num, weight, volume, density, photo, sample_comments, row_id, seed_id, plant_id)] = error_count
                error_count = error_count + 1
                stock_id = 1
        else:
            stock_id = 1

        if row_id != '':
            row_id_fix = row_id + '\r'
            if row_id in row_id_table:
                obs_row_id = row_id_table[row_id][0]
            elif row_id_fix in row_id_table:
                obs_row_id = row_id_table[row_id_fix][0]
            else:
                row_id_error[(sample_id, experiment_name, sample_type, sample_name, kernel_num, weight, volume, density, photo, sample_comments, row_id, seed_id, plant_id)] = error_count
                error_count = error_count + 1
                obs_row_id = 1
        else:
            obs_row_id = 1

        if plant_id != '':
            plant_id_fix = plant_id + '\r'
            if plant_id in plant_id_table:
                obs_plant_id = plant_id_table[plant_id][0]
            elif plant_id_fix in plant_id_table:
                obs_plant_id = plant_id_table[plant_id_fix][0]
            else:
                plant_id_error[(sample_id, experiment_name, sample_type, sample_name, kernel_num, weight, volume, density, photo, sample_comments, row_id, seed_id, plant_id)] = error_count
                error_count = error_count + 1
                obs_plant_id = 1
        else:
            obs_plant_id = 1

        sample_hash = sample_id + sample_type + sample_name + weight + volume + density + kernel_num + photo + sample_comments
        sample_hash_fix = sample_hash + '\r'
        if sample_id not in sample_id_table and sample_id + '\r' not in sample_id_table:
            if sample_hash not in obs_sample_hash_table and sample_hash_fix not in obs_sample_hash_table:
                obs_sample_hash_table[sample_hash] = obs_sample_id
                obs_sample_new[(obs_sample_id, sample_id, sample_type, sample_name, weight, volume, density, kernel_num, photo, sample_comments)] = obs_sample_id
                sample_id_table[sample_id] = (obs_sample_id, sample_id, sample_type, sample_name, weight, volume, density, kernel_num, photo, sample_comments)
                obs_sample_id = obs_sample_id + 1
            else:
                sample_hash_exists[(sample_id, sample_type, sample_name, weight, volume, density, kernel_num, photo, sample_comments)] = obs_sample_id
        else:
            sample_hash_exists[(sample_id, sample_type, sample_name, weight, volume, density, kernel_num, photo, sample_comments)] = obs_sample_id

        if sample_id in sample_id_table:
            temp_obssample_id = sample_id_table[sample_id][0]
        elif sample_id + '\r' in sample_id_table:
            temp_obssample_id = sample_id_table[sample_id + '\r'][0]
        elif sample_hash in obs_sample_hash_table:
            temp_obssample_id = obs_sample_hash_table[sample_hash]
        elif sample_hash_fix in obs_sample_hash_table:
            temp_obssample_id = obs_sample_hash_table[sample_hash_fix]
        else:
            temp_obssample_id = 1
            error_count = error_count + 1

        obs_tracker_sample_hash = 'sample' + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(obs_plant_id) + str(1) + str(obs_row_id) + str(temp_obssample_id) + str(1) + str(1) + str(stock_id) + str(user_hash_table[user.username])
        obs_tracker_sample_hash_fix = obs_tracker_sample_hash + '\r'
        if obs_tracker_sample_hash not in obs_tracker_hash_table and obs_tracker_sample_hash_fix not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_sample_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'sample', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, obs_plant_id, 1, obs_row_id, temp_obssample_id, 1, 1, stock_id, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_sample_id_table[(sample_id)] = (obs_tracker_id, 'sample', experiment_name_table[experiment_name][0], 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, obs_plant_id, 1, obs_row_id, temp_obssample_id, 1, 1, stock_id, user_hash_table[user.username])
            obs_tracker_id = obs_tracker_id + 1
        else:
            obs_tracker_hash_exists[('sample', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, obs_plant_id, 1, obs_row_id, temp_obssample_id, 1, 1, stock_id, user_hash_table[user.username])] = obs_tracker_id

        if stock_id != 1:
            obs_tracker_source_stock_hash = str(obs_tracker_stock_id_table[stock_id][0]) + str(obs_tracker_hash_table[obs_tracker_sample_hash]) + 'sample_from_stock'
            if obs_tracker_source_stock_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_stock_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_stock_id_table[stock_id][0], obs_tracker_hash_table[obs_tracker_sample_hash], 'sample_from_stock')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_stock_id_table[stock_id][0], obs_tracker_hash_table[obs_tracker_sample_hash], 'sample_from_stock')] = obs_tracker_source_id

        if obs_row_id != 1:
            obs_tracker_source_row_hash = str(obs_tracker_obs_row_id_table[obs_row_id][0]) + str(obs_tracker_hash_table[obs_tracker_sample_hash]) + 'sample_from_row'
            if obs_tracker_source_row_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_row_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_row_id_table[obs_row_id][0], obs_tracker_hash_table[obs_tracker_sample_hash], 'sample_from_row')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_row_id_table[obs_row_id][0], obs_tracker_hash_table[obs_tracker_sample_hash], 'sample_from_row')] = obs_tracker_source_id

        if obs_plant_id != 1:
            obs_tracker_source_plant_hash = str(obs_tracker_obs_plant_id_table[obs_plant_id][0]) + str(obs_tracker_hash_table[obs_tracker_sample_hash]) + 'sample_from_plant'
            if obs_tracker_source_plant_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_plant_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_plant_id_table[obs_plant_id][0], obs_tracker_hash_table[obs_tracker_sample_hash], 'sample_from_plant')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_plant_id_table[obs_plant_id][0], obs_tracker_hash_table[obs_tracker_sample_hash], 'sample_from_plant')] = obs_tracker_source_id

        if source_sample_id != '':
            source_sample_id_fix = source_sample_id + '\r'
            if source_sample_id in obs_tracker_sample_id_table:
                obs_tracker_source_sample_id = obs_tracker_sample_id_table[source_sample_id][0]
                obs_tracker_target_sample_id = obs_tracker_sample_id_table[sample_id][0]
                obs_tracker_source_hash = str(obs_tracker_source_sample_id) + str(obs_tracker_target_sample_id) + 'sample_from_sample'
                if obs_tracker_source_hash not in obs_tracker_source_hash_table:
                    obs_tracker_source_hash_table[obs_tracker_source_hash] = obs_tracker_source_id
                    obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_source_sample_id, obs_tracker_target_sample_id, 'sample_from_sample')] = obs_tracker_source_id
                    obs_tracker_source_id = obs_tracker_source_id + 1
                else:
                    obs_tracker_source_hash_exists[(obs_tracker_source_sample_id, obs_tracker_target_sample_id, 'sample_from_sample')] = obs_tracker_source_id
            else:
                source_sample_id_error[(sample_id, experiment_name, sample_type, sample_name, kernel_num, weight, volume, density, photo, sample_comments, row_id, seed_id, plant_id, source_sample_id)] = error_count
                error_count = error_count + 1

        obs_tracker_exp_hash = 'experiment' + str(experiment_name_table[experiment_name][0]) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(user_hash_table[user.username])
        if obs_tracker_exp_hash not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_exp_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'experiment', experiment_name_table[experiment_name][0], 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1

        obs_tracker_source_hash = str(obs_tracker_hash_table[obs_tracker_exp_hash]) + str(obs_tracker_hash_table[obs_tracker_sample_hash]) + 'sample_used_in_experiment'
        if obs_tracker_source_hash not in obs_tracker_source_hash_table:
            obs_tracker_source_hash_table[obs_tracker_source_hash] = obs_tracker_source_id
            obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], obs_tracker_hash_table[obs_tracker_sample_hash], 'sample_used_in_experiment')] = obs_tracker_source_id
            obs_tracker_source_id = obs_tracker_source_id + 1
        else:
            obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], obs_tracker_hash_table[obs_tracker_sample_hash], 'sample_used_in_experiment')] = obs_tracker_source_id

    end = time.clock()
    stats = {}
    stats[("Time: %s" % (end-start), "Errors: %s" % (error_count))] = error_count

    results_dict = {}
    results_dict['obs_sample_new'] = obs_sample_new
    results_dict['obs_tracker_new'] = obs_tracker_new
    results_dict['obs_tracker_source_new'] = obs_tracker_source_new
    results_dict['seed_id_error'] = seed_id_error
    results_dict['row_id_error'] = row_id_error
    results_dict['plant_id_error'] = plant_id_error
    results_dict['source_sample_id_error'] = source_sample_id_error
    results_dict['sample_hash_exists'] = sample_hash_exists
    results_dict['obs_tracker_hash_exists'] = obs_tracker_hash_exists
    results_dict['obs_tracker_source_hash_exists'] = obs_tracker_source_hash_exists
    results_dict['stats'] = stats
    return results_dict

def samples_loader_prep_output(results_dict, new_upload_exp, template_type):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s_%s_prep.csv"' % (new_upload_exp, template_type)
    writer = csv.writer(response)
    writer.writerow(['Stats'])
    writer.writerow([''])
    for key in results_dict['stats'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Samples Table'])
    writer.writerow(['obs_sample_id', 'sample_id', 'sample_type', 'sample_name', 'weight', 'volume', 'density', 'kernel_num', 'photo', 'comments'])
    for key in results_dict['obs_sample_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTracker Table'])
    writer.writerow(['obs_tracker_id', 'obs_entity_type', 'experiment_id', 'field_id', 'glycerol_stock_id', 'isolate_id', 'location_id', 'maize_sample_id', 'obs_culture_id', 'obs_dna_id', 'obs_env_id', 'obs_extract_id', 'obs_microbe_id', 'obs_plant_id', 'obs_plate_id', 'obs_row_id', 'obs_sample_id', 'obs_tissue_id', 'obs_well_id', 'stock_id', 'user_id'])
    for key in results_dict['obs_tracker_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTrackerSource Table'])
    writer.writerow(['obs_tracker_source_id', 'source_obs_id', 'target_obs_id'])
    for key in results_dict['obs_tracker_source_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['---------------------------------------------------------------------------------------------------'])
    writer.writerow([''])
    writer.writerow(['Seed ID Errors'])
    writer.writerow(['sample_id', 'experiment_name', 'sample_type', 'sample_name', 'kernel_num', 'weight', 'volume', 'density', 'photo', 'sample_comments', 'source_row_id', 'source_seed_id', 'source_plant_id'])
    for key in results_dict['seed_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Row ID Errors'])
    writer.writerow(['sample_id', 'experiment_name', 'sample_type', 'sample_name', 'kernel_num', 'weight', 'volume', 'density', 'photo', 'sample_comments', 'source_row_id', 'source_seed_id', 'source_plant_id'])
    for key in results_dict['row_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Plant ID Errors'])
    writer.writerow(['sample_id', 'experiment_name', 'sample_type', 'sample_name', 'kernel_num', 'weight', 'volume', 'density', 'photo', 'sample_comments', 'source_row_id', 'source_seed_id', 'source_plant_id'])
    for key in results_dict['plant_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Source Sample ID Errors'])
    writer.writerow(['sample_id', 'experiment_name', 'sample_type', 'sample_name', 'kernel_num', 'weight', 'volume', 'density', 'photo', 'sample_comments', 'source_row_id', 'source_seed_id', 'source_plant_id', 'source_sample_id'])
    for key in results_dict['source_sample_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Samples Entry Already Exists'])
    for key in results_dict['sample_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTracker Entry Already Exists'])
    for key in results_dict['obs_tracker_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTrackerSource Entry Already Exists'])
    for key in results_dict['obs_tracker_source_hash_exists'].keys():
        writer.writerow(key)
    return response

def samples_loader(results_dict):
    try:
        for key in results_dict['obs_sample_new'].keys():
            try:
                with transaction.atomic():
                    new_obssample = ObsSample.objects.create(id=key[0], sample_id=key[1], sample_type=key[2], sample_name=key[3], weight=key[4], volume=key[5], density=key[6], kernel_num=key[7], photo=key[8], comments=key[9])
            except Exception as e:
                print("ObsSample Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_new'].keys():
            try:
                with transaction.atomic():
                    new_obstracker = ObsTracker.objects.create(id=key[0], obs_entity_type=key[1], experiment_id=key[2], field_id=key[3], glycerol_stock_id=key[4], isolate_id=key[5], location_id=key[6], maize_sample_id=key[7], obs_culture_id=key[8], obs_dna_id=key[9], obs_env_id=key[10], obs_extract_id=key[11], obs_microbe_id=key[12], obs_plant_id=key[13], obs_plate_id=key[14], obs_row_id=key[15], obs_sample_id=key[16], obs_tissue_id=key[17], obs_well_id=key[18], stock_id=key[19], user_id=key[20])
            except Exception as e:
                print("ObsTracker Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_source_new'].keys():
            try:
                with transaction.atomic():
                    new_obstrackersource = ObsTrackerSource.objects.create(id=key[0], source_obs_id=key[1], target_obs_id=key[2], relationship=key[3])
            except Exception as e:
                print("ObsTrackerSource Error: %s %s" % (e.message, e.args))
                return False
    except Exception as e:
        print("Error: %s %s" % (e.message, e.args))
        return False
    return True

def maize_loader_prep(upload_file, user):
    start = time.clock()

    maize_sample_new = OrderedDict({})
    #--- Key = (maize_sample_id, maize_id, gps_altitude, county, weight, appearance, photo, gps_accuracy, gps_latitude, gps_longitude, harvest_date, maize_variety, moisture_content, seed_source, source_type, storage_conditions, storage_months, sub_location, village)
    #--- Value = (maize_sample_id)
    obs_tracker_new = OrderedDict({})
    #--- Key = (obs_tracker_id, obs_entity_type, experiment_id, field_id, glycerol_stock_id, isolate_id, location_id, maize_sample_id, obs_culture_id, obs_dna_id, obs_env_id, obs_extract_id, obs_microbe_id, obs_plant_id, obs_plate_id, obs_row_id, obs_sample_id, obs_tissue_id, obs_well_id, stock_id, user_id)
    #--- Value = (obs_tracker_id)
    obs_tracker_source_new = OrderedDict({})

    user_hash_table = loader_db_mirror.user_hash_mirror()
    maize_sample_hash_table = loader_db_mirror.maize_sample_hash_mirror()
    maize_sample_id = loader_db_mirror.maize_sample_id_mirror()
    maize_id_table = loader_db_mirror.maize_id_mirror()
    obs_tracker_hash_table = loader_db_mirror.obs_tracker_hash_mirror()
    obs_tracker_source_hash_table = loader_db_mirror.obs_tracker_source_hash_mirror()
    obs_tracker_id = loader_db_mirror.obs_tracker_id_mirror()
    obs_tracker_source_id = loader_db_mirror.obs_tracker_source_id_mirror()
    experiment_name_table = loader_db_mirror.experiment_name_mirror()

    error_count = 0
    maize_sample_hash_exists = OrderedDict({})
    obs_tracker_hash_exists = OrderedDict({})
    obs_tracker_source_hash_exists = OrderedDict({})

    maize_sample_file = csv.DictReader(codecs.iterdecode(upload_file, 'utf-8'))
    for row in maize_sample_file:
        maize_id = row["Maize ID"]
        experiment_name = row["Experiment Name"]
        county = row["County"]
        sub_location = row["Sub Location"]
        village = row["Village"]
        weight = row["Weight"]
        harvest_date = row["Harvest Date"]
        storage_months = row["Storage Months"]
        storage_conditions = row["Storage Conditions"]
        maize_variety = row["Maize Variety"]
        seed_source = row["Seed Source"]
        moisture_content = row["Moisture Content"]
        source_type = row["Source Type"]
        appearance = row["Appearance"]
        gps_latitude = row["GPS Latitude"]
        gps_longitude = row["GPS Longitude"]
        gps_altitude = row["GPS Altitude"]
        gps_accuracy = row["GPS Accuracy"]
        photo = row["Photo"]
        user = user

        maize_hash = maize_id + gps_altitude + county + weight + appearance + photo + gps_accuracy + gps_latitude + gps_longitude + harvest_date + maize_variety + moisture_content + seed_source + source_type + storage_conditions + storage_months + sub_location + village
        maize_hash_fix = maize_hash + '\r'
        if maize_id not in maize_id_table and maize_id + '\r' not in maize_id_table:
            if maize_hash not in maize_sample_hash_table and maize_hash_fix not in maize_sample_hash_table:
                maize_sample_hash_table[maize_hash] = maize_sample_id
                maize_sample_new[(maize_sample_id, maize_id, gps_altitude, county, weight, appearance, photo, gps_accuracy, gps_latitude, gps_longitude, harvest_date, maize_variety, moisture_content, seed_source, source_type, storage_conditions, storage_months, sub_location, village)] = maize_sample_id
                maize_id_table[maize_id] = (maize_sample_id, maize_id, gps_altitude, county, weight, appearance, photo, gps_accuracy, gps_latitude, gps_longitude, harvest_date, maize_variety, moisture_content, seed_source, source_type, storage_conditions, storage_months, sub_location, village)
                maize_sample_id = maize_sample_id + 1
            else:
                maize_sample_hash_exists[(maize_id, gps_altitude, county, weight, appearance, photo, gps_accuracy, gps_latitude, gps_longitude, harvest_date, maize_variety, moisture_content, seed_source, source_type, storage_conditions, storage_months, sub_location, village)] = maize_sample_id
        else:
            maize_sample_hash_exists[(maize_id, gps_altitude, county, weight, appearance, photo, gps_accuracy, gps_latitude, gps_longitude, harvest_date, maize_variety, moisture_content, seed_source, source_type, storage_conditions, storage_months, sub_location, village)] = maize_sample_id

        if maize_id in maize_id_table:
            temp_maizesample_id = maize_id_table[maize_id][0]
        elif maize_id + '\r' in maize_id_table:
            temp_maizesample_id = maize_id_table[maize_id + '\r'][0]
        elif maize_hash in maize_sample_hash_table:
            temp_maizesample_id = maize_sample_hash_table[maize_hash]
        elif maize_hash_fix in maize_sample_hash_table:
            temp_maizesample_id = maize_sample_hash_table[maize_hash_fix]
        else:
            temp_maizesample_id = 1
            error_count = error_count + 1

        tracker_maize_sample_hash = 'maize' + str(1) + str(1) + str(1) + str(1) + str(1) + str(temp_maizesample_id) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(user_hash_table[user.username])
        tracker_maize_sample_hash_fix = tracker_maize_sample_hash + '\r'
        if tracker_maize_sample_hash not in obs_tracker_hash_table and tracker_maize_sample_hash_fix not in obs_tracker_hash_table:
            obs_tracker_hash_table[tracker_maize_sample_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'maize', 1, 1, 1, 1, 1, temp_maizesample_id, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1
        else:
            obs_tracker_hash_exists[('maize', 1, 1, 1, 1, 1, temp_maizesample_id, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, user_hash_table[user.username])] = obs_tracker_id

        obs_tracker_exp_hash = 'experiment' + str(experiment_name_table[experiment_name][0]) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(user_hash_table[user.username])
        if obs_tracker_exp_hash not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_exp_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'experiment', experiment_name_table[experiment_name][0], 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1

        obs_tracker_source_hash = str(obs_tracker_hash_table[obs_tracker_exp_hash]) + str(obs_tracker_hash_table[tracker_maize_sample_hash]) + 'maize_used_in_experiment'
        if obs_tracker_source_hash not in obs_tracker_source_hash_table:
            obs_tracker_source_hash_table[obs_tracker_source_hash] = obs_tracker_source_id
            obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], obs_tracker_hash_table[tracker_maize_sample_hash], 'maize_used_in_experiment')] = obs_tracker_source_id
            obs_tracker_source_id = obs_tracker_source_id + 1
        else:
            obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], obs_tracker_hash_table[tracker_maize_sample_hash], 'maize_used_in_experiment')] = obs_tracker_source_id

    end = time.clock()
    stats = {}
    stats[("Time: %s" % (end-start), "Errors: %s" % (error_count))] = error_count

    results_dict = {}
    results_dict['maize_sample_new'] = maize_sample_new
    results_dict['obs_tracker_new'] = obs_tracker_new
    results_dict['obs_tracker_source_new'] = obs_tracker_source_new
    results_dict['maize_sample_hash_exists'] = maize_sample_hash_exists
    results_dict['obs_tracker_hash_exists'] = obs_tracker_hash_exists
    results_dict['obs_tracker_source_hash_exists'] = obs_tracker_source_hash_exists
    results_dict['stats'] = stats
    return results_dict

def maize_loader_prep_output(results_dict, new_upload_exp, template_type):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s_%s_prep.csv"' % (new_upload_exp, template_type)
    writer = csv.writer(response)
    writer.writerow(['Stats'])
    writer.writerow([''])
    for key in results_dict['stats'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Maize Samples Table'])
    writer.writerow(['maize_sample_id', 'maize_id', 'gps_altitude', 'county', 'weight', 'appearance', 'photo', 'gps_accuracy', 'gps_latitude', 'gps_longitude', 'harvest_date', 'maize_variety', 'moisture_content', 'seed_source', 'source_type', 'storage_conditions', 'storage_months', 'sub_location', 'village'])
    for key in results_dict['maize_sample_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTracker Table'])
    writer.writerow(['obs_tracker_id', 'obs_entity_type', 'experiment_id', 'field_id', 'glycerol_stock_id', 'isolate_id', 'location_id', 'maize_sample_id', 'obs_culture_id', 'obs_dna_id', 'obs_env_id', 'obs_extract_id', 'obs_microbe_id', 'obs_plant_id', 'obs_plate_id', 'obs_row_id', 'obs_sample_id', 'obs_tissue_id', 'obs_well_id', 'stock_id', 'user_id'])
    for key in results_dict['obs_tracker_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTrackerSource Table'])
    writer.writerow(['obs_tracker_source_id', 'obs_source_id', 'obs_target_id', 'relationship'])
    for key in results_dict['obs_tracker_source_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['---------------------------------------------------------------------------------------------------'])
    writer.writerow([''])
    writer.writerow(['Maize Sample Entry Already Exists'])
    for key in results_dict['maize_sample_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTracker Entry Already Exists'])
    for key in results_dict['obs_tracker_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTrackerSource Entry Already Exists'])
    for key in results_dict['obs_tracker_source_hash_exists'].keys():
        writer.writerow(key)
    return response

def maize_loader(results_dict):
    try:
        for key in results_dict['maize_sample_new'].keys():
            try:
                with transaction.atomic():
                    new_maizesample = MaizeSample.objects.create(id=key[0], maize_id=key[1], gps_altitude=key[2], county=key[3], weight=key[4], appearance=key[5], photo=key[6], gps_accuracy=key[7], gps_latitude=key[8], gps_longitude=key[9], harvest_date=key[10], maize_variety=key[11], moisture_content=key[12], seed_source=key[13], source_type=key[14], storage_conditions=key[15], storage_months=key[16], sub_location=key[17], village=key[18])
            except Exception as e:
                print("MaizeSample Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = ObsTracker.objects.create(id=key[0], obs_entity_type=key[1], experiment_id=key[2], field_id=key[3], glycerol_stock_id=key[4], isolate_id=key[5], location_id=key[6], maize_sample_id=key[7], obs_culture_id=key[8], obs_dna_id=key[9], obs_env_id=key[10], obs_extract_id=key[11], obs_microbe_id=key[12], obs_plant_id=key[13], obs_plate_id=key[14], obs_row_id=key[15], obs_sample_id=key[16], obs_tissue_id=key[17], obs_well_id=key[18], stock_id=key[19], user_id=key[20])
            except Exception as e:
                print("ObsTracker Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_source_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = ObsTrackerSource.objects.create(id=key[0], source_obs_id=key[1], target_obs_id=key[2], relationship=key[3])
            except Exception as e:
                print("ObsTrackerSource Error: %s %s" % (e.message, e.args))
                return False
    except Exception as e:
        print("Error: %s %s" % (e.message, e.args))
        return False
    return True

def separation_loader_prep(upload_file, user):
    start = time.clock()

    separation_new = OrderedDict({})
    #--- Key = (separation_id, obs_sample_id, separation_type, apparatus, sg, light_weight, intermediate_weight, heavy_weight, light_percent, intermediate_percent, heavy_percent, operating_factor, comments)
    #--- Value = (separation_id)

    user_hash_table = loader_db_mirror.user_hash_mirror()
    separation_hash_table = loader_db_mirror.separation_hash_mirror()
    separation_id = loader_db_mirror.separation_id_mirror()
    sample_id_table = loader_db_mirror.sample_id_mirror()

    error_count = 0
    sample_id_error = OrderedDict({})
    separation_hash_exists = OrderedDict({})

    separation_file = csv.DictReader(codecs.iterdecode(upload_file, 'utf-8'))
    for row in separation_file:
        sample_id = row["Sample ID"]
        sample_name = row["Sample Name"]
        separation_type = row["Separation Type"]
        apparatus = row["Apparatus"]
        sg = row["SG"]
        light_weight = row["Light Weight"]
        medium_weight = row["Medium Weight"]
        heavy_weight = row["Heavy Weight"]
        light_percent = row["Light Percent"]
        medium_percent = row["Medium Percent"]
        heavy_percent = row["Heavy Percent"]
        operating_factor = row["Operating Factor"]
        comments = row["Separation Comments"]

        if sample_id != '':
            seed_id_fix = sample_id + '\r'
            if sample_id in sample_id_table:
                obs_sample_id = sample_id_table[sample_id][0]
            elif seed_id_fix in sample_id_table:
                obs_sample_id = sample_id_table[seed_id_fix][0]
            else:
                sample_id_error[(sample_id, sample_name, separation_type, apparatus, sg, light_weight, medium_weight, heavy_weight, light_percent, medium_percent, heavy_percent, operating_factor, comments)] = error_count
                error_count = error_count + 1
                obs_sample_id = 1
        else:
            obs_sample_id = 1

        separation_hash = str(obs_sample_id) + separation_type + apparatus + sg + light_weight + medium_weight + heavy_weight + light_percent + medium_percent + heavy_percent + operating_factor + comments
        separation_hash_fix = separation_hash + '\r'
        if separation_hash not in separation_hash_table and separation_hash_fix not in separation_hash_table:
            separation_hash_table[separation_hash] = separation_id
            separation_new[(separation_id, obs_sample_id, separation_type, apparatus, sg, light_weight, medium_weight, heavy_weight, light_percent, medium_percent, heavy_percent, operating_factor, comments)] = separation_id
            separation_id = separation_id + 1
        else:
            separation_hash_exists[(obs_sample_id, separation_type, apparatus, sg, light_weight, medium_weight, heavy_weight, light_percent, medium_percent, heavy_percent, operating_factor, comments)] = obs_sample_id

    end = time.clock()
    stats = {}
    stats[("Time: %s" % (end-start), "Errors: %s" % (error_count))] = error_count

    results_dict = {}
    results_dict['separation_new'] = separation_new
    results_dict['sample_id_error'] = sample_id_error
    results_dict['separation_hash_exists'] = separation_hash_exists
    results_dict['stats'] = stats
    return results_dict

def separation_loader_prep_output(results_dict, new_upload_exp, template_type):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s_%s_prep.csv"' % (new_upload_exp, template_type)
    writer = csv.writer(response)
    writer.writerow(['Stats'])
    writer.writerow([''])
    for key in results_dict['stats'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Separation Table'])
    writer.writerow(['separation_id', 'obs_sample_id', 'separation_type', 'apparatus', 'sg', 'light_weight', 'medium_weight', 'heavy_weight', 'light_percent', 'medium_percent', 'heavy_percent', 'operating_factor', 'comments'])
    for key in results_dict['separation_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['---------------------------------------------------------------------------------------------------'])
    writer.writerow([''])
    writer.writerow(['Sample ID Errors'])
    writer.writerow(['sample_id', 'sample_name', 'separation_type', 'apparatus', 'sg', 'light_weight', 'medium_weight', 'heavy_weight', 'light_percent', 'medium_percent', 'heavy_percent', 'operating_factor', 'comments'])
    for key in results_dict['sample_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Separation Entry Already Exists'])
    for key in results_dict['separation_hash_exists'].keys():
        writer.writerow(key)
    return response

def separation_loader(results_dict):
    try:
        for key in results_dict['separation_new'].keys():
            try:
                with transaction.atomic():
                    new_separation = Separation.objects.create(id=key[0], obs_sample_id=key[1], separation_type=key[2], apparatus=key[3], SG=key[4], light_weight=key[5], intermediate_weight=key[6], heavy_weight=key[7], light_percent=key[8], intermediate_percent=key[9], heavy_percent=key[10], operating_factor=key[11], comments=key[12])
            except Exception as e:
                print("Separation Error: %s %s" % (e.message, e.args))
                return False
    except Exception as e:
        print("Error: %s %s" % (e.message, e.args))
        return False
    return True

def isolate_loader_prep(upload_file, user):
    start = time.clock()

    isolate_new = OrderedDict({})
    #--- Key = (isolate_table_id, passport_id, location_id, disease_info_id, isolate_id, isolate_name, plant_organ, comments)
    #--- Value = (isolate_table_id)
    passport_new = OrderedDict({})
    #--- Key = (passport_id, collecting_id, people_id, taxonomy_id)
    #--- Value = (passport_id)
    collecting_new = OrderedDict({})
    #--- Key = (collecting_id, user_id, collection_date, collection_method, comments)
    #--- Value = (collecting_id)
    people_new = OrderedDict({})
    #--- Key = (people_id, first_name, last_name, organization, phone, email, comments)
    #--- Value = (people_id)
    taxonomy_new = OrderedDict({})
    #--- Key = (taxonomy_id, genus, species, population, common_name, alias, race, subtaxa)
    #--- Value = (taxonomy_id)
    obs_tracker_new = OrderedDict({})
    #--- Key = (obs_tracker_id, obs_entity_type, experiment_id, field_id, glycerol_stock_id, isolate_id, location_id, maize_sample_id, obs_culture_id, obs_dna_id, obs_env_id, obs_extract_id, obs_microbe_id, obs_plant_id, obs_plate_id, obs_row_id, obs_sample_id, obs_tissue_id, obs_well_id, stock_id, user_id)
    #--- Value = (obs_tracker_id)
    obs_tracker_source_new = OrderedDict({})
    #--- Key = (obs_tracker_source_id, source_obs_id, target_obs_id, relationship)
    #--- Value = (obs_tracker_source_id)

    user_hash_table = loader_db_mirror.user_hash_mirror()
    passport_hash_table = loader_db_mirror.passport_hash_mirror()
    passport_id = loader_db_mirror.passport_id_mirror()
    collecting_hash_table = loader_db_mirror.collecting_hash_mirror()
    collecting_id = loader_db_mirror.collecting_id_mirror()
    taxonomy_hash_table = loader_db_mirror.taxonomy_hash_mirror()
    taxonomy_id = loader_db_mirror.taxonomy_id_mirror()
    people_hash_table = loader_db_mirror.people_hash_mirror()
    people_id = loader_db_mirror.people_id_mirror()
    isolate_hash_table = loader_db_mirror.isolate_hash_mirror()
    isolate_table_id = loader_db_mirror.isolate_table_id_mirror()
    row_id_table = loader_db_mirror.row_id_mirror()
    seed_id_table = loader_db_mirror.seed_id_mirror()
    plant_id_table = loader_db_mirror.plant_id_mirror()
    tissue_id_table = loader_db_mirror.tissue_id_mirror()
    microbe_id_table = loader_db_mirror.microbe_id_mirror()
    culture_id_table = loader_db_mirror.culture_id_mirror()
    plate_id_table = loader_db_mirror.plate_id_mirror()
    dna_id_table = loader_db_mirror.dna_id_mirror()
    well_id_table = loader_db_mirror.well_id_mirror()
    isolate_id_table = loader_db_mirror.isolate_id_mirror()
    obs_tracker_hash_table = loader_db_mirror.obs_tracker_hash_mirror()
    obs_tracker_id = loader_db_mirror.obs_tracker_id_mirror()
    experiment_name_table = loader_db_mirror.experiment_name_mirror()
    field_name_table = loader_db_mirror.field_name_mirror()
    disease_name_table = loader_db_mirror.disease_name_mirror()
    location_name_table = loader_db_mirror.location_name_mirror()
    obs_tracker_source_hash_table = loader_db_mirror.obs_tracker_source_hash_mirror()
    obs_tracker_source_id = loader_db_mirror.obs_tracker_source_id_mirror()
    obs_tracker_stock_id_table = loader_db_mirror.obs_tracker_stock_id_mirror()
    obs_tracker_obs_row_id_table = loader_db_mirror.obs_tracker_obs_row_id_mirror()
    obs_tracker_obs_plant_id_table = loader_db_mirror.obs_tracker_obs_plant_id_mirror()
    obs_tracker_obs_tissue_id_table = loader_db_mirror.obs_tracker_obs_tissue_id_mirror()
    obs_tracker_obs_culture_id_table = loader_db_mirror.obs_tracker_obs_culture_id_mirror()
    obs_tracker_obs_plate_id_table = loader_db_mirror.obs_tracker_obs_plate_id_mirror()
    obs_tracker_obs_microbe_id_table = loader_db_mirror.obs_tracker_obs_microbe_id_mirror()
    obs_tracker_obs_well_id_table = loader_db_mirror.obs_tracker_obs_well_id_mirror()
    obs_tracker_obs_dna_id_table = loader_db_mirror.obs_tracker_obs_dna_id_mirror()

    error_count = 0
    seed_id_error = OrderedDict({})
    row_id_error = OrderedDict({})
    plant_id_error = OrderedDict({})
    tissue_id_error = OrderedDict({})
    culture_id_error = OrderedDict({})
    plate_id_error = OrderedDict({})
    well_id_error = OrderedDict({})
    dna_id_error = OrderedDict({})
    microbe_id_error = OrderedDict({})
    location_name_error = OrderedDict({})
    disease_common_name_error = OrderedDict({})
    field_name_error = OrderedDict({})
    collecting_hash_exists = OrderedDict({})
    people_hash_exists = OrderedDict({})
    taxonomy_hash_exists = OrderedDict({})
    passport_hash_exists = OrderedDict({})
    isolate_hash_exists = OrderedDict({})
    obs_tracker_hash_exists = OrderedDict({})
    obs_tracker_source_hash_exists = OrderedDict({})

    isolate_file = csv.DictReader(codecs.iterdecode(upload_file, 'utf-8'))
    for row in isolate_file:
        isolate_id = row["Isolate ID"]
        experiment_name = row["Experiment Name"]
        isolate_name = row["Isolate Name"]
        plant_organ = row["Plant Organ"]
        isolate_comments = row["Isolate Comments"]
        genus = row["Genus"]
        species = row["Species"]
        population = row["Population"]
        alias = row["Alias"]
        race = row["Race"]
        subtaxa = row["Subtaxa"]
        disease_common_name = row["Disease Common Name"]
        row_id = row["Source Row ID"]
        field_name = row["Source Field Name"]
        seed_id = row["Source Seed ID"]
        plant_id = row["Source Plant ID"]
        tissue_id = row["Source Tissue ID"]
        culture_id = row["Source Culture ID"]
        microbe_id = row["Source Microbe ID"]
        plate_id = row["Source Plate ID"]
        well_id = row["Source Well ID"]
        dna_id = row["Source DNA ID"]
        collection_username = row["Username"]
        collection_date = row["Collection Date"]
        collection_method = row["Method"]
        collection_comments = row["Collection Comments"]
        organization = row["Organization"]
        first_name = row["First Name"]
        last_name = row["Last Name"]
        phone = row["Phone"]
        email = row["Email"]
        source_comments = row["Source Comments"]
        location_name = row["Location Name"]
        user = user

        if seed_id != '':
            seed_id_fix = seed_id + '\r'
            if seed_id in seed_id_table:
                stock_id = seed_id_table[seed_id][0]
            elif seed_id_fix in seed_id_table:
                stock_id = seed_id_table[seed_id_fix][0]
            else:
                seed_id_error[(isolate_id, experiment_name, isolate_name, plant_organ, isolate_comments, genus, species, population, alias, race, subtaxa, row_id, field_name, plant_id, seed_id, tissue_id, microbe_id, well_id, plate_id, dna_id, culture_id, collection_username, collection_date, collection_method, collection_comments, organization, first_name, last_name, phone, email, source_comments, location_name)] = error_count
                error_count = error_count + 1
                stock_id = 1
        else:
            stock_id = 1

        if field_name != '':
            field_name_fix = field_name + '\r'
            if field_name in field_name_table:
                field_id = field_name_table[field_name][0]
            elif field_name_fix in field_name_table:
                field_id = field_name_table[field_name_fix][0]
            else:
                field_name_error[(isolate_id, experiment_name, isolate_name, plant_organ, isolate_comments, genus, species, population, alias, race, subtaxa, row_id, field_name, plant_id, seed_id, tissue_id, microbe_id, well_id, plate_id, dna_id, culture_id, collection_username, collection_date, collection_method, collection_comments, organization, first_name, last_name, phone, email, source_comments, location_name)] = error_count
                error_count = error_count + 1
                field_id = 1
        else:
            field_id = 1

        if location_name != '':
            location_name_fix = location_name + '\r'
            if location_name in location_name_table:
                location_id = location_name_table[location_name][0]
            elif location_name_fix in location_name_table:
                location_id = location_name_table[location_name_fix][0]
            else:
                location_name_error[(isolate_id, experiment_name, isolate_name, plant_organ, isolate_comments, genus, species, population, alias, race, subtaxa, row_id, field_name, plant_id, seed_id, tissue_id, microbe_id, well_id, plate_id, dna_id, culture_id, collection_username, collection_date, collection_method, collection_comments, organization, first_name, last_name, phone, email, source_comments, location_name)] = error_count
                error_count = error_count + 1
                location_id = 1
        else:
            location_id = 1

        if row_id != '':
            row_id_fix = row_id + '\r'
            if row_id in row_id_table:
                obs_row_id = row_id_table[row_id][0]
            elif row_id_fix in row_id_table:
                obs_row_id = row_id_table[row_id_fix][0]
            else:
                row_id_error[(isolate_id, experiment_name, isolate_name, plant_organ, isolate_comments, genus, species, population, alias, race, subtaxa, row_id, field_name, plant_id, seed_id, tissue_id, microbe_id, well_id, plate_id, dna_id, culture_id, collection_username, collection_date, collection_method, collection_comments, organization, first_name, last_name, phone, email, source_comments, location_name)] = error_count
                error_count = error_count + 1
                obs_row_id = 1
        else:
            obs_row_id = 1

        if plant_id != '':
            plant_id_fix = plant_id + '\r'
            if plant_id in plant_id_table:
                obs_plant_id = plant_id_table[plant_id][0]
            elif plant_id_fix in plant_id_table:
                obs_plant_id = plant_id_table[plant_id_fix][0]
            else:
                plant_id_error[(isolate_id, experiment_name, isolate_name, plant_organ, isolate_comments, genus, species, population, alias, race, subtaxa, row_id, field_name, plant_id, seed_id, tissue_id, microbe_id, well_id, plate_id, dna_id, culture_id, collection_username, collection_date, collection_method, collection_comments, organization, first_name, last_name, phone, email, source_comments, location_name)] = error_count
                error_count = error_count + 1
                obs_plant_id = 1
        else:
            obs_plant_id = 1

        if tissue_id != '':
            tissue_id_fix = tissue_id + '\r'
            if tissue_id in tissue_id_table:
                obs_tissue_id = tissue_id_table[tissue_id][0]
            elif tissue_id_fix in tissue_id_table:
                obs_tissue_id = tissue_id_table[tissue_id_fix][0]
            else:
                tissue_id_error[(isolate_id, experiment_name, isolate_name, plant_organ, isolate_comments, genus, species, population, alias, race, subtaxa, row_id, field_name, plant_id, seed_id, tissue_id, microbe_id, well_id, plate_id, dna_id, culture_id, collection_username, collection_date, collection_method, collection_comments, organization, first_name, last_name, phone, email, source_comments, location_name)] = error_count
                error_count = error_count + 1
                obs_tissue_id = 1
        else:
            obs_tissue_id = 1

        if culture_id != '':
            culture_id_fix = culture_id + '\r'
            if culture_id in culture_id_table:
                obs_culture_id = culture_id_table[culture_id][0]
            elif culture_id_fix in culture_id_table:
                obs_culture_id = culture_id_table[culture_id_fix][0]
            else:
                culture_id_error[(isolate_id, experiment_name, isolate_name, plant_organ, isolate_comments, genus, species, population, alias, race, subtaxa, row_id, field_name, plant_id, seed_id, tissue_id, microbe_id, well_id, plate_id, dna_id, culture_id, collection_username, collection_date, collection_method, collection_comments, organization, first_name, last_name, phone, email, source_comments, location_name)] = error_count
                error_count = error_count + 1
                obs_culture_id = 1
        else:
            obs_culture_id = 1

        if plate_id != '':
            plate_id_fix = plate_id + '\r'
            if plate_id in plate_id_table:
                obs_plate_id = plate_id_table[plate_id][0]
            elif plate_id_fix in plate_id_table:
                obs_plate_id = plate_id_table[plate_id_fix][0]
            else:
                plate_id_error[(isolate_id, experiment_name, isolate_name, plant_organ, isolate_comments, genus, species, population, alias, race, subtaxa, row_id, field_name, plant_id, seed_id, tissue_id, microbe_id, well_id, plate_id, dna_id, culture_id, collection_username, collection_date, collection_method, collection_comments, organization, first_name, last_name, phone, email, source_comments, location_name)] = error_count
                error_count = error_count + 1
                obs_plate_id = 1
        else:
            obs_plate_id = 1

        if microbe_id != '':
            microbe_id_fix = microbe_id + '\r'
            if microbe_id in microbe_id_table:
                obs_microbe_id = microbe_id_table[microbe_id][0]
            elif microbe_id_fix in microbe_id_table:
                obs_microbe_id = microbe_id_table[microbe_id_fix][0]
            else:
                microbe_id_error[(isolate_id, experiment_name, isolate_name, plant_organ, isolate_comments, genus, species, population, alias, race, subtaxa, row_id, field_name, plant_id, seed_id, tissue_id, microbe_id, well_id, plate_id, dna_id, culture_id, collection_username, collection_date, collection_method, collection_comments, organization, first_name, last_name, phone, email, source_comments, location_name)] = error_count
                error_count = error_count + 1
                obs_microbe_id = 1
        else:
            obs_microbe_id = 1

        if well_id != '':
            well_id_fix = well_id + '\r'
            if well_id in well_id_table:
                obs_well_id = well_id_table[well_id][0]
            elif well_id_fix in well_id_table:
                obs_well_id = well_id_table[well_id_fix][0]
            else:
                well_id_error[(isolate_id, experiment_name, isolate_name, plant_organ, isolate_comments, genus, species, population, alias, race, subtaxa, row_id, field_name, plant_id, seed_id, tissue_id, microbe_id, well_id, plate_id, dna_id, culture_id, collection_username, collection_date, collection_method, collection_comments, organization, first_name, last_name, phone, email, source_comments, location_name)] = error_count
                error_count = error_count + 1
                obs_well_id = 1
        else:
            obs_well_id = 1

        if dna_id != '':
            dna_id_fix = dna_id + '\r'
            if dna_id in dna_id_table:
                obs_dna_id = dna_id_table[dna_id][0]
            elif dna_id_fix in dna_id_table:
                obs_dna_id = dna_id_table[dna_id_fix][0]
            else:
                dna_id_error[(isolate_id, experiment_name, isolate_name, plant_organ, isolate_comments, genus, species, population, alias, race, subtaxa, row_id, field_name, plant_id, seed_id, tissue_id, microbe_id, well_id, plate_id, dna_id, culture_id, collection_username, collection_date, collection_method, collection_comments, organization, first_name, last_name, phone, email, source_comments, location_name)] = error_count
                error_count = error_count + 1
                obs_dna_id = 1
        else:
            obs_dna_id = 1

        if disease_common_name != '':
            disease_common_name_fix = disease_common_name + '\r'
            if disease_common_name in disease_name_table:
                disease_info_id = disease_name_table[disease_common_name][0]
            elif disease_common_name_fix in disease_name_table:
                disease_info_id = disease_name_table[disease_common_name_fix][0]
            else:
                disease_common_name_error[(isolate_id, experiment_name, isolate_name, plant_organ, isolate_comments, genus, species, population, alias, race, subtaxa, row_id, field_name, plant_id, seed_id, tissue_id, microbe_id, well_id, plate_id, dna_id, culture_id, collection_username, collection_date, collection_method, collection_comments, organization, first_name, last_name, phone, email, source_comments, location_name)] = error_count
                error_count = error_count + 1
                disease_info_id = 1
        else:
            disease_info_id = 1

        if collection_username == '':
            collection_user_id = user_hash_table['unknown_person']
        else:
            try:
                collection_user_id = user_hash_table[collection_username]
            except KeyError:
                collection_user_error[(isolate_id, experiment_name, isolate_name, plant_organ, isolate_comments, genus, species, population, alias, race, subtaxa, row_id, field_name, plant_id, seed_id, tissue_id, microbe_id, well_id, plate_id, dna_id, culture_id, collection_username, collection_date, collection_method, collection_comments, organization, first_name, last_name, phone, email, source_comments, location_name, building_name, room, shelf, column, box_name, location_comments)] = error_count
                error_count = error_count + 1
                collection_user_id = user_hash_table['unknown_person']

        collecting_hash = str(collection_user_id) + collection_date + collection_method + collection_comments
        collecting_hash_fix = collecting_hash + '\r'
        if collecting_hash not in collecting_hash_table and collecting_hash_fix not in collecting_hash_table:
            collecting_hash_table[collecting_hash] = collecting_id
            collecting_new[(collecting_id, collection_user_id, collection_date, collection_method, collection_comments)] = collecting_id
            collecting_id = collecting_id + 1
        else:
            collecting_hash_exists[(collection_user_id, collection_date, collection_method, collection_comments)] = collecting_id

        if collecting_hash in collecting_hash_table:
            temp_collecting_id = collecting_hash_table[collecting_hash]
        elif collecting_hash_fix in collecting_hash_table:
            temp_collecting_id = collecting_hash_table[collecting_hash_fix]
        else:
            temp_collecting_id = 1
            error_count = error_count + 1

        taxonomy_hash = genus + species + population + 'Isolate' + alias + race + subtaxa
        taxonomy_hash_fix = taxonomy_hash + '\r'
        if taxonomy_hash not in taxonomy_hash_table and taxonomy_hash_fix not in taxonomy_hash_table:
            taxonomy_hash_table[taxonomy_hash] = taxonomy_id
            taxonomy_new[(taxonomy_id, genus, species, population, 'Isolate', alias, race, subtaxa)] = taxonomy_id
            taxonomy_id = taxonomy_id + 1
        else:
            taxonomy_hash_exists[(genus, species, population, 'Isolate', alias, race, subtaxa)] = taxonomy_id

        if taxonomy_hash in taxonomy_hash_table:
            temp_taxonomy_id = taxonomy_hash_table[taxonomy_hash]
        elif taxonomy_hash_fix in taxonomy_hash_table:
            temp_taxonomy_id = taxonomy_hash_table[taxonomy_hash_fix]
        else:
            temp_taxonomy_id = 1
            error_count = error_count + 1

        people_hash = first_name + last_name + organization + phone + email + source_comments
        people_hash_fix = people_hash + '\r'
        if people_hash not in people_hash_table and people_hash_fix not in people_hash_table:
            people_hash_table[people_hash] = people_id
            people_new[(people_id, first_name, last_name, organization, phone, email, source_comments)] = people_id
            people_id = people_id + 1
        else:
            people_hash_exists[(first_name, last_name, organization, phone, email, source_comments)] = people_id

        if people_hash in people_hash_table:
            temp_people_id = people_hash_table[people_hash]
        elif people_hash_fix in people_hash_table:
            temp_people_id = people_hash_table[people_hash_fix]
        else:
            temp_people_id = 1
            error_count = error_count + 1

        passport_hash = str(temp_collecting_id) + str(temp_people_id) + str(temp_taxonomy_id)
        passport_hash_fix = passport_hash + '\r'
        if passport_hash not in passport_hash_table and passport_hash_fix not in passport_hash_table:
            passport_hash_table[passport_hash] = passport_id
            passport_new[(passport_id, temp_collecting_id, temp_people_id, temp_taxonomy_id)] = passport_id
            passport_id = passport_id + 1
        else:
            passport_hash_exists[(temp_collecting_id, temp_people_id, temp_taxonomy_id)] = passport_id

        if passport_hash in passport_hash_table:
            temp_passport_id = passport_hash_table[passport_hash]
        elif passport_hash_fix in passport_hash_table:
            temp_passport_id = passport_hash_table[passport_hash_fix]
        else:
            temp_passport_id = 1
            error_count = error_count + 1

        isolate_hash = str(temp_passport_id) + str(location_id) + str(disease_info_id) + isolate_id + isolate_name + plant_organ + isolate_comments
        isolate_hash_fix = isolate_hash + '\r'
        if isolate_id not in isolate_id_table and isolate_id + '\r' not in isolate_id_table:
            if isolate_hash not in isolate_hash_table and isolate_hash_fix not in isolate_hash_table:
                isolate_hash_table[isolate_hash] = isolate_table_id
                isolate_new[(isolate_table_id, temp_passport_id, location_id, disease_info_id, isolate_id, isolate_name, plant_organ, isolate_comments)] = isolate_table_id
                isolate_id_table[isolate_id] = (isolate_table_id, temp_passport_id, location_id, disease_info_id, isolate_id, isolate_name, plant_organ, isolate_comments)
                isolate_table_id = isolate_table_id + 1
            else:
                isolate_hash_exists[(temp_passport_id, location_id, disease_info_id, isolate_id, isolate_name, plant_organ, isolate_comments)] = isolate_table_id
        else:
            isolate_hash_exists[(temp_passport_id, location_id, disease_info_id, isolate_id, isolate_name, plant_organ, isolate_comments)] = isolate_table_id

        if isolate_id in isolate_id_table:
            temp_isolate_id = isolate_id_table[isolate_id][0]
        elif isolate_id + '\r' in isolate_id_table:
            temp_isolate_id = isolate_id_table[isolate_id + '\r'][0]
        elif isolate_hash in isolate_hash_table:
            temp_isolate_id = isolate_hash_table[isolate_hash]
        elif isolate_hash_fix in isolate_hash_table:
            temp_isolate_id = isolate_hash_table[isolate_hash_fix]
        else:
            temp_isolate_id = 1
            error_count = error_count + 1

        obs_tracker_isolate_hash = 'isolate' + str(1) + str(field_id) + str(1) + str(temp_isolate_id) + str(location_id) + str(1) + str(obs_culture_id) + str(obs_dna_id) + str(1) + str(1) + str(obs_microbe_id) + str(obs_plant_id) + str(obs_plate_id) + str(obs_row_id) + str(1) + str(obs_tissue_id) + str(obs_well_id) + str(stock_id) + str(user_hash_table[user.username])
        obs_tracker_isolate_hash_fix = obs_tracker_isolate_hash + '\r'
        if obs_tracker_isolate_hash not in obs_tracker_hash_table and obs_tracker_isolate_hash_fix not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_isolate_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'isolate', 1, field_id, 1, temp_isolate_id, location_id, 1, obs_culture_id, obs_dna_id, 1, 1, obs_microbe_id, obs_plant_id, obs_plate_id, obs_row_id, 1, obs_tissue_id, obs_well_id, stock_id, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1
        else:
            obs_tracker_hash_exists[('isolate', 1, field_id, 1, temp_isolate_id, location_id, 1, obs_culture_id, obs_dna_id, 1, 1, obs_microbe_id, obs_plant_id, obs_plate_id, obs_row_id, 1, obs_tissue_id, obs_well_id, stock_id, user_hash_table[user.username])] = obs_tracker_id

        if stock_id != 1:
            obs_tracker_source_stock_hash = str(obs_tracker_stock_id_table[stock_id][0]) + str(obs_tracker_hash_table[obs_tracker_isolate_hash]) + 'isolate_from_stock'
            if obs_tracker_source_stock_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_stock_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_stock_id_table[stock_id][0], obs_tracker_hash_table[obs_tracker_isolate_hash], 'isolate_from_stock')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_stock_id_table[stock_id][0], obs_tracker_hash_table[obs_tracker_isolate_hash], 'isolate_from_stock')] = obs_tracker_source_id

        if obs_row_id != 1:
            obs_tracker_source_row_hash = str(obs_tracker_obs_row_id_table[obs_row_id][0]) + str(obs_tracker_hash_table[obs_tracker_isolate_hash]) + 'isolate_from_row'
            if obs_tracker_source_row_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_row_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_row_id_table[obs_row_id][0], obs_tracker_hash_table[obs_tracker_isolate_hash], 'isolate_from_row')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_row_id_table[obs_row_id][0], obs_tracker_hash_table[obs_tracker_isolate_hash], 'isolate_from_row')] = obs_tracker_source_id

        if obs_plant_id != 1:
            obs_tracker_source_plant_hash = str(obs_tracker_obs_plant_id_table[obs_plant_id][0]) + str(obs_tracker_hash_table[obs_tracker_isolate_hash]) + 'isolate_from_plant'
            if obs_tracker_source_plant_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_plant_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_plant_id_table[obs_plant_id][0], obs_tracker_hash_table[obs_tracker_isolate_hash], 'isolate_from_plant')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_plant_id_table[obs_plant_id][0], obs_tracker_hash_table[obs_tracker_isolate_hash], 'isolate_from_plant')] = obs_tracker_source_id

        if obs_tissue_id != 1:
            obs_tracker_source_tissue_hash = str(obs_tracker_obs_tissue_id_table[obs_tissue_id][0]) + str(obs_tracker_hash_table[obs_tracker_isolate_hash]) + 'isolate_from_tissue'
            if obs_tracker_source_tissue_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_tissue_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_tissue_id_table[obs_tissue_id][0], obs_tracker_hash_table[obs_tracker_isolate_hash], 'isolate_from_tissue')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_tissue_id_table[obs_tissue_id][0], obs_tracker_hash_table[obs_tracker_isolate_hash], 'isolate_from_tissue')] = obs_tracker_source_id

        if obs_culture_id != 1:
            obs_tracker_source_culture_hash = str(obs_tracker_obs_culture_id_table[obs_culture_id][0]) + str(obs_tracker_hash_table[obs_tracker_isolate_hash]) + 'isolate_from_culture'
            if obs_tracker_source_culture_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_culture_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_culture_id_table[obs_culture_id][0], obs_tracker_hash_table[obs_tracker_isolate_hash], 'isolate_from_culture')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_culture_id_table[obs_culture_id][0], obs_tracker_hash_table[obs_tracker_isolate_hash], 'isolate_from_culture')] = obs_tracker_source_id

        if obs_microbe_id != 1:
            obs_tracker_source_microbe_hash = str(obs_tracker_obs_microbe_id_table[obs_microbe_id][0]) + str(obs_tracker_hash_table[obs_tracker_isolate_hash]) + 'isolate_from_microbe'
            if obs_tracker_source_microbe_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_microbe_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_microbe_id_table[obs_microbe_id][0], obs_tracker_hash_table[obs_tracker_isolate_hash], 'isolate_from_microbe')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_microbe_id_table[obs_microbe_id][0], obs_tracker_hash_table[obs_tracker_isolate_hash], 'isolate_from_microbe')] = obs_tracker_source_id

        if obs_plate_id != 1:
            obs_tracker_source_plate_hash = str(obs_tracker_obs_plate_id_table[obs_plate_id][0]) + str(obs_tracker_hash_table[obs_tracker_isolate_hash]) + 'isolate_from_plate'
            if obs_tracker_source_plate_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_plate_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_plate_id_table[obs_plate_id][0], obs_tracker_hash_table[obs_tracker_isolate_hash], 'isolate_from_plate')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_plate_id_table[obs_plate_id][0], obs_tracker_hash_table[obs_tracker_isolate_hash], 'isolate_from_plate')] = obs_tracker_source_id

        if obs_well_id != 1:
            obs_tracker_source_well_hash = str(obs_tracker_obs_well_id_table[obs_well_id][0]) + str(obs_tracker_hash_table[obs_tracker_isolate_hash]) + 'isolate_from_well'
            if obs_tracker_source_well_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_well_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_well_id_table[obs_well_id][0], obs_tracker_hash_table[obs_tracker_isolate_hash], 'isolate_from_well')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_well_id_table[obs_well_id][0], obs_tracker_hash_table[obs_tracker_isolate_hash], 'isolate_from_well')] = obs_tracker_source_id

        if obs_dna_id != 1:
            obs_tracker_source_dna_hash = str(obs_tracker_obs_dna_id_table[obs_dna_id][0]) + str(obs_tracker_hash_table[obs_tracker_isolate_hash]) + 'isolate_from_dna'
            if obs_tracker_source_dna_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_dna_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_dna_id_table[obs_dna_id][0], obs_tracker_hash_table[obs_tracker_isolate_hash], 'isolate_from_dna')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_dna_id_table[obs_dna_id][0], obs_tracker_hash_table[obs_tracker_isolate_hash], 'isolate_from_dna')] = obs_tracker_source_id

        obs_tracker_exp_hash = 'experiment' + str(experiment_name_table[experiment_name][0]) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(user_hash_table[user.username])
        if obs_tracker_exp_hash not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_exp_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'experiment', experiment_name_table[experiment_name][0], 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1

        obs_tracker_source_hash = str(obs_tracker_hash_table[obs_tracker_exp_hash]) + str(obs_tracker_hash_table[obs_tracker_isolate_hash]) + 'isolate_used_in_experiment'
        if obs_tracker_source_hash not in obs_tracker_source_hash_table:
            obs_tracker_source_hash_table[obs_tracker_source_hash] = obs_tracker_source_id
            obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], obs_tracker_hash_table[obs_tracker_isolate_hash], 'isolate_used_in_experiment')] = obs_tracker_source_id
            obs_tracker_source_id = obs_tracker_source_id + 1
        else:
            obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], obs_tracker_hash_table[obs_tracker_isolate_hash], 'isolate_used_in_experiment')] = obs_tracker_source_id

    end = time.clock()
    stats = {}
    stats[("Time: %s" % (end-start), "Errors: %s" % (error_count))] = error_count

    results_dict = {}
    results_dict['isolate_new'] = isolate_new
    results_dict['passport_new'] = passport_new
    results_dict['collecting_new'] = collecting_new
    results_dict['people_new'] = people_new
    results_dict['taxonomy_new'] = taxonomy_new
    results_dict['obs_tracker_new'] = obs_tracker_new
    results_dict['obs_tracker_source_new'] = obs_tracker_source_new
    results_dict['field_name_error'] = field_name_error
    results_dict['disease_common_name_error'] = disease_common_name_error
    results_dict['seed_id_error'] = seed_id_error
    results_dict['row_id_error'] = row_id_error
    results_dict['plant_id_error'] = plant_id_error
    results_dict['tissue_id_error'] = tissue_id_error
    results_dict['culture_id_error'] = culture_id_error
    results_dict['plate_id_error'] = plate_id_error
    results_dict['microbe_id_error'] = microbe_id_error
    results_dict['dna_id_error'] = dna_id_error
    results_dict['well_id_error'] = well_id_error
    results_dict['location_name_error'] = location_name_error
    results_dict['collecting_hash_exists'] = collecting_hash_exists
    results_dict['people_hash_exists'] = people_hash_exists
    results_dict['taxonomy_hash_exists'] = taxonomy_hash_exists
    results_dict['passport_hash_exists'] = passport_hash_exists
    results_dict['isolate_hash_exists'] = isolate_hash_exists
    results_dict['obs_tracker_hash_exists'] = obs_tracker_hash_exists
    results_dict['obs_tracker_source_hash_exists'] = obs_tracker_source_hash_exists
    results_dict['stats'] = stats
    return results_dict

def isolate_loader_prep_output(results_dict, new_upload_exp, template_type):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s_%s_prep.csv"' % (new_upload_exp, template_type)
    writer = csv.writer(response)
    writer.writerow(['Stats'])
    writer.writerow([''])
    for key in results_dict['stats'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Isolate Table'])
    writer.writerow(['isolate_table_id', 'passport_id', 'location_id', 'disease_info_id', 'isolate_id', 'isolate_name', 'plant_organ', 'comments'])
    for key in results_dict['isolate_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Collecting Table'])
    writer.writerow(['collecting_id', 'user_id', 'collection_date', 'collection_method', 'comments'])
    for key in results_dict['collecting_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New People Table'])
    writer.writerow(['people_id', 'first_name', 'last_name', 'organization', 'phone', 'email', 'comments'])
    for key in results_dict['people_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Taxonomy Table'])
    writer.writerow(['taxonomy_id', 'genus', 'species', 'population', 'common_name', 'alias', 'race', 'subtaxa'])
    for key in results_dict['taxonomy_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Passport Table'])
    writer.writerow(['passport_id', 'collecting_id', 'people_id', 'taxonomy_id'])
    for key in results_dict['passport_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTracker Table'])
    writer.writerow(['obs_tracker_id', 'obs_entity_type', 'experiment_id', 'field_id', 'glycerol_stock_id', 'isolate_id', 'location_id', 'maize_sample_id', 'obs_culture_id', 'obs_dna_id', 'obs_env_id', 'obs_extract_id', 'obs_microbe_id', 'obs_plant_id', 'obs_plate_id', 'obs_row_id', 'obs_sample_id', 'obs_tissue_id', 'obs_well_id', 'stock_id', 'user_id'])
    for key in results_dict['obs_tracker_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTrackerSource Table'])
    writer.writerow(['obs_tracker_source_id', 'source_obs_id', 'target_obs_id', 'relationship'])
    for key in results_dict['obs_tracker_source_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['---------------------------------------------------------------------------------------------------'])
    writer.writerow([''])
    writer.writerow(['Seed ID Errors'])
    writer.writerow(['isolate_id', 'experiment_name', 'isolate_name', 'plant_organ', 'isolate_comments', 'genus', 'species', 'population', 'alias', 'race', 'subtaxa', 'source_row_id', 'source_field_name', 'source_plant_id', 'source_seed_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_plate_id', 'source_dna_id', 'source_culture_id', 'collection_username', 'collection_date', 'collection_method', 'collection_comments', 'organization', 'firat_name', 'last_name', 'phone', 'email', 'source_comments', 'location_name'])
    for key in results_dict['seed_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Row ID Errors'])
    writer.writerow(['isolate_id', 'experiment_name', 'isolate_name', 'plant_organ', 'isolate_comments', 'genus', 'species', 'population', 'alias', 'race', 'subtaxa', 'source_row_id', 'source_field_name', 'source_plant_id', 'source_seed_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_plate_id', 'source_dna_id', 'source_culture_id', 'collection_username', 'collection_date', 'collection_method', 'collection_comments', 'organization', 'firat_name', 'last_name', 'phone', 'email', 'source_comments', 'location_name'])
    for key in results_dict['row_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Plant ID Errors'])
    writer.writerow(['isolate_id', 'experiment_name', 'isolate_name', 'plant_organ', 'isolate_comments', 'genus', 'species', 'population', 'alias', 'race', 'subtaxa', 'source_row_id', 'source_field_name', 'source_plant_id', 'source_seed_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_plate_id', 'source_dna_id', 'source_culture_id', 'collection_username', 'collection_date', 'collection_method', 'collection_comments', 'organization', 'firat_name', 'last_name', 'phone', 'email', 'source_comments', 'location_name'])
    for key in results_dict['plant_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Tissue ID Errors'])
    writer.writerow(['isolate_id', 'experiment_name', 'isolate_name', 'plant_organ', 'isolate_comments', 'genus', 'species', 'population', 'alias', 'race', 'subtaxa', 'source_row_id', 'source_field_name', 'source_plant_id', 'source_seed_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_plate_id', 'source_dna_id', 'source_culture_id', 'collection_username', 'collection_date', 'collection_method', 'collection_comments', 'organization', 'firat_name', 'last_name', 'phone', 'email', 'source_comments', 'location_name'])
    for key in results_dict['tissue_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Culture ID Errors'])
    writer.writerow(['isolate_id', 'experiment_name', 'isolate_name', 'plant_organ', 'isolate_comments', 'genus', 'species', 'population', 'alias', 'race', 'subtaxa', 'source_row_id', 'source_field_name', 'source_plant_id', 'source_seed_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_plate_id', 'source_dna_id', 'source_culture_id', 'collection_username', 'collection_date', 'collection_method', 'collection_comments', 'organization', 'firat_name', 'last_name', 'phone', 'email', 'source_comments', 'location_name'])
    for key in results_dict['culture_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Microbe ID Errors'])
    writer.writerow(['isolate_id', 'experiment_name', 'isolate_name', 'plant_organ', 'isolate_comments', 'genus', 'species', 'population', 'alias', 'race', 'subtaxa', 'source_row_id', 'source_field_name', 'source_plant_id', 'source_seed_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_plate_id', 'source_dna_id', 'source_culture_id', 'collection_username', 'collection_date', 'collection_method', 'collection_comments', 'organization', 'firat_name', 'last_name', 'phone', 'email', 'source_comments', 'location_name'])
    for key in results_dict['microbe_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Plate ID Errors'])
    writer.writerow(['isolate_id', 'experiment_name', 'isolate_name', 'plant_organ', 'isolate_comments', 'genus', 'species', 'population', 'alias', 'race', 'subtaxa', 'source_row_id', 'source_field_name', 'source_plant_id', 'source_seed_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_plate_id', 'source_dna_id', 'source_culture_id', 'collection_username', 'collection_date', 'collection_method', 'collection_comments', 'organization', 'firat_name', 'last_name', 'phone', 'email', 'source_comments', 'location_name'])
    for key in results_dict['plate_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Well ID Errors'])
    writer.writerow(['isolate_id', 'experiment_name', 'isolate_name', 'plant_organ', 'isolate_comments', 'genus', 'species', 'population', 'alias', 'race', 'subtaxa', 'source_row_id', 'source_field_name', 'source_plant_id', 'source_seed_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_plate_id', 'source_dna_id', 'source_culture_id', 'collection_username', 'collection_date', 'collection_method', 'collection_comments', 'organization', 'firat_name', 'last_name', 'phone', 'email', 'source_comments', 'location_name'])
    for key in results_dict['well_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['DNA ID Errors'])
    writer.writerow(['isolate_id', 'experiment_name', 'isolate_name', 'plant_organ', 'isolate_comments', 'genus', 'species', 'population', 'alias', 'race', 'subtaxa', 'source_row_id', 'source_field_name', 'source_plant_id', 'source_seed_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_plate_id', 'source_dna_id', 'source_culture_id', 'collection_username', 'collection_date', 'collection_method', 'collection_comments', 'organization', 'firat_name', 'last_name', 'phone', 'email', 'source_comments', 'location_name'])
    for key in results_dict['dna_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Field Name Errors'])
    writer.writerow(['isolate_id', 'experiment_name', 'isolate_name', 'plant_organ', 'isolate_comments', 'genus', 'species', 'population', 'alias', 'race', 'subtaxa', 'source_row_id', 'source_field_name', 'source_plant_id', 'source_seed_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_plate_id', 'source_dna_id', 'source_culture_id', 'collection_username', 'collection_date', 'collection_method', 'collection_comments', 'organization', 'firat_name', 'last_name', 'phone', 'email', 'source_comments', 'location_name'])
    for key in results_dict['field_name_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Location Name Errors'])
    writer.writerow(['isolate_id', 'experiment_name', 'isolate_name', 'plant_organ', 'isolate_comments', 'genus', 'species', 'population', 'alias', 'race', 'subtaxa', 'source_row_id', 'source_field_name', 'source_plant_id', 'source_seed_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_plate_id', 'source_dna_id', 'source_culture_id', 'collection_username', 'collection_date', 'collection_method', 'collection_comments', 'organization', 'firat_name', 'last_name', 'phone', 'email', 'source_comments', 'location_name'])
    for key in results_dict['location_name_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Disease Common Name Errors'])
    writer.writerow(['isolate_id', 'experiment_name', 'isolate_name', 'plant_organ', 'isolate_comments', 'genus', 'species', 'population', 'alias', 'race', 'subtaxa', 'source_row_id', 'source_field_name', 'source_plant_id', 'source_seed_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_plate_id', 'source_dna_id', 'source_culture_id', 'collection_username', 'collection_date', 'collection_method', 'collection_comments', 'organization', 'firat_name', 'last_name', 'phone', 'email', 'source_comments', 'location_name'])
    for key in results_dict['disease_common_name_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Collecting Entries Already Exist'])
    for key in results_dict['collecting_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['People Entries Already Exist'])
    for key in results_dict['people_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Taxonomy Entries Already Exist'])
    for key in results_dict['taxonomy_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Passport Entries Already Exist'])
    for key in results_dict['passport_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Isolate Entry Already Exists'])
    for key in results_dict['isolate_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTracker Entry Already Exists'])
    for key in results_dict['obs_tracker_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTrackerSource Entry Already Exists'])
    for key in results_dict['obs_tracker_source_hash_exists'].keys():
        writer.writerow(key)
    return response

def isolate_loader(results_dict):
    try:
        for key in results_dict['collecting_new'].keys():
            try:
                with transaction.atomic():
                    new_isolate = Collecting.objects.create(id=key[0], user_id=key[1], collection_date=key[2], collection_method=key[3], comments=key[4])
            except Exception as e:
                print("Collecting Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['people_new'].keys():
            try:
                with transaction.atomic():
                    new_isolate = People.objects.create(id=key[0], first_name=key[1], last_name=key[2], organization=key[3], phone=key[4], email=key[5], comments=key[6])
            except Exception as e:
                print("People Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['taxonomy_new'].keys():
            try:
                with transaction.atomic():
                    new_isolate = Taxonomy.objects.create(id=key[0], genus=key[1], species=key[2], population=key[3], common_name=key[4], alias=key[5], race=key[6], subtaxa=key[7])
            except Exception as e:
                print("Taxonomy Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['passport_new'].keys():
            try:
                with transaction.atomic():
                    new_isolate = Passport.objects.create(id=key[0], collecting_id=key[1], people_id=key[2], taxonomy_id=key[3])
            except Exception as e:
                print("Passport Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['isolate_new'].keys():
            try:
                with transaction.atomic():
                    new_isolate = Isolate.objects.create(id=key[0], passport_id=key[1], location_id=key[2], disease_info_id=key[3], isolate_id=key[4], isolate_name=key[5], plant_organ=key[6], comments=key[7])
            except Exception as e:
                print("Isolate Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = ObsTracker.objects.create(id=key[0], obs_entity_type=key[1], experiment_id=key[2], field_id=key[3], glycerol_stock_id=key[4], isolate_id=key[5], location_id=key[6], maize_sample_id=key[7], obs_culture_id=key[8], obs_dna_id=key[9], obs_env_id=key[10], obs_extract_id=key[11], obs_microbe_id=key[12], obs_plant_id=key[13], obs_plate_id=key[14], obs_row_id=key[15], obs_sample_id=key[16], obs_tissue_id=key[17], obs_well_id=key[18], stock_id=key[19], user_id=key[20])
            except Exception as e:
                print("ObsTracker Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_source_new'].keys():
            try:
                with transaction.atomic():
                    new_obstrackersource = ObsTrackerSource.objects.create(id=key[0], source_obs_id=key[1], target_obs_id=key[2], relationship=key[3])
            except Exception as e:
                print("ObsTrackerSource Error: %s %s" % (e.message, e.args))
                return False
    except Exception as e:
        print("Error: %s %s" % (e.message, e.args))
        return False
    return True

def glycerol_stock_loader_prep(upload_file, user):
    start = time.clock()

    glycerol_stock_new = OrderedDict({})
    #--- Key = (id, glycerol_stock_id, stock_date, extract_color, organism, comments)
    #--- Value = (id)
    obs_tracker_new = OrderedDict({})
    #--- Key = (obs_tracker_id, obs_entity_type, experiment_id, field_id, glycerol_stock_id, isolate_id, location_id, maize_sample_id, obs_culture_id, obs_dna_id, obs_env_id, obs_extract_id, obs_microbe_id, obs_plant_id, obs_plate_id, obs_row_id, obs_sample_id, obs_tissue_id, obs_well_id, stock_id, user_id)
    #--- Value = (obs_tracker_id)
    obs_tracker_source_new = OrderedDict({})
    #--- Key = (obs_tracker_source_id, source_obs_id, target_obs_id, relationship)
    #--- Value = (obs_tracker_source_id)

    user_hash_table = loader_db_mirror.user_hash_mirror()
    glycerol_stock_hash_table = loader_db_mirror.glycerol_stock_hash_mirror()
    glycerol_stock_table_id = loader_db_mirror.glycerol_stock_table_id_mirror()
    glycerol_stock_id_table = loader_db_mirror.glycerol_stock_id_mirror()
    row_id_table = loader_db_mirror.row_id_mirror()
    seed_id_table = loader_db_mirror.seed_id_mirror()
    plant_id_table = loader_db_mirror.plant_id_mirror()
    tissue_id_table = loader_db_mirror.tissue_id_mirror()
    microbe_id_table = loader_db_mirror.microbe_id_mirror()
    culture_id_table = loader_db_mirror.culture_id_mirror()
    plate_id_table = loader_db_mirror.plate_id_mirror()
    dna_id_table = loader_db_mirror.dna_id_mirror()
    well_id_table = loader_db_mirror.well_id_mirror()
    isolate_id_table = loader_db_mirror.isolate_id_mirror()
    obs_tracker_hash_table = loader_db_mirror.obs_tracker_hash_mirror()
    obs_tracker_id = loader_db_mirror.obs_tracker_id_mirror()
    experiment_name_table = loader_db_mirror.experiment_name_mirror()
    location_name_table = loader_db_mirror.location_name_mirror()
    field_name_table = loader_db_mirror.field_name_mirror()
    obs_tracker_source_hash_table = loader_db_mirror.obs_tracker_source_hash_mirror()
    obs_tracker_source_id = loader_db_mirror.obs_tracker_source_id_mirror()
    obs_tracker_stock_id_table = loader_db_mirror.obs_tracker_stock_id_mirror()
    obs_tracker_obs_row_id_table = loader_db_mirror.obs_tracker_obs_row_id_mirror()
    obs_tracker_obs_plant_id_table = loader_db_mirror.obs_tracker_obs_plant_id_mirror()
    obs_tracker_obs_tissue_id_table = loader_db_mirror.obs_tracker_obs_tissue_id_mirror()
    obs_tracker_obs_culture_id_table = loader_db_mirror.obs_tracker_obs_culture_id_mirror()
    obs_tracker_obs_plate_id_table = loader_db_mirror.obs_tracker_obs_plate_id_mirror()
    obs_tracker_obs_microbe_id_table = loader_db_mirror.obs_tracker_obs_microbe_id_mirror()
    obs_tracker_obs_well_id_table = loader_db_mirror.obs_tracker_obs_well_id_mirror()
    obs_tracker_obs_dna_id_table = loader_db_mirror.obs_tracker_obs_dna_id_mirror()
    obs_tracker_isolate_table_id_table = loader_db_mirror.obs_tracker_isolate_table_id_mirror()

    error_count = 0
    seed_id_error = OrderedDict({})
    row_id_error = OrderedDict({})
    plant_id_error = OrderedDict({})
    tissue_id_error = OrderedDict({})
    culture_id_error = OrderedDict({})
    plate_id_error = OrderedDict({})
    well_id_error = OrderedDict({})
    dna_id_error = OrderedDict({})
    microbe_id_error = OrderedDict({})
    sample_id_error = OrderedDict({})
    isolate_id_error = OrderedDict({})
    field_name_error = OrderedDict({})
    location_name_error = OrderedDict({})
    glycerol_stock_hash_exists = OrderedDict({})
    obs_tracker_hash_exists = OrderedDict({})

    glycerol_file = csv.DictReader(codecs.iterdecode(upload_file, 'utf-8'))
    for row in glycerol_file:
        glycerol_stock_id = row["Glycerol Stock ID"]
        experiment_name = row["Experiment Name"]
        location_name = row["Location Name"]
        date = row["Date"]
        extract_color = row["Extract Color"]
        organism = row["Organism"]
        comments = row["Glycerol Stock Comments"]
        field_name = row["Source Field Name"]
        row_id = row["Source Row ID"]
        sample_id = row["Source Sample ID"]
        isolate_id = row["Source Isolate ID"]
        seed_id = row["Source Seed ID"]
        plant_id = row["Source Plant ID"]
        tissue_id = row["Source Tissue ID"]
        culture_id = row["Source Culture ID"]
        microbe_id = row["Source Microbe ID"]
        plate_id = row["Source Plate ID"]
        well_id = row["Source Well ID"]
        dna_id = row["Source DNA ID"]
        user = user

        if seed_id != '':
            seed_id_fix = seed_id + '\r'
            if seed_id in seed_id_table:
                stock_id = seed_id_table[seed_id][0]
            elif seed_id_fix in seed_id_table:
                stock_id = seed_id_table[seed_id_fix][0]
            else:
                seed_id_error[(glycerol_stock_id, experiment_name, location_name, date, extract_color, organism, comments, field_name, row_id, plant_id, seed_id, tissue_id, microbe_id, well_id, plate_id, dna_id, culture_id, sample_id, isolate_id)] = error_count
                error_count = error_count + 1
                stock_id = 1
        else:
            stock_id = 1

        if field_name != '':
            field_name_fix = field_name + '\r'
            if field_name in field_name_table:
                field_id = field_name_table[field_name][0]
            elif field_name_fix in field_name_table:
                field_id = field_name_table[field_name_fix][0]
            else:
                field_name_error[(glycerol_stock_id, experiment_name, location_name, date, extract_color, organism, comments, field_name, row_id, plant_id, seed_id, tissue_id, microbe_id, well_id, plate_id, dna_id, culture_id, sample_id, isolate_id)] = error_count
                error_count = error_count + 1
                field_id = 1
        else:
            field_id = 1

        if row_id != '':
            row_id_fix = row_id + '\r'
            if row_id in row_id_table:
                obs_row_id = row_id_table[row_id][0]
            elif row_id_fix in row_id_table:
                obs_row_id = row_id_table[row_id_fix][0]
            else:
                row_id_error[(glycerol_stock_id, experiment_name, location_name, date, extract_color, organism, comments, field_name, row_id, plant_id, seed_id, tissue_id, microbe_id, well_id, plate_id, dna_id, culture_id, sample_id, isolate_id)] = error_count
                error_count = error_count + 1
                obs_row_id = 1
        else:
            obs_row_id = 1

        if plant_id != '':
            plant_id_fix = plant_id + '\r'
            if plant_id in plant_id_table:
                obs_plant_id = plant_id_table[plant_id][0]
            elif plant_id_fix in plant_id_table:
                obs_plant_id = plant_id_table[plant_id_fix][0]
            else:
                plant_id_error[(glycerol_stock_id, experiment_name, location_name, date, extract_color, organism, comments, field_name, row_id, plant_id, seed_id, tissue_id, microbe_id, well_id, plate_id, dna_id, culture_id, sample_id, isolate_id)] = error_count
                error_count = error_count + 1
                obs_plant_id = 1
        else:
            obs_plant_id = 1

        if tissue_id != '':
            tissue_id_fix = tissue_id + '\r'
            if tissue_id in tissue_id_table:
                obs_tissue_id = tissue_id_table[tissue_id][0]
            elif tissue_id_fix in tissue_id_table:
                obs_tissue_id = tissue_id_table[tissue_id_fix][0]
            else:
                tissue_id_error[(glycerol_stock_id, experiment_name, location_name, date, extract_color, organism, comments, field_name, row_id, plant_id, seed_id, tissue_id, microbe_id, well_id, plate_id, dna_id, culture_id, sample_id, isolate_id)] = error_count
                error_count = error_count + 1
                obs_tissue_id = 1
        else:
            obs_tissue_id = 1

        if culture_id != '':
            culture_id_fix = culture_id + '\r'
            if culture_id in culture_id_table:
                obs_culture_id = culture_id_table[culture_id][0]
            elif culture_id_fix in culture_id_table:
                obs_culture_id = culture_id_table[culture_id_fix][0]
            else:
                culture_id_error[(glycerol_stock_id, experiment_name, location_name, date, extract_color, organism, comments, field_name, row_id, plant_id, seed_id, tissue_id, microbe_id, well_id, plate_id, dna_id, culture_id, sample_id, isolate_id)] = error_count
                error_count = error_count + 1
                obs_culture_id = 1
        else:
            obs_culture_id = 1

        if plate_id != '':
            plate_id_fix = plate_id + '\r'
            if plate_id in plate_id_table:
                obs_plate_id = plate_id_table[plate_id][0]
            elif plate_id_fix in plate_id_table:
                obs_plate_id = plate_id_table[plate_id_fix][0]
            else:
                plate_id_error[(glycerol_stock_id, experiment_name, location_name, date, extract_color, organism, comments, field_name, row_id, plant_id, seed_id, tissue_id, microbe_id, well_id, plate_id, dna_id, culture_id, sample_id, isolate_id)] = error_count
                error_count = error_count + 1
                obs_plate_id = 1
        else:
            obs_plate_id = 1

        if microbe_id != '':
            microbe_id_fix = microbe_id + '\r'
            if microbe_id in microbe_id_table:
                obs_microbe_id = microbe_id_table[microbe_id][0]
            elif microbe_id_fix in microbe_id_table:
                obs_microbe_id = microbe_id_table[microbe_id_fix][0]
            else:
                microbe_id_error[(glycerol_stock_id, experiment_name, location_name, date, extract_color, organism, comments, field_name, row_id, plant_id, seed_id, tissue_id, microbe_id, well_id, plate_id, dna_id, culture_id, sample_id, isolate_id)] = error_count
                error_count = error_count + 1
                obs_microbe_id = 1
        else:
            obs_microbe_id = 1

        if well_id != '':
            well_id_fix = well_id + '\r'
            if well_id in well_id_table:
                obs_well_id = well_id_table[well_id][0]
            elif well_id_fix in well_id_table:
                obs_well_id = well_id_table[well_id_fix][0]
            else:
                well_id_error[(glycerol_stock_id, experiment_name, location_name, date, extract_color, organism, comments, field_name, row_id, plant_id, seed_id, tissue_id, microbe_id, well_id, plate_id, dna_id, culture_id, sample_id, isolate_id)] = error_count
                error_count = error_count + 1
                obs_well_id = 1
        else:
            obs_well_id = 1

        if dna_id != '':
            dna_id_fix = dna_id + '\r'
            if dna_id in dna_id_table:
                obs_dna_id = dna_id_table[dna_id][0]
            elif dna_id_fix in dna_id_table:
                obs_dna_id = dna_id_table[dna_id_fix][0]
            else:
                dna_id_error[(glycerol_stock_id, experiment_name, location_name, date, extract_color, organism, comments, field_name, row_id, plant_id, seed_id, tissue_id, microbe_id, well_id, plate_id, dna_id, culture_id, sample_id, isolate_id)] = error_count
                error_count = error_count + 1
                obs_dna_id = 1
        else:
            obs_dna_id = 1

        if sample_id != '':
            sample_id_fix = sample_id + '\r'
            if sample_id in sample_id_table:
                obs_sample_id = sample_id_table[sample_id][0]
            elif sample_id_fix in sample_id_table:
                obs_sample_id = sample_id_table[sample_id_fix][0]
            else:
                sample_id_error[(glycerol_stock_id, experiment_name, location_name, date, extract_color, organism, comments, field_name, row_id, plant_id, seed_id, tissue_id, microbe_id, well_id, plate_id, dna_id, culture_id, sample_id, isolate_id)] = error_count
                error_count = error_count + 1
                obs_sample_id = 1
        else:
            obs_sample_id = 1

        if isolate_id != '':
            isolate_id_fix = isolate_id + '\r'
            if isolate_id in isolate_id_table:
                isolate_table_id = isolate_id_table[isolate_id][0]
            elif isolate_id_fix in isolate_id_table:
                isolate_table_id = isolate_id_table[isolate_id_fix][0]
            else:
                isolate_id_error[(glycerol_stock_id, experiment_name, location_name, date, extract_color, organism, comments, field_name, row_id, plant_id, seed_id, tissue_id, microbe_id, well_id, plate_id, dna_id, culture_id, sample_id, isolate_id)] = error_count
                error_count = error_count + 1
                isolate_table_id = 1
        else:
            isolate_table_id = 1

        if location_name != '':
            location_name_fix = location_name + '\r'
            if location_name in location_name_table:
                location_id = location_name_table[location_name][0]
            elif location_name_fix in location_name_table:
                location_id = location_name_table[location_name_fix][0]
            else:
                location_name_error[(glycerol_stock_id, experiment_name, location_name, date, extract_color, organism, comments, field_name, row_id, plant_id, seed_id, tissue_id, microbe_id, well_id, plate_id, dna_id, culture_id, sample_id, isolate_id)] = error_count
                error_count = error_count + 1
                location_id = 1
        else:
            location_id = 1

        glycerol_stock_hash = glycerol_stock_id + date + extract_color + organism + comments
        glycerol_stock_hash_fix = glycerol_stock_hash + '\r'
        if glycerol_stock_id not in glycerol_stock_id_table and glycerol_stock_id + '\r' not in glycerol_stock_id_table:
            if glycerol_stock_hash not in glycerol_stock_hash_table and glycerol_stock_hash_fix not in glycerol_stock_hash_table:
                glycerol_stock_hash_table[glycerol_stock_hash] = glycerol_stock_table_id
                glycerol_stock_new[(glycerol_stock_table_id, glycerol_stock_id, date, extract_color, organism, comments)] = glycerol_stock_table_id
                glycerol_stock_id_table[glycerol_stock_id] = (glycerol_stock_table_id, glycerol_stock_id, date, extract_color, organism, comments)
                glycerol_stock_table_id = glycerol_stock_table_id + 1
            else:
                glycerol_stock_hash_exists[(glycerol_stock_id + date + extract_color + organism + comments)] = glycerol_stock_table_id
        else:
            glycerol_stock_hash_exists[(glycerol_stock_id + date + extract_color + organism + comments)] = glycerol_stock_table_id

        if glycerol_stock_id in glycerol_stock_id_table:
            temp_glycerol_id = glycerol_stock_id_table[glycerol_stock_id][0]
        elif glycerol_stock_id + '\r' in glycerol_stock_id_table:
            temp_glycerol_id = glycerol_stock_id_table[glycerol_stock_id + '\r'][0]
        elif glycerol_stock_hash in glycerol_stock_hash_table:
            temp_glycerol_id = glycerol_stock_hash_table[glycerol_stock_hash]
        elif glycerol_stock_hash_fix in glycerol_stock_hash_table:
            temp_glycerol_id = glycerol_stock_hash_table[glycerol_stock_hash_fix]
        else:
            temp_glycerol_id = 1
            error_count = error_count + 1

        obs_tracker_glycerol_hash = 'glycerol_stock' + str(1) + str(field_id) + str(temp_glycerol_id) + str(isolate_table_id) + str(location_id) + str(1) + str(obs_culture_id) + str(obs_dna_id) + str(1) + str(1) + str(obs_microbe_id) + str(obs_plant_id) + str(obs_plate_id) + str(obs_row_id) + str(obs_sample_id) + str(obs_tissue_id) + str(obs_well_id) + str(stock_id) + str(user_hash_table[user.username])
        obs_tracker_glycerol_hash_fix = obs_tracker_glycerol_hash + '\r'
        if obs_tracker_glycerol_hash not in obs_tracker_hash_table and obs_tracker_glycerol_hash_fix not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_glycerol_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'glycerol_stock', 1, field_id, temp_glycerol_id, isolate_table_id, location_id, 1, obs_culture_id, obs_dna_id, 1, 1, obs_microbe_id, obs_plant_id, obs_plate_id, obs_row_id, obs_sample_id, obs_tissue_id, obs_well_id, stock_id, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1
        else:
            obs_tracker_hash_exists[('glycerol_stock', 1, field_id, temp_glycerol_id, isolate_table_id, location_id, 1, obs_culture_id, obs_dna_id, 1, 1, obs_microbe_id, obs_plant_id, obs_plate_id, obs_row_id, obs_sample_id, obs_tissue_id, obs_well_id, stock_id, user_hash_table[user.username])] = obs_tracker_id

        if stock_id != 1:
            obs_tracker_source_stock_hash = str(obs_tracker_stock_id_table[stock_id][0]) + str(obs_tracker_hash_table[obs_tracker_glycerol_hash]) + 'isolate_stock_from_stock'
            if obs_tracker_source_stock_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_stock_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_stock_id_table[stock_id][0], obs_tracker_hash_table[obs_tracker_glycerol_hash], 'isolate_stock_from_stock')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_stock_id_table[stock_id][0], obs_tracker_hash_table[obs_tracker_glycerol_hash], 'isolate_stock_from_stock')] = obs_tracker_source_id

        if obs_row_id != 1:
            obs_tracker_source_row_hash = str(obs_tracker_obs_row_id_table[obs_row_id][0]) + str(obs_tracker_hash_table[obs_tracker_glycerol_hash]) + 'isolate_stock_from_row'
            if obs_tracker_source_row_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_row_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_row_id_table[obs_row_id][0], obs_tracker_hash_table[obs_tracker_glycerol_hash], 'isolate_stock_from_row')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_row_id_table[obs_row_id][0], obs_tracker_hash_table[obs_tracker_glycerol_hash], 'isolate_stock_from_row')] = obs_tracker_source_id

        if obs_plant_id != 1:
            obs_tracker_source_plant_hash = str(obs_tracker_obs_plant_id_table[obs_plant_id][0]) + str(obs_tracker_hash_table[obs_tracker_glycerol_hash]) + 'isolate_stock_from_plant'
            if obs_tracker_source_plant_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_plant_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_plant_id_table[obs_plant_id][0], obs_tracker_hash_table[obs_tracker_glycerol_hash], 'isolate_stock_from_plant')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_plant_id_table[obs_plant_id][0], obs_tracker_hash_table[obs_tracker_glycerol_hash], 'isolate_stock_from_plant')] = obs_tracker_source_id

        if obs_tissue_id != 1:
            obs_tracker_source_tissue_hash = str(obs_tracker_obs_tissue_id_table[obs_tissue_id][0]) + str(obs_tracker_hash_table[obs_tracker_glycerol_hash]) + 'isolate_stock_from_tissue'
            if obs_tracker_source_tissue_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_tissue_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_tissue_id_table[obs_tissue_id][0], obs_tracker_hash_table[obs_tracker_glycerol_hash], 'isolate_stock_from_tissue')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_tissue_id_table[obs_tissue_id][0], obs_tracker_hash_table[obs_tracker_glycerol_hash], 'isolate_stock_from_tissue')] = obs_tracker_source_id

        if obs_culture_id != 1:
            obs_tracker_source_culture_hash = str(obs_tracker_obs_culture_id_table[obs_culture_id][0]) + str(obs_tracker_hash_table[obs_tracker_glycerol_hash]) + 'isolate_stock_from_culture'
            if obs_tracker_source_culture_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_culture_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_culture_id_table[obs_culture_id][0], obs_tracker_hash_table[obs_tracker_glycerol_hash], 'isolate_stock_from_culture')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_culture_id_table[obs_culture_id][0], obs_tracker_hash_table[obs_tracker_glycerol_hash], 'isolate_stock_from_culture')] = obs_tracker_source_id

        if obs_microbe_id != 1:
            obs_tracker_source_microbe_hash = str(obs_tracker_obs_microbe_id_table[obs_microbe_id][0]) + str(obs_tracker_hash_table[obs_tracker_glycerol_hash]) + 'isolate_stock_from_microbe'
            if obs_tracker_source_microbe_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_microbe_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_microbe_id_table[obs_microbe_id][0], obs_tracker_hash_table[obs_tracker_glycerol_hash], 'isolate_stock_from_microbe')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_microbe_id_table[obs_microbe_id][0], obs_tracker_hash_table[obs_tracker_glycerol_hash], 'isolate_stock_from_microbe')] = obs_tracker_source_id

        if obs_plate_id != 1:
            obs_tracker_source_plate_hash = str(obs_tracker_obs_plate_id_table[obs_plate_id][0]) + str(obs_tracker_hash_table[obs_tracker_glycerol_hash]) + 'isolate_stock_from_plate'
            if obs_tracker_source_plate_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_plate_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_plate_id_table[obs_plate_id][0], obs_tracker_hash_table[obs_tracker_glycerol_hash], 'isolate_stock_from_plate')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_plate_id_table[obs_plate_id][0], obs_tracker_hash_table[obs_tracker_glycerol_hash], 'isolate_stock_from_plate')] = obs_tracker_source_id

        if obs_well_id != 1:
            obs_tracker_source_well_hash = str(obs_tracker_obs_well_id_table[obs_well_id][0]) + str(obs_tracker_hash_table[obs_tracker_glycerol_hash]) + 'isolate_stock_from_well'
            if obs_tracker_source_well_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_well_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_well_id_table[obs_well_id][0], obs_tracker_hash_table[obs_tracker_glycerol_hash], 'isolate_stock_from_well')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_well_id_table[obs_well_id][0], obs_tracker_hash_table[obs_tracker_glycerol_hash], 'isolate_stock_from_well')] = obs_tracker_source_id

        if obs_dna_id != 1:
            obs_tracker_source_dna_hash = str(obs_tracker_obs_dna_id_table[obs_dna_id][0]) + str(obs_tracker_hash_table[obs_tracker_glycerol_hash]) + 'isolate_stock_from_dna'
            if obs_tracker_source_dna_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_dna_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_dna_id_table[obs_dna_id][0], obs_tracker_hash_table[obs_tracker_glycerol_hash], 'isolate_stock_from_dna')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_dna_id_table[obs_dna_id][0], obs_tracker_hash_table[obs_tracker_glycerol_hash], 'isolate_stock_from_dna')] = obs_tracker_source_id

        if obs_sample_id != 1:
            obs_tracker_source_sample_hash = str(obs_tracker_obs_sample_id_table[obs_sample_id][0]) + str(obs_tracker_hash_table[obs_tracker_glycerol_hash]) + 'isolate_stock_from_sample'
            if obs_tracker_source_sample_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_sample_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_obs_sample_id_table[obs_sample_id][0], obs_tracker_hash_table[obs_tracker_glycerol_hash], 'isolate_stock_from_sample')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_obs_sample_id_table[obs_sample_id][0], obs_tracker_hash_table[obs_tracker_glycerol_hash], 'isolate_stock_from_sample')] = obs_tracker_source_id

        if isolate_table_id != 1:
            obs_tracker_source_isolate_hash = str(obs_tracker_isolate_table_id_table[isolate_table_id][0]) + str(obs_tracker_hash_table[obs_tracker_glycerol_hash]) + 'isolate_stock_from_isolate'
            if obs_tracker_source_isolate_hash not in obs_tracker_source_hash_table:
                obs_tracker_source_hash_table[obs_tracker_source_isolate_hash] = obs_tracker_source_id
                obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_isolate_table_id_table[isolate_table_id][0], obs_tracker_hash_table[obs_tracker_glycerol_hash], 'isolate_stock_from_isolate')] = obs_tracker_source_id
                obs_tracker_source_id = obs_tracker_source_id + 1
            else:
                obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_isolate_table_id_table[isolate_table_id][0], obs_tracker_hash_table[obs_tracker_glycerol_hash], 'isolate_stock_from_isolate')] = obs_tracker_source_id

        obs_tracker_exp_hash = 'experiment' + str(experiment_name_table[experiment_name][0]) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(user_hash_table[user.username])
        if obs_tracker_exp_hash not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_exp_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'experiment', experiment_name_table[experiment_name][0], 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1

        obs_tracker_source_hash = str(obs_tracker_hash_table[obs_tracker_exp_hash]) + str(obs_tracker_hash_table[obs_tracker_glycerol_hash]) + 'isolate_stock_from_experiment'
        if obs_tracker_source_hash not in obs_tracker_source_hash_table:
            obs_tracker_source_hash_table[obs_tracker_source_hash] = obs_tracker_source_id
            obs_tracker_source_new[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], obs_tracker_hash_table[obs_tracker_glycerol_hash], 'isolate_stock_from_experiment')] = obs_tracker_source_id
            obs_tracker_source_id = obs_tracker_source_id + 1
        else:
            obs_tracker_source_hash_exists[(obs_tracker_source_id, obs_tracker_hash_table[obs_tracker_exp_hash], obs_tracker_hash_table[obs_tracker_glycerol_hash], 'isolate_stock_from_experiment')] = obs_tracker_source_id

    end = time.clock()
    stats = {}
    stats[("Time: %s" % (end-start), "Errors: %s" % (error_count))] = error_count

    results_dict = {}
    results_dict['glycerol_stock_new'] = glycerol_stock_new
    results_dict['obs_tracker_new'] = obs_tracker_new
    results_dict['obs_tracker_source_new'] = obs_tracker_source_new
    results_dict['field_name_error'] = field_name_error
    results_dict['sample_id_error'] = sample_id_error
    results_dict['isolate_id_error'] = isolate_id_error
    results_dict['seed_id_error'] = seed_id_error
    results_dict['row_id_error'] = row_id_error
    results_dict['plant_id_error'] = plant_id_error
    results_dict['tissue_id_error'] = tissue_id_error
    results_dict['culture_id_error'] = culture_id_error
    results_dict['plate_id_error'] = plate_id_error
    results_dict['microbe_id_error'] = microbe_id_error
    results_dict['dna_id_error'] = dna_id_error
    results_dict['well_id_error'] = well_id_error
    results_dict['location_name_error'] = location_name_error
    results_dict['glycerol_stock_hash_exists'] = glycerol_stock_hash_exists
    results_dict['obs_tracker_hash_exists'] = obs_tracker_hash_exists
    results_dict['obs_tracker_source_hash_exists'] = obs_tracker_source_hash_exists
    results_dict['stats'] = stats
    return results_dict

def glycerol_stock_loader_prep_output(results_dict, new_upload_exp, template_type):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s_%s_prep.csv"' % (new_upload_exp, template_type)
    writer = csv.writer(response)
    writer.writerow(['Stats'])
    writer.writerow([''])
    for key in results_dict['stats'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Glycerol Stock Table'])
    writer.writerow(['id', 'glycerol_stock_id', 'stock_date', 'extract_color', 'organism', 'comments'])
    for key in results_dict['glycerol_stock_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTracker Table'])
    writer.writerow(['obs_tracker_id', 'obs_entity_type', 'experiment_id', 'field_id', 'glycerol_stock_id', 'isolate_id', 'location_id', 'maize_sample_id', 'obs_culture_id', 'obs_dna_id', 'obs_env_id', 'obs_extract_id', 'obs_microbe_id', 'obs_plant_id', 'obs_plate_id', 'obs_row_id', 'obs_sample_id', 'obs_tissue_id', 'obs_well_id', 'stock_id', 'user_id'])
    for key in results_dict['obs_tracker_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTrackerSource Table'])
    writer.writerow(['obs_tracker_source_id', 'source_obs_id', 'target_obs_id'])
    for key in results_dict['obs_tracker_source_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['---------------------------------------------------------------------------------------------------'])
    writer.writerow([''])
    writer.writerow(['Seed ID Errors'])
    writer.writerow(['glycerol_stock_id', 'experiment_name', 'location_name', 'date', 'extract_color', 'organism', 'comments', 'source_field_name', 'source_row_id', 'source_plant_id', 'source_seed_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_plate_id', 'source_dna_id', 'source_culture_id', 'source_sample_id', 'source_isolate_id'])
    for key in results_dict['seed_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Row ID Errors'])
    writer.writerow(['glycerol_stock_id', 'experiment_name', 'location_name', 'date', 'extract_color', 'organism', 'comments', 'source_field_name', 'source_row_id', 'source_plant_id', 'source_seed_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_plate_id', 'source_dna_id', 'source_culture_id', 'source_sample_id', 'source_isolate_id'])
    for key in results_dict['row_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Plant ID Errors'])
    writer.writerow(['glycerol_stock_id', 'experiment_name', 'location_name', 'date', 'extract_color', 'organism', 'comments', 'source_field_name', 'source_row_id', 'source_plant_id', 'source_seed_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_plate_id', 'source_dna_id', 'source_culture_id', 'source_sample_id', 'source_isolate_id'])
    for key in results_dict['plant_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Tissue ID Errors'])
    writer.writerow(['glycerol_stock_id', 'experiment_name', 'location_name', 'date', 'extract_color', 'organism', 'comments', 'source_field_name', 'source_row_id', 'source_plant_id', 'source_seed_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_plate_id', 'source_dna_id', 'source_culture_id', 'source_sample_id', 'source_isolate_id'])
    for key in results_dict['tissue_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Culture ID Errors'])
    writer.writerow(['glycerol_stock_id', 'experiment_name', 'location_name', 'date', 'extract_color', 'organism', 'comments', 'source_field_name', 'source_row_id', 'source_plant_id', 'source_seed_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_plate_id', 'source_dna_id', 'source_culture_id', 'source_sample_id', 'source_isolate_id'])
    for key in results_dict['culture_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Microbe ID Errors'])
    writer.writerow(['glycerol_stock_id', 'experiment_name', 'location_name', 'date', 'extract_color', 'organism', 'comments', 'source_field_name', 'source_row_id', 'source_plant_id', 'source_seed_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_plate_id', 'source_dna_id', 'source_culture_id', 'source_sample_id', 'source_isolate_id'])
    for key in results_dict['microbe_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Plate ID Errors'])
    writer.writerow(['glycerol_stock_id', 'experiment_name', 'location_name', 'date', 'extract_color', 'organism', 'comments', 'source_field_name', 'source_row_id', 'source_plant_id', 'source_seed_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_plate_id', 'source_dna_id', 'source_culture_id', 'source_sample_id', 'source_isolate_id'])
    for key in results_dict['plate_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Well ID Errors'])
    writer.writerow(['glycerol_stock_id', 'experiment_name', 'location_name', 'date', 'extract_color', 'organism', 'comments', 'source_field_name', 'source_row_id', 'source_plant_id', 'source_seed_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_plate_id', 'source_dna_id', 'source_culture_id', 'source_sample_id', 'source_isolate_id'])
    for key in results_dict['well_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['DNA ID Errors'])
    writer.writerow(['glycerol_stock_id', 'experiment_name', 'location_name', 'date', 'extract_color', 'organism', 'comments', 'source_field_name', 'source_row_id', 'source_plant_id', 'source_seed_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_plate_id', 'source_dna_id', 'source_culture_id', 'source_sample_id', 'source_isolate_id'])
    for key in results_dict['dna_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Isolate ID Errors'])
    writer.writerow(['glycerol_stock_id', 'experiment_name', 'location_name', 'date', 'extract_color', 'organism', 'comments', 'source_field_name', 'source_row_id', 'source_plant_id', 'source_seed_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_plate_id', 'source_dna_id', 'source_culture_id', 'source_sample_id', 'source_isolate_id'])
    for key in results_dict['isolate_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Sample ID Errors'])
    writer.writerow(['glycerol_stock_id', 'experiment_name', 'location_name', 'date', 'extract_color', 'organism', 'comments', 'source_field_name', 'source_row_id', 'source_plant_id', 'source_seed_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_plate_id', 'source_dna_id', 'source_culture_id', 'source_sample_id', 'source_isolate_id'])
    for key in results_dict['sample_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Location Name Errors'])
    writer.writerow(['glycerol_stock_id', 'experiment_name', 'location_name', 'date', 'extract_color', 'organism', 'comments', 'source_field_name', 'source_row_id', 'source_plant_id', 'source_seed_id', 'source_tissue_id', 'source_microbe_id', 'source_well_id', 'source_plate_id', 'source_dna_id', 'source_culture_id', 'source_sample_id', 'source_isolate_id'])
    for key in results_dict['location_name_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Glycerol Stock Entry Already Exists'])
    for key in results_dict['glycerol_stock_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTracker Entry Already Exists'])
    for key in results_dict['obs_tracker_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTrackerSource Entry Already Exists'])
    for key in results_dict['obs_tracker_source_hash_exists'].keys():
        writer.writerow(key)
    return response

def glycerol_stock_loader(results_dict):
    try:
        for key in results_dict['glycerol_stock_new'].keys():
            try:
                with transaction.atomic():
                    new_glycerol = GlycerolStock.objects.create(id=key[0], glycerol_stock_id=key[1], stock_date=key[2], extract_color=key[3], organism=key[4], comments=key[5])
            except Exception as e:
                print("Glycerol Stock Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = ObsTracker.objects.create(id=key[0], obs_entity_type=key[1], experiment_id=key[2], field_id=key[3], glycerol_stock_id=key[4], isolate_id=key[5], location_id=key[6], maize_sample_id=key[7], obs_culture_id=key[8], obs_dna_id=key[9], obs_env_id=key[10], obs_extract_id=key[11], obs_microbe_id=key[12], obs_plant_id=key[13], obs_plate_id=key[14], obs_row_id=key[15], obs_sample_id=key[16], obs_tissue_id=key[17], obs_well_id=key[18], stock_id=key[19], user_id=key[20])
            except Exception as e:
                print("ObsTracker Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_source_new'].keys():
            try:
                with transaction.atomic():
                    new_obstrackersource = ObsTrackerSource.objects.create(id=key[0], source_obs_id=key[1], target_obs_id=key[2], relationship=key[3])
            except Exception as e:
                print("ObsTrackerSource Error: %s %s" % (e.message, e.args))
                return False
    except Exception as e:
        print("Error: %s %s" % (e.message, e.args))
        return False
    return True

def measurement_loader_prep(upload_file, user):
    start = time.clock()

    #-- These are the tables that will hold the curated data that is then written to csv files --
    measurement_new = OrderedDict({})
    #--- Key = (measurement_id, obs_tracker_id, measurement_parameter_id, user_id, time_of_measurement, value, comments)
    #--- Value = (measurement_id)

    measurement_hash_table = loader_db_mirror.measurement_hash_mirror()
    measurement_id = loader_db_mirror.measurement_id_mirror()
    obs_tracker_row_id_table = loader_db_mirror.obs_tracker_row_id_mirror()
    obs_tracker_plant_id_table = loader_db_mirror.obs_tracker_plant_id_mirror()
    obs_tracker_env_id_table = loader_db_mirror.obs_tracker_env_id_mirror()
    obs_tracker_sample_id_table = loader_db_mirror.obs_tracker_sample_id_mirror()
    obs_tracker_microbe_id_table = loader_db_mirror.obs_tracker_microbe_id_mirror()
    obs_tracker_well_id_table = loader_db_mirror.obs_tracker_well_id_mirror()
    obs_tracker_plate_id_table = loader_db_mirror.obs_tracker_plate_id_mirror()
    obs_tracker_dna_id_table = loader_db_mirror.obs_tracker_dna_id_mirror()
    obs_tracker_tissue_id_table = loader_db_mirror.obs_tracker_tissue_id_mirror()
    obs_tracker_extract_id_table = loader_db_mirror.obs_tracker_extract_id_mirror()
    obs_tracker_culture_id_table = loader_db_mirror.obs_tracker_culture_id_mirror()
    obs_tracker_seed_id_table = loader_db_mirror.obs_tracker_seed_id_mirror()
    user_hash_table = loader_db_mirror.user_hash_mirror()
    measurement_param_name_table = loader_db_mirror.measurement_parameter_name_mirror()

    error_count = 0
    obs_id_error = OrderedDict({})
    username_error = OrderedDict({})
    parameter_error = OrderedDict({})
    measurement_hash_exists = OrderedDict({})

    measurement_file = csv.DictReader(codecs.iterdecode(upload_file, 'utf-8'))
    for row in measurement_file:
        obs_id = row["Observation Unit"]
        parameter = row["Parameter Name"]
        username = row["Username"]
        time_of_measurement = row["DateTime"]
        value = row["Value"]
        comments = row["Measurement Comments"]

        if obs_id in obs_tracker_row_id_table:
            obs_tracker_id = obs_tracker_row_id_table[obs_id][0]
        elif obs_id in obs_tracker_plant_id_table:
            obs_tracker_id = obs_tracker_plant_id_table[obs_id][0]
        elif obs_id in obs_tracker_env_id_table:
            obs_tracker_id = obs_tracker_env_id_table[obs_id][0]
        elif obs_id in obs_tracker_sample_id_table:
            obs_tracker_id = obs_tracker_sample_id_table[obs_id][0]
        elif obs_id in obs_tracker_microbe_id_table:
            obs_tracker_id = obs_tracker_microbe_id_table[obs_id][0]
        elif obs_id in obs_tracker_well_id_table:
            obs_tracker_id = obs_tracker_well_id_table[obs_id][0]
        elif obs_id in obs_tracker_plate_id_table:
            obs_tracker_id = obs_tracker_plate_id_table[obs_id][0]
        elif obs_id in obs_tracker_dna_id_table:
            obs_tracker_id = obs_tracker_dna_id_table[obs_id][0]
        elif obs_id in obs_tracker_tissue_id_table:
            obs_tracker_id = obs_tracker_tissue_id_table[obs_id][0]
        elif obs_id in obs_tracker_extract_id_table:
            obs_tracker_id = obs_tracker_extract_id_table[obs_id][0]
        elif obs_id in obs_tracker_culture_id_table:
            obs_tracker_id = obs_tracker_culture_id_table[obs_id][0]
        elif obs_id in obs_tracker_seed_id_table:
            obs_tracker_id = obs_tracker_seed_id_table[obs_id][0]
        else:
            obs_tracker_id = 1
            obs_id_error[(obs_id, parameter, username, time_of_measurement, value, comments)] = obs_id
            error_count = error_count + 1

        if username != '':
            if username in user_hash_table:
                user_id = user_hash_table[username]
            else:
                user_id = user_hash_table['unknown_person']
                username_error[(obs_id, parameter, username, time_of_measurement, value, comments)] = obs_id
                error_count = error_count + 1
        else:
            user_id = user_hash_table['unknown_person']

        if parameter in measurement_param_name_table:
            parameter_id = measurement_param_name_table[parameter][0]
        elif parameter + '\r' in measurement_param_name_table:
            parameter_id = measurement_param_name_table[parameter + '\r'][0]
        else:
            parameter_id = 1
            parameter_error[(obs_id, parameter, username, time_of_measurement, value, comments)] = obs_id
            error_count = error_count + 1

        measurement_hash = str(obs_tracker_id) + str(user_id) + str(parameter_id) + time_of_measurement + value + comments
        measurement_hash_fix = measurement_hash + '\r'
        if measurement_hash not in measurement_hash_table and measurement_hash_fix not in measurement_hash_table:
            measurement_hash_table[measurement_hash] = measurement_id
            measurement_new[(measurement_id, obs_tracker_id, user_id, parameter_id, time_of_measurement, value, comments)] = measurement_id
            measurement_id = measurement_id + 1
        else:
            measurement_hash_exists[(measurement_id, obs_tracker_id, user_id, parameter_id, time_of_measurement, value, comments)] = measurement_id

    end = time.clock()
    stats = {}
    stats[("Time: %s" % (end-start), "Errors: %s" % (error_count))] = error_count

    results_dict = {}
    results_dict['measurement_new'] = measurement_new
    results_dict['obs_id_error'] = obs_id_error
    results_dict['username_error'] = username_error
    results_dict['parameter_error'] = parameter_error
    results_dict['measurement_hash_exists'] = measurement_hash_exists
    results_dict['stats'] = stats
    return results_dict

def measurement_loader_prep_output(results_dict, new_upload_exp, template_type):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s_%s_prep.csv"' % (new_upload_exp, template_type)
    writer = csv.writer(response)
    writer.writerow(['Stats'])
    writer.writerow([''])
    for key in results_dict['stats'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Measurement Table'])
    writer.writerow(['measurement_id', 'obs_tracker_id', 'user_id', 'measurement_parameter_id', 'time_of_measurement', 'value', 'comments'])
    for key in results_dict['measurement_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['---------------------------------------------------------------------------------------------------'])
    writer.writerow([''])
    writer.writerow(['Observation ID Errors'])
    writer.writerow(['observation_id', 'parameter', 'username', 'time_of_measurement', 'value', 'comments'])
    for key in results_dict['obs_id_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Username Errors'])
    writer.writerow(['observation_id', 'parameter', 'username', 'time_of_measurement', 'value', 'comments'])
    for key in results_dict['username_error'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Parameter Errors'])
    writer.writerow(['observation_id', 'parameter', 'username', 'time_of_measurement', 'value', 'comments'])
    for key in results_dict['parameter_error'].keys():
        writer.writerow([key])
    writer.writerow([''])
    writer.writerow(['Measurement Entry Already Exists'])
    for key in results_dict['measurement_hash_exists'].keys():
        writer.writerow(key)
    return response

def measurement_loader(results_dict):
    try:
        for key in results_dict['measurement_new'].keys():
            try:
                with transaction.atomic():
                    new_measurement = Measurement.objects.create(id=key[0], obs_tracker_id=key[1], user_id=key[2], measurement_parameter_id=key[3], time_of_measurement=key[4], value=key[5], comments=key[6])
            except Exception as e:
                print("Measurement Error: %s %s" % (e.message, e.args))
                return False
    except Exception as e:
        print("Error: %s %s" % (e.message, e.args))
        return False
    return True


def primer_loader_prep(upload_file, user):
    start = time.clock()

    primer_new = OrderedDict({})
    #--- Key = (primer_table_id, primer_id, primer_name, primer_tail, size_range, temp_min, temp_max, order_date, comments)
    #--- Value = (primer_table_id)

    user_hash_table = loader_db_mirror.user_hash_mirror()
    primer_hash_table = loader_db_mirror.primer_hash_mirror()
    primer_id_table = loader_db_mirror.primer_id_mirror()
    primer_table_id = loader_db_mirror.primer_table_id_mirror()

    error_count = 0
    primer_hash_exists = OrderedDict({})

    primer_file = csv.DictReader(codecs.iterdecode(upload_file, 'utf-8'))
    for row in primer_file:
        primer_id = row["Primer ID"]
        primer_name = row["Primer Name"]
        primer_tail = row["Primer Tail"]
        size_range = row["Size Range"]
        temp_min = row["Temp Min"]
        temp_max = row["Temp Max"]
        order_date = row["Order Date"]
        comments = row["Comments"]

        primer_hash = primer_id + primer_name + primer_tail + size_range + temp_min + temp_max + order_date + comments
        if primer_id not in primer_id_table and primer_hash not in primer_hash_table:
            primer_hash_table[primer_hash] = primer_table_id
            primer_new[(primer_table_id, primer_id, primer_name, primer_tail, size_range, temp_min, temp_max, order_date, comments)] = primer_table_id
            primer_id_table[primer_id] = (primer_table_id, primer_id, primer_name, primer_tail, size_range, temp_min, temp_max, order_date, comments)
            primer_table_id = primer_table_id + 1
        else:
            primer_hash_exists[(primer_id, primer_name, primer_tail, size_range, temp_min, temp_max, order_date, comments)] = primer_table_id

    end = time.clock()
    stats = {}
    stats[("Time: %s" % (end-start), "Errors: %s" % (error_count))] = error_count

    results_dict = {}
    results_dict['primer_new'] = primer_new
    results_dict['primer_hash_exists'] = primer_hash_exists
    results_dict['stats'] = stats
    return results_dict

def primer_loader_prep_output(results_dict, new_upload_exp, template_type):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s_%s_prep.csv"' % (new_upload_exp, template_type)
    writer = csv.writer(response)
    writer.writerow(['Stats'])
    writer.writerow([''])
    for key in results_dict['stats'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Primer Table'])
    writer.writerow(['primer_table_id', 'primer_id', 'primer_name', 'primer_tail', 'size_range', 'temp_min', 'temp_max', 'order_date', 'comments'])
    for key in results_dict['primer_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['---------------------------------------------------------------------------------------------------'])
    writer.writerow([''])
    writer.writerow(['Primer Entry Already Exists'])
    for key in results_dict['primer_hash_exists'].keys():
        writer.writerow(key)
    return response

def primer_loader(results_dict):
    try:
        for key in results_dict['primer_new'].keys():
            try:
                with transaction.atomic():
                    new_primer = Primer.objects.create(id=key[0], primer_id=key[1], primer_name=key[2], primer_tail=key[3], size_range=key[4], temp_min=key[5], temp_max=key[6], order_date=key[7], comments=key[8])
            except Exception as e:
                print("Primer Error: %s %s" % (e.message, e.args))
                return False
    except Exception as e:
        print("Error: %s %s" % (e.message, e.args))
        return False
    return True


def marker_loader_prep(upload_file, user):
    start = time.clock()

    marker_new = OrderedDict({})
    #--- Key = (marker_table_id, map_feature_interval_id, marker_map_feature_id, primer_f_id, primer_r_id, marker_id, marker_name, length, bac, nam_marker, poly_type, ref_seq, comments, strand, allele)
    #--- Value = (marker_table_id)
    map_feature_new = OrderedDict({})
    #--- Key = (map_feature_table_id, chromosome, genetic_bin, physical_map, genetic_position, physical_position, comments)
    #--- Value = (map_feature_table_id)
    map_feature_interval_new = OrderedDict({})
    #--- Key = (map_feature_interval_table_id, map_feature_start_id, map_feature_end_id, interval_type, interval_name, comments)
    #--- Value = (map_feature_table_id)

    user_hash_table = loader_db_mirror.user_hash_mirror()
    marker_hash_table = loader_db_mirror.marker_hash_mirror()
    map_feature_hash_table = loader_db_mirror.map_feature_hash_mirror()
    map_feature_interval_hash_table = loader_db_mirror.map_feature_interval_hash_mirror()
    marker_id_table = loader_db_mirror.marker_id_mirror()
    primer_id_table = loader_db_mirror.primer_id_mirror()
    marker_table_id = loader_db_mirror.marker_table_id_mirror()
    map_feature_table_id = loader_db_mirror.map_feature_table_id_mirror()
    map_feature_interval_table_id = loader_db_mirror.map_feature_interval_table_id_mirror()

    error_count = 0
    marker_hash_exists = OrderedDict({})
    map_feature_hash_exists = OrderedDict({})
    map_feature_interval_hash_exists = OrderedDict({})
    primer_error = OrderedDict({})

    marker_file = csv.DictReader(codecs.iterdecode(upload_file, 'utf-8'))
    for row in marker_file:
        marker_id = row["Marker ID"]
        interval_type = row["Interval Type"]
        interval_name = row["Interval Name"]
        interval_comments = row["Interval Comments"]
        chromosome = row["Chromosome"]
        genetic_bin = row["Genetic Bin"]
        physical_map = row["Physical Map"]
        start_physical_position = row["Start Physical Position"]
        end_physical_position = row["End Physical Position"]
        start_genetic_position = row["Start Genetic Position"]
        end_genetic_position = row["End Genetic Position"]
        marker_physical_position = row["Marker Physical Position"]
        marker_genetic_position = row["Marker Genetic Position"]
        primer_f_id = row["Primer F ID"]
        primer_r_id = row["Primer R ID"]
        marker_name = row["Marker Name"]
        length = row["Length"]
        bac = row["BAC"]
        nam_marker = row["NAM Marker"]
        poly_type = row["Poly Type"]
        ref_seq = row["Ref Seq"]
        strand = row["Strand"]
        allele = row["Allele"]
        marker_comments = row["Marker Comments"]

        if primer_f_id != '':
            if primer_f_id in primer_id_table:
                primer_f_table_id = primer_id_table[primer_f_id][0]
            else:
                error_count = error_count + 1
                primer_f_table_id = 1
                primer_error[(marker_id, interval_type, interval_name, interval_comments, chromosome, genetic_bin, physical_map, start_physical_pos, end_physical_pos, start_genetic_pos, end_genetic_pos, marker_physical_pos, marker_genetic_pos, primer_f_id, primer_r_id, marker_name, length, bac, nam_marker, poly_type, ref_seq, strand, allele, marker_comments)] = error_count

        if primer_r_id != '':
            if primer_r_id in primer_id_table:
                primer_r_table_id = primer_id_table[primer_r_id][0]
            else:
                error_count = error_count + 1
                primer_r_table_id = 1
                primer_error[(marker_id, interval_type, interval_name, interval_comments, chromosome, genetic_bin, physical_map, start_physical_pos, end_physical_pos, start_genetic_pos, end_genetic_pos, marker_physical_pos, marker_genetic_pos, primer_f_id, primer_r_id, marker_name, length, bac, nam_marker, poly_type, ref_seq, strand, allele, marker_comments)] = error_count

        map_feature_start_hash = chromosome + genetic_bin + physical_map + start_genetic_position + start_physical_position + interval_comments
        if map_feature_start_hash not in map_feature_hash_table:
            map_feature_hash_table[map_feature_start_hash] = map_feature_table_id
            map_feature_new[(map_feature_table_id, chromosome, genetic_bin, physical_map, start_genetic_position, start_physical_position, interval_comments)] = map_feature_table_id
            map_feature_table_id = map_feature_table_id + 1
        else:
            map_feature_hash_exists[(chromosome, genetic_bin, physical_map, start_genetic_position, start_physical_position, interval_comments)] = map_feature_table_id

        map_feature_end_hash = chromosome + genetic_bin + physical_map + end_genetic_position + end_physical_position + interval_comments
        if map_feature_end_hash not in map_feature_hash_table:
            map_feature_hash_table[map_feature_end_hash] = map_feature_table_id
            map_feature_new[(map_feature_table_id, chromosome, genetic_bin, physical_map, end_genetic_position, end_physical_position, interval_comments)] = map_feature_table_id
            map_feature_table_id = map_feature_table_id + 1
        else:
            map_feature_hash_exists[(chromosome, genetic_bin, physical_map, end_genetic_position, end_physical_position, interval_comments)] = map_feature_table_id

        marker_map_feature_hash = chromosome + genetic_bin + physical_map + marker_genetic_position + marker_physical_position + ''
        if marker_map_feature_hash not in map_feature_hash_table:
            map_feature_hash_table[marker_map_feature_hash] = map_feature_table_id
            map_feature_new[(map_feature_table_id, chromosome, genetic_bin, physical_map, marker_genetic_position, marker_physical_position, interval_comments)] = map_feature_table_id
            map_feature_table_id = map_feature_table_id + 1
        else:
            map_feature_hash_exists[(chromosome, genetic_bin, physical_map, marker_genetic_position, marker_physical_position, interval_comments)] = map_feature_table_id

        map_feature_interval_hash = str(map_feature_hash_table[map_feature_start_hash]) + str(map_feature_hash_table[map_feature_end_hash]) + interval_type + interval_name + interval_comments
        if map_feature_interval_hash not in map_feature_hash_table:
            map_feature_interval_hash_table[map_feature_interval_hash] = map_feature_interval_table_id
            map_feature_interval_new[(map_feature_interval_table_id, map_feature_hash_table[map_feature_start_hash], map_feature_hash_table[map_feature_end_hash], interval_type, interval_name, interval_comments)] = map_feature_interval_table_id
            map_feature_interval_table_id = map_feature_interval_table_id + 1
        else:
            map_feature_interval_hash_exists[(map_feature_hash_table[map_feature_start_hash], map_feature_hash_table[map_feature_end_hash], interval_type, interval_name, interval_comments)] = map_feature_interval_table_id

        marker_hash = str(map_feature_interval_hash_table[map_feature_interval_hash]) + str(map_feature_hash_table[marker_map_feature_hash]) + str(primer_f_table_id) + str(primer_r_table_id) + marker_id + marker_name + length + bac + nam_marker + poly_type + ref_seq + marker_comments + strand + allele
        if marker_hash not in marker_hash_table and marker_id not in marker_id_table:
            marker_hash_table[marker_hash] = marker_table_id
            marker_id_table[marker_id] = (map_feature_interval_hash_table[map_feature_interval_hash], map_feature_hash_table[marker_map_feature_hash], primer_f_table_id, primer_r_table_id, marker_id, marker_name, length, bac, nam_marker, poly_type, ref_seq, marker_comments, strand, allele)
            marker_new[(marker_table_id, map_feature_interval_hash_table[map_feature_interval_hash], map_feature_hash_table[marker_map_feature_hash], primer_f_table_id, primer_r_table_id, marker_id, marker_name, length, bac, nam_marker, poly_type, ref_seq, marker_comments, strand, allele)] = marker_table_id
            marker_table_id = marker_table_id + 1
        else:
            marker_hash_exists[(map_feature_interval_hash_table[map_feature_interval_hash], map_feature_hash_table[marker_map_feature_hash], primer_f_table_id, primer_r_table_id, marker_id, marker_name, length, bac, nam_marker, poly_type, ref_seq, marker_comments, strand, allele)] = marker_table_id
            error_count = error_count + 1;

    end = time.clock()
    stats = {}
    stats[("Time: %s" % (end-start), "Errors: %s" % (error_count))] = error_count

    results_dict = {}
    results_dict['marker_new'] = marker_new
    results_dict['map_feature_new'] = map_feature_new
    results_dict['map_feature_interval_new'] = map_feature_interval_new
    results_dict['marker_hash_exists'] = marker_hash_exists
    results_dict['map_feature_hash_exists'] = map_feature_hash_exists
    results_dict['map_feature_interval_hash_exists'] = map_feature_interval_hash_exists
    results_dict['primer_error'] = primer_error
    results_dict['stats'] = stats
    return results_dict

def marker_loader_prep_output(results_dict, new_upload_exp, template_type):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s_%s_prep.csv"' % (new_upload_exp, template_type)
    writer = csv.writer(response)
    writer.writerow(['Stats'])
    writer.writerow([''])
    for key in results_dict['stats'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Marker Table'])
    writer.writerow(['marker_table_id', 'map_feature_interval_table_id', 'marker_map_feature_table_id', 'primer_f_table_id', 'primer_r_table_id', 'marker_id', 'marker_name', 'length', 'bac', 'nam_marker', 'poly_type', 'ref_seq', 'comments', 'strand', 'allele'])
    for key in results_dict['marker_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Map Feature Table'])
    writer.writerow(['map_feature_table_id', 'chromosome', 'genetic_bin', 'physical_map', 'genetic_position', 'physical_position', 'comments'])
    for key in results_dict['map_feature_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Map Feature Interval Table'])
    writer.writerow(['map_feature_interval_table_id', 'map_feature_start_id', 'map_feature_end_id', 'interval_type', 'interval_name', 'comments'])
    for key in results_dict['map_feature_interval_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['---------------------------------------------------------------------------------------------------'])
    writer.writerow([''])
    writer.writerow(['Marker Entry Already Exists'])
    for key in results_dict['marker_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Map Feature Already Exists'])
    for key in results_dict['map_feature_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Map Feature Interval Already Exists'])
    for key in results_dict['map_feature_interval_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Primer Error'])
    for key in results_dict['primer_error'].keys():
        writer.writerow(key)
    return response

def marker_loader(results_dict):
    try:
        for key in results_dict['map_feature_new'].keys():
            try:
                with transaction.atomic():
                    new_primer = MapFeature.objects.create(id=key[0], chromosome=key[1], genetic_bin=key[2], physical_map=key[3], genetic_position=key[4], physical_position=key[5], comments=key[6])
            except Exception as e:
                print("MapFeature Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['map_feature_interval_new'].keys():
            try:
                with transaction.atomic():
                    new_primer = MapFeatureInterval.objects.create(id=key[0], map_feature_start_id=key[1], map_feature_end_id=key[2], interval_type=key[3], interval_name=key[4], comments=key[5])
            except Exception as e:
                print("MapFeatureInterval Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['marker_new'].keys():
            try:
                with transaction.atomic():
                    new_primer = Marker.objects.create(id=key[0], map_feature_interval_id=key[1], marker_map_feature_id=key[2], primer_f_id=key[3], primer_r_id=key[4], marker_id=key[5], marker_name=key[6], length=key[7], bac=key[8], nam_marker=key[9], poly_type=key[10], ref_seq=key[11], comments=key[12], strand=key[13], allele=key[13])
            except Exception as e:
                print("Marker Error: %s %s" % (e.message, e.args))
                return False
    except Exception as e:
        print("Error: %s %s" % (e.message, e.args))
        return False
    return True

def map_feature_interval_loader_prep(upload_file, user):
    start = time.clock()

    map_feature_new = OrderedDict({})
    #--- Key = (map_feature_table_id, chromosome, genetic_bin, physical_map, genetic_position, physical_position, comments)
    #--- Value = (map_feature_table_id)
    map_feature_interval_new = OrderedDict({})
    #--- Key = (map_feature_interval_table_id, map_feature_start_id, map_feature_end_id, interval_type, interval_name, comments)
    #--- Value = (map_feature_table_id)

    map_feature_hash_table = loader_db_mirror.map_feature_hash_mirror()
    map_feature_interval_hash_table = loader_db_mirror.map_feature_interval_hash_mirror()
    map_feature_table_id = loader_db_mirror.map_feature_table_id_mirror()
    map_feature_interval_table_id = loader_db_mirror.map_feature_interval_table_id_mirror()

    error_count = 0
    map_feature_hash_exists = OrderedDict({})
    map_feature_interval_hash_exists = OrderedDict({})

    map_feature_file = csv.DictReader(codecs.iterdecode(upload_file, 'utf-8'))
    for row in map_feature_file:
        interval_name = row["Interval Name"]
        interval_type = row["Interval Type"]
        interval_comments = row["Interval Comments"]
        chromosome = row["Chromosome"]
        genetic_bin = row["Genetic Bin"]
        physical_map = row["Physical Map"]
        start_physical_position = row["Start Physical Position"]
        end_physical_position = row["End Physical Position"]
        start_genetic_position = row["Start Genetic Position"]
        end_genetic_position = row["End Genetic Position"]

        map_feature_start_hash = chromosome + genetic_bin + physical_map + start_genetic_position + start_physical_position + interval_comments
        if map_feature_start_hash not in map_feature_hash_table:
            map_feature_hash_table[map_feature_start_hash] = map_feature_table_id
            map_feature_new[(map_feature_table_id, chromosome, genetic_bin, physical_map, start_genetic_position, start_physical_position, interval_comments)] = map_feature_table_id
            map_feature_table_id = map_feature_table_id + 1
        else:
            map_feature_hash_exists[(chromosome, genetic_bin, physical_map, start_genetic_position, start_physical_position, interval_comments)] = map_feature_table_id

        map_feature_end_hash = chromosome + genetic_bin + physical_map + end_genetic_position + end_physical_position + interval_comments
        if map_feature_end_hash not in map_feature_hash_table:
            map_feature_hash_table[map_feature_end_hash] = map_feature_table_id
            map_feature_new[(map_feature_table_id, chromosome, genetic_bin, physical_map, end_genetic_position, end_physical_position, interval_comments)] = map_feature_table_id
            map_feature_table_id = map_feature_table_id + 1
        else:
            map_feature_hash_exists[(chromosome, genetic_bin, physical_map, end_genetic_position, end_physical_position, interval_comments)] = map_feature_table_id

        map_feature_interval_hash = str(map_feature_hash_table[map_feature_start_hash]) + str(map_feature_hash_table[map_feature_end_hash]) + interval_type + interval_name + interval_comments
        if map_feature_interval_hash not in map_feature_hash_table:
            map_feature_interval_hash_table[map_feature_interval_hash] = map_feature_interval_table_id
            map_feature_interval_new[(map_feature_interval_table_id, map_feature_hash_table[map_feature_start_hash], map_feature_hash_table[map_feature_end_hash], interval_type, interval_name, interval_comments)] = map_feature_interval_table_id
            map_feature_interval_table_id = map_feature_interval_table_id + 1
        else:
            map_feature_interval_hash_exists[(map_feature_hash_table[map_feature_start_hash], map_feature_hash_table[map_feature_end_hash], interval_type, interval_name, interval_comments)] = map_feature_interval_table_id

    end = time.clock()
    stats = {}
    stats[("Time: %s" % (end-start), "Errors: %s" % (error_count))] = error_count

    results_dict = {}
    results_dict['map_feature_new'] = map_feature_new
    results_dict['map_feature_interval_new'] = map_feature_interval_new
    results_dict['map_feature_hash_exists'] = map_feature_hash_exists
    results_dict['map_feature_interval_hash_exists'] = map_feature_interval_hash_exists
    results_dict['stats'] = stats
    return results_dict

def map_feature_interval_loader_prep_output(results_dict, new_upload_exp, template_type):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s_%s_prep.csv"' % (new_upload_exp, template_type)
    writer = csv.writer(response)
    writer.writerow(['Stats'])
    writer.writerow([''])
    for key in results_dict['stats'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Map Feature Table'])
    writer.writerow(['map_feature_table_id', 'chromosome', 'genetic_bin', 'physical_map', 'genetic_position', 'physical_position', 'comments'])
    for key in results_dict['map_feature_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Map Feature Interval Table'])
    writer.writerow(['map_feature_interval_table_id', 'map_feature_start_id', 'map_feature_end_id', 'interval_type', 'interval_name', 'comments'])
    for key in results_dict['map_feature_interval_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['---------------------------------------------------------------------------------------------------'])
    writer.writerow([''])
    writer.writerow(['Map Feature Already Exists'])
    for key in results_dict['map_feature_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Map Feature Interval Already Exists'])
    for key in results_dict['map_feature_interval_hash_exists'].keys():
        writer.writerow(key)
    return response

def map_feature_interval_loader(results_dict):
    try:
        for key in results_dict['map_feature_new'].keys():
            try:
                with transaction.atomic():
                    new_primer = MapFeature.objects.create(id=key[0], chromosome=key[1], genetic_bin=key[2], physical_map=key[3], genetic_position=key[4], physical_position=key[5], comments=key[6])
            except Exception as e:
                print("MapFeature Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['map_feature_interval_new'].keys():
            try:
                with transaction.atomic():
                    new_primer = MapFeatureInterval.objects.create(id=key[0], map_feature_start_id=key[1], map_feature_end_id=key[2], interval_type=key[3], interval_name=key[4], comments=key[5])
            except Exception as e:
                print("MapFeatureInterval Error: %s %s" % (e.message, e.args))
                return False
    except Exception as e:
        print("Error: %s %s" % (e.message, e.args))
        return False
    return True

def nils_loader_prep(upload_file, user):
    start = time.clock()

    map_feature_new = OrderedDict({})
    #--- Key = (map_feature_table_id, chromosome, genetic_bin, physical_map, genetic_position, physical_position, comments)
    #--- Value = (map_feature_table_id)
    map_feature_interval_new = OrderedDict({})
    #--- Key = (map_feature_interval_table_id, map_feature_start_id, map_feature_end_id, interval_type, interval_name, comments)
    #--- Value = (map_feature_table_id)
    stock_new = OrderedDict({})
    #--- Key = (stock_id, passport_id, seed_id, seed_name, cross_type, pedigree, stock_status, stock_date, inoculated, comments)
    #--- Value = (stock_id)
    obs_tracker_new = OrderedDict({})
    #--- Key = (obs_tracker_id, obs_entity_type, experiment_id, field_id, glycerol_stock_id, isolate_id, location_id, maize_sample_id, obs_culture_id, obs_dna_id, obs_env_id, obs_extract_id, obs_microbe_id, obs_plant_id, obs_plate_id, obs_row_id, obs_sample_id, obs_tissue_id, obs_well_id, stock_id, user_id)
    #--- Value = (obs_tracker_id)
    obs_tracker_source_new = OrderedDict({})
    #--- Key = (obs_tracker_source_id, source_obs_id, target_obs_id)
    #--- Value = (obs_tracker_source_id)
    marker_new = OrderedDict({})
    #--- Key = (marker_table_id, map_feature_interval_id, marker_map_feature_id, primer_f_id, primer_r_id, marker_id, marker_name, length, bac, nam_marker, poly_type, ref_seq, comments, strand, allele)
    #--- Value = (marker_table_id)
    measurement_parameter_new = OrderedDict({})
    #--- Key = (measurement_parameter_id, parameter, parameter_type, unit_of_measure, protocol, trait_id_buckler, marker_id)
    #--- Value = (measurement_parameter_id)
    measurement_new = OrderedDict({})
    #--- Key = (measurement_id, obs_tracker_id, measurement_parameter_id, user_id, time_of_measurement, value, comments)
    #--- Value = (measurement_id)

    measurement_hash_table = loader_db_mirror.measurement_hash_mirror()
    measurement_id = loader_db_mirror.measurement_id_mirror()
    marker_hash_table = loader_db_mirror.marker_hash_mirror()
    marker_id_table = loader_db_mirror.marker_id_mirror()
    marker_table_id = loader_db_mirror.marker_table_id_mirror()
    user_hash_table = loader_db_mirror.user_hash_mirror()
    stock_hash_table = loader_db_mirror.stock_hash_mirror()
    stock_id = loader_db_mirror.stock_id_mirror()
    obs_tracker_hash_table = loader_db_mirror.obs_tracker_hash_mirror()
    obs_tracker_id = loader_db_mirror.obs_tracker_id_mirror()
    seed_id_table = loader_db_mirror.seed_id_mirror()
    obs_tracker_source_hash_table = loader_db_mirror.obs_tracker_source_hash_mirror()
    obs_tracker_source_id = loader_db_mirror.obs_tracker_source_id_mirror()
    obs_tracker_seed_id_table = loader_db_mirror.obs_tracker_seed_id_mirror()
    map_feature_hash_table = loader_db_mirror.map_feature_hash_mirror()
    map_feature_interval_hash_table = loader_db_mirror.map_feature_interval_hash_mirror()
    map_feature_table_id = loader_db_mirror.map_feature_table_id_mirror()
    map_feature_interval_table_id = loader_db_mirror.map_feature_interval_table_id_mirror()
    measurement_parameter_hash_table = loader_db_mirror.measurement_parameter_hash_mirror()
    measurement_parameter_id = loader_db_mirror.measurement_parameter_id_mirror()

    error_count = 0
    stock_hash_exists = OrderedDict({})
    seed_id_errors = OrderedDict({})
    obs_tracker_hash_exists = OrderedDict({})
    obs_tracker_source_hash_exists = OrderedDict({})
    map_feature_hash_exists = OrderedDict({})
    map_feature_interval_hash_exists = OrderedDict({})
    marker_hash_exists = OrderedDict({})
    measurement_parameter_hash_exists = OrderedDict({})
    measurement_hash_exists = OrderedDict({})

    nils_file = csv.DictReader(codecs.iterdecode(upload_file, 'utf-8'))
    for row in nils_file:
        interval_name = row["NIL Name"]
        nil_seed_id = row["NIL Seed ID"]
        introgression_parent = row["Introgression Parent Seed ID"]
        backcross_parent = row["Backcross Parent Seed ID"]
        num_introgressions = row["Number of Introgressions"]
        physical_map = row["AGP Version"]
        chromosome = row["Chromosome"]
        start_physical_position = row["Start Physical Position"]
        end_physical_position = row["End Physical Position"]

        introgression_parent_stock_id = 1
        if (introgression_parent not in seed_id_table):
            seed_id_errors[(introgression_parent)] = stock_id
            error_count = error_count + 1
        else:
            introgression_parent_stock_id = seed_id_table[introgression_parent][0]
        backcross_parent_stock_id = 1
        if (backcross_parent not in seed_id_table):
            seed_id_errors[(backcross_parent)] = stock_id
            error_count = error_count + 1
        else:
            backcross_parent_stock_id = seed_id_table[backcross_parent][0]

        if nil_seed_id not in seed_id_table:
            stock_hash = str(1) + nil_seed_id + nil_seed_id + 'introgression' + '' + 'available' + '' + '0' + ''
            if stock_hash not in stock_hash_table:
                stock_hash_table[stock_hash] = stock_id
                stock_new[(stock_id, 1, nil_seed_id, nil_seed_id, 'introgression', '', 'available', '', '0', '')] = stock_id
                seed_id_table[nil_seed_id] = (stock_id, 1, nil_seed_id, nil_seed_id, 'introgression', '', 'available', '', '0', '')
                stock_id = stock_id + 1
            else:
                stock_hash_exists[(1, nil_seed_id, nil_seed_id, 'introgression', '', 'available', '', '0', '')] = stock_id

        obs_tracker_stock_hash = 'stock' + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(1) + str(seed_id_table[nil_seed_id][0]) + str(user_hash_table[user.username])
        if obs_tracker_stock_hash not in obs_tracker_hash_table:
            obs_tracker_hash_table[obs_tracker_stock_hash] = obs_tracker_id
            obs_tracker_new[(obs_tracker_id, 'stock', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, seed_id_table[nil_seed_id][0], user_hash_table[user.username])] = obs_tracker_id
            obs_tracker_id = obs_tracker_id + 1
        else:
            obs_tracker_hash_exists[('stock', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, seed_id_table[nil_seed_id][0], user_hash_table[user.username])] = obs_tracker_id

        if obs_tracker_stock_hash in obs_tracker_hash_table:
            temp_targetobs_id = obs_tracker_hash_table[obs_tracker_stock_hash]
        else:
            temp_targetobs_id = 1
            error_count = error_count + 1

        obs_tracker_source_hash = str(introgression_parent_stock_id) + str(temp_targetobs_id) + 'stock_from_introgression_parent'
        if obs_tracker_source_hash not in obs_tracker_source_hash_table:
            obs_tracker_source_hash_table[obs_tracker_source_hash] = obs_tracker_source_id
            obs_tracker_source_new[(obs_tracker_source_id, introgression_parent_stock_id, temp_targetobs_id, 'stock_from_introgression_parent')] = obs_tracker_source_id
            obs_tracker_source_id = obs_tracker_source_id + 1
        else:
            obs_tracker_source_hash_exists[(introgression_parent_stock_id, temp_targetobs_id, 'stock_from_introgression_parent')] = obs_tracker_source_id

        obs_tracker_source_hash = str(backcross_parent_stock_id) + str(temp_targetobs_id) + 'stock_from_backcross_parent'
        if obs_tracker_source_hash not in obs_tracker_source_hash_table:
            obs_tracker_source_hash_table[obs_tracker_source_hash] = obs_tracker_source_id
            obs_tracker_source_new[(obs_tracker_source_id, backcross_parent_stock_id, temp_targetobs_id, 'stock_from_backcross_parent')] = obs_tracker_source_id
            obs_tracker_source_id = obs_tracker_source_id + 1
        else:
            obs_tracker_source_hash_exists[(backcross_parent_stock_id, temp_targetobs_id, 'stock_from_backcross_parent')] = obs_tracker_source_id

        map_feature_start_hash = chromosome + '' + physical_map + '' + start_physical_position + ''
        if map_feature_start_hash not in map_feature_hash_table:
            map_feature_hash_table[map_feature_start_hash] = map_feature_table_id
            map_feature_new[(map_feature_table_id, chromosome, '', physical_map, '', start_physical_position, '')] = map_feature_table_id
            map_feature_table_id = map_feature_table_id + 1
        else:
            map_feature_hash_exists[(chromosome, '', physical_map, '', start_physical_position, '')] = map_feature_table_id

        map_feature_end_hash = chromosome + '' + physical_map + '' + end_physical_position + ''
        if map_feature_end_hash not in map_feature_hash_table:
            map_feature_hash_table[map_feature_end_hash] = map_feature_table_id
            map_feature_new[(map_feature_table_id, chromosome, '', physical_map, '', end_physical_position, '')] = map_feature_table_id
            map_feature_table_id = map_feature_table_id + 1
        else:
            map_feature_hash_exists[(chromosome, '', physical_map, '', end_physical_position, '')] = map_feature_table_id

        map_feature_interval_hash = str(map_feature_hash_table[map_feature_start_hash]) + str(map_feature_hash_table[map_feature_end_hash]) + 'introgression' + interval_name + ''
        if map_feature_interval_hash not in map_feature_hash_table:
            map_feature_interval_hash_table[map_feature_interval_hash] = map_feature_interval_table_id
            map_feature_interval_new[(map_feature_interval_table_id, map_feature_hash_table[map_feature_start_hash], map_feature_hash_table[map_feature_end_hash], 'introgression', interval_name, '')] = map_feature_interval_table_id
            map_feature_interval_table_id = map_feature_interval_table_id + 1
        else:
            map_feature_interval_hash_exists[(map_feature_hash_table[map_feature_start_hash], map_feature_hash_table[map_feature_end_hash], 'introgression', interval_name, '')] = map_feature_interval_table_id

        length = int(end_physical_position) - int(start_physical_position)
        marker_hash = str(map_feature_interval_hash_table[map_feature_interval_hash]) + str(1) + str(1) + str(1) + interval_name + interval_name + str(length) + '' + '' + 'introgression' + '' + '' + '' + ''
        if marker_hash not in marker_hash_table and interval_name not in marker_id_table:
            marker_hash_table[marker_hash] = marker_table_id
            marker_id_table[interval_name] = (map_feature_interval_hash_table[map_feature_interval_hash], 1, 1, 1, interval_name, interval_name, length, '', '', 'introgression', '', '', '', '')
            marker_new[(marker_table_id, map_feature_interval_hash_table[map_feature_interval_hash], 1, 1, 1, interval_name, interval_name, length, '', '', 'introgression', '', '', '', '')] = marker_table_id
            marker_table_id = marker_table_id + 1
        else:
            marker_hash_exists[(map_feature_interval_hash_table[map_feature_interval_hash], 1, 1, 1, interval_name, interval_name, length, '', '', 'introgression', '', '', '', '')] = marker_table_id
            if interval_name in marker_id_table:
                marker_hash_table[marker_hash] = marker_id_table[interval_name][0]

        measurement_parameter_hash = interval_name + 'introgression' + 'boolean' + '' + '' + str(marker_hash_table[marker_hash])
        if measurement_parameter_hash not in measurement_parameter_hash_table:
            measurement_parameter_hash_table[measurement_parameter_hash] = measurement_parameter_id
            measurement_parameter_new[(measurement_parameter_id, interval_name, 'introgression', 'boolean', '', '', marker_hash_table[marker_hash])] = measurement_parameter_id
            measurement_parameter_id = measurement_parameter_id + 1
        else:
            measurement_parameter_hash_exists[(interval_name, 'introgression', 'boolean', '', '', marker_hash_table[marker_hash])] = measurement_parameter_id

        measurement_hash = str(obs_tracker_hash_table[obs_tracker_stock_hash]) + str(user_hash_table[user.username]) + str(measurement_parameter_hash_table[measurement_parameter_hash]) + '' + '1' + "Introgressions: %s" % (num_introgressions)
        if measurement_hash not in measurement_hash_table:
            measurement_hash_table[measurement_hash] = measurement_id
            measurement_new[(measurement_id, obs_tracker_hash_table[obs_tracker_stock_hash], user_hash_table[user.username], measurement_parameter_hash_table[measurement_parameter_hash], '', '1', "Introgressions: %s" % (num_introgressions))] = measurement_id
            measurement_id = measurement_id + 1
        else:
            measurement_hash_exists[(obs_tracker_hash_table[obs_tracker_stock_hash], user_hash_table[user.username], measurement_parameter_hash_table[measurement_parameter_hash], '', '1', "Introgressions: %s" % (num_introgressions))] = measurement_id

    end = time.clock()
    stats = {}
    stats[("Time: %s" % (end-start), "Errors: %s" % (error_count))] = error_count

    results_dict = {}
    results_dict['map_feature_new'] = map_feature_new
    results_dict['map_feature_interval_new'] = map_feature_interval_new
    results_dict['stock_new'] = stock_new
    results_dict['obs_tracker_new'] = obs_tracker_new
    results_dict['obs_tracker_source_new'] = obs_tracker_source_new
    results_dict['marker_new'] = marker_new
    results_dict['measurement_parameter_new'] = measurement_parameter_new
    results_dict['measurement_new'] = measurement_new
    results_dict['map_feature_hash_exists'] = map_feature_hash_exists
    results_dict['map_feature_interval_hash_exists'] = map_feature_interval_hash_exists
    results_dict['stock_hash_exists'] = stock_hash_exists
    results_dict['obs_tracker_hash_exists'] = obs_tracker_hash_exists
    results_dict['obs_tracker_source_hash_exists'] = obs_tracker_source_hash_exists
    results_dict['marker_hash_exists'] = marker_hash_exists
    results_dict['measurement_parameter_hash_exists'] = measurement_parameter_hash_exists
    results_dict['measurement_hash_exists'] = measurement_hash_exists
    results_dict['seed_id_errors'] = seed_id_errors
    results_dict['stats'] = stats
    return results_dict

def nils_loader_prep_output(results_dict, new_upload_exp, template_type):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s_%s_prep.csv"' % (new_upload_exp, template_type)
    writer = csv.writer(response)
    writer.writerow(['Stats'])
    writer.writerow([''])
    for key in results_dict['stats'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Stock Table'])
    writer.writerow(['stock_id', 'passport_id', 'seed_id', 'seed_name', 'cross_type', 'pedigree', 'stock_status', 'stock_date', 'inoculated', 'comments'])
    for key in results_dict['stock_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTracker Table'])
    writer.writerow(['obs_tracker_id', 'obs_entity_type', 'experiment_id', 'field_id', 'glycerol_stock_id', 'isolate_id', 'location_id', 'maize_sample_id', 'obs_culture_id', 'obs_dna_id', 'obs_env_id', 'obs_extract_id', 'obs_microbe_id', 'obs_plant_id', 'obs_plate_id', 'obs_row_id', 'obs_sample_id', 'obs_tissue_id', 'obs_well_id', 'stock_id', 'user_id'])
    for key in results_dict['obs_tracker_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New ObsTrackerSource Table'])
    writer.writerow(['obs_tracker_source_id', 'source_obs_id', 'target_obs_id', 'relationship'])
    for key in results_dict['obs_tracker_source_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New MapFeature Table'])
    writer.writerow(['map_feature_id', 'chromosome', 'genetic_bin', 'physical_map', 'genetic_position', 'physical_position', 'comments'])
    for key in results_dict['map_feature_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New MapFeature Interval Table'])
    writer.writerow(['map_feature_interval_id', 'map_feature_start_id', 'map_feature_end_id', 'interval_type', 'interval_name', 'comments'])
    for key in results_dict['map_feature_interval_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Marker Table'])
    writer.writerow(['marker_table_id', 'map_feature_interval_id', 'marker_map_feature_id', 'primer_f_id', 'primer_r_id', 'marker_id', 'marker_name', 'length', 'bac', 'nam_marker', 'poly_type', 'ref_seq', 'comments', 'strand', 'allele'])
    for key in results_dict['marker_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New MeasurementParameter Table'])
    writer.writerow(['measurement_parameter_id', 'parameter', 'parameter_type', 'unit_of_measure', 'protocol', 'trait_id_buckler', 'marker_id'])
    for key in results_dict['measurement_parameter_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['New Measurement Table'])
    writer.writerow(['measurement_id', 'obs_tracker_id', 'user_id', 'measurement_parameter_id', 'time_of_measurement', 'value', 'comments'])
    for key in results_dict['measurement_new'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['---------------------------------------------------------------------------------------------------'])
    writer.writerow([''])
    writer.writerow(['Seed ID Errors'])
    for key in results_dict['seed_id_errors'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Stock Entries Already Exist'])
    for key in results_dict['stock_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTracker Entries Already Exist'])
    for key in results_dict['obs_tracker_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['ObsTrackerSource Entries Already Exist'])
    for key in results_dict['obs_tracker_source_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['MapFeature Entries Already Exist'])
    for key in results_dict['map_feature_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['MapFeatureInterval Entries Already Exist'])
    for key in results_dict['map_feature_interval_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Marker Entries Already Exist'])
    for key in results_dict['marker_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['MeasurementParameter Entries Already Exist'])
    for key in results_dict['measurement_parameter_hash_exists'].keys():
        writer.writerow(key)
    writer.writerow([''])
    writer.writerow(['Measurement Entries Already Exist'])
    for key in results_dict['measurement_hash_exists'].keys():
        writer.writerow(key)

    return response

def nils_loader(results_dict):
    try:
        for key in results_dict['stock_new'].keys():
            try:
                with transaction.atomic():
                    new_stock, create = Stock.objects.update_or_create(id=key[0], seed_id=key[2], defaults= { 'passport_id':key[1], 'seed_name':key[3], 'cross_type':key[4], 'pedigree':key[5], 'stock_status':key[6], 'stock_date':key[7], 'inoculated':key[8], 'comments':key[9] } )
            except Exception as e:
                print("Stock Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = ObsTracker.objects.create(id=key[0], obs_entity_type=key[1], experiment_id=key[2], field_id=key[3], glycerol_stock_id=key[4], isolate_id=key[5], location_id=key[6], maize_sample_id=key[7], obs_culture_id=key[8], obs_dna_id=key[9], obs_env_id=key[10], obs_extract_id=key[11], obs_microbe_id=key[12], obs_plant_id=key[13], obs_plate_id=key[14], obs_row_id=key[15], obs_sample_id=key[16], obs_tissue_id=key[17], obs_well_id=key[18], stock_id=key[19], user_id=key[20])
            except Exception as e:
                print("ObsTracker Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['obs_tracker_source_new'].keys():
            try:
                with transaction.atomic():
                    new_stock = ObsTrackerSource.objects.create(id=key[0], source_obs_id=key[1], target_obs_id=key[2], relationship=key[3])
            except Exception as e:
                print("ObsTrackerSource Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['map_feature_new'].keys():
            try:
                with transaction.atomic():
                    new_mf = MapFeature.objects.create(id=key[0], chromosome=key[1], genetic_bin=key[2], physical_map=key[3], genetic_position=key[4], physical_position=key[5], comments=key[6])
            except Exception as e:
                print("MapFeature Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['map_feature_interval_new'].keys():
            try:
                with transaction.atomic():
                    new_mfi = MapFeatureInterval.objects.create(id=key[0], map_feature_start_id=key[1], map_feature_end_id=key[2], interval_type=key[3], interval_name=key[4], comments=key[5])
            except Exception as e:
                print("MapFeatureInterval Error: %s %s" % (e.message, e.args))
                return False
                'marker_table_id', 'map_feature_interval_id', 'marker_map_feature_id', 'primer_f_id', 'primer_r_id', 'marker_id', 'marker_name', 'length', 'bac', 'nam_marker', 'poly_type', 'ref_seq', 'comments', 'strand', 'allele'
        for key in results_dict['marker_new'].keys():
            try:
                with transaction.atomic():
                    new_m = Marker.objects.create(id=key[0], map_feature_interval_id=key[1], marker_map_feature_id=key[2], primer_f_id=key[3], primer_r_id=key[4], marker_id=key[5], marker_name=key[6], length=key[7], bac=key[8], nam_marker=key[9], poly_type=key[10], ref_seq=key[11], comments=key[12], strand=key[13], allele=key[14])
            except Exception as e:
                print("Marker Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['measurement_parameter_new'].keys():
            try:
                with transaction.atomic():
                    new_m = MeasurementParameter.objects.create(id=key[0], parameter=key[1], parameter_type=key[2], unit_of_measure=key[3], protocol=key[4], trait_id_buckler=key[5], marker_id=key[6])
            except Exception as e:
                print("MeasurementParameter Error: %s %s" % (e.message, e.args))
                return False
        for key in results_dict['measurement_new'].keys():
            try:
                with transaction.atomic():
                    new_m = Measurement.objects.create(id=key[0], obs_tracker_id=key[1], user_id=key[2], measurement_parameter_id=key[3], time_of_measurement=key[4], value=key[5], comments=key[6])
            except Exception as e:
                print("Measurement Error: %s %s" % (e.message, e.args))
                return False
    except Exception as e:
        print("Error: %s %s" % (e.message, e.args))
        return False
    return True
