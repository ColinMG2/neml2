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
    const auto L_eff        = pow(_rho_m(), -0.5);                          // Dislocation segment length L = 1/sqrt(rho_m)
    const auto K            = (_h * L_eff * _b) / (pow(_a, 2.0) * _Bk);     // Kink-pair prefactor: K = h·L·b / (a²·Bk)
    const auto mcl_eff      = macaulay(_tau_eff());                         // Positive effective shear stress (for pre-exponential driving force)
    const auto tau_1        = _tau_eff() - _tau_a();                        // Excess stress above athermal threshold
    const auto tau_tilda    = tau_1 / _tau_p;
    const auto phi          = pow((1.0 + exp(clamp(-_s * tau_tilda, -50.0, 50.0))), -1);
    const auto eps          = 1.0e-6;
    const auto tau_th       = phi * macaulay(tau_1) + (1.0 - phi) * eps * _tau_p;
    const auto tau_ratio    = clamp(tau_th / _tau_p, 0.0, 1.0 - 1.0e-6);
    const auto inner        = 1.0 - pow(tau_ratio, _p);
    const auto inner_safe   = clamp(inner, 1.0e-10, 1.0e30);
    const auto D_G          = _D_H * (pow(inner_safe, _q) - _T() / _T_0);
    const auto exp_arg      = clamp((-D_G / (_k_B * _T())), -50.0, 50.0);
    const auto exp_val      = exp(exp_arg);
    const auto v_kp         = K * mcl_eff * exp_val;
    const auto v_drag       = mcl_eff * _b / _Bk;
    const auto Q            = v_kp * v_drag / (v_kp + v_drag + 1.0e-30);
    const auto v            = phi * Q;

    if (out)
        _v = v;

    if (dout_din)
    {
        // Clamp mcl_diff away from zero for derivative terms to avoid
        // pow(0, p-1) = pow(0, negative) = NaN when p < 1, and log(0) = -Inf.
        // The heaviside factor zeros out the result when tau_eff <= tau_a,
        // but IEEE 754 propagates NaN through 0*NaN, so we clamp first.

        // -------- CHAIN RULE COMPUTATION for dv_dtau_eff --------

        const auto tau_1_safe           = clamp(tau_1, 1.0e-30, 1.0e30);
        const auto dtau1_dtau_eff       = 1.0;
        const auto dtau_tilda_dtau_eff  = 1.0 / _tau_p * dtau1_dtau_eff;
        const auto dphi_dtau_eff        = pow(phi, 2.0) * _s * exp(-_s * tau_tilda) * dtau_tilda_dtau_eff;
        const auto dtau_ratio_dtau_eff  = 1 / _tau_p * (dphi_dtau_eff * macaulay(tau_1_safe) + phi * heaviside(tau_1_safe) * dtau1_dtau_eff) - eps * dphi_dtau_eff;
        const auto dD_G_dtau_eff        = -_D_H * _q * pow(inner_safe, _q - 1.0) * _p * pow(tau_ratio, _p - 1.0) * dtau_ratio_dtau_eff;
        const auto dv_kp_dtau_eff       = K * exp_val * (heaviside(_tau_eff()) - mcl_eff / (_k_B * _T()) * dD_G_dtau_eff);
        const auto dv_drag_dtau_eff     = heaviside(_tau_eff()) * _b / _Bk;
        const auto dQ_dtau_eff          = ((dv_kp_dtau_eff * v_drag + v_kp * dv_drag_dtau_eff) * (v_kp + v_drag) - v_kp * v_drag * (dv_kp_dtau_eff + dv_drag_dtau_eff)) / pow(v_kp + v_drag + 1.0e-30, 2.0);

        if (_tau_eff.is_dependent())
            _v.d(_tau_eff) = Q * dphi_dtau_eff + dQ_dtau_eff * phi;

        // -------- CHAIN RULE COMPUTATION for dv_dtau_a --------

        const auto dtau1_dtau_a         = -1.0;
        const auto dtau_tilda_dtau_a    = 1 / _tau_p * dtau1_dtau_a;
        const auto dphi_dtau_a          = pow(phi, 2.0) * _s * exp(-_s * tau_tilda) * dtau_tilda_dtau_a;
        const auto dtau_ratio_dtau_a    = 1 / _tau_p * (dphi_dtau_a * macaulay(tau_1_safe) + phi * heaviside(tau_1_safe) * dtau1_dtau_a) - eps * dphi_dtau_a;
        const auto dD_G_dtau_a          = -_D_H * _q * pow(inner_safe, _q - 1.0) * _p * pow(tau_ratio, _p - 1.0) * dtau_ratio_dtau_a;
        const auto dv_kp_dtau_a         = - K * mcl_eff / (_k_B * _T()) * dD_G_dtau_a * exp_val;
        const auto dQ_dtau_a            = (v_drag * dv_kp_dtau_a * (v_kp + v_drag) - v_kp * v_drag * dv_kp_dtau_a) / pow(v_kp + v_drag + 1.0e-30, 2.0);
        
        if (_tau_a.is_dependent())
            _v.d(_tau_a) = Q * dphi_dtau_a + dQ_dtau_a * phi;

        // -------- CHAIN RULE COMPUTATION for dv_drho_m --------

        const auto dv_kp_drho_m         = - _h * _b * pow(_rho_m(), -1.5) / (2.0 * pow(_a, 2.0) * _Bk) * mcl_eff * exp_val;
        const auto dQ_drho_m            = (v_drag * dv_kp_drho_m * (v_kp + v_drag) - v_kp * v_drag * dv_kp_drho_m) / pow(v_kp + v_drag + 1.0e-30, 2.0);

        if (_rho_m.is_dependent())
            _v.d(_rho_m) = dQ_drho_m * phi;

        // -------- CHAIN RULE COMPUTATION for dv_dT --------

        const auto dD_G_dT              = -_D_H / _T_0;
        const auto dexp_arg_dT          = (-_k_B * _T() * dD_G_dT + D_G * _k_B) / pow(_k_B * _T(), 2.0);
        const auto dv_kp_dT             = K * mcl_eff * dexp_arg_dT * exp_val;
        const auto dQ_dT                = (v_drag * dv_kp_dT * (v_kp + v_drag) - v_kp * v_drag * dv_kp_dT) / pow(v_kp + v_drag + 1.0e-30, 2.0);

        if (_T.is_dependent())
            _v.d(_T) = dQ_dT * phi;

        // -------- CHAIN RULE COMPUTATION for dv_dBk --------

        const auto dv_kp_dBk            = -(_h * L_eff * _b) / pow(_a * _Bk, 2.0) * mcl_eff * exp_val;
        const auto dv_drag_dBk          = -mcl_eff * _b / pow(_Bk, 2.0);
        const auto dQ_dBk               = ((v_drag * dv_kp_dBk + v_kp * dv_drag_dBk) * (v_kp + v_drag) - v_kp * v_drag * (dv_kp_dBk + dv_drag_dBk)) / pow(v_kp + v_drag + 1.0e-30, 2.0);

        if (const auto * const Bk = nl_param("Bk"))
            _v.d(*Bk) = dQ_dBk * phi;

        // -------- CHAIN RULE COMPUTATION for dv_dtau_p --------

        const auto dphi_dtau_p          = -pow(phi, 2.0) * _s * tau_1_safe * exp(-_s * tau_tilda) / pow(_tau_p, 2.0);
        const auto dtau_th_dtau_p       = dphi_dtau_p * macaulay(tau_1_safe) + eps - eps * (_tau_p * dphi_dtau_p + phi);
        const auto dtau_ratio_dtau_p    = dtau_th_dtau_p / _tau_p - tau_ratio / _tau_p;
        const auto dD_G_dtau_p          = -_D_H * _q * pow(inner_safe, _q - 1.0) * _p * pow(tau_ratio, _p - 1.0) * dtau_ratio_dtau_p;
        const auto dv_kp_dtau_p         = -K * mcl_eff / (_k_B * _T()) * dD_G_dtau_p * exp_val;
        const auto dQ_dtau_p            = (v_drag * dv_kp_dtau_p * (v_kp + v_drag) - v_kp * v_drag * dv_kp_dtau_p) / pow(v_kp + v_drag + 1.0e-30, 2.0);

        if (const auto * const tau_p = nl_param("tau_p"))
            _v.d(*tau_p) = Q * dphi_dtau_p + dQ_dtau_p * phi;

        // -------- CHAIN RULE COMPUTATION for dv_dT_0 --------

        const auto dD_G_dT_0            = _D_H * _T() / pow(_T_0, 2.0);
        const auto dv_kp_dT_0           = -K * mcl_eff / (_k_B * _T()) * dD_G_dT_0 * exp_val;
        const auto dQ_dT_0              = (v_drag * dv_kp_dT_0 * (v_kp + v_drag) - v_kp * v_drag * dv_kp_dT_0) / pow(v_kp + v_drag + 1.0e-30, 2.0);

        if (const auto * const T_0 = nl_param("T_0"))
            _v.d(*T_0) = dQ_dT_0 * phi;

        // -------- CHAIN RULE COMPUTATION for dv_dp --------

        const auto dtau_ratiop_dp       = pow(tau_ratio, _p) * log(clamp(tau_ratio, 1.0e-30, 1.0));
        const auto dD_G_dp              = -_D_H * _q * pow(inner_safe, _q - 1.0) * dtau_ratiop_dp;
        const auto dv_kp_dp             = -K * mcl_eff / (_k_B * _T()) *dD_G_dp * exp_val;
        const auto dQ_dp                = (dv_kp_dp * v_drag * (v_kp + v_drag) - v_kp * v_drag * dv_kp_dp) / pow(v_kp + v_drag + 1.0e-30, 2.0);

        if (const auto * const p = nl_param("p"))
            _v.d(*p) = dQ_dp * phi;

        // -------- CHAIN RULE COMPUTATION for dv_dq --------

        const auto dD_G_dq              = _D_H * pow(inner_safe, _q) * log(inner_safe);
        const auto dv_kp_dq             = -K * mcl_eff / (_k_B * _T()) * dD_G_dq * exp_val;
        const auto dQ_dq                = (v_drag * dv_kp_dq * (v_kp + v_drag) - v_kp * v_drag * dv_kp_dq) / pow(v_kp + v_drag + 1.0e-30, 2.0);

        if (const auto * const q = nl_param("q"))
            _v.d(*q) = dQ_dq * phi;

        // -------- CHAIN RULE COMPUTATION for dv_dD_H --------

        const auto dD_G_dD_H            = pow(inner_safe, _q) - _T()/_T_0;
        const auto dv_kp_dD_H           = -K * mcl_eff / (_k_B * _T()) * dD_G_dD_H * exp_val;
        const auto dQ_dD_H              = (v_drag * dv_kp_dD_H * (v_kp + v_drag) - v_kp * v_drag * dv_kp_dD_H) / pow(v_kp + v_drag + 1.0e-30, 2.0);

        if (const auto * const D_H = nl_param("H_0"))
            _v.d(*D_H) = dQ_dD_H * phi;

        // -------- CHAIN RULE COMPUTATION for dv_ds --------

        const auto dphi_ds              = pow(phi, 2.0) * tau_tilda * exp(-_s * tau_tilda);
        const auto dtau_ratio_ds        = macaulay(tau_1_safe) / _tau_p * dphi_ds - eps * dphi_ds;
        const auto dD_G_ds              = -_D_H * _q * pow(inner_safe, _q - 1.0) * _p * pow(tau_ratio, _p - 1.0) * dtau_ratio_ds;
        const auto dv_kp_ds             = -K * mcl_eff / (_k_B * _T()) * dD_G_ds * exp_val;
        const auto dQ_ds                = (v_drag * dv_kp_ds * (v_kp + v_drag) - v_kp * v_drag * dv_kp_ds) / pow(v_kp + v_drag + 1.0e-30, 2.0);

        
        if (const auto * const s = nl_param("s"))
            _v.d(*s) = Q * dphi_ds + dQ_ds * phi;
    }
}
}
