[Drivers]
    [unit]
        type = ModelUnitTest
        model = 'model'
        input_Scalar_names = 'state/internal/rho_m'
        input_Scalar_values = '1.0e12'
        output_Scalar_names = 'state/internal/s_a'
        output_Scalar_values = '4.96'
        check_AD_parameter_derivatives = false
    []
[]

[Models]
    [model]
        type = AthermalStress
        shear_modulus = '40000.0'
        alpha = 0.5
        b = 2.48e-10
        dislocation_density = 'state/internal/rho_m'
        athermal_stress = 'state/internal/s_a'
    []
[]
