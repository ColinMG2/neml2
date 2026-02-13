#pragma once
#include "neml2/models/Model.h"

namespace neml2
{
class Scalar;

class KocksMeckingDislocationDensity : public Model
{
public:
    static OptionSet expected_options();

    KocksMeckingDislocationDensity(const OptionSet & options);

protected:
    void set_value(bool out, bool dout_din, bool d2out_din2) override;

    // Plastic Flow rate
    const Variable<Scalar> & _gamma_dot;
    // const parameter k1
    const Scalar & _k1;
    // const parameter k2
    const Scalar & _k2;
    // dislocation density
    const Scalar & _rho_m;
    // length of pathway for dislocation, L
    const Scalar & _L;
    // output: dislocation density rate
    Variable<Scalar> & _rho_m_dot;
};
}
