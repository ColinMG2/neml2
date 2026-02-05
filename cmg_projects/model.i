[Models]
    [model]
        type = ThermallyActivatedDislocationMobility
        effective_shear = 'state/tau_eff'
        athermal_shear = 'state/tau_a'
        h = 1
        L = 2
        b = 3
        a = 2
        Bk = 5
        pierls_stress = 100
        T_0 = 300
        p = 3
        q = 6
        reference_temperature = 500
        k_B = 1.38e-23
        activation_energy = 100
        v_disl = 'state/internal/v_disl'
    []
[]