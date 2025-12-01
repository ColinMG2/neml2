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
data = pd.read_csv("/home/colinmoose/neml2/Tensile_1_Fig_16.csv")

# For tensile test, we need to create proper strain tensors
strain_11_exp = torch.tensor(data['x'].values, device=device)  # Axial strain
stress_11_exp = torch.tensor(data['y'].values, device=device)  # Axial stress

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

# Gradient descent loop
gamma = 1e-3
loss_history = []
eta_history = []
n_history = []
n_iter = 1000

# Create optimizable parameters - start with just yield stress for stability
sy = model.yield_function_sy.torch().clone().detach().to(device).requires_grad_(True)
print(f"Initial Parameter to optimize:\n sy: {sy.item()}")
print(f"Parameter device: {sy.device}")

optim = torch.optim.Adam([sy], lr=gamma)

print(f"Starting optimization loop with {n_points} data points...")

for i in range(n_iter):
    # Clear gradients manually
    sy.grad = None
    
    # Update model parameter while maintaining gradient connection
    model.yield_function_sy = neml2.Scalar(sy)
    
    # Enable gradients on model parameter
    model.yield_function_sy.requires_grad_(True)

    # Calculate model output and loss with all required inputs
    try:
        model_input = {
            "forces/E": strain_exp,
            "forces/t": neml2.Scalar(t_current),
            "old_forces/t": neml2.Scalar(t_old),
            "old_state/internal/Ep": SR2(Ep_old),
            "state/internal/Ep": SR2(Ep_old)  # Initial guess
        }
        
        output = model.value(model_input)
        stress = output["state/S"]
        # Option 1: Current approach (L2 norm squared - equivalent to sum of squared errors)
        loss = torch.linalg.norm(stress.torch() - stress_exp.torch())**2
        
        # Option 2: Using PyTorch's MSE loss (uncomment to use this instead)
        # loss = torch.nn.functional.mse_loss(stress.torch(), stress_exp.torch(), reduction='sum')
        
        # Record (append) states
        loss_history.append(loss.item())
        eta_history.append(sy.item())  # Using sy as the tracked parameter
        n_history.append(sy.item())    # Dummy value for compatibility
        
        if i % 10 == 0:  # Print every 10 iterations
            print(f"Iteration {i}: Loss = {loss.item():.6f}, sy = {sy.item():.6f}")
            print(f"  Requires grad - sy: {sy.requires_grad}")

        # Compute gradients
        loss.backward()
        
        if i % 10 == 0:  # Print gradient info
            if sy.grad is not None:
                print(f"  Gradient - sy: {sy.grad.item():.6f}")
            else:
                print(f"  Gradient is None")
        
        # Manual parameter update using gradients on sy
        with torch.no_grad():
            if sy.grad is not None:
                sy -= gamma * sy.grad
                
                # Apply constraints (yield stress should be positive)
                sy.data = torch.clamp(sy.data, min=1e-6)
                
                # Clear gradients for next iteration
                sy.grad.zero_()
            else:
                if i == 0:  # Only warn on first iteration
                    print("Warning: No gradients computed")
    
    except Exception as e:
        print(f"Error at iteration {i}: {e}")
        break

# Plot results
if len(loss_history) > 0:
    fig, ax = plt.subplots()
    iterations = torch.arange(len(loss_history))
    ax.plot(iterations, loss_history, 'k-', label='loss')
    ax.set_xlabel('Iteration')
    ax.set_ylabel('Loss')
    ax.legend()
    plt.show()
    print(f"Final loss: {loss_history[-1]:.6f}")
    print(f"Final sy: {sy.item():.6f}")
else:
    print("No optimization data to plot - optimization may have failed immediately")