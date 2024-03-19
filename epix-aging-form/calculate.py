import numpy as np
from logger import logger


def calculate_score(factors, weights):
    # Ensure factors and weights are numpy arrays for vectorized operations
    factors = np.array(factors)
    factors = factors.astype(float) / 5
    logger.info(f"Factors: {factors}")

    weights = np.array(weights)
    logger.info(f"Weights: {weights}")

    # Compute the weighted sum
    S = np.dot(weights, factors)
    logger.info(f"Weighted sum: {S}")

    # Apply the nonlinear transformation
    score = np.tanh(S)
    logger.info(f"Nonlinear transformation: {score}")

    # Apply the scaling factor centered at 0 with range 0-48
    score = (score + 1) * 24
    logger.info(f"Scaled: {score}")

    # Add a very small linear term to the score
    if S > 0:
        score += 3 * S
    print(f"Linear term: {score}")

    if score < 0:
        score = 0

    # Round the score to the nearest integer
    score = int(np.round(score))

    return score


def calculate_bmi(weight, height):
    bmi = weight / (height / 100) ** 2
    if bmi < 18.5:
        # Underweight
        return 2
    elif 18.5 <= bmi < 24.9:
        # Normal weight
        return -2
    elif 25 <= bmi < 29.9:
        # Overweight
        return 2
    else:
        # Obese
        return 4