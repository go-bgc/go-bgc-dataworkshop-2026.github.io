# Helper module for argo_regression_modeling.ipynb
# BGC-Argo Data Workshop 2026, ML Tutorial


import pandas as pd
import xarray as xr
import numpy as np
import scipy
import gsw

from scipy import stats
from sklearn.model_selection import KFold
from sklearn.model_selection import train_test_split

from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import ExtraTreesRegressor

from sklearn import preprocessing
from sklearn import metrics

from sklearn.metrics import mean_squared_error
from sklearn.metrics import r2_score


import matplotlib.pyplot as plt
from cmocean import cm as cmo
from cartopy import crs as ccrs
from cartopy import feature as cfeature   


# %% ML data container - store training/validation data

class CrossValContainer:
    """ Data container for cross-validation folds. 
    Stores training and validation indices for each fold, rather than subcopies of the full dataframe
    Access subsets of the input data using .loc 
    """
    def __init__(self, input_data, nfolds):
        """ 
        :param input_data: pandas dataframe to be split into folds
        :param nfolds: integer number of splits
        """
        fold_list = ['fold' + str(k) for k in range(1, nfolds+1)]
        self.fold_list = fold_list
        self.input_data = input_data
        self.training_inds = {fold:None for fold in fold_list}
        self.validation_inds = {fold: None for fold in fold_list}

    def to_labeled_dataframe(self):
        """ Collapse training and validation data across folds into a single dataframe """
        fullDF = pd.DataFrame()
        for nfold in self.fold_list:
            temp = self.validation_data[nfold]
            temp['fold'] = np.tile(nfold, len(temp))
            fullDF = pd.concat([fullDF, temp], axis=0)

        return fullDF

    def map_folds(self, axs=None, figsize=(12,6), ax_lims = [-125, -119, 30, 40], glider_data=None):
        """ Map the training and validation data for each fold in a paneled plot.
        Modified to automatically plot CCE region for this workshop.
        :param axs: optional array of axes to plot on, if None will create new figure
        :param ax_lims: list of [lon_min, lon_max, lat_min, lat_max] to set map extent
        """
        plot_data = self.input_data.copy()
        nfolds = len(self.fold_list)

        if axs is None:
            fig, axs = plt.subplots(1,nfolds, figsize=figsize, layout='constrained', subplot_kw={'projection': ccrs.PlateCarree()})
        
        for ind, foldtag in enumerate(self.fold_list): 
            ax = axs[ind]
            val_data = plot_data.loc[self.validation_inds[foldtag], :].copy()
            train_data = plot_data.loc[self.training_inds[foldtag], :].copy()


            map_study_region(ax, ax_lims=ax_lims, gridlabel=False)
            ax.scatter(train_data.longitude, train_data.latitude, c='lightgrey', s=1, zorder=3,
                    transform=ccrs.PlateCarree(), label='train')
            ax.scatter(val_data.longitude, val_data.latitude, c='r', s=4, zorder=5,
                    transform=ccrs.PlateCarree(), label='val')
            
            if glider_data is not None:
                ax.scatter(glider_data.longitude, glider_data.latitude, c='navy', s=4, zorder=5,
                        transform=ccrs.PlateCarree())

            # ax.set_extent(ax_lims)
            # # ax.coastlines(resolution = "50m", zorder=5, linewidth = 1)
            # ax.add_feature(cfeature.LAND, zorder=19, linewidth = 1, edgecolor='k', facecolor='linen')
            # ax.set_aspect('equal')
            # ax.gridlines(alpha=0.5)
        
        ax.legend(loc='lower right', fontsize=10, markerscale=2, framealpha=1)
        
        return fig, axs


def subset_folds(platDF, type= 'platform', indexer='platform_id', nfolds=5,
                            latitude_scaler=1 ) -> list[dict[str, pd.DataFrame]]:
    """ 
    Returns dictionary of training and validation dataframes for each fold.

    :param platDF: dataframe for either floatDF or shipDF
    :param type: options by 'platform', 'kmeans', or 'random' 
    :param indexer: choose whether to split by 'wmoid' or 'profid'
                    only used if type = 'platform'
    :param nfolds: (int) number of folds for cross-validation
    :param latitude_scaler: float, scaling ratio for latitude/longitude in k-means
                            default of 1 gives range [-1.1] to match sinusoidal longitude range [-1,1]
                            changing to >1 gives more weight to latitude in clustering (ex: 3 yields range [-3,3])
    :return: training_inds: dictionary with keys 'fold1', 'fold2', ... with training DF integer locs
             validation_inds: dictionary with keys 'fold1', 'fold2', ... with validation DF integer locs

    """
    training_inds = {('fold'+str(k+1)):None for k in range(nfolds)}
    validation_inds = {('fold'+str(k+1)):None for k in range(nfolds)}
    # platDF = platDF.copy()
    
    if type == 'random': # not recommended!
        kf = KFold(n_splits=nfolds, random_state=42, shuffle=True)
        for ind, (train_index, val_index) in enumerate(kf.split(platDF)):
            training_inds['fold' + str(ind+1)] = train_index
            validation_inds['fold' + str(ind+1)] = val_index

    elif type == 'platform': 
        ids = platDF[indexer].unique(); np.random.shuffle(ids)
        holdout_ids = np.array_split(ids, nfolds)
        for k in range(nfolds):
            training_inds[('fold'+str(k+1))] = ~platDF[indexer].isin(holdout_ids[k])
            validation_inds[('fold'+str(k+1))] = platDF[indexer].isin(holdout_ids[k])

    elif type == 'kmeans': 
        kmeans = KMeans(n_clusters=nfolds, random_state=42)
        platDF['sin_longitude'] = np.sin(np.radians(platDF['longitude']))
        platDF['cos_longitude'] = np.cos(np.radians(platDF['longitude']))

        latitude_0to1 = (platDF['latitude'] - platDF['latitude'].min()) / platDF['latitude'].max() #range 0 to 1
        platDF['scaled_latitude'] = -latitude_scaler + latitude_scaler*2*(latitude_0to1) 
        platDF['fold'] = kmeans.fit_predict(platDF[['scaled_latitude', 'sin_longitude', 'cos_longitude']])

        for fnum in range(nfolds):
            training_inds['fold' + str(fnum+1)] = platDF['fold'] != fnum
            validation_inds['fold' + str(fnum+1)] = platDF['fold'] == fnum

    return training_inds, validation_inds


# %% ML model container - store errors from k-fold
class CrossValModelRun:
    """ Model container / instance of a trained model with results stored by fold
    """
    def __init__(self, fold_list, description=''):
        self.fold_list = fold_list
        self.models = {fold: None for fold in fold_list}
        self.validation_errors = {fold: None for fold in fold_list}
        # self.description = description # optional string tag
        self.calibratedDF = None 
        self.cal_coeffs = None

        # self.rmse = None
        # self.median_abs_error = None
        # self.mean_abs_error = None
        # self.bias = None

    def collapse_errors(self):
        """ Collapse validation errors across folds into a single dataframe """
        cv_errors = pd.concat([self.validation_errors[fold] for fold in self.fold_list], axis=0)
        return cv_errors
    

def fit_cv_model(use_cvtainer, target_variable, use_feats, use_algorithm='RFR', use_hyperparams={}):
    modRun = CrossValModelRun(fold_list = use_cvtainer.fold_list)

    # Populate cvtainer fields with validation errors, models for each fold 
    for nfold in use_cvtainer.fold_list:   
        trainDF = use_cvtainer.input_data.loc[use_cvtainer.training_inds[nfold]]
        valDF = use_cvtainer.input_data.loc[use_cvtainer.validation_inds[nfold]]

        modRun.models[nfold], modRun.validation_errors[nfold] = fit_single_regressor(
                                    trainDF, valDF,
                                    var_predict = target_variable, 
                                    feat_list = use_feats, # feature list
                                    regressor_type = use_algorithm,
                                    hyperparams = use_hyperparams)
        
    
    modRun.calibratedDF, modRun.cal_coeffs = apply_linear_calibration(modRun.collapse_errors(), target_variable)

    return modRun

def fit_single_regressor(
              trainingDF, validationDF,
              var_predict, 
              feat_list,
              regressor_type = 'RFR', #regressor
              hyperparams = {'n_estimators': 100}):
    """ 
    Fit single regressor, return validation errors
    """
            
    if regressor_type == 'RFR':
        # Mdl = RandomForestRegressor(n_estimators = hyperparams['n_estimators'], 
        #                             max_features = hyperparams['max_features'],
        #                             min_samples_split = hyperparams['min_samples_split'], 
        #                             bootstrap=True)
        Mdl = RandomForestRegressor(**hyperparams,
                                    bootstrap=True)
    # elif regressor_type == 'ERT':
    #     Mdl =


    # Train the model 
    X_training = trainingDF.dropna(subset=feat_list)[feat_list].to_numpy()
    Y_training = trainingDF.dropna(subset=feat_list)[var_predict].to_numpy().flatten()
    Mdl.fit(X_training, Y_training)

    if validationDF is not None:
        # Apply and get fold validation errors 
        resultDF = validationDF.copy()
        resultDF['val_prediction'] = Mdl.predict(validationDF[feat_list].to_numpy())
        resultDF['val_error'] = resultDF['val_prediction'] - resultDF[var_predict].to_numpy().flatten()
        resultDF['val_relative_error'] = resultDF['val_error'] / resultDF[var_predict].to_numpy().flatten()

        return Mdl, resultDF
    else: return Mdl

def fit_final_model(trainingDF, testDF,  
             var_predict, 
              feat_list,
              regressor_type = 'RFR', #regressor
              hyperparams = {'n_estimators': 100}):
    """ """
    finalMdl, test_errors = fit_single_regressor(trainingDF, 
                                testDF,
                                var_predict,
                                feat_list,
                                regressor_type,
                                hyperparams)
    
    calibrated_test_errors, cal_coeffs = apply_linear_calibration(test_errors, var_predict)
    calibrated_test_errors.rename(columns={'val_prediction':'test_prediction', 
                                'val_error':'test_error', 
                                'val_relative_error':'test_relative_error'}, inplace=True)
    return finalMdl, calibrated_test_errors, cal_coeffs

def apply_final_model(applicationDF, feat_list, finalMdl, cal_coeffs):
    applicationDF = applicationDF.copy()
    applicationDF['uncal_prediction'] = finalMdl.predict(applicationDF[feat_list].to_numpy())
    applicationDF['prediction'] = applicationDF['uncal_prediction'] * cal_coeffs[0] + cal_coeffs[1]
    return applicationDF


def apply_linear_calibration(valDF, target_variable):
    # cal_coeffs = {ncluster:None for ncluster in valDF['cluster'].unique()}
    calibratedDF = valDF.copy()
    calibratedDF['n_decile'] = pd.qcut(calibratedDF['val_prediction'].values, 10, labels=list(range(1, 11))) #
    cal_pred = calibratedDF.groupby('n_decile', observed=True)['val_prediction'].agg(['mean', 'min', 'max', 'count'])
    cal_obs = calibratedDF.groupby('n_decile', observed=True)[target_variable].agg(['mean', 'min', 'max', 'count'])

    stat_var = 'mean'
    lincal = stats.linregress(cal_pred[stat_var].values, cal_obs[stat_var].values)
    calibratedDF['lincal_prediction'] = calibratedDF['val_prediction'] * lincal.slope + lincal.intercept
    calibratedDF['lincal_error'] = calibratedDF['lincal_prediction'] - calibratedDF[target_variable]
    calibratedDF['lincal_relative_error'] = calibratedDF['lincal_error'] / calibratedDF[target_variable]

    return calibratedDF,  [lincal.slope, lincal.intercept]


def summarize_errors(platDF, error_param = 'val_error'):
        platDF = platDF.copy() #self.collapse_errors()

        err = platDF[error_param]
        median_abs_error = np.abs(err).median()
        mean_abs_error = np.abs(err).mean()
        bias = (err.mean())

        platDF[error_param + '_sq'] = platDF[error_param]**2
        mse = np.sum(platDF[error_param + '_sq']) / len(platDF[error_param])
        rmse = np.sqrt(mse)

        # absolute percentage error
        # platDF['ape'] = np.abs(platDF['val_relative_error'])*100
        # median_ape = platDF['ape'].median()
        # mean_ape = platDF['ape'].mean()

        result = [median_abs_error, mean_abs_error, bias, rmse]

        return result

    
def storedRuns_comparison(storedRuns_dict, run_tags = None, error_param='val_error', 
                          target_var='nitrate',
                          by_fold = False,
                          show=True): 
    """ 
    storedRuns: dictionary of ModelVersion objects, runtag as keys
    run_tags: list of run_tags to compare, if None will run all in storedRuns
    """

    #  Collapse folds into a single Dataframe for each run tag
    if run_tags is None: run_tags = [x for x in storedRuns_dict.keys()] # run all 
    
    if by_fold == True:
        storedRuns = {rkey: None for rkey in run_tags}
        for k,v in storedRuns_dict.items(): 
            storedRuns[k] = v.collapse_errors()
    else: storedRuns = storedRuns_dict.copy()

    total_MAEs = pd.DataFrame()


    for run_tag in run_tags[:]:
        errorDF = storedRuns[run_tag].calibratedDF
        # print('==> Results for ' + run_tag)
        # print('\t features ', feat_options[run_tag.split('-')[0]])
        # runResults = storedRuns[run_tag].weighted_validation.copy()
        [run_median_abs_error, run_mean_abs_error, run_bias, run_rmse] = summarize_errors(errorDF, error_param=error_param)

        total_MAEs.loc[run_tag, 'median_AE'] = run_median_abs_error
        total_MAEs.loc[run_tag, 'mean_AE'] = run_mean_abs_error
        total_MAEs.loc[run_tag, 'bias'] = run_bias
        total_MAEs.loc[run_tag, 'RMSE'] = run_rmse

    # total_MAEs['labels'] = feat_list_labels
    # total_MAEs.set_index('labels', inplace=True)
    if show: print(total_MAEs)
    return total_MAEs


# 

# %% Plotting functions

def map_study_region(ax = None, ax_lims = [-130, -118, 30, 40], gridlabel=False):
    """ 
    Mapping shortcut for study region, with mooring location marked"""
    
    if ax is None: 
        fig = plt.figure(figsize=(12, 6), layout='tight')
        ax = fig.add_subplot(1,1,1, projection=ccrs.PlateCarree())

    # CCE mooring location 
    # mooring_loc =  [-120.803990, 34.303747]
    # ax.scatter(mooring_loc[0], mooring_loc[1], c='k', s=40, marker='D', transform=ccrs.PlateCarree(), zorder=10)

    ax.set_extent(ax_lims)
    ax.coastlines(resolution = "50m", zorder=5, linewidth = 1)
    ax.add_feature(cfeature.LAND, zorder=5, linewidth = 1, edgecolor='k', facecolor='linen')
    ax.set_aspect('equal')
    ax.gridlines(draw_labels=gridlabel)

    return ax 


def plot_decile_calibration(ax, cal_pred, cal_obs, stat_var='mean', axlims = [-65, 15]):
    ax.set_aspect('equal')
    ax.scatter(cal_pred[stat_var].values, cal_obs[stat_var].values, color='k', s=30) #, label='decile means')
    ax.plot([-1000,1000], [-1000,1000], color='black', linestyle='--', alpha=0.5, zorder=1)
    ax.grid(True, linestyle='--', alpha=0.5, zorder=0)

    # axlims = [-65, 15]
    ax.vlines(x=0, ymin=axlims[0], ymax=axlims[1], colors='gray', linestyles='-', alpha=0.5)
    ax.hlines(y=0, xmin=axlims[0], xmax=axlims[1], colors='gray', linestyles='-', alpha=0.5)
    ax.set_xlim(axlims)
    ax.set_ylim(axlims)
    ax.set_xlabel('Estimated')
    ax.set_ylabel('Observed')
    
    lincal = stats.linregress(cal_pred[stat_var].values, cal_obs[stat_var].values)

    # Plot the fitted line using plt.axline
    ax.axline(xy1=(0, lincal.intercept), slope=lincal.slope, color='r', 
            label=f'y={lincal.slope:.2f}x+{lincal.intercept:.2f}')

    ax.legend()

    return ax 

# %%  Utility functions ========
def label_run_options(run_list, prefix='feat'):
    """ 
    Convert list to a labeled dictionary.
    @param    run_list: list of items to label
    """
    ascii_uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    runkeys = [prefix + ascii_uppercase[i] for i in range(len(run_list))]
    run_options = {runkeys[i]: run_list[i] for i in range(len(run_list))}

    return run_options, runkeys 

def make_run_tags(feat_options, data_options, target_options):
    """ 
    @ param   feat_options: dict of feature lists (make_feat_dict())
               data_options: dict of datasets for training, validation
                    data_options = {'float': [trainClasses_float, valClasses],
                        'ship': [trainClasses_ship, valClasses],
                        'combined': [trainClasses, valClasses]}
               target_options: list of target variable names"""
    # Automatically generate run tag combinations
    run_tags = []
    for key1 in feat_options.keys():
        for key2 in data_options.keys():
            for target in target_options:
                run_tags.append(key1 + '-' + key2 + '-' + target)
    return run_tags

def expand_hyperparam_tag(hyper_tag):
    """ 
    Temp function for translating a run tag e.g. "maxfeat1_minspit5_nest1000" into a dict of hyperparameters
    For real tuning, would typically automate / pass a grid of parameters to GridSearchCV or similar
    """
    maxfeat = int(hyper_tag.split('_')[0].replace('maxfeat', ''))
    minsplit = int(hyper_tag.split('_')[1].replace('minsplit', ''))
    nestimators = int(hyper_tag.split('_')[2].replace('nest', ''))
    return {'max_features': maxfeat, 'min_samples_split': minsplit, 'n_estimators': nestimators}


def expand_datetime(data, type='dataframe'):
    """ Choose "dataframe" or "dataset" type to expand datetime into year, month, day"""
    out = data.copy()
    if type == 'dataframe':
        out['year'] = data.datetime.astype('datetime64[ns]').map(lambda x: x.year)
        out['month'] = data.datetime.astype('datetime64[ns]').map(lambda x: x.month)
        out['day'] = data.datetime.astype('datetime64[ns]').map(lambda x: x.day)
    elif type == 'dataset':
        out['year'] = data.datetime.astype('datetime64[ns]').dt.year
        out['month'] = data.datetime.astype('datetime64[ns]').dt.month
        out['day'] = data.datetime.astype('datetime64[ns]').dt.day
        out = out.set_coords(['year', 'month', 'day'])
    return out

def datetime2linear(time, ref_time):
    """" Return time in YTD format from datetime format."""
    return (time - np.datetime64(ref_time))/np.timedelta64(1, 'D')

def linear2datetime(num, ref_time):
    """" Return datetime format to YTD.
    @ param num: (int) number of days since ref_time
      ref_time: (str) reference time in 'YYYY-MM-DD' format
    """
    return (num * np.timedelta64(1,'D')) + np.datetime64(ref_time)

def add_seasonal_sines(day_of_year):
    """ Return sinusoidal seasonal variables for a given day_of_year
    Note day_of_year can be days since the start of any reference year 
    
    :param day_of_year: (float) datetime converted to days since Jan 1 (linear_time)
    """

    day_of_year = day_of_year%365.25
    ydcos = np.cos(2*np.pi*np.array(day_of_year)/365.25)
    ydsin = np.sin(2*np.pi*np.array(day_of_year)/365.25)

    return [ydcos, ydsin]


def set_longitude_range(df, end_type = '360'):
    """ Switch between 0-360 to -180,180 range"""
    df = df.copy()
    if end_type == '180':
        inds = df['longitude']>180
        df.loc[inds, 'longitude'] = df.loc[inds, 'longitude'].apply(lambda x: x-360)
    elif end_type == '360':
        inds = df['longitude']<0
        df.loc[inds, 'longitude'] = df.loc[inds, 'longitude'].apply(lambda x: x+360)
    return df

# def list_profile_DFs(platdf):
#     list = []
#     for profid in platdf.profid.unique():
#         list.append(platdf[platdf.profid==profid])
#     return list 


# %% Argopy processing
def create_argo_dataframe(floatDS, bgc_list = []):
    """
    Return dataframe from a single core or BGC float dataset, accessed with Argopy. 
    Assumed to be used in 'expert' mode, i.e. not quality-controlled yet for BGC.
    (From Argopy, download and use .point2profile() and then .to_dataframe() to get input float dataframe)

    :param floatDS: float xr Dataset with profiles 
    :param bgc_list: list of BGC variables to include in the final dataframe
                        ex. ['pH', 'oxygen', 'nitrate'] 
    :return: floatDF (pd.DataFrame): 
    """
    floatDF = floatDS.to_dataframe().reset_index()

    # Default columns to rename, starting with necessary properties across core/bgc
    # Note that Argopy "research mode" has removed "ADJUSTED" from column names
    new_columns = {'LATITUDE':'latitude','LONGITUDE':'longitude', 'TIME':'datetime', 
                'CYCLE_NUMBER':'cycle_number', 'PLATFORM_NUMBER':'wmoid', 
                'PRES_ADJUSTED':'pressure', 'TEMP_ADJUSTED':'temperature', 'PSAL_ADJUSTED':'salinity'}
    # Rename QC and error columns
    new_columns.update({'TIME_QC': 'time_qc', 'POSITION_QC': 'position_qc', 
                        'PRES_ADJUSTED_QC': 'pressure_qc', 
                        'TEMP_ADJUSTED_QC': 'temperature_qc','PSAL_ADJUSTED_QC': 'salinity_qc'})
    new_columns.update({'PRES_ADJUSTED_ERROR': 'pres_error', 
                        'PSAL_ADJUSTED_ERROR': 'psal_error', 'TEMP_ADJUSTED_ERROR': 'temp_error'})
    
    # output_vars = new_columns.values()

    # ==================
    # Add BGC variables to the new column names
    if 'pH' in bgc_list: # expert mode
        new_columns.update({'PH_IN_SITU_TOTAL_ADJUSTED': 'pH', 'PH_IN_SITU_TOTAL_ADJUSTED_QC': 'pH_qc',
                            'PH_IN_SITU_TOTAL_ADJUSTED_ERROR': 'pH_error'})
    if 'oxygen' in bgc_list: 
        new_columns.update({'DOXY_ADJUSTED': 'oxygen', 'DOXY_ADJUSTED_QC': 'oxygen_qc',
                            'DOXY_ADJUSTED_ERROR': 'oxygen_error'})
    if 'nitrate' in bgc_list:
        new_columns.update({'NITRATE_ADJUSTED': 'nitrate', 'NITRATE_ADJUSTED_QC': 'nitrate_qc',
                            'NITRATE_ADJUSTED_ERROR': 'nitrate_error'})
    # ==================

    floatDF.rename(columns=new_columns, inplace=True)

    # Create a unique profile id to be a useful index
    # Make sure strings are zfilled so 1st and 10th profile are different
    floatDF['profid'] = floatDF.apply(lambda x: str(x.wmoid) + '_cyc' + str(x.cycle_number).zfill(3), axis=1)

    # Add calculated variables using gsw
    floatDF['SA']= gsw.SA_from_SP(floatDF['salinity'],floatDF['pressure'],floatDF['longitude'],floatDF['latitude'])
    floatDF['CT'] = gsw.CT_from_t(floatDF['SA'], floatDF['temperature'], floatDF['pressure']) 
    floatDF['sigma0'] = gsw.sigma0(floatDF.SA.values, floatDF.CT.values)
    floatDF['spice'] = gsw.spiciness0(floatDF["SA"].values, floatDF["CT"].values)

    # Turn all QC flags into strings
    qc_vars = [var for var in floatDF.columns.tolist() if '_qc' in var]
    for k in qc_vars:
        floatDF[k] = floatDF[k].astype(str)

    # Standard variable list to return (core)
    # Can reorder by changing the output_vars list 
    output_vars = ['wmoid', 'profid', 'latitude', 'longitude', 'datetime', 
            'pressure', 'CT', 'SA', 'sigma0', 'spice',
            'temperature', 'salinity',
            'temperature_qc', 'salinity_qc', 'pressure_qc',
            'time_qc', 'position_qc',
            'temp_error', 'psal_error', 'pres_error']
    
    for x in bgc_list:
        output_vars = output_vars + [x, x+'_qc', x+'_error']

    return floatDF[output_vars]

def filter_qc_flags(float_df, qc_vars = 'all', use_flags=['1', '2', '5', '8']):
        """
        Filter a dataframe based on QC flags.
        Can choose different QC flags for different variables by calling the function multiple times.
        Note Argopy has this function, but this one allows you to track #obs, filter on position QC.
        @param: float_df (pd.DataFrame): dataframe of float data
                qc_vars (list): list of QC variables to filter
                        default 'all' filters on any variable with '_qc' in the name
                        ['temperature_qc', 'salinity_qc', 'pressure_qc', 'time_qc', 'position_qc', 'pH_qc']
                use_flags : flags that pass QC; default are standard argo QC flags 1, 2, and 8
                        '1' for 'good' data (only '1' returned in 'research' mode)
                        '2' for 'probably good' data
                        '5' for 'changed' data (rare; for position qc where lat/lon was adjusted)
                        '8' for 'interpolated/estimated' data
        @return: float_qc (pd.DataFrame)
        """ 
        print('Using flags: ', use_flags)
        float_qc = float_df.copy().reset_index()
        print ('# of profiles before QC filtering: \t', len(float_qc.profid.unique()))
        print('# of obs before QC filtering: \t\t', len(float_qc), '\n')

        if qc_vars == 'all':
                qc_vars = [var for var in float_qc.columns.tolist() if '_qc' in var]
        
        # for var in qc_vars:
        #         float_qc = float_qc[float_qc[var].isin(use_flags)]
        #         print('# of obs after ', var, ': \t\t', len(float_qc))
        

        qc_table = pd.DataFrame(columns= (use_flags + ['nobs_dropped', 'nobs_remaining']), index=qc_vars)
        for var in qc_vars:
                prevlen = len(float_qc) # store length before filtering
                for flag in use_flags:
                        qc_table.loc[var, flag] = len(float_qc[float_qc[var] == flag])

                # Filter based on use_flags
                float_qc = float_qc[float_qc[var].isin(use_flags)]
                qc_table.loc[var, 'nobs_dropped'] = int(prevlen - len(float_qc))
                qc_table.loc[var, 'nobs_remaining'] = len(float_qc)
        
        print(qc_table)

        print ('\n# of profiles after QC filtering: \t', str(len(float_qc.profid.unique())) + '\n')
        return float_qc
        
def add_mlp(platDF, threshold=0.03, pres_lim=[5,15]):  
    """  
    Calculating mixed layer pressure (MLP) for each Argo profile 
    Use linear interpolation to find mixed layer pressure between two nearest pressure levels

    @param:     platDF
                threshold: Density threshold for mixed layer pressure calculation (default is 0.03 kg/m^3)
    @return:    
    """
    prof_mlps = pd.DataFrame(index=platDF.profid.unique(), columns=['mlp'])
    no_data = [] 

    for id, prof in platDF.groupby('profid'):
        prof_df = prof.reset_index().copy()

        try: # general catch for missing data
            dens10 = prof_df.loc[(prof_df.pressure>pres_lim[0]) & (prof_df.pressure<pres_lim[1])].sigma0.mean()
            dens_tofind = dens10 + threshold 
            mask = prof_df.sigma0.values > dens_tofind

            if mask.any(): # If any values meet threshold density condition
                idx = prof_df.sigma0.index[np.argmax(mask)]
                (p0,d0)= (prof_df.pressure[np.argmax(mask)-1], prof_df.sigma0[np.argmax(mask)-1]) # obs just above mlp
                (p1,d1)= (prof_df.pressure[np.argmax(mask)], prof_df.sigma0[np.argmax(mask)]) # first obs below mlp

                mlp = p1 + (dens_tofind - d1) * ((p1-p0)/(d1-d0)) # Linear interpolation
                prof_mlps.loc[id, 'mlp'] = mlp

            else: 
                prof_mlps.loc[id, 'mlp'] = np.nan
        except: 
            no_data.append(id) # option to add this to return
    
    platDF['mlp'] = platDF.profid.apply(lambda x: prof_mlps.loc[x, 'mlp'] if x in prof_mlps.index else np.nan)
    platDF['mld'] = -gsw.z_from_p(platDF['mlp'], platDF['latitude'])

    return platDF # prof_mlps, no_data

# %% Glider processing

# def create_glider_dataframe(gliderDS):




# Contact: Sangmin Song 
# sangsong@uw.edu
