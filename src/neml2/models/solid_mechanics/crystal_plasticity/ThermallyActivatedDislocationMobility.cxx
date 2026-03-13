#include "neml2/models/solid_mechanics/crystal_plasticity/ThermallyActivatedDislocationMobility.h"
#include "neml2/tensors/Scalar.h"
#include "neml2/tensors/functions/pow.h"
#include "neml2/tensors/functions/exp.h"
#include "neml2/tensors/functions/macaulay.h"
#include "neml2/tensors/functions/heaviside.h"
#include "neml2/tensors/functions/log.h"
#include "neml2/tensors/functions/clamp.h"

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
    options.set_parameter<TensorName<Scalar>>("activation_energy");
    options.set_parameter<TensorName<Scalar>>("T_ref");
    options.set_buffer<TensorName<Scalar>>("k_B");

    return options;
}
ThermallyActivatedDislocationMobility::ThermallyActivatedDislocationMobility(const OptionSet & options) : Model(options),
    _tau_eff(declare_input_variable<Scalar>("effective_shear")),
    _tau_a(declare_input_variable<Scalar>("athermal_shear")),
    _h(declare_parameter<Scalar>("h", "h", true)),
    _L(declare_parameter<Scalar>("L", "L", true)),
    _b(declare_parameter<Scalar>("b", "b", true)),
    _a(declare_parameter<Scalar>("a", "a", true)),
    _Bk(declare_parameter<Scalar>("Bk", "Bk", true)),
    _tau_p(declare_parameter<Scalar>("pierls_stress", "pierls_stress", true)),
    _T_0(declare_parameter<Scalar>("T_0", "T_0", true)),
    _p(declare_parameter<Scalar>("p", "p", true)),
    _q(declare_parameter<Scalar>("q", "q", true)),
    _D_H(declare_parameter<Scalar>("activation_energy", "activation_energy", true)),
    _T(declare_parameter<Scalar>("T_ref", "T_ref", true)),
    _k_B(declare_buffer<Scalar>("k_B", "k_B")),
    _v(declare_output_variable<Scalar>("v_disl"))
{
}
void
ThermallyActivatedDislocationMobility::set_value(bool out, bool dout_din, bool /*d2out_din2*/)
{
    // Precompute common subexpressions
    const auto prefac       = (_h * _L * _b) / (pow(_a, 2.0) * _Bk);
    const auto mcl_eff      = macaulay(_tau_eff());
    const auto mcl_diff     = macaulay(_tau_eff() - _tau_a());
    const auto inner        = 1.0 - pow(mcl_diff, _p) / pow(_tau_p, _p);
    const auto exp_val      = exp(-_D_H / (_k_B * _T) * (pow(inner, _q) - _T / _T_0));

    if (out)
        _v = prefac * mcl_eff * exp_val;

    if (dout_din)
    {
        // Clamp mcl_diff away from zero for derivative terms to avoid
        // pow(0, p-1) = pow(0, negative) = NaN when p < 1, and log(0) = -Inf.
        // The heaviside factor zeros out the result when tau_eff <= tau_a,
        // but IEEE 754 propagates NaN through 0*NaN, so we clamp first.
        const auto mcl_diff_safe = clamp(mcl_diff, 1.0e-30, 1.0e30);
        const auto inner_safe    = 1.0 - pow(mcl_diff_safe, _p) / pow(_tau_p, _p);

        // Shared thermal factor in the tau_eff / tau_a Jacobians
        const auto dexp_core = _D_H / (_k_B * _T) * _q * pow(inner_safe, _q - 1.0)
                               * pow(_tau_p, -_p) * _p * pow(mcl_diff_safe, _p - 1.0)
                               * heaviside(_tau_eff() - _tau_a());

        if (_tau_eff.is_dependent())
            _v.d(_tau_eff) = prefac * heaviside(_tau_eff()) * exp_val
                                    + prefac * mcl_eff * dexp_core * exp_val;

        if (_tau_a.is_dependent())
            _v.d(_tau_a) = -prefac * mcl_eff * dexp_core * exp_val;

        if (const auto * const h = nl_param("h"))
            _v.d(*h) = (_L * _b) / (pow(_a, 2.0) * _Bk) * mcl_eff * exp_val;

        if (const auto * const L = nl_param("L"))
            _v.d(*L) = (_h * _b) / (pow(_a, 2.0) * _Bk) * mcl_eff * exp_val;

        if (const auto * const b = nl_param("b"))
            _v.d(*b) = (_h * _L) / (pow(_a, 2.0) * _Bk) * mcl_eff * exp_val;

        if (const auto * const a = nl_param("a"))
            _v.d(*a) = (-2.0 * _h * _L * _b) / (pow(_a, 3.0) * _Bk) * mcl_eff * exp_val;

        if (const auto * const Bk = nl_param("Bk"))
            _v.d(*Bk) = -(_h * _L * _b) / (pow(_a, 2.0) * pow(_Bk, 2.0)) * mcl_eff * exp_val;

        if (const auto * const tau_p = nl_param("pierls_stress"))
            _v.d(*tau_p) = -prefac * mcl_eff * _D_H / (_k_B * _T)
                           * _q * pow(inner_safe, _q - 1.0)
                           * pow(mcl_diff_safe, _p) * _p * pow(_tau_p, -_p - 1.0) * exp_val;

        if (const auto * const T_0 = nl_param("T_0"))
            _v.d(*T_0) = -prefac * mcl_eff * _D_H / (_k_B * _T)
                          * _T / pow(_T_0, 2.0) * exp_val;

        if (const auto * const p = nl_param("p"))
            _v.d(*p) = prefac * mcl_eff * _D_H / (_k_B * _T)
                       * _q * pow(inner_safe, _q - 1.0)
                       * log(mcl_diff_safe / _tau_p) * pow(mcl_diff_safe / _tau_p, _p) * exp_val;

        if (const auto * const q = nl_param("q"))
            _v.d(*q) = -prefac * mcl_eff * _D_H / (_k_B * _T)
                       * pow(inner_safe, _q) * log(clamp(inner_safe, 1.0e-30, 1.0e30)) * exp_val;
    }
}
}
