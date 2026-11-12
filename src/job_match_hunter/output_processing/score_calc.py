import numpy as np

def calculate_match_percentage(
    jd_requirements: list[str],
    met_requirements: list[str],
) -> float:
    """
    """

    match_percentage =  len(met_requirements) / len(jd_requirements)

    return np.round(match_percentage*100, 1)