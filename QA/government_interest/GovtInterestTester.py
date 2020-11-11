import datetime

from QA.PatentDatabaseTester import PatentDatabaseTester
from lib.configuration import get_config


class GovtInterestTester(PatentDatabaseTester):
    def __init__(self, config):
        end_date = datetime.datetime.strptime(config['DATES']['END_DATE'], '%Y%m%d')
        super().__init__(config, 'NEW_DB', datetime.date(year=1976, month=1, day=1), end_date)
        self.table_config = {
                'patent_contractawardnumber': {
                        "fields": {
                                "patent_id":             {
                                        "data_type":    "varchar",
                                        "null_allowed": False,
                                        "category":     False
                                        },
                                "contract_award_number": {
                                        "data_type":    "varchar",
                                        "null_allowed": False,
                                        "category":     False
                                        }
                                }
                        },
                'patent_govintorg':           {
                        "fields": {
                                "patent_id":       {
                                        "data_type":    "varchar",
                                        "null_allowed": False,
                                        "category":     False
                                        },
                                "organization_id": {
                                        "data_type":    "int",
                                        "null_allowed": False,
                                        "category":     False
                                        }
                                }
                        },
                'government_organization':    {
                        "fields":           {
                                "organization_id": {
                                        "data_type":    "int",
                                        "null_allowed": False,
                                        "category":     False
                                        },
                                "name":            {
                                        "data_type":    "varchar",
                                        "null_allowed": False,
                                        "category":     False
                                        },
                                "level_one":       {
                                        "data_type":    "varchar",
                                        "null_allowed": False,
                                        "category":     False
                                        },
                                "level_two":       {
                                        "data_type":    "varchar",
                                        "null_allowed": True,
                                        "category":     False
                                        },
                                "level_three":     {
                                        "data_type":    "varchar",
                                        "null_allowed": True,
                                        "category":     False
                                        }
                                },
                        "related_entities": [
                                {
                                        "table":       'patent_govintorg',
                                        "source_id":   'organization_id',
                                        "destination": "organization_id"
                                        }]
                        }
                }

        self.extended_qa_data = {
                "DataMonitor_govtinterestsampler": []
                }
        self.qa_data.update(self.extended_qa_data)
        self.patent_exclusion_list.extend(['government_organization'])

    def generate_govt_int_samples(self):
        print("\tGenerating samples for Govt Interest")
        if not self.connection.open:
            self.connection.connect()
        start_dt = datetime.datetime.strptime(self.config['DATES']['START_DATE'], '%Y%m%d')
        end_dt = datetime.datetime.strptime(self.config['DATES']['END_DATE'], '%Y%m%d')
        sample_size = 25
        sample_clause = "ORDER BY RAND() limit {sample_size}".format(sample_size=sample_size)
        organization_where_combinations = {
                "All Patents":     {
                        "where_clause":  "go.`name` NOT LIKE '%United States Government%' and go.`name` is not null",
                        "sample_clause": True
                        },
                "US Govt Patents": {
                        "where_clause":  "go.`name` LIKE '%United States Government%'",
                        "sample_clause": True
                        },
                "No Organization": {
                        "where_clause":  "pg.`patent_id` is null",
                        "sample_clause": False
                        }
                }
        sampler_template = """
SELECT distinct gi.patent_id,
       gi.gi_statement,
       go.organization_id, 
       go.name,
       pca.contract_award_number
FROM   `government_interest` gi
       JOIN ({patent_clause}) p
         ON p.id = gi.patent_id
       LEFT JOIN `patent_contractawardnumber` pca
         ON pca.patent_id = gi.patent_id
       LEFT JOIN `patent_govintorg` pg
         ON pg.patent_id = gi.patent_id
       LEFT JOIN government_organization go
         ON go.`organization_id` = pg.organization_id ;        
        """
        database_type, version = self.config["DATABASE"][self.database_section].split("_")
        for sample_type in organization_where_combinations:
            where_clause = organization_where_combinations[sample_type]["where_clause"]
            patent_clause = """
            SELECT id
                   from (SELECT id
                         from patent pat
                                  join `government_interest` gi on gi.patent_id = pat.id
                                  join patent_govintorg pg on pat.id = pg.patent_id
                                  join government_organization go on pg.organization_id = go.organization_id
                         where date BETWEEN '{start_dt}' AND '{end_dt}' and {where_clause}
                        ) x
                   """.format(start_dt=start_dt, end_dt=end_dt, where_clause=where_clause)
            current_patent_clause = patent_clause
            if organization_where_combinations[sample_type]["sample_clause"]:
                current_patent_clause = "{patent_clause} {sample_clause}".format(patent_clause=patent_clause,
                                                                                 sample_clause=sample_clause)
            else:
                current_patent_clause = current_patent_clause.replace(" join", " left join")
                current_patent_clause = current_patent_clause.replace("left join `government_interest`",
                                                                      " join `government_interest`", )
            sampler_query = sampler_template.format(patent_clause=current_patent_clause, where_clause=where_clause)
            with self.connection.cursor() as gov_int_cursor:
                gov_int_cursor.execute(sampler_query)
                for gov_int_row in gov_int_cursor:
                    self.qa_data['DataMonitor_govtinterestsampler'].append({
                            'sample_type':     sample_type,
                            "database_type":   database_type,
                            'update_version':  version,
                            'patent_id':       gov_int_row[0],
                            'gov_int_stmt':    gov_int_row[1],
                            'patent_contract_award_number':
                                               gov_int_row[
                                                   4],
                            'organization_id': gov_int_row[2],
                            'organization':    gov_int_row[3]
                            })

    def runTests(self):
        super(GovtInterestTester, self).runTests()
        self.generate_govt_int_samples()
        self.save_qa_data()


def begin_gi_test(config):
    qc = GovtInterestTester(config)
    qc.runTests()


if __name__ == '__main__':
    begin_gi_test(get_config())
