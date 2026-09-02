[Drivers]
    [unit]
        type = ModelUnitTest
        model = 'model'
        input_Scalar_names = 'sigma_eff sigma_0 T'
        input_Scalar_values = '1.0e9 4.12916749e8 573.15'
        output_Scalar_names = 'v_disl'
        output_Scalar_values = '7.56579956e-3'
    []
[]

[Models]
    [model]
        type = ThermallyActivatedKinkPairMobilityLaw
        a = 3.16e-10
        k_B = 8.617333262e-5
        m = 0.33
        B_k = 8.3e-5
        tau_p = 950e6
        T_0 = 3325.5
        p = 0.6
        q = 1.4
        H_0 = 2.55
    []
[]