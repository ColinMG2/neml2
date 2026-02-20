[Drivers]
    [unit]
        type = ModelUnitTest
        model = 'model'
        input_Scalar_names = 'state/G'
        input_Scalar_values = 26000
        output_Scalar_names = 'state/internal/s_a'
        output_Scalar_values = '39000'
    []
[]

[Models]
    [model]
        type = AthermalStress
        shear_modulus = 'state/G'
        alpha = 2
        b = 3
        L = 4
        athermal_stress = 'state/internal/s_a'
    []
[]
