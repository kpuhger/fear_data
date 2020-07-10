import csv
import re
import os
from os.path import join
import yaml
import pandas as pd
import numpy as np


###################################################################################################
###################################################################################################
def load_expt_config(config_path):
    """Load expt_info.yaml to obtain project_path, raw_data_path, fig_path, and dict containing any group info.
     
     Parameters
     ----------
     config_path : str to the project yaml file.
     
     Returns
     -------
     expt_info : YAML object
    """
    try: 
        with open (config_path, 'r') as file:
            expt = yaml.safe_load(file)
    except Exception:
        print('Error reading the config file')

    return expt


###################################################################################################

def load_data(config_path, session):
    """loads .csv from VideoFreeze as a pandas df

    Parameters
    ----------
    file: path to the .csv to be loaded
    """
    expt_info = load_expt_config(config_path)
    # raise execption if input for session not in config file.
    if session.lower() not in expt_info['sessions']:
        raise ValueError("`session` not found in sessions list - check expt_config.yaml")
    
    # find session file
    data_path = expt_info['raw_data_path'] if expt_info['raw_data'] else expt_info['proc_data_path']
    file = join(data_path, expt_info[f'{session.lower()}_file'])
    # internal function
    def find_start(file, start_row='Experiment'):
        """Uses regex to find the first row of real data. This function is used as part
        of the load_df function.

        Parameters
        ----------
        file: path to the .csv to be loaded
        """
        with open(file, 'rt') as f:
            reader = csv.reader(f)
            test = [row for row in reader]
        line_num = 0
        for index in test:
            for double_index in index:
                if re.match(start_row,double_index) != None:
                    return(line_num)
            line_num+=1

    # convert training file to pandas df
    df = pd.read_csv(file, skiprows=find_start(file))
    # drop NaNs that can get inserted into
    df = df.replace('nan', np.NaN).dropna(thresh=2).reset_index()   
    # bug from VideoFreeze on some csv files, convert Animal to str
    if df['Animal'].dtype is np.dtype('float64') or df['Animal'].dtype is np.dtype('int64'):
        df.loc[:, 'Animal'] = df['Animal'].astype('int').astype('str')  
    # drop and rename columns
    old_col_list = ['Animal', 'Group', 'Component Name', 'Pct Component Time Freezing', 'Avg Motion Index']
    # reindex to drop extraneous cols
    df = df.reindex(columns=old_col_list)
    # rename columns to remove spaces in colnames
    new_col_list = ['Animal', 'Group', 'Component', 'PctFreeze', 'AvgMotion']
    new_cols = {key:val for (key,val) in zip(df.reindex(columns=old_col_list).columns, new_col_list)}
    df = df.rename(columns=new_cols) 
    
    return df


###################################################################################################

def clean_data(config_path, session, prism_format=False, prism_col='Component'):
    """
    Cleans video fear data files by converting animal ids to strings,
    simplifying component names, and adding phase names (if trace or tone fear)
    """
    
    def get_baseline_vals(df):
        """ Get values up to the first 'tone' component"""
        new_list = []
        for item in df['Component']:
            if item.lower() != 'tone-1':
                new_list.append(item)
            else:
                break
        new_list = [str(item) for item in new_list]
        return new_list

    # load session data
    df = load_data(config_path, session)
    # clean up df
    if session is 'context':
        df['Component'] = df['Component'].astype('int')
        df['Phase'] = 'context'
    else:
        df['Component'] = [ df['Component'][x].lower() for x in range(len(df['Component'])) ]
        df['Phase'] = df['Component']
        baseline_vals = get_baseline_vals(df)
        # add column to denote phase of each bin   
        df.loc[df['Phase'].isin(baseline_vals), 'Phase'] = 'baseline'
        df.loc[df['Phase'].str.contains('tone'), 'Phase'] = 'tone'
        df.loc[df['Phase'].str.contains('trace'), 'Phase'] = 'trace'
        df.loc[~df['Phase'].isin(['baseline', 'tone', 'trace']), 'Phase'] = 'iti'
    
    # Fill in Group info    
    expt_cfg = load_expt_config(config_path)
    mouseDict = expt_cfg['group_ids']
    for key,val in mouseDict.items():
        df.loc[df['Animal'].isin(val), 'Group'] = key
    if expt_cfg['sex'] is True:
        for key, val in expt_cfg['sex_ids'].items():
            df.loc[df['Animal'].isin(val), 'Sex'] = key

    
    if prism_format is True:
        col_order = df[prism_col].unique()
        df = df.pivot_table(values='PctFreeze', index=['Animal', 'Group'], columns=prism_col)
        df = (df
              .reindex(col_order, axis=1)
              .sort_values('Group')
              .reset_index() )
    else:
        df = df.reindex(columns=['Animal', 'Sex', 'Group', 'Phase', 
                               'Component', 'PctFreeze', 'AvgMotion'])
        
    return df


###################################################################################################

def total_df(df, hue=None):
    if hue is not None:
        df = df.groupby(['Animal', hue, 'Phase'], as_index=False).mean()
    else:
        df = df.groupby(['Animal', 'Phase'], as_index=False).mean()
    return df


###################################################################################################