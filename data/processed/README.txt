Processed datasets are generated here by running the Jupyter notebooks.

Files created by notebooks:
  X_train.npy, y_train.npy   — Scaled training arrays
  X_test.npy,  y_test.npy    — Scaled test arrays
  X_train_raw.npy             — Unscaled (for XGBoost)
  X_test_raw.npy              — Unscaled (for XGBoost)
  feature_columns.json        — Ordered list of feature names
  eda_*.png                   — EDA visualisation images
  model_comparison.png        — Training comparison chart

These files are excluded from Git (.gitignore).
Run notebook 02_Preprocessing.ipynb to regenerate them.
