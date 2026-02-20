# Example showing how to set up Orowan equation and Kocks-Mecking dislocation density
# with backward Euler time integration for implicit solve

[Tensors]
  # Material parameters (these would be fit to your specific material)
  [b]
    type = Scalar
    values = '2.5e-10'  # Burgers vector in meters
  []
  
  [k1]
    type = Scalar
    values = '1.0'      # Hardening coefficient
  []
  
  [k2]
    type = Scalar
    values = '10.0'     # Recovery coefficient
  []
  
  [L]
    type = Scalar
    values = '1.0e-6'   # Mean free path
  []
  
  [h]
    type = Scalar
    values = '1.0e-10'  # Dislocation mobility parameter
  []
  
  [a]
    type = Scalar
    values = '5.0e-10'  # Activation distance
  []
  
  [Bk]
    type = Scalar
    values = '1.0e-4'   # Drag coefficient
  []
  
  [tau_p]
    type = Scalar
    values = '1.0e9'    # Pierls stress (Pa)
  []
  
  [T_0]
    type = Scalar
    values = '300'      # Reference temperature (K)
  []
  
  [p]
    type = Scalar
    values = '0.5'      # Exponent p
  []
  
  [q]
    type = Scalar
    values = '1.5'      # Exponent q
  []
  
  [T_ref]
    type = Scalar
    values = '300'      # Reference temperature (K)
  []
  
  [k_B]
    type = Scalar
    values = '1.380649e-23'  # Boltzmann constant (J/K)
  []
  
  [D_H]
    type = Scalar
    values = '2.0e-19'  # Activation energy (J)
  []
[]

[Models]
  [dislocation_mobility]
    type = ThermallyActivatedDislocationMobility
    effective_shear = 'state/tau_eff'
    athermal_shear = 'state/tau_a'
    v_disl = 'state/v_disl'
    h = 'h'
    L = 'L'
    b = 'b'
    a = 'a'
    Bk = 'Bk'
    pierls_stress = 'tau_p'
    T_0 = 'T_0'
    p = 'p'
    q = 'q'
    reference_temperature = 'T_ref'
    k_B = 'k_B'
    activation_energy = 'D_H'
  []

  [orowan]
    type = OrowanEquation
    dislocation_density = 'state/rho_m'      # Current dislocation density (state variable)
    v_disl = 'state/v_disl'                  # Dislocation velocity
    b = 'b'                                  # Burgers vector (parameter)
    gamma_rate = 'state/gamma_rate'          # Output: plastic flow rate
  []

  # Compute dislocation density rate from Kocks-Mecking model
  [kocks_mecking]
    type = KocksMeckingDislocationDensity
    gamma_rate = 'state/gamma_rate'          # Plastic flow rate (from Orowan)
    dislocation_density = 'state/rho_m'      # Current dislocation density (state variable)
    rho_m_rate = 'state/rho_m_rate'          # Output: dislocation density rate
    k1 = 'k1'                                # Hardening coefficient (parameter)
    k2 = 'k2'                                # Recovery coefficient (parameter)
    L = 'L'                                  # Mean free path (parameter)
  []

  # Backward Euler time integration for plastic flow
  # Computes residual: r_gamma = gamma - gamma_old - dt * gamma_rate
  [integrate_gamma]
    type = ScalarBackwardEulerTimeIntegration
    variable = 'state/gamma'                 # State variable being integrated
    # rate automatically inferred as 'state/gamma_rate'
    # time automatically set to 'forces/t'
  []

  # Backward Euler time integration for dislocation density
  # Computes residual: r_rho = rho_m - rho_m_old - dt * rho_m_rate
  [integrate_rho_m]
    type = ScalarBackwardEulerTimeIntegration
    variable = 'state/rho_m'                 # State variable being integrated
    # rate automatically inferred as 'state/rho_m_rate'
    # time automatically set to 'forces/t'
  []

  # Compose all models for the implicit solve
  [implicit_model]
    type = ComposedModel
    models = 'dislocation_mobility orowan kocks_mecking integrate_gamma integrate_rho_m'
  []

  # Solve the implicit system (find gamma and rho_m that give zero residuals)
  [return_map]
    type = ImplicitUpdate
    implicit_model = 'implicit_model'
    solver = 'newton'
  []
[]

[Solvers]
  [newton]
    type = Newton
  []
[]
