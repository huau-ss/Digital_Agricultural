# 查看产品专用模型效果
import joblib
import os

model_dir = r'E:\PyCharm 2025.2.1.1\pythonProjects\Digital Agriculture\backend\models\lstm_per_product'
registry_path = os.path.join(model_dir, 'model_registry.pkl')

# 加载索引
registry = joblib.load(registry_path)

print("=" * 80)
print("Per-Product LSTM Model Results (Sorted by MAPE)")
print("=" * 80)
print(f"{'ID':<6} {'Name':<20} {'Data':<6} {'RMSE':<10} {'MAE':<10} {'R2':<10} {'MAPE':<10}")
print("-" * 80)

# 按MAPE排序
sorted_results = sorted(registry.items(), key=lambda x: x[1]['mape'])

for prod_id, info in sorted_results:
    print(f"{prod_id:<8} {info['product_name']:<20} {info['data_points']:<8} "
          f"{info['rmse']:<10.4f} {info['mae']:<10.4f} {info['r2']:<10.4f} {info['mape']:<9.2f}%")

print("-" * 80)

# Statistics
mapes = [v['mape'] for v in registry.values()]
r2s = [v['r2'] for v in registry.values()]

print(f"\n[Statistics]")
print(f"Total models: {len(registry)}")
print(f"MAPE Avg: {sum(mapes)/len(mapes):.2f}%")
print(f"MAPE Best: {min(mapes):.2f}%")
print(f"MAPE Worst: {max(mapes):.2f}%")
print(f"R2 Avg:   {sum(r2s)/len(r2s):.4f}")
print(f"R2 Best:   {max(r2s):.4f}")

# MAPE Distribution
print(f"\n[MAPE Distribution]")
excellent = sum(1 for m in mapes if m < 3)
good = sum(1 for m in mapes if 3 <= m < 5)
fair = sum(1 for m in mapes if 5 <= m < 8)
poor = sum(1 for m in mapes if m >= 8)

print(f"MAPE < 3% (Excellent): {excellent} ({excellent/len(mapes)*100:.1f}%)")
print(f"MAPE 3-5% (Good):     {good} ({good/len(mapes)*100:.1f}%)")
print(f"MAPE 5-8% (Fair):     {fair} ({fair/len(mapes)*100:.1f}%)")
print(f"MAPE > 8% (Poor):     {poor} ({poor/len(mapes)*100:.1f}%)")

print("\n" + "=" * 80)
