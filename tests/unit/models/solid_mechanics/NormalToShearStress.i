[Drivers]
    [unit]
        type = ModelUnitTest
        model = 'model'
        input_Scalar_names = 'state/s'
        input_Scalar_values = 150
        output_Scalar_names = 'state/tau'
        output_Scalar_values = 75
    []
[]

[Models]
    [model]
        type = NormalToShearStress
        normal_stress = 'state/S'
        shear_stress = 'state/tau'
        schmid_factor = 0.5
    []
[]