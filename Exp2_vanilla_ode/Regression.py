import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import csv
from sklearn.metrics import explained_variance_score
from scipy.integrate import odeint
from pysindy.differentiation import FiniteDifference
from sklearn.linear_model import LinearRegression
from scipy.interpolate import interp1d

fd = FiniteDifference(order=2, d=1)

# Set random seed for reproducibility
torch.manual_seed(42)

# Load array from the CSV file in another file
loaded_data_B_Major_FORC = np.loadtxt('Data/B_unsat_Major2FORC.csv', delimiter=',')
loaded_data_H_Major_FORC = np.loadtxt('Data/H_unsat_Major2FORC.csv', delimiter=',')
loaded_data_B_amp1 = np.loadtxt('Data/B_unsat_amp1.csv', delimiter=',')
loaded_data_H_amp1 = np.loadtxt('Data/H_unsat_amp1.csv', delimiter=',')
loaded_data_B_amp2 = np.loadtxt('Data/B_unsat_amp2.csv', delimiter=',')
loaded_data_H_amp2 = np.loadtxt('Data/H_unsat_amp2.csv', delimiter=',')

B_Major_FORC = loaded_data_B_Major_FORC.reshape(-1,1)
H_Major_FORC = loaded_data_H_Major_FORC.reshape(-1,1)
B_amp1 = loaded_data_B_amp1.reshape(-1,1)
H_amp1 = loaded_data_H_amp1.reshape(-1,1)
B_amp2 = loaded_data_B_amp2.reshape(-1,1)
H_amp2 = loaded_data_H_amp2.reshape(-1,1)

B_major = B_Major_FORC[:595]
H_major = H_Major_FORC[:595]

B1 = B_Major_FORC[596:795]
H1 = H_Major_FORC[596:795]

B2 = B_Major_FORC[995:]
H2 = H_Major_FORC[995:]

B_amp1 = loaded_data_B_amp1.reshape(-1,1)
H_amp1 = loaded_data_H_amp1.reshape(-1,1)
B_amp2 = loaded_data_B_amp2.reshape(-1,1)
H_amp2 = loaded_data_H_amp2.reshape(-1,1)

##########################################################
##################### Scaling the data ###################
##########################################################
def min_max_scaling(X):
    X_min = np.min(X)
    X_max = np.max(X)
    X_scaled = (X - X_min) / (X_max - X_min) * 2 - 1
    return X_scaled, X_min, X_max

def min_max_scaling_inverse(X_scaled, X_min, X_max):
    X_original = (X_scaled + 1) / 2 * (X_max - X_min) + X_min
    return X_original

# Min-Max Scaling
B_Major_FORC_scaled, B_min, B_max = min_max_scaling(loaded_data_B_Major_FORC)
H_Major_FORC_scaled, H_min, H_max = min_max_scaling(loaded_data_H_Major_FORC)

B_Major_FORC_scaled = B_Major_FORC_scaled.reshape(-1,1)
H_Major_FORC_scaled = H_Major_FORC_scaled.reshape(-1,1)

B_major_scaled_train = B_Major_FORC_scaled[:595]
H_major_scaled_train = H_Major_FORC_scaled[:595]

B1_scaled_test = B_Major_FORC_scaled[596:795]
H1_scaled_test = H_Major_FORC_scaled[596:795]

B2_scaled_test = B_Major_FORC_scaled[995:]
H2_scaled_test = H_Major_FORC_scaled[995:]

B_amp1_scaled = (loaded_data_B_amp1 - B_min) / (B_max - B_min) * 2 - 1
H_amp1_scaled = (loaded_data_H_amp1 - H_min) / (H_max - H_min) * 2 - 1

B_amp1_scaled_test = B_amp1_scaled.reshape(-1,1)
H_amp1_scaled_test = H_amp1_scaled.reshape(-1,1)

B_amp2_scaled = (loaded_data_B_amp2 - B_min) / (B_max - B_min) * 2 - 1
H_amp2_scaled = (loaded_data_H_amp2 - H_min) / (H_max - H_min) * 2 - 1

B_amp2_scaled_test = B_amp2_scaled.reshape(-1,1)
H_amp2_scaled_test = H_amp2_scaled.reshape(-1,1)

###################################################
########### Train and test set preparation ########
###################################################

x_train = np.concatenate([B_major_scaled_train[:-1], H_major_scaled_train[:-1]], axis=1)
y_train = B_major_scaled_train[1:]

x_test_1 = np.concatenate([B1_scaled_test[0].reshape(-1,1), H1_scaled_test[0].reshape(-1,1)], axis=1)
y_test_1 = B1_scaled_test[1:]

x_test_2 = np.concatenate([B2_scaled_test[0].reshape(-1,1), H2_scaled_test[0].reshape(-1,1)], axis=1)
y_test_2 = B2_scaled_test[1:]

x_test_amp1 = np.concatenate([B_amp1_scaled_test[0].reshape(-1,1), H_amp1_scaled_test[0].reshape(-1,1)], axis=1)
y_test_amp1 = B_amp1_scaled_test[1:]

x_test_amp2 = np.concatenate([B_amp2_scaled_test[0].reshape(-1,1), H_amp2_scaled_test[0].reshape(-1,1)], axis=1)
y_test_amp2 = B_amp2_scaled_test[1:]

# Regression

## ODE model
## B'' = \alpha_1 B + \alpha_2 B' + \alpha_3 H + \alpha_4 |B|^2 + \alpha_5 |B'|^2 + \alpha_6 |H|^2 +\alpha_7

h = H_major_scaled_train
b = B_major_scaled_train

t = np.linspace(0, 1, h.shape[0])

dh = fd._differentiate(h, t)
db = fd._differentiate(b, t)
d2b = fd._differentiate(db, t)

term1 = b
term2 = db
term3 = h
term4 = np.abs(b)**2
term5 = np.abs(db)**2
term6 = np.abs(h)**2

X = np.concatenate((term1, term2, term3, term4, term5, term6), axis=1)
y = d2b

reg = LinearRegression(fit_intercept=True).fit(X, y)
print(reg.score(X, y))
print(reg.coef_)
print(reg.intercept_)

## Obtained ODE
## B'' = 195.9 B + 24.5 B' -769.6 H -18.3 |B|^2 -1.3 |B'|^2 -115.6 |H|^2 + 57.05

## Now using odeint to predict curve for novel inputs
def system(state, t, h_interp):
    x1, x2 = state  # Unpack the state vector
    # Define the derivatives
    h_val = h_interp(t)
    dx1_dt = x2
    dx2_dt = (195.9 * x1 + 24.5 * x2 - 769.6 * h_val - 18.3 * np.abs(x1)**2 - 1.3 * np.abs(x2)**2 - 115.6 * np.abs(h_val)**2 + 57.05)
    return [dx1_dt, dx2_dt]

h = H1_scaled_test.reshape(-1,)
b = B1_scaled_test.reshape(-1,)
t = np.linspace(0, 1, h.shape[0])
db = fd._differentiate(b, t)

# Create the interpolation function for x with extrapolation
h_interp = interp1d(t, h, fill_value="extrapolate")

# Initial conditions
b0 = B1_scaled_test[0].item()    # Initial value of B
b_prime0 = db[0]  # Initial value of B'
state0 = [b0, b_prime0]

# Solve the ODE system
solution = odeint(system, state0, t, args=(h_interp,))

# Extract solutions
prediction_1 = solution[:, 0]
############

h = H2_scaled_test.reshape(-1,)
b = B2_scaled_test.reshape(-1,)
t = np.linspace(0, 1, h.shape[0])
db = fd._differentiate(b, t)

# Create the interpolation function for x with extrapolation
h_interp = interp1d(t, h, fill_value="extrapolate")

# Initial conditions
b0 = B2_scaled_test[0].item()    # Initial value of B
b_prime0 = db[0]  # Initial value of B'
state0 = [b0, b_prime0]

# Solve the ODE system
solution = odeint(system, state0, t, args=(h_interp,))

# Extract solutions
prediction_2 = solution[:, 0]

#################
h = H_amp1_scaled_test.reshape(-1,)
b = B_amp1_scaled_test.reshape(-1,)
t = np.linspace(0, 1, h.shape[0])
db = fd._differentiate(b, t)

# Create the interpolation function for x with extrapolation
h_interp = interp1d(t, h, fill_value="extrapolate")

# Initial conditions
b0 = B_amp1_scaled_test[0].item()    # Initial value of B
b_prime0 = db[0]  # Initial value of B'
state0 = [b0, b_prime0]

# Solve the ODE system
solution = odeint(system, state0, t, args=(h_interp,))

# Extract solutions
prediction_amp1 = solution[:, 0]

##################
h = H_amp2_scaled_test.reshape(-1,)
b = B_amp2_scaled_test.reshape(-1,)
t = np.linspace(0, 1, h.shape[0])
db = fd._differentiate(b, t)

# Create the interpolation function for x with extrapolation
h_interp = interp1d(t, h, fill_value="extrapolate")

# Initial conditions
b0 = B_amp2_scaled_test[0].item()    # Initial value of B
b_prime0 = db[0]  # Initial value of B'
state0 = [b0, b_prime0]

# Solve the ODE system
solution = odeint(system, state0, t, args=(h_interp,))

# Extract solutions
prediction_amp2 = solution[:, 0]
#######

test_output_data_1 = np.array(prediction_1)
test_output_data_2 = np.array(prediction_2)
test_output_data_amp1 = np.array(prediction_amp1)
test_output_data_amp2 = np.array(prediction_amp2)

test_output_data_1 = test_output_data_1[:-1]
test_output_data_2 = test_output_data_2[:-1]
test_output_data_amp1 = test_output_data_amp1[:-1]
test_output_data_amp2 = test_output_data_amp2[:-1]

test_output_data_1 = min_max_scaling_inverse(test_output_data_1, B_min, B_max)
test_output_data_2 = min_max_scaling_inverse(test_output_data_2, B_min, B_max)
test_output_data_amp1 = min_max_scaling_inverse(test_output_data_amp1, B_min, B_max)
test_output_data_amp2 = min_max_scaling_inverse(test_output_data_amp2, B_min, B_max)
y_test_1 = min_max_scaling_inverse(y_test_1, B_min, B_max)
y_test_2 = min_max_scaling_inverse(y_test_2, B_min, B_max)
y_test_amp1 = min_max_scaling_inverse(y_test_amp1, B_min, B_max)
y_test_amp2 = min_max_scaling_inverse(y_test_amp2, B_min, B_max)

print("#######################################")

# Compute the relative L2 error norm (generalization error)
relative_error_test = np.mean((test_output_data_1.reshape(-1,1) - y_test_1)**2) / np.mean(y_test_1**2)
print("Relative Error Test FORC 1 HystRNN : ", relative_error_test)
relative_error_test = np.mean((test_output_data_2.reshape(-1,1) - y_test_2)**2) / np.mean(y_test_2**2)
print("Relative Error Test FORC 2 HystRNN: ", relative_error_test)
relative_error_test = np.mean((test_output_data_amp1.reshape(-1,1) - y_test_amp1)**2) / np.mean(y_test_amp1**2)
print("Relative Error Test amp 1 HystRNN: ", relative_error_test)
relative_error_test = np.mean((test_output_data_amp2.reshape(-1,1) - y_test_amp2)**2) / np.mean(y_test_amp2**2)
print("Relative Error Test amp 2 HystRNN: ", relative_error_test)

print("#######################################")

R_abs = np.max(np.abs(test_output_data_1.reshape(-1,1) - y_test_1))
print("Max error FORC 1 HystRNN : ", R_abs)
R_abs = np.max(np.abs(test_output_data_2.reshape(-1,1) - y_test_2))
print("Max error FORC 2 HystRNN : ", R_abs)
R_abs = np.max(np.abs(test_output_data_amp1.reshape(-1,1) - y_test_amp1))
print("Max error amp 1 HystRNN : ", R_abs)
R_abs = np.max(np.abs(test_output_data_amp2.reshape(-1,1) - y_test_amp2))
print("Max error amp 2 HystRNN : ", R_abs)

print("#######################################")

evs = explained_variance_score(y_test_1, test_output_data_1.reshape(-1,1))
print("Explained Variance Score FORC 1 HystRNN:", evs)

evs = explained_variance_score(y_test_2, test_output_data_2.reshape(-1,1))
print("Explained Variance Score FORC 2 HystRNN:", evs)

evs = explained_variance_score(y_test_amp1, test_output_data_amp1.reshape(-1,1))
print("Explained Variance Score amp 1 HystRNN:", evs)

evs = explained_variance_score(y_test_amp2, test_output_data_amp2.reshape(-1,1))
print("Explained Variance Score amp 2 HystRNN:", evs)

print("#######################################")

MAE = np.mean(np.abs(test_output_data_1.reshape(-1,1) - y_test_1))
print("MAE FORC 1 HystRNN: ", MAE)
MAE = np.mean(np.abs(test_output_data_2.reshape(-1,1) - y_test_2))
print("MAE FORC 2 HystRNN: ", MAE)
MAE = np.mean(np.abs(test_output_data_amp1.reshape(-1,1) - y_test_amp1))
print("MAE amp 1 HystRNN: ", MAE)
MAE = np.mean(np.abs(test_output_data_amp2.reshape(-1,1) - y_test_amp2))
print("MAE amp 2 HystRNN: ", MAE)

#####################################################
################# Fig. 3a ###########################
#####################################################

# Create the figure and axis objects with reduced width
fig, ax = plt.subplots(figsize=(5, 5))  # You can adjust the width (7 inches) and height (5 inches) as needed

# Plot the data with red and blue lines, one with dotted and one with solid style
ax.plot(H_major, B_major, color='blue', linestyle='solid', linewidth=3, label='Major loop')
ax.plot(H1, B1, color='red', linestyle='solid', linewidth=3, label='FORC')
ax.plot(H1[1:], test_output_data_1, color='black', linestyle='dashdot', linewidth=3, label='pred')

#ax.plot(H2, B2, color='red', linestyle='solid', linewidth=7, label='FORC')


# Set the axis labels with bold font weight
ax.set_xlabel(r"H[A/m]", fontsize=28, color='black')
ax.set_ylabel(r"B[T]", fontsize=28, color='black')

# Set the number of ticks for x-axis and y-axis to 3
ax.set_xticks([-125, 0, 125])
ax.set_yticks([-1.25, 0, 1.25])

# Set tick labels fontweight to bold and increase font size
ax.tick_params(axis='both', which='major', labelsize=28, width=2, length=10)

# Set the spines linewidth to bold
ax.spines['top'].set_linewidth(2)
ax.spines['right'].set_linewidth(2)
ax.spines['bottom'].set_linewidth(2)
ax.spines['left'].set_linewidth(2)

plt.savefig('Figures/ode_reg_1.jpeg', dpi=500, bbox_inches="tight")
plt.show()

#####################################################
################# Fig. 3d ###########################
#####################################################

# Create the figure and axis objects with reduced width
fig, ax = plt.subplots(figsize=(5, 5))  # You can adjust the width (7 inches) and height (5 inches) as needed

# Plot the data with red and blue lines, one with dotted and one with solid style
ax.plot(H_major, B_major, color='blue', linestyle='solid', linewidth=3, label='Major loop')
ax.plot(H2, B2, color='red', linestyle='solid', linewidth=3, label='FORC')
ax.plot(H2[1:], test_output_data_2, color='black', linestyle='dashdot', linewidth=3, label='pred')


# Set the axis labels with bold font weight
ax.set_xlabel(r"H[A/m]", fontsize=28, color='black')
ax.set_ylabel(r"B[T]", fontsize=28, color='black')

# Set the number of ticks for x-axis and y-axis to 3
ax.set_xticks([-125, 0, 125])
ax.set_yticks([-1.25, 0, 1.25])

# Set tick labels fontweight to bold and increase font size
ax.tick_params(axis='both', which='major', labelsize=28, width=2, length=10)

#Set the spines linewidth to bold
ax.spines['top'].set_linewidth(2)
ax.spines['right'].set_linewidth(2)
ax.spines['bottom'].set_linewidth(2)
ax.spines['left'].set_linewidth(2)

plt.savefig('Figures/ode_reg_2.jpeg', dpi=500, bbox_inches="tight")
plt.show()

#####################################################
################# Fig. 3g ###########################
#####################################################

# Create the figure and axis objects with reduced width
fig, ax = plt.subplots(figsize=(5, 5))  # You can adjust the width (7 inches) and height (5 inches) as needed

# Plot the data with red and blue lines, one with dotted and one with solid style
ax.plot(H_major, B_major, color='blue', linestyle='solid', linewidth=3, label='Major loop')
ax.plot(H_amp1, B_amp1, color='red', linestyle='solid', linewidth=3, label='FORC')
ax.plot(H_amp1[1:], test_output_data_amp1, color='black', linestyle='dashdot', linewidth=3, label='pred')


# Set the axis labels with bold font weight
ax.set_xlabel(r"H[A/m]", fontsize=28, color='black')
ax.set_ylabel(r"B[T]", fontsize=28, color='black')

# Set the number of ticks for x-axis and y-axis to 3
ax.set_xticks([-125, 0, 125])
ax.set_yticks([-5, 0, 5, 10, 15])

# Set tick labels fontweight to bold and increase font size
ax.tick_params(axis='both', which='major', labelsize=28, width=2, length=10)

#Set the spines linewidth to bold
ax.spines['top'].set_linewidth(2)
ax.spines['right'].set_linewidth(2)
ax.spines['bottom'].set_linewidth(2)
ax.spines['left'].set_linewidth(2)

plt.savefig('Figures/ode_reg_3.jpeg', dpi=500, bbox_inches="tight")
plt.show()

#####################################################
################# Fig. 3j ###########################
#####################################################


# Create the figure and axis objects with reduced width
fig, ax = plt.subplots(figsize=(5, 5))  # You can adjust the width (7 inches) and height (5 inches) as needed

# Plot the data with red and blue lines, one with dotted and one with solid style
ax.plot(H_major, B_major, color='blue', linestyle='solid', linewidth=3, label='Major loop')
ax.plot(H_amp2, B_amp2, color='red', linestyle='solid', linewidth=3, label='FORC')
ax.plot(H_amp2[1:], test_output_data_amp2, color='black', linestyle='dashdot', linewidth=3, label='pred')


# Set the axis labels with bold font weight
ax.set_xlabel(r"H[A/m]", fontsize=28, color='black')
ax.set_ylabel(r"B[T]", fontsize=28, color='black')

# Set the number of ticks for x-axis and y-axis to 3
ax.set_xticks([-125, 0, 125])
ax.set_yticks([-1.25, 0, 1.25])

# Set tick labels fontweight to bold and increase font size
ax.tick_params(axis='both', which='major', labelsize=28, width=2, length=10)

#Set the spines linewidth to bold
ax.spines['top'].set_linewidth(2)
ax.spines['right'].set_linewidth(2)
ax.spines['bottom'].set_linewidth(2)
ax.spines['left'].set_linewidth(2)

plt.savefig('Figures/ode_reg_4.jpeg', dpi=500, bbox_inches="tight")
plt.show()
