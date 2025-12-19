## Backend Codebase

This is the backend for CloudFuse

This codebase has 3 major components

1. **p7**
  All API interacting with frontend and various other helper functions
2. **repository**
  Definitions of Database tables using Django ORM Models and all functions interacting with these models. Plus it also contains Index and Ranking logic
3. **test**
  Containing all test for the codebase

--- 

## Installation

Note: This codebase should not be installed by it-self. Full Installation described in https://github.com/AAU-SW-P7/P7-Root

---

## Specific Commands for the Backend

```python
pylint .
```
```python
pytest --ignore=test/locust_test
```

