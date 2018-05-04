import csv
import json
from os.path import isfile, join
from os import listdir
import os

# folder path 
gt_folder = "/tmp2/KDDCUP2018/daily_ground_truth/"
prd_folder = "/tmp2/KDDCUP2018/public_submission/"

# define result
json_result = []

# load csv to json
def load_csv_to_json(csvfile_path, client, hr_list):
    with open (csvfile_path) as csvfile:
        reader = csv.DictReader( csvfile )
        for row in reader:
            row_dict = {}
            stat, hr = row['test_id'].split("#")

            # if hr not in range
            if client is not "gt":
                if hr not in hr_list:
                    continue
            # set offset
            offset = 0
            if "24" in hr_list:
                offset = 24
    
            row_dict['Client'] = client
            row_dict['station'] = stat
            if client is not "gt":
                row_dict['hr'] = int(hr) - offset
            else:
                row_dict['hr'] = int(hr)
            row_dict['O3'] = None if row['O3'] == "" else row['O3']
            row_dict['pm25'] = None if row['PM2.5'] == "" else row['PM2.5']
            row_dict['pm10'] = None if row['PM10'] == "" else row['PM10']
            row_dict['offset'] = offset
    
            json_result.append(row_dict)

def load_prd_files(prd_date, hr_start, hr_end):
    # check if folder exists
    if os.path.exists(prd_folder + prd_date):
        # get file list
        prd_date_files = [f for f in listdir(prd_folder + prd_date) if isfile(join(prd_folder + prd_date, f))]
        for prd_file in prd_date_files:
            client = prd_file.replace(",", "").replace(".csv", "").replace("(", "").replace(")", "") + "_" + str(hr_start) + "_" + str(hr_end)
            load_csv_to_json( prd_folder + prd_date + "/" + prd_file, client, [str(x) for x in range(hr_start, hr_end)] )
    
def job():
    # loop for all target dates
    target_date_list = ["2018-05-02", "2018-05-03"]

    for target_date in target_date_list:
        year, month, day = target_date.split("-")
        
        # for short 
        prd1_date = "%s%s%02d" % (year, month, int(day)-1)
        # for long
        prd2_date = "%s%s%02d" % (year, month, int(day)-2)

        # for ground truth
        load_csv_to_json( gt_folder + target_date + "_ground_truth.csv", "gt", [str(x) for x in range(0, 24)] )
        load_csv_to_json( gt_folder + target_date + "_ground_truth.csv", "gt", [str(x) for x in range(24, 48)] )

        # for prediction
        load_prd_files(prd1_date, 0, 24)
        load_prd_files(prd2_date, 24, 48)
    
        # dump 
        with open('data_%s.json' % target_date.replace('-', '') , 'w') as f:
            json.dump(json_result, f)

if __name__ == "__main__":
    job()
