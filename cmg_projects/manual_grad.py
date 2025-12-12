import neml2
from neml2 import SR2
import torch
import matplotlib.pyplot as plt
import pandas as pd

torch.set_default_dtype(torch.double)
if torch.cuda.is_available():
    dev = "cuda:0"
    print("CUDA is available")
    print(f"CUDA version: {torch.version.cuda}")
else:
    dev = "cpu"
    print("CUDA is not available")
device = torch.device(dev)

model = neml2.load_model("test_model.i", "model")
model.to(device=device)  # Move model to the same device using named parameter
print(model)

# Load experimental data
rm_data = pd.read_csv("/home/colinmoose/neml2/cmg_projects/tensile_data/Tensile_1_Fig_16.csv")
temp1_data = pd.read_csv("/home/colinmoose/neml2/cmg_projects/tensile_data/Tensile_1_Fig_18_Temp_621C.csv")
temp2_data = pd.read_csv("/home/colinmoose/neml2/cmg_projects/tensile_data/Tensile_1_Fig17_Temp_516C.csv")
temp3_data = pd.read_csv("/home/colinmoose/neml2/cmg_projects/tensile_data/Tensile_1_Fig_19_Temp 700C.csv")

# For tensile test, we need to create proper strain tensors
strain_11_exp = torch.tensor(rm_data['x'].values, device=device)  # Axial strain
stress_11_exp = torch.tensor(rm_data['y'].values, device=device)  # Axial stress

# Clip values to not include values after ultimate tensile strength
max_stress_idx = torch.argmax(stress_11_exp).item()
strain_11_exp = strain_11_exp[:max_stress_idx + 1]
stress_11_exp = stress_11_exp[:max_stress_idx + 1]

# Create strain and stress tensor inputs for the model
# For a tensile test, strain tensor has only 11 component non-zero
# SR2 in NEML2 uses Voigt notation: [11, 22, 33, 23, 13, 12]
n_points = len(strain_11_exp)

strain_tensor = torch.zeros((n_points, 6), device=device)
stress_tensor = torch.zeros((n_points, 6), device=device)
strain_tensor[:, 0] = strain_11_exp  # 11 component
stress_tensor[:, 0] = stress_11_exp

# Convert to SR2 format
strain_exp = SR2(strain_tensor)
stress_exp = SR2(stress_tensor)

# Create time inputs (required for the model)
t_current = torch.ones(n_points, device=device) * 1.0  # Current time
t_old = torch.zeros(n_points, device=device)  # Old time
Ep_old = torch.zeros((n_points, 6), device=device)  # Old plastic strain

print(f"11 strain values:\n{strain_exp.base[0]}")
print(f"11 stress values:\n{stress_exp.base[0]}")

# Parameter optimization setup using individual parameters (maintaining gradient flow)
# Create optimizable parameters directly from model parameters
sy = model.yield_function_sy.torch().clone().detach().to(device).requires_grad_(True)
eta = model.flow_rate_eta.torch().clone().detach().to(device).requires_grad_(True)
n = model.flow_rate_n.torch().clone().detach().to(device).requires_grad_(True)

# Store parameters in a list for easy iteration
params = [sy, eta, n]
param_names = ['sy', 'eta', 'n']

# Learning rates for each parameter (different scales)
learning_rates = [1e-3, 5e-8, 1e-6]  # [sy, eta, n]

# History tracking
loss_history = []
params_history = []  # Will store [sy, eta, n] at each iteration
n_iter = 2000  # Reduced iterations to prevent getting stuck

print(f"Initial Parameters to optimize:")
print(f" sy: {sy.item():.6f}")
print(f" eta: {eta.item():.6f}")
print(f" n: {n.item():.6f}")
print(f"Parameter device: {sy.device}\n")

print(f"Starting optimization loop with {n_points} data points...")

for i in range(n_iter):
    # Clear gradients for all parameters
    for param in params:
        if param.grad is not None:
            param.grad.zero_()
    
    # Update model parameters while maintaining gradient connection
    model.yield_function_sy = neml2.Scalar(sy)
    model.flow_rate_eta = neml2.Scalar(eta)
    model.flow_rate_n = neml2.Scalar(n)
    
    # Enable gradients on model parameters
    model.yield_function_sy.requires_grad_(True)
    model.flow_rate_eta.requires_grad_(True)
    model.flow_rate_n.requires_grad_(True)

    # Calculate model output and loss with all required inputs
    try:
        model_input = {
            "forces/E": strain_exp,
            "forces/t": neml2.Scalar(t_current),
            "old_forces/t": neml2.Scalar(t_old),
            "old_state/internal/Ep": SR2(Ep_old),
            "state/internal/Ep": SR2(Ep_old)  # Initial guess
        }
        
        # Calculate model output
        output = model.value(model_input)
        stress = output["state/S"]

        # Calculate loss
        loss = torch.nn.functional.mse_loss(stress.torch(), stress_exp.torch(), reduction='sum')
        
        # Record states
        loss_history.append(loss.item())
        params_history.append([p.item() for p in params])  # Store parameter values

        if i % 10 == 0:  # Print every 10 iterations
            print(f"Iteration {i}: Loss = {loss.item():.6f}, sy = {sy.item():.6f}, eta = {eta.item():.6f}, n = {n.item():.6f}")
            print(f"  Requires grad - sy: {sy.requires_grad}, eta: {eta.requires_grad}, n: {n.requires_grad}")

        # Compute gradients
        loss.backward()
        
        if i % 10 == 0:  # Print gradient info
            grad_info = []
            for j, (param, name) in enumerate(zip(params, param_names)):
                if param.grad is not None:
                    grad_info.append(f"{name}: {param.grad.item():.6f}")
                else:
                    grad_info.append(f"{name}: None")
            print(f"  Gradients - {', '.join(grad_info)}")
        
        # Manual parameter update with individual learning rates
        with torch.no_grad():
            for j, param in enumerate(params):
                if param.grad is not None:
                    # Apply learning rate specific to this parameter
                    param -= learning_rates[j] * param.grad
        
    except Exception as e:
        print(f"Error at iteration {i}: {e}")
        print(f"  Parameter values at error: sy={sy.item():.3f}, eta={eta.item():.3f}, n={n.item():.3f}")
        break

# Generate Initial Results
with torch.no_grad():
    initial_results = model(model_input)

# Plot results
if len(loss_history) > 0:
    # Convert parameter history to arrays for plotting
    params_array = torch.tensor(params_history)
    sy_history = params_array[:, 0].numpy()
    eta_history = params_array[:, 1].numpy()
    n_history = params_array[:, 2].numpy()
    
    fig, ax1= plt.subplots(figsize=(10, 8))
    iterations = range(len(loss_history))
    
    # Plot loss
    ax1.plot(iterations, loss_history, 'k-', label='Loss')
    ax1.set_xscale('log')
    ax1.set_yscale('log')
    ax1.set_ylabel('Loss')
    ax1.legend()
    ax1.grid(True)
    
    # Plot parameters
    ax2 = ax1.twinx()
    ax2.plot(iterations, sy_history, 'b-', label='sy (MPa)')
    ax2.plot(iterations, eta_history, 'r-', label='eta')
    ax2.plot(iterations, n_history, 'g-', label='n')
    ax2.set_xlabel('Iteration')
    ax2.set_ylabel('Parameter values')
    ax2.legend()
    ax2.grid(True)

    # Plot model stress vs strain graph comparing to exp data
    plt.figure()
    plt.plot(strain_11_exp, stress_11_exp, 'k--', label="exp_data")
    plt.plot(strain_11_exp, initial_results, 'b', label="init_guess")
    plt.xlabel("Strain")
    plt.ylabel("Stress (MPa)")
    plt.grid()

    
    plt.tight_layout()
    plt.show()
    
    print(f"Final loss: {loss_history[-1]:.6f}")
    print(f"Final parameters:")
    print(f"  sy: {params[0].item():.6f} MPa")
    print(f"  eta: {params[1].item():.6f}")
    print(f"  n: {params[2].item():.6f}")
else:
    print("No optimization data to plot - optimization may have failed immediately")