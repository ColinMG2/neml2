[Drivers]
    [unit]
        type = ModelUnitTest
        model = 'E'
        input_Scalar_names = 'T'
        input_Scalar_values = '250.0'
        output_Scalar_names = 'E'
        output_Scalar_values = '397.942'
    []
[]

[Models]
    [E]
        type = ScalarQuadraticInterpolation
        argument = 'T'
        a = -2.716e-5
        b = 0.01253
        c = 396.507
    []
[]