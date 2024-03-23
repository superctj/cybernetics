from sklearn.linear_model import Lasso
from sklearn.feature_selection import SelectFromModel
import numpy as np

class LassoFeatureSelector:
    def __init__(self,X,y,k):
        self.X = X
        self.y = y
        self.k = k
        self.model = None
        self.update_model()

    def update_model(self):
        self.model = Lasso()
        self.model.fit(self.X, self.y)

    def get_feature(self):
        if self.model is None:
            raise ValueError("Use Update_model")
        
        selector = SelectFromModel(self.model, max_features=self.k)
        selector.fit(self.X, self.y)
        selected_indices = selector.get_support(indices=True)
        return selected_indices

