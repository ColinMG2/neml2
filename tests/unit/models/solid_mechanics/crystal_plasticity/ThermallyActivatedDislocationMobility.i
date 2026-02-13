[Drivers]
    [unit]
        type = ModelUnitTest
        input_Scalar_names = 'state/internal/tau_eff state/internal/tau_a'
        input_Scalar_values = '75 50'
        output_Scalar_names = 'state/internal/v_disl'
        output_Scalar_values = '0'
    []
[]

[Models]
    [model]
        type = ThermallyActivatedDislocationMobility
        effective_shear = 'state/internal/tau_eff'
        athermal_shear = 'state/internal/tau_a'
        h = 1
        L = 2
        b = 3
        a = 2
        Bk = 5
        pierls_stress = 100
        T_0 = 700
        p = 3
        q = 6
        reference_temperature = 500
        k_B = 1.38e-23
        activation_energy = 100
        v_disl = 'state/internal/v_disl'
    []
[]