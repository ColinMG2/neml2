# neml2
[Drivers]
  [unit]
    type = ModelUnitTest
    model = 'model'
    input_Scalar_names = 'L T rho_m flow_rate tau_ss'
    input_Scalar_values = '1.0e-6 573.15 1.0e12 1e-8 130e6'
    output_Scalar_names = 'tau_ss_rate'
    output_Scalar_values = '-75.478608185542'
  []
[]

[Models]
  [model]
    type = SoluteDislocationInteractionRate
    t_a0 = 1e-9
    Q_a = 2.5634826144e-19
    k_B = 1.380649e-23
    b = 2.73664028e-10
    m = 0.33
    tau_s0 = 130e6
    p_ss = 0.37
  []
[]


