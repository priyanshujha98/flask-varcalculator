from datetime import date, timedelta
from math import sqrt
import numpy as np
from scipy import stats
import json

def weightify(values):
  total_weight = sum(values)
  if total_weight == 0:
    return ([0]*len(values), total_weight)
  weights = [v/total_weight for v in values]
  return (weights, total_weight)

with open("data.json") as f:
  raw_data = json.loads(f.read())

def get_prices(c1, c2):
  return list(map(lambda row: row['rates'][c2]/row['rates'][c1], raw_data))

def get_zscore(confidence):
  return stats.norm.ppf(confidence)

def get_n_day_returns(c1, c2, n):
  rates = get_prices(c1, c2)
  diffs = [(rates[i+n]-rates[i])/rates[i] for i in range(0, len(rates)-n, n)]
  return diffs

def get_n_day_portfolio_returns(pairs, n):
  weights, _ = weightify([p[2] for p in pairs])
  pairs_returns = [
    (np.array(get_n_day_returns(p[0], p[1], n))).tolist() for p in pairs
  ]
  return [sum((np.array(r)*w).tolist()) for r, w in zip(pairs_returns, weights)]

# def get_var(returns, confidence):
#   sorted_returns = sorted(returns)
#   index = int(len(sorted_returns)*(1-confidence))+1
#   return sorted_returns[index]

def get_var(returns, confidence):
  variance = np.var(returns)
  stddev = sqrt(variance)
  zscore = get_zscore(confidence)
  return zscore * stddev

def get_n_day_individual_vars(pairs, n, confidence):
  return list(map(
    lambda p: get_var(get_n_day_returns(p[0], p[1], n), confidence)*p[2],
    pairs
  ))

def get_covariance_matrix(pairs, n):
  returns = np.array([get_n_day_returns(p[0], p[1], n) for p in pairs])
  return np.cov(returns)

def get_portfolio_variance(pairs, n):
  weights, _ = weightify([p[2] for p in pairs])
  cov_matrix = get_covariance_matrix(pairs, n)
  return np.dot(np.array(weights), np.dot(cov_matrix, np.array(weights).T))

def get_portfolio_var(pairs, n, confidence):
  if len(pairs) == 1:
    return abs(get_n_day_individual_vars(pairs, n, confidence)[0])
  
  variance = get_portfolio_variance(pairs, n)
  stddev = sqrt(variance)
  zscore = get_zscore(confidence)
  W = sum([p[2] for p in pairs])
  return W*zscore*stddev

# def get_portfolio_var(pairs, n, confidence):
#   return abs(get_var(get_n_day_portfolio_returns(pairs, n), confidence))*sum([p[2] for p in pairs])

def get_betas(pairs, n):
  variance = get_portfolio_variance(pairs, n)
  weights, _ = weightify([p[2] for p in pairs])
  cov_matrix = get_covariance_matrix(pairs, n)
  covariances = np.dot(cov_matrix, np.array(weights).T).tolist()
  return [ c/variance for c in covariances ]

def get_n_day_component_vars(pairs, n, confidence):
  if len(pairs) == 1:
    return [abs(x) for x in get_n_day_individual_vars(pairs, n, confidence)]
  betas = get_betas(pairs, n)
  portfolio_var = get_portfolio_var(pairs, n, confidence)
  weights, _ = weightify([p[2] for p in pairs ])
  return [ portfolio_var * b * w for b,w in zip(betas, weights) ]

# def get_portfolio_var(pairs, n, confidence):
#   return get_var(
#     get_n_day_portfolio_returns(pairs, n), 
#     confidence
#   )

# def get_n_day_component_vars(pairs, n, confidence):
#   portfolio_var = get_portfolio_var(pairs, n, confidence)*sum([p[2] for p in pairs])

#   absent_pairs = [
#     [
#       [
#         pairs[j][0], pairs[j][1], (0 if i == j else pairs[j][2]) 
#       ] for j in range(len(pairs))
#     ] for i in range(len(pairs))
#   ]

#   return [
#     portfolio_var - (
#       get_portfolio_var(absent_pairs[i], n, confidence) *
#       sum([p[2] for p in absent_pairs[i]])
#     )
#     for i in range(len(pairs))
#   ]

