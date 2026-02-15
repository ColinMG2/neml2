#pragma once
#include "neml2/models/Model.h"

namespace neml2
{
class Scalar;

class OrowanEquation : public Model
{
public:
    static OptionSet expected_options();

    OrowanEquation(const OptionSet & options);

protected:
    void set_value(bool out, bool dout_din, bool d2out_din2) override;
    
    // dislocation density (input)
    const Variable<Scalar> & _rho_m;
    // dislocation velocity (input)
    const Variable<Scalar> & _v_disl;
    // Burger's Vector (parameter)
    const Scalar & _b;
    // plastic flow rate (output)
    Variable<Scalar> & _gamma_dot;
};
}