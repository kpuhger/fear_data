# fear_data

Tools to analyze data from VideoFreeze data files.



# Install

Add `fear_data` directory to PYTHONPATH or append using sys.path


# Modules

This package contains the following modules:

* `dataproc`: Functions for processing data.
	* `load_data`: load data from expt_config file for a specified session
	* `clean_data`: runs `load_data` and does additional cleaning of DataFrame.
* `viz`: functions for visualizing cleaned data. Only tested on data collect
	* `plot_tfc_bins`: plot trace fear data for each 'Component'.
	* `plot_tfc_phase`: plot trace fear data for each 'Phase'.