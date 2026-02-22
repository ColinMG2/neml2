#include "neml2/models/solid_mechanics/crystal_plasticity/KocksMeckingDislocationDensity.h"
#include "neml2/tensors/functions/pow.h"

namespace neml2
{
register_NEML2_object(KocksMeckingDislocationDensity);

OptionSet
KocksMeckingDislocationDensity::expected_options()
{
    OptionSet options = Model::expected_options();
    options.doc() = "Computes the dislocation density rate using the Kocks-Mecking model: "
                    "\\f$ \\dot{\\rho_m} = (\\left \\frac{k_1}{L} - k_2 \\rho_m \\right) \\dot{\\gamma} \\f$"
                    "where \\f$ k_1 \\f$ is the hardening coefficient, \\f$ k_2 \\f$ is the recovery coefficient, "
                    "\\f$ L \\f$ is the mean free path, and \\f$ \\dot{\\rho_m} \\f$ is the dislocation density rate.";
    options.set_input("plastic_flow_rate");
    options.set("plastic_flow_rate").doc() = "Plastic flow rate (from Orowan equation)";
    options.set_parameter<TensorName<Scalar>>("k1");
    options.set("k1").doc() = "Hardening coefficient";
    options.set_parameter<TensorName<Scalar>>("k2");
    options.set("k2").doc() = "Recovery coefficient";
    options.set_input("dislocation_density");
    options.set("dislocation_density").doc() = "Current dislocation density";
    options.set_parameter<TensorName<Scalar>>("L");
    options.set("L").doc() = "Mean free path";
    options.set_output("density_rate");
    options.set("density_rate").doc() = "Dislocation density rate";

    return options;
}
KocksMeckingDislocationDensity::KocksMeckingDislocationDensity(const OptionSet & options) : Model(options),
    _gamma_dot(declare_input_variable<Scalar>("plastic_flow_rate")),
    _k1(declare_parameter<Scalar>("k1", "k1", true)),
    _k2(declare_parameter<Scalar>("k2", "k2", true)),
    _rho_m(declare_input_variable<Scalar>("dislocation_density")),
    _L(declare_parameter<Scalar>("L", "L", true)),
    _rho_m_dot(declare_output_variable<Scalar>("density_rate"))
{
}
void
KocksMeckingDislocationDensity::set_value(bool out, bool dout_din, bool /*d2out_din2*/)
{
    if (out)
        _rho_m_dot = (_k1/_L - _k2 * _rho_m()) * _gamma_dot();

    if (dout_din)
    {
        if (_gamma_dot.is_dependent())
            _rho_m_dot.d(_gamma_dot) = _k1/_L - _k2 * _rho_m();
        
        if (_rho_m.is_dependent())
            _rho_m_dot.d(_rho_m) = -_k2 * _gamma_dot();

        if (const auto * const k1 = nl_param("k1"))
            _rho_m_dot.d(*k1) = _gamma_dot() / _L;
        
        if (const auto * const k2 = nl_param("k2"))
            _rho_m_dot.d(*k2) = -_rho_m() * _gamma_dot();
        
        if (const auto * const L = nl_param("L"))
            _rho_m_dot.d(*L) = -(_k1 * _gamma_dot()) / pow(_L, 2.0);
    }
}
}