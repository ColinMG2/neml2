# neml2
# Same map as ScalarExponential.i, but with ``scaling`` promoted to a runtime
# input (wired from a ScalarInputParameter) so the dy/dA action is exercised
# alongside dy/dx.
#   y = A*exp(s*x), A = 2.5, s = -0.75, x = 1.3 -> 2.5 * exp(-0.975)
[Drivers]
  [unit]
    type = ModelUnitTest
    model = 'model'
    input_Scalar_names = 'from variable'
    input_Scalar_values = 'x A'
    output_Scalar_names = 'to'
    output_Scalar_values = 'y'
  []
[]

[Tensors]
  [x]
    type = Python
    expr = 'Scalar(1.3)'
  []
  [A]
    type = Python
    expr = 'Scalar(2.5)'
  []
  [y]
    type = Python
    expr = 'Scalar(2.5 * math.exp(-0.75 * 1.3))'
  []
[]

[Models]
  [A_in]
    type = ScalarInputParameter
  []
  [expmap]
    type = ScalarExponential
    scaling = 'A_in'
    rate = -0.75
  []
  [model]
    type = ComposedModel
    models = 'A_in expmap'
  []
[]
