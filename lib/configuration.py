import configparser
import datetime
import json
import os


def get_config():
    import os
    project_home = os.environ['PACKAGE_HOME']
    import configparser

    config = configparser.ConfigParser()
    filename = 'config.ini'
    config_file = "{home}/{filename}".format(home=project_home, filename=filename)
    config.read(config_file)
    return config


def set_config(config, type='granted_patent'):
    import os
    project_home = os.environ['PACKAGE_HOME']
    filename = 'config.ini'
    if type == 'granted_patent':
        filename = 'config.ini'
    elif type == 'application':
        filename = 'app_config.ini'
    config_file = "{home}/{filename}".format(home=project_home, filename=filename)
    with open(config_file, "w") as f:
        config.write(f)
    return config


def get_section(dag_id, task_id):
    section_lookup = {
            'granted_patent_updater':       {
                    "create_text_yearly_tables":        "Granted Patent - Database Setup",
                    "create_text_yearly_tables-upload": "Granted Patent - Database Setup",
                    "download_xml":                     "Granted Patent - Data Collection",
                    "fix_patent_ids-upload":            "Granted Patent - Data Processing",
                    "merge_db":                         "Granted Patent - Data Processing",
                    "merge_text_db":                    "Granted Patent - Data Processing",
                    "parse_text_data":                  "Granted Patent - XML Parsing",
                    "parse_xml":                        "Granted Patent - XML Parsing",
                    "process_xml":                      "Granted Patent - XML Parsing",
                    "qc_database_setup":                "Granted Patent - Database Setup (QC)",
                    "qc_merge_db":                      "Granted Patent - Data Processing (QC)",
                    "qc_merge_text_db":                 "Granted Patent - Data Processing (QC)",
                    "qc_parse_text_data":               "Granted Patent - XML Parsing (QC)",
                    "qc_upload_new":                    "Granted Patent - Data Processing (QC)",
                    "qc_withdrawn_processor":           "Granted Patent - Data Processing (QC)",
                    "upload_current":                   "Granted Patent - Data Processing",
                    "upload_database_setup":            "Granted Patent - Database Setup",
                    "withdrawn_processor":              "Granted Patent - XML Parsing"
                    },
            'pregrant_publication_updater': {
                    "create_pgpubs_database": "PGPUBS Parser - Database Setup",
                    "drop_database":          "PGPUBS Parser - Database Setup",
                    "merge_database":         "PGPUBS Parser - Data Processing",
                    "parse_pgpubs_xml":       "PGPUBS Parser - XML Parsing",
                    "post_process":           "PGPUBS Parser - Data Processing"
                    },
            '99_daily_checks':              {
                    'api_query_check': 'System Check - API'
                    }

            }

    return section_lookup[dag_id][task_id]


def get_connection_string(config, database='TEMP_UPLOAD_DB'):
    database = '{}'.format(config['PATENTSVIEW_DATABASES'][database])
    host = '{}'.format(config['DATABASE_SETUP']['HOST'])
    user = '{}'.format(config['DATABASE_SETUP']['USERNAME'])
    password = '{}'.format(config['DATABASE_SETUP']['PASSWORD'])
    port = '{}'.format(config['DATABASE_SETUP']['PORT'])
    return 'mysql+pymysql://{0}:{1}@{2}:{3}/{4}?charset=utf8mb4'.format(user, password, host, port, database)


def get_backup_command(**kwargs):
    command = "mydumper"
    config = get_current_config(**kwargs)
    conf_parameter = config['DATABASE_SETUP']['CONFIG_FILE']
    directory_parameter = "{datahome}/{database}_backup".format(datahome=config["FOLDERS"]["WORKING_FOLDER"],
                                                                database=config["PATENTSVIEW_DATABASES"]["RAW_DB"])
    database_parameter = "{database}".format(database=config["PATENTSVIEW_DATABASES"]["RAW_DB"])
    verbosity = 3
    thread = 6

    backup_command = """{command} --defaults-file={conf_parameter} -F 50 -s 5000000 -l 1999999999 -v {verbosity} -t {thread} -B {database} -o {directory_parameter} --lock-all-tables""".format(
            command=command, conf_parameter=conf_parameter, verbosity=verbosity, thread=thread,
            directory_parameter=directory_parameter, database=database_parameter)

    return backup_command


def get_loader_command(config, project_home):
    command = "bash"
    script = "{home}/lib/loader/index_optimized_loader".format(home=project_home)
    conf_parameter = "{home}/resources/sql.conf".format(home=project_home)
    directory_parameter = "{datahome}/{database}_backup".format(datahome=config["FOLDERS"]["WORKING_FOLDER"],
                                                                database=config["PATENTSVIEW_DATABASES"]["OLD_DB"])
    database_parameter = "{database}".format(database=config["PATENTSVIEW_DATABASES"]["RAW_DB"])
    verbosity = 3
    thread = 6

    loader_command = "{command} {script} {conf_parameter} -d {directory_parameter} -s {database_parameter} -v {verbosity} -t {thread} -o".format(
            command=command, script=script, conf_parameter=conf_parameter, directory_parameter=directory_parameter,
            database_parameter=database_parameter, verbosity=verbosity, thread=thread)

    return loader_command


def get_text_table_load_command(project_home, **kwargs):
    command = 'mysql'
    config = get_current_config(**kwargs)
    defaults_parameter = config['DATABASE_SETUP']['CONFIG_FILE']
    script_to_load = "{home}/resources/text_table_triggers.sql".format(home=project_home)
    database = config["PATENTSVIEW_DATABASES"]['TEMP_UPLOAD_DB']
    create_command = "{command} --defaults-file={default_param} {database} < {script_to_load}".format(command=command,
                                                                                                      default_param=defaults_parameter,
                                                                                                      database=database,
                                                                                                      script_to_load=script_to_load)
    return create_command


#
# def get_scp_copy_command(config):
#     # scp -i "$KEYFILE" "$FOLDER"/*.tsv disambiguser@ec2-52-21-62-204.compute-1.amazonaws.com:/data/disambiguation/data
#     command = 'scp'
#     keyfile_parameter = config['DISAMBIGUATION_CREDENTIALS']['KEY_FILE']
#     disambig_input_folder = '{}/disambig_inputs'.format(config['FOLDERS']['WORKING_FOLDER'])
#     source_blob = "{folder}/*.tsv".format(folder=disambig_input_folder)
#     disambig_user = 'disambiguser'
#     disambig_host = "ec2-52-21-62-204.compute-1.amazonaws.com"
#     destination = "/data/disambiguation/data"
#
#     command = "{command} -i {keyfile} {source_blob} {user}@{host}:{destination}".format(command=command,
#                                                                                         keyfile=keyfile_parameter,
#                                                                                         source_blob=source_blob,
#                                                                                         user=disambig_user,
#                                                                                         host=disambig_host,
#                                                                                         destination=destination)
#     return command
#
#
# def get_scp_download_command(config):
#     command = 'scp'
#     keyfile_parameter = config['DISAMBIGUATION_CREDENTIALS']['KEY_FILE']
#     disambig_output_folder = '{}/disambig_output/'.format(config['FOLDERS']['WORKING_FOLDER'])
#     disambig_user = 'disambiguser'
#     disambig_host = "ec2-52-21-62-204.compute-1.amazonaws.com"
#     source_files = {
#             'inventor_disambiguation.tsv': '/data/disambiguation/exp_out/inventor/disambiguation.postprocessed.tsv',
#             'assignee_disambiguation.tsv': '/data/disambiguation/exp_out/assignee/disambiguation.tsv',
#             'location_disambiguation.tsv': '/data/disambiguation/exp_out/location/location_post_processed.tsv'
#             }
#     command_strings = ["mkdir -p {disambig_output_folder}".format(disambig_output_folder=disambig_output_folder)]
#     for dest_file in source_files:
#         command_string = "{command} -i {keyfile} {user}@{host}:{source_file} {disambig_output_folder}/{dest_file} " \
#                          "".format(
#                 command=command, keyfile=keyfile_parameter, dest_file=dest_file, source_file=source_files[dest_file],
#                 user=disambig_user, host=disambig_host, disambig_output_folder=disambig_output_folder)
#         command_strings.append(command_string)
#     return " && ".join(command_strings)

def get_today_dict(type='granted_patent'):
    project_home = os.environ['PACKAGE_HOME']
    config = configparser.ConfigParser()
    config.read(project_home + '/config.ini')
    today = datetime.date.today()
    day_offset = 1
    if type == 'pgpubs':
        day_offset = 3
    offset = (today.weekday() - day_offset) % 7
    latest_release_day = today - datetime.timedelta(days=offset)
    return {
            'execution_date': latest_release_day
            }


def get_table_config(update_config):
    resources_file = "{root}/{resources}/raw_db_tables.json".format(root=update_config["FOLDERS"]["project_root"],
                                                                    resources=update_config["FOLDERS"][
                                                                        "resources_folder"])
    raw_db_table_settings = json.load(open(resources_file))
    return raw_db_table_settings


def get_required_tables(update_config):
    raw_db_table_settings = get_table_config(update_config)
    return raw_db_table_settings.keys()


def get_upload_tables_dict(update_config):
    raw_db_table_settings = get_table_config(update_config)
    required_tables = {x: False for x in raw_db_table_settings["table_list"] if
                       raw_db_table_settings["table_list"][x]["raw_data"]}
    return required_tables


def get_lookup_tables(update_config):
    raw_db_table_settings = get_table_config(update_config)
    lookup_tables = [x for x in raw_db_table_settings["table_list"] if raw_db_table_settings["table_list"][x]["lookup"]]
    return lookup_tables


def get_current_config(type='granted_patent', **kwargs):
    """
    Update config file start and end date to first and last day of the supplied week
    :param type: XML type
    :type cfg: object
    :type yr: int
    :type mth: int
    :type day: int
    :param yr: Year for start and end date
    :param mth: Month for start and end date
    :param day: Day for start and end date
    :param cfg: config to update
    :return: updated config
    """
    config = get_config()
    config_prefix = "upload_"

    if type == 'pgpubs':
        config_prefix = 'pgpubs_'
    execution_date = kwargs['execution_date']
    prev_week = datetime.timedelta(days=6)
    end_date = execution_date.strftime('%Y%m%d')
    start_date = (execution_date - prev_week).strftime('%Y%m%d')
    temp_date = execution_date.strftime('%Y%m%d')

    config['DATES'] = {
            "START_DATE": start_date,
            "END_DATE":   end_date
            }
    prefixed_string = "{prfx}{date}".format(prfx=config_prefix, date=temp_date)
    config['PATENTSVIEW_DATABASES']["TEMP_UPLOAD_DB"] = prefixed_string
    config['FOLDERS']["WORKING_FOLDER"] = "{data_root}/{prefix}".format(prefix=prefixed_string,
                                                                        data_root=config['FOLDERS']['data_root'])
    if type == 'granted_patent':
        config['FOLDERS']['granted_patent_bulk_xml_location'] = '{working_folder}/raw_data/'.format(
                working_folder=config['FOLDERS']['WORKING_FOLDER'])

    return config
