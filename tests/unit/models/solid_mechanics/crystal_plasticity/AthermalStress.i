[Drivers]
    [unit]
        type = ModelUnitTest
        model = 'model'
        output_Scalar_names = 'state/internal/s_a'
        output_Scalar_values = '0.9913306'
        check_AD_parameter_derivatives = false
    []
[]

[Models]
    [model]
        type = AthermalStress
        shear_modulus = '40000.0'
        alpha = 0.5
        b = 2.4783265e-10
        L = 5.0e-6
        athermal_stress = 'state/internal/s_a'
    []
[]
