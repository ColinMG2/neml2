import neml2
from neml2 import SR2
import torch
import matplotlib.pyplot as plt
import pandas as pd
import os

torch.set_default_dtype(torch.double)
if torch.cuda.is_available():
    dev = "cuda:0"
    print("CUDA is available")
    print(f"CUDA version: {torch.version.cuda}")
else:
    dev = "cpu"
    print("CUDA is not available")
device = torch.device(dev)

model = neml2.load_model("test_model.i", "prediction")
model.to(device=device)  # Move model to the same device using named parameter
print(model)

# Load experimental data
path = '/home/colinmoose/neml2/cmg_projects/tensile_data'
data_frames = {}
for filename in os.listdir(path):
    if filename.endswith(".csv"):
        file_path = os.path.join(path, filename)
        df = pd.read_csv(file_path)
        if '621C' in filename:
            temp_label = '621C'
        elif '700C' in filename:
            temp_label = '700C'
        elif 'RT' in filename:
            temp_label = 'RT'
        elif '516C' in filename:
            temp_label = '516C'
        else:
            temp_label = 'unknown'
        
        new_df = df.rename(columns={'x':f'{temp_label}_strain', 'y':f'{temp_label}_stress'})
        data_frames[temp_label] = new_df

strain_data = {}
stress_data = {}

for temp_label, df in data_frames.items():
    strain_col = f'{temp_label}_strain'
    stress_col = f'{temp_label}_stress'
    strain = torch.tensor(df[strain_col].values, device=device)
    stress = torch.tensor(df[stress_col].values, device=device)
    max_stress_idx = torch.argmax(stress).item()
    strain = strain[:max_stress_idx + 1]
    stress = stress[:max_stress_idx + 1]
    strain = strain[:] - strain[0]
    stress = stress[:] - stress[0]
    strain_data[temp_label] = strain
    stress_data[temp_label] = stress
    print(f"For {temp_label}_data:\nStrain:\n{strain_data[temp_label]}\nStress:\n{stress_data[temp_label]}")

# Plot initial dataset
plt.figure()
for temp_label in strain_data:
    plt.plot(strain_data[temp_label].cpu().numpy(), stress_data[temp_label].cpu().numpy(), label=f"{temp_label}C")
plt.xlabel('Strain')
plt.ylabel('Stress (MPa)')
plt.title('Initial Dataset')
plt.grid()
plt.legend()
plt.savefig('clipped_init_data.png')

# Create strain and stress tensor inputs for the model
# For a tensile test, strain tensor has only 11 component non-zero
# SR2 in NEML2 uses Voigt notation: [11, 22, 33, 23, 13, 12]
strain_11_exp = strain_data['RT']
stress_11_exp = stress_data['RT']

n_points = len(strain_11_exp)

strain_tensor = torch.zeros((n_points, 6), device=device)
stress_tensor = torch.zeros((n_points, 6), device=device)
strain_tensor[:, 0] = strain_11_exp  # 11 component
stress_tensor[:, 0] = stress_11_exp

# Convert to SR2 format
strain_exp = SR2(strain_tensor)
stress_exp = SR2(stress_tensor)

strain_vals = strain_exp.torch()[:, 0]
stress_results = []

# Model inputs
model_input = {
    "forces/E": strain_exp,
    "forces/t": neml2.Scalar.full(1, device=device)

}

# Calculate input
with torch.no_grad():
    init_output = model.value(model_input)

input_strain = strain_exp.torch()[:,0]
init_stress = init_output["state/S"].torch()
print(f"Initial strain input:\n{input_strain}\n")
print(f"Initial strain input size:\n{input_strain.size()}")
print(f"Initial model output:\n{init_stress}")
print(f"Initial model output size:\n{init_stress.size()}")

plt.figure()
plt.plot(input_strain.cpu().detach().numpy(), init_stress.cpu().detach().numpy()[:,0],'r--')
plt.xlabel('Strain')
plt.ylabel('Stress (MPa)')
plt.title('Initial Model Output')
plt.savefig('init_model_output.png')

# Parameter optimization setup using individual parameters (maintaining gradient flow)
# Create optimizable parameters directly from model parameters
sy = model.eq4_sy.torch().clone().detach().to(device).requires_grad_(True)
eta = model.eq6_eta.torch().clone().detach().to(device).requires_grad_(True)
n = model.eq6_n.torch().clone().detach().to(device).requires_grad_(True)

# Store parameters in a list for easy iteration
params = [sy, eta, n]
param_names = ['sy', 'eta', 'n']

# Learning rates for each parameter (different scales)
learning_rates = [1e-3, 1e-7, 1e-6]

# setup SGD optimizer without momentum (simple GD) for each parameter and respective learning rates
optim = torch.optim.SGD([
                                {'params':[sy], 'lr': learning_rates[0]},
                                {'params':[eta], 'lr': learning_rates[1]},
                                {'params':[n], 'lr': learning_rates[2]}])

# History tracking
loss_history = []
params_history = []
n_iter = 2000

print(f"Initial Parameters to optimize:")
print(f" sy: {sy.item():.6f}")
print(f" eta: {eta.item():.6f}")
print(f" n: {n.item():.6f}")
print(f"Parameter device: {sy.device}\n")

print(f"Starting optimization loop with {n_points} data points...")

# Generate Initial Results BEFORE optimization
with torch.no_grad():
    initial_output = model.value(model_input)
    initial_stress = initial_output["state/S"].torch()[:,0]

for i in range(n_iter):
    # initialize gradients to zero
    optim.zero_grad()
    
    # Update model parameters while maintaining gradient connection
    model.eq4_sy = neml2.Scalar(sy)
    model.eq6_eta = neml2.Scalar(eta)
    model.eq6_n = neml2.Scalar(n)
    
    # Enable gradients on model parameters
    model.eq4_sy.requires_grad_(True)
    model.eq6_eta.requires_grad_(True)
    model.eq6_n.requires_grad_(True)

    try:
        # Calculate model output
        stress = model.value(model_input)["state/S"]

        # Calculate loss
        loss = torch.nn.functional.mse_loss(stress.torch(), stress_exp.torch(), reduction='sum')
        
        # Record states
        loss_history.append(loss.item())
        params_history.append([p.item() for p in params])  # Store parameter values

        if i % 10 == 0:  # Print every 10 iterations
            print(f"Iteration {i}: Loss = {loss.item():.6f}, sy = {sy.item():.6f}, eta = {eta.item():.6f}, n = {n.item():.6f}")
        
        # Compute gradients
        loss.backward()

        # Copy gradients from NEML2 model parameters to torch optimizer parameters
        sy.grad = model.eq4_sy.torch().grad.clone()
        eta.grad = model.eq6_eta.torch().grad.clone()
        n.grad = model.eq6_n.torch().grad.clone()

        optim.step()

        if i % 10 == 0:
            grad_info = []
            for j, (param, name) in enumerate(zip(params, param_names)):
                if param.grad is not None:
                    grad_info.append(f"{name}: {param.grad.item():.6f}")
                else:
                    grad_info.append(f"{name}: None")
            print(f"  Gradients - {', '.join(grad_info)}")
        
    except Exception as e:
        print(f"Error at iteration {i}: {e}")
        print(f"  Parameter values at error: sy={sy.item():.3f}, eta={eta.item():.3f}, n={n.item():.3f}")
        break

# Generate final prediction with optimized parameters
with torch.no_grad():
    model.eq2_G = neml2.Scalar.full(params[0], device=device)
    model.eq2_K = neml2.Scalar.full(params[1], device=device)
    final_output = model.value(model_input)
    final_stress = final_output["state/S"].torch()[:,0]

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
    plt.savefig('Loss_history.png')

    # Plot model stress vs strain graph comparing to exp data
    plt.figure()
    plt.plot(strain_data['RT'].cpu().numpy(), stress_data['RT'].cpu().numpy(), 'k--', label="exp_data")
    plt.plot(strain_11_exp.cpu().numpy(), initial_stress.cpu().detach().numpy(), 'b-', label="init_guess")
    plt.plot(strain_11_exp.cpu().numpy(), final_stress.cpu().detach().numpy(), 'r-', label="final_guess")
    plt.xlabel("Strain")
    plt.ylabel("Stress (MPa)")
    plt.grid()
    plt.legend()
    plt.title("Stress vs. Strain")
    plt.savefig('stress_strain_comp.png')

    plt.tight_layout()
    plt.show()
    
    print(f"Final loss: {loss_history[-1]:.6f}")
    print(f"Final parameters:")
    print(f"  sy: {params[0].item():.6f} MPa")
    print(f"  eta: {params[1].item():.6f}")
    print(f"  n: {params[2].item():.6f}")
else:
    print("No optimization data to plot - optimization may have failed immediately")