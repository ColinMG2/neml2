#include "neml2/models/solid_mechanics/crystal_plasticity/ThermallyActivatedDislocationMobility.h"
#include "neml2/tensors/Scalar.h"
#include "neml2/tensors/functions/pow.h"
#include "neml2/tensors/functions/exp.h"
#include "neml2/tensors/functions/abs.h"
#include "neml2/tensors/functions/sign.h"

namespace neml2
{
register_NEML2_object(ThermallyActivatedDislocationMobility);

OptionSet
ThermallyActivatedDislocationMobility::expected_options()
{
    OptionSet options = Model::expected_options();
    options.set_input("effective_shear");
    options.set_input("athermal_shear");
    options.set_output("v_disl");
    options.set_parameter<TensorName<Scalar>>("h");
    options.set_parameter<TensorName<Scalar>>("L");
    options.set_parameter<TensorName<Scalar>>("b");
    options.set_parameter<TensorName<Scalar>>("a");
    options.set_parameter<TensorName<Scalar>>("Bk");
    options.set_parameter<TensorName<Scalar>>("pierls_stress");
    options.set_parameter<TensorName<Scalar>>("T_0");
    options.set_parameter<TensorName<Scalar>>("p");
    options.set_parameter<TensorName<Scalar>>("q");
    options.set_buffer<TensorName<Scalar>>("reference_temperature");
    options.set_buffer<TensorName<Scalar>>("k_B");
    options.set_buffer<TensorName<Scalar>>("activation_energy");

    return options;
}
ThermallyActivatedDislocationMobility::ThermallyActivatedDislocationMobility(const OptionSet & options) : Model(options),
    _tau_eff(declare_input_variable<Scalar>("effective_shear")),
    _tau_a(declare_input_variable<Scalar>("athermal_shear")),
    _h(declare_parameter<Scalar>("h", "h")),
    _L(declare_parameter<Scalar>("L", "L")),
    _b(declare_parameter<Scalar>("b", "b")),
    _a(declare_parameter<Scalar>("a", "a")),
    _Bk(declare_parameter<Scalar>("Bk", "Bk")),
    _tau_p(declare_parameter<Scalar>("pierls_stress", "pierls_stress")),
    _T_0(declare_parameter<Scalar>("T_0", "T_0")),
    _p(declare_parameter<Scalar>("p", "p")),
    _q(declare_parameter<Scalar>("q", "q")),
    _T(declare_buffer<Scalar>("T_ref", "reference_temperature")),
    _k_B(declare_buffer<Scalar>("k_B", "k_B")),
    _D_H(declare_buffer<Scalar>("activation_energy", "activation_energy")),
    _v(declare_output_variable<Scalar>("v_disl"))
{
}
void
ThermallyActivatedDislocationMobility::set_value(bool out, bool dout_din, bool /*d2out_din2*/)
{
    const auto & tau_eff = _tau_eff;
    const auto & tau_a = _tau_a;
    const auto h = _h;
    const auto L = _L;
    const auto b = _b;
    const auto a = _a;
    const auto Bk = _Bk;
    const auto tau_p = _tau_p;
    const auto T_0 = _T_0;
    const auto p = _p;
    const auto q = _q;
    const auto k_B = _k_B;
    const auto D_H = _D_H;
    const auto T = _T;
    auto v = (h * L * b) / (pow(a, 2) * Bk) * sign(tau_eff()) * exp(-D_H / (k_B * T) * pow(1 - pow( abs(tau_eff - tau_a)/tau_p ,p), q));

    if (out)
    {
        _v = v;
    }

    if (dout_din)
    {
        if (tau_eff.is_dependent())
        {
            _v.d(_tau_eff) = (h * L * b) / (pow(a, 2) * Bk) * tau_eff / sign(tau_eff()) * exp(-D_H / (k_B * T) * pow(1 - pow(abs(tau_eff - tau_a) / tau_p, p) ,q))
                            - (h * L * b) / (pow(a, 2) * Bk) * sign(tau_eff()) * D_H / (k_B * T) * p * q * pow(tau_p, -p) * pow(abs(tau_eff - tau_a), p-2) * (tau_eff - tau_a)
                            * exp(-D_H / (k_B * T) * pow(1 - pow(abs(tau_eff - tau_a) / tau_p, p) ,q));
        }

        if (tau_a.is_dependent())
        {
            _v.d(_tau_a) = -(h * L * b) / (pow(a, 2) * Bk) * sign(tau_eff()) * D_H / (k_B * T) * p * q * pow(tau_p, -p) * pow(abs(tau_eff - tau_a), p-2) * (tau_eff - tau_a)
                            * exp(-D_H / (k_B * T) * pow(1 - pow(abs(tau_eff - tau_a) / tau_p, p) ,q));
        }

        if (const auto * const T_0_ptr = nl_param("T_0"))
        {
            _v.d(*T_0_ptr) = -(h * L * b) / (pow(a, 2) * Bk) * sign(tau_eff()) * D_H / (k_B * T) * T / (T_0 * T_0) * exp(-D_H / (k_B * T) * pow(1 - pow(abs(tau_eff - tau_a) /tau_p ,p) ,q));
        }
    }
}
}
