[Tensors]
  [T_train]
    type = Scalar
    values = '499.0 550.0 601.0'
    batch_shape = '(3)'
    intermediate_dimension = 1
  []
  [R_values]
    type = Scalar
    values = '300.0 200.0 100.0'
    batch_shape = '(3)'
    intermediate_dimension = 1
  []
  [d_values]
    type = Scalar
    values = '30.0 20.0 15.0'
    batch_shape = '(3)'
    intermediate_dimension = 1
  []
  [sy_values]
    type = Scalar
    values = '550.0 500.0 300.0'
    batch_shape = '(3)'
    intermediate_dimension = 1
  []
  [E_values]
    type = Scalar
    values = '68000.0 72000.0 66000.0'
    batch_shape = '(3)'
    intermediate_dimension = 1
  []
  [mu_values]
    type = Scalar
    values = '300.0 200.0 100.0'
    batch_shape = '(3)'
    intermediate_dimension = 1
  []
  [n_values]
    type = Scalar
    values = '2.0 2.0 2.0'
    batch_shape = '(3)'
    intermediate_dimension = 1
  []
[]

[Models]
  [R]
    type = ScalarLinearInterpolation
    argument = 'forces/T'
    abscissa = 'T_train'
    ordinate = 'R_values'
  []
  [d]
    type = ScalarLinearInterpolation
    argument = 'forces/T'
    abscissa = 'T_train'
    ordinate = 'd_values'
  []
  [sy]
    type = ScalarLinearInterpolation
    argument = 'forces/T'
    abscissa = 'T_train'
    ordinate = 'sy_values'
  []
  [E]
    type = ScalarLinearInterpolation
    argument = 'forces/T'
    abscissa = 'T_train'
    ordinate = 'E_values'
  []
  [mu]
    type = ScalarLinearInterpolation
    argument = 'forces/T'
    abscissa = 'T_train'
    ordinate = 'mu_values'
  []
  [n]
    type = ScalarLinearInterpolation
    argument = 'forces/T'
    abscissa = 'T_train'
    ordinate = 'n_values'
  []
  [mandel_stress]
    type = IsotropicMandelStress
  []
  [vonmises]
    type = SR2Invariant
    invariant_type = 'VONMISES'
    tensor = 'state/internal/M'
    invariant = 'state/internal/s'
  []
  [isoharden]
    type = VoceIsotropicHardening
    saturated_hardening = 'R'
    saturation_rate = 'd' 
  []
  [yield]
    type = YieldFunction
    yield_stress = 'sy'
    isotropic_hardening = 'state/internal/k'
  []
  [flow]
    type = ComposedModel
    models = 'vonmises yield'
  []
  [normality]
    type = Normality
    model = 'flow'
    function = 'state/internal/fp'
    from = 'state/internal/M state/internal/k'
    to = 'state/internal/NM state/internal/Nk'
  []
  [flow_rate]
    type = PerzynaPlasticFlowRate
    reference_stress = 'mu'
    exponent = 'n'
  []
  [Eprate]
    type = AssociativePlasticFlow
  []
  [eprate]
    type = AssociativeIsotropicPlasticHardening
  []
  [Srate]
    type = SR2VariableRate
    variable = 'forces/S'
    rate = 'forces/S_rate'
  []
  [Erate]
    type = SR2VariableRate
    variable = 'state/E'
    rate = 'state/E_rate'
  []
  [elasticity]
    type = LinearIsotropicElasticity
    coefficients = 'E 0.32'
    coefficient_types = 'YOUNGS_MODULUS POISSONS_RATIO'
    rate_form = true
    stress = 'forces/S_rate'
    strain = 'state/internal/Ee_rate'
  []
  [Eerate]
    type = SR2LinearCombination
    from_var = 'state/E_rate state/internal/Ep_rate'
    to_var = 'state/internal/Ee_rate'
    coefficients = '1 -1'
  []
  [integrate_stress]
    type = SR2BackwardEulerTimeIntegration
    variable = 'forces/S'
  []
  [integrate_ep]
    type = ScalarBackwardEulerTimeIntegration
    variable = 'state/internal/ep'
  []
  [integrate_strain]
    type = SR2BackwardEulerTimeIntegration
    variable = 'state/E'
  []
  [mixed]
    type = MixedControlSetup
    above_variable = 'forces/S'
    below_variable = 'state/E'
  []
  [mixed_old]
    type = MixedControlSetup
    control = 'old_forces/control'
    mixed_state = 'old_state/mixed_state'
    fixed_values = 'old_forces/fixed_values'
    above_variable = 'old_forces/S'
    below_variable = 'old_state/E'
  []
  [rename]
    type = CopySR2
    from = 'residual/E'
    to = 'residual/mixed_state'
  []
  [implicit_rate]
    type = ComposedModel
    models = 'mandel_stress vonmises isoharden yield normality flow_rate Eprate eprate Srate Eerate elasticity integrate_stress integrate_ep integrate_strain mixed mixed_old rename'
  []
[]
