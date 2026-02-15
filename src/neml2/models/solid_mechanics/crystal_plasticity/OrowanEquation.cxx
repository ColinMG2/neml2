#include "neml2/models/solid_mechanics/crystal_plasticity/OrowanEquation.h"

namespace neml2
{
register_NEML2_object(OrowanEquation);

OptionSet
OrowanEquation::expected_options()
{
    OptionSet options = Model::expected_options();
    options.set_input("dislocation_density");
    options.set_input("v_disl");
    options.set_parameter<TensorName<Scalar>>("b");
    options.set_output("plastic_flow_rate");

    return options;
}
OrowanEquation::OrowanEquation(const OptionSet & options) : Model(options),
    _rho_m(declare_input_variable<Scalar>("dislocation_density")),
    _v_disl(declare_input_variable<Scalar>("v_disl")),
    _b(declare_parameter<Scalar>("b","b")),
    _gamma_dot(declare_output_variable<Scalar>("plastic_flow_rate"))
{
}
void
OrowanEquation::set_value(bool out, bool dout_din, bool /*d2out_din2*/)
{
    auto gamma_dot = _rho_m() * _b * _v_disl();

    if (out)
    {
        _gamma_dot = gamma_dot;
    }
    if (dout_din)
    {
        if (_rho_m.is_dependent())
            _gamma_dot.d(_rho_m) = _b * _v_disl();
        
        if (_v_disl.is_dependent())
            _gamma_dot.d(_v_disl) = _rho_m() * _b;

        if (const auto * const b = nl_param("b"))
            _gamma_dot.d(*b) = _rho_m() * _v_disl();
    }
}
}