#ifndef libswervedrive_estimator_h
#define libswervedrive_estimator_h

#include <vector>

#include <Eigen/Dense>

#include "libswervedrive/chassis.h"

namespace swervedrive {

class Estimator {
public:
  Estimator(Chassis chassis);
  Estimator(Chassis chassis, Epsilon init);
  ~Estimator() = default;

  // compute the derivatives of the constraining surface in the space of all possible wheel
  // configurations at lambda
  // returns (S_u, S_v, S_w), the vectors containing the derivatives of each steering angle
  // with respect to u, v, and w respectively
  // null_axis is the index of the axis that the derivatives are not parametrised in terms of
  std::vector<Eigen::Vector3d> compute_derivatives(Lambda lambda, int& null_axis);
  Lambda estimate_lambda();
  int handle_singularities(Lambda lambda);
  Eigen::VectorXd S(Lambda lambda);
  std::vector<Lambda> select_starting_points(Eigen::VectorXd q);
  Eigen::Vector3d solve(Eigen::Vector3d derivatives, Eigen::VectorXd q, Lambda lambda);
  Lambda update_parameters(Lambda lambda, Eigen::Vector3d deltas, Eigen::VectorXd q);

protected:
  Chassis chassis_;
  Epsilon epsilon_;

  // threshold when we assume the algorithm has converged to the correct icr based on how much
  // lambda has moved between sucessive iterations
  const double eta_lambda = 1e-4;
  // threshold below which a starting point for iterative icr iteration is selected based on the norm
  // between the measured wheel positions and the wheel positions obtained from that starting point
  const double eta_delta = 1e-2;
  // minimum size of the free parameters delta_m and delta_m to avoid infinate recursion in the line
  // search for the next iteration of the position of lambda
  const double min_delta_size = 1e-2;
  // maximum iterations allowed for the iterative icr estimation algorithm to converge on one point
  const double max_iter = 50;
  // how close a point must be to be considered to be 'on a structural singularity'
  const double singularity_tolerance = 1e-3;
};
}

#endif
