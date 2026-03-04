[Drivers]
    [unit]
        type = ModelUnitTest
        model = 'model'
        input_Scalar_names = 'G'
        input_Scalar_values = 'G'
        output_Scalar_names = 'state/internal/s_a'
        output_Scalar_values = '4.956653 3.71748975 3.22182445 1.4869959'
    []
[]

[Tensors]
    [G]
        type = Scalar
        values = '40000.0 30000.0 26000.0 12000.0'
        batch_shape = '(4)'
        intermediate_dimension = 1
    []
[]

[Models]
    [model]
        type = AthermalStress
        shear_modulus = 'G'
        alpha = 0.5
        b = 2.4783265e-10
        L = 1.0e-6
        athermal_stress = 'state/internal/s_a'
    []
[]
