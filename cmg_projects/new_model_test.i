[Tensors]
    [T_ref]
        type = Scalar
        values = '2956'
    []
    [C]
        type = Scalar
        values = '5000.0'
    []
    [g]
        type = Scalar
        values = '10.0'
    []
    [sy]
        type = Scalar
        values = '500.0'
    []
    [E]
        type = Scalar
        values = '50000.0'
    []
    [G]
        type = Scalar
        values = '19230.76923'
    []
    [k1]
        type = Scalar
        values = '1.0'
    []
    [k2]
        type = Scalar
        values = '10.0'
    []
    [T_0]
        type = Scalar
        values = '2364.8'
    []
    [L]
        type = Scalar
        values = '1.0e-6'
    []
    [a]
        type = Scalar
        values = '3.16e-10'
    []
    [b]
        type = Scalar
        values = '2.73664028e-10'
    []
    [h]
        type = Scalar
        values = '2.5801292e-10'
    []
    [H_0]
        type = Scalar
        values = '1.63'
    []
    [kB]
        type = Scalar
        values = '8.617e-5'
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
        values = '0.3'
    []
[]

[Models]
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
        Bk = 1.0e-4
        pierls_stress = 2.03e3
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
        models = 'mandel_stress kinharden overstress vonmises athermal normality shear_eff shear_athermal v_disl rho_m_rate flow_rate Eprate Kprate Erate Eerate elasticity integrate_rho_m integrate_Kprate integrate_stress integrate_X mixed mixed_old rename'
    []
[]