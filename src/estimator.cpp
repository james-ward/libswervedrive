#include "libswervedrive/estimator.h"


namespace swervedrive {
Estimator::Estimator(const Chassis& chassis, Epsilon init, double eta_lambda,
  double eta_delta,
  double min_delta_line_search,
  double max_iter_lambda,
  double singularity_tolerance) :
  chassis_(chassis), epsilon_(init),
  eta_lambda_(eta_lambda),
  eta_delta_(eta_delta),
  min_delta_line_search_(min_delta_line_search),
  max_iter_lambda_(max_iter_lambda),
  singularity_tolerance_(singularity_tolerance)
{};

Eigen::VectorXd Estimator::lambda_to_betas(Lambda lambda) {
  auto y = (chassis_.a_orth.transpose() * lambda);
  auto x = ((chassis_.a - chassis_.l_v).transpose() * lambda);
  // the steering angles array to be returned
  Eigen::VectorXd S(chassis_.n);
  for (int idx=0; idx < chassis_.n; ++idx) {
    if (abs(x[idx]) < numerical_zero_thresh_) {
      S[idx] = M_PI / 2;
    } else {
      S[idx] = atan(y[idx]/x[idx]);
    }
  }
  return S;
}

}
