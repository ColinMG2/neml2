[Solvers]
    [newton]
        type = Newton
    []
[]

[Models]
    [elastic_strain]
        type = SR2LinearCombination
        from_var = 'forces/E state/internal/Ep'
        to_var = 'state/internal/Ee'
        coefficients = '1 -1'
    []
    [elasticity]
        type = LinearIsotropicElasticity
        strain = 'state/internal/Ee'
        stress = 'state/S'
        coefficient_types = 'SHEAR_MODULUS BULK_MODULUS'
        coefficients = '1.4e5 7.8e4'
    []
    [effective_stress]
        type = SR2Invariant
        invariant_type = 'VONMISES'
        tensor = 'state/S'
        invariant = 'state/internal/s'
    []
    [yield_function]
        type = YieldFunction
        yield_stress = 5
    []
    [flow]
        type = ComposedModel
        models = 'effective_stress yield_function'
    []
    [normality]
        type = Normality
        model = 'flow'
        function = 'state/internal/fp'
        from = 'state/S'
        to = 'state/internal/NM'
    []
    [flow_rate]
        type = PerzynaPlasticFlowRate
        reference_stress = 100
        exponent = 2
    []
    [Eprate]
        type = AssociativePlasticFlow
    []
    [integrate_Ep]
        type = SR2BackwardEulerTimeIntegration
        variable = 'state/internal/Ep'
    []
    [implicit_rate]
        type = ComposedModel
        models = "elastic_strain elasticity effective_stress
                  yield_function flow_rate normality
                  Eprate integrate_Ep"
    []
    [return_map]
        type = ImplicitUpdate
        implicit_model = 'implicit_rate'
        solver = 'newton'
    []
    [model]
        type = ComposedModel
        models = "return_map elastic_strain elasticity"
        additional_outputs = 'state/internal/Ep'
    []
[]