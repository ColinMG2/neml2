#pragma once
#include "neml2/models/Model.h"

namespace neml2
{
class SR2;
class Scalar;
class NormalToShearStress : public Model
{
public:
    static OptionSet expected_options();
    NormalToShearStress(const OptionSet & options);

protected:
    void set_value(bool out, bool dout_din, bool d2out_din2) override;

    const Variable<Scalar> & _S;
    Variable<Scalar> & _tau;
    const Scalar & _m;

};
}