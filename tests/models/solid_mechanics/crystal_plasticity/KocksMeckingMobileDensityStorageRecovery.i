#neml2
[Drivers]
  [unit]
    type = ModelUnitTest
    model = 'model'
    input_Scalar_names = 'p_dot L rho_m'
    input_Scalar_values = '4.289e-4 1.0e-6 1.0e12'
    output_Scalar_names = 'rho_m_dot'
    output_Scalar_values = '1.28026650e13'
  []
[]

[Models]
  [model]
    type = KocksMeckingMobileDensityStorageRecovery
    k1 = 3.0e10
    k2 = 150
    thermally_activated_recovery = false
  []
[]


