#neml2
#
# UNIT SYSTEM: um, MPa, s, eV, K
#
# NOTE: this differs from the TeX reference document, which tabulates parameters
# in mm. Every length-dimensioned input below is therefore 1000^n times its
# tabulated value (n = the power of length): b, a, d_lath, k1, and the initial
# rho_m supplied by the driver / notebook.
#
# Quantities that are NOT length-dimensioned keep their tabulated values:
# stresses (G, tau_p, Young's modulus) in MPa; B_k in MPa*s (the h*b/w group in
# K = 2hb/(w B_k) carries the single power of length, so v comes out in um/s on
# its own); energies (H_0, Q_d) in eV; and all dimensionless coefficients.
#
# The model is unit-agnostic: sigma_a = alpha*G*b/L has b/L dimensionless, and
# gamma_dot = rho_m*b*v is [L^-2][L][L/s] = 1/s. Flow stresses in MPa are
# therefore invariant under this change -- if they move, something is wrong.
[Tensors]
  [a]
    type = Python
    expr = 'Scalar(3.16e-4)'
  []
  [b]
    # um  (Burgers vector, a*sqrt(3)/2)
    type = Python
    expr = 'Scalar(2.73664028e-4)'
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
    a = -2.716e-2
    b = 0.01253e3
    c = 396.507e3
    argument = 'temperature'
  []
  [nu]
    type = ScalarQuadraticInterpolation
    a = 3.157e-9
    b = -8.030e-6
    c = 0.285
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
  # The Newton unknown is u = ln(rho_m), not rho_m itself. Positivity is then
  # structural (exp is never non-positive, so no floor can be violated by an
  # iterate), and u spans ~1.5-4.4 instead of 4.51-81, which puts the density
  # block on the same scale as the other unknowns in the shared residual norm.
  # Everything downstream keeps consuming rho_m, which is now derived.
  [rho_m_from_log]
    type = ScalarExponential
    from = 'log_rho_m'
    to = 'rho_m'
    # Tighter than the 700 default, which only protects exp itself. Downstream
    # log_rho_m_rate divides BY rho_m, so exp(-700) ~ 1e-304 would make that
    # reciprocal overflow to inf and poison the solve with NaN. u is physically
    # ~1.5-4.4 here, so +/-50 (rho_m in [2e-22, 5e21]) is hugely generous while
    # keeping 1/rho_m comfortably finite.
    exponent_max = 50
  []
  [L]
    type = MeanFreePath
    use_L2 = true
    use_L3 = false
    c_lath = 1.0
    d_lath = 0.5
    # um (grain size; occupies the lath slot for tungsten)
    c_block = 0.0
    d_block = 1.0
    c_packet = 0.0
    d_packet = 1.0
    c_PAG = 0.0
    d_PAG = 1.0
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
    from = 'mandel_stress'
    to = 'flow_direction'
  []
  [v_disl]
    type = ThermallyActivatedKinkPairMobilityLaw
    sigma_eff = 'effective_stress'
    sigma_0 = 'athermal_solute_resistance'
    T = 'temperature'
    a = 'a'
    # um (lattice constant)
    k_B = 'k_B_eV'
    m = 'm'
    B_k = 8.3e-11
    tau_p = 950
    T_0 = 3325.5
    p = 0.6
    q = 1.4
    H_0 = 2.55
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
    k1 = 3.0e4
    # um^-1 (storage coefficient)
    thermally_activated_recovery = true
    k2_0 = 6000
    Q_d = 0.01
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
    models = 'G_bottom_inner G_bottom mandel_stress kinharden overstress 
              vonmises rho_m_from_log L isoharden normality v_disl gamma_rate 
              p_rate rho_m_rate log_rho_m_rate Eprate Erate Eerate
              elasticity integrate_log_rho_m integrate_stress
              integrate_X mixed mixed_old'
  []
[]

[EquationSystems]
  [eq_sys]
    type = NonlinearSystem
    model = 'implicit_rate'
    unknowns = 'mixed_state log_rho_m back_stress'
    residuals = 'stress_residual log_rho_m_residual back_stress_residual'
  []
[]


