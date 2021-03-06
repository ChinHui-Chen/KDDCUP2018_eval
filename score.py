#!/usr/bin/env python

# Scoring program for the AutoML challenge
# Isabelle Guyon and Arthur Pesah, ChaLearn, August 2014-November 2016

# ALL INFORMATION, SOFTWARE, DOCUMENTATION, AND DATA ARE PROVIDED "AS-IS". 
# ISABELLE GUYON, CHALEARN, AND/OR OTHER ORGANIZERS OR CODE AUTHORS DISCLAIM
# ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR ANY PARTICULAR PURPOSE, AND THE
# WARRANTY OF NON-INFRINGEMENT OF ANY THIRD PARTY'S INTELLECTUAL PROPERTY RIGHTS. 
# IN NO EVENT SHALL ISABELLE GUYON AND/OR OTHER ORGANIZERS BE LIABLE FOR ANY SPECIAL, 
# INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER ARISING OUT OF OR IN
# CONNECTION WITH THE USE OR PERFORMANCE OF SOFTWARE, DOCUMENTS, MATERIALS, 
# PUBLICATIONS, OR INFORMATION MADE AVAILABLE FOR THE CHALLENGE. 

# Some libraries and options
import os
from sys import argv

import libscores
import yaml
from libscores import ls, filesep, mkdir, read_array, compute_all_scores, write_scores
import pandas as pd
import numpy as np

# Constant used for a missing score
missing_score = -0.999999

# Version number
scoring_version = 1.0

# Const list
aq_list = ['pm25', 'pm10', 'o3']
london_stat_list = ['BL0', 'CD9', 'CD1', 'GN0', 'GR4', 'GN3', 'GR9', 'HV1', 'KF1', 'LW2', 'ST5', 'TH4', 'MY7']
lon_stat_type = {}
bj_stat_type = {}
bj_stat_type['urban'] = ['dongsi_aq','tiantan_aq','guanyuan_aq','wanshouxig_aq','aotizhongx_aq','nongzhangu_aq','wanliu_aq','beibuxinqu_aq','zhiwuyuan_aq','fengtaihua_aq','yungang_aq','gucheng_aq']
bj_stat_type['suburban'] = ['fangshan_aq','daxing_aq','yizhuang_aq','tongzhou_aq','shunyi_aq','pingchang_aq','mentougou_aq','pinggu_aq','huairou_aq','miyun_aq','yanqin_aq']
bj_stat_type['other'] = ['dingling_aq','badaling_aq','miyunshuik_aq','donggaocun_aq','yongledian_aq','yufa_aq','liulihe_aq']
bj_stat_type['traffic'] = ['qianmen_aq','yongdingme_aq','xizhimenbe_aq','nansanhuan_aq','dongsihuan_aq']
lon_stat_type['urban'] = ['BL0', 'KF1']
lon_stat_type['suburban'] = ['GR4']
lon_stat_type['roadside'] = ['CD9', 'GN0', 'GN3', 'GR9', 'HV1', 'LW2', 'TH4']
lon_stat_type['kerbside'] = ['CD1', 'MY7']
lon_stat_type['industrial'] = ['ST5']
stat_to_type_map = {}


def _HERE(*args):
    h = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(h, *args)

def _load_scoring_function():
    with open(_HERE('metric.txt'), 'r') as f:
        metric_name = f.readline().strip()
        return metric_name, getattr(libscores, metric_name)

# compute day, avg level smape
def _compute_day_smape(cond, pd, scoring_function, set_num, predict_name, score_name, score_file, perday_perfix='', label=''):
    '''
    Assume pd is concated.
    '''
    # check if pd is empty
    if pd.empty:
        if 'avg' in cond:
            score_file.write("%s_AVGALL" % (label) + ":\n" )
            score_file.write("%s_STDALL" % (label) + ":\n" )
        if 'top25' in cond:
            score_file.write("%s_AVG25" % (label) + ":\n" )
            score_file.write("%s_STD25" % (label) + ":\n" )
        return

    # count date list again for preventing empty list
    cur_date_list = pd.submit_date.unique()

    # compute perday smape
    if 'perday' in cond:
        for d in cur_date_list:
            aq_d = pd.loc[ pd['submit_date'] == d ]
            score = scoring_function( aq_d.as_matrix(columns=['x']) , aq_d.as_matrix(columns=['y']) )
            score_file.write("%s_%s" % (perday_perfix,d.replace('-','_')) + ": %0.12f\n" % (score))
        return    
    
    # compute avg, top25
    smape_score_list = []
    for d in cur_date_list:
        aq_d = pd.loc[ pd['submit_date'] == d ]
        score = scoring_function( aq_d.as_matrix(columns=['x']) , aq_d.as_matrix(columns=['y']) )
        smape_score_list.append(score) 
    # compute avg smape
    if 'avg' in cond:
        score_file.write("%s_AVGALL" % (label) + ": %0.12f\n" % np.array(smape_score_list).mean())
        score_file.write("%s_STDALL" % (label) + ": %0.12f\n" % np.array(smape_score_list).std())
    # compute top25 smape
    if 'top25' in cond:
        smape_score_list.sort()
        score_file.write("%s_AVG25" % (label) + ": %0.12f\n" % np.array(smape_score_list[0:25]).mean())
        score_file.write("%s_STD25" % (label) + ": %0.12f\n" % np.array(smape_score_list[0:25]).std())

# compute different level smape
def _compute_smape(level, pd_map, scoring_function, set_num, predict_name, score_name, score_file):
    # level = hr
    if level == 'hr':
        # concate all
        pd_all = pd.concat( [pd_map[aq] for aq in aq_list] )
        # compute smape
        _compute_day_smape( ['avg','top25'], pd_all.loc[ (pd_all['hr'] < 24) ], scoring_function, set_num, predict_name, score_name, score_file, label='all_hr_0_23' )
        _compute_day_smape( ['avg','top25'], pd_all.loc[ (pd_all['hr'] < 48) & (pd_all['hr'] >=24 ) ], scoring_function, set_num, predict_name, score_name, score_file, label='all_hr_24_47' )
        _compute_day_smape( ['avg','top25'], pd_all.loc[ (pd_all['hr'] < 48) ], scoring_function, set_num, predict_name, score_name, score_file, label='all_hr_0_47' )

    # level = loc
    elif level == 'loc':
        pd_all = pd.concat( [pd_map[aq] for aq in aq_list] )
        stat_list = pd_all.stat_id.unique()

        _compute_day_smape( ['avg','top25'], pd_all.loc[ (pd_all['stat_id'].isin(london_stat_list) ) ], scoring_function, set_num, predict_name, score_name, score_file, label='lon_all' )
        _compute_day_smape( ['avg','top25'], pd_all.loc[ ~(pd_all['stat_id'].isin(london_stat_list) ) ], scoring_function, set_num, predict_name, score_name, score_file, label='bj_all' )
        for stat in stat_list:
            country = 'bj'
            if stat in london_stat_list:
                country = 'lon'
            _compute_day_smape( ['avg','top25'], pd_all.loc[ (pd_all['stat_id'] == stat ) ], scoring_function, set_num, predict_name, score_name, score_file, label='%s_%s_%s' % (country, stat_to_type_map[stat],stat) )
        for stat_type in bj_stat_type:
            country = "bj"
            _compute_day_smape( ['avg','top25'], pd_all.loc[ (pd_all['stat_id'].isin( bj_stat_type[stat_type] ) ) ], scoring_function, set_num, predict_name, score_name, score_file, label='%s_%s_%s' % (country, stat_type, "all") )
        for stat_type in lon_stat_type:
            country = "lon"
            _compute_day_smape( ['avg','top25'], pd_all.loc[ (pd_all['stat_id'].isin( lon_stat_type[stat_type] ) ) ], scoring_function, set_num, predict_name, score_name, score_file, label='%s_%s_%s' % (country, stat_type, "all") )
    
    # level = aq        
    elif level == 'aq':
        for aq in aq_list:
            _compute_day_smape( ['avg','top25'], pd_map[aq], scoring_function, set_num, predict_name, score_name, score_file, label='all_aq_%s' % (aq) )
            # add bj, lon AQ info
            _compute_day_smape( ['avg','top25'], pd_map[aq].loc[ pd_map[aq]['stat_id'].isin(london_stat_list) ], scoring_function, set_num, predict_name, score_name, score_file, label='lon_aq_%s' % (aq) )
            _compute_day_smape( ['avg','top25'], pd_map[aq].loc[ ~(pd_map[aq]['stat_id'].isin(london_stat_list)) ], scoring_function, set_num, predict_name, score_name, score_file, label='bj_aq_%s' % (aq) )
            
    else:
       raise Exception('Error in calculation of the specific score of the task: level error')


# main function 
def get_smape_score(input_sol_file, input_prd_file, output_file, req_level):

    # open score_file=output_file
    score_file = open(output_file, 'wb')

    # preprocessing: station to type
    for stype in bj_stat_type:
        for sid in bj_stat_type[stype]:
            stat_to_type_map[sid] = stype
    for stype in lon_stat_type:
        for sid in lon_stat_type[stype]:
            stat_to_type_map[sid] = stype

    # get the metric
    metric_name, scoring_function = _load_scoring_function()

    # get all the solution files from the solution directory
    solution_names = [input_sol_file]

    # Loop over files in solution directory and search for predictions with extension .predict having the same basename
    for i, solution_file in enumerate(solution_names):
        set_num = i + 1  # 1-indexed
        score_name = 'set%s_score' % set_num

        # Extract the dataset name from the file name
        basename = solution_file[-solution_file[::-1].index(filesep):-solution_file[::-1].index('.') - 1]

        try:
            # get prediction file
            predict_file = input_prd_file
            predict_name = predict_file[-predict_file[::-1].index(filesep):-predict_file[::-1].index('.') - 1]

            # file to pd
            pd_solution = pd.read_csv(solution_file, sep=',')
            pd_prediction = pd.read_csv(predict_file, sep=',')
            
            # Check shape
            if (len(pd_solution) != len(pd_prediction)): raise ValueError(
                "Bad prediction shape {}".format(prediction.shape))

            # do leftjoin sol and pred data, result cols: ['submit_date', 'test_id', 'PM2.5_x', 'PM10_x', 'O3_x', 'PM2.5_y', 'PM10_y', 'O3_y']
            pd_merged_all = pd.merge( pd_solution, pd_prediction, how='left', on=['submit_date','test_id'] )
            
            # Data preprocessing: Split test_id
            pd_merged_all['stat_id'], pd_merged_all['hr'] = pd_merged_all['test_id'].str.split('#', 1).str

            # Data preprocessing: Replace negative values with np.nan
            pd_merged_all[ pd_merged_all < 0 ] = np.nan

            # Data preprocessing: Remove missing value in gt
            pd_merged_lon = pd_merged_all.loc[ pd_merged_all['stat_id'].isin(london_stat_list) ]
            pd_merged_bj = pd_merged_all.loc[ ~pd_merged_all['stat_id'].isin(london_stat_list) ]

            pd_merged_lon = pd_merged_lon.replace('', np.nan, regex=True).dropna( subset=['PM2.5_x', 'PM10_x'], how='any' )
            pd_merged_bj = pd_merged_bj.replace('', np.nan, regex=True).dropna( subset=['PM2.5_x', 'PM10_x', 'O3_x'], how='any' )

            pd_merged_all = pd.concat( [pd_merged_lon, pd_merged_bj] )

            # Data preprocessing: filter missing value
            pd_merged_map = {}
            pd_merged_map['pm25'] = pd_merged_all[['submit_date', 'test_id', 'PM2.5_x', 'PM2.5_y', 'stat_id', 'hr']]
            pd_merged_map['pm10'] = pd_merged_all[['submit_date', 'test_id', 'PM10_x', 'PM10_y', 'stat_id', 'hr']]
            pd_merged_map['o3'] = pd_merged_all[['submit_date', 'test_id', 'O3_x', 'O3_y', 'stat_id', 'hr']].dropna( subset=['O3_x'] )
            # Data preprocessing: rename columns
            pd_merged_map['pm25'] = pd_merged_map['pm25'].rename(columns={'PM2.5_x':'x', 'PM2.5_y':'y'})
            pd_merged_map['pm10'] = pd_merged_map['pm10'].rename(columns={'PM10_x':'x', 'PM10_y':'y'})
            pd_merged_map['o3'] = pd_merged_map['o3'].rename(columns={'O3_x':'x', 'O3_y':'y'})
            # Data preprocessing: replace nan with 0 in prediction
            pd_merged_map['pm25'] = pd_merged_map['pm25'].replace(np.nan, 0, regex=True)
            pd_merged_map['pm10'] = pd_merged_map['pm10'].replace(np.nan, 0, regex=True)
            pd_merged_map['o3'] = pd_merged_map['o3'].replace(np.nan, 0, regex=True)

            # Data preprocessing: cast to numeric
            for aq in aq_list:
                pd_merged_map[aq][['hr']] = pd_merged_map[aq][['hr']].apply(pd.to_numeric)

            try:
                # Perday smape
                if req_level == "" or req_level == "perday":
                    pd_all = pd.concat([ pd_merged_map[aq] for aq in aq_list ])
                    _compute_day_smape('perday', pd_all, scoring_function, set_num, predict_name, score_name, score_file, perday_perfix='all')
                # 0-23, 24-47, 0-47: total, top25 smape
                if req_level == "" or req_level == "hr":
                    _compute_smape('hr', pd_merged_map, scoring_function, set_num, predict_name, score_name, score_file)
                # City, station: smape X2
                if req_level == "" or req_level == "loc":
                    _compute_smape('loc', pd_merged_map, scoring_function, set_num, predict_name, score_name, score_file)
                # AQ
                if req_level == "" or req_level == "aq":
                    _compute_smape('aq', pd_merged_map, scoring_function, set_num, predict_name, score_name, score_file)
            except:
                raise
                raise Exception('Error in calculation of the specific score of the task')

        except Exception as inst:
            score = missing_score
            print(
                "======= Set %d" % set_num + " (" + basename.capitalize() + "): score(" + score_name + ")=ERROR =======")
            print(inst)

    # End loop for solution_file in solution_names
    score_file.close()

if __name__ == "__main__":
    get_smape_score( "./sample_prd.csv" , "./sample_sol.csv", "output.txt", "")
