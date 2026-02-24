#include "neml2/models/solid_mechanics/crystal_plasticity/ThermallyActivatedDislocationMobility.h"
#include "neml2/tensors/Scalar.h"
#include "neml2/tensors/functions/pow.h"
#include "neml2/tensors/functions/exp.h"
#include "neml2/tensors/functions/macaulay.h"
#include "neml2/tensors/functions/heaviside.h"
#include "neml2/tensors/functions/log.h"

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
    _h(declare_parameter<Scalar>("h", "h", true)),
    _L(declare_parameter<Scalar>("L", "L", true)),
    _b(declare_parameter<Scalar>("b", "b", true)),
    _a(declare_parameter<Scalar>("a", "a", true)),
    _Bk(declare_parameter<Scalar>("Bk", "Bk", true)),
    _tau_p(declare_parameter<Scalar>("pierls_stress", "pierls_stress", true)),
    _T_0(declare_parameter<Scalar>("T_0", "T_0", true)),
    _p(declare_parameter<Scalar>("p", "p", true)),
    _q(declare_parameter<Scalar>("q", "q", true)),
    _T(declare_buffer<Scalar>("T_ref", "reference_temperature")),
    _k_B(declare_buffer<Scalar>("k_B", "k_B")),
    _D_H(declare_buffer<Scalar>("activation_energy", "activation_energy")),
    _v(declare_output_variable<Scalar>("v_disl"))
{
}
void
ThermallyActivatedDislocationMobility::set_value(bool out, bool dout_din, bool /*d2out_din2*/)
{
    if (out)
        _v = (_h * _L * _b) / (pow(_a, 2.0) * _Bk) * macaulay(_tau_eff()) * exp(-_D_H / (_k_B * _T) * (pow((1 - (pow(macaulay(_tau_eff() - _tau_a()) ,_p))/pow(_tau_p, _p)), _q) - _T/_T_0));

    if (dout_din)
    {
        if (_tau_eff.is_dependent())
        {
            _v.d(_tau_eff) = Scalar((_h * _L * _b) / (pow(_a, 2) * _Bk) * heaviside(_tau_eff()) * exp(-_D_H / (_k_B * _T) * (pow((1 - (pow(macaulay(_tau_eff() - _tau_a()) ,_p))/pow(_tau_p, _p)), _q) - _T/_T_0))
                            + (_h * _L * _b) / (pow(_a, 2) * _Bk) * macaulay(_tau_eff()) * _D_H / (_k_B * _T) * _q * pow((1 - (pow(macaulay(_tau_eff() - _tau_a()) ,_p))/pow(_tau_p, _p)), _q-1) * pow(_tau_p, -_p)
                            * _p * pow(macaulay(_tau_eff() - _tau_a()), _p-1) * heaviside(_tau_eff() - _tau_a()) * exp(-_D_H / (_k_B * _T) * (pow((1 - (pow(macaulay(_tau_eff() - _tau_a()) ,_p))/pow(_tau_p, _p)), _q) - _T/_T_0)));
        }

        if (_tau_a.is_dependent())
        {
            _v.d(_tau_a) = Scalar(-(_h * _L * _b) / (pow(_a, 2) * _Bk) * macaulay(_tau_eff()) * _D_H / (_k_B * _T) * _q * pow((1 - (pow(macaulay(_tau_eff() - _tau_a()) ,_p))/pow(_tau_p, _p)), _q-1) * pow(_tau_p, -_p)
                            * _p * pow(macaulay(_tau_eff() - _tau_a()), _p-1) * heaviside(_tau_eff() - _tau_a()) * exp(-_D_H / (_k_B * _T) * (pow((1 - (pow(macaulay(_tau_eff() - _tau_a()) ,_p))/pow(_tau_p, _p)), _q) - _T/_T_0)));
        }

        if (const auto * const h = nl_param("h"))
            _v.d(*h) = Scalar((_L * _b) / (pow(_a, 2) * _Bk) * macaulay(_tau_eff()) * exp(-_D_H / (_k_B * _T) * (pow((1 - (pow(macaulay(_tau_eff() - _tau_a()) ,_p))/pow(_tau_p, _p)), _q) - _T/_T_0)));

        if (const auto * const L = nl_param("L"))
            _v.d(*L) = Scalar((_h * _b) / (pow(_a, 2) * _Bk) * macaulay(_tau_eff()) * exp(-_D_H / (_k_B * _T) * (pow((1 - (pow(macaulay(_tau_eff() - _tau_a()) ,_p))/pow(_tau_p, _p)), _q) - _T/_T_0)));
        
        if (const auto * const b = nl_param("b"))
            _v.d(*b) = Scalar((_h * _L) / (pow(_a, 2) * _Bk) * macaulay(_tau_eff()) * exp(-_D_H / (_k_B * _T) * (pow((1 - (pow(macaulay(_tau_eff() - _tau_a()) ,_p))/pow(_tau_p, _p)), _q) - _T/_T_0)));
        
        if (const auto * const a = nl_param("a"))
            _v.d(*a) = Scalar((-2 * _h * _L * _b) / (pow(_a, 3) * _Bk) * macaulay(_tau_eff()) * exp(-_D_H / (_k_B * _T) * (pow((1 - (pow(macaulay(_tau_eff() - _tau_a()) ,_p))/pow(_tau_p, _p)), _q) - _T/_T_0)));
        
        if (const auto * const Bk = nl_param("Bk"))
            _v.d(*Bk) = Scalar(-(_h * _L * _b) / (pow(_a, 2) * pow(_Bk, 2)) * macaulay(_tau_eff()) * exp(-_D_H / (_k_B * _T) * (pow((1 - (pow(macaulay(_tau_eff() - _tau_a()) ,_p))/pow(_tau_p, _p)), _q) - _T/_T_0)));
        
        if (const auto * const tau_p = nl_param("pierls_stress"))
            _v.d(*tau_p) = Scalar(-(_h * _L * _b) / (pow(_a, 2) * _Bk) * macaulay(_tau_eff()) * _D_H / (_k_B * _T) * _q * pow((1 - (pow(macaulay(_tau_eff() - _tau_a()) ,_p))/pow(_tau_p, _p)), _q-1)
            * pow(macaulay(_tau_eff() - _tau_a()) , _p) * _p * pow(_tau_p, -_p-1) * exp(-_D_H / (_k_B * _T) * (pow((1 - (pow(macaulay(_tau_eff() - _tau_a()) ,_p))/pow(_tau_p, _p)), _q) - _T/_T_0)));

        if (const auto * const T_0 = nl_param("T_0"))
            _v.d(*T_0) = Scalar(-(_h * _L * _b) / (pow(_a, 2) * _Bk) * macaulay(_tau_eff()) * _D_H / (_k_B * _T) * _T / pow(_T_0, 2.0) 
            * exp(-_D_H / (_k_B * _T) * (pow((1 - (pow(macaulay(_tau_eff() - _tau_a()) ,_p))/pow(_tau_p, _p)), _q) - _T/_T_0)));

        if (const auto * const p = nl_param("p"))
            _v.d(*p) = Scalar((_h * _L * _b) / (pow(_a, 2) * _Bk) * macaulay(_tau_eff()) * _D_H / (_k_B * _T) * _q * pow((1 - (pow(macaulay(_tau_eff() - _tau_a()) ,_p))/pow(_tau_p, _p)), _q-1) 
            * log((macaulay(_tau_eff() - _tau_a()) / _tau_p)) * pow((macaulay(_tau_eff() - _tau_a()) / _tau_p),_p) 
            * exp(-_D_H / (_k_B * _T) * (pow((1 - (pow(macaulay(_tau_eff() - _tau_a()) ,_p))/pow(_tau_p, _p)), _q) - _T/_T_0)));
        
        if (const auto * const q = nl_param("q"))
            _v.d(*q) = Scalar(-(_h * _L * _b) / (pow(_a, 2) * _Bk) * macaulay(_tau_eff()) * _D_H / (_k_B * _T) * pow((1 - (pow(macaulay(_tau_eff() - _tau_a()) ,_p))/pow(_tau_p, _p)), _q)
            * log(1 - pow((macaulay(_tau_eff() - _tau_a()) / _tau_p), _p)) * exp(-_D_H / (_k_B * _T) * (pow((1 - (pow(macaulay(_tau_eff() - _tau_a()) ,_p))/pow(_tau_p, _p)), _q) - _T/_T_0)));
    }
}
}
