[Tensors]
    [T_train] # Kelvin
        type = Scalar
        values = '522.15 523.15 673.15 673.15 673.15 753.15 823.15 823.15 824.15'
        batch_shape = '(9)'
        intermediate_dimension = 1
    []
    [T_ref_values] # K
        type = Scalar
        values = '523.15 523.15 673.15 673.15 673.15 753.15 823.15 823.15 823.15'
        batch_shape = '(9)'
        intermediate_dimension = 1
    []
    [C] # MPa
        type = Scalar
        values = '41500.0'
        batch_shape = '(1)'
    []
    [g] # unitless
        type = Scalar
        values = '350.0'
        batch_shape = '(1)'
    []
    [k1] # mm^-1
        type = Scalar
        values = '8.3e5'
        batch_shape = '(1)'
    []
    [k2] # unitless
        type = Scalar
        values = '150.0'
        batch_shape = '(1)'
    []
    [T_0] # K
        type = Scalar
        values = '2956.0'
        batch_shape = '(1)'
    []
    [tau_p] # MPa
        type = Scalar
        values = '2.03e3'
        batch_shape = '(1)'
    []
    [H_0] # eV
        type = Scalar
        values = '1.63'
        batch_shape = '(1)'
    []
    [Bk] # MPa * s
        type = Scalar
        values = '8.3e-6'
        batch_shape = '(1)'
    []
    [alpha]
        type = Scalar
        values = '0.5'
    []
    [p]
        type = Scalar
        values = '0.86'
    []
    [q]
        type = Scalar
        values = '1.69'
    []
    [m]
        type = Scalar
        values = '0.333'
    []
    [a] # mm
        type = Scalar
        values = '3.16e-7'
    []
    [b] # mm
        type = Scalar
        values = '2.73664028e-7'
    []
    [h] # mm
        type = Scalar
        values = '2.5801292e-7'
    []
    [kB] # eV/K
        type = Scalar
        values = '8.617e-5'
    []
[]

[Models]
    [T_ref]
        type = ScalarLinearInterpolation
        argument = 'forces/T'
        abscissa = 'T_train'
        ordinate = 'T_ref_values'
    []
    [T_C]
        type = ScalarLinearCombination
        from_var = 'forces/T'
        to_var = 'forces/T_C'
        constant_coefficient = '-273.15'
    []
    [E]
        type = ScalarQuadraticInterpolation
        a = '-2.716e-2'
        b = '0.01253e3'
        c = '396507'
        argument = 'forces/T_C'
        output = 'E'
    []
    [nu]
        type = ScalarQuadraticInterpolation
        a = '3.157e-9'
        b = '-8.030e-6'
        c = '0.285'
        argument = 'forces/T_C'
        output = 'nu'
    []
    [G_bottom_inner]
        type = ScalarLinearCombination
        from_var = 'nu'
        to_var = 'G_bottom_inner'
        constant_coefficient = '1'
    []
    [G_bottom]
        type = ScalarMultiplication
        from_var = 'G_bottom_inner'
        to_var = 'G_bottom'
        coefficient = '2'
    []
    [G]
        type = ScalarMultiplication
        from_var = 'E G_bottom'
        to_var = 'G'
        reciprocal = 'false true'
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
        alpha = 'alpha'
        b = 'b'
        dislocation_density = 'state/internal/rho_m'
        athermal_stress = 'state/internal/s_a'
    []
    [yield]
        type = YieldFunction
        yield_stress = '0.0'
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
        dislocation_density = 'state/internal/rho_m'
        h = 'h'
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
        coefficients = 'E nu'
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
        models = 'T_ref T_C G_bottom G_bottom_inner G mandel_stress kinharden overstress vonmises athermal normality shear_eff shear_athermal v_disl rho_m_rate flow_rate Eprate Kprate Erate Eerate elasticity integrate_rho_m integrate_Kprate integrate_stress integrate_X mixed mixed_old rename'
    []
[]