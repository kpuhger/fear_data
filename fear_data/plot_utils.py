"""
Functions and utilities to apply aesthetic styling to plots.
Modified from neuroDSP: https://github.com/neurodsp-tools/neurodsp/tree/master/neurodsp/plts
"""
import os
import inspect
import seaborn as sns
from itertools import cycle
from functools import wraps
from os.path import join
import matplotlib.pyplot as plt

###################################################################################################

################################################################################
# Plotting utility functions
################################################################################

def check_ax(ax, figsize=None):
    """Check whether a figure axes object is defined, define if not.
    Parameters
    ----------
    ax : matplotlib.Axes or None
        Axes object to check if is defined.
    Returns
    -------
    ax : matplotlib.Axes
        Figure axes object to use.
    """

    if not ax:
        _, ax = plt.subplots(figsize=figsize)

    return ax

###################################################################################################

# define color palette:
kp_pal = ['#2b88f0', #blue
          '#FF0036', #red 
           '#EF862E', #orange
           '#28A649', #green
           '#9147B1', #purple
           '#00B9B9', #cyan
           '#F97B7B', #salmon
           '#FFD85B', #yellow
           '#bdbdbd'] #gray


def set_palette(pal=kp_pal, show=False):
    sns.set_palette(pal)
    if show == True:
        sns.palplot(pal)
    elif show == False:
        return pal


###################################################################################################

def savefig(func):
    """Decorator function to save out figures."""

    @wraps(func)
    def decorated(*args, **kwargs):

        save_fig = kwargs.pop('save_fig', False)
        fig_name = kwargs.pop('fig_name', None)
        fig_path = kwargs.pop('fig_path', None)

        func(*args, **kwargs)

        if save_fig:
            full_path = join(fig_path, fig_name) if fig_path else os.path.expanduser(f'~/Desktop/{fig_name}.png')
            plt.savefig(full_path)
            
    return decorated


###################################################################################################

################################################################################
# Plot style settings
################################################################################

"""Default settings for plots."""
## Define collections of style arguments
# Plot style arguments are those that can be defined on an axis object
AXIS_STYLE_ARGS = ['title', 'xlabel', 'ylabel', 'xlim', 'ylim']
# Custom style arguments are those that are custom-handled by the plot style function
CUSTOM_STYLE_ARGS = ['title_fontsize', 'label_size', 'labelpad', 'tick_labelsize',
                     'legend_size', 'legend_loc', 'markerscale']
STYLE_ARGS = AXIS_STYLE_ARGS + CUSTOM_STYLE_ARGS
## Define default values for aesthetic
# These are all custom style arguments
TITLE_FONTSIZE = 40
LABEL_SIZE = 36
LABEL_PAD = 5
TICK_LABELSIZE = 32
LEGEND_SIZE = 18
LEGEND_LOC = 'best'
MARKERSCALE = 1

###################################################################################################
###################################################################################################

# TODO: create a version of for barplots -> apply_bar_style()

def apply_custom_style(ax, style_args=AXIS_STYLE_ARGS, **kwargs):
    """Apply custom plot style.
    Parameters
    ----------
    ax : matplotlib.Axes
        Figure axes to apply style to.
    style_args : list of str
        A list of arguments to be sub-selected from `kwargs` and applied as axis styling.
    **kwargs
        Keyword arguments that define custom style to apply.
    """

    # Apply any provided axis style arguments
    plot_kwargs = {key : val for key, val in kwargs.items() if key in style_args}
    ax.set(**plot_kwargs)
    
    # If a title was provided, update the size
    if ax.get_title():
        ax.title.set_size(kwargs.pop('title_fontsize', TITLE_FONTSIZE))

    # Settings for the axis labels
    label_size = kwargs.pop('label_size', LABEL_SIZE)
    ax.xaxis.label.set_size(label_size)
    ax.yaxis.label.set_size(label_size)

    # Settings for the axis ticks
    ax.tick_params(axis='both', which='major', pad=kwargs.pop('pad', LABEL_PAD),
                   labelsize=kwargs.pop('tick_labelsize', TICK_LABELSIZE))

    # If labels were provided, [1] check for duplicate labels and [2] add a legend
    if ax.get_legend_handles_labels()[0]:
        # if legend labels get duplicated, pick the original ones (e.g., adding swarmplot to boxplot)
        handles, labels = ax.get_legend_handles_labels()
        nhandles = len(handles)
        first_handle = int(nhandles/2) if nhandles > 2 else 0
        ax.legend(handles[first_handle:nhandles], labels[first_handle:nhandles], frameon=False, 
                  prop={'size': kwargs.pop('legend_size', LEGEND_SIZE)},
                  loc=kwargs.pop('legend_loc', LEGEND_LOC),
                  markerscale=kwargs.pop('markerscale', MARKERSCALE))

    plt.tight_layout()


###################################################################################################

def style_plot(func, *args, **kwargs):
    """Decorator function to make a plot and run apply_custom_style() on it.
    Parameters
    ----------
    func : callable
        The plotting function for creating a plot.
    *args, **kwargs
        Arguments & keyword arguments.
        These should include any arguments for the plot, and those for applying plot style.
    Notes
    -----
    This is a decorator, for plot, functions that functions roughly as:
    - catching all inputs that relate to plot style
    - create a plot, using the passed in plotting function & passing in all non-style arguments
    - passing the style related arguments into a apply_custom_style()
    This function itself does not apply create any plots or apply any styling itself.
    By default, this function applies styling with the `apply_custom_style` function. Custom
    functions for applying style can be passed in using `apply_custom_style` as a keyword argument.
    The `apply_custom_style` function applies different plot elements,
    """
    def get_default_args(func):
        """
        returns a dictionary of arg_name:default_values for the input function
        """
        argspec = inspect.getfullargspec(func)
        return dict(zip(reversed(argspec.args), reversed(argspec.defaults)))


    @wraps(func)
    def decorated(*args, **kwargs):

        # Grab a custom style function, if provided, and grab any provided style arguments
        style_func = kwargs.pop('custom_style', apply_custom_style)
        style_args = kwargs.pop('style_args', STYLE_ARGS)
        kwargs_local = get_default_args(func)
        kwargs_local.update(kwargs)
        style_kwargs = {key : kwargs.pop(key) for key in style_args if key in kwargs}
        # Create the plot
        func(*args, **kwargs)
        # Get plot axis, if a specific one was provided, or just grab current and apply style
        cur_ax = kwargs['ax'] if 'ax' in kwargs and kwargs['ax'] is not None else plt.gca()
        style_func(cur_ax, **style_kwargs)

    return decorated


###################################################################################################

