# ML Tutorial, GO-BGC Data Workshop 2026

This tutorial guides participants through the development of a simple machine learning regression model (random forest) using BGC-Argo data. We apply the model to subsurface data from a glider from the [California Underwater Glider Network](https://globalocean.noaa.gov/project/california-underwater-glider-network/) to estimate a novel nitrate record over 2022. 


## Access

Start your Jupyterhub server with "Resource Allocation" at 29GB RAM. 
To download the tutorial, navigate to the folder you want to download the repository into, then run: 

```
git clone https://github.com/go-bgc/tutorial-machine-learning-2026
cd tutorial-machine-learning-2026
ls # view the files
```

The two files you need to open are:

1. `argo_regression_modeling.ipynb`: main Jupyter notebook that goes through an ML workflow
2. `argotools.py`: helper module to store functions used in the notebook


The data used in the tutorial are stored in the Jupyterhub folder `shared/go-bgc-2026/data/machine_learning_tutorial/`.

- `mldata_CUGNline66_2022_traj0.csv` : Glider data from line 66
- `mldata_ARGO_2014-2025_qc1258.csv` : Argo training data accessed with Argopy

