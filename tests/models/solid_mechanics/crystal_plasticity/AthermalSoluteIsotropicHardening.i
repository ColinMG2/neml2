# neml2
[Drivers]
  [unit]
    type = ModelUnitTest
    model = 'model'
    input_Scalar_names = 'L'
    input_Scalar_values = '1.0'
    output_Scalar_names = 'athermal_solute_resistance'
    output_Scalar_values = '6.64075826e-5'
  []
[]

[Models]
  [model]
    type = AthermalSoluteIsotropicHardening
    G = 160156.25
    alpha = 0.5
    b = 2.73664028e-10
    m = 0.33
    include_solid_solution = false
  []
[]

