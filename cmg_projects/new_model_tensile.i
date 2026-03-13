[Tensors]
    [T_train]
        type = Scalar
        values = '292.15 789.15 894.15 974.15'
        batch_shape = '(4)'
        intermediate_dimension = 1
    []
    [C_values]
        type = Scalar
        values = '12000.0 8000.0 5000.0 2500.0'
        batch_shape = '(4)'
        intermediate_dimension = 1
    []
    [g_values]
        type = Scalar
        values = '4.0 5.0 6.5 8.0'
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
        values = '38461.53846 26153.84615 27692.30769 25384.61538'
        batch_shape = '(4)'
        intermediate_dimension = 1
    []
    [k1_values]
        type = Scalar
        values = '6.0 5.0 4.0 3.0'
        batch_shape = '(4)'
        intermediate_dimension = 1
    []
    [k2_values]
        type = Scalar
        values = '2.0 2.5 3.0 3.5'
        batch_shape = '(4)'
        intermediate_dimension = 1
    []
    [T_0_values]
        type = Scalar
        values = '234.52 631.32 715.32 778.52'
        batch_shape = '(4)'
        intermediate_dimension = 1
    []
    [T_ref_values]
        type = Scalar
        values = '293.15 789.15 894.15 973.15'
        batch_shape = '(4)'
        intermediate_dimension = 1
    []
    [pierls_stress_values]
        type = Scalar
        values = '350.0 450.0 550.0 700.0'
        batch_shape = '(4)'
        intermediate_dimension = 1
    []
    [H_0_values]
        type = Scalar
        values = '0.50 0.65 0.70 0.85'
        batch_shape = '(4)'
        intermediate_dimension = 1
    []
    [Bk_values]
        type = Scalar
        values = '1.0e-4 1.5e-4 2.0e-4 2.5e-4'
        batch_shape = '(4)'
        intermediate_dimension = 1
    []
    [L]
        type = Scalar
        values = '1.0e-6'
    []
    [a]
        type = Scalar
        values = '2.86e-10'
    []
    [b]
        type = Scalar
        values = '2.4783265e-10'
    []
    [h]
        type = Scalar
        values = '2.33518022e-10'
    []
    [kB]
        type = Scalar
        values = '8.617e-5'
    []
    [p]
        type = Scalar
        values = '0.5'
    []
    [q]
        type = Scalar
        values = '1.25'
    []
    [m]
        type = Scalar
        values = '0.3'
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
    [k1]
        type = ScalarLinearInterpolation
        argument = 'forces/T'
        abscissa = 'T_train'
        ordinate = 'k1_values'
    []
    [k2]
        type = ScalarLinearInterpolation
        argument = 'forces/T'
        abscissa = 'T_train'
        ordinate = 'k2_values'
    []
    [T_0]
        type = ScalarLinearInterpolation
        argument = 'forces/T'
        abscissa = 'T_train'
        ordinate = 'T_0_values'
    []
    [T_ref]
        type = ScalarLinearInterpolation
        argument = 'forces/T'
        abscissa = 'T_train'
        ordinate = 'T_ref_values'
    []
    [tau_p]
        type = ScalarLinearInterpolation
        argument = 'forces/T'
        abscissa = 'T_train'
        ordinate = 'pierls_stress_values'
    []
    [H_0]
        type = ScalarLinearInterpolation
        argument = 'forces/T'
        abscissa = 'T_train'
        ordinate = 'H_0_values'
    []
    [Bk]
        type = ScalarLinearInterpolation
        argument = 'forces/T'
        abscissa = 'T_train'
        ordinate = 'Bk_values'
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
        dislocation_density = 'state/internal/rho_m'
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
        models = 'overstress vonmises yield full_yield'
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
        Bk = 'Bk'
        pierls_stress = 'tau_p'
        T_ref = 'T_ref'
        T_0 = 'T_0'
        p = 'p'
        q = 'q'
        k_B = 'kB'
        activation_energy = 'H_0'
        v_disl = 'state/internal/v_disl'
    []
    [rho_m_rate]
        type = KocksMeckingDislocationDensity
        plastic_flow_rate = 'state/internal/gamma_rate'
        k1 = 'k1'
        k2 = 'k2'
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
        models = 'mandel_stress kinharden overstress vonmises athermal normality shear_eff shear_athermal v_disl rho_m_rate flow_rate Eprate Kprate Erate Eerate elasticity integrate_rho_m integrate_Kprate integrate_X integrate_stress mixed mixed_old rename'
    []
[]