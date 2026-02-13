#include "neml2/models/solid_mechanics/crystal_plasticity/KocksMeckingDislocationDensity.h"

namespace neml2
{
register_NEML2_object(KocksMeckingDislocationDensity);

OptionSet
KocksMeckingDislocationDensity::expected_options()
{
    OptionSet options = Model::expected_options();
    options.set_input("plastic_flow_rate");
    options.set_parameter<TensorName<Scalar>>("k1");
    options.set_parameter<TensorName<Scalar>>("k2");
    options.set_parameter<TensorName<Scalar>>("rho_m");
    options.set_parameter<TensorName<Scalar>>("L");
    options.set_output("density_rate");

    return options;
}
KocksMeckingDislocationDensity::KocksMeckingDislocationDensity(const OptionSet & options) : Model(options),
    _gamma_dot(declare_input_variable<Scalar>("plastic_flow_rate")),
    _k1(declare_parameter<Scalar>("k1", "k1")),
    _k2(declare_parameter<Scalar>("k2", "k2")),
    _rho_m(declare_parameter<Scalar>("rho_m", "rho_m")),
    _L(declare_parameter<Scalar>("L", "L")),
    _rho_m_dot(declare_output_variable<Scalar>("density_rate"))
{
}
void
KocksMeckingDislocationDensity::set_value(bool out, bool dout_din, bool /*d2out_din2*/)
{
    const auto & gamma_dot = _gamma_dot;
    const auto k1 = _k1;
    const auto k2 = _k2;
    const auto rho_m = _rho_m;
    const auto L = _L;
    auto rho_m_dot = (k1/L - k2 * rho_m) * gamma_dot;

    if (out)
    {
        _rho_m_dot = rho_m_dot;
    }

    if (dout_din)
    {
        auto drho_m_dot_dgamma_dot = rho_m_dot / gamma_dot;

        if (const auto * const k1 = nl_param("k1"))
            _rho_m_dot.d(*k1) = gamma_dot / L;
        
        if (const auto * const k2 = nl_param("k2"))
            _rho_m_dot.d(*k2) = -rho_m * gamma_dot;
    }
}
}