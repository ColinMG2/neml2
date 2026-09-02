#neml2
[Drivers]
  [unit]
    type = ModelUnitTest
    model = 'model'
    input_Scalar_names = 'p_dot L rho_m T'
    input_Scalar_values = '4.289e-4 1.0e-6 1.0e12 573.15'
    output_Scalar_names = 'rho_m_dot'
    output_Scalar_values = '1.07652741e13'
  []
[]

[Models]
  [model]
    type = KocksMeckingMobileDensityStorageRecovery
    k1 = 3.0e10
    thermally_activated_recovery = true
    k2_0 = 6000
    Q_d = 0.01
    k_B = 8.617e-5
    T = 'T'
  []
[]


