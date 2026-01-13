[Solvers]
    [newton]
        type = Newton
        rel_tol = 1e-08
        abs_tol = 1e-10
        max_its = 50
        verbose = true
    []
[]

[Models]
    [eq1]
        type = SR2LinearCombination
        from_var = 'forces/E state/Ep'
        to_var = 'state/Ee'
        coefficients = '1 -1'
    []
    [eq2]
        type = LinearIsotropicElasticity
        strain = 'state/Ee'
        stress = 'state/S'
        coefficient_types = 'SHEAR_MODULUS BULK_MODULUS'
        coefficients = '38.5e3 83.3e3'
    []
    [eq3]
        type = SR2Invariant
        invariant_type = 'VONMISES'
        tensor = 'state/S'
        invariant = 'state/s'
    []
    [eq4]
        type = YieldFunction
        yield_stress = 150
        yield_function = 'state/fp'
        effective_stress = 'state/s'
    []
    [flow]
        type = ComposedModel
        models = 'eq3 eq4'
    []
    [eq5]
        type = Normality
        model = 'flow'
        function = 'state/fp'
        from = 'state/S'
        to = 'state/N'
    []
    [eq6]
        type = PerzynaPlasticFlowRate
        reference_stress = 100
        exponent = 2
        yield_function = 'state/fp'
        flow_rate = 'state/gamma_rate'
    []
    [eq7]
        type = AssociativePlasticFlow
        flow_rate = 'state/gamma_rate'
        flow_direction = 'state/N'
        plastic_strain_rate = 'state/Ep_rate'
    []
    [eq8]
        type = SR2BackwardEulerTimeIntegration
        variable = 'state/Ep'
    []
    [system]
        type = ComposedModel
        models = "eq1 eq2 flow eq5 eq6 eq7 eq8"
    []
    [model]
        type = ImplicitUpdate
        implicit_model = 'system'
        solver = 'newton'
    []
    [prediction]
        type = ComposedModel
        models = 'model eq1 eq2'
        additional_outputs = 'state/S'
    []
[]