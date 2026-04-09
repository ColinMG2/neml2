[Drivers]
    [unit]
        type = ModelUnitTest
        model = 'E'
        input_Scalar_names = 'forces/T'
        input_Scalar_values = '250'
        output_Scalar_names = 'parameters/E'
        output_Scalar_values = '397.942'
        check_second_derivatives = true
        check_AD_parameter_derivatives = false
    []
[]

[Models]
    [E]
        type = ScalarQuadraticInterpolation
        a = '-2.716e-5'
        b = '0.01253'
        c = '396.507'
        argument = 'forces/T'
    []
[]