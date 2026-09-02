[Drivers]
    [unit]
        type = ModelUnitTest
        model = 'model'
        input_Scalar_names = 'rho_m v_disl'
        input_Scalar_values = '1.0e12 9.79788932e5'
        output_Scalar_names = 'gamma_dot'
        output_Scalar_values = '2.68133e8'
    []
[]

[Models]
    [model]
        type = OrowanPlasticShearRate
        b = 2.73664027846e-10
    []
[]