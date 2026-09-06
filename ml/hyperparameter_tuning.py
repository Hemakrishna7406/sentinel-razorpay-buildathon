"""
Sentinel — Advanced Hyperparameter Optimization

Implements comprehensive hyperparameter tuning for XGBoost using:
- Grid Search for exhaustive search
- Random Search for exploration
- Bayesian Optimization for efficient optimization (optional, requires optuna)

Maintains precision >= 95% constraint throughout optimization.
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import xgboost as xgb
from sklearn.metrics import average_precision_score, precision_recall_curve

logger = logging.getLogger(__name__)


class HyperparameterTuner:
    """
    Advanced hyperparameter tuning for XGBoost with precision constraints.
    """

    def __init__(
        self,
        dtrain: xgb.DMatrix,
        dval: xgb.DMatrix,
        scale_pos_weight: float,
        min_precision: float = 0.95,
        min_recall: float = 0.85,
        seed: int = 42,
    ):
        """
        Initialize the tuner.

        Args:
            dtrain: Training DMatrix
            dval: Validation DMatrix
            scale_pos_weight: Class imbalance weight
            min_precision: Minimum acceptable precision (default 95%)
            min_recall: Minimum acceptable recall (default 85%)
            seed: Random seed
        """
        self.dtrain = dtrain
        self.dval = dval
        self.scale_pos_weight = scale_pos_weight
        self.min_precision = min_precision
        self.min_recall = min_recall
        self.seed = seed

        self.best_params = None
        self.best_score = -1.0
        self.best_model = None

        self.trial_history: List[Dict[str, Any]] = []

    def _train_and_evaluate(
        self, params: Dict[str, Any], num_boost_round: int = 200, early_stopping_rounds: int = 20
    ) -> Tuple[xgb.Booster, float, float, float]:
        """
        Train model with given params and evaluate.

        Returns:
            Tuple of (model, precision, recall, aucpr)
        """
        full_params = {
            "objective": "binary:logistic",
            "eval_metric": "aucpr",
            "scale_pos_weight": self.scale_pos_weight,
            "tree_method": "hist",
            "seed": self.seed,
            **params,
        }

        evals = [(self.dval, "val")]
        model = xgb.train(
            params=full_params,
            dtrain=self.dtrain,
            num_boost_round=num_boost_round,
            evals=evals,
            early_stopping_rounds=early_stopping_rounds,
            verbose_eval=False,
        )

        # Evaluate on validation
        val_preds = model.predict(self.dval)
        val_labels = self.dval.get_label()

        # Find optimal threshold for target precision
        precisions, recalls, thresholds = precision_recall_curve(val_labels, val_preds)

        # Find thresholds where precision >= min_precision
        valid_idx = np.where(precisions[:-1] >= self.min_precision)[0]

        if len(valid_idx) == 0:
            # No threshold meets precision constraint
            return model, 0.0, 0.0, 0.0

        # Among valid thresholds, pick one with best recall
        best_idx = valid_idx[np.argmax(recalls[valid_idx])]
        threshold = thresholds[best_idx]
        precision = precisions[best_idx]
        recall = recalls[best_idx]

        # Calculate AUCPR
        aucpr = average_precision_score(val_labels, val_preds)

        return model, float(precision), float(recall), float(aucpr)

    def grid_search(self, param_grid: Optional[Dict[str, List[Any]]] = None) -> Tuple[xgb.Booster, Dict[str, Any]]:
        """
        Perform grid search over hyperparameter space.

        Args:
            param_grid: Dictionary mapping param names to lists of values to try.
                       If None, uses default comprehensive grid.

        Returns:
            Tuple of (best_model, best_params)
        """
        if param_grid is None:
            param_grid = {
                "max_depth": [3, 4, 5, 6],
                "learning_rate": [0.01, 0.05, 0.1],
                "min_child_weight": [1, 3, 5],
                "subsample": [0.8, 0.9, 1.0],
                "colsample_bytree": [0.8, 0.9, 1.0],
                "gamma": [0, 0.1, 0.2],
            }

        logger.info(f"Starting grid search with {self._count_combinations(param_grid)} combinations")

        best_score = -1.0
        best_params = None
        best_model = None

        # Generate all combinations
        param_combinations = self._generate_combinations(param_grid)

        for i, params in enumerate(param_combinations):
            logger.info(f"Trial {i+1}/{len(param_combinations)}: {params}")

            model, precision, recall, aucpr = self._train_and_evaluate(params)

            # Track trial
            trial = {
                "params": params.copy(),
                "precision": precision,
                "recall": recall,
                "aucpr": aucpr,
                "meets_constraints": precision >= self.min_precision and recall >= self.min_recall,
            }
            self.trial_history.append(trial)

            # Check if meets constraints
            if precision >= self.min_precision and recall >= self.min_recall:
                # Use AUCPR as optimization metric
                if aucpr > best_score:
                    best_score = aucpr
                    best_params = params.copy()
                    best_model = model
                    logger.info(
                        f"New best model: AUCPR={aucpr:.4f}, " f"Precision={precision:.4f}, Recall={recall:.4f}"
                    )

        if best_model is None:
            logger.warning("No configuration met precision/recall constraints. Using best by AUCPR.")
            # Fallback: pick best AUCPR regardless of constraints
            best_trial = max(self.trial_history, key=lambda x: x["aucpr"])
            best_params = best_trial["params"]
            best_model, _, _, _ = self._train_and_evaluate(best_params)

        self.best_model = best_model
        self.best_params = best_params
        self.best_score = best_score

        logger.info(f"Grid search complete. Best AUCPR: {best_score:.4f}")
        return best_model, best_params

    def random_search(
        self, param_distributions: Optional[Dict[str, Tuple[Any, Any]]] = None, n_iter: int = 50
    ) -> Tuple[xgb.Booster, Dict[str, Any]]:
        """
        Perform random search over hyperparameter space.

        Args:
            param_distributions: Dict mapping param names to (min, max) tuples
            n_iter: Number of random configurations to try

        Returns:
            Tuple of (best_model, best_params)
        """
        if param_distributions is None:
            param_distributions = {
                "max_depth": (3, 10),
                "learning_rate": (0.01, 0.3),
                "min_child_weight": (1, 10),
                "subsample": (0.6, 1.0),
                "colsample_bytree": (0.6, 1.0),
                "gamma": (0, 0.5),
            }

        logger.info(f"Starting random search with {n_iter} iterations")

        best_score = -1.0
        best_params = None
        best_model = None

        for i in range(n_iter):
            # Sample random parameters
            params = {}
            for param_name, (min_val, max_val) in param_distributions.items():
                if param_name == "max_depth":
                    params[param_name] = np.random.randint(min_val, max_val + 1)
                elif param_name == "min_child_weight":
                    params[param_name] = np.random.randint(min_val, max_val + 1)
                else:
                    params[param_name] = np.random.uniform(min_val, max_val)

            logger.info(f"Trial {i+1}/{n_iter}: {params}")

            model, precision, recall, aucpr = self._train_and_evaluate(params)

            # Track trial
            trial = {
                "params": params.copy(),
                "precision": precision,
                "recall": recall,
                "aucpr": aucpr,
                "meets_constraints": precision >= self.min_precision and recall >= self.min_recall,
            }
            self.trial_history.append(trial)

            # Check if meets constraints
            if precision >= self.min_precision and recall >= self.min_recall:
                if aucpr > best_score:
                    best_score = aucpr
                    best_params = params.copy()
                    best_model = model
                    logger.info(
                        f"New best model: AUCPR={aucpr:.4f}, " f"Precision={precision:.4f}, Recall={recall:.4f}"
                    )

        if best_model is None:
            logger.warning("No configuration met precision/recall constraints. Using best by AUCPR.")
            best_trial = max(self.trial_history, key=lambda x: x["aucpr"])
            best_params = best_trial["params"]
            best_model, _, _, _ = self._train_and_evaluate(best_params)

        self.best_model = best_model
        self.best_params = best_params
        self.best_score = best_score

        logger.info(f"Random search complete. Best AUCPR: {best_score:.4f}")
        return best_model, best_params

    def bayesian_optimization(self, n_trials: int = 50) -> Tuple[xgb.Booster, Dict[str, Any]]:
        """
        Perform Bayesian optimization using Optuna.

        Args:
            n_trials: Number of trials

        Returns:
            Tuple of (best_model, best_params)
        """
        try:
            import optuna
            from optuna.samplers import TPESampler
        except ImportError:
            logger.error("Optuna not installed. Install with: pip install optuna")
            logger.info("Falling back to random search")
            return self.random_search(n_iter=n_trials)

        logger.info(f"Starting Bayesian optimization with {n_trials} trials")

        def objective(trial):
            params = {
                "max_depth": trial.suggest_int("max_depth", 3, 10),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
                "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                "gamma": trial.suggest_float("gamma", 0, 0.5),
            }

            model, precision, recall, aucpr = self._train_and_evaluate(params)

            # Track trial
            trial_record = {
                "params": params.copy(),
                "precision": precision,
                "recall": recall,
                "aucpr": aucpr,
                "meets_constraints": precision >= self.min_precision and recall >= self.min_recall,
            }
            self.trial_history.append(trial_record)

            # Penalize if constraints not met
            if precision < self.min_precision or recall < self.min_recall:
                return -1.0  # Invalid configuration

            return aucpr

        study = optuna.create_study(direction="maximize", sampler=TPESampler(seed=self.seed))

        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

        # Get best params and retrain
        best_params = study.best_params
        best_model, _, _, best_score = self._train_and_evaluate(best_params)

        self.best_model = best_model
        self.best_params = best_params
        self.best_score = best_score

        logger.info(f"Bayesian optimization complete. Best AUCPR: {best_score:.4f}")
        logger.info(f"Best params: {best_params}")

        return best_model, best_params

    def _generate_combinations(self, param_grid: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
        """Generate all parameter combinations from grid."""
        keys = list(param_grid.keys())
        values = list(param_grid.values())

        combinations = []

        def _recurse(index, current_params):
            if index == len(keys):
                combinations.append(current_params.copy())
                return

            key = keys[index]
            for value in values[index]:
                current_params[key] = value
                _recurse(index + 1, current_params)

        _recurse(0, {})
        return combinations

    def _count_combinations(self, param_grid: Dict[str, List[Any]]) -> int:
        """Count total combinations in grid."""
        count = 1
        for values in param_grid.values():
            count *= len(values)
        return count

    def get_tuning_report(self) -> Dict[str, Any]:
        """Get comprehensive tuning report."""
        if not self.trial_history:
            return {"error": "No trials completed"}

        valid_trials = [t for t in self.trial_history if t["meets_constraints"]]

        return {
            "total_trials": len(self.trial_history),
            "valid_trials": len(valid_trials),
            "best_aucpr": self.best_score,
            "best_params": self.best_params,
            "avg_precision": np.mean([t["precision"] for t in self.trial_history]),
            "avg_recall": np.mean([t["recall"] for t in self.trial_history]),
            "top_5_trials": sorted(self.trial_history, key=lambda x: x["aucpr"], reverse=True)[:5],
        }
