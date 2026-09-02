# neml2
[Drivers]
  [unit]
    type = ModelUnitTest
    model = 'model'
    input_Scalar_names = 'L T rho_m flow_rate'
    input_Scalar_values = '1.0e-6 573.15 1.0e12 4.289e-4'
    output_Scalar_names = 'athermal_solute_resistance'
    output_Scalar_values = '4.12916749e8'
  []
[]

[Models]
  [model]
    type = AthermalSoluteIsotropicHardening
    G = 160156.25e6
    alpha = 0.5
    b = 2.73664028e-10
    include_solid_solution = true
    t_a0 = 1e-9
    Q_a = 2.5635e-19
    k_B = 1.380649e-23
    T = 'T'
    rho_m = 'rho_m'
    flow_rate = 'flow_rate'
    m = 0.33
    tau_s0 = 130e6
    p_ss = 0.37
  []
[]


