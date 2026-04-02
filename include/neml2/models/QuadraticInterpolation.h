#pragma once
#include "neml2/models/Model.h"

namespace neml2
{
template <typename T>
class QuadraticInterpolation : public Model
{
public:
    static OptionSet expected_options();

    QuadraticInterpolation(const OptionSet & options);

protected:
    void set_value(bool out, bool dout_din, bool d2out_din2) override;

    // coefficient of x^2
    const T & _a;

    // coefficient of x
    const T & _b;

    // constant offset term
    const T & _c;

    // Scalar argument (the interpolation input x)
    const Variable<Scalar> & _x;

    // The interpolated output
    Variable<T> & _y;
};
}