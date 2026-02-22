[Drivers]
    [unit]
        type = ModelUnitTest
        model = 'model'
        input_Scalar_names = 'state/internal/tau_eff state/internal/tau_a'
        input_Scalar_values = '75e6 50e6'
        output_Scalar_names = 'state/internal/v_disl'
        output_Scalar_values = '113254.9002'
        check_AD_parameter_derivatives = false
    []
[]

[Models]
    [model]
        type = ThermallyActivatedDislocationMobility
        effective_shear = 'state/internal/tau_eff'
        athermal_shear = 'state/internal/tau_a'
        h = 1.0e-10
        L = 1.0e-6
        b = 2.5e-10
        a = 5.0e-10
        Bk = 1.0e-4
        pierls_stress = 1.0e9
        T_0 = 973
        p = 0.5
        q = 1.5
        reference_temperature = 773
        k_B = 1.38e-23
        activation_energy = 2.0e-19
        v_disl = 'state/internal/v_disl'
    []
[]