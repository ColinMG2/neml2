# neml2
# y = A*exp(s*x) with A = 2.5, s = -0.75, x = 1.3
#   -> 2.5 * exp(-0.975) = 0.94263050...
[Drivers]
  [unit]
    type = ModelUnitTest
    model = 'model'
    input_Scalar_names = 'from'
    input_Scalar_values = 'x'
    output_Scalar_names = 'to'
    output_Scalar_values = 'y'
  []
[]

[Tensors]
  [x]
    type = Python
    expr = 'Scalar(1.3)'
  []
  [y]
    type = Python
    expr = 'Scalar(2.5 * math.exp(-0.75 * 1.3))'
  []
[]

[Models]
  [model]
    type = ScalarExponential
    scaling = 2.5
    rate = -0.75
  []
[]
