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
    options.set_input("dislocation_density");
    options.set_input("temperature");
    options.set_buffer<TensorName<Scalar>>("h");
    options.set_buffer<TensorName<Scalar>>("b");
    options.set_buffer<TensorName<Scalar>>("a");
    options.set_parameter<TensorName<Scalar>>("Bk");
    options.set_parameter<TensorName<Scalar>>("tau_p");
    options.set_parameter<TensorName<Scalar>>("T_0");
    options.set_parameter<TensorName<Scalar>>("p");
    options.set_parameter<TensorName<Scalar>>("q");
    options.set_parameter<TensorName<Scalar>>("H_0");
    options.set_buffer<TensorName<Scalar>>("k_B");
    options.set_parameter<TensorName<Scalar>>("s");
    options.set_output("v_disl");

    return options;
}
ThermallyActivatedDislocationMobility::ThermallyActivatedDislocationMobility(const OptionSet & options) : Model(options),
    _tau_eff(declare_input_variable<Scalar>("effective_shear")),
    _tau_a(declare_input_variable<Scalar>("athermal_shear")),
    _rho_m(declare_input_variable<Scalar>("dislocation_density")),
    _T(declare_input_variable<Scalar>("temperature")),
    _h(declare_buffer<Scalar>("h", "h")),
    _b(declare_buffer<Scalar>("b", "b")),
    _a(declare_buffer<Scalar>("a", "a")),
    _Bk(declare_parameter<Scalar>("Bk", "Bk", true)),
    _tau_p(declare_parameter<Scalar>("tau_p", "tau_p", true)),
    _T_0(declare_parameter<Scalar>("T_0", "T_0", true)),
    _p(declare_parameter<Scalar>("p", "p", true)),
    _q(declare_parameter<Scalar>("q", "q", true)),
    _D_H(declare_parameter<Scalar>("H_0", "H_0", true)),
    _k_B(declare_buffer<Scalar>("k_B", "k_B")),
    _s(declare_parameter<Scalar>("s","s", true)),
    _v(declare_output_variable<Scalar>("v_disl"))
{
}
void
ThermallyActivatedDislocationMobility::set_value(bool out, bool dout_din, bool /*d2out_din2*/)
{
    // Precompute common subexpressions
    const auto L_eff        = pow(_rho_m(), -0.5);
    const auto prefac       = (_h * L_eff * _b) / (pow(_a, 2.0) * _Bk);
    const auto mcl_eff      = macaulay(_tau_eff());
    const auto tau_1        = _tau_eff() - _tau_a();
    const auto tau_tilda    = tau_1 / _tau_p;
    const auto phi          = pow((1 + exp(-_s * tau_tilda)), -1);
    const auto eps          = 1.0e-6;
    const auto tau_th       = phi * macaulay(tau_1) + (1 - phi) * eps * _tau_p;
    const auto inner        =  1 - pow(tau_th, _p) / pow(_tau_p, _p);
    const auto D_G          = _D_H * (pow(inner, _q) - _T() / _T_0);
    const auto exp_val      = exp(-D_G / (_k_B * _T()));

    if (out)
        _v = prefac * mcl_eff * exp_val;

    if (dout_din)
    {
        // Clamp mcl_diff away from zero for derivative terms to avoid
        // pow(0, p-1) = pow(0, negative) = NaN when p < 1, and log(0) = -Inf.
        // The heaviside factor zeros out the result when tau_eff <= tau_a,
        // but IEEE 754 propagates NaN through 0*NaN, so we clamp first.
        const auto tau_1_safe          = clamp(tau_1, 1.0e-30, 1.0e30);
        const auto tau_tilda_safe      = tau_1_safe / _tau_p;
        const auto phi_safe            = pow((1 + exp(-_s * tau_tilda_safe)), -1);
        const auto tau_th_safe         = phi_safe * macaulay(tau_1_safe) + (1 - phi_safe) * eps * _tau_p;
        const auto inner_safe          = 1.0 - pow(tau_th_safe, _p) / pow(_tau_p, _p);

        // Shared thermal factor in the tau_eff / tau_a Jacobians
        const auto dexp_core = _D_H / (_k_B * _T()) * _q * pow(inner_safe, _q - 1.0)
                               * _p * pow(tau_th_safe / _tau_p, _p - 1.0);

        if (_tau_eff.is_dependent())
            _v.d(_tau_eff) = prefac * heaviside(_tau_eff()) * exp_val + prefac * mcl_eff * dexp_core * 
                                    (pow(phi_safe, 2.0) * _s / _tau_p * exp(-_s * tau_tilda_safe) * 
                                    (macaulay(tau_1_safe)/_tau_p - eps) + phi_safe * heaviside(tau_1_safe) / _tau_p) * exp_val;

        if (_tau_a.is_dependent())
            _v.d(_tau_a) = -prefac * mcl_eff * dexp_core * (pow(phi_safe, 2.0) * _s / _tau_p * exp(-_s * tau_tilda_safe) * 
                                    (macaulay(tau_1_safe)/_tau_p - eps) + phi_safe * heaviside(tau_1_safe) / _tau_p) * exp_val;

        if (_rho_m.is_dependent())
            _v.d(_rho_m) = (-0.5 * _h * _b * pow(_rho_m(), -1.5)) / (pow(_a, 2.0) * _Bk) * mcl_eff * exp_val;

        if (_T.is_dependent())
            _v.d(_T) = prefac * mcl_eff * _D_H / (_k_B * pow(_T(), 2.0)) * pow(inner_safe, _q) * exp_val;

        if (const auto * const Bk = nl_param("Bk"))
            _v.d(*Bk) = -(_h * L_eff * _b) / (pow(_a, 2.0) * pow(_Bk, 2.0)) * mcl_eff * exp_val;

        if (const auto * const tau_p = nl_param("tau_p"))
            _v.d(*tau_p) = -prefac * mcl_eff * dexp_core * (pow(phi_safe, 2.0) * _s * tau_tilda_safe / pow(_tau_p, 2.0) * 
                            macaulay(tau_1_safe) * exp(-_s * tau_tilda_safe) + phi_safe * macaulay(tau_1_safe) / pow(_tau_p, 2.0) - 
                            pow(phi_safe, 2.0) * _s * tau_tilda_safe * eps / _tau_p) * exp_val;

        if (const auto * const T_0 = nl_param("T_0"))
            _v.d(*T_0) = -prefac * mcl_eff * _D_H / (_k_B * _T())
                          * _T() / pow(_T_0, 2.0) * exp_val;

        if (const auto * const p = nl_param("p"))
            _v.d(*p) = prefac * mcl_eff * _D_H / (_k_B * _T()) * _q * pow(inner_safe, _q - 1.0)
                       * log(tau_th_safe / _tau_p) * pow(tau_th_safe / _tau_p, _p) * exp_val;

        if (const auto * const q = nl_param("q"))
            _v.d(*q) = -prefac * mcl_eff * _D_H / (_k_B * _T()) * pow(inner_safe, _q) * log(inner_safe) * exp_val;
        
        if (const auto * const s = nl_param("s"))
            _v.d(*s) = prefac * mcl_eff * dexp_core * (pow(phi_safe, 2.0) * tau_tilda_safe * exp(-_s * tau_tilda_safe) 
                        * (macaulay(tau_1_safe) / _tau_p - eps)) * exp_val;
    }
}
}
