[Drivers]
    [unit]
        type = ModelUnitTest
        model = 'model'
        input_Scalar_names = 'state/internal/M'
        input_Scalar_values = 150
        output_Scalar_names = 'state/internal/tau'
        output_Scalar_values = 75
    []
[]

[Models]
    [model]
        type = NormalToShearStress
        normal_stress = 'state/internal/M'
        shear_stress = 'state/internal/tau'
        schmid_factor = 0.5
    []
[]