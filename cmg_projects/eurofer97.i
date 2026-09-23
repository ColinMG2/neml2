# neml2
[Tensors]
  [a]
    type = Python
    expr = 'Scalar(2.87e-4)'
  []
  [b]
    # um  (Burgers vector, a*sqrt(3)/2)
    type = Python
    expr = 'Scalar(2.48549291e-4)'
  []
  [m]
    ## Schmid factor (unitless)
    type = Python
    expr = 'Scalar(0.33)'
  []
  [k_B_eV]
    ## eV/K
    type = Python
    expr = 'Scalar(8.617e-5)'
  []
[]

[Models]
  [E]
    type = ScalarQuadraticInterpolation
    a = -7.626e-2
    b = 0.01879e3
    c = 207.968e3
    argument = 'temperature'
  []
  [nu]
    type = ScalarQuadraticInterpolation
    a = 1.609e-9
    b = -4.449e-5
    c = 0.302
    argument = 'temperature'
  []
  [G_bottom_inner]
    type = ScalarLinearCombination
    from = 'nu'
    to = 'G_bottom_inner'
    offset = '1'
  []
  [G_bottom]
    type = ScalarMultiplication
    from = 'G_bottom_inner'
    to = 'G_bottom'
    scaling = 2
  []
  [G]
    type = ScalarMultiplication
    from = 'E G_bottom'
    to = 'G'
    reciprocal = 'false true'
  []
  [mandel_stress]
    type = IsotropicMandelStress
    cauchy_stress = 'stress'
  []
  [kinharden]
    type = FredrickArmstrongPlasticHardening
    C = 0.0
    g = 0.0
  []
  [overstress]
    type = SR2LinearCombination
    from = 'mandel_stress back_stress'
    to = 'overstress'
    weights = '1 -1'
  []
  [vonmises]
    type = SR2Invariant
    invariant_type = 'VONMISES'
    tensor = 'overstress'
    invariant = 'effective_stress'
  []
  [rho_m_from_log]
    type = ScalarExponential
    from = 'log_rho_m'
    to = 'rho_m'
    exponent_max = 50
  []
  [L]
    type = MeanFreePath
    use_L2 = true
    use_L3 = true
    c_lath = 1.0
    d_lath = 0.5
    c_block = 0.3
    d_block = 3.1
    c_packet = 0.0
    d_packet = 1.0
    c_PAG = 0.1
    d_PAG = 7.0
    c_MX = 0.3
    d_MX = 1.5
    c_M23C6 = 0.2
    d_M23C6 = 4.56e-1
    rho_min = 1e-3
  []
  [isoharden]
    type = AthermalSoluteIsotropicHardening
    G = 'G'
    alpha = 0.23
    b = 'b'
    m = 'm'
    include_solid_solution = false
  []
  [solute_rate]
    type = SoluteDislocationInteractionRate
    t_a0 = 7e-9
    Q_a = 1.6
    p_ss = 0.35
    tau_s0 = 105
    b = 'b'
    m = 'm'
    k_B = 'k_B_eV'
    T = 'temperature'
    flow_rate = 'flow_rate'
    flow_rate_min = 1e-12
  []
  [integrate_tau_ss]
    type = ScalarBackwardEulerTimeIntegration
    variable = 'tau_ss'
  []
  [isotropic_resistance]
    type = ScalarLinearCombination
    from = 'athermal_solute_resistance tau_ss'
    to = 'sigma_0'
    weights = '1 3.03030303'
  []
  [yield_surface]
    type = YieldFunction
    yield_stress = 0.0
    isotropic_hardening = 'sigma_0'
  []
  [flow]
    type = ComposedModel
    models = 'overstress vonmises yield_surface'
  []
  [normality]
    type = Normality
    model = 'flow'
    function = 'yield_function'
    from = 'mandel_stress'
    to = 'flow_direction'
  []
  [v_disl]
    type = ThermallyActivatedKinkPairMobilityLaw
    sigma_eff = 'effective_stress'
    sigma_0 = 'sigma_0'
    T = 'temperature'
    a = 'a'
    k_B = 'k_B_eV'
    m = 'm'
    B_k = 6.6e-11
    tau_p = 380
    T_0 = 1530.42175
    p = 0.6
    q = 1.95
    H_0 = 2.17
    # Above ~530 K the imposed rate is carried by tau* << 1 MPa, i.e. the solution sits
    # on the corner of <tau_eff - tau_0>; smooth it so Newton stops cycling across it.
    smoothing_width = 0.1
  []
  [gamma_rate]
    type = OrowanPlasticShearRate
    b = 'b'
  []
  [p_rate]
    type = ScalarMultiplication
    from = 'gamma_dot'
    to = 'flow_rate'
    scaling = 'm'
  []
  [rho_m_rate]
    type = KocksMeckingMobileDensityStorageRecovery
    k1 = 7.8e4
    thermally_activated_recovery = true
    k2_0 = 6750
    Q_d = 0.007
    k_B = 'k_B_eV'
    T = 'temperature'
  []
  # u_dot = rho_m_dot / rho_m. As rho_m -> 0 the Kocks-Mecking storage term
  # k1/(L*rho_m) -> +infinity (L stays finite at 1/Lambda_micro), so u_dot
  # -> +infinity and the collapsed-density state actively repels. In linear
  # space rho_m_dot -> k1*p_dot/L, merely finite, which is what let Newton
  # settle on the spurious fully-elastic root.
  [log_rho_m_rate]
    type = ScalarMultiplication
    from = 'rho_m_rate rho_m'
    to = 'log_rho_m_rate'
    reciprocal = 'false true'
  []
  [Eprate]
    type = AssociativePlasticFlow
  []
  [Erate]
    type = SR2VariableRate
    variable = 'strain'
  []
  [Eerate]
    type = SR2LinearCombination
    from = 'strain_rate plastic_strain_rate'
    to = 'elastic_strain_rate'
    weights = '1 -1'
  []
  [elasticity]
    type = LinearIsotropicElasticity
    coefficients = 'E nu'
    coefficient_types = 'YOUNGS_MODULUS POISSONS_RATIO'
    strain = 'elastic_strain'
    rate_form = true
  []
  [integrate_log_rho_m]
    type = ScalarBackwardEulerTimeIntegration
    variable = 'log_rho_m'
  []
  [integrate_stress]
    type = SR2BackwardEulerTimeIntegration
    variable = 'stress'
  []
  [integrate_X]
    type = SR2BackwardEulerTimeIntegration
    variable = 'back_stress'
  []
  [mixed]
    type = MixedControlSetup
    x_above = 'fixed_values'
    x_below = 'mixed_state'
    y = 'stress'
    z = 'strain'
  []
  [mixed_old]
    type = MixedControlSetup
    control = 'control~1'
    x_above = 'fixed_values~1'
    x_below = 'mixed_state~1'
    y = 'stress~1'
    z = 'strain~1'
  []
  [implicit_rate]
    type = ComposedModel
    models = 'G_bottom_inner G_bottom mandel_stress kinharden overstress vonmises rho_m_from_log 
              L isoharden solute_rate integrate_tau_ss isotropic_resistance normality v_disl
              gamma_rate p_rate rho_m_rate log_rho_m_rate Eprate Erate Eerate
              elasticity integrate_log_rho_m integrate_stress
              integrate_X mixed mixed_old'
  []
[]

[EquationSystems]
  [eq_sys]
    type = NonlinearSystem
    model = 'implicit_rate'
    unknowns = 'mixed_state log_rho_m back_stress tau_ss'
    residuals = 'stress_residual log_rho_m_residual back_stress_residual tau_ss_residual'
  []
[]

