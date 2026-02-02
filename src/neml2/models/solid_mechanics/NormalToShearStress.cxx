#include "neml2/models/solid_mechanics/NormalToShearStress.h"
#include "neml2/tensors/Scalar.h"

namespace neml2
{
register_NEML2_object(NormalToShearStress);

OptionSet
NormalToShearStress::expected_options()
{
    OptionSet options = Model::expected_options();
    options.set_input("normal_stress");
    options.set_output("shear_stress");
    options.set_parameter<TensorName<Scalar>>("schmid_factor");

    return options;
}
NormalToShearStress::NormalToShearStress(const OptionSet & options) : Model(options),
    _S(declare_input_variable<Scalar>("normal_stress")),
    _tau(declare_output_variable<Scalar>("shear_stress")),
    _m(declare_parameter<Scalar>("m", "schmid_factor", /*allow nonlinear=*/ true))
{
}
void
NormalToShearStress::set_value(bool out, bool dout_din, bool /*d2out_din2*/)
{
    const auto & S = _S;
    const auto m = _m;
    auto tau = S * m;

    if (out)
        _tau = tau;
    if (dout_din)
    {
        _tau.d(_S) = m;
    }
}
}
