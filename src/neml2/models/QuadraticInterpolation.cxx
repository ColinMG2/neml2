#include "neml2/models/QuadraticInterpolation.h"
#include "neml2/tensors/Scalar.h"
#include "neml2/tensors/Vec.h"
#include "neml2/tensors/SR2.h"
#include "neml2/tensors/indexing.h"
#include "neml2/tensors/shape_utils.h"
#include "neml2/misc/assertions.h"

namespace neml2
{
template <typename T>
OptionSet
QuadraticInterpolation<T>::expected_options()
{
    OptionSet options = Model::expected_options();
    options.set<bool>("define_second_derivatives") = true;
    options.set<TensorName<T>>("a");
    options.set<TensorName<T>>("b");
    options.set<TensorName<T>>("c");
    options.set_input("argument");
    options.set_output("output");

    return options;
}
template <typename T>
QuadraticInterpolation<T>::QuadraticInterpolation(const OptionSet & options) : Model(options),
    _a(this-> template declare_parameter<T>("a", "a")),
    _b(this-> template declare_parameter<T>("b", "b")),
    _c(this-> template declare_parameter<T>("c", "c")),
    _x(this-> template declare_input_variable<Scalar>("argument")),
    _y(options.get("output").user_specified()
        ? this-> template declare_output_variable<T>("output")
        : this-> template declare_output_variable<T>(VariableName(PARAMETERS, name())))
{
}

template <typename T>
void
QuadraticInterpolation<T>::set_value(bool out, bool dout_din, bool d2out_din2)
{
    const auto x = this->_x();

    if (out)
    {
        this->_y = this->_a * x * x + this->_b * x + this->_c;
    }

    if (dout_din)
    {
        if (this->_x.is_dependent())
        {
            this->_y.d(this->_x) = 2.0 * this->_a * x + this->_b;
        }
    }

    if (d2out_din2)
    {
        if (this->_x.is_dependent())
        {
            this->_y.d2(this->_x, this->_x) = 2.0 * this->_a;
        }
    }
}
#define REGISTER(T)                                                             \
    using T##QuadraticInterpolation = QuadraticInterpolation<T>;                \
    register_NEML2_object(T##QuadraticInterpolation);                           \
    template class QuadraticInterpolation<T>
REGISTER(Scalar);
REGISTER(Vec);
REGISTER(SR2);
}