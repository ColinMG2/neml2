[Drivers]
    [unit]
        type = ModelUnitTest
        model = 'model'
        input_Scalar_names = 'state/internal/gamma_rate state/internal/rho_m'
        input_Scalar_values = '1.41568625e-4 1.0e12'
        output_Scalar_names = 'state/internal/rho_m_rate'
        output_Scalar_values = '-1415686108.4314'
        check_AD_parameter_derivatives = false
    []
[]

[Models]
    [model]
        type = KocksMeckingDislocationDensity
        plastic_flow_rate = 'state/internal/gamma_rate'
        k1 = 1
        k2 = 10
        dislocation_density = 'state/internal/rho_m'
        density_rate = 'state/internal/rho_m_rate'
    []
[]