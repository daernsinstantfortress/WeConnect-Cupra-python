def addBearerAuthHeader(token, headers=None):
    headers = headers or {}
    headers['Authorization'] = f'Bearer {token}'
    headers["app-market"] = "android"
    headers["app-brand"] = "cupra"
    headers["app-version"] = "2.15.0"
    headers["origin"] = "app"
    return headers
