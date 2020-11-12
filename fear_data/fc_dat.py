import csv
import re
import os
from os.path import join
from pathlib import Path
import yaml
import pandas as pd
import numpy as np


###################################################################################################
###################################################################################################
def load_expt_config(config_path):
    """Load expt_info.yaml to obtain project_path, raw_data_path, fig_path, and dict containing any group info.
     
     Parameters
     ----------
     config_path : path to the project yaml file.
     
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
    config_path : path to the project yaml file.
    session : the session to load data from the config_file
    
    Returns
    -------
    df : pandas DataFrame of data from the specified session.
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
    
    # Fill in Group info    
    expt_cfg = load_expt_config(config_path)
    mouseDict = expt_cfg['group_ids']
    for key,val in mouseDict.items():
        df.loc[df['Animal'].isin(val), 'Group'] = key
    if expt_cfg['sex'] is True:
        for key, val in expt_cfg['sex_ids'].items():
            df.loc[df['Animal'].isin(val), 'Sex'] = key
    
    return df


###################################################################################################

def clean_data(config_path, session, prism_format=False, prism_col='Component'):
    """
    Cleans video fear data files by converting animal ids to strings,
    simplifying component names, and adding phase names (if trace or tone fear).
    
    Parameters
    ----------
    config_path : path to the project yaml file.
    session : the session to load data from the config_file
    prism_format : if `True` will convert the data into long-format for use in Prism.
    prism_col : column to use for data labels if prim_format == True.
    
    Returns
    -------
    df : cleaned DataFrame with 'Phase' labeled.
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
    """
    Group DataFrame by 'Phase'. Used for plotting data by Phase.
    
    Parameters
    ----------
    df : pandas DataFrame to perform grouping on.
    hue : Default None. Can be used to include an additional grouping variable.
    
    Returns
    -------
    df : pandas DataFrame grouped by Phase
    """
    if hue is not None:
        df = df.groupby(['Animal', hue, 'Phase'], as_index=False).mean()
    else:
        df = df.groupby(['Animal', 'Phase'], as_index=False).mean()
    return df


###################################################################################################

def tfc_comp_times(df, session):
    """
    Load component times from 'TFC phase components.xlsx'
    
    Parameters
    ----------
    config_path : path to the project yaml file.
    session : the session to label.
    
    Returns
    -------
    comp_labs : pandas DataFrame grouped by Phase.
    """
    
    curr_dir = str(Path(__file__).parents[1]) + '/files/'
    comp_labs_file = curr_dir + 'TFC phase components.xlsx'

    if 'train' in session.lower():
        protoc = 'train'
    elif 'tone' in session.lower():
        protoc = 'tone'
    else:
        raise ValueError('session must include "train" or "tone"')
    # load TFC phase components.xlsx file
    comp_labs = pd.read_excel(comp_labs_file, sheet_name=protoc)
    
    return comp_labs
    
###################################################################################################

def label_fc_data(config_path, session):
    """
    * Load fear conditioning data from corresponding session.
    * Used primarily on data with high temporal resolution (e.g., <1 sec per component).
    
    Parameters
    ----------
    config_path : path to the project yaml file.
    session : the session to label.
    
    Returns
    -------
    df : pandas DataFrame with 'Component' giving session time and 'epoch' the labeled component.
    """
    df = load_data(config_path, session)
    comp_labs = tfc_comp_times(df, session)
    # add time labels as component labels
    n_components = len(df.query('Animal == @df.Animal.unique()[0]'))
    session_end = max(comp_labs['end'])
    df['Component'] = np.tile(np.linspace(0, session_end, n_components), len(df.Animal.unique()))
    #df['Component'] = round(df['Component'].astype('float64'), 2)
    df['Component'] = np.around(df['Component'].astype('float64'), 2)
    df['epoch'] = df['Component']
    # label the TFC components
    for i in range(len(comp_labs['phase'])):
        df.loc[df['Component'].between(comp_labs['start'][i], comp_labs['end'][i]), 'epoch'] = comp_labs['phase'][i]
    # label tone, trace, and iti for all protocols
    
    return df

###################################################################################################

def tfc_trials_df(config_path, session='train', win_start=-20, win_end=60):
    """
    * Loads data and adds labels using `label_fc_data`
    * Add column for `Trial` and `trial_time`
    * Specify start and end of each trial with `win_start` and `win_end`
    
    Parameters
    ----------
    config_path : path to the project yaml file.
    session : the session used to label.
    win_start : start of window for each trial (Note: tone onset is t=0)
    win_end : end of window for each trial (Note: tone onset is t=0)
    
    Returns
    -------
    df : pandas DataFrame of trial-level data
    """
    
    df = label_fc_data(config_path, session)    
    comp_labs = tfc_comp_times(df, session)
    # create list of tone values
    trials_idx = [ tone for tone in range(len(comp_labs['phase'])) if 'tone' in comp_labs['phase'][tone] ]
    # determine number of tone trials from label
    n_subjects = len(df['Animal'].unique())
    n_trials = len(trials_idx)
    trial_no = int(1)
    # subset trial data (-20 prior to CS --> 40s after trace/shock)
    for tone in trials_idx:
        start = comp_labs.loc[tone,'start'] + win_start
        end = comp_labs.loc[tone,'start'] + win_end
        df.loc[(start <= df.Component) & (df.Component <= end), 'Trial'] = int(trial_no)
        trial_no += 1
    #drop time rows outside of (win_start,win_end) trial window    
    df = df.dropna().reset_index(drop=True)
    df['Trial'] = df['Trial'].astype(int)
    # add equally spaced time values for each trial/animal
    trial_time = np.around(np.linspace(win_start, win_end, len(df.query('Animal == @df.Animal[0] and Trial == @df.Trial[0]'))), 1)
    df['trial_time'] = np.tile(trial_time, n_trials*n_subjects)

    return df