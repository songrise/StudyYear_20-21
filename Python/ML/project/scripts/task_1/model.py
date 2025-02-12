# -*- coding : utf-8 -*-
# @FileName  : model.py
# @Author    : Ruixiang JIANG (Songrise)
# @Time      : 2021-05-01
# @Github    ：https://github.com/songrise
# @Descriptions: Regression model and experiments for task 1


# %%

from sklearn.feature_selection import RFECV
from sklearn.svm import SVC
import keras
import numpy as np
import matplotlib.pyplot as plt
# import seaborn as sns
import pandas as pd

from my_linear_regression import MyLinearRegression
from sklearn.model_selection import KFold
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.ensemble import StackingRegressor
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import Lasso
from sklearn.linear_model import BayesianRidge
from sklearn.linear_model import ElasticNet
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import make_scorer
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import GridSearchCV
import pickle


# %%load data
train = pd.read_csv("../../data/processed_teleplay.csv", delimiter=",")
test = pd.read_csv("../../data/processed_newTeleplay.csv", delimiter=",")
# train = train[:1000]  # dev only

train = train.drop(["teleplay_id"], axis=1)
test = test.drop(["teleplay_id"], axis=1)
y_train = train["rating"]
X_train = train.drop(["rating"], axis=1)
del train

# %%
N_FOLD = 5  # used for model evaluation
OPT_N_FOLD = 3  # used for hyper-param searching
SEED = 4434
mse = make_scorer(mean_squared_error)


def rmse_cv(*args, **kwargs):
    return np.mean(np.sqrt(cross_val_score(*args, scoring=mse)))


# %%baseline
kf = KFold(N_FOLD)
lr_rmse = []
for train_index, test_index in kf.split(X_train):
    lr_X_train, lr_X_test = X_train.iloc[train_index], X_train.iloc[test_index]
    lr_y_train, lr_y_test = y_train.iloc[train_index], y_train.iloc[test_index]
    lr = MyLinearRegression()
    lr.fit(lr_X_train, lr_y_train)
    lr_rmse.append(np.sqrt(mean_squared_error(
        lr.predict(lr_X_test), lr_y_test)))

print("LR 5fold RMSE ", np.mean(lr_rmse))

# n = 2 expansion
lr_rmse = []
for train_index, test_index in kf.split(X_train):
    lr_X_train, lr_X_test = X_train.iloc[train_index], X_train.iloc[test_index]
    lr_y_train, lr_y_test = y_train.iloc[train_index], y_train.iloc[test_index]
    lr = MyLinearRegression(poly_degree=2)
    lr.fit(lr_X_train, lr_y_train)
    lr_rmse.append(np.sqrt(mean_squared_error(
        lr.predict(lr_X_test), lr_y_test)))

print("LR, n=2 expansion, 5fold RMSE ", np.mean(lr_rmse))

lasso = Lasso(alpha=1e-2)
print("Lasso, 5fold RMSE ", rmse_cv(lasso, X_train, y_train,  cv=N_FOLD))

# rf = RandomForestRegressor(random_state=SEED)
# print(rmse_cv(rf, X_train, y_train,  cv=N_FOLD))

mlp = MLPRegressor(hidden_layer_sizes=(300, 300, 200), learning_rate="adaptive",
                   random_state=SEED, max_iter=2000, early_stopping=True)

print("MLP 5fold RMSE ", rmse_cv(mlp, X_train, y_train,  cv=N_FOLD))

# %%model stacking
# used package because it has to be optimized as a whole by GridSearch CV
lr = LinearRegression()
rf = RandomForestRegressor(
    n_estimators=400, random_state=SEED)
# lasso = Lasso(random_state=SEED)
ridge = BayesianRidge()
svr = SVR()
knn = KNeighborsRegressor(27)
dt = DecisionTreeRegressor(max_depth=32)
gbdt = GradientBoostingRegressor(n_estimators=400, random_state=SEED)

base_models = [("lr", lr), ("rf", rf),
               ("ridge", ridge), ("dt", dt),
               ("svr", svr), ("knn", knn),
               ("gbdt", gbdt)]  # , ("mlp", mlp)]
meta_model = LinearRegression()

stacked = StackingRegressor(estimators=base_models,
                            final_estimator=meta_model, n_jobs=6, verbose=2)
try:
    with open("model.pickle", "rb") as m:
        stacked = pickle.load(m)
except FileNotFoundError:
    pass

print("Stacked model baseline RMSE: ", rmse_cv(
    stacked, X_train, y_train,  cv=N_FOLD))


# %%hyper-parameter optimization
# param_grid = {
#     "rf__min_samples_split": [3, 12],
#     # "rf__n_estimators": [100, 400],
#     #   "gbdt__n_estimators": [100, 400],
#     "svr__kernel": ["linear", "poly", "rbf"],
#     #   "knn__n_neighbors": [3, 9, 27],
#     "dt__max_depth": [32, None]
# }

# opt = GridSearchCV(stacked, param_grid=param_grid,
#                    cv=OPT_N_FOLD, scoring='neg_mean_squared_error', n_jobs=-1, verbose=2)
# opt.fit(X_train, y_train, verbose=2)
# print(opt.best_estimator_)
# %%RFE

# Create the RFE object and compute a cross-validated score.
svr = BayesianRidge()
# The "accuracy" scoring is proportional to the number of correct
# classifications

min_features_to_select = 1  # Minimum number of features to consider
rfecv = RFECV(estimator=svr, step=1, cv=N_FOLD,
              scoring=make_scorer(mean_squared_error, greater_is_better=False),
              min_features_to_select=min_features_to_select)
rfecv.fit(X_train, y_train)

print("Optimal number of features : %d" % rfecv.n_features_)

# Plot number of features VS. cross-validation scores
plt.figure()
plt.xlabel("Number of features selected")
plt.ylabel("Cross validation score (negative MSE)")
plt.plot(range(min_features_to_select,
               len(rfecv.grid_scores_) + min_features_to_select),
         rfecv.grid_scores_)
plt.show()

# %%save model
# the model is evaluated by cv, but not yet fitted.
stacked.fit(X_train, y_train)
with open('model.pickle', 'wb') as f:
    pickle.dump(stacked, f)


# %% Inference

pred = stacked.predict(test)
new_tele = pd.read_csv("../../data/New_teleplay.csv", delimiter=",")
new_tele["rating"] = pred
new_tele.to_csv("fin_19079662D_task1.csv", index=False)

# %%
