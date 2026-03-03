[Tensors]
    [T_train]
        type = Scalar
        values = '19.9 516.0 621.0 701.0'
        batch_shape = '(4)'
        intermediate_dimension = 1
    []
    [C_values]
        type = Scalar
        values = '50.0 100.0 200.0 300.0'
        batch_shape = '(4)'
        intermediate_dimension = 1
    []
    [g_values]
        type = Scalar
        values = '2.5 5.0 10.0 15.0'
        batch_shape = '(4)'
        intermediate_dimension = 1
    []
    [sy_values]
        type = Scalar
        values = '600.0 550.0 500.0 300.0'
        batch_shape = '(4)'
        intermediate_dimension = 1
    []
    [E_values]
        type = Scalar
        values = ' 100000.0 68000.0 72000.0 66000.0'
        batch_shape = '(4)'
        intermediate_dimension = 1
    []
    [G_values]
        type = Scalar
        values = '200000.0 26153.84615 27692.30769 25384.61538'
        batch_shape = '(4)'
        intermediate_dimension = 1
    []
    [sy_values]
        type = Scalar
        values = '600.0 550.0 500.0 300.0'
        batch_shape = '(4)'
        intermediate_dimension = 1
    []
    [T_0]
        type = Scalar
        values = '180.0 200.0 320.0 440.0'
        batch_shape = '(4)'
        intermediate_dimension = 1
    []
    [L]
        type = Scalar
        values = '1.0e-6'
        batch_shape = '(1)'
    []
    [a]
        type = Scalar
        values = '2.86e-10'
        batch_shape = '(1)'
    []
    [b]
        type = Scalar
        values = '2.4783265e-10'
        batch_shape = '(1)'
    []
    [h]
        type = Scalar
        values = '2.33518022e-10'
        batch_shape = '(1)'
    []
    [H_0]
        type = Scalar
        values = '1.63'
        batch_shape = '(1)'
    []
    [kB]
        type = Scalar
        values = '8.617e-5'
        batch_shape = '(1)'
    []
    [p]
        type = Scalar
        values = '0.86'
        batch_shape = '(1)'
    []
    [q]
        type = Scalar
        values = '1.69'
        batch_shape = '(1)'
    []
    [m]
        type = Scalar
        values = '0.3'
        batch_shape = '(1)'
    []
[]

[Models]
    [C]
        type = ScalarLinearInterpolation
        argument = 'forces/T'
        abscissa = 'T_train'
        ordinate = 'C_values'
    []
    [g]
        type = ScalarLinearInterpolation
        argument = 'forces/T'
        abscissa = 'T_train'
        ordinate = 'g_values'
    []
    [E]
        type = ScalarLinearInterpolation
        argument = 'forces/T'
        abscissa = 'T_train'
        ordinate = 'E_values'
    []
    [G]
        type = ScalarLinearInterpolation
        argument = 'forces/T'
        abscissa = 'T_train'
        ordinate = 'G_values'
    []
    [sy]
        type = ScalarLinearInterpolation
        argument = 'forces/T'
        abscissa = 'T_train'
        ordinate = 'sy_values'
    []
    [mandel_stress]
        type = IsotropicMandelStress
    []
    [kinharden]
        type = FredrickArmstrongPlasticHardening
        C = 'C'
        g = 'g'
    []
    [overstress]
        type = SR2LinearCombination
        from_var = 'state/internal/M state/internal/X'
        to_var = 'state/internal/O'
        coefficients = '1 -1'
    []
    [vonmises]
        type = SR2Invariant
        invariant_type = 'VONMISES'
        tensor = 'state/internal/O'
        invariant = 'state/internal/s'
    []
    [athermal]
        type = AthermalStress
        shear_modulus = 'G'
        alpha = 0.5
        b = 'b'
        L = 'L'
        athermal_stress = 'state/internal/s_a'
    []
    [yield]
        type = YieldFunction
        yield_stress = 'sy'
    []
    [full_yield]
        type = ScalarLinearCombination
        from_var = 'state/internal/fp state/internal/s_a'
        to_var = 'state/internal/fp_n'
        coefficients = '1 -1'
    []
    [flow]
        type = ComposedModel
        models = 'overstress vonmises full_yield'
    []
    [normality]
        type = Normality
        model = 'flow'
        function = 'state/internal/fp_n'
        from = 'state/internal/M state/internal/X'
        to = 'state/internal/NM state/internal/NX'
    []
    [shear_eff]
        type = NormalToShearStress
        normal_stress = 'state/internal/s'
        shear_stress = 'state/internal/tau_eff'
        schmid_factor = 'm'
    []
    [shear_athermal]
        type = NormalToShearStress
        normal_stress = 'state/internal/s_a'
        shear_stress = 'state/internal/tau_a'
        schmid_factor = 'm'
    []
    [v_disl]
        type = ThermallyActivatedDislocationMobility
        effective_shear = 'state/internal/tau_eff'
        athermal_shear = 'state/internal/tau_a'
        h = 'h'
        L = 'L'
        b = 'b'
        a = 'a'
        Bk = 1.0e-4
        pierls_stress = 2.03e3
        T_0 = 'T_0'
        p = 'p'
        q = 'q'
        reference_temperature = 'T_train'
        k_B = 'kB'
        activation_energy = 'H_0'
        v_disl = 'state/internal/v_disl'
    []
    [rho_m_rate]
        type = KocksMeckingDislocationDensity
        plastic_flow_rate = 'state/internal/gamma_rate'
        k1 = 1.0
        k2 = 10.0
        dislocation_density = 'state/internal/rho_m'
        L = 'L'
        density_rate = 'state/internal/rho_m_rate'
    []
    [flow_rate]
        type = OrowanEquation
        dislocation_density = 'state/internal/rho_m'
        v_disl = 'state/internal/v_disl'
        b = 'b'
        plastic_flow_rate = 'state/internal/gamma_rate'
    []
    [Eprate]
        type = AssociativePlasticFlow
    []
    [Kprate]
        type = AssociativeKinematicPlasticHardening
    []
    [Erate]
        type = SR2VariableRate
        variable = 'forces/E'
        rate = 'forces/E_rate'
    []
    [Eerate]
        type = SR2LinearCombination
        from_var = 'forces/E_rate state/internal/Ep_rate'
        to_var = 'state/internal/Ee_rate'
        coefficients = '1 -1'
    []
    [elasticity]
        type = LinearIsotropicElasticity
        coefficients = 'E 0.3'
        coefficient_types = 'YOUNGS_MODULUS POISSONS_RATIO'
        rate_form = true
    []
    [integrate_gamma]
        type = ScalarBackwardEulerTimeIntegration
        variable = 'state/internal/gamma'
    []
    [integrate_rho_m]
        type = ScalarBackwardEulerTimeIntegration
        variable = 'state/internal/rho_m'
    []
    [integrate_Kprate]
        type = SR2BackwardEulerTimeIntegration
        variable = 'state/internal/Kp'
    []
    [integrate_stress]
        type = SR2BackwardEulerTimeIntegration
        variable = 'state/S'
    []
    [integrate_X]
        type = SR2BackwardEulerTimeIntegration
        variable = 'state/internal/X'
    []
    [mixed]
        type = MixedControlSetup
        above_variable = 'state/S'
        below_variable = 'forces/E'
    []
    [mixed_old]
        type = MixedControlSetup
        control = 'old_forces/control'
        mixed_state = 'old_state/mixed_state'
        fixed_values = 'old_forces/fixed_values'
        above_variable = 'old_state/S'
        below_variable = 'old_forces/E'
    []
    [rename]
        type = CopySR2
        from = 'residual/S'
        to = 'residual/mixed_state'
    []
    [implicit_rate]
        type = ComposedModel
        models = 'mandel_stress kinharden overstress vonmises athermal yield normality shear_eff shear_athermal v_disl rho_m_rate flow_rate Eprate Kprate Erate Eerate elasticity integrate_gamma integrate_rho_m integrate_Kprate integrate_stress integrate_X mixed mixed_old rename'
    []
[]