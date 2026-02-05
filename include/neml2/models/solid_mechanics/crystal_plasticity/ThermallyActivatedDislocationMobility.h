#pragma once
#include "neml2/models/Model.h"

namespace neml2
{
class Scalar;

class ThermallyActivatedDislocationMobility : public Model
{
public:
    static OptionSet expected_options();

    ThermallyActivatedDislocationMobility(const OptionSet & options);

protected:
    void set_value(bool out, bool dout_din, bool d2out_din2) override;

    // Input variables (effective shear and athermal shear)
    const Variable<Scalar> & _tau_eff;
    const Variable<Scalar> & _tau_a;

    // Parameters for training
    const Scalar & _h;
    const Scalar & _L;
    const Scalar & _b;
    const Scalar & _a;
    const Scalar & _Bk;
    const Scalar & _tau_p;
    const Scalar & _T_0;
    const Scalar & _p;
    const Scalar & _q;

    // Buffers
    const Scalar & _T;
    const Scalar & _k_B;
    const Scalar & _D_H;

    // Output variable (dislocation velocity)
    Variable<Scalar> & _v;

};
}