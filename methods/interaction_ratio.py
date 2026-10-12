import numpy as np


def interaction_ratio(assignment: np.ndarray, flows: np.ndarray) -> float:
    """Sum of flows within districts divided by the sum of flows between districts.

    `assignment[i]` is the district of the CBG in row/column i of `flows`, and
    `flows[o, d]` is the number of trips from CBG o to CBG d. Trips that start and
    end in the same CBG count as within-district.
    """
    districts = np.unique(assignment)
    membership = (assignment[:, None] == districts[None, :]).astype(flows.dtype)
    within = np.trace(membership.T @ flows @ membership)
    return within / (flows.sum() - within)
