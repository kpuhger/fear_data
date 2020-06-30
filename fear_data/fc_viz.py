import os
import matplotlib.pyplot as plt
import seaborn as sns
from .plot_utils import savefig, style_plot, check_ax 


################################################################################

@savefig
@style_plot
def plot_fc_bins(df, session, xvar='Component', yvar='PctFreeze', ax=None, fig_size=(16,10), **kwargs):
    
    """ Pointplot of specified `session`.
    
    Parameters
    ----------
    df : pandas DataFrame from load_data.clean_dat()
    session : name of session
    
    Notes
    -----
    - Save fig by adding save_fig=True, can specify fig_path to save to (default is to user Desktop)
    
    """
    
    ax = check_ax(ax, figsize=fig_size)

    # get bins for tone and trace interval
    bins_list = list(df['Component'].unique())
    # draw grey rectangle around tone bin
    if session.lower() != 'context':
        tones = [i-0.5 for i in range(len(bins_list)) if 'tone-' in bins_list[i].lower()]
        [ ax.axvspan(to, to+1, facecolor="grey", alpha=0.15) for to in tones ]
    # draw line to indicate shock
    if session.lower() == 'train':
        traces = [i-0.5 for i in range(len(bins_list)) if 'trace-' in bins_list[i].lower()]
        [ ax.axvspan(tr+1, tr+1.15, facecolor='#ffb200') for tr in traces ]

    sns.pointplot(x=xvar,
                  y=yvar,
                  data=df,
                  ci=68,
                  ax=ax,
                  scale=2.25,
                  errwidth=6,
                  capsize=0.05,
                  **kwargs)

    ax.set_ylabel('Freezing (%)')
    ax.set_xlabel('Time (mins)')
    # replace with x-labels with mins if using Component
    if session is not 'context':
    # if xvar is 'Component' and df['Phase'] != 'context':
        min_bins = [i for i in range(len(df['Component'].unique())) if (i+1) % 3 == 0]
        min_labs = [ i+1 for i in range(len(min_bins)) ]
        ax.set_xticks(min_bins)
        ax.set_xticklabels(min_labs)
    # remove legend title
    if 'hue' in kwargs.keys():
        l = ax.legend()
        l.set_title(None)
    sns.despine()
    
    
@savefig
@style_plot    
def plot_fc_phase(df, xvar='Phase', yvar='PctFreeze', kind='bar', pts=True, ax=None, fig_size=(16,9),**kwargs):
    
    """ Pointplot or barplot (specified by kind).
    
    Parameters
    ----------
    df : pandas DataFrame from load_data.clean_dat()
    xvar : x-axis variable (default: 'Phase')
    yvar : y-axis variable (default: 'PctFreeze')
    kind : type of seaborn plot to use (must be 'point' or 'bar')
    
    
    Notes
    -----
    - For plot aes -> set label_size=36, tick_labelsize=24
    - If `kind` = 'point' -> set markerscale=0.4
    - Save fig by adding save_fig=True, can specify fig_path to save to (default is to user Desktop)
    
    """
    if 'hue' in kwargs.keys():
        df = df.groupby(['Animal', kwargs.get('hue'), 'Phase'], as_index=False).mean()
    else:
        df = df.groupby(['Animal', 'Phase'], as_index=False).mean()
    # create figure
    ax = check_ax(ax, figsize=fig_size)
    # additional plot param for pointplot
    if kind == 'point':
        kwargs['scale'] = 4
        pts = False
    # Determine the plotting function
    # use `kind` to specify type of phase plot
    plot_func = getattr(sns, kind+'plot')
    
    plot_func(x=xvar,
              y=yvar,
              data=df,
              ci=68,
              ax=ax,
              errwidth=8,
              capsize=0.05,
              **kwargs)
    
    if pts == True:
        sns.swarmplot(x=xvar, y=yvar, color='black', data=df, dodge=True, size=22, **kwargs)
        handles, labels = ax.get_legend_handles_labels()
        nhandles = len(handles)
        first_handle = int(nhandles/2)
        plt.legend(handles[first_handle:nhandles], labels[first_handle:nhandles])

    ax.set_ylabel('Freezing (%)')
    ax.set_xlabel('')
    # replace with x-labels with mins if using Component
    if xvar is 'Component':
        min_bins = [i for i in range(len(df['Component'].unique())) if (i+1) % 3 == 0]
        min_labs = [ i+1 for i in range(len(min_bins)) ]
        ax.set_xticks(min_bins)
        ax.set_xticklabels(min_labs)
    # remove legend title
    if 'hue' in kwargs.keys():
        l = ax.legend()
        l.set_title(None)
    sns.despine()