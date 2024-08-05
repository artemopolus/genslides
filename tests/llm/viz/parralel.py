import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Create a sample dataset with vectors of different lengths
data = {
    'Vector1': [10, 20, 30, 40, 50],
    'Vector2': [15, 25, 35],
    'Vector3': [5, 10],
}

# Pad shorter vectors with NaN values to make them the same length
max_length = max(len(v) for v in data.values())
for key, value in data.items():
    data[key] = value + [np.nan] * (max_length - len(value))

df = pd.DataFrame(data)

# Normalize the data
df_normalized = (df - df.mean()) / df.std()

# Create the parallel coordinates plot
plt.figure(figsize=(10, 6))
pd.plotting.parallel_coordinates(df_normalized, 'Vector1', color=['blue', 'red', 'green'])
plt.xlabel("Features")
plt.ylabel("Normalized Values")
plt.title("Parallel Coordinates Plot of Vectors with Different Lengths")
plt.legend(loc='lower right')
plt.show()
