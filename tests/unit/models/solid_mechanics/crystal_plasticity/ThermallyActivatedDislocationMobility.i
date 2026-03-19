[Drivers]
    [unit]
        type = ModelUnitTest
        model = 'model'
        input_Scalar_names = 'state/internal/tau_eff state/internal/tau_a state/internal/rho_m'
        input_Scalar_values = '75.0 50.0 1.0e12'
        output_Scalar_names = 'state/internal/v_disl'
        output_Scalar_values = '1673.4107'
        check_AD_parameter_derivatives = false
    []
[]

[Models]
    [model]
        type = ThermallyActivatedDislocationMobility
        effective_shear = 'state/internal/tau_eff'
        athermal_shear = 'state/internal/tau_a'
        dislocation_density = 'state/internal/rho_m'
        h = 2.3352e-10
        b = 2.4768e-10
        a = 2.86e-10
        Bk = 1.0e-4
        pierls_stress = 360
        T_0 = 778.52
        p = 0.86
        q = 1.69
        T_ref = 973.15
        k_B = 8.617e-5
        activation_energy = 1.63
        v_disl = 'state/internal/v_disl'
    []
[]