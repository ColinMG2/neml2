[Tensors]
    [T_train]
        type = Scalar
        values = '399.0 500, 601.0'
        batch_shape = '(3)'
        intermediate_dimension = 1
    []
    [C_values]
        type = Scalar
        values = '100.0 200.0 300.0'
        batch_shape = '(3)'
        intermediate_dimension = 1
    []
    [g_values]
        type = Scalar
        values = '5.0 10.0 15.0'
        batch_shape = '(3)'
        intermediate_dimension = 1
    []
    [sy_values]
        type = Scalar
        values = '550.0 500.0 300.0'
        batch_shape = '(3)'
        intermediate_dimension = 1
    []
    [E_values]
        type = Scalar
        values = '68000.0 72000.0 66000.0'
        batch_shape = '(3)'
        intermediate_dimension = 1
    []
    [G_values]
        type = Scalar
        values = '26153.84615 27692.30769 25384.61538'
        batch_shape = '(3)'
        intermediate_dimension = 1
    []
    [sy_values]
        type = Scalar
        values = '550.0 500.0 300.0'
        batch_shape = '(3)'
        intermediate_dimension = 1
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
        b = 1
        L = 1
        athermal_stress = 'state/internal/s_a'
    []
    [yield]
        type = YieldFunction
        yield_stress = 'sy'
    []
    [full_yield]
        type = ScalarLinearCombination
        from_var = 'yield athermal'
        to_var = 'state/internal/fp'
        coefficients = '1 -1'
    []
    [flow]
        type = ComposedModel
        models = 'vonmises full_yield'
    []
    [normality]
        type = Normality
        model = 'flow'
        function = 'state/internal/fp'
        from = 'state/internal/M state/internal/X'
        to = 'state/internal/NM state/internal/NX'
    []
    [shear]
        type = NormalToShearStress
        normal_stress = 'state/internal/M state/internal/s_a'
        shear_stress = 'state/internal/tau_eff state/internal/tau_a'
        schmid_factor = 0.5
    []
    [v_disl]
        type = ThermallyActivatedDislocationMobility
        effective_shear = 'state/internal/tau_eff'
        athermal_shear = 'state/internal/tau_a'
        h = 1
        L = 1
        b = 1
        a = 2
        Bk = 5
        pierls_stress = 500
        T_0 = 600
        p = 2
        q = 3
        reference_temperature = 'T_train'
        k_B = 1.380649e-23
        activation_energy = 100
    []
    [rho_m_rate]
        type = KocksMeckingDislocationDensity
        plastic_flow_rate = 'state/internal/gamma_rate'
        k1 = 2
        k2 = 2
        rho_m = 0.5
        L = 1
        density_rate = 'state/internal/rho_m_rate'
    []
    [flow_rate]
        type = OrowanEquation
        dislocation_density = 'state/internal/rho_m'
        v_disl = 'state/internal/v_disl'
        b = 0.5
        plastic_flow_rate = 'state/internal/gamma_rate'
    []
    [Eprate]
        type = AssociativePlasticFlow
    []
    [eprate]
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
    [integrate_stress]
        type = SR2BackwardEulerTimeIntegration
        variable = 'state/S'
    []
    [integrate_ep]
        type = ScalarBackwardEulerTimeIntegration
        variable = 'state/internal/ep'
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
        models = 'mandel_stress vonmises kinharden athermal yield full_yield flow normality shear v_disl rho_m_rate flow_rate Eprate eprate Erate Eerate elasticity integrate_stress integrate_ep mixed mixed_old rename'
    []
[]