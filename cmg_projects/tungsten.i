#neml2
[Tensors]
  [C]
    # MPa
    type = Python
    expr = 'Scalar(0.0)'
  []
  [g]
    type = Python
    expr = 'Scalar(0.0)'
  []
  [b]
    #mm
    type = Python
    expr = 'Scalar(2.73664028e-7)'
  []
[]

[Models]
  [mandel_stress]
    type = IsotropicMandelStress
    cauchy_stress = 'stress'
  []
  [kinharden]
    type = FredrickArmstrongPlasticHardening
    C = 'C'
    g = 'g'
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
    tensor = 'mandel_stress'
    invariant = 'effective_stress'
  []
  [L]
    type = MeanFreePath
    use_L2 = true
    use_L3 = false
    c_lath = 1.0
    d_lath = 0.5e-3
    c_block = 0.0
    d_block = 1.0
    c_packet = 0.0
    d_packet = 1.0
    c_PAG = 0.0
    d_PAG = 1.0
  []
  [isoharden]
    type = AthermalSoluteIsotropicHardening
    G = 160156.25
    alpha = 0.23
    b = 'b'
    include_solid_solution = false
  []
  [yield_surface]
    type = YieldFunction
    yield_stress = 0.0
    isotropic_hardening = 'athermal_solute_resistance'
  []
  [flow]
    type = ComposedModel
    models = 'overstress vonmises yield_surface'
  []
  [normality]
    type = Normality
    model = 'flow'
    function = 'yield_function'
    from = 'mandel_stress athermal_solute_resistance'
    to = 'flow_direction athermal_solute_resistance_direction'
  []
  [v_disl]
    type = ThermallyActivatedKinkPairMobilityLaw
    sigma_eff = 'effective_stress'
    sigma_0 = 'athermal_solute_resistance'
    T = 'temperature'
    a = 3.16e-7
    k_B = 8.617e-5
    m = 0.33
    B_k = 8.3e-11
    tau_p = 950
    T_0 = 3325.5
    p = 0.6
    q = 1.4
    H_0 = 2.55
  []
  [gamma_rate]
    type = OrowanPlasticShearRate
    b = 'b'
  []
  [p_rate]
    type = ScalarMultiplication
    from = 'gamma_dot'
    to = 'flow_rate'
    scaling = 0.33
  []
  [rho_m_rate]
    type = KocksMeckingMobileDensityStorageRecovery
    k1 = 3.0e7
    thermally_activated_recovery = true
    k2_0 = 6000.0
    Q_d = 0.01
    k_B = 8.617e-5
    T = 'temperature'
    rho_m_dot = 'rho_m_dot'
  []
  [Eprate]
    type = AssociativePlasticFlow
  []
  [eprate]
    type = AssociativeIsotropicPlasticHardening
    isotropic_hardening_direction = 'athermal_solute_resistance_direction'
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
    coefficients = '410000 0.28'
    coefficient_types = 'YOUNGS_MODULUS POISSONS_RATIO'
    strain = 'elastic_strain'
    rate_form = true
  []
  [integrate_rho_m]
    type = ScalarBackwardEulerTimeIntegration
    variable = 'rho_m'
  []
  [integrate_stress]
    type = SR2BackwardEulerTimeIntegration
    variable = 'stress'
  []
  [integrate_X]
    type = SR2BackwardEulerTimeIntegration
    variable = 'back_stress'
  []
  [integrate_ep]
    type = ScalarBackwardEulerTimeIntegration
    variable = 'equivalent_plastic_strain'
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
    models = 'mandel_stress kinharden overstress vonmises L 
              isoharden yield_surface normality v_disl
              gamma_rate p_rate rho_m_rate Eprate eprate Erate Eerate
              elasticity integrate_rho_m integrate_stress 
              integrate_X mixed mixed_old'
  []
[]

[EquationSystems]
  [eq_sys]
    type = NonlinearSystem
    model = 'implicit_rate'
    unknowns = 'mixed_state rho_m back_stress equivalent_plastic_strain'
    residuals = 'stress_residual rho_m_residual back_stress_residual equivalent_plastic_strain_residual'
  []
[]


